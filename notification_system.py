#!/usr/bin/env python3
"""
Smart Notification System
Intelligent alerts, achievements, reminders, and engagement analytics
"""

import os
import sqlite3
import json
import smtplib
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import time
import schedule

class NotificationType(Enum):
    """Notification types"""
    ACHIEVEMENT = "achievement"
    REMINDER = "reminder"
    MILESTONE = "milestone"
    STREAK = "streak"
    REVIEW_DUE = "review_due"
    GOAL_PROGRESS = "goal_progress"
    RECOMMENDATION = "recommendation"
    SYSTEM = "system"

class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Notification:
    """Notification data structure"""
    id: Optional[int] = None
    type: NotificationType = NotificationType.SYSTEM
    priority: NotificationPriority = NotificationPriority.MEDIUM
    title: str = ""
    message: str = ""
    data: Dict[str, Any] = None
    recipient: str = "default"
    channels: List[str] = None  # ['email', 'push', 'in_app']
    scheduled_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    is_read: bool = False
    is_sent: bool = False
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.channels is None:
            self.channels = ['in_app']
        if self.created_at is None:
            self.created_at = datetime.now()

class SmartNotificationSystem:
    def __init__(self, db_path="practice_data/problems.db", config_path=None):
        self.db_path = Path(db_path)
        self.notifications_db_path = self.db_path.parent / "notifications.db"
        self.config_path = config_path or self.db_path.parent / "notification_config.json"
        
        # Setup logging
        self.setup_logging()
        
        # Initialize configuration
        self.config = self.load_config()
        
        # Initialize database
        self.init_database()
        
        # Notification handlers
        self.handlers = {
            'email': self._send_email,
            'push': self._send_push,
            'webhook': self._send_webhook,
            'in_app': self._store_in_app
        }
        
        # Achievement definitions
        self.achievements = self._load_achievements()
        
        # Scheduler for background tasks
        self.scheduler = schedule
        self._setup_scheduled_tasks()
        self._start_scheduler()
        
        logging.info("Smart Notification System initialized")
    
    def setup_logging(self):
        """Setup notification logging"""
        log_dir = self.db_path.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'notifications.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self) -> Dict[str, Any]:
        """Load notification configuration"""
        default_config = {
            'email': {
                'enabled': False,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'from_email': 'coding-practice@example.com',
                'from_name': 'Coding Practice System'
            },
            'push': {
                'enabled': False,
                'vapid_public_key': '',
                'vapid_private_key': '',
                'vapid_email': ''
            },
            'webhook': {
                'enabled': False,
                'default_url': '',
                'secret_key': ''
            },
            'reminders': {
                'enabled': True,
                'daily_reminder_time': '19:00',
                'weekly_summary_day': 'sunday',
                'weekly_summary_time': '09:00',
                'streak_reminder_threshold': 2
            },
            'achievements': {
                'enabled': True,
                'instant_notifications': True,
                'summary_notifications': True
            },
            'templates': {
                'achievement': {
                    'title': '🏆 Achievement Unlocked!',
                    'body': 'Congratulations! You earned: {achievement_name}'
                },
                'streak': {
                    'title': '🔥 Streak Alert!',
                    'body': 'You have a {streak_days} day streak! Keep it up!'
                },
                'reminder': {
                    'title': '📚 Time to Practice',
                    'body': 'You haven\'t practiced today. Ready to solve some problems?'
                },
                'milestone': {
                    'title': '🎯 Milestone Reached!',
                    'body': 'You\'ve completed {count} problems! Amazing progress!'
                }
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    # Deep merge configs
                    config = self._deep_merge(default_config, user_config)
                    return config
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
        
        # Save default config
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def init_database(self):
        """Initialize notifications database"""
        conn = sqlite3.connect(self.notifications_db_path)
        cursor = conn.cursor()
        
        # Notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                priority TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                data TEXT,
                recipient TEXT DEFAULT 'default',
                channels TEXT,
                scheduled_for DATETIME,
                expires_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                sent_at DATETIME,
                read_at DATETIME,
                is_read BOOLEAN DEFAULT 0,
                is_sent BOOLEAN DEFAULT 0
            )
        ''')
        
        # User preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default',
                notification_type TEXT,
                channel TEXT,
                enabled BOOLEAN DEFAULT 1,
                settings TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Achievements table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT DEFAULT 'default',
                achievement_key TEXT NOT NULL,
                achievement_name TEXT NOT NULL,
                description TEXT,
                earned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                progress INTEGER DEFAULT 0,
                target INTEGER DEFAULT 1,
                is_earned BOOLEAN DEFAULT 0,
                data TEXT
            )
        ''')
        
        # Notification analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_id INTEGER,
                event_type TEXT, -- sent, opened, clicked, dismissed
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                channel TEXT,
                user_agent TEXT,
                ip_address TEXT,
                data TEXT,
                FOREIGN KEY (notification_id) REFERENCES notifications (id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON notifications(recipient)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_scheduled ON notifications(scheduled_for)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_achievements_user ON achievements(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analytics_notification ON notification_analytics(notification_id)')
        
        conn.commit()
        conn.close()
    
    def _load_achievements(self) -> Dict[str, Dict]:
        """Load achievement definitions"""
        return {
            # Problem solving achievements
            'first_problem': {
                'name': 'First Steps',
                'description': 'Solve your first problem',
                'target': 1,
                'icon': '🎯',
                'points': 10
            },
            'problem_solver_10': {
                'name': 'Problem Solver',
                'description': 'Solve 10 problems',
                'target': 10,
                'icon': '💪',
                'points': 50
            },
            'problem_solver_50': {
                'name': 'Code Warrior',
                'description': 'Solve 50 problems',
                'target': 50,
                'icon': '⚔️',
                'points': 200
            },
            'problem_solver_100': {
                'name': 'Code Master',
                'description': 'Solve 100 problems',
                'target': 100,
                'icon': '👑',
                'points': 500
            },
            
            # Streak achievements
            'streak_3': {
                'name': 'Getting Started',
                'description': '3-day practice streak',
                'target': 3,
                'icon': '🔥',
                'points': 25
            },
            'streak_7': {
                'name': 'Week Warrior',
                'description': '7-day practice streak',
                'target': 7,
                'icon': '🔥',
                'points': 75
            },
            'streak_30': {
                'name': 'Dedication Master',
                'description': '30-day practice streak',
                'target': 30,
                'icon': '🔥',
                'points': 300
            },
            
            # Speed achievements
            'speed_demon': {
                'name': 'Speed Demon',
                'description': 'Solve a problem in under 10 minutes',
                'target': 1,
                'icon': '⚡',
                'points': 30
            },
            'lightning_fast': {
                'name': 'Lightning Fast',
                'description': 'Solve a problem in under 5 minutes',
                'target': 1,
                'icon': '⚡',
                'points': 50
            },
            
            # Difficulty achievements
            'medium_master': {
                'name': 'Medium Master',
                'description': 'Solve 20 medium problems',
                'target': 20,
                'icon': '🎖️',
                'points': 150
            },
            'hard_hero': {
                'name': 'Hard Hero',
                'description': 'Solve 10 hard problems',
                'target': 10,
                'icon': '🏆',
                'points': 200
            },
            
            # Topic achievements
            'array_expert': {
                'name': 'Array Expert',
                'description': 'Solve 15 array problems',
                'target': 15,
                'icon': '📊',
                'points': 100
            },
            'tree_master': {
                'name': 'Tree Master',
                'description': 'Solve 10 tree problems',
                'target': 10,
                'icon': '🌳',
                'points': 120
            },
            'graph_guru': {
                'name': 'Graph Guru',
                'description': 'Solve 8 graph problems',
                'target': 8,
                'icon': '🕸️',
                'points': 150
            },
            
            # Special achievements
            'night_owl': {
                'name': 'Night Owl',
                'description': 'Solve problems after midnight',
                'target': 5,
                'icon': '🦉',
                'points': 40
            },
            'early_bird': {
                'name': 'Early Bird',
                'description': 'Solve problems before 6 AM',
                'target': 5,
                'icon': '🐦',
                'points': 40
            },
            'perfectionist': {
                'name': 'Perfectionist',
                'description': 'Solve 10 problems on first attempt',
                'target': 10,
                'icon': '💎',
                'points': 100
            }
        }
    
    def send_notification(self, notification: Notification) -> bool:
        """Send a notification through specified channels"""
        try:
            # Store in database
            notification_id = self._save_notification(notification)
            notification.id = notification_id
            
            # Check if should be sent now or scheduled
            if notification.scheduled_for and notification.scheduled_for > datetime.now():
                self.logger.info(f"Notification {notification_id} scheduled for {notification.scheduled_for}")
                return True
            
            # Send through all specified channels
            success = True
            for channel in notification.channels:
                if channel in self.handlers:
                    try:
                        channel_success = self.handlers[channel](notification)
                        if not channel_success:
                            success = False
                        else:
                            self._track_analytics(notification.id, 'sent', channel)
                    except Exception as e:
                        self.logger.error(f"Error sending notification via {channel}: {e}")
                        success = False
            
            # Update sent status
            if success:
                self._update_notification_status(notification.id, sent_at=datetime.now(), is_sent=True)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")
            return False
    
    def create_achievement_notification(self, achievement_key: str, user_id: str = "default") -> Optional[Notification]:
        """Create achievement notification"""
        if achievement_key not in self.achievements:
            return None
        
        achievement = self.achievements[achievement_key]
        template = self.config['templates']['achievement']
        
        return Notification(
            type=NotificationType.ACHIEVEMENT,
            priority=NotificationPriority.HIGH,
            title=template['title'],
            message=template['body'].format(achievement_name=achievement['name']),
            data={
                'achievement_key': achievement_key,
                'achievement': achievement,
                'points_earned': achievement['points']
            },
            recipient=user_id,
            channels=['in_app', 'push'] if self.config['push']['enabled'] else ['in_app']
        )
    
    def create_streak_notification(self, streak_days: int, user_id: str = "default") -> Notification:
        """Create streak notification"""
        template = self.config['templates']['streak']
        
        # Determine priority based on streak
        if streak_days >= 30:
            priority = NotificationPriority.CRITICAL
        elif streak_days >= 7:
            priority = NotificationPriority.HIGH
        else:
            priority = NotificationPriority.MEDIUM
        
        return Notification(
            type=NotificationType.STREAK,
            priority=priority,
            title=template['title'],
            message=template['body'].format(streak_days=streak_days),
            data={
                'streak_days': streak_days,
                'streak_type': 'daily'
            },
            recipient=user_id,
            channels=['in_app', 'push'] if streak_days % 7 == 0 else ['in_app']
        )
    
    def create_reminder_notification(self, user_id: str = "default", custom_message: str = None) -> Notification:
        """Create practice reminder notification"""
        template = self.config['templates']['reminder']
        
        message = custom_message if custom_message else template['body']
        
        return Notification(
            type=NotificationType.REMINDER,
            priority=NotificationPriority.MEDIUM,
            title=template['title'],
            message=message,
            data={
                'reminder_type': 'daily_practice',
                'suggested_problems': 2
            },
            recipient=user_id,
            channels=['push'] if self.config['push']['enabled'] else ['in_app']
        )
    
    def create_milestone_notification(self, milestone_type: str, count: int, user_id: str = "default") -> Notification:
        """Create milestone notification"""
        template = self.config['templates']['milestone']
        
        return Notification(
            type=NotificationType.MILESTONE,
            priority=NotificationPriority.HIGH,
            title=template['title'],
            message=template['body'].format(count=count),
            data={
                'milestone_type': milestone_type,
                'count': count
            },
            recipient=user_id,
            channels=['in_app', 'email'] if count % 50 == 0 else ['in_app']
        )
    
    def create_review_due_notification(self, due_count: int, user_id: str = "default") -> Notification:
        """Create spaced repetition review notification"""
        return Notification(
            type=NotificationType.REVIEW_DUE,
            priority=NotificationPriority.HIGH,
            title="📝 Reviews Due",
            message=f"You have {due_count} problems ready for review!",
            data={
                'due_count': due_count,
                'review_type': 'spaced_repetition'
            },
            recipient=user_id,
            channels=['in_app', 'push']
        )
    
    def check_and_award_achievements(self, user_id: str = "default", event_data: Dict = None):
        """Check for new achievements and award them"""
        if not self.config['achievements']['enabled']:
            return
        
        try:
            user_stats = self._get_user_stats(user_id)
            new_achievements = []
            
            # Check each achievement
            for achievement_key, achievement_def in self.achievements.items():
                if not self._is_achievement_earned(user_id, achievement_key):
                    if self._check_achievement_criteria(achievement_key, user_stats, event_data):
                        self._award_achievement(user_id, achievement_key)
                        new_achievements.append(achievement_key)
            
            # Send notifications for new achievements
            if new_achievements and self.config['achievements']['instant_notifications']:
                for achievement_key in new_achievements:
                    notification = self.create_achievement_notification(achievement_key, user_id)
                    if notification:
                        self.send_notification(notification)
            
            return new_achievements
            
        except Exception as e:
            self.logger.error(f"Error checking achievements: {e}")
            return []
    
    def get_notifications(self, user_id: str = "default", limit: int = 50, unread_only: bool = False) -> List[Dict]:
        """Get notifications for user"""
        conn = sqlite3.connect(self.notifications_db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT id, type, priority, title, message, data, channels,
                   scheduled_for, expires_at, created_at, sent_at, read_at,
                   is_read, is_sent
            FROM notifications
            WHERE recipient = ?
        '''
        params = [user_id]
        
        if unread_only:
            query += ' AND is_read = 0'
        
        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        
        notifications = []
        for row in cursor.fetchall():
            notifications.append({
                'id': row[0],
                'type': row[1],
                'priority': row[2],
                'title': row[3],
                'message': row[4],
                'data': json.loads(row[5]) if row[5] else {},
                'channels': json.loads(row[6]) if row[6] else [],
                'scheduled_for': row[7],
                'expires_at': row[8],
                'created_at': row[9],
                'sent_at': row[10],
                'read_at': row[11],
                'is_read': bool(row[12]),
                'is_sent': bool(row[13])
            })
        
        conn.close()
        return notifications
    
    def mark_notification_read(self, notification_id: int, user_id: str = "default") -> bool:
        """Mark notification as read"""
        try:
            self._update_notification_status(notification_id, read_at=datetime.now(), is_read=True)
            self._track_analytics(notification_id, 'read', 'in_app')
            return True
        except Exception as e:
            self.logger.error(f"Error marking notification as read: {e}")
            return False
    
    def get_user_achievements(self, user_id: str = "default") -> List[Dict]:
        """Get user achievements"""
        conn = sqlite3.connect(self.notifications_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT achievement_key, achievement_name, description, earned_at, 
                   progress, target, is_earned, data
            FROM achievements
            WHERE user_id = ?
            ORDER BY earned_at DESC, achievement_key
        ''', (user_id,))
        
        achievements = []
        for row in cursor.fetchall():
            achievements.append({
                'key': row[0],
                'name': row[1],
                'description': row[2],
                'earned_at': row[3],
                'progress': row[4],
                'target': row[5],
                'is_earned': bool(row[6]),
                'data': json.loads(row[7]) if row[7] else {}
            })
        
        conn.close()
        return achievements
    
    def get_notification_analytics(self, days: int = 30) -> Dict:
        """Get notification analytics"""
        conn = sqlite3.connect(self.notifications_db_path)
        cursor = conn.cursor()
        
        # Total notifications sent
        cursor.execute('''
            SELECT COUNT(*) FROM notifications 
            WHERE sent_at >= DATE('now', '-{} days')
        '''.format(days))
        total_sent = cursor.fetchone()[0]
        
        # Notifications by type
        cursor.execute('''
            SELECT type, COUNT(*) as count
            FROM notifications 
            WHERE sent_at >= DATE('now', '-{} days')
            GROUP BY type
            ORDER BY count DESC
        '''.format(days))
        by_type = dict(cursor.fetchall())
        
        # Read rate
        cursor.execute('''
            SELECT 
                COUNT(CASE WHEN is_read = 1 THEN 1 END) as read_count,
                COUNT(*) as total_count
            FROM notifications 
            WHERE sent_at >= DATE('now', '-{} days')
        '''.format(days))
        read_data = cursor.fetchone()
        read_rate = (read_data[0] / read_data[1] * 100) if read_data[1] > 0 else 0
        
        # Channel performance
        cursor.execute('''
            SELECT channel, COUNT(*) as count
            FROM notification_analytics 
            WHERE timestamp >= DATE('now', '-{} days')
            AND event_type = 'sent'
            GROUP BY channel
        '''.format(days))
        channel_performance = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_sent': total_sent,
            'by_type': by_type,
            'read_rate': round(read_rate, 2),
            'channel_performance': channel_performance,
            'period_days': days
        }
    
    def _setup_scheduled_tasks(self):
        """Setup scheduled notification tasks"""
        if self.config['reminders']['enabled']:
            # Daily reminder
            self.scheduler.every().day.at(
                self.config['reminders']['daily_reminder_time']
            ).do(self._send_daily_reminders)
            
            # Weekly summary
            getattr(self.scheduler.every(), self.config['reminders']['weekly_summary_day']).at(
                self.config['reminders']['weekly_summary_time']
            ).do(self._send_weekly_summary)
    
    def _start_scheduler(self):
        """Start the notification scheduler"""
        def run_scheduler():
            while True:
                self.scheduler.run_pending()
                time.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
    
    def _send_daily_reminders(self):
        """Send daily practice reminders"""
        try:
            # Check who hasn't practiced today
            users_to_remind = self._get_users_needing_reminders()
            
            for user_id in users_to_remind:
                reminder = self.create_reminder_notification(user_id)
                self.send_notification(reminder)
                
            self.logger.info(f"Sent daily reminders to {len(users_to_remind)} users")
            
        except Exception as e:
            self.logger.error(f"Error sending daily reminders: {e}")
    
    def _send_weekly_summary(self):
        """Send weekly summary notifications"""
        try:
            users = self._get_all_users()
            
            for user_id in users:
                summary = self._generate_weekly_summary(user_id)
                if summary:
                    notification = Notification(
                        type=NotificationType.SYSTEM,
                        priority=NotificationPriority.MEDIUM,
                        title="📊 Weekly Summary",
                        message=summary,
                        recipient=user_id,
                        channels=['email'] if self.config['email']['enabled'] else ['in_app']
                    )
                    self.send_notification(notification)
                    
            self.logger.info(f"Sent weekly summaries to {len(users)} users")
            
        except Exception as e:
            self.logger.error(f"Error sending weekly summaries: {e}")
    
    # Notification handlers
    def _send_email(self, notification: Notification) -> bool:
        """Send email notification"""
        if not self.config['email']['enabled']:
            return False
        
        try:
            config = self.config['email']
            
            msg = MIMEMultipart()
            msg['From'] = f"{config['from_name']} <{config['from_email']}>"
            msg['To'] = notification.recipient  # Assuming recipient is email
            msg['Subject'] = notification.title
            
            body = notification.message
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
            server.login(config['username'], config['password'])
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
            return False
    
    def _send_push(self, notification: Notification) -> bool:
        """Send push notification"""
        if not self.config['push']['enabled']:
            return False
        
        # This would integrate with a push service like Firebase FCM
        # For now, return True as placeholder
        self.logger.info(f"Push notification sent: {notification.title}")
        return True
    
    def _send_webhook(self, notification: Notification) -> bool:
        """Send webhook notification"""
        if not self.config['webhook']['enabled']:
            return False
        
        try:
            payload = {
                'id': notification.id,
                'type': notification.type.value,
                'title': notification.title,
                'message': notification.message,
                'data': notification.data,
                'timestamp': notification.created_at.isoformat()
            }
            
            response = requests.post(
                self.config['webhook']['default_url'],
                json=payload,
                headers={'X-Secret': self.config['webhook']['secret_key']},
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Error sending webhook: {e}")
            return False
    
    def _store_in_app(self, notification: Notification) -> bool:
        """Store in-app notification (already stored, just return True)"""
        return True
    
    # Helper methods
    def _save_notification(self, notification: Notification) -> int:
        """Save notification to database"""
        conn = sqlite3.connect(self.notifications_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notifications 
            (type, priority, title, message, data, recipient, channels, 
             scheduled_for, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            notification.type.value,
            notification.priority.value,
            notification.title,
            notification.message,
            json.dumps(notification.data),
            notification.recipient,
            json.dumps(notification.channels),
            notification.scheduled_for,
            notification.expires_at,
            notification.created_at
        ))
        
        notification_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return notification_id
    
    def _update_notification_status(self, notification_id: int, **kwargs):
        """Update notification status"""
        conn = sqlite3.connect(self.notifications_db_path)
        cursor = conn.cursor()
        
        set_clauses = []
        params = []
        
        for key, value in kwargs.items():
            set_clauses.append(f"{key} = ?")
            params.append(value)
        
        if set_clauses:
            query = f"UPDATE notifications SET {', '.join(set_clauses)} WHERE id = ?"
            params.append(notification_id)
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
    
    def _track_analytics(self, notification_id: int, event_type: str, channel: str, **kwargs):
        """Track notification analytics"""
        conn = sqlite3.connect(self.notifications_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notification_analytics 
            (notification_id, event_type, channel, data)
            VALUES (?, ?, ?, ?)
        ''', (notification_id, event_type, channel, json.dumps(kwargs)))
        
        conn.commit()
        conn.close()
    
    def _get_user_stats(self, user_id: str) -> Dict:
        """Get user statistics for achievement checking"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total problems solved
            cursor.execute('''
                SELECT COUNT(*) FROM progress 
                WHERE status = 'completed'
            ''')
            total_solved = cursor.fetchone()[0]
            
            # Problems by difficulty
            cursor.execute('''
                SELECT p.difficulty, COUNT(*) as count
                FROM progress pr
                JOIN problems p ON pr.problem_id = p.id
                WHERE pr.status = 'completed'
                GROUP BY p.difficulty
            ''')
            by_difficulty = dict(cursor.fetchall())
            
            # Problems by topic
            cursor.execute('''
                SELECT p.topic, COUNT(*) as count
                FROM progress pr
                JOIN problems p ON pr.problem_id = p.id
                WHERE pr.status = 'completed'
                GROUP BY p.topic
            ''')
            by_topic = dict(cursor.fetchall())
            
            # Streak information
            cursor.execute('''
                SELECT DISTINCT DATE(completed_at) as date
                FROM progress
                WHERE status = 'completed'
                ORDER BY date DESC
                LIMIT 50
            ''')
            
            dates = [row[0] for row in cursor.fetchall()]
            current_streak = self._calculate_streak(dates)
            
            conn.close()
            
            return {
                'total_solved': total_solved,
                'by_difficulty': by_difficulty,
                'by_topic': by_topic,
                'current_streak': current_streak
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user stats: {e}")
            return {}
    
    def _calculate_streak(self, dates: List[str]) -> int:
        """Calculate current streak from dates"""
        if not dates:
            return 0
        
        streak = 1
        current_date = datetime.strptime(dates[0], '%Y-%m-%d').date()
        
        for i in range(1, len(dates)):
            prev_date = datetime.strptime(dates[i], '%Y-%m-%d').date()
            if (current_date - prev_date).days == 1:
                streak += 1
                current_date = prev_date
            else:
                break
        
        # Check if streak is current (today or yesterday)
        today = datetime.now().date()
        if (today - current_date).days > 1:
            streak = 0
        
        return streak
    
    def _check_achievement_criteria(self, achievement_key: str, user_stats: Dict, event_data: Dict = None) -> bool:
        """Check if achievement criteria is met"""
        achievement = self.achievements[achievement_key]
        target = achievement['target']
        
        if achievement_key.startswith('problem_solver_'):
            return user_stats.get('total_solved', 0) >= target
        
        elif achievement_key.startswith('streak_'):
            return user_stats.get('current_streak', 0) >= target
        
        elif achievement_key == 'speed_demon':
            # Check if any recent problem was solved in under 10 minutes
            return event_data and event_data.get('time_spent', 999) < 600
        
        elif achievement_key == 'lightning_fast':
            # Check if any recent problem was solved in under 5 minutes
            return event_data and event_data.get('time_spent', 999) < 300
        
        elif achievement_key == 'medium_master':
            return user_stats.get('by_difficulty', {}).get('medium', 0) >= target
        
        elif achievement_key == 'hard_hero':
            return user_stats.get('by_difficulty', {}).get('hard', 0) >= target
        
        elif achievement_key in ['array_expert', 'tree_master', 'graph_guru']:
            topic = achievement_key.split('_')[0]
            return user_stats.get('by_topic', {}).get(topic, 0) >= target
        
        # Add more criteria as needed
        return False
    
    def _is_achievement_earned(self, user_id: str, achievement_key: str) -> bool:
        """Check if achievement is already earned"""
        conn = sqlite3.connect(self.notifications_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT is_earned FROM achievements
            WHERE user_id = ? AND achievement_key = ?
        ''', (user_id, achievement_key))
        
        result = cursor.fetchone()
        conn.close()
        
        return result and bool(result[0])
    
    def _award_achievement(self, user_id: str, achievement_key: str):
        """Award achievement to user"""
        achievement = self.achievements[achievement_key]
        
        conn = sqlite3.connect(self.notifications_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO achievements
            (user_id, achievement_key, achievement_name, description, 
             progress, target, is_earned, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            achievement_key,
            achievement['name'],
            achievement['description'],
            achievement['target'],
            achievement['target'],
            True,
            json.dumps(achievement)
        ))
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Achievement '{achievement_key}' awarded to user {user_id}")
    
    def _get_users_needing_reminders(self) -> List[str]:
        """Get users who need practice reminders"""
        # This would check who hasn't practiced today
        # For now, return default user
        return ["default"]
    
    def _get_all_users(self) -> List[str]:
        """Get all users"""
        # For now, return default user
        return ["default"]
    
    def _generate_weekly_summary(self, user_id: str) -> str:
        """Generate weekly summary for user"""
        try:
            stats = self._get_user_stats(user_id)
            return f"This week you solved {stats.get('total_solved', 0)} problems! Keep up the great work!"
        except:
            return ""
    
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
    
    parser = argparse.ArgumentParser(description="Smart Notification System")
    parser.add_argument('--test-notification', action='store_true', help='Send test notification')
    parser.add_argument('--check-achievements', action='store_true', help='Check for new achievements')
    parser.add_argument('--analytics', action='store_true', help='Show notification analytics')
    
    args = parser.parse_args()
    
    notification_system = SmartNotificationSystem()
    
    if args.test_notification:
        test_notification = Notification(
            type=NotificationType.SYSTEM,
            priority=NotificationPriority.MEDIUM,
            title="🧪 Test Notification",
            message="This is a test notification from the Smart Notification System!",
            channels=['in_app']
        )
        
        success = notification_system.send_notification(test_notification)
        print(f"Test notification sent: {success}")
    
    elif args.check_achievements:
        achievements = notification_system.check_and_award_achievements()
        print(f"New achievements: {achievements}")
    
    elif args.analytics:
        analytics = notification_system.get_notification_analytics()
        print(json.dumps(analytics, indent=2))
    
    else:
        print("Smart Notification System")
        print("Use --test-notification, --check-achievements, or --analytics") 