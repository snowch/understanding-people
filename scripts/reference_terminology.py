"""A glossary lookup layer for concepts already taught in reference lessons.

Keep original authored teaching/narration bindings intact. The dictionary cards
are indexed reading aids, each bound to a reviewed parent and its own lesson.
"""
import hashlib
import json
import os
import re
from functools import lru_cache
from html import escape
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BROWSE = '<nav class="glossary-entry-nav" aria-label="Continue browsing the glossary"><a class="glossary-browse" href="#main">Find another term ↑</a></nav>'


@lru_cache(maxsize=1)
def terms():
    data = json.loads((ROOT/'reference/terminology.json').read_text())
    assert data['version'] == 1
    rows = data['terms']
    assert len({t['id'] for t in rows}) == len(rows)
    core_ids = {t['id'] for t in core_terms()}
    assert not core_ids & {t['id'] for t in rows}, 'Use an alias, not a second definition of an existing term'
    for t in rows:
        assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', t['id'])
        assert re.fullmatch(r'reference/[a-z0-9-]+\.md|evidence\.md', t['source'])
        assert all(t.get(k) for k in ('title','meaning','example','forms','anchor'))
        assert hashlib.sha256((ROOT/t['source']).read_bytes()).hexdigest() == t['source_sha256'], f'Review glossary wording after changing {t["source"]}'
        if t.get('alias_of'):assert t['alias_of'] in core_ids
    return rows


def core_terms():
    result = []
    for title,id in re.findall(r'^## (.+?) \{#([^}]+)\}',(ROOT/'glossary.md').read_text(),re.M):
        result.append({'id':id,'title':title,'source':'glossary.md','forms':[title]})
    plurals = {'confirmation-bias':['confirmation biases'], 'correspondence-bias':['correspondence biases'],
               'boundary':['boundaries'], 'habit':['habits'], 'base-rate':['base rates'],
               'descriptive-norm':['descriptive norms'], 'prescriptive-norm':['prescriptive norms'],
               'personality-trait':['personality traits'], 'open-question':['open questions'],
               'leading-question':['leading questions'], 'if-then-plan':['if–then plans','if-then plan','if-then plans']}
    for term in result:term['forms'] += plurals.get(term['id'],[])
    return result


def relative(source, page):
    return Path(os.path.relpath(Path(source).with_suffix('.html'), page.parent)).as_posix()


class TermLinks(HTMLParser):
    def __init__(self, body, selected, page, mark_definitions=True):
        super().__init__(convert_charrefs=False)
        self.selected = selected
        self.page = page
        self.mark_definitions = mark_definitions
        self.out, self.stack = [], []
        self.seen = set(re.findall(r'href="[^"]*glossary\.(?:md|html)#([a-z0-9-]+)"',body))
        self.feed(body)
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.out.append(self.get_starttag_text())
        if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:
            self.stack.append((tag,attrs))

    def handle_startendtag(self, tag, attrs):
        self.out.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        self.out.append(f'</{tag}>')
        for index in range(len(self.stack)-1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, text):
        tags = {tag for tag,_ in self.stack}
        classes = {c for _,attrs in self.stack for c in attrs.get('class','').split()}
        if not tags & {'p','td','th','h2','h3'} or tags & {'a','dfn','script','style','nav','button','textarea','pre','code'} or 'definition' in classes:
            self.out.append(text)
            return
        matches = []
        for term in self.selected:
            if term['id'] in self.seen:
                continue
            pattern = r'(?<![\w-])(?:' + '|'.join(re.escape(f) for f in sorted(term['forms'],key=len,reverse=True)) + r')(?![\w-])'
            found = re.search(pattern, text, re.I)
            if found:
                matches.append((found.start(),found.end(),term))
        cursor = 0
        for start,end,term in sorted(matches,key=lambda m:(m[0],-m[1])):
            if start < cursor:
                continue
            self.out.append(text[cursor:start])
            url = relative('glossary.md',self.page)+'#'+term['id']
            owned = self.mark_definitions and term['source'].replace('.md','.html') == self.page.as_posix()
            target = f' id="definition-{term["id"]}"' if owned else ''
            title = f' title="{escape(term["meaning"],quote=True)}"' if term.get('meaning') else ''
            link = f'<a class="glossary-term"{target} href="{escape(url,quote=True)}" aria-label="{escape(term["title"],quote=True)}: definition in glossary"{title}>{text[start:end]}</a>'
            self.out.append('<dfn class="reference-term">'+link+'</dfn>' if owned and term.get('defines_here',True) else link)
            self.seen.add(term['id'])
            cursor = end
        self.out.append(text[cursor:])

    def handle_entityref(self, name): self.out.append('&'+name+';')
    def handle_charref(self, name): self.out.append('&#'+name+';')
    def handle_comment(self, text): self.out.append('<!--'+text+'-->')


