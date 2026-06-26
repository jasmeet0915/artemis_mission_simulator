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

#include <gtest/gtest.h>

#include <filesystem>
#include <fstream>
#include <string>

#include "artemis_mission_manager/site_metadata_reader.hpp"

namespace fs = std::filesystem;
using artemis_mission_manager::SiteMetadataReader;

namespace
{
fs::path write_temp(const std::string & name, const std::string & content)
{
  const fs::path p = fs::temp_directory_path() / name;
  std::ofstream(p) << content;
  return p;
}
}  // namespace

TEST(SiteMetadataReader, ParsesAllFields)
{
  const auto p = write_temp(
    "smr_valid.yaml",
    "site_id: shackleton_rim\n"
    "display_name: Shackleton Rim\n"
    "description: \"Site 04 - Rim of Shackleton crater\"\n"
    "coordinates:\n"
    "  lat: -89.76681145214992\n"
    "  lon: -171.86989764584402\n"
    "size_x_m: 16000\n"
    "size_y_m: 16000\n"
    "source: nasa_pgda_78\n");

  const auto msg = SiteMetadataReader::fromFile(p);

  EXPECT_EQ(msg.site_id, "shackleton_rim");
  EXPECT_EQ(msg.display_name, "Shackleton Rim");
  EXPECT_EQ(msg.description, "Site 04 - Rim of Shackleton crater");
  EXPECT_NEAR(msg.origin_latitude, -89.76681145214992, 1e-9);
  EXPECT_NEAR(msg.origin_longitude, -171.86989764584402, 1e-9);
  EXPECT_FLOAT_EQ(msg.size_x_m, 16000.0f);
  EXPECT_FLOAT_EQ(msg.size_y_m, 16000.0f);
  EXPECT_EQ(msg.source, "nasa_pgda_78");
}

TEST(SiteMetadataReader, ThrowsOnMissingFile)
{
  EXPECT_THROW(
    SiteMetadataReader::fromFile("/nonexistent/path/metadata.yaml"),
    std::runtime_error);
}

TEST(SiteMetadataReader, ThrowsOnMissingKey)
{
  const auto p = write_temp(
    "smr_missing_key.yaml",
    "site_id: shackleton_rim\n"
    "source: nasa_pgda_78\n");  // display_name, description, coordinates, sizes missing

  EXPECT_THROW(SiteMetadataReader::fromFile(p), std::runtime_error);
}
