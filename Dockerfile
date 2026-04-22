# Use Wine + Python base image for cross-compiling to Windows
FROM tobix/pywine:3.12

# Set working directory inside the container
WORKDIR /app

# Copy dependency list first (leverages Docker layer caching)
COPY requirements.txt .

# Install Python packages inside Wine's Python environment.
# Note: the Linux/Docker path uses PyInstaller (Nuitka cross-compile via Wine
# is not reliably supported). Local Windows builds should prefer Nuitka via
# build.bat, which produces binaries with far fewer antivirus false positives.
RUN xvfb-run sh -c "wine pip install -r requirements.txt; wineserver -w"

# Copy all build scripts and source code into the container
COPY auto_warm_up.py generate_icon.py generate_version_info.py VERSION ./

# Step 1: Generate the multi-size .ico icon file using Pillow (runs under Wine Python)
RUN xvfb-run sh -c "wine python generate_icon.py app.ico; wineserver -w"

# Step 2: Generate PE version info from the VERSION file (embeds metadata in .exe)
RUN xvfb-run sh -c "wine python generate_version_info.py; wineserver -w"

# Step 3: Build the standalone .exe with icon and version info embedded.
# Flags tuned to reduce antivirus false positives:
#   --noupx : never UPX-pack (UPX-packed binaries are heavily flagged by AV)
#   --clean : wipe PyInstaller cache so the build is reproducible
# Signing is done OUTSIDE Docker (on the CI runner) to keep secrets out of image layers.
RUN xvfb-run sh -c "\
    wine pyinstaller \
    --onefile \
    --noconsole \
    --noupx \
    --clean \
    --name AutoWarmUp \
    --icon=app.ico \
    --version-file=version_info.txt \
    auto_warm_up.py; \
    wineserver -w"

# Default command: list the output to confirm the build succeeded
CMD ["ls", "-lh", "dist/"]
