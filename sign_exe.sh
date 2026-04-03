#!/usr/bin/env bash
# =============================================================
#  Sign a Windows .exe using osslsigncode (Authenticode).
#
#  Mode 1 — CA-signed (for CI/CD):
#    Requires CODESIGN_PFX_BASE64 and CODESIGN_PFX_PASSWORD
#    environment variables. Uses a real CA-issued .pfx certificate
#    so Windows SmartScreen displays the Publisher name.
#
#  Mode 2 — Self-signed (fallback for local dev):
#    If no PFX is provided, generates a temporary self-signed
#    certificate. Publisher will NOT appear on SmartScreen but
#    PE metadata will still show in file properties.
#
#  Usage:
#    # CA-signed (set env vars first):
#    export CODESIGN_PFX_BASE64="<base64-encoded .pfx>"
#    export CODESIGN_PFX_PASSWORD="<pfx password>"
#    bash sign_exe.sh dist/AutoWarmUp.exe
#
#    # Self-signed fallback (no env vars):
#    bash sign_exe.sh dist/AutoWarmUp.exe
# =============================================================

set -e

# Path to the .exe to sign (first argument, defaults to dist/AutoWarmUp.exe)
EXE_PATH="${1:-dist/AutoWarmUp.exe}"
# Product description embedded in the Authenticode signature
DESCRIPTION="${2:-Auto Warm-Up}"
# Product URL embedded in the Authenticode signature
URL="${3:-https://github.com/adityabhalsod/auto-warm-up}"

# Temporary working directory for certificate files (cleaned up at exit)
CERT_DIR=$(mktemp -d)
# Ensure cleanup runs no matter what happens
trap 'rm -rf "${CERT_DIR}"' EXIT

# Output paths
PFX_FILE="${CERT_DIR}/signing.pfx"
SIGNED_EXE="${EXE_PATH}.signed"

echo ""
echo "=== Authenticode Signing ==="
echo "  Input: ${EXE_PATH}"
echo ""

# ---------------------------------------------------------------
#  Detect signing mode: CA-signed vs self-signed fallback
# ---------------------------------------------------------------
if [ -n "${CODESIGN_PFX_BASE64:-}" ]; then
    # --- Mode 1: CA-issued certificate from environment variable ---
    echo "[MODE] CA-signed certificate detected"
    echo ""

    # Decode the base64-encoded .pfx file from the environment variable
    echo "[1/2] Decoding .pfx certificate..."
    echo "${CODESIGN_PFX_BASE64}" | base64 -d > "${PFX_FILE}"

    # Password for the .pfx (can be empty string for passwordless certs)
    PFX_PASSWORD="${CODESIGN_PFX_PASSWORD:-}"

    # Sign with SHA-256 Authenticode + RFC 3161 timestamp from DigiCert
    echo "[2/2] Signing with CA certificate (SHA-256 Authenticode)..."
    osslsigncode sign \
        -pkcs12 "${PFX_FILE}" \
        -pass "${PFX_PASSWORD}" \
        -h sha256 \
        -n "${DESCRIPTION}" \
        -i "${URL}" \
        -ts http://timestamp.digicert.com \
        -in "${EXE_PATH}" \
        -out "${SIGNED_EXE}"

    echo "  Signed with CA certificate — Publisher will appear on SmartScreen"

elif [ -n "${CODESIGN_PFX_FILE:-}" ] && [ -f "${CODESIGN_PFX_FILE}" ]; then
    # --- Mode 1b: CA-issued certificate from a file path ---
    echo "[MODE] CA-signed certificate file detected: ${CODESIGN_PFX_FILE}"
    echo ""

    # Copy the .pfx to the temp directory for consistent handling
    cp "${CODESIGN_PFX_FILE}" "${PFX_FILE}"

    # Password for the .pfx (can be empty string for passwordless certs)
    PFX_PASSWORD="${CODESIGN_PFX_PASSWORD:-}"

    # Sign with SHA-256 Authenticode + RFC 3161 timestamp
    echo "[1/1] Signing with CA certificate (SHA-256 Authenticode)..."
    osslsigncode sign \
        -pkcs12 "${PFX_FILE}" \
        -pass "${PFX_PASSWORD}" \
        -h sha256 \
        -n "${DESCRIPTION}" \
        -i "${URL}" \
        -ts http://timestamp.digicert.com \
        -in "${EXE_PATH}" \
        -out "${SIGNED_EXE}"

    echo "  Signed with CA certificate — Publisher will appear on SmartScreen"

