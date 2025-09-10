#!/usr/bin/env python3
"""
Cross-platform macro handler for receiving UDP broadcast commands.

Handles keyboard input simulation, program execution, and system commands
across Windows and Linux platforms. Uses pynput for standard keyboard
input and uinput for Linux Super key combinations (requires sudo).

Author: ProxPad Project
Version: 2.1
"""

import json
import logging
import platform
import socket
import subprocess
import threading
import time
import os

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
    """Cross-platform macro handler for UDP broadcast commands."""
    
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
        self.keyboard_controller = None
        self.uinput_device = None
        
        self._initialize_controllers()
        # Compute key mappings once
        self.key_mapping = self._get_key_mapping()
        self.modifier_mapping = self._get_modifier_mapping()
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _initialize_controllers(self):
        """Initialize keyboard and uinput controllers."""
        # Initialize pynput keyboard controller
        if PYNPUT_AVAILABLE:
            self.keyboard_controller = keyboard.Controller()
            self.logger.info("✅ pynput keyboard controller initialized")
        else:
            self.logger.warning("⚠️  pynput not available - keyboard functionality disabled")
        
        # Initialize uinput for Linux Super key combinations
        if UINPUT_AVAILABLE and self.system == 'linux':
            self._initialize_uinput()
        
        self.logger.info(f"MacroHandler initialized for {self.system} platform")
    
    def _initialize_uinput(self):
        """Initialize uinput device with all needed key codes (explicit list)."""
        try:
            # Explicitly list all common keys, modifiers, special, and media keys
            uinput_keys = []
            # Modifiers
            uinput_keys += [
                uinput.KEY_LEFTCTRL, uinput.KEY_RIGHTCTRL,
                uinput.KEY_LEFTALT, uinput.KEY_RIGHTALT,
                uinput.KEY_LEFTSHIFT, uinput.KEY_RIGHTSHIFT,
                uinput.KEY_LEFTMETA, uinput.KEY_RIGHTMETA,
            ]
            # Letters
            uinput_keys += [getattr(uinput, f'KEY_{chr(i).upper()}') for i in range(ord('a'), ord('z')+1)]
            # Digits
            uinput_keys += [getattr(uinput, f'KEY_{i}') for i in range(0, 10)]
            # Function keys
            uinput_keys += [getattr(uinput, f'KEY_F{i}') for i in range(1, 21)]
            # Arrow keys
            uinput_keys += [uinput.KEY_UP, uinput.KEY_DOWN, uinput.KEY_LEFT, uinput.KEY_RIGHT]
            # Common special keys
            uinput_keys += [
                uinput.KEY_ENTER, uinput.KEY_TAB, uinput.KEY_SPACE, uinput.KEY_ESC,
                uinput.KEY_BACKSPACE, uinput.KEY_DELETE, uinput.KEY_HOME, uinput.KEY_END,
                uinput.KEY_PAGEUP, uinput.KEY_PAGEDOWN, uinput.KEY_CAPSLOCK,
                uinput.KEY_NUMLOCK, uinput.KEY_SCROLLLOCK, uinput.KEY_INSERT,
                uinput.KEY_MENU, uinput.KEY_PAUSE, uinput.KEY_PRINT,
            ]
            # Symbol and punctuation keys
            uinput_keys += [
                uinput.KEY_MINUS, uinput.KEY_EQUAL, uinput.KEY_LEFTBRACE, uinput.KEY_RIGHTBRACE,
                uinput.KEY_BACKSLASH, uinput.KEY_SEMICOLON, uinput.KEY_APOSTROPHE,
                uinput.KEY_GRAVE, uinput.KEY_COMMA, uinput.KEY_DOT, uinput.KEY_SLASH,
            ]
            # Media keys (if available)
            for media_key in ['KEY_VOLUMEUP', 'KEY_VOLUMEDOWN', 'KEY_MUTE', 'KEY_PLAYPAUSE', 'KEY_NEXTSONG', 'KEY_PREVIOUSSONG']:
                key_code = getattr(uinput, media_key, None)
                if key_code:
                    uinput_keys.append(key_code)
            # Remove duplicates
            uinput_keys = list(dict.fromkeys(uinput_keys))
            self.uinput_device = uinput.Device(uinput_keys)
            self.logger.info(f"✅ uinput device initialized with {len(uinput_keys)} keys (explicit list)")
            # Build a name->code map (e.g., 'KEY_A' -> uinput.KEY_A) for combo resolution
            try:
                self.uinput_name_map = {}
                # Letters
                for i in range(ord('a'), ord('z')+1):
                    name = f'KEY_{chr(i).upper()}'
                    if hasattr(uinput, name):
                        self.uinput_name_map[name] = getattr(uinput, name)
                # Digits
                for i in range(0, 10):
                    name = f'KEY_{i}'
                    if hasattr(uinput, name):
                        self.uinput_name_map[name] = getattr(uinput, name)
                # Function keys
                for i in range(1, 21):
                    name = f'KEY_F{i}'
                    if hasattr(uinput, name):
                        self.uinput_name_map[name] = getattr(uinput, name)
                # Common named keys
                named_keys = [
                    'KEY_TAB','KEY_ENTER','KEY_SPACE','KEY_ESC','KEY_BACKSPACE','KEY_DELETE','KEY_HOME','KEY_END',
                    'KEY_PAGEUP','KEY_PAGEDOWN','KEY_CAPSLOCK','KEY_NUMLOCK','KEY_SCROLLLOCK','KEY_INSERT','KEY_MENU',
                    'KEY_PAUSE','KEY_PRINT','KEY_UP','KEY_DOWN','KEY_LEFT','KEY_RIGHT','KEY_LEFTCTRL','KEY_RIGHTCTRL',
                    'KEY_LEFTALT','KEY_RIGHTALT','KEY_LEFTSHIFT','KEY_RIGHTSHIFT','KEY_LEFTMETA','KEY_RIGHTMETA',
                    'KEY_MINUS','KEY_EQUAL','KEY_LEFTBRACE','KEY_RIGHTBRACE','KEY_BACKSLASH','KEY_SEMICOLON','KEY_APOSTROPHE',
                    'KEY_GRAVE','KEY_COMMA','KEY_DOT','KEY_SLASH'
                ]
                for name in named_keys:
                    if hasattr(uinput, name):
                        self.uinput_name_map[name] = getattr(uinput, name)
            except Exception:
                self.uinput_name_map = {}
            # Cache common uinput key lookups to avoid repeated getattr calls later
            try:
                # Basic char mappings
                self.uinput_key_map = {}
                for i in range(ord('a'), ord('z')+1):
                    self.uinput_key_map[chr(i)] = getattr(uinput, f'KEY_{chr(i).upper()}')
                for i in range(0, 10):
                    self.uinput_key_map[str(i)] = getattr(uinput, f'KEY_{i}')

                # Common special keys
                self.uinput_key_map.update({
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
                    'print': uinput.KEY_PRINT,
                    'up': uinput.KEY_UP,
                    'down': uinput.KEY_DOWN,
                    'left': uinput.KEY_LEFT,
                    'right': uinput.KEY_RIGHT,
                    'f1': getattr(uinput, 'KEY_F1'), 'f2': getattr(uinput, 'KEY_F2'),
                })
                # Add remaining function keys
                for i in range(3, 21):
                    self.uinput_key_map[f'f{i}'] = getattr(uinput, f'KEY_F{i}')

                # Symbol/punctuation keys
                self.uinput_key_map.update({
                    '-': uinput.KEY_MINUS,
                    '_': uinput.KEY_MINUS,
                    '=': uinput.KEY_EQUAL,
                    '+': uinput.KEY_EQUAL,
                    '[': uinput.KEY_LEFTBRACE,
                    '{': uinput.KEY_LEFTBRACE,
                    ']': uinput.KEY_RIGHTBRACE,
                    '}': uinput.KEY_RIGHTBRACE,
                    '\\': uinput.KEY_BACKSLASH,
                    '|': uinput.KEY_BACKSLASH,
                    ';': uinput.KEY_SEMICOLON,
                    ':': uinput.KEY_SEMICOLON,
                    "'": uinput.KEY_APOSTROPHE,
                    '"': uinput.KEY_APOSTROPHE,
                    ',': uinput.KEY_COMMA,
                    '<': uinput.KEY_COMMA,
                    '.': uinput.KEY_DOT,
                    '>': uinput.KEY_DOT,
                    '/': uinput.KEY_SLASH,
                    '?': uinput.KEY_SLASH,
                    '`': uinput.KEY_GRAVE,
                    '~': uinput.KEY_GRAVE,
                    ' ': uinput.KEY_SPACE,
                })

                # Media mapping
                self.uinput_media_map = {
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
                }
            except Exception:
                # In case any attribute access fails unexpectedly, keep maps empty
                self.uinput_key_map = {}
                self.uinput_media_map = {}
                self.uinput_name_map = {}
        except PermissionError:
            self.logger.warning("⚠️  uinput requires sudo privileges for key emulation")
            self.logger.warning("   Run with: sudo python macro_handler.py")
            self.uinput_device = None
        except Exception as e:
            self.logger.warning(f"❌ Failed to initialize uinput: {e}")
            self.uinput_device = None
    
    def execute_media_command(self, key_str):
        """Execute media commands using pynput keyboard controller.
        
        Args:
            key_str (str): Media key command string
            
        Returns:
            bool: True if command was executed successfully
        """
        # Media key mappings (pynput and uinput)
        media_mappings = {
            # Use getattr on Key to avoid AttributeError when pynput Key lacks media attrs
            'play': (getattr(Key, 'media_play_pause', None) if Key else None),
            'media_play_pause': (getattr(Key, 'media_play_pause', None) if Key else None),
            'playpause': (getattr(Key, 'media_play_pause', None) if Key else None),
            'next': (getattr(Key, 'media_next', None) if Key else None),
            'media_next': (getattr(Key, 'media_next', None) if Key else None),
            'next_track': (getattr(Key, 'media_next', None) if Key else None),
            'previous': (getattr(Key, 'media_previous', None) if Key else None),
            'prev': (getattr(Key, 'media_previous', None) if Key else None),
            'media_previous': (getattr(Key, 'media_previous', None) if Key else None),
            'prev_track': (getattr(Key, 'media_previous', None) if Key else None),
            'volume_up': (getattr(Key, 'media_volume_up', None) if Key else None),
            'vol_up': (getattr(Key, 'media_volume_up', None) if Key else None),
            'volume_down': (getattr(Key, 'media_volume_down', None) if Key else None),
            'vol_down': (getattr(Key, 'media_volume_down', None) if Key else None),
            'mute': (getattr(Key, 'media_volume_mute', None) if Key else None),
            'volume_mute': (getattr(Key, 'media_volume_mute', None) if Key else None),
        }
        # Try uinput first if available — build uinput mappings only when device exists
        if hasattr(self, 'uinput_device') and self.uinput_device:
            # Use cached uinput media map initialized in _initialize_uinput()
            uinput_key = getattr(self, 'uinput_media_map', {}).get(key_str)
            if uinput_key:
                try:
                    self.uinput_device.emit(uinput_key, 1)
                    time.sleep(0.02)
                    self.uinput_device.emit(uinput_key, 0)
                    self.uinput_device.syn()
                    self.logger.info(f"🎵 Media key executed via uinput: {key_str}")
                    return True
                except Exception as e:
                    self.logger.error(f"❌ Media key error via uinput for '{key_str}': {e}")
                    return False
        # Fallback to pynput
        if not self.keyboard_controller:
            self.logger.error("❌ Keyboard controller not available - media keys disabled")
            return False
        media_key = media_mappings.get(key_str)
        if not media_key:
            return False
        try:
            # Use Key/KeyCode objects from pynput
            self.keyboard_controller.press(media_key)
            self.keyboard_controller.release(media_key)
            self.logger.info(f"🎵 Media key executed via pynput: {key_str}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Media key error for '{key_str}': {e}")
            return False
    
    def execute_key_command(self, key_str):
        """Execute keyboard command - supports single keys and combinations.
        
        Args:
            key_str (str): Key command string (e.g., "key:ctrl+c", "a", "f1")
            
        Returns:
            bool: True if command was executed successfully
        """
        if not self.keyboard_controller:
            self.logger.error("❌ Keyboard controller not available - key commands disabled")
            return False
            
        # Normalize key string by removing prefixes
        normalized_key = self._normalize_key_string(key_str)
        
        self.logger.info(f"⌨️  Processing key command: {normalized_key}")
        
        try:
            if '+' in normalized_key:
                return self._execute_key_combination(normalized_key)
            else:
                return self._execute_single_key(normalized_key)
                
        except Exception as e:
            self.logger.error(f"❌ Key execution error for '{key_str}': {e}")
            return False
    
    def _normalize_key_string(self, key_str):
        """Normalize key string by removing common prefixes.
        
        Args:
            key_str (str): Raw key string
            
        Returns:
            str: Normalized key string
        """
        normalized = key_str
        
        # Remove common prefixes
        prefixes = ['key:', 'Key.']
        for prefix in prefixes:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
                break
                
        return normalized
    
    def _execute_single_key(self, key_str):
        """Execute a single key press.
        
        Args:
            key_str (str): Single key to press
        
        Returns:
            bool: True if key was pressed successfully
        """
        # Try media commands first
        if self.execute_media_command(key_str):
            return True
        # Always use uinput for print_screen if available
        if key_str in ('print_screen', 'print') and hasattr(self, 'uinput_device') and self.uinput_device:
            uinput_key = self._get_uinput_key_code(key_str)
            if uinput_key:
                self.uinput_device.emit(uinput_key, 1)
                time.sleep(0.02)
                self.uinput_device.emit(uinput_key, 0)
                self.uinput_device.syn()
                self.logger.info(f"🔑 uinput key pressed: {key_str}")
                return True
        # Use uinput for all other keys if available
        if hasattr(self, 'uinput_device') and self.uinput_device:
            uinput_key = self._get_uinput_key_code(key_str)
            if uinput_key:
                self.uinput_device.emit(uinput_key, 1)
                time.sleep(0.02)
                self.uinput_device.emit(uinput_key, 0)
                self.uinput_device.syn()
                self.logger.info(f"🔑 uinput key pressed: {key_str}")
                return True
        # Fallback to pynput
        if key_str in self.key_mapping:
            key = self.key_mapping[key_str]
            self._press_and_release_key(key)
            self.logger.info(f"🔑 Special key pressed: {key_str}")
            return True
        if len(key_str) == 1:
            self._press_and_release_key(key_str)
            self.logger.info(f"🔤 Character pressed: {key_str}")
            return True
        self.logger.warning(f"⚠️  Unknown key: {key_str}")
        return False
    
    def _get_key_mapping(self):
        """Get comprehensive key mapping dictionary.
        
        Returns:
            dict: Mapping of string names to pynput Key objects
        """
        return {
            # Modifier keys
            'alt': Key.alt, 'alt_l': Key.alt_l, 'alt_r': Key.alt_r, 'alt_gr': Key.alt_gr,
            'ctrl': Key.ctrl, 'ctrl_l': Key.ctrl_l, 'ctrl_r': Key.ctrl_r,
            'shift': Key.shift, 'shift_l': Key.shift_l, 'shift_r': Key.shift_r,
            'cmd': Key.cmd, 'cmd_l': Key.cmd_l, 'cmd_r': Key.cmd_r,
            
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
            
            # Media keys
            'media_play_pause': Key.media_play_pause, 'media_volume_mute': Key.media_volume_mute,
            'media_volume_down': Key.media_volume_down, 'media_volume_up': Key.media_volume_up,
            'media_previous': Key.media_previous, 'media_next': Key.media_next,
        }
    
    def _press_and_release_key(self, key):
        """Press and release a key with proper timing.
        
        Args:
            key: Key object or character to press
        """
        # Use uinput if available and initialized
        if hasattr(self, 'uinput_device') and self.uinput_device:
            uinput_key = None
            if isinstance(key, str) and len(key) == 1:
                uinput_key = self._get_uinput_key_code(key)
            elif hasattr(key, 'name'):
                uinput_key = self._get_uinput_key_code(key.name)
            if uinput_key:
                self.uinput_device.emit(uinput_key, 1)
                time.sleep(0.02)
                self.uinput_device.emit(uinput_key, 0)
                self.uinput_device.syn()
                return
        # Fallback to pynput
        try:
            from pynput.keyboard import KeyCode
            if isinstance(key, str) and len(key) == 1:
                kc = KeyCode.from_char(key)
                self.keyboard_controller.press(kc)
                time.sleep(0.02)
                self.keyboard_controller.release(kc)
                return
        except Exception:
            pass
        self.keyboard_controller.press(key)
        time.sleep(0.02)
        self.keyboard_controller.release(key)
    
    def _execute_key_combination(self, key_str):
        """Execute key combination (e.g., ctrl+c, alt+tab, super+l, alt+tab) via uinput if available."""
        keys = [k.strip() for k in key_str.split('+')]
        self.logger.info(f"🔗 Parsing key combination: {key_str} -> {keys}")
        keys_to_press = self._parse_key_combination(keys)
        if not keys_to_press:
            self.logger.warning(f"⚠️  No valid keys found in combination: {key_str}")
            return False
        self.logger.info(f"🎯 Executing key combination: {[str(k) for k in keys_to_press]}")

        # Try uinput for all combos if available
        if hasattr(self, 'uinput_device') and self.uinput_device:
            return self._execute_combination_uinput(keys_to_press)

        # Otherwise, use pynput
        return self._execute_standard_combination(keys_to_press, key_str)

    def _execute_combination_uinput(self, keys_to_press):
        """Execute any key combination using uinput (modifiers + key)."""
        # Map modifiers and keys to uinput codes
        key_map = {
            'ctrl': 'KEY_LEFTCTRL', 'control': 'KEY_LEFTCTRL',
            'alt': 'KEY_LEFTALT', 'alt_l': 'KEY_LEFTALT', 'alt_r': 'KEY_RIGHTALT',
            'shift': 'KEY_LEFTSHIFT', 'shift_l': 'KEY_LEFTSHIFT', 'shift_r': 'KEY_RIGHTSHIFT',
            'super': 'KEY_LEFTMETA', 'win': 'KEY_LEFTMETA', 'cmd': 'KEY_LEFTMETA',
            'tab': 'KEY_TAB', 'enter': 'KEY_ENTER', 'esc': 'KEY_ESC', 'escape': 'KEY_ESC',
            'delete': 'KEY_DELETE', 'backspace': 'KEY_BACKSPACE', 'space': 'KEY_SPACE',
            'up': 'KEY_UP', 'down': 'KEY_DOWN', 'left': 'KEY_LEFT', 'right': 'KEY_RIGHT',
        }
        # Add letters and digits
        for i in range(ord('a'), ord('z')+1):
            key_map[chr(i)] = f'KEY_{chr(i).upper()}'
        for i in range(0, 10):
            key_map[str(i)] = f'KEY_{i}'
        # Add function keys
        for i in range(1, 21):
            key_map[f'f{i}'] = f'KEY_F{i}'

        # Convert keys to uinput codes
        uinput_keys = []
        for k in keys_to_press:
            # Resolve the key string for mapping. Handle:
            # - pynput.keyboard.KeyCode with .char
            # - pynput.keyboard.Key with .name
            # - plain strings or repr like "'l'"
            kstr = None
            try:
                if hasattr(k, 'char') and k.char is not None:
                    kstr = str(k.char).lower()
                elif hasattr(k, 'name') and k.name is not None:
                    kstr = str(k.name).lower()
                else:
                    # str(k) for some KeyCode values can be "'l'"; strip quotes
                    kstr = str(k).lower().strip("'\"")
            except Exception:
                kstr = str(k).lower()

            code_name = key_map.get(kstr)
            # Use the cached name->code map built during uinput initialization
            code = getattr(self, 'uinput_name_map', {}).get(code_name) if code_name else None
            if code:
                uinput_keys.append(code)
            else:
                # Try direct mapping for single chars (letters/digits/etc.)
                code = self._get_uinput_key_code(kstr)
                if code:
                    uinput_keys.append(code)
                else:
                    self.logger.warning(f"⚠️  Unknown uinput key for combo: {kstr}")
                    return False

        # Press all modifiers except last key
        try:
            for code in uinput_keys[:-1]:
                self.uinput_device.emit(code, 1)
                time.sleep(0.01)
            # Press and release final key
            self.uinput_device.emit(uinput_keys[-1], 1)
            time.sleep(0.05)
            self.uinput_device.emit(uinput_keys[-1], 0)
            time.sleep(0.01)
            # Release all modifiers in reverse
            for code in reversed(uinput_keys[:-1]):
                self.uinput_device.emit(code, 0)
                time.sleep(0.01)
            self.uinput_device.syn()
            self.logger.info(f"✅ uinput combo executed: {uinput_keys}")
            return True
        except Exception as e:
            self.logger.error(f"❌ uinput combo error: {e}")
            return False
    
    def _parse_key_combination(self, keys):
        """Parse key combination into executable key objects.
        
        Args:
            keys (list): List of key strings
            
        Returns:
            list: List of key objects to press
        """
        keys_to_press = []
        for key in keys:
            if key in self.modifier_mapping:
                mapped_key = self.modifier_mapping[key]
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
                # Try to find it in the special key mapping
                special_key = self._get_special_combination_key(key)
                if special_key:
                    keys_to_press.append(special_key)
                    self.logger.debug(f"Mapped special key '{key}' -> {special_key}")
                else:
                    self.logger.warning(f"⚠️  Unknown key in combination: {key}")
                    return []
        return keys_to_press
    
    def _get_modifier_mapping(self):
        """Get modifier key mapping.
        
        Returns:
            dict: Mapping of modifier names to Key objects
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
    
    def _execute_standard_combination(self, keys_to_press, key_str):
        """Execute standard key combination using pynput.
        
        Args:
            keys_to_press (list): List of keys to press
            key_str (str): Original key string for logging
            
        Returns:
            bool: True if executed successfully
        """
        # Special-case: On Windows, Win+L is handled by the OS and may not be triggered
        # by simulated key injection reliably. Use native LockWorkStation API instead.
        if self.system == 'windows':
            norm = key_str.lower()
            if norm in ('win+l', 'super+l', 'cmd+l'):
                return self._lock_workstation()

        if len(keys_to_press) > 1:
            return self._execute_multi_key_combination(keys_to_press)
        else:
            return self._execute_single_key_from_combination(keys_to_press[0], key_str)

    def _lock_workstation(self):
        """Lock the Windows workstation using native API.

        Returns:
            bool: True if the call succeeded
        """
        try:
            if self.system != 'windows':
                self.logger.warning("⚠️  _lock_workstation called on non-Windows system")
                return False
            import ctypes
            res = ctypes.windll.user32.LockWorkStation()
            if res:
                self.logger.info("🔒 Workstation locked via LockWorkStation()")
                return True
            else:
                self.logger.warning("⚠️  LockWorkStation returned False")
                return False
        except Exception as e:
            self.logger.error(f"❌ Failed to lock workstation: {e}")
            return False
    
    def _execute_multi_key_combination(self, keys_to_press):
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
                contexts.append(self.keyboard_controller.pressed(modifier))
            
            # Enter all contexts
            for context in contexts:
                context.__enter__()
            
            # Press and release the final key
            self.keyboard_controller.press(final_key)
            time.sleep(0.05)  # Brief hold
            self.keyboard_controller.release(final_key)
            
            # Exit all contexts in reverse order
            for context in reversed(contexts):
                context.__exit__(None, None, None)
            
            self.logger.info("✅ Key combination executed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in key combination: {e}")
            return False
    
    def _execute_single_key_from_combination(self, key, key_str):
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
    
    def _get_special_combination_key(self, key_str):
        """Get special key object for use in combinations.
        
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
    
    def _execute_super_combination_uinput(self, keys_to_press):
        """Execute Super key combination using uinput on Linux.
        
        Args:
            keys_to_press (list): List containing Super key and another key
            
        Returns:
            bool: True if executed successfully
        """
        try:
            # Separate Super key and target key
            super_key, other_key = self._separate_super_combination_keys(keys_to_press)
            
            if not super_key or not other_key:
                self.logger.error("❌ Invalid Super key combination format")
                return False
            
            # Get uinput key code
            uinput_key = self._get_uinput_key_code(str(other_key))
            if not uinput_key:
                self.logger.warning(f"⚠️  Unsupported key for uinput Super combination: {other_key}")
                return False
            
            # Execute the combination
            return self._perform_uinput_combination(uinput_key, str(other_key))
            
        except Exception as e:
            self.logger.error(f"❌ Error in uinput Super combination: {e}")
            return False
    
    def _separate_super_combination_keys(self, keys_to_press):
        """Separate Super key and target key from key list.
        
        Args:
            keys_to_press (list): List of keys
            
        Returns:
            tuple: (super_key, other_key) or (None, None) if invalid
        """
        super_key = None
        other_key = None
        
        for key in keys_to_press:
            if str(key) == "Key.cmd":
                super_key = key
            else:
                other_key = key
        
        return super_key, other_key
    
    def _get_uinput_key_code(self, key_str):
        """Get uinput key code for a character or special key."""
        # Use cached map if available, otherwise return None
        return getattr(self, 'uinput_key_map', {}).get(key_str)
    
    def _perform_uinput_combination(self, uinput_key, key_name):
        """Perform the actual uinput key combination.
        
        Args:
            uinput_key: uinput key code
            key_name (str): Key name for logging
            
        Returns:
            bool: True if successful
        """
        try:
            self.logger.info(f"🔑 Executing Super+{key_name} via uinput")
            
            # Press Super key
            self.uinput_device.emit(uinput.KEY_LEFTMETA, 1)
            time.sleep(0.02)
            
            # Press the target key  
            self.uinput_device.emit(uinput_key, 1)
            time.sleep(0.05)
            
            # Release the target key
            self.uinput_device.emit(uinput_key, 0)
            time.sleep(0.02)
            
            # Release Super key
            self.uinput_device.emit(uinput.KEY_LEFTMETA, 0)
            
            # Sync events
            self.uinput_device.syn()
            
            self.logger.info(f"✅ uinput Super combination completed: Super+{key_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ uinput execution error: {e}")
            return False
            
            # Release the other key
            self.uinput_device.emit(uinput_key, 0)

    
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
            return self._execute_normally(final_command)
            
        except Exception as e:
            self.logger.error(f"❌ Error launching program '{exe_str}': {e}")
            return False
    
    def _is_running_as_root(self):
        """Check if currently running as root/sudo.
        
        Returns:
            bool: True if running as root
        """
        import os
        return os.getuid() == 0
    
    def _execute_normally(self, command):
        """Execute command normally (not as root).
        
        Args:
            command (str): Command to execute
            
        Returns:
            bool: True if executed successfully
        """
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            
            self.logger.info(f"✅ Program launched successfully: {command} (PID: {process.pid})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to execute normally: {e}")
            return False
    
    def handle_command(self, data):
        """Process received UDP command.
        
        Args:
            data (dict): Command data dictionary
            
        Returns:
            bool: True if command was processed successfully
        """
        import webbrowser
        action = data.get('action', '')

        if action.startswith('key:'):
            return self.execute_key_command(action)
        elif action.startswith('type:'):
            text = action[5:]
            self.logger.info(f"⌨️ Typing: {text}")
            return self.type_text(text)
        elif action.startswith('exe:'):
            return self.execute_program(action)
        elif action.startswith('url:'):
            url = action[4:]
            self.logger.info(f"🌐 Opening URL: {url}")
            try:
                webbrowser.open(url)
                return True
            except Exception as e:
                self.logger.error(f"❌ Error opening URL '{url}': {e}")
                return False
        else:
            self.logger.warning(f"⚠️  Unknown action format: {action}")
            return False
            
    def type_text(self, text):
        """Type a string sequentially using uinput or pynput, handling shift for uppercase and symbols."""
        # Mapping for shift+number and common symbols
        shift_map = {
            '!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6', '&': '7', '*': '8', '(': '9', ')': '0',
            '_': '-', '+': '=', '{': '[', '}': ']', '|': '\\', ':': ';', '"': '\'', '<': ',', '>': '.', '?': '/', '~': '`'
        }

        # Direct symbols that map to specific uinput codes
        direct_symbols = set(['-','_','=','+','[',']','{','}',';',':',',','.','<','>','/','?','`','~',' ',"'",'"','|'])

        try:
            for char in text:
                use_shift = False
                base_char = char

                # Uppercase letters
                if 'A' <= char <= 'Z':
                    use_shift = True
                    base_char = char.lower()
                # Shifted symbols
                elif char in shift_map:
                    use_shift = True
                    base_char = shift_map[char]
                # Direct symbols (no shift)
                elif char in direct_symbols:
                    base_char = char
                    use_shift = False

                # Use uinput if available
                if hasattr(self, 'uinput_device') and self.uinput_device:
                    keymap = getattr(self, 'uinput_key_map', None)

                    if use_shift:
                        try:
                            self.uinput_device.emit(uinput.KEY_LEFTSHIFT, 1)
                        except Exception:
                            pass
                        time.sleep(0.01)

                    # Special handling for literal backslash
                    if char == '\\':
                        keycode = None
                        if keymap:
                            keycode = keymap.get('\\')
                        if not keycode:
                            keycode = getattr(uinput, 'KEY_BACKSLASH', None)
                        if keycode:
                            try:
                                self.uinput_device.emit(keycode, 1)
                                time.sleep(0.02)
                                self.uinput_device.emit(keycode, 0)
                                self.uinput_device.syn()
                            except Exception:
                                pass
                    else:
                        keycode = None
                        if keymap:
                            keycode = keymap.get(char)
                        if not keycode:
                            keycode = self._get_uinput_key_code(base_char)
                        if keycode:
                            try:
                                self.uinput_device.emit(keycode, 1)
                                time.sleep(0.02)
                                self.uinput_device.emit(keycode, 0)
                                self.uinput_device.syn()
                            except Exception:
                                pass

                    if use_shift:
                        try:
                            self.uinput_device.emit(uinput.KEY_LEFTSHIFT, 0)
                            self.uinput_device.syn()
                        except Exception:
                            pass

                    continue

                # Fallback to pynput
                if self.keyboard_controller:
                    try:
                        from pynput.keyboard import KeyCode
                        kc = KeyCode.from_char(base_char)
                        if use_shift:
                            with self.keyboard_controller.pressed(Key.shift):
                                self.keyboard_controller.press(kc)
                                time.sleep(0.02)
                                self.keyboard_controller.release(kc)
                        else:
                            self.keyboard_controller.press(kc)
                            time.sleep(0.02)
                            self.keyboard_controller.release(kc)
                    except Exception:
                        # Try KeyCode for symbols that fail
                        try:
                            from pynput.keyboard import KeyCode
                            keycode = KeyCode.from_char(char)
                            self.keyboard_controller.press(keycode)
                            time.sleep(0.02)
                            self.keyboard_controller.release(keycode)
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
            self.logger.info("  � Combos: key:ctrl+c, key:alt+tab, key:shift+f10, key:ctrl+alt+delete")
            self.logger.info("  🏃 Navigation: key:up, key:down, key:left, key:right, key:home, key:end")
            self.logger.info("  🚀 Programs: exe:calc, exe:firefox, exe:cmd, etc.")
            self.logger.info("  💡 Examples: key:ctrl+s, key:alt+f4, key:win+r, key:f5, key:delete")
            
            while self.running:
                try:
                    data, addr = sock.recvfrom(1024)
                    command = json.loads(data.decode('utf-8'))
                    self.logger.info(f"Command from {addr[0]}: {command}")
                    self.handle_command(command)
                except json.JSONDecodeError:
                    self.logger.error("Invalid JSON received")
                except Exception as e:
                    self.logger.error(f"Error receiving command: {e}")
                    
        except Exception as e:
            self.logger.error(f"❌ Error setting up UDP listener: {e}")
        finally:
            if 'sock' in locals():
                sock.close()
                self.logger.info("🔌 UDP socket closed")
    
    def _log_capabilities(self):
        """Log the supported commands and capabilities."""
        self.logger.info("📋 Supported commands:")
        self.logger.info("  🎵 Media: key:play, key:next, key:previous, key:volume_up, key:volume_down, key:mute")
        self.logger.info("  ⌨️  Keys: key:a-z, key:0-9, key:f1-f20, key:enter, key:space, key:tab, etc.")
        self.logger.info("  🔗 Combos: key:ctrl+c, key:alt+tab, key:shift+f10, key:ctrl+alt+delete")
        
        # Super key capability info
        if self.uinput_device:
            self.logger.info("  🔑 Super: key:super+a, key:super+l (uinput enabled)")
        elif self.system == 'linux':
            self.logger.info("  ⚠️  Super: key:super+a, key:super+l (requires sudo)")
        else:
            self.logger.info("  🪟 Windows: key:win+r, key:win+l (native support)")
        
        self.logger.info("  🏃 Navigation: key:up, key:down, key:left, key:right, key:home, key:end")
        self.logger.info("  🚀 Programs: exe:calculator, exe:firefox, exe:terminal, etc.")
        self.logger.info("  💡 Examples: key:ctrl+s, key:alt+f4, key:super+r, key:f5, key:delete")
    
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