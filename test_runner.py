#!/usr/bin/env python3
"""
Comprehensive Test Runner for Enhanced Coding Practice System
Tests all components: PWA, Analytics, API, Notifications, Sessions
"""

import os
import sys
import sqlite3
import json
import time
import requests
import threading
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import logging

# Test results tracking
test_results = {
    'passed': 0,
    'failed': 0,
    'skipped': 0,
    'details': []
}

class TestRunner:
    def __init__(self):
        self.project_root = Path.cwd()
        self.test_db_path = self.project_root / "test_data" / "test_problems.db"
        self.setup_test_environment()
        
        # Import modules for testing
        self.import_modules()
        
        print("🧪 Enhanced Coding Practice System - Comprehensive Test Suite")
        print("=" * 70)
    
    def setup_test_environment(self):
        """Setup test environment"""
        test_dir = self.project_root / "test_data"
        test_dir.mkdir(exist_ok=True)
        
        # Create test database
        if not self.test_db_path.exists():
            self.create_test_database()
    
    def import_modules(self):
        """Import all modules for testing"""
        try:
            # Add current directory to path
            sys.path.insert(0, str(self.project_root))
            
            # Import all modules
            self.modules = {}
            
            try:
                from pwa_manager import PWAManager
                self.modules['pwa'] = PWAManager
                print("✅ PWA Manager imported successfully")
            except Exception as e:
                print(f"❌ PWA Manager import failed: {e}")
                self.modules['pwa'] = None
            
            try:
                from analytics_engine import AdvancedAnalytics
                self.modules['analytics'] = AdvancedAnalytics
                print("✅ Analytics Engine imported successfully")
            except Exception as e:
                print(f"❌ Analytics Engine import failed: {e}")
                self.modules['analytics'] = None
            
            try:
                from api_layer import CodingPracticeAPI
                self.modules['api'] = CodingPracticeAPI
                print("✅ API Layer imported successfully")
            except Exception as e:
                print(f"❌ API Layer import failed: {e}")
                self.modules['api'] = None
            
            try:
                from notification_system import SmartNotificationSystem
                self.modules['notifications'] = SmartNotificationSystem
                print("✅ Notification System imported successfully")
            except Exception as e:
                print(f"❌ Notification System import failed: {e}")
                self.modules['notifications'] = None
            
            try:
                from study_session_manager import StudySessionManager
                self.modules['sessions'] = StudySessionManager
                print("✅ Study Session Manager imported successfully")
            except Exception as e:
                print(f"❌ Study Session Manager import failed: {e}")
                self.modules['sessions'] = None
            
        except Exception as e:
            print(f"❌ Module import error: {e}")
    
    def create_test_database(self):
        """Create test database with sample data"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Create problems table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS problems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                topic TEXT NOT NULL,
                platform TEXT DEFAULT 'leetcode',
                url TEXT,
                description TEXT,
                tags TEXT,
                hints TEXT,
                solution TEXT
            )
        ''')
        
        # Create progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem_id INTEGER,
                status TEXT,
                language TEXT,
                time_spent INTEGER,
                attempts INTEGER,
                notes TEXT,
                completed_at DATETIME,
                FOREIGN KEY (problem_id) REFERENCES problems (id)
            )
        ''')
        
        # Insert sample problems
        sample_problems = [
            ("Two Sum", "easy", "arrays", "leetcode", "https://leetcode.com/problems/two-sum/", "Find two numbers that add up to target", "array,hash-table", "", ""),
            ("Add Two Numbers", "medium", "linked-lists", "leetcode", "https://leetcode.com/problems/add-two-numbers/", "Add two numbers represented as linked lists", "linked-list,math", "", ""),
            ("Longest Substring", "medium", "strings", "leetcode", "https://leetcode.com/problems/longest-substring-without-repeating-characters/", "Find longest substring without repeating characters", "string,sliding-window", "", ""),
            ("Median of Two Sorted Arrays", "hard", "arrays", "leetcode", "https://leetcode.com/problems/median-of-two-sorted-arrays/", "Find median of two sorted arrays", "array,binary-search", "", ""),
            ("Valid Parentheses", "easy", "stacks", "leetcode", "https://leetcode.com/problems/valid-parentheses/", "Check if parentheses are valid", "stack,string", "", "")
        ]
        
        cursor.executemany('''
            INSERT INTO problems (title, difficulty, topic, platform, url, description, tags, hints, solution)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_problems)
        
        # Insert sample progress
        sample_progress = [
            (1, "completed", "python", 1200, 1, "Solved using hash map", datetime.now() - timedelta(days=1)),
            (2, "completed", "python", 1800, 2, "Tricky edge cases", datetime.now() - timedelta(days=2)),
            (3, "completed", "python", 2400, 1, "Sliding window approach", datetime.now() - timedelta(days=3)),
            (5, "completed", "python", 900, 1, "Stack-based solution", datetime.now() - timedelta(days=4))
        ]
        
        cursor.executemany('''
            INSERT INTO progress (problem_id, status, language, time_spent, attempts, notes, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', sample_progress)
        
        conn.commit()
        conn.close()
        print("✅ Test database created with sample data")
    
    def run_test(self, test_name, test_func, *args, **kwargs):
        """Run a single test with error handling"""
        try:
            print(f"\n🔬 Testing: {test_name}")
            result = test_func(*args, **kwargs)
            
            if result:
                print(f"✅ PASSED: {test_name}")
                test_results['passed'] += 1
                test_results['details'].append({'test': test_name, 'status': 'PASSED', 'message': 'Success'})
            else:
                print(f"❌ FAILED: {test_name}")
                test_results['failed'] += 1
                test_results['details'].append({'test': test_name, 'status': 'FAILED', 'message': 'Test returned False'})
                
        except Exception as e:
            print(f"❌ ERROR: {test_name} - {str(e)}")
            test_results['failed'] += 1
            test_results['details'].append({'test': test_name, 'status': 'ERROR', 'message': str(e)})
    
    def test_pwa_manager(self):
        """Test PWA Manager functionality"""
        if not self.modules['pwa']:
            print("⏭️  Skipping PWA tests - module not available")
            test_results['skipped'] += 1
            return False
        
        try:
            from flask import Flask
            app = Flask(__name__)
            pwa = self.modules['pwa'](app)
            
            # Test PWA status
            status = pwa.get_pwa_status()
            
            checks = [
                status.get('name') == 'Coding Practice System',
                status.get('version') == '2.0.0',
                status.get('features', {}).get('offline_support') is True,
                status.get('features', {}).get('push_notifications') is True
            ]
            
            print(f"  📱 PWA Name: {status.get('name')}")
            print(f"  📱 Version: {status.get('version')}")
            print(f"  📱 Features: {len(status.get('features', {}))}")
            
            return all(checks)
            
        except Exception as e:
            print(f"  ❌ PWA test error: {e}")
            return False
    
    def test_analytics_engine(self):
        """Test Analytics Engine functionality"""
        if not self.modules['analytics']:
            print("⏭️  Skipping Analytics tests - module not available")
            test_results['skipped'] += 1
            return False
        
        try:
            analytics = self.modules['analytics'](str(self.test_db_path))
            
            # Test learning analytics
            report = analytics.get_learning_analytics("python", 30)
            
            checks = [
                'learning_velocity' in report,
                'skill_progression' in report,
                'knowledge_gaps' in report,
                'optimal_study_times' in report,
                isinstance(report.get('learning_velocity', {}).get('velocity', 0), (int, float))
            ]
            
            print(f"  📊 Velocity: {report.get('learning_velocity', {}).get('velocity', 0):.2f} problems/day")
            print(f"  📊 Trend: {report.get('learning_velocity', {}).get('trend', 'unknown')}")
            print(f"  📊 Analytics sections: {len([k for k in report.keys() if not k.startswith('error')])}")
            
            return all(checks) and 'error' not in report
            
        except Exception as e:
            print(f"  ❌ Analytics test error: {e}")
            return False
    
    def test_api_layer(self):
        """Test API Layer functionality"""
        if not self.modules['api']:
            print("⏭️  Skipping API tests - module not available")
            test_results['skipped'] += 1
            return False
        
        try:
            # Create API instance
            api = self.modules['api'](db_path=str(self.test_db_path))
            
            # Start API server in background thread
            def run_server():
                api.app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)
            
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            # Wait for server to start
            time.sleep(2)
            
            # Test API endpoints
            base_url = "http://127.0.0.1:5001"
            
            # Test documentation endpoint
            response = requests.get(f"{base_url}/api/docs", timeout=5)
            docs_test = response.status_code == 200 and 'title' in response.json()
            
            # Test login endpoint
            login_response = requests.post(f"{base_url}/api/auth/login", 
                                         json={"username": "admin", "password": "admin123"}, 
                                         timeout=5)
            login_test = login_response.status_code == 200
            
            if login_test:
                token = login_response.json().get('token')
                headers = {'Authorization': f'Bearer {token}'}
                
                # Test authenticated endpoint
                problems_response = requests.get(f"{base_url}/api/problems", headers=headers, timeout=5)
                problems_test = problems_response.status_code == 200
            else:
                problems_test = False
            
            print(f"  🌐 API Documentation: {'✅' if docs_test else '❌'}")
            print(f"  🌐 Authentication: {'✅' if login_test else '❌'}")
            print(f"  🌐 Protected Endpoints: {'✅' if problems_test else '❌'}")
            
            return docs_test and login_test and problems_test
            
        except Exception as e:
            print(f"  ❌ API test error: {e}")
            return False
    
    def test_notification_system(self):
        """Test Notification System functionality"""
        if not self.modules['notifications']:
            print("⏭️  Skipping Notification tests - module not available")
            test_results['skipped'] += 1
            return False
        
        try:
            notifications = self.modules['notifications'](str(self.test_db_path))
            
            # Test notification creation
            from notification_system import Notification, NotificationType, NotificationPriority
            
            test_notification = Notification(
                type=NotificationType.ACHIEVEMENT,
                priority=NotificationPriority.HIGH,
                title="Test Achievement",
                message="This is a test achievement notification",
                channels=['in_app']
            )
            
            # Send notification
            send_result = notifications.send_notification(test_notification)
            
            # Test achievement checking
            achievements = notifications.check_and_award_achievements("test_user", {
                'time_spent': 300,  # 5 minutes - should trigger speed achievement
                'attempts': 1
            })
            
            # Get notifications
            user_notifications = notifications.get_notifications("test_user", limit=10)
            
            # Get achievements
            user_achievements = notifications.get_user_achievements("test_user")
            
            print(f"  🔔 Notification sent: {'✅' if send_result else '❌'}")
            print(f"  🔔 Achievement check: {'✅' if isinstance(achievements, list) else '❌'}")
            print(f"  🔔 Notifications count: {len(user_notifications)}")
            print(f"  🔔 Achievements count: {len(user_achievements)}")
            
            return send_result and isinstance(user_notifications, list)
            
        except Exception as e:
            print(f"  ❌ Notification test error: {e}")
            return False
    
    def test_study_session_manager(self):
        """Test Study Session Manager functionality"""
        if not self.modules['sessions']:
            print("⏭️  Skipping Session tests - module not available")
            test_results['skipped'] += 1
            return False
        
        try:
            sessions = self.modules['sessions'](str(self.test_db_path))
            
            # Test session creation
            session_config = {
                'type': 'problem_solving',
                'focus_mode': 'pomodoro',
                'language': 'python',
                'duration': 300,  # 5 minutes for quick test
                'goals': ['Solve 2 problems', 'Practice arrays']
            }
            
            session = sessions.start_session(session_config)
            
            # Test session status
            status = sessions.get_session_status()
            
            # Test adding problem completion
            problem_result = sessions.add_problem_completion({
                'problem_id': 1,
                'time_spent': 180,
                'language': 'python'
            })
            
            # Test session pause/resume
            pause_result = sessions.pause_session()
            time.sleep(1)
            resume_result = sessions.resume_session()
            
            # End session
            completed_session = sessions.end_session(early=True)
            
            # Test analytics
            analytics = sessions.get_productivity_analytics(7)
            
            # Test session history
            history = sessions.get_session_history(7)
            
            print(f"  ⏰ Session started: {'✅' if session else '❌'}")
            print(f"  ⏰ Status tracking: {'✅' if status['active'] else '❌'}")
            print(f"  ⏰ Problem completion: {'✅' if problem_result else '❌'}")
            print(f"  ⏰ Pause/Resume: {'✅' if pause_result and resume_result else '❌'}")
            print(f"  ⏰ Session analytics: {'✅' if 'overview' in analytics else '❌'}")
            
            return all([session, status['active'], problem_result, completed_session])
            
        except Exception as e:
            print(f"  ❌ Session test error: {e}")
            return False
    
    def test_database_integration(self):
        """Test database integration across all components"""
        try:
            # Test database exists and has data
            conn = sqlite3.connect(self.test_db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM problems")
            problem_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM progress")
            progress_count = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"  💾 Problems in DB: {problem_count}")
            print(f"  💾 Progress records: {progress_count}")
            
            return problem_count > 0 and progress_count > 0
            
        except Exception as e:
            print(f"  ❌ Database test error: {e}")
            return False
    
    def test_file_generation(self):
        """Test that all required files were created"""
        required_files = [
            'pwa_manager.py',
            'analytics_engine.py', 
            'api_layer.py',
            'notification_system.py',
            'study_session_manager.py'
        ]
        
        all_exist = True
        for file in required_files:
            file_path = self.project_root / file
            exists = file_path.exists()
            print(f"  📁 {file}: {'✅' if exists else '❌'}")
            if not exists:
                all_exist = False
        
        return all_exist
    
    def test_dependencies(self):
        """Test required dependencies"""
        dependencies = {
            'flask': 'Flask web framework',
            'sqlite3': 'Database support', 
            'requests': 'HTTP client',
            'pandas': 'Data analysis (optional)',
            'numpy': 'Numerical computing (optional)',
            'sklearn': 'Machine learning (optional)'
        }
        
        available = 0
        total = len(dependencies)
        
        for dep, desc in dependencies.items():
            try:
                __import__(dep)
                print(f"  📦 {dep}: ✅ {desc}")
                available += 1
            except ImportError:
                print(f"  📦 {dep}: ⚠️  {desc} (optional)")
        
        print(f"  📦 Dependencies: {available}/{total} available")
        return available >= 3  # Require at least core dependencies
    
    def run_all_tests(self):
        """Run all tests"""
        print(f"\n🚀 Starting comprehensive test suite at {datetime.now()}")
        print("=" * 70)
        
        # Test 1: File Generation
        self.run_test("File Generation", self.test_file_generation)
        
        # Test 2: Dependencies
        self.run_test("Dependencies Check", self.test_dependencies)
        
        # Test 3: Database Integration
        self.run_test("Database Integration", self.test_database_integration)
        
        # Test 4: PWA Manager
        self.run_test("PWA Manager", self.test_pwa_manager)
        
        # Test 5: Analytics Engine
        self.run_test("Analytics Engine", self.test_analytics_engine)
        
        # Test 6: Notification System
        self.run_test("Notification System", self.test_notification_system)
        
        # Test 7: Study Session Manager
        self.run_test("Study Session Manager", self.test_study_session_manager)
        
        # Test 8: API Layer (potentially slow, test last)
        self.run_test("API Layer", self.test_api_layer)
        
        # Print results summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 70)
        print("🧪 TEST RESULTS SUMMARY")
        print("=" * 70)
        
        total_tests = test_results['passed'] + test_results['failed'] + test_results['skipped']
        
        print(f"✅ PASSED: {test_results['passed']}")
        print(f"❌ FAILED: {test_results['failed']}")
        print(f"⏭️  SKIPPED: {test_results['skipped']}")
        print(f"📊 TOTAL: {total_tests}")
        
        if test_results['failed'] == 0:
            print("\n🎉 ALL TESTS PASSED! Your system is ready to use!")
        else:
            print(f"\n⚠️  {test_results['failed']} test(s) failed. See details above.")
        
        # Success rate
        if total_tests > 0:
            success_rate = (test_results['passed'] / (test_results['passed'] + test_results['failed'])) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
        
        # Detailed results
        print("\n📋 DETAILED RESULTS:")
        for detail in test_results['details']:
            status_emoji = "✅" if detail['status'] == 'PASSED' else "❌"
            print(f"  {status_emoji} {detail['test']}: {detail['status']}")
            if detail['status'] != 'PASSED' and detail['message'] != 'Success':
                print(f"    └─ {detail['message']}")

def main():
    """Main test runner"""
    runner = TestRunner()
    runner.run_all_tests()
    
    print(f"\n🏁 Test run completed at {datetime.now()}")
    
    # Return exit code based on results
    return 0 if test_results['failed'] == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 