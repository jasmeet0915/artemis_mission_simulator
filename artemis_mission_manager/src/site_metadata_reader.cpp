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

#include "artemis_mission_manager/site_metadata_reader.hpp"

#include <yaml-cpp/yaml.h>

#include <stdexcept>
#include <string>

#include "ament_index_cpp/get_package_share_directory.hpp"

namespace artemis_mission_manager
{

namespace
{
YAML::Node require(const YAML::Node & node, const char * key, const std::string & where)
{
  if (!node[key]) {
    throw std::runtime_error(where + " is missing required key: " + key);
  }
  return node[key];
}
}  // namespace

artemis_mission_interfaces::msg::SiteMetadata SiteMetadataReader::fromFile(
  const std::filesystem::path & metadata_yaml)
{
  if (!std::filesystem::exists(metadata_yaml)) {
    throw std::runtime_error("SiteMetadata file not found: " + metadata_yaml.string());
  }

  const YAML::Node root = YAML::LoadFile(metadata_yaml.string());
  const std::string where = metadata_yaml.string();

  artemis_mission_interfaces::msg::SiteMetadata msg;
  msg.site_id = require(root, "site_id", where).as<std::string>();
  msg.display_name = require(root, "display_name", where).as<std::string>();
  msg.description = require(root, "description", where).as<std::string>();

  const YAML::Node coords = require(root, "coordinates", where);
  msg.origin_latitude = require(coords, "lat", where + ":coordinates").as<double>();
  msg.origin_longitude = require(coords, "lon", where + ":coordinates").as<double>();

  msg.size_x_m = require(root, "size_x_m", where).as<float>();
  msg.size_y_m = require(root, "size_y_m", where).as<float>();
  msg.source = require(root, "source", where).as<std::string>();
  return msg;
}

artemis_mission_interfaces::msg::SiteMetadata SiteMetadataReader::read(const std::string & site_id)
{
  const std::filesystem::path share =
    ament_index_cpp::get_package_share_directory("artemis_assets");
  return fromFile(share / "models" / site_id / "metadata.yaml");
}

}  // namespace artemis_mission_manager
