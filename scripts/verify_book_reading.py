#!/usr/bin/env python3
"""Follow the reading guide, save it, return to a chapter and use it offline.

No screenshots or media are generated. Optional argument checks a live base URL.
"""
import argparse,functools,json,os,threading
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright,expect
from verify_page_narration import RangeHandler,ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[1]
BOOKS=('social-animal','personality-puzzle','learning-and-behavior','mistakes-were-made','dance-of-anger','difficult-conversations','influence')

def verify(base):
 with sync_playwright() as pw:
  proxy={'server':os.environ['HTTPS_PROXY'],'bypass':'localhost,127.0.0.1'} if os.environ.get('HTTPS_PROXY') else None
  b=pw.chromium.launch(proxy=proxy);c=b.new_context(proxy=proxy,service_workers='block');p=c.new_page()
  errors=[];requests=[];p.on('pageerror',lambda e:errors.append(str(e)));p.on('request',lambda r:requests.append(r.url))
  for source in ('index.html','contents.html','about.html','references.html'):
   p.goto(base+source)
   link=p.locator('.reading-connections').get_by_role('link',name='Books for deeper reading')
   expect(link).to_have_count(1);link.click()
   expect(p).to_have_url(base+'reading/books.html')
  expect(p.locator('h1')).to_have_text('Books for deeper reading')
  expect(p.locator('.book-sidebar [data-section="about"]')).to_have_attribute('open','')
  expect(p.locator('.book-sidebar a[aria-current="page"]')).to_have_attribute('href','books.html')
  expect(p.locator('.page-narration')).to_have_count(0)
  expect(p.locator('.narration-update')).to_contain_text('Written edition')
  for id in BOOKS:expect(p.locator('h2#'+id)).to_have_count(1)
  expect(p.locator('.prose a[href^="https://"]')).to_have_count(7)
  p.locator('.on-page > summary').click();p.locator('.on-page a[href="#dance-of-anger"]').click()
  expect(p).to_have_url(base+'reading/books.html#dance-of-anger')
  save=p.locator('button[data-reading-current]');expect(save).to_be_visible();save.click()
  expect(save).to_have_attribute('aria-pressed','true')
  p.locator('.reading-tools').get_by_role('link',name='Reading list',exact=True).click()
  expect(p.locator('#reading-list-items h2 a')).to_have_attribute('href',base+'reading/books.html#dance-of-anger')
  p.locator('#reading-list-items h2 a').click()
  expect(p.locator('#dance-of-anger')).to_be_visible()
  p.locator('.prose a[href="../chapters/06-personality-habits-situations.html"]').click()
  expect(p.locator('h1')).to_have_text('Personality, habits and situations')
  # The guide can be saved from a nested path and found through keyword search.
  p.goto(base+'search.html');p.locator('#meaning-search').uncheck()
  p.locator('#book-search-query').fill('The Dance of Anger');p.locator('#book-search-query').press('Enter')
  result=p.locator('#search-results li').filter(has=p.locator('h3 a[href*="reading/books.html"]'))
  expect(result).to_have_count(1);expect(result.locator('[data-reading-save]')).to_have_attribute('aria-pressed','true')
  expect(result.get_by_role('link',name='Listen',exact=True)).to_have_count(0)
  for width in (320,390,834,1440):
   for scheme in ('light','dark'):
    p.set_viewport_size({'width':width,'height':950});p.emulate_media(color_scheme=scheme)
    p.goto(base+'reading/books.html')
    assert p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,scheme)
    if width<=1050:
     p.locator('.mobile-nav > summary').click()
     expect(p.locator('.mobile-nav [data-section="about"] a[aria-current="page"]')).to_be_visible()
  n=b.new_context(proxy=proxy,java_script_enabled=False,service_workers='block');q=n.new_page()
  q.goto(base+'reading/books.html#learning-and-behavior')
  expect(q.locator('#learning-and-behavior')).to_be_visible()
  expect(q.locator('.prose a[href="../reference/reinforcement.html#tendency-expectation-consequence"]')).to_have_count(1)
  # Installation retains this new page and its chapter routes for offline reading.
  o=b.new_context(proxy=proxy);r=o.new_page();r.goto(base+'reading/books.html')
  r.wait_for_function('navigator.serviceWorker.controller!==null',timeout=30000)
  r.wait_for_function("caches.keys().then(async keys=>(await Promise.all(keys.filter(k=>k.startsWith('understanding-people-')).map(k=>caches.open(k).then(c=>c.match(location.pathname))))).some(Boolean))",timeout=60000)
  o.set_offline(True);r.reload();expect(r.locator('h1')).to_have_text('Books for deeper reading')
  assert not errors,errors
  assert not [u for u in requests if urlsplit(u).path.endswith(('.mp3','.mp4','.onnx','.wasm'))],requests
  b.close()
 print('PASS: seven books, navigation and chapter returns, nested-path save/search, accurate text/audio scope, responsive themes, no-JavaScript reading and installed offline guide.')

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('base',nargs='?');args=parser.parse_args()
 if args.base:verify(args.base.rstrip('/')+'/')
 else:
  s=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(RangeHandler,directory=str(ROOT/'_site')))
  threading.Thread(target=s.serve_forever,daemon=True).start()
  try:verify(f'http://localhost:{s.server_port}/understanding-people/')
  finally:s.shutdown()
