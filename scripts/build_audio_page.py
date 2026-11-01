"""Generate the audio transcript page from the authored narration source."""
from pathlib import Path
import json,hashlib
book=Path(__file__).resolve().parents[1]
def render():
    manifest=json.loads((book/'audio/manifest.json').read_text())
    assert hashlib.sha256((book/'audio/chapter-01.json').read_bytes()).hexdigest()==manifest['source_sha256'], 'Audio narration changed: regenerate audio before publishing.'
    for edition,info in manifest['editions'].items():
        assert hashlib.sha256((book/f'assets/media/audio/chapter-01/{edition}.mp3').read_bytes()).hexdigest()==info['sha256'], 'Audio checksum mismatch'
    d=json.loads((book/'audio/chapter-01.json').read_text())
    parts=['# Listen: Why we misinterpret people','An audio adaptation of Chapter 1, with a short refresher. Synthetic narration uses the same British English voice as the chapter video. The examples are fictional. These recordings work without the illustrations.','[Read Chapter 1](../chapters/01-before-you-explain.md) · [Explore declining help](../reference/declining-help.md)']
    for kind,title in [('full','Audio chapter'),('refresher','Short refresher')]:
     parts+=['## '+title,f'''<section class="audio-edition" aria-label="{title}">
    <p class="audio-note">{manifest['editions'][kind]['label']}</p>
<audio id="audio-{kind}" controls preload="none" aria-label="{title}: Why we misinterpret people"><source src="../assets/media/audio/chapter-01/{kind}.mp3" type="audio/mpeg"></audio>
    <div class="audio-links"><a href="../assets/media/audio/chapter-01/{kind}.mp3" download>Download MP3</a><a href="../assets/media/audio/chapter-01/{kind}-transcript.txt">Plain-text transcript</a><select hidden data-audio-speed="audio-{kind}" aria-label="{title} playback speed"><option value="0.75">0.75× speed</option><option value="1" selected>1× speed</option><option value="1.25">1.25× speed</option><option value="1.5">1.5× speed</option><option value="2">2× speed</option></select></div>
    </section>''', '<details markdown="1"><summary>Read the '+title.lower()+' transcript</summary>','\n\n'.join(d[kind]),'</details>']
    parts+=['## Research mentioned in the audio','- [Nickerson (1998): review of confirmation bias](https://doi.org/10.1037/1089-2680.2.2.175).\n- [Gilbert & Malone (1995): review of correspondence bias](https://pubmed.ncbi.nlm.nih.gov/7870861/).\n- [Lord, Lepper & Preston (1984): considering the opposite](https://pubmed.ncbi.nlm.nih.gov/6527215/).\n- [Malle (2006): meta-analysis of actor–observer explanations](https://pubmed.ncbi.nlm.nih.gov/17073526/).\n- [Henrich, Heine & Norenzayan (2010): limits of generalising across populations](https://pubmed.ncbi.nlm.nih.gov/20550733/).','The practice suggestions are editorial applications. The research cannot identify a particular person’s motive. For the refresher’s family example, see the [declining-help reference and its research limits](../reference/declining-help.md).']
    (book/'audio/chapter-01.md').write_text('\n\n'.join(parts)+'\n')

if __name__=="__main__":render()
