/**
 * Custom Dropdown Component
 * Searchable, multi-select dropdowns
 */

class Dropdown {
    constructor(element, options = {}) {
        this.element = typeof element === 'string'
            ? document.querySelector(element)
            : element;

        if (!this.element) return;

        this.options = {
            placeholder: 'Select an option',
            searchable: false,
            multiple: false,
            clearable: true,
            disabled: false,
            maxHeight: 300,
            onChange: null,
            onSearch: null,
            options: [],
            ...options
        };

        this.isOpen = false;
        this.selectedValues = [];
        this.filteredOptions = [...this.options.options];
        this.focusedIndex = -1;

        this.init();
    }

    init() {
        this.parseOptions();
        this.render();
        this.bindEvents();
    }

    parseOptions() {
        // Parse from existing select element
        if (this.element.tagName === 'SELECT') {
            this.options.options = Array.from(this.element.options).map(opt => ({
                value: opt.value,
                label: opt.textContent,
                disabled: opt.disabled,
                selected: opt.selected
            }));
            this.options.multiple = this.element.multiple;
            this.options.placeholder = this.element.dataset.placeholder || this.options.placeholder;
            this.selectedValues = this.options.options.filter(o => o.selected).map(o => o.value);
        }
        this.filteredOptions = [...this.options.options];
    }

    render() {
        const wrapper = document.createElement('div');
        wrapper.className = `custom-dropdown ${this.options.disabled ? 'disabled' : ''}`;
        wrapper.setAttribute('role', 'combobox');
        wrapper.setAttribute('aria-expanded', 'false');
        wrapper.setAttribute('aria-haspopup', 'listbox');

        wrapper.innerHTML = `
            <div class="dropdown-trigger" tabindex="${this.options.disabled ? -1 : 0}">
                <span class="dropdown-value">${this.getDisplayValue()}</span>
                <div class="dropdown-icons">
                    ${this.options.clearable && this.selectedValues.length > 0 ? `
                        <button class="dropdown-clear" aria-label="Clear selection">
                            <i class="fas fa-times"></i>
                        </button>
                    ` : ''}
                    <i class="fas fa-chevron-down dropdown-arrow"></i>
                </div>
            </div>
            <div class="dropdown-menu" role="listbox" style="max-height: ${this.options.maxHeight}px">
                ${this.options.searchable ? `
                    <div class="dropdown-search">
                        <i class="fas fa-search"></i>
                        <input type="text" placeholder="Search..." aria-label="Search options">
                    </div>
                ` : ''}
                <div class="dropdown-options">
                    ${this.renderOptions()}
                </div>
                ${this.filteredOptions.length === 0 ? `
                    <div class="dropdown-empty">No options found</div>
                ` : ''}
            </div>
        `;

        // Replace or wrap original element
        if (this.element.tagName === 'SELECT') {
            this.element.style.display = 'none';
            this.element.parentNode.insertBefore(wrapper, this.element.nextSibling);
        } else {
            this.element.appendChild(wrapper);
        }

        this.wrapper = wrapper;
        this.trigger = wrapper.querySelector('.dropdown-trigger');
        this.menu = wrapper.querySelector('.dropdown-menu');
        this.searchInput = wrapper.querySelector('.dropdown-search input');
        this.optionsContainer = wrapper.querySelector('.dropdown-options');
    }

    renderOptions() {
        return this.filteredOptions.map((opt, index) => `
            <div class="dropdown-option ${this.selectedValues.includes(opt.value) ? 'selected' : ''} ${opt.disabled ? 'disabled' : ''}"
                 role="option"
                 aria-selected="${this.selectedValues.includes(opt.value)}"
                 data-value="${opt.value}"
                 data-index="${index}">
                ${this.options.multiple ? `
                    <span class="dropdown-checkbox">
                        <i class="fas fa-check"></i>
                    </span>
                ` : ''}
                ${opt.icon ? `<i class="${opt.icon}"></i>` : ''}
                <span class="dropdown-option-label">${opt.label}</span>
                ${opt.description ? `<span class="dropdown-option-desc">${opt.description}</span>` : ''}
            </div>
        `).join('');
    }

    getDisplayValue() {
        if (this.selectedValues.length === 0) {
            return `<span class="placeholder">${this.options.placeholder}</span>`;
        }

        if (this.options.multiple) {
            const selected = this.options.options.filter(o => this.selectedValues.includes(o.value));
            if (selected.length > 2) {
                return `${selected.length} selected`;
            }
            return selected.map(o => `<span class="dropdown-tag">${o.label}</span>`).join('');
        }

        const selected = this.options.options.find(o => o.value === this.selectedValues[0]);
        return selected ? selected.label : this.options.placeholder;
    }

