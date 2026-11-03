"""Check the revised concept-first chapters without screenshots or recordings."""
import json,sys
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];base=sys.argv[1].rstrip('/')+'/'
archive=json.loads((ROOT/'docs/chapter-revision-anchors.json').read_text())
with sync_playwright() as pw:
 b=pw.chromium.launch();page=b.new_page(service_workers='block');errors=[];page.on('pageerror',lambda e:errors.append(str(e)));definitions=[]
 for n,e in archive.items():
  page.goto(urljoin(base,e['path'].replace('.md','.html')))
  expect(page.locator('main video,main audio')).to_have_count(0)
  expect(page.locator('.remember-cue')).to_have_count(1)
  expect(page.locator('main .compact-practice')).to_have_count(1)
  expect(page.locator('main .more-practice[open]')).to_have_count(0)
  expect(page.locator('.practice-check .answer-check')).to_have_count(2)
  assert page.locator('main a[href*="reference/"]').count()>=3
  for anchor in e['ids']:expect(page.locator('[id="'+anchor+'"]').first).to_have_count(1);assert page.locator('[id="'+anchor+'"]').count()==1,(n,anchor)
  for marker in e['notes']:
   note=marker.split(': ',1)[1].split(' | ',1)[0];expect(page.locator('[data-notes-id="'+note+'"]')).to_have_count(1)
  definitions.extend(page.locator('.definition dd').all_text_contents())
  # Existing chapter notes load and remain distinct across the revision.
  key='understanding-people:practice:v1:/understanding-people/:week-'+n
  page.evaluate('key=>localStorage.setItem(key,JSON.stringify({version:1,fields:{date:"2026-11-10",event:"Earlier chapter note",thought:"Earlier explanation",action:"A practical check",review:"Return to it"}}))',key)
  page.reload();notes=page.locator('[data-notes-id="week-'+n+'"]');notes.locator('> summary').click();expect(notes.locator('[name=event]')).to_have_value('Earlier chapter note');notes.locator('[name=review]').fill('Reviewed after the revision');page.reload();expect(page.locator('[data-notes-id="week-'+n+'"] [name=review]')).to_have_value('Reviewed after the revision')
  for width in [320,390,834,1440]:
   page.set_viewport_size({'width':width,'height':950});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(n,width)
 page.goto(base+'glossary.html');glossary=' '.join(page.locator('main').inner_text().split())
 for d in definitions:assert ' '.join(d.split()) in glossary,d
 page.goto(base+'index.html');expect(page.locator('main video')).to_have_count(0)
 page.goto(base+'reference/confirmation-bias.html');expect(page.locator('main audio')).to_have_count(2)
 page.goto(base+'chapters/11-conflict-manipulation-boundaries.html');expect(page.locator('main')).to_contain_text('Support or protection need not wait');expect(page.locator('main')).to_contain_text('do not provoke a response')
 assert not errors,errors;b.close()
print('Passed: Chapters 2–12, all earlier section/definition anchors, compact practice, reference links, restored/edited notes for every chapter, matching glossary definitions, responsive layouts, paused chapter/overview media and retained reference audio. No screenshots or recordings created.')
