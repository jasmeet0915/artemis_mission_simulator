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

#ifndef LUNAR_ILLUMINATOR__GAZEBO__GZ_LIGHT_PUBLISHER_HPP_
#define LUNAR_ILLUMINATOR__GAZEBO__GZ_LIGHT_PUBLISHER_HPP_

#include <array>
#include <string>

#include "gz/msgs/light.pb.h"
#include "gz/transport/Node.hh"
#include "lunar_illuminator/sun_direction.hpp"

namespace lunar_illuminator
{
namespace gazebo
{

/// Static appearance of the light, everything except its direction.
/**
 * Sent on every update because Gazebo may replace rather than merge the light
 * component: a message carrying only a direction risks zeroing the colours and
 * blacking the scene out.
 */
struct LightAppearance
{
  std::string name{"sun"};
  std::array<float, 4> diffuse{{0.8f, 0.8f, 0.8f, 1.0f}};
  std::array<float, 4> specular{{0.2f, 0.2f, 0.2f, 1.0f}};
  // float, not double: gz.msgs.Light stores these as float, so a double here
  // would promise precision the wire format cannot carry.
  float attenuation_range{1000.0f};
  float attenuation_constant{0.9f};
  float attenuation_linear{0.01f};
  float attenuation_quadratic{0.001f};
  bool cast_shadows{true};
};

/// Publishes light updates to Gazebo over gz-transport.
class GzLightPublisher
{
public:
  explicit GzLightPublisher(LightAppearance appearance);

  /// Advertise on /world/<world_name>/light_config. False on an empty name.
  bool advertise(const std::string & world_name);

  /// Publish the full light spec with this direction. False if not advertised.
  bool publish(const Vector3 & direction);

  /// The advertised topic, or an empty string before advertise() succeeds.
  const std::string & topic() const {return topic_;}

  /// Assemble the complete message. Static and pure so it is testable without
  /// a transport node or a running simulator.
  static gz::msgs::Light buildLightMsg(
    const LightAppearance & appearance, const Vector3 & direction);

private:
  LightAppearance appearance_;
  gz::transport::Node node_;
  gz::transport::Node::Publisher publisher_;
  std::string topic_;
};

}  // namespace gazebo
}  // namespace lunar_illuminator

#endif  // LUNAR_ILLUMINATOR__GAZEBO__GZ_LIGHT_PUBLISHER_HPP_
