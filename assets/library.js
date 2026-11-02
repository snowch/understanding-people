/* Search is local; the complete, grouped catalogue also works without JavaScript. */
(() => {
  const input = document.querySelector('#library-query');
  if (!input) return;
  const entries = [...document.querySelectorAll('[data-library-search]')];
  const normalise = text => text.toLocaleLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '');
  const clear = document.querySelector('#library-clear');
  const status = document.querySelector('#library-status');
  function update() {
    const terms = normalise(input.value).trim().split(/\s+/).filter(Boolean);
    let count = 0;
    for (const entry of entries) {
      entry.hidden = (status.value !== 'all' && entry.dataset.status !== status.value) || !terms.every(term => normalise(entry.dataset.librarySearch).includes(term));
      if (!entry.hidden) count++;
    }
    for (const group of document.querySelectorAll('.library-group')) {
      group.hidden = ![...group.querySelectorAll('[data-library-search]')].some(entry => !entry.hidden);
    }
    document.querySelector('#library-result-count').textContent = `${count} of ${entries.length} entries`;
    document.querySelector('#library-empty').hidden = count !== 0;
    clear.hidden = !terms.length;
  }
  input.addEventListener('input', update);
  status.addEventListener('change', update);
  clear.addEventListener('click', () => { input.value = ''; update(); input.focus(); });
  document.querySelectorAll('.library-topics a').forEach(link => link.addEventListener('click', () => { input.value = ''; status.value = 'all'; update(); }));
  document.querySelector('.library-search').hidden = false;
  update();
})();
