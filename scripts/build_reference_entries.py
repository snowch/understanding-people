"""Render original written reference entries from their canonical authored content."""
import json
from functools import lru_cache
from pathlib import Path
from build_reference_stubs import CAVEAT
ROOT=Path(__file__).resolve().parents[1]

@lru_cache(maxsize=1)
def content():
    return [e for path in sorted((ROOT/'reference/entries').glob('*.json')) for e in json.loads(path.read_text())['entries']]

def render():
    catalogue={e['appNode']:e for g in json.loads((ROOT/'reference/catalog.json').read_text())['groups'] for e in g['entries']}
    bank=json.loads((ROOT/'reference/research-sources.json').read_text());sources=bank['sources']
    entries=content();assert len({e['id'] for e in entries})==len(entries), 'Duplicate reference content'
    used=set()
    for d in entries:
        e=catalogue[d['id']]
        assert e['status']=='developed', 'Authored entry must have developed status'
        assert len(d['practice'])==3 and len(d['takeaways'])==3
        assert all(k in sources for k in d['sources']) and d['sources']
        used.update(d['sources'])
        chunks=['# '+e['title'], d['meaning'], '> **Remember:** '+d['cue'], 'The brief example is fictional. Possible explanations and practical suggestions are editorial applications; they are not a test that identifies a motive, trait or diagnosis.']
        if d.get('specialistCaveat'):chunks += [CAVEAT,'See [When to seek other help](../support.md) for support routes and their limits.']
        chunks += ['<span id="what-the-full-entry-will-cover"></span>', '## How it may arise',d['arise'], '## What the evidence supports']
        for key in d['sources']:
            ref=sources[key];chunks += [ref['explanation']+' '+ref['limit']+' ['+ref['title']+']('+ref['url']+')']
        chunks += ['## What else could explain it? {#a-distinction-to-keep-in-mind}',d['alternatives'],'These alternatives are starting points, not an exhaustive list.','## What to notice and check',d['notice'],'## How to respond',d['respond'],'**A brief fictional example:** '+d['example']]
        chunks += ['## Read the foundations {#read-the-foundations-now}', '\n'.join('- ['+(ROOT/p).read_text().splitlines()[0][2:]+'](../'+p+')' for p in e['foundation'])]
        if d.get('related'):
            chunks += ['## Related entries','These are editorial reading connections, not evidence of a cause or diagnosis in your situation.', '\n'.join('- ['+catalogue[r['node']]['title']+']('+Path(catalogue[r['node']]['source']).name+'): '+r['why'] for r in d['related'])]
        chunks += ['<span id="evidence-to-develop"></span>', '[Source access and research scope](sources.md). This is a selected reference entry, not a systematic review or an individual assessment.', '<section class="key-takeaways" markdown="1" aria-labelledby="key-takeaways">','## Key takeaways {#key-takeaways}', '\n'.join('- '+p for p in d['takeaways']),'</section>', '<section class="reader-action compact-practice" markdown="1" aria-labelledby="practice">','## Put it into practice {#practice}','\n'.join(str(i)+'. '+p for i,p in enumerate(d['practice'],1)),'<!-- practice-notes: reference-'+d['id']+' | '+e['title']+' -->','</section>']
        (ROOT/e['source']).write_text('\n\n'.join(chunks)+'\n')
    chunks=['# Research sources for the reference library',bank['method'],'Read sources beside the claims in each entry. Research findings, public guidance and editorial applications have different roles. Checking a link or the structure of a page does not establish scientific accuracy.','No third-party figures, questionnaire items, diagnostic checklists or recordings are reproduced. The source titles identify the cited works; explanations and fictional examples are original writing.']
    for key in sorted(used):
        s=sources[key];chunks+=['## '+s['title']+' {#'+key+'}','['+s['title']+']('+s['url']+')',s['explanation'],s['limit'],'**Access scope:** '+s['access']+' Checked '+s['checked']+'. [Source record]('+s['record']+').']
    (ROOT/'reference/sources.md').write_text('\n\n'.join(chunks)+'\n')
if __name__=='__main__':render()
