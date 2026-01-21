/**
 * Enhanced Dashboard JavaScript
 * Real-time updates, interactive charts, and modern UI interactions
 */

// Global variables
let socket = null;
let currentSession = null;
let chartUpdateInterval = null;
const REFRESH_INTERVAL = 30000; // 30 seconds
const ANIMATION_DURATION = 300;

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeWebApp();
    setupGlobalEventListeners();
    initializeNotifications();
});

/**
 * Initialize the web application
 */
function initializeWebApp() {
    console.log('🚀 Initializing Enhanced Coding Practice Dashboard');
    
    // Initialize Socket.IO for real-time updates
    initializeSocketIO();
    
    // Initialize service worker for PWA
    initializeServiceWorker();
    
    // Setup periodic data refresh
    setupPeriodicRefresh();
    
    // Initialize tooltips and popovers
    initializeBootstrapComponents();
    
    console.log('✅ Dashboard initialization complete');
}

/**
 * Initialize Socket.IO connection for real-time updates
 */
function initializeSocketIO() {
    if (typeof io !== 'undefined') {
        socket = io({
            transports: ['websocket', 'polling'],
            timeout: 5000,
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: 5
        });

        socket.on('connect', function() {
            console.log('🔌 Connected to real-time server');
            showNotification('Connected to real-time updates', 'success');
        });

        socket.on('disconnect', function() {
            console.log('🔌 Disconnected from server');
            showNotification('Connection lost - trying to reconnect...', 'warning');
        });

        socket.on('reconnect', function() {
            console.log('🔌 Reconnected to server');
            showNotification('Connection restored', 'success');
            refreshDashboard();
        });

        // Listen for real-time data updates
        socket.on('stats_update', handleStatsUpdate);
        socket.on('new_activity', handleNewActivity);
        socket.on('session_update', handleSessionUpdate);
        socket.on('recommendation_update', handleRecommendationUpdate);
        
    } else {
        console.warn('⚠️ Socket.IO not available - real-time updates disabled');
    }
}

/**
 * Initialize service worker for PWA functionality
 */
function initializeServiceWorker() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => {
                console.log('✅ Service Worker registered:', registration);
            })
            .catch(error => {
                console.warn('⚠️ Service Worker registration failed:', error);
            });
    }
}

/**
 * Setup periodic data refresh
 */
function setupPeriodicRefresh() {
    // Refresh dashboard data every 30 seconds
    chartUpdateInterval = setInterval(() => {
        refreshDashboardData();
    }, 30000);
    
    // Refresh on window focus
    window.addEventListener('focus', refreshDashboardData);
}

/**
 * Initialize Bootstrap components (tooltips, popovers, etc.)
 */
function initializeBootstrapComponents() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Setup global event listeners
 */
function setupGlobalEventListeners() {
    // Handle keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
    
    // Handle network status
    window.addEventListener('online', () => {
        showNotification('Back online', 'success');
        refreshDashboardData();
    });
    
    window.addEventListener('offline', () => {
        showNotification('You are offline', 'warning');
    });
    
    // Handle window resize for responsive charts
    window.addEventListener('resize', debounce(handleWindowResize, 300));
}

/**
 * Handle keyboard shortcuts
 */
function handleKeyboardShortcuts(event) {
    // Ctrl/Cmd + R - Refresh dashboard
    if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
        event.preventDefault();
        refreshDashboard();
    }
    
    // Ctrl/Cmd + P - Start practice
    if ((event.ctrlKey || event.metaKey) && event.key === 'p') {
        event.preventDefault();
        window.location.href = '/practice';
    }
    
    // Ctrl/Cmd + S - Start study session
    if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault();
        startStudySession();
    }
}

/**
 * Handle window resize events
 */
function handleWindowResize() {
    // Resize Plotly charts
    if (typeof Plotly !== 'undefined') {
        const chartElements = document.querySelectorAll('[id$="-chart"]');
        chartElements.forEach(element => {
            if (element.layout) {
                Plotly.Plots.resize(element);
            }
        });
    }
}

/**
 * Real-time event handlers
 */
function handleStatsUpdate(data) {
    updateStatsCards(data);
    showNotification('Stats updated', 'info', 2000);
}

function handleNewActivity(activity) {
    prependActivityToFeed(activity);
    showNotification(`New activity: ${activity.title}`, 'info', 3000);
}

function handleSessionUpdate(session) {
    currentSession = session;
    updateSessionUI(session);
}

function handleRecommendationUpdate(recommendations) {
    updateRecommendationsList(recommendations);
}

/**
 * Update stats cards with new data
 */
function updateStatsCards(stats) {
    const animations = [];
    
    // Animate counter changes
    Object.keys(stats).forEach(key => {
        const element = document.getElementById(key.replace('_', '-'));
        if (element) {
            const oldValue = parseInt(element.textContent) || 0;
            const newValue = stats[key];
            
            if (oldValue !== newValue) {
                animations.push(animateCounter(element, oldValue, newValue));
            }
        }
    });
    
    Promise.all(animations).then(() => {
        console.log('✅ Stats cards updated');
    });
}

/**
 * Animate counter changes
 */
function animateCounter(element, start, end, duration = 1000) {
    return new Promise(resolve => {
        const startTime = performance.now();
        const isPercentage = element.textContent.includes('%');
        const suffix = isPercentage ? '%' : (element.textContent.includes('h') ? 'h' : '');
        
        function updateCounter(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function for smooth animation
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const current = Math.round(start + (end - start) * easeOutQuart);
            
            element.textContent = current + suffix;
            
            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            } else {
                resolve();
            }
        }
        
        requestAnimationFrame(updateCounter);
    });
}

