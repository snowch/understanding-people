"""Build output under the Pages subpath; audio, transcript, notes and responsive checks."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
import tempfile,json
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def copyfile(self,source,outputfile):
  try:super().copyfile(source,outputfile)
  except (BrokenPipeError,ConnectionResetError):pass
with tempfile.TemporaryDirectory() as folder:
 Path(folder,'understanding-people').symlink_to(ROOT/'_site',target_is_directory=True)
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=folder));Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as p:
   b=p.chromium.launch();page=b.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));base=f'http://127.0.0.1:{server.server_port}/understanding-people/'
   page.goto(base+'audio/chapter-01.html')
   for name,info in json.loads((ROOT/'audio/manifest.json').read_text())['editions'].items():
    expected=info['seconds']
    player=page.locator('#audio-'+name);page.locator('[data-audio-speed="audio-'+name+'"]').select_option('1.25');player.evaluate('(a)=>a.load()')
    page.wait_for_function('id=>document.getElementById(id).readyState>=1',arg='audio-'+name)
    duration=player.evaluate('(a)=>a.duration');assert abs(duration-expected)<.2,duration
    page.locator('[data-audio-speed="audio-'+name+'"]').select_option('1.5');assert player.evaluate('(a)=>a.playbackRate')==1.5
    player.evaluate('(a)=>a.play()');page.wait_for_function('id=>document.getElementById(id).currentTime>0',arg='audio-'+name);player.evaluate('(a)=>a.pause()')
   page.get_by_text('Read the short refresher transcript',exact=True).click();expect(page.locator('main')).to_contain_text('What did they say or do?')
   for width in [390,1280]:
    page.set_viewport_size({'width':width,'height':1000});page.goto(base+'audio/chapter-01.html');page.screenshot(path=f'/workspace/book-audio-{width}.png');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   page.goto(base+'reference/declining-help.html');expect(page.locator('main')).to_contain_text('A fictional example that changes as you learn')
   page.locator('[data-notes-id="declining-help-pilot"] summary').click();page.locator('#declining-help-pilot-review').fill('A respectful no was useful. I stopped pressing.');page.reload();page.locator('[data-notes-id="declining-help-pilot"] summary').click();expect(page.locator('#declining-help-pilot-review')).to_have_value('A respectful no was useful. I stopped pressing.')
   page.locator('[data-notes-id="declining-help-pilot"] summary').click();page.screenshot(path='/workspace/book-pilot-reference.png')
   page.goto(base+'chapters/01-before-you-explain.html');expect(page.locator('#chapter-audio')).to_have_attribute('preload','none');expect(page.get_by_role('link',name='Transcript & short refresher')).to_be_visible()
   assert not errors,errors
   b.close()
 finally:server.shutdown()
print('Passed: real MP3 metadata/playback/speed, transcripts, Pages subpath URLs, reference notes persistence and phone/desktop rendering.')
