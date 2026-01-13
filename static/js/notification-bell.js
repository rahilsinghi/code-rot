/**
 * Notification Bell Component
 * Real-time notification dropdown with badges
 */

class NotificationBell {
    constructor(options = {}) {
        this.options = {
            container: null,
            maxNotifications: 50,
            pollInterval: 30000, // 30 seconds
            markReadOnClick: true,
            onNotificationClick: null,
            onMarkAllRead: null,
            fetchUrl: null,
            ...options
        };

        this.notifications = [];
        this.unreadCount = 0;
        this.isOpen = false;
        this.element = null;

        this.init();
    }

    init() {
        this.render();
        this.bindEvents();
        
        if (this.options.fetchUrl) {
            this.startPolling();
        }
    }

    render() {
        const container = this.options.container 
            ? (typeof this.options.container === 'string' 
                ? document.querySelector(this.options.container) 
                : this.options.container)
            : document.body;

        this.element = document.createElement('div');
        this.element.className = 'notification-bell-container';
        this.element.innerHTML = `
            <button class="notification-bell-trigger" aria-label="Notifications" aria-haspopup="true" aria-expanded="false">
                <i class="fas fa-bell"></i>
                <span class="notification-badge" style="display: none;">0</span>
            </button>
            <div class="notification-dropdown" role="menu">
                <div class="notification-header">
                    <h4>Notifications</h4>
                    <button class="notification-mark-all" title="Mark all as read">
                        <i class="fas fa-check-double"></i>
                    </button>
                </div>
                <div class="notification-list">
                    <div class="notification-empty">
                        <i class="fas fa-bell-slash"></i>
                        <p>No notifications</p>
                    </div>
                </div>
                <div class="notification-footer">
                    <a href="/notifications" class="notification-view-all">View all notifications</a>
                </div>
            </div>
        `;

        container.appendChild(this.element);

        this.trigger = this.element.querySelector('.notification-bell-trigger');
        this.badge = this.element.querySelector('.notification-badge');
        this.dropdown = this.element.querySelector('.notification-dropdown');
        this.list = this.element.querySelector('.notification-list');
        this.markAllBtn = this.element.querySelector('.notification-mark-all');
    }

