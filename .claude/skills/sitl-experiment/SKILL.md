---
name: sitl-experiment
description: Diagnose and fix a PX4 flight-behaviour problem — oscillation, instability, sluggish or jittery response — by measuring it in ulogs, tracing it to the responsible controller, and validating a fix with controlled SITL parameter sweeps. Use when a log or simulated flight looks wrong and the cause is not yet known.
argument-hint: "<symptom, e.g. 'transition is jittery' or a .ulg path>"
allowed-tools: Bash, Read, Glob, Grep, Write, Edit
---

# PX4 SITL Flight Experiment

Turn "this flight feels wrong" into a measured root cause and a validated fix.
The loop is: **measure → localise → trace → falsify → fix → re-verify.**

The discipline that matters most: *never explain a symptom until you have found
where it actually starts, and never trust a hypothesis you have not tried to
break.* Most wasted effort in this work comes from fixing the phase where a
problem was noticed rather than the phase where it began, and from tuning a
controller that was never in the loop.

## Scripts

In `scripts/`, relative to this skill. All three are dependency-light
(`pyulog`, `numpy`, `pymavlink`) and safe to run repeatedly.

| Script | Purpose |
|---|---|
| `analyze_log.py` | `scan`, `compare`, `trace` — all measurement |
| `run_case.sh` | Fly one case with parameter overrides, save its ulog |
| `fly_profile.py` | The scripted flight, driven over MAVLink |

Run `analyze_log.py --help` and `analyze_log.py <mode> --help` for options.

## Phase 1 — Measure, and localise before explaining

Scan the **whole flight**, never just the window where the symptom was
reported:

```bash
python3 scripts/analyze_log.py scan flight.ulg
```

This prints per-window amplitude, peak-to-peak and dominant frequency, labelled
with VTOL state, and flags every window that is not quiet.

Read the first flagged window, not the worst one. A problem reported "during
transition" that is already present in the hover before it is a hover problem,
and any fix aimed at transition logic will be aimed at the wrong code. This
reframing is usually the single highest-value step in the whole investigation.

Then pick the axis and signal deliberately:

- Roll / pitch / yaw are `xyz[0]` / `xyz[1]` / `xyz[2]`.
- Scan each axis before concluding the problem is on one of them. A
  single-axis problem points at a specific effector; a multi-axis one points at
  estimation, filtering or structure.

Confirm the motion is **physical** before chasing controllers:

```bash
python3 scripts/analyze_log.py compare flight.ulg --phase hover
```

In SIH/Gazebo, `*_groundtruth` topics carry the simulator's true state, and
`compare` reports them automatically. If ground truth is quiet while the
estimate oscillates, the problem is sensing or estimation and the control
investigation below is a dead end.

Watch the aliasing warning. If most spectral energy sits near Nyquist for the
logged rate, the reported frequency is not trustworthy — raise `SDLOG_PROFILE`
or read a faster topic (`sensor_gyro`) before quoting a number.

## Phase 2 — Trace which controller is actually in the loop

Do not assume the mode you are flying determines which controller moves a given
actuator. Verify it from the log:

```bash
python3 scripts/analyze_log.py trace flight.ulg --phase hover \
  --signal actuator_servos:control[0] \
  --candidate vehicle_torque_setpoint_virtual_mc:xyz[1] \
  --candidate vehicle_torque_setpoint_virtual_fw:xyz[1]
```

A candidate that is flat while the output swings cannot be driving it. Compare
amplitude ratios first and correlation second, since aliasing destroys phase on
slowly-logged topics.

Useful structure when reading PX4 logs:

- `vehicle_torque_setpoint` multi-instance 0 and 1 separate the two allocation
  groups; on a VTOL these are typically motors and control surfaces.
- `vehicle_torque_setpoint_virtual_mc` / `_virtual_fw` expose each controller's
  request *before* blending, which is what makes authorship provable.
- `control_allocator_status.torque_setpoint_achieved` shows saturation. Sustained
  saturation with a steady oscillation is a limit cycle: the loop gain is too
  high for the effector, and no amount of setpoint tuning upstream will fix it.