    bindEvents() {
        // Toggle on click
        this.trigger.addEventListener('click', (e) => {
            if (e.target.closest('.dropdown-clear')) return;
            this.toggle();
        });

        // Keyboard navigation
        this.trigger.addEventListener('keydown', (e) => this.handleKeyboard(e));

        // Clear button
        const clearBtn = this.wrapper.querySelector('.dropdown-clear');
        if (clearBtn) {
            clearBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.clear();
            });
        }

        // Option selection
        this.optionsContainer.addEventListener('click', (e) => {
            const option = e.target.closest('.dropdown-option');
            if (option && !option.classList.contains('disabled')) {
                this.selectValue(option.dataset.value);
            }
        });

        // Search
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                this.filter(e.target.value);
            });
            this.searchInput.addEventListener('keydown', (e) => this.handleKeyboard(e));
        }

        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!this.wrapper.contains(e.target)) {
                this.close();
            }
        });
    }

    handleKeyboard(e) {
        switch (e.key) {
            case 'Enter':
            case ' ':
                e.preventDefault();
                if (!this.isOpen) {
                    this.open();
                } else if (this.focusedIndex >= 0) {
                    const opt = this.filteredOptions[this.focusedIndex];
                    if (opt && !opt.disabled) {
                        this.selectValue(opt.value);
                    }
                }
                break;
            case 'ArrowDown':
                e.preventDefault();
                if (!this.isOpen) {
                    this.open();
                } else {
                    this.focusNext();
                }
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.focusPrev();
                break;
            case 'Escape':
                this.close();
                break;
            case 'Tab':
                this.close();
                break;
        }
    }

    focusNext() {
        const enabledOptions = this.filteredOptions.filter(o => !o.disabled);
        if (enabledOptions.length === 0) return;

        let nextIndex = this.focusedIndex + 1;
        while (nextIndex < this.filteredOptions.length && this.filteredOptions[nextIndex].disabled) {
            nextIndex++;
        }
        if (nextIndex >= this.filteredOptions.length) nextIndex = 0;

        this.setFocusedIndex(nextIndex);
    }

    focusPrev() {
        let prevIndex = this.focusedIndex - 1;
        while (prevIndex >= 0 && this.filteredOptions[prevIndex].disabled) {
            prevIndex--;
        }
        if (prevIndex < 0) prevIndex = this.filteredOptions.length - 1;

        this.setFocusedIndex(prevIndex);
    }

    setFocusedIndex(index) {
        this.focusedIndex = index;
        const options = this.optionsContainer.querySelectorAll('.dropdown-option');
        options.forEach((opt, i) => {
            opt.classList.toggle('focused', i === index);
            if (i === index) {
                opt.scrollIntoView({ block: 'nearest' });
            }
        });
    }

    open() {
        if (this.options.disabled || this.isOpen) return;

        this.isOpen = true;
        this.wrapper.setAttribute('aria-expanded', 'true');
        this.wrapper.classList.add('open');

        if (this.searchInput) {
            this.searchInput.focus();
        }
    }

    close() {
        if (!this.isOpen) return;

        this.isOpen = false;
        this.wrapper.setAttribute('aria-expanded', 'false');
        this.wrapper.classList.remove('open');
        this.focusedIndex = -1;

        if (this.searchInput) {
            this.searchInput.value = '';
            this.filter('');
        }
    }

    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    selectValue(value) {
        if (this.options.multiple) {
            const index = this.selectedValues.indexOf(value);
            if (index === -1) {
                this.selectedValues.push(value);
            } else {
                this.selectedValues.splice(index, 1);
            }
        } else {
            this.selectedValues = [value];
            this.close();
        }

        this.updateDisplay();
        this.syncSelect();

        if (this.options.onChange) {
            this.options.onChange(this.getValue(), this);
        }
    }

    filter(query) {
        const q = query.toLowerCase();
        this.filteredOptions = this.options.options.filter(opt =>
            opt.label.toLowerCase().includes(q)
        );

        this.optionsContainer.innerHTML = this.renderOptions();

        const empty = this.menu.querySelector('.dropdown-empty');
        if (this.filteredOptions.length === 0) {
            if (!empty) {
                this.optionsContainer.insertAdjacentHTML('afterend', '<div class="dropdown-empty">No options found</div>');
            }
        } else if (empty) {
            empty.remove();
        }

        if (this.options.onSearch) {
            this.options.onSearch(query, this);
        }
    }

    updateDisplay() {
        this.trigger.querySelector('.dropdown-value').innerHTML = this.getDisplayValue();
        this.optionsContainer.innerHTML = this.renderOptions();

        // Update clear button
        const clearBtn = this.wrapper.querySelector('.dropdown-clear');
        if (this.options.clearable) {
            if (this.selectedValues.length > 0 && !clearBtn) {
                const icons = this.trigger.querySelector('.dropdown-icons');
                icons.insertAdjacentHTML('afterbegin', `
                    <button class="dropdown-clear" aria-label="Clear selection">
                        <i class="fas fa-times"></i>
                    </button>
                `);
                this.wrapper.querySelector('.dropdown-clear').addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.clear();
                });
            } else if (this.selectedValues.length === 0 && clearBtn) {
                clearBtn.remove();
            }
        }
    }

    syncSelect() {
        if (this.element.tagName === 'SELECT') {
            Array.from(this.element.options).forEach(opt => {
                opt.selected = this.selectedValues.includes(opt.value);
            });
            this.element.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }

    getValue() {
        return this.options.multiple ? this.selectedValues : this.selectedValues[0];
    }

    setValue(value) {
        this.selectedValues = Array.isArray(value) ? value : [value];
        this.updateDisplay();
        this.syncSelect();
    }

    clear() {
        this.selectedValues = [];
        this.updateDisplay();
        this.syncSelect();

        if (this.options.onChange) {
            this.options.onChange(null, this);
        }
    }

    destroy() {
        if (this.element.tagName === 'SELECT') {
            this.element.style.display = '';
        }
        this.wrapper.remove();
    }
}

