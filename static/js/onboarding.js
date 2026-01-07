/**
 * Welcome & Onboarding Modal
 * First-time user experience
 */

class OnboardingManager {
    constructor(options = {}) {
        this.options = {
            storageKey: 'onboardingComplete',
            showOnFirstVisit: true,
            steps: [
                {
                    title: 'Welcome to Code Practice! 🎉',
                    content: `
                        <p>Your personal coding practice companion for mastering data structures and algorithms.</p>
                        <div class="onboarding-features">
                            <div class="feature">
                                <i class="fas fa-brain"></i>
                                <span>AI-Powered Recommendations</span>
                            </div>
                            <div class="feature">
                                <i class="fas fa-redo"></i>
                                <span>Spaced Repetition</span>
                            </div>
                            <div class="feature">
                                <i class="fas fa-chart-line"></i>
                                <span>Progress Analytics</span>
                            </div>
                        </div>
                    `,
                    image: null
                },
                {
                    title: 'Track Your Progress 📈',
                    content: `
                        <p>Watch your skills grow with detailed analytics and visualizations.</p>
                        <ul class="onboarding-list">
                            <li><i class="fas fa-check"></i> Daily streaks and milestones</li>
                            <li><i class="fas fa-check"></i> Topic mastery tracking</li>
                            <li><i class="fas fa-check"></i> Performance insights</li>
                            <li><i class="fas fa-check"></i> Study time analytics</li>
                        </ul>
                    `,
                    image: null
                },
                {
                    title: 'Smart Practice Sessions 🧠',
                    content: `
                        <p>Our intelligent system suggests what to practice next based on:</p>
                        <ul class="onboarding-list">
                            <li><i class="fas fa-star"></i> Your skill gaps</li>
                            <li><i class="fas fa-clock"></i> Optimal review timing</li>
                            <li><i class="fas fa-bullseye"></i> Your goals</li>
                            <li><i class="fas fa-chart-bar"></i> Performance patterns</li>
                        </ul>
                    `,
                    image: null
                },
                {
                    title: 'Keyboard Shortcuts ⌨️',
                    content: `
                        <p>Speed up your workflow with these shortcuts:</p>
                        <div class="shortcut-grid">
                            <div class="shortcut"><kbd>/</kbd> Open search</div>
                            <div class="shortcut"><kbd>?</kbd> Show shortcuts</div>
                            <div class="shortcut"><kbd>D</kbd> Toggle dark mode</div>
                            <div class="shortcut"><kbd>N</kbd> Next problem</div>
                            <div class="shortcut"><kbd>H</kbd> Go home</div>
                            <div class="shortcut"><kbd>S</kbd> Open settings</div>
                        </div>
                    `,
                    image: null
                },
                {
                    title: "You're All Set! 🚀",
                    content: `
                        <p>Start your coding journey today!</p>
                        <div class="onboarding-cta">
                            <p class="cta-text">Set your daily goal:</p>
                            <div class="goal-selector">
                                <button class="goal-btn" data-goal="1">1</button>
                                <button class="goal-btn" data-goal="3">3</button>
                                <button class="goal-btn active" data-goal="5">5</button>
                                <button class="goal-btn" data-goal="10">10</button>
                            </div>
                            <p class="goal-label">problems per day</p>
                        </div>
                    `,
                    image: null
                }
            ],
            onComplete: null,
            ...options
        };

        this.currentStep = 0;
        this.modal = null;
        
        if (this.options.showOnFirstVisit && !this.isComplete()) {
            this.show();
        }
    }

    isComplete() {
        return localStorage.getItem(this.options.storageKey) === 'true';
    }

    markComplete() {
        localStorage.setItem(this.options.storageKey, 'true');
    }

    show() {
        this.createModal();
        this.renderStep(0);
        document.body.style.overflow = 'hidden';
    }

    hide() {
        if (this.modal) {
            this.modal.classList.add('hiding');
            setTimeout(() => {
                this.modal.remove();
                this.modal = null;
                document.body.style.overflow = '';
            }, 300);
        }
    }

