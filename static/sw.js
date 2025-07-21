
// Service Worker for Coding Practice System PWA
const CACHE_NAME = 'coding-practice-v2.0.0';
const OFFLINE_URL = '/offline';

const CACHE_URLS = [
    '/',
    '/static/css/mobile.css',
    '/static/js/pwa.js',
    '/static/js/offline.js',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    '/offline',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
    'https://cdn.plot.ly/plotly-latest.min.js',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js'
];

// Install event - cache resources
self.addEventListener('install', (event) => {
    console.log('Service Worker installing');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Caching app shell');
                return cache.addAll(CACHE_URLS);
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker activating');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', (event) => {
    if (event.request.mode === 'navigate') {
        // Handle navigation requests
        event.respondWith(
            fetch(event.request)
                .catch(() => {
                    return caches.open(CACHE_NAME)
                        .then((cache) => {
                            return cache.match(OFFLINE_URL);
                        });
                })
        );
    } else if (event.request.url.startsWith(self.location.origin)) {
        // Handle same-origin requests
        event.respondWith(
            caches.match(event.request)
                .then((cachedResponse) => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    
                    return fetch(event.request)
                        .then((response) => {
                            // Cache successful responses
                            if (response.status === 200) {
                                const responseClone = response.clone();
                                caches.open(CACHE_NAME)
                                    .then((cache) => {
                                        cache.put(event.request, responseClone);
                                    });
                            }
                            return response;
                        });
                })
        );
    }
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
    console.log('Background sync triggered:', event.tag);
    
    if (event.tag === 'problem-completion') {
        event.waitUntil(syncProblemCompletion());
    } else if (event.tag === 'review-completion') {
        event.waitUntil(syncReviewCompletion());
    }
});

// Push notification handling
self.addEventListener('push', (event) => {
    console.log('Push message received');
    
    const options = {
        body: event.data ? event.data.text() : 'New achievement unlocked!',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/badge-72x72.png',
        vibrate: [200, 100, 200],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'view',
                title: 'View Progress',
                icon: '/static/icons/action-view.png'
            },
            {
                action: 'dismiss',
                title: 'Dismiss',
                icon: '/static/icons/action-dismiss.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('Coding Practice', options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
    console.log('Notification clicked:', event.action);
    
    event.notification.close();
    
    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// Sync functions
async function syncProblemCompletion() {
    try {
        const pendingData = await getStoredData('pending-completions');
        for (const data of pendingData) {
            await fetch('/api/complete_problem', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
        }
        await clearStoredData('pending-completions');
        console.log('Problem completions synced');
    } catch (error) {
        console.error('Sync failed:', error);
    }
}

async function syncReviewCompletion() {
    try {
        const pendingData = await getStoredData('pending-reviews');
        for (const data of pendingData) {
            await fetch('/api/complete_review', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
        }
        await clearStoredData('pending-reviews');
        console.log('Review completions synced');
    } catch (error) {
        console.error('Review sync failed:', error);
    }
}

// IndexedDB helpers
async function getStoredData(storeName) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('CodingPracticeDB', 1);
        request.onsuccess = (event) => {
            const db = event.target.result;
            const transaction = db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const getAllRequest = store.getAll();
            
            getAllRequest.onsuccess = () => {
                resolve(getAllRequest.result);
            };
        };
        request.onerror = () => reject(request.error);
    });
}

async function clearStoredData(storeName) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('CodingPracticeDB', 1);
        request.onsuccess = (event) => {
            const db = event.target.result;
            const transaction = db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const clearRequest = store.clear();
            
            clearRequest.onsuccess = () => resolve();
        };
        request.onerror = () => reject(request.error);
    });
}
