# One-Week PX4 Quaternion and SLAM/Odometry Curriculum

## Outcome

After 40 focused hours, you should be able to:

- Trace rotations and poses across NED, FRD, ENU, FLU, body, camera, odometry, and map frames.
- Read and compose PX4 Hamilton quaternions without guessing multiplication order.
- Explain gimbal lock, quaternion inversion, normalization, and `q` versus `-q`.
- Read PX4's `VehicleAttitude` and `VehicleOdometry` contracts directly from source.
- Explain the SLAM front end, back end, drift, loop closure, relocalization, and VIO at an integration level.
- Trace external vision from a SLAM/VIO producer through MAVLink or DDS, uORB, EKF2, and flight-control outputs.
- Diagnose a likely frame, quaternion, timestamp, covariance, or reset error with a small PX4 experiment.

This curriculum targets **PX4 integration and debugging fluency**, not production SLAM implementation or estimator research.

## Schedule and accounting

Use five eight-hour study days. Breaks are not included in the 40 hours.

| Day | Quaternion and rotation work | SLAM/PX4 odometry work | Total |
| --- | ---: | ---: | ---: |
| 1 | 4 h | 4 h | 8 h |
| 2 | 4 h | 4 h | 8 h |
| 3 | 4 h | 4 h | 8 h |
| 4 | 4 h | 4 h | 8 h |
| 5 | 4 h | 4 h | 8 h |
| **Total** | **20 h** | **20 h** | **40 h** |

Every four-hour block follows this rhythm:

1. **Retrieve — 20 minutes:** answer yesterday's questions without notes.
2. **Acquire — 60 minutes:** one lesson or selected primary-source reading.
3. **Practice — 120 minutes:** calculate, inspect source, run SITL, or modify a small test.
4. **Explain — 40 minutes:** write or speak a concise explanation and record remaining uncertainties.

Do not turn the acquisition hour into several hours of passive reading. The practice is the curriculum.

### Non-negotiable source-code rule

Every lesson must end with a PX4 source exercise. Merely opening a file does not count. Each exercise must produce four things:

1. **Locate:** identify the message definition, function, parameter, or test that owns the behavior.
2. **Predict:** write what the code should do for one concrete input before running it.
3. **Verify:** use a unit test, SITL, `listener`, log, or call trace to compare prediction with behavior.
4. **Record:** save the relevant path/line, observed value, and one-sentence conclusion.

Use this evidence format in every block:

```text
source location:
input and prediction:
verification method:
observed result:
conclusion:
```

The existing frame and quaternion lessons contain a **PX4 source exercise** section. Future lessons should be considered incomplete until that section exists.

---

## Day 1 — Every value belongs to a frame

### Quaternion track — 4 hours

**Tangible win:** predict the sign and meaning of a PX4 yaw before touching quaternion multiplication.

#### Retrieve — 20 minutes

Without notes, draw a drone and label its forward, right, and down axes. Then draw north, east, and down. Write one sentence explaining why “yaw 30 degrees” is incomplete without a frame and convention.

#### Acquire — 60 minutes

- Complete [Lesson 0001: Frames Before Quaternions](lessons/0001-frames-before-quaternions.html).
- Review the [gimbal frame-math cheat sheet](reference/gimbal-frame-math-cheat-sheet.html).
- Read the frame and quaternion comments in [`VehicleAttitude.msg`](../msg/versioned/VehicleAttitude.msg).

#### Practice — 120 minutes

1. Draw NED and FRD axes from three different vehicle headings.
2. For vehicle yaws `0°`, `+90°`, and `-45°`, predict where body-forward points in NED.
3. Revisit the gimbal reproduction. Given an earth target of `0°`, calculate the required relative gimbal yaw for each vehicle yaw.
4. Run or inspect these PX4 topics and annotate every quaternion with its source and destination frames:

   ```text
   listener vehicle_attitude -n 1
   listener gimbal_device_set_attitude -n 1
   listener gimbal_device_attitude_status -n 1
   ```

