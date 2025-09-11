# config.py

PROXMOX_HOST = "192.168.1.123"
PROXMOX_USER = "root@pam"
PROXMOX_TOKEN_ID = "ProxPad"
PROXMOX_TOKEN_SECRET = ""
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

# Enable vibration feedback on button press (if supported by hardware)
VIBRATION = True  
VIBRATION_MS = 30  # Vibration duration in milliseconds

# Time in minutes to wait before locking the screen after sending the lock command
SCREENSAVER = 60 # In minutes, set to 0 to disable
SCREENSAVER_24H = True # If True, use 24-hour format in the screensaver clock
SCREENSAVER_SECONDS = False # If True, show seconds in the screensaver clock
SCREENSAVER_COLOR = "#ffffffff"  # Color of the clock text in the screensaver
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
    ["#f5e0dc", "VSCode", "https://dl.flathub.org/media/com/visualstudio/code/010f3e47b4a5d6ceacfef95267b079a8/icons/128x128/com.visualstudio.code.png", "exe:code"],
    ["#f2cdcd", "TextEditor", "https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/GNOME_Text_Editor_Icon.svg/120px-GNOME_Text_Editor_Icon.svg.png", "exe:gnome-text-editor"],
    ["#fff4d6", "OrcaSlicer", "https://orcaslicers.com/wp-content/uploads/2024/12/orca.webp", "exe:~/Documents/3D_Printer/OrcaSlicer/run_me.sh"],
    ["#f5c2e7", "Calculator", "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/GNOME_Calculator_icon_2020.svg/120px-GNOME_Calculator_icon_2020.svg.png", "exe:gnome-calculator"],    
    ["#ffd6a5", "Gnote", "https://dl.flathub.org/media/org/gnome/Gnote/dca870ae6f603979b447056added4351/icons/128x128/org.gnome.Gnote.png", "exe:flatpak run org.gnome.Gnote"],
    
    ["#ffe5b4", "Screenshot", "bi bi-camera", "key:print_screen"],
    ["#d3f6e5", "FileZilla", "https://dl.flathub.org/media/org/filezillaproject/Filezilla/62055f94666ea8362cdaa170895f65f9/icons/128x128/org.filezillaproject.Filezilla.png", "exe:flatpak run org.filezillaproject.Filezilla"],
    ["#bde0fe", "AnyDesk", "https://dl.flathub.org/media/com/anydesk/Anydesk.desktop/8fc71f2bca80e319ff2c00cb3c4fa008/icons/128x128/com.anydesk.Anydesk.desktop.png", "exe: flatpak run com.anydesk.Anydesk"],
    ["#c6f6dd", "NoMachine", "https://dl.flathub.org/media/com/nomachine/nxplayer/5326e00b335dec3d33b82abbde961789/icons/128x128/com.nomachine.nxplayer.png", "exe:flatpak run com.nomachine.nxplayer"],
    ["#d0f0f2", "Parsec", "https://dl.flathub.org/media/com/parsecgaming/parsec/22a654406fc9c48c5935415a0d5b6cc4/icons/128x128/com.parsecgaming.parsec.png", "exe:flatpak run com.parsecgaming.parsec"],
    
    ["#b7d6ff", "Resolve", "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/DaVinci_Resolve_Studio.png/120px-DaVinci_Resolve_Studio.png", "exe:/opt/resolve/bin/resolve %u"],
    ["#cdb4db", "OBS", "https://dl.flathub.org/media/com/obsproject/Studio/66bdcc448bac3c60f95fd550a3018436/icons/128x128/com.obsproject.Studio.png", "exe:flatpak run com.obsproject.Studio"],
    ["#e9d8a6", "MPV", "https://dl.flathub.org/media/io/mpv/Mpv/dbc3d9b10433853e6d47894eea85edda/icons/128x128/io.mpv.Mpv.png", "exe:flatpak run io.mpv.Mpv"],
    ["#e6e7e9", "YT Music", "https://upload.wikimedia.org/wikipedia/commons/thumb/archive/6/6a/20230802004651%21Youtube_Music_icon.svg/120px-Youtube_Music_icon.svg.png", "url:https://music.youtube.com"],
    ["#ffd6e0", "YouTube", "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fd/YouTube_full-color_icon_%282024%29.svg/250px-YouTube_full-color_icon_%282024%29.svg.png", "url:https://youtube.com"],
    
    ["#cba6f7", "EasySSH", "https://dl.flathub.org/media/com/github/muriloventuroso.easyssh/3f48db4f2c5ea9f7c1843ac759ab1e99/icons/128x128@2/com.github.muriloventuroso.easyssh.png", "exe:flatpak run com.github.muriloventuroso.easyssh"],
    ["#f7c5c5", "Terminal", "https://upload.wikimedia.org/wikipedia/commons/thumb/d/da/GNOME_Terminal_icon_2019.svg/120px-GNOME_Terminal_icon_2019.svg.png", "exe:gnome-terminal"],
    ["#e8d7ff", "Monitor", "https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/GNOME_System_Monitor_icon_2019.svg/120px-GNOME_System_Monitor_icon_2019.svg.png", "exe:gnome-system-monitor"],
    ["#f3f0ff", "Lock PC", "bi bi-house-lock", "key:super+l"],
    ["#e2f0d9", "Matrix", "https://www.awicons.com/free-icons/download/object-icons/activity-monitor-icons-by-gordon-irving/png/256/Matrix.png", "exe:eog --fullscreen ~/Documents/Code/ProxPad/matrix.jpg"]
]

