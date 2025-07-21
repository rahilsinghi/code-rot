#!/usr/bin/env python3
"""
Study Session Manager
Pomodoro timers, focus modes, distraction blocking, and productivity analytics
"""

import os
import sqlite3
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess
import platform

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class SessionState(Enum):
    """Study session states"""
    IDLE = "idle"
    ACTIVE = "active"
    BREAK = "break"
    LONG_BREAK = "long_break"
    PAUSED = "paused"
    COMPLETED = "completed"

class FocusMode(Enum):
    """Focus mode types"""
    POMODORO = "pomodoro"
    DEEP_WORK = "deep_work"
    SPRINT = "sprint"
    CUSTOM = "custom"
    FREE_FLOW = "free_flow"

class SessionType(Enum):
    """Session types"""
    PROBLEM_SOLVING = "problem_solving"
    REVIEW = "review"
    LEARNING = "learning"
    DEBUGGING = "debugging"
    INTERVIEW_PREP = "interview_prep"

@dataclass
class StudySession:
    """Study session data structure"""
    id: Optional[int] = None
    session_type: SessionType = SessionType.PROBLEM_SOLVING
    focus_mode: FocusMode = FocusMode.POMODORO
    state: SessionState = SessionState.IDLE
    
    # Timing
    planned_duration: int = 1500  # 25 minutes in seconds
    actual_duration: int = 0
    break_duration: int = 300  # 5 minutes
    long_break_duration: int = 900  # 15 minutes
    
    # Session data
    language: str = "python"
    topic: str = ""
    goals: List[str] = None
    problems_planned: int = 0
    problems_completed: int = 0
    
    # Tracking
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    pause_time: Optional[datetime] = None
    total_pause_duration: int = 0
    
    # Performance
    focus_score: float = 0.0
    productivity_score: float = 0.0
    distraction_count: int = 0
    interruption_count: int = 0
    
    # Metadata
    notes: str = ""
    tags: List[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.goals is None:
            self.goals = []
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now()

class StudySessionManager:
    def __init__(self, db_path="practice_data/problems.db", config_path=None):
        self.db_path = Path(db_path)
        self.sessions_db_path = self.db_path.parent / "study_sessions.db"
        self.config_path = config_path or self.db_path.parent / "session_config.json"
        
        # Setup logging
        self.setup_logging()
        
        # Load configuration
        self.config = self.load_config()
        
        # Initialize database
        self.init_database()
        
        # Session management
        self.current_session: Optional[StudySession] = None
        self.session_timer: Optional[threading.Timer] = None
        self.timer_callbacks: List[Callable] = []
        
        # Focus mode settings
        self.focus_modes = self._load_focus_modes()
        
        # Audio system for notifications
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
                self.audio_enabled = True
            except:
                self.audio_enabled = False
        else:
            self.audio_enabled = False
        
        # Process monitoring for distractions
        self.monitoring_active = False
        self.blocked_apps = set()
        
        logging.info("Study Session Manager initialized")
    
    def setup_logging(self):
        """Setup session logging"""
        log_dir = self.db_path.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'study_sessions.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self) -> Dict[str, Any]:
        """Load session configuration"""
        default_config = {
            'pomodoro': {
                'work_duration': 1500,  # 25 minutes
                'short_break': 300,     # 5 minutes
                'long_break': 900,      # 15 minutes
                'sessions_before_long_break': 4
            },
            'deep_work': {
                'work_duration': 5400,  # 90 minutes
                'break_duration': 900   # 15 minutes
            },
            'sprint': {
                'work_duration': 900,   # 15 minutes
                'break_duration': 180   # 3 minutes
            },
            'audio': {
                'enabled': True,
                'work_start_sound': 'bell.wav',
                'break_start_sound': 'chime.wav',
                'session_end_sound': 'complete.wav',
                'volume': 0.7
            },
            'notifications': {
                'desktop_enabled': True,
                'sound_enabled': True,
                'popup_duration': 5,
                'reminder_interval': 600  # 10 minutes
            },
            'distraction_blocking': {
                'enabled': False,
                'blocked_websites': [
                    'youtube.com', 'facebook.com', 'twitter.com', 
                    'instagram.com', 'tiktok.com', 'reddit.com'
                ],
                'blocked_apps': [
                    'Discord', 'Slack', 'WhatsApp', 'Telegram',
                    'Spotify', 'iTunes', 'VLC'
                ],
                'allowlist_mode': False,
                'break_time_access': True
            },
            'goals': {
                'daily_sessions': 4,
                'daily_duration': 7200,  # 2 hours
                'weekly_sessions': 20,
                'problems_per_session': 2
            },
            'analytics': {
                'track_applications': True,
                'track_keystrokes': False,
                'track_mouse_activity': False,
                'idle_threshold': 300  # 5 minutes
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    config = self._deep_merge(default_config, user_config)
                    return config
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
        
        # Save default config
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def init_database(self):
        """Initialize study sessions database"""
        conn = sqlite3.connect(self.sessions_db_path)
        cursor = conn.cursor()
        
        # Study sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_type TEXT NOT NULL,
                focus_mode TEXT NOT NULL,
                state TEXT NOT NULL,
                planned_duration INTEGER,
                actual_duration INTEGER,
                break_duration INTEGER,
                long_break_duration INTEGER,
                language TEXT,
                topic TEXT,
                goals TEXT,
                problems_planned INTEGER DEFAULT 0,
                problems_completed INTEGER DEFAULT 0,
                start_time DATETIME,
                end_time DATETIME,
                pause_time DATETIME,
                total_pause_duration INTEGER DEFAULT 0,
                focus_score REAL DEFAULT 0.0,
                productivity_score REAL DEFAULT 0.0,
                distraction_count INTEGER DEFAULT 0,
                interruption_count INTEGER DEFAULT 0,
                notes TEXT,
                tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Session activities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                activity_type TEXT,  -- problem_solved, break_taken, distraction, etc.
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                duration INTEGER,
                data TEXT,
                FOREIGN KEY (session_id) REFERENCES study_sessions (id)
            )
        ''')
        
        # Focus metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS focus_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metric_type TEXT,  -- focus_score, productivity, distraction
                value REAL,
                context TEXT,
                FOREIGN KEY (session_id) REFERENCES study_sessions (id)
            )
        ''')
        
        # Session goals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                goal_text TEXT NOT NULL,
                is_completed BOOLEAN DEFAULT 0,
                completed_at DATETIME,
                FOREIGN KEY (session_id) REFERENCES study_sessions (id)
            )
        ''')
        
        # Daily goals tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE,
                target_sessions INTEGER,
                target_duration INTEGER,
                target_problems INTEGER,
                actual_sessions INTEGER DEFAULT 0,
                actual_duration INTEGER DEFAULT 0,
                actual_problems INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_date ON study_sessions(DATE(start_time))')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_type ON study_sessions(session_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_activities_session ON session_activities(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_session ON focus_metrics(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_goals_session ON session_goals(session_id)')
        
        conn.commit()
        conn.close()
    
    def _load_focus_modes(self) -> Dict[str, Dict]:
        """Load focus mode configurations"""
        return {
            FocusMode.POMODORO.value: {
                'name': 'Pomodoro',
                'description': 'Classic 25min work + 5min break cycles',
                'work_duration': self.config['pomodoro']['work_duration'],
                'break_duration': self.config['pomodoro']['short_break'],
                'long_break_duration': self.config['pomodoro']['long_break'],
                'sessions_before_long_break': self.config['pomodoro']['sessions_before_long_break'],
                'icon': '🍅'
            },
            FocusMode.DEEP_WORK.value: {
                'name': 'Deep Work',
                'description': '90min focused sessions with 15min breaks',
                'work_duration': self.config['deep_work']['work_duration'],
                'break_duration': self.config['deep_work']['break_duration'],
                'long_break_duration': self.config['deep_work']['break_duration'],
                'sessions_before_long_break': 2,
                'icon': '🧠'
            },
            FocusMode.SPRINT.value: {
                'name': 'Sprint',
                'description': 'Quick 15min bursts with 3min breaks',
                'work_duration': self.config['sprint']['work_duration'],
                'break_duration': self.config['sprint']['break_duration'],
                'long_break_duration': 600,
                'sessions_before_long_break': 6,
                'icon': '⚡'
            },
            FocusMode.CUSTOM.value: {
                'name': 'Custom',
                'description': 'User-defined session parameters',
                'work_duration': 1800,  # 30 minutes default
                'break_duration': 300,
                'long_break_duration': 900,
                'sessions_before_long_break': 3,
                'icon': '⚙️'
            },
            FocusMode.FREE_FLOW.value: {
                'name': 'Free Flow',
                'description': 'Unstructured focus time with manual breaks',
                'work_duration': 0,  # No time limit
                'break_duration': 0,
                'long_break_duration': 0,
                'sessions_before_long_break': 0,
                'icon': '🌊'
            }
        }
    
    def start_session(self, session_config: Dict[str, Any]) -> StudySession:
        """Start a new study session"""
        if self.current_session and self.current_session.state == SessionState.ACTIVE:
            raise ValueError("Another session is already active")
        
        # Create session
        session = StudySession(
            session_type=SessionType(session_config.get('type', 'problem_solving')),
            focus_mode=FocusMode(session_config.get('focus_mode', 'pomodoro')),
            language=session_config.get('language', 'python'),
            topic=session_config.get('topic', ''),
            goals=session_config.get('goals', []),
            problems_planned=session_config.get('problems_planned', 0),
            notes=session_config.get('notes', ''),
            tags=session_config.get('tags', [])
        )
        
        # Set timing based on focus mode
        mode_config = self.focus_modes[session.focus_mode.value]
        session.planned_duration = session_config.get('duration', mode_config['work_duration'])
        session.break_duration = mode_config['break_duration']
        session.long_break_duration = mode_config['long_break_duration']
        
        # Save to database
        session.id = self._save_session(session)
        session.start_time = datetime.now()
        session.state = SessionState.ACTIVE
        
        self.current_session = session
        
        # Start timer if not free flow
        if session.focus_mode != FocusMode.FREE_FLOW:
            self._start_timer(session.planned_duration, self._on_session_complete)
        
        # Enable distraction blocking
        if self.config['distraction_blocking']['enabled']:
            self._enable_distraction_blocking()
        
        # Start monitoring
        if self.config['analytics']['track_applications']:
            self._start_activity_monitoring()
        
        # Play start sound
        self._play_sound('work_start_sound')
        
        # Send desktop notification
        self._send_desktop_notification(
            "Study Session Started",
            f"Focus mode: {mode_config['name']} ({session.planned_duration//60} min)"
        )
        
        self.logger.info(f"Started {session.focus_mode.value} session (ID: {session.id})")
        return session
    
    def pause_session(self) -> bool:
        """Pause current session"""
        if not self.current_session or self.current_session.state != SessionState.ACTIVE:
            return False
        
        self.current_session.state = SessionState.PAUSED
        self.current_session.pause_time = datetime.now()
        
        # Cancel timer
        if self.session_timer:
            self.session_timer.cancel()
        
        # Disable distraction blocking during pause
        if self.config['distraction_blocking']['enabled']:
            self._disable_distraction_blocking()
        
        self._update_session_in_db(self.current_session)
        self._log_activity('session_paused')
        
        self.logger.info(f"Paused session {self.current_session.id}")
        return True
    
    def resume_session(self) -> bool:
        """Resume paused session"""
        if not self.current_session or self.current_session.state != SessionState.PAUSED:
            return False
        
        # Calculate pause duration
        if self.current_session.pause_time:
            pause_duration = (datetime.now() - self.current_session.pause_time).total_seconds()
            self.current_session.total_pause_duration += int(pause_duration)
            self.current_session.pause_time = None
        
        self.current_session.state = SessionState.ACTIVE
        
        # Calculate remaining time
        if self.current_session.focus_mode != FocusMode.FREE_FLOW:
            elapsed = (datetime.now() - self.current_session.start_time).total_seconds()
            elapsed -= self.current_session.total_pause_duration
            remaining = max(0, self.current_session.planned_duration - elapsed)
            
            if remaining > 0:
                self._start_timer(remaining, self._on_session_complete)
            else:
                self._on_session_complete()
        
        # Re-enable distraction blocking
        if self.config['distraction_blocking']['enabled']:
            self._enable_distraction_blocking()
        
        self._update_session_in_db(self.current_session)
        self._log_activity('session_resumed')
        
        self.logger.info(f"Resumed session {self.current_session.id}")
        return True
    
    def end_session(self, early: bool = False) -> Optional[StudySession]:
        """End current session"""
        if not self.current_session:
            return None
        
        session = self.current_session
        session.end_time = datetime.now()
        session.state = SessionState.COMPLETED
        
        # Calculate actual duration
        if session.start_time:
            total_duration = (session.end_time - session.start_time).total_seconds()
            session.actual_duration = int(total_duration - session.total_pause_duration)
        
        # Cancel timer
        if self.session_timer:
            self.session_timer.cancel()
            self.session_timer = None
        
        # Calculate scores
        session.focus_score = self._calculate_focus_score(session)
        session.productivity_score = self._calculate_productivity_score(session)
        
        # Cleanup
        self._disable_distraction_blocking()
        self._stop_activity_monitoring()
        
        # Update database
        self._update_session_in_db(session)
        self._log_activity('session_ended', {'early': early})
        
        # Update daily goals
        self._update_daily_goals(session)
        
        # Play completion sound
        self._play_sound('session_end_sound')
        
        # Send completion notification
        duration_str = f"{session.actual_duration // 60}m {session.actual_duration % 60}s"
        self._send_desktop_notification(
            "Session Completed!",
            f"Duration: {duration_str} | Focus: {session.focus_score:.1f}/10"
        )
        
        completed_session = session
        self.current_session = None
        
        self.logger.info(f"Ended session {completed_session.id} ({duration_str})")
        return completed_session
    
    def start_break(self, break_type: str = 'short') -> bool:
        """Start a break between sessions"""
        if self.current_session:
            self.end_session()
        
        break_duration = (
            self.config['pomodoro']['long_break'] if break_type == 'long'
            else self.config['pomodoro']['short_break']
        )
        
        # Create break session
        break_session = StudySession(
            session_type=SessionType.REVIEW,  # Use review as break type
            focus_mode=FocusMode.POMODORO,
            state=SessionState.BREAK if break_type == 'short' else SessionState.LONG_BREAK,
            planned_duration=break_duration,
            start_time=datetime.now()
        )
        
        break_session.id = self._save_session(break_session)
        self.current_session = break_session
        
        # Allow access during breaks
        if self.config['distraction_blocking']['break_time_access']:
            self._disable_distraction_blocking()
        
        # Start break timer
        self._start_timer(break_duration, self._on_break_complete)
        
        # Play break sound
        self._play_sound('break_start_sound')
        
        # Send notification
        break_name = "Long Break" if break_type == 'long' else "Short Break"
        self._send_desktop_notification(
            f"{break_name} Started",
            f"Take a break for {break_duration//60} minutes"
        )
        
        self.logger.info(f"Started {break_type} break ({break_duration//60} min)")
        return True
    
    def get_session_status(self) -> Dict[str, Any]:
        """Get current session status"""
        if not self.current_session:
            return {
                'active': False,
                'state': 'idle',
                'message': 'No active session'
            }
        
        session = self.current_session
        now = datetime.now()
        
        # Calculate elapsed and remaining time
        if session.start_time:
            elapsed = (now - session.start_time).total_seconds() - session.total_pause_duration
            remaining = max(0, session.planned_duration - elapsed) if session.planned_duration > 0 else 0
        else:
            elapsed = 0
            remaining = session.planned_duration
        
        return {
            'active': True,
            'session_id': session.id,
            'state': session.state.value,
            'focus_mode': session.focus_mode.value,
            'session_type': session.session_type.value,
            'elapsed_seconds': int(elapsed),
            'remaining_seconds': int(remaining),
            'elapsed_formatted': self._format_duration(int(elapsed)),
            'remaining_formatted': self._format_duration(int(remaining)),
            'progress_percentage': (elapsed / session.planned_duration * 100) if session.planned_duration > 0 else 0,
            'problems_completed': session.problems_completed,
            'problems_planned': session.problems_planned,
            'distraction_count': session.distraction_count,
            'interruption_count': session.interruption_count,
            'is_paused': session.state == SessionState.PAUSED
        }
    
    def get_session_history(self, days: int = 7, limit: int = 50) -> List[Dict]:
        """Get session history"""
        conn = sqlite3.connect(self.sessions_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, session_type, focus_mode, state, planned_duration, actual_duration,
                   language, topic, problems_planned, problems_completed,
                   start_time, end_time, focus_score, productivity_score,
                   distraction_count, interruption_count, notes
            FROM study_sessions
            WHERE start_time >= DATE('now', '-{} days')
            ORDER BY start_time DESC
            LIMIT ?
        '''.format(days), (limit,))
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'id': row[0],
                'session_type': row[1],
                'focus_mode': row[2],
                'state': row[3],
                'planned_duration': row[4],
                'actual_duration': row[5],
                'language': row[6],
                'topic': row[7],
                'problems_planned': row[8],
                'problems_completed': row[9],
                'start_time': row[10],
                'end_time': row[11],
                'focus_score': row[12] or 0.0,
                'productivity_score': row[13] or 0.0,
                'distraction_count': row[14] or 0,
                'interruption_count': row[15] or 0,
                'notes': row[16] or ''
            })
        
        conn.close()
        return sessions
    
    def get_productivity_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get productivity analytics"""
        conn = sqlite3.connect(self.sessions_db_path)
        cursor = conn.cursor()
        
        # Total sessions and time
        cursor.execute('''
            SELECT 
                COUNT(*) as total_sessions,
                SUM(actual_duration) as total_time,
                AVG(actual_duration) as avg_session_length,
                AVG(focus_score) as avg_focus_score,
                AVG(productivity_score) as avg_productivity_score
            FROM study_sessions
            WHERE start_time >= DATE('now', '-{} days')
            AND state = 'completed'
        '''.format(days))
        
        overview = cursor.fetchone()
        
        # Sessions by focus mode
        cursor.execute('''
            SELECT focus_mode, COUNT(*) as count, SUM(actual_duration) as total_time
            FROM study_sessions
            WHERE start_time >= DATE('now', '-{} days')
            AND state = 'completed'
            GROUP BY focus_mode
            ORDER BY count DESC
        '''.format(days))
        
        by_focus_mode = {}
        for row in cursor.fetchall():
            by_focus_mode[row[0]] = {
                'sessions': row[1],
                'total_time': row[2] or 0
            }
        
        # Daily breakdown
        cursor.execute('''
            SELECT 
                DATE(start_time) as date,
                COUNT(*) as sessions,
                SUM(actual_duration) as total_time,
                AVG(focus_score) as avg_focus,
                SUM(problems_completed) as problems
            FROM study_sessions
            WHERE start_time >= DATE('now', '-{} days')
            AND state = 'completed'
            GROUP BY DATE(start_time)
            ORDER BY date
        '''.format(days))
        
        daily_stats = []
        for row in cursor.fetchall():
            daily_stats.append({
                'date': row[0],
                'sessions': row[1],
                'total_time': row[2] or 0,
                'avg_focus': round(row[3] or 0, 1),
                'problems': row[4] or 0
            })
        
        # Best performance metrics
        cursor.execute('''
            SELECT MAX(focus_score), MAX(productivity_score), MAX(actual_duration)
            FROM study_sessions
            WHERE start_time >= DATE('now', '-{} days')
            AND state = 'completed'
        '''.format(days))
        
        best_metrics = cursor.fetchone()
        
        conn.close()
        
        return {
            'overview': {
                'total_sessions': overview[0] or 0,
                'total_time_seconds': overview[1] or 0,
                'total_time_formatted': self._format_duration(overview[1] or 0),
                'avg_session_length': int(overview[2] or 0),
                'avg_session_formatted': self._format_duration(int(overview[2] or 0)),
                'avg_focus_score': round(overview[3] or 0, 1),
                'avg_productivity_score': round(overview[4] or 0, 1)
            },
            'by_focus_mode': by_focus_mode,
            'daily_stats': daily_stats,
            'best_metrics': {
                'best_focus_score': round(best_metrics[0] or 0, 1),
                'best_productivity_score': round(best_metrics[1] or 0, 1),
                'longest_session': int(best_metrics[2] or 0),
                'longest_session_formatted': self._format_duration(int(best_metrics[2] or 0))
            },
            'period_days': days
        }
    
    def add_problem_completion(self, problem_data: Dict[str, Any]) -> bool:
        """Add problem completion to current session"""
        if not self.current_session or self.current_session.state != SessionState.ACTIVE:
            return False
        
        self.current_session.problems_completed += 1
        
        # Log activity
        self._log_activity('problem_completed', problem_data)
        
        # Update session in database
        self._update_session_in_db(self.current_session)
        
        self.logger.info(f"Problem completed in session {self.current_session.id}")
        return True
    
    def add_session_goal(self, goal_text: str) -> bool:
        """Add goal to current session"""
        if not self.current_session:
            return False
        
        self.current_session.goals.append(goal_text)
        
        # Save goal to database
        conn = sqlite3.connect(self.sessions_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO session_goals (session_id, goal_text)
            VALUES (?, ?)
        ''', (self.current_session.id, goal_text))
        
        conn.commit()
        conn.close()
        
        return True
    
    def complete_session_goal(self, goal_text: str) -> bool:
        """Mark session goal as completed"""
        if not self.current_session:
            return False
        
        conn = sqlite3.connect(self.sessions_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE session_goals 
            SET is_completed = 1, completed_at = ?
            WHERE session_id = ? AND goal_text = ?
        ''', (datetime.now(), self.current_session.id, goal_text))
        
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0
    
    # Timer and callback methods
    def _start_timer(self, duration: float, callback: Callable):
        """Start session timer"""
        if self.session_timer:
            self.session_timer.cancel()
        
        self.session_timer = threading.Timer(duration, callback)
        self.session_timer.start()
    
    def _on_session_complete(self):
        """Handle session completion"""
        if self.current_session:
            self._play_sound('session_end_sound')
            self._send_desktop_notification(
                "Session Complete!",
                "Time for a break. Great work!"
            )
            
            # Auto-start break if enabled
            if self.config.get('auto_break', True):
                # Determine break type based on session count
                session_count = self._get_completed_sessions_today()
                break_type = 'long' if session_count % self.focus_modes['pomodoro']['sessions_before_long_break'] == 0 else 'short'
                
                self.end_session()
                threading.Timer(2.0, lambda: self.start_break(break_type)).start()
            else:
                self.end_session()
    
    def _on_break_complete(self):
        """Handle break completion"""
        if self.current_session:
            self._play_sound('break_start_sound')  # Gentle reminder
            self._send_desktop_notification(
                "Break Over!",
                "Ready to start your next session?"
            )
            self.end_session()
    
    # Activity monitoring
    def _start_activity_monitoring(self):
        """Start monitoring user activity"""
        if not PSUTIL_AVAILABLE:
            return
        
        self.monitoring_active = True
        
        def monitor():
            while self.monitoring_active and self.current_session:
                try:
                    # Monitor active applications
                    active_apps = self._get_active_applications()
                    
                    # Check for distracting apps
                    for app in active_apps:
                        if app.lower() in [blocked.lower() for blocked in self.config['distraction_blocking']['blocked_apps']]:
                            self.current_session.distraction_count += 1
                            self._log_activity('distraction_detected', {'app': app})
                    
                    # Update focus metrics
                    focus_score = self._calculate_current_focus()
                    self._record_focus_metric('focus_score', focus_score)
                    
                    time.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    self.logger.error(f"Error in activity monitoring: {e}")
                    break
        
        threading.Thread(target=monitor, daemon=True).start()
    
    def _stop_activity_monitoring(self):
        """Stop activity monitoring"""
        self.monitoring_active = False
    
    def _get_active_applications(self) -> List[str]:
        """Get list of active applications"""
        if not PSUTIL_AVAILABLE:
            return []
        
        try:
            active_apps = []
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name']:
                        active_apps.append(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return list(set(active_apps))
        except Exception as e:
            self.logger.error(f"Error getting active applications: {e}")
            return []
    
    # Distraction blocking
    def _enable_distraction_blocking(self):
        """Enable distraction blocking"""
        if not self.config['distraction_blocking']['enabled']:
            return
        
        blocked_sites = self.config['distraction_blocking']['blocked_websites']
        blocked_apps = self.config['distraction_blocking']['blocked_apps']
        
        # Block websites (simplified - would need more sophisticated implementation)
        self._block_websites(blocked_sites)
        
        # Track blocked apps for monitoring
        self.blocked_apps = set(app.lower() for app in blocked_apps)
        
        self.logger.info("Distraction blocking enabled")
    
    def _disable_distraction_blocking(self):
        """Disable distraction blocking"""
        if not self.config['distraction_blocking']['enabled']:
            return
        
        # Unblock websites
        self._unblock_websites()
        
        # Clear blocked apps
        self.blocked_apps.clear()
        
        self.logger.info("Distraction blocking disabled")
    
    def _block_websites(self, sites: List[str]):
        """Block websites (basic implementation)"""
        # This is a simplified implementation
        # In practice, you'd modify hosts file or use system firewall
        pass
    
    def _unblock_websites(self):
        """Unblock websites"""
        # Restore original hosts file or firewall rules
        pass
    
    # Audio notifications
    def _play_sound(self, sound_key: str):
        """Play notification sound"""
        if not self.audio_enabled or not self.config['audio']['enabled']:
            return
        
        sound_file = self.config['audio'].get(sound_key, '')
        if not sound_file or not Path(sound_file).exists():
            # Use system beep as fallback
            self._system_beep()
            return
        
        try:
            sound = pygame.mixer.Sound(sound_file)
            sound.set_volume(self.config['audio']['volume'])
            sound.play()
        except Exception as e:
            self.logger.error(f"Error playing sound: {e}")
            self._system_beep()
    
    def _system_beep(self):
        """System beep fallback"""
        try:
            if platform.system() == "Darwin":  # macOS
                os.system("afplay /System/Library/Sounds/Glass.aiff")
            elif platform.system() == "Windows":
                os.system("rundll32 user32.dll,MessageBeep")
            else:  # Linux
                os.system("pactl upload-sample /usr/share/sounds/alsa/Front_Left.wav bell")
        except:
            print("\a")  # Terminal bell as last resort
    
    # Desktop notifications
    def _send_desktop_notification(self, title: str, message: str):
        """Send desktop notification"""
        if not self.config['notifications']['desktop_enabled']:
            return
        
        try:
            if platform.system() == "Darwin":  # macOS
                script = f'display notification "{message}" with title "{title}"'
                subprocess.run(["osascript", "-e", script])
            elif platform.system() == "Windows":
                # Would use plyer or win10toast for Windows notifications
                pass
            else:  # Linux
                subprocess.run(["notify-send", title, message])
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")
    
    # Scoring and analytics
    def _calculate_focus_score(self, session: StudySession) -> float:
        """Calculate focus score for session"""
        if not session.actual_duration:
            return 0.0
        
        base_score = 10.0
        
        # Reduce score for distractions
        distraction_penalty = min(5.0, session.distraction_count * 0.5)
        
        # Reduce score for interruptions
        interruption_penalty = min(3.0, session.interruption_count * 0.3)
        
        # Reduce score for excessive pauses
        pause_penalty = min(2.0, (session.total_pause_duration / 60) * 0.1)
        
        focus_score = max(0.0, base_score - distraction_penalty - interruption_penalty - pause_penalty)
        
        return round(focus_score, 1)
    
    def _calculate_productivity_score(self, session: StudySession) -> float:
        """Calculate productivity score for session"""
        if not session.actual_duration:
            return 0.0
        
        base_score = 10.0
        
        # Goal completion bonus
        if session.problems_planned > 0:
            completion_rate = session.problems_completed / session.problems_planned
            goal_bonus = completion_rate * 2.0
        else:
            goal_bonus = 1.0 if session.problems_completed > 0 else 0.0
        
        # Duration effectiveness (longer isn't always better)
        if session.actual_duration > 0:
            planned_ratio = session.actual_duration / session.planned_duration if session.planned_duration > 0 else 1.0
            if 0.8 <= planned_ratio <= 1.2:  # Sweet spot
                duration_bonus = 1.0
            else:
                duration_bonus = max(0.0, 1.0 - abs(planned_ratio - 1.0))
        else:
            duration_bonus = 0.0
        
        productivity_score = min(10.0, base_score + goal_bonus + duration_bonus)
        
        return round(productivity_score, 1)
    
    def _calculate_current_focus(self) -> float:
        """Calculate current focus level"""
        # Simplified focus calculation
        # In practice, this would use more sophisticated metrics
        base_focus = 8.0
        
        if self.current_session:
            recent_distractions = self.current_session.distraction_count
            focus_reduction = min(3.0, recent_distractions * 0.2)
            return max(0.0, base_focus - focus_reduction)
        
        return base_focus
    
    # Database helpers
    def _save_session(self, session: StudySession) -> int:
        """Save session to database"""
        conn = sqlite3.connect(self.sessions_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO study_sessions 
            (session_type, focus_mode, state, planned_duration, actual_duration,
             break_duration, long_break_duration, language, topic, goals,
             problems_planned, problems_completed, start_time, end_time,
             pause_time, total_pause_duration, focus_score, productivity_score,
             distraction_count, interruption_count, notes, tags, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session.session_type.value,
            session.focus_mode.value,
            session.state.value,
            session.planned_duration,
            session.actual_duration,
            session.break_duration,
            session.long_break_duration,
            session.language,
            session.topic,
            json.dumps(session.goals),
            session.problems_planned,
            session.problems_completed,
            session.start_time,
            session.end_time,
            session.pause_time,
            session.total_pause_duration,
            session.focus_score,
            session.productivity_score,
            session.distraction_count,
            session.interruption_count,
            session.notes,
            json.dumps(session.tags),
            session.created_at
        ))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return session_id
    
    def _update_session_in_db(self, session: StudySession):
        """Update session in database"""
        if not session.id:
            return
        
        conn = sqlite3.connect(self.sessions_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE study_sessions SET
                state = ?, actual_duration = ?, end_time = ?, pause_time = ?,
                total_pause_duration = ?, problems_completed = ?, focus_score = ?,
                productivity_score = ?, distraction_count = ?, interruption_count = ?,
                notes = ?, goals = ?, tags = ?
            WHERE id = ?
        ''', (
            session.state.value,
            session.actual_duration,
            session.end_time,
            session.pause_time,
            session.total_pause_duration,
            session.problems_completed,
            session.focus_score,
            session.productivity_score,
            session.distraction_count,
            session.interruption_count,
            session.notes,
            json.dumps(session.goals),
            json.dumps(session.tags),
            session.id
        ))
        
        conn.commit()
        conn.close()
    
    def _log_activity(self, activity_type: str, data: Dict[str, Any] = None):
        """Log session activity"""
        if not self.current_session:
            return
        
        conn = sqlite3.connect(self.sessions_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO session_activities (session_id, activity_type, data)
            VALUES (?, ?, ?)
        ''', (
            self.current_session.id,
            activity_type,
            json.dumps(data or {})
        ))
        
        conn.commit()
        conn.close()
    
    def _record_focus_metric(self, metric_type: str, value: float, context: str = ""):
        """Record focus metric"""
        if not self.current_session:
            return
        
        conn = sqlite3.connect(self.sessions_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO focus_metrics (session_id, metric_type, value, context)
            VALUES (?, ?, ?, ?)
        ''', (self.current_session.id, metric_type, value, context))
        
        conn.commit()
        conn.close()
    
    def _update_daily_goals(self, session: StudySession):
        """Update daily goals tracking"""
        today = datetime.now().date()
        
        conn = sqlite3.connect(self.sessions_db_path)
        cursor = conn.cursor()
        
        # Insert or update daily goals
        cursor.execute('''
            INSERT OR REPLACE INTO daily_goals 
            (date, target_sessions, target_duration, target_problems,
             actual_sessions, actual_duration, actual_problems)
            VALUES (?, ?, ?, ?, 
                    COALESCE((SELECT actual_sessions FROM daily_goals WHERE date = ?), 0) + 1,
                    COALESCE((SELECT actual_duration FROM daily_goals WHERE date = ?), 0) + ?,
                    COALESCE((SELECT actual_problems FROM daily_goals WHERE date = ?), 0) + ?)
        ''', (
            today,
            self.config['goals']['daily_sessions'],
            self.config['goals']['daily_duration'],
            self.config['goals']['problems_per_session'],
            today,
            today,
            session.actual_duration,
            today,
            session.problems_completed
        ))
        
        conn.commit()
        conn.close()
    
    # Utility methods
    def _get_completed_sessions_today(self) -> int:
        """Get number of completed sessions today"""
        conn = sqlite3.connect(self.sessions_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM study_sessions
            WHERE DATE(start_time) = DATE('now')
            AND state = 'completed'
        ''')
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to readable string"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s" if secs > 0 else f"{minutes}m"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def _deep_merge(self, dict1: Dict, dict2: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Study Session Manager")
    parser.add_argument('--start', action='store_true', help='Start a new session')
    parser.add_argument('--status', action='store_true', help='Show current session status')
    parser.add_argument('--analytics', action='store_true', help='Show productivity analytics')
    parser.add_argument('--history', type=int, default=7, help='Show session history (days)')
    parser.add_argument('--focus-mode', choices=['pomodoro', 'deep_work', 'sprint', 'free_flow'], 
                       default='pomodoro', help='Focus mode for new session')
    parser.add_argument('--duration', type=int, help='Session duration in minutes')
    
    args = parser.parse_args()
    
    session_manager = StudySessionManager()
    
    if args.start:
        config = {
            'type': 'problem_solving',
            'focus_mode': args.focus_mode,
            'language': 'python'
        }
        if args.duration:
            config['duration'] = args.duration * 60
        
        session = session_manager.start_session(config)
        print(f"✅ Started {session.focus_mode.value} session (ID: {session.id})")
        print(f"Duration: {session.planned_duration // 60} minutes")
        
    elif args.status:
        status = session_manager.get_session_status()
        if status['active']:
            print(f"🎯 Active Session: {status['focus_mode']} ({status['state']})")
            print(f"⏱️  Elapsed: {status['elapsed_formatted']}")
            print(f"⏳ Remaining: {status['remaining_formatted']}")
            print(f"📊 Progress: {status['progress_percentage']:.1f}%")
            print(f"✅ Problems: {status['problems_completed']}/{status['problems_planned']}")
        else:
            print("💤 No active session")
            
    elif args.analytics:
        analytics = session_manager.get_productivity_analytics()
        overview = analytics['overview']
        print(f"📊 Productivity Analytics ({analytics['period_days']} days)")
        print(f"Sessions: {overview['total_sessions']}")
        print(f"Total Time: {overview['total_time_formatted']}")
        print(f"Avg Session: {overview['avg_session_formatted']}")
        print(f"Avg Focus: {overview['avg_focus_score']}/10")
        print(f"Best Focus: {analytics['best_metrics']['best_focus_score']}/10")
        
    else:
        history = session_manager.get_session_history(days=args.history)
        print(f"📋 Recent Sessions ({len(history)} sessions)")
        for session in history[:5]:
            duration = session['actual_duration'] or 0
            duration_str = f"{duration // 60}m {duration % 60}s"
            print(f"  {session['start_time'][:16]} | {session['focus_mode']} | {duration_str} | Focus: {session['focus_score']}/10")
        
        print("\nUse --start to begin a session, --status for current status, --analytics for insights") 