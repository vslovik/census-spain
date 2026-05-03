#!/usr/bin/env bash
# Compress ADRH raw files with zstd -15 and stream directly to S3.
# SHA256 checksum of each compressed stream is computed locally and
# stored as S3 object metadata for post-hoc integrity verification.
# Run: bash compress_and_upload_ine_adrh.sh
# Requires: zstd, aws CLI, profile AWSAdministratorAccess-268271485741

set -euo pipefail

SRC_DIR="$HOME/.openclaw/workspace/downloads/ine_5650"
S3_DEST="s3://hsf-group-ai-spain-hvac/ine-adrh/raw"
AWS_PROFILE="AWSAdministratorAccess-268271485741"
ZSTD_LEVEL=15
CHECKSUM_FILE="$(dirname "$0")/ine_adrh_checksums.sha256"

TABLES=(30824 30825 30826 30827 30828 30829 30830 30831 30832 37677)

log() { echo "[$(date '+%H:%M:%S')] $*"; }

upload_file() {
    local src="$1"
    local filename
    filename="$(basename "$src")"
    local dest="${S3_DEST}/${filename}.zst"
    local tmp_zst
    tmp_zst="$(mktemp --suffix=.zst)"

    log "Compressing: $filename"
    local start=$SECONDS
    zstd -${ZSTD_LEVEL} -c "$src" > "$tmp_zst"

    # Compute SHA256 of the compressed file before uploading
    local sha256
    sha256="$(sha256sum "$tmp_zst" | awk '{print $1}')"
    echo "${sha256}  ${filename}.zst" >> "$CHECKSUM_FILE"

    log "Uploading: $filename.zst (sha256=${sha256:0:16}...)"
    aws s3 cp "$tmp_zst" "$dest" \
        --profile "$AWS_PROFILE" \
        --content-encoding zstd \
        --metadata "sha256=${sha256},source=${filename},zstd_level=${ZSTD_LEVEL}" \
        --no-progress

    rm "$tmp_zst"
    local elapsed=$(( SECONDS - start ))
    local size_mb=$(( $(stat -c%s "$src") / 1048576 ))
    log "Done: $filename (${size_mb} MB raw -> S3 in ${elapsed}s)"
}

# Upload metadata manifest first (uncompressed)
log "Uploading tables_with_links.json..."
aws s3 cp "${SRC_DIR}/tables_with_links.json" \
    "${S3_DEST}/tables_with_links.json" \
    --profile "$AWS_PROFILE" --no-progress
log "Manifest uploaded."

# Process each table: CSV then JSON
for table in "${TABLES[@]}"; do
    for ext in csv json; do
        f="${SRC_DIR}/${table}.${ext}"
        if [[ -f "$f" ]]; then
            upload_file "$f"
        else
            log "WARNING: $f not found, skipping."
        fi
    done
done

log "All done. Verifying S3 contents..."
aws s3 ls "${S3_DEST}/" --profile "$AWS_PROFILE" --human-readable
