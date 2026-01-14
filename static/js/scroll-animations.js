/**
 * Scroll Animations Component
 * Animate elements when they scroll into view
 */

class ScrollAnimations {
    constructor(options = {}) {
        this.options = {
            selector: '[data-animate]',
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px',
            once: true,
            delay: 0,
            duration: 600,
            easing: 'ease-out',
            disabled: false,
            ...options
        };

        this.observer = null;
        this.elements = [];

        if (!this.options.disabled && this.supportsIntersectionObserver()) {
            this.init();
        } else {
            // Fallback: show all elements immediately
            this.showAll();
        }
    }

    supportsIntersectionObserver() {
        return 'IntersectionObserver' in window;
    }

    init() {
        this.createObserver();
        this.observeElements();
        this.handleReducedMotion();
    }

    createObserver() {
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.animateElement(entry.target);
                    
                    if (this.options.once) {
                        this.observer.unobserve(entry.target);
                    }
                } else if (!this.options.once) {
                    this.resetElement(entry.target);
                }
            });
        }, {
            threshold: this.options.threshold,
            rootMargin: this.options.rootMargin
        });
    }

    observeElements() {
        this.elements = document.querySelectorAll(this.options.selector);
        
        this.elements.forEach((el, index) => {
            // Set initial state
            this.prepareElement(el, index);
            this.observer.observe(el);
        });
    }

    prepareElement(el, index) {
        const animation = el.dataset.animate || 'fadeInUp';
        const delay = parseInt(el.dataset.animateDelay) || (index * 100);
        const duration = parseInt(el.dataset.animateDuration) || this.options.duration;

        el.style.opacity = '0';
        el.style.transition = `all ${duration}ms ${this.options.easing} ${delay}ms`;
        
        // Set initial transform based on animation type
        const transforms = {
            fadeInUp: 'translateY(30px)',
            fadeInDown: 'translateY(-30px)',
            fadeInLeft: 'translateX(-30px)',
            fadeInRight: 'translateX(30px)',
            zoomIn: 'scale(0.9)',
            zoomOut: 'scale(1.1)',
            flipInX: 'perspective(400px) rotateX(90deg)',
            flipInY: 'perspective(400px) rotateY(90deg)',
            fadeIn: 'none'
        };

        if (transforms[animation]) {
            el.style.transform = transforms[animation];
        }

        el.dataset.prepared = 'true';
    }

    animateElement(el) {
        el.style.opacity = '1';
        el.style.transform = 'none';
        el.classList.add('animated');

        // Dispatch event
        el.dispatchEvent(new CustomEvent('animateIn', { bubbles: true }));
    }

    resetElement(el) {
        const animation = el.dataset.animate || 'fadeInUp';
        
        el.style.opacity = '0';
        el.classList.remove('animated');

        const transforms = {
            fadeInUp: 'translateY(30px)',
            fadeInDown: 'translateY(-30px)',
            fadeInLeft: 'translateX(-30px)',
            fadeInRight: 'translateX(30px)',
            zoomIn: 'scale(0.9)',
            zoomOut: 'scale(1.1)'
        };

        if (transforms[animation]) {
            el.style.transform = transforms[animation];
        }
    }

    showAll() {
        document.querySelectorAll(this.options.selector).forEach(el => {
            el.style.opacity = '1';
            el.style.transform = 'none';
        });
    }

    handleReducedMotion() {
        const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        
        if (mediaQuery.matches) {
            this.showAll();
            this.destroy();
        }

        mediaQuery.addEventListener('change', (e) => {
            if (e.matches) {
                this.showAll();
                this.destroy();
            }
        });
    }

    // Refresh observer (for dynamically added elements)
    refresh() {
        this.observeElements();
    }

    // Animate a specific element programmatically
    animate(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        if (element && !element.dataset.prepared) {
            this.prepareElement(element, 0);
        }
        if (element) {
            setTimeout(() => this.animateElement(element), 10);
        }
    }

    destroy() {
        if (this.observer) {
            this.observer.disconnect();
        }
    }
}

// Scroll progress indicator
class ScrollProgress {
    constructor(options = {}) {
        this.options = {
            container: null, // null for whole page
            showBar: true,
            showPercent: false,
            position: 'top', // top, bottom
            color: 'var(--accent-primary)',
            height: 4,
            onChange: null,
            ...options
        };

        this.progress = 0;
        this.init();
    }

    init() {
        if (this.options.showBar) {
            this.createBar();
        }
        this.bindEvents();
        this.updateProgress();
    }

    createBar() {
        this.bar = document.createElement('div');
        this.bar.className = `scroll-progress-bar ${this.options.position}`;
        this.bar.innerHTML = `
            <div class="scroll-progress-fill"></div>
            ${this.options.showPercent ? '<span class="scroll-progress-percent">0%</span>' : ''}
        `;
        document.body.appendChild(this.bar);

        this.fill = this.bar.querySelector('.scroll-progress-fill');
    }

    bindEvents() {
        const target = this.options.container || window;
        target.addEventListener('scroll', () => this.updateProgress(), { passive: true });
        window.addEventListener('resize', () => this.updateProgress(), { passive: true });
    }

