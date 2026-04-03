"""
Auto Warm-Up: Prevents Windows from detecting idle state and locking the screen.
Simulates tiny mouse movements at regular intervals — no admin rights required.
Runs silently in the system tray with start/stop control.
Supports auto-start on Windows boot via the user-level registry (no admin needed).
"""

import ctypes
import ctypes.wintypes
import threading
import time
import sys
import os
import winreg

# --- Windows API structures and constants for simulating input ---

# Input event type: mouse input
INPUT_MOUSE = 0
# Mouse event flag: movement occurred
MOUSEEVENTF_MOVE = 0x0001

class MOUSEINPUT(ctypes.Structure):
    """Structure representing a simulated mouse input event."""
    _fields_ = [
        ("dx", ctypes.wintypes.LONG),       # Horizontal movement delta
        ("dy", ctypes.wintypes.LONG),       # Vertical movement delta
        ("mouseData", ctypes.wintypes.DWORD), # Additional mouse data (unused here)
        ("dwFlags", ctypes.wintypes.DWORD),  # Mouse event flags (move, click, etc.)
        ("time", ctypes.wintypes.DWORD),     # Timestamp (0 = system assigns)
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)), # Extra app-specific info
    ]

class INPUT(ctypes.Structure):
    """Union structure wrapping different input types for SendInput API."""

    class _INPUT(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]  # Only mouse input variant needed

    _fields_ = [
        ("type", ctypes.wintypes.DWORD),  # Type of input (INPUT_MOUSE = 0)
        ("ii", _INPUT),                    # The actual input data union
    ]


def move_mouse(dx, dy):
    """Simulate a relative mouse movement by (dx, dy) pixels using Windows SendInput API."""
    # Build a MOUSEINPUT struct with the desired delta and MOVE flag
    mouse_input = MOUSEINPUT(
        dx=dx,
        dy=dy,
        mouseData=0,
        dwFlags=MOUSEEVENTF_MOVE,
        time=0,
        dwExtraInfo=ctypes.pointer(ctypes.c_ulong(0)),
    )
    # Wrap it in an INPUT struct tagged as mouse input
    input_event = INPUT(type=INPUT_MOUSE)
    input_event.ii.mi = mouse_input
    # Send the synthetic input event to the OS
    ctypes.windll.user32.SendInput(1, ctypes.byref(input_event), ctypes.sizeof(INPUT))


def prevent_idle(interval_seconds=30, stop_event=None):
    """
    Continuously jiggle the mouse by 1 pixel back-and-forth to reset the idle timer.
    Runs until stop_event is set or the process is killed.
    """
    # Direction toggle: alternates between +1 and -1 so the cursor stays in place
    direction = 1
    while not (stop_event and stop_event.is_set()):
        # Move mouse 1 pixel in the current direction
        move_mouse(direction, 0)
        # Reverse direction for the next cycle so net movement is zero
        direction *= -1
        # Also reset the OS idle/screen-saver timer directly
        # ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001 | 0x00000002)
        # Wait before the next jiggle
        time.sleep(interval_seconds)


# --- Auto-start on boot via Windows Registry (HKCU, no admin required) ---

# Registry key path for user-level startup programs
_STARTUP_REG_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
# Name used to identify this app's registry entry
_STARTUP_REG_NAME = "AutoWarmUp"


def get_exe_path():
    """Return the path to the current executable (works for both .exe and .py)."""
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller-bundled .exe — use the executable path
        return sys.executable
    else:
        # Running as a .py script — use the script's absolute path
        return os.path.abspath(sys.argv[0])


def is_autostart_enabled():
    """Check if Auto Warm-Up is registered to start on Windows boot."""
    try:
        # Open the user-level Run key for reading
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _STARTUP_REG_KEY, 0, winreg.KEY_READ)
        # Try to read our app's registry value
        winreg.QueryValueEx(key, _STARTUP_REG_NAME)
        # Close the key handle after reading
        winreg.CloseKey(key)
        # Value exists — auto-start is enabled
        return True
    except FileNotFoundError:
        # Registry value doesn't exist — auto-start is disabled
        return False
    except OSError:
        # Unexpected registry error — treat as disabled
        return False


