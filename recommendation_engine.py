#!/usr/bin/env python3
"""
Smart Problem Recommendation Engine
Uses machine learning-inspired algorithms to suggest optimal next problems
"""

import sqlite3
import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter

class RecommendationEngine:
    def __init__(self, db_path="practice_data/practice.db"):
        self.db_path = db_path
        
    def get_personalized_recommendations(self, language="python", count=5) -> List[Dict]:
        """Get personalized problem recommendations based on user's progress"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Analyze user's performance patterns
        user_profile = self._analyze_user_profile(cursor, language)
        
        # Get candidate problems
        candidates = self._get_candidate_problems(cursor, language, user_profile)
        
        # Score and rank problems
        scored_problems = self._score_problems(candidates, user_profile)
        
        # Return top recommendations
        recommendations = sorted(scored_problems, key=lambda x: x['recommendation_score'], reverse=True)[:count]
        
        conn.close()
        return recommendations
    
    def _analyze_user_profile(self, cursor, language) -> Dict:
        """Analyze user's solving patterns and performance"""
        profile = {
            'total_solved': 0,
            'difficulty_distribution': {'easy': 0, 'medium': 0, 'hard': 0},
            'topic_mastery': {},
            'average_time': 0,
            'success_rate': 1.0,
            'recent_activity': [],
            'learning_velocity': 0,
            'preferred_difficulty': 'easy',
            'weak_topics': [],
            'strong_topics': []
        }
        
        # Get basic stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                AVG(time_spent) as avg_time,
                COUNT(CASE WHEN p.difficulty = 'easy' THEN 1 END) as easy,
                COUNT(CASE WHEN p.difficulty = 'medium' THEN 1 END) as medium,
                COUNT(CASE WHEN p.difficulty = 'hard' THEN 1 END) as hard
            FROM progress pr
            JOIN problems p ON pr.problem_id = p.id
            WHERE pr.status = 'completed' AND pr.language = ?
        ''', (language,))
        
        stats = cursor.fetchone()
        if stats and stats[0] > 0:
            profile['total_solved'] = stats[0]
            profile['average_time'] = stats[1] or 0
            profile['difficulty_distribution'] = {
                'easy': stats[2],
                'medium': stats[3], 
                'hard': stats[4]
            }
        
        # Analyze topic performance
        cursor.execute('''
            SELECT 
                p.topic,
                COUNT(*) as solved_count,
                AVG(pr.time_spent) as avg_time,
                AVG(pr.attempts) as avg_attempts
            FROM progress pr
            JOIN problems p ON pr.problem_id = p.id
            WHERE pr.status = 'completed' AND pr.language = ?
            GROUP BY p.topic
        ''', (language,))
        
        topic_stats = cursor.fetchall()
        for topic, count, avg_time, avg_attempts in topic_stats:
            # Calculate mastery score (0-1) based on problems solved and performance
            mastery_score = min(1.0, count / 10.0)  # 10 problems = full mastery
            if avg_time and avg_attempts:
                # Adjust for efficiency (lower time and attempts = higher mastery)
                efficiency_factor = max(0.5, 1.0 - (avg_attempts - 1) * 0.1)
                mastery_score *= efficiency_factor
            
            profile['topic_mastery'][topic] = mastery_score
        
        # Determine preferred difficulty based on recent success
        cursor.execute('''
            SELECT p.difficulty, COUNT(*) as count
            FROM progress pr
            JOIN problems p ON pr.problem_id = p.id
            WHERE pr.status = 'completed' AND pr.language = ?
            AND DATE(pr.completed_at) >= DATE('now', '-30 days')
            GROUP BY p.difficulty
            ORDER BY count DESC
        ''', (language,))
        
        recent_difficulty = cursor.fetchall()
        if recent_difficulty:
            profile['preferred_difficulty'] = recent_difficulty[0][0]
        
        # Calculate learning velocity (problems per week)
        cursor.execute('''
            SELECT COUNT(*) as count
            FROM progress pr
            WHERE pr.status = 'completed' AND pr.language = ?
            AND DATE(pr.completed_at) >= DATE('now', '-7 days')
        ''', (language,))
        
        recent_count = cursor.fetchone()[0]
        profile['learning_velocity'] = recent_count
        
        # Identify weak and strong topics
        if profile['topic_mastery']:
            sorted_topics = sorted(profile['topic_mastery'].items(), key=lambda x: x[1])
            profile['weak_topics'] = [topic for topic, score in sorted_topics[:3] if score < 0.7]
            profile['strong_topics'] = [topic for topic, score in sorted_topics[-3:] if score > 0.8]
        
        return profile
    
    def _get_candidate_problems(self, cursor, language, user_profile) -> List[Dict]:
        """Get candidate problems for recommendation"""
        # Get unsolved problems
        cursor.execute('''
            SELECT p.* FROM problems p
            LEFT JOIN progress pr ON p.id = pr.problem_id AND pr.language = ?
            WHERE pr.id IS NULL OR pr.status != 'completed'
        ''', (language,))
        
        problems = cursor.fetchall()
        
        candidates = []
        for problem in problems:
            candidates.append({
                'id': problem[0],
                'title': problem[1],
                'slug': problem[2],
                'difficulty': problem[3],
                'topic': problem[4],
                'platform': problem[5],
                'description': problem[6],
                'examples': problem[7],
                'constraints': problem[8],
                'hints': problem[9],
                'url': problem[10],
                'tags': problem[11]
            })
        
        return candidates
    
    def _score_problems(self, candidates, user_profile) -> List[Dict]:
        """Score problems based on user profile and learning objectives"""
        scored_problems = []
        
        for problem in candidates:
            score = self._calculate_recommendation_score(problem, user_profile)
            problem['recommendation_score'] = score
            problem['recommendation_reasons'] = self._get_recommendation_reasons(problem, user_profile, score)
            scored_problems.append(problem)
        
        return scored_problems
    
    def _calculate_recommendation_score(self, problem, user_profile) -> float:
        """Calculate recommendation score for a problem"""
        score = 0.0
        
        # 1. Difficulty progression score (30% weight)
        difficulty_score = self._get_difficulty_score(problem['difficulty'], user_profile)
        score += difficulty_score * 0.3
        
        # 2. Topic relevance score (25% weight)
        topic_score = self._get_topic_score(problem['topic'], user_profile)
        score += topic_score * 0.25
        
        # 3. Learning path score (20% weight)
        learning_score = self._get_learning_path_score(problem, user_profile)
        score += learning_score * 0.2
        
        # 4. Variety score (15% weight)
        variety_score = self._get_variety_score(problem, user_profile)
        score += variety_score * 0.15
        
        # 5. Platform preference score (10% weight)
        platform_score = self._get_platform_score(problem['platform'], user_profile)
        score += platform_score * 0.1
        
        return min(1.0, score)
    
    def _get_difficulty_score(self, difficulty, user_profile) -> float:
        """Score based on optimal difficulty progression"""
        total_solved = user_profile['total_solved']
        
        # Beginner phase (0-20 problems): Focus on easy
        if total_solved < 20:
            return 1.0 if difficulty == 'easy' else 0.3
        
        # Intermediate phase (20-100 problems): Mix of easy/medium
        elif total_solved < 100:
            if difficulty == 'easy':
                return 0.7
            elif difficulty == 'medium':
                return 1.0
            else:
                return 0.4
        
        # Advanced phase (100+ problems): All difficulties
        else:
            if difficulty == 'easy':
                return 0.5
            elif difficulty == 'medium':
                return 0.9
            else:
                return 1.0
    
    def _get_topic_score(self, topic, user_profile) -> float:
        """Score based on topic mastery and learning needs"""
        mastery = user_profile['topic_mastery'].get(topic, 0.0)
        
        # Prioritize weak topics for improvement
        if topic in user_profile['weak_topics']:
            return 1.0
        
        # Moderate score for new topics
        if mastery == 0.0:
            return 0.8
        
        # Lower score for mastered topics (but not zero for reinforcement)
        if mastery > 0.8:
            return 0.4
        
        # Good score for partially learned topics
        return 0.7
    
    def _get_learning_path_score(self, problem, user_profile) -> float:
        """Score based on optimal learning path"""
        # Fundamental topics should be prioritized early
        fundamental_topics = ['arrays', 'strings', 'linked-lists', 'stacks']
        advanced_topics = ['dynamic-programming', 'graphs', 'backtracking']
        
        total_solved = user_profile['total_solved']
        
        if total_solved < 30 and problem['topic'] in fundamental_topics:
            return 1.0
        elif total_solved >= 50 and problem['topic'] in advanced_topics:
            return 1.0
        else:
            return 0.6
    
    def _get_variety_score(self, problem, user_profile) -> float:
        """Score to encourage variety in problem solving"""
        # Encourage trying different platforms and topics
        return 0.8  # Neutral variety score
    
    def _get_platform_score(self, platform, user_profile) -> float:
        """Score based on platform preference"""
        # Slight preference for LeetCode due to interview relevance
        if platform.lower() == 'leetcode':
            return 1.0
        else:
            return 0.8
    
    def _get_recommendation_reasons(self, problem, user_profile, score) -> List[str]:
        """Generate human-readable reasons for recommendation"""
        reasons = []
        
        # Difficulty-based reasons
        if problem['difficulty'] == 'easy' and user_profile['total_solved'] < 20:
            reasons.append("🎯 Perfect for building fundamentals")
        elif problem['difficulty'] == 'medium' and 20 <= user_profile['total_solved'] < 100:
            reasons.append("📈 Good challenge for your current level")
        elif problem['difficulty'] == 'hard' and user_profile['total_solved'] >= 100:
            reasons.append("🚀 Advanced problem to push your limits")
        
        # Topic-based reasons
        if problem['topic'] in user_profile['weak_topics']:
            reasons.append(f"💪 Strengthen your {problem['topic']} skills")
        elif problem['topic'] not in user_profile['topic_mastery']:
            reasons.append(f"🌟 Explore new topic: {problem['topic']}")
        
        # Learning path reasons
        fundamental_topics = ['arrays', 'strings', 'linked-lists']
        if problem['topic'] in fundamental_topics and user_profile['total_solved'] < 30:
            reasons.append("🏗️ Essential foundation topic")
        
        # High score reasons
        if score > 0.8:
            reasons.append("⭐ Highly recommended for you")
        
        return reasons or ["📚 Good practice problem"]
    
    def get_daily_challenge(self, language="python") -> Optional[Dict]:
        """Get a single daily challenge problem"""
        recommendations = self.get_personalized_recommendations(language, 1)
        return recommendations[0] if recommendations else None
    
    def get_topic_recommendations(self, topic, language="python", count=3) -> List[Dict]:
        """Get recommendations for a specific topic"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        user_profile = self._analyze_user_profile(cursor, language)
        
        # Get problems from specific topic
        cursor.execute('''
            SELECT p.* FROM problems p
            LEFT JOIN progress pr ON p.id = pr.problem_id AND pr.language = ?
            WHERE p.topic = ? AND (pr.id IS NULL OR pr.status != 'completed')
        ''', (language, topic))
        
        problems = cursor.fetchall()
        
        candidates = []
        for problem in problems:
            candidates.append({
                'id': problem[0],
                'title': problem[1],
                'slug': problem[2],
                'difficulty': problem[3],
                'topic': problem[4],
                'platform': problem[5],
                'description': problem[6],
                'examples': problem[7],
                'constraints': problem[8],
                'hints': problem[9],
                'url': problem[10],
                'tags': problem[11]
            })
        
        # Score and return top recommendations
        scored_problems = self._score_problems(candidates, user_profile)
        recommendations = sorted(scored_problems, key=lambda x: x['recommendation_score'], reverse=True)[:count]
        
        conn.close()
        return recommendations

if __name__ == "__main__":
    engine = RecommendationEngine()
    
    # Test recommendations
    recommendations = engine.get_personalized_recommendations("python", 5)
    
    print("🎯 Personalized Recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['title']} ({rec['difficulty']})")
        print(f"   Topic: {rec['topic']}")
        print(f"   Score: {rec['recommendation_score']:.2f}")
        print(f"   Reasons: {', '.join(rec['recommendation_reasons'])}")
    
    # Test daily challenge
    daily = engine.get_daily_challenge("python")
    if daily:
        print(f"\n🌟 Daily Challenge: {daily['title']} ({daily['difficulty']})")
        print(f"   {', '.join(daily['recommendation_reasons'])}") 