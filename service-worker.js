const CACHE_NAME = "studyflow-v1";
const urlsToCache = ["/", "/manifest.json", "/favicon.png", "/icon-192.png", "/Icon-512.png", "/app.py"];

self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache)));
});

self.addEventListener("fetch", event => {
  event.respondWith(caches.match(event.request).then(res => res || fetch(event.request)));
});

self.addEventListener("push", event => {
  const data = event.data? event.data.text() : "StudyFlow 📚 - Nouvelle notification";
  event.waitUntil(
    self.registration.showNotification("StudyFlow", {
      body: data,
      icon: "/Icon-512.png",
      badge: "/favicon.png"
    })
  );
});
