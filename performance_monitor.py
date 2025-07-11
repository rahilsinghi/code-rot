#!/usr/bin/env python3
"""
System Performance Monitor and Diagnostic Tool
Comprehensive monitoring with optimization recommendations and health analysis
"""

import time
import psutil
import sqlite3
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from collections import deque, defaultdict
import statistics
import subprocess
import platform
import gc

class SystemMetrics:
    """System metrics collector and analyzer"""
    
    def __init__(self):
        self.cpu_history = deque(maxlen=100)
        self.memory_history = deque(maxlen=100)
        self.disk_history = deque(maxlen=100)
        self.network_history = deque(maxlen=100)
        
    def collect_metrics(self) -> Dict:
        """Collect current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Network metrics
            network_io = psutil.net_io_counters()
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'frequency': cpu_freq.current if cpu_freq else None
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used,
                    'free': memory.free
                },
                'swap': {
                    'total': swap.total,
                    'used': swap.used,
                    'percent': swap.percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent,
                    'read_bytes': disk_io.read_bytes if disk_io else 0,
                    'write_bytes': disk_io.write_bytes if disk_io else 0
                },
                'network': {
                    'bytes_sent': network_io.bytes_sent if network_io else 0,
                    'bytes_recv': network_io.bytes_recv if network_io else 0,
                    'packets_sent': network_io.packets_sent if network_io else 0,
                    'packets_recv': network_io.packets_recv if network_io else 0
                },
                'process': {
                    'cpu_percent': process_cpu,
                    'memory_rss': process_memory.rss,
                    'memory_vms': process_memory.vms,
                    'memory_percent': process.memory_percent()
                }
            }
            
            # Update history
            self.cpu_history.append(cpu_percent)
            self.memory_history.append(memory.percent)
            self.disk_history.append(disk.percent)
            
            return metrics
            
        except Exception as e:
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

class PerformanceAnalyzer:
    """Analyzes performance data and provides insights"""
    
    def __init__(self):
        self.thresholds = {
            'cpu_high': 80.0,
            'cpu_critical': 95.0,
            'memory_high': 80.0,
            'memory_critical': 95.0,
            'disk_high': 85.0,
            'disk_critical': 95.0,
            'response_time_slow': 1.0,
            'response_time_critical': 5.0
        }
    
    def analyze_system_health(self, metrics: Dict) -> Dict:
        """Analyze system health and provide status"""
        health_status = {
            'overall': 'healthy',
            'issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        try:
            # CPU Analysis
            cpu_percent = metrics.get('cpu', {}).get('percent', 0)
            if cpu_percent > self.thresholds['cpu_critical']:
                health_status['issues'].append(f"Critical CPU usage: {cpu_percent:.1f}%")
                health_status['overall'] = 'critical'
                health_status['recommendations'].append("Stop non-essential processes")
            elif cpu_percent > self.thresholds['cpu_high']:
                health_status['warnings'].append(f"High CPU usage: {cpu_percent:.1f}%")
                if health_status['overall'] == 'healthy':
                    health_status['overall'] = 'warning'
                health_status['recommendations'].append("Monitor CPU-intensive processes")
            
            # Memory Analysis
            memory_percent = metrics.get('memory', {}).get('percent', 0)
            if memory_percent > self.thresholds['memory_critical']:
                health_status['issues'].append(f"Critical memory usage: {memory_percent:.1f}%")
                health_status['overall'] = 'critical'
                health_status['recommendations'].append("Free up memory immediately")
            elif memory_percent > self.thresholds['memory_high']:
                health_status['warnings'].append(f"High memory usage: {memory_percent:.1f}%")
                if health_status['overall'] == 'healthy':
                    health_status['overall'] = 'warning'
                health_status['recommendations'].append("Consider clearing caches")
            
            # Disk Analysis
            disk_percent = metrics.get('disk', {}).get('percent', 0)
            if disk_percent > self.thresholds['disk_critical']:
                health_status['issues'].append(f"Critical disk usage: {disk_percent:.1f}%")
                health_status['overall'] = 'critical'
                health_status['recommendations'].append("Free up disk space immediately")
            elif disk_percent > self.thresholds['disk_high']:
                health_status['warnings'].append(f"High disk usage: {disk_percent:.1f}%")
                if health_status['overall'] == 'healthy':
                    health_status['overall'] = 'warning'
                health_status['recommendations'].append("Clean up temporary files")
            
            # Swap Analysis
            swap_percent = metrics.get('swap', {}).get('percent', 0)
            if swap_percent > 50:
                health_status['warnings'].append(f"High swap usage: {swap_percent:.1f}%")
                health_status['recommendations'].append("Consider adding more RAM")
            
        except Exception as e:
            health_status['issues'].append(f"Analysis error: {str(e)}")
            health_status['overall'] = 'error'
        
        return health_status
    
    def analyze_trends(self, metrics_history: List[Dict]) -> Dict:
        """Analyze performance trends over time"""
        if len(metrics_history) < 2:
            return {'error': 'Insufficient data for trend analysis'}
        
        trends = {
            'cpu_trend': 'stable',
            'memory_trend': 'stable',
            'disk_trend': 'stable',
            'performance_trend': 'stable'
        }
        
        try:
            # Extract time series data
            cpu_values = [m.get('cpu', {}).get('percent', 0) for m in metrics_history[-10:]]
            memory_values = [m.get('memory', {}).get('percent', 0) for m in metrics_history[-10:]]
            disk_values = [m.get('disk', {}).get('percent', 0) for m in metrics_history[-10:]]
            
            # Calculate trends
            if len(cpu_values) >= 3:
                cpu_slope = self._calculate_slope(cpu_values)
                trends['cpu_trend'] = self._interpret_slope(cpu_slope)
            
            if len(memory_values) >= 3:
                memory_slope = self._calculate_slope(memory_values)
                trends['memory_trend'] = self._interpret_slope(memory_slope)
            
            if len(disk_values) >= 3:
                disk_slope = self._calculate_slope(disk_values)
                trends['disk_trend'] = self._interpret_slope(disk_slope)
            
            # Overall performance trend
            if any(trend in ['increasing', 'rapidly_increasing'] for trend in trends.values()):
                trends['performance_trend'] = 'degrading'
            elif any(trend == 'decreasing' for trend in trends.values()):
                trends['performance_trend'] = 'improving'
            
        except Exception as e:
            trends['error'] = str(e)
        
        return trends
    
    def _calculate_slope(self, values: List[float]) -> float:
        """Calculate slope of values using linear regression"""
        if len(values) < 2:
            return 0
        
        n = len(values)
        x_values = list(range(n))
        
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        return numerator / denominator if denominator != 0 else 0
    
    def _interpret_slope(self, slope: float) -> str:
        """Interpret slope value as trend"""
        if slope > 2:
            return 'rapidly_increasing'
        elif slope > 0.5:
            return 'increasing'
        elif slope < -2:
            return 'rapidly_decreasing'
        elif slope < -0.5:
            return 'decreasing'
        else:
            return 'stable'

class PerformanceMonitor:
    """Main performance monitoring system"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.db_path = Path("practice_data/performance.db")
        self.metrics_collector = SystemMetrics()
        self.analyzer = PerformanceAnalyzer()
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_thread = None
        self.monitoring_interval = 30  # seconds
        
        # Performance history
        self.metrics_history = deque(maxlen=1000)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize performance database"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cpu_percent REAL,
                memory_percent REAL,
                disk_percent REAL,
                process_cpu_percent REAL,
                process_memory_mb REAL,
                metrics_json TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                severity TEXT,
                description TEXT,
                metrics_json TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON performance_metrics(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_timestamp ON performance_events(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_type ON performance_events(event_type)')
        
        conn.commit()
        conn.close()
    
    def start_monitoring(self) -> None:
        """Start background performance monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop background performance monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect metrics
                metrics = self.metrics_collector.collect_metrics()
                
                if 'error' not in metrics:
                    # Store metrics
                    self._store_metrics(metrics)
                    self.metrics_history.append(metrics)
                    
                    # Analyze health
                    health = self.analyzer.analyze_system_health(metrics)
                    
                    # Log events if needed
                    if health['overall'] != 'healthy':
                        self._log_performance_event(health, metrics)
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(self.monitoring_interval)
    
    def _store_metrics(self, metrics: Dict) -> None:
        """Store metrics in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO performance_metrics 
                (cpu_percent, memory_percent, disk_percent, process_cpu_percent, 
                 process_memory_mb, metrics_json)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                metrics.get('cpu', {}).get('percent', 0),
                metrics.get('memory', {}).get('percent', 0),
                metrics.get('disk', {}).get('percent', 0),
                metrics.get('process', {}).get('cpu_percent', 0),
                metrics.get('process', {}).get('memory_rss', 0) / 1024 / 1024,  # Convert to MB
                json.dumps(metrics)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error storing metrics: {e}")
    
    def _log_performance_event(self, health: Dict, metrics: Dict) -> None:
        """Log performance event"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            event_type = 'health_check'
            severity = health['overall']
            description = f"System health: {severity}"
            
            if health['issues']:
                description += f" - Issues: {', '.join(health['issues'])}"
            if health['warnings']:
                description += f" - Warnings: {', '.join(health['warnings'])}"
            
            cursor.execute('''
                INSERT INTO performance_events 
                (event_type, severity, description, metrics_json)
                VALUES (?, ?, ?, ?)
            ''', (event_type, severity, description, json.dumps(metrics)))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error logging event: {e}")
    
    def get_current_status(self) -> Dict:
        """Get current system status"""
        metrics = self.metrics_collector.collect_metrics()
        if 'error' in metrics:
            return metrics
        
        health = self.analyzer.analyze_system_health(metrics)
        trends = self.analyzer.analyze_trends(list(self.metrics_history))
        
        return {
            'metrics': metrics,
            'health': health,
            'trends': trends,
            'monitoring_active': self.monitoring_active
        }
    
    def get_performance_report(self, hours: int = 24) -> Dict:
        """Get comprehensive performance report"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get metrics from last N hours
            since = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT cpu_percent, memory_percent, disk_percent, 
                       process_cpu_percent, process_memory_mb, timestamp
                FROM performance_metrics
                WHERE timestamp >= ?
                ORDER BY timestamp
            ''', (since.isoformat(),))
            
            metrics_data = cursor.fetchall()
            
            # Get events from last N hours
            cursor.execute('''
                SELECT event_type, severity, description, timestamp
                FROM performance_events
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            ''', (since.isoformat(),))
            
            events_data = cursor.fetchall()
            
            conn.close()
            
            # Calculate statistics
            if metrics_data:
                cpu_values = [row[0] for row in metrics_data]
                memory_values = [row[1] for row in metrics_data]
                disk_values = [row[2] for row in metrics_data]
                
                stats = {
                    'cpu': {
                        'avg': statistics.mean(cpu_values),
                        'max': max(cpu_values),
                        'min': min(cpu_values),
                        'current': cpu_values[-1] if cpu_values else 0
                    },
                    'memory': {
                        'avg': statistics.mean(memory_values),
                        'max': max(memory_values),
                        'min': min(memory_values),
                        'current': memory_values[-1] if memory_values else 0
                    },
                    'disk': {
                        'avg': statistics.mean(disk_values),
                        'max': max(disk_values),
                        'min': min(disk_values),
                        'current': disk_values[-1] if disk_values else 0
                    }
                }
            else:
                stats = {'error': 'No data available'}
            
            # Format events
            events = []
            for event in events_data:
                events.append({
                    'type': event[0],
                    'severity': event[1],
                    'description': event[2],
                    'timestamp': event[3]
                })
            
            return {
                'period_hours': hours,
                'data_points': len(metrics_data),
                'statistics': stats,
                'events': events,
                'events_count': len(events),
                'system_info': self._get_system_info()
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_system_info(self) -> Dict:
        """Get system information"""
        try:
            return {
                'platform': platform.platform(),
                'processor': platform.processor(),
                'architecture': platform.architecture(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': round(psutil.virtual_memory().total / 1024 / 1024 / 1024, 2),
                'disk_total_gb': round(psutil.disk_usage('/').total / 1024 / 1024 / 1024, 2)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def optimize_system(self) -> Dict:
        """Perform system optimization"""
        optimization_results = {
            'actions_taken': [],
            'recommendations': [],
            'before_metrics': None,
            'after_metrics': None
        }
        
        try:
            # Get before metrics
            optimization_results['before_metrics'] = self.metrics_collector.collect_metrics()
            
            # Perform optimizations
            
            # 1. Garbage collection
            collected = gc.collect()
            optimization_results['actions_taken'].append(f"Garbage collection: {collected} objects collected")
            
            # 2. Clear system caches (if available)
            try:
                if hasattr(psutil, 'virtual_memory'):
                    # Try to clear page cache on Linux
                    if platform.system() == 'Linux':
                        subprocess.run(['sync'], check=False, capture_output=True)
                        optimization_results['actions_taken'].append("System sync completed")
            except Exception:
                pass
            
            # 3. Database optimization
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('VACUUM')
                cursor.execute('ANALYZE')
                conn.close()
                optimization_results['actions_taken'].append("Database optimized")
            except Exception:
                pass
            
            # Wait a moment and get after metrics
            time.sleep(2)
            optimization_results['after_metrics'] = self.metrics_collector.collect_metrics()
            
            # Generate recommendations
            current_status = self.get_current_status()
            if 'health' in current_status:
                optimization_results['recommendations'] = current_status['health'].get('recommendations', [])
            
        except Exception as e:
            optimization_results['error'] = str(e)
        
        return optimization_results

# Global performance monitor instance
_performance_monitor = None

def get_performance_monitor(config: Dict = None) -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor(config)
    return _performance_monitor 