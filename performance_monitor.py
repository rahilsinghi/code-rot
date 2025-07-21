#!/usr/bin/env python3
"""
Enhanced Performance Monitoring System
Comprehensive system health, database optimization, and user performance analytics
"""

import os
import sys
import time
import psutil
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from collections import defaultdict, deque
import threading

class PerformanceMonitor:
    def __init__(self, db_path="practice_data/problems.db"):
        self.db_path = Path(db_path)
        self.monitor_db_path = self.db_path.parent / "performance_metrics.db"
        self.config_path = self.db_path.parent / "monitor_config.json"
        
        # Performance metrics storage
        self.metrics_buffer = deque(maxlen=1000)
        self.query_times = deque(maxlen=100)
        self.system_stats = deque(maxlen=60)  # 1 minute of data at 1-second intervals
        
        # Setup logging
        self.setup_logging()
        
        # Initialize monitoring database
        self.init_monitoring_db()
        
        # Load configuration
        self.load_config()
        
        # Start background monitoring
        self.start_background_monitoring()
    
    def setup_logging(self):
        """Setup performance monitoring logging"""
        log_dir = self.db_path.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'performance.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self):
        """Load monitoring configuration"""
        default_config = {
            "monitoring_enabled": True,
            "system_monitoring_interval": 60,  # seconds
            "database_monitoring": True,
            "query_performance_tracking": True,
            "alert_thresholds": {
                "cpu_usage": 85,
                "memory_usage": 90,
                "disk_usage": 85,
                "query_time_ms": 1000,
                "database_size_mb": 500
            },
            "retention_days": 30,
            "optimization_suggestions": True,
            "performance_reports": True
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                self.logger.warning(f"Could not load monitor config: {e}")
        
        self.config = default_config
        self.save_config()
    
    def save_config(self):
        """Save monitoring configuration"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def init_monitoring_db(self):
        """Initialize performance monitoring database"""
        conn = sqlite3.connect(self.monitor_db_path)
        cursor = conn.cursor()
        
        # System performance metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cpu_percent REAL,
                memory_percent REAL,
                memory_used_mb REAL,
                disk_percent REAL,
                disk_free_gb REAL,
                network_sent_mb REAL,
                network_recv_mb REAL
            )
        ''')
        
        # Database performance metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS db_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                query_type TEXT,
                query_time_ms REAL,
                rows_affected INTEGER,
                database_size_mb REAL,
                table_name TEXT
            )
        ''')
        
        # User performance analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metric_type TEXT,
                metric_value REAL,
                language TEXT,
                topic TEXT,
                difficulty TEXT,
                metadata TEXT
            )
        ''')
        
        # Performance alerts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                alert_type TEXT,
                severity TEXT,
                message TEXT,
                resolved BOOLEAN DEFAULT FALSE,
                resolution_time DATETIME
            )
        ''')
        
        # Create indexes for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_db_metrics_timestamp ON db_metrics(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_metrics_timestamp ON user_metrics(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON performance_alerts(timestamp)')
        
        conn.commit()
        conn.close()
    
    def start_background_monitoring(self):
        """Start background system monitoring thread"""
        if not self.config.get("monitoring_enabled", True):
            return
        
        def monitor_system():
            while True:
                try:
                    self.collect_system_metrics()
                    time.sleep(self.config.get("system_monitoring_interval", 60))
                except Exception as e:
                    self.logger.error(f"System monitoring error: {e}")
                    time.sleep(60)
        
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
        self.logger.info("Background system monitoring started")
    
    def collect_system_metrics(self):
        """Collect current system performance metrics"""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Disk usage for the database directory
            disk = psutil.disk_usage(self.db_path.parent)
            
            # Network statistics
            network = psutil.net_io_counters()
            
            # Database size
            db_size_mb = self.get_database_size()
            
            metrics = {
                'timestamp': datetime.now(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_mb': memory.used / (1024 * 1024),
                'disk_percent': (disk.used / disk.total) * 100,
                'disk_free_gb': disk.free / (1024 * 1024 * 1024),
                'network_sent_mb': network.bytes_sent / (1024 * 1024),
                'network_recv_mb': network.bytes_recv / (1024 * 1024),
                'database_size_mb': db_size_mb
            }
            
            # Store in buffer for real-time access
            self.system_stats.append(metrics)
            
            # Store in database
            self.store_system_metrics(metrics)
            
            # Check for alerts
            self.check_system_alerts(metrics)
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    def store_system_metrics(self, metrics: Dict):
        """Store system metrics in database"""
        try:
            conn = sqlite3.connect(self.monitor_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_metrics 
                (cpu_percent, memory_percent, memory_used_mb, disk_percent, disk_free_gb, 
                 network_sent_mb, network_recv_mb)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics['cpu_percent'], metrics['memory_percent'], metrics['memory_used_mb'],
                metrics['disk_percent'], metrics['disk_free_gb'], metrics['network_sent_mb'],
                metrics['network_recv_mb']
            ))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            self.logger.error(f"Error storing system metrics: {e}")
    
    def track_query_performance(self, query_type: str, query_time: float, 
                              rows_affected: int = 0, table_name: str = ""):
        """Track database query performance"""
        if not self.config.get("query_performance_tracking", True):
            return
        
        try:
            query_time_ms = query_time * 1000
            self.query_times.append(query_time_ms)
            
            # Store in database
            conn = sqlite3.connect(self.monitor_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO db_metrics 
                (query_type, query_time_ms, rows_affected, database_size_mb, table_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (query_type, query_time_ms, rows_affected, self.get_database_size(), table_name))
            
            conn.commit()
            conn.close()
            
            # Check for slow query alerts
            threshold = self.config["alert_thresholds"]["query_time_ms"]
            if query_time_ms > threshold:
                self.create_alert("slow_query", "warning", 
                                f"Slow query detected: {query_type} took {query_time_ms:.2f}ms")
        
        except Exception as e:
            self.logger.error(f"Error tracking query performance: {e}")
    
    def track_user_performance(self, metric_type: str, value: float, 
                             language: str = "", topic: str = "", 
                             difficulty: str = "", metadata: Dict = None):
        """Track user performance metrics"""
        try:
            conn = sqlite3.connect(self.monitor_db_path)
            cursor = conn.cursor()
            
            metadata_json = json.dumps(metadata) if metadata else ""
            
            cursor.execute('''
                INSERT INTO user_metrics 
                (metric_type, metric_value, language, topic, difficulty, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (metric_type, value, language, topic, difficulty, metadata_json))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            self.logger.error(f"Error tracking user performance: {e}")
    
    def get_database_size(self) -> float:
        """Get database size in MB"""
        try:
            if self.db_path.exists():
                size_bytes = self.db_path.stat().st_size
                return size_bytes / (1024 * 1024)
            return 0
        except Exception:
            return 0
    
    def check_system_alerts(self, metrics: Dict):
        """Check system metrics against alert thresholds"""
        thresholds = self.config["alert_thresholds"]
        
        # CPU usage alert
        if metrics['cpu_percent'] > thresholds["cpu_usage"]:
            self.create_alert("high_cpu", "warning", 
                            f"High CPU usage: {metrics['cpu_percent']:.1f}%")
        
        # Memory usage alert
        if metrics['memory_percent'] > thresholds["memory_usage"]:
            self.create_alert("high_memory", "warning", 
                            f"High memory usage: {metrics['memory_percent']:.1f}%")
        
        # Disk usage alert
        if metrics['disk_percent'] > thresholds["disk_usage"]:
            self.create_alert("high_disk", "warning", 
                            f"High disk usage: {metrics['disk_percent']:.1f}%")
        
        # Database size alert
        if metrics['database_size_mb'] > thresholds["database_size_mb"]:
            self.create_alert("large_database", "info", 
                            f"Database size: {metrics['database_size_mb']:.1f}MB")
    
    def create_alert(self, alert_type: str, severity: str, message: str):
        """Create a performance alert"""
        try:
            conn = sqlite3.connect(self.monitor_db_path)
            cursor = conn.cursor()
            
            # Check if similar alert exists and is unresolved
            cursor.execute('''
                SELECT id FROM performance_alerts 
                WHERE alert_type = ? AND resolved = FALSE 
                AND timestamp > datetime('now', '-1 hour')
            ''', (alert_type,))
            
            if cursor.fetchone():
                conn.close()
                return  # Don't spam similar alerts
            
            cursor.execute('''
                INSERT INTO performance_alerts (alert_type, severity, message)
                VALUES (?, ?, ?)
            ''', (alert_type, severity, message))
            
            conn.commit()
            conn.close()
            
            self.logger.warning(f"Alert created: {message}")
        
        except Exception as e:
            self.logger.error(f"Error creating alert: {e}")
    
    def get_system_health_report(self) -> Dict:
        """Generate comprehensive system health report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'system_status': 'healthy',
                'alerts': [],
                'performance_summary': {},
                'recommendations': [],
                'database_health': {}
            }
            
            # Get recent system metrics
            if self.system_stats:
                recent_metrics = list(self.system_stats)[-10:]  # Last 10 readings
                
                avg_cpu = sum(m['cpu_percent'] for m in recent_metrics) / len(recent_metrics)
                avg_memory = sum(m['memory_percent'] for m in recent_metrics) / len(recent_metrics)
                avg_disk = sum(m['disk_percent'] for m in recent_metrics) / len(recent_metrics)
                
                report['performance_summary'] = {
                    'avg_cpu_percent': round(avg_cpu, 2),
                    'avg_memory_percent': round(avg_memory, 2),
                    'avg_disk_percent': round(avg_disk, 2),
                    'database_size_mb': round(self.get_database_size(), 2)
                }
                
                # Determine system status
                if avg_cpu > 80 or avg_memory > 85 or avg_disk > 80:
                    report['system_status'] = 'warning'
                if avg_cpu > 95 or avg_memory > 95 or avg_disk > 95:
                    report['system_status'] = 'critical'
            
            # Get recent alerts
            report['alerts'] = self.get_recent_alerts()
            
            # Get database health
            report['database_health'] = self.get_database_health()
            
            # Generate recommendations
            report['recommendations'] = self.generate_performance_recommendations()
            
            return report
        
        except Exception as e:
            self.logger.error(f"Error generating system health report: {e}")
            return {'error': str(e)}
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """Get recent performance alerts"""
        try:
            conn = sqlite3.connect(self.monitor_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT alert_type, severity, message, timestamp, resolved
                FROM performance_alerts 
                WHERE timestamp > datetime('now', '-{} hours')
                ORDER BY timestamp DESC
                LIMIT 20
            '''.format(hours))
            
            alerts = []
            for row in cursor.fetchall():
                alerts.append({
                    'type': row[0],
                    'severity': row[1],
                    'message': row[2],
                    'timestamp': row[3],
                    'resolved': bool(row[4])
                })
            
            conn.close()
            return alerts
        
        except Exception as e:
            self.logger.error(f"Error getting recent alerts: {e}")
            return []
    
    def get_database_health(self) -> Dict:
        """Analyze database health and performance"""
        try:
            health = {
                'size_mb': self.get_database_size(),
                'query_performance': {},
                'table_stats': {},
                'optimization_needed': False
            }
            
            # Query performance analysis
            if self.query_times:
                query_times = list(self.query_times)
                health['query_performance'] = {
                    'avg_query_time_ms': round(sum(query_times) / len(query_times), 2),
                    'max_query_time_ms': round(max(query_times), 2),
                    'slow_queries_count': len([t for t in query_times if t > 500])
                }
            
            # Table statistics
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get table sizes
            tables = ['problems', 'progress']
            for table in tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                health['table_stats'][table] = {'row_count': count}
            
            conn.close()
            
            # Determine if optimization is needed
            if (health['size_mb'] > 100 or 
                health['query_performance'].get('avg_query_time_ms', 0) > 100):
                health['optimization_needed'] = True
            
            return health
        
        except Exception as e:
            self.logger.error(f"Error analyzing database health: {e}")
            return {'error': str(e)}
    
    def generate_performance_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        try:
            # System performance recommendations
            if self.system_stats:
                recent_stats = list(self.system_stats)[-5:]
                avg_cpu = sum(s['cpu_percent'] for s in recent_stats) / len(recent_stats)
                avg_memory = sum(s['memory_percent'] for s in recent_stats) / len(recent_stats)
                
                if avg_cpu > 70:
                    recommendations.append("High CPU usage detected. Consider optimizing database queries or reducing concurrent operations.")
                
                if avg_memory > 80:
                    recommendations.append("High memory usage. Consider implementing query result caching or pagination for large datasets.")
                
                db_size = self.get_database_size()
                if db_size > 200:
                    recommendations.append(f"Database size is {db_size:.1f}MB. Consider archiving old data or implementing data retention policies.")
            
            # Query performance recommendations
            if self.query_times:
                avg_query_time = sum(self.query_times) / len(self.query_times)
                if avg_query_time > 200:
                    recommendations.append("Slow query performance detected. Consider adding database indexes or optimizing complex queries.")
            
            # Database optimization recommendations
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check for missing indexes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            existing_indexes = [row[0] for row in cursor.fetchall()]
            
            recommended_indexes = [
                'idx_progress_completed_at',
                'idx_problems_difficulty_topic',
                'idx_progress_problem_language'
            ]
            
            missing_indexes = [idx for idx in recommended_indexes if idx not in existing_indexes]
            if missing_indexes:
                recommendations.append(f"Consider adding database indexes: {', '.join(missing_indexes)}")
            
            conn.close()
            
            if not recommendations:
                recommendations.append("System performance is optimal. No immediate optimizations needed.")
            
            return recommendations
        
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return ["Error generating performance recommendations"]
    
    def optimize_database(self):
        """Perform database optimization operations"""
        try:
            self.logger.info("Starting database optimization...")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Vacuum database to reclaim space
            self.logger.info("Vacuuming database...")
            cursor.execute('VACUUM')
            
            # Analyze tables for query optimization
            self.logger.info("Analyzing tables...")
            cursor.execute('ANALYZE')
            
            # Create missing indexes
            recommended_indexes = {
                'idx_progress_completed_at_lang': 'CREATE INDEX IF NOT EXISTS idx_progress_completed_at_lang ON progress(completed_at, language)',
                'idx_problems_topic_diff': 'CREATE INDEX IF NOT EXISTS idx_problems_topic_diff ON problems(topic, difficulty)',
                'idx_progress_status_lang': 'CREATE INDEX IF NOT EXISTS idx_progress_status_lang ON progress(status, language)'
            }
            
            for index_name, index_sql in recommended_indexes.items():
                self.logger.info(f"Creating index: {index_name}")
                cursor.execute(index_sql)
            
            conn.commit()
            conn.close()
            
            # Clean up old monitoring data
            self.cleanup_old_metrics()
            
            self.logger.info("Database optimization completed")
            
        except Exception as e:
            self.logger.error(f"Error optimizing database: {e}")
    
    def cleanup_old_metrics(self):
        """Clean up old performance metrics"""
        try:
            retention_days = self.config.get("retention_days", 30)
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            conn = sqlite3.connect(self.monitor_db_path)
            cursor = conn.cursor()
            
            # Clean up old system metrics
            cursor.execute('DELETE FROM system_metrics WHERE timestamp < ?', (cutoff_date,))
            deleted_system = cursor.rowcount
            
            # Clean up old database metrics
            cursor.execute('DELETE FROM db_metrics WHERE timestamp < ?', (cutoff_date,))
            deleted_db = cursor.rowcount
            
            # Clean up resolved alerts older than 7 days
            alert_cutoff = datetime.now() - timedelta(days=7)
            cursor.execute('DELETE FROM performance_alerts WHERE timestamp < ? AND resolved = TRUE', (alert_cutoff,))
            deleted_alerts = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Cleaned up old metrics: {deleted_system} system, {deleted_db} database, {deleted_alerts} alerts")
        
        except Exception as e:
            self.logger.error(f"Error cleaning up old metrics: {e}")
    
    def get_performance_analytics(self, days: int = 7) -> Dict:
        """Get detailed performance analytics"""
        try:
            analytics = {
                'period_days': days,
                'system_trends': {},
                'database_trends': {},
                'user_performance': {},
                'bottlenecks': [],
                'improvements': []
            }
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # System performance trends
            conn = sqlite3.connect(self.monitor_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    AVG(cpu_percent) as avg_cpu,
                    MAX(cpu_percent) as max_cpu,
                    AVG(memory_percent) as avg_memory,
                    MAX(memory_percent) as max_memory,
                    AVG(disk_percent) as avg_disk
                FROM system_metrics 
                WHERE timestamp > ?
            ''', (cutoff_date,))
            
            system_data = cursor.fetchone()
            if system_data:
                analytics['system_trends'] = {
                    'avg_cpu_percent': round(system_data[0] or 0, 2),
                    'max_cpu_percent': round(system_data[1] or 0, 2),
                    'avg_memory_percent': round(system_data[2] or 0, 2),
                    'max_memory_percent': round(system_data[3] or 0, 2),
                    'avg_disk_percent': round(system_data[4] or 0, 2)
                }
            
            # Database performance trends
            cursor.execute('''
                SELECT 
                    AVG(query_time_ms) as avg_query_time,
                    MAX(query_time_ms) as max_query_time,
                    COUNT(*) as total_queries
                FROM db_metrics 
                WHERE timestamp > ?
            ''', (cutoff_date,))
            
            db_data = cursor.fetchone()
            if db_data:
                analytics['database_trends'] = {
                    'avg_query_time_ms': round(db_data[0] or 0, 2),
                    'max_query_time_ms': round(db_data[1] or 0, 2),
                    'total_queries': db_data[2] or 0
                }
            
            conn.close()
            
            # Identify bottlenecks
            if analytics['system_trends'].get('avg_cpu_percent', 0) > 60:
                analytics['bottlenecks'].append("High average CPU usage")
            
            if analytics['database_trends'].get('avg_query_time_ms', 0) > 150:
                analytics['bottlenecks'].append("Slow database query performance")
            
            return analytics
        
        except Exception as e:
            self.logger.error(f"Error getting performance analytics: {e}")
            return {'error': str(e)}

