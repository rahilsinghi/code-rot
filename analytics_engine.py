#!/usr/bin/env python3
"""
Advanced Analytics Engine for Coding Practice System
Provides deep insights, predictive analytics, and learning optimization
"""

import sqlite3
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict, Counter
import math
import statistics
from pathlib import Path

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.metrics import mean_squared_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False

class AnalyticsEngine:
    """Advanced analytics engine for coding practice insights"""
    
    def __init__(self, db_path: str = "practice_data/problems.db"):
        self.db_path = db_path
        self.cache = {}
        self.cache_expiry = {}
        
    def _get_cached_or_compute(self, cache_key: str, compute_func, ttl: int = 3600):
        """Get cached result or compute if expired"""
        now = datetime.now()
        
        if (cache_key in self.cache and 
            cache_key in self.cache_expiry and 
            now < self.cache_expiry[cache_key]):
            return self.cache[cache_key]
        
        result = compute_func()
        self.cache[cache_key] = result
        self.cache_expiry[cache_key] = now + timedelta(seconds=ttl)
        
        return result
    
    def get_comprehensive_analytics(self, language: str = "python") -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        return {
            'performance_metrics': self.get_performance_metrics(language),
            'learning_patterns': self.get_learning_patterns(language),
            'difficulty_progression': self.get_difficulty_progression(language),
            'topic_mastery': self.get_topic_mastery_analysis(language),
            'time_analysis': self.get_time_analysis(language),
            'retention_analysis': self.get_retention_analysis(language),
            'predictive_insights': self.get_predictive_insights(language),
            'optimization_recommendations': self.get_optimization_recommendations(language),
            'comparative_analysis': self.get_comparative_analysis(language),
            'streak_analysis': self.get_streak_analysis(language),
            'efficiency_metrics': self.get_efficiency_metrics(language),
            'weakness_analysis': self.get_weakness_analysis(language)
        }
    
    def get_performance_metrics(self, language: str) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        def compute():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Basic metrics
            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT pr.problem_id) as total_solved,
                    AVG(pr.time_spent) as avg_time,
                    MIN(pr.time_spent) as min_time,
                    MAX(pr.time_spent) as max_time,
                    AVG(pr.attempts) as avg_attempts
                FROM progress pr
                WHERE pr.status = 'completed' AND pr.language = ?
            ''', (language,))
            
            basic_stats = cursor.fetchone()
            
            # Difficulty breakdown
            cursor.execute('''
                SELECT 
                    p.difficulty,
                    COUNT(*) as count,
                    AVG(pr.time_spent) as avg_time,
                    AVG(pr.attempts) as avg_attempts
                FROM progress pr
                JOIN problems p ON pr.problem_id = p.id
                WHERE pr.status = 'completed' AND pr.language = ?
                GROUP BY p.difficulty
            ''', (language,))
            
            difficulty_stats = {}
            for row in cursor.fetchall():
                difficulty_stats[row[0]] = {
                    'count': row[1],
                    'avg_time': row[2] or 0,
                    'avg_attempts': row[3] or 0
                }
            
            # Success rate by difficulty
            cursor.execute('''
                SELECT 
                    p.difficulty,
                    COUNT(CASE WHEN pr.status = 'completed' THEN 1 END) as completed,
                    COUNT(*) as total
                FROM progress pr
                JOIN problems p ON pr.problem_id = p.id
                WHERE pr.language = ?
                GROUP BY p.difficulty
            ''', (language,))
            
            success_rates = {}
            for row in cursor.fetchall():
                success_rates[row[0]] = (row[1] / row[2]) * 100 if row[2] > 0 else 0
            
            conn.close()
            
            return {
                'basic_stats': {
                    'total_solved': basic_stats[0] or 0,
                    'avg_time': basic_stats[1] or 0,
                    'min_time': basic_stats[2] or 0,
                    'max_time': basic_stats[3] or 0,
                    'avg_attempts': basic_stats[4] or 0
                },
                'difficulty_stats': difficulty_stats,
                'success_rates': success_rates
            }
        
        return self._get_cached_or_compute("performance_metrics", compute)
    
    def get_learning_patterns(self, language: str) -> Dict[str, Any]:
        """Analyze learning patterns and habits"""
        def compute():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Daily activity patterns
            cursor.execute('''
                SELECT 
                    strftime('%w', pr.completed_at) as day_of_week,
                    strftime('%H', pr.completed_at) as hour,
                    COUNT(*) as count
                FROM progress pr
                WHERE pr.status = 'completed' AND pr.language = ?
                GROUP BY day_of_week, hour
                ORDER BY day_of_week, hour
            ''', (language,))
            
            activity_patterns = defaultdict(lambda: defaultdict(int))
            for row in cursor.fetchall():
                activity_patterns[int(row[0])][int(row[1])] = row[2]
            
            # Weekly progress trends
            cursor.execute('''
                SELECT 
                    strftime('%Y-%W', pr.completed_at) as week,
                    COUNT(*) as count,
                    AVG(pr.time_spent) as avg_time
                FROM progress pr
                WHERE pr.status = 'completed' AND pr.language = ?
                GROUP BY week
                ORDER BY week
            ''', (language,))
            
            weekly_trends = []
            for row in cursor.fetchall():
                weekly_trends.append({
                    'week': row[0],
                    'count': row[1],
                    'avg_time': row[2] or 0
                })
            
            # Learning velocity calculation
            if len(weekly_trends) >= 2:
                recent_weeks = weekly_trends[-4:]  # Last 4 weeks
                velocity = sum(week['count'] for week in recent_weeks) / len(recent_weeks)
            else:
                velocity = 0
            
            conn.close()
            
            return {
                'activity_patterns': dict(activity_patterns),
                'weekly_trends': weekly_trends,
                'learning_velocity': velocity,
                'most_active_day': max(activity_patterns.keys(), 
                                     key=lambda k: sum(activity_patterns[k].values())) if activity_patterns else 0,
                'most_active_hour': self._get_most_active_hour(activity_patterns)
            }
        
        return self._get_cached_or_compute("learning_patterns", compute)
    
    def get_difficulty_progression(self, language: str) -> Dict[str, Any]:
        """Analyze difficulty progression over time"""
        def compute():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    DATE(pr.completed_at) as date,
                    p.difficulty,
                    COUNT(*) as count
                FROM progress pr
                JOIN problems p ON pr.problem_id = p.id
                WHERE pr.status = 'completed' AND pr.language = ?
                GROUP BY date, p.difficulty
                ORDER BY date
            ''', (language,))
            
            progression = defaultdict(lambda: defaultdict(int))
            for row in cursor.fetchall():
                progression[row[0]][row[1]] = row[2]
            
            # Calculate progression metrics
            difficulty_scores = {'easy': 1, 'medium': 2, 'hard': 3}
            daily_scores = []
            
            for date, difficulties in progression.items():
                weighted_score = sum(difficulty_scores[diff] * count 
                                   for diff, count in difficulties.items())
                total_problems = sum(difficulties.values())
                avg_difficulty = weighted_score / total_problems if total_problems > 0 else 0
                daily_scores.append({'date': date, 'avg_difficulty': avg_difficulty})
            
            # Trend analysis
            if len(daily_scores) >= 2 and SKLEARN_AVAILABLE:
                dates_numeric = [(datetime.strptime(item['date'], '%Y-%m-%d') - 
                                datetime.strptime(daily_scores[0]['date'], '%Y-%m-%d')).days 
                               for item in daily_scores]
                scores = [item['avg_difficulty'] for item in daily_scores]
                
                X = np.array(dates_numeric).reshape(-1, 1)
                y = np.array(scores)
                
                model = LinearRegression()
                model.fit(X, y)
                
                trend_slope = model.coef_[0]
                trend_direction = "increasing" if trend_slope > 0.01 else "decreasing" if trend_slope < -0.01 else "stable"
            else:
                trend_slope = 0
                trend_direction = "insufficient_data"
            
            conn.close()
            
            return {
                'daily_progression': dict(progression),
                'daily_scores': daily_scores,
                'trend_slope': trend_slope,
                'trend_direction': trend_direction,
                'current_avg_difficulty': daily_scores[-1]['avg_difficulty'] if daily_scores else 0
            }
        
        return self._get_cached_or_compute("difficulty_progression", compute)
    
    def get_topic_mastery_analysis(self, language: str) -> Dict[str, Any]:
        """Analyze topic mastery and learning efficiency"""
        def compute():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    p.topic,
                    COUNT(*) as problems_solved,
                    AVG(pr.time_spent) as avg_time,
                    AVG(pr.attempts) as avg_attempts,
                    MIN(pr.time_spent) as min_time,
                    MAX(pr.time_spent) as max_time,
                    COUNT(CASE WHEN p.difficulty = 'easy' THEN 1 END) as easy_count,
                    COUNT(CASE WHEN p.difficulty = 'medium' THEN 1 END) as medium_count,
                    COUNT(CASE WHEN p.difficulty = 'hard' THEN 1 END) as hard_count
                FROM progress pr
                JOIN problems p ON pr.problem_id = p.id
                WHERE pr.status = 'completed' AND pr.language = ?
                GROUP BY p.topic
                ORDER BY problems_solved DESC
            ''', (language,))
            
            topic_stats = {}
            for row in cursor.fetchall():
                topic = row[0]
                problems_solved = row[1]
                avg_time = row[2] or 0
                avg_attempts = row[3] or 0
                
                # Calculate mastery score (0-100)
                mastery_score = min(100, (problems_solved / 10) * 100)  # 10 problems = 100% mastery
                
                # Adjust for efficiency (lower time and attempts = higher mastery)
                efficiency_factor = max(0.5, 1.0 - (avg_attempts - 1) * 0.1)
                time_factor = max(0.5, 1.0 - (avg_time - 15) / 60)  # 15 min baseline
                
                adjusted_mastery = mastery_score * efficiency_factor * time_factor
                
                topic_stats[topic] = {
                    'problems_solved': problems_solved,
                    'avg_time': avg_time,
                    'avg_attempts': avg_attempts,
                    'min_time': row[4] or 0,
                    'max_time': row[5] or 0,
                    'difficulty_distribution': {
                        'easy': row[6],
                        'medium': row[7],
                        'hard': row[8]
                    },
                    'mastery_score': round(adjusted_mastery, 1),
                    'efficiency_factor': round(efficiency_factor, 2),
                    'time_factor': round(time_factor, 2)
                }
            
            # Identify strengths and weaknesses
            sorted_topics = sorted(topic_stats.items(), key=lambda x: x[1]['mastery_score'], reverse=True)
            
            strengths = [topic for topic, stats in sorted_topics[:3] if stats['mastery_score'] > 70]
            weaknesses = [topic for topic, stats in sorted_topics[-3:] if stats['mastery_score'] < 50]
            
            conn.close()
            
            return {
                'topic_stats': topic_stats,
                'strengths': strengths,
                'weaknesses': weaknesses,
                'total_topics': len(topic_stats),
                'mastery_distribution': self._get_mastery_distribution(topic_stats)
            }
        
        return self._get_cached_or_compute("topic_mastery", compute)
    
    def get_time_analysis(self, language: str) -> Dict[str, Any]:
        """Analyze time usage patterns and efficiency"""
        def compute():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    pr.time_spent,
                    p.difficulty,
                    p.topic,
                    pr.completed_at
                FROM progress pr
                JOIN problems p ON pr.problem_id = p.id
                WHERE pr.status = 'completed' AND pr.language = ? AND pr.time_spent > 0
                ORDER BY pr.completed_at
            ''', (language,))
            
            time_data = []
            for row in cursor.fetchall():
                time_data.append({
                    'time_spent': row[0],
                    'difficulty': row[1],
                    'topic': row[2],
                    'completed_at': row[3]
                })
            
            if not time_data:
                return {'error': 'No time data available'}
            
            # Time statistics
            times = [item['time_spent'] for item in time_data]
            time_stats = {
                'mean': statistics.mean(times),
                'median': statistics.median(times),
                'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
                'min': min(times),
                'max': max(times),
                'percentiles': {
                    '25th': np.percentile(times, 25),
                    '75th': np.percentile(times, 75),
                    '90th': np.percentile(times, 90)
                }
            }
            
            # Time by difficulty
            difficulty_times = defaultdict(list)
            for item in time_data:
                difficulty_times[item['difficulty']].append(item['time_spent'])
            
            difficulty_time_stats = {}
            for diff, times in difficulty_times.items():
                if times:
                    difficulty_time_stats[diff] = {
                        'mean': statistics.mean(times),
                        'median': statistics.median(times),
                        'count': len(times)
                    }
            
            # Time improvement trend
            if len(time_data) >= 5:
                recent_times = times[-10:]  # Last 10 problems
                early_times = times[:10]   # First 10 problems
                
                recent_avg = statistics.mean(recent_times)
                early_avg = statistics.mean(early_times)
                
                improvement_rate = ((early_avg - recent_avg) / early_avg) * 100 if early_avg > 0 else 0
            else:
                improvement_rate = 0
            
            conn.close()
            
            return {
                'time_stats': time_stats,
                'difficulty_time_stats': difficulty_time_stats,
                'improvement_rate': improvement_rate,
                'total_time_spent': sum(times),
                'efficiency_score': self._calculate_efficiency_score(time_data)
            }
        
        return self._get_cached_or_compute("time_analysis", compute)
    
    def get_retention_analysis(self, language: str) -> Dict[str, Any]:
        """Analyze problem retention and review patterns"""
        def compute():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get review data if available
            cursor.execute('''
                SELECT 
                    problem_id,
                    COUNT(*) as review_count,
                    AVG(CASE WHEN performance = 'excellent' THEN 4
                             WHEN performance = 'good' THEN 3
                             WHEN performance = 'fair' THEN 2
                             WHEN performance = 'poor' THEN 1
                             ELSE 0 END) as avg_performance
                FROM spaced_repetition
                WHERE language = ?
                GROUP BY problem_id
            ''', (language,))
            
            review_data = {}
            for row in cursor.fetchall():
                review_data[row[0]] = {
                    'review_count': row[1],
                    'avg_performance': row[2] or 0
                }
            
            # Calculate retention metrics
            if review_data:
                retention_rates = []
                for problem_id, data in review_data.items():
                    retention_rate = (data['avg_performance'] / 4) * 100
                    retention_rates.append(retention_rate)
                
                avg_retention = statistics.mean(retention_rates) if retention_rates else 0
                retention_distribution = self._get_retention_distribution(retention_rates)
            else:
                avg_retention = 0
                retention_distribution = {}
            
            conn.close()
            
            return {
                'review_data': review_data,
                'avg_retention_rate': avg_retention,
                'retention_distribution': retention_distribution,
                'total_reviewed_problems': len(review_data),
                'retention_score': self._calculate_retention_score(review_data)
            }
        
        return self._get_cached_or_compute("retention_analysis", compute)
    
    def get_predictive_insights(self, language: str) -> Dict[str, Any]:
        """Generate predictive insights using machine learning"""
        def compute():
            if not SKLEARN_AVAILABLE:
                return {'error': 'Machine learning libraries not available'}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get historical data
            cursor.execute('''
                SELECT 
                    DATE(pr.completed_at) as date,
                    COUNT(*) as daily_count,
                    AVG(pr.time_spent) as avg_time
                FROM progress pr
                WHERE pr.status = 'completed' AND pr.language = ?
                GROUP BY DATE(pr.completed_at)
                ORDER BY date
            ''', (language,))
            
            daily_data = []
            for row in cursor.fetchall():
                daily_data.append({
                    'date': row[0],
                    'count': row[1],
                    'avg_time': row[2] or 0
                })
            
            if len(daily_data) < 7:
                return {'error': 'Insufficient data for predictions'}
            
            # Prepare data for prediction
            dates = [datetime.strptime(item['date'], '%Y-%m-%d') for item in daily_data]
            days_since_start = [(date - dates[0]).days for date in dates]
            counts = [item['count'] for item in daily_data]
            
            # Predict future performance
            X = np.array(days_since_start).reshape(-1, 1)
            y = np.array(counts)
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Predict next 7 days
            future_days = [(dates[-1] + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 8)]
            future_X = np.array([(datetime.strptime(date, '%Y-%m-%d') - dates[0]).days 
                               for date in future_days]).reshape(-1, 1)
            future_predictions = model.predict(future_X)
            
            predictions = []
            for i, date in enumerate(future_days):
                predictions.append({
                    'date': date,
                    'predicted_count': max(0, round(future_predictions[i], 1))
                })
            
            # Calculate model accuracy
            y_pred = model.predict(X)
            mse = mean_squared_error(y, y_pred)
            accuracy = max(0, 100 - (mse / np.var(y)) * 100) if np.var(y) > 0 else 0
            
            conn.close()
            
            return {
                'predictions': predictions,
                'model_accuracy': round(accuracy, 1),
                'trend_slope': model.coef_[0],
                'expected_weekly_problems': sum(pred['predicted_count'] for pred in predictions)
            }
        
        return self._get_cached_or_compute("predictive_insights", compute)
    
    def get_optimization_recommendations(self, language: str) -> List[Dict[str, Any]]:
        """Generate optimization recommendations based on analysis"""
        analytics = self.get_comprehensive_analytics(language)
        recommendations = []
        
        # Performance-based recommendations
        perf_metrics = analytics.get('performance_metrics', {})
        if perf_metrics.get('basic_stats', {}).get('avg_time', 0) > 30:
            recommendations.append({
                'type': 'time_optimization',
                'priority': 'high',
                'title': 'Reduce Average Solving Time',
                'description': 'Your average solving time is above 30 minutes. Consider practicing more fundamental concepts.',
                'action': 'Focus on easier problems to build speed and confidence'
            })
        
        # Topic mastery recommendations
        topic_mastery = analytics.get('topic_mastery', {})
        weaknesses = topic_mastery.get('weaknesses', [])
        if weaknesses:
            recommendations.append({
                'type': 'topic_focus',
                'priority': 'medium',
                'title': 'Strengthen Weak Topics',
                'description': f'Focus on improving: {", ".join(weaknesses)}',
                'action': f'Dedicate 30% of practice time to {weaknesses[0]} problems'
            })
        
        # Learning pattern recommendations
        learning_patterns = analytics.get('learning_patterns', {})
        if learning_patterns.get('learning_velocity', 0) < 2:
            recommendations.append({
                'type': 'consistency',
                'priority': 'high',
                'title': 'Increase Practice Frequency',
                'description': 'Your learning velocity is below optimal. Aim for daily practice.',
                'action': 'Set a goal of solving at least 2 problems per day'
            })
        
        # Difficulty progression recommendations
        difficulty_prog = analytics.get('difficulty_progression', {})
        if difficulty_prog.get('trend_direction') == 'stable':
            recommendations.append({
                'type': 'challenge',
                'priority': 'medium',
                'title': 'Increase Problem Difficulty',
                'description': 'You\'ve plateaued at your current difficulty level.',
                'action': 'Gradually introduce more medium/hard problems'
            })
        
        return recommendations
    
    def get_comparative_analysis(self, language: str) -> Dict[str, Any]:
        """Compare performance across different dimensions"""
        def compute():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Language comparison
            cursor.execute('''
                SELECT 
                    pr.language,
                    COUNT(*) as problems_solved,
                    AVG(pr.time_spent) as avg_time
                FROM progress pr
                WHERE pr.status = 'completed'
                GROUP BY pr.language
            ''')
            
            language_comparison = {}
            for row in cursor.fetchall():
                language_comparison[row[0]] = {
                    'problems_solved': row[1],
                    'avg_time': row[2] or 0
                }
            
            # Platform comparison
            cursor.execute('''
                SELECT 
                    p.platform,
                    COUNT(*) as problems_solved,
                    AVG(pr.time_spent) as avg_time
                FROM progress pr
                JOIN problems p ON pr.problem_id = p.id
                WHERE pr.status = 'completed' AND pr.language = ?
                GROUP BY p.platform
            ''', (language,))
            
            platform_comparison = {}
            for row in cursor.fetchall():
                platform_comparison[row[0]] = {
                    'problems_solved': row[1],
                    'avg_time': row[2] or 0
                }
            
            conn.close()
            
            return {
                'language_comparison': language_comparison,
                'platform_comparison': platform_comparison,
                'preferred_language': max(language_comparison.keys(), 
                                        key=lambda k: language_comparison[k]['problems_solved']) if language_comparison else None,
                'preferred_platform': max(platform_comparison.keys(), 
                                        key=lambda k: platform_comparison[k]['problems_solved']) if platform_comparison else None
            }
        
        return self._get_cached_or_compute("comparative_analysis", compute)
    
    def get_streak_analysis(self, language: str) -> Dict[str, Any]:
        """Analyze practice streaks and consistency"""
        def compute():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT DISTINCT DATE(completed_at) as date
                FROM progress
                WHERE status = 'completed' AND language = ?
                ORDER BY date
            ''', (language,))
            
            practice_dates = [row[0] for row in cursor.fetchall()]
            
            if not practice_dates:
                return {'error': 'No practice data available'}
            
            # Calculate streaks
            streaks = []
            current_streak = 1
            
            for i in range(1, len(practice_dates)):
                prev_date = datetime.strptime(practice_dates[i-1], '%Y-%m-%d')
                curr_date = datetime.strptime(practice_dates[i], '%Y-%m-%d')
                
                if (curr_date - prev_date).days == 1:
                    current_streak += 1
                else:
                    streaks.append(current_streak)
                    current_streak = 1
            
            streaks.append(current_streak)
            
            # Current streak calculation
            today = datetime.now().date()
            last_practice = datetime.strptime(practice_dates[-1], '%Y-%m-%d').date()
            days_since_last = (today - last_practice).days
            
            if days_since_last <= 1:
                current_active_streak = current_streak
            else:
                current_active_streak = 0
            
            conn.close()
            
            return {
                'all_streaks': streaks,
                'longest_streak': max(streaks) if streaks else 0,
                'current_streak': current_active_streak,
                'average_streak': statistics.mean(streaks) if streaks else 0,
                'total_practice_days': len(practice_dates),
                'days_since_last_practice': days_since_last
            }
        
        return self._get_cached_or_compute("streak_analysis", compute)
    
    def get_efficiency_metrics(self, language: str) -> Dict[str, Any]:
        """Calculate efficiency metrics and productivity scores"""
        def compute():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get efficiency data
            cursor.execute('''
                SELECT 
                    pr.time_spent,
                    pr.attempts,
                    p.difficulty,
                    p.topic
                FROM progress pr
                JOIN problems p ON pr.problem_id = p.id
                WHERE pr.status = 'completed' AND pr.language = ? AND pr.time_spent > 0
            ''', (language,))
            
            efficiency_data = []
            for row in cursor.fetchall():
                efficiency_data.append({
                    'time_spent': row[0],
                    'attempts': row[1] or 1,
                    'difficulty': row[2],
                    'topic': row[3]
                })
            
            if not efficiency_data:
                return {'error': 'No efficiency data available'}
            
            # Calculate efficiency scores
            difficulty_weights = {'easy': 1, 'medium': 2, 'hard': 3}
            efficiency_scores = []
            
            for item in efficiency_data:
                # Base score from difficulty
                base_score = difficulty_weights[item['difficulty']]
                
                # Adjust for time (lower is better)
                time_factor = max(0.1, 1.0 - (item['time_spent'] - 15) / 45)  # 15-60 min range
                
                # Adjust for attempts (lower is better)
                attempt_factor = max(0.1, 1.0 - (item['attempts'] - 1) * 0.2)
                
                efficiency_score = base_score * time_factor * attempt_factor
                efficiency_scores.append(efficiency_score)
            
            # Overall efficiency metrics
            avg_efficiency = statistics.mean(efficiency_scores)
            efficiency_trend = self._calculate_efficiency_trend(efficiency_scores)
            
            conn.close()
            
            return {
                'average_efficiency': round(avg_efficiency, 2),
                'efficiency_trend': efficiency_trend,
                'efficiency_distribution': self._get_efficiency_distribution(efficiency_scores),
                'top_efficiency_percentile': np.percentile(efficiency_scores, 90),
                'productivity_score': self._calculate_productivity_score(efficiency_data)
            }
        
        return self._get_cached_or_compute("efficiency_metrics", compute)
    
    def get_weakness_analysis(self, language: str) -> Dict[str, Any]:
        """Identify and analyze specific weaknesses"""
        def compute():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get problems with multiple attempts or high time
            cursor.execute('''
                SELECT 
                    p.topic,
                    p.difficulty,
                    pr.time_spent,
                    pr.attempts,
                    p.title
                FROM progress pr
                JOIN problems p ON pr.problem_id = p.id
                WHERE pr.status = 'completed' AND pr.language = ?
                AND (pr.attempts > 1 OR pr.time_spent > 45)
                ORDER BY pr.attempts DESC, pr.time_spent DESC
            ''', (language,))
            
            weakness_data = []
            for row in cursor.fetchall():
                weakness_data.append({
                    'topic': row[0],
                    'difficulty': row[1],
                    'time_spent': row[2] or 0,
                    'attempts': row[3] or 1,
                    'title': row[4]
                })
            
            # Analyze patterns
            topic_weakness = defaultdict(list)
            difficulty_weakness = defaultdict(list)
            
            for item in weakness_data:
                topic_weakness[item['topic']].append(item)
                difficulty_weakness[item['difficulty']].append(item)
            
            # Calculate weakness scores
            topic_weakness_scores = {}
            for topic, items in topic_weakness.items():
                avg_attempts = statistics.mean([item['attempts'] for item in items])
                avg_time = statistics.mean([item['time_spent'] for item in items])
                weakness_score = (avg_attempts - 1) * 20 + (avg_time - 30) * 0.5
                topic_weakness_scores[topic] = max(0, weakness_score)
            
            conn.close()
            
            return {
                'weakness_patterns': weakness_data[:10],  # Top 10 challenging problems
                'topic_weakness_scores': topic_weakness_scores,
                'most_challenging_topic': max(topic_weakness_scores.keys(), 
                                             key=lambda k: topic_weakness_scores[k]) if topic_weakness_scores else None,
                'weakness_summary': self._generate_weakness_summary(weakness_data),
                'improvement_suggestions': self._generate_improvement_suggestions(topic_weakness_scores)
            }
        
        return self._get_cached_or_compute("weakness_analysis", compute)
    
    # Helper methods
    def _get_most_active_hour(self, activity_patterns: Dict) -> int:
        """Find the most active hour across all days"""
        hour_totals = defaultdict(int)
        for day_data in activity_patterns.values():
            for hour, count in day_data.items():
                hour_totals[hour] += count
        return max(hour_totals.keys(), key=lambda k: hour_totals[k]) if hour_totals else 0
    
    def _get_mastery_distribution(self, topic_stats: Dict) -> Dict[str, int]:
        """Calculate mastery level distribution"""
        distribution = {'beginner': 0, 'intermediate': 0, 'advanced': 0, 'expert': 0}
        
        for stats in topic_stats.values():
            score = stats['mastery_score']
            if score < 25:
                distribution['beginner'] += 1
            elif score < 50:
                distribution['intermediate'] += 1
            elif score < 75:
                distribution['advanced'] += 1
            else:
                distribution['expert'] += 1
        
        return distribution
    
    def _calculate_efficiency_score(self, time_data: List[Dict]) -> float:
        """Calculate overall efficiency score"""
        if not time_data:
            return 0
        
        difficulty_weights = {'easy': 1, 'medium': 2, 'hard': 3}
        total_weighted_score = 0
        total_weight = 0
        
        for item in time_data:
            weight = difficulty_weights[item['difficulty']]
            # Efficiency = difficulty / time (normalized)
            efficiency = weight / max(1, item['time_spent'] / 15)  # 15 min baseline
            total_weighted_score += efficiency * weight
            total_weight += weight
        
        return total_weighted_score / total_weight if total_weight > 0 else 0
    
    def _get_retention_distribution(self, retention_rates: List[float]) -> Dict[str, int]:
        """Calculate retention rate distribution"""
        distribution = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
        
        for rate in retention_rates:
            if rate >= 80:
                distribution['excellent'] += 1
            elif rate >= 60:
                distribution['good'] += 1
            elif rate >= 40:
                distribution['fair'] += 1
            else:
                distribution['poor'] += 1
        
        return distribution
    
    def _calculate_retention_score(self, review_data: Dict) -> float:
        """Calculate overall retention score"""
        if not review_data:
            return 0
        
        total_score = 0
        total_weight = 0
        
        for data in review_data.values():
            weight = data['review_count']
            score = data['avg_performance'] * 25  # Convert to 0-100 scale
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0
    
    def _calculate_efficiency_trend(self, efficiency_scores: List[float]) -> str:
        """Calculate efficiency trend direction"""
        if len(efficiency_scores) < 5:
            return "insufficient_data"
        
        recent_avg = statistics.mean(efficiency_scores[-5:])
        early_avg = statistics.mean(efficiency_scores[:5])
        
        if recent_avg > early_avg * 1.1:
            return "improving"
        elif recent_avg < early_avg * 0.9:
            return "declining"
        else:
            return "stable"
    
    def _get_efficiency_distribution(self, efficiency_scores: List[float]) -> Dict[str, int]:
        """Get efficiency score distribution"""
        distribution = {'low': 0, 'medium': 0, 'high': 0, 'excellent': 0}
        
        for score in efficiency_scores:
            if score < 1:
                distribution['low'] += 1
            elif score < 2:
                distribution['medium'] += 1
            elif score < 3:
                distribution['high'] += 1
            else:
                distribution['excellent'] += 1
        
        return distribution
    
    def _calculate_productivity_score(self, efficiency_data: List[Dict]) -> float:
        """Calculate productivity score based on problems solved per hour"""
        if not efficiency_data:
            return 0
        
        total_problems = len(efficiency_data)
        total_time_hours = sum(item['time_spent'] for item in efficiency_data) / 60
        
        return total_problems / total_time_hours if total_time_hours > 0 else 0
    
    def _generate_weakness_summary(self, weakness_data: List[Dict]) -> Dict[str, Any]:
        """Generate summary of weaknesses"""
        if not weakness_data:
            return {}
        
        total_problems = len(weakness_data)
        avg_attempts = statistics.mean([item['attempts'] for item in weakness_data])
        avg_time = statistics.mean([item['time_spent'] for item in weakness_data])
        
        most_common_topic = Counter([item['topic'] for item in weakness_data]).most_common(1)[0][0]
        
        return {
            'total_challenging_problems': total_problems,
            'avg_attempts': round(avg_attempts, 1),
            'avg_time': round(avg_time, 1),
            'most_problematic_topic': most_common_topic
        }
    
    def _generate_improvement_suggestions(self, topic_weakness_scores: Dict[str, float]) -> List[str]:
        """Generate improvement suggestions based on weakness analysis"""
        suggestions = []
        
        if not topic_weakness_scores:
            return suggestions
        
        # Sort topics by weakness score
        sorted_topics = sorted(topic_weakness_scores.items(), key=lambda x: x[1], reverse=True)
        
        for topic, score in sorted_topics[:3]:  # Top 3 weakest topics
            if score > 10:
                suggestions.append(f"Focus on {topic} fundamentals - practice easier problems first")
            elif score > 5:
                suggestions.append(f"Review {topic} concepts and common patterns")
            else:
                suggestions.append(f"Maintain {topic} skills with regular practice")
        
        return suggestions
    
    def export_analytics_report(self, language: str = "python", format: str = "json") -> str:
        """Export comprehensive analytics report"""
        analytics = self.get_comprehensive_analytics(language)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'language': language,
            'analytics': analytics
        }
        
        if format == "json":
            filename = f"analytics_report_{language}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            return filename
        
        return ""


if __name__ == "__main__":
    # Example usage
    engine = AnalyticsEngine()
    
    print("🔍 Generating Comprehensive Analytics Report...")
    analytics = engine.get_comprehensive_analytics("python")
    
    print("\n📊 Performance Metrics:")
    print(json.dumps(analytics['performance_metrics'], indent=2))
    
    print("\n🧠 Learning Patterns:")
    print(json.dumps(analytics['learning_patterns'], indent=2))
    
    print("\n💡 Optimization Recommendations:")
    recommendations = engine.get_optimization_recommendations("python")
    for rec in recommendations:
        print(f"- {rec['title']}: {rec['description']}")
    
    print("\n📈 Exporting full report...")
    filename = engine.export_analytics_report("python")
    print(f"Report saved to: {filename}") 