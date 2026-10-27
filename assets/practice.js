// Copyright © 2026 Christopher Snow
// Notes stay in localStorage. No notes are transmitted or used as HTML.
(() => {
  'use strict';
  const bookPath = new URL('../', document.currentScript.src).pathname;
  const prefix = `understanding-people:practice:v1:${bookPath}:`;
  document.querySelectorAll('.practice-notes').forEach(panel => {
    const key = prefix + panel.dataset.notesId;
    const fields = [...panel.querySelectorAll('textarea, input')];
    const status = panel.querySelector('.notes-status');
    const message = text => { if (status.textContent !== text) status.textContent = text; };
    const mirror = () => fields.forEach(field => {
      field.nextElementSibling.textContent = field.value;
    });
    const values = () => Object.fromEntries(fields.map(field => [field.name, field.value]));
    const read = () => {
      try {
        const raw = localStorage.getItem(key);
        if (raw === null) {
          fields.forEach(field => { field.value = ''; });
          message('No saved notes for this exercise yet.');
        } else {
          const saved = JSON.parse(raw);
          if (!saved || saved.version !== 1 || !saved.fields ||
              fields.some(field => typeof saved.fields[field.name] !== 'string')) {
            throw new Error('Unreadable notes');
          }
          fields.forEach(field => { field.value = saved.fields[field.name]; });
          message('Saved notes loaded from this browser.');
        }
      } catch {
        message('Saved notes could not be loaded. You can still write here and download a copy.');
      }
      mirror();
    };
    read();
    panel.classList.add('notes-ready');
    panel.querySelector('.notes-controls').hidden = false;
    panel.addEventListener('input', event => {
      if (!fields.includes(event.target)) return;
      mirror();
      try {
        localStorage.setItem(key, JSON.stringify({version: 1, fields: values()}));
        message('Saved in this browser on this device.');
      } catch {
        message('These changes could not be saved. Keep this page open and download your notes before leaving.');
      }
    });
    panel.querySelector('[data-notes-download]').addEventListener('click', () => {
      const lines = ['Understanding people — practice notes', panel.dataset.notesTitle,
        location.origin + location.pathname, ''];
      fields.forEach(field => {
        lines.push(panel.querySelector(`label[for="${field.id}"]`).textContent, field.value || '(blank)', '');
      });
      const url = URL.createObjectURL(new Blob([lines.join('\n')], {type: 'text/plain;charset=utf-8'}));
      const link = document.createElement('a');
      link.href = url;
      link.download = `understanding-people-${panel.dataset.notesId}.txt`;
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    });
    panel.querySelector('[data-notes-delete]').addEventListener('click', () => {
      if (!confirm('Delete the notes for this exercise from this browser? Download a copy first if you want to keep them.')) return;
      try {
        localStorage.removeItem(key);
      } catch {
        message('Saved notes could not be deleted. They have been left on this page so you can keep a copy.');
        return;
      }
      fields.forEach(field => { field.value = ''; });
      mirror();
      message('Notes for this exercise deleted from this browser. Downloaded copies are unchanged.');
    });
    // Keep another open copy of the same exercise in step, including deletion.
    window.addEventListener('storage', event => {
      if (event.key === key || event.key === null) read();
    });
  });
})();
