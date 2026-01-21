/**
 * Global Toast Notification System
 * Beautiful, stackable notifications with different types
 */

class ToastManager {
    constructor() {
        this.container = null;
        this.toasts = [];
        this.maxToasts = 5;
        this.defaultDuration = 4000;
        this.animationDuration = 300;
        this.init();
    }

    init() {
        // Create toast container
        this.container = document.createElement('div');
        this.container.id = 'toast-container';
        this.container.className = 'toast-container';
        document.body.appendChild(this.container);
    }

    /**
     * Show a toast notification
     * @param {string} message - The message to display
     * @param {string} type - Type: 'success', 'error', 'warning', 'info'
     * @param {object} options - Additional options
     */
    show(message, type = 'info', options = {}) {
        const {
            title = this.getDefaultTitle(type),
            duration = this.defaultDuration,
            closable = true,
            icon = this.getIcon(type),
            action = null,
            actionText = 'Action',
            onClose = null
        } = options;

        // Remove oldest toast if at max
        if (this.toasts.length >= this.maxToasts) {
            this.remove(this.toasts[0].id);
        }

        const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        const toast = document.createElement('div');
        toast.id = id;
        toast.className = `toast-item toast-${type} toast-enter`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'polite');

        toast.innerHTML = `
            <div class="toast-icon">${icon}</div>
            <div class="toast-content">
                ${title ? `<div class="toast-title">${title}</div>` : ''}
                <div class="toast-message">${message}</div>
                ${action ? `<button class="toast-action" onclick="(${action.toString()})()">${actionText}</button>` : ''}
            </div>
            <div class="toast-actions">
                ${closable ? `<button class="toast-close" aria-label="Close notification">&times;</button>` : ''}
            </div>
            <div class="toast-progress">
                <div class="toast-progress-bar" style="animation-duration: ${duration}ms"></div>
            </div>
        `;

        // Add close handler
        if (closable) {
            toast.querySelector('.toast-close').addEventListener('click', () => {
                this.remove(id, onClose);
            });
        }

        // Click anywhere to dismiss
        toast.addEventListener('click', (e) => {
            if (e.target === toast || e.target.closest('.toast-content')) {
                this.remove(id, onClose);
            }
        });

        this.container.appendChild(toast);
        this.toasts.push({ id, element: toast, timeout: null });

        // Auto remove after duration
        if (duration > 0) {
            const timeout = setTimeout(() => {
                this.remove(id, onClose);
            }, duration);
            
            const toastRecord = this.toasts.find(t => t.id === id);
            if (toastRecord) toastRecord.timeout = timeout;
        }

        // Pause on hover
        toast.addEventListener('mouseenter', () => {
            const toastRecord = this.toasts.find(t => t.id === id);
            if (toastRecord && toastRecord.timeout) {
                clearTimeout(toastRecord.timeout);
                toast.querySelector('.toast-progress-bar').style.animationPlayState = 'paused';
            }
        });

        toast.addEventListener('mouseleave', () => {
            const toastRecord = this.toasts.find(t => t.id === id);
            if (toastRecord && duration > 0) {
                toastRecord.timeout = setTimeout(() => {
                    this.remove(id, onClose);
                }, duration / 2);
                toast.querySelector('.toast-progress-bar').style.animationPlayState = 'running';
            }
        });

        return id;
    }

    remove(id, callback = null) {
        const index = this.toasts.findIndex(t => t.id === id);
        if (index === -1) return;

        const { element, timeout } = this.toasts[index];
        
        if (timeout) clearTimeout(timeout);
        
        element.classList.remove('toast-enter');
        element.classList.add('toast-exit');
        
        setTimeout(() => {
            if (element.parentNode) {
                element.parentNode.removeChild(element);
            }
            if (callback) callback();
        }, 300);

        this.toasts.splice(index, 1);
    }

    clear() {
        this.toasts.forEach(t => this.remove(t.id));
    }

    getDefaultTitle(type) {
        const titles = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Info'
        };
        return titles[type] || '';
    }

    getIcon(type) {
        const icons = {
            success: '<i class="fas fa-check-circle"></i>',
            error: '<i class="fas fa-times-circle"></i>',
            warning: '<i class="fas fa-exclamation-triangle"></i>',
            info: '<i class="fas fa-info-circle"></i>'
        };
        return icons[type] || icons.info;
    }

    // Convenience methods
    success(message, options = {}) {
        return this.show(message, 'success', options);
    }

    error(message, options = {}) {
        return this.show(message, 'error', { ...options, duration: options.duration || 6000 });
    }

    warning(message, options = {}) {
        return this.show(message, 'warning', options);
    }

    info(message, options = {}) {
        return this.show(message, 'info', options);
    }

    // Promise-based toast for async operations
    async promise(promise, messages = {}) {
        const {
            loading = 'Loading...',
            success = 'Success!',
            error = 'Something went wrong'
        } = messages;

        const loadingId = this.show(loading, 'info', { 
            closable: false, 
            duration: 0,
            title: 'Processing'
        });

        try {
            const result = await promise;
            this.remove(loadingId);
            this.success(typeof success === 'function' ? success(result) : success);
            return result;
        } catch (err) {
            this.remove(loadingId);
            this.error(typeof error === 'function' ? error(err) : error);
            throw err;
        }
    }
}

// Initialize and expose globally
const toast = new ToastManager();

// Global function for easy access
window.showToast = (message, type = 'info', options = {}) => toast.show(message, type, options);
window.toast = toast;

// Also add to window for backwards compatibility
window.showNotification = window.showToast;




