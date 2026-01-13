/**
 * Pagination Component
 * Flexible pagination with multiple variants
 */

class Pagination {
    constructor(options = {}) {
        this.options = {
            container: null,
            totalItems: 0,
            itemsPerPage: 10,
            currentPage: 1,
            maxVisiblePages: 5,
            showFirstLast: true,
            showPrevNext: true,
            showInfo: true,
            showPageSizes: true,
            pageSizes: [10, 25, 50, 100],
            variant: 'default', // default, pills, bordered, minimal
            size: 'md', // sm, md, lg
            align: 'center', // left, center, right
            onChange: null,
            onPageSizeChange: null,
            ...options
        };

        this.totalPages = Math.ceil(this.options.totalItems / this.options.itemsPerPage);
        this.element = null;

        this.init();
    }

    init() {
        this.render();
        this.bindEvents();
    }

    render() {
        const container = this.options.container
            ? (typeof this.options.container === 'string'
                ? document.querySelector(this.options.container)
                : this.options.container)
            : document.body;

        if (this.element) {
            this.element.remove();
        }

        this.element = document.createElement('nav');
        this.element.className = `pagination-wrapper align-${this.options.align}`;
        this.element.setAttribute('aria-label', 'Pagination');
        this.element.innerHTML = this.getHTML();

        container.appendChild(this.element);
    }

    getHTML() {
        const { showInfo, showPageSizes } = this.options;
        
        return `
            <div class="pagination-container">
                ${showInfo ? this.getInfoHTML() : ''}
                <div class="pagination-nav">
                    ${this.getPaginationHTML()}
                </div>
                ${showPageSizes ? this.getPageSizesHTML() : ''}
            </div>
        `;
    }

    getInfoHTML() {
        const start = (this.options.currentPage - 1) * this.options.itemsPerPage + 1;
        const end = Math.min(start + this.options.itemsPerPage - 1, this.options.totalItems);
        
        return `
            <div class="pagination-info">
                Showing <strong>${start}</strong> to <strong>${end}</strong> of <strong>${this.options.totalItems}</strong>
            </div>
        `;
    }

    getPageSizesHTML() {
        const { pageSizes, itemsPerPage } = this.options;
        
        return `
            <div class="pagination-size">
                <label>Show:</label>
                <select class="page-size-select">
                    ${pageSizes.map(size => `
                        <option value="${size}" ${size === itemsPerPage ? 'selected' : ''}>${size}</option>
                    `).join('')}
                </select>
            </div>
        `;
    }

    getPaginationHTML() {
        const { currentPage, showFirstLast, showPrevNext, variant, size } = this.options;
        const pages = this.getVisiblePages();

        let html = `<ul class="pagination ${variant} ${size}">`;

        // First button
        if (showFirstLast) {
            html += `
                <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                    <button class="page-link" data-page="1" aria-label="First page">
                        <i class="fas fa-angle-double-left"></i>
                    </button>
                </li>
            `;
        }

        // Previous button
        if (showPrevNext) {
            html += `
                <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                    <button class="page-link" data-page="${currentPage - 1}" aria-label="Previous page">
                        <i class="fas fa-angle-left"></i>
                    </button>
                </li>
            `;
        }

        // Page numbers
        pages.forEach(page => {
            if (page === '...') {
                html += `
                    <li class="page-item ellipsis">
                        <span class="page-link">...</span>
                    </li>
                `;
            } else {
                html += `
                    <li class="page-item ${page === currentPage ? 'active' : ''}">
                        <button class="page-link" data-page="${page}" ${page === currentPage ? 'aria-current="page"' : ''}>
                            ${page}
                        </button>
                    </li>
                `;
            }
        });

        // Next button
        if (showPrevNext) {
            html += `
                <li class="page-item ${currentPage === this.totalPages ? 'disabled' : ''}">
                    <button class="page-link" data-page="${currentPage + 1}" aria-label="Next page">
                        <i class="fas fa-angle-right"></i>
                    </button>
                </li>
            `;
        }

        // Last button
        if (showFirstLast) {
            html += `
                <li class="page-item ${currentPage === this.totalPages ? 'disabled' : ''}">
                    <button class="page-link" data-page="${this.totalPages}" aria-label="Last page">
                        <i class="fas fa-angle-double-right"></i>
                    </button>
                </li>
            `;
        }

        html += '</ul>';
        return html;
    }

    getVisiblePages() {
        const { currentPage, maxVisiblePages } = this.options;
        const pages = [];

        if (this.totalPages <= maxVisiblePages) {
            for (let i = 1; i <= this.totalPages; i++) {
                pages.push(i);
            }
        } else {
            const half = Math.floor(maxVisiblePages / 2);
            let start = currentPage - half;
            let end = currentPage + half;

            if (start < 1) {
                start = 1;
                end = maxVisiblePages;
            }

            if (end > this.totalPages) {
                end = this.totalPages;
                start = this.totalPages - maxVisiblePages + 1;
            }

            if (start > 1) {
                pages.push(1);
                if (start > 2) pages.push('...');
            }

            for (let i = start; i <= end; i++) {
                if (i > 1 && i < this.totalPages) {
                    pages.push(i);
                }
            }

            if (end < this.totalPages) {
                if (end < this.totalPages - 1) pages.push('...');
                pages.push(this.totalPages);
            }
        }

        return pages;
    }

