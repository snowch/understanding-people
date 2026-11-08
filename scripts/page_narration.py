"""Derive page narration from authored reading content, without navigation or forms.

No TTS requests happen during the site build. A checked manifest binds each
recording to the spoken text and section anchors of its current page.
"""
import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from narration_voices import media_path, manifest_path, VOICES, DEFAULT

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "audio/narration-manifest.json"
VOICE = "en-US-AndrewMultilingualNeural"
RATE = "-2%"
VERSION = 1
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


@dataclass
class Node:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)


class Tree(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Node("root")
        self.stack = [self.root]
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def clean(text):
    return re.sub(r"\s+", " ", text.replace("&", " and ").replace("→", ", then ").replace("↗", "").replace("\xa0", " ")).strip()


def sentence(text):
    text = clean(text)
    return text if not text or text.endswith((".", "?", "!", "…", ":", ";", '"', "”", "’")) else text + "."


def inline(node):
    if isinstance(node, str):
        return node
    if node.tag == "br":
        return " "
    return "".join(inline(c) for c in node.children)


def descendants(node, tag):
    for child in node.children:
        if isinstance(child, Node):
            if child.tag == tag:
                yield child
            yield from descendants(child, tag)


def eligible(source):
    # Compatibility notices/redirects have no independent lesson to narrate.
    return not source.startswith("audio/") and source not in {'settings.md', 'downloads/index.md', 'search.md', 'reading-list.md'}


def speech_sections(title, body):
    opening = sentence(title)
    if clean(title).casefold() != 'understanding people':
        opening = 'Understanding people. ' + opening
    sections = [{"title": title, "anchor": "main", "paragraphs": [opening]}]
    skipped = {"page-narration", "reference-listenings", "audio-edition", "audio-exercise", "practice-notes",
               "reference-formats", "library-search", "library-topics", "library-entry-formats", "notes-help", "audio-chapters"}

    def add(text):
        text = clean(text)
        if text:
            sections[-1]["paragraphs"].append(sentence(text))

    def walk(node):
        if isinstance(node, str):
            if node.strip():
                add(node)
            return
        classes = set(node.attrs.get("class", "").split())
        if "practice-notes" in classes:
            add("Optional practice notes are available on the page. Pause the recording if you want to write.")
            return
        if (node.tag in {"script", "style", "nav", "noscript", "audio", "video", "button", "select", "textarea", "input"}
                or classes & skipped or "hidden" in node.attrs or node.attrs.get("aria-hidden") == "true"):
            return
        if node.tag in {"h2", "h3", "h4"}:
            heading = clean(inline(node))
            sections.append({"title": heading, "anchor": node.attrs.get("id", "main"), "paragraphs": [sentence(heading)]})
            return
        if node.tag == "table":
            rows = list(descendants(node, "tr"))
            headers = []
            if rows and any(c.tag == "th" for c in rows[0].children if isinstance(c, Node)):
                headers = [clean(inline(c)) for c in rows.pop(0).children if isinstance(c, Node) and c.tag in {"th", "td"}]
            for row in rows:
                cells = [clean(inline(c)) for c in row.children if isinstance(c, Node) and c.tag in {"th", "td"}]
                add(" ".join((headers[i] + ": " if i < len(headers) else "") + value.rstrip(".") + "." for i, value in enumerate(cells)))
            return
        if node.tag == "details" and "answer-check" in classes:
            add("Pause here to consider your answer before listening to the example answer.")
        elif node.tag == "details" and "more-practice" in classes:
            add("Optional deeper practice follows. You can stop here or continue.")
        if node.tag in {"p", "summary", "dt", "li"}:
            # Nested lists and multi-paragraph list items must retain their order.
            block_children = any(isinstance(c, Node) and c.tag in {"p", "ul", "ol", "details"} for c in node.children)
            if not block_children:
                add(inline(node))
                return
        if node.tag in {"pre", "code"}:
            add(inline(node))
            return
        for child in node.children:
            walk(child)

    walk(Tree(body).root)
    return [s for s in sections if s["paragraphs"]]


def fingerprint(sections):
    payload = {"version": VERSION, "voice": VOICE, "rate": RATE, "sections": sections}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def transcript(sections):
    return "\n\n".join("\n\n".join(s["paragraphs"]) for s in sections) + "\n"


def load_manifest(voice=DEFAULT):
    path = manifest_path(voice)
    if not path.exists():
        return None
    manifest = json.loads(path.read_text())
    assert manifest["voice"] == VOICES[voice]['id'] and manifest["rate"] == RATE and manifest["version"] == VERSION
    return manifest


def stamp(seconds):
    seconds = round(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02}:{seconds:02}" if hours else f"{minutes}:{seconds:02}"


def render(source, title, body, page, manifest, editions=None):
    if not eligible(source) or manifest is None:
        return ""
    sections = speech_sections(title, body)
    editions = editions or {DEFAULT: manifest}
    from written_editions import verify as verify_written
    if verify_written(source, fingerprint(sections), editions):
        return '<p class="narration-update">Written edition · Audio for this text is not available. Existing audiobook downloads retain their recorded edition.</p>'
    variants = {}
    for voice, edition in editions.items():
        entry = edition['pages'].get(source)
        assert entry, f'{VOICES[voice]["name"]} narration is missing for {source}'
        from spoken_narration import check_entry
        check_entry(source, fingerprint(sections), entry, voice)
        for suffix, key in ((".mp3", "audio_sha256"), (".txt", "transcript_sha256")):
            path = ROOT / media_path(source, suffix, voice)
            assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == entry[key], f"Narration file checksum mismatch: {path}"
        def edition_url(suffix, key):
            if suffix == '.mp3':
                from narration_delivery import remote_url
                remote = remote_url(source, voice, entry)
                if remote:
                    return remote
            return Path(os.path.relpath(media_path(source, suffix, voice), page.parent)).as_posix() + '?v=' + entry[key][:12]
        variants[voice] = {'name': VOICES[voice]['name'], 'audio': edition_url('.mp3', 'audio_sha256'),
                           'filename': Path(source).stem + '-' + VOICES[voice]['id'] + '.mp3',
                           'transcript': edition_url('.txt', 'transcript_sha256'),
                           'duration': stamp(entry['duration']), 'seconds': entry['duration'], 'sections': entry['sections']}
    entry = manifest['pages'][source]
    is_lesson = entry.get('mode') == 'spoken-lesson'
    def url(suffix):
        return escape(variants[DEFAULT]['audio' if suffix == '.mp3' else 'transcript'], quote=True)
    practice_hint = ('Includes optional practice and example answers: pause when prompted. ' if 'class="answer-check"' in body
                     else 'Pause whenever you want to reflect or write. ' if 'class="reader-action"' in body else '')
    if is_lesson:
        practice_hint = ('A spoken adaptation. Full references and additional practice are on the written page. '
                         if 'reader-action' in body else 'A spoken adaptation. The written page has the full text and links. ')
    jumps = "".join(f'<li><button type="button" hidden data-audio-seek="page-narration-audio" data-start="{s["start"]}">{stamp(s["start"])} · {escape(s["title"])}</button><a href="#{escape(s["anchor"], quote=True)}">Read {escape(s["title"])}</a></li>' for s in entry["sections"])
    choices = ''.join(f'<option value="{key}">{escape(data["name"])}</option>' for key, data in variants.items())
    from urllib.parse import quote
    settings = Path(os.path.relpath(Path('settings.html'), page.parent)).as_posix() + '?return=' + quote(page.as_posix() + '#page-narration-title', safe='')
    audiobook = Path(os.path.relpath(Path('downloads/index.html'), page.parent)).as_posix()
    fallback = ''.join(f'<a href="{escape(v["audio"], quote=True)}" download="{escape(v["filename"], quote=True)}">Download {escape(v["name"])} MP3</a> ' for k, v in variants.items() if k != DEFAULT)
    payload = json.dumps(variants, ensure_ascii=False).replace('<', '\\u003c')
    return f'''<section class="page-narration audio-edition" aria-labelledby="page-narration-title">
<div class="narration-heading"><h2 id="page-narration-title">{'Listen to this lesson' if is_lesson else 'Listen to this page'}</h2><span class="audio-kind">Synthetic voice</span></div>
<div class="lesson-transport" hidden>
<button type="button" class="lesson-toggle" data-player-toggle aria-label="Play lesson"><svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path data-player-play d="m9 5 11 7-11 7Z" fill="currentColor"/><path data-player-pause d="M8 5h3v14H8zm6 0h3v14h-3z" fill="currentColor"/></svg></button>
<div class="lesson-timeline"><input type="range" data-player-seek aria-label="Lesson playback position" min="0" max="{entry['duration']}" value="0" step="1"><div class="lesson-time"><span data-player-elapsed>0:00</span><span aria-hidden="true"> / </span><span data-narration-duration data-seconds="{entry['duration']}">{stamp(entry['duration'])}</span></div></div>
<button type="button" class="lesson-mute" data-player-mute aria-label="Mute lesson" aria-pressed="false"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 5 6 9H3v6h3l5 4V5Z"/><path data-player-volume d="M15 8a6 6 0 0 1 0 8m3-11a10 10 0 0 1 0 14"/><path data-player-muted d="m16 9 5 6m0-6-5 6"/></svg></button>
</div>
<audio class="narration-native" id="page-narration-audio" controls preload="none" aria-label="Listen to {escape(title, quote=True)}"><source src="{url('.mp3')}" type="audio/mpeg"></audio>
<div class="narration-toolbar"><div class="audio-links"><label hidden class="narration-voice"><span class="visually-hidden">Voice</span><select data-narration-voice aria-label="Narration voice">{choices}</select></label><label hidden class="narration-speed"><span class="visually-hidden">Speed</span><select data-audio-speed="page-narration-audio" aria-label="Page narration speed"><option value="0.75">0.75×</option><option value="1" selected>1×</option><option value="1.25">1.25×</option><option value="1.5">1.5×</option><option value="2">2×</option></select></label><a class="narration-transcript" href="{url('.txt')}" aria-label="Read transcript">Transcript</a></div>
<details class="narration-sections"><summary>Choose a section</summary><ol class="audio-chapters">{jumps}</ol><div class="narration-resources"><a class="narration-download" href="{url('.mp3')}" download="{escape(variants[DEFAULT]['filename'], quote=True)}">Download MP3</a><a href="{escape(settings, quote=True)}">Voice settings</a><a class="whole-book-download" href="{escape(audiobook, quote=True)}">Download the audiobook</a></div><p class="audio-note"><span data-narration-name>Andrew</span> · Synthetic narration{' · Spoken lesson' if is_lesson else ''}</p><p class="narration-help">{practice_hint}Audio streams when played; download the MP3 for offline listening.</p></details></div>
<noscript><p>Voice preferences need JavaScript. Andrew is shown above. {fallback}Both recordings use the same lesson text.</p></noscript>
<script type="application/json" class="narration-variants">{payload}</script>
<p class="audio-status" role="status" aria-live="polite"></p>
</section>'''
