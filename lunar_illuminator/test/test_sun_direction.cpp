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

#include <string>

#include "gtest/gtest.h"
#include "lunar_illuminator/sun_direction.hpp"

using lunar_illuminator::lightDirectionEnu;
using lunar_illuminator::Vector3;
using lunar_illuminator::worldNameForSite;

namespace
{
constexpr double kTol = 1e-9;

void expectVec(const Vector3 & actual, double x, double y, double z)
{
  EXPECT_NEAR(actual.x, x, kTol);
  EXPECT_NEAR(actual.y, y, kTol);
  EXPECT_NEAR(actual.z, z, kTol);
}
}  // namespace

// The Sun direction now arrives as an ENU unit vector on SkyObject; the
// illuminator only negates it into the light's travel direction.

TEST(LightDirection, IsTheNegatedSunDirection)
{
  // gz.msgs.Light.direction is the travel direction of the light, i.e. from
  // the sun into the scene.
  const Vector3 to_sun{0.1, -0.2, 0.9};
  expectVec(lightDirectionEnu(to_sun), -0.1, 0.2, -0.9);
}

TEST(LightDirection, SunOverheadShinesStraightDown)
{
  expectVec(lightDirectionEnu(Vector3{0.0, 0.0, 1.0}), 0.0, 0.0, -1.0);
}

TEST(LightDirection, PreservesMagnitude)
{
  // Pure negation, so whatever length the caller passes comes straight back.
  const Vector3 light = lightDirectionEnu(Vector3{3.0, -4.0, 12.0});
  expectVec(light, -3.0, 4.0, -12.0);
}

TEST(WorldName, AppendsWorldSuffixToSiteId)
{
  EXPECT_EQ(worldNameForSite("shackleton_rim"), "shackleton_rim_world");
  EXPECT_EQ(worldNameForSite("empty_lunar"), "empty_lunar_world");
}

TEST(WorldName, EmptySiteIdYieldsEmptyString)
{
  // Guards against advertising "/world/_world/light_config" on a blank id.
  EXPECT_EQ(worldNameForSite(""), "");
}
