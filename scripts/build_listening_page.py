"""Publish a transcript and answer sheet from the exact narrated source."""
import hashlib, json
from html import escape
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def render():
 source=ROOT/'audio/confirmation-bias-exercise.json';d=json.loads(source.read_text())
 m=json.loads((ROOT/'audio/confirmation-bias-manifest.json').read_text())
 assert hashlib.sha256(source.read_bytes()).hexdigest()==m['source_sha256'],'Regenerate listening audio after script changes'
 audio=ROOT/'assets/media/audio/confirmation-bias-exercise/exercise.mp3'
 assert hashlib.sha256(audio.read_bytes()).hexdigest()==m['audio_sha256'],'Listening audio checksum mismatch'
 duration=round(m['duration']);label=f'{duration//60}:{duration%60:02}'
 parts=['# '+d['title'],'A guided listening exercise: hear a message, record what you noticed, then listen again. Practise checking a belief without forcing a favourable interpretation.','[Read the confirmation-bias reference](../reference/confirmation-bias.md) · [Listen to the detailed explanation](confirmation-bias-explained.md).',f'''<section class="audio-edition" aria-label="Guided listening exercise">
<p class="audio-note">{label} · Fictional example · Synthetic narration</p>
<audio id="listening-exercise" controls preload="none" aria-label="Confirmation bias listening exercise"><source src="../assets/media/audio/confirmation-bias-exercise/exercise.mp3" type="audio/mpeg"></audio>
<div class="audio-links"><a href="../assets/media/audio/confirmation-bias-exercise/exercise.mp3" download>Download MP3</a><a href="../assets/media/audio/confirmation-bias-exercise/transcript.txt">Plain-text transcript</a></div>
</section>''','## Before you press play','Imagine you suspect: **“Alex only contacts me when they need something.”** Listen before opening the transcript or review below. After the first message, write both the supporting details and the details that make the belief less certain. Leave those answers unchanged when you add your second-listen notes.','There are two 15-second pauses. **Pause the player for as long as you need.** You can use the notes below or paper. If listening is difficult, use the transcript one section at a time; the comparison is the same.','<!-- practice-notes: confirmation-listening | What did I notice? -->','<details markdown="1"><summary>Transcript and review — open after your first listen, or use instead of audio</summary>']
 for s in d['segments']:
  if 'pause' in s:parts+=['*Pause for '+str(s['pause'])+' seconds, or longer.*']
  elif 'repeat' in s:parts+=['### The same message, replayed',next(t['text'] for t in d['segments'] if t['id']==s['repeat'])]
  else:parts+=['### '+('Alex’s message' if s['id']=='message' else {'intro':'Set up','first-check':'First comparison','replay-intro':'Listen again','second-check':'Second comparison','review':'Review'}[s['id']]),s['text']]
 parts+=['</details>','## Try it in your own life','Choose one belief about an ordinary interaction. Write a specific observation that supports it and one that could challenge it. If either is unknown, leave it unknown. Decide on one fair check, then return to what actually happened.','In the [private app, version 0.16.0 or later](https://github.com/snowch/understanding-people-app/releases/tag/v0.16.0), open **Confirmation bias → Read the full entry → Save exercise answers in the app**. Save the four answers in My situations, then choose a next step. The transcript works offline in the app; the recording opens on this website. Book and app notes are separate.','## What this exercise can tell you','This is an authored practice activity, not a validated assessment or evidence that listening once changes a lasting habit. Remembering different details on a second listen does not by itself demonstrate confirmation bias. Compare **how you judged the information**, not just what you remembered.','For the research and its limits, see [why confirmation bias happens and what may help](../reference/confirmation-bias.md).']
 page='\n\n'.join(parts)+'\n';(ROOT/'audio/confirmation-bias-exercise.md').write_text(page)
if __name__=='__main__':render()
