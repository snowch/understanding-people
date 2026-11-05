"""Published narrator editions. The original Andrew URLs remain stable."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = 'andrew'
VOICES = {
    'andrew': {'name': 'Andrew', 'id': 'en-US-AndrewMultilingualNeural', 'bitrate': '96k'},
    'jenny': {'name': 'Jenny', 'id': 'en-US-JennyNeural', 'bitrate': '80k'},
}


def manifest_path(voice=DEFAULT):
    assert voice in VOICES
    return ROOT / 'audio' / ('narration-manifest.json' if voice == DEFAULT else f'narration-{voice}-manifest.json')


def media_path(source, suffix, voice=DEFAULT):
    assert voice in VOICES
    base = Path('assets/media/narration')
    if voice != DEFAULT:
        base /= voice
    return base / Path(source).with_suffix(suffix)