    updateProgress() {
        let scrollTop, scrollHeight, clientHeight;

        if (this.options.container) {
            const el = typeof this.options.container === 'string'
                ? document.querySelector(this.options.container)
                : this.options.container;
            scrollTop = el.scrollTop;
            scrollHeight = el.scrollHeight;
            clientHeight = el.clientHeight;
        } else {
            scrollTop = window.scrollY;
            scrollHeight = document.documentElement.scrollHeight;
            clientHeight = window.innerHeight;
        }

        this.progress = Math.min(100, (scrollTop / (scrollHeight - clientHeight)) * 100);

        if (this.fill) {
            this.fill.style.width = `${this.progress}%`;
        }

        if (this.options.showPercent) {
            const percentEl = this.bar.querySelector('.scroll-progress-percent');
            if (percentEl) {
                percentEl.textContent = `${Math.round(this.progress)}%`;
            }
        }

        if (this.options.onChange) {
            this.options.onChange(this.progress);
        }
    }

    getProgress() {
        return this.progress;
    }

    destroy() {
        if (this.bar) {
            this.bar.remove();
        }
    }
}

// Parallax effect
class ParallaxScroll {
    constructor(selector, options = {}) {
        this.elements = document.querySelectorAll(selector);
        this.options = {
            speed: 0.5,
            direction: 'vertical', // vertical, horizontal
            ...options
        };

        if (this.elements.length > 0) {
            this.init();
        }
    }

    init() {
        this.bindEvents();
        this.update();
    }

    bindEvents() {
        window.addEventListener('scroll', () => this.update(), { passive: true });
    }

    update() {
        const scrollY = window.scrollY;

        this.elements.forEach(el => {
            const rect = el.getBoundingClientRect();
            const speed = parseFloat(el.dataset.parallaxSpeed) || this.options.speed;
            const offset = (scrollY - el.offsetTop) * speed;

            if (this.options.direction === 'vertical') {
                el.style.transform = `translateY(${offset}px)`;
            } else {
                el.style.transform = `translateX(${offset}px)`;
            }
        });
    }
}

// Styles
const scrollStyles = document.createElement('style');
scrollStyles.textContent = `
    /* Animated elements initial state */
    [data-animate] {
        will-change: opacity, transform;
    }

    [data-animate].animated {
        will-change: auto;
    }

    /* Scroll progress bar */
    .scroll-progress-bar {
        position: fixed;
        left: 0;
        right: 0;
        height: 4px;
        background: var(--bg-tertiary);
        z-index: 9999;
    }

    .scroll-progress-bar.top {
        top: 0;
    }

    .scroll-progress-bar.bottom {
        bottom: 0;
    }

    .scroll-progress-fill {
        height: 100%;
        background: var(--gradient-primary);
        width: 0;
        transition: width 0.1s linear;
    }

    .scroll-progress-percent {
        position: absolute;
        right: 1rem;
        top: 50%;
        transform: translateY(-50%);
        font-size: 0.625rem;
        font-weight: 600;
        color: var(--text-muted);
        background: var(--bg-card);
        padding: 0.125rem 0.375rem;
        border-radius: 4px;
    }

    /* Smooth scroll */
    html.smooth-scroll {
        scroll-behavior: smooth;
    }

    @media (prefers-reduced-motion: reduce) {
        html.smooth-scroll {
            scroll-behavior: auto;
        }

        [data-animate] {
            opacity: 1 !important;
            transform: none !important;
            transition: none !important;
        }
    }

    /* Scroll to top button */
    .scroll-to-top {
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: var(--accent-primary);
        color: white;
        border: none;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.25rem;
        box-shadow: var(--shadow-lg);
        opacity: 0;
        visibility: hidden;
        transform: translateY(20px);
        transition: all 0.3s ease;
        z-index: 1000;
    }

    .scroll-to-top.visible {
        opacity: 1;
        visibility: visible;
        transform: translateY(0);
    }

    .scroll-to-top:hover {
        transform: translateY(-4px);
    }

    /* Parallax container */
    .parallax-container {
        overflow: hidden;
        position: relative;
    }

    [data-parallax] {
        will-change: transform;
    }
`;
document.head.appendChild(scrollStyles);

// Auto-initialize
const scrollAnimations = new ScrollAnimations();

// Scroll to top button
function initScrollToTop() {
    const btn = document.createElement('button');
    btn.className = 'scroll-to-top';
    btn.innerHTML = '<i class="fas fa-chevron-up"></i>';
    btn.setAttribute('aria-label', 'Scroll to top');
    document.body.appendChild(btn);

    btn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            btn.classList.add('visible');
        } else {
            btn.classList.remove('visible');
        }
    }, { passive: true });
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initScrollToTop);
} else {
    initScrollToTop();
}

// Export
window.ScrollAnimations = ScrollAnimations;
window.ScrollProgress = ScrollProgress;
window.ParallaxScroll = ParallaxScroll;
window.scrollAnimations = scrollAnimations;


