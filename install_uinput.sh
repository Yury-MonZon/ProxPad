#!/bin/sh
# ProxPad uinput setup for non-root usage

set -e

echo "Adding uinput to modules-load.d..."
echo "uinput" | sudo tee /etc/modules-load.d/uinput.conf

echo "Creating udev rule for /dev/uinput group and permissions..."
echo 'KERNEL=="uinput", MODE="0660", GROUP="input", TAG+="uaccess"' | sudo tee /etc/udev/rules.d/99-uinput.rules

echo "Adding current user ($USER) to input group..."
sudo gpasswd -a "$USER" input

echo "Reloading udev rules..."
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "Loading uinput kernel module..."
sudo modprobe uinput

echo "Setup complete!"
echo "Please reboot for group changes to take effect."