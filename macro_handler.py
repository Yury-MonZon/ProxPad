#!/usr/bin/env python3
"""
Cross-platform macro handler for receiving UDP broadcast commands.

Handles keyboard input simulation, program execution, and system commands
across Windows and Linux platforms. Uses pynput for standard keyboard
input and uinput for Linux Super key combinations (requires sudo).

Author: ProxPad Project
Version: 2.3    
"""

import json
import platform
import socket
import subprocess
import threading
import time
import os
import logging

# Optional dependencies with graceful fallbacks
try:
    from pynput import keyboard
    from pynput.keyboard import Key, KeyCode
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    keyboard = None
    Key = None
    KeyCode = None
    pass

UINPUT_AVAILABLE = False
uinput = None
system = platform.system().lower()
if system == 'linux':
    try:
        import uinput
        UINPUT_AVAILABLE = True
    except ImportError:
        pass

if system == 'linux':
    if UINPUT_AVAILABLE and os.path.exists('/dev/uinput') and os.access('/dev/uinput', os.W_OK):
        print("[ProxPad] Using uinput for Linux key emulation (supports Super/Win combos)")
    else:
        print("[ProxPad] uinput not available or not accessible. Using pynput. WARNING: On Linux, special key combos (Win/Super) may not work without uinput.")
        if not PYNPUT_AVAILABLE:
            print("[ProxPad] ERROR: pynput not available. Please install pynput.")
elif system == 'windows':
    print("[ProxPad] Using pynput for Windows key emulation.")
    if not PYNPUT_AVAILABLE:
        print("[ProxPad] ERROR: pynput not available. Please install pynput.")
else:
    print(f"[ProxPad] Unknown OS: {system}. Key emulation may not work.")

