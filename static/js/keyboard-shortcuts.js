/**
 * Keyboard Shortcuts System
 * Power user keyboard navigation and shortcuts
 */

class KeyboardShortcuts {
    constructor() {
        this.shortcuts = new Map();
        this.enabled = true;
        this.helpModalVisible = false;
        
        this.init();
        this.registerDefaultShortcuts();
    }

    init() {
        document.addEventListener('keydown', (e) => this.handleKeydown(e));
        
        // Create help modal
        this.createHelpModal();
    }

    handleKeydown(e) {
        // Ignore if disabled or in input/textarea
        if (!this.enabled) return;
        if (this.isInInput(e.target)) return;

        const key = this.getKeyCombo(e);
        const shortcut = this.shortcuts.get(key);

        if (shortcut) {
            e.preventDefault();
            shortcut.action(e);
        }
    }

    getKeyCombo(e) {
        const parts = [];
        if (e.ctrlKey || e.metaKey) parts.push('ctrl');
        if (e.altKey) parts.push('alt');
        if (e.shiftKey) parts.push('shift');
        parts.push(e.key.toLowerCase());
        return parts.join('+');
    }

    isInInput(element) {
        const tagName = element.tagName.toLowerCase();
        return tagName === 'input' || 
               tagName === 'textarea' || 
               tagName === 'select' ||
               element.isContentEditable;
    }

    /**
     * Register a keyboard shortcut
     * @param {string} key - Key combination (e.g., 'ctrl+k', 'shift+?', 'g')
     * @param {Function} action - Function to execute
     * @param {string} description - Description for help modal
     * @param {string} category - Category for grouping
     */
    register(key, action, description, category = 'General') {
        this.shortcuts.set(key.toLowerCase(), {
            action,
            description,
            category,
            key: key
        });
    }

    /**
     * Unregister a shortcut
     */
    unregister(key) {
        this.shortcuts.delete(key.toLowerCase());
    }

    /**
     * Enable/disable shortcuts
     */
    setEnabled(enabled) {
        this.enabled = enabled;
    }

    /**
     * Register default shortcuts
     */
    registerDefaultShortcuts() {
        // Help
        this.register('shift+?', () => this.toggleHelpModal(), 'Show keyboard shortcuts', 'Help');
        this.register('escape', () => this.closeAllModals(), 'Close modals', 'Help');

        // Navigation
        this.register('g', () => this.showNavigationPalette(), 'Go to page...', 'Navigation');
        this.register('h', () => this.navigateTo('/'), 'Go to Dashboard', 'Navigation');
        this.register('p', () => this.navigateTo('/practice'), 'Go to Practice', 'Navigation');
        this.register('a', () => this.navigateTo('/analytics'), 'Go to Analytics', 'Navigation');
        this.register('r', () => this.navigateTo('/review'), 'Go to Review', 'Navigation');
        this.register('s', () => this.navigateTo('/settings'), 'Go to Settings', 'Navigation');

        // Theme
        this.register('t', () => this.toggleTheme(), 'Toggle dark/light mode', 'Theme');

        // Search/Command Palette
        this.register('ctrl+k', () => this.showCommandPalette(), 'Open command palette', 'Search');
        this.register('/', () => this.focusSearch(), 'Focus search', 'Search');

        // Actions
        this.register('n', () => this.startNewSession(), 'Start new session', 'Actions');
        this.register('ctrl+s', () => this.saveSettings(), 'Save settings', 'Actions');
        
        // Quick Actions
        this.register('1', () => this.quickAction(1), 'Quick action 1', 'Quick');
        this.register('2', () => this.quickAction(2), 'Quick action 2', 'Quick');
        this.register('3', () => this.quickAction(3), 'Quick action 3', 'Quick');
    }

    // Action implementations
    navigateTo(path) {
        window.location.href = path;
    }

    toggleTheme() {
        if (window.themeManager) {
            window.themeManager.toggle();
        } else if (window.toggleTheme) {
            window.toggleTheme();
        }
    }

    focusSearch() {
        const searchInput = document.querySelector('[data-search], #search, .search-input, input[type="search"]');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }

    startNewSession() {
        const sessionBtn = document.querySelector('[data-start-session], #startSessionBtn, .start-session-btn');
        if (sessionBtn) {
            sessionBtn.click();
        } else {
            window.toast?.info('Press N on the Study Sessions page to start a session');
        }
    }

    saveSettings() {
        const saveBtn = document.querySelector('[data-save-settings], #saveSettingsBtn, .save-settings-btn');
        if (saveBtn) {
            saveBtn.click();
            window.toast?.success('Settings saved!');
        }
    }

    quickAction(num) {
        const quickActionBtns = document.querySelectorAll('.quick-action-btn, [data-quick-action]');
        if (quickActionBtns[num - 1]) {
            quickActionBtns[num - 1].click();
        }
    }

