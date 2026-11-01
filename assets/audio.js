// Playback speed is optional; native audio controls work without JavaScript.
for(const select of document.querySelectorAll('[data-audio-speed]')){
 select.hidden=false;
 select.addEventListener('change',()=>{const player=document.getElementById(select.dataset.audioSpeed);if(player)player.playbackRate=Number(select.value)});
}
// Section links are explicit playback actions; nothing loads on page arrival.
for(const button of document.querySelectorAll('[data-audio-seek]')){
 button.hidden=false;
 button.addEventListener('click',()=>{
  const player=document.getElementById(button.dataset.audioSeek),start=Number(button.dataset.start),status=document.querySelector('.audio-status');
  if(!player||!Number.isFinite(start))return;
  player.currentTime=start;
  player.play().then(()=>{if(status)status.textContent='Selected section: '+button.textContent;}).catch(()=>{if(status)status.textContent='Playback could not start. Use the audio controls or download the MP3.';});
 });
}
