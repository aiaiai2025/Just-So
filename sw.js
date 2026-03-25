// ══════════════════════════════════════════════════════════════════════════════
// Stem Player — Service Worker
//
// HOW TO UPDATE when you change songs or audio files:
//   Bump the version number below (e.g. 'v2' → 'v3') and re-upload this file.
//   The next time a user visits with internet, everything re-caches automatically.
// ══════════════════════════════════════════════════════════════════════════════
const CACHE_VERSION = 'v1';
const CACHE_NAME    = 'stem-player-' + CACHE_VERSION;

// App shell — always cache these
const SHELL = [
    './',
    './index.html',
    './songs.json',
    './manifest.json',
];

// ── Install: cache shell + all audio files listed in songs.json ──────────────
self.addEventListener('install', event => {
    event.waitUntil(
        (async () => {
            const cache = await caches.open(CACHE_NAME);

            // Cache the app shell
            await cache.addAll(SHELL);

            // Read songs.json and cache every audio file it references
            try {
                const resp = await fetch('./songs.json');
                if (resp.ok) {
                    const data  = await resp.json();
                    const songs = Array.isArray(data) ? data : (data.songs || []);
                    const audioUrls = songs.flatMap(s => [s.vocal, s.instr]).filter(Boolean);
                    // Cache audio files one at a time so a single failure doesn't abort all
                    for (const url of audioUrls) {
                        try {
                            await cache.add(url);
                        } catch(e) {
                            console.warn('[SW] Could not cache:', url, e.message);
                        }
                    }
                }
            } catch(e) {
                console.warn('[SW] Could not read songs.json during install:', e.message);
            }

            // Skip waiting so the new SW activates immediately
            await self.skipWaiting();
        })()
    );
});

// ── Activate: delete old caches ───────────────────────────────────────────────
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys()
            .then(keys => Promise.all(
                keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
            ))
            .then(() => self.clients.claim())
    );
});

// ── Fetch: cache-first, fall back to network ──────────────────────────────────
self.addEventListener('fetch', event => {
    // Only handle GET requests
    if (event.request.method !== 'GET') return;

    event.respondWith(
        caches.match(event.request).then(cached => {
            if (cached) return cached;
            // Not in cache — try network, and cache the response for next time
            return fetch(event.request).then(response => {
                if (response.ok) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                }
                return response;
            }).catch(() => {
                // Network failed and nothing cached — return a simple offline message
                // (only affects non-audio requests; audio is pre-cached at install time)
                return new Response('Offline — content not cached', {
                    status: 503,
                    headers: { 'Content-Type': 'text/plain' }
                });
            });
        })
    );
});
