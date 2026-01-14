/**
 * Tag/Chip Input Component
 * Multi-value input with tags
 */

class TagInput {
    constructor(element, options = {}) {
        this.element = typeof element === 'string'
            ? document.querySelector(element)
            : element;

        if (!this.element) return;

        this.options = {
            placeholder: 'Add a tag...',
            maxTags: Infinity,
            minLength: 1,
            maxLength: 50,
            allowDuplicates: false,
            allowSpaces: false,
            delimiter: ',',
            trimValue: true,
            validate: null,
            transform: null, // Function to transform input before adding
            suggestions: [],
            autocomplete: true,
            closable: true,
            disabled: false,
            onChange: null,
            onAdd: null,
            onRemove: null,
            onInvalid: null,
            ...options
        };

        this.tags = [];
        this.wrapper = null;
        this.input = null;
        this.suggestionsDropdown = null;

        this.init();
    }

    init() {
        this.parseExisting();
        this.render();
        this.bindEvents();
    }

    parseExisting() {
        // Parse from existing input value
        if (this.element.tagName === 'INPUT' && this.element.value) {
            const values = this.element.value.split(this.options.delimiter);
            this.tags = values.filter(v => v.trim()).map(v => v.trim());
        }
    }

    render() {
        // Create wrapper
        this.wrapper = document.createElement('div');
        this.wrapper.className = `tag-input-wrapper ${this.options.disabled ? 'disabled' : ''}`;

        this.wrapper.innerHTML = `
            <div class="tag-input-tags"></div>
            <input type="text" 
                   class="tag-input-field" 
                   placeholder="${this.options.placeholder}"
                   ${this.options.disabled ? 'disabled' : ''}>
            ${this.options.autocomplete && this.options.suggestions.length > 0 ? `
                <div class="tag-suggestions"></div>
            ` : ''}
        `;

        // Insert wrapper
        if (this.element.tagName === 'INPUT') {
            this.element.style.display = 'none';
            this.element.parentNode.insertBefore(this.wrapper, this.element.nextSibling);
        } else {
            this.element.appendChild(this.wrapper);
        }

        this.tagsContainer = this.wrapper.querySelector('.tag-input-tags');
        this.input = this.wrapper.querySelector('.tag-input-field');
        this.suggestionsDropdown = this.wrapper.querySelector('.tag-suggestions');

        this.renderTags();
    }

    renderTags() {
        this.tagsContainer.innerHTML = this.tags.map((tag, index) => `
            <span class="tag-chip" data-index="${index}">
                <span class="tag-text">${this.escapeHtml(tag)}</span>
                ${this.options.closable ? `
                    <button class="tag-remove" aria-label="Remove ${tag}">
                        <i class="fas fa-times"></i>
                    </button>
                ` : ''}
            </span>
        `).join('');

        // Update hidden input
        if (this.element.tagName === 'INPUT') {
            this.element.value = this.tags.join(this.options.delimiter);
        }

        // Update placeholder
        if (this.tags.length >= this.options.maxTags) {
            this.input.disabled = true;
            this.input.placeholder = '';
        } else {
            this.input.disabled = this.options.disabled;
            this.input.placeholder = this.options.placeholder;
        }
    }

