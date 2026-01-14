/**
 * Data Export & Import Manager
 * Export/import user data, settings, and progress
 */

class DataManager {
    constructor() {
        this.version = '1.0';
        this.exportableKeys = [
            'theme',
            'recentSearches',
            'settings',
            'studySessions',
            'completedProblems',
            'reviewSchedule',
            'achievements',
            'preferences'
        ];
    }

    /**
     * Export all user data
     * @param {string} format - 'json' or 'csv'
     */
    async exportData(format = 'json') {
        const data = this.collectData();
        
        if (format === 'json') {
            return this.exportAsJSON(data);
        } else if (format === 'csv') {
            return this.exportAsCSV(data);
        }
    }

    /**
     * Collect all exportable data
     */
    collectData() {
        const data = {
            meta: {
                version: this.version,
                exportedAt: new Date().toISOString(),
                source: 'Coding Practice System'
            },
            settings: {},
            progress: {},
            cache: {}
        };

        // Collect from localStorage
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            try {
                const value = localStorage.getItem(key);
                
                if (key.startsWith('cache_')) {
                    data.cache[key] = JSON.parse(value);
                } else if (this.exportableKeys.some(k => key.includes(k))) {
                    data.settings[key] = JSON.parse(value);
                } else {
                    data.progress[key] = this.tryParseJSON(value);
                }
            } catch (e) {
                data.progress[key] = localStorage.getItem(key);
            }
        }

        // Collect from sessionStorage
        data.session = {};
        for (let i = 0; i < sessionStorage.length; i++) {
            const key = sessionStorage.key(i);
            data.session[key] = this.tryParseJSON(sessionStorage.getItem(key));
        }

