"""Produce the optional listening exercise. Requires edge-tts and FFmpeg.
Only the authored script is sent to speech synthesis. Cache stays outside the repo.
The replay reuses exactly the same message segment.
"""
import asyncio, hashlib, json, os, subprocess
from pathlib import Path
import edge_tts
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'audio/confirmation-bias-exercise.json'
OUT=ROOT/'assets/media/audio/confirmation-bias-exercise'
CACHE=Path(os.environ.get('LISTENING_AUDIO_CACHE','/workspace/listening-audio-cache'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def duration(p):return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(p)],text=True).strip())
def norm(s):return ''.join(c.lower() for c in s if c.isalnum())
async def main():
 d=json.loads(SOURCE.read_text());CACHE.mkdir(exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
 paths={};timeline=[];transcript=[];elapsed=0
 for s in d['segments']:
  if 'repeat' in s:
   path=paths[s['repeat']];text=next(t['text'] for t in d['segments'] if t['id']==s['repeat']);transcript.append('[Same message replayed]\n'+text)
  elif 'pause' in s:
   path=CACHE/f"silence-{s['pause']}.wav"
   subprocess.run(['ffmpeg','-loglevel','error','-y','-f','lavfi','-i','anullsrc=r=24000:cl=mono','-t',str(s['pause']),str(path)],check=True)
   transcript.append(f"[Pause: {s['pause']} seconds. Pause the player for longer if needed.]")
  else:
   voice=s.get('voice',d['voice']);text=s['text'];key=hashlib.sha256((voice+d['rate']+text).encode()).hexdigest();mp3=CACHE/(key+'.mp3');meta=CACHE/(key+'.json');path=CACHE/(key+'.wav')
   if not mp3.exists() or not meta.exists():
    words=[]
    with mp3.open('wb') as f:
     async for item in edge_tts.Communicate(text,voice=voice,rate=d['rate'],boundary='WordBoundary',proxy=os.environ.get('HTTPS_PROXY')).stream():
      if item['type']=='audio':f.write(item['data'])
      elif item['type']=='WordBoundary':words.append(item['text'])
    assert norm(''.join(words))==norm(text),(s['id'],'word boundary mismatch')
    meta.write_text(json.dumps({'text':text,'words':words}))
   assert norm(''.join(json.loads(meta.read_text())['words']))==norm(text)
   subprocess.run(['ffmpeg','-loglevel','error','-y','-i',str(mp3),'-ar','24000','-ac','1',str(path)],check=True)
   transcript.append(('Alex: ' if s['id']=='message' else 'Narrator: ')+text)
  paths[s['id']]=path;seconds=duration(path)
  timeline.append({'id':s['id'],'start':round(elapsed,3),'duration':seconds,'segment_sha256':sha(path)})
  elapsed+=seconds;print(s['id'],round(seconds,1),flush=True)
 listing=CACHE/'concat.txt';listing.write_text(''.join("file '"+str(paths[s['id']])+"'\n" for s in d['segments']))
 audio=OUT/'exercise.mp3'
 subprocess.run(['ffmpeg','-loglevel','error','-y','-f','concat','-safe','0','-i',str(listing),'-af','loudnorm=I=-16:TP=-1.5:LRA=11','-ar','24000','-ac','1','-b:a','96k','-metadata','title='+d['title'],'-metadata','artist=Understanding people','-metadata','copyright=© 2026 Christopher Snow',str(audio)],check=True)
 (OUT/'transcript.txt').write_text(d['title']+'\nFictional example · Synthetic narration\n\n'+'\n\n'.join(transcript)+'\n')
 manifest={'source_sha256':sha(SOURCE),'audio_sha256':sha(audio),'duration':duration(audio),'timeline':timeline}
 (ROOT/'audio/confirmation-bias-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('Finished',manifest['duration'],flush=True)
if __name__=='__main__':asyncio.run(main())
