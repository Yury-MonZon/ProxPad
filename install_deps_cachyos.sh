#!/bin/sh
# Install all required Python libraries and system dependencies for ProxPad (CachyOS/Arch)
set -e

# System dependencies
sudo pacman -S --needed python-flask python-proxmoxer python-requests python-pynput python-uinput

# Optional: Install via pip for user if not available in repo
# python3 -m pip install --user python-uinput pynput --break-system-packages

echo "All dependencies installed. Please ensure you have set up uinput permissions as described in the docs."
