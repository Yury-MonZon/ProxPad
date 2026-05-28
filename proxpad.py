#!/usr/bin/env python3
"""
ProxPad - Proxmox VM Control Interface

A Flask-based web interface for managing Proxmox VMs with integrated
macro broadcasting system. Provides responsive touchscreen interface
for VM control and macro execution across multiple platforms.

Author: ProxPad Project
Version: 2.3
"""

import json
import socket
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from flask import Flask, jsonify, render_template, request
from proxmoxer import ProxmoxAPI

import config
# Always define PROXMOX_ENABLED before any usage
PROXMOX_ENABLED = False

# Initialize Flask application
app = Flask(__name__)

# UDP Broadcast configuration for macro system
BROADCAST_PORT = 5005
BROADCAST_IP = '255.255.255.255'

def send_broadcast_command(action: str) -> bool:
    """Send UDP broadcast command to VMs running macro handlers.
    
    Args:
        action (str): Command string to broadcast (e.g., "key:ctrl+c", "exe:calc")
        
    Returns:
        bool: True if broadcast was sent successfully
    """
    sock = None
    try:
        # Create and configure UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(1.0)  # Set timeout for safety
        
        # Prepare command payload
        command = {
            'action': action,
            'timestamp': int(time.time())
        }
        
        # Send broadcast message
        message = json.dumps(command).encode('utf-8')
        sock.sendto(message, (BROADCAST_IP, BROADCAST_PORT))
        
        app.logger.info(f"📡 Broadcast sent: {action}")
        return True
        
    except socket.timeout:
        app.logger.warning(f"⚠️  Broadcast timeout for: {action}")
        return False
    except Exception as e:
        app.logger.error(f"❌ Broadcast error for '{action}': {e}")
        return False
    finally:
        if sock:
            sock.close()

def get_macro_pages():
    """Get list of available macro pages from config."""
    pages = []
    page_num = 1
    while True:
        macro_attr = f'PAGE{page_num}_MACROS'
        if hasattr(config, macro_attr):
            pages.append({
                'id': f'macro{page_num}',
                'name': f'M{page_num}',
                'route': f'/macro{page_num}',
                'macros': getattr(config, macro_attr, [])
            })
            page_num += 1
        else:
            break
    return pages

# Global Proxmox API connection
proxmox: Optional[ProxmoxAPI] = None

def initialize_proxmox_connection() -> Tuple[bool, str]:
    """Initialize connection to Proxmox API with comprehensive error handling.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    global proxmox
    
    try:
        app.logger.info(f"🔌 Connecting to Proxmox: {config.PROXMOX_HOST}")
        
        # Initialize Proxmox API connection
        proxmox = ProxmoxAPI(
            config.PROXMOX_HOST,
            user=config.PROXMOX_USER,
            token_name=config.PROXMOX_TOKEN_ID,
            token_value=config.PROXMOX_TOKEN_SECRET,
            verify_ssl=config.VERIFY_SSL
        )
        
        # Test connection and get version
        version_info = proxmox.version.get()
        app.logger.info(f"✅ Connected to Proxmox {version_info.get('version', 'Unknown')}")
        
        # Validate permissions and access
        return _validate_proxmox_permissions()
        
    except Exception as e:
        error_msg = f"Failed to connect to Proxmox: {e}"
        app.logger.error(f"❌ {error_msg}")
        return False, error_msg

def _validate_proxmox_permissions() -> Tuple[bool, str]:
    """Validate Proxmox API permissions and detect privilege separation issues.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Test node access
        nodes = proxmox.nodes.get()
        if not nodes:
            return False, "No nodes accessible - check token permissions"
        
        app.logger.info(f"📊 Found {len(nodes)} Proxmox nodes")
        
        # Test VM access on first node
        test_node = nodes[0]['node']
        vm_list = proxmox.nodes(test_node).qemu.get()
        
        if len(vm_list) == 0:
            warning_msg = (
                "⚠️  No VMs visible - possible token permission issue. "
                "Ensure token has VM.Audit permissions and 'Privilege Separation' is disabled."
            )
            app.logger.warning(warning_msg)
            return False, warning_msg
        
        app.logger.info(f"✅ VM access validated: {len(vm_list)} VMs found")
        return True, f"Successfully connected with access to {len(vm_list)} VMs"
        
    except Exception as e:
        error_msg = f"Permission validation failed: {e}"
        app.logger.error(f"❌ {error_msg}")
        return False, error_msg

