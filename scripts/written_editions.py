"""Explicit text-first revisions. Never alter or silently rebind approved recordings."""
import hashlib
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

@lru_cache(maxsize=1)
def editions():
    path = ROOT / 'audio/written-editions.json'
    data = json.loads(path.read_text()) if path.exists() else {'version': 1, 'pages': {}}
    assert data['version'] == 1
    return data['pages']

def verify(source, fingerprint, manifests):
    """A text-only route must bind its actual text; archived audio stays verified."""
    item = editions().get(source)
    if not item:
        return False
    assert item['reason'].strip() and item['date']
    assert item['page_text_sha256'] == fingerprint, f'Written edition changed: review {source}'
    recorded = item['status'] == 'revised-text'
    assert recorded or item['status'] == 'new-text'
    from spoken_narration import scripts, for_voice, fingerprint as script_fingerprint
    for voice, manifest in manifests.items():
        entry = manifest['pages'].get(source)
        if not recorded:
            assert entry is None and source not in scripts(), f'{source}: use a revision record for existing audio'
            continue
        assert entry and item['recorded_page_text_sha256'] == entry['page_text_sha256']
        assert item['recorded_source_hashes'] == entry['source_hashes']
        path, script = scripts()[source]
        assert entry['script_sha256'] == script_fingerprint(for_voice(script, voice))
        assert entry['script_source'] == path.relative_to(ROOT).as_posix()
        assert [(s['title'],s['anchor']) for s in entry['sections']] == [(s['title'],s['anchor']) for s in script['sections']]
        assert entry['pauses_verified'] and entry['pause_engine_version'] == 1
        from narration_voices import media_path
        for suffix,key in [('.mp3','audio_sha256'),('.txt','transcript_sha256')]:
            assert hashlib.sha256((ROOT/media_path(source,suffix,voice)).read_bytes()).hexdigest() == entry[key]
        actual={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in script['source_files']}
        assert actual == item['current_source_hashes'], f'Unreviewed source revision: {source}'
    return True

def recorded_sources(pages):
    from page_narration import eligible
    return {s for s,_ in pages if eligible(s) and editions().get(s,{}).get('status') != 'new-text'}
