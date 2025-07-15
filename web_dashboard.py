#!/usr/bin/env python3
"""
Advanced Web Dashboard for Coding Practice System
Provides real-time visualization, progress tracking, and session management
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import io
import base64
from typing import Dict, List, Optional

# Import existing modules
try:
    from practice import PracticeManager
    from progress_visualizer import ProgressVisualizer
    from recommendation_engine import RecommendationEngine
    from spaced_repetition import SpacedRepetitionManager
    from database_manager import DatabaseManager
    from performance_monitor import PerformanceMonitor
    from cache_manager import CacheManager
    from error_handler import ErrorHandler
except ImportError as e:
    print(f"⚠️  Some modules not available: {e}")

# Try to import plotting libraries
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd
    import numpy as np
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your-secret-key-here'

class WebDashboard:
    """Main web dashboard class"""
    
    def __init__(self):
        self.practice_manager = PracticeManager()
        self.error_handler = ErrorHandler()
        self.cache_manager = CacheManager()
        self.performance_monitor = PerformanceMonitor()
        
        # Initialize optional modules
        self.progress_visualizer = None
        self.recommendation_engine = None
        self.spaced_repetition = None
        
        try:
            self.progress_visualizer = ProgressVisualizer()
            self.recommendation_engine = RecommendationEngine()
            self.spaced_repetition = SpacedRepetitionManager()
        except Exception as e:
            self.error_handler.handle_error(e, "dashboard_initialization")
    
    def get_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data"""
        try:
            # Use caching for performance
            cache_key = "dashboard_data"
            cached_data = self.cache_manager.get(cache_key)
            if cached_data:
                return cached_data
            
            # Get basic statistics
            stats = self._get_basic_stats()
            
            # Get recent activity
            recent_activity = self._get_recent_activity()
            
            # Get topic distribution
            topic_distribution = self._get_topic_distribution()
            
            # Get difficulty distribution
            difficulty_distribution = self._get_difficulty_distribution()
            
            # Get learning velocity
            learning_velocity = self._get_learning_velocity()
            
            # Get recommendations
            recommendations = self._get_recommendations()
            
            # Get due reviews
            due_reviews = self._get_due_reviews()
            
            # Get system health
            system_health = self.performance_monitor.get_system_health()
            
            dashboard_data = {
                'stats': stats,
                'recent_activity': recent_activity,
                'topic_distribution': topic_distribution,
                'difficulty_distribution': difficulty_distribution,
                'learning_velocity': learning_velocity,
                'recommendations': recommendations,
                'due_reviews': due_reviews,
                'system_health': system_health,
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache the data
            self.cache_manager.set(cache_key, dashboard_data, ttl=300)  # 5 minutes
            
            return dashboard_data
            
        except Exception as e:
            self.error_handler.handle_error(e, "get_dashboard_data")
            return {'error': str(e)}
    
    def _get_basic_stats(self) -> Dict:
        """Get basic statistics"""
        try:
            conn = sqlite3.connect(self.practice_manager.db_path)
            cursor = conn.cursor()
            
            # Total problems
            cursor.execute("SELECT COUNT(*) FROM problems")
            total_problems = cursor.fetchone()[0]
            
            # Completed problems
            cursor.execute("SELECT COUNT(DISTINCT problem_id) FROM progress WHERE status = 'completed'")
            completed_problems = cursor.fetchone()[0]
            
            # Current streak
            cursor.execute('''
                SELECT COUNT(*) FROM (
                    SELECT DATE(completed_at) as date
                    FROM progress 
                    WHERE status = 'completed'
                    GROUP BY DATE(completed_at)
                    ORDER BY date DESC
                    LIMIT 30
                ) WHERE date >= DATE('now', '-30 days')
            ''')
            current_streak = cursor.fetchone()[0]
            
            # Average time per problem
            cursor.execute("SELECT AVG(time_spent) FROM progress WHERE status = 'completed' AND time_spent > 0")
            avg_time = cursor.fetchone()[0] or 0
            
            # Success rate (completed vs attempted)
            cursor.execute("SELECT COUNT(*) FROM progress")
            total_attempts = cursor.fetchone()[0]
            success_rate = (completed_problems / total_attempts * 100) if total_attempts > 0 else 0
            
            conn.close()
            
            return {
                'total_problems': total_problems,
                'completed_problems': completed_problems,
                'completion_rate': (completed_problems / total_problems * 100) if total_problems > 0 else 0,
                'current_streak': current_streak,
                'avg_time_minutes': round(avg_time, 1),
                'success_rate': round(success_rate, 1)
            }
            
        except Exception as e:
            self.error_handler.handle_error(e, "_get_basic_stats")
            return {}
    
    def _get_recent_activity(self) -> List[Dict]:
        """Get recent activity"""
        try:
            conn = sqlite3.connect(self.practice_manager.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT p.title, p.difficulty, p.topic, pr.completed_at, pr.time_spent, pr.notes
                FROM progress pr
                JOIN problems p ON pr.problem_id = p.id
                WHERE pr.status = 'completed'
                ORDER BY pr.completed_at DESC
                LIMIT 10
            ''')
            
            activities = []
            for row in cursor.fetchall():
                activities.append({
                    'title': row[0],
                    'difficulty': row[1],
                    'topic': row[2],
                    'completed_at': row[3],
                    'time_spent': row[4],
                    'notes': row[5]
                })
            
            conn.close()
            return activities
            
        except Exception as e:
            self.error_handler.handle_error(e, "_get_recent_activity")
            return []
    
    def _get_topic_distribution(self) -> Dict:
        """Get topic distribution"""
        try:
            conn = sqlite3.connect(self.practice_manager.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT p.topic, COUNT(*) as count
                FROM progress pr
                JOIN problems p ON pr.problem_id = p.id
                WHERE pr.status = 'completed'
                GROUP BY p.topic
                ORDER BY count DESC
            ''')
            
            distribution = {}
            for row in cursor.fetchall():
                distribution[row[0]] = row[1]
            
            conn.close()
            return distribution
            
        except Exception as e:
            self.error_handler.handle_error(e, "_get_topic_distribution")
            return {}
    
    def _get_difficulty_distribution(self) -> Dict:
        """Get difficulty distribution"""
        try:
            conn = sqlite3.connect(self.practice_manager.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT p.difficulty, COUNT(*) as count
                FROM progress pr
                JOIN problems p ON pr.problem_id = p.id
                WHERE pr.status = 'completed'
                GROUP BY p.difficulty
            ''')
            
            distribution = {}
            for row in cursor.fetchall():
                distribution[row[0]] = row[1]
            
            conn.close()
            return distribution
            
        except Exception as e:
            self.error_handler.handle_error(e, "_get_difficulty_distribution")
            return {}
    
    def _get_learning_velocity(self) -> List[Dict]:
        """Get learning velocity over time"""
        try:
            conn = sqlite3.connect(self.practice_manager.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT DATE(completed_at) as date, COUNT(*) as count
                FROM progress
                WHERE status = 'completed'
                AND DATE(completed_at) >= DATE('now', '-30 days')
                GROUP BY DATE(completed_at)
                ORDER BY date
            ''')
            
            velocity = []
            for row in cursor.fetchall():
                velocity.append({
                    'date': row[0],
                    'count': row[1]
                })
            
            conn.close()
            return velocity
            
        except Exception as e:
            self.error_handler.handle_error(e, "_get_learning_velocity")
            return []
    
    def _get_recommendations(self) -> List[Dict]:
        """Get problem recommendations"""
        try:
            if not self.recommendation_engine:
                return []
            
            recommendations = self.recommendation_engine.get_personalized_recommendations(
                language="python", count=5
            )
            
            return recommendations
            
        except Exception as e:
            self.error_handler.handle_error(e, "_get_recommendations")
            return []
    
    def _get_due_reviews(self) -> List[Dict]:
        """Get problems due for review"""
        try:
            if not self.spaced_repetition:
                return []
            
            due_reviews = self.spaced_repetition.get_due_reviews(limit=5)
            return due_reviews
            
        except Exception as e:
            self.error_handler.handle_error(e, "_get_due_reviews")
            return []
    
    def generate_chart(self, chart_type: str, data: Dict) -> str:
        """Generate chart and return base64 encoded image"""
        if not PLOTTING_AVAILABLE:
            return ""
        
        try:
            plt.style.use('seaborn-v0_8')
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if chart_type == 'topic_distribution':
                topics = list(data.keys())
                counts = list(data.values())
                
                bars = ax.bar(topics, counts, color='skyblue', edgecolor='navy', alpha=0.7)
                ax.set_title('Problems Solved by Topic', fontsize=16, fontweight='bold')
                ax.set_xlabel('Topic', fontsize=12)
                ax.set_ylabel('Problems Solved', fontsize=12)
                
                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(height)}', ha='center', va='bottom')
                
                plt.xticks(rotation=45, ha='right')
                
            elif chart_type == 'difficulty_distribution':
                difficulties = list(data.keys())
                counts = list(data.values())
                colors = ['#90EE90', '#FFD700', '#FF6B6B']  # Light green, gold, light red
                
                wedges, texts, autotexts = ax.pie(counts, labels=difficulties, colors=colors,
                                                 autopct='%1.1f%%', startangle=90)
                ax.set_title('Problems by Difficulty', fontsize=16, fontweight='bold')
                
            elif chart_type == 'learning_velocity':
                dates = [item['date'] for item in data]
                counts = [item['count'] for item in data]
                
                ax.plot(dates, counts, marker='o', linewidth=2, markersize=6,
                       color='#4CAF50', markerfacecolor='#2E7D32')
                ax.set_title('Learning Velocity (Last 30 Days)', fontsize=16, fontweight='bold')
                ax.set_xlabel('Date', fontsize=12)
                ax.set_ylabel('Problems Solved', fontsize=12)
                ax.grid(True, alpha=0.3)
                
                plt.xticks(rotation=45, ha='right')
            
            plt.tight_layout()
            
            # Convert to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            plt.close()
            
            return f"data:image/png;base64,{img_base64}"
            
        except Exception as e:
            self.error_handler.handle_error(e, "generate_chart")
            return ""

