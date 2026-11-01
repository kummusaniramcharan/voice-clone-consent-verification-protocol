/**
 * VoiceClone Service Worker
 * Caches the application shell, UI assets, WASM runtimes, and neural weights
 * to ensure resilience against unstable or slow venue/college Wi-Fi.
 */

const CACHE_NAME = 'voiceclone-cache-v3';
const APP_SHELL = [
  '/',
  '/index.html',
  '/train.html',
  '/how-it-works.html',
  '/scam-safety.html',
  '/about.html',
  '/selftest.html',
  '/css/styles.css',
  '/js/features.js',
  '/js/model.js',
  '/js/worker.js',
  '/js/train.js',
  '/js/ui.js',
  '/data/helplines.json',
  '/samples/sample_human.mp3',
  '/samples/sample_ai.mp3'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(APP_SHELL).catch((err) => {
        console.warn('Some shell files could not be precached:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Cache-first for WASM, ONNX, and model weights
  if (
    url.pathname.endsWith('.wasm') || 
    url.pathname.endsWith('.onnx') || 
    url.hostname.includes('huggingface.co') ||
    url.hostname.includes('jsdelivr.net')
  ) {
    event.respondWith(
      caches.open(CACHE_NAME).then((cache) => {
        return cache.match(event.request).then((cachedResponse) => {
          if (cachedResponse) return cachedResponse;
          return fetch(event.request).then((networkResponse) => {
            if (networkResponse && networkResponse.status === 200) {
              cache.put(event.request, networkResponse.clone());
            }
            return networkResponse;
          });
        });
      })
    );
    return;
  }

  // Network-first with cache fallback for standard application requests
  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request);
    })
  );
});
