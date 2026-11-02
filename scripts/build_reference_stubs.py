"""Render explicitly unfinished reference pages and the coverage inventory."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CAVEAT='This material provides general information and has not received specialist review. It is not a diagnostic tool or an individual assessment of safety. For advice about your circumstances, seek appropriately qualified support.'

def render():
    groups=json.loads((ROOT/'reference/catalog.json').read_text())['groups']
    catalogue={e['appNode']:e for g in groups for e in g['entries']}
    data=json.loads((ROOT/'reference/stubs.json').read_text())
    stubs={s['node']:s for s in data['entries']}
    assert len(stubs)==len(data['entries']), 'Duplicate stub node'
    assert set(stubs)=={k for k,e in catalogue.items() if e['status']=='stub'}, 'Stub status mismatch'
    inventory=['# Reference content inventory', 'The library has '+str(sum(e['status']=='developed' for e in catalogue.values()))+' developed written topics and '+str(len(stubs))+' remaining stubs. Developed means written with selected sources and editorial practice, not specialist-reviewed or established as scientifically complete. The app’s practice goals and skills are separate from this inventory.', 'The original coverage map was seeded from `'+data['provenance']['repository']+'` at `'+data['provenance']['commit']+'`. The 108 expanded entries now have original authored content in `reference/entries/` and scoped sources in `reference/research-sources.json`. The three earlier developed entries retain their existing canonical sources. This inventory maps book content to app IDs; it does not mean the app automatically downloads the new full text.', '| Topic | Status | App node | Foundation |', '| --- | --- | --- | --- |']
    for group in groups:
        for e in group['entries']:
            inventory.append('| ['+e['title']+'](../'+e['source']+') | '+e['status']+' | `'+e['appNode']+'` | '+', '.join('[Chapter '+str(int(Path(p).name[:2]))+'](../'+p+')' for p in e['foundation'])+' |')
            if e['status']!='stub':continue
            s=stubs[e['appNode']]
            parts=['# '+e['title'], '<p class="reference-status"><strong>Stub — full entry planned</strong></p>',s['summary'], 'This is a starting outline. The full explanation, evidence review and practice material are still to be written.']
            if s['specialistCaveat']:parts += [CAVEAT,'For help with your circumstances, see [When to seek other help](../support.md).']
            parts+=['## A distinction to keep in mind',s['distinction'],'## What the full entry will cover',
                '- Meaning and limits, with brief supporting examples.\n- How this may arise, with research separated from possible explanations.\n- Patterns, exceptions and alternatives that would change the explanation.\n- Your own contribution, useful responses and their trade-offs.\n- Key takeaways and one observation–action–review exercise.',
                '**Reader’s question to address:** '+s['readerQuestion'],
                'For now, the [situation worksheet](../worksheet.md) provides a place to record an occasion, your explanation and a next step. The question above is part of the outline, not an assessment.',
                '## Read the foundations now', '\n'.join('- [Chapter '+str(int(Path(p).name[:2]))+' — '+(ROOT/p).read_text().splitlines()[0][2:]+'](../'+p+')' for p in e['foundation'])]
            if s['related']:
                parts+=['## Related entries', 'These are reading connections, not evidence that one idea causes another in your situation.', '\n'.join('- ['+catalogue[r['node']]['title']+']('+Path(catalogue[r['node']]['source']).name+'): '+r['why'] for r in s['related'])]
            parts+=['## Evidence to develop']
            lead=s.get('researchLead')
            if lead:parts+=['Candidate source from the app: ['+lead['name']+']('+lead['url']+'). Its relevance, claims and limitations need checking for this full book entry. This link does not mean the stub has received an evidence review.']
            else:parts+=['Sources have not been selected for this book entry. Relevant reviews, competing evidence and limits need checking before the explanation is developed.']
            (ROOT/e['source']).write_text('\n\n'.join(parts)+'\n')
    (ROOT/'docs/reference-inventory.md').write_text('\n\n'.join(inventory[:3])+'\n\n'+'\n'.join(inventory[3:])+'\n')
if __name__=='__main__':render()
