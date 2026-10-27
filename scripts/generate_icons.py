#!/usr/bin/env python3
# Copyright © 2026 Christopher Snow
"""Regenerate checked-in PNG app icons. Requires Playwright and Chromium."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
svg = (ROOT / "assets/app-icon.svg").read_text()
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="chromium")
    page = browser.new_page(device_scale_factor=1)
    for size, name in [(180, "apple-touch-icon"), (192, "icon-192"), (512, "icon-512")]:
        page.set_viewport_size({"width": size, "height": size})
        page.set_content('<style>html,body{margin:0}svg{display:block;width:100vw;height:100vh}</style>' + svg)
        page.screenshot(path=str(ROOT / f"assets/{name}.png"))
    browser.close()
