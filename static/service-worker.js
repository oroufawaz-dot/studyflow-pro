const CACHE_NAME = "studyflow-v4";
self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll([".", "icon-512.png"])));
});
self.addEventListener("fetch", event => {
  event.respondWith(caches.match(event.request).then(r => r || fetch(event.request)));
});
self.addEventListener("push", function(event) {
  const data = event.data? event.data.text() : "Rappel StudyFlow";
  event.waitUntil(
    self.registration.showNotification("StudyFlow 📚", {
      body: data,
      icon: "icon-512.png",
      badge: "favicon.png",
      vibrate: [200, 100, 200]
    })
  );
});
