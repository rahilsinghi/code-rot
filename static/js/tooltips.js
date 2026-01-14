/**
 * Custom Tooltip System
 * Lightweight, accessible tooltips
 */

class TooltipManager {
    constructor() {
        this.tooltip = null;
        this.currentTarget = null;
        this.hideTimeout = null;
        this.showDelay = 300;
        this.hideDelay = 100;
        
        this.init();
    }

    init() {
        this.createTooltip();
        this.bindGlobalEvents();
        this.initializeTooltips();
    }

    createTooltip() {
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'custom-tooltip';
        this.tooltip.setAttribute('role', 'tooltip');
        this.tooltip.innerHTML = `
            <div class="tooltip-content"></div>
            <div class="tooltip-arrow"></div>
        `;
        document.body.appendChild(this.tooltip);
    }

    bindGlobalEvents() {
        // Use event delegation for better performance
        document.addEventListener('mouseenter', (e) => {
            const target = e.target.closest('[data-tooltip]');
            if (target) {
                this.scheduleShow(target);
            }
        }, true);

        document.addEventListener('mouseleave', (e) => {
            const target = e.target.closest('[data-tooltip]');
            if (target) {
                this.scheduleHide();
            }
        }, true);

        document.addEventListener('focusin', (e) => {
            const target = e.target.closest('[data-tooltip]');
            if (target) {
                this.show(target);
            }
        });

        document.addEventListener('focusout', (e) => {
            const target = e.target.closest('[data-tooltip]');
            if (target) {
                this.hide();
            }
        });

        // Hide on scroll
        window.addEventListener('scroll', () => this.hide(), { passive: true });

        // Hide on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hide();
            }
        });
    }

    initializeTooltips() {
        // Add aria-describedby for accessibility
        document.querySelectorAll('[data-tooltip]').forEach((el, index) => {
            const id = `tooltip-${index}`;
            el.setAttribute('aria-describedby', id);
        });
    }

    scheduleShow(target) {
        clearTimeout(this.hideTimeout);
        this.showTimeout = setTimeout(() => {
            this.show(target);
        }, this.showDelay);
    }

    scheduleHide() {
        clearTimeout(this.showTimeout);
        this.hideTimeout = setTimeout(() => {
            this.hide();
        }, this.hideDelay);
    }

    show(target) {
        if (!target) return;

        const content = target.getAttribute('data-tooltip');
        const position = target.getAttribute('data-tooltip-position') || 'top';
        const variant = target.getAttribute('data-tooltip-variant') || '';

        if (!content) return;

        this.currentTarget = target;
        this.tooltip.querySelector('.tooltip-content').innerHTML = content;
        this.tooltip.className = `custom-tooltip ${position} ${variant}`;
        this.tooltip.classList.add('visible');

        this.position(target, position);
    }

    hide() {
        clearTimeout(this.showTimeout);
        this.tooltip.classList.remove('visible');
        this.currentTarget = null;
    }

    position(target, placement) {
        const targetRect = target.getBoundingClientRect();
        const tooltipRect = this.tooltip.getBoundingClientRect();
        const scrollY = window.scrollY;
        const scrollX = window.scrollX;
        const gap = 8;

        let top, left;

        switch (placement) {
            case 'top':
                top = targetRect.top + scrollY - tooltipRect.height - gap;
                left = targetRect.left + scrollX + (targetRect.width - tooltipRect.width) / 2;
                break;
            case 'bottom':
                top = targetRect.bottom + scrollY + gap;
                left = targetRect.left + scrollX + (targetRect.width - tooltipRect.width) / 2;
                break;
            case 'left':
                top = targetRect.top + scrollY + (targetRect.height - tooltipRect.height) / 2;
                left = targetRect.left + scrollX - tooltipRect.width - gap;
                break;
            case 'right':
                top = targetRect.top + scrollY + (targetRect.height - tooltipRect.height) / 2;
                left = targetRect.right + scrollX + gap;
                break;
        }

        // Keep tooltip within viewport
        const padding = 10;
        const maxLeft = window.innerWidth - tooltipRect.width - padding;
        const maxTop = window.innerHeight + scrollY - tooltipRect.height - padding;

        left = Math.max(padding, Math.min(left, maxLeft));
        top = Math.max(scrollY + padding, Math.min(top, maxTop));

        this.tooltip.style.top = `${top}px`;
        this.tooltip.style.left = `${left}px`;
    }

    // Programmatic API
    create(element, content, options = {}) {
        element.setAttribute('data-tooltip', content);
        if (options.position) {
            element.setAttribute('data-tooltip-position', options.position);
        }
        if (options.variant) {
            element.setAttribute('data-tooltip-variant', options.variant);
        }
    }

    update(element, content) {
        element.setAttribute('data-tooltip', content);
        if (this.currentTarget === element) {
            this.tooltip.querySelector('.tooltip-content').innerHTML = content;
        }
    }

    destroy(element) {
        element.removeAttribute('data-tooltip');
        element.removeAttribute('data-tooltip-position');
        element.removeAttribute('data-tooltip-variant');
        if (this.currentTarget === element) {
            this.hide();
        }
    }
}

