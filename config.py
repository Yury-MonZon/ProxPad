# config.py

PROXMOX_HOST = "192.168.1.123"
PROXMOX_USER = "root@pam"
PROXMOX_TOKEN_ID = "ProxPad"
PROXMOX_TOKEN_SECRET = ""
# PROXMOX_TOKEN_SECRET = ""
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

# Time in minutes to wait before locking the screen after sending the lock command
SCREENSAVER = 1 # In minutes, set to 0 to disable
SCREENSAVER_24H = True # If True, use 24-hour format in the screensaver clock
SCREENSAVER_SECONDS = False # If True, show seconds in the screensaver clock
SCREENSAVER_COLOR = "#525252ff"  # Color of the clock text in the screensaver
SCREENSAVER_BLANK = False  # If True, show blank screen instead of screensaver image

# Tab bar positioning in landscape mode
# False = tabs on left side, True = tabs on right side
TABS_RIGHT = True

# Default music player to launch (can be 'spotify', 'rhythmbox', 'vlc', 'audacious', etc.)
MUSIC_PLAYER = "url:https://music.youtube.com"
MUSIC_PLAYER_ICON = "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/YouTube_Music_full_logo.svg/1024px-YouTube_Music_full_logo.svg.png"

# Macro button configuration
PAGE1_MACRO_ROWS = 4
PAGE1_MACRO_COLS = 5