Once you know the responsible controller, read its source before sweeping. Gain
scaling, feedforward and airspeed or altitude compensation inside the controller
are common causes of "the gains look reasonable but behave as if they are 10x
larger", and you cannot guess these from parameter values alone.

## Phase 3 — Sweep, and try to falsify

Each case runs the same flight with one thing changed:

```bash
bash scripts/run_case.sh baseline --model sihsim_xvert \
  --flight-args "--takeoff-alt 30 --hover-hold 8 --to-fw --fw-hold 10"

bash scripts/run_case.sh nogainscale --model sihsim_xvert \
  --flight-args "--takeoff-alt 30 --hover-hold 8 --to-fw --fw-hold 10" \
  PX4_PARAM_FW_ARSP_SCALE_EN=0
```

Logs land in `/tmp/sitl_cases/<case>.ulg`, with PX4 stdout and the flight
transcript alongside for post-mortems.

Rules that keep a sweep trustworthy:

1. **Override with `PX4_PARAM_*`, never by editing files.** rcS applies these
   after the airframe file, so the binary and the working tree stay identical
   across cases. Confirm each override actually landed —
   `ULog(path, ['x']).initial_parameters['NAME']` — because a wrong parameter
   type is silently rejected.
2. **One variable per case.** Two at once cannot be attributed.
3. **Include a deliberately extreme case.** Cut the suspect gain by 30x, not
   20%. If the symptom is unchanged, that hypothesis is dead and you have
   eliminated a whole class of causes in one run. This is the cheapest
   information available, and a negative result here is a success.
4. **Fix the flight profile across cases.** Same altitude, same hold times.
   `fly_profile.py` exits non-zero if a phase fails, so distinguish "flew badly"
   from "did not fly".
5. **Repeat the winner** at least twice. SITL is not perfectly deterministic.

Compare cases on the same window:

```bash
python3 scripts/analyze_log.py compare /tmp/sitl_cases/*.ulg --phase hover
python3 scripts/analyze_log.py compare /tmp/sitl_cases/*.ulg --phase transition
```

Judge a candidate fix on **every** phase, not the one you were fixing. A change
that calms hover and degrades cruise is not a fix. Check the phases you did not
target, and if the fix is a gain reduction, confirm it did not merely make the
vehicle too sluggish to oscillate — step response and tracking error matter as
much as amplitude.

## Phase 4 — Land the fix and re-verify honestly

Write the change into the airframe file under
`ROMFS/px4fmu_common/init.d-posix/airframes/`, then **re-run with no overrides
at all** to prove the committed default reproduces the swept result. A fix that
only works as an environment override is not a fix.

Comment the *why*, since the next reader will not have the logs. State the
mechanism and the number that motivated it:

```bash
# The elevons sit in the propwash, so they keep authority at zero freestream,
# but airspeed scaling assumes freestream and clamps to a 6.8x gain boost below
# FW_AIRSPD_STALL — enough to drive a ~20 Hz pitch limit cycle in hover.
param set-default FW_ARSP_SCALE_EN 0
```

Report to the user: the symptom as measured, where it actually began, the
mechanism, the before/after numbers, and what you checked for regressions.
Include the hypotheses you falsified — they tell the next person which paths are
already closed. State plainly what you did *not* test, especially real-hardware
behaviour, since SIH aerodynamics are approximate and a propwash or stall effect
that dominates in simulation may not transfer.

## Notes

- Build once up front: `make px4_sitl_sih` (or the target matching your model).
  `run_case.sh` uses its own rootfs under `build/<target>/tmp_sitl_cases`, so
  sweeps never disturb an interactive `make ... <model>` session.
- Non-VTOL logs have no `vtol_vehicle_status`, so phase auto-detection is
  unavailable; pass explicit `--start`/`--end` from a `scan` instead.
- `run_case.sh` kills lingering PX4 processes from the same build before
  starting. Close interactive SITL sessions first.
