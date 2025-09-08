# config.py

PROXMOX_HOST = "192.168.1.123"
PROXMOX_USER = "root@pam"
PROXMOX_TOKEN_ID = "ProxPad"
PROXMOX_TOKEN_SECRET = "TOKEN_SECRET_HERE"
VERIFY_SSL = False

# List of VMs to manage
VM_IDS = [104, 103, 102, 107]

# This doesn't work properly with some VMs and GPU passthrough, so you can disable it if needed
HIDE_REBOOT = True

# List of lists of VMs that share the same resources (e.g., GPU)
# When one VM from a group is running, others in the same group will be hidden
# Example: [[104, 103], [102, 107]] means VMs 104&103 share resources, and 102&107 share resources
SAME_RESOURCES = [
    [104, 103, 107],  
    []   
]

# If True, show confirmation dialog before sending actions
SHY = True

# Tab bar positioning in landscape mode
# False = tabs on left side, True = tabs on right side
TABS_RIGHT = True

# Default music player to launch (can be 'spotify', 'rhythmbox', 'vlc', 'audacious', etc.)
MUSIC_PLAYER = "rhythmbox"

# Macro button configuration
PAGE1_MACRO_ROWS = 3
PAGE1_MACRO_COLS = 4

# Icons from https://icons.getbootstrap.com/
# Bootstrap Icons uses `bi bi-<icon-name>`
# Button = [color, label, icon, action]
MACRO1_1  = ["#f38ba8", "Copy", "bi bi-clipboard", "key:ctrl+c"]
MACRO1_2  = ["#a6e3a1", "Paste", "bi bi-clipboard-plus", "key:ctrl+v"]
MACRO1_3  = ["#89b4fa", "Undo", "bi bi-arrow-counterclockwise", "key:ctrl+z"]
MACRO1_4  = ["#f9e2af", "Save", "bi bi-save", "key:ctrl+s"]
MACRO1_5  = ["#cba6f7", "Screenshot", "bi bi-camera", "key:print_screen"]
MACRO1_6  = ["#f38ba8", "YouTube", "bi bi-youtube", "url:https://youtube.com"]
MACRO1_7  = ["#f5e0dc", "Lock PC", "bi bi-lock", "key:super+l"]
MACRO1_8  = ["#bac2de", "Alt+Tab", "bi bi-arrow-repeat", "key:alt+tab"]
MACRO1_9  = ["#fab387", "Win+R", "bi bi-window", "key:cmd+r"]
MACRO1_10 = ["#74c7ec", "Type", "bi bi-keyboard", "key:A+B+c"]
MACRO1_11 = ["#b4befe", "Calculator", "bi bi-calculator", "exe:calc"]
MACRO1_12 = ["#f2cdcd", "Play/Pause", "bi bi-play-circle", "key:media_play_pause"]

# Macro button configuration
PAGE2_MACRO_ROWS = 3
PAGE2_MACRO_COLS = 4

# Icons from https://icons.getbootstrap.com/
# Bootstrap Icons uses `bi bi-<icon-name>`
# Button = [color, label, icon, action]
MACRO2_1  = ["#f38ba8", "Copy", "bi bi-clipboard", "key:ctrl+c"]
MACRO2_2  = ["#a6e3a1", "Paste", "bi bi-clipboard-plus", "key:ctrl+v"]
MACRO2_3  = ["#89b4fa", "Undo", "bi bi-arrow-counterclockwise", "key:ctrl+z"]
MACRO2_4  = ["#f9e2af", "Save", "bi bi-save", "key:ctrl+s"]
MACRO2_5  = ["#cba6f7", "Screenshot", "bi bi-camera", "key:print_screen"]
MACRO2_6  = ["#f38ba8", "YouTube", "bi bi-youtube", "url:https://youtube.com"]
MACRO2_7  = ["#f5e0dc", "Lock PC", "bi bi-lock", "key:super+l"]
MACRO2_8  = ["#bac2de", "Alt+Tab", "bi bi-arrow-repeat", "key:alt+tab"]
MACRO2_9  = ["#fab387", "Win+R", "bi bi-window", "key:cmd+r"]
MACRO2_10 = ["#74c7ec", "Paste", "bi bi-clipboard", "key:ctrl+v"]
MACRO2_11 = ["#b4befe", "Calculator", "bi bi-calculator", "exe:calc"]
MACRO2_12 = ["#f2cdcd", "Play/Pause", "bi bi-play-circle", "key:media_play_pause"]

# MACRO CONFIGURATION
# Format: ["color", "label", "icon", "action"]
# 
# Available Actions:
# - Key commands (Single): "key:a", "key:1", "key:f1", "key:enter", "key:space", "key:delete"
# - Key combinations: "key:ctrl+c", "key:alt+tab", "key:ctrl+shift+n", "key:cmd+r"
# - Special keys: "key:up", "key:down", "key:left", "key:right", "key:home", "key:end"
# - Function keys: "key:f1" through "key:f20"
# - Media keys: "key:media_play_pause", "key:media_volume_up", "key:media_next"
# - Executables: "exe:calc.exe", "exe:notepad.exe"
# - Web URLs: "url:http://google.com" (opens in default browser)
# - Custom actions: "custom_action1", "refresh_status"
#
# Key Examples:
# Single Keys:
#   Letters: key:a, key:b, key:z
#   Numbers: key:1, key:2, key:0  
#   Function: key:f1, key:f12, key:f20
#   Special: key:space, key:enter, key:tab, key:escape, key:delete, key:backspace
#   Arrows: key:up, key:down, key:left, key:right
#   Navigation: key:home, key:end, key:page_up, key:page_down, key:insert
#
# Key Combinations:
#   Basic: key:ctrl+c, key:ctrl+v, key:ctrl+z
#   Alt combos: key:alt+tab, key:alt+f4
#   Multi-mod: key:ctrl+shift+esc, key:ctrl+alt+delete
#   Windows/Cmd: key:cmd+r, key:cmd+space (Mac style)
#
# Media Keys:
#   key:media_play_pause, key:media_next, key:media_previous
#   key:media_stop, key:media_volume_up, key:media_volume_down
#   key:media_volume_mute
