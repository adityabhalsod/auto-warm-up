# Use Wine + Python base image for cross-compiling to Windows
FROM tobix/pywine:3.12

# Set working directory inside the container
WORKDIR /app

# Install osslsigncode for self-signing the .exe (reduces AV false positives)
RUN apt-get update && apt-get install -y --no-install-recommends \
    osslsigncode openssl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency list first (leverages Docker layer caching)
COPY requirements.txt .

# Install Python packages inside Wine's Python environment
RUN xvfb-run sh -c "wine pip install -r requirements.txt; wineserver -w"

# Copy all build scripts and source code into the container
COPY auto_warm_up.py generate_icon.py generate_version_info.py sign_exe.sh VERSION ./

# Step 1: Generate the multi-size .ico icon file using Pillow (runs under Wine Python)
RUN xvfb-run sh -c "wine python generate_icon.py app.ico; wineserver -w"

# Step 2: Generate PE version info from the VERSION file (embeds metadata in .exe)
RUN xvfb-run sh -c "wine python generate_version_info.py; wineserver -w"

# Step 3: Build the standalone .exe with icon and version info embedded
RUN xvfb-run sh -c "\
    wine pyinstaller \
    --onefile \
    --noconsole \
    --name AutoWarmUp \
    --icon=app.ico \
    --version-file=version_info.txt \
    auto_warm_up.py; \
    wineserver -w"

# Step 4: Self-sign the .exe with a generated certificate (no external secrets needed)
RUN bash sign_exe.sh dist/AutoWarmUp.exe "Auto Warm-Up" "https://github.com/adityabhalsod/auto-warm-up"

# Default command: list the output to confirm the build succeeded
CMD ["ls", "-lh", "dist/"]
