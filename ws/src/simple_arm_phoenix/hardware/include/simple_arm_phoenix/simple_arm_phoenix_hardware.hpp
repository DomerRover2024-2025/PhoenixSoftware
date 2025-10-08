// Copyright 2023 ros2_control Development Team
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

// ^ The above is text from the original version by the ros2_control team. This version is modified from example 7.

#ifndef SIMPLE_ARM_PHOENIX__SIMPLE_ARM_PHOENIX_HPP_
#define SIMPLE_ARM_PHOENIX__SIMPLE_ARM_PHOENIX_HPP_

// Import Libraries needed
#include "string"
#include "unordered_map"
#include "vector"

#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"

#include <stdio.h>
#include <string.h>

#include <fcntl.h>
#include <errno.h>
#include <termios.h>
#include <unistd.h>
#include <chrono>
#include <sys/ioctl.h>
#include <sys/file.h>
#include <thread>

#include <stdio.h>
#include <string.h>

#include <fcntl.h>
#include <errno.h>
#include <termios.h>
#include <unistd.h>
#include <chrono>
#include <sys/ioctl.h>
#include <sys/file.h>
#include <thread>

#include <bits/stdc++.h>

// Simplify some syntax with this declaration
using hardware_interface::return_type;

// namespace should be the same as the package name
namespace simple_arm_phoenix
{
using CallbackReturn = rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn; // More syntax reduction

class HARDWARE_INTERFACE_PUBLIC ArmSystem : public hardware_interface::SystemInterface // Define custom class inheriting a system interface
{
public: // Override required ftns
  CallbackReturn on_init(const hardware_interface::HardwareInfo & info) override;
  
  CallbackReturn on_activate(const rclcpp_lifecycle::State & previous_state) override;

  std::vector<hardware_interface::StateInterface> export_state_interfaces() override;

  std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;

  return_type read(const rclcpp::Time & time, const rclcpp::Duration & period) override;

  return_type write(const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/) override;

protected: // Vectors to be inherited and used in the .cpp file. These are the arrays that hold current values and command values of the joints.
  /// The size of this vector is (standard_interfaces_.size() x nr_joints)
  std::vector<double> joint_position_command_;
  std::vector<double> joint_position_;
  int serial_port;
  struct termios tty;
  // Array of strings (Honestly IDK why this is needed)
  std::unordered_map<std::string, std::vector<std::string>> joint_interfaces = {
    {"position", {}}};
};

}  // namespace ros2_control_demo_example_7

#endif  // ROS2_CONTROL_DEMO_EXAMPLE_7__R6BOT_HARDWARE_HPP_

