#!/usr/bin/env python3
"""
Verify that all JSON download links in tables_with_links.json are alive
by downloading the first 1MB of each and checking it looks like valid JSON.

Usage:
    python3 ine_verify_links.py
"""

import json
import urllib.request
from pathlib import Path

DOWNLOADS_DIR   = Path.home() / ".openclaw/workspace/downloads/ine_5650"
TABLES_FILE     = DOWNLOADS_DIR / "tables_with_links.json"
CHUNK_SIZE      = 1 * 1024 * 1024  # 1 MB
TIMEOUT         = 30

tables = json.loads(TABLES_FILE.read_text())

print(f"Verifying {len(tables)} tables\n")
print(f"{'ID':<8} {'Status':<8} {'Bytes':<12} {'Looks like JSON':<16} Title")
print("-" * 90)

all_ok = True

for t in tables:
    tid      = t["id"]
    url      = t.get("json_url")
    title    = t.get("title", "")[:50]

    if not url:
        print(f"{tid:<8} {'NO URL':<8} {'':<12} {'':<16} {title}")
        all_ok = False
        continue

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            status = resp.status
            chunk  = resp.read(CHUNK_SIZE)
            first  = chunk.lstrip()
            looks_json = first[:1] in (b"[", b"{")
            print(f"{tid:<8} {status:<8} {len(chunk):<12,} {'✅ yes' if looks_json else '❌ no':<16} {title}")
            if not looks_json:
                print(f"         preview: {first[:120]}")
                all_ok = False
    except Exception as e:
        print(f"{tid:<8} {'ERROR':<8} {'':<12} {'❌':<16} {e}")
        all_ok = False

print()
print("✅ All links OK" if all_ok else "❌ Some links failed — check above")