def enable_autostart():
    """Register Auto Warm-Up to start automatically on Windows boot (user-level, no admin)."""
    try:
        # Open the user-level Run key with write access
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _STARTUP_REG_KEY, 0, winreg.KEY_SET_VALUE)
        # Get the path to the current executable
        exe_path = get_exe_path()
        # Write the app path as a REG_SZ string value so Windows launches it at login
        winreg.SetValueEx(key, _STARTUP_REG_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
        # Close the key handle after writing
        winreg.CloseKey(key)
        return True
    except OSError:
        # Registry write failed (shouldn't happen for HKCU but handle gracefully)
        return False


def disable_autostart():
    """Remove Auto Warm-Up from the Windows boot startup registry."""
    try:
        # Open the user-level Run key with write access
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _STARTUP_REG_KEY, 0, winreg.KEY_SET_VALUE)
        # Delete our app's registry value to stop auto-starting
        winreg.DeleteValue(key, _STARTUP_REG_NAME)
        # Close the key handle after deletion
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        # Value already doesn't exist — nothing to remove
        return True
    except OSError:
        # Registry delete failed — handle gracefully
        return False


def run_with_tray():
    """
    Launch the jiggler with a system tray icon for easy start/stop/quit control.
    Falls back to console mode if pystray is not available.
    """
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError:
        # pystray or Pillow not installed — fall back to simple console mode
        run_console()
        return

    # Shared flag to signal the jiggler thread to stop
    stop_event = threading.Event()
    # Reference holder for the background jiggler thread
    jiggler_thread = [None]

    def create_icon_image(color):
        """Generate a small colored circle icon for the system tray."""
        # Create a 64x64 RGBA image with a filled circle
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((4, 4, 60, 60), fill=color)
        return image

    def start_jiggler(icon, item):
        """Start the background jiggler thread and update the tray icon to green."""
        if jiggler_thread[0] is None or not jiggler_thread[0].is_alive():
            # Clear any previous stop signal so the loop runs
            stop_event.clear()
            # Spawn a daemon thread so it dies when the main process exits
            jiggler_thread[0] = threading.Thread(target=prevent_idle, args=(30, stop_event), daemon=True)
            jiggler_thread[0].start()
            # Green icon = active
            icon.icon = create_icon_image("green")
            icon.title = "Auto Warm-Up (Running)"

    def stop_jiggler(icon, item):
        """Stop the jiggler thread and turn the tray icon red."""
        # Signal the loop to exit
        stop_event.set()
        # Red icon = paused
        icon.icon = create_icon_image("red")
        icon.title = "Auto Warm-Up (Paused)"

    def quit_app(icon, item):
        """Cleanly shut down: stop the jiggler and remove the tray icon."""
        stop_event.set()
        icon.stop()

    def toggle_autostart(icon, item):
        """Toggle auto-start on boot: enable if disabled, disable if enabled."""
        if is_autostart_enabled():
            # Currently enabled — remove from startup registry
            disable_autostart()
        else:
            # Currently disabled — add to startup registry
            enable_autostart()

    def autostart_checked(item):
        """Return True if auto-start is currently enabled (shows checkmark in menu)."""
        return is_autostart_enabled()

    # Build the tray menu with Start / Stop / Auto-Start toggle / Quit options
    menu = pystray.Menu(
        pystray.MenuItem("Start", start_jiggler),
        pystray.MenuItem("Stop", stop_jiggler),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Start on Boot", toggle_autostart, checked=autostart_checked),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", quit_app),
    )

    # Create the tray icon (starts green = active by default)
    icon = pystray.Icon(
        "auto_warm_up",
        create_icon_image("green"),
        "Auto Warm-Up (Running)",
        menu,
    )

    # Auto-start the jiggler immediately on launch
    stop_event.clear()
    jiggler_thread[0] = threading.Thread(target=prevent_idle, args=(30, stop_event), daemon=True)
    jiggler_thread[0].start()

    # Block on the tray icon event loop (runs until Quit is selected)
    icon.run()


def run_console():
    """Simple console mode: prints status and jiggles until Ctrl+C is pressed."""
    print("=" * 50)
    print("  Auto Warm-Up — Keep-Alive Utility")
    print("=" * 50)
    print()
    print("  Status : RUNNING")
    print("  Action : Mouse jiggles every 30 seconds")
    print("  Stop   : Press Ctrl+C to exit")
    print()
    print("=" * 50)

    try:
        # Run the jiggler on the main thread (blocks until KeyboardInterrupt)
        prevent_idle(interval_seconds=30)
    except KeyboardInterrupt:
        # User pressed Ctrl+C — exit gracefully
        print("\nStopped. Screen lock prevention disabled.")


if __name__ == "__main__":
    # Entry point: try tray mode first, fall back to console
    run_with_tray()
