#!/usr/bin/env python3
"""
Spaced Repetition System for Coding Practice
Implements intelligent review scheduling based on forgetting curves
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import math

class SpacedRepetitionManager:
    def __init__(self, db_path="practice_data/practice.db"):
        self.db_path = db_path
        
        # Spaced repetition intervals (in days)
        self.intervals = [1, 3, 7, 14, 30, 90, 180, 365]
        
        # Performance multipliers
        self.performance_multipliers = {
            'excellent': 1.3,  # Increase interval by 30%
            'good': 1.0,       # Keep same interval
            'fair': 0.7,       # Reduce interval by 30%
            'poor': 0.4        # Reduce interval by 60%
        }
    
    def init_review_system(self):
        """Initialize review tracking tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Review schedule table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS review_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem_id INTEGER,
                language TEXT NOT NULL,
                current_interval INTEGER DEFAULT 1,
                next_review_date DATE,
                review_count INTEGER DEFAULT 0,
                ease_factor REAL DEFAULT 2.5,
                last_performance TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (problem_id) REFERENCES problems (id),
                UNIQUE(problem_id, language)
            )
        ''')
        
        # Review history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS review_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem_id INTEGER,
                language TEXT NOT NULL,
                performance TEXT NOT NULL,
                time_spent INTEGER,
                review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (problem_id) REFERENCES problems (id)
            )
        ''')
        
        # Add indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_review_schedule_date ON review_schedule(next_review_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_review_schedule_problem ON review_schedule(problem_id, language)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_review_history_date ON review_history(review_date)')
        
        conn.commit()
        conn.close()
    
    def add_problem_to_review(self, problem_id, language="python"):
        """Add a newly completed problem to the review schedule"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate first review date (1 day from now)
        next_review = (datetime.now() + timedelta(days=1)).date()
        
        cursor.execute('''
            INSERT OR REPLACE INTO review_schedule 
            (problem_id, language, current_interval, next_review_date, review_count, ease_factor)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (problem_id, language, 1, next_review, 0, 2.5))
        
        conn.commit()
        conn.close()
    
    def get_due_reviews(self, language="python", limit=10) -> List[Dict]:
        """Get problems due for review"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date()
        
        cursor.execute('''
            SELECT p.id, p.title, p.difficulty, p.topic, p.platform, p.url,
                   rs.current_interval, rs.review_count, rs.ease_factor, rs.next_review_date
            FROM review_schedule rs
            JOIN problems p ON rs.problem_id = p.id
            WHERE rs.language = ? AND rs.next_review_date <= ?
            ORDER BY rs.next_review_date, rs.review_count DESC
            LIMIT ?
        ''', (language, today, limit))
        
        reviews = cursor.fetchall()
        conn.close()
        
        due_problems = []
        for review in reviews:
            due_problems.append({
                'id': review[0],
                'title': review[1],
                'difficulty': review[2],
                'topic': review[3],
                'platform': review[4],
                'url': review[5],
                'current_interval': review[6],
                'review_count': review[7],
                'ease_factor': review[8],
                'next_review_date': review[9],
                'days_overdue': (today - datetime.strptime(review[9], '%Y-%m-%d').date()).days
            })
        
        return due_problems
    
    def record_review_performance(self, problem_id, performance, time_spent=None, notes=None, language="python"):
        """Record review performance and update schedule"""
        if performance not in self.performance_multipliers:
            raise ValueError(f"Invalid performance: {performance}. Use: excellent, good, fair, poor")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Record review history
        cursor.execute('''
            INSERT INTO review_history (problem_id, language, performance, time_spent, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (problem_id, language, performance, time_spent, notes))
        
        # Get current review data
        cursor.execute('''
            SELECT current_interval, review_count, ease_factor 
            FROM review_schedule 
            WHERE problem_id = ? AND language = ?
        ''', (problem_id, language))
        
        current_data = cursor.fetchone()
        if not current_data:
            # Problem not in review system, add it
            self.add_problem_to_review(problem_id, language)
            current_interval, review_count, ease_factor = 1, 0, 2.5
        else:
            current_interval, review_count, ease_factor = current_data
        
        # Calculate new interval and ease factor
        new_interval, new_ease_factor = self._calculate_next_interval(
            current_interval, ease_factor, performance, review_count
        )
        
        # Calculate next review date
        next_review_date = (datetime.now() + timedelta(days=new_interval)).date()
        
        # Update review schedule
        cursor.execute('''
            UPDATE review_schedule 
            SET current_interval = ?, next_review_date = ?, review_count = ?, 
                ease_factor = ?, last_performance = ?
            WHERE problem_id = ? AND language = ?
        ''', (new_interval, next_review_date, review_count + 1, new_ease_factor, performance, problem_id, language))
        
        conn.commit()
        conn.close()
        
        return {
            'next_review_date': next_review_date,
            'interval_days': new_interval,
            'ease_factor': new_ease_factor
        }
    
    def _calculate_next_interval(self, current_interval, ease_factor, performance, review_count):
        """Calculate next review interval using modified SM-2 algorithm"""
        multiplier = self.performance_multipliers[performance]
        
        # Adjust ease factor based on performance
        if performance == 'excellent':
            new_ease_factor = min(3.0, ease_factor + 0.1)
        elif performance == 'good':
            new_ease_factor = ease_factor
        elif performance == 'fair':
            new_ease_factor = max(1.3, ease_factor - 0.15)
        else:  # poor
            new_ease_factor = max(1.3, ease_factor - 0.2)
        
        # Calculate new interval
        if performance in ['poor', 'fair']:
            # Reset to shorter interval for poor performance
            new_interval = max(1, int(current_interval * multiplier))
        else:
            # Use ease factor for good/excellent performance
            if review_count == 0:
                new_interval = 1
            elif review_count == 1:
                new_interval = 3
            else:
                new_interval = int(current_interval * new_ease_factor)
        
        # Cap the maximum interval
        new_interval = min(new_interval, 365)
        
        return new_interval, new_ease_factor
    
    def get_review_statistics(self, language="python", days=30) -> Dict:
        """Get review statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get total problems in review system
        cursor.execute('''
            SELECT COUNT(*) FROM review_schedule WHERE language = ?
        ''', (language,))
        total_in_system = cursor.fetchone()[0]
        
        # Get due reviews
        today = datetime.now().date()
        cursor.execute('''
            SELECT COUNT(*) FROM review_schedule 
            WHERE language = ? AND next_review_date <= ?
        ''', (language, today))
        due_count = cursor.fetchone()[0]
        
        # Get upcoming reviews (next 7 days)
        next_week = (datetime.now() + timedelta(days=7)).date()
        cursor.execute('''
            SELECT COUNT(*) FROM review_schedule 
            WHERE language = ? AND next_review_date > ? AND next_review_date <= ?
        ''', (language, today, next_week))
        upcoming_count = cursor.fetchone()[0]
        
        # Get review performance stats
        since_date = (datetime.now() - timedelta(days=days)).date()
        cursor.execute('''
            SELECT performance, COUNT(*) 
            FROM review_history 
            WHERE language = ? AND DATE(review_date) >= ?
            GROUP BY performance
        ''', (language, since_date))
        
        performance_stats = dict(cursor.fetchall())
        
        # Get average ease factor
        cursor.execute('''
            SELECT AVG(ease_factor) FROM review_schedule WHERE language = ?
        ''', (language,))
        avg_ease_factor = cursor.fetchone()[0] or 2.5
        
        conn.close()
        
        return {
            'total_in_system': total_in_system,
            'due_count': due_count,
            'upcoming_count': upcoming_count,
            'performance_stats': performance_stats,
            'avg_ease_factor': avg_ease_factor
        }
    
    def suggest_review_session(self, language="python", target_time=30) -> List[Dict]:
        """Suggest problems for a review session based on available time"""
        due_reviews = self.get_due_reviews(language, limit=50)
        
        if not due_reviews:
            return []
        
        # Estimate time per problem based on difficulty and review count
        time_estimates = {
            'easy': 10,
            'medium': 20,
            'hard': 35
        }
        
        session_problems = []
        total_time = 0
        
        # Prioritize overdue problems first
        due_reviews.sort(key=lambda x: (-x['days_overdue'], x['review_count']))
        
        for problem in due_reviews:
            # Estimate time for this problem
            base_time = time_estimates.get(problem['difficulty'], 20)
            
            # Reduce time estimate for problems reviewed multiple times
            time_reduction = min(0.5, problem['review_count'] * 0.1)
            estimated_time = int(base_time * (1 - time_reduction))
            
            if total_time + estimated_time <= target_time:
                problem['estimated_time'] = estimated_time
                session_problems.append(problem)
                total_time += estimated_time
            
            if total_time >= target_time * 0.9:  # 90% of target time
                break
        
        return session_problems
    
    def get_retention_insights(self, language="python") -> Dict:
        """Analyze retention patterns and provide insights"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get problems with multiple reviews
        cursor.execute('''
            SELECT p.topic, p.difficulty, rs.review_count, rs.ease_factor,
                   AVG(CASE WHEN rh.performance = 'excellent' THEN 4
                           WHEN rh.performance = 'good' THEN 3
                           WHEN rh.performance = 'fair' THEN 2
                           WHEN rh.performance = 'poor' THEN 1
                           ELSE 0 END) as avg_performance_score
            FROM review_schedule rs
            JOIN problems p ON rs.problem_id = p.id
            LEFT JOIN review_history rh ON rs.problem_id = rh.problem_id AND rs.language = rh.language
            WHERE rs.language = ? AND rs.review_count >= 2
            GROUP BY p.topic, p.difficulty, rs.problem_id
            HAVING COUNT(rh.id) >= 2
        ''', (language,))
        
        retention_data = cursor.fetchall()
        
        # Analyze by topic and difficulty
        topic_retention = {}
        difficulty_retention = {}
        
        for topic, difficulty, review_count, ease_factor, avg_performance in retention_data:
            # Topic analysis
            if topic not in topic_retention:
                topic_retention[topic] = {'problems': 0, 'avg_ease': 0, 'avg_performance': 0}
            
            topic_retention[topic]['problems'] += 1
            topic_retention[topic]['avg_ease'] += ease_factor
            topic_retention[topic]['avg_performance'] += avg_performance
            
            # Difficulty analysis
            if difficulty not in difficulty_retention:
                difficulty_retention[difficulty] = {'problems': 0, 'avg_ease': 0, 'avg_performance': 0}
            
            difficulty_retention[difficulty]['problems'] += 1
            difficulty_retention[difficulty]['avg_ease'] += ease_factor
            difficulty_retention[difficulty]['avg_performance'] += avg_performance
        
        # Calculate averages
        for topic_data in topic_retention.values():
            if topic_data['problems'] > 0:
                topic_data['avg_ease'] /= topic_data['problems']
                topic_data['avg_performance'] /= topic_data['problems']
        
        for diff_data in difficulty_retention.values():
            if diff_data['problems'] > 0:
                diff_data['avg_ease'] /= diff_data['problems']
                diff_data['avg_performance'] /= diff_data['problems']
        
        conn.close()
        
        return {
            'topic_retention': topic_retention,
            'difficulty_retention': difficulty_retention
        }
    
    def cleanup_old_reviews(self, days_threshold=365):
        """Remove very old review entries to keep database clean"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        
        cursor.execute('''
            DELETE FROM review_history 
            WHERE review_date < ?
        ''', (cutoff_date.isoformat(),))
        
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return deleted_count

if __name__ == "__main__":
    # Test the spaced repetition system
    sr = SpacedRepetitionManager()
    sr.init_review_system()
    
    # Example usage
    print("🧠 Spaced Repetition System Test")
    print("=" * 40)
    
    # Get review statistics
    stats = sr.get_review_statistics()
    print(f"Total problems in system: {stats['total_in_system']}")
    print(f"Due for review: {stats['due_count']}")
    print(f"Upcoming (next week): {stats['upcoming_count']}")
    print(f"Average ease factor: {stats['avg_ease_factor']:.2f}")
    
    # Get due reviews
    due_reviews = sr.get_due_reviews(limit=5)
    if due_reviews:
        print(f"\n📚 Due Reviews:")
        for i, review in enumerate(due_reviews, 1):
            print(f"{i}. {review['title']} ({review['difficulty']})")
            print(f"   Review #{review['review_count']}, {review['days_overdue']} days overdue")
    
    # Suggest review session
    session = sr.suggest_review_session(target_time=30)
    if session:
        print(f"\n⏰ 30-minute Review Session:")
        total_time = 0
        for i, problem in enumerate(session, 1):
            print(f"{i}. {problem['title']} (~{problem['estimated_time']} min)")
            total_time += problem['estimated_time']
        print(f"Total estimated time: {total_time} minutes") 