def integration_example():
    """Example of how to integrate performance monitoring"""
    monitor = PerformanceMonitor()
    
    # Track a database query
    start_time = time.time()
    # ... perform database operation ...
    query_time = time.time() - start_time
    monitor.track_query_performance("SELECT", query_time, 10, "problems")
    
    # Track user performance
    monitor.track_user_performance("completion_time", 25.5, "python", "arrays", "medium")
    
    # Get system health
    health_report = monitor.get_system_health_report()
    print(f"System Status: {health_report['system_status']}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance Monitoring System")
    parser.add_argument('--health', action='store_true', help='Show system health report')
    parser.add_argument('--optimize', action='store_true', help='Optimize database')
    parser.add_argument('--analytics', type=int, metavar='DAYS', help='Show performance analytics for N days')
    parser.add_argument('--cleanup', action='store_true', help='Cleanup old metrics')
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor()
    
    if args.health:
        health = monitor.get_system_health_report()
        print("\n🏥 System Health Report")
        print("=" * 40)
        print(f"Status: {health['system_status'].upper()}")
        print(f"Database Size: {health['database_health'].get('size_mb', 0):.1f} MB")
        print(f"Average CPU: {health['performance_summary'].get('avg_cpu_percent', 0):.1f}%")
        print(f"Average Memory: {health['performance_summary'].get('avg_memory_percent', 0):.1f}%")
        
        if health['recommendations']:
            print("\n💡 Recommendations:")
            for rec in health['recommendations']:
                print(f"• {rec}")
    
    elif args.optimize:
        monitor.optimize_database()
        print("✅ Database optimization completed")
    
    elif args.analytics:
        analytics = monitor.get_performance_analytics(args.analytics)
        print(f"\n📊 Performance Analytics ({args.analytics} days)")
        print("=" * 40)
        print(f"System - Avg CPU: {analytics['system_trends'].get('avg_cpu_percent', 0):.1f}%")
        print(f"Database - Avg Query Time: {analytics['database_trends'].get('avg_query_time_ms', 0):.1f}ms")
        
        if analytics['bottlenecks']:
            print("\n⚠️  Bottlenecks:")
            for bottleneck in analytics['bottlenecks']:
                print(f"• {bottleneck}")
    
    elif args.cleanup:
        monitor.cleanup_old_metrics()
        print("✅ Cleanup completed")
    
    else:
        print("Performance Monitoring System")
        print("Use --help for available options") 