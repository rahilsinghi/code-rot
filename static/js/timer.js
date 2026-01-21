/**
 * Timer & Stopwatch Component
 * Pomodoro, countdown, and stopwatch functionality
 */

class Timer {
    constructor(options = {}) {
        this.options = {
            type: 'stopwatch', // 'stopwatch', 'countdown', 'pomodoro'
            duration: 25 * 60, // seconds (for countdown/pomodoro)
            breakDuration: 5 * 60, // for pomodoro
            longBreakDuration: 15 * 60,
            sessionsBeforeLongBreak: 4,
            autoStart: false,
            tickSound: false,
            alarmSound: true,
            visualNotifications: true,
            persistState: true,
            onTick: null,
            onComplete: null,
            onStateChange: null,
            ...options
        };

        this.seconds = this.options.type === 'stopwatch' ? 0 : this.options.duration;
        this.isRunning = false;
        this.intervalId = null;
        this.state = 'idle'; // 'idle', 'running', 'paused', 'work', 'break', 'longBreak'
        this.pomodoroSession = 0;
        this.totalWorkTime = 0;

        if (this.options.autoStart) {
            this.start();
        }
    }

    start() {
        if (this.isRunning) return;

        this.isRunning = true;
        this.setState(this.options.type === 'pomodoro' ? 'work' : 'running');

        this.intervalId = setInterval(() => {
            this.tick();
        }, 1000);
    }

    tick() {
        if (this.options.type === 'stopwatch') {
            this.seconds++;
            if (this.state === 'work') this.totalWorkTime++;
        } else {
            this.seconds--;
            if (this.state === 'work') this.totalWorkTime++;

            if (this.seconds <= 0) {
                this.handleComplete();
            }
        }

        if (this.options.onTick) {
            this.options.onTick(this.getTime(), this);
        }

        if (this.options.tickSound && this.seconds <= 5 && this.options.type !== 'stopwatch') {
            this.playSound('tick');
        }
    }

    handleComplete() {
        if (this.options.type === 'pomodoro') {
            if (this.state === 'work') {
                this.pomodoroSession++;
                
                if (this.pomodoroSession % this.options.sessionsBeforeLongBreak === 0) {
                    this.seconds = this.options.longBreakDuration;
                    this.setState('longBreak');
                } else {
                    this.seconds = this.options.breakDuration;
                    this.setState('break');
                }
            } else {
                this.seconds = this.options.duration;
                this.setState('work');
            }
        } else {
            this.pause();
        }

        if (this.options.alarmSound) {
            this.playSound('alarm');
        }

        if (this.options.onComplete) {
            this.options.onComplete(this.state, this);
        }
    }

    pause() {
        if (!this.isRunning) return;

        this.isRunning = false;
        clearInterval(this.intervalId);
        this.setState('paused');
    }

    resume() {
        if (this.isRunning) return;
        this.start();
    }

    toggle() {
        if (this.isRunning) {
            this.pause();
        } else {
            this.start();
        }
    }

    reset() {
        this.pause();
        this.seconds = this.options.type === 'stopwatch' ? 0 : this.options.duration;
        this.pomodoroSession = 0;
        this.setState('idle');
    }

    skip() {
        if (this.options.type === 'pomodoro') {
            this.seconds = 0;
            this.handleComplete();
        }
    }

    setState(newState) {
        this.state = newState;
        if (this.options.onStateChange) {
            this.options.onStateChange(newState, this);
        }
    }

    getTime() {
        const hours = Math.floor(this.seconds / 3600);
        const minutes = Math.floor((this.seconds % 3600) / 60);
        const secs = this.seconds % 60;

        return {
            hours,
            minutes,
            seconds: secs,
            totalSeconds: this.seconds,
            formatted: this.format(hours, minutes, secs),
            shortFormat: this.format(0, minutes, secs, false)
        };
    }

    format(h, m, s, showHours = true) {
        const pad = (n) => n.toString().padStart(2, '0');
        
        if (showHours && h > 0) {
            return `${pad(h)}:${pad(m)}:${pad(s)}`;
        }
        return `${pad(m)}:${pad(s)}`;
    }

    getProgress() {
        if (this.options.type === 'stopwatch') {
            return 0;
        }
        
        let total;
        if (this.state === 'work' || this.state === 'idle') {
            total = this.options.duration;
        } else if (this.state === 'longBreak') {
            total = this.options.longBreakDuration;
        } else {
            total = this.options.breakDuration;
        }

        return ((total - this.seconds) / total) * 100;
    }

