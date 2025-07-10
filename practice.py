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
        print(f"📂 File location: {file_path}")
        
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

if __name__ == "__main__":
    main() 