class MacroHandler:

    def __init__(self, port=5005):
        """Initialize the macro handler.
        Args:
            port (int): UDP port to listen on (default: 5005)
        """
        self.port = port
        self.running = True
        self.system = platform.system().lower()
        
        # Setup logging with proper formatting
        self._setup_logging()
        
        # Initialize input controllers
        self.pynput_controller = None
        self.uinput_device = None
        
        # Build all maps during initialization
        if UINPUT_AVAILABLE:
            self.uinput_key_map = self._build_uinput_key_map()
            self.uinput_combo_map = self._build_uinput_combo_map()
            self.uinput_media_map = self._build_uinput_media_map()
        else:
            self.uinput_key_map = {}
            self.uinput_media_map = {}
            self.uinput_combo_map = {}
        
        if PYNPUT_AVAILABLE:
            self.pyinput_key_map = self._build_pynput_key_map()
            self.pynput_modifier_map = self._build_pynput_modifier_map()
            self.pyinput_media_map = self._build_pynput_media_map()
        else:
            self.pyinput_key_map = {}
            self.pynput_modifier_map = {}
            self.pyinput_media_map = {}
        
        self._initialize_controllers()

    def _key_hold(self):
        """Hold key for a short duration to ensure system registers it."""
        time.sleep(0.01)

    def execute_media_command_pynput(self, key_str):
        """Execute media commands using pynput keyboard controller.

        Args:
            key_str (str): Media key command string

        Returns:
            bool: True if command was executed successfully
        """
        # Try uinput first if available
        if self.uinput_device:
            # Use cached uinput media map initialized in _initialize_uinput()
            uinput_key = self.uinput_media_map.get(key_str)
            if uinput_key:
                try:
                    self.uinput_device.emit(uinput_key, 1)
                    self._key_hold()
                    self.uinput_device.emit(uinput_key, 0)
                    self.uinput_device.syn()
                    self.logger.info(f"🎵 Media key executed via uinput: {key_str}")
                    return True
                except Exception as e:
                    self.logger.error(f"❌ Media key error via uinput for '{key_str}': {e}")
                    return False

        # Fallback to pynput if available
        if self.pynput_controller:
            # Get the media key identifier from pre-built map
            media_key_id = self.pyinput_media_map.get(key_str)
            if not media_key_id:
                # Not a media key, return False silently
                return False

            # Convert string identifier to actual Key object
            try:
                media_key = getattr(Key, media_key_id, None)
                if not media_key:
                    self.logger.error(f"❌ Media key '{media_key_id}' not available in pynput")
                    return False
            except Exception as e:
                self.logger.error(f"❌ Error getting media key '{media_key_id}': {e}")
                return False

            try:
                # Use Key/KeyCode objects from pynput
                self.pynput_controller.press(media_key)
                self.pynput_controller.release(media_key)
                self.logger.info(f"🎵 Media key executed via pynput: {key_str}")
                return True
            except Exception as e:
                self.logger.error(f"❌ Media key error for '{key_str}': {e}")
                return False

        # No input method available
        return False

    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _build_uinput_key_map(self):
        """Build uinput key mapping."""
        uinput_key_map = {}
        # Basic char mappings
        for i in range(ord('a'), ord('z')+1):
            uinput_key_map[chr(i)] = getattr(uinput, f'KEY_{chr(i).upper()}', None)
        for i in range(0, 10):
            uinput_key_map[str(i)] = getattr(uinput, f'KEY_{i}', None)

        # Common special keys
        uinput_key_map.update({
            'enter': uinput.KEY_ENTER,
            'tab': uinput.KEY_TAB,
            'space': uinput.KEY_SPACE,
            'esc': uinput.KEY_ESC,
            'escape': uinput.KEY_ESC,
            'backspace': uinput.KEY_BACKSPACE,
            'delete': uinput.KEY_DELETE,
            'home': uinput.KEY_HOME,
            'end': uinput.KEY_END,
            'page_up': uinput.KEY_PAGEUP,
            'page_down': uinput.KEY_PAGEDOWN,
            'caps_lock': uinput.KEY_CAPSLOCK,
            'num_lock': uinput.KEY_NUMLOCK,
            'scroll_lock': uinput.KEY_SCROLLLOCK,
            'insert': uinput.KEY_INSERT,
            'menu': uinput.KEY_MENU,
            'pause': uinput.KEY_PAUSE,
            'print_screen': uinput.KEY_PRINT,
            'up': uinput.KEY_UP,
            'down': uinput.KEY_DOWN,
            'left': uinput.KEY_LEFT,
            'right': uinput.KEY_RIGHT,
        })

        # Punctuation and symbols
        uinput_key_map.update({
            '!': uinput.KEY_1,          # Shift+1
            '@': uinput.KEY_2,          # Shift+2
            '#': uinput.KEY_3,          # Shift+3
            '$': uinput.KEY_4,          # Shift+4
            '%': uinput.KEY_5,          # Shift+5
            '^': uinput.KEY_6,          # Shift+6
            '&': uinput.KEY_7,          # Shift+7
            '*': uinput.KEY_8,          # Shift+8
            '(': uinput.KEY_9,          # Shift+9
            ')': uinput.KEY_0,          # Shift+0
            '_': uinput.KEY_MINUS,      # Shift+-
            '+': uinput.KEY_EQUAL,      # Shift+=
            '{': uinput.KEY_LEFTBRACE,  # Shift+[
            '}': uinput.KEY_RIGHTBRACE, # Shift+]
            '|': uinput.KEY_BACKSLASH,  # Shift+\
            ':': uinput.KEY_SEMICOLON,  # Shift+;
            '"': uinput.KEY_APOSTROPHE, # Shift+'
            '<': uinput.KEY_COMMA,      # Shift+,
            '>': uinput.KEY_DOT,        # Shift+.
            '?': uinput.KEY_SLASH,      # Shift+/
            '~': uinput.KEY_GRAVE,      # Shift+`
            '-': uinput.KEY_MINUS,      # Direct
            '=': uinput.KEY_EQUAL,      # Direct
            '[': uinput.KEY_LEFTBRACE,  # Direct
            ']': uinput.KEY_RIGHTBRACE, # Direct
            '\\': uinput.KEY_BACKSLASH, # Direct
            ';': uinput.KEY_SEMICOLON,  # Direct
            "'": uinput.KEY_APOSTROPHE, # Direct
            ',': uinput.KEY_COMMA,      # Direct
            '.': uinput.KEY_DOT,        # Direct
            '/': uinput.KEY_SLASH,      # Direct
            '`': uinput.KEY_GRAVE,      # Direct
        })
        return uinput_key_map

    def _build_uinput_media_map(self):
        """Build uinput key and media mapping."""
        uinput_media_map = {}
        # Media mapping
        uinput_media_map.update({
            'play': getattr(uinput, 'KEY_PLAYPAUSE', None),
            'media_play_pause': getattr(uinput, 'KEY_PLAYPAUSE', None),
            'playpause': getattr(uinput, 'KEY_PLAYPAUSE', None),
            'next': getattr(uinput, 'KEY_NEXTSONG', None),
            'media_next': getattr(uinput, 'KEY_NEXTSONG', None),
            'next_track': getattr(uinput, 'KEY_NEXTSONG', None),
            'previous': getattr(uinput, 'KEY_PREVIOUSSONG', None),
            'prev': getattr(uinput, 'KEY_PREVIOUSSONG', None),
            'media_previous': getattr(uinput, 'KEY_PREVIOUSSONG', None),
            'prev_track': getattr(uinput, 'KEY_PREVIOUSSONG', None),
            'volume_up': getattr(uinput, 'KEY_VOLUMEUP', None),
            'vol_up': getattr(uinput, 'KEY_VOLUMEUP', None),
            'volume_down': getattr(uinput, 'KEY_VOLUMEDOWN', None),
            'vol_down': getattr(uinput, 'KEY_VOLUMEDOWN', None),
            'mute': getattr(uinput, 'KEY_MUTE', None),
            'volume_mute': getattr(uinput, 'KEY_MUTE', None),
        })
        return uinput_media_map

    def _build_uinput_combo_map(self):
        """Build uinput key map for combinations during initialization."""
        combo_map = {}
        # Modifiers
        combo_map.update({
            'ctrl': 'KEY_LEFTCTRL', 'control': 'KEY_LEFTCTRL',
            'alt': 'KEY_LEFTALT', 'alt_l': 'KEY_LEFTALT', 'alt_r': 'KEY_RIGHTALT',
            'shift': 'KEY_LEFTSHIFT', 'shift_l': 'KEY_LEFTSHIFT', 'shift_r': 'KEY_RIGHTSHIFT',
            'super': 'KEY_LEFTMETA', 'win': 'KEY_LEFTMETA', 'cmd': 'KEY_LEFTMETA',
        })
        
        # Special keys for combinations
        combo_map.update({
            'tab': 'KEY_TAB', 'enter': 'KEY_ENTER', 'esc': 'KEY_ESC', 'escape': 'KEY_ESC',
            'delete': 'KEY_DELETE', 'backspace': 'KEY_BACKSPACE', 'space': 'KEY_SPACE',
            'up': 'KEY_UP', 'down': 'KEY_DOWN', 'left': 'KEY_LEFT', 'right': 'KEY_RIGHT',
            'home': 'KEY_HOME', 'end': 'KEY_END', 
            'page_up': 'KEY_PAGEUP', 'page_down': 'KEY_PAGEDOWN',
        })
        
        # Add letters and digits
        for i in range(ord('a'), ord('z')+1):
            combo_map[chr(i)] = f'KEY_{chr(i).upper()}'
        for i in range(0, 10):
            combo_map[str(i)] = f'KEY_{i}'
        
        # Add function keys
        for i in range(1, 25):
            combo_map[f'f{i}'] = f'KEY_F{i}'
        
        return combo_map

    def _initialize_uinput(self):
        """Initialize uinput device with all needed key codes."""
        try:
            # Include all events from key map, media map, and combo map
            all_events = list(self.uinput_key_map.values()) + list(self.uinput_media_map.values())
            
            # Add modifier keys from combo map
            modifier_keys = ['KEY_LEFTCTRL', 'KEY_LEFTALT', 'KEY_RIGHTALT', 'KEY_LEFTSHIFT', 'KEY_RIGHTSHIFT', 'KEY_LEFTMETA']
            for mod_key in modifier_keys:
                mod_code = getattr(uinput, mod_key, None)
                if mod_code:
                    all_events.append(mod_code)
            
            all_events = [e for e in all_events if e is not None]  # Filter out None values
            self.uinput_device = uinput.Device(all_events, name="ProxPad Keyboard")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize uinput device: {e}")
            self.uinput_device = None
    
    def execute_program(self, exe_str):
        """Execute program directly.
        
        Args:
            exe_str (str): Program command string (e.g., "exe:calc", "calculator")
        
        Returns:
            bool: True if program was launched successfully
        """
        try:
            # Remove exe: prefix if present
            final_command = exe_str[4:] if exe_str.startswith('exe:') else exe_str
            self.logger.info(f"🚀 Launching program: {final_command}")
            process = subprocess.Popen(
                final_command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            self.logger.info(f"✅ Program launched successfully: {final_command} (PID: {process.pid})")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error launching program '{exe_str}': {e}")
    
    def execute_key_command(self, key_str):
        """Execute keyboard command - supports single keys and combinations.
        
        Args:
            key_str (str): Key command string (e.g., "key:ctrl+c", "a", "f1")
            
        Returns:
            bool: True if command was executed successfully
        """
        if not self.uinput_device and not self.pynput_controller:
            self.logger.error("❌ No input device available - key commands disabled")
            return False
            
        # Normalize key string by removing prefixes
        normalized_key = self._normalize_key_string(key_str)
        
        self.logger.debug(f"Processing key command: {normalized_key}")
        
        try:
            if '+' in normalized_key:
                return self._execute_key_combination(normalized_key)
            else:
                return self._execute_single_key(normalized_key)
                
        except Exception as e:
            self.logger.error(f"❌ Key execution error for '{key_str}': {e}")
            return False
    
    def _normalize_key_string(self, key_str):
        """Normalize key string by removing common prefixes and map synonyms."""
        normalized = key_str
        # Remove common prefixes
        prefixes = ['key:', 'Key.']
        for prefix in prefixes:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
                break
        # Map synonyms for OS modifier keys
        synonyms = {
            'win': 'cmd', 'super': 'cmd', 'cmd': 'cmd',
            'win_l': 'cmd', 'super_l': 'cmd', 'cmd_l': 'cmd',
            'win_r': 'cmd', 'super_r': 'cmd', 'cmd_r': 'cmd',
        }
        norm_lower = normalized.lower()
        if norm_lower in synonyms:
            normalized = 'cmd'
        return normalized
    
    def _execute_single_key(self, key_str):
        """Execute a single key press.
        
        Args:
            key_str (str): Single key to press
        
        Returns:
            bool: True if key was pressed successfully
        """
        # Try media commands first
        if self.execute_media_command_pynput(key_str):
            return True
        # Normalize and map key
        norm_key_str = key_str.lower()
        if norm_key_str in ('win', 'super', 'cmd'):
            norm_key_str = 'cmd'
        uinput_key = None
        if self.uinput_device:
            # Always resolve Win/Super/Cmd to KEY_LEFTMETA for uinput
            if norm_key_str == 'cmd':
                uinput_key = getattr(uinput, 'KEY_LEFTMETA', None)
            else:
                uinput_key = self._get_uinput_key_code(norm_key_str)
        if uinput_key:
            self.uinput_device.emit(uinput_key, 1)
            self._key_hold()
            self.uinput_device.emit(uinput_key, 0)
            self.uinput_device.syn()
            self.logger.info(f"✅ uinput key pressed: {key_str}")
            return True
        # Fallback to pynput
        key = self.pyinput_key_map.get(key_str)
        if key:
            self._press_and_release_key(key)
            self.logger.info(f"✅ pynput key pressed: {key_str}")
            return True
        if len(key_str) == 1:
            self._press_and_release_key(key_str)
            self.logger.info(f"✅ Character pressed: {key_str}")
            return True
        self.logger.warning(f"⚠️ Unknown key: {key_str}")
        return False
    
    def _build_pynput_key_map(self):
        """Get comprehensive key mapping dictionary, including synonyms for OS modifier keys."""
        map = {
            # Modifier keys
            'alt': Key.alt, 'alt_l': Key.alt_l, 'alt_r': Key.alt_r, 'alt_gr': Key.alt_gr,
            'ctrl': Key.ctrl, 'ctrl_l': Key.ctrl_l, 'ctrl_r': Key.ctrl_r,
            'shift': Key.shift, 'shift_l': Key.shift_l, 'shift_r': Key.shift_r,
            'cmd': Key.cmd, 'cmd_l': Key.cmd_l, 'cmd_r': Key.cmd_r,
            # Synonyms for OS modifier keys
            'win': Key.cmd, 'super': Key.cmd,
            'win_l': Key.cmd_l, 'super_l': Key.cmd_l,
            'win_r': Key.cmd_r, 'super_r': Key.cmd_r,
            # Special keys
            'backspace': Key.backspace, 'delete': Key.delete, 'enter': Key.enter,
            'esc': Key.esc, 'escape': Key.esc, 'tab': Key.tab, 'space': Key.space,
            'caps_lock': Key.caps_lock, 'num_lock': Key.num_lock, 'scroll_lock': Key.scroll_lock,
            'insert': Key.insert, 'home': Key.home, 'end': Key.end,
            'page_up': Key.page_up, 'page_down': Key.page_down,
            'menu': Key.menu, 'pause': Key.pause, 'print_screen': Key.print_screen,
            # Arrow keys
            'up': Key.up, 'down': Key.down, 'left': Key.left, 'right': Key.right,
            # Function keys
            'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4, 'f5': Key.f5, 'f6': Key.f6,
            'f7': Key.f7, 'f8': Key.f8, 'f9': Key.f9, 'f10': Key.f10, 'f11': Key.f11, 'f12': Key.f12,
            'f13': Key.f13, 'f14': Key.f14, 'f15': Key.f15, 'f16': Key.f16,
            'f17': Key.f17, 'f18': Key.f18, 'f19': Key.f19, 'f20': Key.f20,
            'f21': getattr(Key, 'f21', None), 'f22': getattr(Key, 'f22', None),
            'f23': getattr(Key, 'f23', None), 'f24': getattr(Key, 'f24', None),
            # Media keys
            'media_play_pause': Key.media_play_pause, 'media_volume_mute': Key.media_volume_mute,
            'media_volume_down': Key.media_volume_down, 'media_volume_up': Key.media_volume_up,
            'media_previous': Key.media_previous, 'media_next': Key.media_next,
        }
        return map
    
    def _press_and_release_key(self, key):
        """Press and release a key with proper timing, always preferring uinput if available."""
        # Use uinput if available and initialized
        if self.uinput_device:
            uinput_key = None
            kstr = None
            if isinstance(key, str):
                kstr = key
            elif hasattr(key, 'name') and key.name:
                kstr = key.name
            elif hasattr(key, 'char') and key.char:
                kstr = key.char
            if kstr:
                kstr = kstr.lower()
                # Always resolve Win/Super/Cmd to KEY_LEFTMETA for uinput
                if kstr in ('win', 'super', 'cmd', 'leftmeta'):
                    uinput_key = getattr(uinput, 'KEY_LEFTMETA', None)
                else:
                    uinput_key = self._get_uinput_key_code(kstr)
            if uinput_key:
                self.uinput_device.emit(uinput_key, 1)
                self._key_hold()
                self.uinput_device.emit(uinput_key, 0)
                self.uinput_device.syn()
                return
        # Fallback to pynput
        try:
            from pynput.keyboard import KeyCode
            if isinstance(key, str) and len(key) == 1:
                kc = KeyCode.from_char(key)
                self.pynput_controller.press(kc)
                self._key_hold()
                self.pynput_controller.release(kc)
                return
        except Exception:
            pass
        self.pynput_controller.press(key)
        self._key_hold()
        self.pynput_controller.release(key)
    
    def _execute_key_combination(self, key_str):
        """Execute key combination (e.g., ctrl+c, alt+tab, super+l, alt+tab) via uinput if available."""
        keys = [k.strip() for k in key_str.split('+')]
        self.logger.debug(f"Parsing key combination: {key_str} -> {keys}")
        
        if self.uinput_device:
            keys_to_press = self._parse_key_combination(keys, True)
            if not keys_to_press:
                self.logger.warning(f"⚠️ No valid keys found in combination: {key_str}")
                return False
            self.logger.debug(f"Executing key combination: {[str(k) for k in keys_to_press]}")
            return self._execute_combination_uinput(keys_to_press)

        # Otherwise, use pynput
        if self.pynput_controller:
            keys_to_press = self._parse_key_combination(keys, False)
            return self._execute_standard_combo_pynput(keys_to_press, key_str)
        return False

    def _execute_combination_uinput(self, keys_to_press):
        """Execute any key combination using uinput (modifiers + key)."""
        # Use pre-built combo map from initialization
        key_map = self.uinput_combo_map

        # Convert keys to uinput codes
        uinput_keys = []
        for k in keys_to_press:
            # k is now a string since we parsed with use_uinput=True
            kstr = str(k).lower().strip()
            self.logger.debug(f"Processing key string: '{kstr}'")
            
            code_name = key_map.get(kstr)
            # Use direct getattr instead of cached map for reliability
            code = getattr(uinput, code_name, None) if code_name else None
            if code:
                uinput_keys.append(code)
                self.logger.debug(f"Mapped {kstr} to uinput code: {code}")
            else:
                # Try direct map for single chars (letters/digits/etc.)
                code = self._get_uinput_key_code(kstr)
                if code:
                    uinput_keys.append(code)
                    self.logger.debug(f"Used direct map for {kstr}: {code}")
                else:
                    self.logger.warning(f"⚠️ Unknown uinput key for combo: {kstr}")
                    return False

        # Press all modifiers except last key
        try:
            for code in uinput_keys[:-1]:
                self.uinput_device.emit(code, 1)
                self.uinput_device.syn()
                self._key_hold()
            # Press and release final key
            self._key_hold()
            self.uinput_device.emit(uinput_keys[-1], 1)
            self.uinput_device.syn()
            self._key_hold()
            self.uinput_device.emit(uinput_keys[-1], 0)
            self.uinput_device.syn()
            self._key_hold()
            # Release all modifiers in reverse
            for code in reversed(uinput_keys[:-1]):
                self.uinput_device.emit(code, 0)
                self.uinput_device.syn()
                self._key_hold()
            self.uinput_device.syn()
            self.logger.info(f"✅ uinput combo executed: {keys_to_press}")
            return True
        except Exception as e:
            self.logger.error(f"❌ uinput combo error: {e}")
            return False
    
    def _parse_key_combination(self, keys, use_uinput=False):
        """Parse key combination into executable key objects or strings.
        
        Args:
            keys (list): List of key strings
            use_uinput (bool): Whether to return strings for uinput or Key objects for pynput
            
        Returns:
            list: List of key objects (pynput) or strings (uinput) to press
        """
        keys_to_press = []
        for key in keys:
            if use_uinput:
                # For uinput, return normalized strings
                if key in self.pynput_modifier_map:
                    # Map to uinput modifier names
                    uinput_modifiers = {
                        'ctrl': 'ctrl', 'control': 'ctrl',
                        'alt': 'alt',
                        'shift': 'shift',
                        'cmd': 'super', 'win': 'super', 'super': 'super',
                    }
                    mapped_key = uinput_modifiers.get(key, key)
                    keys_to_press.append(mapped_key)
                    self.logger.debug(f"Mapped modifier '{key}' -> '{mapped_key}' for uinput")
                elif len(key) == 1:
                    # Single characters stay as strings
                    keys_to_press.append(key.lower())
                    self.logger.debug(f"Added character key for uinput: '{key}'")
                else:
                    # Special keys
                    special_key = self._get_special_combination_key_uinput(key)
                    if special_key:
                        keys_to_press.append(special_key)
                        self.logger.debug(f"Mapped special key '{key}' -> '{special_key}' for uinput")
                    else:
                        self.logger.warning(f"⚠️ Unknown key in combination: {key}")
                        return []
            else:
                # For pynput, return Key objects
                if key in self.pynput_modifier_map:
                    mapped_key = self.pynput_modifier_map[key]
                    keys_to_press.append(mapped_key)
                    self.logger.debug(f"Mapped modifier '{key}' -> {mapped_key}")
                elif len(key) == 1:
                    # Convert single characters to KeyCode for pynput compatibility
                    try:
                        from pynput.keyboard import KeyCode
                        keys_to_press.append(KeyCode.from_char(key))
                        self.logger.debug(f"Added character key (KeyCode): '{key}'")
                    except Exception:
                        keys_to_press.append(key)
                        self.logger.debug(f"Added character key: '{key}'")
                else:
                    # Try to find it in the special key map
                    special_key = self._get_special_combination_key_pynput(key)
                    if special_key:
                        keys_to_press.append(special_key)
                        self.logger.debug(f"Mapped special key '{key}' -> {special_key}")
                    else:
                        self.logger.warning(f"⚠️ Unknown key in combination: {key}")
                        return []
        return keys_to_press

    def _build_pynput_modifier_map(self):
        """Get modifier key map.
        
        Returns:
            dict: map of modifier names to Key objects
        """
        return {
            # Control variations
            'ctrl': Key.ctrl, 'control': Key.ctrl,
            # Alt variations
            'alt': Key.alt,
            # Shift
            'shift': Key.shift,
            # Super/Windows/Cmd variations
            'cmd': Key.cmd, 'win': Key.cmd, 'super': Key.cmd,
        }
    
    def _execute_standard_combo_pynput(self, keys_to_press, key_str):
        """Execute standard key combo"""
        
        # Special-case: On Windows, Win+L is handled by the OS and may not be triggered
        # by simulated key injection reliably. Use native LockWorkStation API instead.
        if self.system == 'windows':
            norm = key_str.lower()
            if norm in ('win+l', 'super+l', 'cmd+l'):
                return self._lock_win_pc()

        if len(keys_to_press) > 1:
            return self._execute_multi_key_combo_pynput(keys_to_press)
        else:
            return self._execute_single_key_from_combo_pynput(keys_to_press[0], key_str)

    def _lock_win_pc(self):
        """Lock the Windows workstation using native API.

        Returns:
            bool: True if the call succeeded
        """
        try:
            if self.system != 'windows':
                self.logger.warning("⚠️ _lock_win_pc called on non-Windows system")
                return False
            import ctypes
            res = ctypes.windll.user32.LockWorkStation()
            if res:
                self.logger.info("🔒 PC Locked via LockWorkStation()")
                return True
            else:
                self.logger.warning("⚠️ LockWorkStation returned False")
                return False
        except Exception as e:
            self.logger.error(f"❌ Failed to lock workstation: {e}")
            return False
    
    def _execute_multi_key_combo_pynput(self, keys_to_press):
        """Execute multi-key combination using context managers.
        
        Args:
            keys_to_press (list): List of keys to press
            
        Returns:
            bool: True if executed successfully
        """
        modifiers = keys_to_press[:-1]  # All but the last key
        final_key = keys_to_press[-1]   # The last key
        
        try:
            # Use context managers for proper modifier handling
            contexts = []
            for modifier in modifiers:
                self.logger.debug(f"Preparing modifier: {modifier}")
                contexts.append(self.pynput_controller.pressed(modifier))
            
            # Enter all contexts
            for context in contexts:
                context.__enter__()
            
            # Press and release the final key
            self.pynput_controller.press(final_key)
            self._key_hold()
            self.pynput_controller.release(final_key)
            
            # Exit all contexts in reverse order
            for context in reversed(contexts):
                context.__exit__(None, None, None)
            
            self.logger.info("✅ Key combination executed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in key combination: {e}")
            return False

    def _execute_single_key_from_combo_pynput(self, key, key_str):
        """Execute single key from what was parsed as a combination.
        
        Args:
            key: Single key to press
            key_str (str): Original key string for logging
            
        Returns:
            bool: True if executed successfully
        """
        try:
            self._press_and_release_key(key)
            self.logger.info(f"✅ Single key executed: {key_str}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error executing single key '{key_str}': {e}")
            return False
    
    def _get_special_combination_key_uinput(self, key_str):
        """Get special key string for use in uinput combinations.
        
        Args:
            key_str (str): Key name string
            
        Returns:
            str or None if not found
        """
        special_keys = {
            'backspace': 'backspace', 'delete': 'delete', 'enter': 'enter',
            'esc': 'esc', 'escape': 'esc', 'tab': 'tab', 'space': 'space',
            'up': 'up', 'down': 'down', 'left': 'left', 'right': 'right',
            'home': 'home', 'end': 'end', 'page_up': 'page_up', 'page_down': 'page_down',
            'f1': 'f1', 'f2': 'f2', 'f3': 'f3', 'f4': 'f4', 'f5': 'f5', 'f6': 'f6',
            'f7': 'f7', 'f8': 'f8', 'f9': 'f9', 'f10': 'f10', 'f11': 'f11', 'f12': 'f12',
        }
        return special_keys.get(key_str)
    
    def _get_special_combination_key_pynput(self, key_str):
        """Get special key object for use in pynput combinations.
        
        Args:
            key_str (str): Key name string
            
        Returns:
            Key object or None if not found
        """
        special_keys = {
            'backspace': Key.backspace, 'delete': Key.delete, 'enter': Key.enter,
            'esc': Key.esc, 'escape': Key.esc, 'tab': Key.tab, 'space': Key.space,
            'up': Key.up, 'down': Key.down, 'left': Key.left, 'right': Key.right,
            'home': Key.home, 'end': Key.end, 'page_up': Key.page_up, 'page_down': Key.page_down,
            'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4, 'f5': Key.f5, 'f6': Key.f6,
            'f7': Key.f7, 'f8': Key.f8, 'f9': Key.f9, 'f10': Key.f10, 'f11': Key.f11, 'f12': Key.f12,
        }
        return special_keys.get(key_str)
    
    def _get_uinput_key_code(self, key_str):
        """Get uinput key code for a character or special key."""
        # Use cached map if available, otherwise return None
        return getattr(self, 'uinput_key_map', {}).get(key_str)

    def handle_command(self, data):
        """Process received UDP command, supporting multi-step macros with robust parsing."""
        import webbrowser
        action = data.get('action', '')

        def split_actions(s):
            """
            Split macro string into actions at semicolons followed by optional whitespace and a valid keyword.
            E.g. 'type:abc;def; key:enter' => ['type:abc;def', 'key:enter']
            """
            import re
            keywords = ('key:', 'type:', 'exe:', 'url:', 'delay:')
            # Build regex: semicolon, optional whitespace, then keyword
            pattern = r';\s*(?=' + '|'.join(re.escape(kw) for kw in keywords) + ')'
            parts = re.split(pattern, s)
            return [x.strip() for x in parts if x.strip()]

        actions = split_actions(action)
        success = True
        for act in actions:
            if act.startswith('delay:'):
                try:
                    delay_val = float(act[6:])
                    self.logger.debug(f"Delay: {delay_val} sec")
                    time.sleep(delay_val)
                    ok = True
                except Exception as e:
                    self.logger.error(f"❌ Error in delay: {e}")
                    ok = False
            elif act.startswith('key:'):
                ok = self.execute_key_command(act)
            elif act.startswith('type:'):
                text = act[5:]
                self.logger.debug(f"Typing: {text}")
                ok = self.type_text(text)
            elif act.startswith('exe:'):
                self.logger.debug(f"Executing program: {act[5:]}")
                ok = self.execute_program(act)
            elif act.startswith('url:'):
                url = act[4:]
                self.logger.debug(f"Opening URL: {url}")
                try:
                    webbrowser.open(url)
                    ok = True
                except Exception as e:
                    self.logger.error(f"❌ Error opening URL '{url}': {e}")
                    ok = False
            else:
                self.logger.warning(f"⚠️ Unknown action format: {act}")
                ok = False
            success = success and ok
            # Only add default delay if not a delay: action
            if not act.startswith('delay:'):
                self._key_hold()
        return success
            
    def type_text(self, text):
        """Type a string sequentially using uinput or pynput, handling shift for uppercase and symbols."""
        try:
            for char in text:
                # Use uinput if available
                if self.uinput_device:
                    keymap = getattr(self, 'uinput_key_map', None)
                    
                    # Handle uppercase letters
                    if 'A' <= char <= 'Z':
                        # Press shift, then the lowercase letter
                        self.uinput_device.emit(uinput.KEY_LEFTSHIFT, 1)
                        self._key_hold()
                        key_code = keymap.get(char.lower()) if keymap else None
                        if key_code:
                            self.uinput_device.emit(key_code, 1)
                            self._key_hold()
                            self.uinput_device.emit(key_code, 0)
                        self.uinput_device.emit(uinput.KEY_LEFTSHIFT, 0)
                        self.uinput_device.syn()
                        self._key_hold()
                        continue
                    
                    # Handle lowercase letters and numbers
                    if ('a' <= char <= 'z') or ('0' <= char <= '9'):
                        key_code = keymap.get(char) if keymap else None
                        if key_code:
                            self.uinput_device.emit(key_code, 1)
                            self._key_hold()
                            self.uinput_device.emit(key_code, 0)
                            self.uinput_device.syn()
                            self._key_hold()
                        continue
                    
                    # Handle symbols that require shift
                    shift_symbols = {
                        '!': uinput.KEY_1, '@': uinput.KEY_2, '#': uinput.KEY_3, '$': uinput.KEY_4,
                        '%': uinput.KEY_5, '^': uinput.KEY_6, '&': uinput.KEY_7, '*': uinput.KEY_8,
                        '(': uinput.KEY_9, ')': uinput.KEY_0, '_': uinput.KEY_MINUS, '+': uinput.KEY_EQUAL,
                        '{': uinput.KEY_LEFTBRACE, '}': uinput.KEY_RIGHTBRACE, '|': uinput.KEY_BACKSLASH,
                        ':': uinput.KEY_SEMICOLON, '"': uinput.KEY_APOSTROPHE, '<': uinput.KEY_COMMA,
                        '>': uinput.KEY_DOT, '?': uinput.KEY_SLASH, '~': uinput.KEY_GRAVE
                    }
                    
                    if char in shift_symbols:
                        self.uinput_device.emit(uinput.KEY_LEFTSHIFT, 1)
                        self._key_hold()
                        self.uinput_device.emit(shift_symbols[char], 1)
                        self._key_hold()
                        self.uinput_device.emit(shift_symbols[char], 0)
                        self.uinput_device.emit(uinput.KEY_LEFTSHIFT, 0)
                        self.uinput_device.syn()
                        self._key_hold()
                        continue
                    
                    # Handle direct symbols (no shift needed)
                    direct_symbols = {
                        '-': uinput.KEY_MINUS, '=': uinput.KEY_EQUAL, '[': uinput.KEY_LEFTBRACE,
                        ']': uinput.KEY_RIGHTBRACE, '\\': uinput.KEY_BACKSLASH, ';': uinput.KEY_SEMICOLON,
                        "'": uinput.KEY_APOSTROPHE, ',': uinput.KEY_COMMA, '.': uinput.KEY_DOT,
                        '/': uinput.KEY_SLASH, '`': uinput.KEY_GRAVE, ' ': uinput.KEY_SPACE
                    }
                    
                    if char in direct_symbols:
                        self.uinput_device.emit(direct_symbols[char], 1)
                        self._key_hold()
                        self.uinput_device.emit(direct_symbols[char], 0)
                        self.uinput_device.syn()
                        self._key_hold()
                        continue
                    
                    # Handle space separately
                    if char == ' ':
                        self.uinput_device.emit(uinput.KEY_SPACE, 1)
                        self._key_hold()
                        self.uinput_device.emit(uinput.KEY_SPACE, 0)
                        self.uinput_device.syn()
                        self._key_hold()
                        continue
                    
                    # If we can't find the character, try fallback
                    self.logger.warning(f"⚠️ Unknown character for uinput: '{char}'")
                    continue

                # Fallback to pynput
                if self.pynput_controller:
                    try:
                        from pynput.keyboard import KeyCode
                        kc = KeyCode.from_char(char)
                        self.pynput_controller.press(kc)
                        self._key_hold()
                        self.pynput_controller.release(kc)
                    except Exception:
                        # Try KeyCode for symbols that fail
                        try:
                            from pynput.keyboard import KeyCode
                            keycode = KeyCode.from_char(char)
                            self.pynput_controller.press(keycode)
                            self._key_hold()
                            self.pynput_controller.release(keycode)
                        except Exception:
                            self.logger.warning(f"⚠️ Could not type symbol: {char}")

            self.logger.info(f"✅ Typed: {text}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error typing '{text}': {e}")
            return False
    
    def listen_for_commands(self):
        """Listen for UDP broadcast commands"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', self.port))
            
            self.logger.info(f"Listening for commands on port {self.port}")
            self.logger.info("Supported commands:")
            self.logger.info("  🎵 Media: key:play, key:next, key:previous, key:volume_up, key:volume_down, key:mute")
            self.logger.info("  ⌨️ Keys: key:a-z, key:0-9, key:f1-f20, key:enter, key:space, key:tab, etc.")
            self.logger.info("  🔣 Combos: key:ctrl+c, key:alt+tab, key:shift+f10, key:ctrl+alt+delete")
            self.logger.info("  🔤 Text: type:Hello World!, type:password123, etc.")
            self.logger.info("  ⏳ Delay: delay:0.5 (seconds)")
            self.logger.info("  🏃 Navigation: key:up, key:down, key:left, key:right, key:home, key:end")
            self.logger.info("  🚀 Programs: exe:calc, exe:firefox, exe:cmd, etc.")
            self.logger.info("  💡 Examples: key:ctrl+s, key:alt+f4, key:win+r, key:f5, key:delete")
            
            while self.running:
                try:
                    data, addr = sock.recvfrom(1024)
                    command = json.loads(data.decode('utf-8'))
                    self.logger.debug(f"Command from {addr[0]}: {command}")
                    self.handle_command(command)
                except json.JSONDecodeError:
                    self.logger.error("⚠️ Invalid JSON received")
                except Exception as e:
                    self.logger.error(f"❌ Error receiving command: {e}")
                    
        except Exception as e:
            self.logger.error(f"❌ Error setting up UDP listener: {e}")
        finally:
            if 'sock' in locals():
                sock.close()
                self.logger.info("🔌 UDP socket closed")
    
    def start(self):
        """Start the macro handler service."""
        self.logger.info("🚀 Starting MacroHandler service...")
        
        # Start UDP listener in background thread
        listener_thread = threading.Thread(
            target=self.listen_for_commands, 
            name="UDP-Listener",
            daemon=True
        )
        listener_thread.start()
        self.logger.info("🎧 UDP listener thread started")
        
        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("🛑 Shutdown signal received")
            self.running = False
            self.logger.info("✅ MacroHandler stopped gracefully")

    def _initialize_controllers(self):
        """Initialize keyboard and uinput controllers."""
        if self.system == 'windows':
            # Always use pynput on Windows
            if PYNPUT_AVAILABLE:
                self.pynput_controller = keyboard.Controller()
                self.logger.info("✅ pynput keyboard controller initialized for Windows")
            else:
                self.logger.warning("⚠️ pynput not available - keyboard functionality disabled on Windows")
        elif self.system == 'linux':
            # Try uinput first on Linux
            if UINPUT_AVAILABLE:
                try:
                    self._initialize_uinput()
                    if self.uinput_device:
                        self.logger.info("✅ uinput device initialized for Linux")
                        return  # Don't initialize pynput if uinput succeeds
                except Exception as e:
                    self.logger.warning(f"❌ uinput initialization failed on Linux: {e}")
            # If uinput failed or not available, try pynput
            if PYNPUT_AVAILABLE:
                self.pynput_controller = keyboard.Controller()
                self.logger.info("✅ pynput keyboard controller initialized on Linux")
            else:
                self.logger.warning("⚠️ pynput not available - keyboard functionality disabled on Linux")
        else:
            self.logger.warning(f"❌ Unknown OS: {self.system}. Key emulation will not work.")

    def _build_pynput_media_map(self):
        """Get media key map dictionary."""
        return {
            'play': 'media_play_pause',
            'media_play_pause': 'media_play_pause',
            'playpause': 'media_play_pause',
            'next': 'media_next',
            'media_next': 'media_next',
            'next_track': 'media_next',
            'previous': 'media_previous',
            'prev': 'media_previous',
            'media_previous': 'media_previous',
            'prev_track': 'media_previous',
            'volume_up': 'media_volume_up',
            'vol_up': 'media_volume_up',
            'volume_down': 'media_volume_down',
            'vol_down': 'media_volume_down',
            'mute': 'media_volume_mute',
            'volume_mute': 'media_volume_mute',
        }

def main():
    """Main entry point for the macro handler."""
    try:
        handler = MacroHandler()
        handler.start()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())