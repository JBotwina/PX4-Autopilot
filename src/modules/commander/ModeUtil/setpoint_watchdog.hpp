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

#pragma once

#include "setpoint_types.hpp"

#include <drivers/drv_hrt.h>
#include <uORB/Subscription.hpp>

namespace mode_util
{

class SetpointWatchdog
{
public:
	void reset(hrt_abstime now) { _started_at = now; }
	void disable() { _started_at = 0; }

	bool timedOut(SetpointType setpoint_type, uint16_t timeout_ms, hrt_abstime now);

	static bool isTimedOut(hrt_abstime now, hrt_abstime started_at, hrt_abstime latest_setpoint,
			       uint16_t timeout_ms)
	{
		if (started_at == 0 || timeout_ms == 0) {
			return false;
		}

		// Ignore cached setpoints from before watchdog activation and invalid future timestamps.
		const hrt_abstime valid_latest_setpoint = latest_setpoint <= now ? latest_setpoint : 0;
		const hrt_abstime reference_time = valid_latest_setpoint > started_at ? valid_latest_setpoint : started_at;
		const hrt_abstime timeout_us = static_cast<hrt_abstime>(timeout_ms) * 1000;

		return now > reference_time && now - reference_time > timeout_us;
	}

private:
	void configureSubscriptions(SetpointType setpoint_type, ORB_ID primary_topic,
				    ORB_ID secondary_topic = ORB_ID::INVALID);
	hrt_abstime freshnessTimestamp(SetpointType setpoint_type);

	uORB::Subscription _primary_sub;
	uORB::Subscription _secondary_sub;
	SetpointType _configured_type{SetpointType::Invalid};
	hrt_abstime _primary_timestamp{0};
	hrt_abstime _secondary_timestamp{0};

	hrt_abstime _started_at{0};
};

} // namespace mode_util
