/****************************************************************************
 *
 *   Copyright (c) 2026 PX4 Development Team. All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in
 *    the documentation and/or other materials provided with the
 *    distribution.
 * 3. Neither the name PX4 nor the names of its contributors may be
 *    used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 * COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
 * OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
 * AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 * ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 *
 ****************************************************************************/

#include "setpoint_watchdog.hpp"

#include <uORB/topics/actuator_motors.h>
#include <uORB/topics/actuator_servos.h>
#include <uORB/topics/fixed_wing_lateral_setpoint.h>
#include <uORB/topics/fixed_wing_longitudinal_setpoint.h>
#include <uORB/topics/goto_setpoint.h>
#include <uORB/topics/position_setpoint_triplet.h>
#include <uORB/topics/rover_attitude_setpoint.h>
#include <uORB/topics/rover_position_setpoint.h>
#include <uORB/topics/rover_rate_setpoint.h>
#include <uORB/topics/rover_speed_setpoint.h>
#include <uORB/topics/rover_steering_setpoint.h>
#include <uORB/topics/rover_throttle_setpoint.h>
#include <uORB/topics/trajectory_setpoint.h>
#include <uORB/topics/trajectory_setpoint6dof.h>
#include <uORB/topics/vehicle_attitude_setpoint.h>
#include <uORB/topics/vehicle_rates_setpoint.h>
#include <uORB/topics/vehicle_thrust_setpoint.h>
#include <uORB/topics/vehicle_torque_setpoint.h>

namespace
{

template<typename T>
hrt_abstime updateTimestamp(uORB::Subscription &subscription, hrt_abstime &timestamp)
{
	T setpoint{};

	if (subscription.update(&setpoint)) {
		timestamp = setpoint.timestamp;
	}

	return timestamp;
}

hrt_abstime latestOf(hrt_abstime first, hrt_abstime second)
{
	return first > second ? first : second;
}

hrt_abstime oldestOf(hrt_abstime first, hrt_abstime second)
{
	return first < second ? first : second;
}

} // namespace

