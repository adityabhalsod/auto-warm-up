"""
Auto Warm-Up: Prevents Windows from detecting idle state and locking the screen.
Simulates tiny mouse movements at regular intervals — no admin rights required.
Runs silently in the system tray with start/stop control.
"""

import ctypes
import ctypes.wintypes
import threading
import time
import sys
import os

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

    # Build the tray menu with Start / Stop / Quit options
    menu = pystray.Menu(
        pystray.MenuItem("Start", start_jiggler),
        pystray.MenuItem("Stop", stop_jiggler),
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
