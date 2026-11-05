"""Authored listening scripts and their source/recording integrity contract."""
import hashlib
import copy
import json
import re
from pathlib import Path
from narration_voices import VOICES, DEFAULT

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'audio/spoken'
ENGINE_VERSION = 1
SAMPLE_RATE = 24000


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scripts():
    result = {}
    for path in sorted(DIRECTORY.glob('*.json')):
        data = json.loads(path.read_text())
        validate(data)
        assert data['source'] not in result, 'Duplicate spoken script source'
        result[data['source']] = (path, data)
    return result


def validate(data):
    assert data['version'] == 1
    assert data['voice'] in {v['id'] for v in VOICES.values()} and data['rate'] == '-2%'
    assert data['source_files'] and data['sections']
    for path in [data['source'], *data['source_files']]:
        target = (ROOT / path).resolve()
        assert target.is_relative_to(ROOT) and target.is_file(), path
    for section in data['sections']:
        assert section['title'] and section['anchor'] and section['paragraphs']
        for paragraph in section['paragraphs']:
            text = paragraph['text']
            assert text.strip() == text and len(text.split()) <= 120, 'Use a connected spoken paragraph, not a page/chunk'
            assert not any(token in text.lower() for token in ['https://', 'doi.org', 'doi:', 'et al.', 'go deeper:', 'research record.', 'show an example answer', 'plain-text transcript'])
            assert not re.search(r'\([12]\d{3}[a-z]?\)', text), 'Introduce research conversationally, not as a parenthetical citation'
            assert not re.match(r'^(Definition|Evidence|Example|Limit):', text), 'Write a spoken transition instead of reading a page label'
            assert text.endswith(('.', '?', '!', '”')), 'Do not split an unfinished sentence'
            assert 700 <= paragraph['pause_after_ms'] <= 15000
        assert section['paragraphs'][-1]['pause_after_ms'] >= 1400, 'Give a topic transition room'


def fingerprint(data):
    return hashlib.sha256(json.dumps({'engine': ENGINE_VERSION, 'script': data}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def source_hashes(data):
    return {name: sha(ROOT / name) for name in data['source_files']}


def transcript(data):
    blocks = []
    for section in data['sections']:
        for paragraph in section['paragraphs']:
            blocks.append(paragraph['text'])
            if paragraph['pause_after_ms'] >= 3000:
                blocks.append('[Pause: ' + str(paragraph['pause_after_ms'] / 1000).removesuffix('.0') + ' seconds. Pause the player for longer if helpful.]')
    return '\n\n'.join(blocks) + '\n'


def for_voice(data, voice=DEFAULT):
    """One authored text, independently timed recordings for each narrator."""
    result = copy.deepcopy(data)
    result['voice'] = VOICES[voice]['id']
    validate(result)
    return result


def check_entry(source, body_fingerprint, entry, voice=DEFAULT):
    path, data = scripts()[source]
    data = for_voice(data, voice)
    assert entry['script_source'] == path.relative_to(ROOT).as_posix()
    assert entry['script_sha256'] == fingerprint(data), f'Spoken script changed for {source}; review it and run scripts/synthesise_spoken.py {path.stem}'
    assert entry['source_hashes'] == source_hashes(data), f'Written source changed for {source}; review the spoken adaptation before recording'
    assert entry['page_text_sha256'] == body_fingerprint, f'Page teaching changed for {source}; review the spoken adaptation before recording'
    expected = [(s['title'], s['anchor']) for s in data['sections']]
    assert [(s['title'], s['anchor']) for s in entry['sections']] == expected
    assert entry.get('pause_engine_version') == ENGINE_VERSION and entry.get('pauses_verified')
    return data
