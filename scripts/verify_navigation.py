"""Exercise the library and book hierarchy under a GitHub Pages base path."""
import sys
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, expect
from book_navigation import ENTRIES
from build import CHAPTERS, PAGES
base=sys.argv[1].rstrip('/')+'/'
shots=Path('/tmp/book-navigation');shots.mkdir(exist_ok=True)
with sync_playwright() as pw:
    browser=pw.chromium.launch()
    context=browser.new_context(service_workers='block')
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    for source, _ in PAGES:
        path='index.html' if source=='book.md' else source.replace('.md','.html')
        page.goto(urljoin(base,path))
        expect(page.locator('.book-sidebar .nav-section')).to_have_count(4)
        expect(page.locator('.book-sidebar .nav-section[open]')).to_have_count(1)
        # No unstructured resource list or independently promoted audio pages.
        expect(page.locator('.resource-list')).to_have_count(0)
        if source.startswith('audio/confirmation-'):
            expect(page.locator('.book-sidebar [data-section="library"]')).to_have_attribute('open','')
            expect(page.locator('.breadcrumbs a').last).to_have_text('Confirmation bias')
            expect(page.locator('.pagination a')).to_have_attribute('href','../reference/confirmation-bias.html')
            expect(page.locator('.book-sidebar .nav-recordings a[aria-current="page"]')).to_have_count(1)
        if source.startswith('chapters/'):
            expect(page.locator('.book-sidebar .chapter-list [aria-current="page"]')).to_have_count(1)
    page.goto(base+'chapters/01-before-you-explain.html')
    expect(page.locator('.pagination [rel=prev]')).to_have_attribute('href','../index.html')
    expect(page.locator('.pagination [rel=next]')).to_have_attribute('href','02-what-counts-as-knowing.html')
    page.goto(base+'conclusion.html');expect(page.locator('.pagination [rel=next]')).to_have_count(0)
    for width in [320,390,834,1440]:
        page.set_viewport_size({'width':width,'height':950})
        page.goto(base+'reference/index.html')
        search=page.get_by_role('searchbox',name='Find a topic or behaviour')
        expect(page.locator('.library-entry:visible')).to_have_count(len(ENTRIES))
        search.fill('independence');expect(page.locator('.library-entry:visible')).to_have_count(1)
        expect(page.locator('.library-entry:visible h3')).to_have_text('Declining help')
        search.fill('attribution');expect(page.locator('.library-entry:visible h3')).to_have_text('Correspondence bias')
        search.fill('no-such-topic');expect(page.locator('#library-empty')).to_be_visible()
        expect(page.locator('#library-result-count')).to_have_text('0 of 3 entries')
        page.get_by_role('button',name='Clear search').click();expect(search).to_be_focused()
        expect(page.locator('.library-entry:visible')).to_have_count(3)
        search.fill('nothing');page.locator('.library-topics a').first.click()
        expect(page.locator('.library-entry:visible')).to_have_count(3)
        page.evaluate('scrollTo(0,0)');page.screenshot(path=str(shots/f'library-{width}.png'))
        page.locator('.library-entry h3 a',has_text='Confirmation bias').click()
        page.locator('main .reference-listenings a').first.click()
        expect(page.locator('h1')).to_contain_text('Confirmation bias')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        if width<=800:
            page.locator('.mobile-nav > summary').click()
            nav=page.locator('.mobile-nav')
            assert nav.locator('.nav-topic a').first.evaluate('(e)=>getComputedStyle(e).display')=='block'
            expect(nav.locator('[data-section="library"]')).to_have_attribute('open','')
            nav.locator('[data-section="practice"] > summary').click()
            page.screenshot(path=str(shots/f'mobile-nav-{width}.png'))
            nav.get_by_role('link',name='Choose a practice',exact=True).click()
            expect(page.locator('h1')).to_have_text('Practice')
        else:
            page.screenshot(path=str(shots/f'audio-context-{width}.png'))
        page.goto(base+'audio/confirmation-bias-explained.html')
        page.locator('.pagination a').click();expect(page.locator('h1')).to_have_text('Confirmation bias')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.set_viewport_size({'width':1440,'height':1000});page.emulate_media(color_scheme='dark');page.goto(base+'reference/index.html');page.screenshot(path=str(shots/'library-dark.png'))
    nojs=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844});q=nojs.new_page();q.goto(base+'reference/index.html')
    expect(q.locator('.library-entry:visible')).to_have_count(3);expect(q.locator('.library-search')).to_be_hidden()
    q.locator('.mobile-nav > summary').click();q.locator('.mobile-nav [data-section="book"] > summary').click()
    q.locator('.mobile-nav').get_by_role('link',name='01 Why we misinterpret people',exact=True).click()
    expect(q.locator('h1')).to_have_text('Why we misinterpret people')
    assert not errors,errors
    browser.close()
print('Passed: four-section hierarchy on every page, topic search/clear/empty states, mobile navigation, breadcrumbs/audio return, chapter order, base-path links, responsive screenshots and no-JavaScript browsing.')
