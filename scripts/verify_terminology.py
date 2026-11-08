#!/usr/bin/env python3
"""Follow reference → definition → context/listening; verify all reference links.

No argument serves _site under the project path. A URL runs the same live check.
No screenshots or recordings are created.
"""
import argparse
import functools
import json
import os
import threading
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from playwright.sync_api import sync_playwright,expect
from verify_page_narration import RangeHandler,ThreadingHTTPServer
from reference_terminology import terms,core_terms
from book_navigation import ENTRIES

ROOT=Path(__file__).resolve().parents[1]

def verify(base):
 total=len(terms())+len(core_terms())
 with sync_playwright() as pw:
  proxy={'server':os.environ['HTTPS_PROXY'],'bypass':'localhost,127.0.0.1'} if os.environ.get('HTTPS_PROXY') else None
  browser=pw.chromium.launch(proxy=proxy);context=browser.new_context(proxy=proxy,service_workers='block')
  page=context.new_page();errors=[];requests=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('request',lambda r:requests.append(r.url))
  page.goto(base+'reference/family-membership.html')
  term=page.locator('#definition-family-boundary-ambiguity')
  expect(term).to_have_text('family boundary ambiguity')
  term.focus();page.keyboard.press('Enter')
  expect(page).to_have_url(base+'glossary.html#family-boundary-ambiguity')
  expect(page.locator('#family-boundary-ambiguity')).to_be_in_viewport()
  family=page.locator('.glossary-entry').filter(has=page.locator('h2#family-boundary-ambiguity'))
  expect(family.locator('.definition')).to_contain_text('who counts as part of a family')
  expect(family.locator('.definition-example')).to_contain_text('personal limit')
  expect(page.locator('.narration-heading')).to_contain_text('foundation terms')
  family.get_by_role('link',name='Read in context').click()
  expect(page).to_have_url(base+'reference/family-membership.html#definition-family-boundary-ambiguity')
  # Filtering is local; an in-glossary contrast clears the filter and exposes its target.
  page.goto(base+'glossary.html');query=page.get_by_role('searchbox',name='Find a term')
  expect(page.locator('.glossary-entry')).to_have_count(total)
  titles=page.locator('.glossary-entry h2').all_text_contents()
  assert titles==sorted(titles,key=str.casefold)
  query.fill('family boundary')
  expect(family).to_be_visible();expect(page.locator('.glossary-entry:visible')).to_have_count(1)
  family.get_by_role('link',name='personal boundary',exact=True).click()
  expect(query).to_have_value('')
  expect(page.locator('#boundary')).to_be_visible()
  query.fill('implementation intention')
  alias=page.locator('.glossary-entry:visible');expect(alias).to_have_count(1)
  alias.get_by_role('link',name='if–then plan',exact=True).click()
  expect(query).to_have_value('');expect(page.locator('#if-then-plan')).to_be_visible()
  # The meanings of diagnoses and informal labels remain distinct.
  query.fill('narciss')
  expect(page.locator('#narcissism')).to_be_visible()
  expect(page.locator('#narcissistic-personality-disorder')).to_be_visible()
  expect(page.locator('#narcissism').locator('..')).to_contain_text('Everyday label')
  expect(page.locator('#narcissistic-personality-disorder').locator('..')).to_contain_text('Clinical vocabulary')
  query.fill('OCD')
  expect(page.locator('#ocd')).to_be_visible()
  expect(page.locator('#obsession')).to_be_visible();expect(page.locator('#compulsion')).to_be_visible()
  expect(page.locator('.glossary-entry:visible')).to_have_count(3)
  expect(page.locator('#ocpd')).to_be_hidden()
  query.fill('OCPD')
  expect(page.locator('#ocpd')).to_be_visible()
  page.locator('#ocpd').locator('..').locator('a[href="#ocd"]').click()
  expect(query).to_have_value('');expect(page.locator('#ocd')).to_be_visible()
  query.fill('unmatchedtermzzzz');expect(page.locator('#glossary-empty')).to_be_visible()
  page.get_by_role('button',name='Clear',exact=True).click();expect(query).to_be_focused()
  query.fill('family boundary')
  family.get_by_role('link',name='Find another term ↑').click()
  expect(query).to_have_value('');expect(query).to_be_focused()
  expect(page.locator('.glossary-entry:visible')).to_have_count(total)
  # Every lookup has a real context anchor and a primary narrated lesson.
  for term in terms():
   row=page.locator('.glossary-entry').filter(has=page.locator('h2#'+term['id']))
   expect(row.get_by_role('link',name='Read in context')).to_have_attribute('href',term['source'].replace('.md','.html')+'#definition-'+term['id'])
   expect(row.get_by_role('link',name='Listen to the lesson')).to_have_attribute('href',term['source'].replace('.md','.html')+'#page-narration-title')
  for entry in ENTRIES:
   page.goto(base+entry['source'].replace('.md','.html'))
   links=page.locator('a.glossary-term');hrefs=links.evaluate_all('(els)=>els.map(e=>e.getAttribute("href"))')
   assert len(hrefs)==len(set(hrefs)),entry['source']
   assert not page.locator('a a').count(),entry['source']
   expect(page.locator('.page-narration')).to_have_count(1)
  # A lookup result must offer the relevant reference's audio, not the foundation tour.
  page.goto(base+'search.html');page.locator('#meaning-search').uncheck()
  page.locator('#book-search-query').fill('family boundary ambiguity')
  page.locator('#book-search-form').evaluate('(form)=>form.requestSubmit()')
  result=page.locator('#search-results li').filter(has=page.locator('h3 a[href*="glossary.html#family-boundary-ambiguity"]'))
  expect(result).to_have_count(1)
  expect(result.get_by_role('link',name='Listen in context')).to_have_attribute('href',base+'reference/family-membership.html#page-narration-title')
  # Phone/tablet/desktop in both themes, including deep-link and filtered views.
  for width in (320,390,834,1440):
   for scheme in ('light','dark'):
    page.set_viewport_size({'width':width,'height':950});page.emulate_media(color_scheme=scheme)
    page.goto(base+'glossary.html#family-boundary-ambiguity')
    expect(page.locator('#family-boundary-ambiguity')).to_be_visible()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,scheme)
    query.fill('OCD');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    # Re-selecting the same fragment must work even without a hashchange event.
    contents=page.locator('.on-page')
    if not contents.evaluate('(el)=>el.open'):contents.locator('> summary').click()
    contents.locator('a[href="#family-boundary-ambiguity"]').click()
    expect(query).to_have_value('');expect(page.locator('#family-boundary-ambiguity')).to_be_visible()
  # Native no-JavaScript anchors and all terms stay available.
  c=browser.new_context(proxy=proxy,java_script_enabled=False,service_workers='block');p=c.new_page()
  p.goto(base+'glossary.html#family-boundary-ambiguity')
  expect(p.locator('.glossary-entry')).to_have_count(total)
  expect(p.locator('.glossary-lookup-controls')).to_be_hidden()
  expect(p.locator('#family-boundary-ambiguity')).to_be_visible()
  expect(p.locator('#family-boundary-ambiguity')).to_be_in_viewport()
  p.locator('#family-boundary-ambiguity').locator('..').get_by_role('link',name='Read in context').click()
  expect(p.locator('#definition-family-boundary-ambiguity')).to_be_visible()
  assert not errors,errors
  assert not [u for u in requests if urlsplit(u).path.endswith(('.mp3','.mp4','.onnx','.wasm'))], 'Looking up words must not download media or a model'
  browser.close()
 print(f'PASS: all {len(ENTRIES)} references, {total} glossary headwords, precise return/audio links, local filter, aliases/contrasts, clinical distinctions, search listening destinations, responsive themes and no-JavaScript access.')

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('base',nargs='?');args=parser.parse_args()
 if args.base:verify(args.base.rstrip('/')+'/')
 else:
  server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(RangeHandler,directory=str(ROOT/'_site')))
  threading.Thread(target=server.serve_forever,daemon=True).start()
  try:verify(f'http://localhost:{server.server_port}/understanding-people/')
  finally:server.shutdown()
