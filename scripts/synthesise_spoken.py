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
import shutil
import subprocess
import sys
import wave
from datetime import datetime, timezone
from pathlib import Path

import edge_tts
import build
import spoken_narration as spoken
from page_narration import MANIFEST, ROOT, fingerprint as page_fingerprint, media_path, speech_sections
from narration_voices import DEFAULT, VOICES, manifest_path

CACHE = Path(os.environ.get('BOOK_SPOKEN_CACHE', '/workspace/book-spoken-cache'))


def atomic_text(path, text):
    pending = path.with_name(path.name + '.partial')
    try:
        pending.write_text(text)
        pending.replace(path)
    finally:
        pending.unlink(missing_ok=True)


def atomic_copy(source, destination):
    pending = destination.with_name(destination.name + '.partial')
    try:
        shutil.copyfile(source, pending)
        pending.replace(destination)
    finally:
        pending.unlink(missing_ok=True)


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


async def synthesise(data, workers, network=None, locks=None):
    network = network if network is not None else asyncio.Semaphore(workers)
    locks = locks if locks is not None else {}

    async def take(text):
        signature = hashlib.sha256(json.dumps({'voice': data['voice'], 'rate': data['rate'], 'text': text}, sort_keys=True).encode()).hexdigest()
        async with locks.setdefault(signature, asyncio.Lock()):
            path, meta = CACHE / (signature + '.mp3'), CACHE / (signature + '.json')
            if path.exists() and meta.exists():
                try:
                    saved = json.loads(meta.read_text())
                except (OSError, ValueError):
                    saved = {}
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
                    atomic_text(meta, json.dumps({'text': text, 'words': words, 'words_verified': True, 'sha256': spoken.sha(path)}, ensure_ascii=False))
                    print('Paragraph ready:', text[:65], flush=True)
                    return path
                except Exception as error:
                    status = getattr(error, 'status', None)
                    print(f'Retry {attempt + 1}/6: {type(error).__name__}' + (f' HTTP {status}' if status else ''), flush=True)
                    if attempt == 5:
                        raise
                    await asyncio.sleep(min(2 ** attempt, 16))

    paragraphs = [p for s in data['sections'] for p in s['paragraphs']]
    outcomes = await asyncio.gather(*(take(p['text']) for p in paragraphs), return_exceptions=True)
    failures = [outcome for outcome in outcomes if isinstance(outcome, BaseException)]
    if failures:
        raise RuntimeError(f'{len(failures)} spoken paragraphs need retry; other completed takes are cached') from failures[0]
    return outcomes


def page_binding(data):
    page = build.OUT / build.destination(data['source'])
    html = page.read_text()
    title = re.search(r'<h1>(.*?)</h1>', html, re.S).group(1)
    from html import unescape
    body = re.search(r'<div class="prose">(.*)</div>\s*</article>', html, re.S).group(1)
    ids = build.Document(html).ids
    assert all(s['anchor'] in ids for s in data['sections']), 'A spoken section needs an existing reading anchor'
    return page_fingerprint(speech_sections(unescape(title), body))


