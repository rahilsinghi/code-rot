#!/usr/bin/env python3
"""
Automated Coding Practice CLI Tool
Manages problem selection, file generation, progress tracking, and git automation
"""

import json
import os
import sys
import argparse
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import random
from typing import Dict, List, Optional, Tuple

try:
    from problem_fetcher import ProblemFetcher
except ImportError:
    print("⚠️  Problem fetcher module not found. Some features may be limited.")
    ProblemFetcher = None

try:
    from progress_visualizer import ProgressVisualizer
except ImportError:
    print("⚠️  Progress visualizer module not found. Basic stats only.")
    ProgressVisualizer = None

try:
    from recommendation_engine import RecommendationEngine
except ImportError:
    print("⚠️  Recommendation engine module not found. Basic problem selection only.")
    RecommendationEngine = None

try:
    from spaced_repetition import SpacedRepetitionManager
except ImportError:
    print("⚠️  Spaced repetition module not found. Review features limited.")
    SpacedRepetitionManager = None

class PracticeManager:
    def __init__(self):
        self.root_dir = Path.cwd()
        self.db_path = self.root_dir / "practice_data" / "problems.db"
        self.config_path = self.root_dir / "practice_data" / "config.json"
        self.progress_path = self.root_dir / "practice_data" / "progress.json"
        self.ensure_directories()
        self.init_database()
        self.load_config()
    
    def ensure_directories(self):
        """Create necessary directories"""
        (self.root_dir / "practice_data").mkdir(exist_ok=True)
        
    def init_database(self):
        """Initialize SQLite database for problems and progress"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Problems table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS problems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                difficulty TEXT NOT NULL,
                topic TEXT NOT NULL,
                platform TEXT NOT NULL,
                description TEXT,
                examples TEXT,
                constraints TEXT,
                hints TEXT,
                url TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem_id INTEGER,
                language TEXT NOT NULL,
                status TEXT NOT NULL,
                file_path TEXT,
                time_spent INTEGER,
                attempts INTEGER DEFAULT 1,
                notes TEXT,
                completed_at TIMESTAMP,
                last_reviewed TIMESTAMP,
                FOREIGN KEY (problem_id) REFERENCES problems (id)
            )
        ''')
        
        # Add performance indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_problems_difficulty ON problems(difficulty)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_problems_topic ON problems(topic)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_problems_platform ON problems(platform)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_progress_status ON progress(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_progress_language ON progress(language)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_progress_completed_at ON progress(completed_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_progress_problem_language ON progress(problem_id, language)')
        
        conn.commit()
        conn.close()
        
        # Initialize spaced repetition system if available
        if SpacedRepetitionManager:
            sr_manager = SpacedRepetitionManager(self.db_path)
            sr_manager.init_review_system()
    
    def load_config(self):
        """Load or create configuration"""
        default_config = {
            "languages": ["python", "javascript", "typescript", "react"],
            "current_language": "python",
            "difficulty_preference": "mixed",
            "topic_preference": "sequential",
            "daily_goal": 3,
            "review_interval": 7,
            "auto_git": True
        }
        
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def populate_initial_problems(self):
        """Populate database with initial set of problems"""
        print("🔄 Setting up practice database...")
        
        # Check if problems already exist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM problems')
        existing_count = cursor.fetchone()[0]
        conn.close()
        
        if existing_count > 0:
            print(f"📚 Database already contains {existing_count} problems.")
            response = input("Do you want to add more problems? (y/n): ")
            if response.lower() != 'y':
                print("Setup complete - using existing problems.")
                return
        
        # Use the fetcher if available, otherwise fall back to basic problems
        if ProblemFetcher:
            print("🚀 Using enhanced problem fetcher...")
            self.fetch_problems('all', 30, force=True)
        else:
            print("📝 Adding basic problem set...")
            self._add_basic_problems()
    
    def _add_basic_problems(self):
        """Fallback method to add basic problems if fetcher is not available"""
        basic_problems = [
            {
                "title": "Two Sum",
                "slug": "two-sum",
                "difficulty": "easy",
                "topic": "arrays",
                "platform": "leetcode",
                "description": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
                "examples": "[]",
                "constraints": "",
                "hints": "",
                "url": "https://leetcode.com/problems/two-sum/",
                "tags": "array,hash-table"
            },
            {
                "title": "Reverse String",
                "slug": "reverse-string",
                "difficulty": "easy", 
                "topic": "strings",
                "platform": "leetcode",
                "description": "Write a function that reverses a string. The input string is given as an array of characters s.",
                "examples": "[]",
                "constraints": "",
                "hints": "",
                "url": "https://leetcode.com/problems/reverse-string/",
                "tags": "two-pointers,string"
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for problem in basic_problems:
            cursor.execute('''
                INSERT OR IGNORE INTO problems 
                (title, slug, difficulty, topic, platform, description, examples, constraints, hints, url, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                problem['title'], problem['slug'], problem['difficulty'],
                problem['topic'], problem['platform'], problem['description'],
                problem['examples'], problem['constraints'], problem['hints'],
                problem['url'], problem['tags']
            ))
        
        conn.commit()
        conn.close()
        print(f"✅ Added {len(basic_problems)} basic problems")
    
    def get_next_problem(self, topic=None, difficulty=None, selection_mode="sequential"):
        """Get next problem based on criteria with smart recommendations"""
        # Try to use smart recommendations if available
        if RecommendationEngine and selection_mode == "smart":
            engine = RecommendationEngine(self.db_path)
            if topic:
                recommendations = engine.get_topic_recommendations(topic, self.config["current_language"], 1)
            else:
                recommendations = engine.get_personalized_recommendations(self.config["current_language"], 1)
            
            if recommendations:
                problem = recommendations[0]
                # Add recommendation info for display
                problem['is_recommended'] = True
                problem['recommendation_reasons'] = problem.get('recommendation_reasons', [])
                return problem
        
        # Fallback to original logic
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build query based on filters
        query = '''
            SELECT p.* FROM problems p
            LEFT JOIN progress pr ON p.id = pr.problem_id AND pr.language = ?
            WHERE pr.id IS NULL OR pr.status != 'completed'
        '''
        params = [self.config["current_language"]]
        
        if topic:
            query += " AND p.topic = ?"
            params.append(topic)
        
        if difficulty:
            query += " AND p.difficulty = ?"
            params.append(difficulty)
        
        if selection_mode == "random":
            query += " ORDER BY RANDOM() LIMIT 1"
        else:
            query += " ORDER BY p.id LIMIT 1"
        
        cursor.execute(query, params)
        problem = cursor.fetchone()
        conn.close()
        
        if problem:
            return {
                "id": problem[0],
                "title": problem[1],
                "slug": problem[2],
                "difficulty": problem[3],
                "topic": problem[4],
                "platform": problem[5],
                "description": problem[6],
                "examples": problem[7],
                "constraints": problem[8],
                "hints": problem[9],
                "url": problem[10],
                "tags": problem[11],
                "is_recommended": False
            }
        return None
    
    def generate_problem_file(self, problem, language):
        """Generate problem file with template"""
        language_extensions = {
            "python": "py",
            "javascript": "js",
            "typescript": "ts",
            "react": "jsx"
        }
        
        ext = language_extensions.get(language, "py")
        timestamp = datetime.now().strftime("%Y-%m-%d")
        filename = f"{problem['slug']}_{problem['difficulty']}_{timestamp}.{ext}"
        
        # Determine directory based on platform
        platform_dir = self.root_dir / "problem-solving" / problem['platform']
        platform_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = platform_dir / filename
        
        # Generate template based on language
        template = self.get_template(problem, language)
        
        with open(file_path, 'w') as f:
            f.write(template)
        
        return file_path
    
    def get_template(self, problem, language):
        """Generate language-specific template"""
        try:
            examples = json.loads(problem['examples']) if problem['examples'] else []
        except json.JSONDecodeError:
            examples = []
        
        if language == "python":
            return f'''"""