#### Explain — 40 minutes

Produce a half-page “frame ledger” with this format:

```text
value:
source frame:
destination frame:
units/convention:
evidence:
```

### SLAM/odometry track — 4 hours

**Tangible win:** explain what PX4 consumes from SLAM and what remains on the companion computer.

#### Retrieve — 20 minutes

From memory, write a one-line distinction among visual odometry, VIO, and SLAM. It is fine to be wrong; correct it at the end of the block.

#### Acquire — 60 minutes

- Complete [Lesson 0002: The PX4 Odometry Contract](lessons/0002-px4-odometry-contract.html).
- Read the abstract and introduction of [Cadena et al., *Past, Present, and Future of SLAM*](https://arxiv.org/abs/1606.05830).
- Read the overview and PX4-tuning portions of the [PX4 VIO guide](https://docs.px4.io/main/en/computer_vision/visual_inertial_odometry).
- Read [`VehicleOdometry.msg`](../msg/versioned/VehicleOdometry.msg) once without trying to memorize it.

#### Practice — 120 minutes

1. Draw this pipeline and label which machine owns each stage:

   ```text
   camera + IMU → VIO/SLAM → odometry contract → EKF2 → controllers
                        ↘ map → planner → setpoints ↗
   ```

2. Annotate a hypothetical `VehicleOdometry` message with units, frames, and invalid-value behavior.
3. Classify ten fields into five categories: pose, velocity, time, uncertainty, and continuity/reset.
4. Explain why `[0,0,0]` velocity means “measured stationary,” not “velocity unavailable.”

#### Explain — 40 minutes

Write a corrected four-sentence explanation of visual odometry, VIO, SLAM, and PX4's role. End with: “PX4 normally consumes ______, not ______.”

### Day 1 exit check

- Can you distinguish local FRD from body FRD?
- Can you state what `VehicleAttitude.q` rotates from and to?
- Can you identify the map branch and the odometry branch of a SLAM system?

---

## Day 2 — Compose rotations and poses

### Quaternion track — 4 hours

**Tangible win:** calculate a quaternion inverse and composition, then verify it with PX4's library.

#### Retrieve — 20 minutes

Draw NED and FRD without looking them up. Predict the relative yaw for `vehicle = +90°`, `earth target = 0°`.

#### Acquire — 60 minutes

- Complete [Lesson 0003: Quaternions as Rotations](lessons/0003-quaternions-as-rotations.html).
- Keep the [quaternion rotation cheat sheet](reference/quaternion-rotation-cheat-sheet.html) beside you.
- Read the convention comments at the top of [`Quaternion.hpp`](../src/lib/matrix/matrix/Quaternion.hpp).

#### Practice — 120 minutes

1. Calculate the pure-yaw quaternions for `0°`, `+90°`, `-90°`, `180°`, and `360°`.
2. Invert each and state the physical rotation represented by the result.
3. Verify these invariants using a tiny C++ test or an existing PX4 matrix test:

   ```text
   q * q^-1 = identity
   q and -q rotate a vector identically
   q2 * q1 means first q1, then q2
   ```

4. Reproduce the gimbal conversion with `matrix::Quatf`:

   ```cpp
   q_joint = q_vehicle.inversed() * q_target;
   q_vehicle * q_joint == q_target;
   ```

#### Explain — 40 minutes

Explain the inverse without using the phrase “negative angle” until the final sentence. Focus first on reversing a frame mapping.

### SLAM/odometry track — 4 hours

**Tangible win:** solve a camera-to-body-to-world transform chain in the correct direction.

#### Retrieve — 20 minutes

Write the Day 1 SLAM pipeline from memory. Circle the boundary where the odometry contract begins.

#### Acquire — 60 minutes

- Read the pose/frame portions of [`VehicleOdometry.msg`](../msg/versioned/VehicleOdometry.msg).
- Review the frame definitions in the PX4 VIO guide.
- Read only enough of [Cadena et al.](https://arxiv.org/abs/1606.05830) to understand robot state, landmarks, measurements, and maximum-a-posteriori estimation.

#### Practice — 120 minutes

Use this notation consistently: `T_A_B` maps coordinates from frame B into frame A.

1. Prove with labels—not expanded matrices—that:

   ```text
   T_A_C = T_A_B * T_B_C
   T_B_A = inverse(T_A_B)
   ```

2. Build a transform tree containing `map`, `odom`, `camera`, and `body FRD`.
3. Given `T_map_camera` from SLAM and a calibrated `T_body_camera`, derive `T_map_body`.
4. Compare that derivation with `q_vehicle^-1 * q_target` from the gimbal bug. Identify the shared inverse-and-compose pattern.

#### Explain — 40 minutes

Record a two-minute explanation answering: “Why can numerically correct pose values still be physically wrong?”

### Day 2 exit check

- Can you predict multiplication order before running code?
- Can you derive `T_map_body` without trial-and-error inversion?
- Can you explain why sensor mounting calibration belongs in the transform chain?

---

## Day 3 — Singular coordinates and imperfect estimation

### Quaternion track — 4 hours

**Tangible win:** distinguish a valid orientation from a failing Euler representation.

#### Retrieve — 20 minutes

Write the yaw-only quaternion formula and the PX4 gimbal conversion from memory. Check them only after committing an answer.

#### Acquire — 60 minutes

- Complete [Lesson 0004: Gimbal Lock and Quaternions](lessons/0004-gimbal-lock-and-quaternions.html).
- Review the [gimbal-lock cheat sheet](reference/gimbal-lock-cheat-sheet.html).
- Use [Solà's quaternion paper](https://arxiv.org/abs/1711.02508) only as a reference for product, inverse, unit quaternion, and vector rotation definitions.

#### Practice — 120 minutes

1. Demonstrate two different roll/yaw pairs that represent the same orientation at `pitch = 90°`.
2. Convert a smooth pitch path from `80°` through `100°` into quaternions and Euler angles. Record which representation jumps.
3. Use `Quatf`, `Eulerf`, and `Dcmf` to perform a round trip away from and at the Euler singularity.
4. Write tests that compare physical orientations using quaternion dot product or rotated vectors instead of raw component equality.

#### Explain — 40 minutes

Explain this sentence in your own words: “The orientation is valid, but one coordinate chart failed.” Include the mechanical-gimbal caveat.

### SLAM/odometry track — 4 hours

**Tangible win:** describe where drift comes from and how loop closure changes an estimate.

#### Retrieve — 20 minutes

Draw the four-frame transform chain from Day 2 and derive `T_map_body` again.

#### Acquire — 60 minutes

- Read the abstract, system overview, and architecture figure of [ORB-SLAM3](https://arxiv.org/abs/2007.11898).
- Review the front-end/back-end and robustness portions of [Cadena et al.](https://arxiv.org/abs/1606.05830).

#### Practice — 120 minutes

1. Build a one-page architecture diagram containing tracking, feature association, keyframes, local mapping, optimization, place recognition, relocalization, and loop closure.
2. For each block, state whether it primarily consumes sensor data, produces constraints, or optimizes state.
3. Explain why incremental odometry drifts and why revisiting a place supplies a new long-range constraint.
4. Construct a timeline where loop closure moves the map pose by one metre. Decide which value should remain smooth for PX4 flight control and which transform may absorb the correction.

#### Explain — 40 minutes

Explain the difference between `map` and `odom` to an imaginary PX4 developer. Include why a discontinuous loop-closure correction can be dangerous to a controller.

### Day 3 exit check

- Can you recognize an Euler jump that is not a physical attitude jump?
- Can you distinguish the SLAM front end from the back end?
- Can you explain drift, loop closure, and relocalization without saying “the algorithm just corrects itself”?

---

## Day 4 — Meet the real PX4 interfaces

### Quaternion track — 4 hours

**Tangible win:** audit a quaternion at a PX4 interface boundary.

#### Retrieve — 20 minutes

List five facts required before a quaternion array is meaningful. Include order, convention, source frame, destination frame, and normalization.

#### Acquire — 60 minutes

- Read [`Quaternion.hpp`](../src/lib/matrix/matrix/Quaternion.hpp) around multiplication, inversion, vector rotation, and aliases such as `Quatf`.
- Read [`VehicleAttitude.msg`](../msg/versioned/VehicleAttitude.msg).
- Read the quaternion-validation portion of [`EKF2.cpp`](../src/modules/ekf2/EKF2.cpp).

#### Practice — 120 minutes

Create a small quaternion audit harness or unit test. Feed it:

1. Identity.
2. A normalized 90° yaw.
3. The same orientation as `-q`.
4. A zero quaternion.
5. A quaternion with norm `0.95`.
6. A valid quaternion with the wrong direction (`q^-1`).
7. A valid quaternion in the wrong frame convention.

For every case, separate “numerically invalid” from “numerically valid but semantically wrong.”

#### Explain — 40 minutes

Create a reusable quaternion review checklist. It must make no reference to the variable name being trustworthy evidence.

### SLAM/odometry track — 4 hours

**Tangible win:** trace one external-vision sample from transport to EKF2 fusion.

#### Retrieve — 20 minutes

Write the `VehicleOdometry` field groups from memory: pose, velocity, time, uncertainty, and continuity/reset.

#### Acquire — 60 minutes

- Read [`VehicleOdometry.msg`](../msg/versioned/VehicleOdometry.msg) carefully.
- Trace `MavlinkReceiver::handle_message_odometry()` in [`mavlink_receiver.cpp`](../src/modules/mavlink/mavlink_receiver.cpp).
- Trace `EKF2::UpdateExtVisionSample()` in [`EKF2.cpp`](../src/modules/ekf2/EKF2.cpp).
- Review external-vision controls and delay in the [PX4 EKF2 guide](https://docs.px4.io/main/en/advanced_config/tuning_the_ecl_ekf#external-vision-system).

#### Practice — 120 minutes

1. Draw both supported delivery paths:

   ```text
   MAVLink ODOMETRY → mavlink_receiver → vehicle_visual_odometry → EKF2
   DDS VehicleOdometry → /fmu/in/vehicle_visual_odometry → EKF2
   ```

2. Annotate where time synchronization, frame conversion, validation, variance selection, and reset handling occur.
3. Build three sample packets: fully valid, position-only, and velocity-only. Use the correct NaN invalid markers.
4. Create a failure table for wrong frame, inverse quaternion, stale timestamp, fake zero variance, and missing reset increment.

#### Explain — 40 minutes

Write a one-page “odometry contract checklist” that a SLAM producer must satisfy before its output is allowed to influence PX4.

### Day 4 exit check

- Can you distinguish numeric quaternion validation from frame correctness?
- Can you trace both MAVLink and DDS paths without claiming ROS 2 is required?
- Can you explain why capture time, covariance, and reset counter affect flight behavior?

---

## Day 5 — PX4 external-odometry debugging capstone

### Quaternion track — 4 hours

**Tangible win:** implement and defend the exact camera/SLAM-to-PX4 orientation conversion.

#### Retrieve — 20 minutes

On blank paper, write:

- PX4 quaternion order and convention.
- `VehicleAttitude.q` direction.
- The gimbal earth-to-joint conversion.
- The transform-chain composition rule.
- The difference between `q` and `q^-1`.

#### Acquire — 40 minutes

Review only the sections of Lessons 0002–0004 where your retrieval answers were weak. Do not reread all three lessons.

#### Practice — 140 minutes

Given these calibration outputs:

```text
T_slam_camera
T_body_camera
desired PX4 local frame
```

1. Derive the body pose PX4 expects, with every frame written in every symbol.
2. Implement the quaternion conversion using PX4 `matrix` types or a small test harness.
3. Verify it by transforming body-forward, body-right, and body-down basis vectors.
4. Test identity, 90° yaw, combined roll/pitch/yaw, and `q/-q` cases.
5. Review the result as though it were a safety-critical PR: convention, order, frames, unit norm, edge cases, and tests.

#### Explain — 40 minutes

Give a five-minute explanation of the implementation without saying “I tried this order and it worked.” Every inverse and product must be justified by frame cancellation.

### SLAM/odometry track — 4 hours

**Tangible win:** diagnose intentionally corrupted external odometry in PX4 SITL.

#### Retrieve — 20 minutes

Write the complete odometry contract from memory. Mark anything uncertain, then verify it against `VehicleOdometry.msg`.

#### Capstone setup — 40 minutes

Run PX4 SITL and use a small MAVLink or DDS publisher to send a deterministic synthetic trajectory. ROS 2 is optional. Start with:

```text
stationary for 5 s
move forward 5 m over 10 s
yaw 90° over 5 s
move forward 5 m over 10 s
```

Publish position, quaternion, velocity, capture timestamp, variances, and reset counter. If publisher setup consumes the full 40 minutes, use a prerecorded or unit-test-driven sample instead and preserve the remaining time for diagnosis.

#### Practice — 140 minutes

1. Verify reception with:

   ```text
   listener vehicle_visual_odometry
   listener vehicle_odometry
   listener vehicle_attitude
   ```

2. Enable the intended external-vision fusion inputs and verify EKF2 innovations/status rather than relying only on the Gazebo picture.
3. Inject these faults one at a time:

   - Swap right and down axes.
   - Publish `q^-1` instead of `q`.
   - Add 100 ms to the effective measurement delay.
   - Report unrealistically small variance.
   - Jump the pose without incrementing `reset_counter`.

4. For each fault, write:

   ```text
   predicted symptom:
   observed topic/log evidence:
   root cause:
   minimal correction:
   regression test:
   ```

#### Explain — 40 minutes

Produce a final five-minute briefing: “How SLAM odometry reaches PX4, the five most dangerous contract violations, and how I would prove which one occurred.”

### Day 5 exit check

- Can you derive the orientation conversion from frame labels?
- Can you distinguish frame, quaternion-direction, latency, covariance, and reset failures from evidence?
- Can you propose a regression test before proposing a code fix?

---

## Final assessment

You are ready to contribute effectively at the integration/debugging level when you can complete all of these without guessing:

1. Given two named frames, derive the relative quaternion or pose using inverse and composition.
2. Explain why `q` and `-q` are equivalent but `q` and `q^-1` usually are not.
3. Identify a gimbal-lock Euler jump without claiming the physical attitude disappeared.
4. Annotate every `VehicleOdometry` field with units, frame, timing, uncertainty, and invalid behavior.
5. Explain front end, back end, drift, loop closure, and relocalization.
6. Trace a MAVLink or DDS external-vision sample into EKF2.
7. Predict the distinct symptoms of an axis swap, inverse quaternion, latency error, overconfident covariance, and unreported reset.
8. Build a small reproduction and cite listener or log evidence.

Target at least **6 of 8 independently**. For anything missed, add two focused practice hours later rather than rereading the entire week.

## Primary-source reading strategy

Do not read every source cover to cover during this week.

- **PX4 source and message definitions:** read precisely; they are the contract you will implement.
- **PX4 VIO and EKF2 guides:** read the overview, external-vision, delay, covariance, and troubleshooting sections.
- **Cadena et al.:** use for the SLAM problem structure, estimation perspective, and robustness vocabulary.
- **ORB-SLAM3:** use its overview and architecture to attach the vocabulary to a real system.
- **Solà:** use as a quaternion reference when a convention or equation needs verification; postpone Lie theory and full error-state derivations.

## Daily learning log

End each day with five lines:

```text
One thing I can now derive:
One thing I can now diagnose:
One mistake I made today:
One concept still unclear:
One experiment that would resolve it:
```

Ask your agent to quiz you from yesterday's exit checks at the start of each new day. Retrieval should happen before hints or notes.
