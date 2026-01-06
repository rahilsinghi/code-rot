/**
 * Theme Toggle System
 * Handles dark/light mode switching with localStorage persistence
 */

class ThemeManager {
    constructor() {
        this.theme = this.getSavedTheme() || this.getSystemPreference();
        this.init();
    }

    getSavedTheme() {
        return localStorage.getItem('theme');
    }

    getSystemPreference() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    init() {
        // Apply saved theme immediately
        this.applyTheme(this.theme);

        // Listen for system preference changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                this.applyTheme(e.matches ? 'dark' : 'light');
            }
        });

        // Initialize toggle buttons after DOM loaded
        document.addEventListener('DOMContentLoaded', () => {
            this.initToggleButtons();
            this.updateCharts();
        });
    }

    applyTheme(theme) {
        this.theme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);

        // Update any toggle buttons
        this.updateToggleButtons();

        // Update chart colors if Plotly is available
        this.updateCharts();

        // Dispatch event for other components
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
    }

    toggle() {
        const newTheme = this.theme === 'dark' ? 'light' : 'dark';
        this.applyTheme(newTheme);
        
        // Show notification
        if (window.showToast) {
            window.showToast(`Switched to ${newTheme} mode`, 'info');
        }
    }

    initToggleButtons() {
        // Add click handlers to all theme toggle elements
        document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
            btn.addEventListener('click', () => this.toggle());
        });

        // Create navbar toggle if it doesn't exist
        this.createNavbarToggle();
    }

    createNavbarToggle() {
        const navbar = document.querySelector('.navbar-nav');
        if (!navbar || document.getElementById('theme-toggle-nav')) return;

        const toggleItem = document.createElement('li');
        toggleItem.className = 'nav-item ms-2';
        toggleItem.innerHTML = `
            <div class="theme-toggle" id="theme-toggle-nav" data-theme-toggle title="Toggle dark/light mode">
                <div class="theme-toggle-slider"></div>
            </div>
        `;
        
        navbar.appendChild(toggleItem);
        toggleItem.querySelector('[data-theme-toggle]').addEventListener('click', () => this.toggle());
    }

    updateToggleButtons() {
        document.querySelectorAll('.theme-toggle').forEach(toggle => {
            toggle.setAttribute('aria-checked', this.theme === 'dark');
        });
    }

    updateCharts() {
        if (typeof Plotly === 'undefined') return;

        const isDark = this.theme === 'dark';
        const chartLayout = {
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: {
                color: isDark ? '#adb5bd' : '#6c757d'
            },
            xaxis: {
                gridcolor: isDark ? '#495057' : '#e9ecef',
                linecolor: isDark ? '#495057' : '#e9ecef'
            },
            yaxis: {
                gridcolor: isDark ? '#495057' : '#e9ecef',
                linecolor: isDark ? '#495057' : '#e9ecef'
            }
        };

        // Update all Plotly charts
        document.querySelectorAll('[id*="-chart"]').forEach(chart => {
            if (chart.data) {
                Plotly.relayout(chart, chartLayout);
            }
        });
    }
}

// Initialize theme manager
const themeManager = new ThemeManager();

// Global function for toggle buttons
window.toggleTheme = () => themeManager.toggle();
window.themeManager = themeManager;

