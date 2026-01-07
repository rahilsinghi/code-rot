/**
 * Accessible Tab Component
 * WAI-ARIA compliant tabbed interface
 */

class TabPanel {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' 
            ? document.querySelector(container) 
            : container;
        
        if (!this.container) return;

        this.options = {
            activeClass: 'active',
            animationDuration: 300,
            onChange: null,
            keyboard: true,
            autoActivate: false, // Auto-activate on arrow key
            ...options
        };

        this.tabs = [];
        this.panels = [];
        this.activeIndex = 0;

        this.init();
    }

    init() {
        this.tabs = Array.from(this.container.querySelectorAll('[role="tab"]'));
        this.panels = Array.from(this.container.querySelectorAll('[role="tabpanel"]'));

        if (this.tabs.length === 0) {
            this.createFromStructure();
        }

        this.setupAccessibility();
        this.bindEvents();
        this.activateTab(this.getInitialTab());
    }

    createFromStructure() {
        // Create tabs from data-tab-panel structure
        const tabList = this.container.querySelector('.tab-list');
        const tabContent = this.container.querySelector('.tab-content');

        if (!tabList || !tabContent) return;

        const items = tabList.querySelectorAll('.tab-item');
        const panes = tabContent.querySelectorAll('.tab-pane');

        items.forEach((item, index) => {
            const id = `tab-${Date.now()}-${index}`;
            const panelId = `panel-${Date.now()}-${index}`;

            item.setAttribute('role', 'tab');
            item.setAttribute('id', id);
            item.setAttribute('aria-controls', panelId);
            item.setAttribute('tabindex', index === 0 ? '0' : '-1');

            if (panes[index]) {
                panes[index].setAttribute('role', 'tabpanel');
                panes[index].setAttribute('id', panelId);
                panes[index].setAttribute('aria-labelledby', id);
                panes[index].setAttribute('tabindex', '0');
            }
        });

        tabList.setAttribute('role', 'tablist');
        
        this.tabs = Array.from(items);
        this.panels = Array.from(panes);
    }

    setupAccessibility() {
        this.tabs.forEach((tab, index) => {
            tab.setAttribute('aria-selected', 'false');
            tab.setAttribute('tabindex', '-1');
        });
    }

    bindEvents() {
        this.tabs.forEach((tab, index) => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                this.activateTab(index);
            });

            if (this.options.keyboard) {
                tab.addEventListener('keydown', (e) => this.handleKeydown(e, index));
            }
        });
    }

    handleKeydown(e, currentIndex) {
        let newIndex = currentIndex;
        let handled = false;

        switch (e.key) {
            case 'ArrowLeft':
            case 'ArrowUp':
                newIndex = currentIndex === 0 ? this.tabs.length - 1 : currentIndex - 1;
                handled = true;
                break;
            case 'ArrowRight':
            case 'ArrowDown':
                newIndex = currentIndex === this.tabs.length - 1 ? 0 : currentIndex + 1;
                handled = true;
                break;
            case 'Home':
                newIndex = 0;
                handled = true;
                break;
            case 'End':
                newIndex = this.tabs.length - 1;
                handled = true;
                break;
            case 'Enter':
            case ' ':
                this.activateTab(currentIndex);
                handled = true;
                break;
        }

        if (handled) {
            e.preventDefault();
            this.tabs[newIndex].focus();
            
            if (this.options.autoActivate) {
                this.activateTab(newIndex);
            }
        }
    }

    getInitialTab() {
        // Check for hash match
        const hash = window.location.hash.slice(1);
        if (hash) {
            const index = this.panels.findIndex(p => p.id === hash);
            if (index !== -1) return index;
        }

        // Check for active class
        const activeTab = this.tabs.findIndex(t => t.classList.contains(this.options.activeClass));
        return activeTab !== -1 ? activeTab : 0;
    }

    activateTab(index) {
        if (index < 0 || index >= this.tabs.length) return;
        if (index === this.activeIndex && this.tabs[index].getAttribute('aria-selected') === 'true') return;

        // Deactivate current
        this.tabs.forEach((tab, i) => {
            tab.setAttribute('aria-selected', 'false');
            tab.setAttribute('tabindex', '-1');
            tab.classList.remove(this.options.activeClass);
        });

        this.panels.forEach((panel, i) => {
            panel.hidden = true;
            panel.classList.remove(this.options.activeClass);
        });

        // Activate new
        const tab = this.tabs[index];
        const panel = this.panels[index];

        tab.setAttribute('aria-selected', 'true');
        tab.setAttribute('tabindex', '0');
        tab.classList.add(this.options.activeClass);

        if (panel) {
            panel.hidden = false;
            panel.classList.add(this.options.activeClass);
            
            // Animate panel
            panel.style.animation = `tabFadeIn ${this.options.animationDuration}ms ease`;
        }

        this.activeIndex = index;

        if (this.options.onChange) {
            this.options.onChange(index, tab, panel);
        }
    }

    // Public API
    next() {
        const newIndex = this.activeIndex === this.tabs.length - 1 ? 0 : this.activeIndex + 1;
        this.activateTab(newIndex);
    }

    prev() {
        const newIndex = this.activeIndex === 0 ? this.tabs.length - 1 : this.activeIndex - 1;
        this.activateTab(newIndex);
    }

    goTo(index) {
        this.activateTab(index);
    }

    getActive() {
        return {
            index: this.activeIndex,
            tab: this.tabs[this.activeIndex],
            panel: this.panels[this.activeIndex]
        };
    }
}

