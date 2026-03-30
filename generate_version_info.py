"""
Generate a PyInstaller-compatible version_info.txt file from the VERSION file.
Embeds Windows PE version resources (file version, product name, company, description)
into the .exe so Windows Explorer shows proper metadata and antivirus trusts the binary.
"""

import sys
import os

# PyInstaller VSVersionInfo template — this becomes the PE VERSIONINFO resource
VERSION_INFO_TEMPLATE = """# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers are lists of 4 16-bit integers: [major, minor, patch, build]
    filevers=({major}, {minor}, {patch}, {build}),
    prodvers=({major}, {minor}, {patch}, {build}),
    # Contains a bitmask specifying the valid bits in 'flags'
    mask=0x3f,
    # File flags: 0 = final release build
    flags=0x0,
    # Operating system: VOS_NT_WINDOWS32 (Windows NT)
    OS=0x40004,
    # File type: VFT_APP (application)
    fileType=0x1,
    # File subtype: not applicable for applications
    subtype=0x0,
    # Creation date and time: not set (left to the OS)
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [
            StringStruct(u'CompanyName', u'{company}'),
            StringStruct(u'FileDescription', u'{description}'),
            StringStruct(u'FileVersion', u'{version_str}'),
            StringStruct(u'InternalName', u'{internal_name}'),
            StringStruct(u'LegalCopyright', u'{copyright}'),
            StringStruct(u'OriginalFilename', u'{original_filename}'),
            StringStruct(u'ProductName', u'{product_name}'),
            StringStruct(u'ProductVersion', u'{version_str}'),
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""


def parse_version(version_str):
    """Parse a semver string like '1.0.0' into (major, minor, patch) integers."""
    # Strip any pre-release suffix (e.g. '-beta.3') for numeric version fields
    base = version_str.split("-")[0]
    # Split into major.minor.patch components
    parts = base.strip().split(".")
    # Pad with zeros if fewer than 3 parts are present
    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0
    return major, minor, patch


def generate_version_info(version_str, output_path="version_info.txt"):
    """Generate the version_info.txt file used by PyInstaller --version-file flag."""
    # Parse the semantic version string into numeric components
    major, minor, patch = parse_version(version_str)

    # Fill the template with project-specific metadata
    content = VERSION_INFO_TEMPLATE.format(
        major=major,
        minor=minor,
        patch=patch,
        build=0,                                              # Build number (0 for releases)
        company="Aditya Bhalsod",                             # Company or author name
        description="Keep-alive utility that prevents Windows screen lock",  # Shown in file properties
        version_str=version_str,                              # Human-readable version string
        internal_name="AutoWarmUp",                           # Internal product identifier
        copyright="Copyright (c) 2024-2026 Aditya Bhalsod. MIT License.",  # Legal text
        original_filename="AutoWarmUp.exe",                   # Original filename in PE header
        product_name="Auto Warm-Up",                          # Product name in file properties
    )

    # Write the version info file to disk
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Log confirmation for build scripts
    print(f"Version info generated: {output_path} (version={version_str})")


if __name__ == "__main__":
    # Read version from VERSION file or accept as CLI argument
    if len(sys.argv) > 1:
        # Version string passed directly (used by CI)
        ver = sys.argv[1]
    elif os.path.exists("VERSION"):
        # Read from the VERSION file in the project root
        with open("VERSION", "r") as f:
            ver = f.read().strip()
    else:
        # Fallback default version
        ver = "1.0.0"

    # Optional second argument for output file path
    out = sys.argv[2] if len(sys.argv) > 2 else "version_info.txt"
    generate_version_info(ver, out)