namespace mode_util
{

bool SetpointWatchdog::timedOut(SetpointType setpoint_type, uint16_t timeout_ms, hrt_abstime now)
{
	return isTimedOut(now, _started_at, freshnessTimestamp(setpoint_type), timeout_ms);
}

void SetpointWatchdog::configureSubscriptions(SetpointType setpoint_type, ORB_ID primary_topic,
		ORB_ID secondary_topic)
{
	if (_configured_type != setpoint_type) {
		_primary_sub = uORB::Subscription{primary_topic};
		_secondary_sub = uORB::Subscription{secondary_topic};
		_primary_timestamp = 0;
		_secondary_timestamp = 0;
		_configured_type = setpoint_type;
	}
}

hrt_abstime SetpointWatchdog::freshnessTimestamp(SetpointType setpoint_type)
{
	switch (setpoint_type) {
	case SetpointType::Invalid:
		return 0;

	case SetpointType::DirectActuators:
		// Motors and servos are independently optional, so either stream refreshes this setpoint type.
		configureSubscriptions(setpoint_type, ORB_ID::actuator_motors, ORB_ID::actuator_servos);
		return latestOf(updateTimestamp<actuator_motors_s>(_primary_sub, _primary_timestamp),
				updateTimestamp<actuator_servos_s>(_secondary_sub, _secondary_timestamp));

	case SetpointType::Goto:
		configureSubscriptions(setpoint_type, ORB_ID::goto_setpoint);
		return updateTimestamp<goto_setpoint_s>(_primary_sub, _primary_timestamp);

	case SetpointType::FixedwingLateralLongitudinal:
		// For setpoint types with required paired topics, the slower stream determines freshness.
		configureSubscriptions(setpoint_type, ORB_ID::fixed_wing_lateral_setpoint,
				       ORB_ID::fixed_wing_longitudinal_setpoint);
		return oldestOf(updateTimestamp<fixed_wing_lateral_setpoint_s>(_primary_sub, _primary_timestamp),
				updateTimestamp<fixed_wing_longitudinal_setpoint_s>(_secondary_sub, _secondary_timestamp));

	case SetpointType::Trajectory:
		configureSubscriptions(setpoint_type, ORB_ID::trajectory_setpoint);
		return updateTimestamp<trajectory_setpoint_s>(_primary_sub, _primary_timestamp);

	case SetpointType::Rates:
		configureSubscriptions(setpoint_type, ORB_ID::vehicle_rates_setpoint);
		return updateTimestamp<vehicle_rates_setpoint_s>(_primary_sub, _primary_timestamp);

	case SetpointType::Attitude:
		configureSubscriptions(setpoint_type, ORB_ID::vehicle_attitude_setpoint);
		return updateTimestamp<vehicle_attitude_setpoint_s>(_primary_sub, _primary_timestamp);

	case SetpointType::RoverPosition:
		configureSubscriptions(setpoint_type, ORB_ID::rover_position_setpoint);
		return updateTimestamp<rover_position_setpoint_s>(_primary_sub, _primary_timestamp);

	case SetpointType::RoverSpeedAttitude:
		configureSubscriptions(setpoint_type, ORB_ID::rover_speed_setpoint, ORB_ID::rover_attitude_setpoint);
		return oldestOf(updateTimestamp<rover_speed_setpoint_s>(_primary_sub, _primary_timestamp),
				updateTimestamp<rover_attitude_setpoint_s>(_secondary_sub, _secondary_timestamp));

	case SetpointType::RoverSpeedRate:
		configureSubscriptions(setpoint_type, ORB_ID::rover_speed_setpoint, ORB_ID::rover_rate_setpoint);
		return oldestOf(updateTimestamp<rover_speed_setpoint_s>(_primary_sub, _primary_timestamp),
				updateTimestamp<rover_rate_setpoint_s>(_secondary_sub, _secondary_timestamp));

	case SetpointType::RoverSpeedSteering:
		configureSubscriptions(setpoint_type, ORB_ID::rover_speed_setpoint, ORB_ID::rover_steering_setpoint);
		return oldestOf(updateTimestamp<rover_speed_setpoint_s>(_primary_sub, _primary_timestamp),
				updateTimestamp<rover_steering_setpoint_s>(_secondary_sub, _secondary_timestamp));

	case SetpointType::RoverThrottleAttitude:
		configureSubscriptions(setpoint_type, ORB_ID::rover_throttle_setpoint, ORB_ID::rover_attitude_setpoint);
		return oldestOf(updateTimestamp<rover_throttle_setpoint_s>(_primary_sub, _primary_timestamp),
				updateTimestamp<rover_attitude_setpoint_s>(_secondary_sub, _secondary_timestamp));

	case SetpointType::RoverThrottleRate:
		configureSubscriptions(setpoint_type, ORB_ID::rover_throttle_setpoint, ORB_ID::rover_rate_setpoint);
		return oldestOf(updateTimestamp<rover_throttle_setpoint_s>(_primary_sub, _primary_timestamp),
				updateTimestamp<rover_rate_setpoint_s>(_secondary_sub, _secondary_timestamp));

	case SetpointType::RoverThrottleSteering:
		configureSubscriptions(setpoint_type, ORB_ID::rover_throttle_setpoint, ORB_ID::rover_steering_setpoint);
		return oldestOf(updateTimestamp<rover_throttle_setpoint_s>(_primary_sub, _primary_timestamp),
				updateTimestamp<rover_steering_setpoint_s>(_secondary_sub, _secondary_timestamp));

	case SetpointType::Trajectory_6dof:
		configureSubscriptions(setpoint_type, ORB_ID::trajectory_setpoint6dof);
		return updateTimestamp<trajectory_setpoint6dof_s>(_primary_sub, _primary_timestamp);

	case SetpointType::ThrustAndTorque:
		configureSubscriptions(setpoint_type, ORB_ID::vehicle_thrust_setpoint, ORB_ID::vehicle_torque_setpoint);
		return oldestOf(updateTimestamp<vehicle_thrust_setpoint_s>(_primary_sub, _primary_timestamp),
				updateTimestamp<vehicle_torque_setpoint_s>(_secondary_sub, _secondary_timestamp));

	case SetpointType::PositionTriplet:
		configureSubscriptions(setpoint_type, ORB_ID::position_setpoint_triplet);
		return updateTimestamp<position_setpoint_triplet_s>(_primary_sub, _primary_timestamp);
	}

	return 0;
}

} // namespace mode_util
