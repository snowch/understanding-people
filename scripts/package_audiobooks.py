#!/usr/bin/env python3
"""Package existing recordings into single-file, chaptered AAC-LC M4B editions.

Explicit production only; never called by the normal website build. Temporary
PCM and final release artifacts stay outside Git and the Pages output.
"""
import argparse
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import wave

from book_audiobook import ordering, REPOSITORY, MANIFEST
from narration_voices import ROOT, VOICES, manifest_path, media_path

RATE = 24000


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-show_chapters', '-of', 'json', str(path)]))


def atoms(stream, start, end):
    offset = start
    while offset < end:
        stream.seek(offset)
        header = stream.read(8)
        assert len(header) == 8
        size, name = struct.unpack('>I4s', header)
        length = 8
        if size == 1:
            size = struct.unpack('>Q', stream.read(8))[0]
            length = 16
        if size == 0:
            size = end - offset
        assert size >= length and offset + size <= end
        yield name, offset, offset + length, offset + size
        offset += size


def nero_chapters(path):
    with path.open('rb') as stream:
        top = list(atoms(stream, 0, path.stat().st_size))
        moov = next(a for a in top if a[0] == b'moov')
        assert moov[1] < next(a[1] for a in top if a[0] == b'mdat'), 'Fast-start metadata must precede audio'
        udta = next(a for a in atoms(stream, moov[2], moov[3]) if a[0] == b'udta')
        chpl = next(a for a in atoms(stream, udta[2], udta[3]) if a[0] == b'chpl')
        stream.seek(chpl[2]); data = stream.read(chpl[3] - chpl[2])
        assert data[0] == 1
        count, cursor, result = data[8], 9, []
        for _ in range(count):
            start = struct.unpack_from('>Q', data, cursor)[0] / 10_000_000
            length = data[cursor + 8]; cursor += 9
            title = data[cursor:cursor+length].decode('utf-8'); cursor += length
            result.append((start, title))
        assert cursor == len(data)
        return result


def verify(path, chapters):
    data = probe(path)
    audio = [s for s in data['streams'] if s['codec_type'] == 'audio']
    assert len(audio) == 1 and audio[0]['codec_name'] == 'aac' and audio[0]['profile'] == 'LC'
    assert int(audio[0]['sample_rate']) == RATE and audio[0]['channels'] == 1
    assert any(s.get('disposition', {}).get('attached_pic') for s in data['streams']), 'Book artwork is missing'
    assert len(data['chapters']) == len(chapters)
    nero = nero_chapters(path)
    assert len(nero) == len(chapters)
    for expected, actual, alternate in zip(chapters, data['chapters'], nero):
        assert actual['tags']['title'] == alternate[1] == expected['title']
        assert abs(float(actual['start_time']) - expected['start_sample']/RATE) < .003
        assert abs(alternate[0] - expected['start_sample']/RATE) < .003
    duration = float(data['format']['duration'])
    assert abs(duration - chapters[-1]['end_sample']/RATE) < .25
    assert int(data['format']['tags']['media_type']) == 2
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(path), '-map', '0:a:0', '-f', 'null', '-'], check=True)
    return duration


def metadata(path, chapters, title, voice):
    def escape(text):
        return text.replace('\\', '\\\\').replace('=', '\\=').replace(';', '\\;').replace('#', '\\#').replace('\n', '\\\n')
    lines = [';FFMETADATA1', 'title=' + escape(title), 'artist=Christopher Snow', 'album=Understanding people',
             'genre=Audiobook', 'media_type=2', 'copyright=Copyright 2026 Christopher Snow',
             'comment=Synthetic narration: ' + VOICES[voice]['id'] + '. Existing authored recordings, with their pauses.']
    for c in chapters:
        assert len(c['title'].encode()) <= 255, 'Chapter name exceeds the interoperable Nero limit'
        lines += ['[CHAPTER]', f'TIMEBASE=1/{RATE}', 'START='+str(c['start_sample']), 'END='+str(c['end_sample']), 'title='+escape(c['title'])]
    path.write_text('\n'.join(lines)+'\n')


