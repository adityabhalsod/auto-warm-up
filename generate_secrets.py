"""
Generate GitHub Actions secret values for code signing.
Reads a .pfx certificate file and prints the two secret values
(CODESIGN_PFX_BASE64 and CODESIGN_PFX_PASSWORD) ready to paste
into GitHub → Settings → Secrets and variables → Actions.

Usage:
    python generate_secrets.py path/to/certificate.pfx
    python generate_secrets.py path/to/certificate.pfx "YourPfxPassword"
"""

import sys
import base64
import os


def generate_secrets(pfx_path, pfx_password=""):
    """Read a .pfx file and print the two GitHub secret values."""
    # Verify the .pfx file exists before attempting to read it
    if not os.path.isfile(pfx_path):
        print(f"ERROR: File not found: {pfx_path}")
        sys.exit(1)

    # Read the raw binary content of the .pfx certificate file
    with open(pfx_path, "rb") as f:
        pfx_bytes = f.read()

    # Encode the binary .pfx to a single-line base64 string (no line wrapping)
    pfx_base64 = base64.b64encode(pfx_bytes).decode("ascii")

    # Print separator and instructions
    print("")
    print("=" * 60)
    print("  GitHub Actions Secrets — Copy these values exactly")
    print("=" * 60)
    print("")

    # Print the first secret: base64-encoded certificate
    print("Secret 1 ─────────────────────────────────────────────")
    print(f"  Name  : CODESIGN_PFX_BASE64")
    print(f"  Value :")
    print(f"  {pfx_base64}")
    print("")

    # Print the second secret: certificate password
    print("Secret 2 ─────────────────────────────────────────────")
    print(f"  Name  : CODESIGN_PFX_PASSWORD")
    # Show placeholder if password is empty so the user knows what to enter
    print(f"  Value : {pfx_password if pfx_password else '(leave blank — no password set)'}")
    print("")

    print("=" * 60)
    print("  Paste each value into:")
    print("  github.com/adityabhalsod/auto-warm-up")
    print("  → Settings → Secrets and variables → Actions")
    print("  → New repository secret")
    print("=" * 60)
    print("")


if __name__ == "__main__":
    # Require at least the .pfx file path as an argument
    if len(sys.argv) < 2:
        print("Usage: python generate_secrets.py <path-to-pfx> [pfx-password]")
        print("Example: python generate_secrets.py codesign.pfx MyPassword123")
        sys.exit(1)

    # First argument: path to the .pfx certificate file
    pfx_file = sys.argv[1]
    # Second argument (optional): password for the .pfx (defaults to empty string)
    password = sys.argv[2] if len(sys.argv) > 2 else ""

    generate_secrets(pfx_file, password)
