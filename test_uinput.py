import os
import sys
import time

# Try to import uinput
try:
    import uinput
    UINPUT_AVAILABLE = True
except ImportError:
    UINPUT_AVAILABLE = False

# Check for /dev/uinput access
def has_uinput_access():
    return os.path.exists('/dev/uinput') and os.access('/dev/uinput', os.W_OK)

if UINPUT_AVAILABLE and has_uinput_access():
    print("Using uinput for key emulation.")
    events = [getattr(uinput, 'KEY_VOLUMEUP', None)]
    with uinput.Device(events) as device:
        time.sleep(1)
        print("Sending Volume Up...")
        if getattr(uinput, 'KEY_VOLUMEUP', None):
            device.emit(getattr(uinput, 'KEY_VOLUMEUP'), 1)
            time.sleep(0.1)
            device.emit(getattr(uinput, 'KEY_VOLUMEUP'), 0)
            device.syn()
            print("Volume Up sent via uinput.")
        else:
            print("uinput.KEY_VOLUMEUP not available on this system.")
else:
    print("uinput not available or not accessible. Falling back to pynput.")
    try:
        from pynput.keyboard import Key, Controller
        keyboard = Controller()
        time.sleep(1)
        print("Sending Super+L with pynput...")
        keyboard.press(Key.cmd)
        keyboard.press('l')
        keyboard.release('l')
        keyboard.release(Key.cmd)
        print("Done")
    except ImportError:
        print("pynput is not installed. Please install it with 'pip install pynput'.")
        sys.exit(1)
