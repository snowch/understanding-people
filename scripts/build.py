#!/usr/bin/env python3
# Copyright © 2026 Christopher Snow
"""Build the static book and validate local links and fragment targets."""

from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit
import hashlib
import json
import os
import re
import shutil

import markdown

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_site"
PAGES = [
    ("book.md", "Introduction"),
    ("contents.md", "Contents & reading routes"),
    ("how-to-use.md", "How to use this book"),
    ("evidence.md", "How we use evidence"),
    ("chapters/01-before-you-explain.md", "Why we misinterpret people"),
    ("chapters/02-what-counts-as-knowing.md", "What counts as knowing?"),
    ("chapters/03-needs-motives-goals.md", "Needs, motives and competing goals"),
    ("chapters/04-beliefs-identity-history.md", "Beliefs, identity and personal history"),
    ("chapters/05-emotion-stress-coping.md", "Emotion, stress and coping"),
    ("chapters/06-personality-habits-situations.md", "Personality, habits and situations"),
    ("chapters/07-culture-groups-power.md", "Culture, groups and power"),
    ("chapters/08-questions-listening-disagreement.md", "Questions, listening and disagreement"),
    ("chapters/09-truth-lies-uncertainty.md", "Truth, lies and uncertainty"),
    ("chapters/10-motivation-influence-cooperation.md", "Motivation, influence and cooperation"),
    ("chapters/11-conflict-manipulation-boundaries.md", "Conflict, manipulation and boundaries"),
    ("chapters/12-putting-understanding-to-work.md", "Putting understanding to work"),
    ("worksheet.md", "Situation worksheet"),
    ("support.md", "When to seek other help"),
    ("glossary.md", "Glossary"),
    ("references.md", "Sources & further reading"),
    ("about.md", "About the book & author"),
]
CHAPTERS = [
    ("Why we misinterpret people", "chapters/01-before-you-explain.md"),
    ("What counts as knowing?", "chapters/02-what-counts-as-knowing.md"),
    ("Needs, motives and competing goals", "chapters/03-needs-motives-goals.md"),
    ("Beliefs, identity and personal history", "chapters/04-beliefs-identity-history.md"),
    ("Emotion, stress and coping", "chapters/05-emotion-stress-coping.md"),
    ("Personality, habits and situations", "chapters/06-personality-habits-situations.md"),
    ("Culture, groups and power", "chapters/07-culture-groups-power.md"),
    ("Questions, listening and disagreement", "chapters/08-questions-listening-disagreement.md"),
    ("Truth, lies and uncertainty", "chapters/09-truth-lies-uncertainty.md"),
    ("Motivation, influence and cooperation", "chapters/10-motivation-influence-cooperation.md"),
    ("Conflict, manipulation and boundaries", "chapters/11-conflict-manipulation-boundaries.md"),
    ("Putting understanding to work", "chapters/12-putting-understanding-to-work.md"),
]


def book_navigation(source, page):
    def entry(item, caption, number="", fragment="", planned=False):
        current = ' aria-current="page"' if item == source and not fragment else ""
        href = relative(destination(item), page) + fragment
        status = '<small class="nav-status">Planned</small>' if planned else ""
        return (f'<li><a href="{escape(href)}"{current}>'
                f'<span class="nav-number">{number}</span>'
                f'<span class="nav-title">{escape(caption)}{status}</span></a></li>')

    chapters = [entry("book.md", "Introduction", "—")]
    for number, (caption, item) in enumerate(CHAPTERS, 1):
        chapters.append(entry(item or "contents.md", caption, f"{number:02}",
                              "" if item else f"#chapter-{number:02}", planned=item is None))
    resources = [entry(item, caption) for item, caption in PAGES
                 if item != "book.md" and not item.startswith("chapters/")]
    return (f'<ol class="chapter-list">{"".join(chapters)}</ol>'
            '<p class="nav-label resources-label">READING TOOLS</p>'
            f'<ul class="resource-list">{"".join(resources)}</ul>')


def destination(source):
    return Path("index.html") if str(source) == "book.md" else Path(source).with_suffix(".html")


def relative(target, page):
    return Path(os.path.relpath(target, page.parent)).as_posix()


def rewrite_link(match):
    url = urlsplit(unescape(match.group(2)))
    if not url.scheme and not url.netloc and url.path.endswith(".md"):
        path = Path(url.path)
        path = path.with_name("index.html") if path.name == "book.md" else path.with_suffix(".html")
        url = url._replace(path=path.as_posix())
    return f'{match.group(1)}="{escape(urlunsplit(url), quote=True)}"'


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.links = []
        self.feed(text)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if attrs.get("id"):
            if attrs["id"] in self.ids:
                raise ValueError(f"Duplicate ID: {attrs['id']}")
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if attrs.get(key):
                self.links.append(attrs[key])


