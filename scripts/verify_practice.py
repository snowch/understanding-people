#!/usr/bin/env python3
# Copyright © 2026 Christopher Snow
"""Verify practice and local notes in a served book; requires Playwright/Chromium."""
import sys
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
from build import CHAPTERS, destination

base = sys.argv[1]
first = urljoin(base, destination(CHAPTERS[0][1]).as_posix())
second = urljoin(base, destination(CHAPTERS[1][1]).as_posix())


def reveal_more(page):
    more = page.locator('details.more-practice')
    if more.count() and more.get_attribute('open') is None:
        more.locator(':scope > summary').click()


with sync_playwright() as pw:
    browser = pw.chromium.launch(channel='chromium')
    context = browser.new_context(accept_downloads=True, service_workers='block')
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    question_count = recall_count = note_count = 0
    for _, source in CHAPTERS:
        page.goto(urljoin(base, destination(source).as_posix()))
        assert page.locator('.remember-cue').count() == 1
        compact = source == CHAPTERS[0][1]
        check = page.locator('.practice-check' if compact else '.chapter-check')
        questions = check.locator('.answer-check')
        if compact:
            assert questions.count() == 2
            assert page.locator('.compact-practice').count() == 1
            assert page.locator('details.more-practice[open]').count() == 0
            assert page.locator('.practice-notes[open]').count() == 0
            assert page.locator('#key-takeaways').evaluate("e => !!(e.compareDocumentPosition(document.querySelector('#put-it-into-practice')) & Node.DOCUMENT_POSITION_FOLLOWING)")
        else:
            assert 3 <= questions.count() <= 4
            assert page.locator('#can-you-use-it').evaluate("e => !!(e.compareDocumentPosition(document.querySelector('#key-takeaways')) & Node.DOCUMENT_POSITION_FOLLOWING)")
        question_count += questions.count()
        recall_count += page.locator('.recall-practice').count()
        note_count += page.locator('.practice-notes').count()
        assert questions.evaluate_all('panels => panels.every(panel => !panel.open)')
        assert page.locator('.key-takeaways li').count() in [3, 4, 5]
        for width in [320, 390, 834, 1440]:
            page.set_viewport_size({'width': width, 'height': 950})
            page.locator('.practice-notes').first.evaluate('e => e.open = true')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (source, width)
        for panel in page.locator('.reader-action, .chapter-check, .practice-check, .recall-practice, .remember-cue').all():
            label = panel.get_attribute('aria-labelledby')
            assert panel.locator(f'[id="{label}"]').count() == 1
    assert (question_count, recall_count, note_count) == (35, 6, 14)
    page.goto(first)
    reveal_more(page)
    three = page.locator('[data-notes-id="chapter-01-three-questions"]')
    three.locator('summary').click()
    for label, answer in [
        ('What did they say or do?', 'They said the plan was not ready.'),
        ('Why do I think they did it?', 'I guessed they disliked it.'),
        ('How could I check?', 'Ask what still needs doing.'),
    ]:
        three.get_by_label(label, exact=True).fill(answer)
    page.reload()
    reveal_more(page)
    three.locator('summary').click()
    assert three.get_by_label('How could I check?', exact=True).input_value() == 'Ask what still needs doing.'
    summary = page.locator('.practice-check summary').first
    assert summary.locator('..').get_attribute('open') is None
    summary.focus()
    page.keyboard.press('Enter')
    assert summary.locator('..').get_attribute('open') is not None
    page.keyboard.press('Space')
    assert summary.locator('..').get_attribute('open') is None
    notes = page.locator('[data-notes-id="week-01-confirmation"]')
    notes.locator('summary').focus()
    page.keyboard.press('Enter')
    sample = '<img src=x onerror=alert(1)> I noticed praise as well as criticism.'
    notes.get_by_label('What happened?', exact=True).fill(sample)
    notes.get_by_label('What did I think it meant?', exact=True).fill('I thought they disliked the idea.')
    notes.get_by_label('Date to return', exact=False).fill('2026-11-03')
    assert 'Saved in this browser' in notes.locator('[role=status]').inner_text()
    page.evaluate("localStorage.setItem('another-book', 'leave me alone')")
    other = page.locator('[data-notes-id="week-01-correspondence"]')
    other.locator('summary').click()
    other.get_by_label('What happened?', exact=True).fill('A late arrival may have another explanation.')
    # Navigation/reload restore each exercise separately, including the date.
    page.goto(second)
    next_notes = page.locator('.practice-notes')
    next_notes.locator('summary').click()
    assert next_notes.get_by_label('What happened?', exact=True).input_value() == ''
    next_notes.get_by_label('What happened?', exact=True).fill('Another chapter, separate notes.')
    page.goto(first)
    reveal_more(page)
    notes.locator('summary').click()
    assert notes.get_by_label('What happened?', exact=True).input_value() == sample
    assert notes.get_by_label('Date to return', exact=False).input_value() == '2026-11-03'
    assert notes.locator('img').count() == 0
    with page.expect_download() as download_info:
        notes.get_by_role('button', name='Download these notes').click()
    downloaded = Path(download_info.value.path()).read_text()
    assert sample in downloaded and '2026-11-03' in downloaded
    assert 'A late arrival' not in downloaded
    # Print mirrors include long text in closed notes; screen textareas may scroll.
    long_note = 'A longer observation. ' * 200
    notes.get_by_label('What did I notice, ask or try?', exact=True).fill(long_note)
    notes.locator('summary').click()
    page.locator('details.more-practice').evaluate('e => e.open = false')
    page.emulate_media(media='print')
    mirror = notes.locator('[name=action] + .notes-print-value')
    assert mirror.is_visible() and mirror.inner_text().strip() == long_note.strip()
    assert notes.locator('[name=action]').is_hidden()
    assert notes.locator('.notes-controls').is_hidden()
    assert page.locator('.practice-check .answer-check').first.locator('li').first.is_visible()
    assert page.locator('.practice-check .answer-check').nth(1).locator('p').first.is_visible()
    page.pdf(path='/tmp/understanding-people-practice.pdf', format='A4')
    page.emulate_media(media='screen', color_scheme='dark')
    reveal_more(page)
    notes.locator('summary').click()
    assert notes.get_by_label('What happened?', exact=True).is_visible()
    page.screenshot(path='/tmp/practice-dark.png', full_page=False)
    page.emulate_media(color_scheme='light')
    # Cancelled deletion preserves notes. Confirmed deletion touches only one key.
    page.once('dialog', lambda dialog: dialog.dismiss())
    notes.get_by_role('button', name='Delete these notes').click()
    assert notes.get_by_label('What happened?', exact=True).input_value() == sample
    page.once('dialog', lambda dialog: dialog.accept())
    notes.get_by_role('button', name='Delete these notes').click()
    assert notes.get_by_label('What happened?', exact=True).input_value() == ''
    assert page.evaluate("localStorage.getItem('another-book')") == 'leave me alone'
    page.reload()
    reveal_more(page)
    notes.locator('summary').click()
    assert notes.get_by_label('What happened?', exact=True).input_value() == ''
    other.locator('summary').click()
    assert other.get_by_label('What happened?', exact=True).input_value().startswith('A late arrival')
    # Broken records do not crash the book or get interpreted as markup.
    key = page.evaluate("Object.keys(localStorage).find(k => k.includes('week-01-correspondence'))")
    page.evaluate('key => localStorage.setItem(key, "broken json")', key)
    page.reload()
    reveal_more(page)
    other.locator('summary').click()
    assert 'could not be loaded' in other.locator('[role=status]').inner_text()
    # Blocked access and full storage are visible failures; export still works.
    for setup in [
        "Object.defineProperty(window, 'localStorage', {get() {throw new Error('blocked')}})",
        "Storage.prototype.setItem = () => {throw new Error('quota')}"
    ]:
        blocked = browser.new_context(accept_downloads=True, service_workers='block')
        blocked.add_init_script(setup)
        bp = blocked.new_page(); bp.goto(first); reveal_more(bp)
        bn = bp.locator('[data-notes-id="week-01-confirmation"]'); bn.locator('summary').click()
        bn.get_by_label('What happened?', exact=True).fill('Keep this unsaved note.')
        assert 'could not be saved' in bn.locator('[role=status]').inner_text()
        with bp.expect_download() as di:
            bn.get_by_role('button', name='Download these notes').click()
        assert 'Keep this unsaved note.' in Path(di.value.path()).read_text()
        blocked.close()
    # Without JS, the writing space and printable prompts remain, with honest guidance.
    nojs = browser.new_context(java_script_enabled=False, service_workers='block')
    np = nojs.new_page(); np.goto(first); reveal_more(np)
    nn = np.locator('[data-notes-id="week-01-confirmation"]'); nn.locator('summary').click()
    assert nn.locator('noscript').is_visible()
    assert nn.get_by_label('What happened?', exact=True).is_visible()
    assert nn.locator('.notes-controls').is_hidden()
    nojs.close()
    # Once cached online, notes also save and reload offline.
    offline = browser.new_context()
    op = offline.new_page(); op.goto(first); reveal_more(op)
    op.evaluate('navigator.serviceWorker.ready')
    op.wait_for_function('navigator.serviceWorker.controller !== null')
    offline.set_offline(True)
    op.reload(); reveal_more(op)
    on = op.locator('[data-notes-id="week-01-confirmation"]'); on.locator('summary').click()
    on.get_by_label('What happened?', exact=True).fill('Written offline.')
    op.reload(); reveal_more(op); on.locator('summary').click()
    assert on.get_by_label('What happened?', exact=True).input_value() == 'Written offline.'
    assert not errors, errors
    browser.close()
print('Passed: 12 chapter checks (35 answer reveals), 6 later recalls, 13 weekly exercises and the three-question practice; keyboard, local notes, export/delete, storage failures, no-JS, offline, responsive and print checks.')
