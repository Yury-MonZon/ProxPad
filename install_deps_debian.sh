#!/bin/sh
# Install all required Python libraries and system dependencies for ProxPad (Debian/Ubuntu)
set -e

# System dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-flask python3-requests python3-proxmoxer python3-pynput python3-uinput

# Optional: Install via pip for user if not available in repo
# python3 -m pip install --user pynput python-uinput --break-system-packages

echo "All dependencies installed. Please ensure you have set up uinput permissions as described in the docs."
