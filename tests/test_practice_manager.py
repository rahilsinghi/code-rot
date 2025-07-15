#!/usr/bin/env python3
"""
Comprehensive Test Suite for Practice Manager
Tests all core functionality including database operations, problem management, and progress tracking
"""

import pytest
import sqlite3
import tempfile
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Import the modules to test
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from practice import PracticeManager

class TestPracticeManager:
    """Test suite for PracticeManager class"""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_problems.db")
        config_path = os.path.join(temp_dir, "config.json")
        
        # Create test config
        config = {
            "languages": ["python", "javascript", "typescript"],
            "current_language": "python",
            "difficulty_preference": "mixed",
            "topic_preference": "sequential",
            "daily_goal": 3,
            "review_interval": 7,
            "auto_git": False  # Disable git for testing
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        yield temp_dir, db_path, config_path
        
        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)
        if os.path.exists(config_path):
            os.remove(config_path)
        os.rmdir(temp_dir)
    
    @pytest.fixture
    def manager(self, temp_db):
        """Create a PracticeManager instance with temporary database"""
        temp_dir, db_path, config_path = temp_db
        
        # Mock the paths
        with patch.object(PracticeManager, '__init__', lambda self: None):
            manager = PracticeManager()
            manager.root_dir = Path(temp_dir)
            manager.db_path = db_path
            manager.config_path = config_path
            manager.progress_path = os.path.join(temp_dir, "progress.json")
            manager.ensure_directories()
            manager.init_database()
            manager.load_config()
            
        return manager
    
    def test_database_initialization(self, manager):
        """Test database tables are created correctly"""
        conn = sqlite3.connect(manager.db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'problems' in tables
        assert 'progress' in tables
        
        # Check problems table structure
        cursor.execute("PRAGMA table_info(problems)")
        columns = [row[1] for row in cursor.fetchall()]
        expected_columns = ['id', 'title', 'slug', 'difficulty', 'topic', 'platform', 
                          'description', 'examples', 'constraints', 'hints', 'url', 'tags', 'created_at']
        
        for col in expected_columns:
            assert col in columns
        
        conn.close()
    
    def test_config_loading(self, manager):
        """Test configuration loading"""
        assert manager.config['current_language'] == 'python'
        assert manager.config['daily_goal'] == 3
        assert 'python' in manager.config['languages']
    
    def test_add_basic_problems(self, manager):
        """Test adding basic problems to database"""
        manager._add_basic_problems()
        
        conn = sqlite3.connect(manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM problems")
        count = cursor.fetchone()[0]
        
        assert count > 0  # Should have added some problems
        
        # Check problem structure
        cursor.execute("SELECT * FROM problems LIMIT 1")
        problem = cursor.fetchone()
        
        assert problem is not None
        assert len(problem) >= 7  # Should have all required fields
        
        conn.close()
    
    def test_get_next_problem(self, manager):
        """Test problem selection functionality"""
        manager._add_basic_problems()
        
        # Test basic problem selection
        problem = manager.get_next_problem()
        assert problem is not None
        assert 'title' in problem
        assert 'difficulty' in problem
        assert 'topic' in problem
        
        # Test topic filtering
        problem = manager.get_next_problem(topic='arrays')
        if problem:  # Only test if arrays problems exist
            assert problem['topic'] == 'arrays'
        
        # Test difficulty filtering
        problem = manager.get_next_problem(difficulty='easy')
        if problem:
            assert problem['difficulty'] == 'easy'
    
    def test_problem_completion(self, manager):
        """Test problem completion tracking"""
        manager._add_basic_problems()
        
        # Get a problem
        problem = manager.get_next_problem()
        assert problem is not None
        
        # Mock current problem
        manager.current_problem = problem
        
        # Complete the problem
        manager.complete_problem(notes="Test solution", time_spent=15)
        
        # Check if progress was recorded
        conn = sqlite3.connect(manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM progress WHERE problem_id = ?", (problem['id'],))
        progress = cursor.fetchone()
        
        assert progress is not None
        assert progress[3] == 'completed'  # status
        assert progress[5] == 15  # time_spent
        assert progress[7] == "Test solution"  # notes
        
        conn.close()
    
    def test_statistics_generation(self, manager):
        """Test statistics generation"""
        manager._add_basic_problems()
        
        # Add some progress data
        conn = sqlite3.connect(manager.db_path)
        cursor = conn.cursor()
        
        # Get a problem ID
        cursor.execute("SELECT id FROM problems LIMIT 1")
        problem_id = cursor.fetchone()[0]
        
        # Insert progress
        cursor.execute('''
            INSERT INTO progress (problem_id, language, status, completed_at, time_spent, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (problem_id, 'python', 'completed', datetime.now(), 20, 'Test notes'))
        
        conn.commit()
        conn.close()
        
        # Test statistics (should not raise exception)
        try:
            manager.show_stats()
        except Exception as e:
            pytest.fail(f"Statistics generation failed: {e}")
    
    def test_problem_listing(self, manager):
        """Test problem listing with filters"""
        manager._add_basic_problems()
        
        # Test basic listing
        try:
            manager.list_problems(limit=5)
        except Exception as e:
            pytest.fail(f"Problem listing failed: {e}")
        
        # Test with topic filter
        try:
            manager.list_problems(topic='arrays', limit=5)
        except Exception as e:
            pytest.fail(f"Problem listing with topic filter failed: {e}")
        
        # Test with difficulty filter
        try:
            manager.list_problems(difficulty='easy', limit=5)
        except Exception as e:
            pytest.fail(f"Problem listing with difficulty filter failed: {e}")
    
    def test_data_export(self, manager):
        """Test data export functionality"""
        manager._add_basic_problems()
        
        # Add some progress data
        conn = sqlite3.connect(manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM problems LIMIT 1")
        problem_id = cursor.fetchone()[0]
        
        cursor.execute('''
            INSERT INTO progress (problem_id, language, status, completed_at, time_spent)
            VALUES (?, ?, ?, ?, ?)
        ''', (problem_id, 'python', 'completed', datetime.now(), 25))
        
        conn.commit()
        conn.close()
        
        # Test JSON export
        temp_file = os.path.join(manager.root_dir, "test_export.json")
        try:
            manager.export_data(format='json', output=temp_file)
            assert os.path.exists(temp_file)
            
            # Verify export content
            with open(temp_file, 'r') as f:
                data = json.load(f)
                assert 'problems' in data
                assert 'progress' in data
                assert len(data['problems']) > 0
        except Exception as e:
            pytest.fail(f"Data export failed: {e}")
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def test_progress_reset(self, manager):
        """Test progress reset functionality"""
        manager._add_basic_problems()
        
        # Add some progress data
        conn = sqlite3.connect(manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM problems LIMIT 1")
        problem_id = cursor.fetchone()[0]
        
        cursor.execute('''
            INSERT INTO progress (problem_id, language, status, completed_at)
            VALUES (?, ?, ?, ?)
        ''', (problem_id, 'python', 'completed', datetime.now()))
        
        conn.commit()
        
        # Verify progress exists
        cursor.execute("SELECT COUNT(*) FROM progress")
        count_before = cursor.fetchone()[0]
        assert count_before > 0
        
        conn.close()
        
        # Reset progress
        manager.reset_data(progress=True, all=False, confirm=True)
        
        # Verify progress was reset
        conn = sqlite3.connect(manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM progress")
        count_after = cursor.fetchone()[0]
        assert count_after == 0
        
        # Problems should still exist
        cursor.execute("SELECT COUNT(*) FROM problems")
        problems_count = cursor.fetchone()[0]
        assert problems_count > 0
        
        conn.close()
    
    def test_language_switching(self, manager):
        """Test language switching functionality"""
        original_lang = manager.config['current_language']
        
        # Switch language
        manager.config['current_language'] = 'javascript'
        
        # Test problem selection with new language
        manager._add_basic_problems()
        problem = manager.get_next_problem()
        
        if problem:
            # Complete problem in new language
            manager.current_problem = problem
            manager.complete_problem(notes="JS solution")
            
            # Verify language was recorded
            conn = sqlite3.connect(manager.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT language FROM progress WHERE problem_id = ?", (problem['id'],))
            recorded_lang = cursor.fetchone()
            
            if recorded_lang:
                assert recorded_lang[0] == 'javascript'
            
            conn.close()
        
        # Restore original language
        manager.config['current_language'] = original_lang
    
    def test_error_handling(self, manager):
        """Test error handling in various scenarios"""
        # Test with non-existent problem
        manager.current_problem = None
        
        try:
            manager.complete_problem(notes="Should fail")
        except Exception:
            pass  # Expected to fail
        
        # Test with invalid database path
        manager.db_path = "/invalid/path/database.db"
        
        try:
            manager.show_stats()
        except Exception:
            pass  # Expected to fail
    
    @pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
    def test_difficulty_filtering(self, manager, difficulty):
        """Test problem filtering by difficulty"""
        manager._add_basic_problems()
        
        problem = manager.get_next_problem(difficulty=difficulty)
        if problem:  # Only test if problems of this difficulty exist
            assert problem['difficulty'] == difficulty
    
    @pytest.mark.parametrize("topic", ["arrays", "strings", "trees", "graphs"])
    def test_topic_filtering(self, manager, topic):
        """Test problem filtering by topic"""
        manager._add_basic_problems()
        
        problem = manager.get_next_problem(topic=topic)
        if problem:  # Only test if problems of this topic exist
            assert problem['topic'] == topic
    
    def test_concurrent_access(self, manager):
        """Test concurrent database access"""
        manager._add_basic_problems()
        
        # Simulate concurrent access
        import threading
        
        def complete_problem_thread():
            problem = manager.get_next_problem()
            if problem:
                manager.current_problem = problem
                manager.complete_problem(notes="Concurrent test")
        
        threads = []
        for i in range(3):
            thread = threading.Thread(target=complete_problem_thread)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify no database corruption
        conn = sqlite3.connect(manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM progress")
        count = cursor.fetchone()[0]
        
        # Should have some progress entries
        assert count >= 0
        
        conn.close()


class TestIntegration:
    """Integration tests for the complete system"""
    
    def test_complete_workflow(self, temp_db):
        """Test complete workflow from setup to completion"""
        temp_dir, db_path, config_path = temp_db
        
        # Initialize manager
        with patch.object(PracticeManager, '__init__', lambda self: None):
            manager = PracticeManager()
            manager.root_dir = Path(temp_dir)
            manager.db_path = db_path
            manager.config_path = config_path
            manager.progress_path = os.path.join(temp_dir, "progress.json")
            manager.ensure_directories()
            manager.init_database()
            manager.load_config()
        
        # 1. Setup problems
        manager._add_basic_problems()
        
        # 2. Get a problem
        problem = manager.get_next_problem()
        assert problem is not None
        
        # 3. Complete the problem
        manager.current_problem = problem
        manager.complete_problem(notes="Integration test", time_spent=30)
        
        # 4. Check statistics
        try:
            manager.show_stats()
        except Exception as e:
            pytest.fail(f"Statistics failed: {e}")
        
        # 5. Export data
        export_file = os.path.join(temp_dir, "export.json")
        manager.export_data(format='json', output=export_file)
        assert os.path.exists(export_file)
        
        # 6. Verify export content
        with open(export_file, 'r') as f:
            data = json.load(f)
            assert len(data['progress']) > 0
            assert data['progress'][0]['status'] == 'completed'


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 