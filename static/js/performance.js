/**
 * Performance Utilities
 * Lazy loading, debouncing, throttling, and optimization helpers
 */

// ===== Debounce =====
function debounce(func, wait, immediate = false) {
    let timeout;
    return function executedFunction(...args) {
        const context = this;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

// ===== Throttle =====
function throttle(func, limit) {
    let inThrottle;
    return function executedFunction(...args) {
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// ===== Request Animation Frame Throttle =====
function rafThrottle(func) {
    let ticking = false;
    return function executedFunction(...args) {
        const context = this;
        if (!ticking) {
            requestAnimationFrame(() => {
                func.apply(context, args);
                ticking = false;
            });
            ticking = true;
        }
    };
}

// ===== Lazy Loading =====
class LazyLoader {
    constructor(options = {}) {
        this.options = {
            root: null,
            rootMargin: '50px',
            threshold: 0.1,
            ...options
        };
        
        this.observer = null;
        this.init();
    }

    init() {
        if ('IntersectionObserver' in window) {
            this.observer = new IntersectionObserver(
                this.handleIntersection.bind(this),
                this.options
            );
        }
    }

    handleIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                this.loadElement(entry.target);
                this.observer.unobserve(entry.target);
            }
        });
    }

    loadElement(element) {
        // Lazy load images
        if (element.tagName === 'IMG') {
            if (element.dataset.src) {
                element.src = element.dataset.src;
            }
            if (element.dataset.srcset) {
                element.srcset = element.dataset.srcset;
            }
            element.classList.remove('lazy');
            element.classList.add('loaded');
        }

        // Lazy load background images
        if (element.dataset.bg) {
            element.style.backgroundImage = `url(${element.dataset.bg})`;
            element.classList.remove('lazy-bg');
            element.classList.add('loaded');
        }

        // Lazy load iframes
        if (element.tagName === 'IFRAME' && element.dataset.src) {
            element.src = element.dataset.src;
            element.classList.remove('lazy');
            element.classList.add('loaded');
        }

        // Custom callback
        if (element.dataset.lazyCallback) {
            const callback = window[element.dataset.lazyCallback];
            if (typeof callback === 'function') {
                callback(element);
            }
        }

        // Dispatch event
        element.dispatchEvent(new CustomEvent('lazyloaded'));
    }

    observe(elements) {
        if (!this.observer) {
            // Fallback for browsers without IntersectionObserver
            elements.forEach(el => this.loadElement(el));
            return;
        }

        if (typeof elements === 'string') {
            elements = document.querySelectorAll(elements);
        }

        elements.forEach(el => this.observer.observe(el));
    }

    disconnect() {
        if (this.observer) {
            this.observer.disconnect();
        }
    }
}

// ===== Virtual Scroll =====
class VirtualScroller {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' 
            ? document.querySelector(container) 
            : container;
        
        this.options = {
            itemHeight: 50,
            buffer: 5,
            renderItem: (item, index) => `<div>${item}</div>`,
            ...options
        };

        this.items = [];
        this.scrollTop = 0;
        this.visibleItems = [];
        
        if (this.container) {
            this.init();
        }
    }

    init() {
        // Create wrapper elements
        this.viewport = document.createElement('div');
        this.viewport.className = 'virtual-scroll-viewport';
        this.viewport.style.cssText = 'overflow-y: auto; height: 100%;';

        this.content = document.createElement('div');
        this.content.className = 'virtual-scroll-content';
        this.content.style.cssText = 'position: relative;';

        this.viewport.appendChild(this.content);
        this.container.appendChild(this.viewport);

        // Bind scroll handler
        this.viewport.addEventListener('scroll', throttle(() => {
            this.scrollTop = this.viewport.scrollTop;
            this.render();
        }, 16));
    }

    setItems(items) {
        this.items = items;
        this.content.style.height = `${items.length * this.options.itemHeight}px`;
        this.render();
    }

    render() {
        const { itemHeight, buffer, renderItem } = this.options;
        const viewportHeight = this.viewport.clientHeight;
        
        const startIndex = Math.max(0, Math.floor(this.scrollTop / itemHeight) - buffer);
        const endIndex = Math.min(
            this.items.length,
            Math.ceil((this.scrollTop + viewportHeight) / itemHeight) + buffer
        );

        let html = '';
        for (let i = startIndex; i < endIndex; i++) {
            html += `<div class="virtual-item" style="
                position: absolute;
                top: ${i * itemHeight}px;
                height: ${itemHeight}px;
                width: 100%;
            ">${renderItem(this.items[i], i)}</div>`;
        }

        this.content.innerHTML = html;
    }

    scrollToIndex(index) {
        this.viewport.scrollTop = index * this.options.itemHeight;
    }
}

