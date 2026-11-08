#!/usr/bin/env python3
"""Exercise actual local-model retrieval, privacy, failure recovery and reading links."""
import argparse
import functools
import json
import os
from pathlib import Path
import threading
import time
from urllib.parse import urlsplit, unquote

from playwright.sync_api import sync_playwright, expect
from build import Document, OUT
from book_search import ASSETS, ROOT
from verify_page_narration import RangeHandler, ThreadingHTTPServer


def verify(base, screenshots=False):
    base = base.rstrip('/')+'/'
    index = json.loads((OUT/'assets/search/index.json').read_text())
    docs = {d['url']: Document((OUT/d['url']).read_text()) for d in index['documents']}
    for p in index['passages']:
        assert p['anchor'] in docs[index['documents'][p['document']]['url']].ids
    for d in index['documents']:
        for kind in ['listen', 'practice']:
            assert not d[kind] or d[kind] in docs[d['url']].ids, (d['url'],kind,d[kind])
    assert len(index['documents']) == 161
    cases = json.loads((ROOT/'docs/search-questions.json').read_text())
    with sync_playwright() as pw:
        proxy={'server':os.environ['HTTPS_PROXY']} if base.startswith('https://') and os.environ.get('HTTPS_PROXY') else None
        browser=pw.chromium.launch(proxy=proxy)
        context=browser.new_context(proxy=proxy,service_workers='block')
        page=context.new_page();requests=[];errors=[]
        page.on('request',lambda r:requests.append(r.url))
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base+'reference/index.html')
        library=page.get_by_role('searchbox',name='Find a topic or behaviour')
        library.fill('matriarch')
        expect(page.locator('.library-entry:visible h3',has_text='Family expectations')).to_be_visible()
        expect(page.locator('#library-query-note')).to_contain_text('no dedicated entry')
        matriarch_topics=page.locator('.library-entry:visible h3').all_text_contents()
        library.fill('patriarch')
        expect(page.locator('.library-entry:visible h3',has_text='Family expectations')).to_be_visible()
        assert matriarch_topics==page.locator('.library-entry:visible h3').all_text_contents()
        page.goto(base+'chapters/01-before-you-explain.html')
        page.locator('.header-search').click()
        expect(page.locator('h1')).to_have_text('Search the book')
        expect(page.locator('.page-narration')).to_have_count(0)
        query=page.get_by_role('searchbox',name='What would you like to understand?')
        expect(query).to_be_visible()
        assert not any('/models/' in u or '/vendor/' in u or '.wasm' in u for u in requests)
        page.locator('#meaning-search').uncheck()
        query.fill('confirmation bias');query.press('Enter')
        expect(page.locator('#search-results li h3').first).to_have_text('Confirmation bias')
        query.fill('matriarch');query.press('Enter')
        expect(page.locator('#search-results li h3').first).to_have_text('Family expectations')
        expect(page.locator('#search-term-note')).to_contain_text('no dedicated entry')
        expect(page.locator('#search-results li .search-result-kind').first).to_contain_text('Related topic')
        assert not any('/models/' in u or '/vendor/' in u or '.wasm' in u for u in requests)
        page.locator('#meaning-search').check()
        outcomes=[]
        for case in cases:
            query.fill(case['query']);start=time.monotonic();query.press('Enter')
            expect(page.locator('#search-loading')).to_have_text('Search complete. Results are passages from the book.',timeout=120000)
            hrefs=page.locator('#search-results li h3 a').evaluate_all('(links)=>links.map(a=>a.href.split("#")[0])')
            paths=[u.removeprefix(base) for u in hrefs]
            hit=next((i+1 for i,path in enumerate(paths) if path in case['expected']),None)
            outcomes.append({'query':case['query'],'rank':hit,'seconds':round(time.monotonic()-start,2),'top3':paths[:3]})
            print(json.dumps(outcomes[-1]),flush=True)
            if case.get('required'):assert hit is not None and hit<=3,outcomes[-1]
            assert len(paths)==len(set(paths))
        # A model benchmark is a regression aid, not proof that all questions work.
        Path('/tmp/book-search-relevance.json').write_text(json.dumps(outcomes,indent=2))
        passed=sum(r['rank'] is not None and r['rank']<=3 for r in outcomes)
        print(f'Relevance: {passed}/{len(cases)} questions have an expected reading in the first three.',flush=True)
        assert passed>=len(cases)-2, outcomes
        assert outcomes[0]['rank']==1
        # A plain refusal should not lead with a personality-disorder label.
        query.fill(cases[0]['query']);query.press('Enter')
        expect(page.locator('#search-loading')).to_have_text('Search complete. Results are passages from the book.',timeout=30000)
        assert not any('disorder' in t.lower() for t in page.locator('#search-results li h3').all_text_contents()[:3])
        assert not any(urlsplit(u).netloc!=urlsplit(base).netloc for u in requests)
        assert not any(unquote(urlsplit(u).query).find('refuses')>=0 or 'q=' in urlsplit(u).query for u in requests)
        assert not page.evaluate('Object.entries(localStorage).some(([k,v])=>k.includes("query")||v.includes("Dad refuses"))')
        for width in [320,390,834,1024,1440]:
            page.set_viewport_size({'width':width,'height':950})
            for scheme in ['light','dark']:
                page.emulate_media(color_scheme=scheme)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), (width,scheme)
                expect(page.locator('.mobile-search-link' if width<=1050 else '.header-search')).to_be_visible()
                if screenshots and width in [390,1440]:page.screenshot(path=f'/tmp/book-search-{width}-{scheme}.png',full_page=False)
        page.set_viewport_size({'width':1440,'height':1000})
        first=page.locator('#search-results li').first
        first.locator('h3 a').click()
        expect(page.locator('h1')).to_have_text('Declining help')
        assert urlsplit(page.url).fragment
        page.go_back()
        # Unrelated text should not receive invented answers or a spurious label.
        query=page.locator('#book-search-query');query.fill('zzqvpxj987');query.press('Enter')
        expect(page.locator('#search-loading')).to_have_text('Search complete. Results are passages from the book.',timeout=30000)
        expect(page.locator('#search-empty')).to_be_visible()
        page.get_by_role('button',name='Clear',exact=True).click()
        expect(query).to_have_value('');expect(query).to_be_focused()
        expect(page.locator('#search-results-region')).to_be_hidden()
        # Cancel a delayed cold model load. A late response cannot restore results.
        cold=browser.new_context(proxy=proxy,service_workers='block')
        cold.route('**/models/**',lambda route:route.abort())
        q=cold.new_page();q.goto(base+'search.html');q.locator('#book-search-query').fill('confirmation bias');q.locator('#book-search-query').press('Enter')
        expect(q.locator('#search-loading')).to_contain_text('Keyword results are still available',timeout=60000)
        expect(q.locator('#search-results h3').first).to_have_text('Confirmation bias')
        cold.close()
        # Keywords still work when vector delivery fails.
        broken=browser.new_context(proxy=proxy,service_workers='block');broken.route('**/vectors.bin*',lambda r:r.abort())
        q=broken.new_page();q.goto(base+'search.html');q.locator('#book-search-query').fill('confirmation bias');q.locator('#book-search-query').press('Enter')
        expect(q.locator('#search-loading')).to_contain_text('Keyword results are still available')
        expect(q.locator('#search-results h3').first).to_have_text('Confirmation bias');broken.close()
        nojs=browser.new_context(proxy=proxy,service_workers='block',java_script_enabled=False)
        q=nojs.new_page();q.goto(base+'search.html');expect(q.locator('#book-search-form')).to_be_hidden()
        expect(q.get_by_role('link',name='reference library',exact=True)).to_be_visible();nojs.close()
        # Stop a genuinely pending cold load and submit a different keyword search.
        held=[]
        cancel_context=browser.new_context(proxy=proxy,service_workers='block')
        cancel_context.route('**/models/**',lambda r:held.append(r))
        q=cancel_context.new_page();q.goto(base+'search.html')
        q.locator('#book-search-query').fill('confirmation bias')
        with q.expect_request(lambda r:'/models/' in r.url,timeout=60000):q.locator('#book-search-query').press('Enter')
        expect(q.locator('#search-cancel')).to_be_visible()
        q.locator('#search-cancel').click()
        expect(q.locator('#search-loading')).to_contain_text('Meaning search stopped')
        q.locator('#meaning-search').uncheck();q.locator('#book-search-query').fill('correspondence bias');q.locator('#book-search-query').press('Enter')
        expect(q.locator('#search-results h3').first).to_have_text('Correspondence bias')
        for route in held:
            try:route.abort()
            except Exception:pass  # The worker may already have cancelled it.
        cancel_context.unroute_all(behavior='ignoreErrors')
        cancel_context.close()
        # First reading does not cache 47 MB. A requested model is cached and
        # performs a fresh, different inference after an offline page reload.
        offline=browser.new_context(proxy=proxy)
        q=offline.new_page();q.goto(base+'search.html')
        q.evaluate('navigator.serviceWorker.ready')
        q.wait_for_function('navigator.serviceWorker.controller!==null')
        cached=q.evaluate('''async()=>{const keys=await caches.keys();return (await Promise.all(keys.map(async k=>(await (await caches.open(k)).keys()).map(r=>r.url)))).flat()}''')
        assert not any(u.endswith(('.wasm','.onnx')) for u in cached)
        offline.set_offline(True)
        q.locator('#book-search-query').fill('confirmation bias');q.locator('#book-search-query').press('Enter')
        expect(q.locator('#search-loading')).to_contain_text('Keyword results are still available',timeout=30000)
        expect(q.locator('#search-results h3').first).to_have_text('Confirmation bias')
        offline.set_offline(False)
        q.locator('#book-search-query').fill('Dad refuses help even when he is struggling');q.locator('#book-search-query').press('Enter')
        expect(q.locator('#search-loading')).to_have_text('Search complete. Results are passages from the book.',timeout=120000)
        cached=q.evaluate('''async()=>{const keys=await caches.keys();return (await Promise.all(keys.map(async k=>(await (await caches.open(k)).keys()).map(r=>r.url)))).flat()}''')
        assert any(u.endswith('.wasm') for u in cached) and any(u.endswith('.onnx') for u in cached)
        offline.set_offline(True);q.reload()
        expect(q.locator('#book-search-form')).to_be_visible()
        q.locator('#book-search-query').fill('Why do I only notice evidence that I am right?');q.locator('#book-search-query').press('Enter')
        expect(q.locator('#search-loading')).to_have_text('Search complete. Results are passages from the book.',timeout=60000)
        expect(q.locator('#search-results h3').first).to_have_text('Confirmation bias')
        offline.close()
        assert not errors,errors
        browser.close()
    print('Passed actual browser meaning search, relevance cases, keyword fallback, privacy, deduplication, deep links, responsive light/dark layouts, no-JS browsing, cancellation and fresh offline inference with on-demand model caching.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('base',nargs='?');parser.add_argument('--screenshots',action='store_true');args=parser.parse_args()
    if args.base:verify(args.base,args.screenshots)
    else:
        server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(RangeHandler,directory=str(OUT)))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:verify(f'http://localhost:{server.server_port}/understanding-people/',args.screenshots)
        finally:server.shutdown()
