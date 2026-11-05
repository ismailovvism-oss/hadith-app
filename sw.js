/* Библиотека хадисов — офлайн-слой. Всё, что открыл читатель, остаётся в кеше.
   Сеть в приоритете: обновления доезжают сразу, кеш отвечает, только когда сети нет или она молчит
   дольше NET_WAIT. Аварийный выключатель — открыть сайт с «?nosw=1».
   На github.io адрес общий с «Библиотекой тафсиров», поэтому трогаем только свои кеши «hd-». */
const CACHE = "hd-1";
const NET_WAIT = 3000;
const SHELL = ["./", "index.html", "manifest.webmanifest", "icons/app-icon.svg", "icons/app-icon-192.png", "data/config.json"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(k => Promise.all(k.filter(n => n.startsWith("hd-") && n !== CACHE).map(n => caches.delete(n))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  const fonts = /(^|\.)(googleapis|gstatic)\.com$/.test(url.hostname);
  if (e.request.method !== "GET" || !(url.origin === location.origin || fonts)) return;
  e.respondWith(fresh(e.request));
});

async function fresh(req) {
  const cache = await caches.open(CACHE);
  const net = fetch(req).then(r => {
    if (r.ok || r.type === "opaque") cache.put(req, r.clone());
    return r;
  });
  const wait = new Promise(res => setTimeout(res, NET_WAIT));
  const first = await Promise.race([net.catch(() => null), wait]);
  if (first) return first;
  const saved = await cache.match(req) || (req.mode === "navigate" && await cache.match("index.html"));
  return saved || net;
}
