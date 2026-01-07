/**
 * Animated Stats Counter
 * Smooth number animations with formatting
 */

class StatsCounter {
    constructor(element, options = {}) {
        this.element = typeof element === 'string' 
            ? document.querySelector(element) 
            : element;
        
        if (!this.element) return;

        this.options = {
            start: 0,
            end: parseInt(this.element.dataset.count) || 100,
            duration: 2000,
            delay: 0,
            easing: 'easeOutExpo',
            separator: ',',
            decimal: '.',
            decimals: 0,
            prefix: '',
            suffix: '',
            onStart: null,
            onComplete: null,
            onUpdate: null,
            startOnView: true,
            ...options
        };

        this.currentValue = this.options.start;
        this.hasStarted = false;

        this.init();
    }

    init() {
        // Set initial value
        this.render(this.options.start);

        if (this.options.startOnView) {
            this.observeVisibility();
        } else {
            setTimeout(() => this.start(), this.options.delay);
        }
    }

    observeVisibility() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !this.hasStarted) {
                    setTimeout(() => this.start(), this.options.delay);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.2 });

        observer.observe(this.element);
    }

    start() {
        if (this.hasStarted) return;
        this.hasStarted = true;

        if (this.options.onStart) {
            this.options.onStart(this);
        }

        const startTime = performance.now();
        const { start, end, duration } = this.options;

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            const easedProgress = this.ease(progress);
            this.currentValue = start + (end - start) * easedProgress;

            this.render(this.currentValue);

            if (this.options.onUpdate) {
                this.options.onUpdate(this.currentValue, this);
            }

            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                this.currentValue = end;
                this.render(end);
                
                if (this.options.onComplete) {
                    this.options.onComplete(this);
                }
            }
        };

        requestAnimationFrame(animate);
    }

    ease(t) {
        const easings = {
            linear: t => t,
            easeInQuad: t => t * t,
            easeOutQuad: t => t * (2 - t),
            easeInOutQuad: t => t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t,
            easeInCubic: t => t * t * t,
            easeOutCubic: t => (--t) * t * t + 1,
            easeInOutCubic: t => t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1,
            easeOutExpo: t => t === 1 ? 1 : 1 - Math.pow(2, -10 * t),
            easeOutBack: t => {
                const c1 = 1.70158;
                const c3 = c1 + 1;
                return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
            }
        };

        return easings[this.options.easing] 
            ? easings[this.options.easing](t) 
            : easings.easeOutExpo(t);
    }

    format(value) {
        const { decimals, separator, decimal, prefix, suffix } = this.options;
        
        // Round to specified decimals
        const fixed = value.toFixed(decimals);
        
        // Split into integer and decimal parts
        const parts = fixed.split('.');
        
        // Add thousand separators
        parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, separator);
        
        // Join with decimal separator
        const formatted = parts.join(decimal);
        
        return prefix + formatted + suffix;
    }

    render(value) {
        this.element.textContent = this.format(value);
    }

    // Update the target value
    update(newEnd, animate = true) {
        this.options.start = this.currentValue;
        this.options.end = newEnd;
        
        if (animate) {
            this.hasStarted = false;
            this.start();
        } else {
            this.currentValue = newEnd;
            this.render(newEnd);
        }
    }

    // Reset to start
    reset() {
        this.hasStarted = false;
        this.currentValue = this.options.start;
        this.render(this.options.start);
    }
}

// Auto-initialize counters
function initCounters() {
    document.querySelectorAll('[data-counter]').forEach(element => {
        new StatsCounter(element, {
            end: parseInt(element.dataset.count) || 0,
            duration: parseInt(element.dataset.duration) || 2000,
            decimals: parseInt(element.dataset.decimals) || 0,
            prefix: element.dataset.prefix || '',
            suffix: element.dataset.suffix || ''
        });
    });
}

// Run on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCounters);
} else {
    initCounters();
}

// Styles for counter components
const counterStyles = document.createElement('style');
counterStyles.textContent = `
    /* Stats Card */
    .stat-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }

    .stat-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-md);
    }

    .stat-icon {
        width: 48px;
        height: 48px;
        margin: 0 auto 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--bg-tertiary);
        border-radius: 12px;
        font-size: 1.25rem;
        color: var(--accent-primary);
    }

    .stat-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1;
        margin-bottom: 0.5rem;
    }

    .stat-label {
        font-size: 0.875rem;
        color: var(--text-muted);
    }

    /* Stat with trend */
    .stat-trend {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        font-size: 0.75rem;
        font-weight: 500;
        padding: 0.25rem 0.5rem;
        border-radius: 20px;
        margin-top: 0.75rem;
    }

    .stat-trend.up {
        background: rgba(81, 207, 102, 0.15);
        color: var(--accent-success);
    }

    .stat-trend.down {
        background: rgba(255, 107, 107, 0.15);
        color: var(--accent-danger);
    }

    .stat-trend.neutral {
        background: var(--bg-tertiary);
        color: var(--text-muted);
    }

    /* Stats Row */
    .stats-row {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
    }

    /* Inline Stat */
    .stat-inline {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        background: var(--bg-card);
        border-radius: 10px;
        border: 1px solid var(--border-color);
    }

    .stat-inline .stat-icon {
        margin: 0;
        width: 40px;
        height: 40px;
        font-size: 1rem;
    }

    .stat-inline .stat-content {
        flex: 1;
    }

    .stat-inline .stat-value {
        font-size: 1.5rem;
        margin-bottom: 0.125rem;
    }

    .stat-inline .stat-label {
        font-size: 0.75rem;
    }

    /* Big Number */
    .big-number {
        font-size: 4rem;
        font-weight: 800;
        background: var(--gradient-primary);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1;
    }

    /* Counter with ring */
    .stat-ring {
        position: relative;
        width: 120px;
        height: 120px;
        margin: 0 auto 1rem;
    }

    .stat-ring svg {
        transform: rotate(-90deg);
    }

    .stat-ring-bg {
        fill: none;
        stroke: var(--bg-tertiary);
        stroke-width: 8;
    }

    .stat-ring-fill {
        fill: none;
        stroke: var(--accent-primary);
        stroke-width: 8;
        stroke-linecap: round;
        stroke-dasharray: 326.73;
        stroke-dashoffset: 326.73;
        transition: stroke-dashoffset 1.5s ease-out;
    }

    .stat-ring-value {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text-primary);
    }

    /* Color variants */
    .stat-card.success .stat-icon { color: var(--accent-success); background: rgba(81, 207, 102, 0.15); }
    .stat-card.warning .stat-icon { color: var(--accent-warning); background: rgba(255, 193, 7, 0.15); }
    .stat-card.danger .stat-icon { color: var(--accent-danger); background: rgba(255, 107, 107, 0.15); }
    .stat-card.info .stat-icon { color: var(--accent-info); background: rgba(0, 207, 240, 0.15); }

    /* Animated dot for live stats */
    .stat-live::after {
        content: '';
        display: inline-block;
        width: 8px;
        height: 8px;
        background: var(--accent-success);
        border-radius: 50%;
        margin-left: 0.5rem;
        animation: pulse-live 1.5s ease-in-out infinite;
    }

    @keyframes pulse-live {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.2); }
    }
`;
document.head.appendChild(counterStyles);

// Export
window.StatsCounter = StatsCounter;
window.createCounter = (el, options) => new StatsCounter(el, options);

