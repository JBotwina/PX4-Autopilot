#!/usr/bin/env python3
"""Quantify flight behaviour in PX4 ulogs. Requires pyulog and numpy.

Modes:
  scan     whole flight in fixed windows, flagging oscillation episodes
  compare  one window per log, side by side across experiment cases
  trace    find which of several candidate signals actually drives an output

Examples:
  analyze_log.py scan case.ulg
  analyze_log.py scan case.ulg --field xyz[0] --window 1.0
  analyze_log.py compare baseline.ulg fix.ulg --phase transition
  analyze_log.py compare a.ulg b.ulg --start 34 --end 42
  analyze_log.py trace case.ulg --start 34 --end 42 \
      --signal actuator_servos:control[0] \
      --candidate vehicle_torque_setpoint_virtual_mc:xyz[1] \
      --candidate vehicle_torque_setpoint_virtual_fw:xyz[1]
"""

import argparse
import sys

import numpy as np
from pyulog import ULog

DEG = 180.0 / np.pi
VTOL_NAMES = {0: "UNDEF", 1: "TR>FW", 2: "TR>MC", 3: "MC", 4: "FW"}
OSC_THRESHOLD = 5.0  # deg/s std; above this a hover/transition window is not quiet


def read(path, topics=None):
    return ULog(path, topics)


def series(ulog, name, field, scale=1.0, multi_id=0):
    """Return (t_seconds, values) for one topic field, or (None, None)."""
    for d in ulog.data_list:
        if d.name == name and d.multi_id == multi_id:
            if field not in d.data:
                return None, None
            return (np.asarray(d.data["timestamp"], dtype=float) / 1e6,
                    np.asarray(d.data[field], dtype=float) * scale)
    return None, None


def oscillation(t, y):
    """Amplitude and dominant frequency of the fluctuation about the mean.

    Returns None when the window holds too few samples to be meaningful.
    """
    if t is None or len(t) < 16:
        return None
    detrended = y - y.mean()
    dt = np.median(np.diff(t))
    if not np.isfinite(dt) or dt <= 0:
        return None
    spec = np.abs(np.fft.rfft(detrended * np.hanning(len(detrended))))
    freqs = np.fft.rfftfreq(len(detrended), dt)
    peak = freqs[np.argmax(spec[1:]) + 1] if len(freqs) > 1 else float("nan")
    nyquist = 0.5 / dt
    high = freqs > 0.8 * nyquist
    return dict(std=float(y.std()), p2p=float(np.ptp(y)), peak_hz=float(peak),
                fs=float(1 / dt), nyquist=float(nyquist),
                near_nyquist=float((spec[high] ** 2).sum() / max((spec[1:] ** 2).sum(), 1e-30)))


def vtol_phases(ulog):
    """Locate the first MC->FW and FW->MC transition, if this is a VTOL log."""
    t, st = series(ulog, "vtol_vehicle_status", "vehicle_vtol_state")
    if t is None:
        return {}
    out = {}
    for want, key in [(1, "transition"), (2, "back_transition")]:
        for i in range(len(st) - 1):
            if st[i] != want and st[i + 1] == want:
                end = t[-1]
                for j in range(i + 1, len(st)):
                    if st[j] != want:
                        end = t[j]
                        break
                out[key] = (float(t[i + 1]), float(end))
                break
    if "transition" in out:
        a, _ = out["transition"]
        out["hover"] = (max(t[0], a - 8.0), a - 0.2)
    if "transition" in out:
        _, b = out["transition"]
        out["cruise"] = (b + 2.0, min(t[-1], b + 12.0))
    return out


def state_at(ulog, t_query):
    t, st = series(ulog, "vtol_vehicle_status", "vehicle_vtol_state")
    if t is None:
        return ""
    return VTOL_NAMES.get(int(st[np.argmin(np.abs(t - t_query))]), "?")


def cmd_scan(args):
    ulog = read(args.log)
    t, y = series(ulog, args.topic, args.field, DEG if args.degrees else 1.0)
    if t is None:
        print(f"ERROR: {args.topic}:{args.field} not in log", file=sys.stderr)
        return 1
    phases = vtol_phases(ulog)
    print(f"=== {args.log}  {args.topic}:{args.field}"
          f"{' [deg/s]' if args.degrees else ''} ===")
    for key, (a, b) in sorted(phases.items(), key=lambda kv: kv[1][0]):
        print(f"  phase {key:16s} {a:8.2f} -> {b:8.2f}s  ({b - a:.2f}s)")
    print(f"\n{'t':>7} {'state':>6} {'std':>9} {'p2p':>9} {'peak':>8}   flag")
    worst, worst_t = 0.0, None
    for start in np.arange(np.floor(t[0]), t[-1], args.window):
        m = (t >= start) & (t < start + args.window)
        r = oscillation(t[m], y[m])
        if r is None:
            continue
        state = state_at(ulog, start)
        hot = r["std"] > args.threshold
        if hot and state != "FW" and r["std"] > worst:
            worst, worst_t = r["std"], start
        print(f"{start:7.1f} {state:>6} {r['std']:9.2f} {r['p2p']:9.1f} "
              f"{r['peak_hz']:7.2f}Hz   {'<<< OSCILLATING' if hot else ''}")
    if worst_t is not None:
        print(f"\n  worst non-cruise window: {worst:.2f} at t={worst_t:.1f}s")
    else:
        print(f"\n  no window outside cruise exceeded {args.threshold} — flight is quiet")
    return 0


def resolve_window(ulog, args):
    if args.start is not None and args.end is not None:
        return args.start, args.end
    phases = vtol_phases(ulog)
    if args.phase in phases:
        return phases[args.phase]
    return None