    bindEvents() {
        // Input keydown
        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === this.options.delimiter || e.key === 'Tab') {
                e.preventDefault();
                this.addTag(this.input.value);
            } else if (e.key === 'Backspace' && !this.input.value && this.tags.length > 0) {
                this.removeTag(this.tags.length - 1);
            } else if (e.key === 'Escape') {
                this.hideSuggestions();
            } else if (e.key === 'ArrowDown' && this.suggestionsDropdown) {
                e.preventDefault();
                this.navigateSuggestions(1);
            } else if (e.key === 'ArrowUp' && this.suggestionsDropdown) {
                e.preventDefault();
                this.navigateSuggestions(-1);
            }
        });

        // Input for suggestions
        this.input.addEventListener('input', () => {
            if (this.options.autocomplete && this.options.suggestions.length > 0) {
                this.showSuggestions(this.input.value);
            }
        });

        // Focus wrapper on click
        this.wrapper.addEventListener('click', (e) => {
            if (e.target === this.wrapper || e.target === this.tagsContainer) {
                this.input.focus();
            }
        });

        // Remove tag button
        this.tagsContainer.addEventListener('click', (e) => {
            const removeBtn = e.target.closest('.tag-remove');
            if (removeBtn) {
                const chip = removeBtn.closest('.tag-chip');
                const index = parseInt(chip.dataset.index);
                this.removeTag(index);
            }
        });

        // Suggestions click
        if (this.suggestionsDropdown) {
            this.suggestionsDropdown.addEventListener('click', (e) => {
                const item = e.target.closest('.tag-suggestion');
                if (item) {
                    this.addTag(item.dataset.value);
                    this.hideSuggestions();
                }
            });
        }

        // Close suggestions on outside click
        document.addEventListener('click', (e) => {
            if (!this.wrapper.contains(e.target)) {
                this.hideSuggestions();
            }
        });

        // Paste handling
        this.input.addEventListener('paste', (e) => {
            e.preventDefault();
            const text = e.clipboardData.getData('text');
            const values = text.split(this.options.delimiter);
            values.forEach(v => this.addTag(v));
        });
    }

    addTag(value) {
        // Clean value
        if (this.options.trimValue) {
            value = value.trim();
        }

        if (!this.options.allowSpaces) {
            value = value.replace(/\s+/g, '');
        }

        // Transform
        if (this.options.transform) {
            value = this.options.transform(value);
        }

        // Validate
        if (!this.validateTag(value)) {
            return false;
        }

        // Add tag
        this.tags.push(value);
        this.input.value = '';
        this.renderTags();
        this.hideSuggestions();

        // Callbacks
        if (this.options.onAdd) {
            this.options.onAdd(value, this);
        }
        if (this.options.onChange) {
            this.options.onChange(this.tags, this);
        }

        return true;
    }

    validateTag(value) {
        // Length check
        if (value.length < this.options.minLength || value.length > this.options.maxLength) {
            this.triggerInvalid(value, 'length');
            return false;
        }

        // Max tags check
        if (this.tags.length >= this.options.maxTags) {
            this.triggerInvalid(value, 'maxTags');
            return false;
        }

        // Duplicate check
        if (!this.options.allowDuplicates && this.tags.includes(value)) {
            this.triggerInvalid(value, 'duplicate');
            return false;
        }

        // Custom validation
        if (this.options.validate && !this.options.validate(value)) {
            this.triggerInvalid(value, 'custom');
            return false;
        }

        return true;
    }

    triggerInvalid(value, reason) {
        this.wrapper.classList.add('invalid');
        setTimeout(() => this.wrapper.classList.remove('invalid'), 500);

        if (this.options.onInvalid) {
            this.options.onInvalid(value, reason, this);
        }
    }

    removeTag(index) {
        const removed = this.tags.splice(index, 1)[0];
        this.renderTags();

        if (this.options.onRemove) {
            this.options.onRemove(removed, this);
        }
        if (this.options.onChange) {
            this.options.onChange(this.tags, this);
        }
    }

    showSuggestions(query) {
        if (!this.suggestionsDropdown) return;

        const q = query.toLowerCase();
        const matches = this.options.suggestions.filter(s => 
            s.toLowerCase().includes(q) && !this.tags.includes(s)
        ).slice(0, 10);

        if (matches.length === 0 || !query) {
            this.hideSuggestions();
            return;
        }

        this.suggestionsDropdown.innerHTML = matches.map((s, i) => `
            <div class="tag-suggestion ${i === 0 ? 'active' : ''}" data-value="${this.escapeHtml(s)}">
                ${this.highlightMatch(s, query)}
            </div>
        `).join('');

        this.suggestionsDropdown.classList.add('visible');
    }

    hideSuggestions() {
        if (this.suggestionsDropdown) {
            this.suggestionsDropdown.classList.remove('visible');
        }
    }

    navigateSuggestions(direction) {
        if (!this.suggestionsDropdown || !this.suggestionsDropdown.classList.contains('visible')) return;

        const items = this.suggestionsDropdown.querySelectorAll('.tag-suggestion');
        const current = this.suggestionsDropdown.querySelector('.tag-suggestion.active');
        let index = Array.from(items).indexOf(current);

        index += direction;
        if (index < 0) index = items.length - 1;
        if (index >= items.length) index = 0;

        items.forEach((item, i) => item.classList.toggle('active', i === index));

        // If enter is pressed, select the active suggestion
        if (items[index]) {
            items[index].scrollIntoView({ block: 'nearest' });
        }
    }

    highlightMatch(text, query) {
        const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    escapeRegex(text) {
        return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    // Public API
    getTags() {
        return [...this.tags];
    }

    setTags(tags) {
        this.tags = [...tags];
        this.renderTags();
    }

    addTags(tags) {
        tags.forEach(tag => this.addTag(tag));
    }

    clear() {
        this.tags = [];
        this.renderTags();
    }

    destroy() {
        if (this.element.tagName === 'INPUT') {
            this.element.style.display = '';
        }
        this.wrapper.remove();
    }
}

// Styles
const tagInputStyles = document.createElement('style');
tagInputStyles.textContent = `
    .tag-input-wrapper {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 0.75rem;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        min-height: 44px;
        cursor: text;
        transition: border-color 0.2s ease;
        position: relative;
    }

    .tag-input-wrapper:focus-within {
        border-color: var(--accent-primary);
        box-shadow: 0 0 0 3px rgba(var(--accent-primary-rgb), 0.1);
    }

    .tag-input-wrapper.disabled {
        background: var(--bg-tertiary);
        cursor: not-allowed;
    }

    .tag-input-wrapper.invalid {
        animation: shake 0.3s ease;
        border-color: var(--accent-danger);
    }

    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-4px); }
        75% { transform: translateX(4px); }
    }

    .tag-input-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 0.375rem;
    }

    .tag-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.375rem;
        padding: 0.25rem 0.5rem;
        background: var(--accent-primary);
        color: white;
        border-radius: 6px;
        font-size: 0.8125rem;
        font-weight: 500;
        animation: tagIn 0.2s ease;
    }

    @keyframes tagIn {
        from {
            opacity: 0;
            transform: scale(0.8);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }

    .tag-remove {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 16px;
        height: 16px;
        padding: 0;
        background: rgba(255, 255, 255, 0.2);
        border: none;
        border-radius: 50%;
        color: white;
        font-size: 0.5rem;
        cursor: pointer;
        transition: background 0.2s ease;
    }

    .tag-remove:hover {
        background: rgba(255, 255, 255, 0.3);
    }

    .tag-input-field {
        flex: 1;
        min-width: 100px;
        padding: 0.25rem 0;
        background: none;
        border: none;
        color: var(--text-primary);
        font-size: 0.9375rem;
        outline: none;
    }

    .tag-input-field::placeholder {
        color: var(--text-muted);
    }

    /* Suggestions */
    .tag-suggestions {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        margin-top: 4px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        box-shadow: var(--shadow-lg);
        max-height: 200px;
        overflow-y: auto;
        z-index: 100;
        opacity: 0;
        visibility: hidden;
        transform: translateY(-10px);
        transition: all 0.2s ease;
    }

    .tag-suggestions.visible {
        opacity: 1;
        visibility: visible;
        transform: translateY(0);
    }

    .tag-suggestion {
        padding: 0.625rem 0.875rem;
        cursor: pointer;
        transition: background 0.15s ease;
    }

    .tag-suggestion:hover,
    .tag-suggestion.active {
        background: var(--bg-tertiary);
    }

    .tag-suggestion mark {
        background: rgba(var(--accent-primary-rgb), 0.2);
        color: var(--accent-primary);
        padding: 0 2px;
        border-radius: 2px;
    }

    /* Tag variants */
    .tag-chip.success { background: var(--accent-success); }
    .tag-chip.warning { background: var(--accent-warning); color: #212529; }
    .tag-chip.danger { background: var(--accent-danger); }
    .tag-chip.info { background: var(--accent-info); }
    .tag-chip.secondary { background: var(--bg-tertiary); color: var(--text-primary); }

    /* Outlined tags */
    .tag-chip.outlined {
        background: transparent;
        border: 1px solid var(--accent-primary);
        color: var(--accent-primary);
    }

    .tag-chip.outlined .tag-remove {
        background: rgba(var(--accent-primary-rgb), 0.1);
        color: var(--accent-primary);
    }
`;
document.head.appendChild(tagInputStyles);

// Export
window.TagInput = TagInput;
window.createTagInput = (el, options) => new TagInput(el, options);


