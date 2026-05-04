#!/usr/bin/env python3
"""
Download INE Atlas de distribución de renta tables using direct JSON API URLs.
No browser required — plain wget-style streaming download.

Source of URLs: tables_with_links.json (produced by ine_find_links.py)

Usage:
    python3 ine_download.py              # download all missing
    python3 ine_download.py 30829        # download a single table by ID
    python3 ine_download.py --all        # re-download everything (overwrite)
"""

import json
import sys
import urllib.request
from pathlib import Path

DOWNLOADS_DIR = Path(__file__).parent / "data/input/ine_adrh"
TABLES_FILE   = DOWNLOADS_DIR / "tables_with_links.json"
CHUNK         = 1024 * 1024   # 1 MB read chunks
TIMEOUT       = 600           # seconds per file

# ── Args ───────────────────────────────────────────────────────────────────────
force_all = "--all" in sys.argv
target_id = next((a for a in sys.argv[1:] if not a.startswith("-")), None)

# ── Load table list ────────────────────────────────────────────────────────────
if not TABLES_FILE.exists():
    print(f"Error: {TABLES_FILE} not found.")
    print("Run ine_find_links.py first to discover all download URLs.")
    sys.exit(1)

tables = json.loads(TABLES_FILE.read_text())

if target_id and not any(t["id"] == target_id for t in tables):
    print(f"Error: table ID '{target_id}' not found.")
    print(f"Known IDs: {[t['id'] for t in tables]}")
    sys.exit(1)

# ── Decide what to download ────────────────────────────────────────────────────
already_done = {p.stem for p in DOWNLOADS_DIR.glob("*.json") if p.stem != "tables"}

if target_id:
    remaining = [t for t in tables if t["id"] == target_id]
elif force_all:
    remaining = tables
else:
    remaining = [t for t in tables if t["id"] not in already_done]

if not remaining:
    print("✅  All files already downloaded. Use --all to re-download.")
    sys.exit(0)

print(f"Already done : {sorted(already_done)}")
print(f"To download  : {[t['id'] for t in remaining]}")
print()

# ── Download ───────────────────────────────────────────────────────────────────
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

for table in remaining:
    tid  = table["id"]
    url  = table.get("json_url")
    dest = DOWNLOADS_DIR / f"{tid}.json"

    if not url:
        print(f"⚠️  {tid}: no json_url in tables_with_links.json — skipping")
        continue

    print(f"→ {tid}: {table.get('title', '')[:60]}")
    print(f"  {url}")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp, \
             open(dest, "wb") as f:
            downloaded = 0
            while True:
                chunk = resp.read(CHUNK)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                print(f"  {downloaded / 1_048_576:.1f} MB ...", end="\r")

        size_mb = dest.stat().st_size / 1_048_576
        print(f"  ✅  Saved {dest.name}  ({size_mb:.1f} MB)        ")

    except Exception as e:
        print(f"  ❌  Failed: {e}")

    print()

print("Done. Files in:", DOWNLOADS_DIR)
