"""Check the published exercise, exact replay, player and answer persistence."""
import hashlib,json,subprocess,sys
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];base=sys.argv[1].rstrip('/')+'/'
m=json.loads((ROOT/'audio/confirmation-bias-manifest.json').read_text());timeline={s['id']:s for s in m['timeline']}
assert timeline['message']['segment_sha256']==timeline['replay']['segment_sha256']
assert 180<m['duration']<240
subprocess.run(['ffmpeg','-v','error','-i',str(ROOT/'assets/media/audio/confirmation-bias-exercise/exercise.mp3'),'-f','null','-'],check=True)
with sync_playwright() as pw:
 b=pw.chromium.launch();p=b.new_page(service_workers='block');errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
 p.goto(base+'reference/confirmation-bias.html')
 p.evaluate('''() => localStorage.setItem('understanding-people:practice:v1:/understanding-people/:confirmation-listening', JSON.stringify({version:1,fields:{date:'',event:'Earlier listening note',thought:'Existing comparison',action:'Listen again',review:'Keep an open question'}}))''')
 p.reload();p.locator('.reference-listenings a[href="#listen-exercise"]').click()
 expect(p.locator('#listening-exercise')).to_have_attribute('preload','none');expect(p.locator('#listening-exercise')).to_have_attribute('controls','')
 assert p.locator('[data-notes-id="confirmation-listening"] textarea').count()==4
 audio=p.locator('#listening-exercise');audio.evaluate('e=>e.load()');p.wait_for_function('document.querySelector("#listening-exercise").readyState>=1')
 assert abs(audio.evaluate('e=>e.duration')-m['duration'])<.2
 audio.evaluate('e=>e.play()');p.wait_for_function('document.querySelector("#listening-exercise").currentTime>0');audio.evaluate('e=>e.pause()')
 audio.evaluate('(e,start)=>e.currentTime=start',timeline['replay']['start']);p.wait_for_function('(start)=>Math.abs(document.querySelector("#listening-exercise").currentTime-start)<.2',arg=timeline['replay']['start'])
 expect(p.locator('#listen-exercise')).to_have_attribute('open','')
 expect(p.locator('#confirmation-listening-event')).to_have_value('Earlier listening note')
 note=p.locator('#confirmation-listening-event');note.fill('The request supports “asking today”. <img src=x>');p.reload();expect(note).to_have_value('The request supports “asking today”. <img src=x>')
 assert p.locator('.practice-notes img').count()==0
 for width in [320,390,1024,1440]:
  p.set_viewport_size({'width':width,'height':950});assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
  if width in [390,1440]:
   p.evaluate('scrollTo(0,0)');p.screenshot(path=f'/tmp/book-listening-{width}.png',full_page=False)
 assert not errors,errors
 b.close()
print('Passed: exact replay, 3:50 audio decode/play/seek, optional loading, transcript links, saved answers/reload and responsive layout.')
