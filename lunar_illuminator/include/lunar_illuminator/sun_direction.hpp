// Copyright 2026 Jasmeet Singh
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#ifndef LUNAR_ILLUMINATOR__SUN_DIRECTION_HPP_
#define LUNAR_ILLUMINATOR__SUN_DIRECTION_HPP_

#include <string>

namespace lunar_illuminator
{

/// A vector in the observer's local ENU frame: x = East, y = North, z = Up.
struct Vector3
{
  double x{0.0};
  double y{0.0};
  double z{0.0};
};

/// Unit vector a directional light travels along, in ENU.
/**
 * This is the negated Sun direction: light leaves the Sun and travels into the
 * scene, which is the convention gz.msgs.Light's `direction` field expects. The
 * Sun direction arrives ready-made on artemis_mission_interfaces/SkyObject's
 * `direction_enu`, so no angle-to-vector reconstruction happens here.
 */
Vector3 lightDirectionEnu(const Vector3 & sun_direction_enu);

/// Simulator world name for a site id, e.g. "shackleton_rim" -> "shackleton_rim_world".
/**
 * A project naming convention rather than a simulator one, so it belongs in the
 * portable layer. Returns an empty string for an empty site id so callers never
 * build a topic against a half-formed world name.
 */
std::string worldNameForSite(const std::string & site_id);

}  // namespace lunar_illuminator

#endif  // LUNAR_ILLUMINATOR__SUN_DIRECTION_HPP_