def check_links():
    documents = {p.resolve(): Document(p.read_text(encoding="utf-8")) for p in OUT.rglob("*.html")}
    errors = []
    for page, document in documents.items():
        for link in document.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            target = (page.parent / unquote(url.path)).resolve() if url.path else page
            if target.is_dir():
                target /= "index.html"
            if not target.is_relative_to(OUT) or not target.is_file():
                errors.append(f"{page.relative_to(OUT)}: missing target {link}")
            elif url.fragment and target in documents and unquote(url.fragment) not in documents[target].ids:
                errors.append(f"{page.relative_to(OUT)}: missing anchor {link}")
    if errors:
        raise ValueError("\n".join(errors))
    return len(documents)


def practice_notes(match):
    """Expand a stable exercise marker into accessible, printable note fields."""
    note_id, title = match.groups()
    fields = [
        ("event", "What happened?"),
        ("thought", "What did I think it meant?"),
        ("action", "What did I notice, ask or try?"),
        ("review", "What did I learn, and what would I do differently next time?"),
    ]
    if note_id == "chapter-01-three-questions":
        fields = [
            ("event", "What did they say or do?"),
            ("thought", "Why do I think they did it?"),
            ("action", "How could I check?"),
            ("review", "After checking: what did I learn, and what will I do next?"),
        ]
    inputs = []
    for key, label in fields:
        field_id = f"{note_id}-{key}"
        inputs.append(f'<div class="notes-field"><label for="{field_id}">{label}</label>'
                      f'<textarea id="{field_id}" name="{key}" rows="3" maxlength="12000" '
                      'autocomplete="off" spellcheck="false"></textarea>'
                      '<div class="notes-print-value" aria-hidden="true"></div></div>')
    return f'''<details class="practice-notes" data-notes-id="{note_id}" data-notes-title="{escape(title, quote=True)}">
<summary>My practice notes: {escape(title)}</summary>
<p class="notes-help">Notes save automatically in this browser on this device; they are not sent to the book’s author or synced to other devices. Anyone using this browser may be able to read them. Avoid names and sensitive details. Download a copy to keep: clearing browser data can remove saved notes.</p>
<noscript><p>Automatic saving and downloading need JavaScript. You can copy your notes elsewhere or print this page for handwriting. Typing here without JavaScript will not save your notes.</p></noscript>
<div class="notes-field"><label for="{note_id}-date">Date to return to these notes (optional)</label><input id="{note_id}-date" name="date" type="date"><div class="notes-print-value" aria-hidden="true"></div></div>
{''.join(inputs)}
<div class="notes-controls" hidden><button type="button" data-notes-download>Download these notes</button><button type="button" data-notes-delete>Delete these notes</button></div>
<p class="notes-status" role="status" aria-live="polite"></p>
</details>'''