# Initialize Proxmox connection at startup


# Only attempt Proxmox connection if token secret is set
if hasattr(config, 'PROXMOX_TOKEN_SECRET') and config.PROXMOX_TOKEN_SECRET:
    connection_success, connection_message = initialize_proxmox_connection()
    if connection_success:
        PROXMOX_ENABLED = True
        app.logger.info("✅ ProxPad initialization completed successfully")
    else:
        app.logger.critical(f"💥 Proxmox disabled: {connection_message}")
        print(f"❌ Proxmox disabled: {connection_message}")
else:
    app.logger.info("❌ Proxmox token secret is empty: Proxmox features disabled.")

# In-memory queue for popup notifications
_pending_popups: List[Dict[str, Any]] = []

# Configuration constants

VM_IDS = config.VM_IDS
SHY = config.SHY
SAME_RESOURCES = getattr(config, 'SAME_RESOURCES', [])
HIDE_REBOOT = getattr(config, 'HIDE_REBOOT', False)

def format_ram(ram_bytes):
    gb = ram_bytes / (1024 ** 3)
    return max(round(gb, 2), 0)

@app.route('/')
def index() -> str:
    """Main dashboard showing VM status and controls."""
    app.logger.info("📊 Loading main dashboard")
    vms_data = []
    error_message = None
    if PROXMOX_ENABLED:
        try:
            vms_data = _get_visible_vms_data()
        except Exception as e:
            app.logger.error(f"❌ Dashboard error: {e}")
            error_message = str(e)
    macro_pages = get_macro_pages()
    return render_template(
        'index.html',
        vms=vms_data,
        shy=SHY,
        hide_reboot=HIDE_REBOOT,
        config=config,
        proxmox_enabled=PROXMOX_ENABLED,
        error_message=error_message,
        macro_pages=macro_pages
    )

def _get_visible_vms_data() -> List[Dict[str, Any]]:
    """
    Get VM data with resource group visibility filtering.
    Returns:
        List of VM dictionaries with status information
    """
    if not PROXMOX_ENABLED:
        app.logger.info("Proxmox is disabled or connection failed: no VM data available.")
        return []
    try:
        # Get primary node
        nodes = proxmox.nodes.get()
        if not nodes:
            raise Exception("No Proxmox nodes available")
        node = nodes[0]['node']
        # Collect all VM statuses and information
        all_vm_statuses = {}
        for vmid in VM_IDS:
            vm_info = _get_vm_info(node, vmid)
            all_vm_statuses[vmid] = vm_info
        # Apply resource group visibility rules
        hidden_vms = _determine_hidden_vms(all_vm_statuses)
        # Build visible VM list
        visible_vms = [
            all_vm_statuses[vmid]
            for vmid in VM_IDS
            if vmid not in hidden_vms
        ]
        app.logger.info(f"📋 Dashboard loaded: {len(visible_vms)} VMs visible")
        return visible_vms
    except Exception as e:
        app.logger.error(f"❌ Failed to get VM data: {e}")
        return []

def _get_vm_info(node: str, vmid: int) -> Dict[str, Any]:
    """
    Get comprehensive information for a single VM.
    Args:
        node: Proxmox node name
        vmid: VM identifier
    Returns:
        Dictionary with VM status and resource information
    """
    try:
        # Get VM status and resource usage
        status_data = proxmox.nodes(node).qemu(vmid).status.current.get()
        vm_status = status_data.get('status', 'unknown')
        
        # Get VM name from configuration
        vm_name = _get_vm_name(node, vmid)
        
        # Calculate resource usage for running VMs
        ram_gb = None
        cpu_percent = None
        if vm_status == 'running':
            ram_gb = format_ram(status_data.get('mem', 0))
            cpu_percent = round(status_data.get('cpu', 0) * 100, 1)
        
        return {
            'vmid': vmid,
            'name': vm_name,
            'status': vm_status,
            'ram_gb': ram_gb,
            'cpu_percent': cpu_percent
        }
        
    except Exception as e:
        app.logger.warning(f"⚠️ Failed to get info for VM {vmid}: {e}")
        return {
            'vmid': vmid,
            'name': f'VM {vmid}',
            'status': 'error',
            'ram_gb': None,
            'cpu_percent': None
        }