def produce(voice, sequences, output, cache):
    narration = json.loads(manifest_path(voice).read_text())
    assert narration['voice'] == VOICES[voice]['id']
    wav_path = cache / (voice + '-complete.wav')
    chapters, cursor = [], 0
    try:
        with wave.open(str(wav_path), 'wb') as wav:
            wav.setparams((1, 2, RATE, 0, 'NONE', 'not compressed'))
            for source, title in sequences['complete']:
                entry = narration['pages'][source]
                original = ROOT / media_path(source, '.mp3', voice)
                assert sha(original) == entry['audio_sha256']
                pcm = subprocess.check_output(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(original), '-map', '0:a:0', '-ar', str(RATE), '-ac', '1', '-f', 's16le', '-'])
                assert len(pcm) % 2 == 0 and pcm
                frames = len(pcm) // 2
                chapters.append({'source': source, 'title': title, 'start_sample': cursor, 'end_sample': cursor+frames,
                                 'audio_sha256': entry['audio_sha256'], 'decoded_pcm_sha256': hashlib.sha256(pcm).hexdigest()})
                wav.writeframesraw(pcm); cursor += frames
                print(f'{voice}: assembled {len(chapters)}/{len(sequences["complete"])}', flush=True)
        editions = {}
        for kind in ['course', 'complete']:
            selected = chapters[:len(sequences['course'])] if kind == 'course' else chapters
            filename = f'understanding-people-{kind}-{voice}.m4b'
            final = output / filename
            temporary = output / (filename + '.partial')
            meta = cache / (voice + '-' + kind + '.ffmetadata')
            title = f'Understanding people — {"complete book" if kind == "complete" else "course"} ({VOICES[voice]["name"]})'
            metadata(meta, selected, title, voice)
            seconds = selected[-1]['end_sample'] / RATE
            print(f'{voice}: encoding {kind}, {seconds/3600:.2f} hours', flush=True)
            subprocess.run(['ffmpeg', '-nostdin', '-hide_banner', '-v', 'error', '-y', '-i', str(wav_path), '-i', str(meta), '-i', str(ROOT/'assets/icon-512.png'),
                            '-t', str(seconds), '-map', '0:a:0', '-map', '2:v:0', '-map_metadata', '1', '-map_chapters', '1',
                            '-c:a', 'aac', '-profile:a', 'aac_low', '-b:a', '80k', '-ar', str(RATE), '-ac', '1', '-c:v', 'copy',
                            '-disposition:v', 'attached_pic', '-movflags', '+faststart', '-f', 'ipod', str(temporary)], check=True)
            verified_duration = verify(temporary, selected)
            temporary.replace(final)
            editions[kind] = {'filename': filename, 'bytes': final.stat().st_size, 'sha256': sha(final), 'duration': verified_duration,
                              'chapter_count': len(selected), 'chapters': selected, 'codec': 'AAC-LC', 'sample_rate': RATE, 'channels': 1, 'bitrate': 80000}
            print(f'{voice}: verified {filename}, {len(selected)} markers in both chapter tables', flush=True)
        return {'voice': VOICES[voice]['id'], 'narration_manifest_sha256': sha(manifest_path(voice)), 'editions': editions}
    finally:
        wav_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release-tag', required=True)
    parser.add_argument('--output', type=Path, default=Path('/workspace/audiobook-release'))
    parser.add_argument('--cache', type=Path, default=Path('/workspace/audiobook-packaging-cache'))
    args = parser.parse_args()
    assert all(c.isalnum() or c in '-._' for c in args.release_tag)
    for folder in [args.output, args.cache]:
        assert not folder.resolve().is_relative_to(ROOT), 'Large release artifacts and intermediates must stay outside Git/Pages'
        folder.mkdir(parents=True, exist_ok=True)
    from build import CHAPTERS, PAGES
    sequences = ordering(CHAPTERS, PAGES)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        jobs = {voice: pool.submit(produce, voice, sequences, args.output, args.cache) for voice in VOICES}
        voices = {voice: future.result() for voice, future in jobs.items()}
    data = {'version': 1, 'repository': REPOSITORY, 'release_tag': args.release_tag, 'generated': datetime.now(timezone.utc).isoformat(),
            'source_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True, cwd=ROOT).strip(),
            'producer_sha256': sha(Path(__file__)), 'cover_source': 'assets/icon-512.png', 'cover_sha256': sha(ROOT/'assets/icon-512.png'), 'voices': voices}
    sums = []
    for record in voices.values():
        for edition in record['editions'].values():
            edition['url'] = f'https://github.com/{REPOSITORY}/releases/download/{args.release_tag}/{edition["filename"]}'
            sums.append(edition['sha256'] + '  ' + edition['filename'])
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    (args.output/'SHA256SUMS.txt').write_text('\n'.join(sums)+'\n')
    (args.output/'audiobook-manifest.json').write_bytes(MANIFEST.read_bytes())
    print('All four single-file audiobooks verified. Publish release assets before pushing the download page.', flush=True)


if __name__ == '__main__':
    main()
