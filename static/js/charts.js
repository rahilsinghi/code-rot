/**
 * Enhanced Chart System
 * Beautiful, interactive charts with theme support
 */

class ChartManager {
    constructor() {
        this.charts = {};
        this.isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        
        // Listen for theme changes
        window.addEventListener('themeChanged', (e) => {
            this.isDark = e.detail.theme === 'dark';
            this.updateAllCharts();
        });
    }

    getColors() {
        return {
            primary: this.isDark ? '#4dabf7' : '#0d6efd',
            success: this.isDark ? '#51cf66' : '#198754',
            warning: this.isDark ? '#ffd43b' : '#ffc107',
            danger: this.isDark ? '#ff6b6b' : '#dc3545',
            info: this.isDark ? '#74c0fc' : '#0dcaf0',
            purple: this.isDark ? '#845ef7' : '#6f42c1',
            pink: this.isDark ? '#f783ac' : '#d63384',
            text: this.isDark ? '#adb5bd' : '#6c757d',
            grid: this.isDark ? '#495057' : '#e9ecef',
            background: 'transparent'
        };
    }

    getBaseLayout() {
        const colors = this.getColors();
        return {
            paper_bgcolor: colors.background,
            plot_bgcolor: colors.background,
            font: {
                family: 'system-ui, -apple-system, sans-serif',
                color: colors.text,
                size: 12
            },
            margin: { t: 30, r: 20, b: 40, l: 50 },
            xaxis: {
                gridcolor: colors.grid,
                linecolor: colors.grid,
                zerolinecolor: colors.grid
            },
            yaxis: {
                gridcolor: colors.grid,
                linecolor: colors.grid,
                zerolinecolor: colors.grid
            },
            showlegend: true,
            legend: {
                bgcolor: 'transparent',
                font: { color: colors.text }
            }
        };
    }

    // Progress Ring Chart
    createProgressRing(elementId, value, maxValue = 100, label = '') {
        const colors = this.getColors();
        const percentage = (value / maxValue) * 100;
        
        const data = [{
            type: 'pie',
            hole: 0.75,
            values: [percentage, 100 - percentage],
            marker: {
                colors: [colors.primary, colors.grid]
            },
            textinfo: 'none',
            hoverinfo: 'none',
            rotation: -90,
            direction: 'clockwise'
        }];

        const layout = {
            ...this.getBaseLayout(),
            margin: { t: 0, r: 0, b: 0, l: 0 },
            showlegend: false,
            annotations: [{
                text: `<b>${Math.round(percentage)}%</b><br><span style="font-size:11px">${label}</span>`,
                showarrow: false,
                font: { size: 20, color: colors.text }
            }]
        };

        Plotly.newPlot(elementId, data, layout, { responsive: true, displayModeBar: false });
        this.charts[elementId] = { type: 'progressRing', value, maxValue, label };
    }

    // Line Chart with gradient fill
    createLineChart(elementId, data, options = {}) {
        const colors = this.getColors();
        const { title = '', xLabel = '', yLabel = '' } = options;

        const traces = data.map((series, idx) => ({
            x: series.x,
            y: series.y,
            name: series.name || `Series ${idx + 1}`,
            type: 'scatter',
            mode: 'lines+markers',
            line: {
                color: [colors.primary, colors.success, colors.warning, colors.purple][idx % 4],
                width: 3,
                shape: 'spline'
            },
            marker: {
                size: 8,
                color: [colors.primary, colors.success, colors.warning, colors.purple][idx % 4]
            },
            fill: 'tozeroy',
            fillcolor: `${[colors.primary, colors.success, colors.warning, colors.purple][idx % 4]}20`
        }));

        const layout = {
            ...this.getBaseLayout(),
            title: { text: title, font: { size: 16 } },
            xaxis: { ...this.getBaseLayout().xaxis, title: xLabel },
            yaxis: { ...this.getBaseLayout().yaxis, title: yLabel }
        };

        Plotly.newPlot(elementId, traces, layout, { responsive: true, displayModeBar: false });
        this.charts[elementId] = { type: 'line', data, options };
    }

    // Bar Chart with rounded corners effect
    createBarChart(elementId, data, options = {}) {
        const colors = this.getColors();
        const { title = '', horizontal = false } = options;

        const traces = [{
            x: horizontal ? data.values : data.labels,
            y: horizontal ? data.labels : data.values,
            type: 'bar',
            orientation: horizontal ? 'h' : 'v',
            marker: {
                color: data.values.map((_, i) => 
                    [colors.primary, colors.success, colors.warning, colors.danger, colors.info, colors.purple][i % 6]
                ),
                line: { width: 0 }
            },
            text: data.values.map(v => v.toString()),
            textposition: 'auto',
            hovertemplate: '%{x}: %{y}<extra></extra>'
        }];

        const layout = {
            ...this.getBaseLayout(),
            title: { text: title, font: { size: 16 } },
            bargap: 0.3
        };

        Plotly.newPlot(elementId, traces, layout, { responsive: true, displayModeBar: false });
        this.charts[elementId] = { type: 'bar', data, options };
    }