def _get_vm_name(node: str, vmid: int) -> str:
    """Get VM name from configuration.
    
    Args:
        node: Proxmox node name
        vmid: VM identifier
        
    Returns:
        VM name or fallback identifier
    """
    try:
        config_data = proxmox.nodes(node).qemu(vmid).config.get()
        return config_data.get('name', f'VM {vmid}')
    except Exception:
        return f'VM {vmid}'

def _determine_hidden_vms(all_vm_statuses: Dict[int, Dict[str, Any]]) -> Set[int]:
    """Determine which VMs should be hidden based on SAME_RESOURCES groups.
    
    Args:
        all_vm_statuses: Dictionary mapping VM IDs to status information
        
    Returns:
        Set of VM IDs that should be hidden
    """
    hidden_vms = set()
    
    for resource_group in SAME_RESOURCES:
        # Find running VMs in this resource group
        running_vms_in_group = [
            vmid for vmid in resource_group 
            if all_vm_statuses.get(vmid, {}).get('status') == 'running'
        ]
        
        # Hide non-running VMs in groups with running VMs
        if running_vms_in_group:
            for vmid in resource_group:
                if vmid not in running_vms_in_group:
                    hidden_vms.add(vmid)
    
    return hidden_vms

@app.route('/media')
def media() -> str:
    """Media control interface page.
    
    Returns:
        Rendered HTML template for media controls
    """
    try:
        app.logger.info("🎵 Loading media control interface")
        return render_template('media.html', config=config)
    except Exception as e:
        app.logger.error(f"❌ Media interface error: {e}")
        return f"Media interface error: {e}", 500


@app.route('/macro<int:page_num>')
def macro_page(page_num: int) -> str:
    """Macro control interface for additional pages."""
    try:
        app.logger.info(f"⌨️ Loading macro control interface {page_num}")
        macro_attr = f'PAGE{page_num}_MACROS'
        macro_configs = getattr(config, macro_attr, [])
        macro_rows_attr = f'PAGE{page_num}_MACRO_ROWS'
        macro_cols_attr = f'PAGE{page_num}_MACRO_COLS'
        macro_rows = getattr(config, macro_rows_attr, 4)
        macro_cols = getattr(config, macro_cols_attr, 5)
        return render_template('macro.html', config=config, macro_configs=macro_configs, page_num=page_num, macro_rows=macro_rows, macro_cols=macro_cols)
    except Exception as e:
        app.logger.error(f"❌ Macro{page_num} interface error: {e}")
        return f"Macro{page_num} interface error: {e}", 500

@app.route('/vm')
@app.route('/proxmox')
def vm_page() -> str:
    """VM management page.
    
    Returns:
        Rendered HTML template for VM controls
    """
    try:
        app.logger.info("🖥️ Loading VM management interface")
        vms_data = _get_visible_vms_data()
        
        return render_template(
            'proxmox.html', 
            vms=vms_data, 
            shy=SHY, 
            hide_reboot=HIDE_REBOOT
        )
        
    except Exception as e:
        app.logger.error(f"❌ VM interface error: {e}")
        return f"VM interface error: {e}", 500

