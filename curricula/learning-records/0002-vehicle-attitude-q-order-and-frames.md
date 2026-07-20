# VehicleAttitude.q order and frames

```text
source location:
  msg/versioned/VehicleAttitude.msg (lines 2, 10)

observed result:
  order: Hamilton convention, q(w, x, y, z) — scalar first
  source frame: FRD body frame
  destination frame: NED earth frame

conclusion:
  VehicleAttitude.q rotates from FRD body into NED earth; array layout is [w, x, y, z].
```
