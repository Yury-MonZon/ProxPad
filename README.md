# 📱 ProxPad - Proxmox Control Center & Macro Pad

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.0+-blue.svg)](https://flask.palletsprojects.com/)
[![GitHub stars](https://img.shields.io/github/stars/Yury-MonZon/ProxPad?style=social)](https://github.com/Yury-MonZon/ProxPad/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Yury-MonZon/ProxPad?style=social)](https://github.com/Yury-MonZon/ProxPad/network)

> **Turn your old iPad/Android tablet/phone into a dedicated Proxmox Control Center and macro pad!** 📱⚡

ProxPad is a web-based Stream Deck that puts your entire Proxmox infrastructure at your fingertips. Designed with mobile-first usability, it delivers seamless VM management, macro automation, and media control - all from a touch-optimized interface that works anywhere!

---

## ✨ Why ProxPad? Practical Benefits

📱 **Device Reuse**: Turn your old iPad/Android tablet/phone into a dedicated Proxmox Control Center and macro pad

⚡ **Real-Time Updates**: Live VM status with instant auto-refresh. Always know what's running

🎯 **Smart Resource Management**: Hides VMs that share the same resources. Prevents running 2 VMs with the same GPU/SSD/etc

🎮 **Macro Automation**: Execute macros, launch apps, control media - all with one tap

📳 **Haptic Feedback**: Vibration feedback on button press (configurable)

🎨 **GIF Support**: Animated buttons for a dynamic interface

---

## 📸 See It In Action!

**Mobile Experience - Clean Interface!**
![VM Page](images/landscape1.jpg)
*Your entire Proxmox fleet, beautifully organized*

---
![Macro Page](images/landscape2.jpg)
*One-tap macro execution - convenient control*

---
![Media Page](images/landscape3.jpg)
*Media control features, integrated with the interface*

---

## 🛠️ Architecture - Elegantly Simple

### 🖥️ **Server Component** (`proxpad.py`)
- Runs on your Proxmox server or LXC container
- Serves the stunning web interface
- Handles all VM management via Proxmox API
- Centralized configuration in `config.py`

### 📱 **Client Component** (`macro_handler.py`)
- Ultra-lightweight Python script
- Cross-platform: Windows & Linux support
- Minimal dependencies: `pynput` + optional `uinput`
- Listens for UDP commands and executes locally

---

## 🚀 Feature Showcase - What ProxPad Offers

| Feature | What It Does | Practical Benefit |
|---------|--------------|-------------------|
| **📱 Mobile-Optimized** | Touch-first responsive design | Use it anywhere, anytime |
| **🔄 Live Updates** | Real-time VM status monitoring | Always know what's running |
| **⚡ Quick Actions** | One-tap Start/Stop/Reboot/Shutdown | Control VMs instantly |
| **🎯 Smart Resources** | Auto-hide conflicting VMs | No more hardware conflicts |
| **🎮 Macro Pages** | Customizable macro buttons | Automate tasks efficiently |
| **🎨 GIF Icons** | Animated button support | Dynamic visual interface |
| **🎵 Media Control** | Integrated media player controls | Complete media hub |
| **📳 Haptic Feedback** | Vibration feedback on button press | Configurable user feedback |
| **🔒 Secure API** | Proxmox token authentication | Secure access |
| **🛠️ Easy Setup** | Automated install scripts | Running in minutes |

---

## 🎯 Quick Start - Get Running in 5 Minutes!

### 1️⃣ **Clone & Install**
```bash
git clone https://github.com/Yury-MonZon/ProxPad.git
cd ProxPad

# Server dependencies (Proxmox/LXC)
./install_deps_debian.sh  # or install_debs_cachyos.sh

# Client dependencies (VMs)
pip install pynput
```

### 2️⃣ **Configure Proxmox API**
- Log into Proxmox → Datacenter → Permissions → API Tokens
- Create token: `root@pam!ProxPad`
- **CRITICAL**: Disable "Privilege Separation"

### 3️⃣ **Setup Config**
```python
# config.py
PROXMOX_HOST = "your-proxmox-ip"
PROXMOX_TOKEN_ID = "root@pam!ProxPad"
PROXMOX_TOKEN_SECRET = "your-secret-token"
VM_IDS = [101, 102, 103, 104]
SAME_RESOURCES = [[101, 102], [103, 104]]  # Conflict groups
```

### 4️⃣ **Launch & Go!**
```bash
python proxpad.py
# Visit: http://your-ip:5000
```

---

## 🎮 Macro Commands - Available Actions

Create powerful macros with these commands:

| Command | Example | What It Does |
|---------|---------|--------------|
| **Key Press** | `key:win+l` | Lock screen |
| **Execute** | `exe:calc` | Open calculator |
| **Type Text** | `type:Hello World` | Type text |
| **Delay** | `delay:0.5` | Wait 0.5 seconds |
| **Open URL** | `url:https://google.com` | Open browser |
| **Chain Commands** | `key:win; delay:0.1; type:calc; key:enter` | Complex sequences |

---

## 🐧 Linux Support - The uinput Advantage!

**Why uinput is useful:**
- ✅ **Reliable**: All key combos work perfectly (including Super/Win!)
- ✅ **No Popups**: No annoying permission dialogs (Wayland)
- ✅ **Secure**: Proper kernel-level input handling
- ✅ **Flexible**: Non-root usage with correct permissions

**Setup in 30 seconds:**
```bash
# Inside your Linux VM
./install_uinput.sh
reboot
```

That's it! Full keyboard emulation without any limitations!

---

## 📱 Usage Scenarios - How People Love ProxPad!

### 🎮 **Gamers & Streamers**
- Launch gaming VMs with one tap
- Control media without alt-tabbing
- Macro automation for streaming

### 🏠 **Home Lab Enthusiasts**
- Manage homelab from couch
- Automate daily tasks
- Show off to friends! 😎

### 🏢 **IT Professionals**
- Manage server farms from anywhere
- Quick VM restarts during emergencies
- Monitor infrastructure on-the-go

---

## 🔧 Advanced Configuration

### **Resource Management**
```python
SAME_RESOURCES = [
    [101, 102],  # GPU sharing VMs
    [103, 104],  # USB device VMs
]
```

### **Custom Macros**
```python
MACROS = {
    "gaming": "key:win; delay:0.2; type:steam; key:enter",
    "work": "url:https://company-portal.com",
}
```

### **Security Options**
```python
VERIFY_SSL = False  # For self-signed certs
SHY_MODE = True    # Confirmation dialogs
```

---

## 🚨 Troubleshooting - Quick Fixes!

| Problem | Solution |
|---------|----------|
| **Connection Failed** | Check API token permissions (VM.Audit + VM.PowerMgmt) |
| **VMs Not Showing** | Verify VM_IDS in config and token permissions |
| **Page Not Updating** | Clear browser cache, ensure server running |
| **Macros Not Working** | Run macro_handler.py in target VM |
| **Linux Keys Not Working** | Install uinput and reboot |

---

## 🌟 Community & Support

### **Need Help? We've Got You Covered!**
- 📋 **Issues**: Report bugs on GitHub
- 💬 **Discord**: DM author `monzon4765`
- 💰 **Premium Support**: One-on-one setup paid assistance available

### **Contributing Welcome!**
- 🎨 UI/UX improvements
- 🔧 New features
- 🐛 Bug fixes
- 📚 Documentation

---

## 📜 License - Open Source!

```
ProxPad - Proxmox Control Deck & Macro Pad
Copyright (C) 2024 Yury Monzon

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
```

---

## 🎉 Support the Project - Help Us Improve

Love ProxPad? **Show your support and help us keep developing!**

[![Donate](https://storage.ko-fi.com/cdn/fullLogoKofi.png)](https://ko-fi.com/yurymonzon)

Every donation helps us:
- 🚀 Add new features
- 🐛 Fix bugs faster
- 📚 Improve documentation
- 🌟 Grow the community

**Your support helps ProxPad development!** ❤️

---

## 🚀 Ready to Enhance Your Proxmox Experience?

**What are you waiting for?**

1. ⭐ **Star the repo** - Show your love!
2. 🚀 **Install now** - Get running in minutes!
3. 📱 **Transform your phone** - Become a Proxmox power user!
4. 🎉 **Join the community** - Share your experience!

---

**#Homelab #Proxmox #ReuseOldTablet #HardwareMacroPad #VFIO**
