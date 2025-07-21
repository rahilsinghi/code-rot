#!/usr/bin/env python3
"""
Enhanced Web Dashboard for Coding Practice System
Real-time analytics, interactive charts, and modern UI
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit
import plotly.graph_objs as go
import plotly.utils
import pandas as pd

try:
    from recommendation_engine import RecommendationEngine
    from spaced_repetition import SpacedRepetitionManager
    from progress_visualizer import ProgressVisualizer
except ImportError:
    print("⚠️  Some modules not found. Limited functionality.")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

class DashboardManager:
    def __init__(self, db_path="practice_data/problems.db"):
        self.db_path = db_path
        
    def get_dashboard_stats(self, language="python", days=30):
        """Get comprehensive dashboard statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Basic stats
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT pr.problem_id) as completed,
                AVG(pr.time_spent) as avg_time,
                COUNT(CASE WHEN p.difficulty = 'easy' THEN 1 END) as easy,
                COUNT(CASE WHEN p.difficulty = 'medium' THEN 1 END) as medium,
                COUNT(CASE WHEN p.difficulty = 'hard' THEN 1 END) as hard,
                COUNT(DISTINCT p.topic) as unique_topics
            FROM progress pr
            JOIN problems p ON pr.problem_id = p.id
            WHERE pr.status = 'completed' AND pr.language = ?
            AND DATE(pr.completed_at) >= DATE('now', '-{} days')
        '''.format(days), (language,))
        
        basic_stats = cursor.fetchone()
        
        # Daily progress for chart
        cursor.execute('''
            SELECT DATE(pr.completed_at) as date, COUNT(*) as count
            FROM progress pr
            WHERE pr.status = 'completed' AND pr.language = ?
            AND DATE(pr.completed_at) >= DATE('now', '-{} days')
            GROUP BY DATE(pr.completed_at)
            ORDER BY date
        '''.format(days), (language,))
        
        daily_progress = cursor.fetchall()
        
        # Topic distribution
        cursor.execute('''
            SELECT p.topic, COUNT(*) as count
            FROM progress pr
            JOIN problems p ON pr.problem_id = p.id
            WHERE pr.status = 'completed' AND pr.language = ?
            GROUP BY p.topic
            ORDER BY count DESC
        ''', (language,))
        
        topic_stats = cursor.fetchall()
        
        # Recent activity
        cursor.execute('''
            SELECT p.title, p.difficulty, p.topic, pr.completed_at, pr.time_spent
            FROM progress pr
            JOIN problems p ON pr.problem_id = p.id
            WHERE pr.status = 'completed' AND pr.language = ?
            ORDER BY pr.completed_at DESC
            LIMIT 10
        ''', (language,))
        
        recent_activity = cursor.fetchall()
        
        conn.close()
        
        return {
            'basic_stats': basic_stats,
            'daily_progress': daily_progress,
            'topic_stats': topic_stats,
            'recent_activity': recent_activity
        }
    
    def get_real_time_recommendations(self, language="python", count=5):
        """Get real-time problem recommendations"""
        try:
            engine = RecommendationEngine(self.db_path)
            return engine.get_personalized_recommendations(language, count)
        except:
            return []
    
    def get_review_dashboard(self, language="python"):
        """Get spaced repetition dashboard data"""
        try:
            sr_manager = SpacedRepetitionManager(self.db_path)
            stats = sr_manager.get_review_statistics(language, 30)
            due_reviews = sr_manager.get_due_reviews(language, 10)
            return {
                'stats': stats,
                'due_reviews': due_reviews
            }
        except:
            return {'stats': {}, 'due_reviews': []}

dashboard_manager = DashboardManager()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/stats')
def api_stats():
    """API endpoint for dashboard statistics"""
    language = request.args.get('language', 'python')
    days = int(request.args.get('days', 30))
    
    stats = dashboard_manager.get_dashboard_stats(language, days)
    return jsonify(stats)

@app.route('/api/recommendations')
def api_recommendations():
    """API endpoint for problem recommendations"""
    language = request.args.get('language', 'python')
    count = int(request.args.get('count', 5))
    
    recommendations = dashboard_manager.get_real_time_recommendations(language, count)
    return jsonify(recommendations)

@app.route('/api/reviews')
def api_reviews():
    """API endpoint for spaced repetition data"""
    language = request.args.get('language', 'python')
    
    review_data = dashboard_manager.get_review_dashboard(language)
    return jsonify(review_data)

@app.route('/api/progress-chart')
def api_progress_chart():
    """Generate interactive progress chart"""
    language = request.args.get('language', 'python')
    days = int(request.args.get('days', 30))
    
    stats = dashboard_manager.get_dashboard_stats(language, days)
    daily_data = stats['daily_progress']
    
    if not daily_data:
        return jsonify({'data': [], 'layout': {}})
    
    dates = [row[0] for row in daily_data]
    counts = [row[1] for row in daily_data]
    
    # Create Plotly chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=counts,
        mode='lines+markers',
        name='Problems Solved',
        line=dict(color='#4CAF50', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='Daily Problem Solving Progress',
        xaxis_title='Date',
        yaxis_title='Problems Solved',
        template='plotly_white',
        height=400
    )
    
    return jsonify(json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig)))

@app.route('/api/topic-chart')
def api_topic_chart():
    """Generate topic distribution chart"""
    language = request.args.get('language', 'python')
    days = int(request.args.get('days', 30))
    
    stats = dashboard_manager.get_dashboard_stats(language, days)
    topic_data = stats['topic_stats']
    
    if not topic_data:
        return jsonify({'data': [], 'layout': {}})
    
    topics = [row[0] for row in topic_data]
    counts = [row[1] for row in topic_data]
    
    # Create Plotly pie chart
    fig = go.Figure(data=[go.Pie(
        labels=topics,
        values=counts,
        hole=0.4,
        textinfo='label+percent',
        textposition='outside'
    )])
    
    fig.update_layout(
        title='Problems Solved by Topic',
        template='plotly_white',
        height=400
    )
    
    return jsonify(json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig)))

@socketio.on('connect')
def handle_connect():
    """Handle websocket connection"""
    print('Client connected')
    emit('status', {'msg': 'Connected to practice dashboard'})

@socketio.on('request_live_stats')
def handle_live_stats(data):
    """Handle real-time stats request"""
    language = data.get('language', 'python')
    days = data.get('days', 30)
    
    stats = dashboard_manager.get_dashboard_stats(language, days)
    emit('live_stats', stats)

@socketio.on('request_recommendations')
def handle_recommendations(data):
    """Handle real-time recommendations request"""
    language = data.get('language', 'python')
    count = data.get('count', 5)
    
    recommendations = dashboard_manager.get_real_time_recommendations(language, count)
    emit('recommendations', recommendations)

def create_templates_directory():
    """Create templates directory with dashboard HTML"""
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    dashboard_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coding Practice Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .dashboard-card { transition: transform 0.2s; }
        .dashboard-card:hover { transform: translateY(-2px); }
        .metric-value { font-size: 2rem; font-weight: bold; }
        .chart-container { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; }
        .recommendation-card { border-left: 4px solid #007bff; }
        .activity-item { padding: 10px; border-bottom: 1px solid #eee; }
        .nav-pills .nav-link.active { background-color: #007bff; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <!-- Header -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="d-flex justify-content-between align-items-center py-3">
                    <h1><i class="fas fa-code me-2"></i>Coding Practice Dashboard</h1>
                    <div class="d-flex align-items-center">
                        <select id="languageSelect" class="form-select me-3" style="width: 150px;">
                            <option value="python">Python</option>
                            <option value="javascript">JavaScript</option>
                            <option value="typescript">TypeScript</option>
                            <option value="react">React</option>
                        </select>
                        <span class="badge bg-success" id="connectionStatus">Connected</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Metrics Cards -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card dashboard-card h-100">
                    <div class="card-body text-center">
                        <i class="fas fa-check-circle fa-2x text-success mb-2"></i>
                        <h5>Problems Solved</h5>
                        <div class="metric-value text-success" id="totalSolved">-</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card dashboard-card h-100">
                    <div class="card-body text-center">
                        <i class="fas fa-clock fa-2x text-info mb-2"></i>
                        <h5>Avg Time</h5>
                        <div class="metric-value text-info" id="avgTime">-</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card dashboard-card h-100">
                    <div class="card-body text-center">
                        <i class="fas fa-brain fa-2x text-warning mb-2"></i>
                        <h5>Due Reviews</h5>
                        <div class="metric-value text-warning" id="dueReviews">-</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card dashboard-card h-100">
                    <div class="card-body text-center">
                        <i class="fas fa-trophy fa-2x text-danger mb-2"></i>
                        <h5>Topics Covered</h5>
                        <div class="metric-value text-danger" id="topicsCovered">-</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts Row -->
        <div class="row mb-4">
            <div class="col-lg-8">
                <div class="chart-container">
                    <div id="progressChart"></div>
                </div>
            </div>
            <div class="col-lg-4">
                <div class="chart-container">
                    <div id="topicChart"></div>
                </div>
            </div>
        </div>

        <!-- Content Tabs -->
        <div class="row">
            <div class="col-12">
                <ul class="nav nav-pills mb-3" id="dashboardTabs">
                    <li class="nav-item">
                        <a class="nav-link active" data-bs-toggle="pill" href="#recommendations">
                            <i class="fas fa-lightbulb me-2"></i>Recommendations
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" data-bs-toggle="pill" href="#reviews">
                            <i class="fas fa-redo me-2"></i>Reviews
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" data-bs-toggle="pill" href="#activity">
                            <i class="fas fa-history me-2"></i>Recent Activity
                        </a>
                    </li>
                </ul>

                <div class="tab-content">
                    <!-- Recommendations Tab -->
                    <div class="tab-pane fade show active" id="recommendations">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-robot me-2"></i>AI-Powered Recommendations</h5>
                            </div>
                            <div class="card-body" id="recommendationsContainer">
                                <div class="text-center">
                                    <div class="spinner-border" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Reviews Tab -->
                    <div class="tab-pane fade" id="reviews">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-brain me-2"></i>Spaced Repetition Reviews</h5>
                            </div>
                            <div class="card-body" id="reviewsContainer">
                                <div class="text-center">
                                    <div class="spinner-border" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Activity Tab -->
                    <div class="tab-pane fade" id="activity">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-history me-2"></i>Recent Activity</h5>
                            </div>
                            <div class="card-body" id="activityContainer">
                                <div class="text-center">
                                    <div class="spinner-border" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // WebSocket connection
        const socket = io();
        let currentLanguage = 'python';

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            loadDashboard();
            setupEventListeners();
        });

        function setupEventListeners() {
            // Language selector
            document.getElementById('languageSelect').addEventListener('change', function(e) {
                currentLanguage = e.target.value;
                loadDashboard();
            });

            // Tab switches
            document.querySelectorAll('[data-bs-toggle="pill"]').forEach(tab => {
                tab.addEventListener('shown.bs.tab', function(e) {
                    if (e.target.getAttribute('href') === '#recommendations') {
                        loadRecommendations();
                    } else if (e.target.getAttribute('href') === '#reviews') {
                        loadReviews();
                    }
                });
            });
        }

        function loadDashboard() {
            loadStats();
            loadCharts();
            loadRecommendations();
        }

        function loadStats() {
            fetch(`/api/stats?language=${currentLanguage}&days=30`)
                .then(response => response.json())
                .then(data => {
                    const stats = data.basic_stats;
                    if (stats) {
                        document.getElementById('totalSolved').textContent = stats[0] || 0;
                        document.getElementById('avgTime').textContent = stats[1] ? `${stats[1].toFixed(1)}m` : 'N/A';
                        document.getElementById('topicsCovered').textContent = stats[5] || 0;
                    }
                    
                    // Load recent activity
                    loadRecentActivity(data.recent_activity);
                })
                .catch(error => console.error('Error loading stats:', error));
        }

        function loadCharts() {
            // Progress chart
            fetch(`/api/progress-chart?language=${currentLanguage}&days=30`)
                .then(response => response.json())
                .then(fig => {
                    if (fig.data && fig.layout) {
                        Plotly.newPlot('progressChart', fig.data, fig.layout, {responsive: true});
                    }
                })
                .catch(error => console.error('Error loading progress chart:', error));

            // Topic chart
            fetch(`/api/topic-chart?language=${currentLanguage}&days=30`)
                .then(response => response.json())
                .then(fig => {
                    if (fig.data && fig.layout) {
                        Plotly.newPlot('topicChart', fig.data, fig.layout, {responsive: true});
                    }
                })
                .catch(error => console.error('Error loading topic chart:', error));
        }

        function loadRecommendations() {
            fetch(`/api/recommendations?language=${currentLanguage}&count=5`)
                .then(response => response.json())
                .then(recommendations => {
                    const container = document.getElementById('recommendationsContainer');
                    
                    if (!recommendations || recommendations.length === 0) {
                        container.innerHTML = '<p class="text-muted">No recommendations available. Solve a few problems to get personalized suggestions!</p>';
                        return;
                    }

                    const html = recommendations.map((rec, index) => `
                        <div class="card recommendation-card mb-3">
                            <div class="card-body">
                                <div class="d-flex justify-content-between align-items-start">
                                    <div>
                                        <h6 class="card-title">${index + 1}. ${rec.title}</h6>
                                        <p class="card-text">
                                            <span class="badge bg-${getDifficultyColor(rec.difficulty)}">${rec.difficulty}</span>
                                            <span class="badge bg-secondary ms-1">${rec.topic}</span>
                                            <span class="badge bg-info ms-1">${rec.platform}</span>
                                        </p>
                                        ${rec.recommendation_reasons ? `<p class="text-muted small">💡 ${rec.recommendation_reasons.join(', ')}</p>` : ''}
                                    </div>
                                    <div class="text-end">
                                        <small class="text-muted">Score: ${(rec.recommendation_score || 0).toFixed(2)}</small>
                                        ${rec.url ? `<br><a href="${rec.url}" target="_blank" class="btn btn-sm btn-outline-primary mt-1">Open</a>` : ''}
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('');
                    
                    container.innerHTML = html;
                })
                .catch(error => {
                    console.error('Error loading recommendations:', error);
                    document.getElementById('recommendationsContainer').innerHTML = '<p class="text-danger">Error loading recommendations</p>';
                });
        }

        function loadReviews() {
            fetch(`/api/reviews?language=${currentLanguage}`)
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('reviewsContainer');
                    const dueReviews = data.due_reviews || [];
                    const stats = data.stats || {};
                    
                    // Update due reviews counter
                    document.getElementById('dueReviews').textContent = stats.due_count || 0;
                    
                    if (dueReviews.length === 0) {
                        container.innerHTML = '<p class="text-muted">🎉 No reviews due! Great job staying on top of your studies.</p>';
                        return;
                    }

                    const html = `
                        <div class="mb-3">
                            <h6>Review Statistics</h6>
                            <div class="row">
                                <div class="col-md-3">
                                    <div class="text-center">
                                        <div class="h4 text-danger">${stats.due_count || 0}</div>
                                        <small>Due Now</small>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="text-center">
                                        <div class="h4 text-warning">${stats.upcoming_count || 0}</div>
                                        <small>Next 7 Days</small>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="text-center">
                                        <div class="h4 text-info">${stats.total_in_system || 0}</div>
                                        <small>In System</small>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="text-center">
                                        <div class="h4 text-success">${(stats.avg_ease_factor || 0).toFixed(1)}</div>
                                        <small>Avg Ease</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <hr>
                        ${dueReviews.map(review => `
                            <div class="activity-item">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <strong>${review.title}</strong>
                                        <div>
                                            <span class="badge bg-${getDifficultyColor(review.difficulty)}">${review.difficulty}</span>
                                            <span class="badge bg-secondary ms-1">${review.topic}</span>
                                            <small class="text-muted ms-2">Review #${(review.review_count || 0) + 1}</small>
                                        </div>
                                    </div>
                                    <div class="text-end">
                                        <small class="text-danger">${review.days_overdue} days overdue</small>
                                        <br><small class="text-muted">Ease: ${(review.ease_factor || 0).toFixed(2)}</small>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    `;
                    
                    container.innerHTML = html;
                })
                .catch(error => {
                    console.error('Error loading reviews:', error);
                    document.getElementById('reviewsContainer').innerHTML = '<p class="text-danger">Error loading review data</p>';
                });
        }

        function loadRecentActivity(activities) {
            const container = document.getElementById('activityContainer');
            
            if (!activities || activities.length === 0) {
                container.innerHTML = '<p class="text-muted">No recent activity to display.</p>';
                return;
            }

            const html = activities.map(activity => `
                <div class="activity-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${activity[0]}</strong>
                            <div>
                                <span class="badge bg-${getDifficultyColor(activity[1])}">${activity[1]}</span>
                                <span class="badge bg-secondary ms-1">${activity[2]}</span>
                            </div>
                        </div>
                        <div class="text-end">
                            <small class="text-muted">${new Date(activity[3]).toLocaleDateString()}</small>
                            ${activity[4] ? `<br><small>${activity[4]} min</small>` : ''}
                        </div>
                    </div>
                </div>
            `).join('');
            
            container.innerHTML = html;
        }

        function getDifficultyColor(difficulty) {
            const colors = {
                'easy': 'success',
                'medium': 'warning',
                'hard': 'danger'
            };
            return colors[difficulty] || 'secondary';
        }

        // WebSocket handlers
        socket.on('connect', function() {
            document.getElementById('connectionStatus').textContent = 'Connected';
            document.getElementById('connectionStatus').className = 'badge bg-success';
        });

        socket.on('disconnect', function() {
            document.getElementById('connectionStatus').textContent = 'Disconnected';
            document.getElementById('connectionStatus').className = 'badge bg-danger';
        });

        // Auto-refresh every 5 minutes
        setInterval(loadDashboard, 5 * 60 * 1000);
    </script>
</body>
</html>
    '''
    
    (templates_dir / 'dashboard.html').write_text(dashboard_html)

if __name__ == '__main__':
    create_templates_directory()
    print("🌐 Starting Enhanced Web Dashboard...")
    print("📊 Dashboard available at: http://localhost:5000")
    print("🚀 Features: Real-time analytics, AI recommendations, spaced repetition tracking")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True) 