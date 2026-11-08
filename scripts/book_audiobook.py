"""Audiobook ordering and the offline-download catalogue. No synthesis here."""
from html import escape
from pathlib import Path
import hashlib
import json
import os
import re
from urllib.parse import quote

from book_navigation import ENTRIES, target
from narration_voices import ROOT, VOICES, manifest_path
from page_narration import eligible

MANIFEST = ROOT / 'audio/audiobook-manifest.json'
REPOSITORY = 'snowch/understanding-people'


def ordering(chapters, pages):
    from written_editions import recorded_sources
    recorded = recorded_sources(pages)
    core = [('book.md', 'Introduction')]
    core += [(source, f'{i:02}. {title}') for i, (title, source) in enumerate(chapters, 1)]
    core += [('conclusion.md', 'Conclusion — What to take with you')]
    references = [(entry['source'], 'Reference — ' + entry['title']) for entry in ENTRIES if entry['source'] in recorded]
    used = {source for source, _ in [*core, *references]}
    guides = [(source, 'Guide — ' + title) for source, title in pages if source in recorded and source not in used]
    complete = core + references + guides
    expected = recorded
    assert len(core) == 14 and len(complete) == len(expected)
    assert {source for source, _ in complete} == expected
    return {'complete': complete, 'course': core}


def load(chapters, pages, editions):
    data = json.loads(MANIFEST.read_text())
    assert data['version'] == 1 and data['repository'] == REPOSITORY
    assert re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', data['release_tag'])
    expected = ordering(chapters, pages)
    for voice, info in VOICES.items():
        assert data['voices'][voice]['voice'] == info['id']
        assert data['voices'][voice]['narration_manifest_sha256'] == hashlib.sha256(manifest_path(voice).read_bytes()).hexdigest(), 'Review and repackage the audiobook after changing narration'
        for kind, sequence in expected.items():
            edition = data['voices'][voice]['editions'][kind]
            assert edition['filename'] == f'understanding-people-{kind}-{voice}.m4b'
            assert [(c['source'], c['title']) for c in edition['chapters']] == sequence
            assert edition['url'] == f'https://github.com/{REPOSITORY}/releases/download/{data["release_tag"]}/{edition["filename"]}'
            assert edition['bytes'] > 0 and len(edition['sha256']) == 64
            assert edition['chapters'][0]['start_sample'] == 0
            previous = 0
            for chapter in edition['chapters']:
                assert chapter['start_sample'] == previous and chapter['end_sample'] > previous
                assert chapter['audio_sha256'] == editions[voice]['pages'][chapter['source']]['audio_sha256']
                previous = chapter['end_sample']
    return data


def duration(seconds):
    minutes = round(seconds / 60)
    hours, minutes = divmod(minutes, 60)
    return (f'{hours} hr ' if hours else '') + f'{minutes} min'


def render(data, page):
    def download(voice, kind):
        info, edition = VOICES[voice], data['voices'][voice]['editions'][kind]
        return (f'<a class="audiobook-download" href="{escape(edition["url"], quote=True)}" download="{edition["filename"]}" '
                f'aria-label="Download {info["name"]} — {"complete book" if kind == "complete" else "course only"}">Download {info["name"]}<span aria-hidden="true">↓</span></a>'
                f'<p class="audiobook-file-info">M4B · {duration(edition["duration"])} · {edition["bytes"] / 1_000_000:.0f} MB · {len(edition["chapters"])} chapters</p>')
    cards = []
    settings = Path(os.path.relpath(Path('settings.html'), page.parent)).as_posix() + '?return=' + quote(page.as_posix(), safe='')
    for voice, info in VOICES.items():
        cards.append(f'<section class="audiobook-edition" data-audiobook-voice="{voice}"><h3>{info["name"]}</h3><span class="audiobook-preferred" data-download-preferred hidden>Your selected voice</span><p>Synthetic narration · US English</p>{download(voice,"complete")}<a class="audiobook-preview" href="{settings}">Preview the voices in Settings</a></section>')
    core = ''.join('<div>' + download(voice, 'course') + '</div>' for voice in VOICES)
    chapters = data['voices']['andrew']['editions']['course']['chapters']
    sequence = ''.join('<li><a href="' + escape(Path(os.path.relpath(target(c['source']), page.parent)).as_posix(), quote=True) + '">' + escape(c['title']) + '</a></li>' for c in chapters)
    return f'''<section class="audiobook-library" aria-labelledby="complete-audiobook">
<h2 id="complete-audiobook">The recorded book, in one file</h2>
<p>This edition contains the course, reference library and reading guides in {len(data['voices']['andrew']['editions']['complete']['chapters'])} sections, including the expanded reference library. Each section is adapted for listening, with time to reflect.</p>
<div class="audiobook-editions">{''.join(cards)}</div>
<details class="audiobook-course"><summary>Smaller download: just the course</summary><p>One file per voice, containing the introduction, twelve chapters and conclusion. The reference library and reading guides are left out of this smaller edition.</p><div class="audiobook-course-links">{core}</div></details>
<details class="audiobook-contents"><summary>The first fourteen chapters</summary><ol>{sequence}</ol><p>The complete edition continues with reference entries grouped by topic, then reading and support guides.</p></details>
<p class="audiobook-release">Downloads are hosted in this book’s GitHub Releases. No GitHub account is needed. <a href="https://github.com/{REPOSITORY}/releases/tag/{data['release_tag']}">Edition details and checksums</a>.</p>
</section>'''
