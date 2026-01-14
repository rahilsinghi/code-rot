/**
 * Cache Manager
 * Client-side caching with localStorage, sessionStorage, and IndexedDB
 */

class CacheManager {
    constructor() {
        this.memoryCache = new Map();
        this.maxMemoryItems = 100;
        this.defaultTTL = 5 * 60 * 1000; // 5 minutes
        this.dbName = 'CodingPracticeCache';
        this.dbVersion = 1;
        this.db = null;
        
        this.init();
    }

    async init() {
        // Initialize IndexedDB for larger data
        try {
            this.db = await this.openIndexedDB();
        } catch (e) {
            console.warn('IndexedDB not available, falling back to localStorage');
        }
    }

    openIndexedDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                if (!db.objectStoreNames.contains('cache')) {
                    const store = db.createObjectStore('cache', { keyPath: 'key' });
                    store.createIndex('expiry', 'expiry', { unique: false });
                }
            };
        });
    }

    /**
     * Get a cached item
     * @param {string} key - Cache key
     * @returns {any} Cached value or null
     */
    async get(key) {
        // Check memory cache first
        const memoryItem = this.memoryCache.get(key);
        if (memoryItem) {
            if (Date.now() < memoryItem.expiry) {
                return memoryItem.value;
            }
            this.memoryCache.delete(key);
        }

        // Check localStorage
        const localItem = localStorage.getItem(`cache_${key}`);
        if (localItem) {
            try {
                const parsed = JSON.parse(localItem);
                if (Date.now() < parsed.expiry) {
                    // Promote to memory cache
                    this.setMemory(key, parsed.value, parsed.expiry - Date.now());
                    return parsed.value;
                }
                localStorage.removeItem(`cache_${key}`);
            } catch (e) {
                localStorage.removeItem(`cache_${key}`);
            }
        }

        // Check IndexedDB
        if (this.db) {
            try {
                const dbItem = await this.getFromIndexedDB(key);
                if (dbItem && Date.now() < dbItem.expiry) {
                    this.setMemory(key, dbItem.value, dbItem.expiry - Date.now());
                    return dbItem.value;
                }
            } catch (e) {
                console.warn('Error reading from IndexedDB:', e);
            }
        }

        return null;
    }

    /**
     * Set a cached item
     * @param {string} key - Cache key
     * @param {any} value - Value to cache
     * @param {number} ttl - Time to live in milliseconds
     * @param {string} storage - Storage type: 'memory', 'local', 'indexeddb'
     */
    async set(key, value, ttl = this.defaultTTL, storage = 'local') {
        const expiry = Date.now() + ttl;

        // Always set in memory
        this.setMemory(key, value, ttl);

        if (storage === 'local' || storage === 'both') {
            try {
                const item = JSON.stringify({ value, expiry });
                if (item.length < 5000000) { // 5MB limit
                    localStorage.setItem(`cache_${key}`, item);
                }
            } catch (e) {
                console.warn('localStorage full, falling back to IndexedDB');
                storage = 'indexeddb';
            }
        }

        if ((storage === 'indexeddb' || storage === 'both') && this.db) {
            try {
                await this.setInIndexedDB(key, value, expiry);
            } catch (e) {
                console.warn('Error writing to IndexedDB:', e);
            }
        }
    }

    setMemory(key, value, ttl) {
        // Evict oldest items if at capacity
        if (this.memoryCache.size >= this.maxMemoryItems) {
            const firstKey = this.memoryCache.keys().next().value;
            this.memoryCache.delete(firstKey);
        }

        this.memoryCache.set(key, {
            value,
            expiry: Date.now() + ttl
        });
    }

    getFromIndexedDB(key) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['cache'], 'readonly');
            const store = transaction.objectStore('cache');
            const request = store.get(key);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        });
    }

    setInIndexedDB(key, value, expiry) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['cache'], 'readwrite');
            const store = transaction.objectStore('cache');
            const request = store.put({ key, value, expiry });
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve();
        });
    }

    /**
     * Remove a cached item
     */
    async remove(key) {
        this.memoryCache.delete(key);
        localStorage.removeItem(`cache_${key}`);
        
        if (this.db) {
            try {
                await this.removeFromIndexedDB(key);
            } catch (e) {
                console.warn('Error removing from IndexedDB:', e);
            }
        }
    }

    removeFromIndexedDB(key) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['cache'], 'readwrite');
            const store = transaction.objectStore('cache');
            const request = store.delete(key);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve();
        });
    }

    /**
     * Clear all cached items
     */
    async clear() {
        this.memoryCache.clear();
        
        // Clear localStorage cache items
        const keysToRemove = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key.startsWith('cache_')) {
                keysToRemove.push(key);
            }
        }
        keysToRemove.forEach(key => localStorage.removeItem(key));

        // Clear IndexedDB
        if (this.db) {
            try {
                await this.clearIndexedDB();
            } catch (e) {
                console.warn('Error clearing IndexedDB:', e);
            }
        }
    }

    clearIndexedDB() {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['cache'], 'readwrite');
            const store = transaction.objectStore('cache');
            const request = store.clear();
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve();
        });
    }

    /**
     * Clean up expired items
     */
    async cleanup() {
        const now = Date.now();

        // Clean memory cache
        for (const [key, item] of this.memoryCache) {
            if (now >= item.expiry) {
                this.memoryCache.delete(key);
            }
        }

        // Clean localStorage
        const keysToRemove = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key.startsWith('cache_')) {
                try {
                    const item = JSON.parse(localStorage.getItem(key));
                    if (now >= item.expiry) {
                        keysToRemove.push(key);
                    }
                } catch (e) {
                    keysToRemove.push(key);
                }
            }
        }
        keysToRemove.forEach(key => localStorage.removeItem(key));

        // Clean IndexedDB
        if (this.db) {
            try {
                await this.cleanupIndexedDB(now);
            } catch (e) {
                console.warn('Error cleaning up IndexedDB:', e);
            }
        }
    }

    cleanupIndexedDB(now) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['cache'], 'readwrite');
            const store = transaction.objectStore('cache');
            const index = store.index('expiry');
            const range = IDBKeyRange.upperBound(now);
            
            const request = index.openCursor(range);
            request.onerror = () => reject(request.error);
            request.onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    cursor.delete();
                    cursor.continue();
                } else {
                    resolve();
                }
            };
        });
    }

    /**
     * Get or set pattern - fetch from cache or execute function
     * @param {string} key - Cache key
     * @param {Function} fetchFn - Function to execute if cache miss
     * @param {number} ttl - Time to live
     */
    async getOrSet(key, fetchFn, ttl = this.defaultTTL, storage = 'local') {
        const cached = await this.get(key);
        if (cached !== null) {
            return cached;
        }

        const value = await fetchFn();
        await this.set(key, value, ttl, storage);
        return value;
    }

    /**
     * Cache API responses
     */
    async fetchWithCache(url, options = {}, ttl = this.defaultTTL) {
        const cacheKey = `api_${url}_${JSON.stringify(options)}`;
        
        return this.getOrSet(cacheKey, async () => {
            const response = await fetch(url, options);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        }, ttl);
    }

    /**
     * Get cache statistics
     */
    getStats() {
        let localStorageSize = 0;
        let localStorageCount = 0;
        
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key.startsWith('cache_')) {
                localStorageSize += localStorage.getItem(key).length;
                localStorageCount++;
            }
        }

        return {
            memoryItems: this.memoryCache.size,
            localStorageItems: localStorageCount,
            localStorageSize: `${(localStorageSize / 1024).toFixed(2)} KB`
        };
    }
}

// Initialize and expose globally
const cache = new CacheManager();
window.cache = cache;

// Run cleanup periodically
setInterval(() => cache.cleanup(), 60000);




