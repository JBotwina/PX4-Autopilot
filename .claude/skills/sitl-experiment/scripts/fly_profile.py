#!/usr/bin/env python3
"""Fly a scripted SITL profile over MAVLink so every experiment run is identical.

Requires pymavlink. Exits 0 only if every requested phase succeeded, so a run
that fails outright is distinguishable from one that merely flies badly.

  fly_profile.py --takeoff-alt 30 --hover-hold 8 --to-fw --fw-hold 12
  fly_profile.py --takeoff-alt 50 --to-fw --fw-hold 20 --to-mc --land
"""

import argparse
import sys
import time

from pymavlink import mavutil

VTOL_STATE = {0: "UNDEF", 1: "TRANS_TO_FW", 2: "TRANS_TO_MC", 3: "MC", 4: "FW"}
T_START = time.time()


def log(msg):
    print(f"[fly {time.time() - T_START:6.1f}s] {msg}", flush=True)


class Vehicle:
    """MAVLink connection that keeps the latest telemetry in one place."""

    def __init__(self, url):
        self.m = mavutil.mavlink_connection(url)
        log(f"connecting on {url}")
        if self.m.wait_heartbeat(timeout=90) is None:
            raise RuntimeError("no heartbeat")
        log(f"heartbeat from system {self.m.target_system}")
        self.rel_alt = None
        self.amsl = None
        self.vtol = None
        self.armed = False
        self.acks = {}

    def pump(self, seconds=0.0):
        """Drain queued messages for `seconds`, refreshing cached state."""
        deadline = time.time() + seconds
        while True:
            msg = self.m.recv_match(blocking=False)
            while msg is not None:
                t = msg.get_type()
                if t == "GLOBAL_POSITION_INT":
                    self.rel_alt = msg.relative_alt / 1000.0
                    self.amsl = msg.alt / 1000.0
                elif t == "EXTENDED_SYS_STATE":
                    self.vtol = msg.vtol_state
                elif t == "HEARTBEAT":
                    self.armed = bool(msg.base_mode
                                      & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
                elif t == "COMMAND_ACK":
                    self.acks[msg.command] = msg.result
                msg = self.m.recv_match(blocking=False)
            if time.time() >= deadline:
                return
            time.sleep(0.02)

    def request_streams(self):
        for mid, hz in [(mavutil.mavlink.MAVLINK_MSG_ID_EXTENDED_SYS_STATE, 10),
                        (mavutil.mavlink.MAVLINK_MSG_ID_GLOBAL_POSITION_INT, 10)]:
            self.cmd(mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, mid, int(1e6 / hz))
            self.pump(0.2)

    def set_param(self, name, value, is_int=False):
        """Set one parameter. Type must match the firmware's or PX4 rejects it."""
        ptype = (mavutil.mavlink.MAV_PARAM_TYPE_INT32 if is_int
                 else mavutil.mavlink.MAV_PARAM_TYPE_REAL32)
        self.m.mav.param_set_send(self.m.target_system, self.m.target_component,
                                  name.encode(), float(value), ptype)
        deadline = time.time() + 4
        while time.time() < deadline:
            msg = self.m.recv_match(type="PARAM_VALUE", blocking=True, timeout=0.5)
            if msg and msg.param_id.strip("\x00") == name:
                log(f"param {name} = {msg.param_value}")
                return True
        log(f"WARNING: no confirmation for {name} (wrong type?)")
        return False

    def cmd(self, command, *params):
        self.acks.pop(command, None)
        p = list(params) + [0] * (7 - len(params))
        self.m.mav.command_long_send(self.m.target_system, self.m.target_component,
                                     command, 0, *p)

    def wait_ack(self, command, timeout=10):
        deadline = time.time() + timeout
        while time.time() < deadline:
            self.pump(0.1)
            if command in self.acks:
                return self.acks[command]
        return None

    def wait_for(self, predicate, timeout, what):
        deadline = time.time() + timeout
        while time.time() < deadline:
            self.pump(0.1)
            if predicate():
                return True
        log(f"TIMEOUT waiting for {what}")
        return False


def arm_and_takeoff(v, alt, timeout):
    if not v.wait_for(lambda: v.amsl is not None, 90, "position fix"):
        return False
    # MAV_CMD_NAV_TAKEOFF param7 is AMSL, not height above home.
    target_amsl = v.amsl + alt
    log(f"home {v.amsl:.1f} m AMSL, takeoff target {target_amsl:.1f} m AMSL")
    v.pump(5)

    log("arming")
    v.cmd(mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 1)
    if v.wait_ack(mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM) != 0:
        log("arm rejected, retrying with force flag")
        v.cmd(mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 1, 21196)
        if v.wait_ack(mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM) != 0:
            log("ARM FAILED")
            return False

    nan = float("nan")
    v.cmd(mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, nan, nan, nan, target_amsl)
    log(f"takeoff ack {v.wait_ack(mavutil.mavlink.MAV_CMD_NAV_TAKEOFF)}")

    log(f"climbing to {alt} m")
    if not v.wait_for(lambda: v.rel_alt is not None and v.rel_alt >= alt - 1.5,
                      timeout, f"{alt} m"):
        log(f"reached only {v.rel_alt} m")
        return False
    log(f"reached {v.rel_alt:.1f} m")
    return True


def transition(v, want, timeout):
    name = VTOL_STATE[want]
    log(f"commanding transition to {name}")
    v.cmd(mavutil.mavlink.MAV_CMD_DO_VTOL_TRANSITION, want)
    log(f"transition ack {v.wait_ack(mavutil.mavlink.MAV_CMD_DO_VTOL_TRANSITION)}")
    if not v.wait_for(lambda: v.vtol == want, timeout, name):
        log(f"last state {VTOL_STATE.get(v.vtol, v.vtol)}")
        return False
    log(f"{name} reached")
    return True


def hold_state(v, want, seconds):
    """Hold a VTOL state, failing if it is lost (e.g. a quad-chute)."""
    log(f"holding {VTOL_STATE[want]} for {seconds}s")
    deadline = time.time() + seconds
    while time.time() < deadline:
        v.pump(0.5)
        if v.vtol != want:
            log(f"LOST {VTOL_STATE[want]}, now {VTOL_STATE.get(v.vtol, v.vtol)}")
            return False
    log("held")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="udpin:0.0.0.0:14540")
    ap.add_argument("--takeoff-alt", type=float, default=30.0)
    ap.add_argument("--takeoff-timeout", type=float, default=120.0)
    ap.add_argument("--hover-hold", type=float, default=8.0,
                    help="settle time at altitude before any transition")
    ap.add_argument("--to-fw", action="store_true", help="transition to fixed wing")
    ap.add_argument("--fw-hold", type=float, default=12.0)
    ap.add_argument("--to-mc", action="store_true", help="transition back to hover")
    ap.add_argument("--mc-hold", type=float, default=10.0)
    ap.add_argument("--land", action="store_true")
    ap.add_argument("--extra-hover", type=float, default=0.0,
                    help="extra quiet hover time, useful as a clean reference window")
    args = ap.parse_args()

    v = Vehicle(args.url)
    v.request_streams()
    # keep a link/RC dropout from ending the run early
    v.set_param("NAV_RCL_ACT", 0, is_int=True)
    v.set_param("NAV_DLL_ACT", 0, is_int=True)
    v.set_param("COM_DISARM_LAND", 0)
    v.set_param("MIS_TAKEOFF_ALT", args.takeoff_alt)

    if not arm_and_takeoff(v, args.takeoff_alt, args.takeoff_timeout):
        return 1

    log(f"settling {args.hover_hold}s")
    v.pump(args.hover_hold)
    if args.extra_hover > 0:
        log(f"extra hover reference window {args.extra_hover}s")
        v.pump(args.extra_hover)

    if args.to_fw:
        if not transition(v, 4, 40):
            return 1
        if not hold_state(v, 4, args.fw_hold):
            return 1

    if args.to_mc:
        if not transition(v, 3, 40):
            return 1
        if not hold_state(v, 3, args.mc_hold):
            return 1

    if args.land:
        log("landing")
        v.cmd(mavutil.mavlink.MAV_CMD_NAV_LAND)
        log(f"land ack {v.wait_ack(mavutil.mavlink.MAV_CMD_NAV_LAND)}")
        v.wait_for(lambda: not v.armed, 120, "disarm after landing")

    log("SUCCESS: profile complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
