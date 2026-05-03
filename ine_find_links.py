#!/usr/bin/env python3
"""
For each table in tables.json, visit its dlgExport page and extract
the direct JSON API link (servicios.ine.es/wstempus/...).

Saves results to tables_with_links.json.

Usage:
    python3 ine_find_links.py
"""

import json
from pathlib import Path
from playwright.sync_api import sync_playwright

DOWNLOADS_DIR = Path.home() / ".openclaw/workspace/downloads/ine_5650"
TABLES_FILE   = DOWNLOADS_DIR / "tables.json"
OUTPUT_FILE   = DOWNLOADS_DIR / "tables_with_links.json"
USER_DATA_DIR = Path.home() / ".openclaw/browser/openclaw/user-data"

tables = json.loads(TABLES_FILE.read_text())
results = []

with sync_playwright() as p:
    br = p.chromium.launch_persistent_context(str(USER_DATA_DIR), headless=True)
    page = br.new_page()

    for table in tables:
        tid = table["id"]
        export_url = table["export_url"]
        print(f"→ Inspecting table {tid} ...")

        page.goto(export_url, wait_until="networkidle", timeout=60_000)

        # Extract all links
        json_url  = None
        xlsx_url  = None
        csv_sc_url = None

        for el in page.query_selector_all("a"):
            href = el.get_attribute("href") or ""
            if "wstempus" in href and "DATOS_TABLA" in href:
                json_url = href
            if href.endswith(".xlsx"):
                xlsx_url = "https://www.ine.es/jaxiT3/" + href if not href.startswith("http") else href
            if "csv_bdsc" in href:
                csv_sc_url = "https://www.ine.es/jaxiT3/" + href if not href.startswith("http") else href

        # Get page title for table name
        title = page.title()

        entry = {
            "id": tid,
            "title": title,
            "export_url": export_url,
            "json_url": json_url,
            "xlsx_url": xlsx_url,
            "csv_sc_url": csv_sc_url,
        }
        results.append(entry)

        print(f"  title    : {title[:70]}")
        print(f"  json_url : {json_url}")
        print(f"  xlsx_url : {xlsx_url}")
        print(f"  csv_url  : {csv_sc_url}")
        print()

    br.close()

OUTPUT_FILE.write_text(json.dumps(results, indent=2, ensure_ascii=False))
print(f"Saved {len(results)} entries to {OUTPUT_FILE}")