def build():
    sources = {}
    for name, label in PAGES:
        text = (ROOT / name).read_text(encoding="utf-8")
        heading = re.match(r"# (.+)\n", text)
        if not heading:
            raise ValueError(f"Missing title: {name}")
        sources[name] = (heading[1], text[heading.end():])
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "assets", OUT / "assets")
    shutil.copyfile(ROOT / "manifest.webmanifest", OUT / "manifest.webmanifest")
    css_hash = hashlib.sha256((ROOT / "assets/book.css").read_bytes()).hexdigest()[:12]

    for index, (name, label) in enumerate(PAGES):
        title, text = sources[name]
        page = destination(name)
        converter = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists", "md_in_html", "attr_list"],
                                      extension_configs={"toc": {"toc_depth": "2-3"}})
        body = converter.convert(text)
        body = re.sub(r'<!-- practice-notes: ([a-z0-9-]+) \| ([^\n]+?) -->', practice_notes, body)
        body = re.sub(r'\b(href|src)="([^"]*)"', rewrite_link, body)
        body = body.replace("<table>", '<div class="table-scroll" role="region" aria-label="Comparison table" tabindex="0"><table>')
        body = body.replace("</table>", "</table></div>")
        nav_html = book_navigation(name, page)
        pagination = []
        for offset, direction, relation in [(-1, "Previous", "prev"), (1, "Next", "next")]:
            if 0 <= index + offset < len(PAGES):
                item, caption = PAGES[index + offset]
                pagination.append(f'<a rel="{relation}" href="{relative(destination(item), page)}"><small>{direction}</small>{escape(caption)}</a>')
        contents = f'<details class="on-page"><summary>On this page</summary>{converter.toc}</details>' if converter.toc_tokens else ""
        home = relative(Path("index.html"), page)
        eyebrow = "A SCIENCE-INFORMED GUIDE" if name == "book.md" else "UNDERSTANDING PEOPLE · DRAFT EDITION"
        description = f"{title}. A science-informed guide to what drives people and how to respond."
        notes_script = (f'<script defer src="{relative(Path("assets/practice.js"), page)}"></script>'
                        if 'class="practice-notes"' in body else '')
        html = f'''<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{escape(description, quote=True)}">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#27664f">
<title>{escape(title)}{'' if name == 'book.md' else ' · Understanding people'}</title>
<link rel="icon" href="{relative(Path('assets/favicon.svg'), page)}" type="image/svg+xml">
<link rel="apple-touch-icon" href="{relative(Path('assets/apple-touch-icon.png'), page)}">
<link rel="manifest" href="{relative(Path('manifest.webmanifest'), page)}">
<link rel="stylesheet" href="{relative(Path('assets/book.css'), page)}?v={css_hash}">
<script defer src="{relative(Path('assets/install.js'), page)}"></script>
{notes_script}
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><a class="brand" href="{home}"><span class="brand-mark" aria-hidden="true">u.</span>Understanding people</a><div class="header-actions"><a class="explore-book" href="{relative(Path('contents.html'), page)}">Explore the book <span aria-hidden="true">↗</span></a><button class="install-button" type="button" aria-label="Install Understanding people" title="Install Understanding people" hidden><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v12m-4-4 4 4 4-4M4 15v5h16v-5"/></svg></button></div></header>
<dialog id="install-help" aria-labelledby="install-title">
<h2 id="install-title">Install Understanding people</h2>
<p>Add the book to your home screen or desktop for a separate reading window.</p>
<ul><li><strong>iPhone or iPad:</strong> open this page in Safari, tap Share, then Add to Home Screen. If offered, leave Open as Web App switched on.</li><li><strong>Chrome or Edge:</strong> open the browser menu and look for Install app, Install page as app, or Add to Home screen.</li><li><strong>Safari on Mac:</strong> choose File → Add to Dock, if available.</li></ul>
<p>If your browser has no install option, you can bookmark the book and read it here.</p>
<form method="dialog"><button type="submit">Close</button></form>
</dialog>
<details class="mobile-nav"><summary>Contents</summary><nav aria-label="Book on mobile">{nav_html}</nav></details>
<div class="layout">
<aside class="book-sidebar"><p class="nav-label">THE BOOK</p><p class="sidebar-title">Understanding<br>people</p><nav aria-label="Book chapters">{nav_html}</nav></aside>
<main id="main" tabindex="-1"><article>
<header class="chapter-header"><p class="eyebrow">{eyebrow}</p><h1>{escape(title)}</h1></header>
{contents}<div class="prose">{body}</div>
</article>
<nav class="pagination" aria-label="Continue reading">{''.join(pagination)}</nav>
<footer><div><span>Understanding people · Draft edition</span><p class="copyright">© 2026 Christopher Snow</p></div><a href="https://github.com/snowch/understanding-people/blob/main/{name}">Page source</a></footer>
</main></div>
<script>
const sidebar = document.querySelector('.book-sidebar');
const current = sidebar.querySelector('[aria-current="page"]');
if (current && sidebar.clientHeight) {{
    const bottom = current.offsetTop + current.offsetHeight;
    if (bottom > sidebar.clientHeight) sidebar.scrollTop = bottom - sidebar.clientHeight + 24;
}}
</script>
</body></html>
'''
        output = OUT / page
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(html, encoding="utf-8")
    (OUT / ".nojekyll").touch()
    files = sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob("*") if p.is_file())
    digest = hashlib.sha256()
    for name in files:
        digest.update(name.encode())
        digest.update((OUT / name).read_bytes())
    worker = (ROOT / "scripts/service-worker.js").read_text()
    digest.update(worker.encode())
    worker = worker.replace("__VERSION__", digest.hexdigest()[:16]).replace("__FILES__", json.dumps(["./", *files]))
    (OUT / "sw.js").write_text(worker, encoding="utf-8")
    print(f"Built {check_links()} pages; all local links and anchors resolve.")


if __name__ == "__main__":
    build()
