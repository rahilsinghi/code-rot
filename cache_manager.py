#!/usr/bin/env python3
"""
Advanced Caching and Performance Optimization System
Multi-layer caching with intelligent invalidation and memory management
"""

import time
import json
import hashlib
import threading
import gc
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from pathlib import Path
from collections import OrderedDict
import pickle
import weakref
from functools import wraps
import psutil
import os

class CacheLayer:
    """Individual cache layer with specific characteristics"""
    
    def __init__(self, name: str, max_size: int = 1000, ttl: int = 3600):
        self.name = name
        self.max_size = max_size
        self.ttl = ttl
        self.cache = OrderedDict()
        self.timestamps = {}
        self.hit_count = 0
        self.miss_count = 0
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache with thread safety"""
        with self.lock:
            if key in self.cache:
                # Check if expired
                if self._is_expired(key):
                    self._remove(key)
                    self.miss_count += 1
                    return None
                
                # Move to end (LRU)
                self.cache.move_to_end(key)
                self.hit_count += 1
                return self.cache[key]
            
            self.miss_count += 1
            return None
    
    def set(self, key: str, value: Any) -> None:
        """Set item in cache with thread safety"""
        with self.lock:
            # Remove if exists
            if key in self.cache:
                self._remove(key)
            
            # Check size limit
            while len(self.cache) >= self.max_size:
                self._remove_oldest()
            
            # Add new item
            self.cache[key] = value
            self.timestamps[key] = time.time()
    
    def remove(self, key: str) -> bool:
        """Remove item from cache"""
        with self.lock:
            return self._remove(key)
    
    def clear(self) -> None:
        """Clear all items from cache"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def _remove(self, key: str) -> bool:
        """Internal remove method"""
        if key in self.cache:
            del self.cache[key]
            del self.timestamps[key]
            return True
        return False
    
    def _remove_oldest(self) -> None:
        """Remove oldest item (LRU)"""
        if self.cache:
            oldest_key = next(iter(self.cache))
            self._remove(oldest_key)
    
    def _is_expired(self, key: str) -> bool:
        """Check if item is expired"""
        if key not in self.timestamps:
            return True
        
        age = time.time() - self.timestamps[key]
        return age > self.ttl
    
    def cleanup_expired(self) -> int:
        """Remove expired items and return count"""
        expired_keys = []
        
        with self.lock:
            for key in list(self.cache.keys()):
                if self._is_expired(key):
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._remove(key)
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'name': self.name,
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': round(hit_rate, 2),
            'ttl': self.ttl
        }

