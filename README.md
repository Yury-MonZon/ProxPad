# ProxPad - Proxmox VM Management Interface

ProxPad is a web-based macropad interface for managing Proxmox virtual machines with a focus on mobile-friendly design and resource conflict prevention.

## Screenshots

**Portrait Mode (Mobile)**
![VM Page](images/landscape1.jpg)
![Macro Page](images/landscape2.jpg)
![Media Page](images/landscape3.jpg)

## Features
- **Mobile-Optimized Interface**: Responsive grid layout adapts to all screens
- **Resource Conflict Management**: Hides VMs that share resources when another in the group is running
- **Real-time Status Updates**: Live VM status, CPU, RAM
- **Quick Actions**: Start, stop, restart, shutdown, reboot VMs
- **Confirmation Dialogs**: Optional before executing VM actions
- **Auto-refresh**: Page updates when VM visibility changes

## Prerequisites
- Proxmox VE server
- Python 3.6+
- Flask
- proxmoxer library

## Installation

1. **Clone the project:**
   ```sh
   git clone https://github.com/Yury-MonZon/ProxPad.git
   cd ProxPad
   ```

2. **Install dependencies:**
   - On Arch/CachyOS: `./install_debs_cachyos.sh`
   - On Debian/Ubuntu: `./install_deps_debian.sh`

3. **Configure Proxmox API Token:**
   - Log into Proxmox web interface
   - Go to **Datacenter → Permissions → API Tokens**
   - Create a new token (e.g., user: `root@pam`, token ID: `ProxPad`)
   - **Disable "Privilege Separation" for the token**

4. **Configure ProxPad:**
   Edit `config.py`:
   ```python
   PROXMOX_HOST = "your.proxmox.server.ip"
   PROXMOX_USER = "root@pam"
   PROXMOX_TOKEN_ID = "ProxPad"
   PROXMOX_TOKEN_SECRET = "your-token-secret"
   VERIFY_SSL = False
   VM_IDS = [101, 102, 103, 104]
   SAME_RESOURCES = [ [101, 102], [103, 104] ]
   SHY = True
   ......
   ```

## Linux Keyboard Emulation: Why Use uinput?

On modern Linux distributions, direct keyboard emulation for macros and media keys is best achieved using the kernel's `uinput` device. This avoids the security restrictions and reliability issues of the xdg-desktop-portal API, which is designed for sandboxed apps and may block or restrict special key combos (like Super/Win+L) for security reasons.

**Why uinput?**
- Works reliably for all key combos, including Super/Win keys
- No need for user confirmation dialogs every time
- Avoids sandbox and security limitations of portals
- Can be set up for non-root usage with proper permissions

**How to install and set up uinput:**
1. Run the provided install script **inside your Linux VM(not needed for Windows VM)**:
   ```sh
   ./install_uinput.sh
   ```
   This will:
   - Load the uinput kernel module at boot
   - Set correct group and permissions for `/dev/uinput`
   - Add your user to the `input` group
   - Reload udev rules

2. Reboot or log out/in for group changes to take effect.

After setup, ProxPad will use uinput for keyboard emulation on Linux, allowing secure, reliable macro execution without root or portal limitations.

For more details, see the comments in `install_uinput.sh` and the macro handler source code.

## Configuration Options

### VM_IDS
List of Proxmox VM IDs to manage.

### SAME_RESOURCES
Define groups of VMs that share physical resources (GPUs, etc.).
- When any VM in a group is **running**, all others in that group are **hidden**
- When the running VM **stops**, others become **visible**

**Example:**
```python
SAME_RESOURCES = [
    [101, 102, 103],  # VMs sharing GPU #1
    [104, 105]        # VMs sharing GPU #2
]
```

### SHY
Set to `True` to show confirmation dialogs before VM actions.

## Running ProxPad

1. **Start the server:**
   ```sh
   python proxpad.py
   ```
2. **Access the interface:**
   - Open your browser to `http://your-server-ip:5000`
   - For mobile, bookmark or "Add to Home Screen"
3. **Background operation:**
   ```sh
   nohup python proxpad.py &
   ./run_me.sh &
   ```

## Usage

### Desktop/Tablet
- Responsive grid for VMs
- Landscape: more VMs horizontally
- Portrait: VMs stacked vertically

### Mobile Phones
- Optimized button layouts for touch
- Compact landscape mode
- Thumb-friendly sizing

### VM States
- **Green Start**: VM stopped
- **Red Stop/Reset**: VM running
- **Blue Reboot**: Graceful restart
- **Gray Shutdown**: Graceful shutdown

### Resource Management
- When VM 100 starts → VMs 101/102 hide (per config)
- When VM 100 stops → VMs 101/102 reappear
- Page auto-refreshes on visibility change

## Macro Handler: Running macro_handler.py in VMs

To process media keys, macro buttons, and program execution, you must run `macro_handler.py` inside each Windows or Linux VM you want to control. This script listens for UDP broadcast commands from ProxPad and executes the requested actions locally in the VM.

- On Windows: Run `python macro_handler.py` (requires Python and pynput)
- On Linux: Run `python macro_handler.py` (requires Python, pynput, and uinput for full key support)

**Note:**
- The macro handler must be running in the background in each VM for ProxPad's media and macro buttons to work.
- On Linux, ensure uinput is set up for full key emulation (see above).
- You can set up the macro handler to start automatically on VM boot for seamless integration.

## Troubleshooting

### Connection Issues
- Check Proxmox API token (disable Privilege Separation)
- Token needs `VM.Audit` and `VM.PowerMgmt` permissions
- Ensure network connectivity
- Set `VERIFY_SSL = False` for self-signed certs

### VM Not Appearing
- Check `VM_IDS` in config
- Check token permissions
- VM may be hidden due to `SAME_RESOURCES`

### Page Not Updating
- Ensure server is running
- Check browser cache
- Reload page

## License

This project is open source. Feel free to modify and distribute according to your needs.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve ProxPad.

## Support the project
[![Donate](https://storage.ko-fi.com/cdn/fullLogoKofi.png)](https://ko-fi.com/yurymonzon)

If you found this project useful, consider supporting my work with a small donation: https://ko-fi.com/yurymonzon Your support is greatly appreciated!


