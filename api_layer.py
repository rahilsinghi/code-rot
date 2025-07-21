#!/usr/bin/env python3
"""
REST API Layer for Coding Practice System
Comprehensive endpoints for all functionality with authentication and rate limiting
"""

import os
import sqlite3
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from functools import wraps
import time

from flask import Flask, request, jsonify, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

try:
    from practice import PracticeManager
    from analytics_engine import AdvancedAnalytics
    from spaced_repetition import SpacedRepetitionManager
    from recommendation_engine import RecommendationEngine
    from progress_visualizer import ProgressVisualizer
    from git_automation import GitAutomation
    from performance_monitor import PerformanceMonitor
    from pwa_manager import PWAManager
except ImportError:
    print("⚠️  Some modules not found. API will have limited functionality.")

class CodingPracticeAPI:
    def __init__(self, db_path="practice_data/problems.db", secret_key=None):
        self.app = Flask(__name__)
        self.db_path = Path(db_path)
        self.api_db_path = self.db_path.parent / "api.db"
        
        # Configuration
        self.app.config['SECRET_KEY'] = secret_key or secrets.token_hex(32)
        self.app.config['JWT_SECRET_KEY'] = secrets.token_hex(32)
        self.app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
        
        # Setup CORS
        CORS(self.app, resources={r"/api/*": {"origins": "*"}})
        
        # Setup rate limiter
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=["1000 per hour", "100 per minute"],
            storage_uri="memory://"
        )
        
        # Setup logging
        self.setup_logging()
        
        # Initialize databases
        self.init_api_database()
        
        # Initialize managers
        self.practice_manager = None
        self.analytics = None
        self.spaced_repetition = None
        self.recommendation_engine = None
        self.progress_visualizer = None
        self.git_automation = None
        self.performance_monitor = None
        
        self._init_managers()
        
        # Register routes
        self.register_routes()
        
        logging.info("Coding Practice API initialized")
    
    def setup_logging(self):
        """Setup API logging"""
        log_dir = self.db_path.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'api.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def init_api_database(self):
        """Initialize API-specific database tables"""
        conn = sqlite3.connect(self.api_db_path)
        cursor = conn.cursor()
        
        # API users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                api_key TEXT UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                is_active BOOLEAN DEFAULT 1,
                permissions TEXT DEFAULT '["read"]'
            )
        ''')
        
        # API usage tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                endpoint TEXT,
                method TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                response_code INTEGER,
                response_time REAL,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES api_users (id)
            )
        ''')
        
        # API tokens table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                token_hash TEXT,
                expires_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES api_users (id)
            )
        ''')
        
        # Webhook configurations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webhooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                url TEXT NOT NULL,
                events TEXT NOT NULL,
                secret TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES api_users (id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_tokens_user ON api_tokens(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_webhooks_user ON webhooks(user_id)')
        
        conn.commit()
        conn.close()
        
        # Create default admin user if not exists
        self._create_default_admin()
    
    def _init_managers(self):
        """Initialize all system managers"""
        try:
            self.practice_manager = PracticeManager()
            self.analytics = AdvancedAnalytics(str(self.db_path))
            self.spaced_repetition = SpacedRepetitionManager(str(self.db_path))
            self.recommendation_engine = RecommendationEngine(str(self.db_path))
            self.progress_visualizer = ProgressVisualizer(str(self.db_path))
            self.git_automation = GitAutomation()
            self.performance_monitor = PerformanceMonitor(str(self.db_path))
        except Exception as e:
            self.logger.error(f"Error initializing managers: {e}")
    
    def _create_default_admin(self):
        """Create default admin user"""
        conn = sqlite3.connect(self.api_db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM api_users WHERE username = ?', ('admin',))
        if not cursor.fetchone():
            api_key = secrets.token_hex(32)
            password_hash = generate_password_hash('admin123')
            
            cursor.execute('''
                INSERT INTO api_users (username, email, password_hash, api_key, permissions)
                VALUES (?, ?, ?, ?, ?)
            ''', ('admin', 'admin@localhost', password_hash, api_key, '["read", "write", "admin"]'))
            
            conn.commit()
            self.logger.info(f"Default admin user created with API key: {api_key}")
        
        conn.close()
    
    def require_auth(self, permissions=None):
        """Authentication decorator"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                auth_header = request.headers.get('Authorization')
                api_key = request.headers.get('X-API-Key')
                
                user = None
                
                if auth_header and auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
                    user = self._verify_jwt_token(token)
                elif api_key:
                    user = self._verify_api_key(api_key)
                
                if not user:
                    return jsonify({'error': 'Authentication required'}), 401
                
                if permissions and not self._check_permissions(user, permissions):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                g.current_user = user
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def track_usage(self, f):
        """Usage tracking decorator"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            user_id = getattr(g, 'current_user', {}).get('id', None)
            
            try:
                response = f(*args, **kwargs)
                status_code = getattr(response, 'status_code', 200) if hasattr(response, 'status_code') else 200
            except Exception as e:
                status_code = 500
                response = jsonify({'error': str(e)}), 500
            
            # Track usage
            self._log_api_usage(
                user_id=user_id,
                endpoint=request.endpoint,
                method=request.method,
                status_code=status_code,
                response_time=time.time() - start_time,
                ip_address=get_remote_address(),
                user_agent=request.headers.get('User-Agent', '')
            )
            
            return response
        return decorated_function
    
    def register_routes(self):
        """Register all API routes"""
        
        # Authentication routes
        @self.app.route('/api/auth/login', methods=['POST'])
        @self.limiter.limit("10 per minute")
        @self.track_usage
        def login():
            """User login endpoint"""
            data = request.get_json()
            if not data or not data.get('username') or not data.get('password'):
                return jsonify({'error': 'Username and password required'}), 400
            
            user = self._authenticate_user(data['username'], data['password'])
            if user:
                token = self._generate_jwt_token(user)
                return jsonify({
                    'token': token,
                    'user': {
                        'id': user['id'],
                        'username': user['username'],
                        'permissions': json.loads(user['permissions'])
                    }
                })
            else:
                return jsonify({'error': 'Invalid credentials'}), 401
        
        @self.app.route('/api/auth/register', methods=['POST'])
        @self.limiter.limit("5 per minute")
        @self.track_usage
        def register():
            """User registration endpoint"""
            data = request.get_json()
            required_fields = ['username', 'password', 'email']
            
            if not data or not all(field in data for field in required_fields):
                return jsonify({'error': 'Username, password, and email required'}), 400
            
            try:
                user_id = self._create_user(
                    data['username'], 
                    data['password'], 
                    data['email']
                )
                return jsonify({'user_id': user_id, 'message': 'User created successfully'}), 201
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        
        # Problem management routes
        @self.app.route('/api/problems', methods=['GET'])
        @self.require_auth(['read'])
        @self.track_usage
        def get_problems():
            """Get all problems with filtering"""
            language = request.args.get('language', 'python')
            difficulty = request.args.get('difficulty')
            topic = request.args.get('topic')
            platform = request.args.get('platform')
            limit = request.args.get('limit', 50, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            try:
                problems = self._get_problems_filtered(
                    language=language,
                    difficulty=difficulty,
                    topic=topic,
                    platform=platform,
                    limit=limit,
                    offset=offset
                )
                return jsonify({'problems': problems})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/problems/<int:problem_id>', methods=['GET'])
        @self.require_auth(['read'])
        @self.track_usage
        def get_problem(problem_id):
            """Get specific problem details"""
            try:
                problem = self._get_problem_by_id(problem_id)
                if problem:
                    return jsonify({'problem': problem})
                else:
                    return jsonify({'error': 'Problem not found'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/problems', methods=['POST'])
        @self.require_auth(['write'])
        @self.track_usage
        def add_problem():
            """Add new problem"""
            data = request.get_json()
            required_fields = ['title', 'difficulty', 'topic', 'description']
            
            if not data or not all(field in data for field in required_fields):
                return jsonify({'error': 'Required fields missing'}), 400
            
            try:
                problem_id = self._add_problem(data)
                return jsonify({'problem_id': problem_id, 'message': 'Problem added successfully'}), 201
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # Progress tracking routes
        @self.app.route('/api/progress', methods=['GET'])
        @self.require_auth(['read'])
        @self.track_usage
        def get_progress():
            """Get user progress"""
            language = request.args.get('language', 'python')
            days = request.args.get('days', 30, type=int)
            
            try:
                if self.practice_manager:
                    stats = self.practice_manager.get_stats(language)
                    return jsonify({'progress': stats})
                else:
                    return jsonify({'error': 'Progress tracking unavailable'}), 503
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/progress/complete', methods=['POST'])
        @self.require_auth(['write'])
        @self.track_usage
        def complete_problem():
            """Mark problem as completed"""
            data = request.get_json()
            required_fields = ['problem_id', 'time_spent', 'language']
            
            if not data or not all(field in data for field in required_fields):
                return jsonify({'error': 'Required fields missing'}), 400
            
            try:
                self._mark_problem_complete(data)
                return jsonify({'message': 'Problem marked as completed'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # Analytics routes
        @self.app.route('/api/analytics/overview', methods=['GET'])
        @self.require_auth(['read'])
        @self.track_usage
        def get_analytics_overview():
            """Get analytics overview"""
            language = request.args.get('language', 'python')
            days = request.args.get('days', 30, type=int)
            
            try:
                if self.analytics:
                    analytics = self.analytics.get_learning_analytics(language, days)
                    return jsonify({'analytics': analytics})
                else:
                    return jsonify({'error': 'Analytics unavailable'}), 503
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/analytics/recommendations', methods=['GET'])
        @self.require_auth(['read'])
        @self.track_usage
        def get_recommendations():
            """Get AI recommendations"""
            language = request.args.get('language', 'python')
            
            try:
                if self.recommendation_engine:
                    recommendations = self.recommendation_engine.get_personalized_recommendations(language, limit=10)
                    return jsonify({'recommendations': recommendations})
                else:
                    return jsonify({'error': 'Recommendations unavailable'}), 503
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # Spaced repetition routes
        @self.app.route('/api/spaced-repetition/due', methods=['GET'])
        @self.require_auth(['read'])
        @self.track_usage
        def get_due_reviews():
            """Get problems due for review"""
            language = request.args.get('language', 'python')
            
            try:
                if self.spaced_repetition:
                    due_problems = self.spaced_repetition.get_due_problems(language)
                    return jsonify({'due_problems': due_problems})
                else:
                    return jsonify({'error': 'Spaced repetition unavailable'}), 503
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/spaced-repetition/review', methods=['POST'])
        @self.require_auth(['write'])
        @self.track_usage
        def complete_review():
            """Complete a spaced repetition review"""
            data = request.get_json()
            required_fields = ['problem_id', 'performance', 'language']
            
            if not data or not all(field in data for field in required_fields):
                return jsonify({'error': 'Required fields missing'}), 400
            
            try:
                if self.spaced_repetition:
                    self.spaced_repetition.review_problem(
                        data['problem_id'], 
                        data['performance'], 
                        data['language']
                    )
                    return jsonify({'message': 'Review completed'})
                else:
                    return jsonify({'error': 'Spaced repetition unavailable'}), 503
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # Git automation routes
        @self.app.route('/api/git/status', methods=['GET'])
        @self.require_auth(['read'])
        @self.track_usage
        def get_git_status():
            """Get git repository status"""
            try:
                if self.git_automation:
                    status = self.git_automation.get_repo_status()
                    return jsonify({'git_status': status})
                else:
                    return jsonify({'error': 'Git automation unavailable'}), 503
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/git/commit', methods=['POST'])
        @self.require_auth(['write'])
        @self.track_usage
        def git_commit():
            """Commit changes to git"""
            data = request.get_json()
            message = data.get('message', 'API commit') if data else 'API commit'
            
            try:
                if self.git_automation:
                    result = self.git_automation.commit_changes(message)
                    return jsonify({'result': result})
                else:
                    return jsonify({'error': 'Git automation unavailable'}), 503
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # System monitoring routes
        @self.app.route('/api/system/health', methods=['GET'])
        @self.require_auth(['read'])
        @self.track_usage
        def system_health():
            """Get system health status"""
            try:
                if self.performance_monitor:
                    health = self.performance_monitor.get_system_health()
                    return jsonify({'health': health})
                else:
                    # Basic health check
                    return jsonify({
                        'health': {
                            'status': 'healthy',
                            'timestamp': datetime.now().isoformat(),
                            'services': {
                                'api': 'active',
                                'database': 'active'
                            }
                        }
                    })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # API documentation route
        @self.app.route('/api/docs', methods=['GET'])
        def api_documentation():
            """API documentation endpoint"""
            return jsonify(self._generate_api_docs())
        
        # Webhook management routes
        @self.app.route('/api/webhooks', methods=['GET'])
        @self.require_auth(['read'])
        @self.track_usage
        def get_webhooks():
            """Get user webhooks"""
            try:
                webhooks = self._get_user_webhooks(g.current_user['id'])
                return jsonify({'webhooks': webhooks})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/webhooks', methods=['POST'])
        @self.require_auth(['write'])
        @self.track_usage
        def create_webhook():
            """Create new webhook"""
            data = request.get_json()
            required_fields = ['url', 'events']
            
            if not data or not all(field in data for field in required_fields):
                return jsonify({'error': 'URL and events required'}), 400
            
            try:
                webhook_id = self._create_webhook(
                    g.current_user['id'],
                    data['url'],
                    data['events'],
                    data.get('secret', '')
                )
                return jsonify({'webhook_id': webhook_id, 'message': 'Webhook created'}), 201
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # API usage statistics
        @self.app.route('/api/usage/stats', methods=['GET'])
        @self.require_auth(['admin'])
        @self.track_usage
        def get_usage_stats():
            """Get API usage statistics (admin only)"""
            try:
                stats = self._get_usage_statistics()
                return jsonify({'usage_stats': stats})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # Error handlers
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'Endpoint not found'}), 404
        
        @self.app.errorhandler(429)
        def rate_limit_exceeded(error):
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({'error': 'Internal server error'}), 500
    
    # Helper methods for authentication and authorization
    def _authenticate_user(self, username, password):
        """Authenticate user credentials"""
        conn = sqlite3.connect(self.api_db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM api_users WHERE username = ? AND is_active = 1', (username,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user[3], password):  # user[3] is password_hash
            # Update last login
            cursor.execute('UPDATE api_users SET last_login = ? WHERE id = ?', 
                         (datetime.now(), user[0]))
            conn.commit()
            conn.close()
            
            # Convert to dict
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'api_key': user[4],
                'permissions': user[8]
            }
        
        conn.close()
        return None
    
    def _verify_jwt_token(self, token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            user_id = payload['user_id']
            
            conn = sqlite3.connect(self.api_db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM api_users WHERE id = ? AND is_active = 1', (user_id,))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'api_key': user[4],
                    'permissions': user[8]
                }
        except jwt.InvalidTokenError:
            pass
        
        return None
    
    def _verify_api_key(self, api_key):
        """Verify API key"""
        conn = sqlite3.connect(self.api_db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM api_users WHERE api_key = ? AND is_active = 1', (api_key,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'api_key': user[4],
                'permissions': user[8]
            }
        
        return None
    
    def _check_permissions(self, user, required_permissions):
        """Check if user has required permissions"""
        user_permissions = json.loads(user['permissions'])
        return any(perm in user_permissions for perm in required_permissions)
    
    def _generate_jwt_token(self, user):
        """Generate JWT token for user"""
        payload = {
            'user_id': user['id'],
            'username': user['username'],
            'exp': datetime.utcnow() + self.app.config['JWT_ACCESS_TOKEN_EXPIRES']
        }
        return jwt.encode(payload, self.app.config['JWT_SECRET_KEY'], algorithm='HS256')
    
    def _create_user(self, username, password, email):
        """Create new user"""
        conn = sqlite3.connect(self.api_db_path)
        cursor = conn.cursor()
        
        # Check if username or email already exists
        cursor.execute('SELECT id FROM api_users WHERE username = ? OR email = ?', (username, email))
        if cursor.fetchone():
            conn.close()
            raise ValueError('Username or email already exists')
        
        # Create user
        password_hash = generate_password_hash(password)
        api_key = secrets.token_hex(32)
        
        cursor.execute('''
            INSERT INTO api_users (username, email, password_hash, api_key)
            VALUES (?, ?, ?, ?)
        ''', (username, email, password_hash, api_key))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return user_id
    
    def _log_api_usage(self, user_id, endpoint, method, status_code, response_time, ip_address, user_agent):
        """Log API usage"""
        try:
            conn = sqlite3.connect(self.api_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO api_usage 
                (user_id, endpoint, method, response_code, response_time, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, endpoint, method, status_code, response_time, ip_address, user_agent))
            
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Error logging API usage: {e}")
    
    # Helper methods for data operations
    def _get_problems_filtered(self, language, difficulty=None, topic=None, platform=None, limit=50, offset=0):
        """Get filtered problems"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM problems WHERE 1=1'
        params = []
        
        if difficulty:
            query += ' AND difficulty = ?'
            params.append(difficulty)
        
        if topic:
            query += ' AND topic = ?'
            params.append(topic)
        
        if platform:
            query += ' AND platform = ?'
            params.append(platform)
        
        query += ' LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        problems = []
        
        for row in cursor.fetchall():
            problems.append({
                'id': row[0],
                'title': row[1],
                'difficulty': row[2],
                'topic': row[3],
                'platform': row[4],
                'url': row[5],
                'description': row[6],
                'tags': row[7],
                'hints': row[8],
                'solution': row[9]
            })
        
        conn.close()
        return problems
    
    def _get_problem_by_id(self, problem_id):
        """Get problem by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM problems WHERE id = ?', (problem_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'title': row[1],
                'difficulty': row[2],
                'topic': row[3],
                'platform': row[4],
                'url': row[5],
                'description': row[6],
                'tags': row[7],
                'hints': row[8],
                'solution': row[9]
            }
        
        return None
    
    def _add_problem(self, data):
        """Add new problem"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO problems (title, difficulty, topic, platform, url, description, tags, hints, solution)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['title'],
            data['difficulty'],
            data['topic'],
            data.get('platform', 'custom'),
            data.get('url', ''),
            data['description'],
            data.get('tags', ''),
            data.get('hints', ''),
            data.get('solution', '')
        ))
        
        problem_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return problem_id
    
    def _mark_problem_complete(self, data):
        """Mark problem as completed"""
        if self.practice_manager:
            # Use practice manager if available
            self.practice_manager.mark_completed(
                data['problem_id'],
                data['time_spent'],
                data['language'],
                data.get('notes', ''),
                data.get('attempts', 1)
            )
        else:
            # Direct database update as fallback
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO progress (problem_id, status, language, time_spent, attempts, notes, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['problem_id'],
                'completed',
                data['language'],
                data['time_spent'],
                data.get('attempts', 1),
                data.get('notes', ''),
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
    
    def _get_user_webhooks(self, user_id):
        """Get user's webhooks"""
        conn = sqlite3.connect(self.api_db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM webhooks WHERE user_id = ? AND is_active = 1', (user_id,))
        webhooks = []
        
        for row in cursor.fetchall():
            webhooks.append({
                'id': row[0],
                'url': row[2],
                'events': json.loads(row[3]),
                'created_at': row[6]
            })
        
        conn.close()
        return webhooks
    
    def _create_webhook(self, user_id, url, events, secret):
        """Create new webhook"""
        conn = sqlite3.connect(self.api_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO webhooks (user_id, url, events, secret)
            VALUES (?, ?, ?, ?)
        ''', (user_id, url, json.dumps(events), secret))
        
        webhook_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return webhook_id
    
    def _get_usage_statistics(self):
        """Get API usage statistics"""
        conn = sqlite3.connect(self.api_db_path)
        cursor = conn.cursor()
        
        # Total requests
        cursor.execute('SELECT COUNT(*) FROM api_usage')
        total_requests = cursor.fetchone()[0]
        
        # Requests by endpoint
        cursor.execute('''
            SELECT endpoint, COUNT(*) as count
            FROM api_usage 
            GROUP BY endpoint 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        endpoint_stats = cursor.fetchall()
        
        # Requests by user
        cursor.execute('''
            SELECT u.username, COUNT(*) as count
            FROM api_usage au
            LEFT JOIN api_users u ON au.user_id = u.id
            GROUP BY au.user_id
            ORDER BY count DESC
            LIMIT 10
        ''')
        user_stats = cursor.fetchall()
        
        # Average response time
        cursor.execute('SELECT AVG(response_time) FROM api_usage')
        avg_response_time = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_requests': total_requests,
            'endpoint_stats': [{'endpoint': row[0], 'count': row[1]} for row in endpoint_stats],
            'user_stats': [{'username': row[0] or 'Anonymous', 'count': row[1]} for row in user_stats],
            'avg_response_time': round(avg_response_time, 3)
        }
    
    def _generate_api_docs(self):
        """Generate API documentation"""
        return {
            'title': 'Coding Practice System API',
            'version': '1.0.0',
            'description': 'Comprehensive REST API for the coding practice system',
            'base_url': '/api',
            'authentication': {
                'methods': ['JWT Bearer Token', 'API Key'],
                'jwt_header': 'Authorization: Bearer <token>',
                'api_key_header': 'X-API-Key: <api_key>'
            },
            'endpoints': {
                'authentication': {
                    'POST /auth/login': 'User login',
                    'POST /auth/register': 'User registration'
                },
                'problems': {
                    'GET /problems': 'Get problems with filtering',
                    'GET /problems/<id>': 'Get specific problem',
                    'POST /problems': 'Add new problem'
                },
                'progress': {
                    'GET /progress': 'Get user progress',
                    'POST /progress/complete': 'Mark problem as completed'
                },
                'analytics': {
                    'GET /analytics/overview': 'Get analytics overview',
                    'GET /analytics/recommendations': 'Get AI recommendations'
                },
                'spaced_repetition': {
                    'GET /spaced-repetition/due': 'Get problems due for review',
                    'POST /spaced-repetition/review': 'Complete review'
                },
                'system': {
                    'GET /system/health': 'System health check',
                    'GET /git/status': 'Git repository status',
                    'POST /git/commit': 'Commit changes'
                },
                'webhooks': {
                    'GET /webhooks': 'Get user webhooks',
                    'POST /webhooks': 'Create webhook'
                },
                'admin': {
                    'GET /usage/stats': 'API usage statistics (admin only)'
                }
            },
            'rate_limits': {
                'default': '1000 per hour, 100 per minute',
                'login': '10 per minute',
                'register': '5 per minute'
            },
            'examples': {
                'login': {
                    'url': 'POST /api/auth/login',
                    'payload': {'username': 'user', 'password': 'pass'},
                    'response': {'token': 'jwt_token', 'user': {'id': 1, 'username': 'user'}}
                },
                'get_problems': {
                    'url': 'GET /api/problems?difficulty=medium&topic=arrays&limit=10',
                    'headers': {'Authorization': 'Bearer <token>'},
                    'response': {'problems': []}
                },
                'complete_problem': {
                    'url': 'POST /api/progress/complete',
                    'headers': {'Authorization': 'Bearer <token>'},
                    'payload': {
                        'problem_id': 1,
                        'time_spent': 1800,
                        'language': 'python',
                        'notes': 'Solved using dynamic programming'
                    }
                }
            }
        }
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the API server"""
        print(f"🚀 Starting Coding Practice API on {host}:{port}")
        print(f"📚 API Documentation: http://{host}:{port}/api/docs")
        print(f"🔐 Default admin credentials: username=admin, password=admin123")
        
        self.app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Coding Practice System REST API")
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--db-path', default='practice_data/problems.db', help='Database path')
    
    args = parser.parse_args()
    
    api = CodingPracticeAPI(db_path=args.db_path)
    api.run(host=args.host, port=args.port, debug=args.debug) 