// ===== Resource Preloading =====
const preloader = {
    preloadImage(src) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.onerror = reject;
            img.src = src;
        });
    },

    preloadImages(sources) {
        return Promise.all(sources.map(src => this.preloadImage(src)));
    },

    preloadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.onload = resolve;
            script.onerror = reject;
            script.src = src;
            document.head.appendChild(script);
        });
    },

    preloadStyle(href) {
        return new Promise((resolve, reject) => {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.onload = resolve;
            link.onerror = reject;
            link.href = href;
            document.head.appendChild(link);
        });
    },

    prefetch(url) {
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = url;
        document.head.appendChild(link);
    },

    preconnect(url) {
        const link = document.createElement('link');
        link.rel = 'preconnect';
        link.href = url;
        document.head.appendChild(link);
    }
};

// ===== Performance Monitoring =====
const perfMonitor = {
    marks: new Map(),
    
    start(label) {
        this.marks.set(label, performance.now());
    },

    end(label) {
        const startTime = this.marks.get(label);
        if (startTime) {
            const duration = performance.now() - startTime;
            this.marks.delete(label);
            return duration;
        }
        return null;
    },

    measure(label, fn) {
        this.start(label);
        const result = fn();
        const duration = this.end(label);
        console.log(`${label}: ${duration.toFixed(2)}ms`);
        return result;
    },

    async measureAsync(label, fn) {
        this.start(label);
        const result = await fn();
        const duration = this.end(label);
        console.log(`${label}: ${duration.toFixed(2)}ms`);
        return result;
    },

    getPageLoadMetrics() {
        const timing = performance.timing;
        return {
            domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
            loadComplete: timing.loadEventEnd - timing.navigationStart,
            domInteractive: timing.domInteractive - timing.navigationStart,
            firstPaint: performance.getEntriesByType('paint')
                .find(p => p.name === 'first-paint')?.startTime || 0,
            firstContentfulPaint: performance.getEntriesByType('paint')
                .find(p => p.name === 'first-contentful-paint')?.startTime || 0
        };
    }
};

// ===== Memory-efficient Event Delegation =====
function delegate(parentSelector, eventType, childSelector, callback) {
    const parent = document.querySelector(parentSelector);
    if (!parent) return;

    parent.addEventListener(eventType, (e) => {
        const target = e.target.closest(childSelector);
        if (target && parent.contains(target)) {
            callback.call(target, e);
        }
    });
}

// ===== Request Idle Callback Polyfill =====
window.requestIdleCallback = window.requestIdleCallback || function(callback) {
    const start = Date.now();
    return setTimeout(() => {
        callback({
            didTimeout: false,
            timeRemaining: () => Math.max(0, 50 - (Date.now() - start))
        });
    }, 1);
};

// ===== Defer Non-Critical Work =====
function deferWork(callback, priority = 'low') {
    if (priority === 'high') {
        return requestAnimationFrame(callback);
    } else if (priority === 'idle') {
        return requestIdleCallback(callback, { timeout: 1000 });
    } else {
        return setTimeout(callback, 0);
    }
}

// ===== Batch DOM Updates =====
class DOMBatcher {
    constructor() {
        this.reads = [];
        this.writes = [];
        this.scheduled = false;
    }

    read(fn) {
        this.reads.push(fn);
        this.scheduleFlush();
    }

    write(fn) {
        this.writes.push(fn);
        this.scheduleFlush();
    }

    scheduleFlush() {
        if (!this.scheduled) {
            this.scheduled = true;
            requestAnimationFrame(() => this.flush());
        }
    }

    flush() {
        // Execute all reads first
        const reads = this.reads.splice(0);
        reads.forEach(fn => fn());

        // Then execute all writes
        const writes = this.writes.splice(0);
        writes.forEach(fn => fn());

        this.scheduled = false;

        // If more work was added during flush, schedule again
        if (this.reads.length || this.writes.length) {
            this.scheduleFlush();
        }
    }
}

// ===== Exports =====
window.debounce = debounce;
window.throttle = throttle;
window.rafThrottle = rafThrottle;
window.LazyLoader = LazyLoader;
window.VirtualScroller = VirtualScroller;
window.preloader = preloader;
window.perfMonitor = perfMonitor;
window.delegate = delegate;
window.deferWork = deferWork;
window.DOMBatcher = DOMBatcher;

// Initialize lazy loader for images
document.addEventListener('DOMContentLoaded', () => {
    const lazyLoader = new LazyLoader();
    lazyLoader.observe('[data-src], [data-bg], .lazy');
    window.lazyLoader = lazyLoader;
});




