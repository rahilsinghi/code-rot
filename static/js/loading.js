/**
 * Loading State Manager
 * Handles skeleton loading states and transitions
 */

class LoadingManager {
    constructor() {
        this.loadingElements = new Map();
        this.defaultDuration = 300;
        this.minDisplayTime = 500;
    }

    /**
     * Show skeleton loading state for an element
     * @param {string|HTMLElement} selector - Element or selector
     * @param {string} type - Skeleton type: 'card', 'list', 'table', 'stats', 'chart', 'text', 'custom'
     * @param {object} options - Additional options
     */
    show(selector, type = 'text', options = {}) {
        const element = typeof selector === 'string' 
            ? document.querySelector(selector) 
            : selector;
        
        if (!element) return;

        const { count = 3, animation = 'shimmer' } = options;
        
        // Store original content
        if (!this.loadingElements.has(element)) {
            this.loadingElements.set(element, {
                originalHTML: element.innerHTML,
                originalClass: element.className
            });
        }

        // Generate skeleton HTML
        const skeletonHTML = this.generateSkeleton(type, count, animation);
        
        element.innerHTML = skeletonHTML;
        element.classList.add('loading');
    }

    /**
     * Hide loading state and restore content
     * @param {string|HTMLElement} selector - Element or selector
     * @param {string} newContent - Optional new content to show
     */
    hide(selector, newContent = null) {
        const element = typeof selector === 'string' 
            ? document.querySelector(selector) 
            : selector;
        
        if (!element) return;

        const stored = this.loadingElements.get(element);
        
        element.classList.remove('loading');
        element.classList.add('loaded');
        
        if (newContent !== null) {
            element.innerHTML = newContent;
        } else if (stored) {
            element.innerHTML = stored.originalHTML;
        }

        // Add fade-in animation to content
        element.style.animation = 'fadeIn 0.3s ease';
        setTimeout(() => {
            element.style.animation = '';
            element.classList.remove('loaded');
        }, 300);

        this.loadingElements.delete(element);
    }

    /**
     * Generate skeleton HTML based on type
     */
    generateSkeleton(type, count, animation) {
        const animClass = animation === 'pulse' ? 'skeleton-pulse' : 
                         animation === 'wave' ? 'skeleton-wave' : '';

        switch (type) {
            case 'card':
                return this.generateCardSkeleton(count, animClass);
            case 'list':
                return this.generateListSkeleton(count, animClass);
            case 'table':
                return this.generateTableSkeleton(count, animClass);
            case 'stats':
                return this.generateStatsSkeleton(count, animClass);
            case 'chart':
                return this.generateChartSkeleton(animClass);
            case 'profile':
                return this.generateProfileSkeleton(animClass);
            case 'comment':
                return this.generateCommentSkeleton(count, animClass);
            case 'text':
            default:
                return this.generateTextSkeleton(count, animClass);
        }
    }

    generateTextSkeleton(count, animClass) {
        return Array(count).fill(0).map((_, i) => 
            `<div class="skeleton skeleton-text ${animClass}" style="width: ${100 - (i * 10)}%"></div>`
        ).join('');
    }

    generateCardSkeleton(count, animClass) {
        return Array(count).fill(0).map(() => `
            <div class="skeleton-card mb-3">
                <div class="skeleton-card-header">
                    <div class="skeleton skeleton-avatar ${animClass}"></div>
                    <div style="flex: 1;">
                        <div class="skeleton skeleton-text ${animClass}" style="width: 60%"></div>
                        <div class="skeleton skeleton-text sm ${animClass}" style="width: 40%"></div>
                    </div>
                </div>
                <div class="skeleton-card-content">
                    <div class="skeleton skeleton-text ${animClass}"></div>
                    <div class="skeleton skeleton-text ${animClass}"></div>
                    <div class="skeleton skeleton-text ${animClass}" style="width: 80%"></div>
                </div>
            </div>
        `).join('');
    }

