#!/usr/bin/env bash
# =============================================================
#  Linux Build Script: Cross-compile auto_warm_up.py to a
#  Windows .exe using Docker (Wine + Python + PyInstaller).
#  No Wine installation needed on host — Docker handles it.
# =============================================================

set -e

# Name for the Docker image used during the build
IMAGE_NAME="auto-warm-up-builder"

# Directory where this script lives (project root)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "=== Auto Warm-Up — Linux → Windows .exe Builder ==="
echo ""

# Step 1: Verify Docker is available
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed. Please install Docker first."
    exit 1
fi

echo "[1/3] Building Docker image (Wine + Python + PyInstaller)..."
echo "       This may take a few minutes on the first run..."
echo ""

# Step 2: Build the Docker image which compiles the .exe during image build
docker build -t "$IMAGE_NAME" "$SCRIPT_DIR"

echo ""
echo "[2/3] Extracting AutoWarmUp.exe from the Docker image..."

# Step 3: Create a temporary container and copy the .exe out of it
# Create output directory on host
mkdir -p "$SCRIPT_DIR/dist"

# Run a throwaway container, copy the built .exe, then remove the container
CONTAINER_ID=$(docker create "$IMAGE_NAME")
docker cp "$CONTAINER_ID:/app/dist/AutoWarmUp.exe" "$SCRIPT_DIR/dist/AutoWarmUp.exe"
docker rm "$CONTAINER_ID" > /dev/null

echo ""
echo "[3/3] Cleaning up Docker build image..."
docker rmi "$IMAGE_NAME" > /dev/null 2>&1 || true

echo ""
echo "============================================================"
echo "  BUILD COMPLETE!"
echo ""
echo "  Your Windows .exe is at:"
echo "    $SCRIPT_DIR/dist/AutoWarmUp.exe"
echo ""
echo "  Copy it to your Windows 11 PC and double-click to run."
echo "============================================================"
echo ""
