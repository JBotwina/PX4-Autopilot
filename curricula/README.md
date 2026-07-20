# PX4 Learning Program

This directory contains a 3.5-week, 140-hour practical PX4 program. Complete the
curricula in numerical order.

| Sequence | Curriculum | Time | Main outcome |
| --- | --- | ---: | --- |
| 1 | [Quaternions and PX4 odometry](0001-quaternions-and-px4-odometry-week.md) | 40 h | Interpret and debug orientation, frames, SLAM/VIO odometry, and estimator integration. |
| 2 | [PX4 systems and debugging](0002-px4-systems-debugging-2.5-weeks.md) | 100 h | Trace internal and external data flow, logging, vehicle intent, simulation, and tests. |
| **Total** |  | **140 h** | Bounded, evidence-driven PX4 issue investigation and contribution ability. |

Supporting material:

- [Lesson table of contents](lessons/index.html) links every interactive lesson in study order.
- [`reference/`](reference/) contains compact cheat sheets and system maps.
- [`learning-records/`](learning-records/) records durable changes in understanding.
- [`RESOURCES.md`](RESOURCES.md) is the curated primary-source list.
- [`NOTES.md`](NOTES.md) records teaching preferences.

## Lesson order

Week 1 uses these lessons in study order:

1. [Frames Before Quaternions](lessons/0001-frames-before-quaternions.html) — Day 1 orientation track
2. [The PX4 Odometry Contract](lessons/0002-px4-odometry-contract.html) — Day 1 SLAM/odometry track
3. [Quaternions as Rotations](lessons/0003-quaternions-as-rotations.html) — Day 2 orientation track
4. [Gimbal Lock and Quaternions](lessons/0004-gimbal-lock-and-quaternions.html) — Day 3 orientation track

The later systems curriculum uses:

5. [Trace PX4 Logging for a Swarm](lessons/0005-trace-px4-logging-for-a-swarm.html) — Week A roadmap and Day A5 capstone

The long-term application is PX4 swarm logging and multi-vehicle observability.
Every curriculum block therefore emphasizes vehicle identity, timestamps, frame
semantics, reproducible evidence, or state isolation where relevant.
