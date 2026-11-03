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
for(const player of document.querySelectorAll('audio')){
 player.addEventListener('play',()=>{for(const other of document.querySelectorAll('audio'))if(other!==player)other.pause();});
 const showAudioError=()=>{const status=player.closest('.audio-edition')?.querySelector('.audio-status');if(status)status.textContent='Audio could not load. Check your connection, try the MP3 download, or read the transcript.';};
 player.addEventListener('error',showAudioError);
 for(const source of player.querySelectorAll('source'))source.addEventListener('error',showAudioError);
}
for(const select of document.querySelectorAll('[data-audio-speed]')){
 select.hidden=false;
 if(select.parentElement.classList.contains('narration-speed'))select.parentElement.hidden=false;
 select.addEventListener('change',()=>{const player=document.getElementById(select.dataset.audioSpeed);if(player)player.playbackRate=Number(select.value)});
}
// Section links are explicit playback actions; nothing loads on page arrival.
for(const button of document.querySelectorAll('[data-audio-seek]')){
 button.hidden=false;
 button.addEventListener('click',()=>{
  const player=document.getElementById(button.dataset.audioSeek),start=Number(button.dataset.start),status=player?.closest('.audio-edition')?.querySelector('.audio-status');
  if(!player||!Number.isFinite(start))return;
  if(player.readyState>=1)player.currentTime=start;
  else player.addEventListener('loadedmetadata',()=>{player.currentTime=start;},{once:true});
  player.play().then(()=>{if(status)status.textContent='Selected section: '+button.textContent;}).catch(()=>{if(status)status.textContent='Playback could not start. Use the audio controls or download the MP3.';});
 });
}
