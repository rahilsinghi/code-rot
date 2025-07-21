#!/usr/bin/env python3
"""
Progressive Web App (PWA) Manager
Mobile-first support with offline capabilities and push notifications
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from flask import Flask, render_template, request, jsonify, send_from_directory
import logging

class PWAManager:
    def __init__(self, app: Flask = None):
        self.app = app
        self.static_dir = Path("static")
        self.templates_dir = Path("templates") 
        self.pwa_config = {
            "name": "Coding Practice System",
            "short_name": "CodePractice",
            "description": "AI-powered coding practice with spaced repetition",
            "version": "2.0.0",
            "theme_color": "#007bff",
            "background_color": "#ffffff",
            "display": "standalone",
            "orientation": "portrait-primary",
            "scope": "/",
            "start_url": "/",
            "lang": "en",
            "categories": ["education", "productivity", "developer"]
        }
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize PWA support with Flask app"""
        self.app = app
        self.setup_directories()
        self.generate_manifest()
        self.generate_service_worker()
        self.generate_mobile_templates()
        self.register_routes()
        
        logging.info("PWA Manager initialized with mobile-first support")
    
    def setup_directories(self):
        """Create necessary directories for PWA assets"""
        self.static_dir.mkdir(exist_ok=True)
        (self.static_dir / "icons").mkdir(exist_ok=True)
        (self.static_dir / "css").mkdir(exist_ok=True)
        (self.static_dir / "js").mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
    
    def generate_manifest(self):
        """Generate Web App Manifest for PWA"""
        manifest = {
            "name": self.pwa_config["name"],
            "short_name": self.pwa_config["short_name"],
            "description": self.pwa_config["description"],
            "version": self.pwa_config["version"],
            "theme_color": self.pwa_config["theme_color"],
            "background_color": self.pwa_config["background_color"],
            "display": self.pwa_config["display"],
            "orientation": self.pwa_config["orientation"],
            "scope": self.pwa_config["scope"],
            "start_url": self.pwa_config["start_url"],
            "lang": self.pwa_config["lang"],
            "categories": self.pwa_config["categories"],
            "icons": [
                {
                    "src": "/static/icons/icon-192x192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/static/icons/icon-512x512.png", 
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any maskable"
                }
            ],
            "screenshots": [
                {
                    "src": "/static/icons/screenshot-mobile.png",
                    "sizes": "375x812",
                    "type": "image/png",
                    "form_factor": "narrow"
                },
                {
                    "src": "/static/icons/screenshot-desktop.png",
                    "sizes": "1280x720", 
                    "type": "image/png",
                    "form_factor": "wide"
                }
            ]
        }
        
        manifest_path = self.static_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
    
    def generate_service_worker(self):
        """Generate Service Worker for offline functionality"""
        service_worker_js = '''
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
'''
        
        sw_path = self.static_dir / "sw.js"
        with open(sw_path, 'w') as f:
            f.write(service_worker_js)
    
    def generate_mobile_css(self):
        """Generate mobile-first CSS"""
        mobile_css = '''
/* Mobile-First CSS for Coding Practice PWA */

:root {
    --primary-color: #007bff;
    --success-color: #28a745;
    --warning-color: #ffc107;
    --danger-color: #dc3545;
    --info-color: #17a2b8;
    --dark-color: #343a40;
    --light-color: #f8f9fa;
    --border-radius: 8px;
    --shadow: 0 2px 4px rgba(0,0,0,0.1);
    --shadow-hover: 0 4px 8px rgba(0,0,0,0.15);
}

/* Base mobile styles */
body {
    font-size: 16px;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    overflow-x: hidden;
}

/* Mobile navigation */
.mobile-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: white;
    border-top: 1px solid #dee2e6;
    z-index: 1030;
    padding: 8px 0;
    box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
}

.mobile-nav .nav {
    justify-content: space-around;
}

.mobile-nav .nav-link {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 8px 12px;
    color: #6c757d;
    text-decoration: none;
    transition: color 0.3s;
}

.mobile-nav .nav-link.active,
.mobile-nav .nav-link:hover {
    color: var(--primary-color);
}

.mobile-nav .nav-link i {
    font-size: 18px;
    margin-bottom: 4px;
}

.mobile-nav .nav-link span {
    font-size: 12px;
    font-weight: 500;
}

/* Content padding for mobile nav */
.main-content {
    padding-bottom: 80px;
}

/* Mobile-optimized cards */
.dashboard-card {
    margin-bottom: 1rem;
    border: none;
    border-radius: var(--border-radius);
    box-shadow: var(--shadow);
    transition: box-shadow 0.3s;
}

.dashboard-card:hover {
    box-shadow: var(--shadow-hover);
}

/* Mobile metrics */
.mobile-metric {
    text-align: center;
    padding: 1rem;
    background: white;
    border-radius: var(--border-radius);
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
}

.mobile-metric .metric-value {
    font-size: 2rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
}

.mobile-metric .metric-label {
    color: #6c757d;
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Touch-friendly buttons */
.btn {
    min-height: 44px;
    padding: 12px 20px;
    border-radius: var(--border-radius);
    font-weight: 500;
    transition: all 0.3s;
}

.btn-fab {
    position: fixed;
    bottom: 90px;
    right: 20px;
    width: 56px;
    height: 56px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    z-index: 1020;
}

/* Mobile forms */
.form-control {
    min-height: 44px;
    border-radius: var(--border-radius);
    border: 1px solid #ced4da;
    padding: 12px 16px;
}

.form-control:focus {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 0.2rem rgba(0,123,255,0.25);
}

/* Mobile charts */
.chart-container {
    background: white;
    border-radius: var(--border-radius);
    box-shadow: var(--shadow);
    padding: 1rem;
    margin-bottom: 1rem;
    overflow-x: auto;
}

.chart-container .js-plotly-plot {
    min-height: 300px;
}

/* Recommendation cards */
.recommendation-card {
    border-left: 4px solid var(--primary-color);
    margin-bottom: 1rem;
    border-radius: var(--border-radius);
    box-shadow: var(--shadow);
}

.recommendation-card .card-body {
    padding: 1rem;
}

.recommendation-badge {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
    margin-right: 4px;
    margin-bottom: 4px;
}

/* Activity items */
.activity-item {
    padding: 1rem;
    border-bottom: 1px solid #dee2e6;
    background: white;
}

.activity-item:last-child {
    border-bottom: none;
}

.activity-meta {
    color: #6c757d;
    font-size: 0.875rem;
}

/* Loading states */
.loading-spinner {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 200px;
}

.loading-text {
    margin-left: 0.5rem;
    color: #6c757d;
}

/* Offline indicator */
.offline-indicator {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    background: var(--warning-color);
    color: white;
    text-align: center;
    padding: 8px;
    z-index: 1040;
    transform: translateY(-100%);
    transition: transform 0.3s;
}

.offline-indicator.show {
    transform: translateY(0);
}

/* Install prompt */
.install-prompt {
    position: fixed;
    bottom: 90px;
    left: 20px;
    right: 20px;
    background: white;
    border: 1px solid #dee2e6;
    border-radius: var(--border-radius);
    padding: 1rem;
    box-shadow: var(--shadow-hover);
    z-index: 1025;
    transform: translateY(100%);
    transition: transform 0.3s;
}

.install-prompt.show {
    transform: translateY(0);
}

/* Toast notifications */
.toast-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1050;
}

.toast {
    background: white;
    border: 1px solid rgba(0,0,0,0.1);
    border-radius: var(--border-radius);
    box-shadow: var(--shadow);
    margin-bottom: 0.5rem;
}

/* Responsive adjustments */
@media (min-width: 768px) {
    .mobile-nav {
        display: none;
    }
    
    .main-content {
        padding-bottom: 0;
    }
    
    .btn-fab {
        display: none;
    }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    :root {
        --bg-color: #121212;
        --surface-color: #1e1e1e;
        --text-color: #ffffff;
        --text-secondary: #aaaaaa;
    }
    
    body {
        background-color: var(--bg-color);
        color: var(--text-color);
    }
    
    .dashboard-card,
    .mobile-metric,
    .chart-container {
        background: var(--surface-color);
        border-color: #333;
    }
    
    .mobile-nav {
        background: var(--surface-color);
        border-top-color: #333;
    }
}

/* Animation utilities */
.fade-in {
    animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

.slide-up {
    animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
    from { transform: translateY(20px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}

/* Pull-to-refresh */
.ptr-content {
    transform: translateY(var(--ptr-distance, 0px));
    transition: transform 0.3s ease-out;
}

.ptr-refresh {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 60px;
    background: var(--light-color);
    margin-top: -60px;
}

/* Haptic feedback simulation */
.btn:active,
.nav-link:active {
    transform: scale(0.98);
}
'''
        
        css_path = self.static_dir / "css" / "mobile.css"
        with open(css_path, 'w') as f:
            f.write(mobile_css)
    
    def generate_pwa_js(self):
        """Generate PWA JavaScript utilities"""
        pwa_js = '''
// PWA JavaScript Utilities
class PWAManager {
    constructor() {
        this.isOnline = navigator.onLine;
        this.deferredPrompt = null;
        this.init();
    }
    
    init() {
        this.registerServiceWorker();
        this.setupOfflineHandling();
        this.setupInstallPrompt();
        this.setupNotifications();
        this.setupPullToRefresh();
        this.bindEvents();
    }
    
    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/static/sw.js');
                console.log('SW registered:', registration);
                
                // Handle updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            this.showUpdateAvailable();
                        }
                    });
                });
            } catch (error) {
                console.log('SW registration failed:', error);
            }
        }
    }
    
    setupOfflineHandling() {
        const offlineIndicator = document.createElement('div');
        offlineIndicator.className = 'offline-indicator';
        offlineIndicator.innerHTML = '<i class="fas fa-wifi"></i> You are offline';
        document.body.appendChild(offlineIndicator);
        
        const updateOnlineStatus = () => {
            this.isOnline = navigator.onLine;
            offlineIndicator.classList.toggle('show', !this.isOnline);
            
            if (this.isOnline) {
                this.syncOfflineData();
            }
        };
        
        window.addEventListener('online', updateOnlineStatus);
        window.addEventListener('offline', updateOnlineStatus);
        updateOnlineStatus();
    }
    
    setupInstallPrompt() {
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallPrompt();
        });
        
        window.addEventListener('appinstalled', () => {
            console.log('PWA installed');
            this.hideInstallPrompt();
            this.showToast('App installed successfully!', 'success');
        });
    }
    
    showInstallPrompt() {
        const prompt = document.createElement('div');
        prompt.className = 'install-prompt';
        prompt.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-download me-2"></i>
                <div class="flex-grow-1">
                    <strong>Install App</strong>
                    <div class="small text-muted">Get the full experience</div>
                </div>
                <button class="btn btn-primary btn-sm ms-2" onclick="pwaManager.installApp()">Install</button>
                <button class="btn btn-outline-secondary btn-sm ms-1" onclick="pwaManager.hideInstallPrompt()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        document.body.appendChild(prompt);
        
        setTimeout(() => prompt.classList.add('show'), 100);
        this.installPromptElement = prompt;
    }
    
    async installApp() {
        if (this.deferredPrompt) {
            this.deferredPrompt.prompt();
            const result = await this.deferredPrompt.userChoice;
            console.log('Install result:', result);
            this.deferredPrompt = null;
            this.hideInstallPrompt();
        }
    }
    
    hideInstallPrompt() {
        if (this.installPromptElement) {
            this.installPromptElement.classList.remove('show');
            setTimeout(() => {
                this.installPromptElement.remove();
                this.installPromptElement = null;
            }, 300);
        }
    }
    
    async setupNotifications() {
        if ('Notification' in window && 'serviceWorker' in navigator) {
            const permission = await Notification.requestPermission();
            if (permission === 'granted') {
                console.log('Notifications enabled');
            }
        }
    }
    
    setupPullToRefresh() {
        let startY = 0;
        let currentY = 0;
        let distance = 0;
        let isRefreshing = false;
        
        const container = document.querySelector('.main-content');
        if (!container) return;
        
        container.addEventListener('touchstart', (e) => {
            if (window.scrollY === 0) {
                startY = e.touches[0].pageY;
            }
        });
        
        container.addEventListener('touchmove', (e) => {
            if (startY === 0 || isRefreshing) return;
            
            currentY = e.touches[0].pageY;
            distance = currentY - startY;
            
            if (distance > 0 && window.scrollY === 0) {
                e.preventDefault();
                distance = Math.min(distance, 100);
                container.style.setProperty('--ptr-distance', distance + 'px');
                
                if (distance > 60) {
                    this.showPullToRefreshIndicator();
                }
            }
        });
        
        container.addEventListener('touchend', () => {
            if (distance > 60 && !isRefreshing) {
                this.triggerRefresh();
            }
            
            startY = 0;
            currentY = 0;
            distance = 0;
            container.style.setProperty('--ptr-distance', '0px');
        });
    }
    
    showPullToRefreshIndicator() {
        let indicator = document.querySelector('.ptr-refresh');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'ptr-refresh';
            indicator.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Release to refresh';
            document.querySelector('.main-content').prepend(indicator);
        }
    }
    
    async triggerRefresh() {
        if (typeof loadDashboard === 'function') {
            await loadDashboard();
            this.showToast('Dashboard refreshed', 'success');
        }
        
        setTimeout(() => {
            const indicator = document.querySelector('.ptr-refresh');
            if (indicator) indicator.remove();
        }, 1000);
    }
    
    async syncOfflineData() {
        if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
            try {
                await navigator.serviceWorker.ready.then(registration => {
                    return registration.sync.register('problem-completion');
                });
                console.log('Background sync registered');
            } catch (error) {
                console.log('Background sync failed:', error);
            }
        }
    }
    
    showUpdateAvailable() {
        const updateBanner = document.createElement('div');
        updateBanner.className = 'alert alert-info alert-dismissible';
        updateBanner.innerHTML = `
            <strong>Update Available!</strong> 
            A new version is ready.
            <button class="btn btn-sm btn-outline-primary ms-2" onclick="pwaManager.applyUpdate()">
                Update Now
            </button>
        `;
        document.body.insertBefore(updateBanner, document.body.firstChild);
    }
    
    async applyUpdate() {
        if ('serviceWorker' in navigator) {
            const registration = await navigator.serviceWorker.getRegistration();
            if (registration && registration.waiting) {
                registration.waiting.postMessage({ type: 'SKIP_WAITING' });
                window.location.reload();
            }
        }
    }
    
    showToast(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'primary'} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;
        
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(toast);
        toast.classList.add('show');
        
        setTimeout(() => {
            toast.remove();
        }, duration);
    }
    
    bindEvents() {
        // Add haptic feedback for supported devices
        document.addEventListener('touchstart', (e) => {
            if (e.target.matches('.btn, .nav-link, .card')) {
                if (navigator.vibrate) {
                    navigator.vibrate(10);
                }
            }
        });
    }
    
    // Offline storage utilities
    async storeOfflineData(storeName, data) {
        if ('indexedDB' in window) {
            const db = await this.openDB();
            const transaction = db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            return store.add(data);
        }
    }
    
    async openDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('CodingPracticeDB', 1);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                if (!db.objectStoreNames.contains('pending-completions')) {
                    db.createObjectStore('pending-completions', { keyPath: 'id', autoIncrement: true });
                }
                
                if (!db.objectStoreNames.contains('pending-reviews')) {
                    db.createObjectStore('pending-reviews', { keyPath: 'id', autoIncrement: true });
                }
            };
        });
    }
}

// Initialize PWA Manager
const pwaManager = new PWAManager();

// Export for global use
window.pwaManager = pwaManager;
'''
        
        js_path = self.static_dir / "js" / "pwa.js"
        with open(js_path, 'w') as f:
            f.write(pwa_js)
    
    def generate_mobile_templates(self):
        """Generate mobile-optimized HTML templates"""
        self.generate_mobile_css()
        self.generate_pwa_js()
        
        # Generate offline page
        offline_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Offline - Coding Practice</title>
    <link href="/static/css/mobile.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="d-flex align-items-center justify-content-center min-vh-100 bg-light">
    <div class="text-center">
        <div class="mb-4">
            <i class="fas fa-wifi-slash fa-4x text-muted"></i>
        </div>
        <h2 class="mb-3">You're Offline</h2>
        <p class="text-muted mb-4">
            Don't worry! You can still view your cached progress<br>
            and the app will sync when you're back online.
        </p>
        <div class="d-grid gap-2 col-6 mx-auto">
            <button class="btn btn-primary" onclick="window.location.reload()">
                <i class="fas fa-sync-alt me-2"></i>Try Again
            </button>
            <a href="/" class="btn btn-outline-secondary">
                <i class="fas fa-home me-2"></i>Go Home
            </a>
        </div>
    </div>
