"""Optional audio production, not part of the Pages build. Needs edge-tts and FFmpeg.
Uses the configured proxy. Only authored public narration is sent for speech.
"""
import asyncio,hashlib,json,os,re,subprocess,sys,tempfile
from pathlib import Path
import edge_tts
ROOT=Path(__file__).resolve().parents[1]
config=json.loads((ROOT/'audio/chapter-01.json').read_text())
cache=Path(os.environ.get('BOOK_AUDIO_CACHE','/workspace/book-audio-cache'));cache.mkdir(exist_ok=True)
out=ROOT/'assets/media/audio/chapter-01';out.mkdir(parents=True,exist_ok=True)
def norm(s):return ''.join(c.lower() for c in s if c.isalnum())
async def main():
 for edition in ['full','refresher']:
  paths=[]
  for i,text in enumerate(config[edition]):
   sig=hashlib.sha256((text+config['voice']+config['rate']).encode()).hexdigest();path=cache/(sig+'.mp3');meta=cache/(sig+'.json')
   if not path.exists() or not meta.exists():
    words=[]
    c=edge_tts.Communicate(text,voice=config['voice'],rate=config['rate'],boundary='WordBoundary',proxy=os.environ.get('HTTPS_PROXY'))
    with path.open('wb') as f:
     async for item in c.stream():
      if item['type']=='audio':f.write(item['data'])
      elif item['type']=='WordBoundary':words.append(item['text'])
    assert norm(''.join(words))==norm(text),(edition,i,'provider boundary mismatch')
    meta.write_text(json.dumps({'text':text,'words':words}));print(edition,i+1,flush=True)
   paths.append(path)
  listing=cache/(edition+'-concat.txt');listing.write_text(''.join("file '"+str(p)+"'\n" for p in paths))
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(listing),'-af','loudnorm=I=-16:TP=-1.5:LRA=11','-ar','24000','-ac','1','-b:a','96k','-metadata','title='+config['title']+(' — refresher' if edition=='refresher' else ''),'-metadata','artist=Understanding people','-metadata','copyright=© 2026 Christopher Snow',str(out/(edition+'.mp3'))],check=True)
  (out/(edition+'-transcript.txt')).write_text(config['title']+'\n'+('Audio chapter' if edition=='full' else 'Short refresher')+' · Synthetic narration: '+config['voice']+'\n\n'+'\n\n'.join(config[edition])+'\n')
  print(edition,'complete',flush=True)
asyncio.run(main())
from audio_metadata import write_metadata
write_metadata()
