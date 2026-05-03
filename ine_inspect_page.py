#!/usr/bin/env python3
"""
Inspect the INE dlgExport page to find download buttons/links.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path

with sync_playwright() as p:
    br = p.chromium.launch_persistent_context(
        str(Path.home() / '.openclaw/browser/openclaw/user-data'), headless=True)
    page = br.new_page()
    page.goto('https://www.ine.es/jaxiT3/dlgExport.htm?t=30829&L=0',
              wait_until='networkidle', timeout=60000)

    for el in page.query_selector_all('a, button, input[type=button], input[type=submit]'):
        txt    = el.inner_text().strip()
        href   = el.get_attribute('href') or ''
        onclick = el.get_attribute('onclick') or ''
        if txt or onclick:
            print(f'TEXT={repr(txt[:60])}\n  HREF={href[:100]}\n  ONCLICK={onclick[:100]}\n')

    br.close()
