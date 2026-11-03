#!/usr/bin/env python3
"""Produce only explicitly selected authored spoken lessons, with real PCM gaps.

Usage: python scripts/synthesise_spoken.py chapter-01 confirmation-bias
Requires edge-tts 7.3.1, FFmpeg/ffprobe. No synthesis occurs in the Pages build.
"""
import argparse
import array
import asyncio
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import wave
from datetime import datetime, timezone
from pathlib import Path

import edge_tts
import build
import spoken_narration as spoken
from page_narration import MANIFEST, ROOT, fingerprint as page_fingerprint, media_path, speech_sections

CACHE = Path(os.environ.get('BOOK_SPOKEN_CACHE', '/workspace/book-spoken-cache'))


def norm(text):
    return ''.join(c.casefold() for c in text if c.isalnum())


def probe(path):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(path)], text=True))


def decode(path):
    return subprocess.check_output(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(path), '-ar', str(spoken.SAMPLE_RATE), '-ac', '1', '-f', 's16le', '-'])


def trim_edges(raw):
    samples = array.array('h', raw)
    if sys.byteorder != 'little':
        samples.byteswap()
    # Retain guards around speech; preserve every internal pause and consonant.
    first = next((i for i, sample in enumerate(samples) if abs(sample) >= 32), None)
    assert first is not None, 'Speech paragraph is silent'
    last = len(samples) - next(i for i, sample in enumerate(reversed(samples)) if abs(sample) >= 32)
    first = max(0, first - int(.08 * spoken.SAMPLE_RATE))
    last = min(len(samples), last + int(.12 * spoken.SAMPLE_RATE))
    return raw[first * 2:last * 2]


def assemble(data, takes, wav_path):
    cursor = 0
    sections, pauses = [], []
    with wave.open(str(wav_path), 'wb') as out:
        out.setparams((1, 2, spoken.SAMPLE_RATE, 0, 'NONE', 'not compressed'))
        out.writeframes(b'\0' * int(.35 * spoken.SAMPLE_RATE) * 2)
        cursor += int(.35 * spoken.SAMPLE_RATE)
        paragraph_index = 0
        for section_index, section in enumerate(data['sections']):
            start = cursor / spoken.SAMPLE_RATE if section_index else 0
            for paragraph in section['paragraphs']:
                raw = trim_edges(decode(takes[paragraph_index]))
                out.writeframes(raw)
                cursor += len(raw) // 2
                pause_start = cursor / spoken.SAMPLE_RATE
                count = round(paragraph['pause_after_ms'] * spoken.SAMPLE_RATE / 1000)
                out.writeframes(b'\0' * count * 2)
                cursor += count
                pauses.append({'paragraph': paragraph_index, 'start': pause_start, 'end': cursor / spoken.SAMPLE_RATE, 'requested_ms': paragraph['pause_after_ms']})
                paragraph_index += 1
            sections.append({'title': section['title'], 'anchor': section['anchor'], 'start': round(start, 3), 'end': round(cursor / spoken.SAMPLE_RATE, 3)})
    return sections, pauses


def verify_gaps(mp3, pauses):
    samples = array.array('h', decode(mp3))
    if sys.byteorder != 'little':
        samples.byteswap()
    for pause in pauses:
        # Exclude MP3 encoder/window edges; measure the intended gap itself.
        start = round((pause['start'] + .08) * spoken.SAMPLE_RATE)
        end = round((pause['end'] - .08) * spoken.SAMPLE_RATE)
        values = samples[start:end]
        assert values and max(map(abs, values)) <= 64, ('A paragraph/reflection gap is not silent', pause)
        pause['verified_silence_ms'] = round(len(values) * 1000 / spoken.SAMPLE_RATE)


async def synthesise(data, workers):
    network = asyncio.Semaphore(workers)
    locks = {}

    async def take(text):
        signature = hashlib.sha256(json.dumps({'voice': data['voice'], 'rate': data['rate'], 'text': text}, sort_keys=True).encode()).hexdigest()
        async with locks.setdefault(signature, asyncio.Lock()):
            path, meta = CACHE / (signature + '.mp3'), CACHE / (signature + '.json')
            if path.exists() and meta.exists():
                saved = json.loads(meta.read_text())
                if saved.get('sha256') == spoken.sha(path) and saved.get('text') == text and saved.get('words_verified'):
                    return path
            for attempt in range(6):
                try:
                    words = []
                    part = path.with_suffix('.part')
                    async with network:
                        with part.open('wb') as out:
                            async for item in edge_tts.Communicate(text, voice=data['voice'], rate=data['rate'], boundary='WordBoundary', proxy=os.environ.get('HTTPS_PROXY')).stream():
                                if item['type'] == 'audio':
                                    out.write(item['data'])
                                elif item['type'] == 'WordBoundary':
                                    words.append(item['text'])
                    assert norm(' '.join(words)) == norm(text), 'Provider did not return the complete spoken paragraph'
                    await asyncio.to_thread(probe, part)
                    part.replace(path)
                    meta.write_text(json.dumps({'text': text, 'words': words, 'words_verified': True, 'sha256': spoken.sha(path)}, ensure_ascii=False))
                    print('Paragraph ready:', text[:65], flush=True)
                    return path
                except Exception as error:
                    status = getattr(error, 'status', None)
                    print(f'Retry {attempt + 1}/6: {type(error).__name__}' + (f' HTTP {status}' if status else ''), flush=True)
                    if attempt == 5:
                        raise
                    await asyncio.sleep(min(2 ** attempt, 16))

    paragraphs = [p for s in data['sections'] for p in s['paragraphs']]
    return await asyncio.gather(*(take(p['text']) for p in paragraphs))


