#!/usr/bin/env python3
"""Real reading-list journeys, storage failures, privacy and offline/base-path checks.

With no argument serves _site locally under /understanding-people/.
Pass a deployed project URL for a smaller live smoke check. No media is fetched.
"""
import functools
import json
import os
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright, expect
from verify_page_narration import RangeHandler

ROOT = Path(__file__).resolve().parents[1]
server = None
live = len(sys.argv) > 1
if live:
    base = sys.argv[1].rstrip('/') + '/'
else:
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(RangeHandler, directory=str(ROOT/'_site')))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://localhost:{server.server_port}/understanding-people/'
book_path = '/' + base.split('/', 3)[3]
key = 'understanding-people:reading-list:v1:' + book_path
ref = 'reference/confirmation-bias.html'
errors = []

with sync_playwright() as pw:
    proxy = {'server':os.environ['HTTPS_PROXY']} if live and os.environ.get('HTTPS_PROXY') else None
    browser = pw.chromium.launch(proxy=proxy)
    context = browser.new_context(service_workers='block', accept_downloads=True, proxy=proxy)
    context.on('page', lambda p: p.on('pageerror', lambda e: errors.append(str(e))))
    page = context.new_page()
    requests = []
    page.on('request', lambda r: requests.append(r.url))
    page.goto(base+'search.html')
    expect(page.locator('#book-search-form')).to_be_visible()
    page.locator('#meaning-search').uncheck()
    page.locator('#book-search-query').fill('confirmation bias')
    page.locator('#book-search-form').evaluate('(f)=>f.requestSubmit()')
    result = page.locator('#search-results li').filter(has=page.locator(f'h3 a[href*="{ref}"]')).first
    save = result.locator('[data-reading-save]')
    expect(save).to_be_visible()
    target = result.locator('h3 a').get_attribute('href')
    save.click()
    expect(save).to_have_attribute('aria-pressed', 'true')
    state = page.evaluate('(key)=>JSON.parse(localStorage.getItem(key))', key)
    assert len(state['items']) == 1 and state['items'][0]['url'] == ref
    assert state['items'][0]['fragment'] and 'confirmation bias' not in json.dumps(state)
    assert page.url == base+'search.html', 'Search query must not enter URL'
    # A repeated search re-renders saved controls without duplicating the entry.
    page.locator('#book-search-form').evaluate('(f)=>f.requestSubmit()')
    expect(result.locator('[data-reading-save]')).to_have_attribute('aria-pressed', 'true')
    page.goto(base+'reading-list.html')
    expect(page.locator('#reading-list-items li')).to_have_count(1)
    expect(page.locator('#reading-list-items h2 a')).to_have_attribute('href', target)
    assert page.locator('audio').count() == 0
    # Keyboard actions and cross-tab read/unread/filter state.
    second = context.new_page(); second.goto(base+ref)
    expect(second.locator('[data-reading-save]')).to_have_attribute('aria-pressed', 'true')
    page.locator('#reading-list-items button').first.focus(); page.keyboard.press('Enter')
    expect(page.locator('#reading-list-items li')).to_have_count(0)
    expect(page.locator('[data-reading-filter="unread"]')).to_be_focused()
    page.locator('[data-reading-filter="read"]').click()
    expect(page.locator('#reading-list-items li')).to_have_count(1)
    # Backup and safe merging; untrusted titles/URLs cannot render HTML or leave book.
    page.locator('.reading-list-backup summary').click()
    with page.expect_download() as info: page.locator('#reading-list-download').click()
    backup = json.loads(Path(info.value.path()).read_text())
    assert backup['items'][0]['read'] is True
    if not live:
        payload = {'version':1, 'items':[{'url':ref, 'read':False}, {'url':'reference/declining-help.html', 'fragment':'javascript:alert(1)', 'title':'<img src=x onerror=alert(1)>'}, {'url':'javascript:alert(1)'}, {'url':'https://example.org/'}]}
        page.locator('#reading-list-import').set_input_files({'name':'backup.json','mimeType':'application/json','buffer':json.dumps(payload).encode()})
        expect(page.locator('#reading-save-status')).to_contain_text('1 saved page restored')
        page.locator('[data-reading-filter="all"]').click()
        expect(page.locator('#reading-list-items li')).to_have_count(2)
        assert page.locator('#reading-list-items img').count() == 0
        assert all(a.startswith(base) for a in page.locator('#reading-list-items h2 a').evaluate_all('(els)=>els.map(e=>e.href)'))
        assert page.evaluate('(key)=>JSON.parse(localStorage.getItem(key)).items[0].read', key) is True
        page.locator('#reading-list-import').set_input_files({'name':'bad.json','mimeType':'application/json','buffer':b'not JSON'})
        expect(page.locator('#reading-save-status')).to_contain_text('could not be restored')
        expect(page.locator('#reading-list-items li')).to_have_count(2)
    # Removing in one tab updates the saved state in another; no preference/notes loss.
    second.evaluate("localStorage.setItem('unrelated-notes','keep me')")
    page.locator('#reading-list-items li').filter(has=page.get_by_role('link', name='Confirmation bias', exact=True)).get_by_role('button', name='Remove from reading list: Confirmation bias', exact=True).click()
    expect(second.locator('[data-reading-save]')).to_have_attribute('aria-pressed', 'false')
    assert page.evaluate("localStorage.getItem('unrelated-notes')") == 'keep me'
    second.reload(); expect(second.locator('[data-reading-save]')).to_have_attribute('aria-pressed', 'false')
    second.close()
    assert not any(url.split('?')[0].endswith(('.mp3','.mp4','.onnx','.wasm')) for url in requests), 'Bookmarking must not load media or inference'
    if not live:
        # Current-page save retains an existing deep link and survives reload.
        page.goto(base+ref+'#key-takeaways')
        page.locator('[data-reading-save]').click()
        page.reload(); expect(page.locator('[data-reading-save]')).to_have_attribute('aria-pressed','true')
        assert page.evaluate('(key)=>JSON.parse(localStorage.getItem(key)).items[0].fragment',key) == 'key-takeaways'
        # Responsive controls at phone/tablet/desktop, dark/light, without horizontal overflow.
        for width in (320,390,834,1440):
            for scheme in ('light','dark'):
                page.set_viewport_size({'width':width,'height':900}); page.emulate_media(color_scheme=scheme)
                for path in ('reading-list.html', ref, 'search.html'):
                    page.goto(base+path)
                    if path == 'reading-list.html': expect(page.locator('#reading-list-controls')).to_be_visible()
                    if path == ref: expect(page.locator('[data-reading-save]')).to_be_visible()
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'), (width,scheme,path)
                if width == 390:
                    # Open mobile navigation and find a usable named reading-list destination.
                    page.locator('.mobile-nav > summary').click()
                    page.locator('.mobile-nav [data-section="book"] > summary').evaluate('(el)=>{if(!el.parentNode.open)el.click()}')
                    expect(page.locator('.mobile-nav a[aria-current="page"]')).to_have_count(1)
                    expect(page.locator('.mobile-nav a[href="reading-list.html"]')).to_be_visible()
        # Corrupt, blocked and quota-full storage remain honest and never destroy old data.
        for failure in ('blocked','quota','corrupt'):
            c = browser.new_context(service_workers='block')
            if failure == 'blocked': c.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new DOMException('blocked','SecurityError')}})")
            if failure == 'quota': c.add_init_script("Storage.prototype.setItem=function(){throw new DOMException('full','QuotaExceededError')}")
            p = c.new_page(); p.goto(base+ref)
            expect(p.locator('[data-reading-save]')).to_be_visible()
            if failure == 'corrupt':
                p.evaluate('(key)=>localStorage.setItem(key,"corrupt original")',key); p.reload()
            p.locator('[data-reading-save]').click()
            expect(p.locator('#reading-save-status')).to_contain_text('this page only')
            with p.expect_download() as info: p.locator('#reading-save-status button').click()
            assert len(json.loads(Path(info.value.path()).read_text())['items']) == 1
            if failure == 'corrupt': assert p.evaluate('(key)=>localStorage.getItem(key)',key) == 'corrupt original'
            c.close()
        # No-JS readers retain navigation and never see an inert Save action.
        c = browser.new_context(java_script_enabled=False, service_workers='block'); p = c.new_page()
        p.goto(base+ref); expect(p.locator('[data-reading-save]')).to_be_hidden(); expect(p.locator('.reading-tools a')).to_be_visible()
        p.goto(base+'reading-list.html'); expect(p.locator('.prose noscript')).to_be_visible(); c.close()
        # Catalogue failure never clears an existing list.
        c = browser.new_context(service_workers='block'); p = c.new_page()
        p.route('**/assets/reading-list-index.json*',lambda route:route.abort())
        p.goto(base+'reading-list.html'); expect(p.locator('#reading-save-status')).to_contain_text('has not been changed'); c.close()
        # Offline installed reader uses cached HTML, script and catalogue, including new saves.
        c = browser.new_context(); p = c.new_page(); p.goto(base+ref)
        p.evaluate('''async()=>{await Promise.race([navigator.serviceWorker.ready,new Promise((_,r)=>setTimeout(()=>r(Error('service worker timeout')),60000))]);}''')
        p.reload(); expect(p.locator('[data-reading-save]')).to_be_visible()
        c.set_offline(True); p.goto(base+'reading-list.html'); expect(p.locator('#reading-list-controls')).to_be_visible()
        p.goto(base+ref); p.locator('[data-reading-save]').click()
        p.goto(base+'reading-list.html'); expect(p.locator('#reading-list-items li')).to_have_count(1)
        c.close()
    assert not errors, errors
    context.close(); browser.close()
if server: server.shutdown()
print('PASS: reading-list search/page journeys, safe backups, storage, layout, privacy and offline' if not live else 'PASS: live search, save, restore, read/unread and cross-tab reading-list journeys')