// Auto-initialize
function initDropdowns() {
    document.querySelectorAll('[data-dropdown]').forEach(el => {
        new Dropdown(el);
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDropdowns);
} else {
    initDropdowns();
}

// Styles
const dropdownStyles = document.createElement('style');
dropdownStyles.textContent = `
    .custom-dropdown {
        position: relative;
        width: 100%;
    }

    .custom-dropdown.disabled {
        opacity: 0.6;
        pointer-events: none;
    }

    .dropdown-trigger {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem 1rem;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .dropdown-trigger:hover {
        border-color: var(--accent-primary);
    }

    .dropdown-trigger:focus {
        outline: none;
        border-color: var(--accent-primary);
        box-shadow: 0 0 0 3px rgba(var(--accent-primary-rgb), 0.15);
    }

    .dropdown-value {
        flex: 1;
        color: var(--text-primary);
        font-size: 0.9375rem;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .dropdown-value .placeholder {
        color: var(--text-muted);
    }

    .dropdown-icons {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .dropdown-arrow {
        color: var(--text-muted);
        transition: transform 0.2s ease;
    }

    .custom-dropdown.open .dropdown-arrow {
        transform: rotate(180deg);
    }

    .dropdown-clear {
        background: none;
        border: none;
        padding: 0.25rem;
        color: var(--text-muted);
        cursor: pointer;
        line-height: 1;
    }

    .dropdown-clear:hover {
        color: var(--accent-danger);
    }

    .dropdown-menu {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        margin-top: 4px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        box-shadow: var(--shadow-lg);
        z-index: 1000;
        overflow: hidden;
        opacity: 0;
        visibility: hidden;
        transform: translateY(-10px);
        transition: all 0.2s ease;
    }

    .custom-dropdown.open .dropdown-menu {
        opacity: 1;
        visibility: visible;
        transform: translateY(0);
    }

    .dropdown-search {
        display: flex;
        align-items: center;
        padding: 0.75rem;
        border-bottom: 1px solid var(--border-color);
        gap: 0.5rem;
    }

    .dropdown-search i {
        color: var(--text-muted);
    }

    .dropdown-search input {
        flex: 1;
        border: none;
        background: none;
        color: var(--text-primary);
        font-size: 0.875rem;
        outline: none;
    }

    .dropdown-options {
        overflow-y: auto;
    }

    .dropdown-option {
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem;
        cursor: pointer;
        gap: 0.75rem;
        transition: background 0.15s ease;
    }

    .dropdown-option:hover,
    .dropdown-option.focused {
        background: var(--bg-tertiary);
    }

    .dropdown-option.selected {
        background: rgba(var(--accent-primary-rgb), 0.1);
    }

    .dropdown-option.disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    .dropdown-checkbox {
        width: 18px;
        height: 18px;
        border: 2px solid var(--border-color);
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.625rem;
        color: transparent;
        transition: all 0.2s ease;
    }

    .dropdown-option.selected .dropdown-checkbox {
        background: var(--accent-primary);
        border-color: var(--accent-primary);
        color: white;
    }

    .dropdown-option-label {
        flex: 1;
        color: var(--text-primary);
    }

    .dropdown-option-desc {
        font-size: 0.75rem;
        color: var(--text-muted);
    }

    .dropdown-empty {
        padding: 1rem;
        text-align: center;
        color: var(--text-muted);
        font-size: 0.875rem;
    }

    .dropdown-tag {
        display: inline-flex;
        align-items: center;
        padding: 0.125rem 0.5rem;
        background: var(--accent-primary);
        color: white;
        border-radius: 4px;
        font-size: 0.75rem;
        margin-right: 0.25rem;
    }
`;
document.head.appendChild(dropdownStyles);

// Export
window.Dropdown = Dropdown;
window.createDropdown = (el, options) => new Dropdown(el, options);

