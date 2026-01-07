/**
 * Enhanced Difficulty Selector Component
 * Visual difficulty selection with descriptions
 */

class DifficultySelector {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' 
            ? document.querySelector(container) 
            : container;
        
        this.options = {
            selected: null,
            onChange: null,
            showDescriptions: true,
            showStats: true,
            difficulties: [
                {
                    id: 'easy',
                    label: 'Easy',
                    color: '#51cf66',
                    gradient: 'linear-gradient(135deg, #51cf66 0%, #40c057 100%)',
                    icon: 'fa-seedling',
                    description: 'Perfect for beginners',
                    timeEstimate: '10-15 min',
                    count: 0
                },
                {
                    id: 'medium',
                    label: 'Medium',
                    color: '#ffd43b',
                    gradient: 'linear-gradient(135deg, #ffd43b 0%, #fab005 100%)',
                    icon: 'fa-fire',
                    description: 'Build your skills',
                    timeEstimate: '20-30 min',
                    count: 0
                },
                {
                    id: 'hard',
                    label: 'Hard',
                    color: '#ff6b6b',
                    gradient: 'linear-gradient(135deg, #ff6b6b 0%, #fa5252 100%)',
                    icon: 'fa-bolt',
                    description: 'Challenge yourself',
                    timeEstimate: '30-45 min',
                    count: 0
                }
            ],
            ...options
        };
        
