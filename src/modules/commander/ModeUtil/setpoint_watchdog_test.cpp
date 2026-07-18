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

#include <gtest/gtest.h>

#include "setpoint_watchdog.hpp"

using mode_util::SetpointWatchdog;
using namespace time_literals;

TEST(SetpointWatchdog, TimeoutStartsAtActivation)
{
	constexpr hrt_abstime activation_time = 1_s;
	constexpr uint16_t timeout_ms = 50;

	EXPECT_FALSE(SetpointWatchdog::isTimedOut(activation_time + 50_ms, activation_time, 0, timeout_ms));
	EXPECT_TRUE(SetpointWatchdog::isTimedOut(activation_time + 50_ms + 1, activation_time, 0, timeout_ms));

	// A cached setpoint from before activation must not extend the grace period.
	EXPECT_TRUE(SetpointWatchdog::isTimedOut(activation_time + 50_ms + 1, activation_time,
			activation_time - 10_ms, timeout_ms));

	// A timestamp ahead of the local clock is invalid and must not postpone the timeout.
	EXPECT_TRUE(SetpointWatchdog::isTimedOut(activation_time + 50_ms + 1, activation_time,
			activation_time + 1_s, timeout_ms));
}

TEST(SetpointWatchdog, NewSetpointRefreshesDeadline)
{
	constexpr hrt_abstime activation_time = 1_s;
	constexpr hrt_abstime setpoint_time = activation_time + 40_ms;
	constexpr uint16_t timeout_ms = 50;

	EXPECT_FALSE(SetpointWatchdog::isTimedOut(setpoint_time + 50_ms, activation_time, setpoint_time, timeout_ms));
	EXPECT_TRUE(SetpointWatchdog::isTimedOut(setpoint_time + 50_ms + 1, activation_time, setpoint_time, timeout_ms));
}

TEST(SetpointWatchdog, DisabledTimeoutNeverTriggers)
{
	EXPECT_FALSE(SetpointWatchdog::isTimedOut(10_s, 1_s, 0, 0));
	EXPECT_FALSE(SetpointWatchdog::isTimedOut(10_s, 0, 0, 10));
}
