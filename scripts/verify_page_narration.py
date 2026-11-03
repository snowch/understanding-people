#!/usr/bin/env python3
"""Verify coverage, current scripts, media delivery and the listening journey.

With no URL, starts a local byte-range server under /understanding-people/.
Uses Playwright/Chromium. Creates no screenshots or recordings.
"""
import functools
import hashlib
import json
import os
import re
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright, expect
from build import PAGES, destination
from page_narration import ROOT, MANIFEST, VOICE, eligible, media_path


class RangeHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        path = path.removeprefix('/understanding-people')
        return super().translate_path(path)

    def send_head(self):
        self.remaining = None
        path = Path(self.translate_path(self.path))
        header = self.headers.get('Range', '')
        match = re.fullmatch(r'bytes=(\d+)-(\d*)', header)
        if match and path.is_file():
            size = path.stat().st_size
            start, end = int(match[1]), min(int(match[2]) if match[2] else size - 1, size - 1)
            if start > end:
                self.send_error(416)
                return None
            result = path.open('rb')
            result.seek(start)
            self.remaining = end - start + 1
            self.send_response(206)
            self.send_header('Content-Type', self.guess_type(str(path)))
            self.send_header('Content-Length', str(self.remaining))
            self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
            self.end_headers()
            return result
        return super().send_head()

    def end_headers(self):
        self.send_header('Accept-Ranges', 'bytes')
        super().end_headers()

    def copyfile(self, source, output):
        try:
            if self.remaining is None:
                return super().copyfile(source, output)
            while self.remaining:
                data = source.read(min(65536, self.remaining))
                if not data:
                    break
                output.write(data)
                self.remaining -= len(data)
        except (BrokenPipeError, ConnectionResetError):
            pass  # A native player may abandon a range when seeking.

    def log_message(self, *args):
        pass