# Initialize dashboard
dashboard = WebDashboard()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/dashboard')
def api_dashboard():
    """API endpoint for dashboard data"""
    data = dashboard.get_dashboard_data()
    return jsonify(data)

@app.route('/api/chart/<chart_type>')
def api_chart(chart_type):
    """API endpoint for charts"""
    data = dashboard.get_dashboard_data()
    
    if chart_type == 'topic_distribution':
        chart_data = data.get('topic_distribution', {})
    elif chart_type == 'difficulty_distribution':
        chart_data = data.get('difficulty_distribution', {})
    elif chart_type == 'learning_velocity':
        chart_data = data.get('learning_velocity', [])
    else:
        return jsonify({'error': 'Invalid chart type'})
    
    chart_base64 = dashboard.generate_chart(chart_type, chart_data)
    return jsonify({'chart': chart_base64})

@app.route('/api/start_session', methods=['POST'])
def api_start_session():
    """Start a new practice session"""
    try:
        data = request.json
        topic = data.get('topic')
        difficulty = data.get('difficulty')
        language = data.get('language', 'python')
        mode = data.get('mode', 'smart')
        
        # Get next problem
        problem = dashboard.practice_manager.get_next_problem(
            topic=topic, difficulty=difficulty, selection_mode=mode
        )
        
        if problem:
            dashboard.practice_manager.current_problem = problem
            return jsonify({
                'success': True,
                'problem': problem
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No problems found matching criteria'
            })
            
    except Exception as e:
        dashboard.error_handler.handle_error(e, "api_start_session")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/complete_problem', methods=['POST'])