    bindEvents() {
        // Toggle dropdown
        this.trigger.addEventListener('click', () => this.toggle());

        // Mark all as read
        this.markAllBtn.addEventListener('click', () => this.markAllRead());

        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!this.element.contains(e.target)) {
                this.close();
            }
        });

        // Keyboard navigation
        this.trigger.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.toggle();
            } else if (e.key === 'Escape') {
                this.close();
            }
        });
    }

    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    open() {
        this.isOpen = true;
        this.trigger.setAttribute('aria-expanded', 'true');
        this.element.classList.add('open');
        this.dropdown.classList.add('visible');
    }

    close() {
        this.isOpen = false;
        this.trigger.setAttribute('aria-expanded', 'false');
        this.element.classList.remove('open');
        this.dropdown.classList.remove('visible');
    }

    addNotification(notification) {
        const item = {
            id: notification.id || Date.now(),
            title: notification.title,
            message: notification.message,
            type: notification.type || 'info', // info, success, warning, error
            icon: notification.icon || this.getTypeIcon(notification.type),
            time: notification.time || new Date(),
            read: notification.read || false,
            url: notification.url || null,
            data: notification.data || {}
        };

        // Add to beginning
        this.notifications.unshift(item);

        // Limit notifications
        if (this.notifications.length > this.options.maxNotifications) {
            this.notifications.pop();
        }

        this.updateUI();
        this.animateBell();

        // Show browser notification if supported
        if (Notification.permission === 'granted' && !document.hasFocus()) {
            new Notification(item.title, {
                body: item.message,
                icon: '/static/icons/icon-192x192.png'
            });
        }

        return item;
    }

    getTypeIcon(type) {
        const icons = {
            info: 'fas fa-info-circle',
            success: 'fas fa-check-circle',
            warning: 'fas fa-exclamation-triangle',
            error: 'fas fa-times-circle',
            achievement: 'fas fa-trophy',
            reminder: 'fas fa-clock',
            streak: 'fas fa-fire'
        };
        return icons[type] || icons.info;
    }

    updateUI() {
        // Update badge
        this.unreadCount = this.notifications.filter(n => !n.read).length;
        this.badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
        this.badge.style.display = this.unreadCount > 0 ? 'flex' : 'none';

        // Update list
        if (this.notifications.length === 0) {
            this.list.innerHTML = `
                <div class="notification-empty">
                    <i class="fas fa-bell-slash"></i>
                    <p>No notifications</p>
                </div>
            `;
        } else {
            this.list.innerHTML = this.notifications.map(n => this.renderNotification(n)).join('');
            
            // Bind click handlers
            this.list.querySelectorAll('.notification-item').forEach(item => {
                item.addEventListener('click', () => {
                    const id = parseInt(item.dataset.id);
                    this.handleNotificationClick(id);
                });
            });
        }
    }

    renderNotification(notification) {
        const timeAgo = this.formatTimeAgo(notification.time);
        
        return `
            <div class="notification-item ${notification.read ? '' : 'unread'} ${notification.type}" 
                 data-id="${notification.id}" 
                 role="menuitem"
                 tabindex="0">
                <div class="notification-icon ${notification.type}">
                    <i class="${notification.icon}"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-title">${notification.title}</div>
                    <div class="notification-message">${notification.message}</div>
                    <div class="notification-time">${timeAgo}</div>
                </div>
                ${!notification.read ? '<div class="notification-dot"></div>' : ''}
            </div>
        `;
    }

    formatTimeAgo(date) {
        const now = new Date();
        const diff = now - new Date(date);
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (seconds < 60) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        return new Date(date).toLocaleDateString();
    }

    handleNotificationClick(id) {
        const notification = this.notifications.find(n => n.id === id);
        if (!notification) return;

        // Mark as read
        if (this.options.markReadOnClick && !notification.read) {
            this.markRead(id);
        }

        // Navigate if URL provided
        if (notification.url) {
            window.location.href = notification.url;
        }

        // Callback
        if (this.options.onNotificationClick) {
            this.options.onNotificationClick(notification);
        }
    }

    markRead(id) {
        const notification = this.notifications.find(n => n.id === id);
        if (notification) {
            notification.read = true;
            this.updateUI();
        }
    }

    markAllRead() {
        this.notifications.forEach(n => n.read = true);
        this.updateUI();

        if (this.options.onMarkAllRead) {
            this.options.onMarkAllRead();
        }
    }

    animateBell() {
        this.trigger.classList.add('ring');
        setTimeout(() => {
            this.trigger.classList.remove('ring');
        }, 500);
    }

    startPolling() {
        this.fetchNotifications();
        setInterval(() => this.fetchNotifications(), this.options.pollInterval);
    }

    async fetchNotifications() {
        if (!this.options.fetchUrl) return;

        try {
            const response = await fetch(this.options.fetchUrl);
            const data = await response.json();
            
            if (data.notifications) {
                // Only add new notifications
                const existingIds = this.notifications.map(n => n.id);
                const newNotifications = data.notifications.filter(n => !existingIds.includes(n.id));
                
                newNotifications.forEach(n => this.addNotification(n));
            }
        } catch (err) {
            console.error('Failed to fetch notifications:', err);
        }
    }

    clear() {
        this.notifications = [];
        this.updateUI();
    }

    destroy() {
        this.element.remove();
    }
}