    bindEvents() {
        // Page click
        this.element.querySelectorAll('.page-link[data-page]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const page = parseInt(e.currentTarget.dataset.page);
                if (page >= 1 && page <= this.totalPages && page !== this.options.currentPage) {
                    this.goToPage(page);
                }
            });
        });

        // Page size change
        const sizeSelect = this.element.querySelector('.page-size-select');
        if (sizeSelect) {
            sizeSelect.addEventListener('change', (e) => {
                const newSize = parseInt(e.target.value);
                this.setPageSize(newSize);
            });
        }
    }

    goToPage(page) {
        this.options.currentPage = page;
        this.render();
        this.bindEvents();

        if (this.options.onChange) {
            this.options.onChange(page, this);
        }
    }

    setPageSize(size) {
        this.options.itemsPerPage = size;
        this.options.currentPage = 1;
        this.totalPages = Math.ceil(this.options.totalItems / size);
        this.render();
        this.bindEvents();

        if (this.options.onPageSizeChange) {
            this.options.onPageSizeChange(size, this);
        }
    }

    setTotalItems(total) {
        this.options.totalItems = total;
        this.totalPages = Math.ceil(total / this.options.itemsPerPage);
        if (this.options.currentPage > this.totalPages) {
            this.options.currentPage = this.totalPages || 1;
        }
        this.render();
        this.bindEvents();
    }

    getCurrentPage() {
        return this.options.currentPage;
    }

    getPageSize() {
        return this.options.itemsPerPage;
    }

    destroy() {
        if (this.element) {
            this.element.remove();
        }
    }
}

// Styles
const paginationStyles = document.createElement('style');
paginationStyles.textContent = `
    .pagination-wrapper {
        margin: 1.5rem 0;
    }

    .pagination-wrapper.align-left { text-align: left; }
    .pagination-wrapper.align-center { text-align: center; }
    .pagination-wrapper.align-right { text-align: right; }

    .pagination-container {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: center;
        gap: 1rem;
    }

    .pagination-wrapper.align-left .pagination-container { justify-content: flex-start; }
    .pagination-wrapper.align-right .pagination-container { justify-content: flex-end; }

    .pagination-info {
        font-size: 0.875rem;
        color: var(--text-muted);
    }

    .pagination-info strong {
        color: var(--text-primary);
    }

    .pagination-size {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.875rem;
        color: var(--text-muted);
    }

    .page-size-select {
        padding: 0.375rem 0.75rem;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 6px;
        color: var(--text-primary);
        font-size: 0.875rem;
        cursor: pointer;
    }

    .page-size-select:focus {
        outline: none;
        border-color: var(--accent-primary);
    }

    /* Pagination List */
    .pagination {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .page-item {
        display: inline-flex;
    }

    .page-link {
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 36px;
        height: 36px;
        padding: 0 0.5rem;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        color: var(--text-primary);
        font-size: 0.875rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .page-link:hover:not(:disabled) {
        background: var(--bg-tertiary);
        border-color: var(--accent-primary);
    }

    .page-item.active .page-link {
        background: var(--accent-primary);
        border-color: var(--accent-primary);
        color: white;
    }

    .page-item.disabled .page-link {
        opacity: 0.5;
        cursor: not-allowed;
        pointer-events: none;
    }

    .page-item.ellipsis .page-link {
        background: none;
        border: none;
        cursor: default;
        color: var(--text-muted);
    }

    /* Size Variants */
    .pagination.sm .page-link {
        min-width: 28px;
        height: 28px;
        font-size: 0.75rem;
        border-radius: 6px;
    }

    .pagination.lg .page-link {
        min-width: 44px;
        height: 44px;
        font-size: 1rem;
        border-radius: 10px;
    }

    /* Style Variants */
    .pagination.pills .page-link {
        border-radius: 20px;
    }

    .pagination.bordered .page-link {
        border-width: 2px;
    }

    .pagination.minimal .page-link {
        background: none;
        border: none;
    }

    .pagination.minimal .page-item.active .page-link {
        background: var(--accent-primary);
    }

    .pagination.minimal .page-link:hover:not(:disabled) {
        background: var(--bg-tertiary);
    }

    /* Icons only nav */
    .pagination.icons-only .page-link span {
        display: none;
    }

    /* Mobile */
    @media (max-width: 576px) {
        .pagination-container {
            flex-direction: column;
            gap: 0.75rem;
        }

        .pagination {
            gap: 0.125rem;
        }

        .page-link {
            min-width: 32px;
            height: 32px;
            font-size: 0.8125rem;
        }
    }
`;
document.head.appendChild(paginationStyles);

// Export
window.Pagination = Pagination;
window.createPagination = (options) => new Pagination(options);

