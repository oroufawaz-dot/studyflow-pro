// StudyFlow - Service Worker pour notifications même app fermée
self.addEventListener('install', function(event) {
  self.skipWaiting();
});

self.addEventListener('activate', function(event) {
  event.waitUntil(clients.claim());
});

self.addEventListener('push', function(event) {
  let data = {title: 'StudyFlow Parakou', body: '🔔 Rappel de tâche / cours!'};
  try {
    if (event.data) {
      data = event.data.json();
    }
  } catch(e) {}
  
  const options = {
    body: data.body,
    icon: '0e3309b2-d8ee-6996-3018-5d74e8147d8d.jpeg',
    badge: '0e3309b2-d8ee-6996-3018-5d74e8147d8d.jpeg',
    vibrate: [200, 100, 200],
    data: { url: '/' }
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({type: 'window'}).then(function(clientList) {
      for (let client of clientList) {
        if (client.url === '/' && 'focus' in client) return client.focus();
      }
      if (clients.openWindow) return clients.openWindow('/');
    })
  );
});
