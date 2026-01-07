/**
 * Chart Color Themes for Plotly
 * Consistent chart styling across themes
 */

const ChartThemes = {
    // Theme color palettes
    palettes: {
        light: {
            primary: ['#0d6efd', '#198754', '#ffc107', '#dc3545', '#6f42c1', '#0dcaf0'],
            background: '#ffffff',
            paper: '#f8f9fa',
            gridColor: '#e9ecef',
            textColor: '#212529',
            mutedColor: '#6c757d',
            borderColor: '#dee2e6'
        },
        dark: {
            primary: ['#4dabf7', '#51cf66', '#ffd43b', '#ff6b6b', '#b197fc', '#74c0fc'],
            background: '#212529',
            paper: '#2d3238',
            gridColor: '#495057',
            textColor: '#f8f9fa',
            mutedColor: '#adb5bd',
            borderColor: '#495057'
        },
        ocean: {
            primary: ['#64ffda', '#57c4e5', '#ffd166', '#ff6b6b', '#a78bfa', '#06d6a0'],
            background: '#0a192f',
            paper: '#112240',
            gridColor: '#233554',
            textColor: '#ccd6f6',
            mutedColor: '#8892b0',
            borderColor: '#233554'
        },
        forest: {
            primary: ['#4caf50', '#66bb6a', '#ffb74d', '#ef5350', '#ba68c8', '#4dd0e1'],
            background: '#1b2d1b',
            paper: '#243524',
            gridColor: '#2d4a2d',
            textColor: '#e8f5e9',
            mutedColor: '#a5d6a7',
            borderColor: '#2d4a2d'
        },
        sunset: {
            primary: ['#ff7043', '#ffca28', '#66bb6a', '#ef5350', '#ab47bc', '#4fc3f7'],
            background: '#2d1b2d',
            paper: '#3d2438',
            gridColor: '#4a2c4a',
            textColor: '#fce4ec',
            mutedColor: '#f8bbd9',
            borderColor: '#4a2c4a'
        },
        midnight: {
            primary: ['#ff8906', '#3da9fc', '#9b5de5', '#e53170', '#f9bc60', '#7cc5ff'],
            background: '#0f0e17',
            paper: '#1a1826',
            gridColor: '#2e2b3f',
            textColor: '#fffffe',
            mutedColor: '#a7a9be',
            borderColor: '#2e2b3f'
        }
    },

    // Get current theme
    getCurrentTheme() {
        return document.documentElement.getAttribute('data-theme') || 'light';
    },

    // Get palette for current theme
    getPalette() {
        const theme = this.getCurrentTheme();
        return this.palettes[theme] || this.palettes.light;
    },

    // Get Plotly layout defaults
    getLayoutDefaults() {
        const palette = this.getPalette();
        
        return {
            paper_bgcolor: palette.paper,
            plot_bgcolor: palette.background,
            font: {
                color: palette.textColor,
                family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
            },
            title: {
                font: {
                    size: 16,
                    color: palette.textColor
                }
            },
            xaxis: {
                gridcolor: palette.gridColor,
                linecolor: palette.borderColor,
                tickcolor: palette.mutedColor,
                tickfont: { color: palette.mutedColor },
                title: { font: { color: palette.mutedColor } }
            },
            yaxis: {
                gridcolor: palette.gridColor,
                linecolor: palette.borderColor,
                tickcolor: palette.mutedColor,
                tickfont: { color: palette.mutedColor },
                title: { font: { color: palette.mutedColor } }
            },
            legend: {
                font: { color: palette.textColor },
                bgcolor: 'transparent'
            },
            margin: { t: 40, r: 20, b: 40, l: 50 }
        };
    },

    // Get config defaults
    getConfigDefaults() {
        return {
            responsive: true,
            displayModeBar: false,
            scrollZoom: false
        };
    },

    // Merge with user layout
    mergeLayout(userLayout = {}) {
        const defaults = this.getLayoutDefaults();
        return this.deepMerge(defaults, userLayout);
    },

    // Deep merge helper
    deepMerge(target, source) {
        const result = { ...target };
        for (const key in source) {
            if (source[key] instanceof Object && key in target && target[key] instanceof Object) {
                result[key] = this.deepMerge(target[key], source[key]);
            } else {
                result[key] = source[key];
            }
        }
        return result;
    },

    // Create line chart
    createLineChart(elementId, data, userLayout = {}) {
        const palette = this.getPalette();
        
        const traces = data.map((series, i) => ({
            x: series.x,
            y: series.y,
            name: series.name || `Series ${i + 1}`,
            type: 'scatter',
            mode: series.mode || 'lines+markers',
            line: {
                color: series.color || palette.primary[i % palette.primary.length],
                width: 2,
                shape: 'spline'
            },
            marker: {
                size: 6,
                color: series.color || palette.primary[i % palette.primary.length]
            },
            fill: series.fill || 'none',
            fillcolor: series.fillcolor || 'rgba(0,0,0,0.1)'
        }));

        const layout = this.mergeLayout(userLayout);
        const config = this.getConfigDefaults();

        Plotly.newPlot(elementId, traces, layout, config);
    },

    // Create bar chart
    createBarChart(elementId, data, userLayout = {}) {
        const palette = this.getPalette();
        
        const traces = data.map((series, i) => ({
            x: series.x,
            y: series.y,
            name: series.name || `Series ${i + 1}`,
            type: 'bar',
            marker: {
                color: series.color || palette.primary[i % palette.primary.length],
                line: {
                    width: 0
                }
            }
        }));

        const layout = this.mergeLayout({
            barmode: userLayout.barmode || 'group',
            bargap: 0.3,
            ...userLayout
        });
        const config = this.getConfigDefaults();

        Plotly.newPlot(elementId, traces, layout, config);
    },

    // Create pie chart
    createPieChart(elementId, data, userLayout = {}) {
        const palette = this.getPalette();
        
        const trace = {
            values: data.values,
            labels: data.labels,
            type: 'pie',
            hole: data.donut ? 0.5 : 0,
            marker: {
                colors: data.colors || palette.primary
            },
            textinfo: 'label+percent',
            textfont: {
                color: palette.textColor
            },
            hovertemplate: '%{label}<br>%{value}<br>%{percent}<extra></extra>'
        };

        const layout = this.mergeLayout({
            showlegend: true,
            legend: {
                orientation: 'h',
                yanchor: 'bottom',
                y: -0.2
            },
            ...userLayout
        });
        const config = this.getConfigDefaults();

        Plotly.newPlot(elementId, [trace], layout, config);
    },

    // Create donut chart
    createDonutChart(elementId, data, userLayout = {}) {
        this.createPieChart(elementId, { ...data, donut: true }, userLayout);
    },

    // Create area chart
    createAreaChart(elementId, data, userLayout = {}) {
        const palette = this.getPalette();
        
        const traces = data.map((series, i) => {
            const color = series.color || palette.primary[i % palette.primary.length];
            return {
                x: series.x,
                y: series.y,
                name: series.name || `Series ${i + 1}`,
                type: 'scatter',
                mode: 'lines',
                line: {
                    color: color,
                    width: 2,
                    shape: 'spline'
                },
                fill: 'tozeroy',
                fillcolor: this.hexToRgba(color, 0.2)
            };
        });

        const layout = this.mergeLayout(userLayout);
        const config = this.getConfigDefaults();

        Plotly.newPlot(elementId, traces, layout, config);
    },

    // Create radar chart
    createRadarChart(elementId, data, userLayout = {}) {
        const palette = this.getPalette();
        
        const traces = data.map((series, i) => ({
            type: 'scatterpolar',
            r: series.r,
            theta: series.theta,
            name: series.name || `Series ${i + 1}`,
            fill: 'toself',
            fillcolor: this.hexToRgba(series.color || palette.primary[i], 0.2),
            line: {
                color: series.color || palette.primary[i % palette.primary.length]
            }
        }));

        const layout = this.mergeLayout({
            polar: {
                radialaxis: {
                    visible: true,
                    range: [0, Math.max(...data.flatMap(s => s.r))],
                    gridcolor: palette.gridColor,
                    linecolor: palette.borderColor
                },
                angularaxis: {
                    gridcolor: palette.gridColor,
                    linecolor: palette.borderColor
                },
                bgcolor: palette.paper
            },
            ...userLayout
        });
        const config = this.getConfigDefaults();

        Plotly.newPlot(elementId, traces, layout, config);
    },

    // Create heatmap
    createHeatmap(elementId, data, userLayout = {}) {
        const palette = this.getPalette();
        
        const trace = {
            z: data.z,
            x: data.x,
            y: data.y,
            type: 'heatmap',
            colorscale: data.colorscale || [
                [0, palette.background],
                [1, palette.primary[0]]
            ],
            showscale: data.showscale !== false,
            hovertemplate: '%{x}<br>%{y}<br>Value: %{z}<extra></extra>'
        };

        const layout = this.mergeLayout(userLayout);
        const config = this.getConfigDefaults();

        Plotly.newPlot(elementId, [trace], layout, config);
    },

    // Helper: hex to rgba
    hexToRgba(hex, alpha = 1) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    },

    // Update chart on theme change
    updateAllCharts() {
        document.querySelectorAll('.js-plotly-plot').forEach(chart => {
            const layout = this.getLayoutDefaults();
            Plotly.relayout(chart, layout);
        });
    }
};

// Export globally
window.ChartThemes = ChartThemes;

// Auto-update charts on theme change
const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        if (mutation.attributeName === 'data-theme') {
            ChartThemes.updateAllCharts();
        }
    });
});

observer.observe(document.documentElement, { attributes: true });