# Icons from https://icons.getbootstrap.com/
# Bootstrap Icons uses `bi bi-<icon-name>`
# Or you can use direct image URLs for custom icons
# Button = [color, label, icon, action]
PAGE1_MACROS = [
    ["#f5e0dc", "VSCode", "https://code.visualstudio.com/assets/images/code-stable.png", "exe:code"],
    ["#f2cdcd", "SelectAll", "bi bi-clipboard-plus", "key:ctrl+a"],
    ["#f38ba8", "Calculator", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/GNOME_Calculator_icon_2020.svg/120px-GNOME_Calculator_icon_2020.svg.png", "exe:gnome-calculator"],
    ["#cba6f7", "EasySSH", "https://dl.flathub.org/media/com/github/muriloventuroso.easyssh/3f48db4f2c5ea9f7c1843ac759ab1e99/icons/128x128@2/com.github.muriloventuroso.easyssh.png", "exe:flatpak run com.github.muriloventuroso.easyssh"],
    ["#f5c2e7", "Gnote", "https://dl.flathub.org/media/org/gnome/Gnote/dca870ae6f603979b447056added4351/icons/128x128/org.gnome.Gnote.png", "exe:flatpak run org.gnome.Gnote"],
    ["#eba0ac", "Screenshot", "bi bi-camera", "key:print_screen"],
    ["#fab387", "YouTube", "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fd/YouTube_full-color_icon_%282024%29.svg/250px-YouTube_full-color_icon_%282024%29.svg.png", "url:https://youtube.com"],
    ["#74c7ec", "Matrix", "https://www.awicons.com/free-icons/download/object-icons/activity-monitor-icons-by-gordon-irving/png/256/Matrix.png", "exe:eog --fullscreen ~/Documents/Code/ProxPad/matrix.jpg"],
    ["#f4dbd6", "Matrix1", "https://www.awicons.com/free-icons/download/object-icons/activity-monitor-icons-by-gordon-irving/png/256/Matrix.png", "exe:eog --fullscreen ~/Documents/Code/ProxPad/matrix.jpg"],
    ["#f9e2af", "Parsec", "https://dl.flathub.org/media/com/parsecgaming/parsec/22a654406fc9c48c5935415a0d5b6cc4/icons/128x128/com.parsecgaming.parsec.png", "exe:flatpak run com.parsecgaming.parsec"],
    ["#e7c6ff", "Matrix2", "https://www.awicons.com/free-icons/download/object-icons/activity-monitor-icons-by-gordon-irving/png/256/Matrix.png", "exe:eog --fullscreen ~/Documents/Code/ProxPad/matrix.jpg"],
    ["#d8b4f2", "Matrix3", "https://www.awicons.com/free-icons/download/object-icons/activity-monitor-icons-by-gordon-irving/png/256/Matrix.png", "exe:eog --fullscreen ~/Documents/Code/ProxPad/matrix.jpg"],
    ["#b7e4d8", "Matrix4", "https://www.awicons.com/free-icons/download/object-icons/activity-monitor-icons-by-gordon-irving/png/256/Matrix.png", "exe:eog --fullscreen ~/Documents/Code/ProxPad/matrix.jpg"],
    ["#a2d2ff", "Matrix5", "https://www.awicons.com/free-icons/download/object-icons/activity-monitor-icons-by-gordon-irving/png/256/Matrix.png", "exe:eog --fullscreen ~/Documents/Code/ProxPad/matrix.jpg"],
    ["#9ad0f6", "Matrix6", "https://www.awicons.com/free-icons/download/object-icons/activity-monitor-icons-by-gordon-irving/png/256/Matrix.png", "exe:eog --fullscreen ~/Documents/Code/ProxPad/matrix.jpg"],
    ["#c6def1", "Matrix7", "https://www.awicons.com/free-icons/download/object-icons/activity-monitor-icons-by-gordon-irving/png/256/Matrix.png", "exe:eog --fullscreen ~/Documents/Code/ProxPad/matrix.jpg"],
    ["#94e2d5", "Terminal", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/da/GNOME_Terminal_icon_2019.svg/120px-GNOME_Terminal_icon_2019.svg.png", "exe:gnome-terminal"],
    ["#a6e3a1", "Monitor", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/GNOME_System_Monitor_icon_2019.svg/120px-GNOME_System_Monitor_icon_2019.svg.png", "exe:gnome-system-monitor"],
    ["#89b4fa", "Lock PC", "bi bi-house-lock", "key:super+l"],
    ["#ffd6a5", "Matrix", "https://www.awicons.com/free-icons/download/object-icons/activity-monitor-icons-by-gordon-irving/png/256/Matrix.png", "exe:eog --fullscreen ~/Documents/Code/ProxPad/matrix.jpg"]
]

# Macro button configuration
PAGE2_MACRO_ROWS = 4
PAGE2_MACRO_COLS = 5

# Icons from https://icons.getbootstrap.com/
# Bootstrap Icons uses `bi bi-<icon-name>`
# Or you can use direct image URLs for custom icons
# Button = [color, label, icon, action]
PAGE2_MACROS = [
    ["#f5e0dc", "VSCode", "bi bi-code", "exe:code"],
    ["#f2cdcd", "AllPrintable", "bi bi-clipboard-plus", "type:!#$%&'( )*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"],
    ["#f5c2e7", "Undo", "bi bi-arrow-counterclockwise", "key:ctrl+z"],
    ["#cba6f7", "Save", "bi bi-save", "key:ctrl+s"],
    ["#f38ba8", "Screenshot", "bi bi-camera", "key:print_screen"],
    ["#eba0ac", "YouTube", "bi bi-youtube", "url:https://youtube.com"],
    ["#fab387", "Lock PC", "bi bi-lock", "key:super+l"],
    ["#f9e2af", "Alt+Tab", "bi bi-arrow-repeat", "key:alt+tab"],
    ["#a6e3a1", "Win+R", "bi bi-term", "type:random_word"],
    ["#94e2d5", "Paste", "bi bi-clipboard", "key:ctrl+v"],
    ["#89b4fa", "Calculator", "bi bi-calculator", "exe:calc"],
    ["#74c7ec", "Calculator", "bi bi-calculator-fill", "exe:calc"],
    ["#b4befe", "Calculator", "bi bi-calculator", "exe:calc"],
    ["#c6d0f5", "Calculator", "bi bi-calculator-fill", "exe:calc"],
    ["#d9e2b6", "Calculator", "bi bi-clipboard", "exe:calc"],
    ["#ffd8b8", "Calculator", "bi bi-file-earmark", "exe:calc"],
    ["#e6d7f2", "Calculator", "bi bi-hdd", "exe:calc"],
    ["#dbe7f9", "Calculator", "bi bi-cpu", "exe:calc"],
    ["#e8f6ef", "Calculator", "bi bi-gear", "exe:calc"],
    ["#ffeef8", "Calculator", "bi bi-wrench", "exe:calc"],
    ["#fff4d6", "Play/Pause", "bi bi-play-circle", "key:media_play_pause"]
]

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
# - Type text: "type:Hello World"
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
