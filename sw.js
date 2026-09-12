// Inkstone service worker: cache-first for offline editing
const CACHE = 'inkstone-v1';
const ASSETS = [
  './', './index.html', './i18n.js', './manifest.json', './icon.svg',
  './vendor/marked.min.js', './vendor/katex.min.js', './vendor/auto-render.min.js',
  './vendor/mermaid.min.js', './vendor/dom-to-image-more.min.js',
  './vendor/purify.min.js', './vendor/fonts/KaTeX_Main-Regular.woff2',
  './vendor/fonts/KaTeX_Math-Italic.woff2', './vendor/fonts/KaTeX_Size1-Regular.woff2',
  './vendor/fonts/KaTeX_Size2-Regular.woff2', './vendor/fonts/KaTeX_AMS-Regular.woff2'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request).then(hit => hit || fetch(e.request).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put(e.request, copy));
      return res;
    }).catch(() => caches.match('./index.html')))
  );
});