Problem: {problem['title']}
Platform: {problem['platform'].title()}
Difficulty: {problem['difficulty'].title()}
Date: {datetime.now().strftime("%Y-%m-%d")}
URL: {problem['url']}

Problem Description:
{problem['description']}

Examples:
{chr(10).join([f"Input: {ex.get('input', '')}" + chr(10) + f"Output: {ex.get('output', '')}" + (chr(10) + f"Explanation: {ex['explanation']}" if ex.get('explanation') else '') for ex in examples])}

Constraints:
{problem['constraints']}

Tags: {problem['tags']}
"""

def solution():
    """
    Approach:
    1. [Step 1 description]
    2. [Step 2 description]
    3. [Step 3 description]
    
    Time Complexity: O(?)
    Space Complexity: O(?)
    """
    pass

def solution_optimized():
    """
    Optimized approach:
    [Describe the optimized approach]
    
    Time Complexity: O(?)
    Space Complexity: O(?)
    """
    pass

def test_solution():
    """Test cases for the solution"""
    # Test cases based on examples
{chr(10).join([f"    # Test case {i+1}: {ex.get('input', '')}" for i, ex in enumerate(examples)])}
    
    print("All test cases passed!")

if __name__ == "__main__":
    test_solution()
'''
        
        elif language == "javascript":
            return f'''/**
 * Problem: {problem['title']}
 * Platform: {problem['platform'].title()}
 * Difficulty: {problem['difficulty'].title()}
 * Date: {datetime.now().strftime("%Y-%m-%d")}
 * URL: {problem['url']}
 * 
 * Problem Description:
 * {problem['description']}
 * 
 * Examples:
{chr(10).join([f" * Input: {ex.get('input', '')}" + chr(10) + f" * Output: {ex.get('output', '')}" + (chr(10) + f" * Explanation: {ex['explanation']}" if ex.get('explanation') else '') for ex in examples])}
 * 
 * Constraints:
 * {problem['constraints']}
 * 
 * Tags: {problem['tags']}
 */

/**
 * Approach:
 * 1. [Step 1 description]
 * 2. [Step 2 description]
 * 3. [Step 3 description]
 * 
 * Time Complexity: O(?)
 * Space Complexity: O(?)
 */
function solution() {{
    // Implementation here
}}

/**
 * Optimized approach:
 * [Describe the optimized approach]
 * 
 * Time Complexity: O(?)
 * Space Complexity: O(?)
 */
function solutionOptimized() {{
    // Optimized implementation here
}}

function testSolution() {{
    // Test cases based on examples
{chr(10).join([f"    // Test case {i+1}: {ex.get('input', '')}" for i, ex in enumerate(examples)])}
    
    console.log("All test cases passed!");
}}

// Run tests
testSolution();
'''
        
        # Add TypeScript and React templates similarly
        return self.get_template(problem, "python")  # Fallback to Python
    
    def start_practice(self, topic=None, difficulty=None, language=None, selection_mode="sequential"):
        """Start a practice session"""
        if language:
            self.config["current_language"] = language
            self.save_config()
        
        problem = self.get_next_problem(topic, difficulty, selection_mode)
        if not problem:
            print("\n❌ No problems found matching your criteria.")
            print("💡 Try:")
            print("   - Removing filters")
            print("   - Running 'python3 practice.py fetch' to get more problems")
            print("   - Using 'python3 practice.py setup' to populate initial problems")
            return
        
        # Enhanced problem display
        difficulty_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
        
        print(f"\n{'='*60}")
        print(f"📝 PROBLEM: {problem['title']}")
        print(f"{'='*60}")
        print(f"{difficulty_emoji.get(problem['difficulty'], '⚪')} Difficulty: {problem['difficulty'].title()}")
        print(f"📚 Topic: {problem['topic'].title()}")
        print(f"🏆 Platform: {problem['platform'].title()}")
        
        # Show recommendation info if available
        if problem.get('is_recommended') and problem.get('recommendation_reasons'):
            print(f"🎯 Recommended: {', '.join(problem['recommendation_reasons'])}")
        
        if problem.get('url'):
            print(f"🔗 URL: {problem['url']}")
        
        print(f"\n📖 Description:")
        print(problem['description'])
        
        if problem.get('examples'):
            try:
                examples = json.loads(problem['examples'])
                if examples:
                    print(f"\n💡 Examples:")
                    for i, example in enumerate(examples, 1):
                        print(f"  Example {i}:")
                        if isinstance(example, dict):
                            for key, value in example.items():
                                print(f"    {key}: {value}")
                        else:
                            print(f"    {example}")
            except (json.JSONDecodeError, TypeError):
                if problem['examples'].strip():
                    print(f"\n💡 Examples: {problem['examples']}")
        
        if problem.get('constraints'):
            print(f"\n⚠️  Constraints:")
            print(problem['constraints'])
        
        # Generate problem file
        file_path = self.generate_problem_file(problem, self.config["current_language"])
        
        # Record session start
        self.record_session_start(problem["id"], str(file_path))
        
        print(f"\n✅ Generated solution file: {file_path}")
        print(f"\n🚀 Happy coding! Run 'python3 practice.py complete' when done.")
        
        # Auto-open disabled by default - uncomment next lines to enable
        # try:
        #     subprocess.run(["open", str(file_path)], check=False)
        # except:
        #     pass
    
    def record_session_start(self, problem_id, file_path):
        """Record the start of a practice session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO progress (problem_id, language, status, file_path, completed_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (problem_id, self.config["current_language"], "in_progress", file_path, None))
        
        conn.commit()
        conn.close()
    
    def complete_problem(self, notes=None, time_spent=None):
        """Mark current problem as completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find the most recent in-progress problem
        cursor.execute('''
            SELECT id, problem_id, file_path FROM progress 
            WHERE status = 'in_progress' AND language = ?
            ORDER BY id DESC LIMIT 1
        ''', (self.config["current_language"],))
        
        session = cursor.fetchone()
        if not session:
            print("❌ No active practice session found!")
            conn.close()
            return
        
        # Update progress
        cursor.execute('''
            UPDATE progress 
            SET status = 'completed', notes = ?, time_spent = ?, completed_at = ?
            WHERE id = ?
        ''', (notes, time_spent, datetime.now().isoformat(), session[0]))
        
        # Get problem details
        cursor.execute('SELECT title, difficulty, topic FROM problems WHERE id = ?', (session[1],))
        problem = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        print(f"✅ Completed: {problem[0]} ({problem[1]})")
        
        # Add to spaced repetition system if available
        if SpacedRepetitionManager:
            sr_manager = SpacedRepetitionManager(self.db_path)
            sr_manager.add_problem_to_review(session[1], self.config["current_language"])
        
        # Auto-commit to git if enabled
        if self.config.get("auto_git", True):
            self.git_commit(problem[0], problem[1], problem[2])
        
        # Update progress files
        self.update_progress_files()
    
    def git_commit(self, problem_title, difficulty, topic):
        """Commit completed problem to git"""
        try:
            subprocess.run(["git", "add", "."], check=True)
            commit_message = f"✅ Solved: {problem_title} ({difficulty}) - {topic}"
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            
            # Create tag for milestones
            total_completed = self.get_total_completed()
            if total_completed % 10 == 0:  # Every 10 problems
                tag_name = f"milestone-{total_completed}"
                subprocess.run(["git", "tag", tag_name], check=False)
                print(f"🏆 Milestone reached! Created tag: {tag_name}")
            
            print("📝 Changes committed to git")
        except subprocess.CalledProcessError:
            print("⚠️ Git commit failed (not a git repository?)")
    
    def get_total_completed(self):
        """Get total number of completed problems"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM progress WHERE status = "completed"')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def update_progress_files(self):
        """Update progress tracking files"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN p.difficulty = 'easy' THEN 1 ELSE 0 END) as easy,
                SUM(CASE WHEN p.difficulty = 'medium' THEN 1 ELSE 0 END) as medium,
                SUM(CASE WHEN p.difficulty = 'hard' THEN 1 ELSE 0 END) as hard
            FROM progress pr
            JOIN problems p ON pr.problem_id = p.id
            WHERE pr.status = 'completed'
        ''')
        
        stats = cursor.fetchone()
        conn.close()
        
        # Update progress tracker file
        progress_file = self.root_dir / "docs" / "learning-notes" / "progress-tracker.md"
        if progress_file.exists():
            content = progress_file.read_text()
            
            # Update statistics section
            content = content.replace("- **Total**: 0", f"- **Total**: {stats[0]}")
            content = content.replace("- **Easy**: 0", f"- **Easy**: {stats[1]}")
            content = content.replace("- **Medium**: 0", f"- **Medium**: {stats[2]}")
            content = content.replace("- **Hard**: 0", f"- **Hard**: {stats[3]}")
            
            progress_file.write_text(content)
    
    def show_stats(self):
        """Display practice statistics"""
        # Use enhanced visualizer if available, otherwise basic stats
        if ProgressVisualizer:
            visualizer = ProgressVisualizer(self.db_path)
            visualizer.print_progress_summary(30, self.config["current_language"])
            return
        
        # Fallback to basic stats
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Basic statistics
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT pr.problem_id) as completed,
                COUNT(CASE WHEN p.difficulty = 'easy' THEN 1 END) as easy,
                COUNT(CASE WHEN p.difficulty = 'medium' THEN 1 END) as medium,
                COUNT(CASE WHEN p.difficulty = 'hard' THEN 1 END) as hard,
                AVG(pr.time_spent) as avg_time
            FROM progress pr
            JOIN problems p ON pr.problem_id = p.id
            WHERE pr.status = 'completed' AND pr.language = ?
        ''', (self.config["current_language"],))
        
        stats = cursor.fetchone()
        
        print(f"\n📊 Practice Statistics ({self.config['current_language'].title()})")
        print("=" * 50)
        print(f"✅ Problems Completed: {stats[0] or 0}")
        print(f"🟢 Easy: {stats[1] or 0}")
        print(f"🟡 Medium: {stats[2] or 0}")
        print(f"🔴 Hard: {stats[3] or 0}")
        print(f"⏱️  Average Time: {stats[4]:.1f} minutes" if stats[4] else "⏱️  Average Time: N/A")
        
        conn.close()
    
    def visualize_progress(self, days=30, language=None, create_charts=False, export_report=False):
        """Generate enhanced progress visualizations and reports"""
        if not ProgressVisualizer:
            print("❌ Progress visualizer not available. Please ensure progress_visualizer.py exists.")
            return
        
        if not language:
            language = self.config["current_language"]
        
        visualizer = ProgressVisualizer(self.db_path)
        
        # Always show text summary
        visualizer.print_progress_summary(days, language)
        
        # Generate charts if requested
        if create_charts:
            print(f"\n🎨 Generating visual charts...")
            success = visualizer.create_progress_charts(days, language)
            if success:
                print(f"✅ Charts saved to practice_data/charts/")
        
        # Export report if requested
        if export_report:
            print(f"\n📄 Exporting detailed report...")
            report_file = visualizer.export_report(days, language)
            print(f"✅ Report saved to {report_file}")
    
    def get_recommendations(self, count=5, topic=None, language=None, daily=False):
        """Get smart problem recommendations"""
        if not RecommendationEngine:
            print("❌ Recommendation engine not available. Please ensure recommendation_engine.py exists.")
            return
        
        if not language:
            language = self.config["current_language"]
        
        engine = RecommendationEngine(self.db_path)
        
        try:
            if daily:
                # Get daily challenge
                recommendation = engine.get_daily_challenge(language)
                if recommendation:
                    print(f"\n🌟 Daily Challenge")
                    print("=" * 50)
                    self._display_recommendation(recommendation, 1)
                else:
                    print("❌ No daily challenge available. Try fetching more problems.")
            
            elif topic:
                # Get topic-specific recommendations
                recommendations = engine.get_topic_recommendations(topic, language, count)
                if recommendations:
                    print(f"\n🎯 {topic.title()} Recommendations")
                    print("=" * 50)
                    for i, rec in enumerate(recommendations, 1):
                        self._display_recommendation(rec, i)
                else:
                    print(f"❌ No recommendations found for topic: {topic}")
            
            else:
                # Get personalized recommendations
                recommendations = engine.get_personalized_recommendations(language, count)
                if recommendations:
                    print(f"\n🎯 Personalized Recommendations ({language.title()})")
                    print("=" * 50)
                    for i, rec in enumerate(recommendations, 1):
                        self._display_recommendation(rec, i)
                else:
                    print("❌ No recommendations available. Try solving a few problems first.")
        
        except Exception as e:
            print(f"❌ Error generating recommendations: {e}")
    
    def _display_recommendation(self, rec, index):
        """Display a single recommendation in a formatted way"""
        difficulty_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
        
        print(f"\n{index}. {rec['title']}")
        print(f"   {difficulty_emoji.get(rec['difficulty'], '⚪')} Difficulty: {rec['difficulty'].title()}")
        print(f"   📚 Topic: {rec['topic'].title()}")
        print(f"   🏆 Platform: {rec['platform'].title()}")
        print(f"   📊 Score: {rec.get('recommendation_score', 0):.2f}/1.00")
        
        if 'recommendation_reasons' in rec and rec['recommendation_reasons']:
            print(f"   💡 Why: {', '.join(rec['recommendation_reasons'])}")
        
        if rec.get('url'):
            print(f"   🔗 URL: {rec['url']}")
        
        print()  # Empty line for spacing
    
    def list_problems(self, topic=None, difficulty=None, status=None, limit=20):
        """List problems with optional filters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build query with filters
        query = '''
            SELECT p.id, p.title, p.difficulty, p.topic, p.platform,
                   COALESCE(pr.status, 'pending') as status
            FROM problems p
            LEFT JOIN progress pr ON p.id = pr.problem_id AND pr.language = ?
        '''
        params = [self.config["current_language"]]
        conditions = []
        
        if topic:
            conditions.append("p.topic = ?")
            params.append(topic)
        
        if difficulty:
            conditions.append("p.difficulty = ?")
            params.append(difficulty)
        
        if status:
            if status == 'pending':
                conditions.append("(pr.status IS NULL OR pr.status != 'completed')")
            else:
                conditions.append("pr.status = ?")
                params.append(status)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += f" ORDER BY p.id LIMIT {limit}"
        
        cursor.execute(query, params)
        problems = cursor.fetchall()
        conn.close()
        
        if not problems:
            print("No problems found matching your criteria.")
            return
        
        print(f"\n📋 Problems List (showing {len(problems)} results)")
        print("=" * 80)
        print(f"{'ID':<4} {'Title':<30} {'Difficulty':<10} {'Topic':<15} {'Platform':<10} {'Status':<10}")
        print("-" * 80)
        
        for problem in problems:
            status_emoji = "✅" if problem[5] == "completed" else "🔄" if problem[5] == "in_progress" else "⏳"
            print(f"{problem[0]:<4} {problem[1][:29]:<30} {problem[2]:<10} {problem[3]:<15} {problem[4]:<10} {status_emoji} {problem[5]:<10}")
    
    def reset_data(self, progress_only=False, reset_all=False, confirm=False):
        """Reset progress or entire database"""
        if not confirm:
            if reset_all:
                response = input("⚠️  This will delete ALL problems and progress. Are you sure? (yes/no): ")
            elif progress_only:
                response = input("⚠️  This will delete ALL progress data. Are you sure? (yes/no): ")
            else:
                print("Please specify --progress or --all flag")
                return
            
            if response.lower() != 'yes':
                print("Operation cancelled.")
                return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if reset_all:
                cursor.execute('DELETE FROM progress')
                cursor.execute('DELETE FROM problems')
                print("✅ All data reset successfully!")
            elif progress_only:
                cursor.execute('DELETE FROM progress')
                print("✅ Progress data reset successfully!")
            
            conn.commit()
        except Exception as e:
            print(f"❌ Error resetting data: {e}")
        finally:
            conn.close()
    
    def export_data(self, format_type='json', output_file=None):
        """Export problems and progress data"""
        import csv
        from datetime import datetime
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all data
        cursor.execute('''
            SELECT p.*, pr.status, pr.completed_at, pr.time_spent, pr.notes
            FROM problems p
            LEFT JOIN progress pr ON p.id = pr.problem_id AND pr.language = ?
        ''', (self.config["current_language"],))
        
        data = cursor.fetchall()
        conn.close()
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"practice_export_{timestamp}.{format_type}"
        
        try:
            if format_type == 'json':
                export_data = []
                for row in data:
                    export_data.append({
                        'id': row[0], 'title': row[1], 'slug': row[2],
                        'difficulty': row[3], 'topic': row[4], 'platform': row[5],
                        'description': row[6], 'examples': row[7], 'constraints': row[8],
                        'hints': row[9], 'url': row[10], 'tags': row[11],
                        'status': row[13], 'completed_at': row[14], 'time_spent': row[15],
                        'notes': row[16]
                    })
                
                with open(output_file, 'w') as f:
                    json.dump(export_data, f, indent=2)
            
            elif format_type == 'csv':
                with open(output_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    headers = ['id', 'title', 'slug', 'difficulty', 'topic', 'platform',
                              'description', 'examples', 'constraints', 'hints', 'url', 'tags',
                              'status', 'completed_at', 'time_spent', 'notes']
                    writer.writerow(headers)
                    writer.writerows(data)
            
            print(f"✅ Data exported to {output_file}")
        
        except Exception as e:
            print(f"❌ Error exporting data: {e}")
    
    def import_problems(self, file_path, format_type='json'):
        """Import problems from file"""
        import csv
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return
        
        try:
            problems = []
            
            if format_type == 'json':
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        problems = data
                    else:
                        problems = [data]
            
            elif format_type == 'csv':
                with open(file_path, 'r') as f:
                    reader = csv.DictReader(f)
                    problems = list(reader)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            imported_count = 0
            for problem in problems:
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO problems 
                        (title, slug, difficulty, topic, platform, description, examples, constraints, url, tags)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        problem.get('title', ''), problem.get('slug', ''),
                        problem.get('difficulty', ''), problem.get('topic', ''),
                        problem.get('platform', ''), problem.get('description', ''),
                        problem.get('examples', ''), problem.get('constraints', ''),
                        problem.get('url', ''), problem.get('tags', '')
                    ))
                    if cursor.rowcount > 0:
                        imported_count += 1
                except Exception as e:
                    print(f"⚠️  Skipped problem {problem.get('title', 'Unknown')}: {e}")
            
            conn.commit()
            conn.close()
            
            print(f"✅ Successfully imported {imported_count} problems from {file_path}")
        
        except Exception as e:
            print(f"❌ Error importing problems: {e}")
    
    def review_problems(self, days_ago=7):
        """Show problems solved N days ago for review"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate date range
        review_date = datetime.now() - timedelta(days=days_ago)
        start_date = review_date.strftime("%Y-%m-%d")
        end_date = (review_date + timedelta(days=1)).strftime("%Y-%m-%d")
        
        cursor.execute('''
            SELECT p.title, p.difficulty, p.topic, p.url, pr.completed_at, pr.notes
            FROM progress pr
            JOIN problems p ON pr.problem_id = p.id
            WHERE pr.status = 'completed' 
            AND pr.language = ?
            AND DATE(pr.completed_at) >= ? 
            AND DATE(pr.completed_at) < ?
            ORDER BY pr.completed_at
        ''', (self.config["current_language"], start_date, end_date))
        
        problems = cursor.fetchall()
        conn.close()
        
        if not problems:
            print(f"📚 No problems found from {days_ago} days ago to review.")
            return
        
        print(f"\n📚 Review: Problems solved {days_ago} days ago")
        print("=" * 60)
        
        for i, (title, difficulty, topic, url, completed_at, notes) in enumerate(problems, 1):
            print(f"\n{i}. {title} ({difficulty})")
            print(f"   Topic: {topic}")
            print(f"   URL: {url}")
            if notes:
                print(f"   Notes: {notes}")
            print(f"   Completed: {completed_at}")
        
        print(f"\n💡 Consider revisiting these {len(problems)} problems to reinforce your learning!")
    
    def fetch_problems(self, source='sample', limit=50, force=False):
        """Fetch new problems from external sources"""
        if not ProblemFetcher:
            print("❌ Problem fetcher not available. Please ensure problem_fetcher.py exists.")
            return
        
        # Check if we already have problems and force is not set
        if not force:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM problems')
            count = cursor.fetchone()[0]
            conn.close()
            
            if count > 0:
                response = input(f"📚 Database already contains {count} problems. Fetch more? (y/n): ")
                if response.lower() != 'y':
                    print("Fetch cancelled.")
                    return
        
        fetcher = ProblemFetcher()
        problems = []
        
        try:
            if source == 'sample' or source == 'all':
                sample_problems = fetcher.fetch_sample_problems()
                problems.extend(sample_problems)
            
            if source == 'leetcode' or source == 'all':
                print("🔄 Fetching from LeetCode API...")
                leetcode_problems = fetcher.fetch_leetcode_problems(limit)
                problems.extend(leetcode_problems)
            
            if not problems:
                print("❌ No problems fetched.")
                return
            
            # Insert problems into database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            inserted_count = 0
            skipped_count = 0
            
            for problem in problems:
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO problems 
                        (title, slug, difficulty, topic, platform, description, examples, constraints, hints, url, tags)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        problem['title'], problem['slug'], problem['difficulty'],
                        problem['topic'], problem['platform'], problem['description'],
                        problem['examples'], problem['constraints'], problem.get('hints', ''),
                        problem['url'], problem['tags']
                    ))
                    
                    if cursor.rowcount > 0:
                        inserted_count += 1
                    else:
                        skipped_count += 1
                        
                except Exception as e:
                    print(f"⚠️  Error inserting {problem['title']}: {e}")
                    skipped_count += 1
            
            conn.commit()
            conn.close()
            
            print(f"\n✅ Fetch complete!")
            print(f"   📥 Inserted: {inserted_count} new problems")
            print(f"   ⏭️  Skipped: {skipped_count} duplicates")
            print(f"   📊 Total in database: {inserted_count + skipped_count}")
            
        except Exception as e:
            print(f"❌ Error during fetch: {e}")
    
    def show_due_reviews(self, limit=10, language=None):
        """Show problems due for spaced repetition review"""
        if not SpacedRepetitionManager:
            print("❌ Spaced repetition system not available. Please ensure spaced_repetition.py exists.")
            return
        
        if not language:
            language = self.config["current_language"]
        
        sr_manager = SpacedRepetitionManager(self.db_path)
        due_reviews = sr_manager.get_due_reviews(language, limit)
        
        if not due_reviews:
            print(f"\n🎉 No reviews due! Great job staying on top of your studies.")
            print(f"💡 Try adding more problems to your review schedule by solving new problems.")
            return
        
        print(f"\n📚 Problems Due for Review ({language.title()})")
        print("=" * 60)
        
        for i, review in enumerate(due_reviews, 1):
            difficulty_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
            
            print(f"\n{i}. {review['title']}")
            print(f"   {difficulty_emoji.get(review['difficulty'], '⚪')} Difficulty: {review['difficulty'].title()}")
            print(f"   📚 Topic: {review['topic'].title()}")
            print(f"   🏆 Platform: {review['platform'].title()}")
            print(f"   📊 Review #: {review['review_count'] + 1}")
            print(f"   ⏰ Overdue: {review['days_overdue']} days")
            print(f"   🧠 Ease Factor: {review['ease_factor']:.2f}")
            
            if review.get('url'):
                print(f"   🔗 URL: {review['url']}")
        
        print(f"\n💡 Use 'python3 practice.py review-session' to start reviewing these problems!")
    
    def start_review_session(self, target_time=30, language=None):
        """Start a spaced repetition review session"""
        if not SpacedRepetitionManager:
            print("❌ Spaced repetition system not available. Please ensure spaced_repetition.py exists.")
            return
        
        if not language:
            language = self.config["current_language"]
        
        sr_manager = SpacedRepetitionManager(self.db_path)
        session_problems = sr_manager.suggest_review_session(language, target_time)
        
        if not session_problems:
            print(f"\n🎉 No reviews needed right now!")
            print(f"💡 All your problems are scheduled for future review. Keep solving new problems!")
            return
        
        print(f"\n⏰ {target_time}-Minute Review Session ({language.title()})")
        print("=" * 60)
        
        total_time = 0
        for i, problem in enumerate(session_problems, 1):
            difficulty_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
            
            print(f"\n{i}. {problem['title']}")
            print(f"   {difficulty_emoji.get(problem['difficulty'], '⚪')} Difficulty: {problem['difficulty'].title()}")
            print(f"   📚 Topic: {problem['topic'].title()}")
            print(f"   ⏱️  Estimated Time: {problem['estimated_time']} minutes")
            print(f"   📊 Review #: {problem['review_count'] + 1}")
            print(f"   ⏰ Overdue: {problem['days_overdue']} days")
            
            if problem.get('url'):
                print(f"   🔗 URL: {problem['url']}")
            
            total_time += problem['estimated_time']
        
        print(f"\n📊 Session Summary:")
        print(f"   🔢 Problems: {len(session_problems)}")
        print(f"   ⏱️  Total Time: {total_time} minutes")
        
        print(f"\n🚀 Instructions:")
        print(f"   1. Review each problem above")
        print(f"   2. Try to solve them from memory")
        print(f"   3. Rate your performance when done:")
        print(f"      python3 practice.py review-complete <problem_id> <performance>")
        print(f"   4. Performance ratings: excellent, good, fair, poor")
    
    def complete_review(self, problem_id, performance, time_spent=None, notes=None, language=None):
        """Complete a review and update spaced repetition schedule"""
        if not SpacedRepetitionManager:
            print("❌ Spaced repetition system not available. Please ensure spaced_repetition.py exists.")
            return
        
        if not language:
            language = self.config["current_language"]
        
        # Validate problem exists
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT title, difficulty, topic FROM problems WHERE id = ?', (problem_id,))
        problem = cursor.fetchone()
        conn.close()
        
        if not problem:
            print(f"❌ Problem with ID {problem_id} not found.")
            return
        
        sr_manager = SpacedRepetitionManager(self.db_path)
        
        try:
            result = sr_manager.record_review_performance(
                problem_id, performance, time_spent, notes, language
            )
            
            performance_emoji = {
                'excellent': '🌟',
                'good': '👍',
                'fair': '👌',
                'poor': '😅'
            }
            
            print(f"\n✅ Review Completed!")
            print(f"📚 Problem: {problem[0]} ({problem[1]})")
            print(f"{performance_emoji.get(performance, '📊')} Performance: {performance.title()}")
            
            if time_spent:
                print(f"⏱️  Time Spent: {time_spent} minutes")
            
            print(f"📅 Next Review: {result['next_review_date']}")
            print(f"⏰ Interval: {result['interval_days']} days")
            print(f"🧠 Ease Factor: {result['ease_factor']:.2f}")
            
            if notes:
                print(f"📝 Notes: {notes}")
            
            # Auto-commit if enabled
            if self.config.get("auto_git", True):
                try:
                    subprocess.run(["git", "add", "."], check=True)
                    commit_message = f"📚 Reviewed: {problem[0]} ({performance}) - {problem[2]}"
                    subprocess.run(["git", "commit", "-m", commit_message], check=True)
                    print("📝 Review committed to git")
                except subprocess.CalledProcessError:
                    pass  # Ignore git errors
        
        except ValueError as e:
            print(f"❌ Error: {e}")
        except Exception as e:
            print(f"❌ Error recording review: {e}")
    
    def show_review_stats(self, language=None, days=30):
        """Show spaced repetition statistics and insights"""
        if not SpacedRepetitionManager:
            print("❌ Spaced repetition system not available. Please ensure spaced_repetition.py exists.")
            return
        
        if not language:
            language = self.config["current_language"]
        
        sr_manager = SpacedRepetitionManager(self.db_path)
        
        # Get basic statistics
        stats = sr_manager.get_review_statistics(language, days)
        
        print(f"\n🧠 Spaced Repetition Statistics ({language.title()})")
        print("=" * 60)
        print(f"📊 Total Problems in System: {stats['total_in_system']}")
        print(f"🔴 Due for Review: {stats['due_count']}")
        print(f"📅 Upcoming (Next 7 Days): {stats['upcoming_count']}")
        print(f"🧠 Average Ease Factor: {stats['avg_ease_factor']:.2f}")
        
        # Performance breakdown
        if stats['performance_stats']:
            print(f"\n📈 Review Performance (Last {days} Days):")
            total_reviews = sum(stats['performance_stats'].values())
            
            performance_emoji = {
                'excellent': '🌟',
                'good': '👍',
                'fair': '👌',
                'poor': '😅'
            }
            
            for performance, count in stats['performance_stats'].items():
                percentage = (count / total_reviews) * 100 if total_reviews > 0 else 0
                emoji = performance_emoji.get(performance, '📊')
                print(f"   {emoji} {performance.title()}: {count} ({percentage:.1f}%)")
        
        # Get retention insights
        insights = sr_manager.get_retention_insights(language)
        
        if insights['topic_retention']:
            print(f"\n📚 Topic Retention Analysis:")
            sorted_topics = sorted(
                insights['topic_retention'].items(),
                key=lambda x: x[1]['avg_ease'],
                reverse=True
            )
            
            for topic, data in sorted_topics[:5]:  # Top 5 topics
                if data['problems'] >= 2:  # Only show topics with multiple problems
                    print(f"   📖 {topic.title()}: {data['avg_ease']:.2f} ease factor ({data['problems']} problems)")
        
        if insights['difficulty_retention']:
            print(f"\n🎯 Difficulty Retention Analysis:")
            for difficulty, data in insights['difficulty_retention'].items():
                if data['problems'] >= 2:
                    print(f"   🎯 {difficulty.title()}: {data['avg_ease']:.2f} ease factor ({data['problems']} problems)")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if stats['due_count'] > 0:
            print(f"   📚 You have {stats['due_count']} problems due for review!")
            print(f"   🚀 Run 'python3 practice.py review-session' to start reviewing")
        else:
            print(f"   🎉 All caught up with reviews! Keep solving new problems.")
        
        if stats['avg_ease_factor'] < 2.0:
            print(f"   🧠 Your average ease factor is low. Focus on understanding concepts deeply.")
        elif stats['avg_ease_factor'] > 2.8:
            print(f"   🌟 Excellent retention! Consider tackling harder problems.")

def main():
    parser = argparse.ArgumentParser(description="Automated Coding Practice CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start a practice session')
    start_parser.add_argument('--topic', help='Filter by topic')
    start_parser.add_argument('--difficulty', choices=['easy', 'medium', 'hard'], help='Filter by difficulty')
    start_parser.add_argument('--language', choices=['python', 'javascript', 'typescript', 'react'], help='Programming language')
    start_parser.add_argument('--mode', choices=['sequential', 'random', 'topic', 'smart'], default='sequential', help='Selection mode')
    
    # Complete command
    complete_parser = subparsers.add_parser('complete', help='Mark current problem as completed')
    complete_parser.add_argument('--notes', help='Add notes about the solution')
    complete_parser.add_argument('--time', type=int, help='Time spent in minutes')
    
    # Stats command
    subparsers.add_parser('stats', help='Show practice statistics')
    
    # Setup command
    subparsers.add_parser('setup', help='Initial setup and populate problems')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List problems with filters')
    list_parser.add_argument('--topic', help='Filter by topic')
    list_parser.add_argument('--difficulty', choices=['easy', 'medium', 'hard'], help='Filter by difficulty')
    list_parser.add_argument('--status', choices=['completed', 'pending', 'in_progress'], help='Filter by status')
    list_parser.add_argument('--limit', type=int, default=20, help='Limit number of results')
    
    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Reset progress or database')
    reset_parser.add_argument('--progress', action='store_true', help='Reset only progress data')
    reset_parser.add_argument('--all', action='store_true', help='Reset everything (problems + progress)')
    reset_parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export data')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format')
    export_parser.add_argument('--output', help='Output file path')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import problems from file')
    import_parser.add_argument('file', help='Input file path')
    import_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Import format')
    
    # Review command
    review_parser = subparsers.add_parser('review', help='Review previously solved problems')
    review_parser.add_argument('--days', type=int, default=7, help='Review problems from N days ago')
    
    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch new problems from external APIs')
    fetch_parser.add_argument('--source', choices=['leetcode', 'sample', 'all'], default='sample', help='Source to fetch from')
    fetch_parser.add_argument('--limit', type=int, default=50, help='Number of problems to fetch')
    fetch_parser.add_argument('--force', action='store_true', help='Force fetch even if problems exist')
    
    # Visualize command
    visualize_parser = subparsers.add_parser('visualize', help='Generate progress visualizations and reports')
    visualize_parser.add_argument('--days', type=int, default=30, help='Number of days to analyze')
    visualize_parser.add_argument('--language', default='python', help='Programming language to analyze')
    visualize_parser.add_argument('--charts', action='store_true', help='Generate visual charts (requires matplotlib)')
    visualize_parser.add_argument('--export', action='store_true', help='Export report to JSON')
    
    # Recommend command
    recommend_parser = subparsers.add_parser('recommend', help='Get smart problem recommendations')
    recommend_parser.add_argument('--count', type=int, default=5, help='Number of recommendations')
    recommend_parser.add_argument('--topic', help='Get recommendations for specific topic')
    recommend_parser.add_argument('--language', default='python', help='Programming language')
    recommend_parser.add_argument('--daily', action='store_true', help='Get daily challenge')
    
    # Review commands for spaced repetition
    review_due_parser = subparsers.add_parser('review-due', help='Show problems due for review')
    review_due_parser.add_argument('--limit', type=int, default=10, help='Maximum number of problems to show')
    review_due_parser.add_argument('--language', default='python', help='Programming language')
    
    review_session_parser = subparsers.add_parser('review-session', help='Start a spaced repetition review session')
    review_session_parser.add_argument('--time', type=int, default=30, help='Target session time in minutes')
    review_session_parser.add_argument('--language', default='python', help='Programming language')
    
    review_complete_parser = subparsers.add_parser('review-complete', help='Complete a review with performance rating')
    review_complete_parser.add_argument('problem_id', type=int, help='Problem ID that was reviewed')
    review_complete_parser.add_argument('performance', choices=['excellent', 'good', 'fair', 'poor'], help='Review performance')
    review_complete_parser.add_argument('--time', type=int, help='Time spent in minutes')
    review_complete_parser.add_argument('--notes', help='Review notes')
    review_complete_parser.add_argument('--language', default='python', help='Programming language')
    
    review_stats_parser = subparsers.add_parser('review-stats', help='Show spaced repetition statistics')
    review_stats_parser.add_argument('--language', default='python', help='Programming language')
    review_stats_parser.add_argument('--days', type=int, default=30, help='Days to analyze')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = PracticeManager()
    
    if args.command == 'setup':
        manager.populate_initial_problems()
    elif args.command == 'start':
        manager.start_practice(args.topic, args.difficulty, args.language, args.mode)
    elif args.command == 'complete':
        manager.complete_problem(args.notes, args.time)
    elif args.command == 'stats':
        manager.show_stats()
    elif args.command == 'list':
        manager.list_problems(args.topic, args.difficulty, args.status, args.limit)
    elif args.command == 'reset':
        manager.reset_data(args.progress, args.all, args.confirm)
    elif args.command == 'export':
        manager.export_data(args.format, args.output)
    elif args.command == 'import':
        manager.import_problems(args.file, args.format)
    elif args.command == 'review':
        manager.review_problems(args.days)
    elif args.command == 'fetch':
        manager.fetch_problems(args.source, args.limit, args.force)
    elif args.command == 'visualize':
        manager.visualize_progress(args.days, args.language, args.charts, args.export)
    elif args.command == 'recommend':
        manager.get_recommendations(args.count, args.topic, args.language, args.daily)
    elif args.command == 'review-due':
        manager.show_due_reviews(args.limit, args.language)
    elif args.command == 'review-session':
        manager.start_review_session(args.time, args.language)
    elif args.command == 'review-complete':
        manager.complete_review(args.problem_id, args.performance, args.time, args.notes, args.language)
    elif args.command == 'review-stats':
        manager.show_review_stats(args.language, args.days)

if __name__ == "__main__":
    main() 