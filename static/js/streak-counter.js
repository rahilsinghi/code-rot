/**
 * Streak Counter Component
 * Track daily practice streaks with persistence
 */

class StreakCounter {
    constructor(options = {}) {
        this.options = {
            storageKey: 'practiceStreak',
            onStreakChange: null,
            onMilestone: null,
            milestones: [7, 14, 30, 50, 100, 365],
            ...options
        };

        this.data = this.loadData();
        this.checkStreak();
    }

    loadData() {
        const stored = localStorage.getItem(this.options.storageKey);
        if (stored) {
            return JSON.parse(stored);
        }
        return {
            currentStreak: 0,
            longestStreak: 0,
            lastPracticeDate: null,
            totalDays: 0,
            streakHistory: [],
            milestones: []
        };
    }

    saveData() {
        localStorage.setItem(this.options.storageKey, JSON.stringify(this.data));
    }

    /**
     * Get today's date string (YYYY-MM-DD)
     */
    getToday() {
        return new Date().toISOString().split('T')[0];
    }

    /**
     * Get yesterday's date string
     */
    getYesterday() {
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        return yesterday.toISOString().split('T')[0];
    }

    /**
     * Check and update streak status
     */
    checkStreak() {
        const today = this.getToday();
        const yesterday = this.getYesterday();
        const lastPractice = this.data.lastPracticeDate;

        // If last practice was before yesterday, streak is broken
        if (lastPractice && lastPractice < yesterday) {
            if (this.data.currentStreak > 0) {
                // Save broken streak to history
                this.data.streakHistory.push({
                    streak: this.data.currentStreak,
                    endDate: lastPractice,
                    startDate: this.getStreakStartDate()
                });
                
                // Reset streak
                this.data.currentStreak = 0;
                this.saveData();
                
                if (this.options.onStreakChange) {
                    this.options.onStreakChange(0, 'broken');
                }
            }
        }
    }

    /**
     * Record practice for today
     */
    recordPractice() {
        const today = this.getToday();
        const yesterday = this.getYesterday();
        const lastPractice = this.data.lastPracticeDate;

        // Already practiced today
        if (lastPractice === today) {
            return {
                success: true,
                alreadyRecorded: true,
                streak: this.data.currentStreak
            };
        }

        // Continue streak from yesterday or start new
        if (lastPractice === yesterday || lastPractice === null) {
            this.data.currentStreak++;
        } else if (lastPractice < yesterday) {
            // Streak was broken, start fresh
            this.data.currentStreak = 1;
        }

        this.data.lastPracticeDate = today;
        this.data.totalDays++;

        // Update longest streak
        if (this.data.currentStreak > this.data.longestStreak) {
            this.data.longestStreak = this.data.currentStreak;
        }

        // Check for milestones
        this.checkMilestones();

        this.saveData();

        if (this.options.onStreakChange) {
            this.options.onStreakChange(this.data.currentStreak, 'continued');
        }

        return {
            success: true,
            alreadyRecorded: false,
            streak: this.data.currentStreak,
            isNewRecord: this.data.currentStreak === this.data.longestStreak
        };
    }

    /**
     * Check for milestone achievements
     */
    checkMilestones() {
        const streak = this.data.currentStreak;
        
        for (const milestone of this.options.milestones) {
            if (streak === milestone && !this.data.milestones.includes(milestone)) {
                this.data.milestones.push(milestone);
                
                if (this.options.onMilestone) {
                    this.options.onMilestone(milestone);
                }

                // Trigger celebration
                if (window.confetti) {
                    window.confetti.celebration();
                }

                // Show toast
                if (window.toast) {
                    window.toast.success(`🔥 ${milestone}-Day Streak! Keep it up!`);
                }
            }
        }
    }

    /**
     * Get streak start date
     */
    getStreakStartDate() {
        const start = new Date();
        start.setDate(start.getDate() - this.data.currentStreak + 1);
        return start.toISOString().split('T')[0];
    }

    /**
     * Get streak data
     */
    getStats() {
        return {
            currentStreak: this.data.currentStreak,
            longestStreak: this.data.longestStreak,
            totalDays: this.data.totalDays,
            lastPracticeDate: this.data.lastPracticeDate,
            practicedToday: this.data.lastPracticeDate === this.getToday(),
            milestones: this.data.milestones,
            streakHistory: this.data.streakHistory
        };
    }

    /**
     * Reset streak (for testing)
     */
    reset() {
        this.data = {
            currentStreak: 0,
            longestStreak: 0,
            lastPracticeDate: null,
            totalDays: 0,
            streakHistory: [],
            milestones: []
        };
        this.saveData();
    }

