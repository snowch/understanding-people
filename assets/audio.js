// Playback speed is optional; native audio controls work without JavaScript.
for(const select of document.querySelectorAll('[data-audio-speed]')){
 select.hidden=false;
 select.addEventListener('change',()=>{const player=document.getElementById(select.dataset.audioSpeed);if(player)player.playbackRate=Number(select.value)});
}
