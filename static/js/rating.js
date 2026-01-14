/**
 * Star Rating Component
 * Interactive star ratings with half-star support
 */

class Rating {
    constructor(element, options = {}) {
        this.element = typeof element === 'string'
            ? document.querySelector(element)
            : element;

        if (!this.element) return;

        this.options = {
            max: 5,
            value: 0,
            step: 1, // 1 for full stars, 0.5 for half stars
            readonly: false,
            disabled: false,
            size: 'md', // sm, md, lg, xl
            color: 'gold', // gold, primary, danger
            showValue: true,
            showCount: false,
            count: 0,
            icon: 'star', // star, heart, thumb
            emptyIcon: null, // optional different icon for empty
            onChange: null,
            onHover: null,
            ...options
        };

        this.hoveredValue = 0;
        this.init();
    }

    init() {
        this.render();
        if (!this.options.readonly && !this.options.disabled) {
            this.bindEvents();
        }
    }

    render() {
        const { max, value, size, color, showValue, showCount, count, readonly, disabled } = this.options;

        this.element.className = `rating ${size} ${color} ${readonly ? 'readonly' : ''} ${disabled ? 'disabled' : ''}`;
        this.element.setAttribute('role', 'slider');
        this.element.setAttribute('aria-valuemin', '0');
        this.element.setAttribute('aria-valuemax', max);
        this.element.setAttribute('aria-valuenow', value);
        this.element.setAttribute('tabindex', readonly || disabled ? '-1' : '0');

        this.element.innerHTML = `
            <div class="rating-stars">
                ${this.renderStars(value)}
            </div>
            ${showValue ? `<span class="rating-value">${value.toFixed(1)}</span>` : ''}
            ${showCount ? `<span class="rating-count">(${count.toLocaleString()})</span>` : ''}
        `;

        this.starsContainer = this.element.querySelector('.rating-stars');
    }

    renderStars(activeValue) {
        const { max, step } = this.options;
        let html = '';

        for (let i = 1; i <= max; i++) {
            const fillPercent = this.getStarFill(i, activeValue, step);
            html += `
                <span class="rating-star" data-value="${i}">
                    ${this.getStarIcon(fillPercent)}
                </span>
            `;
        }

        return html;
    }

    getStarFill(starIndex, value, step) {
        if (value >= starIndex) {
            return 100;
        } else if (value >= starIndex - 1 && step === 0.5) {
            const decimal = value - Math.floor(value);
            return decimal >= 0.5 ? 50 : 0;
        }
        return 0;
    }

    getStarIcon(fillPercent) {
        const icons = {
            star: { full: 'fas fa-star', half: 'fas fa-star-half-alt', empty: 'far fa-star' },
            heart: { full: 'fas fa-heart', half: 'fas fa-heart', empty: 'far fa-heart' },
            thumb: { full: 'fas fa-thumbs-up', half: 'fas fa-thumbs-up', empty: 'far fa-thumbs-up' }
        };

        const iconSet = icons[this.options.icon] || icons.star;

        if (fillPercent >= 100) {
            return `<i class="${iconSet.full}"></i>`;
        } else if (fillPercent >= 50) {
            return `<i class="${iconSet.half}"></i>`;
        }
        return `<i class="${iconSet.empty}"></i>`;
    }

    bindEvents() {
        // Click
        this.starsContainer.addEventListener('click', (e) => {
            const star = e.target.closest('.rating-star');
            if (star) {
                const value = this.getClickValue(e, star);
                this.setValue(value);
            }
        });

        // Hover
        this.starsContainer.addEventListener('mousemove', (e) => {
            const star = e.target.closest('.rating-star');
            if (star) {
                const value = this.getClickValue(e, star);
                this.showPreview(value);
            }
        });

        this.starsContainer.addEventListener('mouseleave', () => {
            this.showPreview(0);
        });

        // Keyboard
        this.element.addEventListener('keydown', (e) => {
            let newValue = this.options.value;

            switch (e.key) {
                case 'ArrowRight':
                case 'ArrowUp':
                    e.preventDefault();
                    newValue = Math.min(this.options.max, newValue + this.options.step);
                    break;
                case 'ArrowLeft':
                case 'ArrowDown':
                    e.preventDefault();
                    newValue = Math.max(0, newValue - this.options.step);
                    break;
                case 'Home':
                    e.preventDefault();
                    newValue = 0;
                    break;
                case 'End':
                    e.preventDefault();
                    newValue = this.options.max;
                    break;
            }

            if (newValue !== this.options.value) {
                this.setValue(newValue);
            }
        });
    }

    getClickValue(event, star) {
        const starValue = parseInt(star.dataset.value);
        
        if (this.options.step === 0.5) {
            const rect = star.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const isHalf = x < rect.width / 2;
            return isHalf ? starValue - 0.5 : starValue;
        }
        
        return starValue;
    }

