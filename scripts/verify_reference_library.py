"""Check written coverage, research accountability and the reader's local practice journey.

This verifies publishing behaviour, not scientific accuracy, learning or legal compliance.
It creates no screenshots or audio/video recordings.
"""
import json,sys
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
base=sys.argv[1].rstrip('/')+'/'
cat=json.loads((ROOT/'reference/catalog.json').read_text());entries=[e for g in cat['groups'] for e in g['entries']]
authored=[e for p in (ROOT/'reference/entries').glob('*.json') for e in json.loads(p.read_text())['entries']]
assert len(entries)==111 and all(e['status']=='developed' for e in entries)
assert len(authored)==108 and len({e['id'] for e in authored})==108
assert not json.loads((ROOT/'reference/stubs.json').read_text())['entries']
assert {e['id'] for e in authored}=={e['appNode'] for e in entries}-{'confirmation','correspondence','refusehelp'}
bank=json.loads((ROOT/'reference/research-sources.json').read_text())['sources']
for e in authored:
    assert e['sources'] and all(k in bank for k in e['sources'])
    assert len(e['practice'])==len(e['takeaways'])==3
    assert all(bank[k]['access'] and bank[k]['limit'] and bank[k]['checked'] for k in e['sources'])
with sync_playwright() as pw:
    b=pw.chromium.launch();context=b.new_context(service_workers='block');page=context.new_page();errors=[];media=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:media.append(r.url) if urlsplit(r.url).path.endswith(('.mp3','.mp4','.webm','.wav')) else None)
    page.goto(base+'reference/index.html');expect(page.locator('.library-entry')).to_have_count(111)
    expect(page.locator('.nav-stub')).to_have_count(0)
    for e in entries:
        page.goto(urljoin(base,e['source'].replace('.md','.html')))
        expect(page.locator('main h1')).to_have_text(e['title'])
        expect(page.locator('main .reference-status')).to_have_count(0)
        expect(page.locator('main')).not_to_contain_text('Stub — full entry planned')
        expect(page.locator('main .reader-action')).to_have_count(1)
        assert page.locator('main .practice-notes textarea').count()>=4
        expect(page.locator('.book-sidebar a[aria-current="page"]')).to_have_count(1)
        if e['appNode'] not in ['confirmation','correspondence','refusehelp']:
            expect(page.locator('main .key-takeaways li')).to_have_count(3)
            assert page.locator('main a[href^="https://"]').count()>=1
            for anchor in ['a-distinction-to-keep-in-mind','read-the-foundations-now','related-entries','evidence-to-develop','what-the-full-entry-will-cover']:
                expect(page.locator('#'+anchor)).to_have_count(1)
    assert not media,media
    # Separate entries must not overwrite each other's answers; saved data is text.
    for slug,node in [('autonomy','autonomy'),('gaslighting','gaslighting')]:
        page.goto(base+'reference/'+slug+'.html');panel=page.locator('[data-notes-id="reference-'+node+'"]');panel.locator('> summary').click()
        page.locator('#reference-'+node+'-event').fill('My '+node+' observation <img src=x onerror=alert(1)>')
        page.reload();panel.locator('> summary').click();expect(page.locator('#reference-'+node+'-event')).to_have_value('My '+node+' observation <img src=x onerror=alert(1)>')
        expect(panel.locator('img')).to_have_count(0)
    page.goto(base+'reference/autonomy.html');expect(page.locator('#reference-autonomy-event')).to_have_value('My autonomy observation <img src=x onerror=alert(1)>')
    page.goto(base+'reference/pd-narcissistic.html');expect(page.locator('main')).to_contain_text('has not received specialist review')
    expect(page.locator('label[for="reference-pd-narcissistic-thought"]')).to_have_text('What remains uncertain or needs professional assessment?')
    for width in [320,390,834,1440]:
        page.set_viewport_size({'width':width,'height':950})
        for slug in ['index','sources','gaslighting','pd-narcissistic','agreeableness','autonomy']:
            page.goto(base+'reference/'+slug+'.html');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,slug)
        page.goto(base+'reference/index.html');page.locator('#library-query').fill('gaslighting');page.locator('.library-entry:visible h3 a').click();expect(page.locator('main h1')).to_have_text('Gaslighting & undermining your reality')
        page.goto(base+'reference/index.html');page.locator('#library-status').select_option('developed');expect(page.locator('.library-entry:visible')).to_have_count(111)
        page.locator('#library-status').select_option('stub');expect(page.locator('#library-empty')).to_be_visible()
    nojs=b.new_context(java_script_enabled=False,service_workers='block',viewport={'width':390,'height':900});q=nojs.new_page();q.goto(base+'reference/autonomy.html');q.locator('.practice-notes > summary').focus();q.keyboard.press('Enter');expect(q.locator('.practice-notes textarea').first).to_be_visible();expect(q.locator('.practice-notes noscript')).to_be_visible()
    assert not errors,errors
    b.close()
print('Passed: all 111 written routes, 108 authored coverage, citations/access scope, old anchors, practice structure, note isolation/escaping/reload, clinical prompts, no unsolicited media, search, status filters, responsive widths and no-JavaScript notes. No recordings or screenshots created.')
