# Use Wine + Python base image for cross-compiling to Windows
FROM tobix/pywine:3.12

# Set working directory inside the container
WORKDIR /app

# Copy dependency list first (leverages Docker layer caching)
COPY requirements.txt .

# Install Python packages inside Wine's Python environment
RUN wine pip install -r requirements.txt 2>/dev/null

# Copy the application source code
COPY auto_warm_up.py .

# Build the standalone Windows .exe (single file, no console window)
RUN wine pyinstaller --onefile --noconsole --name AutoWarmUp auto_warm_up.py 2>/dev/null

# Default command: just list the output to confirm the build succeeded
CMD ["ls", "-lh", "dist/"]
