#!/usr/bin/env python3
# Copyright © 2026 Christopher Snow
"""Browser checks against a served build. Requires Playwright and Chromium.

Usage: python scripts/verify_install.py http://127.0.0.1:8000/understanding-people/_site/
Native install events are simulated; OS installation itself needs a real browser.
"""
import sys
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
from build import PAGES, destination

base = sys.argv[1]
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="chromium")
    context = browser.new_context()
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(urljoin(base, "chapters/09-truth-lies-uncertainty.html"))
    page.evaluate("navigator.serviceWorker.ready")
    page.wait_for_function("navigator.serviceWorker.controller !== null")
    assert page.evaluate("navigator.serviceWorker.controller.scriptURL") == urljoin(base, "sw.js")
    assert page.locator('link[rel="manifest"]').evaluate("e => e.href") == urljoin(base, "manifest.webmanifest")
    manifest = context.request.get(urljoin(base, "manifest.webmanifest")).json()
    assert manifest["scope"] == "./" and manifest["start_url"] == "./"
    for icon in manifest["icons"]:
        response = context.request.get(urljoin(base, icon["src"]))
        assert response.ok and response.headers["content-type"].startswith("image/png")
    for width in [320, 390, 834, 1440]:
        page.set_viewport_size({"width": width, "height": 900})
        assert page.locator('.brand').is_visible()
        assert page.get_by_role("button", name="Install Understanding people").is_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    # Reload without service-worker support to make the manual-help path deterministic.
    help_context = browser.new_context(service_workers="block", viewport={"width": 390, "height": 844})
    help_page = help_context.new_page()
    help_page.goto(base)
    help_page.get_by_role("button", name="Install Understanding people").click()
    assert help_page.get_by_role("dialog").is_visible()
    help_page.keyboard.press("Escape")
    assert not help_page.get_by_role("dialog").is_visible()
    assert help_page.get_by_role("button", name="Install Understanding people").evaluate("e => e === document.activeElement")
    for outcome in ["dismissed", "accepted"]:
        help_page.evaluate("""outcome => {
          const event = new Event('beforeinstallprompt', {cancelable:true});
          event.prompt = async () => { window.promptCalls = (window.promptCalls || 0) + 1; };
          event.userChoice = Promise.resolve({outcome});
          dispatchEvent(event);
        }""", outcome)
        help_page.get_by_role("button", name="Install Understanding people").click()
        help_page.wait_for_function("!document.querySelector('.install-button').disabled")
    assert help_page.evaluate("window.promptCalls") == 2
    help_page.evaluate("dispatchEvent(new Event('appinstalled'))")
    assert help_page.locator('.install-button').is_hidden()
    standalone_context = browser.new_context()
    standalone_context.add_init_script("Object.defineProperty(navigator, 'standalone', {value:true})")
    standalone_page = standalone_context.new_page()
    standalone_page.goto(base)
    assert standalone_page.locator('.install-button').is_hidden()
    # All chapters are saved, even if not previously visited, including hashed CSS URLs.
    context.set_offline(True)
    for path in ['', *(destination(source).as_posix() for source, _ in PAGES)]:
        response = page.goto(urljoin(base, path))
        assert response.ok, path
        assert page.locator('h1').count() == 1
        assert page.locator('.copyright').inner_text() == '© 2026 Christopher Snow'
        assert page.evaluate("getComputedStyle(document.body).backgroundColor") == 'rgb(248, 247, 242)'
    assert not errors, errors
    browser.close()
    print('Passed: install events, manual-help dialog, focus, installed state, manifest/icons, responsive header and all book pages offline.')
