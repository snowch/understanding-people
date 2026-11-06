// Playback speed is optional; native audio controls work without JavaScript.
function revealAudioSection() {
 let fragment;
 try{fragment=decodeURIComponent(location.hash.slice(1));}catch{return;}
 const target=document.getElementById(fragment);
 if(!target)return;
 let parent=target;
 while(parent){if(parent.tagName==='DETAILS')parent.open=true;parent=parent.parentElement;}
 target.scrollIntoView();
}
window.addEventListener('hashchange',revealAudioSection);
if(location.hash)revealAudioSection();
// One pending seek per player: switching narrator cannot leave an old callback.
const pendingSeeks=new WeakMap();
const playbackRequests=new WeakMap();
function nextPlaybackRequest(player){const token=(playbackRequests.get(player)||0)+1;playbackRequests.set(player,token);return token;}
function seekAudio(player,start){if(player.readyState>=1)player.currentTime=start;else pendingSeeks.set(player,start);}
for(const player of document.querySelectorAll('audio')){
 player.addEventListener('loadedmetadata',()=>{const start=pendingSeeks.get(player);if(start!==undefined){player.currentTime=start;pendingSeeks.delete(player);}});
 player.addEventListener('play',()=>{for(const other of document.querySelectorAll('audio'))if(other!==player)other.pause();});
 const showAudioError=()=>{const panel=player.closest('.audio-edition'),status=panel?.querySelector('.audio-status');if(status){status.dataset.kind='error';status.textContent='Audio could not load. Check your connection, try the MP3 download, or read the transcript.';const resources=panel.querySelector('.narration-sections');if(resources)resources.open=true;}};
 player.addEventListener('error',showAudioError);
 for(const source of player.querySelectorAll('source'))source.addEventListener('error',showAudioError);
}
for(const panel of document.querySelectorAll('.page-narration')){
 const config=panel.querySelector('.narration-variants');if(!config)continue;
 const variants=JSON.parse(config.textContent),player=panel.querySelector('audio'),select=panel.querySelector('[data-narration-voice]'),status=panel.querySelector('.audio-status');
 status.dataset.kind='info';
 let voice='andrew';
 function apply(preferences,meta={}){
  const next=variants[preferences.voice]?preferences.voice:'andrew',edition=variants[next];
  if(next!==voice){
   const old=variants[voice],time=pendingSeeks.get(player)??player.currentTime;
   let target=0;
   if(time>0&&!player.ended&&time<old.seconds-.5){const match=old.sections.findIndex(s=>time<s.end),i=match<0?old.sections.length-1:match;const section=old.sections[i],other=edition.sections[i];const fraction=Math.max(0,Math.min(1,(time-section.start)/(section.end-section.start)));target=other.start+fraction*(other.end-other.start);}
   nextPlaybackRequest(player);player.pause();pendingSeeks.delete(player);
   // load() can override preload=none in Chromium. Setting src keeps the
   // unrequested edition unloaded while resetting the native playback state.
   player.src=edition.audio;player.querySelector('source').src=edition.audio;
   if(target>0)pendingSeeks.set(player,target);
   voice=next;
   panel.querySelector('[data-narration-name]').textContent=edition.name;
   panel.querySelector('[data-narration-duration]').textContent=edition.duration;
   panel.querySelector('[data-narration-duration]').dataset.seconds=edition.seconds;
   panel.querySelector('.narration-download').href=edition.audio;
   panel.querySelector('.narration-download').download=edition.filename;
   panel.querySelector('.narration-transcript').href=edition.transcript;
   panel.querySelectorAll('[data-audio-seek]').forEach((button,i)=>{const section=edition.sections[i];button.dataset.start=section.start;const seconds=Math.round(section.start),minutes=Math.floor(seconds/60);button.textContent=minutes+':'+String(seconds%60).padStart(2,'0')+' · '+section.title;});
   if(meta.saved!==undefined||meta.external){status.dataset.kind='info';status.textContent=edition.name+' selected. Press Play to listen.';}
  }
  player.defaultPlaybackRate=preferences.speed;player.playbackRate=preferences.speed;
  if(select)select.value=next;
  const speed=panel.querySelector('[data-audio-speed]');if(speed)speed.value=String(preferences.speed);
  if(meta.saved===false){status.dataset.kind='warning';status.textContent='Your choice applies on this page, but your browser blocked saving it for other pages.';}
 }
 if(select){
  select.parentElement.hidden=false;
  select.addEventListener('change',()=>window.BookSettings?.set({voice:select.value}));
 }
 if(window.BookSettings){apply(window.BookSettings.get());window.BookSettings.subscribe(apply);}
 // Progressive enhancement: the same media element remains the native fallback.
 const transport=panel.querySelector('.lesson-transport');
 if(transport){
  const toggle=transport.querySelector('[data-player-toggle]'),seek=transport.querySelector('[data-player-seek]'),mute=transport.querySelector('[data-player-mute]'),elapsed=transport.querySelector('[data-player-elapsed]'),duration=panel.querySelector('[data-narration-duration]');
  function clock(value){const seconds=Math.floor(Math.max(0,value||0));return Math.floor(seconds/60)+':'+String(seconds%60).padStart(2,'0');}
  function sync(){
   const length=Number.isFinite(player.duration)&&player.duration>0?player.duration:Number(duration.dataset.seconds);
   const time=Math.max(0,Math.min(length,pendingSeeks.get(player)??player.currentTime));
   toggle.classList.toggle('is-playing',!player.paused);
   toggle.setAttribute('aria-label',player.paused?(player.ended?'Replay lesson':'Play lesson'):'Pause lesson');
   seek.max=length;seek.value=time;seek.style.setProperty('--played',(length?time/length*100:0)+'%');
   elapsed.textContent=player.ended?duration.textContent:clock(time);
   seek.setAttribute('aria-valuetext',elapsed.textContent+' of '+duration.textContent);
   mute.setAttribute('aria-pressed',String(player.muted));mute.setAttribute('aria-label',player.muted?'Unmute lesson':'Mute lesson');
  }
  toggle.addEventListener('click',()=>{
   if(!player.paused){player.pause();return;}
   const request=nextPlaybackRequest(player);
   player.play().catch(error=>{if(playbackRequests.get(player)!==request||error.name==='AbortError')return;status.dataset.kind='error';status.textContent='Playback could not start. Try the MP3 download or read the transcript.';});
  });
  seek.addEventListener('input',()=>{seekAudio(player,Number(seek.value));sync();});
  mute.addEventListener('click',()=>{player.muted=!player.muted;sync();});
  for(const event of ['play','pause','ended','timeupdate','durationchange','loadedmetadata','emptied','volumechange'])player.addEventListener(event,sync);
  panel.dataset.enhanced='true';transport.hidden=false;sync();
 }
}
for(const select of document.querySelectorAll('[data-audio-speed]')){
 select.hidden=false;
 if(select.parentElement.classList.contains('narration-speed'))select.parentElement.hidden=false;
 select.addEventListener('change',()=>{const player=document.getElementById(select.dataset.audioSpeed);if(player)player.playbackRate=Number(select.value);if(player?.id==='page-narration-audio')window.BookSettings?.set({speed:Number(select.value)});});
}
// Section links are explicit playback actions; nothing loads on page arrival.
for(const button of document.querySelectorAll('[data-audio-seek]')){
 button.hidden=false;
 button.addEventListener('click',()=>{
  const player=document.getElementById(button.dataset.audioSeek),start=Number(button.dataset.start),status=player?.closest('.audio-edition')?.querySelector('.audio-status');
  if(!player||!Number.isFinite(start))return;
  const request=nextPlaybackRequest(player);
  seekAudio(player,start);
  player.play().then(()=>{if(playbackRequests.get(player)===request&&!player.paused&&status){status.dataset.kind='info';status.textContent='Selected section: '+button.textContent;}}).catch(error=>{if(playbackRequests.get(player)!==request||error.name==='AbortError')return;if(status){status.dataset.kind='error';status.textContent='Playback could not start. Use the audio controls or download the MP3.';}});
 });
}
