/**
 * Accessible Modal Component
 * WAI-ARIA compliant modal dialogs
 */

class Modal {
    constructor(options = {}) {
        this.options = {
            id: `modal-${Date.now()}`,
            title: '',
            content: '',
            size: 'md', // sm, md, lg, xl, full
            closable: true,
            closeOnOverlay: true,
            closeOnEscape: true,
            showHeader: true,
            showFooter: true,
            footerButtons: [],
            animation: 'fade', // fade, slide, scale, none
            animationDuration: 300,
            backdrop: true,
            onOpen: null,
            onClose: null,
            onConfirm: null,
            ...options
        };

        this.isOpen = false;
        this.previousActiveElement = null;
        this.modal = null;
        this.overlay = null;

        this.create();
    }

    create() {
        // Create overlay
        this.overlay = document.createElement('div');
        this.overlay.className = `modal-overlay ${this.options.animation}`;
        this.overlay.setAttribute('aria-hidden', 'true');

        // Create modal
        this.modal = document.createElement('div');
        this.modal.className = `modal-container ${this.options.size} ${this.options.animation}`;
        this.modal.setAttribute('role', 'dialog');
        this.modal.setAttribute('aria-modal', 'true');
        this.modal.setAttribute('aria-labelledby', `${this.options.id}-title`);
        this.modal.setAttribute('id', this.options.id);
        this.modal.setAttribute('tabindex', '-1');

        this.modal.innerHTML = `
            ${this.options.showHeader ? `
                <div class="modal-header">
                    <h3 class="modal-title" id="${this.options.id}-title">${this.options.title}</h3>
                    ${this.options.closable ? `
                        <button class="modal-close" aria-label="Close modal">
                            <i class="fas fa-times"></i>
                        </button>
                    ` : ''}
                </div>
            ` : ''}
            <div class="modal-body">
                ${this.options.content}
            </div>
            ${this.options.showFooter ? `
                <div class="modal-footer">
                    ${this.renderFooterButtons()}
                </div>
            ` : ''}
        `;

        this.overlay.appendChild(this.modal);
        document.body.appendChild(this.overlay);

        this.bindEvents();
    }

    renderFooterButtons() {
        if (this.options.footerButtons.length === 0) {
            return `
                <button class="modal-btn secondary" data-action="close">Cancel</button>
                <button class="modal-btn primary" data-action="confirm">Confirm</button>
            `;
        }

        return this.options.footerButtons.map(btn => `
            <button class="modal-btn ${btn.class || ''}" data-action="${btn.action || 'close'}">
                ${btn.icon ? `<i class="${btn.icon}"></i>` : ''}
                ${btn.text}
            </button>
        `).join('');
    }

    bindEvents() {
        // Close button
        const closeBtn = this.modal.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }

        // Overlay click
        if (this.options.closeOnOverlay) {
            this.overlay.addEventListener('click', (e) => {
                if (e.target === this.overlay) {
                    this.close();
                }
            });
        }

        // Escape key
        if (this.options.closeOnEscape) {
            this.escapeHandler = (e) => {
                if (e.key === 'Escape' && this.isOpen) {
                    this.close();
                }
            };
            document.addEventListener('keydown', this.escapeHandler);
        }

        // Footer buttons
        this.modal.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                if (action === 'close') {
                    this.close();
                } else if (action === 'confirm') {
                    if (this.options.onConfirm) {
                        this.options.onConfirm(this);
                    }
                    this.close();
                }
            });
        });

        // Trap focus
        this.modal.addEventListener('keydown', (e) => this.trapFocus(e));
    }

    trapFocus(e) {
        if (e.key !== 'Tab') return;

        const focusable = this.modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault();
            first.focus();
        }
    }

    open() {
        if (this.isOpen) return;

        this.previousActiveElement = document.activeElement;
        this.isOpen = true;

        // Prevent body scroll
        document.body.style.overflow = 'hidden';
        document.body.classList.add('modal-open');

        // Show modal
        this.overlay.classList.add('visible');
        this.modal.classList.add('visible');

        // Focus modal
        requestAnimationFrame(() => {
            const autofocus = this.modal.querySelector('[autofocus]');
            if (autofocus) {
                autofocus.focus();
            } else {
                this.modal.focus();
            }
        });

        if (this.options.onOpen) {
            this.options.onOpen(this);
        }
    }

    close() {
        if (!this.isOpen) return;

        this.isOpen = false;

        // Hide modal
        this.overlay.classList.remove('visible');
        this.modal.classList.remove('visible');

        // Restore body scroll
        document.body.style.overflow = '';
        document.body.classList.remove('modal-open');

        // Restore focus
        if (this.previousActiveElement) {
            this.previousActiveElement.focus();
        }

        if (this.options.onClose) {
            this.options.onClose(this);
        }
    }

    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    setContent(content) {
        const body = this.modal.querySelector('.modal-body');
        if (body) {
            body.innerHTML = content;
        }
    }

    setTitle(title) {
        const titleEl = this.modal.querySelector('.modal-title');
        if (titleEl) {
            titleEl.textContent = title;
        }
    }

    destroy() {
        if (this.escapeHandler) {
            document.removeEventListener('keydown', this.escapeHandler);
        }
        this.overlay.remove();
    }
}

