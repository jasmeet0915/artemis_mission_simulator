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

#include <memory>
#include <stdexcept>
#include <string>

#include "rclcpp/rclcpp.hpp"

#include "artemis_mission_interfaces/msg/site_metadata.hpp"
#include "artemis_mission_manager/site_metadata_reader.hpp"

namespace
{
using artemis_mission_interfaces::msg::SiteMetadata;
using artemis_mission_manager::SiteMetadataReader;

class MissionManager : public rclcpp::Node
{
public:
  MissionManager()
  : rclcpp::Node("mission_manager")
  {
  }

  /// Resolve the site parameter, load its metadata, and publish it latched.
  /// Throws std::runtime_error if the parameter is empty or the site cannot be loaded.
  void init()
  {
    const std::string site = this->declare_parameter<std::string>("site", "");
    if (site.empty()) {
      throw std::runtime_error(
        "Required parameter 'site' is empty. Launch with site:=<site_name>.");
    }

    SiteMetadata msg = SiteMetadataReader::read(site);
    msg.header.stamp = this->now();

    rclcpp::QoS qos(rclcpp::KeepLast(1));
    qos.reliable().transient_local();
    pub_ = this->create_publisher<SiteMetadata>("/mission/site_metadata", qos);
    pub_->publish(msg);
    RCLCPP_INFO(this->get_logger(), "Published latched site metadata for '%s'", site.c_str());
  }

private:
  rclcpp::Publisher<SiteMetadata>::SharedPtr pub_;
};
}  // namespace

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  try {
    auto node = std::make_shared<MissionManager>();
    node->init();
    // The node keeps spinning so late-joining subscribers receive the latched sample.
    rclcpp::spin(node);
  } catch (const std::exception & e) {
    RCLCPP_FATAL(rclcpp::get_logger("mission_manager"), "%s", e.what());
    rclcpp::shutdown();
    return 1;
  }
  rclcpp::shutdown();
  return 0;
}
