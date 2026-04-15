/* KF Portionsrechner — Service Worker
   Strategie: Stale-while-revalidate für die App-Shell.
   Daten liegen in IndexedDB (vom Browser eh offline verfügbar),
   der SW cacht nur die statischen Assets. */

const CACHE_VERSION = 'v1';
const CACHE_NAME = `kuefa-${CACHE_VERSION}`;

// Relative Pfade, damit es unter https://<user>.github.io/Kuefa-calculator/ funktioniert
const APP_SHELL = [
  './',
  './index.html'
];

// Install: App-Shell vorab cachen
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL))
  );
  // Neue Version soll sofort aktiv werden (nach clients.claim in activate)
  self.skipWaiting();
});

// Activate: alte Caches löschen
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// Fetch: Stale-while-revalidate für GETs im eigenen Scope
self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  // Nur eigene Origin cachen
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    caches.open(CACHE_NAME).then(async (cache) => {
      const cached = await cache.match(req, { ignoreSearch: false });
      const network = fetch(req).then((resp) => {
        // Nur erfolgreiche Responses cachen
        if (resp && resp.status === 200 && resp.type === 'basic') {
          cache.put(req, resp.clone());
          // Clients benachrichtigen, wenn neue Version da ist
          if (cached && cached.status === 200) {
            cached.clone().text().then((oldText) => {
              resp.clone().text().then((newText) => {
                if (oldText !== newText) {
                  self.clients.matchAll().then((clients) => {
                    clients.forEach((c) => c.postMessage({ type: 'SW_UPDATE_AVAILABLE' }));
                  });
                }
              }).catch(() => {});
            }).catch(() => {});
          }
        }
        return resp;
      }).catch(() => cached); // offline → Cache
      return cached || network;
    })
  );
});

// Nachricht vom Client: sofort aktualisieren
self.addEventListener('message', (event) => {
  if (event.data === 'SKIP_WAITING') self.skipWaiting();
});
