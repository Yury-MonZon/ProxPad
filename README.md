# ProxPad - Proxmox VM Management Interface

ProxPad is a web-based interface for managing Proxmox virtual machines with a focus on mobile-friendly design and resource conflict prevention.

## Screenshots

### Portrait Mode (Mobile)
![VM Page](images/landscape.jpg)

![Macro Page](images/landscape2.jpg)

![Media Page](images/landscape3.jpg)


## Features

- **Mobile-Optimized Interface**: Responsive grid layout that adapts to different screen sizes and orientations
- **Resource Conflict Management**: Automatically hides VMs that share the same resources (like GPUs) when another VM in the group is running
- **Real-time Status Updates**: Live monitoring of VM status, CPU usage, and RAM consumption
- **Quick Actions**: Start, stop, restart, shutdown, and reboot VMs with a single tap
- **Confirmation Dialogs**: Optional confirmation prompts before executing VM actions
- **Auto-refresh**: Page automatically updates when VM visibility changes due to resource sharing

## Prerequisites

- Proxmox VE server
- Python 3.6+
- Flask
- proxmoxer library

## Installation

1. **Clone or download the project files**:
   ```bash
   git clone https://github.com/Yury-MonZon/ProxPad.git
   cd ProxPad
   ```

2. **Install dependencies**:
   ```bash
   pip3 install flask proxmoxer
   ```

3. **Configure Proxmox API Token**:
   - Log into your Proxmox web interface
   - Go to **Datacenter → Permissions → API Tokens**
   - Create a new token (e.g., user: `root@pam`, token ID: `ProxPad`)
   - **Important**: Disable "Privilege Separation" for the token

4. **Configure ProxPad**:
   Edit `config.py` with your settings:
   ```python
   PROXMOX_HOST = "your.proxmox.server.ip"
   PROXMOX_USER = "root@pam"
   PROXMOX_TOKEN_ID = "ProxPad"
   PROXMOX_TOKEN_SECRET = "your-token-secret"
   VERIFY_SSL = False  # Set to True if using valid SSL certificates
   
   # List of VM IDs you want to manage
   VM_IDS = [101, 102, 103, 104]
   
   # Resource sharing groups (see below for details)
   SAME_RESOURCES = [
       [101, 102],  # These VMs share resources
       [103, 104]   # Add more groups as needed
   ]
   
   # Show confirmation dialogs
   SHY = True
   ```

## Configuration Options

### VM_IDS
List of Proxmox VM IDs that you want to manage through ProxPad.

### SAME_RESOURCES
This is the key feature for preventing resource conflicts. Define groups of VMs that share the same physical resources (like GPUs, special hardware, etc.).

**How it works**:
- When any VM in a group is **running**, all other VMs in that group are **hidden** from the interface
- When the running VM **stops**, the other VMs in the group become **visible** again
- This prevents accidentally starting multiple VMs that would conflict over the same hardware

**Example configurations**:
```python
# Example 1: Two separate GPU groups
SAME_RESOURCES = [
    [101, 102, 103],  # VMs sharing GPU #1
    [104, 105]        # VMs sharing GPU #2
]

# Example 2: One large GPU group
SAME_RESOURCES = [
    [101, 102, 103],  # All VMs share the same GPU
    []
]

# Example 3: No resource sharing
SAME_RESOURCES = [
    []  # No resource conflicts
]
```

### SHY
When set to `True`, shows confirmation dialogs before executing VM actions. Set to `False` for immediate actions.

## Running ProxPad

1. **Start the server**:
   ```bash
   python3 proxpad.py
   ```

2. **Access the interface**:
   - Open your browser to `http://your-server-ip:5000`
   - For mobile use, you can bookmark or "Add to Home Screen"

3. **Background operation** (optional):
   ```bash
   # Run in background
   nohup python3 proxpad.py &
   
   # Or use the provided script
   ./run_me.sh &
   ```

## Usage

### Desktop/Tablet
- VMs are displayed in a responsive grid
- Landscape mode optimizes for more VMs horizontally
- Portrait mode stacks VMs vertically

### Mobile Phones
- Optimized button layouts for touch interaction
- Landscape mode uses compact button arrangements
- All actions accessible with thumb-friendly sizing

### VM States
- **Green Start button**: VM is stopped and can be started
- **Red Stop/Reset buttons**: VM is running with available actions
- **Blue Reboot button**: Graceful restart option
- **Gray Shutdown button**: Graceful shutdown option

### Resource Management
- When VM 100 starts → VMs 101 and 102 automatically hide (based on example config 2)
- When VM 100 stops → VMs 101 and 102 automatically reappear
- Page refreshes automatically when VM visibility changes

## Troubleshooting

### Connection Issues
1. **Check Proxmox API token**: Ensure token exists and "Privilege Separation" is disabled
2. **Verify permissions**: Token needs `VM.Audit` and `VM.PowerMgmt` permissions
3. **Network connectivity**: Ensure ProxPad server can reach Proxmox host
4. **SSL verification**: Set `VERIFY_SSL = False` if using self-signed certificates

### VM Not Appearing
1. **Check VM_IDS**: Ensure VM ID is listed in config
2. **Check permissions**: Token must have access to specific VMs
3. **Check SAME_RESOURCES**: VM might be hidden due to resource sharing

### Page Not Updating
1. **Check browser console**: Look for JavaScript errors
2. **Verify network**: Ensure `/vm_status` endpoint is accessible
3. **Refresh manually**: Browser cache might need clearing

## Security Notes

- ProxPad runs on HTTP by default (port 5000)
- For production use, consider running behind a reverse proxy with HTTPS
- API token should have minimal required permissions
- Consider firewall rules to restrict access to the web interface

## File Structure

```
ProxPad/
├── proxpad.py          # Main Flask application
├── config.py           # Configuration file
├── requirements.txt    # Python dependencies
├── run_me.sh          # Startup script
└── README.md          # This file
```

## License

This project is open source. Feel free to modify and distribute according to your needs.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve ProxPad.

## Support the project
[![Donate](https://storage.ko-fi.com/cdn/fullLogoKofi.png)](https://ko-fi.com/yurymonzon)

If you found this project useful, consider supporting my work with a small donation: https://ko-fi.com/yurymonzon Your support is greatly appreciated!

