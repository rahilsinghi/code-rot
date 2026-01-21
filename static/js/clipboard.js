/**
 * Clipboard Utility
 * Copy text, code, and rich content to clipboard
 */

class ClipboardManager {
    constructor() {
        this.copyHistory = [];
        this.maxHistory = 10;
        this.successDuration = 2000;
        this.animationDuration = 300;
        this.init();
    }

    init() {
        // Auto-initialize copy buttons
        this.initCopyButtons();
        
        // Watch for dynamically added elements
        this.observeDOM();
    }

    initCopyButtons() {
        document.querySelectorAll('[data-copy]').forEach(btn => {
            if (!btn.hasAttribute('data-clipboard-initialized')) {
                this.attachCopyHandler(btn);
                btn.setAttribute('data-clipboard-initialized', 'true');
            }
        });
    }

    attachCopyHandler(btn) {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            
            const target = btn.dataset.copy;
            const copyType = btn.dataset.copyType || 'text';
            let content;

            if (target === 'self') {
                content = btn.dataset.copyValue || btn.textContent;
            } else if (target.startsWith('#') || target.startsWith('.')) {
                const el = document.querySelector(target);
                content = el ? (el.value || el.textContent) : '';
            } else {
                content = target;
            }

            const success = await this.copy(content, copyType);
            this.showFeedback(btn, success);
        });
    }

    async copy(content, type = 'text') {
        try {
            if (type === 'rich' && navigator.clipboard.write) {
                // Copy as HTML for rich content
                const blob = new Blob([content], { type: 'text/html' });
                await navigator.clipboard.write([
                    new ClipboardItem({ 'text/html': blob })
                ]);
            } else {
                // Plain text copy
                await navigator.clipboard.writeText(content);
            }

            // Add to history
            this.addToHistory(content);
            
            // Dispatch event
            document.dispatchEvent(new CustomEvent('clipboard:copy', {
                detail: { content, type }
            }));

            return true;
        } catch (err) {
            // Fallback for older browsers
            return this.fallbackCopy(content);
        }
    }

    fallbackCopy(content) {
        const textarea = document.createElement('textarea');
        textarea.value = content;
        textarea.style.position = 'fixed';
        textarea.style.left = '-9999px';
        textarea.style.top = '0';
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();

        try {
            const success = document.execCommand('copy');
            if (success) {
                this.addToHistory(content);
            }
            return success;
        } catch (err) {
            console.error('Fallback copy failed:', err);
            return false;
        } finally {
            document.body.removeChild(textarea);
        }
    }

    addToHistory(content) {
        // Avoid duplicates
        const existing = this.copyHistory.findIndex(item => item.content === content);
        if (existing !== -1) {
            this.copyHistory.splice(existing, 1);
        }

        this.copyHistory.unshift({
            content,
            timestamp: new Date(),
            preview: content.substring(0, 100)
        });

        // Limit history size
        if (this.copyHistory.length > this.maxHistory) {
            this.copyHistory.pop();
        }
    }

    showFeedback(btn, success) {
        const originalContent = btn.innerHTML;
        const originalClass = btn.className;

        if (success) {
            btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
            btn.classList.add('copied');
        } else {
            btn.innerHTML = '<i class="fas fa-times"></i> Failed';
            btn.classList.add('copy-failed');
        }

        setTimeout(() => {
            btn.innerHTML = originalContent;
            btn.className = originalClass;
        }, 2000);
    }

    observeDOM() {
        const observer = new MutationObserver((mutations) => {
            let shouldInit = false;
            mutations.forEach(mutation => {
                if (mutation.addedNodes.length > 0) {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === 1 && (
                            node.hasAttribute('data-copy') ||
                            node.querySelector('[data-copy]')
                        )) {
                            shouldInit = true;
                        }
                    });
                }
            });
            if (shouldInit) {
                this.initCopyButtons();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    // Copy code block with formatting
    async copyCode(element) {
        const code = element.querySelector('code') || element;
        const text = code.textContent;
        return await this.copy(text);
    }

    // Copy as formatted text
    async copyFormatted(content) {
        return await this.copy(content, 'rich');
    }

    // Get copy history
    getHistory() {
        return this.copyHistory;
    }

    // Clear history
    clearHistory() {
        this.copyHistory = [];
    }
}

