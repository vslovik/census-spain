#!/usr/bin/env bash
# Verify integrity of ADRH files archived on S3.
#
# Three verification levels (run all by default):
#   1. SIZE     — compare S3 object sizes vs locally re-compressed sizes
#   2. CHECKSUM — compare local sha256 manifest vs SHA256 stored in S3 metadata
#   3. ZSTD     — stream each S3 object through `zstd -t` (frame integrity check)
#
# Usage:
#   bash verify_ine_adrh_s3.sh              # all three checks
#   bash verify_ine_adrh_s3.sh size         # size only (fast, ~10s)
#   bash verify_ine_adrh_s3.sh checksum     # checksum manifest only (~15s)
#   bash verify_ine_adrh_s3.sh zstd         # zstd test only (downloads ~1 GB, ~10 min)
#
# Requires: aws CLI, zstd, jq

set -euo pipefail

SRC_DIR="$HOME/.openclaw/workspace/downloads/ine_5650"
S3_BUCKET="hsf-group-ai-spain-hvac"
S3_PREFIX="ine-adrh/raw"
AWS_PROFILE="AWSAdministratorAccess-268271485741"
ZSTD_LEVEL=15
CHECKSUM_FILE="$(dirname "$0")/ine_adrh_checksums.sha256"
TABLES=(30824 30825 30826 30827 30828 30829 30830 30831 30832 37677)
MODE="${1:-all}"

PASS=0; FAIL=0

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
ok()   { echo "  OK  $*"; PASS=$(( PASS + 1 )); }
fail() { echo "  FAIL $*"; FAIL=$(( FAIL + 1 )); }

# ── 1. SIZE CHECK ──────────────────────────────────────────────────────────────
check_sizes() {
    log "=== SIZE CHECK ==="
    log "Re-compressing each file locally and comparing with S3 object size..."
    for table in "${TABLES[@]}"; do
        for ext in csv json; do
            local_file="${SRC_DIR}/${table}.${ext}"
            s3_key="${S3_PREFIX}/${table}.${ext}.zst"
            [[ -f "$local_file" ]] || { log "SKIP: $local_file not found locally"; continue; }

            # Get S3 object size
            s3_size=$(aws s3api head-object \
                --bucket "$S3_BUCKET" \
                --key "$s3_key" \
                --profile "$AWS_PROFILE" \
                --query 'ContentLength' --output text 2>/dev/null) || {
                fail "${table}.${ext}.zst — object not found on S3"
                continue
            }

            # Re-compress locally to get expected size
            local_size=$(zstd -${ZSTD_LEVEL} -c "$local_file" | wc -c)

            if [[ "$s3_size" -eq "$local_size" ]]; then
                ok "${table}.${ext}.zst — size ${s3_size} bytes"
            else
                fail "${table}.${ext}.zst — S3=${s3_size} bytes, local=${local_size} bytes (diff=$(( s3_size - local_size )))"
            fi
        done
    done
}

# ── 2. CHECKSUM CHECK ─────────────────────────────────────────────────────────
check_checksums() {
    log "=== CHECKSUM CHECK (local manifest vs S3 metadata) ==="

    if [[ ! -f "$CHECKSUM_FILE" ]]; then
        log "WARNING: $CHECKSUM_FILE not found. Checksum check requires upload script to have been run."
        log "         Falling back to comparing local recompute vs S3-stored SHA256..."
    fi

    for table in "${TABLES[@]}"; do
        for ext in csv json; do
            s3_key="${S3_PREFIX}/${table}.${ext}.zst"
            filename="${table}.${ext}.zst"

            # Get SHA256 stored in S3 object metadata (set during upload)
            s3_sha256=$(aws s3api head-object \
                --bucket "$S3_BUCKET" \
                --key "$s3_key" \
                --profile "$AWS_PROFILE" \
                --query 'Metadata.sha256' --output text 2>/dev/null) || {
                fail "$filename — object not found on S3"
                continue
            }

            if [[ "$s3_sha256" == "None" || -z "$s3_sha256" ]]; then
                log "  NOTE: $filename — no sha256 metadata (uploaded before checksum support was added)"
                # Fall back to S3 checksum attribute (if uploaded with --checksum-algorithm SHA256)
                s3_sha256=$(aws s3api get-object-attributes \
                    --bucket "$S3_BUCKET" \
                    --key "$s3_key" \
                    --object-attributes Checksum \
                    --profile "$AWS_PROFILE" \
                    --query 'Checksum.ChecksumSHA256' --output text 2>/dev/null || echo "None")
                if [[ "$s3_sha256" == "None" || -z "$s3_sha256" ]]; then
                    log "  SKIP: $filename — no checksum stored (re-upload with updated script to add)"
                    continue
                fi
                # S3 checksum attribute stores base64-encoded SHA256; convert to hex for comparison
                s3_sha256=$(echo "$s3_sha256" | base64 -d | xxd -p | tr -d '\n')
            fi

            # Get local SHA256 from manifest or recompute
            if [[ -f "$CHECKSUM_FILE" ]]; then
                local_sha256=$(grep " ${filename}$" "$CHECKSUM_FILE" | awk '{print $1}' || echo "")
            else
                local_sha256=""
            fi

            if [[ -z "$local_sha256" ]]; then
                local_file="${SRC_DIR}/${table}.${ext}"
                [[ -f "$local_file" ]] || { log "  SKIP: source file not available locally"; continue; }
                log "  Recomputing SHA256 for $filename (not in manifest)..."
                local_sha256=$(zstd -${ZSTD_LEVEL} -c "$local_file" | sha256sum | awk '{print $1}')
            fi

            if [[ "$s3_sha256" == "$local_sha256" ]]; then
                ok "$filename — sha256 ${s3_sha256:0:16}..."
            else
                fail "$filename — local=${local_sha256:0:16}... S3=${s3_sha256:0:16}..."
            fi
        done
    done
}

# ── 3. ZSTD FRAME INTEGRITY CHECK ─────────────────────────────────────────────
check_zstd() {
    log "=== ZSTD FRAME INTEGRITY CHECK (streams from S3, no local storage) ==="
    log "This downloads ~1 GB total. Press Ctrl+C to abort."
    for table in "${TABLES[@]}"; do
        for ext in csv json; do
            s3_key="${S3_PREFIX}/${table}.${ext}.zst"
            filename="${table}.${ext}.zst"

            log "Testing: $filename"
            result=$(aws s3 cp "s3://${S3_BUCKET}/${s3_key}" - \
                --profile "$AWS_PROFILE" --no-progress 2>/dev/null \
                | zstd -t 2>&1) && {
                ok "$filename — zstd frame valid"
            } || {
                fail "$filename — zstd test FAILED: $result"
            }
        done
    done
}

# ── MAIN ───────────────────────────────────────────────────────────────────────
log "Verifying s3://${S3_BUCKET}/${S3_PREFIX}/"
echo ""

case "$MODE" in
    size)      check_sizes ;;
    checksum)  check_checksums ;;
    zstd)      check_zstd ;;
    all)       check_sizes; echo ""; check_checksums; echo ""; check_zstd ;;
    *)         echo "Usage: $0 [size|checksum|zstd|all]"; exit 1 ;;
esac

echo ""
log "=== RESULT: ${PASS} passed, ${FAIL} failed ==="
[[ "$FAIL" -eq 0 ]] && exit 0 || exit 1