const CACHE='consulta-rg-offline-v4';
const CORE=['/static/offline.html','/static/style.css','/static/manifest.json','/static/icon-192.svg','/static/icon-512.svg','/static/jsQR.js'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET') return;
  if(e.request.mode==='navigate'){e.respondWith(fetch(e.request).catch(()=>caches.match('/static/offline.html')));return;}
  if(new URL(e.request.url).origin===location.origin){
    e.respondWith(fetch(e.request).then(r=>{if(r.ok){const copy=r.clone();caches.open(CACHE).then(c=>c.put(e.request,copy));}return r;}).catch(()=>caches.match(e.request)));
  }
});