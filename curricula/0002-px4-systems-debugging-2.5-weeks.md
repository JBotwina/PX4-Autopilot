# PX4 Systems and Debugging — 2.5-Week Continuation

## Purpose

This 100-hour continuation builds practical PX4 codebase fluency for bounded,
test-backed contributions. It follows the quaternion and SLAM/odometry week and
connects that domain knowledge to the infrastructure needed for the longer-term
swarm-logging goal.

This is not a maintainer or research curriculum. The target is to become able to:

- enter an unfamiliar PX4 issue without treating the repository as a black box;
- trace data across a module, uORB, the logger, MAVLink, Commander, and Navigator;
- reproduce behavior in SITL and distinguish PX4 behavior from simulator behavior;
- make a concrete prediction from source, verify it, and preserve the result in a test;
- contribute small fixes, diagnostics, documentation, and regression tests safely.

## Schedule and accounting

Each full week contains five eight-hour days. The final half-week contains two
eight-hour days and one four-hour day.

| Period | Track | Hours |
| --- | --- | ---: |
| Week A | PX4 modules, uORB, work queues, and parameters | 20 h |
| Week A | ULog and PX4 logging | 20 h |
| Week B | MAVLink inside PX4 | 20 h |
| Week B | Commander, Navigator, and mission state machines | 20 h |
| Half-week C | SITL, Gazebo, and PX4 testing | 20 h |
| **Total** |  | **100 h** |

Every four-hour block uses the same rhythm as the first curriculum:

1. **Retrieve — 20 minutes:** answer from memory before opening notes or source.
2. **Acquire — 60 minutes:** read one small part of the official docs and source.
3. **Practice — 120 minutes:** trace, predict, run, perturb, and test.
4. **Explain — 40 minutes:** record evidence and explain the behavior plainly.

### Evidence rule for every block

Opening a source file is not completion. Every block must produce:

```text
source location:
input and prediction:
verification method:
observed result:
conclusion:
next regression test:
```

Keep changes made for experiments outside a final patch unless the exercise asks
for a test. Before retaining a change, restore the normal input and prove that the
observed behavior returns to normal.

---

# Week A — Internal data flow and durable evidence

## Week A outcome

At the end of this week, you should be able to trace one value from a scheduled
module through uORB into a ULog file or live ULog stream, explain where samples
can be overwritten or dropped, and keep independent logging state for two PX4
vehicles.

## Day A1 — A PX4 module and a PX4 log are pipelines

### Modules track — module lifecycle and ownership (4 hours)

**Tangible win:** explain who constructs, schedules, runs, reports, and destroys a
work-queue module.

#### Retrieve — 20 minutes

Draw your current mental model of a PX4 module. Mark where you think its thread,
inputs, parameters, and command-line entry point live.

#### Acquire — 60 minutes