def cmd_compare(args):
    print(f"window: {args.phase if args.start is None else f'{args.start}-{args.end}s'}")
    print(f"\n{'case':28} {'std':>9} {'p2p':>9} {'peak':>9} "
          f"{'alloc_ok%':>10} {'window':>8}")
    for path in args.logs:
        ulog = read(path)
        win = resolve_window(ulog, args)
        if win is None:
            print(f"{path.split('/')[-1]:28} -- phase not found --")
            continue
        a, b = win
        t, y = series(ulog, args.topic, args.field, DEG if args.degrees else 1.0)
        if t is None:
            print(f"{path.split('/')[-1]:28} -- signal missing --")
            continue
        m = (t >= a) & (t < b)
        r = oscillation(t[m], y[m])
        tc, sat = series(ulog, "control_allocator_status", "torque_setpoint_achieved")
        ok = float("nan")
        if tc is not None:
            ms = (tc >= a) & (tc < b)
            ok = sat[ms].mean() * 100 if ms.any() else float("nan")
        if r is None:
            print(f"{path.split('/')[-1]:28} -- window too short --")
            continue
        print(f"{path.split('/')[-1]:28} {r['std']:9.2f} {r['p2p']:9.1f} "
              f"{r['peak_hz']:8.2f}Hz {ok:10.1f} {b - a:7.2f}s")
        if r["near_nyquist"] > 0.15:
            print(f"{'':28} WARNING: {r['near_nyquist']:.0%} of energy near "
                  f"Nyquist ({r['nyquist']:.0f}Hz) — logged too slowly to trust peak")
        tg, yg = series(ulog, args.topic + "_groundtruth", args.field,
                        DEG if args.degrees else 1.0)
        if tg is not None:
            mg = (tg >= a) & (tg < b)
            rg = oscillation(tg[mg], yg[mg])
            if rg:
                # Ground truth close to the estimate means the airframe really is
                # moving; a large gap would point at sensing or estimation instead.
                note = ("matches estimate" if abs(rg["std"] - r["std"]) < 0.25 * max(r["std"], 1e-6)
                        else "DIVERGES from estimate — suspect sensing/estimation")
                print(f"{'':28} groundtruth: std={rg['std']:.2f} "
                      f"peak={rg['peak_hz']:.2f}Hz  ({note})")
    return 0


def cmd_trace(args):
    """Compare an output signal against candidate drivers by amplitude and shape."""
    ulog = read(args.log)
    win = resolve_window(ulog, args)
    if win is None:
        print(f"ERROR: could not resolve window", file=sys.stderr)
        return 1
    a, b = win
    st, sf = args.signal.split(":")
    ts, ys = series(ulog, st, sf)
    if ts is None:
        print(f"ERROR: signal {args.signal} not in log", file=sys.stderr)
        return 1
    m = (ts >= a) & (ts < b)
    ref = ys[m]
    print(f"=== trace {args.signal} in [{a:.2f},{b:.2f}]s of {args.log.split('/')[-1]} ===")
    print(f"  signal: std={ref.std():.4f} rms={np.sqrt(np.mean(ref**2)):.4f} "
          f"logged at {1/np.median(np.diff(ts[m])):.0f} Hz\n")
    print(f"  {'candidate':52} {'std':>9} {'ratio':>7} {'corr':>7}")
    for cand in args.candidate:
        ct, cf = cand.split(":")
        tc, yc = series(ulog, ct, cf)
        if tc is None:
            print(f"  {cand:52} -- missing --")
            continue
        interp = np.interp(ts[m], tc, yc)
        mc_ = (tc >= a) & (tc < b)
        cstd = yc[mc_].std() if mc_.any() else float("nan")
        ratio = ref.std() / cstd if cstd > 1e-12 else float("inf")
        corr = np.corrcoef(ref, interp)[0, 1] if len(ref) > 2 else float("nan")
        print(f"  {cand:52} {cstd:9.4f} {ratio:7.2f} {corr:+7.3f}")
    print("\n  A candidate whose std is ~0 while the signal swings cannot be driving it.")
    print("  Prefer the amplitude ratio over corr when the signal is logged slower")
    print("  than the oscillation, because aliasing destroys phase.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_signal_args(p):
        p.add_argument("--topic", default="vehicle_angular_velocity")
        p.add_argument("--field", default="xyz[1]",
                       help="xyz[0]=roll xyz[1]=pitch xyz[2]=yaw")
        p.add_argument("--degrees", action="store_true", default=True)
        p.add_argument("--radians", dest="degrees", action="store_false")

    s = sub.add_parser("scan", help="whole flight, window by window")
    s.add_argument("log")
    s.add_argument("--window", type=float, default=2.0)
    s.add_argument("--threshold", type=float, default=OSC_THRESHOLD)
    add_signal_args(s)
    s.set_defaults(func=cmd_scan)

    c = sub.add_parser("compare", help="one window across several logs")
    c.add_argument("logs", nargs="+")
    c.add_argument("--phase", default="transition",
                   choices=["hover", "transition", "back_transition", "cruise"])
    c.add_argument("--start", type=float)
    c.add_argument("--end", type=float)
    add_signal_args(c)
    c.set_defaults(func=cmd_compare)

    t = sub.add_parser("trace", help="find which signal drives an output")
    t.add_argument("log")
    t.add_argument("--signal", required=True, metavar="topic:field")
    t.add_argument("--candidate", action="append", required=True, metavar="topic:field")
    t.add_argument("--phase", default="hover",
                   choices=["hover", "transition", "back_transition", "cruise"])
    t.add_argument("--start", type=float)
    t.add_argument("--end", type=float)
    t.set_defaults(func=cmd_trace)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
