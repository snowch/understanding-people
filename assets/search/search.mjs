const buildQuery=new URL(import.meta.url).search;
const {createRanker,terms,normalise,planQuery}=await import('./rank.mjs'+buildQuery);
const form=document.querySelector('#book-search-form');
if(form){
 const query=document.querySelector('#book-search-query'),meaning=document.querySelector('#meaning-search');
 const loading=document.querySelector('#search-loading'),cancel=document.querySelector('#search-cancel');
 const clear=document.querySelector('#search-clear'),region=document.querySelector('#search-results-region');
 const list=document.querySelector('#search-results'),count=document.querySelector('#search-results-count');
 const more=document.querySelector('#search-more'),suggestions=document.querySelector('#search-suggestions');
 let data,ranker,vectorRanker,initializing,loadingVectors,worker,busy=false,job=0,timer,results=[],limit=6,current='',mode='Keywords';
 const root=new URL('../../',import.meta.url);
 const link=(label,path)=>{const a=document.createElement('a');a.textContent=label;a.href=new URL(path,root);return a;};
 async function init(){
  if(!initializing)initializing=(async()=>{
   const response=await fetch(new URL('./index.json'+buildQuery,import.meta.url));
   if(!response.ok)throw new Error('Search files unavailable.');
   data=await response.json();ranker=createRanker(data);
   document.querySelector('#search-privacy').textContent=`Searches stay on this device and aren’t saved. The first meaning search downloads about ${Math.ceil(data.engine_bytes/1e6)} MB.`;
  })().catch(error=>{initializing=null;throw error;});
  return initializing;
 }
 async function initVectors(){
  if(!loadingVectors)loadingVectors=(async()=>{
   const response=await fetch(new URL('./vectors.bin'+buildQuery,import.meta.url));
   if(!response.ok)throw new Error('Vectors unavailable.');
   const bytes=await response.arrayBuffer();
   if(crypto.subtle){const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');if(hash!==data.vectors_sha256)throw new Error('Search files have different versions.');}
   vectorRanker=createRanker(data,bytes);
  })().catch(error=>{loadingVectors=null;throw error;});
  return loadingVectors;
 }
 function stop(terminate=false){job++;clearTimeout(timer);if(worker&&(busy||terminate)){worker.terminate();worker=null;}busy=false;cancel.hidden=true;}
 function excerpt(text){
  if(text.length<310)return text;
  const words=terms(current),lower=normalise(text);
  let hit=words.map(w=>lower.indexOf(w)).filter(i=>i>=0).sort((a,b)=>a-b)[0]||0;
  let start=Math.max(0,hit-90);if(start)start=text.indexOf(' ',start)+1;
  let end=text.lastIndexOf(' ',start+290);if(end<start)end=start+290;
  return (start?'… ':'')+text.slice(start,end)+(end<text.length?' …':'');
 }
 function render(){
  list.replaceChildren();region.hidden=false;
  const plan=planQuery(current,data.documents),note=document.querySelector('#search-term-note');
  note.textContent=plan.notice;note.hidden=!plan.notice;
  for(const result of results.slice(0,limit)){
   const d=data.documents[result.document],p=data.passages[result.passage];
   const li=document.createElement('li'),kind=document.createElement('p'),h=document.createElement('h3');
   kind.className='search-result-kind';kind.textContent=(result.related?'Related topic · ':'')+(d.clinical?'Clinical reference':d.kind);
   h.append(link(d.title,d.url+'#'+p.anchor));
   li.append(kind,h);
   if(p.heading!==d.title){const section=document.createElement('p');section.className='search-result-section';section.textContent=p.heading;li.append(section);}
   const quote=document.createElement('p');quote.className='search-excerpt';quote.textContent=excerpt(p.text);li.append(quote);
   const actions=document.createElement('div');actions.className='search-result-actions';actions.append(link('Read passage',d.url+'#'+p.anchor));
   if(d.listen)actions.append(link('Listen',d.url+'#'+d.listen));
   if(d.practice)actions.append(link('Practise',d.url+'#'+d.practice));
   const save=document.createElement('button');save.type='button';save.className='reading-save';save.hidden=true;save.dataset.readingSave=d.url;save.dataset.readingFragment=p.anchor;actions.append(save);
   li.append(actions);list.append(li);
  }
  document.dispatchEvent(new Event('reading-list:refresh'));
  count.textContent=results.length?`${mode} · ${Math.min(limit,results.length)} related ${results.length===1?'page':'pages'}${results.length>limit?' shown':''}`:'No close matches';
  document.querySelector('#search-empty').hidden=results.length!==0;
  more.hidden=results.length<=limit;
 }
 function fail(message){clearTimeout(timer);busy=false;cancel.hidden=true;loading.classList.remove('visually-hidden');loading.textContent=message;}
 async function search(event){
  event?.preventDefault();stop();const id=job;textCleanup();
  current=query.value.trim();if(!current){region.hidden=true;suggestions.hidden=false;return;}
  clear.hidden=false;suggestions.hidden=true;limit=6;loading.textContent='Searching the book…';
  try{await init();if(job!==id)return;
   results=ranker(current);mode='Keywords';render();
   if(!meaning.checked){loading.classList.add('visually-hidden');loading.textContent='Keyword search. Your question stays on this device.';return;}
   if(!window.Worker||!window.WebAssembly){fail('Meaning search is not supported in this browser. Keyword results are shown.');return;}
   cancel.hidden=false;loading.textContent='Loading meaning search. Keyword results are ready below.';
   try{await initVectors();}catch(error){if(job===id)fail('Meaning-search files could not load. Keyword results are still available; try again after reloading.');return;}
   if(job!==id)return;
   busy=true;
   if(!worker)worker=new Worker(new URL('./worker.mjs'+buildQuery,import.meta.url),{type:'module'});
   worker.onmessage=({data:message})=>{
    if(message.id!==job)return;
    if(message.kind==='progress')loading.textContent=message.stage+' Keyword results remain below.';
    if(message.kind==='error'){worker.terminate();worker=null;fail(message.message);}
    if(message.kind==='result'){
     clearTimeout(timer);busy=false;cancel.hidden=true;
     results=vectorRanker(current,message.embedding);mode='Meaning + keywords';render();
     loading.textContent='Search complete. Results are passages from the book.';
     loading.classList.add('visually-hidden');
    }
   };
   worker.onerror=()=>{if(job===id){worker.terminate();worker=null;fail('Meaning search could not load. Keyword results are still available.');}};
   timer=setTimeout(()=>{if(job===id){stop();fail('Meaning search took too long. Keyword results are still available; try again when your connection is ready.');}},120000);
   worker.postMessage({id,text:planQuery(current,data.documents).embeddingText});
  }catch(error){if(job!==id)return;fail('The search files could not load. Try again online, or browse the book below.');region.hidden=true;}
 }
 function textCleanup(){loading.textContent='';loading.classList.remove('visually-hidden');}
 form.addEventListener('submit',search);
 cancel.addEventListener('click',()=>{stop();loading.textContent='Meaning search stopped. Keyword results remain below.';query.focus();});
 clear.addEventListener('click',()=>{stop(true);query.value='';current='';list.replaceChildren();region.hidden=true;suggestions.hidden=false;clear.hidden=true;textCleanup();query.focus();});
 meaning.addEventListener('change',()=>{if(!meaning.checked){stop();if(ranker&&current){results=ranker(current);mode='Keywords';render();}loading.textContent='Keyword search selected.';}});
 query.addEventListener('input',()=>{if(query.value.trim()!==current){stop();clear.hidden=!query.value;loading.classList.remove('visually-hidden');loading.textContent='Press Search to update the results.';}});
 more.addEventListener('click',()=>{const previous=limit;limit+=6;render();const next=list.children[previous];if(next){next.querySelector('h3 a').focus({preventScroll:true});next.scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});}});
 for(const b of document.querySelectorAll('.search-examples button'))b.addEventListener('click',()=>{query.value=b.textContent;search();});
 form.hidden=false;suggestions.hidden=false;
}
