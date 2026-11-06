#!/usr/bin/env python3
"""Check the reading layout and progressive-enhancement audio interface."""
import argparse
import functools
import json
import os
import threading
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright, expect
from page_narration import ROOT
from verify_page_narration import RangeHandler, ThreadingHTTPServer


def luminance(rgb):
    values = [v/255 for v in rgb]
    return sum(weight*(v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4)
               for v, weight in zip(values, [.2126, .7152, .0722]))


def verify(base, screenshots=False):
    base = base.rstrip('/') + '/'
    routes = ['index.html', 'chapters/01-before-you-explain.html', 'reference/deception.html',
              'reference/confirmation-bias.html', 'reference/index.html', 'settings.html',
              'worksheet.html', 'chapters/12-putting-understanding-to-work.html']
    errors, unexpected, media = [], [], []
    metrics = []
    with sync_playwright() as pw:
        proxy = {'server': os.environ['HTTPS_PROXY']} if base.startswith('https://') and os.environ.get('HTTPS_PROXY') else None
        browser = pw.chromium.launch(proxy=proxy)
        context = browser.new_context(proxy=proxy, service_workers='block')
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda r: unexpected.append(r.url) if urlsplit(r.url).netloc and urlsplit(r.url).netloc != urlsplit(base).netloc else None)
        page.on('request', lambda r: media.append(r.url) if urlsplit(r.url).path.endswith('.mp3') else None)
        for route in routes:
            page.goto(base + route)
            page.evaluate('document.fonts.ready')
            loaded = page.evaluate('Array.from(document.fonts).filter(f=>f.status==="loaded").map(f=>f.family)')
            assert 'Newsreader' in loaded and 'Public Sans' in loaded, (route, loaded)
            for width in [320, 390, 834, 1024, 1440]:
                for scheme in ['light', 'dark']:
                    page.set_viewport_size({'width': width, 'height': 1000})
                    page.emulate_media(color_scheme=scheme)
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), (route, width, scheme)
                    if width <= 1050:
                        expect(page.locator('.book-sidebar')).to_be_hidden()
                        expect(page.locator('.mobile-nav > summary')).to_be_visible()
                    else:
                        expect(page.locator('.book-sidebar')).to_be_visible()
                    panel = page.locator('.page-narration')
                    if panel.count():
                        expect(panel.locator('[data-player-toggle]')).to_be_visible()
                        expect(panel.locator('audio')).to_be_hidden()
                        expect(panel.locator('audio')).to_have_attribute('preload', 'none')
                        height = panel.bounding_box()['height']
                        assert height <= (250 if width < 600 else 200), (route, width, height)
                        if route == 'reference/deception.html':
                            reading = page.locator('.prose').bounding_box()['y']
                            assert reading < (750 if width == 320 else 700), (width, reading)
                            metrics.append({'width': width, 'scheme': scheme, 'player_height': round(height,1), 'reading_top': round(reading,1)})
                    colors = page.evaluate('''()=>{const get=(e,p)=>getComputedStyle(e)[p].match(/[\\d.]+/g).slice(0,3).map(Number);return [get(document.body,'color'),get(document.body,'backgroundColor')]}''')
                    contrast = (max(map(luminance, colors))+.05)/(min(map(luminance, colors))+.05)
                    assert contrast >= 7, (route, scheme, contrast)
                    if screenshots and route in ['index.html', 'reference/deception.html', 'settings.html', 'reference/index.html'] and width in [390, 834, 1440]:
                        name = Path(route).stem
                        page.screenshot(path=f'/tmp/course-{name}-{width}-{scheme}.png', full_page=False)
            print('Passed reading layouts:', route, flush=True)
        assert not media, media
        assert not unexpected, unexpected
        # The compact controls must be real controls, including a cold keyboard seek.
        page.goto(base + 'reference/deception.html')
        page.set_viewport_size({'width': 834, 'height': 1000})
        panel = page.locator('.page-narration')
        slider = panel.get_by_role('slider', name='Lesson playback position')
        slider.focus()
        page.keyboard.press('ArrowRight')
        expect(panel.locator('[data-player-elapsed]')).to_have_text('0:01')
        assert not media, media
        toggle = panel.get_by_role('button', name='Play lesson', exact=True)
        toggle.focus()
        page.keyboard.press('Space')
        page.wait_for_function('(()=>{const a=document.querySelector("#page-narration-audio");return !a.paused&&a.currentTime>=1&&a.currentTime<8})()')
        pause = panel.get_by_role('button', name='Pause lesson', exact=True)
        expect(pause).to_be_visible()
        pause.focus()
        page.keyboard.press('Space')
        assert panel.locator('audio').evaluate('e=>e.paused')
        panel.get_by_role('button', name='Mute lesson', exact=True).click()
        assert panel.locator('audio').evaluate('e=>e.muted')
        panel.get_by_role('button', name='Unmute lesson', exact=True).click()
        assert not panel.locator('audio').evaluate('e=>e.muted')
        # Cold seeking and opening a disclosure must not fetch an unplayed edition.
        page.get_by_label('Narration voice', exact=True).select_option('jenny')
        variants = json.loads(panel.locator('.narration-variants').text_content())
        assert abs(float(slider.get_attribute('max')) - variants['jenny']['seconds']) < .001
        panel.locator('.narration-sections > summary').click()
        expect(panel.get_by_role('link', name='Download MP3', exact=True)).to_be_visible()
        expect(panel.get_by_role('link', name='Voice settings', exact=True)).to_be_visible()
        assert panel.locator('audio').evaluate('e=>e.paused')
        # Native controls and all reading content are available without enhancement.
        nojs = browser.new_context(proxy=proxy, service_workers='block', java_script_enabled=False, viewport={'width': 390, 'height': 1000})
        n = nojs.new_page()
        n.goto(base + 'reference/deception.html')
        expect(n.locator('.page-narration audio')).to_be_visible()
        expect(n.locator('.lesson-transport')).to_be_hidden()
        expect(n.get_by_role('link', name='Download Jenny MP3', exact=True)).to_be_visible()
        n.locator('.narration-sections > summary').click()
        expect(n.get_by_role('link', name='Download MP3', exact=True)).to_be_visible()
        failed = browser.new_context(proxy=proxy, service_workers='block')
        failed.route('**/assets/media/narration/**', lambda route: route.abort())
        f = failed.new_page()
        f.goto(base + 'reference/deception.html')
        f.get_by_role('button', name='Play lesson', exact=True).click()
        expect(f.locator('.audio-status')).to_be_visible()
        expect(f.locator('.audio-status')).to_contain_text('Audio could not load')
        expect(f.get_by_role('link', name='Download MP3', exact=True)).to_be_visible()
        expect(f.get_by_role('link', name='Read transcript', exact=True)).to_be_visible()
        # Print removes transport/navigation while retaining the explanation.
        page.emulate_media(media='print')
        expect(panel).to_be_hidden()
        expect(page.locator('.prose')).to_be_visible()
        expect(page.locator('.site-header')).to_be_hidden()
        assert not errors, errors
        browser.close()
    print(json.dumps(metrics, indent=2))
    print('Passed: self-hosted typography, eight page types at five widths in light/dark modes, compact player/visible reading, tablet navigation, text contrast, no external requests or unsolicited audio, keyboard play/pause/cold seeking, mute, voice-specific progress, advanced resources, native no-JavaScript fallback and print.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base', nargs='?')
    parser.add_argument('--screenshots', action='store_true')
    args = parser.parse_args()
    if args.base:
        verify(args.base, args.screenshots)
    else:
        server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(RangeHandler, directory=str(ROOT / '_site')))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            verify(f'http://localhost:{server.server_port}/understanding-people/', args.screenshots)
        finally:
            server.shutdown()
