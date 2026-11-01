#!/usr/bin/env python3
"""Check Chapter 1 media pause, old links, glossary and responsive reading."""
import sys
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
base = sys.argv[1]
for folder in ('media/chapter-01', 'media/audio/chapter-01'):
    assert not (ROOT / '_site/assets' / folder).exists(), folder
with sync_playwright() as pw:
    browser = pw.chromium.launch(channel='chromium')
    page = browser.new_page(service_workers='block')
    page.goto(urljoin(base, 'chapters/01-before-you-explain.html'))
    assert page.locator('video,audio').count() == 0
    assert page.locator('a[href*="audio/chapter-01"],a[href*="media/chapter-01"]').count() == 0
    for anchor in ('separate-layers', 'what-did-rowan-actually-say', 'check-an-answer', 'check-own-account', 'choose-response', 'week-correspondence'):
        assert page.locator(f'#{anchor}').count() == 1, anchor
    definitions = page.locator('.definition dd').all_text_contents()
    for width in (390, 834, 1440):
        page.set_viewport_size({'width': width, 'height': 950})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.screenshot(path=f'/tmp/chapter-one-{width}.png', full_page=True)
    page.goto(urljoin(base, 'glossary.html'))
    for definition in definitions:
        assert ' '.join(definition.split()) in ' '.join(page.locator('body').inner_text().split())
    page.goto(urljoin(base, 'audio/chapter-01.html'))
    assert page.locator('video,audio').count() == 0
    page.get_by_role('link', name='Read the revised chapter: Why we misinterpret people').click()
    assert page.url.endswith('/chapters/01-before-you-explain.html')
    for path in ('reference/declining-help.html', 'worksheet.html'):
        page.goto(urljoin(base, path))
        assert page.locator('a[href*="audio/chapter-01"]').count() == 0
    browser.close()
print('Passed: removed published Chapter 1 media, old audio link notice, stable anchors, matching definitions and responsive layouts.')
