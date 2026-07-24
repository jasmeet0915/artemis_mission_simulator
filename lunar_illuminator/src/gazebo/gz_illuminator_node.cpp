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

#include "lunar_illuminator/gazebo/gz_illuminator_node.hpp"

#include <memory>
#include <string>
#include <vector>

#include "lunar_illuminator/sun_direction.hpp"

namespace lunar_illuminator
{
namespace gazebo
{

namespace
{
constexpr int kWarnThrottleMs = 5000;

std::array<float, 4> toRgba(const std::vector<double> & values)
{
  std::array<float, 4> rgba{{0.0f, 0.0f, 0.0f, 1.0f}};
  for (size_t i = 0; i < rgba.size() && i < values.size(); ++i) {
    rgba[i] = static_cast<float>(values[i]);
  }
  return rgba;
}
}  // namespace

GzIlluminatorNode::GzIlluminatorNode()
: rclcpp::Node("lunar_illuminator")
{
  const auto site_metadata_topic = this->declare_parameter<std::string>(
    "site_metadata_topic", "/mission/site_metadata");
  const auto sun_topic = this->declare_parameter<std::string>(
    "sun_topic", "/lunar_sky_tracker/sun");

  light_publisher_ =
    std::make_unique<GzLightPublisher>(readAppearanceParameters());

  // The mission manager latches site metadata, so match its durability or a
  // late-joining illuminator would never learn the world name.
  rclcpp::QoS metadata_qos{1};
  metadata_qos.transient_local();

  site_metadata_subscription_ =
    this->create_subscription<artemis_mission_interfaces::msg::SiteMetadata>(
    site_metadata_topic, metadata_qos,
    [this](const artemis_mission_interfaces::msg::SiteMetadata & msg) {
      this->onSiteMetadata(msg);
    });

  sun_subscription_ =
    this->create_subscription<artemis_mission_interfaces::msg::SkyObject>(
    sun_topic, 10,
    [this](const artemis_mission_interfaces::msg::SkyObject & msg) {
      this->onSkyObject(msg);
    });

  RCLCPP_INFO(
    this->get_logger(),
    "Lunar Illuminator waiting for site metadata on %s.",
    site_metadata_topic.c_str());
}

LightAppearance GzIlluminatorNode::readAppearanceParameters()
{
  LightAppearance appearance;
  appearance.name = this->declare_parameter<std::string>("light_name", "sun");

  appearance.diffuse = toRgba(
    this->declare_parameter<std::vector<double>>(
      "diffuse", {0.8, 0.8, 0.8, 1.0}));
  appearance.specular = toRgba(
    this->declare_parameter<std::vector<double>>(
      "specular", {0.2, 0.2, 0.2, 1.0}));

  appearance.attenuation_range = static_cast<float>(
    this->declare_parameter<double>("attenuation_range", 1000.0));
  appearance.attenuation_constant = static_cast<float>(
    this->declare_parameter<double>("attenuation_constant", 0.9));
  appearance.attenuation_linear = static_cast<float>(
    this->declare_parameter<double>("attenuation_linear", 0.01));
  appearance.attenuation_quadratic = static_cast<float>(
    this->declare_parameter<double>("attenuation_quadratic", 0.001));
  appearance.cast_shadows =
    this->declare_parameter<bool>("cast_shadows", true);

  return appearance;
}

void GzIlluminatorNode::onSiteMetadata(
  const artemis_mission_interfaces::msg::SiteMetadata & msg)
{
  // Metadata is latched and may be re-delivered; only act on a real change.
  if (msg.site_id == site_id_) {
    return;
  }

  const std::string world_name = worldNameForSite(msg.site_id);
  if (world_name.empty()) {
    RCLCPP_ERROR(
      this->get_logger(),
      "Site metadata carried an empty site_id; cannot resolve a world name.");
    return;
  }

  if (!light_publisher_->advertise(world_name)) {
    // Keep the node alive: Gazebo may simply not be up yet.
    RCLCPP_ERROR(
      this->get_logger(),
      "Could not advertise the light topic for world '%s'.",
      world_name.c_str());
    return;
  }

  site_id_ = msg.site_id;
  RCLCPP_INFO(
    this->get_logger(), "Illuminating '%s' via %s.",
    msg.display_name.c_str(), light_publisher_->topic().c_str());
}

void GzIlluminatorNode::onSkyObject(
  const artemis_mission_interfaces::msg::SkyObject & msg)
{
  if (light_publisher_->topic().empty()) {
    RCLCPP_WARN_THROTTLE(
      this->get_logger(), *this->get_clock(), kWarnThrottleMs,
      "Dropping sun updates until site metadata names the world.");
    return;
  }

  // Elevation below the horizon is ordinary geometry here; whoever owns scene
  // appearance decides what night should look like. The Sun direction is
  // already an ENU unit vector on the message, so we only negate it.
  const Vector3 direction = lightDirectionEnu(
    Vector3{msg.direction_enu.x, msg.direction_enu.y, msg.direction_enu.z});

  if (!light_publisher_->publish(direction)) {
    RCLCPP_WARN_THROTTLE(
      this->get_logger(), *this->get_clock(), kWarnThrottleMs,
      "Failed to publish a light update on %s.",
      light_publisher_->topic().c_str());
  }
}

}  // namespace gazebo
}  // namespace lunar_illuminator
