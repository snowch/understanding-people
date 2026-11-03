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
    return not source.startswith("audio/")


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


def media_path(source, suffix):
    return Path("assets/media/narration") / Path(source).with_suffix(suffix)


def transcript(sections):
    return "\n\n".join("\n\n".join(s["paragraphs"]) for s in sections) + "\n"


def load_manifest():
    if not MANIFEST.exists():
        return None
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["voice"] == VOICE and manifest["rate"] == RATE and manifest["version"] == VERSION
    return manifest


def stamp(seconds):
    seconds = round(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02}:{seconds:02}" if hours else f"{minutes}:{seconds:02}"


def render(source, title, body, page, manifest):
    if not eligible(source) or manifest is None:
        return ""
    sections = speech_sections(title, body)
    entry = manifest["pages"].get(source)
    assert entry and entry["text_sha256"] == fingerprint(sections), f"Narration is missing or stale for {source}. Run python scripts/synthesise_pages.py."
    for suffix, key in ((".mp3", "audio_sha256"), (".txt", "transcript_sha256")):
        path = ROOT / media_path(source, suffix)
        assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == entry[key], f"Narration file checksum mismatch: {path}"
    def url(suffix):
        key = 'audio_sha256' if suffix == '.mp3' else 'transcript_sha256'
        return escape(Path(os.path.relpath(media_path(source, suffix), page.parent)).as_posix() + '?v=' + entry[key][:12], quote=True)
    practice_hint = ('Includes optional practice and example answers: pause when prompted. ' if 'class="answer-check"' in body
                     else 'Pause whenever you want to reflect or write. ' if 'class="reader-action"' in body else '')
    jumps = "".join(f'<li><button type="button" hidden data-audio-seek="page-narration-audio" data-start="{s["start"]}">{stamp(s["start"])} · {escape(s["title"])}</button><a href="#{escape(s["anchor"], quote=True)}">Read {escape(s["title"])}</a></li>' for s in entry["sections"])
    return f'''<section class="page-narration audio-edition" aria-labelledby="page-narration-title">
<div class="narration-heading"><h2 id="page-narration-title">Listen to this page</h2><span>{stamp(entry['duration'])}</span></div>
<p class="audio-note">Andrew · Synthetic narration</p>
<audio id="page-narration-audio" controls preload="none" aria-label="Listen to {escape(title, quote=True)}"><source src="{url('.mp3')}" type="audio/mpeg"></audio>
<div class="audio-links"><a href="{url('.mp3')}" download>Download MP3</a><a href="{url('.txt')}">Read transcript</a><label hidden class="narration-speed">Speed <select data-audio-speed="page-narration-audio" aria-label="Page narration speed"><option value="0.75">0.75×</option><option value="1" selected>1×</option><option value="1.25">1.25×</option><option value="1.5">1.5×</option><option value="2">2×</option></select></label></div>
<details class="narration-sections"><summary>Choose a section</summary><ol class="audio-chapters">{jumps}</ol></details>
<p class="narration-help">{practice_hint}Audio streams when played; download the MP3 for offline listening.</p>
<p class="audio-status" role="status" aria-live="polite"></p>
</section>'''
