/* KF Portionsrechner — Service Worker
   Strategie: Stale-while-revalidate für die App-Shell.
   Daten liegen in IndexedDB (vom Browser eh offline verfügbar),
   der SW cacht nur die statischen Assets. */

const CACHE_VERSION = 'v2';
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
          // Clients benachrichtigen, wenn neue Version da ist (best-effort)
          if (cached && cached.status === 200) {
            cached.clone().text().then((oldText) => {
              resp.clone().text().then((newText) => {
                if (oldText !== newText) {
                  broadcastUpdate();
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

// Hilfsfunktion: alle Clients über neue Version informieren
function broadcastUpdate() {
  self.clients.matchAll({ includeUncontrolled: true }).then((clients) => {
    clients.forEach((c) => c.postMessage({ type: 'SW_UPDATE_AVAILABLE' }));
  });
}

// Aktive Update-Prüfung (vom Client angefragt).
// Holt index.html frisch (Cache-Bypass), vergleicht mit gecachter Version
// und antwortet über den MessageChannel-Port.
async function checkForUpdate() {
  try {
    const cache = await caches.open(CACHE_NAME);
    const cachedResp = await cache.match('./index.html') || await cache.match('./');
    if (!cachedResp) return { updateAvailable: false, reason: 'no-cache' };
    const networkResp = await fetch('./index.html', { cache: 'no-store' });
    if (!networkResp || networkResp.status !== 200) {
      return { updateAvailable: false, reason: 'network-fail' };
    }
    const [oldText, newText] = await Promise.all([
      cachedResp.clone().text(),
      networkResp.clone().text()
    ]);
    if (oldText !== newText) {
      // Cache gleich aktualisieren, damit ein reload die neue Version bekommt
      await cache.put('./index.html', networkResp.clone());
      return { updateAvailable: true };
    }
    return { updateAvailable: false };
  } catch (e) {
    return { updateAvailable: false, reason: 'error', error: String(e) };
  }
}

// Nachrichten vom Client
self.addEventListener('message', (event) => {
  if (event.data === 'SKIP_WAITING') {
    self.skipWaiting();
    return;
  }
  if (event.data && event.data.type === 'CHECK_UPDATE') {
    const port = event.ports && event.ports[0];
    checkForUpdate().then((result) => {
      if (port) port.postMessage(result);
      if (result.updateAvailable) broadcastUpdate();
    });
  }
});
