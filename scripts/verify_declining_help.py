"""Check concept-led reading, optional examples and retained notes under the Pages path."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
base=sys.argv[1].rstrip('/')+'/reference/declining-help.html'
shots=Path('/tmp/declining-help-check');shots.mkdir(exist_ok=True)
with sync_playwright() as pw:
    browser=pw.chromium.launch()
    context=browser.new_context(service_workers='block')
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(base)
    expect(page.locator('main h2').first).to_have_text('What a refusal tells you')
    case=page.locator('#a-case-that-changes')
    expect(case).not_to_have_attribute('open','')
    expect(case.locator('p').first).to_be_hidden()
    case.locator('summary').focus();page.keyboard.press('Enter')
    expect(case.locator('p').first).to_be_visible()
    case.locator('summary').click()
    for anchor in ['independence','compare-possibilities','family','my-part','try-and-review','put-it-into-practice']:
        expect(page.locator('#'+anchor)).to_have_count(1)
    expect(page.locator('main .reader-action')).to_have_count(1)
    expect(page.locator('main h2').last).to_have_text('Put it into practice')
    # Existing notes survive the content change using their original storage key and fields.
    page.evaluate('''() => localStorage.setItem('understanding-people:practice:v1:/understanding-people/:declining-help-pilot', JSON.stringify({version:1,fields:{date:'',event:'Existing observation',thought:'My first explanation',action:'Ask once',review:'Keep the choice clear'}}))''')
    page.reload()
    notes=page.locator('[data-notes-id="declining-help-pilot"]')
    notes.locator('summary').click()
    expect(page.locator('#declining-help-pilot-event')).to_have_value('Existing observation')
    page.locator('#declining-help-pilot-review').fill('A clearer agreement')
    page.reload();expect(page.locator('#declining-help-pilot-review')).to_have_value('A clearer agreement')
    for width in [390,834,1440]:
        page.set_viewport_size({'width':width,'height':1000});page.goto(base)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.screenshot(path=str(shots/f'entry-{width}.png'))
        page.locator('#compare-possibilities').scroll_into_view_if_needed()
        page.screenshot(path=str(shots/f'examples-{width}.png'))
    nojs=browser.new_context(java_script_enabled=False);q=nojs.new_page();q.goto(base)
    q.locator('#a-case-that-changes summary').click();expect(q.locator('#a-case-that-changes p').first).to_be_visible()
    assert not errors,errors
    browser.close()
print('Passed: concept-led reading, optional case with keyboard/no-JS, stable anchors, existing note recovery/edit/reload, responsive layouts.')
