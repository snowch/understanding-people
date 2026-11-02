"""Verify unfinished coverage is clearly labelled and navigable under a Pages base path."""
import json,sys
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
base=sys.argv[1].rstrip('/')+'/'
catalog=json.loads((ROOT/'reference/catalog.json').read_text());entries=[e for g in catalog['groups'] for e in g['entries']];stubs=[e for e in entries if e['status']=='stub'];developed=[e for e in entries if e['status']=='developed']
assert len({e['appNode'] for e in entries})==len(entries)
assert len({e['source'] for e in entries})==len(entries)
shots=Path('/tmp/reference-stubs-check');shots.mkdir(exist_ok=True)
with sync_playwright() as pw:
 b=pw.chromium.launch();page=b.new_page(service_workers='block');errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 for e in stubs:
  page.goto(urljoin(base,e['source'].replace('.md','.html')))
  expect(page.locator('main .reference-status')).to_have_text('Stub — full entry planned')
  expect(page.locator('main h1')).to_have_text(e['title'])
  expect(page.locator('main')).to_contain_text('still to be written')
  assert page.locator('main a[href*="chapters/"]').count()>=1
  assert page.locator('main a[href*="worksheet.html"]').count()==1
  expect(page.locator('.book-sidebar a[aria-current="page"]')).to_have_count(1)
 for width in [390,834,1440]:
  page.set_viewport_size({'width':width,'height':950});page.goto(base+'reference/index.html')
  page.locator('#library-status').select_option('stub');expect(page.locator('.library-entry:visible')).to_have_count(len(stubs))
  page.locator('#library-query').fill('gaslighting');expect(page.locator('.library-entry:visible h3')).to_have_text('Gaslighting & undermining your reality')
  page.screenshot(path=str(shots/f'search-{width}.png'))
  page.locator('.library-entry:visible h3 a').click()
  expect(page.locator('main')).to_contain_text('has not received specialist review')
  page.screenshot(path=str(shots/f'stub-{width}.png'))
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.locator('main a[href*="chapters/"]').first.click();expect(page.locator('main h1')).to_have_text('Why we misinterpret people')
  page.goto(base+'reference/index.html');page.locator('#library-status').select_option('developed');expect(page.locator('.library-entry:visible')).to_have_count(len(developed))
  page.locator('#library-query').fill('gaslighting');expect(page.locator('#library-empty')).to_be_visible()
  page.locator('.library-topics a[href="#clinical-vocabulary"]').click();expect(page.locator('.library-entry:visible')).to_have_count(len(entries))
  page.locator('#library-query').fill('narcissist');page.locator('.library-entry h3 a',has_text='Narcissistic personality disorder').click();expect(page.locator('main .reference-status')).to_be_visible()
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 assert not errors,errors
 b.close()
print(f'Passed: all {len(stubs)} stub routes/status/chapters/worksheet/current navigation; status and text filters, clear topic filters, clinical caveats and responsive layouts.')