// Quick modal functions
function showAlert(message, title = 'Alert') {
    return new Promise(resolve => {
        const modal = new Modal({
            title,
            content: `<p>${message}</p>`,
            size: 'sm',
            footerButtons: [
                { text: 'OK', class: 'primary', action: 'confirm' }
            ],
            onConfirm: () => resolve(true),
            onClose: () => resolve(false)
        });
        modal.open();
    });
}

function showConfirm(message, title = 'Confirm') {
    return new Promise(resolve => {
        const modal = new Modal({
            title,
            content: `<p>${message}</p>`,
            size: 'sm',
            footerButtons: [
                { text: 'Cancel', class: 'secondary', action: 'close' },
                { text: 'Confirm', class: 'primary', action: 'confirm' }
            ],
            onConfirm: () => resolve(true),
            onClose: () => resolve(false)
        });
        modal.open();
    });
}

function showPrompt(message, title = 'Input', defaultValue = '') {
    return new Promise(resolve => {
        const modal = new Modal({
            title,
            content: `
                <p>${message}</p>
                <input type="text" class="modal-input" value="${defaultValue}" autofocus>
            `,
            size: 'sm',
            onConfirm: (m) => {
                const input = m.modal.querySelector('.modal-input');
                resolve(input ? input.value : null);
            },
            onClose: () => resolve(null)
        });
        modal.open();
    });
}

// Styles
const modalStyles = document.createElement('style');
modalStyles.textContent = `
    .modal-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(4px);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1rem;
        z-index: 10010;
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.3s ease, visibility 0.3s ease;
    }

    .modal-overlay.visible {
        opacity: 1;
        visibility: visible;
    }

    .modal-container {
        background: var(--bg-card);
        border-radius: 16px;
        box-shadow: var(--shadow-xl);
        max-height: 90vh;
        display: flex;
        flex-direction: column;
        outline: none;
        transform: scale(0.95) translateY(20px);
        opacity: 0;
        transition: transform 0.3s ease, opacity 0.3s ease;
    }

    .modal-container.visible {
        transform: scale(1) translateY(0);
        opacity: 1;
    }

    /* Sizes */
    .modal-container.sm { width: 400px; }
    .modal-container.md { width: 560px; }
    .modal-container.lg { width: 800px; }
    .modal-container.xl { width: 1140px; }
    .modal-container.full { 
        width: calc(100vw - 2rem); 
        height: calc(100vh - 2rem);
    }

    /* Animations */
    .modal-overlay.slide .modal-container {
        transform: translateY(-100px);
    }
    .modal-overlay.slide.visible .modal-container {
        transform: translateY(0);
    }

    .modal-overlay.scale .modal-container {
        transform: scale(0.5);
    }
    .modal-overlay.scale.visible .modal-container {
        transform: scale(1);
    }

    /* Header */
    .modal-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.25rem 1.5rem;
        border-bottom: 1px solid var(--border-color);
    }

    .modal-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
    }

    .modal-close {
        width: 36px;
        height: 36px;
        border: none;
        background: none;
        color: var(--text-muted);
        cursor: pointer;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
    }

    .modal-close:hover {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }

    /* Body */
    .modal-body {
        padding: 1.5rem;
        overflow-y: auto;
        flex: 1;
    }

    .modal-body p {
        color: var(--text-secondary);
        line-height: 1.6;
        margin: 0;
    }

    /* Input */
    .modal-input {
        width: 100%;
        padding: 0.75rem 1rem;
        margin-top: 1rem;
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-primary);
        font-size: 1rem;
        transition: border-color 0.2s ease;
    }

    .modal-input:focus {
        outline: none;
        border-color: var(--accent-primary);
    }

    /* Footer */
    .modal-footer {
        display: flex;
        justify-content: flex-end;
        gap: 0.75rem;
        padding: 1.25rem 1.5rem;
        border-top: 1px solid var(--border-color);
    }

    .modal-btn {
        padding: 0.625rem 1.25rem;
        border: none;
        border-radius: 8px;
        font-size: 0.9375rem;
        font-weight: 500;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        transition: all 0.2s ease;
    }

    .modal-btn.primary {
        background: var(--accent-primary);
        color: white;
    }

    .modal-btn.primary:hover {
        filter: brightness(1.1);
    }

    .modal-btn.secondary {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }

    .modal-btn.secondary:hover {
        background: var(--border-color);
    }

    .modal-btn.danger {
        background: var(--accent-danger);
        color: white;
    }

    .modal-btn.success {
        background: var(--accent-success);
        color: white;
    }

    /* Body scroll lock */
    body.modal-open {
        overflow: hidden;
    }

    /* Mobile */
    @media (max-width: 576px) {
        .modal-container {
            width: 100% !important;
            max-height: 85vh;
            margin: auto;
            border-radius: 16px 16px 0 0;
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
        }

        .modal-overlay {
            align-items: flex-end;
            padding: 0;
        }

        .modal-container.visible {
            transform: translateY(0);
        }

        .modal-overlay .modal-container {
            transform: translateY(100%);
        }
    }
`;
document.head.appendChild(modalStyles);

// Export
window.Modal = Modal;
window.showAlert = showAlert;
window.showConfirm = showConfirm;
window.showPrompt = showPrompt;