// Code block copy enhancement
function enhanceCodeBlocks() {
    document.querySelectorAll('.code-block:not(.copy-enhanced)').forEach(block => {
        block.classList.add('copy-enhanced');
        
        // Find or create actions container
        let actions = block.querySelector('.code-actions');
        if (!actions) {
            const header = block.querySelector('.code-header');
            if (header) {
                actions = document.createElement('div');
                actions.className = 'code-actions';
                header.appendChild(actions);
            }
        }

        if (actions && !actions.querySelector('.copy-code-btn')) {
            const copyBtn = document.createElement('button');
            copyBtn.className = 'code-action-btn copy-code-btn';
            copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy';
            copyBtn.addEventListener('click', async () => {
                const success = await clipboard.copyCode(block);
                
                if (success) {
                    copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                    copyBtn.classList.add('copied');
                } else {
                    copyBtn.innerHTML = '<i class="fas fa-times"></i> Failed';
                }

                setTimeout(() => {
                    copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy';
                    copyBtn.classList.remove('copied');
                }, 2000);
            });
            actions.appendChild(copyBtn);
        }
    });
}

// Styles
const clipboardStyles = document.createElement('style');
clipboardStyles.textContent = `
    /* Copy button states */
    [data-copy] {
        cursor: pointer;
        transition: all 0.2s ease;
    }

    [data-copy].copied {
        color: var(--accent-success) !important;
    }

    [data-copy].copy-failed {
        color: var(--accent-danger) !important;
    }

    /* Copy tooltip */
    .copy-tooltip {
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        padding: 0.375rem 0.75rem;
        background: var(--bg-tertiary);
        color: var(--text-primary);
        font-size: 0.75rem;
        border-radius: 6px;
        white-space: nowrap;
        opacity: 0;
        visibility: hidden;
        transition: all 0.2s ease;
        pointer-events: none;
        margin-bottom: 0.5rem;
    }

    .copy-tooltip::after {
        content: '';
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
        border: 6px solid transparent;
        border-top-color: var(--bg-tertiary);
    }

    [data-copy]:hover .copy-tooltip {
        opacity: 1;
        visibility: visible;
    }

    /* Copy history panel */
    .copy-history {
        position: fixed;
        bottom: 1rem;
        right: 1rem;
        width: 320px;
        max-height: 400px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        box-shadow: var(--shadow-lg);
        z-index: 1000;
        overflow: hidden;
        display: none;
    }

    .copy-history.visible {
        display: block;
        animation: slideUp 0.3s ease;
    }

    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .copy-history-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem 1rem;
        background: var(--bg-tertiary);
        border-bottom: 1px solid var(--border-color);
    }

    .copy-history-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    .copy-history-close {
        background: none;
        border: none;
        color: var(--text-muted);
        cursor: pointer;
        padding: 0.25rem;
    }

    .copy-history-list {
        max-height: 300px;
        overflow-y: auto;
    }

    .copy-history-item {
        padding: 0.75rem 1rem;
        border-bottom: 1px solid var(--border-color);
        cursor: pointer;
        transition: background 0.15s ease;
    }

    .copy-history-item:hover {
        background: var(--bg-tertiary);
    }

    .copy-history-item:last-child {
        border-bottom: none;
    }

    .copy-history-preview {
        font-size: 0.8125rem;
        color: var(--text-secondary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .copy-history-time {
        font-size: 0.6875rem;
        color: var(--text-muted);
        margin-top: 0.25rem;
    }

    .copy-history-empty {
        padding: 2rem 1rem;
        text-align: center;
        color: var(--text-muted);
        font-size: 0.875rem;
    }

    /* One-click copy input */
    .copy-input-group {
        display: flex;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        overflow: hidden;
    }

    .copy-input-group input {
        flex: 1;
        padding: 0.625rem 0.875rem;
        border: none;
        background: var(--bg-tertiary);
        color: var(--text-primary);
        font-size: 0.875rem;
    }

    .copy-input-group input:focus {
        outline: none;
    }

    .copy-input-group button {
        padding: 0.625rem 1rem;
        border: none;
        background: var(--accent-primary);
        color: white;
        cursor: pointer;
        transition: filter 0.2s ease;
    }

    .copy-input-group button:hover {
        filter: brightness(1.1);
    }
`;
document.head.appendChild(clipboardStyles);

// Initialize
const clipboard = new ClipboardManager();

// Run on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', enhanceCodeBlocks);
} else {
    enhanceCodeBlocks();
}

// Export
window.clipboard = clipboard;
window.copyToClipboard = (content) => clipboard.copy(content);
window.enhanceCodeBlocks = enhanceCodeBlocks;