    /**
     * Create streak display element
     */
    createDisplay(container) {
        const stats = this.getStats();
        const html = `
            <div class="streak-display">
                <div class="streak-flame ${stats.currentStreak > 0 ? 'active' : ''}">
                    <i class="fas fa-fire"></i>
                </div>
                <div class="streak-info">
                    <div class="streak-count">${stats.currentStreak}</div>
                    <div class="streak-label">Day Streak</div>
                </div>
                <div class="streak-status">
                    ${stats.practicedToday 
                        ? '<span class="badge bg-success"><i class="fas fa-check me-1"></i>Done Today</span>'
                        : '<span class="badge bg-warning text-dark"><i class="fas fa-clock me-1"></i>Practice Today!</span>'
                    }
                </div>
            </div>
            <div class="streak-details">
                <div class="streak-stat">
                    <span class="streak-stat-value">${stats.longestStreak}</span>
                    <span class="streak-stat-label">Best Streak</span>
                </div>
                <div class="streak-stat">
                    <span class="streak-stat-value">${stats.totalDays}</span>
                    <span class="streak-stat-label">Total Days</span>
                </div>
            </div>
        `;
        
        if (typeof container === 'string') {
            container = document.querySelector(container);
        }
        
        if (container) {
            container.innerHTML = html;
        }
        
        return html;
    }

    /**
     * Create weekly heatmap
     */
    createHeatmap(container, weeks = 12) {
        const today = new Date();
        const cells = [];
        
        // Generate cells for past weeks
        for (let w = weeks - 1; w >= 0; w--) {
            for (let d = 0; d < 7; d++) {
                const date = new Date(today);
                date.setDate(date.getDate() - (w * 7 + (6 - d)));
                const dateStr = date.toISOString().split('T')[0];
                
                const practiced = this.wasPracticedOn(dateStr);
                cells.push({
                    date: dateStr,
                    practiced,
                    day: date.getDay()
                });
            }
        }
        
        const html = `
            <div class="streak-heatmap">
                <div class="heatmap-labels">
                    <span>Mon</span>
                    <span>Wed</span>
                    <span>Fri</span>
                </div>
                <div class="heatmap-grid">
                    ${cells.map(cell => `
                        <div class="heatmap-cell ${cell.practiced ? 'practiced' : ''}" 
                             title="${cell.date}"
                             data-date="${cell.date}">
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        if (typeof container === 'string') {
            container = document.querySelector(container);
        }
        
        if (container) {
            container.innerHTML = html;
        }
        
        return html;
    }

    /**
     * Check if practiced on a specific date
     */
    wasPracticedOn(dateStr) {
        const lastPractice = this.data.lastPracticeDate;
        if (!lastPractice) return false;
        
        const targetDate = new Date(dateStr);
        const lastDate = new Date(lastPractice);
        const streakStart = new Date(lastDate);
        streakStart.setDate(streakStart.getDate() - this.data.currentStreak + 1);
        
        // Check if date is within current streak
        if (targetDate >= streakStart && targetDate <= lastDate) {
            return true;
        }
        
        // Check historical streaks
        for (const history of this.data.streakHistory) {
            const histStart = new Date(history.startDate);
            const histEnd = new Date(history.endDate);
            if (targetDate >= histStart && targetDate <= histEnd) {
                return true;
            }
        }
        
        return false;
    }
}

// Initialize global instance
const streakCounter = new StreakCounter({
    onStreakChange: (streak, status) => {
        console.log(`Streak ${status}: ${streak} days`);
    },
    onMilestone: (milestone) => {
        console.log(`Milestone reached: ${milestone} days!`);
    }
});

window.streakCounter = streakCounter;

// CSS for streak display
const streakStyles = document.createElement('style');
streakStyles.textContent = `
    .streak-display {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        background: var(--bg-card);
        border-radius: 12px;
        border: 1px solid var(--border-color);
    }
    
    .streak-flame {
        width: 50px;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.75rem;
        color: var(--text-muted);
        background: var(--bg-tertiary);
        border-radius: 50%;
        transition: all 0.3s ease;
    }
    
    .streak-flame.active {
        color: #ff6b6b;
        background: rgba(255, 107, 107, 0.15);
        animation: flame-pulse 1.5s ease-in-out infinite;
    }
    
    @keyframes flame-pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.1); }
    }
    
    .streak-info {
        flex: 1;
    }
    
    .streak-count {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1;
    }
    
    .streak-label {
        font-size: 0.875rem;
        color: var(--text-muted);
    }
    
    .streak-details {
        display: flex;
        gap: 2rem;
        padding: 1rem;
        margin-top: 0.5rem;
    }
    
    .streak-stat {
        text-align: center;
    }
    
    .streak-stat-value {
        display: block;
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .streak-stat-label {
        font-size: 0.75rem;
        color: var(--text-muted);
    }
    
    .streak-heatmap {
        display: flex;
        gap: 0.5rem;
    }
    
    .heatmap-labels {
        display: flex;
        flex-direction: column;
        justify-content: space-around;
        font-size: 0.625rem;
        color: var(--text-muted);
        padding: 2px 0;
    }
    
    .heatmap-grid {
        display: grid;
        grid-template-columns: repeat(12, 1fr);
        grid-template-rows: repeat(7, 1fr);
        gap: 3px;
        grid-auto-flow: column;
    }
    
    .heatmap-cell {
        width: 12px;
        height: 12px;
        background: var(--bg-tertiary);
        border-radius: 2px;
        transition: background 0.2s ease;
    }
    
    .heatmap-cell.practiced {
        background: var(--accent-success);
    }
    
    .heatmap-cell:hover {
        outline: 2px solid var(--accent-primary);
        outline-offset: 1px;
    }
`;
document.head.appendChild(streakStyles);



