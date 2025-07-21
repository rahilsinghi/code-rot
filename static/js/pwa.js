
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
