"""
Generate a multi-size .ico file for AutoWarmUp.exe using Pillow.
Produces a professional-looking mouse/cursor icon with multiple resolutions
so Windows displays it correctly at all DPI scales.
"""

from PIL import Image, ImageDraw, ImageFont
import sys
import os


def create_icon_frame(size):
    """Create a single icon frame at the given resolution with a green circle and cursor shape."""
    # Create a transparent RGBA canvas at the requested size
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    # Drawing context for shapes and text
    draw = ImageDraw.Draw(img)

    # Outer padding as fraction of size for consistent scaling
    pad = size // 8
    # Draw a filled green circle as the background (brand color)
    draw.ellipse(
        (pad, pad, size - pad, size - pad),
        fill=(76, 175, 80, 255),       # Material Green 500
        outline=(56, 142, 60, 255),    # Darker green border for depth
        width=max(1, size // 32),      # Border width scales with icon size
    )

    # Draw a simplified mouse cursor arrow in white inside the circle
    cx = size // 2       # Horizontal center
    cy = size // 2       # Vertical center
    # Scale factor for the cursor shape relative to icon size
    s = size / 64.0

    # Define cursor arrow polygon points (scaled from a 64px base design)
    cursor_points = [
        (cx - int(8 * s), cy - int(12 * s)),   # Top-left tip of arrow
        (cx + int(6 * s), cy + int(2 * s)),     # Right edge
        (cx + int(1 * s), cy + int(5 * s)),     # Inner notch right
        (cx + int(4 * s), cy + int(12 * s)),    # Bottom-right tail
        (cx + int(0 * s), cy + int(9 * s)),     # Inner notch bottom
        (cx - int(4 * s), cy + int(12 * s)),    # Bottom-left tail
        (cx - int(1 * s), cy + int(5 * s)),     # Inner notch left
    ]

    # Fill the cursor shape in white with a dark outline for visibility
    draw.polygon(cursor_points, fill=(255, 255, 255, 240), outline=(33, 33, 33, 200))

    return img


def generate_ico(output_path="app.ico"):
    """Generate a multi-resolution .ico file containing all standard Windows icon sizes."""
    # Standard Windows icon sizes from smallest to largest (taskbar, explorer, tiles)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    # Generate one frame per size
    frames = [create_icon_frame(s) for s in sizes]

    # Save all frames into a single .ico file (Pillow handles the multi-image format)
    frames[0].save(
        output_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],   # Declare the resolution of each frame
        append_images=frames[1:],         # Attach additional frames after the first
    )
    # Confirm output path and file size for build logs
    print(f"Icon generated: {output_path} ({os.path.getsize(output_path)} bytes)")


if __name__ == "__main__":
    # Allow optional output path override via CLI argument
    out = sys.argv[1] if len(sys.argv) > 1 else "app.ico"
    generate_ico(out)
