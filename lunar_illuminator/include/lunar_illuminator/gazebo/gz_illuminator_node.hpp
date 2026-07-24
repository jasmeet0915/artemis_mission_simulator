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

#ifndef LUNAR_ILLUMINATOR__GAZEBO__GZ_ILLUMINATOR_NODE_HPP_
#define LUNAR_ILLUMINATOR__GAZEBO__GZ_ILLUMINATOR_NODE_HPP_

#include <memory>
#include <string>

#include "artemis_mission_interfaces/msg/site_metadata.hpp"
#include "artemis_mission_interfaces/msg/sky_object.hpp"
#include "lunar_illuminator/gazebo/gz_light_publisher.hpp"
#include "rclcpp/rclcpp.hpp"

namespace lunar_illuminator
{
namespace gazebo
{

/// Drives Gazebo's sun light from the lunar sky tracker's az/el.
/**
 * The site metadata names the world, so nothing can be published until the
 * first metadata message arrives. Sun messages before that are dropped.
 */
class GzIlluminatorNode : public rclcpp::Node
{
public:
  GzIlluminatorNode();

private:
  void onSiteMetadata(const artemis_mission_interfaces::msg::SiteMetadata & msg);
  void onSkyObject(const artemis_mission_interfaces::msg::SkyObject & msg);

  LightAppearance readAppearanceParameters();

  std::unique_ptr<GzLightPublisher> light_publisher_;
  std::string site_id_;

  rclcpp::Subscription<artemis_mission_interfaces::msg::SiteMetadata>::SharedPtr
    site_metadata_subscription_;
  rclcpp::Subscription<artemis_mission_interfaces::msg::SkyObject>::SharedPtr
    sun_subscription_;
};

}  // namespace gazebo
}  // namespace lunar_illuminator

#endif  // LUNAR_ILLUMINATOR__GAZEBO__GZ_ILLUMINATOR_NODE_HPP_