    generateListSkeleton(count, animClass) {
        return `
            <div class="skeleton-list">
                ${Array(count).fill(0).map(() => `
                    <div class="skeleton-list-item">
                        <div class="skeleton skeleton-avatar ${animClass}"></div>
                        <div class="skeleton-list-item-content">
                            <div class="skeleton skeleton-text ${animClass}" style="width: 60%"></div>
                            <div class="skeleton skeleton-text sm ${animClass}" style="width: 40%"></div>
                        </div>
                        <div class="skeleton skeleton-badge ${animClass}"></div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    generateTableSkeleton(count, animClass) {
        return `
            <div class="skeleton-table">
                <div class="skeleton-table-row">
                    <div class="skeleton skeleton-table-cell narrow ${animClass}"></div>
                    <div class="skeleton skeleton-table-cell wide ${animClass}"></div>
                    <div class="skeleton skeleton-table-cell ${animClass}"></div>
                    <div class="skeleton skeleton-table-cell narrow ${animClass}"></div>
                </div>
                ${Array(count).fill(0).map(() => `
                    <div class="skeleton-table-row">
                        <div class="skeleton skeleton-table-cell narrow ${animClass}"></div>
                        <div class="skeleton skeleton-table-cell wide ${animClass}"></div>
                        <div class="skeleton skeleton-table-cell ${animClass}"></div>
                        <div class="skeleton skeleton-table-cell narrow ${animClass}"></div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    generateStatsSkeleton(count, animClass) {
        return `
            <div class="skeleton-stats">
                ${Array(count).fill(0).map(() => `
                    <div class="skeleton-stat-card">
                        <div class="skeleton skeleton-stat-icon ${animClass}"></div>
                        <div class="skeleton skeleton-stat-value ${animClass}"></div>
                        <div class="skeleton skeleton-stat-label ${animClass}"></div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    generateChartSkeleton(animClass) {
        const heights = [60, 80, 45, 90, 70, 55, 85, 65].map(h => `${h}%`);
        return `
            <div class="skeleton-chart">
                <div class="skeleton skeleton-chart-title ${animClass}"></div>
                <div class="skeleton-chart-area">
                    ${heights.map(h => `
                        <div class="skeleton skeleton-chart-bar ${animClass}" style="height: ${h}"></div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    generateProfileSkeleton(animClass) {
        return `
            <div class="skeleton-profile">
                <div class="skeleton skeleton-avatar xl ${animClass}"></div>
                <div class="skeleton-profile-info">
                    <div class="skeleton skeleton-profile-name ${animClass}"></div>
                    <div class="skeleton skeleton-profile-bio ${animClass}"></div>
                    <div class="skeleton skeleton-text sm ${animClass}" style="width: 100px"></div>
                </div>
            </div>
        `;
    }

    generateCommentSkeleton(count, animClass) {
        return Array(count).fill(0).map(() => `
            <div class="skeleton-comment">
                <div class="skeleton skeleton-avatar ${animClass}"></div>
                <div class="skeleton-comment-content">
                    <div class="skeleton-comment-header">
                        <div class="skeleton skeleton-text ${animClass}" style="width: 100px; height: 0.875rem;"></div>
                        <div class="skeleton skeleton-text sm ${animClass}" style="width: 60px;"></div>
                    </div>
                    <div class="skeleton skeleton-text ${animClass}"></div>
                    <div class="skeleton skeleton-text ${animClass}" style="width: 80%"></div>
                </div>
            </div>
        `).join('');
    }

    /**
     * Wrap an async function with loading state
     * @param {string|HTMLElement} selector - Element to show loading on
     * @param {Function} asyncFn - Async function to execute
     * @param {string} type - Skeleton type
     */
    async wrap(selector, asyncFn, type = 'text', options = {}) {
        this.show(selector, type, options);
        try {
            const result = await asyncFn();
            this.hide(selector);
            return result;
        } catch (error) {
            this.hide(selector);
            throw error;
        }
    }

    /**
     * Show page loading overlay
     */
    showPageLoading(text = 'Loading...') {
        let overlay = document.getElementById('page-loading-overlay');
        
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'page-loading-overlay';
            overlay.className = 'page-loading';
            overlay.innerHTML = `
                <div class="page-loading-content">
                    <div class="page-loading-spinner"></div>
                    <div class="page-loading-text">${text}</div>
                </div>
            `;
            document.body.appendChild(overlay);
        } else {
            overlay.querySelector('.page-loading-text').textContent = text;
            overlay.classList.remove('hidden');
        }
    }

    /**
     * Hide page loading overlay
     */
    hidePageLoading() {
        const overlay = document.getElementById('page-loading-overlay');
        if (overlay) {
            overlay.classList.add('hidden');
        }
    }

    /**
     * Create inline loading indicator
     */
    createInlineLoader(size = 'sm') {
        const loader = document.createElement('span');
        loader.className = 'inline-loading';
        loader.innerHTML = `<span class="spinner spinner-${size}"></span>`;
        return loader;
    }

    /**
     * Add loading state to a button
     */
    buttonLoading(button, loading = true, text = 'Loading...') {
        if (loading) {
            button.dataset.originalText = button.innerHTML;
            button.disabled = true;
            button.innerHTML = `<span class="spinner spinner-sm me-2"></span>${text}`;
        } else {
            button.disabled = false;
            button.innerHTML = button.dataset.originalText || button.innerHTML;
        }
    }
}

// Initialize and expose globally
const loading = new LoadingManager();
window.loading = loading;

// Utility function for quick access
window.showLoading = (selector, type, options) => loading.show(selector, type, options);
window.hideLoading = (selector, content) => loading.hide(selector, content);




