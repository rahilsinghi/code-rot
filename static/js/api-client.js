/**
 * API Client with Error Handling & Retry Logic
 * Robust HTTP client with automatic retries, error handling, and request queuing
 */

class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
        this.retryConfig = {
            maxRetries: 3,
            baseDelay: 1000,
            maxDelay: 10000,
            retryOn: [408, 429, 500, 502, 503, 504]
        };
        this.timeout = 30000;
        this.requestQueue = [];
        this.isOnline = navigator.onLine;
        this.pendingRequests = new Map();
        
        this.init();
    }

    init() {
        // Monitor online status
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.processQueue();
            window.toast?.success('Connection restored');
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            window.toast?.warning('You are offline. Requests will be queued.');
        });
    }

    /**
     * Set base URL
     */
    setBaseURL(url) {
        this.baseURL = url;
    }

    /**
     * Set default headers
     */
    setHeaders(headers) {
        this.defaultHeaders = { ...this.defaultHeaders, ...headers };
    }

    /**
     * Set auth token
     */
    setAuthToken(token) {
        if (token) {
            this.defaultHeaders['Authorization'] = `Bearer ${token}`;
        } else {
            delete this.defaultHeaders['Authorization'];
        }
    }

    /**
     * Main request method with retry logic
     */
    async request(url, options = {}) {
        const fullURL = url.startsWith('http') ? url : `${this.baseURL}${url}`;
        const config = {
            method: 'GET',
            headers: { ...this.defaultHeaders, ...options.headers },
            ...options
        };

        // If offline, queue the request
        if (!this.isOnline && config.method !== 'GET') {
            return this.queueRequest(fullURL, config);
        }

        // Create abort controller for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        config.signal = controller.signal;

        // Track pending request
        const requestId = `${config.method}_${fullURL}_${Date.now()}`;
        this.pendingRequests.set(requestId, controller);

        try {
            const response = await this.executeWithRetry(fullURL, config);
            clearTimeout(timeoutId);
            this.pendingRequests.delete(requestId);
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            this.pendingRequests.delete(requestId);
            throw this.handleError(error, fullURL, config);
        }
    }

    /**
     * Execute request with retry logic
     */
    async executeWithRetry(url, config, attempt = 0) {
        try {
            const response = await fetch(url, config);

            // Check if we should retry
            if (!response.ok && this.shouldRetry(response.status, attempt)) {
                const delay = this.calculateDelay(attempt);
                await this.sleep(delay);
                return this.executeWithRetry(url, config, attempt + 1);
            }

            // Handle response
            return this.handleResponse(response);
        } catch (error) {
            // Retry on network errors
            if (this.isNetworkError(error) && attempt < this.retryConfig.maxRetries) {
                const delay = this.calculateDelay(attempt);
                await this.sleep(delay);
                return this.executeWithRetry(url, config, attempt + 1);
            }
            throw error;
        }
    }

    /**
     * Handle response parsing
     */
    async handleResponse(response) {
        const contentType = response.headers.get('content-type');
        let data;

        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            data = await response.text();
        }

        if (!response.ok) {
            const error = new APIError(
                data.message || data.error || `HTTP ${response.status}`,
                response.status,
                data
            );
            throw error;
        }

        return {
            data,
            status: response.status,
            headers: Object.fromEntries(response.headers.entries())
        };
    }

    /**
     * Handle and format errors
     */
    handleError(error, url, config) {
        if (error instanceof APIError) {
            return error;
        }

        if (error.name === 'AbortError') {
            return new APIError('Request timeout', 408, { url });
        }

        if (!navigator.onLine) {
            return new APIError('No internet connection', 0, { url });
        }

        return new APIError(
            error.message || 'Network error',
            0,
            { url, originalError: error.toString() }
        );
    }

    /**
     * Check if request should be retried
     */
    shouldRetry(status, attempt) {
        return (
            attempt < this.retryConfig.maxRetries &&
            this.retryConfig.retryOn.includes(status)
        );
    }

    /**
     * Calculate delay with exponential backoff and jitter
     */
    calculateDelay(attempt) {
        const exponentialDelay = this.retryConfig.baseDelay * Math.pow(2, attempt);
        const jitter = Math.random() * 1000;
        return Math.min(exponentialDelay + jitter, this.retryConfig.maxDelay);
    }

    /**
     * Check if error is a network error
     */
    isNetworkError(error) {
        return (
            error.name === 'TypeError' ||
            error.message.includes('Failed to fetch') ||
            error.message.includes('Network request failed')
        );
    }

    /**
     * Queue request for when online
     */
    queueRequest(url, config) {
        return new Promise((resolve, reject) => {
            this.requestQueue.push({ url, config, resolve, reject });
            window.toast?.info('Request queued for when online');
        });
    }

    /**
     * Process queued requests
     */
    async processQueue() {
        const queue = [...this.requestQueue];
        this.requestQueue = [];

        for (const { url, config, resolve, reject } of queue) {
            try {
                const response = await this.request(url, config);
                resolve(response);
            } catch (error) {
                reject(error);
            }
        }
    }

    /**
     * Cancel all pending requests
     */
    cancelAll() {
        this.pendingRequests.forEach(controller => controller.abort());
        this.pendingRequests.clear();
    }

    /**
     * Cancel specific request
     */
    cancel(requestId) {
        const controller = this.pendingRequests.get(requestId);
        if (controller) {
            controller.abort();
            this.pendingRequests.delete(requestId);
        }
    }

    // Utility
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // HTTP Methods
    async get(url, options = {}) {
        return this.request(url, { ...options, method: 'GET' });
    }

    async post(url, data, options = {}) {
        return this.request(url, {
            ...options,
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async put(url, data, options = {}) {
        return this.request(url, {
            ...options,
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async patch(url, data, options = {}) {
        return this.request(url, {
            ...options,
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }

    async delete(url, options = {}) {
        return this.request(url, { ...options, method: 'DELETE' });
    }

    // Convenience methods with error handling
    async safeGet(url, options = {}) {
        try {
            return await this.get(url, options);
        } catch (error) {
            this.showError(error);
            return { data: null, error };
        }
    }

    async safePost(url, data, options = {}) {
        try {
            return await this.post(url, data, options);
        } catch (error) {
            this.showError(error);
            return { data: null, error };
        }
    }

    showError(error) {
        const message = error.getUserMessage?.() || error.message || 'An error occurred';
        window.toast?.error(message);
    }
}

/**
 * Custom API Error class
 */
class APIError extends Error {
    constructor(message, status, data = {}) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.data = data;
        this.timestamp = new Date().toISOString();
    }

    getUserMessage() {
        const messages = {
            0: 'Unable to connect. Please check your internet connection.',
            400: 'Invalid request. Please check your input.',
            401: 'Please log in to continue.',
            403: 'You do not have permission to perform this action.',
            404: 'The requested resource was not found.',
            408: 'Request timed out. Please try again.',
            429: 'Too many requests. Please wait a moment.',
            500: 'Server error. Please try again later.',
            502: 'Server is temporarily unavailable.',
            503: 'Service unavailable. Please try again later.',
            504: 'Server took too long to respond.'
        };
        return messages[this.status] || this.message;
    }

    isAuthError() {
        return this.status === 401 || this.status === 403;
    }

    isServerError() {
        return this.status >= 500;
    }

    isClientError() {
        return this.status >= 400 && this.status < 500;
    }

    isNetworkError() {
        return this.status === 0;
    }

    toJSON() {
        return {
            name: this.name,
            message: this.message,
            status: this.status,
            data: this.data,
            timestamp: this.timestamp
        };
    }
}

/**
 * Request interceptor manager
 */
class InterceptorManager {
    constructor() {
        this.requestInterceptors = [];
        this.responseInterceptors = [];
    }

    addRequestInterceptor(onFulfilled, onRejected) {
        const id = this.requestInterceptors.length;
        this.requestInterceptors.push({ onFulfilled, onRejected });
        return id;
    }

    addResponseInterceptor(onFulfilled, onRejected) {
        const id = this.responseInterceptors.length;
        this.responseInterceptors.push({ onFulfilled, onRejected });
        return id;
    }

    removeRequestInterceptor(id) {
        this.requestInterceptors[id] = null;
    }

    removeResponseInterceptor(id) {
        this.responseInterceptors[id] = null;
    }
}

// Initialize default API client
const api = new APIClient('http://localhost:4500');
window.api = api;
window.APIClient = APIClient;
window.APIError = APIError;

// Add global error handler for unhandled API errors
window.addEventListener('unhandledrejection', (event) => {
    if (event.reason instanceof APIError) {
        event.preventDefault();
        window.toast?.error(event.reason.getUserMessage());
        console.error('Unhandled API Error:', event.reason.toJSON());
    }
});

