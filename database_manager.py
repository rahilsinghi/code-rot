#!/usr/bin/env python3
"""
Database Manager with Connection Pooling and Performance Monitoring
Provides optimized database operations with caching and performance tracking
"""

import sqlite3
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
from pathlib import Path
import logging
from collections import defaultdict
import gc

class DatabaseManager:
    """Advanced database manager with connection pooling and performance monitoring"""
    
    def __init__(self, db_path: str = "practice_data/problems.db", config: Dict = None):
        self.db_path = db_path
        self.config = config or {}
        self.performance_config = self.config.get('performance', {})
        
        # Connection pool
        self.pool_size = self.performance_config.get('connection_pool_size', 10)
        self.connection_pool = []
        self.pool_lock = threading.Lock()
        self.query_timeout = self.performance_config.get('query_timeout', 30)
        
        # Performance monitoring
        self.performance_stats = {
            'query_count': 0,
            'total_time': 0,
            'avg_time': 0,
            'slow_queries': [],
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Caching system
        self.enable_caching = self.performance_config.get('enable_caching', True)
        self.cache_duration = self.performance_config.get('cache_duration', 3600)
        self.query_cache = {}
        self.cache_timestamps = {}
        
        # Batch processing
        self.batch_size = self.performance_config.get('batch_size', 100)
        
        # Initialize connection pool
        self._initialize_pool()
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup performance logging"""
        self.logger = logging.getLogger('DatabaseManager')
        if self.config.get('ui', {}).get('verbose_logging', False):
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
    
    def _initialize_pool(self):
        """Initialize connection pool"""
        with self.pool_lock:
            for _ in range(self.pool_size):
                conn = sqlite3.connect(self.db_path, timeout=self.query_timeout)
                conn.row_factory = sqlite3.Row  # Enable dict-like access
                self.connection_pool.append(conn)
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool with automatic return"""
        conn = None
        try:
            with self.pool_lock:
                if self.connection_pool:
                    conn = self.connection_pool.pop()
                else:
                    # Create new connection if pool is empty
                    conn = sqlite3.connect(self.db_path, timeout=self.query_timeout)
                    conn.row_factory = sqlite3.Row
            
            yield conn
            
        finally:
            if conn:
                with self.pool_lock:
                    if len(self.connection_pool) < self.pool_size:
                        self.connection_pool.append(conn)
                    else:
                        conn.close()
    
    def execute_query(self, query: str, params: Tuple = (), cache_key: str = None) -> List[Dict]:
        """Execute query with performance monitoring and caching"""
        start_time = time.time()
        
        # Check cache first
        if cache_key and self.enable_caching and self._is_cache_valid(cache_key):
            self.performance_stats['cache_hits'] += 1
            return self.query_cache[cache_key]
        
        # Execute query
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                # Fetch results
                if query.strip().upper().startswith('SELECT'):
                    results = [dict(row) for row in cursor.fetchall()]
                else:
                    conn.commit()
                    results = []
                
                # Cache results if enabled
                if cache_key and self.enable_caching:
                    self.query_cache[cache_key] = results
                    self.cache_timestamps[cache_key] = time.time()
                    self.performance_stats['cache_misses'] += 1
                
                return results
                
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise
        
        finally:
            # Update performance stats
            execution_time = time.time() - start_time
            self._update_performance_stats(query, execution_time)
    
    def execute_batch(self, queries: List[Tuple[str, Tuple]], transaction: bool = True) -> List[Any]:
        """Execute multiple queries in batch with optional transaction"""
        results = []
        
        try:
            with self.get_connection() as conn:
                if transaction:
                    conn.execute('BEGIN TRANSACTION')
                
                cursor = conn.cursor()
                for query, params in queries:
                    cursor.execute(query, params)
                    
                    if query.strip().upper().startswith('SELECT'):
                        results.append([dict(row) for row in cursor.fetchall()])
                    else:
                        results.append(cursor.rowcount)
                
                if transaction:
                    conn.commit()
                
        except Exception as e:
            if transaction:
                conn.rollback()
            self.logger.error(f"Batch execution failed: {e}")
            raise
        
        return results
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached result is still valid"""
        if cache_key not in self.cache_timestamps:
            return False
        
        age = time.time() - self.cache_timestamps[cache_key]
        return age < self.cache_duration
    
    def _update_performance_stats(self, query: str, execution_time: float):
        """Update performance statistics"""
        self.performance_stats['query_count'] += 1
        self.performance_stats['total_time'] += execution_time
        self.performance_stats['avg_time'] = (
            self.performance_stats['total_time'] / self.performance_stats['query_count']
        )
        
        # Track slow queries (> 1 second)
        if execution_time > 1.0:
            self.performance_stats['slow_queries'].append({
                'query': query[:100] + '...' if len(query) > 100 else query,
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 10 slow queries
            if len(self.performance_stats['slow_queries']) > 10:
                self.performance_stats['slow_queries'].pop(0)
    
    def get_performance_report(self) -> Dict:
        """Get comprehensive performance report"""
        cache_hit_rate = 0
        total_cache_requests = self.performance_stats['cache_hits'] + self.performance_stats['cache_misses']
        if total_cache_requests > 0:
            cache_hit_rate = (self.performance_stats['cache_hits'] / total_cache_requests) * 100
        
        return {
            'query_statistics': {
                'total_queries': self.performance_stats['query_count'],
                'total_time': round(self.performance_stats['total_time'], 3),
                'average_time': round(self.performance_stats['avg_time'], 3),
                'slow_queries_count': len(self.performance_stats['slow_queries'])
            },
            'cache_statistics': {
                'hit_rate': round(cache_hit_rate, 2),
                'total_hits': self.performance_stats['cache_hits'],
                'total_misses': self.performance_stats['cache_misses'],
                'cached_items': len(self.query_cache)
            },
            'connection_pool': {
                'pool_size': self.pool_size,
                'available_connections': len(self.connection_pool)
            },
            'slow_queries': self.performance_stats['slow_queries']
        }
    
    def optimize_database(self):
        """Perform database optimization tasks"""
        optimization_queries = [
            'VACUUM;',
            'ANALYZE;',
            'PRAGMA optimize;'
        ]
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                for query in optimization_queries:
                    cursor.execute(query)
                conn.commit()
            
            self.logger.info("Database optimization completed")
            
        except Exception as e:
            self.logger.error(f"Database optimization failed: {e}")
    
    def clear_cache(self):
        """Clear query cache"""
        self.query_cache.clear()
        self.cache_timestamps.clear()
        self.performance_stats['cache_hits'] = 0
        self.performance_stats['cache_misses'] = 0
        
        # Force garbage collection
        gc.collect()
    
    def close_all_connections(self):
        """Close all connections in pool"""
        with self.pool_lock:
            for conn in self.connection_pool:
                conn.close()
            self.connection_pool.clear()
    
    def __del__(self):
        """Cleanup on destruction"""
        self.close_all_connections()

# Singleton instance for global use
_db_manager = None

def get_db_manager(db_path: str = "practice_data/problems.db", config: Dict = None) -> DatabaseManager:
    """Get singleton database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path, config)
    return _db_manager 