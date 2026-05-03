#!/usr/bin/env bash
# Extract selected files from CensoPersonas_2021.zip, compress each with
# zstd -15, and upload to S3 with SHA256 integrity metadata.
#
# Source zip: https://www.ine.es/censos2021/CensoPersonas_2021.zip
# Downloaded: April 2024
#
# Files uploaded (others skipped — R/SAS/SPSS/Stata formats not needed):
#   CSV/CensoPersonas_2021.tab   → ine-census-2021/raw/CensoPersonas_2021.tab.zst
#   md_CensoPersonas_2021.txt    → ine-census-2021/raw/md_CensoPersonas_2021.txt.zst
#   dr_CensoPersonas_2021.xlsx   → ine-census-2021/raw/dr_CensoPersonas_2021.xlsx.zst
#   Leeme.txt                    → ine-census-2021/raw/Leeme.txt.zst
#
# Run from project root: bash compress_and_upload_censo_personas.sh
# Requires: unzip, zstd, aws CLI (profile AWSAdministratorAccess-268271485741)

set -euo pipefail

ZIP_FILE="data/input/ine_census_2021/CensoPersonas_2021.zip"
S3_DEST="s3://hsf-group-ai-spain-hvac/ine-census-2021/raw"
AWS_PROFILE="AWSAdministratorAccess-268271485741"
ZSTD_LEVEL=15
CHECKSUM_FILE="$(dirname "$0")/censo_personas_checksums.sha256"
TMP_DIR="$(mktemp -d)"

# zip_internal_path:target_filename pairs (tab-separated for readability)
FILES=(
    "CSV/CensoPersonas_2021.tab	CensoPersonas_2021.tab"
    "md_CensoPersonas_2021.txt	md_CensoPersonas_2021.txt"
    "dr_CensoPersonas_2021.xlsx	dr_CensoPersonas_2021.xlsx"
    "Leeme.txt	Leeme.txt"
)

log()     { echo "[$(date '+%H:%M:%S')] $*"; }
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

compress_and_upload() {
    local src="$1"
    local filename="$2"
    local tmp_zst="${TMP_DIR}/${filename}.zst"

    log "Compressing: $filename"
    local start=$SECONDS
    zstd -${ZSTD_LEVEL} -c "$src" > "$tmp_zst"

    local sha256
    sha256="$(sha256sum "$tmp_zst" | awk '{print $1}')"
    echo "${sha256}  ${filename}.zst" >> "$CHECKSUM_FILE"

    local size_mb
    size_mb=$(( $(stat -c%s "$src") / 1048576 ))

    log "Uploading: ${filename}.zst  sha256=${sha256:0:16}...  (${size_mb} MB raw)"
    aws s3 cp "$tmp_zst" "${S3_DEST}/${filename}.zst" \
        --profile "$AWS_PROFILE" \
        --content-encoding zstd \
        --metadata "sha256=${sha256},source=${filename},zstd_level=${ZSTD_LEVEL},origin_zip=CensoPersonas_2021.zip,origin_url=https://www.ine.es/censos2021/CensoPersonas_2021.zip" \
        --no-progress

    rm "$tmp_zst"
    local elapsed=$(( SECONDS - start ))
    log "Done: $filename  (${elapsed}s)"
}

# --- extract ---
log "Extracting selected files from: $ZIP_FILE"
for entry in "${FILES[@]}"; do
    zip_path="${entry%%	*}"
    local_name="${entry##*	}"
    log "  $zip_path → $local_name"
    unzip -p "$ZIP_FILE" "$zip_path" > "${TMP_DIR}/${local_name}"
done
log "Extraction complete."

# --- compress + upload ---
for entry in "${FILES[@]}"; do
    local_name="${entry##*	}"
    compress_and_upload "${TMP_DIR}/${local_name}" "$local_name"
done

log "All uploads done."
log ""
log "S3 contents:"
aws s3 ls "${S3_DEST}/" --profile "$AWS_PROFILE" --human-readable