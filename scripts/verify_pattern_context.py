#!/usr/bin/env python3
"""Read generic explanations, follow the cycle, save an observation and return.

No screenshots, audio production or reader-data requests. Optional live base URL.
"""
import argparse,functools,os,threading
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
from verify_page_narration import RangeHandler,ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[1]

def verify(base):
 with sync_playwright() as pw:
  proxy={'server':os.environ['HTTPS_PROXY'],'bypass':'localhost,127.0.0.1'} if os.environ.get('HTTPS_PROXY') else None
  b=pw.chromium.launch(proxy=proxy);c=b.new_context(proxy=proxy,service_workers='block');p=c.new_page()
  errors=[];media=[];p.on('pageerror',lambda e:errors.append(str(e)))
  p.on('request',lambda r:media.append(r.url) if r.url.split('?')[0].endswith(('.mp3','.mp4','.onnx','.wasm')) else None)
  p.goto(base+'chapters/06-personality-habits-situations.html')
  routes=p.locator('.reading-connections');routes.locator('> details > summary').click()
  routes.get_by_role('link',name='Consequences that sustain a pattern').click()
  expect(p.locator('#tendency-expectation-consequence')).to_have_text('A tendency, an expectation, or a result?')
  expect(p.locator('#tendency-expectation-consequence + p')).to_contain_text('can overlap')
  expect(p.locator('.prose table tbody tr')).to_have_count(3)
  expect(p.locator('#silence-and-consequences')).to_be_visible()
  expect(p.locator('.prose')).to_contain_text('Silence can reflect agreement, uncertainty, fatigue')
  for slug in ('reinforcement','criticism','people-pleasing'):
   p.goto(base+'reference/'+slug+'.html')
   expect(p.locator('.narration-update')).to_contain_text('Written edition')
   expect(p.locator('.page-narration')).to_have_count(0)
   expect(p.locator('.reader-action')).to_have_count(1)
   expect(p.locator('.key-takeaways li')).to_have_count(3)
  p.goto(base+'reference/index.html')
  lookup=p.get_by_role('searchbox',name='Find a topic or behaviour')
  for phrase in ('appeasement','conflict-avoidant accommodation'):
   lookup.fill(phrase)
   expect(p.locator('.library-entry:visible h3')).to_have_text('People-pleasing & automatic agreement')
   expect(p.locator('.library-entry:visible')).not_to_contain_text('Listen')
  p.goto(base+'reference/people-pleasing.html')
  expect(p.locator('#agreement-relief-cycle')).to_be_visible()
  expect(p.locator('.prose')).to_contain_text('Immediate tension or anxiety falls')
  expect(p.locator('.prose')).to_contain_text('what it costs later')
  p.locator('#definition-appeasement').click()
  row=p.locator('#appeasement').locator('..')
  expect(row.locator('.definition')).to_contain_text('not a diagnosis')
  expect(row.get_by_role('link',name='Listen to the lesson')).to_have_count(0)
  row.get_by_role('link',name='Read in context').click()
  expect(p).to_have_url(base+'reference/people-pleasing.html#definition-appeasement')
  notes=p.locator('[data-notes-id="reference-people-pleasing"]');notes.locator('> summary').click()
  notes.locator('textarea[name="event"]').fill('Fictional practice: I agreed to an extra task. No objection was voiced.')
  notes.locator('textarea[name="thought"]').fill('I predicted disapproval. I do not know what refusal would have brought.')
  p.reload();notes.locator('> summary').click()
  expect(notes.locator('textarea[name="thought"]')).to_have_value('I predicted disapproval. I do not know what refusal would have brought.')
  for width in (320,390,834,1440):
   p.set_viewport_size({'width':width,'height':950})
   for scheme in ('light','dark'):
    p.emulate_media(color_scheme=scheme)
    for slug in ('reinforcement','criticism','people-pleasing'):
     p.goto(base+'reference/'+slug+'.html')
     assert p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,scheme,slug)
  p.goto(base+'downloads/index.html')
  expect(p.locator('.recorded-edition-note')).to_contain_text('later written additions')
  expect(p.locator('.recorded-edition-note a')).to_have_count(3)
  p.goto(base+'reference/learned.html');expect(p.locator('.page-narration')).to_have_count(1)
  nc=b.new_context(proxy=proxy,java_script_enabled=False,service_workers='block');q=nc.new_page()
  q.goto(base+'reference/people-pleasing.html#agreement-relief-cycle')
  expect(q.locator('#agreement-relief-cycle')).to_be_visible()
  q.locator('.practice-notes > summary').focus();q.keyboard.press('Enter')
  expect(q.locator('.practice-notes textarea').first).to_be_visible()
  assert not errors,errors
  assert not media,media
  b.close()
 print('PASS: generic comparison, agreement/relief cycle, context links, one practice/recap, glossary, saved observations, accurate audio scope, responsive themes and no-JavaScript reading.')

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('base',nargs='?');args=parser.parse_args()
 if args.base:verify(args.base.rstrip('/')+'/')
 else:
  s=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(RangeHandler,directory=str(ROOT/'_site')))
  threading.Thread(target=s.serve_forever,daemon=True).start()
  try:verify(f'http://localhost:{s.server_port}/understanding-people/')
  finally:s.shutdown()