// Auto-initialize tabs
function initTabs() {
    document.querySelectorAll('[data-tabs]').forEach(container => {
        new TabPanel(container);
    });
}

// Run on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTabs);
} else {
    initTabs();
}

// Styles
const tabStyles = document.createElement('style');
tabStyles.textContent = `
    @keyframes tabFadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Tab container */
    .tabs-container {
        width: 100%;
    }

    /* Tab list */
    [role="tablist"] {
        display: flex;
        gap: 0;
        border-bottom: 2px solid var(--border-color);
        margin-bottom: 1.5rem;
    }

    /* Individual tab */
    [role="tab"] {
        padding: 0.875rem 1.25rem;
        background: none;
        border: none;
        border-bottom: 2px solid transparent;
        margin-bottom: -2px;
        color: var(--text-secondary);
        font-size: 0.9375rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        white-space: nowrap;
    }

    [role="tab"]:hover {
        color: var(--text-primary);
        background: var(--bg-tertiary);
    }

    [role="tab"][aria-selected="true"] {
        color: var(--accent-primary);
        border-bottom-color: var(--accent-primary);
    }

    [role="tab"]:focus {
        outline: none;
        box-shadow: inset 0 0 0 2px var(--accent-primary);
    }

    [role="tab"]:focus:not(:focus-visible) {
        box-shadow: none;
    }

    /* Tab with icon */
    [role="tab"] i {
        margin-right: 0.5rem;
    }

    /* Tab badge */
    [role="tab"] .badge {
        margin-left: 0.5rem;
        font-size: 0.75rem;
    }

    /* Tab panel */
    [role="tabpanel"] {
        outline: none;
    }

    [role="tabpanel"][hidden] {
        display: none;
    }

    /* Pill tabs variant */
    .tabs-pills [role="tablist"] {
        gap: 0.5rem;
        border-bottom: none;
        background: var(--bg-tertiary);
        padding: 0.375rem;
        border-radius: 10px;
        width: fit-content;
    }

    .tabs-pills [role="tab"] {
        border-radius: 8px;
        border-bottom: none;
        margin-bottom: 0;
    }

    .tabs-pills [role="tab"][aria-selected="true"] {
        background: var(--bg-card);
        box-shadow: var(--shadow-sm);
        color: var(--text-primary);
    }

    /* Vertical tabs variant */
    .tabs-vertical {
        display: flex;
        gap: 1.5rem;
    }

    .tabs-vertical [role="tablist"] {
        flex-direction: column;
        border-bottom: none;
        border-right: 2px solid var(--border-color);
        margin-bottom: 0;
        padding-right: 0;
        min-width: 200px;
    }

    .tabs-vertical [role="tab"] {
        text-align: left;
        border-bottom: none;
        border-right: 2px solid transparent;
        margin-right: -2px;
        margin-bottom: 0;
    }

    .tabs-vertical [role="tab"][aria-selected="true"] {
        border-right-color: var(--accent-primary);
        border-bottom-color: transparent;
    }

    .tabs-vertical .tab-content {
        flex: 1;
    }

    /* Card tabs variant */
    .tabs-card [role="tablist"] {
        border-bottom: 1px solid var(--border-color);
    }

    .tabs-card [role="tab"] {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-bottom: none;
        border-radius: 8px 8px 0 0;
        margin-right: -1px;
        margin-bottom: -1px;
    }

    .tabs-card [role="tab"][aria-selected="true"] {
        background: var(--bg-card);
        border-bottom: 1px solid var(--bg-card);
    }

    /* Responsive */
    @media (max-width: 576px) {
        [role="tablist"] {
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            scrollbar-width: none;
        }

        [role="tablist"]::-webkit-scrollbar {
            display: none;
        }

        .tabs-vertical {
            flex-direction: column;
        }

        .tabs-vertical [role="tablist"] {
            flex-direction: row;
            border-right: none;
            border-bottom: 2px solid var(--border-color);
            min-width: auto;
            overflow-x: auto;
        }

        .tabs-vertical [role="tab"] {
            border-right: none;
            border-bottom: 2px solid transparent;
        }

        .tabs-vertical [role="tab"][aria-selected="true"] {
            border-bottom-color: var(--accent-primary);
        }
    }
`;
document.head.appendChild(tabStyles);

// Export
window.TabPanel = TabPanel;
window.createTabs = (container, options) => new TabPanel(container, options);

