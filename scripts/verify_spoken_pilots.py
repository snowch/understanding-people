#!/usr/bin/env python3
"""Check the four authored listening pilots, including actual delivered MP3 gaps.

With no URL, starts a local range server. Does not record screenshots or claim
that technical checks establish naturalness or pronunciation.
"""
import copy
import functools
import hashlib
import json
import os
import sys
import tempfile
import threading
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright, expect
from build import destination
from page_narration import ROOT, MANIFEST
from spoken_narration import scripts, fingerprint, transcript
from synthesise_spoken import verify_gaps
from verify_page_narration import RangeHandler, ThreadingHTTPServer


def verify(base):
    base = base.rstrip('/') + '/'
    registry = scripts()
    manifest = json.loads(MANIFEST.read_text())
    assert len(registry) == 4
    with sync_playwright() as pw, tempfile.TemporaryDirectory() as folder:
        proxy = {'server': os.environ['HTTPS_PROXY']} if base.startswith('https://') and os.environ.get('HTTPS_PROXY') else None
        b = pw.chromium.launch(proxy=proxy)
        context = b.new_context(proxy=proxy, service_workers='block')
        page = context.new_page()
        errors, automatic = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda r: automatic.append(r.url) if urlsplit(r.url).path.endswith('.mp3') else None)
        for source, (_, data) in registry.items():
            entry = manifest['pages'][source]
            assert entry['mode'] == 'spoken-lesson' and entry['script_sha256'] == fingerprint(data)
            page.goto(base + destination(source).as_posix())
            panel = page.locator('.page-narration')
            expect(panel.get_by_role('heading', name='Listen to this lesson')).to_be_visible()
            expect(panel).to_contain_text('Spoken lesson')
            expect(panel).to_contain_text('Full references and additional practice')
            expect(panel.locator('audio')).to_have_attribute('preload', 'none')
            assert page.locator('.prose a[href^="https://"]').count() >= 1
            assert page.locator('.prose .practice-notes textarea').count() >= 4
            audio_url = panel.locator('audio source').evaluate('e=>e.src')
            assert entry['audio_sha256'][:12] in audio_url
            response = context.request.get(audio_url)
            assert response.ok and hashlib.sha256(response.body()).hexdigest() == entry['audio_sha256']
            delivered = Path(folder) / (Path(source).stem + '.mp3')
            delivered.write_bytes(response.body())
            verify_gaps(delivered, copy.deepcopy(entry['pauses']))
            assert len(entry['pauses']) == sum(len(s['paragraphs']) for s in data['sections'])
            assert any(p['requested_ms'] >= 8000 for p in entry['pauses'])
            spoken_text = context.request.get(panel.get_by_role('link', name='Read transcript').evaluate('e=>e.href'))
            assert spoken_text.text() == transcript(data)
            assert not automatic, automatic
            for width in [320, 390, 834, 1440]:
                page.set_viewport_size({'width': width, 'height': 950})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            panel.locator('.narration-sections > summary').click()
            start = entry['sections'][2]['start']
            panel.locator('[data-audio-seek]').nth(2).click()
            page.wait_for_function('(start)=>{let a=document.querySelector("#page-narration-audio");return !a.paused&&a.currentTime>=start&&a.currentTime<start+6}', arg=start)
            assert abs(panel.locator('audio').evaluate('e=>e.duration') - entry['duration']) < .25
            panel.locator('audio').evaluate('e=>e.pause()')
            automatic.clear()
            print('Passed delivered lesson:', data['title'], f"({len(entry['pauses'])} measured pauses)", flush=True)
        assert not errors, errors
        b.close()
    print('Passed: four authored lessons, exact delivered audio/transcripts, actual paragraph/topic/reflection silence after MP3 encoding, source links and note fields, no preload, cold section playback and responsive layouts. Listening quality still needs a listening judgment.')


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