    createModal() {
        if (this.modal) return;

        this.modal = document.createElement('div');
        this.modal.className = 'onboarding-modal';
        this.modal.innerHTML = `
            <div class="onboarding-backdrop"></div>
            <div class="onboarding-container">
                <button class="onboarding-skip" aria-label="Skip onboarding">
                    Skip <i class="fas fa-times"></i>
                </button>
                <div class="onboarding-content"></div>
                <div class="onboarding-progress">
                    ${this.options.steps.map((_, i) => `
                        <div class="progress-dot ${i === 0 ? 'active' : ''}" data-step="${i}"></div>
                    `).join('')}
                </div>
                <div class="onboarding-actions">
                    <button class="onboarding-btn secondary" id="onboarding-prev" style="visibility: hidden;">
                        <i class="fas fa-arrow-left"></i> Back
                    </button>
                    <button class="onboarding-btn primary" id="onboarding-next">
                        Next <i class="fas fa-arrow-right"></i>
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(this.modal);
        this.bindEvents();
        
        // Animate in
        requestAnimationFrame(() => {
            this.modal.classList.add('visible');
        });
    }

    bindEvents() {
        // Skip button
        this.modal.querySelector('.onboarding-skip').addEventListener('click', () => {
            this.complete();
        });

        // Backdrop click
        this.modal.querySelector('.onboarding-backdrop').addEventListener('click', () => {
            this.complete();
        });

        // Next button
        this.modal.querySelector('#onboarding-next').addEventListener('click', () => {
            if (this.currentStep < this.options.steps.length - 1) {
                this.nextStep();
            } else {
                this.complete();
            }
        });

        // Prev button
        this.modal.querySelector('#onboarding-prev').addEventListener('click', () => {
            this.prevStep();
        });

        // Progress dots
        this.modal.querySelectorAll('.progress-dot').forEach(dot => {
            dot.addEventListener('click', () => {
                const step = parseInt(dot.dataset.step);
                this.goToStep(step);
            });
        });

        // Goal buttons (last step)
        this.modal.addEventListener('click', (e) => {
            if (e.target.classList.contains('goal-btn')) {
                this.modal.querySelectorAll('.goal-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                e.target.classList.add('active');
                localStorage.setItem('dailyGoal', e.target.dataset.goal);
            }
        });

        // Keyboard navigation
        document.addEventListener('keydown', this.handleKeydown.bind(this));
    }

    handleKeydown(e) {
        if (!this.modal) return;
        
        if (e.key === 'Escape') {
            this.complete();
        } else if (e.key === 'ArrowRight' || e.key === 'Enter') {
            if (this.currentStep < this.options.steps.length - 1) {
                this.nextStep();
            } else {
                this.complete();
            }
        } else if (e.key === 'ArrowLeft') {
            this.prevStep();
        }
    }

    renderStep(index) {
        const step = this.options.steps[index];
        const content = this.modal.querySelector('.onboarding-content');
        const prevBtn = this.modal.querySelector('#onboarding-prev');
        const nextBtn = this.modal.querySelector('#onboarding-next');
        
        // Update content
        content.innerHTML = `
            <h2 class="onboarding-title">${step.title}</h2>
            <div class="onboarding-body">${step.content}</div>
        `;

        // Update progress dots
        this.modal.querySelectorAll('.progress-dot').forEach((dot, i) => {
            dot.classList.toggle('active', i === index);
            dot.classList.toggle('completed', i < index);
        });

        // Update buttons
        prevBtn.style.visibility = index === 0 ? 'hidden' : 'visible';
        
        if (index === this.options.steps.length - 1) {
            nextBtn.innerHTML = 'Get Started <i class="fas fa-rocket"></i>';
        } else {
            nextBtn.innerHTML = 'Next <i class="fas fa-arrow-right"></i>';
        }

        // Animate content
        content.classList.add('animate');
        setTimeout(() => content.classList.remove('animate'), 400);
    }

    nextStep() {
        if (this.currentStep < this.options.steps.length - 1) {
            this.currentStep++;
            this.renderStep(this.currentStep);
        }
    }

    prevStep() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.renderStep(this.currentStep);
        }
    }

    goToStep(index) {
        if (index >= 0 && index < this.options.steps.length) {
            this.currentStep = index;
            this.renderStep(this.currentStep);
        }
    }

    complete() {
        this.markComplete();
        this.hide();
        
        if (this.options.onComplete) {
            this.options.onComplete();
        }

        // Welcome celebration
        if (window.confetti) {
            setTimeout(() => window.confetti.cannon(), 300);
        }

        if (window.toast) {
            setTimeout(() => {
                window.toast.success('Welcome! Start your first practice session.');
            }, 500);
        }
    }

    // Reset onboarding (for testing)
    reset() {
        localStorage.removeItem(this.options.storageKey);
    }
}

// Create styles
const onboardingStyles = document.createElement('style');
onboardingStyles.textContent = `
    .onboarding-modal {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 10004;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .onboarding-modal.visible {
        opacity: 1;
    }

    .onboarding-modal.hiding {
        opacity: 0;
    }

    .onboarding-backdrop {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(8px);
    }

    .onboarding-container {
        position: relative;
        width: 90%;
        max-width: 500px;
        background: var(--bg-card);
        border-radius: 20px;
        padding: 2.5rem;
        box-shadow: 0 25px 80px rgba(0, 0, 0, 0.4);
        transform: scale(0.9);
        transition: transform 0.3s ease;
    }

    .onboarding-modal.visible .onboarding-container {
        transform: scale(1);
    }

    .onboarding-skip {
        position: absolute;
        top: 1rem;
        right: 1rem;
        background: none;
        border: none;
        color: var(--text-muted);
        font-size: 0.875rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 0.375rem;
        padding: 0.5rem;
    }

    .onboarding-skip:hover {
        color: var(--text-primary);
    }

    .onboarding-content {
        text-align: center;
        min-height: 280px;
    }

    .onboarding-content.animate {
        animation: fadeSlideIn 0.4s ease;
    }

    @keyframes fadeSlideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .onboarding-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 1.5rem;
    }

    .onboarding-body {
        color: var(--text-secondary);
        font-size: 1rem;
        line-height: 1.6;
    }

    .onboarding-body p {
        margin-bottom: 1.5rem;
    }

    .onboarding-features {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin-top: 1.5rem;
    }

    .onboarding-features .feature {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.5rem;
    }

    .onboarding-features .feature i {
        font-size: 2rem;
        color: var(--accent-primary);
    }

    .onboarding-features .feature span {
        font-size: 0.75rem;
        color: var(--text-muted);
    }

    .onboarding-list {
        list-style: none;
        padding: 0;
        text-align: left;
        max-width: 300px;
        margin: 0 auto;
    }

    .onboarding-list li {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.5rem 0;
    }

    .onboarding-list li i {
        color: var(--accent-success);
        font-size: 0.875rem;
    }

    .shortcut-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.75rem;
        max-width: 350px;
        margin: 0 auto;
    }