/**
 * Prepend new activity to activity feed
 */
function prependActivityToFeed(activity) {
    const container = document.getElementById('recent-activity');
    if (!container) return;
    
    const activityHTML = `
        <div class="d-flex align-items-center mb-3 pb-2 border-bottom fade-in">
            <div class="flex-shrink-0 me-3">
                <i class="fas ${activity.icon} text-${activity.color}"></i>
            </div>
            <div class="flex-grow-1">
                <div class="fw-semibold">${activity.title}</div>
                <small class="text-muted">${activity.description}</small>
            </div>
            <div class="text-muted small">
                just now
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('afterbegin', activityHTML);
    
    // Remove oldest activity if more than 10
    const activities = container.querySelectorAll('.d-flex');
    if (activities.length > 10) {
        activities[activities.length - 1].remove();
    }
}

/**
 * Update session UI
 */
function updateSessionUI(session) {
    // Update any session-related UI elements
    if (session.state === 'active') {
        showSessionTimer(session);
    } else {
        hideSessionTimer();
    }
}

/**
 * Show session timer in UI
 */
function showSessionTimer(session) {
    let timerElement = document.getElementById('session-timer-widget');
    
    if (!timerElement) {
        timerElement = document.createElement('div');
        timerElement.id = 'session-timer-widget';
        timerElement.className = 'position-fixed top-0 end-0 m-3 p-3 bg-primary text-white rounded shadow';
        timerElement.style.zIndex = '1050';
        document.body.appendChild(timerElement);
    }
    
    const remainingTime = calculateRemainingTime(session);
    timerElement.innerHTML = `
        <div class="text-center">
            <i class="fas fa-clock mb-1"></i>
            <div class="fw-bold">${formatTime(remainingTime)}</div>
            <small>${session.focus_mode}</small>
        </div>
    `;
}

/**
 * Hide session timer
 */
function hideSessionTimer() {
    const timerElement = document.getElementById('session-timer-widget');
    if (timerElement) {
        timerElement.remove();
    }
}

/**
 * Calculate remaining time for session
 */
function calculateRemainingTime(session) {
    const startTime = new Date(session.start_time);
    const duration = session.planned_duration * 60 * 1000; // Convert to milliseconds
    const elapsed = Date.now() - startTime.getTime();
    return Math.max(0, duration - elapsed);
}

/**
 * Format time in MM:SS format
 */
function formatTime(milliseconds) {
    const minutes = Math.floor(milliseconds / 60000);
    const seconds = Math.floor((milliseconds % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

/**
 * Show notification toast
 */
function showNotification(message, type = 'info', duration = 5000) {
    const toast = createToast(message, type);
    document.body.appendChild(toast);
    
    // Show toast
    const bsToast = new bootstrap.Toast(toast, {
        delay: duration
    });
    bsToast.show();
    
    // Remove from DOM when hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

/**
 * Create toast element
 */
function createToast(message, type) {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.style.position = 'fixed';
    toast.style.top = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '9999';
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    return toast;
}

/**
 * Initialize notification system
 */
function initializeNotifications() {
    // Request notification permission for PWA
    if ('Notification' in window && navigator.serviceWorker) {
        if (Notification.permission === 'default') {
            Notification.requestPermission().then(permission => {
                console.log('Notification permission:', permission);
            });
        }
    }
}

/**
 * Refresh dashboard data
 */
function refreshDashboardData() {
    // Refresh stats
    fetch('http://localhost:4500/api/dashboard/stats')
        .then(response => response.json())
        .then(data => updateStatsCards(data))
        .catch(error => console.warn('Failed to refresh stats:', error));
    
    // Refresh activity
    const activityContainer = document.getElementById('recent-activity');
    if (activityContainer) {
        fetch('http://localhost:4500/api/dashboard/activity?limit=10')
            .then(response => response.json())
            .then(data => {
                if (data.activities) {
                    updateActivityFeed(data.activities);
                }
            })
            .catch(error => console.warn('Failed to refresh activity:', error));
    }
}

/**
 * Update activity feed
 */
function updateActivityFeed(activities) {
    const container = document.getElementById('recent-activity');
    if (!container) return;
    
    if (activities && activities.length > 0) {
        container.innerHTML = activities.map(activity => `
            <div class="d-flex align-items-center mb-3 pb-2 border-bottom">
                <div class="flex-shrink-0 me-3">
                    <i class="fas ${activity.icon} text-${activity.color}"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="fw-semibold">${activity.title}</div>
                    <small class="text-muted">${activity.description}</small>
                </div>
                <div class="text-muted small">
                    ${activity.time_ago}
                </div>
            </div>
        `).join('');
    }
}

/**
 * Utility function for debouncing
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

/**
 * Error handling and logging
 */
window.addEventListener('error', function(e) {
    console.error('JavaScript Error:', e.error);
    showNotification('An error occurred. Please refresh the page.', 'error');
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled Promise Rejection:', e.reason);
    showNotification('A network error occurred.', 'error');
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (chartUpdateInterval) {
        clearInterval(chartUpdateInterval);
    }
    
    if (socket) {
        socket.disconnect();
    }
});

// Export functions for global access
window.dashboard = {
    refreshDashboard: () => location.reload(),
    refreshDashboardData,
    showNotification,
    socket,
    currentSession
}; 