else
    # --- Mode 2: Self-signed fallback (local dev only) ---
    echo "[MODE] No CA certificate found — falling back to self-signed"
    echo "  WARNING: Self-signed = Publisher will NOT appear on SmartScreen"
    echo "  To fix: set CODESIGN_PFX_BASE64 + CODESIGN_PFX_PASSWORD env vars"
    echo ""

    # Paths for self-signed cert generation
    KEY_FILE="${CERT_DIR}/signing.key"
    CERT_FILE="${CERT_DIR}/signing.crt"
    CONF_FILE="${CERT_DIR}/codesign.cnf"

    # Create OpenSSL config with Code Signing EKU extension
    echo "[1/4] Creating code-signing certificate config..."
    cat > "${CONF_FILE}" <<'SSLCONF'
[req]
distinguished_name = req_dn
x509_extensions    = v3_code
prompt             = no

[req_dn]
CN = Aditya Bhalsod
O  = Auto Warm-Up
L  = Rajkot
ST = Gujarat
C  = IN

[v3_code]
keyUsage               = critical, digitalSignature
extendedKeyUsage       = critical, codeSigning
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid,issuer
basicConstraints       = critical, CA:FALSE
SSLCONF

    # Generate RSA-2048 + SHA-256 self-signed certificate (10-year validity)
    echo "[2/4] Generating self-signed code-signing certificate..."
    openssl req -x509 \
        -newkey rsa:2048 \
        -sha256 \
        -keyout "${KEY_FILE}" \
        -out "${CERT_FILE}" \
        -days 3650 \
        -nodes \
        -config "${CONF_FILE}" \
        2>/dev/null

    # Log certificate details for debugging
    echo "  Subject: $(openssl x509 -in "${CERT_FILE}" -noout -subject 2>/dev/null)"

    # Convert to PKCS#12 format required by osslsigncode
    echo "[3/4] Converting to PKCS#12 format..."
    openssl pkcs12 -export \
        -out "${PFX_FILE}" \
        -inkey "${KEY_FILE}" \
        -in "${CERT_FILE}" \
        -passout pass: \
        2>/dev/null

    # Sign with the self-signed certificate
    echo "[4/4] Signing with self-signed certificate (SHA-256 Authenticode)..."
    osslsigncode sign \
        -pkcs12 "${PFX_FILE}" \
        -pass "" \
        -h sha256 \
        -n "${DESCRIPTION}" \
        -i "${URL}" \
        -ts http://timestamp.digicert.com \
        -in "${EXE_PATH}" \
        -out "${SIGNED_EXE}" \
        2>/dev/null || {
            # Timestamp server might be unreachable during Docker build
            echo "  Warning: Timestamp failed, signing without timestamp..."
            osslsigncode sign \
                -pkcs12 "${PFX_FILE}" \
                -pass "" \
                -h sha256 \
                -n "${DESCRIPTION}" \
                -i "${URL}" \
                -in "${EXE_PATH}" \
                -out "${SIGNED_EXE}"
        }

    echo "  Signed with self-signed certificate (Publisher hidden on SmartScreen)"
fi

# Replace the original .exe with the signed version
mv "${SIGNED_EXE}" "${EXE_PATH}"

# Show signature verification in build logs
echo ""
echo "  Output: ${EXE_PATH}"
echo "  --- Signature details ---"
osslsigncode verify "${EXE_PATH}" 2>&1 | grep -E "Signature|Subject|serial" | head -10 || true
echo ""
echo "=== Signing Complete ==="
echo ""
echo "  --- Signature details ---"
osslsigncode verify "${EXE_PATH}" 2>&1 | grep -E "Signature|Subject|serial" | head -10 || true
echo ""
echo "=== Signing Complete ==="
echo ""
