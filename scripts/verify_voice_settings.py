#!/usr/bin/env python3
"""Exercise reader goals for narrator choice, playback and local preferences."""
import functools
import json
import os
import re
import sys
import threading
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright, expect
from page_narration import ROOT
from verify_page_narration import RangeHandler, ThreadingHTTPServer


def verify(base):
    base = base.rstrip('/') + '/'
    key = 'understanding-people:preferences:v1:' + urlsplit(base).path
    chapter = base + 'chapters/03-needs-motives-goals.html'
    errors = []
    with sync_playwright() as pw:
        proxy = {'server': os.environ['HTTPS_PROXY']} if base.startswith('https://') and os.environ.get('HTTPS_PROXY') else None
        browser = pw.chromium.launch(proxy=proxy)
        context = browser.new_context(proxy=proxy, service_workers='block', viewport={'width': 390, 'height': 900})
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        requests = []
        page.on('request', lambda request: requests.append(request.url) if urlsplit(request.url).path.endswith('.mp3') else None)
        page.goto(chapter)
        expect(page.get_by_label('Narration voice', exact=True)).to_have_value('andrew')
        assert not requests, requests
        page.locator('.header-settings').click()
        expect(page.get_by_role('heading', name='Settings', exact=True)).to_be_visible()
        expect(page.locator('[name="narrator"][value="andrew"]')).to_be_enabled()
        expect(page.locator('[data-reading-return]')).to_have_attribute('href', chapter)
        # Hearing a preview must not silently select it for the whole book.
        page.get_by_role('button', name='Preview Jenny', exact=True).click()
        page.wait_for_function('!document.querySelector("#voice-preview").paused && document.querySelector("#voice-preview").currentTime>0')
        expect(page.locator('[name="narrator"][value="andrew"]')).to_be_checked()
        expect(page.locator('[data-preview-name]')).to_have_text('Jenny')
        page.locator('#voice-preview').evaluate('e=>e.currentTime=25.1')
        page.wait_for_function('document.querySelector("#voice-preview").paused')
        expect(page.locator('[data-preview-status]')).to_contain_text('25-second preview')
        # Native radio keyboard navigation must save the narrator too.
        page.locator('[name="narrator"][value="andrew"]').focus()
        page.keyboard.press('ArrowDown')
        expect(page.locator('[name="narrator"][value="jenny"]')).to_be_checked()
        page.get_by_label('Playback speed', exact=True).select_option('1.25')
        saved = page.evaluate('(key)=>JSON.parse(localStorage.getItem(key))', key)
        assert saved['voice'] == 'jenny' and saved['speed'] == 1.25
        page.locator('[data-reading-return]').click()
        expect(page.get_by_label('Narration voice', exact=True)).to_have_value('jenny')
        expect(page.locator('[data-narration-name]')).to_have_text('Jenny')
        expect(page.get_by_label('Page narration speed', exact=True)).to_have_value('1.25')
        variants = json.loads(page.locator('.narration-variants').text_content())
        expect(page.locator('.narration-download')).to_have_attribute('href', variants['jenny']['audio'])
        expect(page.locator('.narration-download')).to_have_attribute('download', re.compile(r'en-US-JennyNeural\.mp3$'))
        page.locator('.narration-sections > summary').click()
        index = 2
        page.locator('[data-audio-seek]').nth(index).click()
        target = variants['jenny']['sections'][index]['start']
        page.wait_for_function('(t)=>{const a=document.querySelector("#page-narration-audio");return !a.paused&&a.currentTime>=t&&a.currentTime<t+6}', arg=target)
        player = page.locator('#page-narration-audio')
        assert abs(player.evaluate('e=>e.duration') - variants['jenny']['seconds']) < .25
        old_time = player.evaluate('e=>e.currentTime')
        section, other = variants['jenny']['sections'][index], variants['andrew']['sections'][index]
        mapped = other['start'] + (old_time-section['start'])/(section['end']-section['start'])*(other['end']-other['start'])
        # Changing a playing voice pauses it. It must not fetch the new voice yet.
        requests.clear()
        page.get_by_label('Narration voice', exact=True).select_option('andrew')
        assert player.evaluate('e=>e.paused')
        page.wait_for_timeout(200)
        assert not [url for url in requests if variants['andrew']['audio'].split('?')[0] in url], requests
        expect(page.locator('.audio-status')).to_contain_text('Press Play')
        player.evaluate('e=>e.play()')
        page.wait_for_function('(t)=>{const a=document.querySelector("#page-narration-audio");return !a.paused&&Math.abs(a.currentTime-t)<3}', arg=mapped)
        assert player.evaluate('e=>e.playbackRate') == 1.25
        # A newly chosen section supersedes the place retained from a voice switch.
        page.get_by_label('Narration voice', exact=True).select_option('jenny')
        page.locator('[data-audio-seek]').nth(3).click()
        target = variants['jenny']['sections'][3]['start']
        page.wait_for_function('(t)=>{const a=document.querySelector("#page-narration-audio");return !a.paused&&a.currentTime>=t&&a.currentTime<t+6}', arg=target)
        player.evaluate('e=>e.pause()')
        # At the end of a completed lesson, a different narrator starts afresh.
        player.evaluate('e=>{e.currentTime=Math.max(0,e.duration-.2);return e.play();}')
        page.wait_for_function('document.querySelector("#page-narration-audio").ended')
        page.get_by_label('Narration voice', exact=True).select_option('andrew')
        player.evaluate('e=>e.play()')
        page.wait_for_function('(()=>{const a=document.querySelector("#page-narration-audio");return !a.paused&&a.readyState>=1&&a.currentTime<3})()')
        player.evaluate('e=>e.pause()')
        page.get_by_label('Narration voice', exact=True).select_option('jenny')
        page.reload()
        expect(page.get_by_label('Narration voice', exact=True)).to_have_value('jenny')
        assert page.locator('#page-narration-audio').evaluate('e=>e.paused')
        page.get_by_role('link', name='Voice settings', exact=True).click()
        expect(page.locator('[data-reading-return]')).to_have_attribute('href', chapter + '#page-narration-title')
        # Reset only preferences, retaining notes and unrelated books' settings.
        page.evaluate('localStorage.setItem("practice-note-test","retain this note")')
        page.get_by_role('button', name='Restore defaults', exact=True).click()
        expect(page.locator('[name="narrator"][value="andrew"]')).to_be_checked()
        expect(page.get_by_label('Playback speed', exact=True)).to_have_value('1')
        assert page.evaluate('localStorage.getItem("practice-note-test")') == 'retain this note'
        page.locator('[data-reading-return]').click()
        # A second tab changes the preference; an open lesson follows without playing.
        second = context.new_page()
        second.goto(base + 'settings.html')
        second.locator('[name="narrator"][value="jenny"]').check()
        expect(page.get_by_label('Narration voice', exact=True)).to_have_value('jenny')
        assert page.locator('#page-narration-audio').evaluate('e=>e.paused')
        second.close()
        for route in ['settings.html', 'chapters/03-needs-motives-goals.html']:
            page.goto(base + route)
            for width in [320, 390, 834, 1440]:
                for scheme in ['light', 'dark']:
                    page.set_viewport_size({'width': width, 'height': 950})
                    page.emulate_media(color_scheme=scheme)
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), (route, width, scheme)
                    expect(page.locator('.header-settings')).to_be_visible()
                    assert page.locator('.header-settings').bounding_box()['width'] >= 44
                    if route == 'settings.html':
                        expect(page.locator('[name="narrator"][value="jenny"]')).to_be_checked()
                        if os.environ.get('PEOPLE_SETTINGS_SCREENSHOTS') and width in [390, 1440]:
                            page.screenshot(path=f'/tmp/book-settings-{width}-{scheme}.png', full_page=True)
        # Corrupt data and another book's preferences must not select an arbitrary URL.
        corrupt = browser.new_context(proxy=proxy, service_workers='block')
        corrupt.add_init_script('localStorage.setItem('+json.dumps(key)+',"{broken");localStorage.setItem("other-book-preferences",JSON.stringify({voice:"jenny"}));')
        c = corrupt.new_page()
        c.goto(chapter)
        expect(c.get_by_label('Narration voice', exact=True)).to_have_value('andrew')
        # Storage denial keeps the controls usable and reports the limitation.
        blocked = browser.new_context(proxy=proxy, service_workers='block')
        blocked.add_init_script('Storage.prototype.getItem=Storage.prototype.setItem=()=>{throw new DOMException("Blocked","SecurityError")};')
        f = blocked.new_page()
        f.on('pageerror', lambda error: errors.append(str(error)))
        f.goto(base + 'settings.html?return=https%3A%2F%2Fexample.com%2F')
        expect(f.locator('[data-reading-return]')).to_have_attribute('href', 'index.html')
        f.locator('[name="narrator"][value="jenny"]').check()
        expect(f.locator('[data-settings-status]')).to_contain_text('blocked saving')
        f.goto(chapter)
        f.get_by_label('Narration voice', exact=True).select_option('jenny')
        expect(f.locator('[data-narration-name]')).to_have_text('Jenny')
        expect(f.locator('.audio-status')).to_contain_text('blocked saving')
        assert f.locator('audio').evaluate('e=>e.paused')
        # Direct alternate MP3 links remain available without JavaScript.
        nojs = browser.new_context(proxy=proxy, java_script_enabled=False, service_workers='block')
        n = nojs.new_page()
        n.goto(base + 'settings.html')
        expect(n.locator('[name="narrator"][value="andrew"]')).to_be_disabled()
        expect(n.get_by_role('link', name='Listen to Jenny', exact=True)).to_be_visible()
        n.goto(chapter)
        expect(n.get_by_role('link', name='Download Jenny MP3', exact=True)).to_be_visible()
        # Saved text includes Settings, while neither full voice is precached.
        offline = browser.new_context(proxy=proxy)
        o = offline.new_page()
        o.goto(base + 'settings.html')
        o.evaluate('navigator.serviceWorker.ready')
        o.wait_for_function('navigator.serviceWorker.controller !== null')
        o.locator('[name="narrator"][value="jenny"]').check()
        offline.set_offline(True)
        o.goto(chapter)
        expect(o.get_by_label('Narration voice', exact=True)).to_have_value('jenny')
        o.locator('.header-settings').click()
        o.locator('[name="narrator"][value="andrew"]').check()
        o.locator('[data-reading-return]').click()
        expect(o.get_by_label('Narration voice', exact=True)).to_have_value('andrew')
        cached = o.evaluate('''async()=>{const keys=await caches.keys();return (await Promise.all(keys.map(async k=>(await (await caches.open(k)).keys()).map(r=>r.url)))).flat()}''')
        assert not any(urlsplit(url).path.endswith('.mp3') for url in cached)
        assert not errors, errors
        browser.close()
    print('Passed: previews without selecting, keyboard narrator choice, persisted voice/speed across pages and reload, voice-specific timelines/download names, pause and retain place on switching, restart after a finished lesson, pending-seek replacement, no auto-play/download, reset without losing notes, cross-tab updates, corrupt/blocked storage, safe return links, no-JS audio links, offline settings without precaching MP3s, mobile/desktop and light/dark layouts.')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        verify(sys.argv[1])
    else:
        server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(RangeHandler, directory=str(ROOT / '_site')))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            verify(f'http://localhost:{server.server_port}/understanding-people/')
        finally:
            server.shutdown()