// Styles
const tooltipStyles = document.createElement('style');
tooltipStyles.textContent = `
    .custom-tooltip {
        position: absolute;
        z-index: 10005;
        max-width: 300px;
        padding: 0.5rem 0.75rem;
        background: var(--bg-tertiary);
        color: var(--text-primary);
        font-size: 0.8125rem;
        line-height: 1.4;
        border-radius: 6px;
        box-shadow: var(--shadow-lg);
        pointer-events: none;
        opacity: 0;
        visibility: hidden;
        transform: scale(0.95);
        transition: opacity 0.15s ease, transform 0.15s ease, visibility 0.15s ease;
    }

    .custom-tooltip.visible {
        opacity: 1;
        visibility: visible;
        transform: scale(1);
    }

    .custom-tooltip .tooltip-arrow {
        position: absolute;
        width: 8px;
        height: 8px;
        background: var(--bg-tertiary);
        transform: rotate(45deg);
    }

    .custom-tooltip.top .tooltip-arrow {
        bottom: -4px;
        left: 50%;
        margin-left: -4px;
    }

    .custom-tooltip.bottom .tooltip-arrow {
        top: -4px;
        left: 50%;
        margin-left: -4px;
    }

    .custom-tooltip.left .tooltip-arrow {
        right: -4px;
        top: 50%;
        margin-top: -4px;
    }

    .custom-tooltip.right .tooltip-arrow {
        left: -4px;
        top: 50%;
        margin-top: -4px;
    }

    /* Dark variant */
    .custom-tooltip.dark {
        background: #1a1d21;
        color: #f8f9fa;
    }

    .custom-tooltip.dark .tooltip-arrow {
        background: #1a1d21;
    }

    /* Info variant */
    .custom-tooltip.info {
        background: var(--accent-info);
        color: white;
    }

    .custom-tooltip.info .tooltip-arrow {
        background: var(--accent-info);
    }

    /* Success variant */
    .custom-tooltip.success {
        background: var(--accent-success);
        color: white;
    }

    .custom-tooltip.success .tooltip-arrow {
        background: var(--accent-success);
    }

    /* Warning variant */
    .custom-tooltip.warning {
        background: var(--accent-warning);
        color: #212529;
    }

    .custom-tooltip.warning .tooltip-arrow {
        background: var(--accent-warning);
    }

    /* Error variant */
    .custom-tooltip.error {
        background: var(--accent-danger);
        color: white;
    }

    .custom-tooltip.error .tooltip-arrow {
        background: var(--accent-danger);
    }

    /* Rich content support */
    .tooltip-content strong {
        font-weight: 600;
    }

    .tooltip-content kbd {
        display: inline-block;
        padding: 0.125rem 0.375rem;
        background: rgba(0, 0, 0, 0.2);
        border-radius: 3px;
        font-size: 0.75rem;
        font-family: inherit;
    }

    .tooltip-content code {
        padding: 0.125rem 0.25rem;
        background: rgba(0, 0, 0, 0.1);
        border-radius: 3px;
        font-family: monospace;
        font-size: 0.8em;
    }
`;
document.head.appendChild(tooltipStyles);

// Initialize
const tooltips = new TooltipManager();
window.tooltips = tooltips;

// Helper function
window.createTooltip = (el, content, options) => tooltips.create(el, content, options);



