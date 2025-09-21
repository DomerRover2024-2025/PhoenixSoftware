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

// The above is copied from example 7 in the ros2_control demos. This one is modified for the arm.

// Import required libraries as well as the .hpp file which defines the hardware interface class
#include "simple_arm_phoenix/simple_arm_phoenix_hardware.hpp" // include the .hpp file
#include <string>
#include <vector>

namespace simple_arm_phoenix // namespace name == package name
{
CallbackReturn ArmSystem::on_init(const hardware_interface::HardwareInfo & info) // make sure class names match in .hpp and .cpp
{
  if (hardware_interface::SystemInterface::on_init(info) != CallbackReturn::SUCCESS)
  {
    return CallbackReturn::ERROR;
  }

  // robot has 6 joints and 1 interface
  joint_position_.assign(6, 0);
  joint_position_command_.assign(6, 0);

  // add names to the string thing in the .hpp
  for (const auto & joint : info_.joints)
  {
    for (const auto & interface : joint.state_interfaces)
    {
      joint_interfaces[interface.name].push_back(joint.name);
    }
  }
  // Boot up serial port connection
  /*

	*/
  return CallbackReturn::SUCCESS;
}

CallbackReturn ArmSystem::on_activate(const rclcpp_lifecycle::State & previous_state)
{
	  serial_port = ::open("/dev/ttyACM0", O_RDWR | O_NOCTTY | O_SYNC);
  if(tcgetattr(serial_port, &tty)!=0){
       // printf("Error %i \n", errno, strerror(errno));
    	printf("error");
	}
	
	if(flock(serial_port, LOCK_EX | LOCK_NB) == -1){
	printf("serial port locked");
	return CallbackReturn::ERROR;
	}
	
  tty.c_cflag &= ~PARENB;
  tty.c_cflag &= ~CSTOPB;
  tty.c_cflag &= ~CSIZE;
  tty.c_cflag |= CS8;
  tty.c_cflag &= ~CRTSCTS;

  tty.c_cflag |= CREAD | CLOCAL;

  tty.c_lflag &= ~ICANON;
  tty.c_lflag &= ~ECHO;
  tty.c_lflag &= ~ECHOE;
  tty.c_lflag &= ~ECHONL;
  tty.c_lflag &= ~ISIG;
  tty.c_iflag &= ~(IXON | IXOFF | IXANY);
  tty.c_iflag &= ~(IGNBRK|BRKINT|PARMRK|ISTRIP|INLCR|IGNCR|ICRNL);

  tty.c_oflag &= ~OPOST;
  tty.c_oflag &= ~ONLCR;

  tty.c_cc[VTIME] = 10;
  tty.c_cc[VMIN] = 0;

  cfsetispeed(&tty, B115200); // set baud rate
  cfsetospeed(&tty, B115200);

  if(tcsetattr(serial_port, TCSANOW, &tty)!=0){
   // printf("Error %i \n", errno, strerror(errno));
	printf("error");
	close(serial_port);
	}
	
   usleep(1000*1000);
 return CallbackReturn::SUCCESS;
}

std::vector<hardware_interface::StateInterface> ArmSystem::export_state_interfaces()
{
  std::vector<hardware_interface::StateInterface> state_interfaces; // create vector to hold state interfaces

  // link each joint to the state interfaces vector
  int ind = 0;
  for (const auto & joint_name : joint_interfaces["position"])
  {
    state_interfaces.emplace_back(joint_name, "position", &joint_position_[ind++]);
  }

  return state_interfaces;
}

std::vector<hardware_interface::CommandInterface> ArmSystem::export_command_interfaces()
{
  std::vector<hardware_interface::CommandInterface> command_interfaces; // create command interfaces vector

  // link each joint to the command interfaces
  int ind = 0;
  for (const auto & joint_name : joint_interfaces["position"])
  {
    command_interfaces.emplace_back(joint_name, "position", &joint_position_command_[ind++]);
  }

  return command_interfaces;
}

// read command
return_type ArmSystem::read(const rclcpp::Time & /*time*/, const rclcpp::Duration & period)
{
  
  // For now, joint position = joint command
  for (auto i = 0ul; i < joint_position_command_.size(); i++)
  {
    joint_position_[i] = joint_position_command_[i];
  }

  printf("Balls!");
  return return_type::OK;
}

return_type ArmSystem::write(const rclcpp::Time &, const rclcpp::Duration &)
{
  // send command from the positon_commands array
  printf("Balls");
  uint8_t write_this[sizeof(float)];
  float writey = 4.05;
  memcpy(&write_this, &writey, sizeof(writey));
  ::write(serial_port, write_this,sizeof(write_this));
  return return_type::OK;
}

}  // namespace ros2_control_demo_example_7

#include "pluginlib/class_list_macros.hpp"

PLUGINLIB_EXPORT_CLASS(
  simple_arm_phoenix::ArmSystem, hardware_interface::SystemInterface)

