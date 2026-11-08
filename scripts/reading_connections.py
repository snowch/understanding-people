"""Supplementary reading routes; never change the text of an approved spoken lesson."""
from html import escape
from pathlib import Path
import json
import os

ROOT=Path(__file__).resolve().parents[1]

def render(source, page):
    entries=json.loads((ROOT/'reference/entries/audit-expansion.json').read_text())['entries']
    catalogue={e['appNode']:e for g in json.loads((ROOT/'reference/catalog.json').read_text())['groups'] for e in g['entries']}
    owner=next((e['appNode'] for e in catalogue.values() if e['source']==source),None)
    links=[]
    for entry in entries:
        item=catalogue[entry['id']]
        if source in item['foundation'] or any(r['node']==owner for r in entry['related']):
            if item['source']==source:continue
            url=Path(os.path.relpath(Path(item['source']).with_suffix('.html'),page.parent)).as_posix()
            links.append('<li><a href="'+escape(url,quote=True)+'">'+escape(item['title'])+'</a> — '+escape(item['summary'])+'</li>')
    if not links:return ''
    return '<section class="reference-formats reading-connections" aria-label="Further reading"><details><summary>Go deeper in the reference library</summary><ul>'+''.join(links)+'</ul></details></section>'
