// Copyright © 2026 Christopher Snow
(() => {
  const base = new URL('../', document.currentScript.src);
  const button = document.querySelector('.install-button');
  const dialog = document.querySelector('#install-help');
  const standalone = window.matchMedia('(display-mode: standalone)');
  let promptEvent = null;
  let installed = standalone.matches || navigator.standalone === true;
  const updateButton = () => { button.hidden = installed; };
  updateButton();
  standalone.addEventListener('change', event => {
    installed = event.matches || navigator.standalone === true;
    updateButton();
  });
  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault();
    promptEvent = event;
  });
  window.addEventListener('appinstalled', () => {
    installed = true;
    promptEvent = null;
    if (dialog.open) dialog.close();
    updateButton();
  });
  button.addEventListener('click', async () => {
    if (!promptEvent) {
      dialog.showModal();
      return;
    }
    const request = promptEvent;
    promptEvent = null;
    button.disabled = true;
    try {
      await request.prompt();
      await request.userChoice;
    } catch {
      dialog.showModal();
    } finally {
      button.disabled = false;
    }
  });
  if ('serviceWorker' in navigator && window.isSecureContext) {
    navigator.serviceWorker.register(new URL('sw.js', base), {scope: base.pathname})
      .catch(error => console.warn('Offline reading is unavailable:', error));
  }
})();
