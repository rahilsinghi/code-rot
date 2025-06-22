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
        
        conn.commit()
        conn.close()
    
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
        initial_problems = [
            {
                "title": "Two Sum",
                "slug": "two-sum",
                "difficulty": "easy",
                "topic": "arrays",
                "platform": "leetcode",
                "description": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
                "examples": '[{"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]", "explanation": "Because nums[0] + nums[1] == 9, we return [0, 1]."}]',
                "constraints": "2 <= nums.length <= 10^4\n-10^9 <= nums[i] <= 10^9\n-10^9 <= target <= 10^9\nOnly one valid answer exists.",
                "url": "https://leetcode.com/problems/two-sum/",
                "tags": "array,hash-table"
            },
            {
                "title": "Valid Parentheses",
                "slug": "valid-parentheses",
                "difficulty": "easy",
                "topic": "stacks",
                "platform": "leetcode",
                "description": "Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.",
                "examples": '[{"input": "s = \\"()\\""", "output": "true"}, {"input": "s = \\"()[]{}\\"", "output": "true"}, {"input": "s = \\"(]\\"", "output": "false"}]',
                "constraints": "1 <= s.length <= 10^4\ns consists of parentheses only '()[]{}'.",
                "url": "https://leetcode.com/problems/valid-parentheses/",
                "tags": "string,stack"
            },
            {
                "title": "Merge Two Sorted Lists",
                "slug": "merge-two-sorted-lists",
                "difficulty": "easy",
                "topic": "linked-lists",
                "platform": "leetcode",
                "description": "You are given the heads of two sorted linked lists list1 and list2. Merge the two lists in a one sorted list.",
                "examples": '[{"input": "list1 = [1,2,4], list2 = [1,3,4]", "output": "[1,1,2,3,4,4]"}]',
                "constraints": "The number of nodes in both lists is in the range [0, 50].\n-100 <= Node.val <= 100\nBoth list1 and list2 are sorted in non-decreasing order.",
                "url": "https://leetcode.com/problems/merge-two-sorted-lists/",
                "tags": "linked-list,recursion"
            },
            {
                "title": "Maximum Subarray",
                "slug": "maximum-subarray",
                "difficulty": "medium",
                "topic": "arrays",
                "platform": "leetcode",
                "description": "Given an integer array nums, find the contiguous subarray (containing at least one number) which has the largest sum and return its sum.",
                "examples": '[{"input": "nums = [-2,1,-3,4,-1,2,1,-5,4]", "output": "6", "explanation": "[4,-1,2,1] has the largest sum = 6."}]',
                "constraints": "1 <= nums.length <= 10^5\n-10^4 <= nums[i] <= 10^4",
                "url": "https://leetcode.com/problems/maximum-subarray/",
                "tags": "array,divide-and-conquer,dynamic-programming"
            },
            {
                "title": "Climbing Stairs",
                "slug": "climbing-stairs",
                "difficulty": "easy",
                "topic": "dynamic-programming",
                "platform": "leetcode",
                "description": "You are climbing a staircase. It takes n steps to reach the top. Each time you can either climb 1 or 2 steps. In how many distinct ways can you climb to the top?",
                "examples": '[{"input": "n = 2", "output": "2", "explanation": "There are two ways to climb to the top: 1. 1 step + 1 step 2. 2 steps"}, {"input": "n = 3", "output": "3", "explanation": "There are three ways to climb to the top: 1. 1 step + 1 step + 1 step 2. 1 step + 2 steps 3. 2 steps + 1 step"}]',
                "constraints": "1 <= n <= 45",
                "url": "https://leetcode.com/problems/climbing-stairs/",
                "tags": "math,dynamic-programming,memoization"
            }
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for problem in initial_problems:
            cursor.execute('''
                INSERT OR IGNORE INTO problems 
                (title, slug, difficulty, topic, platform, description, examples, constraints, url, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                problem["title"], problem["slug"], problem["difficulty"], 
                problem["topic"], problem["platform"], problem["description"],
                problem["examples"], problem["constraints"], problem["url"], problem["tags"]
            ))
        
        conn.commit()
        conn.close()
        print(f"✅ Populated database with {len(initial_problems)} initial problems")
    
    def get_next_problem(self, topic=None, difficulty=None, selection_mode="sequential"):
        """Get next problem based on criteria"""
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
                "tags": problem[11]
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
        examples = json.loads(problem['examples']) if problem['examples'] else []
        
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
            print("🎉 No more problems found matching your criteria!")
            return
        
        print(f"\n🚀 Starting practice session...")
        print(f"📚 Problem: {problem['title']}")
        print(f"🎯 Difficulty: {problem['difficulty'].title()}")
        print(f"📂 Topic: {problem['topic'].title()}")
        print(f"🔗 URL: {problem['url']}")
        
        # Generate problem file
        file_path = self.generate_problem_file(problem, self.config["current_language"])
        print(f"📝 Generated file: {file_path}")
        
        # Record session start
        self.record_session_start(problem["id"], str(file_path))
        
        print(f"\n💡 Happy coding! Use 'python practice.py complete' when you're done.")
        
        # Open file in default editor (optional)
        try:
            subprocess.run(["open", str(file_path)], check=False)
        except:
            pass
    
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Overall stats
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
        
        # Topic breakdown
        cursor.execute('''
            SELECT p.topic, COUNT(*) as count
            FROM progress pr
            JOIN problems p ON pr.problem_id = p.id
            WHERE pr.status = 'completed'
            GROUP BY p.topic
            ORDER BY count DESC
        ''')
        
        topics = cursor.fetchall()
        
        # Recent activity
        cursor.execute('''
            SELECT p.title, p.difficulty, pr.completed_at
            FROM progress pr
            JOIN problems p ON pr.problem_id = p.id
            WHERE pr.status = 'completed'
            ORDER BY pr.completed_at DESC
            LIMIT 5
        ''')
        
        recent = cursor.fetchall()
        conn.close()
        
        print("\n📊 Practice Statistics")
        print("=" * 50)
        print(f"Total Problems Solved: {stats[0]}")
        print(f"  Easy: {stats[1]}")
        print(f"  Medium: {stats[2]}")
        print(f"  Hard: {stats[3]}")
        
        if topics:
            print(f"\n📚 By Topic:")
            for topic, count in topics:
                print(f"  {topic.title()}: {count}")
        
        if recent:
            print(f"\n🕐 Recent Activity:")
            for title, difficulty, completed_at in recent:
                date = datetime.fromisoformat(completed_at).strftime("%Y-%m-%d")
                print(f"  {title} ({difficulty}) - {date}")

def main():
    parser = argparse.ArgumentParser(description="Automated Coding Practice CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start a practice session')
    start_parser.add_argument('--topic', help='Filter by topic')
    start_parser.add_argument('--difficulty', choices=['easy', 'medium', 'hard'], help='Filter by difficulty')
    start_parser.add_argument('--language', choices=['python', 'javascript', 'typescript', 'react'], help='Programming language')
    start_parser.add_argument('--mode', choices=['sequential', 'random', 'topic'], default='sequential', help='Selection mode')
    
    # Complete command
    complete_parser = subparsers.add_parser('complete', help='Mark current problem as completed')
    complete_parser.add_argument('--notes', help='Add notes about the solution')
    complete_parser.add_argument('--time', type=int, help='Time spent in minutes')
    
    # Stats command
    subparsers.add_parser('stats', help='Show practice statistics')
    
    # Setup command
    subparsers.add_parser('setup', help='Initial setup and populate problems')
    
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

if __name__ == "__main__":
    main() 