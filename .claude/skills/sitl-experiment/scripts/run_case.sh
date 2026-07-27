#!/bin/bash
# Fly one experiment case in SITL and save its ulog under a stable name.
#
# Parameters are injected as PX4_PARAM_* environment variables, which rcS turns
# into `param set` calls after the airframe file is sourced. This overrides the
# airframe defaults without editing any tracked file, so every case in a sweep
# runs against an identical binary and a clean tree.
#
# Usage:
#   run_case.sh <case-name> [--model M] [--build-dir D] [--out-dir D]
#               [--flight-args "..."] [PX4_PARAM_X=v ...]
#
# Examples:
#   run_case.sh baseline --model sihsim_xvert --flight-args "--to-fw"
#   run_case.sh lowgain --model sihsim_xvert PX4_PARAM_FW_PR_P=0.01
set -u

MODEL="sihsim_xvert"
BUILD_DIR="build/px4_sitl_sih"
OUT_DIR="/tmp/sitl_cases"
FLIGHT_ARGS="--to-fw"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ $# -lt 1 ]; then
  echo "usage: run_case.sh <case-name> [options] [PX4_PARAM_X=v ...]" >&2
  exit 2
fi
CASE="$1"; shift

OVERRIDES=()
while [ $# -gt 0 ]; do
  case "$1" in
    --model)       MODEL="$2"; shift 2 ;;
    --build-dir)   BUILD_DIR="$2"; shift 2 ;;
    --out-dir)     OUT_DIR="$2"; shift 2 ;;
    --flight-args) FLIGHT_ARGS="$2"; shift 2 ;;
    PX4_PARAM_*)   OVERRIDES+=("$1"); shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

WS="$(git rev-parse --show-toplevel)" || { echo "not in a git repo" >&2; exit 2; }
BUILD="$WS/$BUILD_DIR"
[ -x "$BUILD/bin/px4" ] || { echo "no px4 binary at $BUILD/bin/px4 — build first" >&2; exit 2; }

# Separate rootfs so a sweep never disturbs the interactive `make ...` rootfs.
ROOTFS="$BUILD/tmp_sitl_cases/rootfs"

pkill -f "$BUILD/bin/px4" 2>/dev/null
sleep 2
rm -rf "$ROOTFS"
mkdir -p "$ROOTFS" "$OUT_DIR"
cd "$ROOTFS" || exit 1

export PX4_SIM_MODEL="$MODEL"
export PX4_SIM_SPEED_FACTOR=1
for kv in "${OVERRIDES[@]:-}"; do
  [ -n "$kv" ] && export "$kv" && echo "override: $kv"
done

PX4_LOG="$OUT_DIR/$CASE.px4.log"
nice --20 "$BUILD/bin/px4" "$BUILD/etc" -s etc/init.d-posix/rcS \
  -t "$WS/test_data" -d > "$PX4_LOG" 2>&1 &
PX4_PID=$!
echo "px4 pid $PX4_PID (stdout: $PX4_LOG)"

sleep 8
if ! kill -0 "$PX4_PID" 2>/dev/null; then
  echo "PX4 died during startup; tail of $PX4_LOG:" >&2
  tail -30 "$PX4_LOG" >&2
  exit 1
fi

# shellcheck disable=SC2086
python3 "$SCRIPT_DIR/fly_profile.py" $FLIGHT_ARGS 2>&1 | tee "$OUT_DIR/$CASE.fly.log"
FLY_RC=${PIPESTATUS[0]}

sleep 2
kill -TERM "$PX4_PID" 2>/dev/null
sleep 3
kill -KILL "$PX4_PID" 2>/dev/null

# Copy the log out before the next case wipes the rootfs.
ULG=$(find "$ROOTFS/log" -name "*.ulg" -printf "%T@ %p\n" 2>/dev/null \
      | sort -rn | head -1 | cut -d' ' -f2)
if [ -n "$ULG" ]; then
  cp "$ULG" "$OUT_DIR/$CASE.ulg"
  echo "CASE=$CASE FLY_RC=$FLY_RC ULG=$OUT_DIR/$CASE.ulg"
else
  echo "CASE=$CASE FLY_RC=$FLY_RC ULG=NONE (no ulog produced)" >&2
  exit 1
fi
exit "$FLY_RC"
