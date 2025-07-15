#!/usr/bin/env python3
"""
Advanced Security Scanner
Comprehensive security analysis for coding practice repositories
"""

import os
import re
import ast
import json
import hashlib
import subprocess
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from collections import defaultdict

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import bandit
    from bandit.core import manager
    BANDIT_AVAILABLE = True
except ImportError:
    BANDIT_AVAILABLE = False

try:
    import safety
    SAFETY_AVAILABLE = True
except ImportError:
    SAFETY_AVAILABLE = False

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class VulnerabilityType(Enum):
    INJECTION = "injection"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CRYPTOGRAPHY = "cryptography"
    INPUT_VALIDATION = "input_validation"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    INFORMATION_DISCLOSURE = "information_disclosure"
    INSECURE_COMMUNICATION = "insecure_communication"
    LOGGING = "logging"

@dataclass
class SecurityIssue:
    """Represents a security issue found during scanning"""
    issue_id: str
    severity: SecurityLevel
    vulnerability_type: VulnerabilityType
    title: str
    description: str
    file_path: str
    line_number: int
    code_snippet: str
    recommendation: str
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None
    references: List[str] = None

class SecurityScanner:
    """Advanced security scanner for code analysis"""
    
    def __init__(self, scan_directory: str = "."):
        self.scan_directory = Path(scan_directory)
        self.logger = self._setup_logging()
        self.issues = []
        self.scan_results = {}
        
        # Security patterns for different vulnerability types
        self.security_patterns = self._load_security_patterns()
        
        # Initialize vulnerability database
        self.vuln_db_path = self.scan_directory / "security_data" / "vulnerabilities.db"
        self._init_vulnerability_db()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for security scanner"""
        logger = logging.getLogger('security_scanner')
        logger.setLevel(logging.INFO)
        
        # Create security data directory
        security_dir = self.scan_directory / "security_data"
        security_dir.mkdir(exist_ok=True)
        
        # Create file handler
        log_file = security_dir / "security_scan.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _init_vulnerability_db(self):
        """Initialize vulnerability database"""
        self.vuln_db_path.parent.mkdir(exist_ok=True)
        
        conn = sqlite3.connect(self.vuln_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_issues (
                issue_id TEXT PRIMARY KEY,
                severity TEXT NOT NULL,
                vulnerability_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_number INTEGER NOT NULL,
                code_snippet TEXT,
                recommendation TEXT NOT NULL,
                cwe_id TEXT,
                cvss_score REAL,
                references TEXT,
                scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'open'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_history (
                scan_id TEXT PRIMARY KEY,
                scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                files_scanned INTEGER NOT NULL,
                issues_found INTEGER NOT NULL,
                critical_issues INTEGER NOT NULL,
                high_issues INTEGER NOT NULL,
                medium_issues INTEGER NOT NULL,
                low_issues INTEGER NOT NULL,
                scan_duration REAL NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_security_patterns(self) -> Dict[VulnerabilityType, List[Dict]]:
        """Load security vulnerability patterns"""
        patterns = {
            VulnerabilityType.INJECTION: [
                {
                    'pattern': r'execute\s*\(\s*["\'][^"\']*%[^"\']*["\']',
                    'description': 'Potential SQL injection vulnerability',
                    'severity': SecurityLevel.HIGH,
                    'cwe_id': 'CWE-89',
                    'recommendation': 'Use parameterized queries or prepared statements'
                },
                {
                    'pattern': r'eval\s*\(\s*[^)]*\)',
                    'description': 'Use of eval() function can lead to code injection',
                    'severity': SecurityLevel.CRITICAL,
                    'cwe_id': 'CWE-95',
                    'recommendation': 'Avoid using eval(). Use safer alternatives like ast.literal_eval()'
                },
                {
                    'pattern': r'exec\s*\(\s*[^)]*\)',
                    'description': 'Use of exec() function can lead to code injection',
                    'severity': SecurityLevel.CRITICAL,
                    'cwe_id': 'CWE-95',
                    'recommendation': 'Avoid using exec(). Refactor code to use safer alternatives'
                }
            ],
            VulnerabilityType.CRYPTOGRAPHY: [
                {
                    'pattern': r'md5\s*\(',
                    'description': 'MD5 is cryptographically broken and should not be used',
                    'severity': SecurityLevel.MEDIUM,
                    'cwe_id': 'CWE-327',
                    'recommendation': 'Use SHA-256 or stronger hashing algorithms'
                },
                {
                    'pattern': r'sha1\s*\(',
                    'description': 'SHA-1 is cryptographically weak and should not be used',
                    'severity': SecurityLevel.MEDIUM,
                    'cwe_id': 'CWE-327',
                    'recommendation': 'Use SHA-256 or stronger hashing algorithms'
                },
                {
                    'pattern': r'random\.random\(\)',
                    'description': 'Using random.random() for security purposes is insecure',
                    'severity': SecurityLevel.MEDIUM,
                    'cwe_id': 'CWE-338',
                    'recommendation': 'Use secrets module for cryptographically secure random numbers'
                }
            ],
            VulnerabilityType.AUTHENTICATION: [
                {
                    'pattern': r'password\s*=\s*["\'][^"\']*["\']',
                    'description': 'Hardcoded password found',
                    'severity': SecurityLevel.HIGH,
                    'cwe_id': 'CWE-798',
                    'recommendation': 'Store passwords securely using environment variables or secure storage'
                },
                {
                    'pattern': r'api_key\s*=\s*["\'][^"\']*["\']',
                    'description': 'Hardcoded API key found',
                    'severity': SecurityLevel.HIGH,
                    'cwe_id': 'CWE-798',
                    'recommendation': 'Store API keys securely using environment variables'
                }
            ],
            VulnerabilityType.INPUT_VALIDATION: [
                {
                    'pattern': r'input\s*\(\s*[^)]*\)',
                    'description': 'Unvalidated user input can lead to security issues',
                    'severity': SecurityLevel.MEDIUM,
                    'cwe_id': 'CWE-20',
                    'recommendation': 'Validate and sanitize all user inputs'
                },
                {
                    'pattern': r'raw_input\s*\(\s*[^)]*\)',
                    'description': 'Unvalidated user input can lead to security issues',
                    'severity': SecurityLevel.MEDIUM,
                    'cwe_id': 'CWE-20',
                    'recommendation': 'Validate and sanitize all user inputs'
                }
            ],
            VulnerabilityType.INSECURE_COMMUNICATION: [
                {
                    'pattern': r'http://[^"\'\s]+',
                    'description': 'Insecure HTTP communication detected',
                    'severity': SecurityLevel.MEDIUM,
                    'cwe_id': 'CWE-319',
                    'recommendation': 'Use HTTPS for all communications'
                },
                {
                    'pattern': r'verify\s*=\s*False',
                    'description': 'SSL certificate verification disabled',
                    'severity': SecurityLevel.HIGH,
                    'cwe_id': 'CWE-295',
                    'recommendation': 'Enable SSL certificate verification'
                }
            ],
            VulnerabilityType.INFORMATION_DISCLOSURE: [
                {
                    'pattern': r'print\s*\([^)]*password[^)]*\)',
                    'description': 'Potential password disclosure in logs',
                    'severity': SecurityLevel.MEDIUM,
                    'cwe_id': 'CWE-532',
                    'recommendation': 'Avoid logging sensitive information'
                },
                {
                    'pattern': r'traceback\.print_exc\(\)',
                    'description': 'Stack trace disclosure can reveal sensitive information',
                    'severity': SecurityLevel.LOW,
                    'cwe_id': 'CWE-209',
                    'recommendation': 'Log errors securely without exposing stack traces to users'
                }
            ]
        }
        
        return patterns
    
    def scan_directory(self, target_directory: Optional[str] = None) -> Dict[str, Any]:
        """Perform comprehensive security scan of directory"""
        if target_directory:
            scan_dir = Path(target_directory)
        else:
            scan_dir = self.scan_directory
        
        scan_start = datetime.now()
        scan_id = f"scan_{scan_start.strftime('%Y%m%d_%H%M%S')}"
        
        self.logger.info(f"Starting security scan: {scan_id}")
        
        # Reset issues list
        self.issues = []
        
        # Find all Python files
        python_files = list(scan_dir.rglob("*.py"))
        
        # Scan each file
        for file_path in python_files:
            try:
                self._scan_file(file_path)
            except Exception as e:
                self.logger.error(f"Failed to scan {file_path}: {e}")
        
        # Run external security tools
        self._run_bandit_scan(scan_dir)
        self._run_safety_scan(scan_dir)
        
        # Check for configuration issues
        self._scan_configuration_files(scan_dir)
        
        # Check dependencies
        self._scan_dependencies(scan_dir)
        
        scan_end = datetime.now()
        scan_duration = (scan_end - scan_start).total_seconds()
        
        # Store scan results
        self.scan_results = {
            'scan_id': scan_id,
            'scan_timestamp': scan_start.isoformat(),
            'files_scanned': len(python_files),
            'issues_found': len(self.issues),
            'scan_duration': scan_duration,
            'issues_by_severity': self._get_issues_by_severity(),
            'issues_by_type': self._get_issues_by_type(),
            'issues': [self._issue_to_dict(issue) for issue in self.issues]
        }
        
        # Store in database
        self._store_scan_results()
        
        self.logger.info(f"Security scan completed: {len(self.issues)} issues found")
        
        return self.scan_results
    
    def _scan_file(self, file_path: Path):
        """Scan a single file for security issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Pattern-based scanning
            self._scan_with_patterns(file_path, content)
            
            # AST-based scanning
            self._scan_with_ast(file_path, content)
            
        except Exception as e:
            self.logger.error(f"Error scanning {file_path}: {e}")
    
    def _scan_with_patterns(self, file_path: Path, content: str):
        """Scan file using regex patterns"""
        lines = content.split('\n')
        
        for vuln_type, patterns in self.security_patterns.items():
            for pattern_info in patterns:
                pattern = pattern_info['pattern']
                
                for line_num, line in enumerate(lines, 1):
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    
                    for match in matches:
                        issue = SecurityIssue(
                            issue_id=self._generate_issue_id(file_path, line_num),
                            severity=pattern_info['severity'],
                            vulnerability_type=vuln_type,
                            title=pattern_info['description'],
                            description=pattern_info['description'],
                            file_path=str(file_path),
                            line_number=line_num,
                            code_snippet=line.strip(),
                            recommendation=pattern_info['recommendation'],
                            cwe_id=pattern_info.get('cwe_id'),
                            references=[]
                        )
                        
                        self.issues.append(issue)
    
    def _scan_with_ast(self, file_path: Path, content: str):
        """Scan file using AST analysis"""
        try:
            tree = ast.parse(content)
            
            # Check for dangerous function calls
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    self._check_dangerous_calls(node, file_path)
                elif isinstance(node, ast.Import):
                    self._check_dangerous_imports(node, file_path)
                elif isinstance(node, ast.ImportFrom):
                    self._check_dangerous_imports(node, file_path)
                elif isinstance(node, ast.Str):
                    self._check_sensitive_strings(node, file_path, content)
        
        except SyntaxError:
            # Skip files with syntax errors
            pass
    
    def _check_dangerous_calls(self, node: ast.Call, file_path: Path):
        """Check for dangerous function calls"""
        dangerous_functions = {
            'eval': {
                'severity': SecurityLevel.CRITICAL,
                'description': 'Use of eval() can lead to code injection',
                'recommendation': 'Use ast.literal_eval() or avoid dynamic code execution'
            },
            'exec': {
                'severity': SecurityLevel.CRITICAL,
                'description': 'Use of exec() can lead to code injection',
                'recommendation': 'Avoid dynamic code execution'
            },
            'compile': {
                'severity': SecurityLevel.HIGH,
                'description': 'Use of compile() can be dangerous',
                'recommendation': 'Avoid dynamic code compilation'
            },
            '__import__': {
                'severity': SecurityLevel.MEDIUM,
                'description': 'Dynamic imports can be dangerous',
                'recommendation': 'Use static imports when possible'
            }
        }
        
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in dangerous_functions:
                info = dangerous_functions[func_name]
                
                issue = SecurityIssue(
                    issue_id=self._generate_issue_id(file_path, node.lineno),
                    severity=info['severity'],
                    vulnerability_type=VulnerabilityType.INJECTION,
                    title=f"Dangerous function call: {func_name}()",
                    description=info['description'],
                    file_path=str(file_path),
                    line_number=node.lineno,
                    code_snippet=f"{func_name}(...)",
                    recommendation=info['recommendation'],
                    cwe_id='CWE-95'
                )
                
                self.issues.append(issue)
    
    def _check_dangerous_imports(self, node: ast.AST, file_path: Path):
        """Check for dangerous imports"""
        dangerous_modules = {
            'pickle': {
                'severity': SecurityLevel.MEDIUM,
                'description': 'Pickle module can execute arbitrary code',
                'recommendation': 'Use json or other safe serialization formats'
            },
            'subprocess': {
                'severity': SecurityLevel.MEDIUM,
                'description': 'Subprocess module can be dangerous if used with user input',
                'recommendation': 'Validate all inputs to subprocess calls'
            },
            'os': {
                'severity': SecurityLevel.LOW,
                'description': 'OS module provides system access',
                'recommendation': 'Be careful with system calls and user input'
            }
        }
        
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in dangerous_modules:
                    info = dangerous_modules[alias.name]
                    
                    issue = SecurityIssue(
                        issue_id=self._generate_issue_id(file_path, node.lineno),
                        severity=info['severity'],
                        vulnerability_type=VulnerabilityType.CONFIGURATION,
                        title=f"Potentially dangerous import: {alias.name}",
                        description=info['description'],
                        file_path=str(file_path),
                        line_number=node.lineno,
                        code_snippet=f"import {alias.name}",
                        recommendation=info['recommendation']
                    )
                    
                    self.issues.append(issue)
    
    def _check_sensitive_strings(self, node: ast.Str, file_path: Path, content: str):
        """Check for sensitive information in strings"""
        sensitive_patterns = [
            (r'password', 'Potential password in code'),
            (r'secret', 'Potential secret in code'),
            (r'token', 'Potential token in code'),
            (r'key', 'Potential key in code'),
            (r'api[_-]?key', 'Potential API key in code')
        ]
        
        string_value = node.s.lower()
        
        for pattern, description in sensitive_patterns:
            if re.search(pattern, string_value):
                issue = SecurityIssue(
                    issue_id=self._generate_issue_id(file_path, node.lineno),
                    severity=SecurityLevel.MEDIUM,
                    vulnerability_type=VulnerabilityType.INFORMATION_DISCLOSURE,
                    title=description,
                    description=f"Sensitive information found in string: {pattern}",
                    file_path=str(file_path),
                    line_number=node.lineno,
                    code_snippet=node.s[:50] + "..." if len(node.s) > 50 else node.s,
                    recommendation="Move sensitive information to environment variables or secure storage",
                    cwe_id='CWE-798'
                )
                
                self.issues.append(issue)
    
    def _run_bandit_scan(self, scan_dir: Path):
        """Run Bandit security scanner if available"""
        if not BANDIT_AVAILABLE:
            return
        
        try:
            # This is a simplified version - in practice, you'd run bandit properly
            self.logger.info("Running Bandit security scan...")
            # bandit_manager = manager.BanditManager(config, 'file')
            # bandit_manager.discover_files([str(scan_dir)])
            # bandit_manager.run_tests()
        except Exception as e:
            self.logger.error(f"Bandit scan failed: {e}")
    
    def _run_safety_scan(self, scan_dir: Path):
        """Run Safety scanner for dependency vulnerabilities"""
        if not SAFETY_AVAILABLE:
            return
        
        try:
            requirements_file = scan_dir / "requirements.txt"
            if requirements_file.exists():
                self.logger.info("Running Safety scan for dependencies...")
                # safety_results = safety.check(requirements=requirements_file)
                # Process safety results and add to issues
        except Exception as e:
            self.logger.error(f"Safety scan failed: {e}")
    
    def _scan_configuration_files(self, scan_dir: Path):
        """Scan configuration files for security issues"""
        config_files = [
            "config.json",
            "settings.py",
            ".env",
            "docker-compose.yml",
            "Dockerfile"
        ]
        
        for config_file in config_files:
            file_path = scan_dir / config_file
            if file_path.exists():
                self._scan_config_file(file_path)
    
    def _scan_config_file(self, file_path: Path):
        """Scan a configuration file for security issues"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for common configuration issues
            config_patterns = [
                (r'debug\s*=\s*true', 'Debug mode enabled in production', SecurityLevel.MEDIUM),
                (r'ssl\s*=\s*false', 'SSL disabled', SecurityLevel.HIGH),
                (r'password\s*=\s*["\'][^"\']*["\']', 'Hardcoded password', SecurityLevel.HIGH),
                (r'secret_key\s*=\s*["\'][^"\']*["\']', 'Hardcoded secret key', SecurityLevel.HIGH)
            ]
            
            lines = content.split('\n')
            for line_num, line in enumerate(lines, 1):
                for pattern, description, severity in config_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        issue = SecurityIssue(
                            issue_id=self._generate_issue_id(file_path, line_num),
                            severity=severity,
                            vulnerability_type=VulnerabilityType.CONFIGURATION,
                            title=f"Configuration issue: {description}",
                            description=description,
                            file_path=str(file_path),
                            line_number=line_num,
                            code_snippet=line.strip(),
                            recommendation="Review and secure configuration settings"
                        )
                        
                        self.issues.append(issue)
        
        except Exception as e:
            self.logger.error(f"Error scanning config file {file_path}: {e}")
    
    def _scan_dependencies(self, scan_dir: Path):
        """Scan dependencies for known vulnerabilities"""
        requirements_file = scan_dir / "requirements.txt"
        if not requirements_file.exists():
            return
        
        try:
            with open(requirements_file, 'r') as f:
                requirements = f.read()
            
            # Check for known vulnerable packages (simplified)
            vulnerable_packages = {
                'django<2.2.13': 'Django versions below 2.2.13 have security vulnerabilities',
                'flask<1.1.1': 'Flask versions below 1.1.1 have security vulnerabilities',
                'requests<2.20.0': 'Requests versions below 2.20.0 have security vulnerabilities'
            }
            
            for vuln_package, description in vulnerable_packages.items():
                if vuln_package.split('<')[0] in requirements:
                    issue = SecurityIssue(
                        issue_id=self._generate_issue_id(requirements_file, 1),
                        severity=SecurityLevel.HIGH,
                        vulnerability_type=VulnerabilityType.DEPENDENCY,
                        title=f"Vulnerable dependency: {vuln_package}",
                        description=description,
                        file_path=str(requirements_file),
                        line_number=1,
                        code_snippet=vuln_package,
                        recommendation="Update to the latest secure version"
                    )
                    
                    self.issues.append(issue)
        
        except Exception as e:
            self.logger.error(f"Error scanning dependencies: {e}")
    
    def _generate_issue_id(self, file_path: Path, line_number: int) -> str:
        """Generate unique issue ID"""
        content = f"{file_path}:{line_number}:{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _get_issues_by_severity(self) -> Dict[str, int]:
        """Get issue count by severity"""
        severity_counts = defaultdict(int)
        for issue in self.issues:
            severity_counts[issue.severity.value] += 1
        return dict(severity_counts)
    
    def _get_issues_by_type(self) -> Dict[str, int]:
        """Get issue count by vulnerability type"""
        type_counts = defaultdict(int)
        for issue in self.issues:
            type_counts[issue.vulnerability_type.value] += 1
        return dict(type_counts)
    
    def _issue_to_dict(self, issue: SecurityIssue) -> Dict[str, Any]:
        """Convert SecurityIssue to dictionary"""
        return {
            'issue_id': issue.issue_id,
            'severity': issue.severity.value,
            'vulnerability_type': issue.vulnerability_type.value,
            'title': issue.title,
            'description': issue.description,
            'file_path': issue.file_path,
            'line_number': issue.line_number,
            'code_snippet': issue.code_snippet,
            'recommendation': issue.recommendation,
            'cwe_id': issue.cwe_id,
            'cvss_score': issue.cvss_score,
            'references': issue.references or []
        }
    
    def _store_scan_results(self):
        """Store scan results in database"""
        conn = sqlite3.connect(self.vuln_db_path)
        cursor = conn.cursor()
        
        # Store scan history
        cursor.execute('''
            INSERT INTO scan_history 
            (scan_id, files_scanned, issues_found, critical_issues, 
             high_issues, medium_issues, low_issues, scan_duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.scan_results['scan_id'],
            self.scan_results['files_scanned'],
            self.scan_results['issues_found'],
            self.scan_results['issues_by_severity'].get('critical', 0),
            self.scan_results['issues_by_severity'].get('high', 0),
            self.scan_results['issues_by_severity'].get('medium', 0),
            self.scan_results['issues_by_severity'].get('low', 0),
            self.scan_results['scan_duration']
        ))
        
        # Store issues
        for issue in self.issues:
            cursor.execute('''
                INSERT OR REPLACE INTO security_issues 
                (issue_id, severity, vulnerability_type, title, description, 
                 file_path, line_number, code_snippet, recommendation, 
                 cwe_id, cvss_score, references)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                issue.issue_id,
                issue.severity.value,
                issue.vulnerability_type.value,
                issue.title,
                issue.description,
                issue.file_path,
                issue.line_number,
                issue.code_snippet,
                issue.recommendation,
                issue.cwe_id,
                issue.cvss_score,
                json.dumps(issue.references) if issue.references else None
            ))
        
        conn.commit()
        conn.close()
    
    def generate_security_report(self, format: str = 'json') -> str:
        """Generate security report in specified format"""
        if format == 'json':
            return json.dumps(self.scan_results, indent=2, default=str)
        elif format == 'html':
            return self._generate_html_report()
        elif format == 'markdown':
            return self._generate_markdown_report()
        else:
            return str(self.scan_results)
    
    def _generate_html_report(self) -> str:
        """Generate HTML security report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Security Scan Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
                .summary {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .metric {{ text-align: center; padding: 15px; background-color: #e9ecef; border-radius: 5px; }}
                .critical {{ background-color: #dc3545; color: white; }}
                .high {{ background-color: #fd7e14; color: white; }}
                .medium {{ background-color: #ffc107; }}
                .low {{ background-color: #28a745; color: white; }}
                .issue {{ margin: 15px 0; padding: 15px; border-left: 4px solid #007bff; background-color: #f8f9fa; }}
                .issue-critical {{ border-left-color: #dc3545; }}
                .issue-high {{ border-left-color: #fd7e14; }}
                .issue-medium {{ border-left-color: #ffc107; }}
                .issue-low {{ border-left-color: #28a745; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔒 Security Scan Report</h1>
                <p>Scan ID: {self.scan_results['scan_id']}</p>
                <p>Timestamp: {self.scan_results['scan_timestamp']}</p>
                <p>Files Scanned: {self.scan_results['files_scanned']}</p>
                <p>Issues Found: {self.scan_results['issues_found']}</p>
            </div>
            
            <div class="summary">
                <div class="metric critical">
                    <h3>{self.scan_results['issues_by_severity'].get('critical', 0)}</h3>
                    <p>Critical</p>
                </div>
                <div class="metric high">
                    <h3>{self.scan_results['issues_by_severity'].get('high', 0)}</h3>
                    <p>High</p>
                </div>
                <div class="metric medium">
                    <h3>{self.scan_results['issues_by_severity'].get('medium', 0)}</h3>
                    <p>Medium</p>
                </div>
                <div class="metric low">
                    <h3>{self.scan_results['issues_by_severity'].get('low', 0)}</h3>
                    <p>Low</p>
                </div>
            </div>
            
            <h2>🚨 Security Issues</h2>
        """
        
        for issue in self.scan_results['issues']:
            severity_class = f"issue-{issue['severity']}"
            html += f"""
            <div class="issue {severity_class}">
                <h3>{issue['title']}</h3>
                <p><strong>Severity:</strong> {issue['severity'].upper()}</p>
                <p><strong>Type:</strong> {issue['vulnerability_type']}</p>
                <p><strong>File:</strong> {issue['file_path']}:{issue['line_number']}</p>
                <p><strong>Description:</strong> {issue['description']}</p>
                <p><strong>Code:</strong> <code>{issue['code_snippet']}</code></p>
                <p><strong>Recommendation:</strong> {issue['recommendation']}</p>
                {f"<p><strong>CWE ID:</strong> {issue['cwe_id']}</p>" if issue['cwe_id'] else ""}
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _generate_markdown_report(self) -> str:
        """Generate Markdown security report"""
        md = f"""# 🔒 Security Scan Report

## Summary
- **Scan ID**: {self.scan_results['scan_id']}
- **Timestamp**: {self.scan_results['scan_timestamp']}
- **Files Scanned**: {self.scan_results['files_scanned']}
- **Issues Found**: {self.scan_results['issues_found']}
- **Scan Duration**: {self.scan_results['scan_duration']:.2f} seconds

## Issues by Severity
- **Critical**: {self.scan_results['issues_by_severity'].get('critical', 0)}
- **High**: {self.scan_results['issues_by_severity'].get('high', 0)}
- **Medium**: {self.scan_results['issues_by_severity'].get('medium', 0)}
- **Low**: {self.scan_results['issues_by_severity'].get('low', 0)}

## Issues by Type
"""
        
        for vuln_type, count in self.scan_results['issues_by_type'].items():
            md += f"- **{vuln_type.replace('_', ' ').title()}**: {count}\n"
        
        md += "\n## 🚨 Security Issues\n\n"
        
        for issue in self.scan_results['issues']:
            md += f"### {issue['title']}\n"
            md += f"**Severity**: {issue['severity'].upper()}\n"
            md += f"**Type**: {issue['vulnerability_type']}\n"
            md += f"**File**: {issue['file_path']}:{issue['line_number']}\n"
            md += f"**Description**: {issue['description']}\n"
            md += f"**Code**: `{issue['code_snippet']}`\n"
            md += f"**Recommendation**: {issue['recommendation']}\n"
            if issue['cwe_id']:
                md += f"**CWE ID**: {issue['cwe_id']}\n"
            md += "\n---\n\n"
        
        return md
    
    def get_scan_history(self) -> List[Dict[str, Any]]:
        """Get scan history from database"""
        conn = sqlite3.connect(self.vuln_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM scan_history 
            ORDER BY scan_timestamp DESC
        ''')
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'scan_id': row[0],
                'scan_timestamp': row[1],
                'files_scanned': row[2],
                'issues_found': row[3],
                'critical_issues': row[4],
                'high_issues': row[5],
                'medium_issues': row[6],
                'low_issues': row[7],
                'scan_duration': row[8]
            })
        
        conn.close()
        return history
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics and trends"""
        history = self.get_scan_history()
        
        if not history:
            return {'error': 'No scan history available'}
        
        # Calculate trends
        recent_scans = history[:5]  # Last 5 scans
        
        metrics = {
            'total_scans': len(history),
            'latest_scan': history[0] if history else None,
            'average_issues_per_scan': sum(scan['issues_found'] for scan in history) / len(history),
            'critical_issues_trend': [scan['critical_issues'] for scan in recent_scans],
            'high_issues_trend': [scan['high_issues'] for scan in recent_scans],
            'security_score': self._calculate_security_score(history[0] if history else None)
        }
        
        return metrics
    
    def _calculate_security_score(self, latest_scan: Dict[str, Any]) -> float:
        """Calculate security score based on latest scan"""
        if not latest_scan:
            return 0.0
        
        # Simple scoring: deduct points for issues
        base_score = 100.0
        
        # Deduct points based on severity
        base_score -= latest_scan['critical_issues'] * 20
        base_score -= latest_scan['high_issues'] * 10
        base_score -= latest_scan['medium_issues'] * 5
        base_score -= latest_scan['low_issues'] * 1
        
        return max(0.0, base_score)


def main():
    """Example usage of security scanner"""
    scanner = SecurityScanner()
    
    print("🔍 Starting comprehensive security scan...")
    results = scanner.scan_directory()
    
    print(f"\n📊 Scan Results:")
    print(f"Files scanned: {results['files_scanned']}")
    print(f"Issues found: {results['issues_found']}")
    print(f"Scan duration: {results['scan_duration']:.2f} seconds")
    
    print(f"\n🚨 Issues by severity:")
    for severity, count in results['issues_by_severity'].items():
        print(f"  {severity.upper()}: {count}")
    
    print(f"\n🔒 Issues by type:")
    for vuln_type, count in results['issues_by_type'].items():
        print(f"  {vuln_type.replace('_', ' ').title()}: {count}")
    
    # Generate reports
    print(f"\n📄 Generating security reports...")
    
    # HTML report
    html_report = scanner.generate_security_report('html')
    with open('security_report.html', 'w') as f:
        f.write(html_report)
    
    # Markdown report
    md_report = scanner.generate_security_report('markdown')
    with open('security_report.md', 'w') as f:
        f.write(md_report)
    
    print(f"✅ Reports generated: security_report.html, security_report.md")
    
    # Get security metrics
    metrics = scanner.get_security_metrics()
    print(f"\n📈 Security Score: {metrics.get('security_score', 0):.1f}/100")


if __name__ == "__main__":
    main() 