def annotate(source, body, page):
    if source in ('glossary.md','reference/index.md') or not (source.startswith('reference/') or source.startswith('chapters/') or source=='evidence.md'):
        return body
    selected = [t for t in [*terms(),*core_terms()] if t.get('scope')!='owner' or t['source']==source]
    parser = TermLinks(body,selected,page)
    owned = {t['id'] for t in terms() if t['source']==source}
    assert owned <= parser.seen, f'Term not found where used: {source}: {owned-parser.seen}'
    return ''.join(parser.out)


def card(term, page):
    names = escape(' '.join([term['title'],*term['forms']]),quote=True)
    opening = f'<section class="glossary-reference-term glossary-entry" data-glossary-names="{names}" aria-labelledby="{term["id"]}">'
    back = relative(term['source'],page)+'#definition-'+term['id']
    listen = relative(term['source'],page)+'#page-narration-title'
    contrast = ('<p class="glossary-compare">Compare with a <a href="#boundary">personal boundary</a>.</p>' if term['id']=='family-boundary-ambiguity' else '')
    kind = escape(term.get('kind',''))+' · ' if term.get('kind') else ''
    if term.get('alias_of'):
        target=next(t['title'] for t in core_terms() if t['id']==term['alias_of'])
        return f'{opening}<h2 id="{term["id"]}">{escape(term["title"])}</h2><p>Another name for an <a href="#{term["alias_of"]}">{escape(target.lower())}</a>. Use that definition and example.</p><p class="glossary-entry-links"><a href="{back}">Read in context</a> · <a href="{listen}">Listen to the lesson</a></p>{BROWSE}</section>'
    related = [t for t in [*terms(),*core_terms()] if t['id']!=term['id'] and t.get('scope')!='owner']
    meaning = ''.join(TermLinks('<p>'+escape(term['meaning'])+'</p>',related,page,mark_definitions=False).out).replace('href="glossary.html#','href="#')
    return f'''{opening}
<h2 id="{term['id']}">{escape(term['title'])}</h2>
<div class="definition" role="group" aria-label="Definition: {escape(term['title'],quote=True)}"><dl>
<dt class="visually-hidden"><dfn>{escape(term['title'])}</dfn></dt><dd>{meaning}<p class="definition-example"><strong>Example:</strong> {escape(term['example'])}</p></dd></dl></div>
{contrast}<p class="glossary-entry-links">{kind}<a href="{escape(back,quote=True)}">Read in context</a> · <a href="{escape(listen,quote=True)}">Listen to the lesson</a></p>{BROWSE}
</section>'''


def glossary(body,page):
    """Interleave alphabetically; old headings, examples and anchors stay exact."""
    blocks = re.split(r'(?=<h2\b)',body)
    introduction = blocks.pop(0)
    entries = []
    for block in blocks:
        heading = re.match(r'<h2\b[^>]*>(.*?)</h2>',block,re.S)
        assert heading
        title=re.sub(r'<[^>]+>','',heading[1])
        head,end=block[:heading.end()],block[heading.end():]
        paragraphs=list(re.finditer(r'<p>.*?</p>',end,re.S))
        assert len(paragraphs)>=2
        stop=paragraphs[1].end()
        block='<section class="glossary-entry glossary-foundation-term" data-glossary-names="'+escape(title,quote=True)+'">'+head+'<div class="definition" role="group" aria-label="Definition: '+escape(title,quote=True)+'">'+end[:stop]+'</div>'+end[stop:]+BROWSE+'</section>'
        entries.append((title.casefold(),block))
    for term in terms():
        entries.append((term['title'].casefold(),card(term,page)))
    entries.sort(key=lambda item:item[0])
    return introduction + ''.join(block for _,block in entries)


def glossary_toc(core_toc):
    existing = re.findall(r'<a href="#([^"]+)">([^<]+)</a>',core_toc)
    combined = [*existing,*[(t['id'],t['title']) for t in terms()]]
    combined.sort(key=lambda item:item[1].casefold())
    return '<div class="toc"><ul>'+''.join(f'<li><a href="#{escape(id,quote=True)}">{escape(title)}</a></li>' for id,title in combined)+'</ul></div>'


def controls():
    return '''<div class="glossary-lookup-controls" hidden><label for="glossary-query">Find a term</label><div><input type="search" id="glossary-query" autocomplete="off" placeholder="Try family boundary, OCD or reinforcement…"><button type="button" id="glossary-clear" hidden>Clear</button></div><p id="glossary-count" role="status" aria-live="polite"></p><p id="glossary-empty" hidden>No matching term. Try a shorter phrase or <a href="search.html">search the book</a>.</p></div>'''