@app.route('/media_control/<action>', methods=['POST'])
def media_control(action: str):
    """Handle media control commands via UDP broadcast.
    
    Args:
        action: Media action identifier (play_pause, next, previous, etc.)
        
    Returns:
        JSON response with success status
    """
    try:
        app.logger.info(f"🎵 Media control: {action}")
        
        # Map action to broadcast command
        action_map = {
            'play_pause': 'key:media_play_pause',
            'next': 'key:media_next',
            'previous': 'key:media_previous',
            'volume_up': 'key:volume_up',
            'volume_down': 'key:volume_down',
            'mute': 'key:volume_mute'
        }
        
        if action not in action_map:
            app.logger.warning(f"⚠️ Invalid media action: {action}")
            return jsonify({
                'success': False, 
                'error': f'Invalid action: {action}'
            }), 400
        
        command = action_map[action]
        success = send_broadcast_command(command)
        
        if success:
            app.logger.info(f"✅ Media command sent: {command}")
        else:
            app.logger.error(f"❌ Failed to send media command: {command}")
        
        return jsonify({'success': success})
        
    except Exception as e:
        app.logger.error(f"❌ Media control error: {e}")
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@app.route('/launch_music_player', methods=['POST'])
def launch_music_player():
    """Launch the configured music player application.
    
    Returns:
        JSON response with launch status and player information
    """
    try:
        player = config.MUSIC_PLAYER
        app.logger.info(f"🎵 Launching music player: {player}")

        # Support url:, exe:, key:, type: prefixes
        if player.startswith(('url:', 'exe:', 'key:', 'type:')):
            command = player
        else:
            command = f'exe:{player}'

        success = send_broadcast_command(command)

        if success:
            app.logger.info(f"✅ Music player launched: {player}")
            return jsonify({
                'success': True,
                'player': player
            })
        else:
            app.logger.error(f"❌ Failed to launch music player: {player}")
            return jsonify({
                'success': False,
                'error': 'Failed to send broadcast command'
            })
            
    except Exception as e:
        app.logger.error(f"❌ Music player launch error: {e}")
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@app.route('/api/run_macro', methods=['POST'])
def run_macro():
    """Execute macro commands via broadcast or local execution.

    Supports UDP broadcast commands (key:, exe:, url:, type:).

    Returns:
        JSON response with execution status and output
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid JSON data'
            }), 400
        
        command = data.get('command')
        if not command:
            return jsonify({
                'success': False,
                'error': 'No command provided'
            }), 400
        
        app.logger.info(f"⌨️ Executing macro: {command}")

        # Handle broadcast commands (key:, exe:, url:, type: prefixes)
        if command.startswith(('key:', 'exe:', 'url:', 'type:')):
            return _execute_broadcast_macro(command)
        
    except Exception as e:
        app.logger.error(f"❌ Macro execution error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def _execute_broadcast_macro(command: str):
    """Execute macro command via UDP broadcast.
    
    Args:
        command: Broadcast command (key: or exe: prefix)
        
    Returns:
        JSON response with broadcast status
    """
    success = send_broadcast_command(command)

    # If this is an OS-lock shortcut, inform the caller so the UI can activate
    # the screensaver immediately. We include the flag regardless of broadcast
    # success so the initiating client can react locally.
    screensaver_flag = False
    try:
        if isinstance(command, str) and command.lower() in ('key:super+l', 'key:win+l'):
            screensaver_flag = True
    except Exception:
        screensaver_flag = False

    if success:
        app.logger.info(f"✅ Broadcast macro sent: {command}")
        return jsonify({
            'success': True,
            'output': f'Command sent: {command}',
            'error': '',
            'return_code': 0,
            'screensaver': screensaver_flag
        })
    else:
        app.logger.error(f"❌ Failed to send macro: {command}")
        return jsonify({
            'success': False,
            'output': '',
            'error': 'UDP broadcast failed',
            'return_code': 1,
            'screensaver': screensaver_flag
        })

@app.route('/vm/<int:vmid>/<action>', methods=['POST'])
def control_vm(vmid: int, action: str):
    """Control VM power state operations.
    
    Args:
        vmid: Virtual machine identifier
        action: Power action (start, stop, restart, shutdown, reboot)
        
    Returns:
        JSON response with operation status
    """
    try:
        app.logger.info(f"🔌 VM {vmid} action: {action}")
        
        # Validate action
        valid_actions = ['start', 'stop', 'restart', 'shutdown', 'reboot']
        if action not in valid_actions:
            app.logger.warning(f"⚠️ Invalid VM action: {action}")
            return jsonify({
                'status': 'error',
                'message': f'Invalid action: {action}. Valid actions: {valid_actions}'
            }), 400
        
        # Get primary node
        nodes = proxmox.nodes.get()
        if not nodes:
            raise Exception("No Proxmox nodes available")
        
        node = nodes[0]['node']
        
        # Execute VM action
        vm_endpoint = proxmox.nodes(node).qemu(vmid)
        
        if action == 'start':
            vm_endpoint.status.start.post()
        elif action == 'stop':
            vm_endpoint.status.stop.post()
        elif action == 'restart':
            vm_endpoint.status.reset.post()
        elif action == 'shutdown':
            vm_endpoint.status.shutdown.post()
        elif action == 'reboot':
            vm_endpoint.status.reboot.post()
        
        app.logger.info(f"✅ VM {vmid} {action} initiated successfully")
        
        return jsonify({
            'status': 'success',
            'vmid': vmid,
            'action': action,
            'message': f'VM {vmid} {action} command sent successfully'
        })
        
    except Exception as e:
        app.logger.error(f"❌ VM {vmid} {action} failed: {e}")
        return jsonify({
            'status': 'error',
            'vmid': vmid,
            'action': action,
            'message': str(e)
        }), 500

@app.route('/vm_status')
def vm_status():
    """Get current VM status information with resource group filtering.
    
    Returns:
        JSON array of visible VM status objects
    """
    try:
        app.logger.info("📊 Fetching VM status update")
        
        # Get VM data using the same logic as the dashboard
        vms_data = _get_visible_vms_data()
        
        app.logger.info(f"✅ VM status update: {len(vms_data)} VMs")
        return jsonify(vms_data)
        
    except Exception as e:
        app.logger.error(f"❌ VM status error: {e}")
        return jsonify({
            'error': 'Failed to fetch VM status',
            'message': str(e)
        }), 500

@app.route('/api/popup', methods=['POST'])
def show_popup():
    """Queue a popup notification for display on the web interface.
    
    Accepts JSON:
        text (str): Message to display (required)
        icon (str): Bootstrap icon name or image URL (default: 'info-circle')
        keep (bool): If true, stays until user taps (default: false, auto-dismiss 10s)
    
    Returns:
        JSON response with success status
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid JSON'}), 400
        
        text = data.get('text')
        if not text:
            return jsonify({'success': False, 'error': 'Missing text'}), 400
        
        popup = {
            'id': str(int(time.time() * 1000)),
            'text': text,
            'icon': data.get('icon', 'info-circle'),
            'keep': data.get('keep', False)
        }
        _pending_popups.append(popup)
        
        app.logger.info(f"🪟 Popup queued: {text[:60]}")
        return jsonify({'success': True, 'id': popup['id']})
        
    except Exception as e:
        app.logger.error(f"❌ Popup error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/popup/poll')
def poll_popups():
    """Return and clear all pending popup notifications.
    
    Returns:
        JSON array of pending popup objects
    """
    global _pending_popups
    try:
        popups = list(_pending_popups)
        _pending_popups.clear()
        resp = jsonify(popups)
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        return resp
    except Exception as e:
        app.logger.error(f"❌ Popup poll error: {e}")
        return jsonify([]), 200

if __name__ == '__main__':
    """Main application entry point for server."""
    app.logger.info("🚀 Starting ProxPad server")
    app.logger.info("📋 Available routes:")
    app.logger.info("   - / : Main VM dashboard")
    app.logger.info("   - /media : Media control interface")
    app.logger.info("   - /macro1 : Macro control interface")
    app.logger.info("   - /vm_status : VM status API")
    app.logger.info("   - /api/run_macro : Macro execution API")
    app.logger.info("   - /api/popup : Popup notification API")
    app.logger.info("   - /api/popup/poll : Popup poll endpoint")
    app.logger.info("🌐 Server starting on http://0.0.0.0:5000")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        app.logger.info("🛑 Server stopped by user")
    except Exception as e:
        app.logger.error(f"💥 Server startup failed: {e}")
        raise
