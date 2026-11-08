"""Explicit unchanged-entry reviews when another entry in a source container changes.

Approved manifests, scripts and media stay immutable. This exception only accepts
an unchanged canonical entry, unchanged lesson extraction and the exact reviewed
old/current container hashes. Revised teaching uses written_editions instead.
"""
import hashlib
import json
from functools import lru_cache
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def entry_hash(data):
    return hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

@lru_cache(maxsize=1)
def reviews():
    path=ROOT/'audio/source-container-reviews.json'
    if not path.exists():return {}
    data=json.loads(path.read_text())
    assert data['version']==1 and data['date'] and data['reason'].strip()
    return data['pages']

def verify(source,script,entry,current):
    review=reviews().get(source)
    if not review:return False
    assert review['recorded_source_hashes']==entry['source_hashes'],source
    assert review['current_source_hashes']==current,source
    assert review['page_text_sha256']==entry['page_text_sha256'],source
    assert review['script_sha256'][script['voice']]==entry['script_sha256'],source
    assert len(script['source_files'])==1, 'Only a reviewed canonical entry container is eligible'
    path=script['source_files'][0]
    assert path.startswith('reference/entries/') and path.endswith('.json')
    entries=json.loads((ROOT/path).read_text())['entries']
    canonical=next(e for e in entries if e['id']==review['entry_id'])
    assert entry_hash(canonical)==review['canonical_entry_sha256'],f'Entry changed after source-container review: {source}'
    return True
