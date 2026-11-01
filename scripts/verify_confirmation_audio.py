"""Two reference listening links, detailed playback/chapters and accessible transcripts."""
from pathlib import Path
import json,subprocess,sys
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];base=sys.argv[1].rstrip('/')+'/'
m=json.loads((ROOT/'audio/confirmation-bias-explained-manifest.json').read_text());d=json.loads((ROOT/'audio/confirmation-bias-explained.json').read_text())
assert 8*60<m['duration']<13*60
subprocess.run(['ffmpeg','-v','error','-i',str(ROOT/'assets/media/audio/confirmation-bias-explained/explanation.mp3'),'-f','null','-'],check=True)
with sync_playwright() as pw:
 b=pw.chromium.launch();p=b.new_page(service_workers='block');errors=[];media=[];p.on('pageerror',lambda e:errors.append(str(e)));p.on('request',lambda r:media.append(r.url) if r.url.endswith('.mp3') else None)
 p.goto(base+'reference/confirmation-bias.html');assert p.locator('.reference-listenings a').count()==2
 for width in [320,390,1440]:
  p.set_viewport_size({'width':width,'height':950});assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
  p.locator('#listen').scroll_into_view_if_needed();p.screenshot(path=f'/tmp/reference-audio-links-{width}.png')
 p.emulate_media(color_scheme='dark');p.screenshot(path='/tmp/reference-audio-links-dark.png');p.emulate_media(color_scheme='light')
 p.get_by_role('link',name='Detailed explanation ·').click()
 expect(p.locator('audio')).to_have_attribute('preload','none');assert not media
 expect(p.locator('.audio-chapters button:visible')).to_have_count(len(d['segments']))
 assert len(d['segments'])==8
 # A cold start at a later section must actually seek, rather than play from zero.
 start=m['timeline'][2]['start'];p.locator('[data-audio-seek]').nth(2).click();p.wait_for_function('(start)=>{const a=document.querySelector("audio");return a.readyState>=2&&!a.paused&&a.currentTime>start+.1&&a.currentTime<start+5}',arg=start)
 p.locator('audio').evaluate('e=>e.pause()');assert abs(p.locator('audio').evaluate('e=>e.duration')-m['duration'])<.2
 p.locator('[data-audio-speed]').select_option('1.25');assert p.locator('audio').evaluate('e=>e.playbackRate')==1.25
 p.locator('[data-audio-seek]').first.click();p.wait_for_function('document.querySelector("audio").currentTime<5');p.locator('audio').evaluate('e=>e.pause()')
 for s in d['segments']:assert p.locator('#'+s['id']).count()==1
 assert p.locator('a[href*="10.1037/1089-2680.2.2.175"]').count()>=1
 for width in [320,390,1440]:
  p.set_viewport_size({'width':width,'height':950});assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');p.evaluate('scrollTo(0,0)')
  p.screenshot(path=f'/tmp/confirmation-audio-{width}.png')
 nojs=b.new_context(java_script_enabled=False);q=nojs.new_page();q.goto(base+'audio/confirmation-bias-explained.html');expect(q.locator('audio')).to_be_visible();assert q.locator('[data-audio-seek]:visible').count()==0;expect(q.locator('#meaning')).to_be_visible();expect(q.get_by_role('link',name='Download MP3',exact=True)).to_be_visible()
 assert not errors,errors;b.close()
print('Passed: two reference audio links, no automatic MP3 loading, chapter seek from cold start, playback speed, transcript/source links, no-JS fallback and phone/desktop layouts.')
