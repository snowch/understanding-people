"""A small navigation hierarchy backed by the reference catalogue.

Publishing a page does not automatically promote it into the global navigation.
Recordings belong to a reference entry; chapter pagination follows the book only.
"""
from html import escape
from pathlib import Path
import json
import os

ROOT = Path(__file__).resolve().parents[1]
GROUPS = json.loads((ROOT / 'reference/catalog.json').read_text())['groups']
BIASES = {e['slug']: e for e in json.loads((ROOT / 'reference/biases.json').read_text())['entries']}
ENTRIES = [e for g in GROUPS for e in g['entries']]
for entry in ENTRIES:
    entry['recordings'] = [dict(source=str(Path(a['path']).with_suffix('.md')), title=a['title'], duration=a['duration'], description=a['description'])
                           for a in BIASES.get(entry.get('biasSlug'), {}).get('listenings', [])]


def target(source):
    return Path('index.html') if source == 'book.md' else Path(source).with_suffix('.html')


def href(source, page, fragment=''):
    return escape(Path(os.path.relpath(target(source), page.parent)).as_posix() + fragment, quote=True)


def owner(source):
    return next((e for e in ENTRIES if source == e['source'] or any(a['source'] == source for a in e['recordings'])), None)


def section(source):
    if source.startswith('reference/') or owner(source) or source == 'glossary.md':
        return 'library'
    if source in ('practice/index.md', 'worksheet.md'):
        return 'practice'
    if source in ('evidence.md', 'support.md', 'references.md', 'about.md'):
        return 'about'
    return 'book'


def navigation(source, page, chapters):
    def link(item, title, number=None, fragment=''):
        current = ' aria-current="page"' if item == source and not fragment else ''
        number_html = f'<span class="nav-number">{number}</span>' if number is not None else ''
        return f'<li><a href="{href(item, page, fragment)}"{current}>{number_html}<span class="nav-title">{escape(title)}</span></a></li>'

    book = ''.join(link(s, t) for s, t in [('contents.md', 'Contents & reading routes'), ('how-to-use.md', 'How to use this book')])
    book += '<li><ol class="chapter-list">' + link('book.md', 'Introduction', '—')
    book += ''.join(link(s, t, f'{i:02}') for i, (t, s) in enumerate(chapters, 1))
    book += link('conclusion.md', 'Conclusion', '—') + '</ol></li>'
    library = link('reference/index.md', 'Browse & search all entries')
    library += ''.join(link('reference/index.md', g['title'], fragment='#'+g['id']) for g in GROUPS)
    entry = owner(source)
    if entry:
        library += '<li class="nav-topic"><p class="nav-context-label">CURRENT TOPIC</p><ul>'
        library += link(entry['source'], entry['title'])
        if entry['recordings']:
            library += '<li><ul class="nav-recordings">' + ''.join(link(a['source'], a['title']+' · '+a['duration']) for a in entry['recordings']) + '</ul></li>'
        library += '</ul></li>'
    library += link('glossary.md', 'Glossary')
    practice = link('practice/index.md', 'Choose a practice') + link('worksheet.md', 'Situation worksheet')
    about = ''.join(link(s, t) for s, t in [('about.md', 'About the book & author'), ('evidence.md', 'How we use evidence'), ('references.md', 'Sources & further reading'), ('support.md', 'When to seek other help')])
    groups = [('book', 'The book', book), ('library', 'Reference library', library), ('practice', 'Practice', practice), ('about', 'About & sources', about)]
    return ''.join(f'<details class="nav-section" data-section="{key}"{" open" if section(source) == key else ""}><summary>{title}</summary><ul class="section-links">{body}</ul></details>' for key, title, body in groups)


