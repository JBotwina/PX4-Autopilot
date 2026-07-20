# Mission: PX4 Orientation and Frame Math

## Why
Understand PX4 attitude and gimbal-frame behavior well enough to reproduce, explain, test, and review orientation bugs without guessing from visual behavior alone.

## Success looks like
- Distinguish NED earth-frame headings from FRD vehicle-frame angles.
- Convert an earth-frame gimbal target into a vehicle-relative joint command.
- Predict correct and faulty yaw feedback from PX4 listener output.
- Explain why PX4 uses `q_vehicle.inversed() * q_target` and recognize when that conversion applies.

## Constraints
- Prior calculus and differential-equations experience is rusty; rotation and quaternion math is new.
- Start with geometry and interactive examples before compact notation.
- Tie every abstraction back to the `gz_x500_gimbal` reproduction and PX4 source.

## Out of scope
- Full rigid-body dynamics, controller design, or abstract group theory.
- Deriving general three-dimensional quaternion interpolation in the first lessons.