</body>
</html>
'''
        
        offline_path = self.templates_dir / "offline.html"
        with open(offline_path, 'w') as f:
            f.write(offline_html)
    
    def register_routes(self):
        """Register PWA-specific routes"""
        @self.app.route('/manifest.json')
        def serve_manifest():
            return send_from_directory(self.static_dir, 'manifest.json')
        
        @self.app.route('/sw.js')
        def serve_service_worker():
            return send_from_directory(self.static_dir, 'sw.js')
        
        @self.app.route('/offline')
        def offline_page():
            return render_template('offline.html')
        
        @self.app.route('/api/pwa/install-stats', methods=['POST'])
        def track_install():
            # Track PWA installation for analytics
            return jsonify({'status': 'tracked'})
        
        @self.app.route('/api/pwa/notification-permission', methods=['POST'])
        def notification_permission():
            # Handle notification permission requests
            data = request.get_json()
            permission = data.get('permission', 'default')
            # Store permission status if needed
            return jsonify({'status': 'recorded', 'permission': permission})
    
    def generate_push_notification(self, title: str, body: str, 
                                 icon: str = '/static/icons/icon-192x192.png',
                                 data: Dict = None):
        """Generate push notification payload"""
        return {
            'title': title,
            'body': body,
            'icon': icon,
            'badge': '/static/icons/badge-72x72.png',
            'vibrate': [200, 100, 200],
            'data': data or {},
            'actions': [
                {
                    'action': 'view',
                    'title': 'View Progress',
                    'icon': '/static/icons/action-view.png'
                },
                {
                    'action': 'dismiss', 
                    'title': 'Dismiss',
                    'icon': '/static/icons/action-dismiss.png'
                }
            ]
        }
    
    def get_pwa_status(self) -> Dict:
        """Get PWA configuration and status"""
        return {
            'name': self.pwa_config['name'],
            'version': self.pwa_config['version'],
            'display': self.pwa_config['display'],
            'theme_color': self.pwa_config['theme_color'],
            'features': {
                'offline_support': True,
                'push_notifications': True,
                'background_sync': True,
                'install_prompt': True,
                'pull_to_refresh': True
            },
            'assets_generated': {
                'manifest': (self.static_dir / "manifest.json").exists(),
                'service_worker': (self.static_dir / "sw.js").exists(),
                'mobile_css': (self.static_dir / "css" / "mobile.css").exists(),
                'pwa_js': (self.static_dir / "js" / "pwa.js").exists(),
                'offline_page': (self.templates_dir / "offline.html").exists()
            }
        }

if __name__ == "__main__":
    # Example usage
    from flask import Flask
    app = Flask(__name__)
    pwa = PWAManager(app)
    
    print("PWA Manager Status:")
    status = pwa.get_pwa_status()
    for key, value in status.items():
        print(f"  {key}: {value}") 