    playSound(type) {
        // Using Web Audio API for sounds
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = ctx.createOscillator();
            const gain = ctx.createGain();
            
            oscillator.connect(gain);
            gain.connect(ctx.destination);

            if (type === 'tick') {
                oscillator.frequency.value = 800;
                gain.gain.value = 0.1;
                oscillator.start();
                oscillator.stop(ctx.currentTime + 0.05);
            } else if (type === 'alarm') {
                oscillator.frequency.value = 440;
                gain.gain.value = 0.3;
                oscillator.start();
                
                // Beep pattern
                setTimeout(() => oscillator.frequency.value = 550, 200);
                setTimeout(() => oscillator.frequency.value = 440, 400);
                oscillator.stop(ctx.currentTime + 0.6);
            }
        } catch (e) {
            console.log('Audio not available');
        }
    }

    // Create display element
    createDisplay(container) {
        const el = typeof container === 'string' 
            ? document.querySelector(container) 
            : container;
        
        if (!el) return;

        const time = this.getTime();
        const progress = this.getProgress();

        el.innerHTML = `
            <div class="timer-display ${this.state}">
                <div class="timer-ring" style="--progress: ${progress}%">
                    <svg viewBox="0 0 100 100">
                        <circle class="timer-ring-bg" cx="50" cy="50" r="45"/>
                        <circle class="timer-ring-fill" cx="50" cy="50" r="45"/>
                    </svg>
                    <div class="timer-time">${time.shortFormat}</div>
                </div>
                <div class="timer-state">${this.getStateLabel()}</div>
                <div class="timer-controls">
                    <button class="timer-btn" data-action="reset" title="Reset">
                        <i class="fas fa-redo"></i>
                    </button>
                    <button class="timer-btn primary" data-action="toggle" title="${this.isRunning ? 'Pause' : 'Start'}">
                        <i class="fas fa-${this.isRunning ? 'pause' : 'play'}"></i>
                    </button>
                    ${this.options.type === 'pomodoro' ? `
                        <button class="timer-btn" data-action="skip" title="Skip">
                            <i class="fas fa-forward"></i>
                        </button>
                    ` : ''}
                </div>
                ${this.options.type === 'pomodoro' ? `
                    <div class="timer-sessions">
                        ${Array(this.options.sessionsBeforeLongBreak).fill(0).map((_, i) => `
                            <div class="session-dot ${i < this.pomodoroSession ? 'completed' : ''}"></div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;

        // Bind controls
        el.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                if (this[action]) this[action]();
                this.createDisplay(el);
            });
        });

        // Update on tick
        this.options.onTick = () => this.createDisplay(el);
    }

    getStateLabel() {
        const labels = {
            idle: 'Ready',
            running: 'Running',
            paused: 'Paused',
            work: 'Focus Time',
            break: 'Short Break',
            longBreak: 'Long Break'
        };
        return labels[this.state] || this.state;
    }
}

// Timer styles
const timerStyles = document.createElement('style');
timerStyles.textContent = `
    .timer-display {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
        padding: 1.5rem;
    }

    .timer-ring {
        position: relative;
        width: 200px;
        height: 200px;
    }

    .timer-ring svg {
        width: 100%;
        height: 100%;
        transform: rotate(-90deg);
    }

    .timer-ring-bg {
        fill: none;
        stroke: var(--bg-tertiary);
        stroke-width: 6;
    }

    .timer-ring-fill {
        fill: none;
        stroke: var(--accent-primary);
        stroke-width: 6;
        stroke-linecap: round;
        stroke-dasharray: 283;
        stroke-dashoffset: calc(283 - (283 * var(--progress)) / 100);
        transition: stroke-dashoffset 0.5s ease;
    }

    .timer-display.work .timer-ring-fill { stroke: var(--accent-danger); }
    .timer-display.break .timer-ring-fill { stroke: var(--accent-success); }
    .timer-display.longBreak .timer-ring-fill { stroke: var(--accent-info); }

    .timer-time {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 3rem;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
        color: var(--text-primary);
    }

    .timer-state {
        font-size: 1rem;
        font-weight: 500;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    .timer-controls {
        display: flex;
        gap: 1rem;
    }

    .timer-btn {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        border: none;
        background: var(--bg-tertiary);
        color: var(--text-primary);
        font-size: 1rem;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .timer-btn:hover {
        background: var(--border-color);
        transform: scale(1.1);
    }

    .timer-btn.primary {
        width: 64px;
        height: 64px;
        background: var(--accent-primary);
        color: white;
        font-size: 1.25rem;
    }

    .timer-btn.primary:hover {
        filter: brightness(1.1);
    }

    .timer-sessions {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }

    .session-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: var(--bg-tertiary);
        transition: background 0.3s ease;
    }

    .session-dot.completed {
        background: var(--accent-success);
    }

    /* Compact timer */
    .timer-compact {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 0.75rem 1rem;
        background: var(--bg-card);
        border-radius: 10px;
        border: 1px solid var(--border-color);
    }

    .timer-compact .timer-time {
        position: static;
        transform: none;
        font-size: 1.5rem;
    }

    .timer-compact .timer-controls {
        gap: 0.5rem;
    }

    .timer-compact .timer-btn {
        width: 36px;
        height: 36px;
        font-size: 0.875rem;
    }

    .timer-compact .timer-btn.primary {
        width: 40px;
        height: 40px;
    }

    /* Mini timer (for header) */
    .timer-mini {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.375rem 0.75rem;
        background: var(--bg-tertiary);
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--text-primary);
    }

    .timer-mini.running {
        background: rgba(255, 107, 107, 0.15);
        color: var(--accent-danger);
    }

    .timer-mini.break {
        background: rgba(81, 207, 102, 0.15);
        color: var(--accent-success);
    }
`;
document.head.appendChild(timerStyles);

// Export
window.Timer = Timer;

// Factory functions
window.createStopwatch = (options) => new Timer({ type: 'stopwatch', ...options });
window.createCountdown = (duration, options) => new Timer({ type: 'countdown', duration, ...options });
window.createPomodoro = (options) => new Timer({ type: 'pomodoro', ...options });



