#!/usr/bin/env python3
"""Verify single-file M4Bs, chapter seeking and optional public release delivery."""
import argparse
import functools
import hashlib
import json
from pathlib import Path
import subprocess
import threading
import urllib.request

from playwright.sync_api import sync_playwright
from book_audiobook import MANIFEST, REPOSITORY
from package_audiobooks import RATE, nero_chapters, probe, sha
from narration_voices import ROOT
from verify_page_narration import RangeHandler, ThreadingHTTPServer


class AudiobookHandler(RangeHandler):
    def guess_type(self, path):
        return 'audio/mp4' if str(path).endswith('.m4b') else super().guess_type(path)


def verify(folder, public=False):
    manifest = json.loads(MANIFEST.read_text())
    editions = [edition for voice in manifest['voices'].values() for edition in voice['editions'].values()]
    assert len(editions) == 4
    for voice, record in manifest['voices'].items():
        full, core = record['editions']['complete'], record['editions']['course']
        assert full['chapters'][:14] == core['chapters']
        from build import CHAPTERS, PAGES
        from book_audiobook import ordering
        assert len(full['chapters']) == len({c['source'] for c in full['chapters']}) == len(ordering(CHAPTERS, PAGES)['complete'])
        assert len(core['chapters']) == 14
        assert all(c['end_sample'] > c['start_sample'] for c in full['chapters'])
    for edition in editions:
        path = folder / edition['filename']
        assert path.stat().st_size == edition['bytes'] and sha(path) == edition['sha256']
        data = probe(path)
        audio = [s for s in data['streams'] if s['codec_type'] == 'audio']
        assert len(audio) == 1 and audio[0]['codec_name'] == 'aac' and audio[0]['profile'] == 'LC'
        assert int(audio[0]['sample_rate']) == RATE and audio[0]['channels'] == 1
        assert int(data['format']['tags']['media_type']) == 2
        chapters = data['chapters']
        alternate = nero_chapters(path)
        assert len(chapters) == len(alternate) == edition['chapter_count']
        for expected, actual, nero in zip(edition['chapters'], chapters, alternate):
            assert actual['tags']['title'] == nero[1] == expected['title']
            assert abs(float(actual['start_time']) - expected['start_sample']/RATE) < .003
            assert abs(nero[0] - expected['start_sample']/RATE) < .003
        cover = subprocess.check_output(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(path), '-map', '0:v:0', '-c:v', 'copy', '-f', 'image2pipe', '-'])
        assert hashlib.sha256(cover).hexdigest() == manifest['cover_sha256']
        print('Verified file and both chapter tables:', edition['filename'], flush=True)
    # Exercise the finished containers, not just the original MP3s.
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(AudiobookHandler, directory=str(folder)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            base = f'http://localhost:{server.server_port}/understanding-people/'
            for edition in editions:
                page.goto(base)
                page.set_content('<audio id="book" controls preload="none"></audio>')
                player = page.locator('audio')
                player.evaluate('(a,url)=>a.src=url', base + edition['filename'])
                indices = sorted({1, 13, len(edition['chapters'])//2, len(edition['chapters'])-1})
                for i in indices:
                    start = edition['chapters'][i]['start_sample']/RATE + .25
                    player.evaluate('''(a,t)=>{a.pause();if(a.readyState>=1)a.currentTime=t;else a.addEventListener('loadedmetadata',()=>{a.currentTime=t;},{once:true});return a.play();}''', start)
                    page.wait_for_function('(t)=>{const a=document.querySelector("#book");return !a.paused&&a.currentTime>=t&&a.currentTime<t+6}', arg=start)
                assert abs(player.evaluate('a=>a.duration') - edition['duration']) < .25
                player.evaluate('a=>a.playbackRate=1.25')
                assert player.evaluate('a=>a.playbackRate') == 1.25
                player.evaluate('a=>a.pause()')
                print('Passed finished M4B playback and chapter seeks:', edition['filename'], flush=True)
            assert not errors, errors
            browser.close()
    finally:
        server.shutdown()
    if public:
        release = json.loads(subprocess.check_output(['gh', 'api', f'repos/{REPOSITORY}/releases/tags/{manifest["release_tag"]}']))
        assert not release['draft'] and release['tag_name'] == manifest['release_tag']
        assets = {a['name']: a for a in release['assets']}
        for edition in editions:
            asset = assets[edition['filename']]
            assert asset['size'] == edition['bytes'] and asset['state'] == 'uploaded'
            assert asset['digest'] == 'sha256:' + edition['sha256']
            request = urllib.request.Request(edition['url'], headers={'Range': 'bytes=0-1023'})
            with urllib.request.urlopen(request, timeout=90) as response:
                assert response.status in {200, 206}
                assert int(response.headers['Content-Length']) == (1024 if response.status == 206 else edition['bytes'])
                assert 'attachment' in response.headers.get('Content-Disposition', '')
                prefix = response.read(1024)
            with (folder / edition['filename']).open('rb') as local:
                assert prefix == local.read(1024)
            print('Passed public download, size and server SHA-256:', edition['filename'], flush=True)
        assert assets['audiobook-manifest.json']['digest'] == 'sha256:' + sha(MANIFEST)
    print('Passed: four single-file audiobooks, original artwork, source ordering, sample-derived QuickTime/Nero chapters, actual container playback/seeking and speed.' + (' Public release hashes and downloads verified.' if public else ''))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', type=Path, default=Path('/workspace/audiobook-release'))
    parser.add_argument('--public', action='store_true')
    args = parser.parse_args()
    verify(args.artifacts, args.public)