def page_binding(data):
    page = build.OUT / build.destination(data['source'])
    html = page.read_text()
    title = re.search(r'<h1>(.*?)</h1>', html, re.S).group(1)
    from html import unescape
    body = re.search(r'<div class="prose">(.*)</div>\s*</article>', html, re.S).group(1)
    ids = build.Document(html).ids
    assert all(s['anchor'] in ids for s in data['sections']), 'A spoken section needs an existing reading anchor'
    return page_fingerprint(speech_sections(unescape(title), body))


async def produce(selected, workers):
    manifest = json.loads(MANIFEST.read_text())
    updated = copy.deepcopy(manifest)
    catalogue = await edge_tts.list_voices(proxy=os.environ.get('HTTPS_PROXY'))
    assert all(data['voice'] in {v['ShortName'] for v in catalogue} for _, data in selected)
    for path, data in selected:
        source = data['source']
        signature = spoken.fingerprint(data)
        binding = page_binding(data)
        dependencies = spoken.source_hashes(data)
        old = updated['pages'].get(source, {})
        if (old.get('mode') == 'spoken-lesson' and old.get('script_sha256') == signature
                and old.get('source_hashes') == dependencies and old.get('page_text_sha256') == binding
                and old.get('audio_sha256') == spoken.sha(ROOT / media_path(source, '.mp3'))
                and old.get('transcript_sha256') == spoken.sha(ROOT / media_path(source, '.txt'))):
            print('Already current:', path.stem, flush=True)
            continue
        takes = await synthesise(data, workers)
        wav = CACHE / (signature + '.wav')
        sections, pauses = await asyncio.to_thread(assemble, data, takes, wav)
        output = ROOT / media_path(source, '.mp3')
        temporary = CACHE / (signature + '-final.mp3')
        await asyncio.to_thread(subprocess.run, ['ffmpeg', '-nostdin', '-hide_banner', '-v', 'error', '-y', '-i', str(wav), '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', str(spoken.SAMPLE_RATE), '-ac', '1', '-b:a', '96k', '-metadata', 'title=' + data['title'], '-metadata', 'artist=Understanding people', '-metadata', 'comment=Authored spoken lesson. Synthetic narration: ' + data['voice'], '-metadata', 'copyright=Copyright 2026 Christopher Snow', str(temporary)], check=True)
        await asyncio.to_thread(verify_gaps, temporary, pauses)
        duration = await asyncio.to_thread(probe, temporary)
        assert abs(duration - sections[-1]['end']) < .25
        text = spoken.transcript(data)
        text_cache = CACHE / (signature + '-transcript.txt')
        text_cache.write_text(text)
        # Publish the selected page files only after all spoken paragraphs/gaps verify.
        import shutil
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(temporary, output)
        (ROOT / media_path(source, '.txt')).write_text(text)
        entry = {'title': data['title'], 'mode': 'spoken-lesson', 'script_source': path.relative_to(ROOT).as_posix(),
                 'script_sha256': signature, 'page_text_sha256': binding, 'source_hashes': dependencies,
                 'text_sha256': signature, 'audio_sha256': spoken.sha(output),
                 'transcript_sha256': spoken.sha(ROOT / media_path(source, '.txt')),
                 'words': sum(len(p['text'].split()) for s in data['sections'] for p in s['paragraphs']),
                 'duration': duration, 'sections': sections, 'provider_words_verified': True,
                 'pause_engine_version': spoken.ENGINE_VERSION, 'pauses_verified': True, 'pauses': pauses}
        updated['pages'][source] = entry
        # Each verified page is a resumable checkpoint; no unchanged page is re-rendered.
        updated['generated'] = datetime.now(timezone.utc).isoformat()
        part = MANIFEST.with_suffix('.partial.json')
        part.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + '\n')
        part.replace(MANIFEST)
        print(f'Lesson ready: {path.stem}, {duration / 60:.1f} minutes; {len(pauses)} verified pauses', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('lessons', nargs='+', help='Explicit script stems; no automatic whole-library production')
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--plan', action='store_true')
    args = parser.parse_args()
    assert 1 <= args.workers <= 8
    catalogue = {p.stem: (p, data) for p, data in spoken.scripts().values()}
    selected = [catalogue[name] for name in args.lessons]
    for path, data in selected:
        print(path.stem, sum(len(p['text'].split()) for s in data['sections'] for p in s['paragraphs']), 'words; pauses explicitly authored', flush=True)
    if args.plan:
        return
    CACHE.mkdir(parents=True, exist_ok=True)
    build.build(include_narration=False)
    asyncio.run(produce(selected, args.workers))
    build.build()


if __name__ == '__main__':
    main()