- Read the official [module template guide](https://docs.px4.io/main/en/modules/module_template).
- Read [`WorkItemExample.hpp`](../src/examples/work_item/WorkItemExample.hpp) and
  [`WorkItemExample.cpp`](../src/examples/work_item/WorkItemExample.cpp).
- Locate `ModuleBase`, `ModuleParams`, `ScheduledWorkItem`, `task_spawn()`,
  `init()`, `Run()`, `print_status()`, and `custom_command()`.

#### Practice — 120 minutes

1. Draw the lifecycle from the shell command to the first call to `Run()`.
2. Predict what triggers the example: a fixed interval, a callback, or both.
3. Build SITL, start the example if it is included in the build, and compare
   `status` output with your prediction. If it is not included, use source and an
   existing scheduled module without changing the board configuration.
4. Find one real module that schedules periodically and one that registers a uORB
   callback. Record why each scheduling choice fits its job.
5. Predict what would happen if `Run()` blocked for one second on a shared work
   queue. Verify using work-queue status or a tightly scoped temporary experiment.

#### Explain — 40 minutes

Explain the difference between a module, a task, a work-queue item, and a uORB
callback without using the word “thread” as though all four mean the same thing.

### Logging track — from uORB sample to backend (4 hours)

**Tangible win:** draw the logger path without assuming that a ULog file is just a
CSV dump.

#### Retrieve — 20 minutes

Write the logging path you currently expect, beginning with a publisher and ending
with storage. Circle every boundary where data could be buffered or lost.

#### Acquire — 60 minutes

- Read the overview and usage portions of the official
  [PX4 logging guide](https://docs.px4.io/main/en/dev_log/logging).
- Read the top-level responsibilities in [`logger.cpp`](../src/modules/logger/logger.cpp),
  [`log_writer.cpp`](../src/modules/logger/log_writer.cpp), and
  [`log_writer_file.cpp`](../src/modules/logger/log_writer_file.cpp).
- Skim [Lesson 0005: Trace PX4 Logging for a Swarm](lessons/0005-trace-px4-logging-for-a-swarm.html) as the Week A roadmap; return to its two-vehicle experiment on Day A5.

#### Practice — 120 minutes

1. Draw this path and replace every generic label with a class or function:

   ```text
   uORB publication → logger subscription → ULog encoder → writer → backend
   ```

2. Predict when `logger status` changes as you run `logger on`, `logger off`, arm,
   and disarm in SITL.
3. Run those cases and record the resulting file creation behavior.
4. Locate where file and MAVLink backends diverge. Identify state that belongs to
   the encoder and state that belongs to one backend.

#### Explain — 40 minutes

Explain why “the logger received a sample,” “the writer accepted bytes,” and “the
bytes reached durable storage” are three different claims.

### Day A1 exit check

- Can you name the function that causes a selected module to run again?
- Can you identify the boundary between ULog serialization and backend delivery?
- Can you state one reason a topic could exist in uORB but not appear in a log?

## Day A2 — Queue semantics and topic selection

### Modules track — uORB publication, subscription, and queues (4 hours)

**Tangible win:** predict whether a subscriber receives every publication or only
the latest sample.

#### Retrieve — 20 minutes

From memory, describe what `updated()`, `copy()`, and `update()` should mean. Do
not check the headers until you have committed an answer.

#### Acquire — 60 minutes

- Read the official [uORB messaging guide](https://docs.px4.io/main/en/middleware/uorb),
  especially queue length, message versioning, `listener`, and `uorb top`.
- Read [`Subscription.hpp`](../platforms/common/uORB/Subscription.hpp),
  [`Publication.hpp`](../platforms/common/uORB/Publication.hpp), and
  [`SubscriptionMultiArray.hpp`](../platforms/common/uORB/SubscriptionMultiArray.hpp).
- Compare a default one-sample message with [`VehicleCommand.msg`](../msg/versioned/VehicleCommand.msg).

#### Practice — 120 minutes

1. Choose a high-rate state topic and a queued event/command topic.
2. Predict the effect of a slow subscriber on each.
3. Observe both using `listener` and `uorb top`; record frequency, queue size,
   instance count, and lost-message evidence.
4. Trace a multi-instance topic from its `.msg` definition through a publication
   and a subscriber. Explain what the instance number means and what it does not
   mean.
5. Write a small unit-level experiment or use `uorb_tests` to verify one queue
   assumption.

#### Explain — 40 minutes

Explain why a queue length of one is often correct for state but dangerous for a
command. Include the difference between “latest truth” and “every event.”

### Logging track — default topics, profiles, and intervals (4 hours)

**Tangible win:** predict whether a specific topic and instance will be logged and
at what maximum rate.

#### Retrieve — 20 minutes

List three separate decisions that determine whether a sample reaches a ULog:
topic selection, subscription behavior, and backend capacity.

#### Acquire — 60 minutes

- Read [`logged_topics.cpp`](../src/modules/logger/logged_topics.cpp).
- Read the logging-guide sections on `SDLOG_PROFILE` and `logger_topics.txt`.
- Inspect [`module.yaml`](../src/modules/logger/module.yaml) and
  [`LoggerStatus.msg`](../msg/LoggerStatus.msg).

#### Practice — 120 minutes

1. Pick `vehicle_attitude`, a multi-instance sensor topic, and one topic not in the
   normal profile. Predict which will appear in a default SITL ULog.
2. Create a temporary SITL `logger_topics.txt` that adds the missing topic at a
   bounded interval. Preserve the original file.
3. Produce a short log, inspect it with `ulog_info` or `pyulog`, and compare actual
   topic instances and rates with your prediction.
4. Remove the temporary configuration and prove that default behavior returns.
5. Explain how changing or removing a `.msg` field can affect log consumers.

#### Explain — 40 minutes

Write a decision tree for “the topic exists in `listener` but is absent from the
ULog.”

### Day A2 exit check

- Can you explain why a slow subscriber may miss state samples without a bug?
- Can you identify the source that defines default logger topic selection?
- Can you distinguish uORB queue loss from logger-rate limiting?

## Day A3 — Scheduling and ULog structure

### Modules track — work queues, timing, and performance (4 hours)

**Tangible win:** distinguish publication-driven work from periodic housekeeping
and recognize work that should not block a shared queue.

#### Retrieve — 20 minutes

Draw the lifecycle from Day A1 again. Add the points where a callback is registered,
unregistered, scheduled, and rescheduled after failure.

#### Acquire — 60 minutes

- Revisit `WorkItemExample::init()` and `WorkItemExample::Run()`.
- Inspect the scheduled-work-item implementation under
  [`platforms/common/px4_work_queue`](../platforms/common/px4_work_queue).
- Find `perf_*` counters in two real modules and read the associated status output.

#### Practice — 120 minutes

1. Select one work queue with several consumers and list them using shell status
   commands or source registration sites.
2. Predict the symptom of one consumer overrunning its intended execution time.
3. Use existing performance counters to verify execution interval and elapsed time
   for a selected module.
4. Make a temporary, harmless scheduling-period change in SITL. Predict and observe
   publication-rate and CPU consequences, then revert it.
5. Write a review checklist for callback registration, backup scheduling, cleanup,
   and blocking operations.

#### Explain — 40 minutes

Explain why “my module runs at 100 Hz” is incomplete unless you distinguish desired
schedule, input update rate, actual execution rate, and output publication rate.

### Logging track — ULog definitions, data, and dropout evidence (4 hours)

**Tangible win:** identify the parts of a ULog required to interpret later data and
recognize explicit evidence of loss.

#### Retrieve — 20 minutes

Predict what metadata a standalone log reader needs if it does not have the exact
PX4 source checkout that produced the log.

#### Acquire — 60 minutes

- Read the message-type overview in the official
  [ULog file-format specification](https://docs.px4.io/main/en/dev_log/ulog_file_format).
- Inspect ULog message construction in [`logger.cpp`](../src/modules/logger/logger.cpp)
  and helper code in [`util.cpp`](../src/modules/logger/util.cpp).
- Inspect [`ULogMessagesTest.cpp`](../src/modules/logger/ULogMessagesTest.cpp).

#### Practice — 120 minutes

1. Label the file header, flag bits, format definitions, parameter information,
   add-logged-message records, data records, and dropout records in a small ULog.
2. Predict which records must occur before the first data record for a topic.
3. Verify the ordering using `ulog_info`, `pyulog`, or a hex-aware parser.
4. Use an existing logger unit test as a model and add a temporary assertion for
   one ordering or size invariant. Run the smallest relevant test target.
5. Explain how ULog distinguishes “the value was zero” from “no data was recorded.”

#### Explain — 40 minutes

Explain why preserving definitions and metadata is part of logging correctness,
not optional documentation.

### Day A3 exit check

- Can you identify a shared-work-queue overrun from evidence?
- Can you name the ULog records that make later data self-describing?
- Can you distinguish an explicit dropout record from a flat sensor value?

## Day A4 — Runtime configuration and live log transport

### Modules track — parameter declaration and live update (4 hours)

**Tangible win:** trace a parameter from its definition to a changed branch in a
running module.

#### Retrieve — 20 minutes

Write the steps you expect between `param set NAME value` and a module observing
the new value.

#### Acquire — 60 minutes

- Read the official
  [parameters and configurations guide](https://docs.px4.io/main/en/advanced/parameters_and_configurations).
- Trace `DEFINE_PARAMETERS` and `parameter_update` in
  [`WorkItemExample.hpp`](../src/examples/work_item/WorkItemExample.hpp) and
  [`WorkItemExample.cpp`](../src/examples/work_item/WorkItemExample.cpp).
- Inspect the parameter implementation under [`src/lib/parameters`](../src/lib/parameters).

#### Practice — 120 minutes

1. Choose a low-risk parameter used by a SITL module.
2. Locate its metadata definition, generated binding, cached member, update path,
   and the branch it influences.
3. Predict the exact observable change before setting it.
4. Set it at runtime, confirm `parameter_update`, and verify the module behavior.
5. Restart SITL and distinguish saved, unsaved, default, and reset behavior.

#### Explain — 40 minutes

Explain why changing the parameter store and refreshing a module’s cached parameter
members are separate steps.

### Logging track — file backend versus MAVLink backend (4 hours)

**Tangible win:** explain reliable setup records, normally unacknowledged live data,
and recovery after a dropped ULog chunk.

#### Retrieve — 20 minutes

From memory, list the per-client state required to reconstruct one live ULog
stream: sequence, acknowledgement, partial record, output, and loss counters.

#### Acquire — 60 minutes

- Read the log-streaming section of the official PX4 logging guide.
- Read [`UlogStream.msg`](../msg/UlogStream.msg),
  [`log_writer_mavlink.cpp`](../src/modules/logger/log_writer_mavlink.cpp),
  [`mavlink_ulog.cpp`](../src/modules/mavlink/mavlink_ulog.cpp), and
  [`mavlink_ulog_streaming.py`](../Tools/mavlink_ulog_streaming.py).
- Review the [swarm logging map](reference/px4-swarm-logging-map.html).

#### Practice — 120 minutes

1. Trace one buffer from the logger writer into `ulog_stream`, then into
   `LOGGING_DATA` or `LOGGING_DATA_ACKED`.
2. Predict which packets require acknowledgement and what timeout/retry behavior
   follows a missing acknowledgement.
3. Start a SITL live stream and correlate logger, uORB, and MAVLink status.
4. Simulate or reason from a captured sequence gap. Use `first_message_offset` to
   identify the next parseable ULog boundary.
5. List every variable in the Python client that must become per-vehicle state for
   a swarm collector.

#### Explain — 40 minutes

Explain why MAVLink can transport a ULog without MAVLink understanding every uORB
field inside it.

### Day A4 exit check

- Can you trace a live parameter update all the way into a module decision?
- Can you explain the two acknowledgement behaviors in ULog streaming?
- Can you identify the bandwidth evidence that shows a saturated MAVLink link?

## Day A5 — Week A capstones

### Modules track — build a traceable diagnostic module (4 hours)

**Tangible win:** make a small module behavior explainable from input through output.

#### Retrieve — 20 minutes

Write a checklist containing lifecycle, schedule, subscription, queue semantics,
parameter refresh, publication, cleanup, and performance evidence.

#### Acquire — 40 minutes

Review only the Week A source locations where your retrieval was weak. Select one
existing example or small module to extend temporarily; do not invent a new message
unless the exercise truly needs one.

#### Practice — 140 minutes

1. Add or adapt a small SITL-only diagnostic behavior that subscribes to an existing
   topic, applies a parameter-controlled condition, and reports a bounded result.
2. Before running, predict behavior for default, changed-parameter, no-update, and
   rapid-update cases.
3. Verify with `listener`, `uorb top`, module status, and a focused test.
4. Check cleanup and callback unregistration on stop.
5. Reduce the experiment to the smallest patch that demonstrates one behavior.

#### Explain — 40 minutes

Give a five-minute source tour in which every runtime observation points back to a
specific code path.

### Logging track — two-vehicle swarm logging proof (4 hours)

**Tangible win:** collect two independent logs and prove that loss or reset state
from one vehicle cannot corrupt the other.

#### Retrieve — 20 minutes

Without notes, list every key for one vehicle’s live logging state. Mark which keys
come from MAVLink identity and which come from ULog sequencing.

#### Acquire — 40 minutes

Return to [Lesson 0005: Trace PX4 Logging for a Swarm](lessons/0005-trace-px4-logging-for-a-swarm.html), then review the streaming client and relevant writer/MAVLink source. Decide the smallest
way to run two SITL instances with distinct MAVLink system IDs and endpoints.

#### Practice — 140 minutes

1. Start two vehicles and confirm distinct system IDs.
2. Collect a live ULog from each into separate output files.
3. Record per-vehicle sequence, drop, bytes, and parse-boundary state.
4. Interrupt or throttle one stream without disturbing the other.
5. Open both logs in PlotJuggler or `pyulog` and prove that metadata and vehicle
   trajectories remain separate.
6. Write the smallest regression-test design for a cross-vehicle state leak.

#### Explain — 40 minutes

Present a short incident report: one injected stream fault, its evidence, its
vehicle scope, and why the unaffected vehicle proves state isolation.

### Week A assessment

You pass Week A when you can independently:

1. Trace a scheduled module from shell entry to `Run()` and cleanup.
2. Predict default versus queued uORB delivery.
3. Trace a runtime parameter into a changed decision.
4. Explain ULog metadata, data, and dropout evidence.
5. Diagnose a topic that is visible in uORB but absent from a log.
6. Keep live logging state isolated for two vehicle identities.

Target at least **5 of 6** without trial-and-error source wandering.

---

# Week B — External protocol and vehicle intent

## Week B outcome

At the end of this week, you should be able to trace a MAVLink command or telemetry
message across the PX4 boundary, identify its system/component targeting and
acknowledgement behavior, and follow a requested flight mode or mission item through
Commander and Navigator to observable state.

## Day B1 — Messages cross boundaries; state machines own decisions

### MAVLink track — receive dispatch and identity (4 hours)

**Tangible win:** trace one incoming MAVLink message into the correct uORB topic and
reject an incorrectly targeted message for the right reason.

#### Retrieve — 20 minutes

Write what you think MAVLink system ID, component ID, source identity, and target
identity each mean. Include a case with two vehicles.

#### Acquire — 60 minutes

- Read the official [PX4 MAVLink overview](https://docs.px4.io/main/en/mavlink/).
- Read the receive dispatcher and one simple handler in
  [`mavlink_receiver.cpp`](../src/modules/mavlink/mavlink_receiver.cpp).
- Inspect target fields in [`VehicleCommand.msg`](../msg/versioned/VehicleCommand.msg).

#### Practice — 120 minutes

1. Select one incoming message that becomes a uORB publication.
2. Trace decode, target validation, unit/frame conversion, timestamp assignment,
   publication, and any response.
3. Predict behavior for correct target, wrong system, wrong component, and broadcast.
4. Send or inject each case in SITL and verify with `listener` and MAVLink output.
5. Repeat the trace with two SITL vehicles and prove which one accepted the message.

#### Explain — 40 minutes

Explain why “the UDP packet reached the process” does not prove that PX4 accepted
the message or that the intended module acted on it.

### Commander/Navigator track — responsibilities and state topics (4 hours)

**Tangible win:** distinguish requested intent, allowed mode, active navigation
state, and generated navigation behavior.

#### Retrieve — 20 minutes

Draw separate boxes for Commander and Navigator. Assign arming, mode permission,
mission execution, RTL, and setpoint generation before checking source.

#### Acquire — 60 minutes

- Read the official [developer flight-mode overview](https://docs.px4.io/main/en/concept/flight_modes).
- Read the top-level loops and subscriptions in
  [`Commander.cpp`](../src/modules/commander/Commander.cpp) and
  [`navigator_main.cpp`](../src/modules/navigator/navigator_main.cpp).
- Inspect [`VehicleStatus.msg`](../msg/versioned/VehicleStatus.msg),
  [`VehicleControlMode.msg`](../msg/VehicleControlMode.msg), and
  [`NavigatorStatus.msg`](../msg/NavigatorStatus.msg).

#### Practice — 120 minutes

1. Build a responsibility table: request intake, permission, arming, failsafe,
   active mode, mission execution, and position setpoints.
2. Predict which topics change for a disarmed mode request, an armed valid request,
   and an unavailable mode.
3. Run those cases in SITL and capture `vehicle_status`, `vehicle_control_mode`, and
   navigator status/result evidence.
4. Identify one place where Commander chooses state and one where Navigator reacts
   to that state.

#### Explain — 40 minutes

Explain why Commander and Navigator should not be collapsed into a single box
labeled “autopilot logic.”

### Day B1 exit check

- Can you distinguish message source identity from target identity?
- Can you identify the uORB boundary after an incoming MAVLink message?
- Can you state what Commander owns that Navigator does not?

## Day B2 — Outgoing streams and mode transitions

### MAVLink track — uORB-to-MAVLink streaming and rate control (4 hours)

**Tangible win:** predict when a MAVLink stream sends, at what requested rate, and
what happens when its uORB input does not update.

#### Retrieve — 20 minutes

Draw the inverse of Day B1: begin with a uORB publication and end at an external
MAVLink receiver.

#### Acquire — 60 minutes

- Read the official
  [streaming MAVLink messages guide](https://docs.px4.io/main/en/mavlink/streaming_messages).
- Inspect [`mavlink_stream.cpp`](../src/modules/mavlink/mavlink_stream.cpp),
  [`mavlink_messages.cpp`](../src/modules/mavlink/mavlink_messages.cpp), and one
  simple class under [`streams`](../src/modules/mavlink/streams).
- Locate `configure_streams_to_default()` in
  [`mavlink_main.cpp`](../src/modules/mavlink/mavlink_main.cpp).

#### Practice — 120 minutes

1. Trace one stream’s uORB subscription, `get_size()`, `send()`, and registration.
2. Predict its default rate in two MAVLink modes.
3. Request a new interval using the shell or `MAV_CMD_SET_MESSAGE_INTERVAL` and
   measure the actual rate.
4. Compare `update()`-gated and `copy()`-based stream behavior.
5. Lower the link rate temporarily and predict which evidence shows scheduling
   pressure or saturation. Restore the configuration afterward.

#### Explain — 40 minutes

Explain why requested rate, configured rate, publication rate, and delivered rate
can all differ without any one number being fabricated.

### Commander/Navigator track — user intention and mode requirements (4 hours)

**Tangible win:** explain why a requested mode may be retained as intent, rejected,
or replaced by a fallback.

#### Retrieve — 20 minutes

List the state estimates and inputs you expect Position, Mission, and Offboard modes
to require.

#### Acquire — 60 minutes

- Read the mode-requirements portion of the developer flight-mode overview.
- Read [`UserModeIntention.cpp`](../src/modules/commander/UserModeIntention.cpp),
  [`ModeManagement.cpp`](../src/modules/commander/ModeManagement.cpp), and
  [`mode_requirements.cpp`](../src/modules/commander/ModeUtil/mode_requirements.cpp).
- Inspect [`FailsafeFlags.msg`](../msg/FailsafeFlags.msg).

#### Practice — 120 minutes

1. Choose three modes and map each to its source-defined requirements.
2. Predict the result of requesting each with one required condition unavailable.
3. Use safe SITL conditions to trigger valid and invalid transitions.
4. Record requested intention, reported active mode, relevant failsafe flags, event
   messages, and command acknowledgement.
5. Locate the exact branch that explains one rejected or replaced transition.

#### Explain — 40 minutes

Explain the difference among “the user requested this mode,” “the mode is currently
allowed,” and “this is the navigation state currently controlling the vehicle.”

### Day B2 exit check

- Can you locate both stream registration and default rate configuration?
- Can you explain why a 10 Hz request may yield fewer than ten new samples?
- Can you prove why a particular mode request was refused?

## Day B3 — Command protocol and mission execution

### MAVLink track — commands, acknowledgements, and routing (4 hours)

**Tangible win:** trace one `COMMAND_LONG` or `COMMAND_INT` through
`vehicle_command` and back to `COMMAND_ACK`.

#### Retrieve — 20 minutes

Describe the difference between a telemetry message and a command protocol exchange.
Include retry and acknowledgement expectations.

#### Acquire — 60 minutes

- Read the command-protocol portion of the official MAVLink overview and the
  [MAVLink Command Protocol](https://mavlink.io/en/services/command.html).
- Read command handlers in [`mavlink_receiver.cpp`](../src/modules/mavlink/mavlink_receiver.cpp).
- Inspect [`VehicleCommandAck.msg`](../msg/versioned/VehicleCommandAck.msg) and
  [`mavlink_command_sender.cpp`](../src/modules/mavlink/mavlink_command_sender.cpp).

#### Practice — 120 minutes

1. Trace a safe command through decode, `vehicle_command`, consumer, acknowledgement,
   and outgoing `COMMAND_ACK`.
2. Predict results for accepted, temporarily rejected, denied, unsupported, and
   in-progress cases.
3. Trigger at least three safe cases in SITL and compare the result code and state.
4. Verify source and target identities in both command and acknowledgement.
5. Explain who owns retries for the chosen direction of the command exchange.

#### Explain — 40 minutes

Write a compact command-debugging checklist that prevents “no ACK” from being
treated as a single root cause.

### Commander/Navigator track — mission storage, activation, and progress (4 hours)

**Tangible win:** follow one waypoint from uploaded mission storage to a reached
mission result.

#### Retrieve — 20 minutes

Draw a mission pipeline from QGroundControl or MAVSDK to a position setpoint. Mark
where you think upload, storage, selection, execution, and completion occur.

#### Acquire — 60 minutes

- Read the official [Mission mode guide](https://docs.px4.io/main/en/flight_modes_mc/mission).
- Inspect [`mavlink_mission.cpp`](../src/modules/mavlink/mavlink_mission.cpp),
  [`Mission.msg`](../msg/Mission.msg), [`mission.cpp`](../src/modules/navigator/mission.cpp),
  [`mission_base.cpp`](../src/modules/navigator/mission_base.cpp), and
  [`MissionResult.msg`](../msg/MissionResult.msg).

#### Practice — 120 minutes

1. Upload a three-item mission in SITL.
2. Predict `count`, `current_seq`, mission ID, and result fields before activation.
3. Trace storage ownership and how Navigator learns that the mission changed.
4. Run the mission and correlate current item, reached item, generated setpoint,
   vehicle position, and acknowledgement/event output.
5. Modify one item, re-upload, and prove how the mission ID/update path changes.

#### Explain — 40 minutes

Explain why “mission uploaded,” “Mission mode selected,” “item active,” and “item
reached” are distinct states with distinct evidence.

### Day B3 exit check

- Can you trace a command round trip and identify who generated the ACK?
- Can you distinguish command result codes without guessing from vehicle motion?
- Can you trace a mission item from protocol storage to Navigator progress?

## Day B4 — Time, parameters, failsafes, and RTL

### MAVLink track — time synchronization and parameter microservice (4 hours)

**Tangible win:** distinguish PX4 boot time, external time, transmission time, and
measurement time, then trace one remote parameter change.

#### Retrieve — 20 minutes

List every “time” that could appear in a sensor message sent from another computer.
State which one a fusion or logging system actually needs.

#### Acquire — 60 minutes

- Read [`mavlink_timesync.cpp`](../src/modules/mavlink/mavlink_timesync.cpp) and
  [`TimesyncStatus.msg`](../msg/TimesyncStatus.msg).
- Read [`mavlink_parameters.cpp`](../src/modules/mavlink/mavlink_parameters.cpp).
- Review the official list of supported
  [MAVLink microservices](https://docs.px4.io/main/en/mavlink/protocols).

#### Practice — 120 minutes

1. Draw a time-sync exchange and label offset, round-trip time, local receive time,
   and remote timestamp.
2. Predict the sign of the offset for a synthetic remote clock that is 100 ms ahead.
3. Observe `timesync_status` and identify filtering or rejection behavior from source.
4. Set a safe parameter over MAVLink and trace request, validation, parameter store,
   `parameter_update`, and response.
5. Repeat one operation with two vehicles and prove correct system targeting.

#### Explain — 40 minutes

Explain why correct vehicle identity and correct time base are both mandatory for
merging swarm logs.

### Commander/Navigator track — failsafe arbitration and RTL behavior (4 hours)

**Tangible win:** predict one safe SITL failsafe transition and identify which layer
selected the action versus executed its navigation behavior.

#### Retrieve — 20 minutes

List four conditions that can prevent or interrupt a mode. Separate missing mode
requirements from independent failures such as data-link or battery loss.

#### Acquire — 60 minutes

- Read the high-level failsafe section of the official flight-mode documentation.
- Inspect the failsafe framework under
  [`src/modules/commander/failsafe`](../src/modules/commander/failsafe).
- Read the top-level state progression in [`rtl.cpp`](../src/modules/navigator/rtl.cpp)
  and inspect [`FailsafeFlags.msg`](../msg/FailsafeFlags.msg).

#### Practice — 120 minutes

1. Choose a safe SITL failure such as data-link loss or a deliberately unavailable
   position requirement.
2. Predict flags, Commander action, active navigation state, Navigator behavior,
   and recovery condition.
3. Inject the condition and capture events plus relevant uORB topics.
4. Locate the source branches that selected the action and advanced RTL behavior.
5. Restore the input and verify recovery or the documented latched behavior.

#### Explain — 40 minutes

Explain why “failsafe” is not one state and why observing RTL motion alone does not
identify the original trigger.

### Day B4 exit check

- Can you identify the clock domain of a timestamp before comparing two logs?
- Can you trace a remote parameter write through the same internal update path as a shell write?
- Can you separate failsafe detection, action selection, and navigation execution?

## Day B5 — Week B capstones

### MAVLink track — two-vehicle protocol trace (4 hours)

**Tangible win:** command and observe two vehicles without cross-targeting or
confusing transport endpoints with MAVLink identity.

#### Retrieve — 20 minutes

Write the complete identity, command, acknowledgement, stream-rate, and timestamp
checks you would perform before blaming a swarm vehicle for ignoring a message.

#### Acquire — 40 minutes

Review only weak Week B MAVLink areas. Choose one safe command and two outgoing
telemetry streams that expose the resulting state.

#### Practice — 140 minutes

1. Start two SITL vehicles with distinct system IDs and known endpoints.
2. Request different telemetry rates from each and measure delivery independently.
3. Send the command to vehicle A, vehicle B, a wrong target, and broadcast where
   the protocol permits it.
4. Correlate inbound source identity, `vehicle_command`, consumer state, ACK, and
   outgoing telemetry.
5. Inject one clock or sequence disturbance and keep its evidence scoped per vehicle.
6. Draft a regression test for one identity/routing failure.

#### Explain — 40 minutes

Present a protocol incident timeline that names the source, target, PX4 consumer,
result, and evidence at each step.

### Commander/Navigator track — mission and failsafe state-machine trace (4 hours)

**Tangible win:** explain a mission interruption and recovery from events and state,
not only from the Gazebo animation.

#### Retrieve — 20 minutes

Draw Commander and Navigator state paths from mission request through item execution,
failsafe interruption, recovery, and final result.

#### Acquire — 40 minutes

Review the mission, mode-management, and failsafe sources used this week. Choose a
safe, deterministic interruption supported by SITL.

#### Practice — 140 minutes

1. Upload and start a short mission.
2. Predict all relevant state transitions for the chosen interruption.
3. Inject it at a known mission item.
4. Capture command ACKs, events, `vehicle_status`, failsafe flags, mission result,
   setpoints, and the ULog timeline.
5. Locate the first source branch where observed behavior diverges if a prediction
   was wrong.
6. Propose the smallest automated regression test for the intended behavior.

#### Explain — 40 minutes

Give a five-minute briefing separating request, permission, active mode, mission
progress, failsafe trigger, selected action, and navigation execution.

### Week B assessment

You pass Week B when you can independently:

1. Trace an incoming message into uORB with correct targeting semantics.
2. Trace an outgoing stream and explain its effective rate.
3. Trace a command and acknowledgement round trip.
4. Distinguish user mode intention from active navigation state.
5. Trace a mission item through upload, storage, execution, and result.
6. Separate failsafe detection, action selection, and Navigator execution.

Target at least **5 of 6** without using the Gazebo picture as primary evidence.

---

# Half-week C — SITL, Gazebo, and test-backed contributions

## Half-week outcome

At the end of these five four-hour blocks, you should be able to locate a bug on the
PX4-versus-simulator boundary, reproduce it deterministically, choose the smallest
appropriate test level, and produce a contribution-ready failure-to-regression-test
evidence chain.

## Day C1 morning — SITL process and startup boundaries (4 hours)

**Tangible win:** explain what is simulated by PX4, what is simulated by Gazebo,
and how a selected model is started.

### Retrieve — 20 minutes

Draw PX4, Gazebo, the model, sensors, actuators, MAVLink, and the ground station.
Connect them before reading the documentation.

### Acquire — 60 minutes

- Read the official [PX4 simulation overview](https://docs.px4.io/main/en/simulation/).
- Inspect the SITL startup scripts under
  [`ROMFS/px4fmu_common/init.d-posix`](../ROMFS/px4fmu_common/init.d-posix).
- Inspect simulation module selection in [`src/modules/simulation`](../src/modules/simulation).

### Practice — 120 minutes

1. Start a simple Gazebo SITL vehicle and record the PX4 and Gazebo processes.
2. Trace model selection from the `make` target through environment/startup state.
3. Predict which functions survive if the GUI closes versus if the Gazebo server
   stops versus if PX4 exits. Test only safe local cases.
4. Identify the ports and transports used by Gazebo bridge traffic and external
   MAVLink clients. Do not label every UDP port “the simulator connection.”
5. Save a minimal clean-start reproduction command and environment checklist.

### Explain — 40 minutes

Explain why “SITL is running” does not necessarily mean that physics, sensors, and
external MAVLink clients are all connected.

## Day C1 afternoon — Gazebo bridge data flow (4 hours)

**Tangible win:** trace one simulated sensor into PX4 and one PX4 command back to a
simulated device.

### Retrieve — 20 minutes

Draw the gimbal issue path from earth-frame command to simulated joint. Mark where
you currently believe PX4 ends and Gazebo begins.

### Acquire — 60 minutes

- Inspect [`GZBridge.cpp`](../src/modules/simulation/gz_bridge/GZBridge.cpp) and the
  focused bridge classes under [`gz_bridge`](../src/modules/simulation/gz_bridge).
- Revisit [`GZGimbal.cpp`](../src/modules/simulation/gz_bridge/GZGimbal.cpp).
- Locate one sensor conversion and one actuator/device conversion.

### Practice — 120 minutes

1. For each selected path, write input units/frame, conversion, transport message,
   PX4 topic, and output units/frame.
2. Predict one value numerically before running, then verify it with Gazebo state
   and a PX4 `listener`.
3. Change one safe simulator input and identify which side first observes it.
4. Reproduce the earth-frame gimbal problem and distinguish command intent, PX4
   bridge conversion, joint command, and feedback.
5. Identify the smallest function boundary suitable for a regression test.

### Explain — 40 minutes

Explain how a visually plausible simulation can still violate a frame, unit, sign,
or timestamp contract.

### Day C1 exit check

- Can you name the transport between current PX4 Gazebo and `gz_bridge`?
- Can you distinguish a PX4 uORB path from an external MAVLink connection?
- Can you point to the exact boundary that owns a selected conversion?

## Day C2 morning — Unit and component tests (4 hours)

**Tangible win:** choose a small test that fails for the intended reason before
starting an entire simulator.

### Retrieve — 20 minutes

Classify five example bugs as pure function, small class/state machine, module
integration, or whole-vehicle behavior.

### Acquire — 60 minutes

- Read the official [testing overview](https://docs.px4.io/main/en/test_and_ci/).
- Inspect tests beside the logger, Commander, Navigator, matrix, and simulation code.
- Read the relevant `CMakeLists.txt` entries that register two selected tests.

### Practice — 120 minutes

1. Run one existing unit test target and force one temporary assertion failure.
2. Confirm that the failure message identifies the intended invariant, then restore it.
3. Select one prior curriculum behavior—uORB queue, ULog record, mode transition,
   or gimbal conversion—and write a focused test matrix.
4. Implement the smallest test case if the fixture already supports it; otherwise
   produce a precise test design without adding broad infrastructure.
5. Run formatting and the smallest relevant test command.

### Explain — 40 minutes

Explain why a small deterministic test is preferable when it proves the same
contract as a slow whole-vehicle scenario.

## Day C2 afternoon — SITL and MAVSDK integration tests (4 hours)

**Tangible win:** run one end-to-end test, understand its orchestration, and know
when an issue genuinely requires this level.

### Retrieve — 20 minutes

Write what a unit test cannot prove about arming, mission execution, transport, or
simulator behavior.

### Acquire — 60 minutes

- Read the official [integration-testing overview](https://docs.px4.io/main/en/test_and_ci/integration_testing)
  and [MAVSDK integration-testing guide](https://docs.px4.io/main/en/test_and_ci/integration_testing_mavsdk).
- Inspect [`mavsdk_test_runner.py`](../test/mavsdk_tests/mavsdk_test_runner.py),
  [`autopilot_tester.cpp`](../test/mavsdk_tests/autopilot_tester.cpp), and one focused
  test such as [`test_multicopter_mission.cpp`](../test/mavsdk_tests/test_multicopter_mission.cpp).

### Practice — 120 minutes

1. Map which process starts PX4, Gazebo, MAVSDK, and the test case.
2. Run one narrow supported case, record its logs, and identify its pass conditions.
3. Predict a safe temporary input change that should make it fail for one reason.
4. Verify the failure, restore the input, and prove the test passes again.
5. Compare wall time, determinism, diagnostic quality, and coverage with the unit
   test from the morning.

### Explain — 40 minutes

Write a decision rule for choosing unit, component, SITL integration, or manual
reproduction evidence in a PX4 pull request.

### Day C2 exit check

- Can you run the smallest relevant test instead of the whole suite?
- Can you prove a test failed because of the intended invariant?
- Can you explain what an end-to-end SITL test proves that a unit test does not?

## Day C3 — Contribution capstone (4 hours)

**Tangible win:** turn one reproduced PX4 issue into a small, reviewable,
regression-tested contribution plan or patch.

### Retrieve — 20 minutes

From memory, write the complete chain:

```text
report → reproduction → expected contract → source owner → failing test
       → minimal change → passing test → adjacent checks → evidence
```

### Acquire — 40 minutes

Choose one bounded issue from the earlier curriculum work. Prefer the gimbal-frame
case or a deliberately introduced swarm-logging state-isolation bug because you
already understand their expected behavior. Review only the owning source and its
nearest tests.

### Practice — 140 minutes

1. Write exact reproduction steps from a clean checkout and clean SITL state.
2. State the expected behavior from message/source contracts before inspecting a fix.
3. Reduce the failure to the smallest deterministic test level available.
4. Make or describe the minimum behavior change; avoid unrelated cleanup.
5. Run the failing test before and passing test after the change.
6. Run adjacent tests and formatting appropriate to the files touched.
7. Prepare a contribution summary containing problem, root cause, change, test, and
   safety/compatibility considerations.

### Explain — 40 minutes

Give a five-minute PR walkthrough. Every claim must point to source, test output,
`listener`, event, or log evidence. Do not use “it looks right in Gazebo” as the
only validation.

## Final assessment

You are ready for bounded PX4 issues when you can complete at least **8 of 10**
without guessing:

1. Trace a module from shell entry through scheduling and cleanup.
2. Predict uORB queue and multi-instance behavior.
3. Trace a runtime parameter update into a module branch.
4. Explain topic selection, ULog structure, and backend delivery separately.
5. Keep logging state isolated for multiple MAVLink system IDs.
6. Trace incoming and outgoing MAVLink data with targeting and rate semantics.
7. Trace a command acknowledgement to the module that produced it.
8. Separate mode intent, permission, failsafe selection, and Navigator execution.
9. Draw the PX4/Gazebo boundary for a selected sensor or device.
10. Preserve a reproduction as the smallest appropriate automated test.

Missing an item does not require rereading a week. Schedule one additional four-hour
block that repeats the failed skill on a different PX4 issue.

## Daily learning record

End every eight-hour day—or the final four-hour day—with:

```text
One source path I can now navigate:
One runtime signal I can now interpret:
One prediction that was wrong:
What evidence corrected me:
One bounded issue I could now investigate:
```

At the beginning of the next day, reproduce the prior day’s main diagram from
memory before opening the curriculum or source.
