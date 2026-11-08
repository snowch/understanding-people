/* A private, book-scoped reading queue. No query text, notes or remote service. */
(() => {
  'use strict';
  const script = document.currentScript;
  const root = new URL('../', script.src);
  const key = `understanding-people:reading-list:v1:${root.pathname}`;
  const listPage = document.querySelector('#reading-list-items');
  const status = document.querySelector('#reading-save-status');
  let catalogue, items = [], filter = 'unread', persistent = true, storageWarning = '';
  const say = message => {
    if (!status) return;
    status.textContent = [message, storageWarning].filter(Boolean).join(' ');
    if (storageWarning) {
      const backup = node('button', 'Download temporary list', 'reading-save'); backup.type = 'button';
      backup.addEventListener('click', download); status.append(' ', backup);
    }
  };
  const node = (tag, text, className) => {
    const el = document.createElement(tag);
    if (text !== undefined) el.textContent = text;
    if (className) el.className = className;
    return el;
  };
  function parse(value) {
    if (!value || value.version !== 1 || !Array.isArray(value.items) || value.items.length > 1000)
      throw new Error('Unrecognised reading-list file.');
    const found = new Map();
    for (const row of value.items) {
      if (!row || typeof row.url !== 'string' || !Object.hasOwn(catalogue, row.url)) continue;
      const fragment = typeof row.fragment === 'string' && row.fragment.length <= 300 ? row.fragment : '';
      found.set(row.url, {url:row.url, fragment, read:row.read === true});
    }
    return [...found.values()];
  }
  function load() {
    try {
      const raw = localStorage.getItem(key);
      items = raw === null ? [] : parse(JSON.parse(raw));
    } catch (_) {
      persistent = false;
      storageWarning = 'Your saved list could not be opened. Changes stay on this page only; download a backup before leaving or reloading.';
      say('');
    }
  }
  function persist(message) {
    if (persistent) {
      try { localStorage.setItem(key, JSON.stringify({version:1, items})); }
      catch (_) {
        persistent = false;
        storageWarning = 'Browser storage is unavailable or full. Changes stay on this page only; download a backup before leaving or reloading.';
      }
    }
    refresh();
    say(message);
  }
  function buttonState() {
    for (const b of document.querySelectorAll('[data-reading-save]')) {
      const url = b.dataset.readingSave;
      if (!Object.hasOwn(catalogue, url)) continue;
      const saved = items.some(row => row.url === url);
      b.hidden = false;
      b.setAttribute('aria-pressed', String(saved));
      b.textContent = saved ? 'Saved · remove' : 'Save for later';
      b.setAttribute('aria-label', `${saved ? 'Remove from reading list' : 'Save for later'}: ${catalogue[url]}`);
    }
  }
  function renderList() {
    if (!listPage) return;
    const visible = items.filter(row => filter === 'all' || row.read === (filter === 'read'));
    listPage.replaceChildren();
    const unread = items.filter(row => !row.read).length;
    document.querySelector('#reading-list-count').textContent = `${unread} to read · ${items.length - unread} read`;
    document.querySelector('#reading-list-empty').hidden = visible.length > 0;
    if (!visible.length) {
      const empty = document.querySelector('#reading-list-empty');
      if (!items.length) {
        empty.replaceChildren(node('span', 'Nothing saved yet. '));
        const a = node('a', 'Find something to read'); a.href = new URL('search.html', root);
        const browse = node('a', 'browse the reference library'); browse.href = new URL('reference/index.html', root);
        empty.append(a, node('span', ' or '), browse, node('span', '.'));
      } else empty.textContent = filter === 'read' ? 'No pages marked as read. You can mark a page below All.' : 'Nothing waiting to be read. Look under Read or save something new.';
    }
    for (const row of visible) {
      const li = node('li', undefined, 'reading-list-item');
      const a = node('a', catalogue[row.url]);
      const target = new URL(row.url, root); target.hash = row.fragment;
      a.href = target;
      const h = node('h2'); h.append(a); li.append(h);
      li.append(node('p', row.fragment ? 'Returns to your saved passage' : 'Returns to the page', 'reading-list-location'));
      const actions = node('div', undefined, 'reading-list-item-actions');
      const read = node('button', row.read ? 'Mark unread' : 'Mark as read');
      read.type = 'button'; read.setAttribute('aria-label', `${read.textContent}: ${catalogue[row.url]}`);
      read.addEventListener('click', () => {
        const previousIndex = visible.indexOf(row);
        row.read = !row.read; persist(row.read ? 'Marked as read.' : 'Moved to To read.');
        focusAfterChange(previousIndex);
      });
      const remove = node('button', 'Remove'); remove.type = 'button';
      remove.setAttribute('aria-label', `Remove from reading list: ${catalogue[row.url]}`);
      remove.addEventListener('click', () => {
        const previousIndex = visible.indexOf(row);
        items = items.filter(item => item.url !== row.url); persist('Removed from your reading list.');
        focusAfterChange(previousIndex);
      });
      actions.append(read, remove); li.append(actions); listPage.append(li);
    }
  }
  function focusAfterChange(index) {
    const next = listPage.children[Math.min(index, listPage.children.length - 1)]?.querySelector('button');
    (next || document.querySelector(`[data-reading-filter="${filter}"]`)).focus({preventScroll:true});
  }
  function refresh() { buttonState(); renderList(); }
  function download() {
    const blob = new Blob([JSON.stringify({version:1, items}, null, 2)], {type:'application/json'});
    const url = URL.createObjectURL(blob), a = node('a');
    a.href = url; a.download = 'understanding-people-reading-list.json'; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    say('Backup downloaded.');
  }
  async function init() {
    try {
      const response = await fetch(new URL('assets/reading-list-index.json' + new URL(script.src).search, root));
      if (!response.ok) throw new Error('Catalogue unavailable');
      catalogue = await response.json();
    } catch (_) {
      say('Your reading list could not load. Try reloading online; your saved list has not been changed.');
      return;
    }
    load(); refresh();
    document.querySelector('#reading-list-controls')?.removeAttribute('hidden');
    document.addEventListener('reading-list:refresh', buttonState);
    document.addEventListener('click', event => {
      const b = event.target.closest('[data-reading-save]');
      if (!b || !Object.hasOwn(catalogue, b.dataset.readingSave)) return;
      const url = b.dataset.readingSave;
      if (items.some(row => row.url === url)) {
        items = items.filter(row => row.url !== url); persist('Removed from your reading list.');
      } else {
        const passage = b.dataset.readingFragment || (b.dataset.readingCurrent !== undefined ? decodeFragment(location.hash.slice(1)) : '');
        items.unshift({url, fragment:passage.slice(0,300), read:false});
        persist('Saved to your reading list.');
      }
      // Keep a visible failure beside a search result even when the page heading
      // has scrolled away. The temporary download is available on this page.
      if (storageWarning && b.closest('.search-result-actions')) {
        let notice = b.parentElement.querySelector('.reading-save-warning');
        if (!notice) { notice = node('p', undefined, 'reading-save-warning'); b.parentElement.append(notice); }
        notice.textContent = storageWarning + ' ';
        const backup = node('button', 'Download temporary list', 'reading-save'); backup.type = 'button';
        backup.addEventListener('click', download); notice.append(backup);
      }
    });
    for (const b of document.querySelectorAll('[data-reading-filter]')) b.addEventListener('click', () => {
      filter = b.dataset.readingFilter;
      for (const tab of document.querySelectorAll('[data-reading-filter]')) tab.setAttribute('aria-pressed', String(tab === b));
      renderList();
    });
    document.querySelector('#reading-list-download')?.addEventListener('click', download);
    document.querySelector('#reading-list-import')?.addEventListener('change', async event => {
      const file = event.target.files[0]; if (!file) return;
      try {
        if (file.size > 1000000) throw new Error('File too large');
        const incoming = parse(JSON.parse(await file.text()));
        const existing = new Set(items.map(row => row.url));
        const additions = incoming.filter(row => !existing.has(row.url));
        items.push(...additions); persist(`${additions.length} saved ${additions.length === 1 ? 'page' : 'pages'} restored. Existing saved pages kept unchanged.`);
      } catch (_) { say('This file could not be restored. Choose a reading-list JSON backup; your current list has not changed.'); }
      event.target.value = '';
    });
    window.addEventListener('storage', event => {
      if (!persistent || (event.key !== key && event.key !== null)) return;
      load(); refresh(); say('Reading list updated.');
    });
  }
  function decodeFragment(value) { try { return decodeURIComponent(value); } catch (_) { return ''; } }
  init();
})();