# Macro button configuration
PAGE2_MACRO_ROWS = 4
PAGE2_MACRO_COLS = 5

# Icons from https://icons.getbootstrap.com/
# Bootstrap Icons uses `bi bi-<icon-name>`
# Or you can use direct image URLs for custom icons
# Button = [color, label, icon, action]
PAGE2_MACROS = [
    ["#f2cdcd", "VSCode", "bi bi-code", "exe:code"],
    ["#cba6f7", "AllPrintable", "bi bi-clipboard-plus", "type:!#$%&'( )*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"],
    ["#bde0fe", "Undo", "bi bi-arrow-counterclockwise", "key:ctrl+z"],
    ["#f5e0dc", "Save", "bi bi-save", "key:ctrl+s"],
    ["#ffd6a5", "Screenshot", "bi bi-camera", "key:print_screen"],
    ["#c6f6dd", "YouTube", "bi bi-youtube", "url:https://youtube.com"],
    ["#ffe5b4", "Lock PC", "bi bi-lock", "key:win+l"],
    ["#f5c2e7", "Alt+Tab", "bi bi-arrow-repeat", "key:alt+tab"],
    ["#b7d6ff", "Win+R", "bi bi-term", "key:win+r"],
    ["#d0f0f2", "Paste", "bi bi-clipboard", "key:ctrl+v"],
    ["#cdb4db", "Calculator", "bi bi-calculator", "exe:calc"],
    ["#e9d8a6", "Calculator", "bi bi-calculator-fill", "exe:calc"],
    ["#d3f6e5", "Calculator", "bi bi-calculator", "exe:calc"],
    ["#fff4d6", "Calculator", "bi bi-calculator-fill", "exe:calc"],
    ["#f7c5c5", "Calculator", "bi bi-clipboard", "exe:calc"],
    ["#e8d7ff", "Calculator", "bi bi-file-earmark", "exe:calc"],
    ["#f3f0ff", "Calculator", "bi bi-hdd", "exe:calc"],
    ["#e2f0d9", "Calculator", "bi bi-cpu", "exe:calc"],
    ["#ffd6e0", "Calculator", "bi bi-gear", "exe:calc"],
    ["#fbf1d6", "Calculator", "bi bi-wrench", "exe:calc"],
    ["#90e0ef", "Play/Pause", "bi bi-play-circle", "key:media_play_pause"]
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