class AdvancedCacheManager:
    """Multi-layer caching system with intelligent management"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.performance_config = self.config.get('performance', {})
        self.cache_enabled = self.performance_config.get('enable_caching', True)
        
        # Memory management
        self.memory_limit_mb = self.config.get('optimization', {}).get('memory_limit_mb', 512)
        self.gc_threshold = self.config.get('optimization', {}).get('gc_threshold', 1000)
        
        # Cache layers
        self.layers = {
            'hot': CacheLayer('hot', max_size=100, ttl=300),      # 5 minutes
            'warm': CacheLayer('warm', max_size=500, ttl=1800),   # 30 minutes
            'cold': CacheLayer('cold', max_size=1000, ttl=3600),  # 1 hour
            'persistent': CacheLayer('persistent', max_size=2000, ttl=86400)  # 24 hours
        }
        
        # File-based persistent cache
        self.persistent_cache_path = Path("practice_data/cache")
        self.persistent_cache_path.mkdir(parents=True, exist_ok=True)
        
        # Performance tracking
        self.performance_stats = {
            'cache_operations': 0,
            'memory_optimizations': 0,
            'gc_collections': 0,
            'disk_cache_hits': 0,
            'disk_cache_misses': 0
        }
        
        # Cleanup thread
        self.cleanup_thread = None
        self.cleanup_interval = 300  # 5 minutes
        self.running = True
        
        # Start background cleanup
        self._start_cleanup_thread()
    
    def get(self, key: str, layer: str = 'auto') -> Optional[Any]:
        """Get item from cache with automatic layer selection"""
        if not self.cache_enabled:
            return None
        
        self.performance_stats['cache_operations'] += 1
        
        # Auto layer selection
        if layer == 'auto':
            # Try layers in order of speed
            for layer_name in ['hot', 'warm', 'cold', 'persistent']:
                value = self.layers[layer_name].get(key)
                if value is not None:
                    # Promote to hot cache if from lower layers
                    if layer_name != 'hot':
                        self.layers['hot'].set(key, value)
                    return value
            
            # Try disk cache
            return self._get_from_disk(key)
        
        # Specific layer
        if layer in self.layers:
            return self.layers[layer].get(key)
        
        return None
    
    def set(self, key: str, value: Any, layer: str = 'auto', persist: bool = False) -> None:
        """Set item in cache with automatic layer selection"""
        if not self.cache_enabled:
            return
        
        self.performance_stats['cache_operations'] += 1
        
        # Auto layer selection based on value characteristics
        if layer == 'auto':
            layer = self._determine_optimal_layer(key, value)
        
        # Set in specified layer
        if layer in self.layers:
            self.layers[layer].set(key, value)
        
        # Persist to disk if requested
        if persist:
            self._set_to_disk(key, value)
        
        # Check memory usage
        self._check_memory_usage()
    
    def remove(self, key: str, layer: str = 'all') -> bool:
        """Remove item from cache"""
        if not self.cache_enabled:
            return False
        
        removed = False
        
        if layer == 'all':
            # Remove from all layers
            for cache_layer in self.layers.values():
                if cache_layer.remove(key):
                    removed = True
            
            # Remove from disk
            if self._remove_from_disk(key):
                removed = True
        else:
            # Remove from specific layer
            if layer in self.layers:
                removed = self.layers[layer].remove(key)
        
        return removed
    
    def clear(self, layer: str = 'all') -> None:
        """Clear cache"""
        if layer == 'all':
            for cache_layer in self.layers.values():
                cache_layer.clear()
            self._clear_disk_cache()
        elif layer in self.layers:
            self.layers[layer].clear()
    
    def _determine_optimal_layer(self, key: str, value: Any) -> str:
        """Determine optimal cache layer for value"""
        # Size-based determination
        try:
            size = len(pickle.dumps(value))
            if size < 1024:  # < 1KB
                return 'hot'
            elif size < 10240:  # < 10KB
                return 'warm'
            elif size < 102400:  # < 100KB
                return 'cold'
            else:
                return 'persistent'
        except:
            return 'warm'  # Default
    
    def _get_from_disk(self, key: str) -> Optional[Any]:
        """Get item from disk cache"""
        try:
            cache_file = self.persistent_cache_path / f"{self._hash_key(key)}.cache"
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                    
                # Check expiration
                if time.time() - data['timestamp'] < data['ttl']:
                    self.performance_stats['disk_cache_hits'] += 1
                    return data['value']
                else:
                    cache_file.unlink()  # Remove expired file
        except Exception:
            pass
        
        self.performance_stats['disk_cache_misses'] += 1
        return None
    
    def _set_to_disk(self, key: str, value: Any, ttl: int = 86400) -> None:
        """Set item to disk cache"""
        try:
            cache_file = self.persistent_cache_path / f"{self._hash_key(key)}.cache"
            data = {
                'value': value,
                'timestamp': time.time(),
                'ttl': ttl
            }
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception:
            pass
    
    def _remove_from_disk(self, key: str) -> bool:
        """Remove item from disk cache"""
        try:
            cache_file = self.persistent_cache_path / f"{self._hash_key(key)}.cache"
            if cache_file.exists():
                cache_file.unlink()
                return True
        except Exception:
            pass
        return False
    
    def _clear_disk_cache(self) -> None:
        """Clear all disk cache files"""
        try:
            for cache_file in self.persistent_cache_path.glob("*.cache"):
                cache_file.unlink()
        except Exception:
            pass
    
    def _hash_key(self, key: str) -> str:
        """Generate hash for cache key"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def _check_memory_usage(self) -> None:
        """Check and optimize memory usage"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb > self.memory_limit_mb:
                self._optimize_memory()
        except Exception:
            pass
    
    def _optimize_memory(self) -> None:
        """Optimize memory usage"""
        self.performance_stats['memory_optimizations'] += 1
        
        # Clear hot cache first (smallest impact)
        self.layers['hot'].clear()
        
        # Cleanup expired items
        for layer in self.layers.values():
            layer.cleanup_expired()
        
        # Force garbage collection
        gc.collect()
        self.performance_stats['gc_collections'] += 1
    
    def _start_cleanup_thread(self) -> None:
        """Start background cleanup thread"""
        def cleanup_worker():
            while self.running:
                try:
                    time.sleep(self.cleanup_interval)
                    if self.running:
                        self._periodic_cleanup()
                except Exception:
                    pass
        
        self.cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self.cleanup_thread.start()
    
    def _periodic_cleanup(self) -> None:
        """Periodic cleanup of expired items"""
        total_removed = 0
        
        # Cleanup each layer
        for layer in self.layers.values():
            removed = layer.cleanup_expired()
            total_removed += removed
        
        # Cleanup disk cache
        self._cleanup_disk_cache()
        
        # Garbage collection if threshold reached
        if total_removed > self.gc_threshold:
            gc.collect()
            self.performance_stats['gc_collections'] += 1
    
    def _cleanup_disk_cache(self) -> None:
        """Cleanup expired disk cache files"""
        try:
            for cache_file in self.persistent_cache_path.glob("*.cache"):
                try:
                    with open(cache_file, 'rb') as f:
                        data = pickle.load(f)
                        if time.time() - data['timestamp'] > data['ttl']:
                            cache_file.unlink()
                except Exception:
                    # Remove corrupted files
                    cache_file.unlink()
        except Exception:
            pass
    
    def get_comprehensive_stats(self) -> Dict:
        """Get comprehensive cache statistics"""
        layer_stats = {}
        total_size = 0
        total_hits = 0
        total_misses = 0
        
        for layer_name, layer in self.layers.items():
            stats = layer.get_stats()
            layer_stats[layer_name] = stats
            total_size += stats['size']
            total_hits += stats['hit_count']
            total_misses += stats['miss_count']
        
        total_requests = total_hits + total_misses
        overall_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
        
        # Memory usage
        memory_usage = 0
        try:
            process = psutil.Process()
            memory_usage = process.memory_info().rss / 1024 / 1024
        except Exception:
            pass
        
        return {
            'overall_stats': {
                'total_items': total_size,
                'total_hits': total_hits,
                'total_misses': total_misses,
                'hit_rate': round(overall_hit_rate, 2),
                'memory_usage_mb': round(memory_usage, 2),
                'memory_limit_mb': self.memory_limit_mb
            },
            'layer_stats': layer_stats,
            'performance_stats': self.performance_stats,
            'disk_cache': {
                'hits': self.performance_stats['disk_cache_hits'],
                'misses': self.performance_stats['disk_cache_misses'],
                'files': len(list(self.persistent_cache_path.glob("*.cache")))
            }
        }
    
    def cache_decorator(self, key_func: Callable = None, layer: str = 'auto', ttl: int = None):
        """Decorator for automatic function result caching"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
                
                # Try to get from cache
                cached_result = self.get(cache_key, layer)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.set(cache_key, result, layer)
                
                return result
            
            return wrapper
        return decorator
    
    def shutdown(self) -> None:
        """Shutdown cache manager"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=1)

# Global cache manager instance
_cache_manager = None

def get_cache_manager(config: Dict = None) -> AdvancedCacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = AdvancedCacheManager(config)
    return _cache_manager

# Convenience functions
def cache_get(key: str, layer: str = 'auto') -> Optional[Any]:
    """Convenience function for cache get"""
    return get_cache_manager().get(key, layer)

def cache_set(key: str, value: Any, layer: str = 'auto', persist: bool = False) -> None:
    """Convenience function for cache set"""
    get_cache_manager().set(key, value, layer, persist)

def cache_remove(key: str, layer: str = 'all') -> bool:
    """Convenience function for cache remove"""
    return get_cache_manager().remove(key, layer)

def cached(key_func: Callable = None, layer: str = 'auto', ttl: int = None):
    """Convenience decorator for function caching"""
    return get_cache_manager().cache_decorator(key_func, layer, ttl) 