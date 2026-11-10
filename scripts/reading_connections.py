"""Supplementary reading routes; never change the text of an approved spoken lesson."""
from html import escape
from pathlib import Path
import json
import os

ROOT=Path(__file__).resolve().parents[1]

def render(source, page):
    if source in ('book.md','contents.md','about.md','references.md'):
        url=Path(os.path.relpath(Path('reading/books.html'),page.parent)).as_posix()
        return '<nav class="reference-formats reading-connections" aria-label="Further reading"><p><a href="'+escape(url,quote=True)+'">Books for deeper reading</a> — Choose a book for your question and connect it to the course.</p></nav>'
    entries=json.loads((ROOT/'reference/entries/audit-expansion.json').read_text())['entries']
    catalogue={e['appNode']:e for g in json.loads((ROOT/'reference/catalog.json').read_text())['groups'] for e in g['entries']}
    owner=next((e['appNode'] for e in catalogue.values() if e['source']==source),None)
    links=[];seen=set()
    for entry in entries:
        item=catalogue[entry['id']]
        if source in item['foundation'] or any(r['node']==owner for r in entry['related']):
            if item['source']==source:continue
            url=Path(os.path.relpath(Path(item['source']).with_suffix('.html'),page.parent)).as_posix()
            seen.add(url)
            links.append('<li><a href="'+escape(url,quote=True)+'">'+escape(item['title'])+'</a> — '+escape(item['summary'])+'</li>')
    additions={
        'chapters/06-personality-habits-situations.md':[('reinforcement','Compare a tendency, a learned expectation and the consequences sustaining an action.')],
        'reference/learned.md':[('reinforcement','Distinguish how a pattern began from what keeps it going now.'),('people-pleasing','Separate a feared reaction from what actually happened after agreement or refusal.')],
        'reference/interaction-cycles.md':[('people-pleasing','Follow the agreement-and-relief cycle without assuming equal responsibility or a conscious plan.')],
        'reference/avoidconflict.md':[('people-pleasing','Examine agreement that brings immediate relief while leaving later costs.')],
        'reference/family-membership.md':[('power','Separate a recognised family role from control over decisions, resources and the cost of disagreeing.'),('unequal-treatment','Compare whose conduct gets exceptions and whose duties or choices are restricted.'),('people-pleasing','Consider whether agreement reflects preference, loyalty, pressure or a realistic cost of refusing.')],
        'reference/unequal-treatment.md':[('family-membership','Distinguish belonging, responsibilities and who is assumed to have a right to decide.'),('power','Ask who sets the rules and whether an affected person can challenge them.'),('people-pleasing','Examine accommodation without making a person responsible for another person’s unfair treatment.')],
        'reference/power.md':[('family-membership','Examine family authority without assuming that every leading relative controls others.'),('unequal-treatment','Compare rules, exceptions and how burdens are allocated.'),('people-pleasing','A repeated yes can reflect constrained choices rather than approval.')],
        'reference/familynorms.md':[('family-membership','Separate an inherited expectation from an agreed decision-making role.'),('unequal-treatment','Check whose exceptions are accepted and whose responsibilities are taken for granted.'),('people-pleasing','Consider the immediate relief and later costs of accommodating an expectation.')]
    }
    for node,description in additions.get(source,[]):
        item=catalogue[node]
        url=Path(os.path.relpath(Path(item['source']).with_suffix('.html'),page.parent)).as_posix()
        if url in seen:continue
        seen.add(url)
        links.append('<li><a href="'+escape(url,quote=True)+'">'+escape(item['title'])+'</a> — '+escape(description)+'</li>')
    if not links:return ''
    return '<section class="reference-formats reading-connections" aria-label="Further reading"><details><summary>Go deeper in the reference library</summary><ul>'+''.join(links)+'</ul></details></section>'
