# PX4 Board Support Reply Reference

Use this reference when answering board-support, flight-controller porting, or "officially supported by PX4" questions.

## Minimum Answer

For a new flight controller, tell the requester, with inline citations to the PX4 docs:

1. They do not need private approval to start. The process is public and happens through GitHub.
2. They should create and maintain their own PX4 board target, typically under `boards/<vendor>/<model>/`, instead of reusing a nearby FMU target.
3. They need a unique board ID for bootloader and firmware selection. The ID lives in `firmware.prototype` and is coordinated through a PX4-Bootloader PR.
4. If the board exposes USB, they need a unique VID/PID so QGroundControl can identify it correctly.
5. They must demonstrate stable flight on the current PX4 release and link logs from `logs.px4.io`.
6. They should open a PX4-Autopilot PR containing the board support code, public pinout or connector mapping, a block diagram or schematic summary, and flight-log evidence.
7. After merge, the manufacturer owns maintenance and customer support for that target.

## Useful Documentation

- `docs/en/hardware/board_support_guide.md`: manufacturer process, board IDs, VID/PID, flight logs, PR expectations, support categories.
- `docs/en/hardware/porting_guide.md`: board directory layout and board startup/configuration overview.
- `docs/en/hardware/porting_guide_nuttx.md`: NuttX porting files and firmware-porting sequence.
- `docs/en/hardware/porting_guide_config.md`: PX4 Kconfig and `*.px4board` configuration.
- `docs/en/dev_setup/building_px4.md`: build commands and setup guidance.

## High-Value Local Evidence

Use these searches to ground the answer in real files:

```sh
rg -n "firmware.prototype|default.px4board|nuttx-config|rc.board_sensors" docs/en/hardware boards/px4 boards/ark
rg -n "PX4_BOARD_DIR|PX4_BOARD_VENDOR|PX4_BOARD_MODEL|PX4_BOARD_LABEL" cmake
rg -n "board_id|firmware.prototype|infer_build_target" Tools/bench_test Tools/ci cmake
find boards -maxdepth 3 -name default.px4board -o -name firmware.prototype
```

Representative board target files to inspect:

- `boards/px4/fmu-v5/default.px4board`
- `boards/px4/fmu-v5/firmware.prototype`
- `boards/px4/fmu-v5/init/rc.board_defaults`
- `boards/px4/fmu-v5/nuttx-config/nsh/defconfig`
- `boards/px4/fmu-v5/nuttx-config/include/board.h`
- `boards/px4/fmu-v5/src/board_config.h`

## Reply Template

Use this shape, adjusting for the actual question. Keep the inline citations in the answer; do not rely only on a final reference list.

```md
Yes. The path is public and PR-based; you can start by creating a PX4 board target for GA FC2 and proving it flies on the current release. The PX4 board support guide says manufacturers do not need private approval to begin, and the review happens through GitHub.

1. Create a dedicated target under `boards/<vendor>/<model>/`.
   Start from the closest existing board using the same MCU family, then update `default.px4board`, `nuttx-config/nsh/defconfig`, `nuttx-config/include/board.h`, `src/board_config.h`, and startup files such as `init/rc.board_sensors`. Cite the board support guide and NuttX porting guide.
2. Reserve a unique board ID.
   Put the assigned value in `firmware.prototype` and coordinate it with PX4-Bootloader through a PR. Cite the board support guide.
3. Assign a unique USB VID/PID if the board has USB.
   Do not reuse another vendor's identifiers because QGroundControl uses them for board recognition and firmware matching. Cite the board support guide.
4. Build and test the firmware.
   Build the target, flash it with the PX4 bootloader protocol, fly on the current PX4 release, and upload logs to `logs.px4.io`. Cite the board support guide and building guide.
5. Open the PX4-Autopilot PR.
   Include the board support code, public pinout/connector mapping, block diagram or schematic summary, and flight-log links. Cite the board support guide.
6. Plan ongoing maintenance.
   Manufacturer-supported boards are maintained by the manufacturer after merge. Cite the board support guide or manufacturer-supported autopilots page.
```

## Common Caveats

- If the board is only a peripheral or component, the process is lighter: validate it, update the relevant docs page, and attach proof in a PX4-Autopilot PR. No board ID or firmware target is involved.
- If hardware also runs ArduPilot, recommend aligning the bootloader board ID across both ecosystems to avoid identification and flashing problems.
- New manufacturers should generally avoid the legacy VER/REV ID route and use a dedicated firmware target.
- Do not promise acceptance. Maintainers review the implementation, documentation, flight evidence, and maintainability in the PR.
