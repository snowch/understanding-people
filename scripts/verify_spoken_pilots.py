#!/usr/bin/env python3
"""Check authored lessons, including actual delivered MP3 gaps.

Defaults to the original four pilots. --all checks complete authored coverage;
--lessons selects named scripts. No URL starts a local range server.
"""
import argparse
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
from build import destination, PAGES
from page_narration import ROOT, eligible
from narration_voices import manifest_path, DEFAULT, VOICES
from spoken_narration import scripts, fingerprint, transcript, for_voice
from synthesise_spoken import verify_gaps
from verify_page_narration import RangeHandler, ThreadingHTTPServer


def verify(base, all_lessons=False, lessons=None, voice=DEFAULT):
    base = base.rstrip('/') + '/'
    registry = {source: (path, for_voice(data, voice)) for source, (path, data) in scripts().items()}
    manifest = json.loads(manifest_path(voice).read_text())
    if all_lessons:
        assert set(registry) == {s for s, _ in PAGES if eligible(s)}
    elif lessons:
        names = set(lessons)
        registry = {source: item for source, item in registry.items() if item[0].stem in names}
        assert {p.stem for p, _ in registry.values()} == names
    else:
        pilots = {'chapters/01-before-you-explain.md', 'reference/confirmation-bias.md', 'reference/correspondence-bias.md', 'reference/declining-help.md'}
        registry = {source: item for source, item in registry.items() if source in pilots}
        assert set(registry) == pilots
    with sync_playwright() as pw, tempfile.TemporaryDirectory() as folder:
        proxy = {'server': os.environ['HTTPS_PROXY'], 'bypass':'localhost,127.0.0.1'} if os.environ.get('HTTPS_PROXY') else None
        b = pw.chromium.launch(proxy=proxy)
        context = b.new_context(proxy=proxy, service_workers='block')
        preferences = {'version': 1, 'voice': voice, 'speed': 1}
        preference_key = 'understanding-people:preferences:v1:' + urlsplit(base).path
        context.add_init_script('localStorage.setItem(' + json.dumps(preference_key) + ',' + json.dumps(json.dumps(preferences)) + ');')
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
            expect(panel.locator('[data-narration-name]')).to_have_text(VOICES[voice]['name'])
            expect(panel).to_contain_text('A spoken adaptation')
            expect(panel.locator('audio')).to_have_attribute('preload', 'none')
            if source.startswith('reference/') and source not in {'reference/index.md', 'reference/sources.md'}:
                assert page.locator('.prose a[href^="https://"]').count() >= 1
            notes = page.locator('.prose .practice-notes')
            if notes.count():
                assert notes.locator('textarea').count() >= 4
            audio_url = panel.locator('audio source').evaluate('e=>e.src')
            assert entry['audio_sha256'][:12] in audio_url
            response = context.request.get(audio_url)
            assert response.ok and hashlib.sha256(response.body()).hexdigest() == entry['audio_sha256']
            delivered = Path(folder) / (Path(source).stem + '.mp3')
            delivered.write_bytes(response.body())
            verify_gaps(delivered, copy.deepcopy(entry['pauses']))
            assert len(entry['pauses']) == sum(len(s['paragraphs']) for s in data['sections'])
            if notes.count():
                assert any(p['requested_ms'] >= 8000 for p in entry['pauses'])
            spoken_text = context.request.get(panel.get_by_role('link', name='Read transcript').evaluate('e=>e.href'))
            assert spoken_text.text() == transcript(data)
            # A previous, explicitly played clip may finish buffering after the
            # next navigation. Check the current page's players for preloading.
            current_media = set(page.locator('audio source').evaluate_all('nodes=>nodes.map(n=>n.src)'))
            assert not [url for url in automatic if url in current_media], automatic
            for width in [320, 390, 834, 1440]:
                page.set_viewport_size({'width': width, 'height': 950})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            panel.locator('.narration-sections > summary').click()
            selected = min(2, len(entry['sections']) - 1)
            start = entry['sections'][selected]['start']
            panel.locator('[data-audio-seek]').nth(selected).click()
            page.wait_for_function('(start)=>{let a=document.querySelector("#page-narration-audio");return !a.paused&&a.currentTime>=start&&a.currentTime<start+6}', arg=start)
            assert abs(panel.locator('audio').evaluate('e=>e.duration') - entry['duration']) < .25
            panel.locator('audio').evaluate('e=>e.pause()')
            automatic.clear()
            print('Passed delivered lesson:', data['title'], f"({len(entry['pauses'])} measured pauses)", flush=True)
        assert not errors, errors
        b.close()
    print(f'Passed: {len(registry)} authored lessons, exact delivered audio/transcripts, actual paragraph/topic/reflection silence after MP3 encoding, source links and applicable note fields, no preload, cold section playback and responsive layouts. Technical checks do not establish listening quality.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base', nargs='?')
    parser.add_argument('--voice', choices=VOICES, default=DEFAULT)
    choices = parser.add_mutually_exclusive_group()
    choices.add_argument('--all', action='store_true')
    choices.add_argument('--lessons', nargs='+')
    args = parser.parse_args()
    if args.base:
        verify(args.base, args.all, args.lessons, args.voice)
    else:
        server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(RangeHandler, directory=str(ROOT / '_site')))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            verify(f'http://localhost:{server.server_port}/understanding-people/', args.all, args.lessons, args.voice)
        finally:
            server.shutdown()
