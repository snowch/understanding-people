"""Render the reading-preferences utility page; it is not a narrated lesson."""
import json
from html import escape
from narration_voices import DEFAULT, VOICES, media_path


def render(editions):
    if not editions:
        return '<p>Reading preferences will be available in the completed build.</p>'
    sample = 'chapters/01-before-you-explain.md'
    previews, cards = {}, []
    for voice, edition in editions.items():
        info = VOICES[voice]
        entry = edition['pages'][sample]
        previews[voice] = {'name': info['name'], 'audio': media_path(sample, '.mp3', voice).as_posix() + '?v=' + entry['audio_sha256'][:12]}
        cards.append(f'''<div class="voice-option"><label><input type="radio" name="narrator" value="{voice}" {'checked' if voice == DEFAULT else ''}><span><strong>{escape(info['name'])}</strong><small>US English · {'Original narrator' if voice == DEFAULT else 'Second narrator'}</small></span></label><button type="button" data-preview-voice="{voice}">Preview {escape(info['name'])}</button></div>''')
    samples = ''.join(f'<a href="{escape(v["audio"], quote=True)}">Listen to {escape(v["name"])}</a> ' for v in previews.values())
    payload = json.dumps(previews).replace('<', '\\u003c')
    return f'''<section class="book-preferences" aria-label="Reading preferences">
<a class="settings-back" data-reading-return href="index.html">← Back to reading</a>
<fieldset data-settings-controls disabled><legend>Narrator</legend><p class="settings-help">Choose the voice you would like across the book. Preview either voice before deciding.</p><div class="voice-options">{''.join(cards)}</div>
<div class="voice-preview" hidden><h3>Voice preview · <span data-preview-name>Andrew</span></h3><p>A short sample from Chapter 1. Previewing does not change your choice.</p><audio id="voice-preview" controls preload="none" aria-label="Voice preview"></audio><p data-preview-status role="status"></p></div>
<div class="speed-setting"><label for="reading-speed">Playback speed</label><p id="speed-help">The starting speed for each lesson. You can also change it while listening.</p><select id="reading-speed" aria-describedby="speed-help"><option value="0.75">0.75× · Slower</option><option value="1" selected>1× · Normal</option><option value="1.25">1.25×</option><option value="1.5">1.5×</option><option value="2">2×</option></select></div>
<button type="button" data-settings-reset>Restore defaults</button></fieldset>
<p class="settings-status" data-settings-status role="status" aria-live="polite">Preferences save automatically in this browser on this device.</p>
<noscript><p>Saving voice preferences needs JavaScript. You can still listen to either Chapter 1 recording: {samples}Each lesson also offers a Jenny download alongside its native Andrew player.</p></noscript>
<details class="settings-about"><summary>About the recordings</summary><p>Both are synthetic voices reading the same authored lesson, with pauses for reflection. Research references and longer exercises stay on the written page. Voice choice changes the main lesson player; the two older optional confirmation-bias recordings keep their original voices.</p><p>Andrew: <code>en-US-AndrewMultilingualNeural</code><br>Jenny: <code>en-US-JennyNeural</code></p><p>Preferences are stored locally. They do not sync between devices, and clearing browser data removes them. Restoring defaults does not delete your practice notes.</p></details>
<script type="application/json" id="voice-previews">{payload}</script>
</section>'''