    showPreview(value) {
        if (value === this.hoveredValue) return;
        this.hoveredValue = value;

        if (value > 0) {
            this.starsContainer.innerHTML = this.renderStars(value);
            this.element.classList.add('hovering');
        } else {
            this.starsContainer.innerHTML = this.renderStars(this.options.value);
            this.element.classList.remove('hovering');
        }

        if (this.options.onHover) {
            this.options.onHover(value, this);
        }
    }

    setValue(value) {
        value = Math.round(value / this.options.step) * this.options.step;
        value = Math.max(0, Math.min(this.options.max, value));

        if (value === this.options.value) return;

        this.options.value = value;
        this.element.setAttribute('aria-valuenow', value);
        
        const valueDisplay = this.element.querySelector('.rating-value');
        if (valueDisplay) {
            valueDisplay.textContent = value.toFixed(1);
        }

        this.starsContainer.innerHTML = this.renderStars(value);

        if (this.options.onChange) {
            this.options.onChange(value, this);
        }
    }

    getValue() {
        return this.options.value;
    }

    setReadonly(readonly) {
        this.options.readonly = readonly;
        this.render();
        if (!readonly && !this.options.disabled) {
            this.bindEvents();
        }
    }

    destroy() {
        this.element.innerHTML = '';
        this.element.className = '';
    }
}

// Static display rating (no interaction)
function createStaticRating(value, max = 5, options = {}) {
    const container = document.createElement('div');
    new Rating(container, {
        value,
        max,
        readonly: true,
        ...options
    });
    return container;
}

// Styles
const ratingStyles = document.createElement('style');
ratingStyles.textContent = `
    .rating {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
    }

    .rating.disabled {
        opacity: 0.5;
        pointer-events: none;
    }

    .rating-stars {
        display: flex;
        gap: 0.125rem;
    }

    .rating-star {
        cursor: pointer;
        transition: transform 0.15s ease;
    }

    .rating.readonly .rating-star {
        cursor: default;
    }

    .rating:not(.readonly) .rating-star:hover {
        transform: scale(1.2);
    }

    /* Colors */
    .rating.gold .rating-star i {
        color: #ffc107;
    }

    .rating.gold .rating-star i.far {
        color: var(--text-muted);
    }

    .rating.primary .rating-star i {
        color: var(--accent-primary);
    }

    .rating.primary .rating-star i.far {
        color: var(--text-muted);
    }

    .rating.danger .rating-star i {
        color: var(--accent-danger);
    }

    .rating.danger .rating-star i.far {
        color: var(--text-muted);
    }

    /* Sizes */
    .rating.sm .rating-star {
        font-size: 0.875rem;
    }

    .rating.md .rating-star {
        font-size: 1.25rem;
    }

    .rating.lg .rating-star {
        font-size: 1.75rem;
    }

    .rating.xl .rating-star {
        font-size: 2.5rem;
    }

    /* Value Display */
    .rating-value {
        font-size: 0.9375rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    .rating.sm .rating-value {
        font-size: 0.8125rem;
    }

    .rating.lg .rating-value {
        font-size: 1.125rem;
    }

    /* Count */
    .rating-count {
        font-size: 0.8125rem;
        color: var(--text-muted);
    }

    /* Hover state */
    .rating.hovering .rating-star i {
        transition: color 0.15s ease;
    }

    /* Focus state */
    .rating:focus {
        outline: none;
    }

    .rating:focus .rating-stars {
        outline: 2px solid var(--accent-primary);
        outline-offset: 4px;
        border-radius: 4px;
    }

    /* Rating breakdown */
    .rating-breakdown {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .rating-breakdown-row {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .rating-breakdown-label {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        width: 60px;
        font-size: 0.875rem;
        color: var(--text-secondary);
    }

    .rating-breakdown-label i {
        color: #ffc107;
    }

    .rating-breakdown-bar {
        flex: 1;
        height: 8px;
        background: var(--bg-tertiary);
        border-radius: 4px;
        overflow: hidden;
    }

    .rating-breakdown-fill {
        height: 100%;
        background: #ffc107;
        border-radius: 4px;
        transition: width 0.5s ease;
    }

    .rating-breakdown-count {
        width: 50px;
        text-align: right;
        font-size: 0.8125rem;
        color: var(--text-muted);
    }

    /* Rating input group */
    .rating-input-group {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .rating-input-label {
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--text-primary);
    }

    .rating-input-hint {
        font-size: 0.75rem;
        color: var(--text-muted);
    }
`;
document.head.appendChild(ratingStyles);

// Export
window.Rating = Rating;
window.createRating = (el, options) => new Rating(el, options);
window.createStaticRating = createStaticRating;


