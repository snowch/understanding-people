/* A local dictionary filter. Terms typed here are never saved or sent. */
(() => {
 const controls=document.querySelector('.glossary-lookup-controls');if(!controls)return;
 const input=controls.querySelector('input'),clear=document.querySelector('#glossary-clear');
 const entries=[...document.querySelectorAll('.glossary-entry')];
 const count=document.querySelector('#glossary-count'),empty=document.querySelector('#glossary-empty');
 const normalise=s=>s.normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[–—-]/g,' ').replace(/\s+/g,' ').trim();
 const corpus=entries.map(el=>normalise(el.textContent));
 const names=entries.map(el=>normalise(el.dataset.glossaryNames||el.querySelector('h2').textContent));
 function apply(){
  const words=normalise(input.value).split(' ').filter(Boolean);let shown=0;
  const matches=text=>words.every(word=>text.includes(word));
  const matchingNames=words.length&&names.some(matches);
  entries.forEach((entry,i)=>{entry.hidden=!matches((matchingNames?names:corpus)[i]);if(!entry.hidden)shown++;});
  clear.hidden=!input.value;empty.hidden=shown>0;
  count.textContent=`${shown} of ${entries.length} terms${words.length?' match':' · alphabetical'}`;
 }
 input.addEventListener('input',apply);
 clear.addEventListener('click',()=>{input.value='';apply();input.focus();});
 for(const link of document.querySelectorAll('.glossary-browse'))link.addEventListener('click',event=>{
  event.preventDefault();input.value='';apply();input.focus({preventScroll:true});input.scrollIntoView({block:'center'});
 });
 function revealHash(hash){
  let id;try{id=decodeURIComponent(hash.slice(1));}catch{return;}
  const target=document.getElementById(id);
  if(input.value&&target?.closest('.glossary-entry')){input.value='';apply();target.scrollIntoView({block:'start'});}
 }
 window.addEventListener('hashchange',()=>revealHash(location.hash));
 document.addEventListener('click',event=>{
  const link=event.target.closest('a[href^="#"]');
  if(link)revealHash(link.getAttribute('href'));
 });
 controls.hidden=false;apply();
})();
