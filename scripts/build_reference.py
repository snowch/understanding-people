"""Render the book's canonical pilot entry. App snapshots use the same JSON."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def render():
 d=json.loads((ROOT/'reference/declining-help.json').read_text())
 chunks=['# '+d['title'],d['summary'],'> **Remember:** '+d['cue'],'This reference entry connects the book with the app. Read it here, then use **Declining help → Work through my example** in your downloaded app. You can also use the notes at the end of this page.']
 for s in d['sections']:
  chunks+=['## '+s['title']+' {#'+s['id']+'}',*s['paragraphs']]
  if s.get('comparisons'):chunks+=['| Possibility | What could help you distinguish it? |\n| --- | --- |\n'+'\n'.join('| '+' | '.join(row)+' |' for row in s['comparisons'])]
 chunks+=['For definitions, see [autonomy](../glossary.md#autonomy) and [competence](../glossary.md#competence) in the glossary.']
 chunks+=['## Connect this with the foundations','\n'.join('- ['+f['title']+'](../'+f['chapter'].replace('.html','.md')+'): '+f['why'] for f in d['foundations'])]
 chunks+=['## Put it into practice','In the downloaded app, search for **Declining help**, open **Read the full entry**, then choose **Work through my example**. Your saved situation leads from the offer and response to a next step and a review. It includes whether your understanding and collaboration improved.','The app is currently a private preview. If you do not have access, use these notes instead. Book notes and app notes are stored separately; they do not sync automatically.','<!-- practice-notes: declining-help-pilot | Compare an offer, try a response, review -->']
 chunks+=['## Research and limits',*['['+s['title']+']('+s['url']+') '+s['scope'] for s in d['sources']]]
 (ROOT/'reference/declining-help.md').write_text('\n\n'.join(chunks)+'\n')
if __name__=='__main__':render()