def verify(base):
    base = base.rstrip('/') + '/'
    manifest = json.loads(MANIFEST.read_text())
    expected = {s for s, _ in PAGES if eligible(s)}
    assert set(manifest['pages']) == expected
    assert manifest['voice'] == VOICE and len(expected) == 136
    for source, entry in manifest['pages'].items():
        assert entry['provider_words_verified']
        assert entry['duration'] > 0 and entry['sections'][0]['start'] == 0
        assert all(0 <= s['start'] < s['end'] <= entry['duration'] + 1 for s in entry['sections'])
        for suffix, key in [('.mp3', 'audio_sha256'), ('.txt', 'transcript_sha256')]:
            assert hashlib.sha256((ROOT / media_path(source, suffix)).read_bytes()).hexdigest() == entry[key]
    with sync_playwright() as pw:
        proxy_url = os.environ.get('HTTPS_PROXY') if base.startswith('https://') else None
        proxy = {'server': proxy_url} if proxy_url else None
        browser = pw.chromium.launch(proxy=proxy)
        context = browser.new_context(service_workers='block', accept_downloads=True, proxy=proxy)
        page = context.new_page()
        errors, media = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: media.append(request.url) if urlsplit(request.url).path.endswith('.mp3') else None)
        for source, entry in manifest['pages'].items():
            page.goto(base + destination(source).as_posix())
            panel = page.locator('.page-narration')
            expect(panel).to_have_count(1)
            expect(panel.locator('audio')).to_have_attribute('preload', 'none')
            expect(panel.locator('audio')).to_have_attribute('controls', '')
            expect(panel).to_contain_text('Andrew · Synthetic narration')
            expect(panel.locator('details')).not_to_have_attribute('open', '')
            audio_url = panel.locator('audio source').evaluate('e=>e.src')
            assert audio_url.startswith(base + 'assets/media/narration/')
            response = context.request.get(audio_url, headers={'Range': 'bytes=0-511'})
            assert response.status == 206, (source, response.status)
            assert len(response.body()) == 512
            assert response.headers['content-type'].split(';', 1)[0] in {'audio/mpeg', 'audio/mp3'}
            text = context.request.get(panel.get_by_role('link', name='Read transcript').evaluate('e=>e.href'))
            assert text.ok and hashlib.sha256(text.body()).hexdigest() == entry['transcript_sha256']
            for anchor in {s['anchor'] for s in entry['sections']}:
                expect(page.locator('[id="' + anchor + '"]')).to_have_count(1)
        assert not media, media  # Native players do not fetch on arrival.
        samples = ['book.md', 'chapters/01-before-you-explain.md', 'reference/confirmation-bias.md', 'reference/gaslighting.md', 'reference/sources.md', 'glossary.md']
        for source in samples:
            page.goto(base + destination(source).as_posix())
            for width in [320, 390, 834, 1440]:
                page.set_viewport_size({'width': width, 'height': 950})
                for scheme in ['light', 'dark']:
                    page.emulate_media(color_scheme=scheme)
                    for expanded in [False, True]:
                        page.locator('.narration-sections').evaluate('(e,state)=>e.open=state', expanded)
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (source, width, scheme, expanded)
            page.locator('.narration-sections').evaluate('e=>e.open=false')
            page.locator('.narration-sections > summary').focus()
            page.keyboard.press('Enter')
            expect(page.locator('.narration-sections')).to_have_attribute('open', '')
            # Seek directly into a later section before loading any audio.
            selected = min(2, len(manifest['pages'][source]['sections']) - 1)
            start = manifest['pages'][source]['sections'][selected]['start']
            page.locator('.page-narration [data-audio-seek]').nth(selected).click()
            page.wait_for_function('(start)=>{const a=document.querySelector("#page-narration-audio");return !a.paused&&a.currentTime>=start&&a.currentTime<start+8}', arg=start)
            player = page.locator('#page-narration-audio')
            assert abs(player.evaluate('e=>e.duration') - manifest['pages'][source]['duration']) < .25
            page.get_by_label('Page narration speed', exact=True).select_option('1.5')
            assert player.evaluate('e=>e.playbackRate') == 1.5
            player.evaluate('e=>e.pause()')
            page.emulate_media(media='print')
            expect(page.locator('.page-narration')).to_be_hidden()
            page.emulate_media(media='screen', color_scheme='light')
        # Existing optional audio and the new page player must not overlap.
        page.goto(base + 'reference/confirmation-bias.html')
        page.locator('#page-narration-audio').evaluate('e=>e.play()')
        page.locator('#audio-explanation').evaluate('e=>e.play()')
        page.wait_for_function('document.querySelector("#page-narration-audio").paused && !document.querySelector("#audio-explanation").paused')
        page.locator('#audio-explanation').evaluate('e=>e.pause()')
        page.goto(base + 'chapters/01-before-you-explain.html')
        with page.expect_download() as event:
            page.locator('.page-narration').get_by_role('link', name='Download MP3', exact=True).click()
        assert hashlib.sha256(Path(event.value.path()).read_bytes()).hexdigest() == manifest['pages']['chapters/01-before-you-explain.md']['audio_sha256']
        nojs = browser.new_context(java_script_enabled=False, service_workers='block', viewport={'width': 390, 'height': 900})
        q = nojs.new_page()
        q.goto(base + 'chapters/01-before-you-explain.html')
        expect(q.locator('.page-narration audio')).to_be_visible()
        q.locator('.narration-sections > summary').click()
        expect(q.locator('.page-narration [data-audio-seek]:visible')).to_have_count(0)
        q.locator('.narration-sections a').nth(2).click()
        expect(q.locator('main h1')).to_have_text('Why we misinterpret people')
        expect(q.locator('.narration-speed')).to_be_hidden()
        failed = browser.new_context(service_workers='block')
        failed.route('**/assets/media/narration/**', lambda route: route.abort())
        f = failed.new_page()
        f.goto(base + 'chapters/01-before-you-explain.html')
        f.locator('audio').evaluate('e=>{e.load();e.play().catch(()=>{});} ')
        expect(f.locator('.page-narration .audio-status')).to_contain_text('Audio could not load')
        expect(f.locator('.page-narration').get_by_role('link', name='Read transcript')).to_be_visible()
        failed.close()
        page.goto(base + 'chapters/01-before-you-explain.html#%E0%A4%A')
        expect(page.get_by_label('Page narration speed', exact=True)).to_be_visible()
        # Browser-cached text remains offline without silently downloading hours of audio.
        offline = browser.new_context()
        r = offline.new_page()
        r.goto(base + 'chapters/01-before-you-explain.html')
        r.evaluate('navigator.serviceWorker.ready')
        r.wait_for_function('navigator.serviceWorker.controller !== null')
        keys = r.evaluate('''async()=>{const keys=await caches.keys();return (await Promise.all(keys.map(async k=>(await (await caches.open(k)).keys()).map(r=>r.url)))).flat()}''')
        assert not any(urlsplit(url).path.endswith('.mp3') for url in keys)
        offline.set_offline(True)
        r.reload()
        expect(r.locator('main h1')).to_have_text('Why we misinterpret people')
        expect(r.locator('.page-narration')).to_contain_text('download the MP3 for offline listening')
        assert not errors, errors
        browser.close()
    print(f'Passed: {len(expected)} current Andrew narrations; source/file checksums, all transcripts and range URLs, no automatic audio downloads, section seek/playback/speed, independent optional audio, MP3 download, keyboard/no-JS, light/dark responsive layouts, printing and offline text. No screenshots or recordings created.')


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
