"""Render the book's canonical pilot entry. App snapshots use the same JSON."""
import json
from html import escape
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def render():
 d=json.loads((ROOT/'reference/declining-help.json').read_text())
 sources={s['id']:s for s in d['sources']}
 def body(s):
  parts=list(s['paragraphs'])
  if s.get('example'):parts.append('**Example:** '+s['example'])
  for block in s.get('blocks',[]):
   parts+=['### '+block['title'],*block['paragraphs']]
   if block.get('example'):parts.append('**Example:** '+block['example'])
  if s.get('bullets'):parts.append('\n'.join('- '+line for line in s['bullets']))
  for key in s.get('sources',[]):
   ref=sources[key];parts.append('['+ref['title']+']('+ref['url']+')')
  return parts
 chunks=['# '+d['title'],d['summary'],'> **Remember:** '+d['cue']]
 for s in d['sections']:
  if s.get('practice'):continue
  if s.get('optional'):
   chunks += [f'<details class="evidence-detail reference-case" markdown="1" id="{escape(s["id"],quote=True)}">', '<summary>Optional worked example: '+escape(s['title'])+'</summary>',*body(s),'</details>']
  elif s.get('bullets'):
   chunks += ['<section class="key-takeaways" markdown="1" aria-labelledby="key-takeaways">','## '+s['title']+' {#'+s['id']+'}',*body(s),'</section>']
  else:chunks+=['## '+s['title']+' {#'+s['id']+'}',*body(s)]
 chunks+=['For definitions, see [autonomy](../glossary.md#autonomy) and [competence](../glossary.md#competence) in the glossary.']
 chunks+=['## Connect this with the foundations','\n'.join('- ['+f['title']+'](../'+f['chapter'].replace('.html','.md')+'): '+f['why'] for f in d['foundations'])]
 chunks+=['## Research and limits',*['['+s['title']+']('+s['url']+') '+s['scope'] for s in d['sources']]]
 practice=next(s for s in d['sections'] if s.get('practice'))
 chunks+=['<section class="reader-action compact-practice" markdown="1" aria-labelledby="try-and-review">','<span id="put-it-into-practice"></span>','## '+practice['title']+' {#'+practice['id']+'}',*body(practice),
 'In your downloaded app, search for **Declining help**, open **Read the full entry**, then choose **Work through my example**. The saved situation keeps your observation, next step and review together.',
 'The app is a private preview. You can use the notes below instead. Book and app notes are stored separately and do not sync automatically.',
 '<!-- practice-notes: declining-help-pilot | Compare an offer, try a response, review -->','</section>']
 (ROOT/'reference/declining-help.md').write_text('\n\n'.join(chunks)+'\n')
if __name__=='__main__':render()