def breadcrumbs(source, page, title):
    if source == 'book.md':
        return ''
    parts = [('book.md', 'Home', '')]
    entry = owner(source)
    if entry:
        group = next(g for g in GROUPS if entry in g['entries'])
        parts += [('reference/index.md', 'Reference library', ''), ('reference/index.md', group['title'], '#'+group['id'])]
        if source != entry['source']:
            parts += [(entry['source'], entry['title'], '')]
    elif source == 'reference/index.md':
        pass
    elif section(source) == 'book' and source != 'contents.md':
        parts += [('contents.md', 'The book', '')]
    elif source == 'worksheet.md':
        parts += [('practice/index.md', 'Practice', '')]
    elif source == 'glossary.md':
        parts += [('reference/index.md', 'Reference library', '')]
    html = ''.join(f'<li><a href="{href(s, page, frag)}">{escape(t)}</a></li>' for s, t, frag in parts)
    return f'<nav class="breadcrumbs" aria-label="Breadcrumb"><ol>{html}<li aria-current="page">{escape(title)}</li></ol></nav>'


def pagination(source, page, chapters):
    sequence = [('book.md', 'Introduction')] + [(s, t) for t, s in chapters] + [('conclusion.md', 'Conclusion')]
    index = next((i for i, (s, _) in enumerate(sequence) if source == s), None)
    links = []
    if index is not None:
        for offset, label, rel in [(-1, 'Previous', 'prev'), (1, 'Next', 'next')]:
            if 0 <= index+offset < len(sequence):
                s, title = sequence[index+offset]
                links.append(f'<a rel="{rel}" href="{href(s, page)}"><small>{label}</small>{escape(title)}</a>')
    else:
        entry = owner(source)
        if entry and source != entry['source']:
            links.append(f'<a href="{href(entry["source"], page)}">← Back to {escape(entry["title"])}</a>')
        elif section(source) == 'library' and source != 'reference/index.md':
            links.append(f'<a href="{href("reference/index.md", page)}">← Reference library</a>')
        elif source == 'worksheet.md':
            links.append(f'<a href="{href("practice/index.md", page)}">← Choose a practice</a>')
    return ''.join(links)


def render_library():
    chunks = ['# Reference library', 'Find an explanation, compare possibilities and choose something to try. Each entry brings its reading, practice and any recordings together.',
              '<div class="library-search" hidden><label for="library-query">Find a topic or behaviour</label><div class="library-search-controls"><input id="library-query" type="search" placeholder="Try beliefs, attribution or independence…" aria-describedby="library-result-count"><button type="button" id="library-clear" hidden>Clear search</button></div><p id="library-result-count" role="status" aria-live="polite"></p></div>',
              '<nav class="library-topics" aria-label="Reference topics">' + ''.join(f'<a href="#{g["id"]}">{escape(g["title"])}</a>' for g in GROUPS) + '</nav>']
    for group in GROUPS:
        chunks += [f'<section class="library-group" markdown="1">', f'## {group["title"]} {{#{group["id"]}}}', group['description']]
        for entry in group['entries']:
            search = ' '.join([group['title'], entry['title'], entry['summary'], entry['keywords']])
            file = href(entry['source'], Path('reference/index.html'))
            chunks += [f'<article class="library-entry" data-library-search="{escape(search, quote=True)}"><h3><a href="{file}">{escape(entry["title"])}</a></h3><p>{escape(entry["summary"])}</p><p class="library-entry-formats">Read · Practise'+ (' · Listen' if entry['recordings'] else '') + '</p></article>']
        chunks += ['</section>']
    chunks += ['<p id="library-empty" hidden>No matching entries yet. Try a broader term, browse the topics, or look in the <a href="../glossary.html">glossary</a>.</p>',
               '## Looking for a starting point?', 'For a guided introduction, follow [the book’s chapters](../contents.md). For a short exercise, visit [Practice](../practice/index.md). The [glossary](../glossary.md) covers more terms than the detailed reference entries currently available.',
               '<script defer src="../assets/library.js"></script>']
    (ROOT/'reference/index.md').write_text('\n\n'.join(chunks)+'\n')
