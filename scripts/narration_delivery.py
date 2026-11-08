"""Immutable release delivery for new MP3s beyond the Pages size budget.

Recordings remain in Git and retain normal source/file verification. Only
selected MP3s are omitted from Pages; transcripts stay with their reading page.
"""
import hashlib
import json
import re
import shutil
from functools import lru_cache
from pathlib import Path

from narration_voices import ROOT, VOICES, manifest_path, media_path

MANIFEST = ROOT / 'audio/narration-delivery.json'


@lru_cache(maxsize=1)
def config():
    if not MANIFEST.exists():
        return {'pages': []}
    data = json.loads(MANIFEST.read_text())
    assert data['version'] == 1 and data['repository'] == 'snowch/understanding-people'
    assert re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', data['release_tag'])
    assert len(data['pages']) == len(set(data['pages']))
    for source in data['pages']:
        assert source.startswith('reference/') and source.endswith('.md')
        assert (ROOT/source).resolve().is_relative_to(ROOT) and (ROOT/source).is_file()
    return data


def filename(source, voice, entry):
    return f'narration-{voice}-{Path(source).stem}-{entry["audio_sha256"][:12]}.mp3'


def remote_url(source, voice, entry):
    data = config()
    if source not in data['pages']:
        return None
    return f'https://github.com/{data["repository"]}/releases/download/{data["release_tag"]}/{filename(source,voice,entry)}'


def excluded_paths():
    return {media_path(source, '.mp3', voice).as_posix() for source in config()['pages'] for voice in VOICES}


def export(output):
    """Copy only checksum-verified finals to an existing release directory."""
    data = config()
    result = []
    for voice in VOICES:
        manifest = json.loads(manifest_path(voice).read_text())
        for source in data['pages']:
            entry = manifest['pages'][source]
            path = ROOT / media_path(source, '.mp3', voice)
            assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['audio_sha256']
            name = filename(source, voice, entry)
            shutil.copyfile(path, output/name)
            result.append({'source':source, 'voice':voice, 'filename':name,
                           'bytes':path.stat().st_size, 'sha256':entry['audio_sha256'],
                           'url':remote_url(source,voice,entry)})
    (output/'narration-assets.json').write_text(json.dumps({'version':1, 'release_tag':data['release_tag'], 'files':result}, indent=2)+'\n')
    return result
