#!/usr/bin/env bash
# =============================================================
#  Self-sign a Windows .exe using osslsigncode.
#  Generates a temporary self-signed certificate, signs the
#  binary, and embeds a timestamp. No external CA needed.
#  This reduces antivirus false positives significantly.
# =============================================================

set -e

# Path to the .exe to sign (first argument, defaults to dist/AutoWarmUp.exe)
EXE_PATH="${1:-dist/AutoWarmUp.exe}"
# Product description embedded in the signature (second argument)
DESCRIPTION="${2:-Auto Warm-Up}"
# Product URL embedded in the signature (third argument)
URL="${3:-https://github.com/adityabhalsod/auto-warm-up}"

# Temporary directory for certificate files (cleaned up after signing)
CERT_DIR=$(mktemp -d)
# Paths for the generated key and certificate
KEY_FILE="${CERT_DIR}/signing.key"
CERT_FILE="${CERT_DIR}/signing.crt"
PFX_FILE="${CERT_DIR}/signing.pfx"
# Signed output replaces the original .exe
SIGNED_EXE="${EXE_PATH}.signed"

echo ""
echo "=== Self-Signing Windows .exe ==="
echo "  Input:  ${EXE_PATH}"
echo ""

# Step 1: Generate a self-signed RSA certificate valid for 10 years
echo "[1/3] Generating self-signed certificate..."
openssl req -x509 \
    -newkey rsa:2048 \
    -keyout "${KEY_FILE}" \
    -out "${CERT_FILE}" \
    -days 3650 \
    -nodes \
    -subj "/CN=Aditya Bhalsod/O=Auto Warm-Up/L=Ahmedabad/ST=Gujarat/C=IN" \
    2>/dev/null

# Step 2: Convert to PKCS#12 format (.pfx) required by osslsigncode
echo "[2/3] Converting to PKCS#12 format..."
openssl pkcs12 -export \
    -out "${PFX_FILE}" \
    -inkey "${KEY_FILE}" \
    -in "${CERT_FILE}" \
    -passout pass: \
    2>/dev/null

# Step 3: Sign the .exe with the self-signed certificate
echo "[3/3] Signing ${EXE_PATH}..."
osslsigncode sign \
    -pkcs12 "${PFX_FILE}" \
    -pass "" \
    -n "${DESCRIPTION}" \
    -i "${URL}" \
    -t http://timestamp.digicert.com \
    -in "${EXE_PATH}" \
    -out "${SIGNED_EXE}" \
    2>/dev/null || {
        # If timestamping fails (network issue), sign without timestamp
        echo "  Warning: Timestamp server unreachable, signing without timestamp..."
        osslsigncode sign \
            -pkcs12 "${PFX_FILE}" \
            -pass "" \
            -n "${DESCRIPTION}" \
            -i "${URL}" \
            -in "${EXE_PATH}" \
            -out "${SIGNED_EXE}"
    }

# Replace the original with the signed version
mv "${SIGNED_EXE}" "${EXE_PATH}"

# Clean up temporary certificate files (don't leave private keys lying around)
rm -rf "${CERT_DIR}"

# Verify the signature was applied
echo ""
echo "  Signed successfully: ${EXE_PATH}"
osslsigncode verify "${EXE_PATH}" 2>/dev/null | head -5 || true
echo ""
echo "=== Signing Complete ==="
echo ""