        return data;
    }

    tryParseJSON(str) {
        try {
            return JSON.parse(str);
        } catch {
            return str;
        }
    }

    /**
     * Export as JSON file
     */
    exportAsJSON(data) {
        const json = JSON.stringify(data, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const filename = `coding-practice-export-${this.getDateString()}.json`;
        
        this.downloadFile(blob, filename);
        window.toast?.success('Data exported successfully!');
        
        return { success: true, filename };
    }

    /**
     * Export progress as CSV
     */
    exportAsCSV(data) {
        // Create CSV for problems/progress
        const rows = [['Date', 'Problem', 'Difficulty', 'Status', 'Time', 'Notes']];
        
        // Extract problem data if available
        if (data.progress.completedProblems) {
            const problems = data.progress.completedProblems;
            if (Array.isArray(problems)) {
                problems.forEach(p => {
                    rows.push([
                        p.date || '',
                        p.name || p.problem || '',
                        p.difficulty || '',
                        p.status || 'completed',
                        p.time || '',
                        p.notes || ''
                    ]);
                });
            }
        }

        const csv = rows.map(row => 
            row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')
        ).join('\n');

        const blob = new Blob([csv], { type: 'text/csv' });
        const filename = `coding-practice-progress-${this.getDateString()}.csv`;
        
        this.downloadFile(blob, filename);
        window.toast?.success('Progress exported as CSV!');
        
        return { success: true, filename };
    }

    /**
     * Import data from file
     */
    async importData(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            
            reader.onload = async (e) => {
                try {
                    const data = JSON.parse(e.target.result);
                    const result = await this.processImport(data);
                    resolve(result);
                } catch (error) {
                    reject(new Error('Invalid file format'));
                }
            };
            
            reader.onerror = () => reject(new Error('Failed to read file'));
            reader.readAsText(file);
        });
    }

    /**
     * Process imported data
     */
    async processImport(data) {
        // Validate data structure
        if (!data.meta || !data.meta.version) {
            throw new Error('Invalid export file');
        }

        const stats = {
            settings: 0,
            progress: 0,
            skipped: 0
        };

        // Show confirmation dialog
        const confirmed = await this.showImportConfirmation(data);
        if (!confirmed) {
            return { success: false, cancelled: true };
        }

        // Import settings
        if (data.settings) {
            Object.entries(data.settings).forEach(([key, value]) => {
                try {
                    localStorage.setItem(key, JSON.stringify(value));
                    stats.settings++;
                } catch (e) {
                    stats.skipped++;
                }
            });
        }

        // Import progress
        if (data.progress) {
            Object.entries(data.progress).forEach(([key, value]) => {
                try {
                    const strValue = typeof value === 'string' ? value : JSON.stringify(value);
                    localStorage.setItem(key, strValue);
                    stats.progress++;
                } catch (e) {
                    stats.skipped++;
                }
            });
        }

        window.toast?.success(`Imported ${stats.settings + stats.progress} items!`);
        
        // Reload page to apply settings
        setTimeout(() => {
            if (confirm('Reload page to apply imported settings?')) {
                window.location.reload();
            }
        }, 1000);

        return { success: true, stats };
    }

    /**
     * Show import confirmation
     */
    showImportConfirmation(data) {
        return new Promise((resolve) => {
            const settingsCount = Object.keys(data.settings || {}).length;
            const progressCount = Object.keys(data.progress || {}).length;
            
            const message = `Import ${settingsCount} settings and ${progressCount} progress items?\n\nThis will overwrite existing data.`;
            resolve(confirm(message));
        });
    }

    /**
     * Clear all user data
     */
    clearAllData() {
        if (!confirm('Are you sure you want to clear ALL data? This cannot be undone.')) {
            return false;
        }

        localStorage.clear();
        sessionStorage.clear();
        
        // Clear IndexedDB
        if (window.indexedDB) {
            indexedDB.deleteDatabase('CodingPracticeCache');
        }

        window.toast?.success('All data cleared');
        
        setTimeout(() => {
            window.location.reload();
        }, 1000);

        return true;
    }

    /**
     * Create backup
     */
    async createBackup() {
        const data = this.collectData();
        data.meta.isBackup = true;
        data.meta.backupId = `backup_${Date.now()}`;
        
        // Store backup in IndexedDB for larger storage
        if (window.indexedDB) {
            try {
                await this.storeBackupInIndexedDB(data);
                window.toast?.success('Backup created');
                return { success: true, backupId: data.meta.backupId };
            } catch (e) {
                console.warn('IndexedDB backup failed, using localStorage');
            }
        }

        // Fallback to localStorage
        const backups = this.getBackups();
        backups.unshift(data);
        
        // Keep only last 5 backups
        while (backups.length > 5) {
            backups.pop();
        }

        localStorage.setItem('dataBackups', JSON.stringify(backups));
        window.toast?.success('Backup created');
        
        return { success: true, backupId: data.meta.backupId };
    }

    /**
     * Get list of backups
     */
    getBackups() {
        try {
            return JSON.parse(localStorage.getItem('dataBackups')) || [];
        } catch {
            return [];
        }
    }

    /**
     * Restore from backup
     */
    async restoreBackup(backupId) {
        const backups = this.getBackups();
        const backup = backups.find(b => b.meta.backupId === backupId);
        
        if (!backup) {
            window.toast?.error('Backup not found');
            return { success: false };
        }

        return this.processImport(backup);
    }

    /**
     * Store backup in IndexedDB
     */
    storeBackupInIndexedDB(data) {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('CodingPracticeBackups', 1);
            
            request.onerror = () => reject(request.error);
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains('backups')) {
                    db.createObjectStore('backups', { keyPath: 'meta.backupId' });
                }
            };
            
            request.onsuccess = () => {
                const db = request.result;
                const tx = db.transaction(['backups'], 'readwrite');
                const store = tx.objectStore('backups');
                store.put(data);
                tx.oncomplete = () => resolve();
                tx.onerror = () => reject(tx.error);
            };
        });
    }

    /**
     * Download file helper
     */
    downloadFile(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * Get date string for filenames
     */
    getDateString() {
        const now = new Date();
        return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
    }

    /**
     * Get storage usage statistics
     */
    getStorageStats() {
        let localStorageSize = 0;
        let sessionStorageSize = 0;
        
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            localStorageSize += localStorage.getItem(key).length;
        }
        
        for (let i = 0; i < sessionStorage.length; i++) {
            const key = sessionStorage.key(i);
            sessionStorageSize += sessionStorage.getItem(key).length;
        }

        return {
            localStorage: {
                items: localStorage.length,
                size: `${(localStorageSize / 1024).toFixed(2)} KB`,
                bytes: localStorageSize
            },
            sessionStorage: {
                items: sessionStorage.length,
                size: `${(sessionStorageSize / 1024).toFixed(2)} KB`,
                bytes: sessionStorageSize
            },
            total: {
                items: localStorage.length + sessionStorage.length,
                size: `${((localStorageSize + sessionStorageSize) / 1024).toFixed(2)} KB`,
                bytes: localStorageSize + sessionStorageSize
            }
        };
    }

    /**
     * Create import UI
     */
    showImportDialog() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        
        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (file) {
                try {
                    await this.importData(file);
                } catch (error) {
                    window.toast?.error(error.message);
                }
            }
        };
        
        input.click();
    }
}

// Initialize and expose globally
const dataManager = new DataManager();
window.dataManager = dataManager;

// Convenience functions
window.exportData = (format) => dataManager.exportData(format);
window.importData = () => dataManager.showImportDialog();
window.createBackup = () => dataManager.createBackup();
window.clearAllData = () => dataManager.clearAllData();




