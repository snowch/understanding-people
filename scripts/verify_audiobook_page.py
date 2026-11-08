#!/usr/bin/env python3
"""Reader journeys for whole-book downloads; never downloads hundreds of MB implicitly."""
import argparse
import functools
import json
import os
from pathlib import Path
import threading
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright, expect
from book_audiobook import MANIFEST
from page_narration import ROOT
from verify_page_narration import RangeHandler, ThreadingHTTPServer


def verify(base, screenshots=False):
    base = base.rstrip('/')+'/'
    manifest = json.loads(MANIFEST.read_text())
    with sync_playwright() as pw:
        proxy = {'server':os.environ['HTTPS_PROXY']} if base.startswith('https://') and os.environ.get('HTTPS_PROXY') else None
        browser = pw.chromium.launch(proxy=proxy)
        context = browser.new_context(proxy=proxy, service_workers='block')
        page = context.new_page()
        errors, media = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: media.append(request.url) if urlsplit(request.url).path.endswith(('.m4b','.mp3')) else None)
        page.goto(base+'chapters/01-before-you-explain.html')
        page.locator('.page-narration .narration-sections > summary').click()
        page.locator('.page-narration .whole-book-download').click()
        expect(page).to_have_url(base+'downloads/index.html')
        expect(page.locator('h1')).to_have_text('Download the audiobook')
        expect(page.locator('.page-narration')).to_have_count(0)
        expect(page.locator('.audiobook-edition')).to_have_count(2)
        for voice, record in manifest['voices'].items():
            card = page.locator(f'[data-audiobook-voice="{voice}"]')
            link = card.locator('.audiobook-download')
            expect(link).to_be_visible()
            expect(link).to_have_attribute('href', record['editions']['complete']['url'])
            expect(card).to_contain_text(f'{len(record["editions"]["complete"]["chapters"])} chapters')
            assert link.get_attribute('href').endswith('.m4b')
        expect(page.locator('[data-audiobook-voice="andrew"]')).to_have_attribute('data-preferred','true')
        page.evaluate('window.BookSettings.set({voice:"jenny"})')
        expect(page.locator('[data-audiobook-voice="jenny"]')).to_have_attribute('data-preferred','true')
        page.reload()
        expect(page.locator('[data-audiobook-voice="jenny"] [data-download-preferred]')).to_be_visible()
        page.locator('.audiobook-preview').first.click()
        expect(page.locator('h1')).to_have_text('Settings')
        expect(page.locator('[data-reading-return]')).to_have_attribute('href',base+'downloads/index.html')
        page.locator('[data-reading-return]').click()
        expect(page).to_have_url(base+'downloads/index.html')
        expect(page.locator('.audiobook-course')).not_to_have_attribute('open','')
        page.locator('.audiobook-course > summary').focus()
        page.keyboard.press('Enter')
        for voice, record in manifest['voices'].items():
            link = page.locator(f'.audiobook-course a[href="{record["editions"]["course"]["url"]}"]')
            expect(link).to_be_visible()
        expect(page.locator('.audiobook-course')).to_contain_text('14 chapters')
        page.locator('.audiobook-contents > summary').click()
        expect(page.locator('.audiobook-contents ol li')).to_have_count(14)
        assert not media, media
        for width in [320,390,834,1440]:
            for scheme in ['light','dark']:
                page.set_viewport_size({'width':width,'height':1000});page.emulate_media(color_scheme=scheme)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), (width,scheme)
                if screenshots and width in [390,1440]:
                    page.locator('.audiobook-course').evaluate('e=>e.open=false')
                    page.locator('.audiobook-contents').evaluate('e=>e.open=false')
                    page.screenshot(path=f'/tmp/audiobook-page-{width}-{scheme}.png',full_page=True)
        # Native links remain available without JS, rather than a scripted export.
        nojs = browser.new_context(proxy=proxy, java_script_enabled=False, service_workers='block')
        n = nojs.new_page();n.goto(base+'downloads/index.html')
        expect(n.locator('.audiobook-edition .audiobook-download')).to_have_count(2)
        for link in n.locator('.audiobook-edition .audiobook-download').all():
            expect(link).to_be_visible()
        assert not errors, errors
        browser.close()
    print('Passed: lesson-to-download navigation, two whole-book single-file choices, optional course-only files, complete chapter list, persistent preferred-voice highlighting, keyboard disclosures, no automatic downloads, no-JavaScript links and responsive light/dark layouts.')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base',nargs='?');parser.add_argument('--screenshots',action='store_true')
    args=parser.parse_args()
    if args.base:verify(args.base,args.screenshots)
    else:
        server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(RangeHandler,directory=str(ROOT/'_site')))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:verify(f'http://localhost:{server.server_port}/understanding-people/',args.screenshots)
        finally:server.shutdown()
