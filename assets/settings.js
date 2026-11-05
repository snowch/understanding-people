// Reading preferences are scoped to this book, stored locally, and never sent.
(()=>{
 const script=document.querySelector('script[data-book-settings]');
 if(!script)return;
 const base=new URL('../',script.src),key='understanding-people:preferences:v1:'+base.pathname;
 const voices=script.dataset.voices.split(' '),speeds=[.75,1,1.25,1.5,2];
 const defaults={version:1,voice:'andrew',speed:1},listeners=new Set();
 let storageError=false;
 function normalise(value){return {version:1,voice:voices.includes(value?.voice)?value.voice:defaults.voice,speed:speeds.includes(value?.speed)?value.speed:defaults.speed};}
 function read(){try{return normalise(JSON.parse(localStorage.getItem(key)));}catch(error){storageError=error.name!=='SyntaxError';return {...defaults};}}
 let current=read();
 function notify(meta={}){for(const fn of listeners)fn({...current},meta);}
 function set(change){current=normalise({...current,...change});let saved=true;try{localStorage.setItem(key,JSON.stringify(current));storageError=false;}catch{saved=false;storageError=true;}notify({saved});return saved;}
 window.BookSettings={base,key,get:()=>({...current}),set,subscribe:fn=>listeners.add(fn)};
 window.addEventListener('storage',event=>{if(event.key===key||event.key===null){current=read();notify({external:true,saved:!storageError});}});
 const controls=document.querySelector('[data-settings-controls]'),status=document.querySelector('[data-settings-status]');
 function update(){
  if(!controls)return;
  for(const radio of controls.querySelectorAll('[name="narrator"]'))radio.checked=radio.value===current.voice;
  controls.querySelector('#reading-speed').value=String(current.speed);
  if(status)status.textContent=storageError?'Your browser blocked saving preferences. You can choose a voice on each lesson, but it will not be remembered.':'Preferences save automatically in this browser on this device.';
 }
 if(controls){
  controls.disabled=false;update();listeners.add(update);
  for(const radio of controls.querySelectorAll('[name="narrator"]'))radio.addEventListener('change',()=>{if(radio.checked)set({voice:radio.value});});
  controls.querySelector('#reading-speed').addEventListener('change',event=>set({speed:Number(event.target.value)}));
  controls.querySelector('[data-settings-reset]').addEventListener('click',()=>set(defaults));
 }
 const back=document.querySelector('[data-reading-return]');
 if(back){
  const target=new URLSearchParams(location.search).get('return');
  if(target){try{const url=new URL(target,base);if(url.origin===base.origin&&url.pathname.startsWith(base.pathname)&&(url.pathname.endsWith('.html')||url.pathname===base.pathname)&&url.pathname!==new URL('settings.html',base).pathname)back.href=url.href;}catch{}}
 }
 const preview=document.getElementById('voice-preview');
 if(preview){
  const samples=JSON.parse(document.getElementById('voice-previews').textContent),panel=preview.closest('.voice-preview'),previewStatus=panel.querySelector('[data-preview-status]');
  for(const button of document.querySelectorAll('[data-preview-voice]'))button.addEventListener('click',()=>{
   const sample=samples[button.dataset.previewVoice];if(!sample)return;
   preview.pause();preview.src=sample.audio;preview.playbackRate=1;panel.hidden=false;
   panel.querySelector('[data-preview-name]').textContent=sample.name;
   preview.setAttribute('aria-label',sample.name+' voice preview');
   previewStatus.textContent='Previewing '+sample.name+'. Your narrator choice is unchanged.';
   preview.play().catch(()=>{previewStatus.textContent='Use the audio controls to start the preview.';});
  });
  preview.addEventListener('timeupdate',()=>{if(preview.currentTime>=25&&!preview.paused){preview.pause();previewStatus.textContent='End of the 25-second preview. Choose a narrator above when ready.';}});
  preview.addEventListener('error',()=>{previewStatus.textContent='The preview could not load. Try again when online; your selection is still available.';});
 }
})();
