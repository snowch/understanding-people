#!/usr/bin/env python3
"""Build the static book and validate local links and fragment targets."""

from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit
import hashlib
import os
import re
import shutil

import markdown

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_site"
PAGES = [
    ("book.md", "Introduction"),
    ("contents.md", "Contents & reading routes"),
    ("evidence.md", "How we use evidence"),
    ("chapters/01-before-you-explain.md", "Before you explain someone"),
    ("chapters/09-truth-lies-uncertainty.md", "Truth, lies & uncertainty"),
    ("worksheet.md", "Situation worksheet"),
    ("references.md", "Sources & further reading"),
]


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
    css_hash = hashlib.sha256((ROOT / "assets/book.css").read_bytes()).hexdigest()[:12]

    for index, (name, label) in enumerate(PAGES):
        title, text = sources[name]
        page = destination(name)
        converter = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists"],
                                      extension_configs={"toc": {"toc_depth": "2-3"}})
        body = converter.convert(text)
        body = re.sub(r'\b(href|src)="([^"]*)"', rewrite_link, body)
        body = body.replace("<table>", '<div class="table-scroll" role="region" aria-label="Comparison table" tabindex="0"><table>')
        body = body.replace("</table>", "</table></div>")
        nav = []
        for item, caption in PAGES:
            current = ' aria-current="page"' if item == name else ""
            nav.append(f'<li><a href="{relative(destination(item), page)}"{current}>{escape(caption)}</a></li>')
        nav_html = "".join(nav)
        pagination = []
        for offset, direction, relation in [(-1, "Previous", "prev"), (1, "Next", "next")]:
            if 0 <= index + offset < len(PAGES):
                item, caption = PAGES[index + offset]
                pagination.append(f'<a rel="{relation}" href="{relative(destination(item), page)}"><small>{direction}</small>{escape(caption)}</a>')
        contents = f'<details class="on-page"><summary>On this page</summary>{converter.toc}</details>' if converter.toc_tokens else ""
        home = relative(Path("index.html"), page)
        eyebrow = "A SCIENCE-INFORMED GUIDE" if name == "book.md" else "UNDERSTANDING PEOPLE · INITIAL DRAFT"
        description = f"{title}. A science-informed guide to what drives people and how to respond."
        html = f'''<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{escape(description, quote=True)}">
<meta name="color-scheme" content="light dark">
<title>{escape(title)}{'' if name == 'book.md' else ' · Understanding people'}</title>
<link rel="icon" href="{relative(Path('assets/favicon.svg'), page)}" type="image/svg+xml">
<link rel="stylesheet" href="{relative(Path('assets/book.css'), page)}?v={css_hash}">
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><a class="brand" href="{home}"><span class="brand-mark" aria-hidden="true">u.</span>Understanding people</a><a href="{relative(Path('contents.html'), page)}">Explore the book <span aria-hidden="true">↗</span></a></header>
<details class="mobile-nav"><summary>Book navigation</summary><nav aria-label="Book on mobile"><ul>{nav_html}</ul></nav></details>
<div class="layout">
<aside><p class="nav-label">THE BOOK</p><nav aria-label="Book"><ul>{nav_html}</ul></nav><p class="sidebar-note">Start with curiosity.<br>Check your interpretation.<br>Choose your response.</p></aside>
<main id="main" tabindex="-1"><article>
<header class="chapter-header"><p class="eyebrow">{eyebrow}</p><h1>{escape(title)}</h1></header>
{contents}<div class="prose">{body}</div>
</article>
<nav class="pagination" aria-label="Continue reading">{''.join(pagination)}</nav>
<footer><span>Understanding people · Draft edition</span><a href="https://github.com/snowch/understanding-people/blob/main/{name}">Page source</a></footer>
</main></div>
</body></html>
'''
        output = OUT / page
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(html, encoding="utf-8")
    (OUT / ".nojekyll").touch()
    print(f"Built {check_links()} pages; all local links and anchors resolve.")


if __name__ == "__main__":
    build()
