# SLAM as external evidence for the vehicle state estimate

The learner recognizes that the drone's location used for control is an estimate rather than a directly known value, and that SLAM supplies external evidence that can correct drift in that estimate. Future lessons can build from this two-estimator model: the SLAM/VIO system estimates camera or body motion, while PX4 EKF2 fuses that measurement with onboard sensors instead of simply replacing its state.
