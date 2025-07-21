/**
 * Offline functionality for PWA
 * Handles offline detection and user experience
 */

// Check if we're offline
function isOffline() {
    return !navigator.onLine;
}

// Show offline status
function showOfflineStatus() {
    const offlineNotice = document.createElement('div');
    offlineNotice.id = 'offline-notice';
    offlineNotice.className = 'alert alert-warning fixed-top m-3';
    offlineNotice.innerHTML = `
        <i class="fas fa-wifi me-2"></i>
        You're currently offline. Some features may not be available.
        <button type="button" class="btn-close btn-close-white float-end" onclick="this.parentElement.remove()"></button>
    `;
    document.body.appendChild(offlineNotice);
}

// Hide offline status
function hideOfflineStatus() {
    const notice = document.getElementById('offline-notice');
    if (notice) {
        notice.remove();
    }
}

// Initialize offline detection
document.addEventListener('DOMContentLoaded', function() {
    // Check initial state
    if (isOffline()) {
        showOfflineStatus();
    }
    
    // Listen for online/offline events
    window.addEventListener('online', () => {
        hideOfflineStatus();
        console.log('Connection restored');
    });
    
    window.addEventListener('offline', () => {
        showOfflineStatus();
        console.log('Connection lost');
    });
});

// Export for global access
window.offlineHandler = {
    isOffline,
    showOfflineStatus,
    hideOfflineStatus
}; 