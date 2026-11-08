/* Search is local; the complete, grouped catalogue also works without JavaScript. */
(async () => {
  const scriptURL=new URL(document.currentScript.src),root=new URL('../',scriptURL);
  const input = document.querySelector('#library-query');
  if (!input) return;
  let planQuery=()=>({role:null,notice:''});
  try { ({planQuery}=await import('./search/query.mjs'+scriptURL.search)); }
  catch { /* The original word filter remains usable without this enhancement. */ }
  const entries = [...document.querySelectorAll('[data-library-search]')];
  const normalise = text => text.toLocaleLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '');
  const clear = document.querySelector('#library-clear');
  const status = document.querySelector('#library-status');
  const note=document.querySelector('#library-query-note');
  const documents=entries.map(e=>({title:e.querySelector('h3').textContent}));
  function update() {
    const terms = normalise(input.value).trim().split(/\s+/).filter(Boolean);
    const plan=planQuery(input.value,documents);
    const related=new Set((plan.role?.topics||[]).map(path=>new URL(path,root).href));
    let count = 0;
    for (const entry of entries) {
      const match=terms.every(term => normalise(entry.dataset.librarySearch).includes(term))||related.has(entry.querySelector('h3 a').href);
      entry.hidden = (status.value !== 'all' && entry.dataset.status !== status.value) || !match;
      if (!entry.hidden) count++;
    }
    for (const group of document.querySelectorAll('.library-group')) {
      group.hidden = ![...group.querySelectorAll('[data-library-search]')].some(entry => !entry.hidden);
    }
    document.querySelector('#library-result-count').textContent = `${count} of ${entries.length} entries`;
    document.querySelector('#library-empty').hidden = count !== 0;
    if(note){note.textContent=plan.notice;note.hidden=!plan.notice;}
    clear.hidden = !terms.length;
  }
  input.addEventListener('input', update);
  status.addEventListener('change', update);
  clear.addEventListener('click', () => { input.value = ''; update(); input.focus(); });
  document.querySelectorAll('.library-topics a').forEach(link => link.addEventListener('click', () => { input.value = ''; status.value = 'all'; update(); }));
  document.querySelector('.library-search').hidden = false;
  update();
})();
