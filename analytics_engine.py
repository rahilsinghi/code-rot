#!/usr/bin/env python3
"""
Advanced Analytics Engine
Sophisticated insights, predictive analysis, and machine learning-powered recommendations
"""

import sqlite3
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
from collections import defaultdict, Counter
import math
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestClassifier

class AdvancedAnalytics:
    def __init__(self, db_path="practice_data/problems.db"):
        self.db_path = Path(db_path)
        self.analytics_db_path = self.db_path.parent / "analytics.db" 
        self.models_path = self.db_path.parent / "models"
        self.models_path.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Initialize analytics database
        self.init_analytics_db()
        
        # ML models
        self.models = {
            'difficulty_predictor': None,
            'success_predictor': None,
            'time_predictor': None,
            'topic_recommender': None
        }
        
        # Analytics cache
        self.cache = {}
        self.cache_ttl = {}
        
        logging.info("Advanced Analytics Engine initialized")
    
    def setup_logging(self):
        """Setup analytics logging"""
        log_dir = self.db_path.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'analytics.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def init_analytics_db(self):
        """Initialize advanced analytics database"""
        conn = sqlite3.connect(self.analytics_db_path)
        cursor = conn.cursor()
        
        # Learning patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                pattern_type TEXT,
                pattern_data TEXT,
                confidence_score REAL,
                metadata TEXT
            )
        ''')
        
        # Predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                prediction_type TEXT,
                input_features TEXT,
                prediction_value REAL,
                actual_value REAL,
                accuracy_score REAL,
                model_version TEXT
            )
        ''')
        
        # User clustering results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_clusters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cluster_id INTEGER,
                cluster_name TEXT,
                characteristics TEXT,
                confidence_score REAL
            )
        ''')
        
        # Advanced metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS advanced_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metric_type TEXT,
                metric_name TEXT,
                metric_value REAL,
                language TEXT,
                topic TEXT,
                difficulty TEXT,
                time_period TEXT,
                metadata TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_patterns_timestamp ON learning_patterns(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictions_type ON predictions(prediction_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_type_time ON advanced_metrics(metric_type, timestamp)')
        
        conn.commit()
        conn.close()
    
    def get_learning_analytics(self, language="python", days=30) -> Dict:
        """Generate comprehensive learning analytics"""
        try:
            analytics = {
                'learning_velocity': self.calculate_learning_velocity(language, days),
                'skill_progression': self.analyze_skill_progression(language, days),
                'learning_patterns': self.detect_learning_patterns(language, days),
                'performance_trends': self.analyze_performance_trends(language, days),
                'knowledge_gaps': self.identify_knowledge_gaps(language),
                'optimal_study_times': self.find_optimal_study_times(language, days),
                'retention_analysis': self.analyze_retention_patterns(language, days),
                'difficulty_calibration': self.analyze_difficulty_calibration(language),
                'predictive_insights': self.generate_predictive_insights(language),
                'comparative_analysis': self.generate_comparative_analysis(language, days)
            }
            
            # Cache results
            cache_key = f"learning_analytics_{language}_{days}"
            self.cache[cache_key] = analytics
            self.cache_ttl[cache_key] = datetime.now() + timedelta(hours=1)
            
            return analytics
        
        except Exception as e:
            self.logger.error(f"Error generating learning analytics: {e}")
            return {'error': str(e)}
    
    def calculate_learning_velocity(self, language, days) -> Dict:
        """Calculate learning velocity metrics"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('''
            SELECT 
                DATE(pr.completed_at) as date,
                COUNT(*) as problems_solved,
                AVG(pr.time_spent) as avg_time,
                p.difficulty,
                p.topic
            FROM progress pr
            JOIN problems p ON pr.problem_id = p.id
            WHERE pr.status = 'completed' 
            AND pr.language = ?
            AND DATE(pr.completed_at) >= DATE('now', '-{} days')
            GROUP BY DATE(pr.completed_at), p.difficulty, p.topic
            ORDER BY date
        '''.format(days), conn, params=(language,))
        conn.close()
        
        if df.empty:
            return {'velocity': 0, 'acceleration': 0, 'trend': 'stable'}
        
        # Daily totals
        daily_totals = df.groupby('date')['problems_solved'].sum()
        
        # Calculate velocity (problems per day)
        current_velocity = daily_totals.mean() if not daily_totals.empty else 0
        
        # Calculate acceleration (change in velocity)
        if len(daily_totals) > 7:
            recent_velocity = daily_totals.tail(7).mean()
            older_velocity = daily_totals.head(7).mean()
            acceleration = recent_velocity - older_velocity
        else:
            acceleration = 0
        
        # Determine trend
        if len(daily_totals) >= 3:
            x = np.arange(len(daily_totals))
            slope, _, r_value, _, _ = stats.linregress(x, daily_totals.values)
            
            if slope > 0.1:
                trend = 'accelerating'
            elif slope < -0.1:
                trend = 'decelerating'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        # Topic-specific velocities
        topic_velocities = df.groupby('topic')['problems_solved'].sum().to_dict()
        
        # Difficulty-specific velocities
        difficulty_velocities = df.groupby('difficulty')['problems_solved'].sum().to_dict()
        
        return {
            'velocity': round(current_velocity, 2),
            'acceleration': round(acceleration, 2),
            'trend': trend,
            'topic_velocities': topic_velocities,
            'difficulty_velocities': difficulty_velocities,
            'consistency': self._calculate_consistency(daily_totals)
        }
    
    def analyze_skill_progression(self, language, days) -> Dict:
        """Analyze skill progression across topics and difficulties"""
        conn = sqlite3.connect(self.db_path)
        
        # Get progression data
        df = pd.read_sql_query('''
            SELECT 
                pr.completed_at,
                p.topic,
                p.difficulty,
                pr.time_spent,
                pr.attempts,
                CASE WHEN pr.attempts = 1 THEN 1 ELSE 0 END as first_attempt_success
            FROM progress pr
            JOIN problems p ON pr.problem_id = p.id
            WHERE pr.status = 'completed' 
            AND pr.language = ?
            AND DATE(pr.completed_at) >= DATE('now', '-{} days')
            ORDER BY pr.completed_at
        '''.format(days), conn, params=(language,))
        conn.close()
        
        if df.empty:
            return {'topics': {}, 'difficulties': {}, 'overall_progression': 0}
        
        df['completed_at'] = pd.to_datetime(df['completed_at'])
        
        progression = {
            'topics': {},
            'difficulties': {},
            'overall_progression': 0,
            'mastery_indicators': {}
        }
        
        # Analyze topic progression
        for topic in df['topic'].unique():
            topic_data = df[df['topic'] == topic].sort_values('completed_at')
            
            # Calculate improvement metrics
            early_time = topic_data.head(10)['time_spent'].mean() if len(topic_data) > 10 else topic_data['time_spent'].mean()
            recent_time = topic_data.tail(10)['time_spent'].mean() if len(topic_data) > 10 else topic_data['time_spent'].mean()
            
            time_improvement = (early_time - recent_time) / early_time * 100 if early_time > 0 else 0
            
            early_success = topic_data.head(10)['first_attempt_success'].mean() if len(topic_data) > 10 else topic_data['first_attempt_success'].mean()
            recent_success = topic_data.tail(10)['first_attempt_success'].mean() if len(topic_data) > 10 else topic_data['first_attempt_success'].mean()
            
            success_improvement = (recent_success - early_success) * 100
            
            progression['topics'][topic] = {
                'problems_solved': len(topic_data),
                'time_improvement_percent': round(time_improvement, 2),
                'success_rate_improvement_percent': round(success_improvement, 2),
                'current_success_rate': round(recent_success * 100, 2),
                'mastery_level': self._calculate_mastery_level(topic_data)
            }
        
        # Analyze difficulty progression
        for difficulty in ['easy', 'medium', 'hard']:
            diff_data = df[df['difficulty'] == difficulty]
            if not diff_data.empty:
                progression['difficulties'][difficulty] = {
                    'problems_solved': len(diff_data),
                    'avg_time_spent': round(diff_data['time_spent'].mean(), 2),
                    'success_rate': round(diff_data['first_attempt_success'].mean() * 100, 2)
                }
        
        # Overall progression score
        progression['overall_progression'] = self._calculate_overall_progression(df)
        
        return progression
    
    def detect_learning_patterns(self, language, days) -> Dict:
        """Detect learning patterns using ML techniques"""
        conn = sqlite3.connect(self.db_path)
        
        # Get detailed learning data
        df = pd.read_sql_query('''
            SELECT 
                pr.completed_at,
                p.topic,
                p.difficulty,
                pr.time_spent,
                pr.attempts,
                strftime('%H', pr.completed_at) as hour,
                strftime('%w', pr.completed_at) as day_of_week,
                CASE WHEN pr.attempts = 1 THEN 1 ELSE 0 END as first_attempt_success
            FROM progress pr
            JOIN problems p ON pr.problem_id = p.id
            WHERE pr.status = 'completed' 
            AND pr.language = ?
            AND DATE(pr.completed_at) >= DATE('now', '-{} days')
            ORDER BY pr.completed_at
        '''.format(days), conn, params=(language,))
        conn.close()
        
        if df.empty or len(df) < 10:
            return {'patterns': [], 'insights': []}
        
        patterns = {
            'time_patterns': self._analyze_time_patterns(df),
            'difficulty_patterns': self._analyze_difficulty_patterns(df),
            'topic_patterns': self._analyze_topic_patterns(df),
            'performance_patterns': self._analyze_performance_patterns(df),
            'clustering_results': self._cluster_learning_sessions(df)
        }
        
        # Store patterns in database
        self._store_learning_patterns(patterns, language)
        
        return patterns
    
    def analyze_performance_trends(self, language, days) -> Dict:
        """Analyze performance trends with statistical significance"""
        conn = sqlite3.connect(self.db_path)
        
        df = pd.read_sql_query('''
            SELECT 
                DATE(pr.completed_at) as date,
                COUNT(*) as problems_count,
                AVG(pr.time_spent) as avg_time,
                AVG(CASE WHEN pr.attempts = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                p.difficulty
            FROM progress pr
            JOIN problems p ON pr.problem_id = p.id
            WHERE pr.status = 'completed' 
            AND pr.language = ?
            AND DATE(pr.completed_at) >= DATE('now', '-{} days')
            GROUP BY DATE(pr.completed_at), p.difficulty
            ORDER BY date
        '''.format(days), conn, params=(language,))
        conn.close()
        
        if df.empty:
            return {'trends': {}, 'predictions': {}}
        
        trends = {}
        
        # Analyze trends by difficulty
        for difficulty in df['difficulty'].unique():
            diff_data = df[df['difficulty'] == difficulty].copy()
            
            if len(diff_data) < 3:
                continue
            
            # Time series analysis
            diff_data['date'] = pd.to_datetime(diff_data['date'])
            diff_data = diff_data.sort_values('date')
            
            # Calculate trends
            x = np.arange(len(diff_data))
            
            # Success rate trend
            success_slope, _, success_r2, _, _ = stats.linregress(x, diff_data['success_rate'])
            
            # Time spent trend
            time_slope, _, time_r2, _, _ = stats.linregress(x, diff_data['avg_time'])
            
            trends[difficulty] = {
                'success_rate_trend': {
                    'slope': round(success_slope, 4),
                    'r_squared': round(success_r2**2, 4),
                    'direction': 'improving' if success_slope > 0 else 'declining' if success_slope < 0 else 'stable'
                },
                'time_trend': {
                    'slope': round(time_slope, 4),
                    'r_squared': round(time_r2**2, 4),
                    'direction': 'faster' if time_slope < 0 else 'slower' if time_slope > 0 else 'stable'
                },
                'current_performance': {
                    'success_rate': round(diff_data['success_rate'].iloc[-1] * 100, 2),
                    'avg_time': round(diff_data['avg_time'].iloc[-1], 2)
                }
            }
        
        return trends
    
    def identify_knowledge_gaps(self, language) -> Dict:
        """Identify knowledge gaps using failure patterns"""
        conn = sqlite3.connect(self.db_path)
        
        # Get failure data
        df = pd.read_sql_query('''
            SELECT 
                p.topic,
                p.difficulty,
                p.tags,
                pr.attempts,
                pr.time_spent,
                pr.notes
            FROM progress pr
            JOIN problems p ON pr.problem_id = p.id
            WHERE pr.language = ?
            AND (pr.attempts > 1 OR pr.status = 'in_progress')
        ''', conn, params=(language,))
        conn.close()
        
        if df.empty:
            return {'gaps': [], 'recommendations': []}
        
        gaps = {}
        
        # Analyze by topic
        for topic in df['topic'].unique():
            topic_data = df[df['topic'] == topic]
            
            avg_attempts = topic_data['attempts'].mean()
            avg_time = topic_data['time_spent'].mean()
            problem_count = len(topic_data)
            
            # Calculate difficulty score
            difficulty_weights = {'easy': 1, 'medium': 2, 'hard': 3}
            avg_difficulty = topic_data['difficulty'].map(difficulty_weights).mean()
            
            # Gap severity score
            severity_score = (avg_attempts - 1) * 0.4 + (avg_time / 30) * 0.3 + (problem_count / 10) * 0.3
            
            if severity_score > 0.5:  # Threshold for significant gaps
                gaps[topic] = {
                    'severity_score': round(severity_score, 2),
                    'avg_attempts': round(avg_attempts, 2),
                    'avg_time_spent': round(avg_time, 2),
                    'problem_count': problem_count,
                    'avg_difficulty': round(avg_difficulty, 2),
                    'recommendations': self._generate_gap_recommendations(topic, topic_data)
                }
        
        # Sort by severity
        sorted_gaps = dict(sorted(gaps.items(), key=lambda x: x[1]['severity_score'], reverse=True))
        
        return {
            'gaps': sorted_gaps,
            'priority_topics': list(sorted_gaps.keys())[:3],
            'improvement_suggestions': self._generate_improvement_suggestions(sorted_gaps)
        }
    
    def find_optimal_study_times(self, language, days) -> Dict:
        """Find optimal study times based on performance data"""
        conn = sqlite3.connect(self.db_path)
        
        df = pd.read_sql_query('''
            SELECT 
                strftime('%H', pr.completed_at) as hour,
                strftime('%w', pr.completed_at) as day_of_week,
                pr.time_spent,
                pr.attempts,
                CASE WHEN pr.attempts = 1 THEN 1 ELSE 0 END as first_attempt_success
            FROM progress pr
            JOIN problems p ON pr.problem_id = p.id
            WHERE pr.status = 'completed' 
            AND pr.language = ?
            AND DATE(pr.completed_at) >= DATE('now', '-{} days')
        '''.format(days), conn, params=(language,))
        conn.close()
        
        if df.empty:
            return {'optimal_hours': [], 'optimal_days': []}
        
        df['hour'] = df['hour'].astype(int)
        df['day_of_week'] = df['day_of_week'].astype(int)
        
        # Analyze by hour
        hourly_performance = df.groupby('hour').agg({
            'first_attempt_success': 'mean',
            'time_spent': 'mean'
        }).reset_index()
        
        # Calculate performance score (higher success rate + lower time = better)
        hourly_performance['performance_score'] = (
            hourly_performance['first_attempt_success'] * 0.7 +
            (1 / (hourly_performance['time_spent'] / df['time_spent'].mean())) * 0.3
        )
        
        optimal_hours = hourly_performance.nlargest(3, 'performance_score')['hour'].tolist()
        
        # Analyze by day of week
        daily_performance = df.groupby('day_of_week').agg({
            'first_attempt_success': 'mean',
            'time_spent': 'mean'
        }).reset_index()
        
        daily_performance['performance_score'] = (
            daily_performance['first_attempt_success'] * 0.7 +
            (1 / (daily_performance['time_spent'] / df['time_spent'].mean())) * 0.3
        )
        
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        optimal_days = daily_performance.nlargest(3, 'performance_score')['day_of_week'].tolist()
        optimal_day_names = [day_names[int(day)] for day in optimal_days]
        
        return {
            'optimal_hours': [f"{hour}:00" for hour in optimal_hours],
            'optimal_days': optimal_day_names,
            'hourly_analysis': hourly_performance.to_dict('records'),
            'daily_analysis': daily_performance.to_dict('records')
        }
    
    def analyze_retention_patterns(self, language, days) -> Dict:
        """Analyze retention patterns using spaced repetition data"""
        try:
            # Check if spaced repetition table exists
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='review_schedule'")
            if not cursor.fetchone():
                conn.close()
                return {'retention_data': 'not_available', 'message': 'Spaced repetition data not found'}
            
            # Get review data
            df = pd.read_sql_query('''
                SELECT 
                    rs.problem_id,
                    rs.current_interval,
                    rs.review_count,
                    rs.ease_factor,
                    rs.next_review_date,
                    p.topic,
                    p.difficulty
                FROM review_schedule rs
                JOIN problems p ON rs.problem_id = p.id
                WHERE rs.language = ?
            ''', conn, params=(language,))
            conn.close()
            
            if df.empty:
                return {'retention_data': 'insufficient_data'}
            
            # Analyze retention by topic
            topic_retention = df.groupby('topic').agg({
                'ease_factor': 'mean',
                'current_interval': 'mean',
                'review_count': 'mean'
            }).round(2).to_dict('index')
            
            # Analyze retention by difficulty
            difficulty_retention = df.groupby('difficulty').agg({
                'ease_factor': 'mean',
                'current_interval': 'mean',
                'review_count': 'mean'
            }).round(2).to_dict('index')
            
            # Overall retention metrics
            overall_metrics = {
                'avg_ease_factor': round(df['ease_factor'].mean(), 2),
                'avg_interval_days': round(df['current_interval'].mean(), 2),
                'avg_review_count': round(df['review_count'].mean(), 2),
                'total_problems_in_system': len(df)
            }
            
            return {
                'topic_retention': topic_retention,
                'difficulty_retention': difficulty_retention,
                'overall_metrics': overall_metrics,
                'retention_insights': self._generate_retention_insights(df)
            }
        
        except Exception as e:
            self.logger.error(f"Error analyzing retention patterns: {e}")
            return {'error': str(e)}
    
    def analyze_difficulty_calibration(self, language) -> Dict:
        """Analyze how well difficulty labels match actual performance"""
        conn = sqlite3.connect(self.db_path)
        
        df = pd.read_sql_query('''
            SELECT 
                p.difficulty,
                pr.time_spent,
                pr.attempts,
                CASE WHEN pr.attempts = 1 THEN 1 ELSE 0 END as first_attempt_success
            FROM progress pr
            JOIN problems p ON pr.problem_id = p.id
            WHERE pr.status = 'completed' 
            AND pr.language = ?
        ''', conn, params=(language,))
        conn.close()
        
        if df.empty:
            return {'calibration': 'insufficient_data'}
        
        calibration = {}
        
        for difficulty in ['easy', 'medium', 'hard']:
            diff_data = df[df['difficulty'] == difficulty]
            if diff_data.empty:
                continue
            
            calibration[difficulty] = {
                'avg_time_spent': round(diff_data['time_spent'].mean(), 2),
                'avg_attempts': round(diff_data['attempts'].mean(), 2),
                'success_rate': round(diff_data['first_attempt_success'].mean() * 100, 2),
                'problem_count': len(diff_data)
            }
        
        # Calibration insights
        insights = []
        
        if 'easy' in calibration and 'medium' in calibration:
            if calibration['easy']['success_rate'] < calibration['medium']['success_rate']:
                insights.append("Easy problems may be mislabeled - success rate lower than medium")
        
        if 'medium' in calibration and 'hard' in calibration:
            if calibration['medium']['avg_time_spent'] > calibration['hard']['avg_time_spent']:
                insights.append("Medium problems may be harder than expected - taking longer than hard problems")
        
        return {
            'calibration': calibration,
            'insights': insights,
            'calibration_score': self._calculate_calibration_score(calibration)
        }
    
    def generate_predictive_insights(self, language) -> Dict:
        """Generate predictive insights using ML models"""
        try:
            # Prepare data for predictions
            prediction_data = self._prepare_prediction_data(language)
            
            if not prediction_data or len(prediction_data) < 10:
                return {'predictions': 'insufficient_data'}
            
            predictions = {
                'next_problem_difficulty': self._predict_optimal_difficulty(prediction_data),
                'estimated_completion_time': self._predict_completion_time(prediction_data),
                'success_probability': self._predict_success_probability(prediction_data),
                'recommended_topics': self._predict_optimal_topics(prediction_data),
                'learning_plateau_risk': self._assess_plateau_risk(prediction_data)
            }
            
            return predictions
        
        except Exception as e:
            self.logger.error(f"Error generating predictive insights: {e}")
            return {'error': str(e)}
    
    def generate_comparative_analysis(self, language, days) -> Dict:
        """Generate comparative analysis against benchmarks"""
        user_stats = self._get_user_stats(language, days)
        
        # Synthetic benchmarks (in real implementation, these would come from aggregate user data)
        benchmarks = {
            'beginner': {'problems_per_day': 2, 'avg_time_minutes': 45, 'success_rate': 0.6},
            'intermediate': {'problems_per_day': 4, 'avg_time_minutes': 30, 'success_rate': 0.75},
            'advanced': {'problems_per_day': 6, 'avg_time_minutes': 20, 'success_rate': 0.85}
        }
        
        # Determine user level
        user_level = self._determine_user_level(user_stats, benchmarks)
        
        comparison = {
            'user_level': user_level,
            'user_stats': user_stats,
            'benchmark_comparison': {},
            'improvement_areas': [],
            'strengths': []
        }
        
        # Compare against appropriate benchmark
        if user_level in benchmarks:
            benchmark = benchmarks[user_level]
            
            comparison['benchmark_comparison'] = {
                'problems_per_day': {
                    'user': user_stats.get('problems_per_day', 0),
                    'benchmark': benchmark['problems_per_day'],
                    'difference_percent': ((user_stats.get('problems_per_day', 0) - benchmark['problems_per_day']) / benchmark['problems_per_day']) * 100
                },
                'avg_time_minutes': {
                    'user': user_stats.get('avg_time_minutes', 0),
                    'benchmark': benchmark['avg_time_minutes'],
                    'difference_percent': ((benchmark['avg_time_minutes'] - user_stats.get('avg_time_minutes', 0)) / benchmark['avg_time_minutes']) * 100
                },
                'success_rate': {
                    'user': user_stats.get('success_rate', 0),
                    'benchmark': benchmark['success_rate'],
                    'difference_percent': ((user_stats.get('success_rate', 0) - benchmark['success_rate']) / benchmark['success_rate']) * 100
                }
            }
        
        return comparison
    
    # Helper methods
    def _calculate_consistency(self, daily_totals):
        """Calculate consistency score"""
        if len(daily_totals) < 3:
            return 0
        
        coefficient_variation = daily_totals.std() / daily_totals.mean() if daily_totals.mean() > 0 else 1
        consistency_score = max(0, 1 - coefficient_variation)
        return round(consistency_score, 2)
    
    def _calculate_mastery_level(self, topic_data):
        """Calculate mastery level for a topic"""
        if len(topic_data) < 5:
            return 'novice'
        
        recent_performance = topic_data.tail(10)
        success_rate = recent_performance['first_attempt_success'].mean()
        avg_time = recent_performance['time_spent'].mean()
        
        # Simple mastery calculation
        if success_rate > 0.8 and avg_time < 20:
            return 'expert'
        elif success_rate > 0.6 and avg_time < 35:
            return 'proficient'
        elif success_rate > 0.4:
            return 'developing'
        else:
            return 'novice'
    
    def _calculate_overall_progression(self, df):
        """Calculate overall progression score"""
        if len(df) < 10:
            return 0
        
        # Split data into early and recent periods
        mid_point = len(df) // 2
        early_data = df.head(mid_point)
        recent_data = df.tail(mid_point)
        
        # Compare performance metrics
        early_success = early_data['first_attempt_success'].mean()
        recent_success = recent_data['first_attempt_success'].mean()
        
        early_time = early_data['time_spent'].mean()
        recent_time = recent_data['time_spent'].mean()
        
        # Calculate progression score
        success_improvement = (recent_success - early_success) * 100
        time_improvement = ((early_time - recent_time) / early_time) * 100 if early_time > 0 else 0
        
        progression_score = (success_improvement * 0.6 + time_improvement * 0.4)
        return round(max(-100, min(100, progression_score)), 2)
    
    def _store_learning_patterns(self, patterns, language):
        """Store detected patterns in database"""
        try:
            conn = sqlite3.connect(self.analytics_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO learning_patterns 
                (pattern_type, pattern_data, confidence_score)
                VALUES (?, ?, ?)
            ''', ('comprehensive', json.dumps(patterns), 0.8))
            
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Error storing learning patterns: {e}")
    
    def _analyze_time_patterns(self, df):
        """Analyze time-based learning patterns"""
        hourly_performance = df.groupby('hour').agg({
            'first_attempt_success': 'mean',
            'time_spent': 'mean'
        })
        
        best_hours = hourly_performance['first_attempt_success'].nlargest(3).index.tolist()
        return {
            'best_hours': [f"{hour}:00" for hour in best_hours],
            'hourly_data': hourly_performance.to_dict()
        }
    
    def _analyze_difficulty_patterns(self, df):
        """Analyze difficulty progression patterns"""
        return df.groupby('difficulty').agg({
            'first_attempt_success': 'mean',
            'time_spent': 'mean'
        }).to_dict()
    
    def _analyze_topic_patterns(self, df):
        """Analyze topic preference patterns"""
        return df.groupby('topic').size().to_dict()
    
    def _analyze_performance_patterns(self, df):
        """Analyze overall performance patterns"""
        return {
            'avg_success_rate': df['first_attempt_success'].mean(),
            'avg_time_spent': df['time_spent'].mean(),
            'total_problems': len(df)
        }
    
    def _cluster_learning_sessions(self, df):
        """Cluster learning sessions to identify patterns"""
        if len(df) < 10:
            return {'clusters': 'insufficient_data'}
        
        try:
            # Prepare features for clustering
            features = df[['time_spent', 'attempts', 'first_attempt_success']].values
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Perform clustering
            n_clusters = min(3, len(df) // 5)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(features_scaled)
            
            # Analyze clusters
            cluster_analysis = {}
            for i in range(n_clusters):
                cluster_data = df[clusters == i]
                cluster_analysis[f'cluster_{i}'] = {
                    'size': len(cluster_data),
                    'avg_time': round(cluster_data['time_spent'].mean(), 2),
                    'avg_success': round(cluster_data['first_attempt_success'].mean(), 2),
                    'dominant_topics': cluster_data['topic'].value_counts().head(3).to_dict()
                }
            
            return cluster_analysis
        
        except Exception as e:
            self.logger.error(f"Error in clustering: {e}")
            return {'clusters': 'error'}
    
    def _prepare_prediction_data(self, language):
        """Prepare data for ML predictions"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            df = pd.read_sql_query('''
                SELECT 
                    p.difficulty,
                    p.topic,
                    pr.time_spent,
                    pr.attempts,
                    CASE WHEN pr.attempts = 1 THEN 1 ELSE 0 END as success,
                    pr.completed_at
                FROM progress pr
                JOIN problems p ON pr.problem_id = p.id
                WHERE pr.status = 'completed' 
                AND pr.language = ?
                ORDER BY pr.completed_at DESC
                LIMIT 100
            ''', conn, params=(language,))
            conn.close()
            
            return df.to_dict('records') if not df.empty else []
        
        except Exception as e:
            self.logger.error(f"Error preparing prediction data: {e}")
            conn.close()
            return []
    
    def _predict_optimal_difficulty(self, data):
        """Predict optimal next difficulty level"""
        if not data or len(data) < 5:
            return 'easy'
        
        recent_data = data[:10]  # Last 10 problems
        success_rates = {
            'easy': sum(1 for d in recent_data if d['difficulty'] == 'easy' and d['success'] == 1) / max(1, sum(1 for d in recent_data if d['difficulty'] == 'easy')),
            'medium': sum(1 for d in recent_data if d['difficulty'] == 'medium' and d['success'] == 1) / max(1, sum(1 for d in recent_data if d['difficulty'] == 'medium')),
            'hard': sum(1 for d in recent_data if d['difficulty'] == 'hard' and d['success'] == 1) / max(1, sum(1 for d in recent_data if d['difficulty'] == 'hard'))
        }
        
        # Recommend based on performance
        if success_rates['easy'] > 0.8:
            return 'medium'
        elif success_rates['medium'] > 0.7:
            return 'hard'
        else:
            return 'easy'
    
    def _predict_completion_time(self, data):
        """Predict estimated completion time for next problem"""
        if not data:
            return 30  # Default estimate
        
        recent_times = [d['time_spent'] for d in data[:10] if d['time_spent'] > 0]
        return round(sum(recent_times) / len(recent_times), 0) if recent_times else 30
    
    def _predict_success_probability(self, data):
        """Predict probability of success on first attempt"""
        if not data:
            return 0.5
        
        recent_successes = [d['success'] for d in data[:10]]
        return round(sum(recent_successes) / len(recent_successes), 2) if recent_successes else 0.5
    
    def _predict_optimal_topics(self, data):
        """Predict optimal topics to study next"""
        if not data:
            return ['arrays']
        
        # Analyze topic performance
        topic_performance = {}
        for d in data:
            topic = d['topic']
            if topic not in topic_performance:
                topic_performance[topic] = {'successes': 0, 'total': 0, 'avg_time': 0}
            
            topic_performance[topic]['total'] += 1
            topic_performance[topic]['successes'] += d['success']
            topic_performance[topic]['avg_time'] += d['time_spent']
        
        # Calculate scores and recommend topics that need improvement
        recommendations = []
        for topic, perf in topic_performance.items():
            if perf['total'] > 0:
                success_rate = perf['successes'] / perf['total']
                if success_rate < 0.7:  # Topics needing improvement
                    recommendations.append(topic)
        
        return recommendations[:3] if recommendations else list(topic_performance.keys())[:3]
    
    def _assess_plateau_risk(self, data):
        """Assess risk of learning plateau"""
        if len(data) < 10:
            return 'insufficient_data'
        
        # Check recent performance variance
        recent_times = [d['time_spent'] for d in data[:10]]
        recent_successes = [d['success'] for d in data[:10]]
        
        time_variance = np.var(recent_times) if recent_times else 0
        success_variance = np.var(recent_successes) if recent_successes else 0
        
        # Low variance might indicate plateau
        if time_variance < 50 and success_variance < 0.1:
            return 'high'
        elif time_variance < 100 and success_variance < 0.2:
            return 'medium'
        else:
            return 'low'
    
    def _get_user_stats(self, language, days):
        """Get user statistics for comparison"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_problems,
                    AVG(pr.time_spent) as avg_time,
                    AVG(CASE WHEN pr.attempts = 1 THEN 1.0 ELSE 0.0 END) as success_rate
                FROM progress pr
                JOIN problems p ON pr.problem_id = p.id
                WHERE pr.status = 'completed' 
                AND pr.language = ?
                AND DATE(pr.completed_at) >= DATE('now', '-{} days')
            '''.format(days), (language,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                total_problems, avg_time, success_rate = result
                return {
                    'problems_per_day': round(total_problems / days, 2) if days > 0 else 0,
                    'avg_time_minutes': round(avg_time, 2) if avg_time else 0,
                    'success_rate': round(success_rate, 2) if success_rate else 0,
                    'total_problems': total_problems or 0
                }
            else:
                return {'problems_per_day': 0, 'avg_time_minutes': 0, 'success_rate': 0, 'total_problems': 0}
        
        except Exception as e:
            self.logger.error(f"Error getting user stats: {e}")
            conn.close()
            return {'problems_per_day': 0, 'avg_time_minutes': 0, 'success_rate': 0, 'total_problems': 0}
    
    def _determine_user_level(self, user_stats, benchmarks):
        """Determine user level based on stats"""
        user_score = (
            user_stats['problems_per_day'] * 0.4 +
            (60 - min(60, user_stats['avg_time_minutes'])) * 0.3 +
            user_stats['success_rate'] * 100 * 0.3
        )
        
        if user_score < 30:
            return 'beginner'
        elif user_score < 60:
            return 'intermediate'
        else:
            return 'advanced'
    
    def _generate_gap_recommendations(self, topic, topic_data):
        """Generate recommendations for knowledge gaps"""
        recommendations = []
        
        avg_attempts = topic_data['attempts'].mean()
        if avg_attempts > 2:
            recommendations.append(f"Review fundamental {topic} concepts")
        
        if topic_data['time_spent'].mean() > 40:
            recommendations.append(f"Practice more {topic} problems to improve speed")
        
        return recommendations
    
    def _generate_improvement_suggestions(self, gaps):
        """Generate overall improvement suggestions"""
        suggestions = []
        
        if len(gaps) > 3:
            suggestions.append("Focus on one topic at a time to avoid overwhelming yourself")
        
        top_gap = next(iter(gaps)) if gaps else None
        if top_gap:
            suggestions.append(f"Prioritize studying {top_gap} - it's your biggest knowledge gap")
        
        return suggestions
    
    def _generate_retention_insights(self, df):
        """Generate insights from retention data"""
        insights = []
        
        avg_ease = df['ease_factor'].mean()
        if avg_ease < 2.0:
            insights.append("Overall retention is below average - consider reviewing more frequently")
        elif avg_ease > 2.8:
            insights.append("Excellent retention! You can increase problem difficulty")
        
        return insights
    
    def _calculate_calibration_score(self, calibration):
        """Calculate how well difficulty labels are calibrated"""
        if len(calibration) < 2:
            return 0
        
        # Expected progression: easy > medium > hard (for success rate)
        # Expected progression: easy < medium < hard (for time and attempts)
        score = 0
        
        if 'easy' in calibration and 'medium' in calibration:
            if calibration['easy']['success_rate'] >= calibration['medium']['success_rate']:
                score += 1
            if calibration['easy']['avg_time_spent'] <= calibration['medium']['avg_time_spent']:
                score += 1
        
        if 'medium' in calibration and 'hard' in calibration:
            if calibration['medium']['success_rate'] >= calibration['hard']['success_rate']:
                score += 1
            if calibration['medium']['avg_time_spent'] <= calibration['hard']['avg_time_spent']:
                score += 1
        
        return round(score / 4, 2) if score > 0 else 0

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Advanced Analytics Engine")
    parser.add_argument('--language', default='python', help='Programming language to analyze')
    parser.add_argument('--days', type=int, default=30, help='Number of days to analyze')
    parser.add_argument('--generate-report', action='store_true', help='Generate comprehensive analytics report')
    
    args = parser.parse_args()
    
    analytics = AdvancedAnalytics()
    
    if args.generate_report:
        print(f"\n🔬 Advanced Analytics Report ({args.language})")
        print("=" * 60)
        
        report = analytics.get_learning_analytics(args.language, args.days)
        
        if 'error' not in report:
            print(f"\n📈 Learning Velocity: {report['learning_velocity']['velocity']:.2f} problems/day")
            print(f"🎯 Trend: {report['learning_velocity']['trend']}")
            
            if 'knowledge_gaps' in report and report['knowledge_gaps']['gaps']:
                print(f"\n⚠️  Top Knowledge Gaps:")
                for topic, gap_info in list(report['knowledge_gaps']['gaps'].items())[:3]:
                    print(f"  • {topic}: Severity {gap_info['severity_score']:.2f}")
            
            if 'optimal_study_times' in report:
                print(f"\n⏰ Optimal Study Hours: {', '.join(report['optimal_study_times']['optimal_hours'])}")
                print(f"📅 Optimal Study Days: {', '.join(report['optimal_study_times']['optimal_days'])}")
        else:
            print(f"❌ Error generating report: {report['error']}")
    else:
        print("Advanced Analytics Engine")
        print("Use --generate-report for comprehensive analysis") 