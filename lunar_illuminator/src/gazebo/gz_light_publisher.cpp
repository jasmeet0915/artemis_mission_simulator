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

#include "lunar_illuminator/gazebo/gz_light_publisher.hpp"

#include <string>
#include <utility>

namespace lunar_illuminator
{
namespace gazebo
{

GzLightPublisher::GzLightPublisher(LightAppearance appearance)
: appearance_(std::move(appearance))
{
}

bool GzLightPublisher::advertise(const std::string & world_name)
{
  if (world_name.empty()) {
    // Guards against advertising "/world//light_config".
    return false;
  }

  const std::string topic = "/world/" + world_name + "/light_config";
  publisher_ = node_.Advertise<gz::msgs::Light>(topic);
  if (!publisher_) {
    topic_.clear();
    return false;
  }

  topic_ = topic;
  return true;
}

bool GzLightPublisher::publish(const Vector3 & direction)
{
  if (topic_.empty()) {
    return false;
  }
  return publisher_.Publish(buildLightMsg(appearance_, direction));
}

gz::msgs::Light GzLightPublisher::buildLightMsg(
  const LightAppearance & appearance, const Vector3 & direction)
{
  gz::msgs::Light msg;
  msg.set_name(appearance.name);
  msg.set_type(gz::msgs::Light::DIRECTIONAL);

  msg.mutable_diffuse()->set_r(appearance.diffuse[0]);
  msg.mutable_diffuse()->set_g(appearance.diffuse[1]);
  msg.mutable_diffuse()->set_b(appearance.diffuse[2]);
  msg.mutable_diffuse()->set_a(appearance.diffuse[3]);

  msg.mutable_specular()->set_r(appearance.specular[0]);
  msg.mutable_specular()->set_g(appearance.specular[1]);
  msg.mutable_specular()->set_b(appearance.specular[2]);
  msg.mutable_specular()->set_a(appearance.specular[3]);

  msg.set_range(appearance.attenuation_range);
  msg.set_attenuation_constant(appearance.attenuation_constant);
  msg.set_attenuation_linear(appearance.attenuation_linear);
  msg.set_attenuation_quadratic(appearance.attenuation_quadratic);
  msg.set_cast_shadows(appearance.cast_shadows);

  msg.mutable_direction()->set_x(direction.x);
  msg.mutable_direction()->set_y(direction.y);
  msg.mutable_direction()->set_z(direction.z);

  return msg;
}

}  // namespace gazebo
}  // namespace lunar_illuminator
