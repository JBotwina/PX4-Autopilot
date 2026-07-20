# PX4 Engineering Curriculum Resources

## Knowledge

- [PX4 motion-capture guide: coordinate frames](https://docs.px4.io/main/en/tutorials/motion-capture#coordinate-frames)
  Official introduction to PX4 NED earth axes and FRD vehicle axes. Use before interpreting headings or attitude data.
- [MAVLink common messages: `GIMBAL_DEVICE_SET_ATTITUDE`](https://mavlink.io/en/messages/common.html#GIMBAL_DEVICE_SET_ATTITUDE)
  Protocol source of truth for vehicle-frame versus earth-frame gimbal flags and quaternion semantics.
- [MAVLink Gimbal Protocol v2](https://mavlink.io/en/services/gimbal_v2.html)
  Official explanation of gimbal managers, devices, status messages, and legacy yaw-lock behavior.
- [PX4 `VehicleAttitude.msg`](../msg/versioned/VehicleAttitude.msg)
  Local source of truth for quaternion order and the FRD-body-to-NED-earth rotation convention.
- [PX4 matrix `Quaternion.hpp`](../src/lib/matrix/matrix/Quaternion.hpp)
  Local implementation source for Hamilton multiplication order, axis-angle construction, inverse rotation, and vector rotation.
- [NASA: Spacecraft Attitude Representations](https://ntrs.nasa.gov/citations/19990110711)
  Primary overview comparing attitude matrices, Euler angles, and quaternions; identifies gimbal lock as an Euler-angle singularity and the unit quaternion as a convenient four-component representation.
- [NASA: Navigation Filter Best Practices](https://ntrs.nasa.gov/citations/20180003657)
  Technical treatment of attitude representations. Chapter 8 derives gimbal lock as collinearity of the first and third Euler rotation axes and explains why three-parameter attitude coordinates require a singularity or discontinuity.
- [PX4 gimbal setpoint flags](../msg/GimbalDeviceSetAttitude.msg)
  Local definitions of `YAW_IN_VEHICLE_FRAME`, `YAW_IN_EARTH_FRAME`, and lock bits.
- [PX4 `VehicleOdometry.msg`](../msg/versioned/VehicleOdometry.msg)
  Local source of truth for the external-odometry contract: frames, quaternion direction, timestamps, variances, reset counter, and invalid values.
- [PX4 Visual Inertial Odometry guide](https://docs.px4.io/main/en/computer_vision/visual_inertial_odometry)
  Official companion-computer-to-EKF2 integration guidance, including message transport, sensor mounting, delay, and common failure symptoms.
- [PX4 EKF2 guide](https://docs.px4.io/main/en/advanced_config/tuning_the_ecl_ekf)
  Official description of the estimator state, external-vision fusion controls, covariance handling, delays, innovations, and log analysis.
- [Cadena et al.: Past, Present, and Future of SLAM](https://arxiv.org/abs/1606.05830)
  Canonical research survey and tutorial for the SLAM problem, front end, back end, mapping, estimation, robustness, and loop closure.
- [Campos et al.: ORB-SLAM3](https://arxiv.org/abs/2007.11898)
  Primary system paper showing how a modern visual and visual-inertial SLAM architecture combines tracking, mapping, place recognition, relocalization, and multiple maps.
- [Solà: Quaternion Kinematics for the Error-State Kalman Filter](https://arxiv.org/abs/1711.02508)
  Detailed technical reference for quaternion definitions, products, inverses, vector rotation, perturbations, and use in IMU-driven estimation. Use selected sections rather than reading cover to cover in the first week.
- [Gazebo gimbal bridge](../src/modules/simulation/gz_bridge/GZGimbal.cpp)
  The concrete bug site: current `main` reads a quaternion without first converting an earth-frame command to the vehicle-relative joint frame.
- [Fork PR: respect gimbal setpoint frame](https://github.com/JBotwina/PX4-Autopilot/pull/1)
  Worked PX4 example and regression tests for `q_vehicle.inversed() * q_target`.
- [PX4 uORB messaging guide](https://docs.px4.io/main/en/middleware/uorb)
  Official contract for publish/subscribe behavior, queue length, multi-instance topics, message evolution, `listener`, and `uorb top`. Use for internal data-flow debugging.
- [PX4 full-module template](https://docs.px4.io/main/en/modules/module_template)
  Official work-queue module lifecycle built around `ModuleBase`, `ModuleParams`, `ScheduledWorkItem`, callbacks, and `Run()`. Use before modifying module scheduling.
- [PX4 parameters and configurations guide](https://docs.px4.io/main/en/advanced/parameters_and_configurations)
  Official parameter declaration and runtime-update patterns. Use when tracing a parameter from metadata into module behavior.
- [PX4 logging guide](https://docs.px4.io/main/en/dev_log/logging)
  Official source for logger commands, topic selection, profiles, backends, ULog streaming, bandwidth limits, and diagnostics.
- [PX4 ULog file-format specification](https://docs.px4.io/main/en/dev_log/ulog_file_format)
  Format-level description of definitions, metadata, parameters, data, and dropout messages. Use when a problem lies below PlotJuggler or `pyulog` output.
- [PX4 PlotJuggler log-analysis guide](https://docs.px4.io/main/en/log/plotjuggler_log_analysis)
  Official workflow for synchronized ULog plots, reusable layouts, and custom transformations such as quaternion-to-Euler conversion. Use for time-series diagnosis.
- [PX4 MAVLink overview](https://docs.px4.io/main/en/mavlink/)
  Official map of messages, commands, dialects, code generation, streams, and microservices as implemented by PX4.
- [PX4 MAVLink streaming guide](https://docs.px4.io/main/en/mavlink/streaming_messages)
  Source-oriented guide to turning uORB data into outgoing MAVLink streams and configuring requested or default rates.
- [MAVLink Command Protocol](https://mavlink.io/en/services/command.html)
  Protocol source of truth for command targeting, acknowledgements, progress, retransmission, and result codes.
- [PX4 developer flight-mode overview](https://docs.px4.io/main/en/concept/flight_modes)
  Official description of internal modes, mode requirements, restrictions, and the boundary between user intent and allowed vehicle behavior.
- [PX4 Mission mode guide](https://docs.px4.io/main/en/flight_modes_mc/mission)
  Operational source for mission prerequisites, mission commands, activation, execution, and common behavior. Use alongside Navigator source.
- [PX4 simulation overview](https://docs.px4.io/main/en/simulation/)
  Official map of supported simulators, SITL startup, lockstep timing, Gazebo transport, and process responsibilities.
- [PX4 testing and CI overview](https://docs.px4.io/main/en/test_and_ci/)
  Official entry point for unit, integration, sanitizer, and continuous-integration testing. Use to select an appropriate test level.
- [PX4 MAVSDK integration-testing guide](https://docs.px4.io/main/en/test_and_ci/integration_testing_mavsdk)
  Official end-to-end SITL test runner and fixture workflow. Use when a contract cannot be proven below whole-vehicle integration.

## Wisdom (Communities)

- [PX4 Discuss](https://discuss.px4.io/)
  Use for checking frame-convention assumptions with PX4 integrators when documentation and observed hardware behavior differ.
- [PX4 GitHub issues](https://github.com/PX4/PX4-Autopilot/issues)
  Use for comparing reproductions, logs, and maintainers' interpretation of frame-sensitive bugs.

## Gaps

- The learner's comfort with vectors, trigonometry, matrices, and complex numbers has not yet been established.
- A stable local PlotJuggler installation and reusable multi-vehicle PX4 layout have not yet been verified.