    closeAllModals() {
        // Close Bootstrap modals
        document.querySelectorAll('.modal.show').forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) bsModal.hide();
        });

        // Close help modal
        if (this.helpModalVisible) {
            this.hideHelpModal();
        }

        // Close command palette
        this.hideCommandPalette();
        this.hideNavigationPalette();
    }

    // Help Modal
    createHelpModal() {
        const modal = document.createElement('div');
        modal.id = 'keyboard-help-modal';
        modal.className = 'keyboard-help-modal';
        modal.innerHTML = `
            <div class="keyboard-help-content">
                <div class="keyboard-help-header">
                    <h3><i class="fas fa-keyboard me-2"></i>Keyboard Shortcuts</h3>
                    <button class="keyboard-help-close" onclick="keyboardShortcuts.hideHelpModal()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="keyboard-help-body">
                    ${this.generateHelpContent()}
                </div>
                <div class="keyboard-help-footer">
                    <span class="text-muted">Press <kbd>Shift</kbd> + <kbd>?</kbd> to toggle this help</span>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    generateHelpContent() {
        const categories = new Map();
        
        this.shortcuts.forEach((shortcut) => {
            if (!categories.has(shortcut.category)) {
                categories.set(shortcut.category, []);
            }
            categories.get(shortcut.category).push(shortcut);
        });

        let html = '';
        categories.forEach((shortcuts, category) => {
            html += `
                <div class="keyboard-help-category">
                    <h4>${category}</h4>
                    <div class="keyboard-help-list">
                        ${shortcuts.map(s => `
                            <div class="keyboard-help-item">
                                <span class="keyboard-help-keys">${this.formatKey(s.key)}</span>
                                <span class="keyboard-help-desc">${s.description}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        });

        return html;
    }

    formatKey(key) {
        return key.split('+').map(k => `<kbd>${k}</kbd>`).join(' + ');
    }

    toggleHelpModal() {
        if (this.helpModalVisible) {
            this.hideHelpModal();
        } else {
            this.showHelpModal();
        }
    }

    showHelpModal() {
        const modal = document.getElementById('keyboard-help-modal');
        if (modal) {
            modal.classList.add('visible');
            this.helpModalVisible = true;
        }
    }

    hideHelpModal() {
        const modal = document.getElementById('keyboard-help-modal');
        if (modal) {
            modal.classList.remove('visible');
            this.helpModalVisible = false;
        }
    }

    // Command Palette
    showCommandPalette() {
        let palette = document.getElementById('command-palette');
        
        if (!palette) {
            palette = document.createElement('div');
            palette.id = 'command-palette';
            palette.className = 'command-palette';
            palette.innerHTML = `
                <div class="command-palette-content">
                    <div class="command-palette-input-wrapper">
                        <i class="fas fa-search"></i>
                        <input type="text" id="command-palette-input" placeholder="Type a command or search..." autocomplete="off">
                    </div>
                    <div class="command-palette-results" id="command-palette-results"></div>
                </div>
            `;
            document.body.appendChild(palette);

            // Add event listeners
            const input = palette.querySelector('#command-palette-input');
            input.addEventListener('input', (e) => this.filterCommands(e.target.value));
            input.addEventListener('keydown', (e) => this.handlePaletteKeydown(e));
        }

        palette.classList.add('visible');
        palette.querySelector('#command-palette-input').focus();
        this.filterCommands('');
    }

    hideCommandPalette() {
        const palette = document.getElementById('command-palette');
        if (palette) {
            palette.classList.remove('visible');
        }
    }

    filterCommands(query) {
        const results = document.getElementById('command-palette-results');
        if (!results) return;

        const commands = Array.from(this.shortcuts.values())
            .filter(s => 
                s.description.toLowerCase().includes(query.toLowerCase()) ||
                s.key.toLowerCase().includes(query.toLowerCase())
            )
            .slice(0, 10);

        results.innerHTML = commands.map((cmd, i) => `
            <div class="command-palette-item ${i === 0 ? 'selected' : ''}" data-key="${cmd.key}">
                <span class="command-palette-item-desc">${cmd.description}</span>
                <span class="command-palette-item-key">${this.formatKey(cmd.key)}</span>
            </div>
        `).join('') || '<div class="command-palette-empty">No commands found</div>';

        // Add click handlers
        results.querySelectorAll('.command-palette-item').forEach(item => {
            item.addEventListener('click', () => {
                const shortcut = this.shortcuts.get(item.dataset.key);
                if (shortcut) {
                    this.hideCommandPalette();
                    shortcut.action();
                }
            });
        });
    }

    handlePaletteKeydown(e) {
        const results = document.getElementById('command-palette-results');
        const items = results?.querySelectorAll('.command-palette-item') || [];
        const selected = results?.querySelector('.command-palette-item.selected');

        if (e.key === 'Escape') {
            this.hideCommandPalette();
        } else if (e.key === 'Enter' && selected) {
            const shortcut = this.shortcuts.get(selected.dataset.key);
            if (shortcut) {
                this.hideCommandPalette();
                shortcut.action();
            }
        } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
            e.preventDefault();
            const currentIndex = Array.from(items).indexOf(selected);
            const nextIndex = e.key === 'ArrowDown' 
                ? Math.min(currentIndex + 1, items.length - 1)
                : Math.max(currentIndex - 1, 0);
            
            selected?.classList.remove('selected');
            items[nextIndex]?.classList.add('selected');
            items[nextIndex]?.scrollIntoView({ block: 'nearest' });
        }
    }

    // Navigation Palette
    showNavigationPalette() {
        const pages = [
            { name: 'Dashboard', path: '/', icon: 'fa-tachometer-alt' },
            { name: 'Practice', path: '/practice', icon: 'fa-code' },
            { name: 'Analytics', path: '/analytics', icon: 'fa-chart-line' },
            { name: 'Review', path: '/review', icon: 'fa-redo' },
            { name: 'Settings', path: '/settings', icon: 'fa-cog' },
            { name: 'Study Sessions', path: '/study-sessions', icon: 'fa-clock' },
            { name: 'API Docs', path: 'http://localhost:4500/api/docs', icon: 'fa-book', external: true }
        ];

        let palette = document.getElementById('nav-palette');
        
        if (!palette) {
            palette = document.createElement('div');
            palette.id = 'nav-palette';
            palette.className = 'command-palette';
            palette.innerHTML = `
                <div class="command-palette-content">
                    <div class="command-palette-input-wrapper">
                        <i class="fas fa-compass"></i>
                        <input type="text" id="nav-palette-input" placeholder="Go to page..." autocomplete="off">
                    </div>
                    <div class="command-palette-results" id="nav-palette-results">
                        ${pages.map((page, i) => `
                            <div class="command-palette-item ${i === 0 ? 'selected' : ''}" data-path="${page.path}" ${page.external ? 'data-external="true"' : ''}>
                                <span class="command-palette-item-desc">
                                    <i class="fas ${page.icon} me-2"></i>${page.name}
                                </span>
                                ${page.external ? '<span class="badge bg-secondary">External</span>' : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            document.body.appendChild(palette);

            // Add event listeners
            const input = palette.querySelector('#nav-palette-input');
            input.addEventListener('input', (e) => this.filterNavigation(e.target.value, pages));
            input.addEventListener('keydown', (e) => this.handleNavPaletteKeydown(e));
        }

        palette.classList.add('visible');
        palette.querySelector('#nav-palette-input').focus();
    }

    hideNavigationPalette() {
        const palette = document.getElementById('nav-palette');
        if (palette) {
            palette.classList.remove('visible');
        }
    }

    filterNavigation(query, pages) {
        const results = document.getElementById('nav-palette-results');
        if (!results) return;

        const filtered = pages.filter(p => 
            p.name.toLowerCase().includes(query.toLowerCase())
        );

        results.innerHTML = filtered.map((page, i) => `
            <div class="command-palette-item ${i === 0 ? 'selected' : ''}" data-path="${page.path}" ${page.external ? 'data-external="true"' : ''}>
                <span class="command-palette-item-desc">
                    <i class="fas ${page.icon} me-2"></i>${page.name}
                </span>
                ${page.external ? '<span class="badge bg-secondary">External</span>' : ''}
            </div>
        `).join('') || '<div class="command-palette-empty">No pages found</div>';

        // Add click handlers
        results.querySelectorAll('.command-palette-item').forEach(item => {
            item.addEventListener('click', () => {
                this.hideNavigationPalette();
                if (item.dataset.external === 'true') {
                    window.open(item.dataset.path, '_blank');
                } else {
                    window.location.href = item.dataset.path;
                }
            });
        });
    }

    handleNavPaletteKeydown(e) {
        const results = document.getElementById('nav-palette-results');
        const items = results?.querySelectorAll('.command-palette-item') || [];
        const selected = results?.querySelector('.command-palette-item.selected');

        if (e.key === 'Escape') {
            this.hideNavigationPalette();
        } else if (e.key === 'Enter' && selected) {
            this.hideNavigationPalette();
            if (selected.dataset.external === 'true') {
                window.open(selected.dataset.path, '_blank');
            } else {
                window.location.href = selected.dataset.path;
            }
        } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
            e.preventDefault();
            const currentIndex = Array.from(items).indexOf(selected);
            const nextIndex = e.key === 'ArrowDown' 
                ? Math.min(currentIndex + 1, items.length - 1)
                : Math.max(currentIndex - 1, 0);
            
            selected?.classList.remove('selected');
            items[nextIndex]?.classList.add('selected');
            items[nextIndex]?.scrollIntoView({ block: 'nearest' });
        }
    }
}

// Initialize
const keyboardShortcuts = new KeyboardShortcuts();
window.keyboardShortcuts = keyboardShortcuts;




