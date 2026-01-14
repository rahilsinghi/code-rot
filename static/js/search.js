/**
 * Global Search Component
 * Fuzzy search with recent searches and keyboard navigation
 */

class GlobalSearch {
    constructor(options = {}) {
        this.options = {
            placeholder: 'Search problems, topics, or commands...',
            maxResults: 10,
            maxRecentSearches: 5,
            debounceMs: 200,
            ...options
        };

        this.isOpen = false;
        this.searchData = [];
        this.recentSearches = this.loadRecentSearches();
        this.selectedIndex = -1;
        
        this.init();
    }

    init() {
        this.createSearchModal();
        this.bindEvents();
        this.loadSearchData();
    }

    createSearchModal() {
        const modal = document.createElement('div');
        modal.id = 'global-search-modal';
        modal.className = 'global-search-modal';
        modal.innerHTML = `
            <div class="global-search-backdrop"></div>
            <div class="global-search-container">
                <div class="global-search-header">
                    <div class="global-search-input-wrapper">
                        <i class="fas fa-search"></i>
                        <input 
                            type="text" 
                            id="global-search-input" 
                            placeholder="${this.options.placeholder}"
                            autocomplete="off"
                            spellcheck="false"
                        >
                        <div class="global-search-shortcuts">
                            <kbd>↑↓</kbd> navigate
                            <kbd>↵</kbd> select
                            <kbd>esc</kbd> close
                        </div>
                    </div>
                </div>
                <div class="global-search-body">
                    <div id="global-search-results" class="global-search-results"></div>
                </div>
                <div class="global-search-footer">
                    <span class="search-tip">
                        <i class="fas fa-lightbulb"></i>
                        Tip: Use <kbd>/</kbd> anywhere to open search
                    </span>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        this.modal = modal;
        this.input = modal.querySelector('#global-search-input');
        this.resultsContainer = modal.querySelector('#global-search-results');
    }

    bindEvents() {
        // Open search with / key (if not in input)
        document.addEventListener('keydown', (e) => {
            if (e.key === '/' && !this.isInputFocused()) {
                e.preventDefault();
                this.open();
            }
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });

        // Close on backdrop click
        this.modal.querySelector('.global-search-backdrop').addEventListener('click', () => {
            this.close();
        });

        // Handle input
        this.input.addEventListener('input', debounce((e) => {
            this.search(e.target.value);
        }, this.options.debounceMs));

        // Handle keyboard navigation
        this.input.addEventListener('keydown', (e) => {
            this.handleKeydown(e);
        });
    }

    isInputFocused() {
        const active = document.activeElement;
        return active.tagName === 'INPUT' || 
               active.tagName === 'TEXTAREA' || 
               active.isContentEditable;
    }

    open() {
        this.isOpen = true;
        this.modal.classList.add('open');
        this.input.focus();
        this.input.value = '';
        this.showRecentSearches();
        document.body.style.overflow = 'hidden';
    }

    close() {
        this.isOpen = false;
        this.modal.classList.remove('open');
        this.input.value = '';
        this.selectedIndex = -1;
        document.body.style.overflow = '';
    }

    loadSearchData() {
        // Define searchable items
        this.searchData = [
            // Pages
            { type: 'page', title: 'Dashboard', url: '/', icon: 'fa-home', keywords: 'home main overview' },
            { type: 'page', title: 'Practice', url: '/practice', icon: 'fa-code', keywords: 'coding problems solve' },
            { type: 'page', title: 'Analytics', url: '/analytics', icon: 'fa-chart-bar', keywords: 'stats progress insights' },
            { type: 'page', title: 'Review', url: '/review', icon: 'fa-redo', keywords: 'spaced repetition revise' },
            { type: 'page', title: 'Settings', url: '/settings', icon: 'fa-cog', keywords: 'preferences config' },
            { type: 'page', title: 'Study Sessions', url: '/study-sessions', icon: 'fa-clock', keywords: 'focus pomodoro timer' },
            { type: 'page', title: 'API Documentation', url: 'http://localhost:4500/api/docs', icon: 'fa-book', keywords: 'api docs reference', external: true },

            // Topics
            { type: 'topic', title: 'Arrays', icon: 'fa-list', keywords: 'array list data structure' },
            { type: 'topic', title: 'Linked Lists', icon: 'fa-link', keywords: 'linked list node pointer' },
            { type: 'topic', title: 'Trees', icon: 'fa-sitemap', keywords: 'tree binary bst traversal' },
            { type: 'topic', title: 'Graphs', icon: 'fa-project-diagram', keywords: 'graph dfs bfs shortest path' },
            { type: 'topic', title: 'Dynamic Programming', icon: 'fa-brain', keywords: 'dp memoization optimization' },
            { type: 'topic', title: 'Sorting', icon: 'fa-sort', keywords: 'sort quicksort mergesort' },
            { type: 'topic', title: 'Searching', icon: 'fa-search', keywords: 'binary search linear' },
            { type: 'topic', title: 'Hash Tables', icon: 'fa-hashtag', keywords: 'hash map dictionary' },
            { type: 'topic', title: 'Stacks & Queues', icon: 'fa-layer-group', keywords: 'stack queue lifo fifo' },
            { type: 'topic', title: 'Strings', icon: 'fa-font', keywords: 'string manipulation regex' },

            // Actions
            { type: 'action', title: 'Toggle Dark Mode', action: () => window.themeManager?.toggle(), icon: 'fa-moon', keywords: 'theme dark light mode' },
            { type: 'action', title: 'Show Keyboard Shortcuts', action: () => window.keyboardShortcuts?.showHelpModal(), icon: 'fa-keyboard', keywords: 'shortcuts keys hotkeys' },
            { type: 'action', title: 'Start Practice Session', action: () => window.location.href = '/practice', icon: 'fa-play', keywords: 'start begin practice' },
            { type: 'action', title: 'View Progress', action: () => window.location.href = '/analytics', icon: 'fa-chart-line', keywords: 'progress stats analytics' },
            { type: 'action', title: 'Clear Cache', action: () => { window.cache?.clear(); window.toast?.success('Cache cleared'); }, icon: 'fa-trash', keywords: 'clear cache storage' },

            // Problems (sample)
            { type: 'problem', title: 'Two Sum', difficulty: 'Easy', icon: 'fa-code', keywords: 'two sum array hash' },
            { type: 'problem', title: 'Valid Parentheses', difficulty: 'Easy', icon: 'fa-code', keywords: 'parentheses stack bracket' },
            { type: 'problem', title: 'Merge Two Sorted Lists', difficulty: 'Easy', icon: 'fa-code', keywords: 'merge linked list' },
            { type: 'problem', title: 'Maximum Subarray', difficulty: 'Medium', icon: 'fa-code', keywords: 'kadane array dp' },
            { type: 'problem', title: 'Binary Tree Inorder', difficulty: 'Easy', icon: 'fa-code', keywords: 'tree traversal inorder' },
        ];
    }

    search(query) {
        if (!query.trim()) {
            this.showRecentSearches();
            return;
        }

        const results = this.fuzzySearch(query);
        this.renderResults(results, query);
    }

    fuzzySearch(query) {
        const lowerQuery = query.toLowerCase();
        const words = lowerQuery.split(/\s+/);

        return this.searchData
            .map(item => {
                const searchText = `${item.title} ${item.keywords || ''}`.toLowerCase();
                let score = 0;

                // Exact title match
                if (item.title.toLowerCase() === lowerQuery) {
                    score += 100;
                }
                // Title starts with query
                else if (item.title.toLowerCase().startsWith(lowerQuery)) {
                    score += 50;
                }
                // Title contains query
                else if (item.title.toLowerCase().includes(lowerQuery)) {
                    score += 25;
                }

                // Word matching
                words.forEach(word => {
                    if (searchText.includes(word)) {
                        score += 10;
                    }
                });

                return { ...item, score };
            })
            .filter(item => item.score > 0)
            .sort((a, b) => b.score - a.score)
            .slice(0, this.options.maxResults);
    }

    renderResults(results, query) {
        if (results.length === 0) {
            this.resultsContainer.innerHTML = `
                <div class="search-empty">
                    <i class="fas fa-search"></i>
                    <p>No results found for "${query}"</p>
                    <span>Try different keywords</span>
                </div>
            `;
            return;
        }

        // Group results by type
        const grouped = this.groupByType(results);
        let html = '';

        Object.entries(grouped).forEach(([type, items]) => {
            html += `
                <div class="search-group">
                    <div class="search-group-title">${this.getTypeLabel(type)}</div>
                    ${items.map((item, i) => this.renderResultItem(item, i)).join('')}
                </div>
            `;
        });

        this.resultsContainer.innerHTML = html;
        this.selectedIndex = -1;
        this.bindResultEvents();
    }

    renderResultItem(item, index) {
        const difficultyBadge = item.difficulty 
            ? `<span class="difficulty-badge ${item.difficulty.toLowerCase()}">${item.difficulty}</span>` 
            : '';
        const externalBadge = item.external 
            ? '<i class="fas fa-external-link-alt ms-2"></i>' 
            : '';

        return `
            <div class="search-result-item" data-index="${index}" data-type="${item.type}" data-url="${item.url || ''}" data-action="${item.action ? 'true' : 'false'}">
                <div class="search-result-icon">
                    <i class="fas ${item.icon}"></i>
                </div>
                <div class="search-result-content">
                    <div class="search-result-title">${item.title}${externalBadge}</div>
                    ${difficultyBadge}
                </div>
                <div class="search-result-type">${item.type}</div>
            </div>
        `;
    }

    groupByType(results) {
        return results.reduce((groups, item) => {
            const type = item.type;
            if (!groups[type]) groups[type] = [];
            groups[type].push(item);
            return groups;
        }, {});
    }

    getTypeLabel(type) {
        const labels = {
            page: 'Pages',
            topic: 'Topics',
            action: 'Actions',
            problem: 'Problems'
        };
        return labels[type] || type;
    }

    bindResultEvents() {
        this.resultsContainer.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => this.selectResult(item));
            item.addEventListener('mouseenter', () => {
                this.clearSelection();
                item.classList.add('selected');
            });
        });
    }

    handleKeydown(e) {
        const items = this.resultsContainer.querySelectorAll('.search-result-item');
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            this.selectedIndex = Math.min(this.selectedIndex + 1, items.length - 1);
            this.updateSelection(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            this.selectedIndex = Math.max(this.selectedIndex - 1, -1);
            this.updateSelection(items);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            const selected = items[this.selectedIndex];
            if (selected) {
                this.selectResult(selected);
            }
        }
    }

    updateSelection(items) {
        this.clearSelection();
        if (this.selectedIndex >= 0 && items[this.selectedIndex]) {
            items[this.selectedIndex].classList.add('selected');
            items[this.selectedIndex].scrollIntoView({ block: 'nearest' });
        }
    }

    clearSelection() {
        this.resultsContainer.querySelectorAll('.selected').forEach(el => {
            el.classList.remove('selected');
        });
    }

    selectResult(element) {
        const type = element.dataset.type;
        const url = element.dataset.url;
        const hasAction = element.dataset.action === 'true';
        const title = element.querySelector('.search-result-title').textContent;

        // Save to recent searches
        this.saveRecentSearch(title);

        if (hasAction) {
            // Find and execute action
            const item = this.searchData.find(d => d.title === title && d.action);
            if (item?.action) {
                item.action();
            }
        } else if (url) {
            if (url.startsWith('http')) {
                window.open(url, '_blank');
            } else {
                window.location.href = url;
            }
        }

        this.close();
    }

    showRecentSearches() {
        if (this.recentSearches.length === 0) {
            this.resultsContainer.innerHTML = `
                <div class="search-empty">
                    <i class="fas fa-history"></i>
                    <p>No recent searches</p>
                    <span>Start typing to search</span>
                </div>
            `;
            return;
        }

        this.resultsContainer.innerHTML = `
            <div class="search-group">
                <div class="search-group-title">
                    Recent Searches
                    <button class="clear-recent" onclick="globalSearch.clearRecentSearches()">Clear</button>
                </div>
                ${this.recentSearches.map(term => `
                    <div class="search-result-item recent-search" data-term="${term}">
                        <div class="search-result-icon">
                            <i class="fas fa-history"></i>
                        </div>
                        <div class="search-result-content">
                            <div class="search-result-title">${term}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        // Bind click to search for that term
        this.resultsContainer.querySelectorAll('.recent-search').forEach(item => {
            item.addEventListener('click', () => {
                this.input.value = item.dataset.term;
                this.search(item.dataset.term);
            });
        });
    }

    saveRecentSearch(term) {
        this.recentSearches = [
            term,
            ...this.recentSearches.filter(t => t !== term)
        ].slice(0, this.options.maxRecentSearches);
        
        localStorage.setItem('recentSearches', JSON.stringify(this.recentSearches));
    }

    loadRecentSearches() {
        try {
            return JSON.parse(localStorage.getItem('recentSearches')) || [];
        } catch {
            return [];
        }
    }

    clearRecentSearches() {
        this.recentSearches = [];
        localStorage.removeItem('recentSearches');
        this.showRecentSearches();
    }
}

// Initialize global search
const globalSearch = new GlobalSearch();
window.globalSearch = globalSearch;

// Open search function for buttons/links
window.openSearch = () => globalSearch.open();




