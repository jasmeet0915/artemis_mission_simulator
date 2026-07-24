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

#include "lunar_illuminator/sun_direction.hpp"

#include <string>

namespace lunar_illuminator
{

Vector3 lightDirectionEnu(const Vector3 & sun_direction_enu)
{
  return Vector3{
    -sun_direction_enu.x, -sun_direction_enu.y, -sun_direction_enu.z};
}

std::string worldNameForSite(const std::string & site_id)
{
  if (site_id.empty()) {
    return {};
  }
  return site_id + "_world";
}

}  // namespace lunar_illuminator
