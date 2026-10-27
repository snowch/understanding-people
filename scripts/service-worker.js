// Copyright © 2026 Christopher Snow
// The build substitutes a content hash and the generated book's relative URLs.
const CACHE_PREFIX = 'understanding-people-';
const CACHE_NAME = CACHE_PREFIX + '__VERSION__';
const FILES = __FILES__;
const absolute = path => new URL(path, self.registration.scope).href;
const known = new Set(FILES.map(absolute));

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(FILES.map(absolute))));
});
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(key => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME)
      .map(key => caches.delete(key)));
    await self.clients.claim();
  })());
});
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  url.search = '';
  if (event.request.method !== 'GET' || !known.has(url.href)) return;
  event.respondWith((async () => {
    try {
      const response = await fetch(event.request);
      if (response.ok || response.status < 500) return response;
    } catch { /* The saved edition remains available without a network. */ }
    const cache = await caches.open(CACHE_NAME);
    return (await cache.match(url.href)) || Response.error();
  })());
});