        this.selected = this.options.selected;
        this.render();
    }

    render() {
        if (!this.container) return;
        
        this.container.innerHTML = `
            <div class="difficulty-selector">
                ${this.options.difficulties.map(d => this.renderOption(d)).join('')}
            </div>
        `;
        
        this.bindEvents();
        this.addStyles();
    }

    renderOption(difficulty) {
        const isSelected = this.selected === difficulty.id;
        
        return `
            <div class="difficulty-option ${isSelected ? 'selected' : ''}" 
                 data-difficulty="${difficulty.id}"
                 style="--difficulty-color: ${difficulty.color}; --difficulty-gradient: ${difficulty.gradient}">
                <div class="difficulty-icon">
                    <i class="fas ${difficulty.icon}"></i>
                </div>
                <div class="difficulty-content">
                    <div class="difficulty-label">${difficulty.label}</div>
                    ${this.options.showDescriptions ? `
                        <div class="difficulty-description">${difficulty.description}</div>
                    ` : ''}
                    <div class="difficulty-meta">
                        <span class="difficulty-time">
                            <i class="far fa-clock"></i> ${difficulty.timeEstimate}
                        </span>
                        ${this.options.showStats && difficulty.count > 0 ? `
                            <span class="difficulty-count">${difficulty.count} solved</span>
                        ` : ''}
                    </div>
                </div>
                <div class="difficulty-check">
                    <i class="fas fa-check"></i>
                </div>
            </div>
        `;
    }

    bindEvents() {
        this.container.querySelectorAll('.difficulty-option').forEach(option => {
            option.addEventListener('click', () => {
                const difficulty = option.dataset.difficulty;
                this.select(difficulty);
            });
            
            option.addEventListener('mouseenter', () => {
                option.classList.add('hovered');
            });
            
            option.addEventListener('mouseleave', () => {
                option.classList.remove('hovered');
            });
        });
    }

    select(difficulty) {
        if (this.selected === difficulty) {
            this.selected = null;
        } else {
            this.selected = difficulty;
        }
        
        this.container.querySelectorAll('.difficulty-option').forEach(option => {
            option.classList.toggle('selected', option.dataset.difficulty === this.selected);
        });
        
        if (this.options.onChange) {
            this.options.onChange(this.selected);
        }
    }

    getValue() {
        return this.selected;
    }

    setValue(difficulty) {
        this.select(difficulty);
    }

    updateCount(difficulty, count) {
        const difficultyConfig = this.options.difficulties.find(d => d.id === difficulty);
        if (difficultyConfig) {
            difficultyConfig.count = count;
            this.render();
        }
    }

    addStyles() {
        if (document.getElementById('difficulty-selector-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'difficulty-selector-styles';
        styles.textContent = `
            .difficulty-selector {
                display: flex;
                flex-direction: column;
                gap: 0.75rem;
            }
            
            .difficulty-option {
                display: flex;
                align-items: center;
                gap: 1rem;
                padding: 1rem 1.25rem;
                background: var(--bg-card);
                border: 2px solid var(--border-color);
                border-radius: 12px;
                cursor: pointer;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }
            
            .difficulty-option::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 4px;
                height: 100%;
                background: var(--difficulty-color);
                opacity: 0.5;
                transition: width 0.3s ease, opacity 0.3s ease;
            }
            
            .difficulty-option:hover {
                border-color: var(--difficulty-color);
                transform: translateX(4px);
            }
            
            .difficulty-option:hover::before {
                width: 6px;
                opacity: 1;
            }
            
            .difficulty-option.selected {
                border-color: var(--difficulty-color);
                background: linear-gradient(90deg, 
                    rgba(var(--difficulty-color), 0.05) 0%, 
                    var(--bg-card) 100%
                );
            }
            
            .difficulty-option.selected::before {
                width: 6px;
                opacity: 1;
            }
            
            .difficulty-icon {
                width: 48px;
                height: 48px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: var(--bg-tertiary);
                border-radius: 12px;
                font-size: 1.25rem;
                color: var(--difficulty-color);
                transition: all 0.3s ease;
            }
            
            .difficulty-option:hover .difficulty-icon,
            .difficulty-option.selected .difficulty-icon {
                background: var(--difficulty-gradient);
                color: white;
                transform: scale(1.05);
            }
            
            .difficulty-content {
                flex: 1;
            }
            
            .difficulty-label {
                font-size: 1rem;
                font-weight: 600;
                color: var(--text-primary);
                margin-bottom: 0.125rem;
            }
            
            .difficulty-description {
                font-size: 0.8125rem;
                color: var(--text-muted);
                margin-bottom: 0.375rem;
            }
            
            .difficulty-meta {
                display: flex;
                align-items: center;
                gap: 1rem;
                font-size: 0.75rem;
                color: var(--text-secondary);
            }
            
            .difficulty-time {
                display: flex;
                align-items: center;
                gap: 0.375rem;
            }
            
            .difficulty-count {
                padding: 0.125rem 0.5rem;
                background: var(--bg-tertiary);
                border-radius: 10px;
            }
            
            .difficulty-check {
                width: 28px;
                height: 28px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: var(--bg-tertiary);
                border-radius: 50%;
                color: var(--text-muted);
                font-size: 0.75rem;
                transition: all 0.3s ease;
                opacity: 0;
            }
            
            .difficulty-option.selected .difficulty-check {
                opacity: 1;
                background: var(--difficulty-color);
                color: white;
            }
            
            /* Compact variant */
            .difficulty-selector.compact .difficulty-option {
                padding: 0.75rem 1rem;
            }
            
            .difficulty-selector.compact .difficulty-icon {
                width: 36px;
                height: 36px;
                font-size: 1rem;
            }
            
            .difficulty-selector.compact .difficulty-description {
                display: none;
            }
            
            /* Horizontal variant */
            .difficulty-selector.horizontal {
                flex-direction: row;
            }
            
            .difficulty-selector.horizontal .difficulty-option {
                flex: 1;
                flex-direction: column;
                text-align: center;
                padding: 1.5rem 1rem;
            }
            
            .difficulty-selector.horizontal .difficulty-option::before {
                width: 100%;
                height: 4px;
                bottom: 0;
                top: auto;
            }
            
            .difficulty-selector.horizontal .difficulty-option:hover::before {
                height: 6px;
            }
            
            .difficulty-selector.horizontal .difficulty-content {
                text-align: center;
            }
            
            .difficulty-selector.horizontal .difficulty-meta {
                justify-content: center;
                flex-wrap: wrap;
            }
            
            .difficulty-selector.horizontal .difficulty-check {
                position: absolute;
                top: 8px;
                right: 8px;
                width: 24px;
                height: 24px;
            }
            
            /* Mobile responsive */
            @media (max-width: 576px) {
                .difficulty-selector.horizontal {
                    flex-direction: column;
                }
            }
        `;
        document.head.appendChild(styles);
    }
}

// Export for use
window.DifficultySelector = DifficultySelector;

// Quick creation helper
window.createDifficultySelector = (container, options) => {
    return new DifficultySelector(container, options);
};

