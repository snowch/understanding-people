"""Audio is a format of its reference concept; legacy pages only preserve links."""
import hashlib,json,re
from html import escape
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def stamp(seconds):
    seconds=round(seconds)
    return f'{seconds//60}:{seconds%60:02}'

def load(name,manifest,mp3):
    source=ROOT/f'audio/{name}.json';d=json.loads(source.read_text());m=json.loads((ROOT/f'audio/{manifest}.json').read_text())
    assert hashlib.sha256(source.read_bytes()).hexdigest()==m['source_sha256'], 'Regenerate audio after narration changes'
    assert hashlib.sha256((ROOT/mp3).read_bytes()).hexdigest()==m['audio_sha256'], 'Audio checksum mismatch'
    return d,m

def player(player_id,folder,filename,label,duration,speed=False,voices=()):
    media='../assets/media/audio/'+folder+'/'
    speakers=' and '.join(re.sub(r'(?:Multilingual)?Neural$', '', voice.split('-',2)[-1]) for voice in voices)
    return f'''<section class="audio-edition" aria-label="{escape(label,quote=True)}">
<p class="audio-note">{stamp(duration)} · {escape(speakers)+' · ' if speakers else ''}Synthetic narration · Examples are fictional</p>
<audio id="{player_id}" controls preload="none" aria-label="{escape(label,quote=True)}"><source src="{media+filename}" type="audio/mpeg"></audio>
<div class="audio-links"><a href="{media+filename}" download>Download MP3</a><a href="{media}transcript.txt">Plain-text transcript</a>{f'<select hidden data-audio-speed="{player_id}" aria-label="Playback speed"><option value="0.75">0.75× speed</option><option value="1" selected>1× speed</option><option value="1.25">1.25× speed</option><option value="1.5">1.5× speed</option></select>' if speed else ''}</div>
<p class="audio-status" role="status"></p>
</section>'''

def formats():
    d,m=load('confirmation-bias-explained','confirmation-bias-explained-manifest','assets/media/audio/confirmation-bias-explained/explanation.mp3')
    exercise,em=load('confirmation-bias-exercise','confirmation-bias-manifest','assets/media/audio/confirmation-bias-exercise/exercise.mp3')
    sources=json.loads((ROOT/'reference/biases.json').read_text())['sources'];timeline={s['id']:s for s in m['timeline']}
    catalogue=next(e for e in json.loads((ROOT/'reference/biases.json').read_text())['entries'] if e['id']=='confirmation')['listenings']
    assert [a['duration'] for a in catalogue]==[stamp(m['duration']),stamp(em['duration'])], 'Update recording durations in shared metadata'
    listen=['<section class="reference-listenings" markdown="1" aria-labelledby="listen">','## Listen {#listen}','### Detailed explanation {#listen-explanation}',
            'Why confirmation bias happens, how to notice an uneven test, and what can help. Audio loads when you choose to play or select a recording section.',
            player('audio-explanation','confirmation-bias-explained','explanation.mp3','Detailed explanation of confirmation bias',m['duration'],True,voices=(d['voice'],)),
            '[Try the guided listening exercise · '+stamp(em['duration'])+'](#listen-exercise).',
            '<details class="evidence-detail" markdown="1" id="explanation-transcript"><summary>Recording sections, transcript and research</summary>',
            'Select a time to listen from that section, or read its transcript below.',
            '<ol class="audio-chapters">'+''.join(f'<li><button hidden data-audio-seek="audio-explanation" data-start="{timeline[s["id"]]["start"]}" aria-label="Listen from {escape(s["title"],quote=True)}">{stamp(timeline[s["id"]]["start"])} · {escape(s["title"])}</button><a href="#audio-{s["id"]}">Read {escape(s["title"].lower())}</a></li>' for s in d['segments'])+'</ol>',
            '<noscript><p>Section playback buttons and speed selection need JavaScript. The native player, transcript and download work without it.</p></noscript>']
    for s in d['segments']:
        listen+=['#### '+s['title']+' {#audio-'+s['id']+'}',s['text']]
        if s['sources']:listen+=['**Research behind this section:** '+ '; '.join('['+sources[k]['title']+']('+sources[k]['url']+') '+sources[k]['scope'] for k in s['sources'])]
    listen+=['</details>','</section>']
    practice=['<details class="evidence-detail audio-exercise" markdown="1" id="listen-exercise"><summary>Optional guided listening exercise · '+stamp(em['duration'])+'</summary>',
              'Hear the same fictional message twice. Compare the evidence you noticed and the evidence you dismissed.',
              player('listening-exercise','confirmation-bias-exercise','exercise.mp3','Confirmation bias listening exercise',em['duration'],voices=(exercise['voice'],exercise['message_voice'])),
              'Imagine you suspect: **“Alex only contacts me when they need something.”** Listen before opening the transcript below. After the first message, write both the supporting details and the details that make the belief less certain. Leave those answers unchanged when adding your second-listen notes.',
              'There are two 15-second pauses. **Pause the player for as long as you need.** Use the notes below or paper. If listening is difficult, read the transcript one section at a time.',
              '<!-- practice-notes: confirmation-listening | What did I notice? -->',
              '<details class="evidence-detail" markdown="1" id="exercise-transcript"><summary>Exercise transcript and review — open after your first listen, or use instead of audio</summary>']
    titles={'intro':'Set up','message':'Alex’s message','first-check':'First comparison','replay-intro':'Listen again','second-check':'Second comparison','review':'Review'}
    for s in exercise['segments']:
        if 'pause' in s:practice+=['*Pause for '+str(s['pause'])+' seconds, or longer.*']
        elif 'repeat' in s:practice+=['#### The same message, replayed',next(t['text'] for t in exercise['segments'] if t['id']==s['repeat'])]
        else:practice+=['#### '+titles[s['id']],s['text']]
    practice+=['</details>','This is authored practice, not a validated assessment. Missing a detail alone does not demonstrate confirmation bias. Compare how fairly you judged supporting and challenging information.','</details>']
    return listen,practice

def legacy_page(kind):
    target='listen-explanation' if kind=='explained' else 'listen-exercise'
    title='Confirmation bias '+('explained' if kind=='explained' else 'listening exercise')
    return '\n\n'.join(['# '+title,'This recording, transcript and practice now belong to the Confirmation bias reference entry.',f'<p><a data-audio-redirect="{target}" href="../reference/confirmation-bias.html#{target}">Open the recording on the Confirmation bias page →</a></p>', '<script defer src="../assets/audio-redirect.js"></script>'])+'\n'

def write_legacy(kind):
    (ROOT/f'audio/confirmation-bias-{kind}.md').write_text(legacy_page(kind))
