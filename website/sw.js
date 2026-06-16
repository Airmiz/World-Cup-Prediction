/* World Cup 2026 — service worker.
 * Precache the app shell so the site loads instantly and works offline as a shell.
 * Network-first for same-origin requests (so live data and pages stay fresh, with a
 * cache fallback when offline). Cross-origin requests (ESPN, Wikipedia, Wikidata,
 * the results CSV, club/photo lookups) are left completely untouched — never cached,
 * never intercepted — so live scores are always real-time.
 */
const CACHE = "wc26-v2";
const SHELL = ["./", "index.html", "live.html", "fantasy.html", "manifest.webmanifest",
               "icon-192.png", "icon-512.png", "og.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  // only handle our own same-origin GETs; everything cross-origin passes straight through
  if (e.request.method !== "GET" || url.origin !== self.location.origin) return;
  e.respondWith(
    fetch(e.request)
      .then((r) => { const copy = r.clone(); caches.open(CACHE).then((c) => c.put(e.request, copy)); return r; })
      .catch(() => caches.match(e.request).then((m) => m || caches.match("live.html") || caches.match("index.html")))
  );
});
