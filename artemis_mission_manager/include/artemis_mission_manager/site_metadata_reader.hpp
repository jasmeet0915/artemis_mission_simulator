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

#ifndef ARTEMIS_MISSION_MANAGER__SITE_METADATA_READER_HPP_
#define ARTEMIS_MISSION_MANAGER__SITE_METADATA_READER_HPP_

#include <filesystem>
#include <string>

#include "artemis_mission_interfaces/msg/site_metadata.hpp"

namespace artemis_mission_manager
{

/// Reads a site's metadata.yaml into a SiteMetadata message.
class SiteMetadataReader
{
public:
  /// Parse a metadata.yaml file. Throws std::runtime_error on a missing file
  /// or a missing required key.
  static artemis_mission_interfaces::msg::SiteMetadata fromFile(
    const std::filesystem::path & metadata_yaml);

  /// Resolve site_id to artemis_assets/models/<site_id>/metadata.yaml and parse it.
  static artemis_mission_interfaces::msg::SiteMetadata read(const std::string & site_id);
};

}  // namespace artemis_mission_manager

#endif  // ARTEMIS_MISSION_MANAGER__SITE_METADATA_READER_HPP_