    // Donut/Pie Chart
    createDonutChart(elementId, data, options = {}) {
        const colors = this.getColors();
        const { title = '', showLabels = true } = options;

        const colorPalette = [
            colors.primary, colors.success, colors.warning, 
            colors.danger, colors.info, colors.purple, colors.pink
        ];

        const traces = [{
            values: data.values,
            labels: data.labels,
            type: 'pie',
            hole: 0.5,
            marker: {
                colors: colorPalette.slice(0, data.values.length),
                line: { color: this.isDark ? '#2d3238' : '#ffffff', width: 2 }
            },
            textinfo: showLabels ? 'percent+label' : 'percent',
            textposition: 'outside',
            automargin: true,
            hovertemplate: '%{label}: %{value} (%{percent})<extra></extra>'
        }];

        const layout = {
            ...this.getBaseLayout(),
            title: { text: title, font: { size: 16 } },
            showlegend: true,
            legend: { orientation: 'h', y: -0.1 }
        };

        Plotly.newPlot(elementId, traces, layout, { responsive: true, displayModeBar: false });
        this.charts[elementId] = { type: 'donut', data, options };
    }

    // Heatmap for activity calendar
    createHeatmap(elementId, data, options = {}) {
        const colors = this.getColors();
        const { title = '' } = options;

        const traces = [{
            z: data.values,
            x: data.x,
            y: data.y,
            type: 'heatmap',
            colorscale: [
                [0, colors.grid],
                [0.25, `${colors.success}40`],
                [0.5, `${colors.success}80`],
                [0.75, colors.success],
                [1, colors.primary]
            ],
            showscale: false,
            hovertemplate: '%{x}<br>%{y}<br>Value: %{z}<extra></extra>'
        }];

        const layout = {
            ...this.getBaseLayout(),
            title: { text: title, font: { size: 16 } }
        };

        Plotly.newPlot(elementId, traces, layout, { responsive: true, displayModeBar: false });
        this.charts[elementId] = { type: 'heatmap', data, options };
    }

    // Gauge Chart for metrics
    createGaugeChart(elementId, value, options = {}) {
        const colors = this.getColors();
        const { title = '', max = 100, suffix = '%' } = options;

        const traces = [{
            type: 'indicator',
            mode: 'gauge+number',
            value: value,
            number: { suffix: suffix, font: { color: colors.text, size: 24 } },
            gauge: {
                axis: { 
                    range: [0, max], 
                    tickcolor: colors.text,
                    tickfont: { color: colors.text }
                },
                bar: { color: colors.primary },
                bgcolor: colors.grid,
                borderwidth: 0,
                steps: [
                    { range: [0, max * 0.3], color: `${colors.danger}40` },
                    { range: [max * 0.3, max * 0.7], color: `${colors.warning}40` },
                    { range: [max * 0.7, max], color: `${colors.success}40` }
                ]
            }
        }];

        const layout = {
            ...this.getBaseLayout(),
            title: { text: title, font: { size: 14 } },
            margin: { t: 40, r: 20, b: 20, l: 20 }
        };

        Plotly.newPlot(elementId, traces, layout, { responsive: true, displayModeBar: false });
        this.charts[elementId] = { type: 'gauge', value, options };
    }

    // Update all charts when theme changes
    updateAllCharts() {
        Object.keys(this.charts).forEach(elementId => {
            const chart = this.charts[elementId];
            const element = document.getElementById(elementId);
            if (!element) return;

            switch (chart.type) {
                case 'progressRing':
                    this.createProgressRing(elementId, chart.value, chart.maxValue, chart.label);
                    break;
                case 'line':
                    this.createLineChart(elementId, chart.data, chart.options);
                    break;
                case 'bar':
                    this.createBarChart(elementId, chart.data, chart.options);
                    break;
                case 'donut':
                    this.createDonutChart(elementId, chart.data, chart.options);
                    break;
                case 'heatmap':
                    this.createHeatmap(elementId, chart.data, chart.options);
                    break;
                case 'gauge':
                    this.createGaugeChart(elementId, chart.value, chart.options);
                    break;
            }
        });
    }
}

// Initialize chart manager
window.chartManager = new ChartManager();




