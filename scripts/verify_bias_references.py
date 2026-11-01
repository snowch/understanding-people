"""Check book routes, readable reference pages and separate persistent practice notes."""
import sys,json
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
base=sys.argv[1];data=json.loads((ROOT/'reference/biases.json').read_text())
with sync_playwright() as pw:
    b=pw.chromium.launch(channel='chromium');context=b.new_context(service_workers='block');p=context.new_page()
    errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
    for d in data['entries']:
        p.goto(urljoin(base,'chapters/01-before-you-explain.html'))
        p.locator('main a[href="../reference/'+d['slug']+'.html"]').click()
        expect(p.locator('h1')).to_have_text(d['title'])
        for anchor in ['why','recognise','change','practice']:
            assert p.locator('#'+anchor).count()==1
        for width in [320,390,834,1440]:
            p.set_viewport_size({'width':width,'height':950})
            assert p.evaluate('document.documentElement.scrollWidth<=innerWidth'),(d['id'],width)
            if width in [390,1440]:
                p.screenshot(path=f'/tmp/book-{d["id"]}-{width}.png')
        notes=p.locator('.practice-notes');notes.locator('summary').click()
        note='A fictional practice note for '+d['title']
        notes.locator('textarea[name="thought"]').fill(note)
        p.reload();notes.locator('summary').click()
        assert notes.locator('textarea[name="thought"]').input_value()==note
        assert p.get_by_role('link',name='Get the private app download').get_attribute('href').endswith('/releases/tag/v0.14.0')
        expect(p.locator('main')).to_contain_text('Book notes and app notes are separate')
        p.locator('#practice').scroll_into_view_if_needed();p.screenshot(path=f'/tmp/book-{d["id"]}-practice.png')
    assert not errors,errors
    b.close()
print('Passed: Chapter 1 reference routes, explicit private-app access, separate persistent notes and responsive reading.')