    .shortcut {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.875rem;
        text-align: left;
    }

    .shortcut kbd {
        background: var(--bg-tertiary);
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        min-width: 24px;
        text-align: center;
    }

    .onboarding-cta {
        margin-top: 1.5rem;
    }

    .cta-text {
        margin-bottom: 1rem !important;
    }

    .goal-selector {
        display: flex;
        justify-content: center;
        gap: 0.75rem;
    }

    .goal-btn {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        border: 2px solid var(--border-color);
        background: var(--bg-tertiary);
        color: var(--text-primary);
        font-size: 1.125rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .goal-btn:hover {
        border-color: var(--accent-primary);
    }

    .goal-btn.active {
        background: var(--accent-primary);
        border-color: var(--accent-primary);
        color: white;
        transform: scale(1.1);
    }

    .goal-label {
        font-size: 0.875rem;
        color: var(--text-muted);
        margin-top: 0.75rem !important;
    }

    .onboarding-progress {
        display: flex;
        justify-content: center;
        gap: 0.5rem;
        margin: 2rem 0;
    }

    .progress-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: var(--bg-tertiary);
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .progress-dot:hover {
        background: var(--border-color);
    }

    .progress-dot.active {
        background: var(--accent-primary);
        transform: scale(1.2);
    }

    .progress-dot.completed {
        background: var(--accent-success);
    }

    .onboarding-actions {
        display: flex;
        justify-content: space-between;
    }

    .onboarding-btn {
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .onboarding-btn.secondary {
        background: var(--bg-tertiary);
        border: none;
        color: var(--text-secondary);
    }

    .onboarding-btn.secondary:hover {
        background: var(--border-color);
    }

    .onboarding-btn.primary {
        background: var(--accent-primary);
        border: none;
        color: white;
    }

    .onboarding-btn.primary:hover {
        filter: brightness(1.1);
        transform: translateY(-2px);
    }

    @media (max-width: 576px) {
        .onboarding-container {
            width: 95%;
            padding: 1.5rem;
        }

        .onboarding-title {
            font-size: 1.5rem;
        }

        .onboarding-features {
            flex-direction: column;
            gap: 1rem;
        }

        .shortcut-grid {
            grid-template-columns: 1fr;
        }
    }
`;
document.head.appendChild(onboardingStyles);

// Initialize
const onboarding = new OnboardingManager();
window.onboarding = onboarding;

// Manual trigger
window.showOnboarding = () => {
    onboarding.reset();
    onboarding.show();
};

