/****************************************************************************
 *
 *   Copyright (C) 2023 PX4 Development Team. All rights reserved.
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

#include <gtest/gtest.h>
#include "ModeManagement.hpp"

#include <px4_platform_common/time.h>
#include <uORB/Publication.hpp>
#include <uORB/Subscription.hpp>
#include <uORB/topics/register_ext_component_reply.h>
#include <uORB/topics/register_ext_component_request.h>
#include <uORB/topics/setpoint_config.h>
#include <uORB/topics/vehicle_rates_setpoint.h>

static bool modeValid(uint8_t mode)
{
	return mode >= Modes::FIRST_EXTERNAL_NAV_STATE && mode <= Modes::LAST_EXTERNAL_NAV_STATE;
}

static int32_t readHash(int idx)
{
	char buffer[20];
	snprintf(buffer, sizeof(buffer), "COM_MODE%u_HASH", idx);
	param_t param = param_find(buffer);
	int32_t value{};
	param_get(param, &value);
	return value;
}

TEST(ModeManagementTest, Hashes)
{
	param_control_autosave(false);

	// Reset parameters
	for (int i = 0; i < Modes::MAX_NUM; ++i) {
		char buffer[20];
		snprintf(buffer, sizeof(buffer), "COM_MODE%u_HASH", i);
		param_t param = param_find(buffer);
		param_reset(param);
	}

	// Add full set of modes, which stores the hashes
	Modes modes;
	Modes::Mode mode;

	for (int i = 0; i < Modes::MAX_NUM; ++i) {
		snprintf(mode.name, sizeof(mode.name), "mode %i", i);
		EXPECT_EQ(modes.addExternalMode(mode), Modes::FIRST_EXTERNAL_NAV_STATE + i);
		EXPECT_EQ(readHash(i), events::util::hash_32_fnv1a_const(mode.name));
	}

	EXPECT_FALSE(modes.hasFreeExternalModes());

	// Remove all modes, except last
	for (int i = 0; i < Modes::MAX_NUM - 1; ++i) {
		snprintf(mode.name, sizeof(mode.name), "mode %i", i);
		EXPECT_TRUE(modes.removeExternalMode(Modes::FIRST_EXTERNAL_NAV_STATE + i, mode.name));
	}

	// Add some mode, ensure it gets the same index
	const int mode_to_add_idx = 3;
	snprintf(mode.name, sizeof(mode.name), "mode %i", mode_to_add_idx);
	EXPECT_EQ(modes.addExternalMode(mode), Modes::FIRST_EXTERNAL_NAV_STATE + mode_to_add_idx);

	// Try to add another one with the same name: should succeed, with the hash of the added index reset
	uint8_t added_mode_nav_state = modes.addExternalMode(mode);
	EXPECT_EQ(readHash(added_mode_nav_state - Modes::FIRST_EXTERNAL_NAV_STATE), 0);

	// 3 Modes are used now. Add N-3 new ones which must overwrite previous hashes
	for (int i = 0; i < Modes::MAX_NUM - 3; ++i) {
		snprintf(mode.name, sizeof(mode.name), "new mode %i", i);
		added_mode_nav_state = modes.addExternalMode(mode);
		EXPECT_TRUE(modeValid(added_mode_nav_state));
		EXPECT_EQ(readHash(added_mode_nav_state - Modes::FIRST_EXTERNAL_NAV_STATE),
			  events::util::hash_32_fnv1a_const(mode.name));
	}

	EXPECT_FALSE(modes.hasFreeExternalModes());
}

TEST(ModeManagementTest, SetpointTimeout)
{
	ExternalChecks external_checks;
	ModeManagement mode_management(external_checks);
	uORB::Publication<register_ext_component_request_s> registration_pub{ORB_ID(register_ext_component_request)};
	uORB::Subscription registration_reply_sub{ORB_ID(register_ext_component_reply)};
	uORB::Publication<setpoint_config_s> setpoint_config_pub{ORB_ID(setpoint_config)};
	uORB::Publication<vehicle_rates_setpoint_s> rates_setpoint_pub{ORB_ID(vehicle_rates_setpoint)};

	register_ext_component_request_s registration{};
	registration.timestamp = hrt_absolute_time();
	registration.request_id = 42;
	registration.register_arming_check = true;
	registration.register_mode = true;
	strncpy(registration.name, "Setpoint timeout test", sizeof(registration.name) - 1);
	ASSERT_TRUE(registration_pub.publish(registration));

	ModeManagement::UpdateRequest update_request{};
	mode_management.update(vehicle_status_s::VEHICLE_TYPE_ROTARY_WING, false,
			       vehicle_status_s::NAVIGATION_STATE_AUTO_LOITER,
			       vehicle_status_s::NAVIGATION_STATE_AUTO_LOITER, update_request);

	register_ext_component_reply_s registration_reply{};
	ASSERT_TRUE(registration_reply_sub.update(&registration_reply));
	ASSERT_TRUE(registration_reply.success);
	ASSERT_EQ(registration_reply.request_id, registration.request_id);
	ASSERT_TRUE(modeValid(registration_reply.mode_id));

	setpoint_config_s setpoint_config{};
	setpoint_config.timestamp = hrt_absolute_time();
	setpoint_config.source_id = registration_reply.mode_id;
	setpoint_config.type = setpoint_config_s::TYPE_RATES;
	setpoint_config.should_apply = true;
	setpoint_config.timeout_ms = 20;
	ASSERT_TRUE(setpoint_config_pub.publish(setpoint_config));

	update_request = {};
	mode_management.update(vehicle_status_s::VEHICLE_TYPE_ROTARY_WING, true, registration_reply.mode_id,
			       registration_reply.mode_id, update_request);
	EXPECT_TRUE(update_request.control_setpoint_update);
	EXPECT_FALSE(external_checks.isUnresponsive(registration_reply.arming_check_id));

	vehicle_rates_setpoint_s rates_setpoint{};
	rates_setpoint.timestamp = hrt_absolute_time();
	ASSERT_TRUE(rates_setpoint_pub.publish(rates_setpoint));
	update_request = {};
	mode_management.update(vehicle_status_s::VEHICLE_TYPE_ROTARY_WING, true, registration_reply.mode_id,
			       registration_reply.mode_id, update_request);
	EXPECT_FALSE(external_checks.isUnresponsive(registration_reply.arming_check_id));

	px4_usleep(25_ms);
	update_request = {};
	mode_management.update(vehicle_status_s::VEHICLE_TYPE_ROTARY_WING, true, registration_reply.mode_id,
			       registration_reply.mode_id, update_request);
	EXPECT_TRUE(update_request.mode_status_changed);
	EXPECT_TRUE(external_checks.isUnresponsive(registration_reply.arming_check_id));

	// The failure must remain latched when the failsafe switches away from the external mode.
	update_request = {};
	mode_management.update(vehicle_status_s::VEHICLE_TYPE_ROTARY_WING, true, registration_reply.mode_id,
			       vehicle_status_s::NAVIGATION_STATE_AUTO_LOITER, update_request);
	EXPECT_TRUE(external_checks.isUnresponsive(registration_reply.arming_check_id));

	// Disarming clears the failure and permits a fresh activation attempt.
	update_request = {};
	mode_management.update(vehicle_status_s::VEHICLE_TYPE_ROTARY_WING, false, registration_reply.mode_id,
			       vehicle_status_s::NAVIGATION_STATE_AUTO_LOITER, update_request);
	EXPECT_TRUE(update_request.mode_status_changed);
	EXPECT_FALSE(external_checks.isUnresponsive(registration_reply.arming_check_id));
}
