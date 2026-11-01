"""Render concept-first reference pages from content shared with the offline app."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def content():
    return json.loads((ROOT / 'reference/biases.json').read_text())

def render():
    data = content()
    for d in data['entries']:
        chunks = ['# '+d['title'], d['summary'], '> **Remember:** '+d['cue'], 'Examples are fictional. The comparisons and practice steps are editorial suggestions, not a test that identifies bias in a person.']
        for s in d['sections']:
            chunks += ['## '+s['title']+' {#'+s['id']+'}', *s['paragraphs']]
            if s.get('comparisons'):
                chunks += ['| A thought to examine | A more useful check |\n| --- | --- |\n'+'\n'.join('| '+' | '.join(row)+' |' for row in s['comparisons'])]
            if s['sources']:
                chunks += ['**Research behind this explanation:** '+ '; '.join('['+data['sources'][key]['title'].split('. ')[0]+']('+data['sources'][key]['url']+')' for key in s['sources'])]
        chunks += ['[Read the other bias]('+d['related']+'.md) · [Return to Chapter 1](../chapters/01-before-you-explain.md).']
        chunks += ['<section class="reader-action" markdown="1" aria-labelledby="practice">', '## Put it into practice: '+d['practice']['title'].lower()+' {#practice}', '\n'.join(str(i)+'. '+step for i,step in enumerate(d['practice']['steps'],1)), '<!-- practice-notes: '+d['slug']+'-practice | '+d['practice']['title']+' -->', '</section>']
        chunks += ['## Continue in the app', '[Get the private app download](https://github.com/snowch/understanding-people-app/releases/tag/v0.12.0) (repository access required). Open version 0.12.0 or later, choose **Start → Explore the whole map**, search for **'+d['title']+'**, then select **Read the full entry → Work through my example**. You can also reach the entry through the map’s text list.', 'Record an observation, your answer and one check to try. Save it in **My situations**, then choose **What happened when I tried?** to record the outcome and how your explanation changed.', 'This web page cannot open a downloaded HTML file directly. Without app access, use the notes above. Book notes and app notes are separate; they do not sync automatically.']
        keys = list(dict.fromkeys(k for s in d['sections'] for k in s['sources']))
        chunks += ['## Sources and limits', *['['+data['sources'][k]['title']+']('+data['sources'][k]['url']+') '+data['sources'][k]['scope'] for k in keys]]
        (ROOT / ('reference/'+d['slug']+'.md')).write_text('\n\n'.join(chunks)+'\n')
if __name__ == '__main__':
    render()