// Styles
const bellStyles = document.createElement('style');
bellStyles.textContent = `
    .notification-bell-container {
        position: relative;
    }

    .notification-bell-trigger {
        position: relative;
        background: none;
        border: none;
        padding: 0.5rem;
        color: var(--text-secondary);
        cursor: pointer;
        font-size: 1.25rem;
        transition: color 0.2s ease;
    }

    .notification-bell-trigger:hover {
        color: var(--text-primary);
    }

    .notification-bell-trigger.ring {
        animation: bellRing 0.5s ease;
    }

    @keyframes bellRing {
        0%, 100% { transform: rotate(0); }
        20% { transform: rotate(15deg); }
        40% { transform: rotate(-15deg); }
        60% { transform: rotate(10deg); }
        80% { transform: rotate(-10deg); }
    }

    .notification-badge {
        position: absolute;
        top: 0;
        right: 0;
        min-width: 18px;
        height: 18px;
        padding: 0 5px;
        background: var(--accent-danger);
        color: white;
        font-size: 0.6875rem;
        font-weight: 600;
        border-radius: 9px;
        display: flex;
        align-items: center;
        justify-content: center;
        transform: translate(25%, -25%);
    }

    .notification-dropdown {
        position: absolute;
        top: 100%;
        right: 0;
        width: 360px;
        max-height: 480px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        box-shadow: var(--shadow-xl);
        z-index: 1000;
        opacity: 0;
        visibility: hidden;
        transform: translateY(-10px);
        transition: all 0.2s ease;
        overflow: hidden;
    }

    .notification-dropdown.visible {
        opacity: 1;
        visibility: visible;
        transform: translateY(0);
    }

    .notification-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 1.25rem;
        border-bottom: 1px solid var(--border-color);
    }

    .notification-header h4 {
        margin: 0;
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    .notification-mark-all {
        background: none;
        border: none;
        color: var(--text-muted);
        cursor: pointer;
        padding: 0.375rem;
        border-radius: 6px;
        transition: all 0.2s ease;
    }

    .notification-mark-all:hover {
        background: var(--bg-tertiary);
        color: var(--accent-primary);
    }

    .notification-list {
        max-height: 360px;
        overflow-y: auto;
    }

    .notification-item {
        display: flex;
        align-items: flex-start;
        gap: 0.875rem;
        padding: 1rem 1.25rem;
        cursor: pointer;
        transition: background 0.15s ease;
        position: relative;
    }

    .notification-item:hover {
        background: var(--bg-tertiary);
    }

    .notification-item.unread {
        background: rgba(var(--accent-primary-rgb), 0.05);
    }

    .notification-item.unread:hover {
        background: rgba(var(--accent-primary-rgb), 0.1);
    }

    .notification-icon {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        background: var(--bg-tertiary);
        color: var(--accent-info);
    }

    .notification-icon.success { color: var(--accent-success); background: rgba(81, 207, 102, 0.15); }
    .notification-icon.warning { color: var(--accent-warning); background: rgba(255, 193, 7, 0.15); }
    .notification-icon.error { color: var(--accent-danger); background: rgba(255, 107, 107, 0.15); }
    .notification-icon.achievement { color: #ffd700; background: rgba(255, 215, 0, 0.15); }
    .notification-icon.streak { color: #ff6b6b; background: rgba(255, 107, 107, 0.15); }

    .notification-content {
        flex: 1;
        min-width: 0;
    }

    .notification-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.125rem;
    }

    .notification-message {
        font-size: 0.8125rem;
        color: var(--text-secondary);
        line-height: 1.4;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    .notification-time {
        font-size: 0.6875rem;
        color: var(--text-muted);
        margin-top: 0.375rem;
    }

    .notification-dot {
        width: 8px;
        height: 8px;
        background: var(--accent-primary);
        border-radius: 50%;
        flex-shrink: 0;
        margin-top: 0.25rem;
    }

    .notification-empty {
        padding: 3rem 1rem;
        text-align: center;
        color: var(--text-muted);
    }

    .notification-empty i {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }

    .notification-empty p {
        margin: 0;
        font-size: 0.875rem;
    }

    .notification-footer {
        padding: 0.75rem 1.25rem;
        border-top: 1px solid var(--border-color);
        text-align: center;
    }

    .notification-view-all {
        font-size: 0.8125rem;
        color: var(--accent-primary);
        text-decoration: none;
    }

    .notification-view-all:hover {
        text-decoration: underline;
    }

    @media (max-width: 576px) {
        .notification-dropdown {
            position: fixed;
            top: auto;
            bottom: 0;
            left: 0;
            right: 0;
            width: 100%;
            max-height: 70vh;
            border-radius: 16px 16px 0 0;
        }
    }
`;
document.head.appendChild(bellStyles);

// Export
window.NotificationBell = NotificationBell;

