"""Record final audio provenance; run only after producing the MP3s."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
def write_metadata():
 source=ROOT/'audio/chapter-01.json';d=json.loads(source.read_text());result={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'voice':d['voice'],'rate':d['rate'],'editions':{}}
 for name in ['full','refresher']:
  f=ROOT/f'assets/media/audio/chapter-01/{name}.mp3';duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(f)],text=True));minutes,seconds=divmod(round(duration),60)
  result['editions'][name]={'seconds':duration,'label':f'{minutes} min {seconds:02d} sec','sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'words':len(' '.join(d[name]).split())}
 (ROOT/'audio/manifest.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':write_metadata()
