// Preserve bookmarks while recordings live with their reference concept.
(() => {
  const link = document.querySelector('[data-audio-redirect]');
  if (!link) return;
  const target = new URL(link.href);
  const fragment = location.hash.slice(1);
  const segments = ['meaning','stages','why','recognise','test','change','together','remember'];
  if (link.dataset.audioRedirect === 'listen-explanation' && segments.includes(fragment)) target.hash = 'audio-' + fragment;
  location.replace(target.href);
})();
