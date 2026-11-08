#!/usr/bin/env python3
"""Record terminology coverage for every developed reference, after building."""
import hashlib
import json
from pathlib import Path
import re

from book_navigation import GROUPS, ENTRIES
from reference_terminology import terms, core_terms

ROOT=Path(__file__).resolve().parents[1]


def audit():
    vocabulary=terms();rows=[]
    for group in GROUPS:
        for entry in group['entries']:
            source=entry['source'];raw=(ROOT/source).read_bytes()
            html=(ROOT/'_site'/source.replace('.md','.html')).read_text()
            links=sorted(set(re.findall(r'href="[^"]*glossary\.html#([a-z0-9-]+)"',html)))
            owned=[t['id'] for t in vocabulary if t['source']==source]
            for id in owned:
                assert f'id="definition-{id}"' in html,(source,id)
            rows.append({'source':source,'title':entry['title'],'group':group['title'],
                         'source_sha256':hashlib.sha256(raw).hexdigest(),
                         'definition_contexts':owned,'glossary_links':links,
                         'disposition':'Indexed specialist/ambiguous vocabulary; retain the full explanation and its limits.' if owned else 'Retain the plain-English topic explanation; link relevant glossary vocabulary at first use.'})
    assert len(rows)==len(ENTRIES)==136
    data={'date':'2026-11-08','scope':'Terminology, first-use links, lookup definitions, examples and distinctions across all 136 references; not a new scientific or specialist review.',
          'references_reviewed':len(rows),'glossary_headwords':len(vocabulary)+len(core_terms()),
          'lookup_entries':len(vocabulary),'existing_course_terms':len(core_terms()),'references':rows}
    (ROOT/'docs/reference-terminology-audit.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    out=['# Reference terminology audit','8 November 2026. All 136 developed references were checked for vocabulary that needs a plain-English definition, a distinction from an everyday meaning, or a glossary pointer. This is a terminology and navigation audit, not a new review of scientific accuracy or a specialist review.',
         f'The glossary now indexes {data["glossary_headwords"]} headwords: {data["existing_course_terms"]} existing course terms and {data["lookup_entries"]} reference lookups. Implementation intention points to the existing if–then-plan definition. No extra reference pages or graph nodes are created.',
         '## Decisions','- Link technical or easily confused terms at first use; preserve existing definition links and avoid nested citation links.\n- Keep clinical vocabulary, trait dimensions, research vocabulary and informal labels distinguishable. A definition is not a diagnostic checklist or a motive detector.\n- Explain family boundary ambiguity as uncertainty about family membership or responsibilities, and contrast it with a personal limit.\n- Keep one alphabetical glossary with concise meanings, fictional examples and links back to context and the relevant narration.\n- Leave ordinary expressions alone where the entry already explains them clearly. Do not add a technical label for every everyday action.\n- Preserve all existing lesson text, anchors, note identifiers, recordings, transcripts and audiobook files. The original glossary narration remains the foundation-term tour; reference lookup rows point to their parent lessons.\n- Bind each new lookup to its reviewed parent source fingerprint. Source changes require a wording review before rebuilding.',
         '## Coverage by reference']
    for group in GROUPS:
        out.append('### '+group['title'])
        table=['| Reference | Definition contexts | Glossary links |','| --- | --- | --- |']
        for row in rows:
            if row['group']!=group['title']:continue
            table.append('| ['+row['title']+'](../'+row['source']+') | '+(', '.join(row['definition_contexts']) or 'Topic already explained in the entry')+' | '+str(len(row['glossary_links']))+' |')
        out.append('\n'.join(table))
    out += ['## Verification boundary','The build checks every registered source fingerprint, every return/listening link and exact preservation of the pre-existing spoken teaching extraction. The generated JSON inventory records all 136 reviewed routes. Search and browser checks verify retrieval, keyboard/mobile navigation, no-JavaScript access, filtering and audio preservation; they cannot establish scientific accuracy, diagnostic validity or learning.']
    (ROOT/'docs/reference-terminology-audit.md').write_text('\n\n'.join(out)+'\n')
    print(f'Terminology inventory: {len(rows)} references, {data["glossary_headwords"]} glossary headwords; all definition return targets present.')


if __name__=='__main__':audit()
