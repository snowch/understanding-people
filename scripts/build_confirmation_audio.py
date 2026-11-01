"""Build the detailed audio page from the exact narration and verified media."""
from pathlib import Path
from html import escape
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def render():
 source=ROOT/'audio/confirmation-bias-explained.json';d=json.loads(source.read_text());m=json.loads((ROOT/'audio/confirmation-bias-explained-manifest.json').read_text())
 assert hashlib.sha256(source.read_bytes()).hexdigest()==m['source_sha256'],'Regenerate detailed audio after script changes'
 audio=ROOT/'assets/media/audio/confirmation-bias-explained/explanation.mp3'
 assert hashlib.sha256(audio.read_bytes()).hexdigest()==m['audio_sha256'],'Detailed audio checksum mismatch'
 sources=json.loads((ROOT/'reference/biases.json').read_text())['sources'];timeline={s['id']:s for s in m['timeline']}
 def stamp(seconds):
  seconds=int(seconds);return f'{seconds//60}:{seconds%60:02}'
 catalog=json.loads((ROOT/'reference/biases.json').read_text())['entries'][0]['listenings']
 assert catalog[0]['duration']==stamp(round(m['duration'])), 'Update the reference audio duration'
 parts=['# '+d['title'],'Why confirmation bias happens, how to notice an uneven test, and what can help. Brief examples reinforce the concepts; the separate listening exercise gives you something to practise on.','[Back to the confirmation-bias reference](../reference/confirmation-bias.md) · [Try the 3:50 listening exercise](confirmation-bias-exercise.md).',f'''<section class="audio-edition" aria-label="Detailed confirmation-bias explanation">
<p class="audio-note">{stamp(round(m['duration']))} · Synthetic narration · Examples are fictional</p>
<audio id="audio-explanation" controls preload="none" aria-label="Detailed explanation of confirmation bias"><source src="../assets/media/audio/confirmation-bias-explained/explanation.mp3" type="audio/mpeg"></audio>
<div class="audio-links"><a href="../assets/media/audio/confirmation-bias-explained/explanation.mp3" download>Download MP3</a><a href="../assets/media/audio/confirmation-bias-explained/transcript.txt">Plain-text transcript</a><select hidden data-audio-speed="audio-explanation" aria-label="Playback speed"><option value="0.75">0.75× speed</option><option value="1" selected>1× speed</option><option value="1.25">1.25× speed</option><option value="1.5">1.5× speed</option></select></div>
<p class="audio-status" role="status"></p>
</section>''','## In this recording','Choose a time to start listening there. You can also read any section of the transcript below.','<ol class="audio-chapters">'+''.join(f'<li><button hidden data-audio-seek="audio-explanation" data-start="{timeline[s["id"]]["start"]}" aria-label="Listen from {escape(s["title"],quote=True)}">{stamp(timeline[s["id"]]["start"])} · {escape(s["title"])}</button><a href="#{s["id"]}">Read {escape(s["title"].lower())}</a></li>' for s in d['segments'])+'</ol>','<noscript><p>Section playback buttons and speed selection need JavaScript. The audio player, transcript and download still work without it.</p></noscript>','## Transcript and research']
 for s in d['segments']:
  parts+=['### '+s['title']+' {#'+s['id']+'}',s['text']]
  if s['sources']:parts+=['**Research behind this section:** '+ '; '.join('['+sources[key]['title']+']('+sources[key]['url']+') '+sources[key]['scope'] for key in s['sources'])]
 parts+=['## Practise the comparison','[Open the short listening exercise](confirmation-bias-exercise.md) for a fictional message, an identical replay and saved-answer fields. Or use the [reference page’s fair-test practice](../reference/confirmation-bias.md#practice) on an ordinary situation.','The practical routine is an editorial application of the research, not a validated intervention. This recording has not been shown to improve real-life judgment or relationships.','<script src="../assets/audio.js" defer></script>']
 (ROOT/'audio/confirmation-bias-explained.md').write_text('\n\n'.join(parts)+'\n')
if __name__=='__main__':render()
