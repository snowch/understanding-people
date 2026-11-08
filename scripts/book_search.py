"""Build a passage catalogue from the reading HTML; never calls a model/network."""
import hashlib
import json
from pathlib import Path
import re

from page_narration import Tree, Node, descendants, inline, eligible, ROOT
from book_navigation import ENTRIES

ASSETS = ROOT / 'assets/search'
SKIP = {'practice-notes', 'reference-formats', 'library-search', 'library-topics',
        'audio-edition', 'reference-listenings', 'audio-exercise', 'audio-chapters', 'notes-help'}
SKIP_SECTIONS = {'related entries', 'sources', 'references', 'selected sources', 'further reading',
                 'sources and further reading', 'research sources', 'what to read next'}


def text_of(node):
    if isinstance(node, str):
        return node
    text = ''.join(text_of(c) for c in node.children)
    return ' ' + text + ' ' if node.tag in {'p', 'li', 'dd', 'dt', 'div', 'tr'} else text


def digest(data):
    return hashlib.sha256(data).hexdigest()


def packed(data):
    return json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode()


def catalogue(out, pages, chapters):
    from reference_terminology import terms as glossary_terms
    glossary_listen = {t['id']:t['source'].replace('.md','.html')+'#page-narration-title' for t in glossary_terms()}
    entries = {e['source']: e for e in ENTRIES}
    chapter_numbers = {s: i for i, (_, s) in enumerate(chapters, 1)}
    documents, passages = [], []
    for source, label in pages:
        if not eligible(source):
            continue
        url = 'index.html' if source == 'book.md' else source.replace('.md', '.html')
        tree = Tree((out / url).read_text()).root
        prose = next(n for n in descendants(tree, 'div') if 'prose' in n.attrs.get('class', '').split())
        title = inline(next(descendants(tree, 'h1'))).strip()
        all_nodes = [tree, *(n for tag in ['h2', 'h3', 'h4', 'section', 'div'] for n in descendants(tree, tag))]
        ids = {n.attrs['id'] for n in all_nodes if 'id' in n.attrs}
        practice = next((s for s in ['put-it-into-practice', 'practice', 'try-it', 'reader-action'] if s in ids), None)
        if not practice:
            practice = next((n.attrs.get('aria-labelledby') for n in descendants(prose, 'section') if 'reader-action' in n.attrs.get('class', '').split()), None)
        entry = entries.get(source, {})
        kind = ('Reference' if source in entries else f'Chapter {chapter_numbers[source]}' if source in chapter_numbers
                else 'Glossary' if source == 'glossary.md' else 'Introduction' if source == 'book.md' else 'Reading guide')
        doc = {'url': url, 'title': title, 'kind': kind, 'keywords': entry.get('keywords', ''), 'aliases': entry.get('aliases', []),
               'clinical': 'disorder' in title.lower(),
               'listen': 'page-narration-title' if 'page-narration-title' in ids else None, 'practice': practice}
        document_id = len(documents); documents.append(doc)
        sections = [{'anchor': 'main', 'heading': title, 'paragraphs': []}]
        parent = ''
        skip_section = False

        def walk(n):
            nonlocal parent, skip_section
            if isinstance(n, str):
                return
            classes = set(n.attrs.get('class', '').split())
            if n.tag in {'nav', 'script', 'style', 'noscript', 'audio', 'video', 'button', 'input', 'select', 'textarea', 'label', 'form'} or classes & SKIP or 'hidden' in n.attrs:
                return
            if n.tag in {'h2', 'h3', 'h4'}:
                text = re.sub(r'\s+', ' ', inline(n)).strip()
                if n.tag == 'h2':
                    parent = text
                    skip_section = text.casefold() in SKIP_SECTIONS
                heading = ' / '.join(dict.fromkeys(v for v in [parent, text] if v))
                sections.append({'anchor': n.attrs.get('id', 'main'), 'heading': heading, 'paragraphs': []})
                return
            if n.tag in {'p', 'li', 'dt', 'dd', 'tr'} and not any(isinstance(c, Node) and c.tag in {'p', 'ul', 'ol', 'dl'} for c in n.children):
                text = re.sub(r'\s+', ' ', text_of(n)).strip()
                if text and not skip_section:
                    sections[-1]['paragraphs'].append(text)
                return
            for c in n.children:
                walk(c)

        walk(prose)
        for section in sections:
            words = ' '.join(section['paragraphs']).split()
            for start in range(0, len(words), 120):
                text = ' '.join(words[max(0, start-20):start+140])
                if len(text) < 35:
                    continue
                passage = {'document': document_id, 'anchor': section['anchor'], 'heading': section['heading'], 'text': text}
                if source == 'glossary.md' and section['anchor'] in glossary_listen:
                    passage['listen_url'] = glossary_listen[section['anchor']]
                passages.append(passage)
    return {'version': 1, 'documents': documents, 'passages': passages}


def engine():
    data = json.loads((ASSETS / 'engine.json').read_text())
    for file in data['assets']:
        path = ASSETS / file['path']
        assert path.stat().st_size == file['bytes'] and digest(path.read_bytes()) == file['sha256'], f'Search engine asset changed: {path}'
    return data


def write_index(out, pages, chapters):
    data = catalogue(out, pages, chapters)
    manifest = json.loads((ASSETS / 'vectors.json').read_text())
    assert manifest['corpus_sha256'] == digest(packed(data)), 'Search passages changed. Rebuild embeddings with scripts/prepare_search.py; do not serve stale vectors.'
    assert manifest['engine_sha256'] == digest((ASSETS / 'engine.json').read_bytes())
    assert manifest['passages'] == len(data['passages'])
    assert digest((ASSETS / 'vectors.bin').read_bytes()) == manifest['vectors_sha256']
    assert (ASSETS / 'vectors.bin').stat().st_size == len(data['passages']) * 384
    engine_data = engine()
    data.update({'corpus_sha256': manifest['corpus_sha256'], 'dimensions': 384,
                 'vectors_sha256': manifest['vectors_sha256'],
                 'engine_sha256': manifest['engine_sha256'], 'engine_bytes': sum(a['bytes'] for a in engine_data['assets'])})
    (out / 'assets/search/index.json').write_bytes(packed(data))
    return ['assets/search/' + a['path'] for a in engine_data['assets']]
