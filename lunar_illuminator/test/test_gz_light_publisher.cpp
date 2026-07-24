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
#include "lunar_illuminator/gazebo/gz_light_publisher.hpp"

using lunar_illuminator::gazebo::GzLightPublisher;
using lunar_illuminator::gazebo::LightAppearance;

namespace
{
LightAppearance sunAppearance()
{
  // Mirrors <light name="sun"> in the world SDFs.
  LightAppearance appearance;
  appearance.name = "sun";
  appearance.diffuse = {0.8f, 0.8f, 0.8f, 1.0f};
  appearance.specular = {0.2f, 0.2f, 0.2f, 1.0f};
  appearance.attenuation_range = 1000.0f;
  appearance.attenuation_constant = 0.9f;
  appearance.attenuation_linear = 0.01f;
  appearance.attenuation_quadratic = 0.001f;
  appearance.cast_shadows = true;
  return appearance;
}
}  // namespace

TEST(BuildLightMsg, CarriesTheRequestedDirection)
{
  const auto msg = GzLightPublisher::buildLightMsg(
    sunAppearance(), lunar_illuminator::Vector3{-0.1, -0.2, -0.9});
  EXPECT_DOUBLE_EQ(msg.direction().x(), -0.1);
  EXPECT_DOUBLE_EQ(msg.direction().y(), -0.2);
  EXPECT_DOUBLE_EQ(msg.direction().z(), -0.9);
}

TEST(BuildLightMsg, NamesTheLightAndKeepsItDirectional)
{
  const auto msg = GzLightPublisher::buildLightMsg(
    sunAppearance(), lunar_illuminator::Vector3{0.0, 0.0, -1.0});
  EXPECT_EQ(msg.name(), "sun");
  EXPECT_EQ(msg.type(), gz::msgs::Light::DIRECTIONAL);
}

// The one that matters: Gazebo may replace rather than merge the light, so a
// message missing the appearance fields risks blacking the sun out entirely.
TEST(BuildLightMsg, AlwaysCarriesTheFullAppearanceNotJustDirection)
{
  const auto appearance = sunAppearance();
  const auto msg = GzLightPublisher::buildLightMsg(
    appearance, lunar_illuminator::Vector3{0.0, 0.0, -1.0});

  EXPECT_FLOAT_EQ(msg.diffuse().r(), 0.8f);
  EXPECT_FLOAT_EQ(msg.diffuse().g(), 0.8f);
  EXPECT_FLOAT_EQ(msg.diffuse().b(), 0.8f);
  EXPECT_FLOAT_EQ(msg.diffuse().a(), 1.0f);

  EXPECT_FLOAT_EQ(msg.specular().r(), 0.2f);
  EXPECT_FLOAT_EQ(msg.specular().g(), 0.2f);
  EXPECT_FLOAT_EQ(msg.specular().b(), 0.2f);
  EXPECT_FLOAT_EQ(msg.specular().a(), 1.0f);

  EXPECT_FLOAT_EQ(msg.range(), 1000.0f);
  EXPECT_FLOAT_EQ(msg.attenuation_constant(), 0.9f);
  EXPECT_FLOAT_EQ(msg.attenuation_linear(), 0.01f);
  EXPECT_FLOAT_EQ(msg.attenuation_quadratic(), 0.001f);
  EXPECT_TRUE(msg.cast_shadows());
}

TEST(GzLightPublisher, TopicIsEmptyBeforeAdvertising)
{
  GzLightPublisher publisher{sunAppearance()};
  EXPECT_EQ(publisher.topic(), "");
}

TEST(GzLightPublisher, AdvertiseBuildsTheWorldScopedLightConfigTopic)
{
  GzLightPublisher publisher{sunAppearance()};
  ASSERT_TRUE(publisher.advertise("empty_lunar_world"));
  EXPECT_EQ(publisher.topic(), "/world/empty_lunar_world/light_config");
}

TEST(GzLightPublisher, AdvertiseRejectsAnEmptyWorldName)
{
  // Otherwise we would advertise "/world//light_config".
  GzLightPublisher publisher{sunAppearance()};
  EXPECT_FALSE(publisher.advertise(""));
  EXPECT_EQ(publisher.topic(), "");
}

TEST(GzLightPublisher, PublishBeforeAdvertiseIsRejectedNotCrashing)
{
  GzLightPublisher publisher{sunAppearance()};
  EXPECT_FALSE(publisher.publish(lunar_illuminator::Vector3{0.0, 0.0, -1.0}));
}