def api_complete_problem():
    """Complete current problem"""
    try:
        data = request.json
        notes = data.get('notes', '')
        time_spent = data.get('time_spent', 0)
        
        dashboard.practice_manager.complete_problem(
            notes=notes, time_spent=time_spent
        )
        
        return jsonify({'success': True})
        
    except Exception as e:
        dashboard.error_handler.handle_error(e, "api_complete_problem")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/recommendations')
def api_recommendations():
    """Get problem recommendations"""
    try:
        count = request.args.get('count', 5, type=int)
        topic = request.args.get('topic')
        language = request.args.get('language', 'python')
        
        if dashboard.recommendation_engine:
            if topic:
                recommendations = dashboard.recommendation_engine.get_topic_recommendations(
                    topic, language, count
                )
            else:
                recommendations = dashboard.recommendation_engine.get_personalized_recommendations(
                    language, count
                )
            
            return jsonify({'recommendations': recommendations})
        else:
            return jsonify({'error': 'Recommendation engine not available'})
            
    except Exception as e:
        dashboard.error_handler.handle_error(e, "api_recommendations")
        return jsonify({'error': str(e)})

@app.route('/api/review_due')
def api_review_due():
    """Get problems due for review"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        if dashboard.spaced_repetition:
            due_reviews = dashboard.spaced_repetition.get_due_reviews(limit=limit)
            return jsonify({'due_reviews': due_reviews})
        else:
            return jsonify({'error': 'Spaced repetition not available'})
            
    except Exception as e:
        dashboard.error_handler.handle_error(e, "api_review_due")
        return jsonify({'error': str(e)})

@app.route('/api/system_health')
def api_system_health():
    """Get system health metrics"""
    try:
        health = dashboard.performance_monitor.get_system_health()
        return jsonify(health)
        
    except Exception as e:
        dashboard.error_handler.handle_error(e, "api_system_health")
        return jsonify({'error': str(e)})

@app.route('/api/export_data')
def api_export_data():
    """Export data endpoint"""
    try:
        format_type = request.args.get('format', 'json')
        
        if format_type == 'json':
            dashboard.practice_manager.export_data(format='json', output='temp_export.json')
            return send_file('temp_export.json', as_attachment=True, 
                           download_name=f'practice_data_{datetime.now().strftime("%Y%m%d")}.json')
        else:
            return jsonify({'error': 'Unsupported format'})
            
    except Exception as e:
        dashboard.error_handler.handle_error(e, "api_export_data")
        return jsonify({'error': str(e)})

# Create templates directory and basic HTML template
def create_dashboard_template():
    """Create the dashboard HTML template"""
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)
    
    template_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coding Practice Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .dashboard-card {
            border: none;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border-radius: 10px;
            transition: transform 0.2s;
        }
        .dashboard-card:hover {
            transform: translateY(-5px);
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .chart-container {
            height: 400px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .activity-item {
            border-left: 4px solid #007bff;
            padding-left: 15px;
            margin-bottom: 15px;
        }
        .difficulty-easy { color: #28a745; }
        .difficulty-medium { color: #ffc107; }
        .difficulty-hard { color: #dc3545; }
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="#">
                <i class="fas fa-code"></i> Coding Practice Dashboard
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="#" onclick="refreshData()">
                    <i class="fas fa-sync-alt"></i> Refresh
                </a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <!-- Statistics Cards -->
        <div class="row mb-4">
            <div class="col-md-2">
                <div class="card dashboard-card stat-card">
                    <div class="card-body text-center">
                        <i class="fas fa-tasks fa-2x mb-2"></i>
                        <h5 id="total-problems">0</h5>
                        <small>Total Problems</small>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card dashboard-card stat-card">
                    <div class="card-body text-center">
                        <i class="fas fa-check-circle fa-2x mb-2"></i>
                        <h5 id="completed-problems">0</h5>
                        <small>Completed</small>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card dashboard-card stat-card">
                    <div class="card-body text-center">
                        <i class="fas fa-fire fa-2x mb-2"></i>
                        <h5 id="current-streak">0</h5>
                        <small>Day Streak</small>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card dashboard-card stat-card">
                    <div class="card-body text-center">
                        <i class="fas fa-clock fa-2x mb-2"></i>
                        <h5 id="avg-time">0m</h5>
                        <small>Avg Time</small>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card dashboard-card stat-card">
                    <div class="card-body text-center">
                        <i class="fas fa-percentage fa-2x mb-2"></i>
                        <h5 id="completion-rate">0%</h5>
                        <small>Completion Rate</small>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card dashboard-card stat-card">
                    <div class="card-body text-center">
                        <i class="fas fa-trophy fa-2x mb-2"></i>
                        <h5 id="success-rate">0%</h5>
                        <small>Success Rate</small>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts Row -->
        <div class="row mb-4">
            <div class="col-md-4">
                <div class="card dashboard-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-bar"></i> Topic Distribution</h5>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <img id="topic-chart" src="" alt="Topic Distribution Chart" class="img-fluid">
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card dashboard-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-pie"></i> Difficulty Distribution</h5>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <img id="difficulty-chart" src="" alt="Difficulty Distribution Chart" class="img-fluid">
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card dashboard-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> Learning Velocity</h5>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <img id="velocity-chart" src="" alt="Learning Velocity Chart" class="img-fluid">
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Content Row -->
        <div class="row">
            <div class="col-md-6">
                <div class="card dashboard-card">
                    <div class="card-header">
                        <h5><i class="fas fa-history"></i> Recent Activity</h5>
                    </div>
                    <div class="card-body">
                        <div id="recent-activity"></div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card dashboard-card">
                    <div class="card-header">
                        <h5><i class="fas fa-lightbulb"></i> Recommendations</h5>
                    </div>
                    <div class="card-body">
                        <div id="recommendations"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Quick Actions -->
        <div class="row mt-4">
            <div class="col-12">
                <div class="card dashboard-card">
                    <div class="card-header">
                        <h5><i class="fas fa-play"></i> Quick Actions</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-3">
                                <button class="btn btn-primary w-100" onclick="startSession()">
                                    <i class="fas fa-play"></i> Start Session
                                </button>
                            </div>
                            <div class="col-md-3">
                                <button class="btn btn-success w-100" onclick="viewRecommendations()">
                                    <i class="fas fa-star"></i> Get Recommendations
                                </button>
                            </div>
                            <div class="col-md-3">
                                <button class="btn btn-warning w-100" onclick="viewDueReviews()">
                                    <i class="fas fa-redo"></i> Due Reviews
                                </button>
                            </div>
                            <div class="col-md-3">
                                <button class="btn btn-info w-100" onclick="exportData()">
                                    <i class="fas fa-download"></i> Export Data
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Dashboard JavaScript
        function loadDashboard() {
            fetch('/api/dashboard')
                .then(response => response.json())
                .then(data => {
                    updateStats(data.stats);
                    updateRecentActivity(data.recent_activity);
                    updateRecommendations(data.recommendations);
                    loadCharts();
                })
                .catch(error => console.error('Error loading dashboard:', error));
        }

        function updateStats(stats) {
            document.getElementById('total-problems').textContent = stats.total_problems || 0;
            document.getElementById('completed-problems').textContent = stats.completed_problems || 0;
            document.getElementById('current-streak').textContent = stats.current_streak || 0;
            document.getElementById('avg-time').textContent = (stats.avg_time_minutes || 0) + 'm';
            document.getElementById('completion-rate').textContent = (stats.completion_rate || 0).toFixed(1) + '%';
            document.getElementById('success-rate').textContent = (stats.success_rate || 0).toFixed(1) + '%';
        }

        function updateRecentActivity(activities) {
            const container = document.getElementById('recent-activity');
            container.innerHTML = '';
            
            activities.forEach(activity => {
                const item = document.createElement('div');
                item.className = 'activity-item';
                item.innerHTML = `
                    <h6>${activity.title}</h6>
                    <small class="text-muted">${activity.topic} • ${activity.difficulty}</small><br>
                    <small class="text-muted">${new Date(activity.completed_at).toLocaleDateString()}</small>
                `;
                container.appendChild(item);
            });
        }

        function updateRecommendations(recommendations) {
            const container = document.getElementById('recommendations');
            container.innerHTML = '';
            
            recommendations.forEach(rec => {
                const item = document.createElement('div');
                item.className = 'mb-3';
                item.innerHTML = `
                    <h6>${rec.title}</h6>
                    <small class="text-muted">${rec.topic} • ${rec.difficulty}</small><br>
                    <small class="text-primary">${rec.recommendation_reasons?.join(', ') || ''}</small>
                `;
                container.appendChild(item);
            });
        }

        function loadCharts() {
            ['topic_distribution', 'difficulty_distribution', 'learning_velocity'].forEach(chartType => {
                fetch(`/api/chart/${chartType}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.chart) {
                            const imgId = chartType.replace('_', '-') + '-chart';
                            document.getElementById(imgId).src = data.chart;
                        }
                    })
                    .catch(error => console.error(`Error loading ${chartType} chart:`, error));
            });
        }

        function refreshData() {
            loadDashboard();
        }

        function startSession() {
            // Implement session start logic
            alert('Session start functionality - integrate with practice system');
        }

        function viewRecommendations() {
            // Implement recommendations view
            alert('Recommendations view - integrate with recommendation engine');
        }

        function viewDueReviews() {
            // Implement due reviews view
            alert('Due reviews view - integrate with spaced repetition system');
        }

        function exportData() {
            window.location.href = '/api/export_data?format=json';
        }

        // Load dashboard on page load
        document.addEventListener('DOMContentLoaded', loadDashboard);
        
        // Auto-refresh every 5 minutes
        setInterval(loadDashboard, 300000);
    </script>
</body>
</html>
    '''
    
    template_path = templates_dir / "dashboard.html"
    with open(template_path, 'w') as f:
        f.write(template_content.strip())

if __name__ == '__main__':
    create_dashboard_template()
    print("🌐 Starting Web Dashboard...")
    print("📊 Dashboard available at: http://localhost:5000")
    print("🔄 Auto-refresh enabled every 5 minutes")
    print("📈 Real-time progress tracking and analytics")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 