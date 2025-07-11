#!/usr/bin/env python3
"""
Advanced Error Handling and Logging System
Provides comprehensive error management with categorization, retry logic, and user-friendly messaging
"""

import logging
import sys
import traceback
import time
import functools
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import json
from enum import Enum

class ErrorCategory(Enum):
    """Error categories for better classification"""
    DATABASE = "database"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    CONFIGURATION = "configuration"
    PERFORMANCE = "performance"
    EXTERNAL_API = "external_api"
    USER_INPUT = "user_input"
    SYSTEM = "system"

class ErrorSeverity(Enum):
    """Error severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ErrorHandler:
    """Advanced error handling system with retry logic and user-friendly messaging"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.ui_config = self.config.get('ui', {})
        self.error_log_path = Path("practice_data/logs/errors.log")
        self.performance_log_path = Path("practice_data/logs/performance.log")
        
        # Error statistics
        self.error_stats = {
            'total_errors': 0,
            'errors_by_category': {},
            'errors_by_severity': {},
            'retry_attempts': 0,
            'successful_retries': 0
        }
        
        # User-friendly error messages
        self.error_messages = {
            ErrorCategory.DATABASE: {
                'title': '🗄️ Database Error',
                'message': 'There was an issue with the database operation.',
                'suggestions': [
                    'Check if the database file is accessible',
                    'Ensure sufficient disk space',
                    'Try running database optimization'
                ]
            },
            ErrorCategory.NETWORK: {
                'title': '🌐 Network Error',
                'message': 'Unable to connect to external services.',
                'suggestions': [
                    'Check your internet connection',
                    'Verify API endpoints are accessible',
                    'Check if rate limits are exceeded'
                ]
            },
            ErrorCategory.FILE_SYSTEM: {
                'title': '📁 File System Error',
                'message': 'There was an issue accessing files or directories.',
                'suggestions': [
                    'Check file permissions',
                    'Ensure the directory exists',
                    'Verify sufficient disk space'
                ]
            },
            ErrorCategory.VALIDATION: {
                'title': '✅ Validation Error',
                'message': 'The provided input is invalid.',
                'suggestions': [
                    'Check the input format',
                    'Ensure all required fields are provided',
                    'Verify the data meets requirements'
                ]
            },
            ErrorCategory.EXTERNAL_API: {
                'title': '🔌 External API Error',
                'message': 'There was an issue with an external service.',
                'suggestions': [
                    'Check API service status',
                    'Verify API credentials',
                    'Check rate limiting'
                ]
            }
        }
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup comprehensive logging system"""
        # Create logs directory
        self.error_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Error logger
        self.error_logger = logging.getLogger('ErrorHandler')
        self.error_logger.setLevel(logging.DEBUG)
        
        # File handler for errors
        error_handler = logging.FileHandler(self.error_log_path)
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        error_handler.setFormatter(error_formatter)
        self.error_logger.addHandler(error_handler)
        
        # Console handler for user feedback
        if self.ui_config.get('verbose_logging', False):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter('%(levelname)s: %(message)s')
            console_handler.setFormatter(console_formatter)
            self.error_logger.addHandler(console_handler)
        
        # Performance logger
        self.performance_logger = logging.getLogger('Performance')
        perf_handler = logging.FileHandler(self.performance_log_path)
        perf_formatter = logging.Formatter(
            '%(asctime)s - %(message)s'
        )
        perf_handler.setFormatter(perf_formatter)
        self.performance_logger.addHandler(perf_handler)
    
    def handle_error(self, 
                    error: Exception, 
                    category: ErrorCategory, 
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    context: Dict = None,
                    user_message: str = None) -> Dict:
        """Handle error with categorization and user-friendly messaging"""
        
        # Update statistics
        self.error_stats['total_errors'] += 1
        self.error_stats['errors_by_category'][category.value] = (
            self.error_stats['errors_by_category'].get(category.value, 0) + 1
        )
        self.error_stats['errors_by_severity'][severity.value] = (
            self.error_stats['errors_by_severity'].get(severity.value, 0) + 1
        )
        
        # Create error record
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'category': category.value,
            'severity': severity.value,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {},
            'traceback': traceback.format_exc() if severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH] else None
        }
        
        # Log error
        self.error_logger.error(json.dumps(error_record, indent=2))
        
        # Display user-friendly message
        if self.ui_config.get('color_output', True):
            self._display_user_friendly_error(category, severity, user_message, error)
        
        return error_record
    
    def _display_user_friendly_error(self, 
                                   category: ErrorCategory, 
                                   severity: ErrorSeverity,
                                   user_message: str,
                                   error: Exception):
        """Display user-friendly error message"""
        error_info = self.error_messages.get(category, {
            'title': '⚠️ Error',
            'message': 'An unexpected error occurred.',
            'suggestions': ['Please try again or contact support.']
        })
        
        # Color coding based on severity
        colors = {
            ErrorSeverity.CRITICAL: '\033[91m',  # Red
            ErrorSeverity.HIGH: '\033[93m',      # Yellow
            ErrorSeverity.MEDIUM: '\033[94m',    # Blue
            ErrorSeverity.LOW: '\033[92m',       # Green
            ErrorSeverity.INFO: '\033[96m'       # Cyan
        }
        reset_color = '\033[0m'
        
        color = colors.get(severity, '')
        
        print(f"\n{color}{error_info['title']}{reset_color}")
        print(f"{error_info['message']}")
        
        if user_message:
            print(f"Details: {user_message}")
        
        if severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            print(f"Technical details: {str(error)}")
        
        print("\n💡 Suggestions:")
        for suggestion in error_info['suggestions']:
            print(f"   • {suggestion}")
        
        print()  # Empty line for better readability
    
    def retry_on_error(self, 
                      max_retries: int = 3, 
                      delay: float = 1.0,
                      backoff_factor: float = 2.0,
                      exceptions: tuple = (Exception,)):
        """Decorator for automatic retry on specified exceptions"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        self.error_stats['retry_attempts'] += 1
                        
                        if attempt < max_retries:
                            wait_time = delay * (backoff_factor ** attempt)
                            self.error_logger.warning(
                                f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                                f"Retrying in {wait_time:.1f}s..."
                            )
                            time.sleep(wait_time)
                        else:
                            # Final attempt failed
                            self.handle_error(
                                e, 
                                ErrorCategory.SYSTEM, 
                                ErrorSeverity.HIGH,
                                context={'function': func.__name__, 'attempts': max_retries + 1}
                            )
                            raise
                
                # This should never be reached, but just in case
                if last_exception:
                    raise last_exception
                    
            return wrapper
        return decorator
    
    def performance_monitor(self, operation_name: str):
        """Decorator for performance monitoring"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Log performance
                    self.performance_logger.info(
                        f"{operation_name} - SUCCESS - {execution_time:.3f}s"
                    )
                    
                    # Warn about slow operations
                    if execution_time > 5.0:
                        self.handle_error(
                            Exception(f"Slow operation: {operation_name} took {execution_time:.3f}s"),
                            ErrorCategory.PERFORMANCE,
                            ErrorSeverity.LOW,
                            context={'operation': operation_name, 'duration': execution_time}
                        )
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.performance_logger.error(
                        f"{operation_name} - FAILED - {execution_time:.3f}s - {str(e)}"
                    )
                    raise
                    
            return wrapper
        return decorator
    
    def get_error_report(self) -> Dict:
        """Get comprehensive error statistics report"""
        total_errors = self.error_stats['total_errors']
        retry_success_rate = 0
        
        if self.error_stats['retry_attempts'] > 0:
            retry_success_rate = (
                self.error_stats['successful_retries'] / self.error_stats['retry_attempts']
            ) * 100
        
        return {
            'summary': {
                'total_errors': total_errors,
                'retry_attempts': self.error_stats['retry_attempts'],
                'retry_success_rate': round(retry_success_rate, 2)
            },
            'by_category': self.error_stats['errors_by_category'],
            'by_severity': self.error_stats['errors_by_severity'],
            'log_files': {
                'error_log': str(self.error_log_path),
                'performance_log': str(self.performance_log_path)
            }
        }
    
    def clear_error_stats(self):
        """Clear error statistics"""
        self.error_stats = {
            'total_errors': 0,
            'errors_by_category': {},
            'errors_by_severity': {},
            'retry_attempts': 0,
            'successful_retries': 0
        }

# Global error handler instance
_error_handler = None

def get_error_handler(config: Dict = None) -> ErrorHandler:
    """Get global error handler instance"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler(config)
    return _error_handler

# Convenience functions
def handle_error(error: Exception, 
                category: ErrorCategory, 
                severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                context: Dict = None,
                user_message: str = None) -> Dict:
    """Convenience function for error handling"""
    return get_error_handler().handle_error(error, category, severity, context, user_message)

def retry_on_error(max_retries: int = 3, delay: float = 1.0, backoff_factor: float = 2.0):
    """Convenience decorator for retry logic"""
    return get_error_handler().retry_on_error(max_retries, delay, backoff_factor)

def performance_monitor(operation_name: str):
    """Convenience decorator for performance monitoring"""
    return get_error_handler().performance_monitor(operation_name) 