async def produce(selected, workers, page_workers=1, voice=DEFAULT):
    assert len({data['source'] for _, data in selected}) == len(selected), 'Each lesson may be scheduled only once'
    target_manifest = manifest_path(voice)
    manifest = (json.loads(target_manifest.read_text()) if target_manifest.exists() else
                {'version': 1, 'voice': VOICES[voice]['id'], 'rate': '-2%', 'pages': {}})
    assert manifest['voice'] == VOICES[voice]['id']
    assert all(data['voice'] == manifest['voice'] for _, data in selected)
    updated = copy.deepcopy(manifest)
    catalogue = await edge_tts.list_voices(proxy=os.environ.get('HTTPS_PROXY'))
    assert all(data['voice'] in {v['ShortName'] for v in catalogue} for _, data in selected)
    network = asyncio.Semaphore(workers)
    pages = asyncio.Semaphore(page_workers)
    encoders = asyncio.Semaphore(3)
    checkpoint = asyncio.Lock()
    locks = {}

    async def lesson(path, data):
      async with pages:
        source = data['source']
        signature = spoken.fingerprint(data)
        binding = page_binding(data)
        dependencies = spoken.source_hashes(data)
        old = updated['pages'].get(source, {})
        if (old.get('mode') == 'spoken-lesson' and old.get('script_sha256') == signature
                and old.get('source_hashes') == dependencies and old.get('page_text_sha256') == binding
                and (ROOT / media_path(source, '.mp3', voice)).is_file() and (ROOT / media_path(source, '.txt', voice)).is_file()
                and old.get('audio_sha256') == spoken.sha(ROOT / media_path(source, '.mp3', voice))
                and old.get('transcript_sha256') == spoken.sha(ROOT / media_path(source, '.txt', voice))):
            print('Already current:', path.stem, flush=True)
            return
        print('Recording:', path.stem, flush=True)
        takes = await synthesise(data, workers, network=network, locks=locks)
        wav = CACHE / (signature + '.wav')
        output = ROOT / media_path(source, '.mp3', voice)
        temporary = CACHE / (signature + '-final.mp3')
        async with encoders:
            sections, pauses = await asyncio.to_thread(assemble, data, takes, wav)
            await asyncio.to_thread(subprocess.run, ['ffmpeg', '-nostdin', '-hide_banner', '-v', 'error', '-y', '-i', str(wav), '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', str(spoken.SAMPLE_RATE), '-ac', '1', '-b:a', VOICES[voice]['bitrate'], '-metadata', 'title=' + data['title'], '-metadata', 'artist=Understanding people', '-metadata', 'comment=Authored spoken lesson. Synthetic narration: ' + data['voice'], '-metadata', 'copyright=Copyright 2026 Christopher Snow', str(temporary)], check=True)
            await asyncio.to_thread(verify_gaps, temporary, pauses)
        duration = await asyncio.to_thread(probe, temporary)
        assert abs(duration - sections[-1]['end']) < .25
        text = spoken.transcript(data)
        text_cache = CACHE / (signature + '-transcript.txt')
        text_cache.write_text(text)
        # Publish the selected page files only after all spoken paragraphs/gaps verify.
        output.parent.mkdir(parents=True, exist_ok=True)
        atomic_copy(temporary, output)
        atomic_text(ROOT / media_path(source, '.txt', voice), text)
        entry = {'title': data['title'], 'mode': 'spoken-lesson', 'script_source': path.relative_to(ROOT).as_posix(),
                 'script_sha256': signature, 'page_text_sha256': binding, 'source_hashes': dependencies,
                 'text_sha256': signature, 'audio_sha256': spoken.sha(output),
                 'transcript_sha256': spoken.sha(ROOT / media_path(source, '.txt', voice)),
                 'words': sum(len(p['text'].split()) for s in data['sections'] for p in s['paragraphs']),
                 'duration': duration, 'sections': sections, 'provider_words_verified': True,
                 'pause_engine_version': spoken.ENGINE_VERSION, 'pauses_verified': True, 'pauses': pauses}
        # Each verified page is a resumable checkpoint; no unchanged page is re-rendered.
        async with checkpoint:
            updated['pages'][source] = entry
            updated['generated'] = datetime.now(timezone.utc).isoformat()
            atomic_text(target_manifest, json.dumps(updated, ensure_ascii=False, indent=2) + '\n')
        print(f'Lesson ready: {path.stem}, {duration / 60:.1f} minutes; {len(pauses)} verified pauses', flush=True)

    results = await asyncio.gather(*(lesson(path, data) for path, data in selected), return_exceptions=True)
    failed = [{'lesson': path.stem, 'error': type(result).__name__} for (path, _), result in zip(selected, results) if isinstance(result, BaseException)]
    if failed:
        (CACHE / f'failed-lessons-{voice}.json').write_text(json.dumps(failed, indent=2))
        raise RuntimeError(f'{len(failed)} lessons need retry; completed lessons and paragraphs are cached: {failed}')
    (CACHE / f'failed-lessons-{voice}.json').unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('lessons', nargs='*', help='Explicit authored script stems')
    parser.add_argument('--all', action='store_true', help='Explicitly produce all authored scripts; never extracts page text')
    parser.add_argument('--voice', choices=VOICES, default=DEFAULT)
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--page-workers', type=int, default=1)
    parser.add_argument('--plan', action='store_true')
    args = parser.parse_args()
    assert 1 <= args.workers <= 24 and 1 <= args.page_workers <= 8
    if not args.all and not args.lessons:
        parser.error('Select script names, or explicitly use --all for the authorized authored-script rollout')
    if args.all and args.lessons:
        parser.error('Use named scripts or --all, not both')
    catalogue = {p.stem: (p, data) for p, data in spoken.scripts().values()}
    selected = list(catalogue.values()) if args.all else [catalogue[name] for name in dict.fromkeys(args.lessons)]
    selected = [(path, spoken.for_voice(data, args.voice)) for path, data in selected]
    for path, data in selected:
        print(path.stem, sum(len(p['text'].split()) for s in data['sections'] for p in s['paragraphs']), 'words; pauses explicitly authored', flush=True)
    if args.plan:
        return
    CACHE.mkdir(parents=True, exist_ok=True)
    build.build(include_narration=False)
    asyncio.run(produce(selected, args.workers, args.page_workers, args.voice))
    build.build()


if __name__ == '__main__':
    main()
