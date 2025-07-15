#!/usr/bin/env python3
"""
Advanced Code Quality Validator
Analyzes code complexity, style, performance, and provides improvement suggestions
"""

import ast
import re
import os
import json
import subprocess
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from datetime import datetime
import statistics
from collections import defaultdict, Counter

try:
    import pylint.lint
    from pylint.reporters.text import TextReporter
    from pylint.reporters import BaseReporter
    PYLINT_AVAILABLE = True
except ImportError:
    PYLINT_AVAILABLE = False

try:
    import flake8.api.legacy as flake8
    FLAKE8_AVAILABLE = True
except ImportError:
    FLAKE8_AVAILABLE = False

try:
    import black
    BLACK_AVAILABLE = True
except ImportError:
    BLACK_AVAILABLE = False

try:
    import radon.complexity as radon_complexity
    import radon.metrics as radon_metrics
    from radon.raw import analyze
    RADON_AVAILABLE = True
except ImportError:
    RADON_AVAILABLE = False

class CodeQualityValidator:
    """Advanced code quality analysis and validation"""
    
    def __init__(self):
        self.quality_standards = {
            'max_line_length': 88,
            'max_function_length': 50,
            'max_class_length': 200,
            'max_complexity': 10,
            'min_function_docstring_length': 20,
            'max_nesting_depth': 4,
            'max_parameters': 5
        }
        
        self.style_rules = {
            'snake_case_functions': True,
            'snake_case_variables': True,
            'pascal_case_classes': True,
            'uppercase_constants': True,
            'no_trailing_whitespace': True,
            'consistent_indentation': True,
            'blank_lines_around_functions': True
        }
        
        self.performance_checks = {
            'avoid_global_variables': True,
            'efficient_loops': True,
            'proper_exception_handling': True,
            'memory_efficient_operations': True,
            'avoid_repeated_computations': True
        }
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Comprehensive analysis of a single file"""
        if not os.path.exists(file_path):
            return {'error': f'File not found: {file_path}'}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                return {'error': f'Syntax error: {e}'}
            
            analysis = {
                'file_path': file_path,
                'timestamp': datetime.now().isoformat(),
                'basic_metrics': self._analyze_basic_metrics(content),
                'complexity_analysis': self._analyze_complexity(tree, content),
                'style_analysis': self._analyze_style(content, tree),
                'performance_analysis': self._analyze_performance(tree, content),
                'documentation_analysis': self._analyze_documentation(tree, content),
                'security_analysis': self._analyze_security(tree, content),
                'maintainability_score': 0,  # Calculated later
                'overall_grade': 'A',        # Calculated later
                'suggestions': []            # Populated later
            }
            
            # Calculate overall scores
            analysis['maintainability_score'] = self._calculate_maintainability_score(analysis)
            analysis['overall_grade'] = self._calculate_overall_grade(analysis)
            analysis['suggestions'] = self._generate_suggestions(analysis)
            
            return analysis
            
        except Exception as e:
            return {'error': f'Analysis failed: {str(e)}'}
    
    def analyze_directory(self, directory_path: str, extensions: List[str] = None) -> Dict[str, Any]:
        """Analyze all Python files in a directory"""
        if extensions is None:
            extensions = ['.py']
        
        directory_path = Path(directory_path)
        if not directory_path.exists():
            return {'error': f'Directory not found: {directory_path}'}
        
        file_analyses = {}
        summary_stats = {
            'total_files': 0,
            'total_lines': 0,
            'total_functions': 0,
            'total_classes': 0,
            'avg_complexity': 0,
            'avg_maintainability': 0,
            'grade_distribution': defaultdict(int),
            'common_issues': defaultdict(int)
        }
        
        # Find all Python files
        python_files = []
        for ext in extensions:
            python_files.extend(directory_path.rglob(f'*{ext}'))
        
        # Analyze each file
        for file_path in python_files:
            if file_path.name.startswith('.'):
                continue  # Skip hidden files
            
            analysis = self.analyze_file(str(file_path))
            if 'error' not in analysis:
                file_analyses[str(file_path)] = analysis
                
                # Update summary stats
                summary_stats['total_files'] += 1
                summary_stats['total_lines'] += analysis['basic_metrics']['lines_of_code']
                summary_stats['total_functions'] += analysis['basic_metrics']['function_count']
                summary_stats['total_classes'] += analysis['basic_metrics']['class_count']
                summary_stats['grade_distribution'][analysis['overall_grade']] += 1
                
                # Collect common issues
                for suggestion in analysis['suggestions']:
                    summary_stats['common_issues'][suggestion['category']] += 1
        
        # Calculate averages
        if summary_stats['total_files'] > 0:
            complexities = [a['complexity_analysis']['average_complexity'] 
                          for a in file_analyses.values()]
            maintainabilities = [a['maintainability_score'] 
                               for a in file_analyses.values()]
            
            summary_stats['avg_complexity'] = statistics.mean(complexities) if complexities else 0
            summary_stats['avg_maintainability'] = statistics.mean(maintainabilities) if maintainabilities else 0
        
        return {
            'directory_path': str(directory_path),
            'timestamp': datetime.now().isoformat(),
            'file_analyses': file_analyses,
            'summary_stats': dict(summary_stats),
            'recommendations': self._generate_directory_recommendations(summary_stats)
        }
    
    def _analyze_basic_metrics(self, content: str) -> Dict[str, Any]:
        """Analyze basic code metrics"""
        lines = content.split('\n')
        
        # Count different types of lines
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
            elif stripped.startswith('#'):
                comment_lines += 1
            else:
                code_lines += 1
        
        # Parse AST for function and class counts
        try:
            tree = ast.parse(content)
            function_count = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
            class_count = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
            import_count = len([node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))])
        except:
            function_count = class_count = import_count = 0
        
        return {
            'total_lines': len(lines),
            'lines_of_code': code_lines,
            'comment_lines': comment_lines,
            'blank_lines': blank_lines,
            'function_count': function_count,
            'class_count': class_count,
            'import_count': import_count,
            'comment_ratio': comment_lines / max(1, code_lines),
            'avg_line_length': statistics.mean([len(line) for line in lines]) if lines else 0
        }
    
    def _analyze_complexity(self, tree: ast.AST, content: str) -> Dict[str, Any]:
        """Analyze code complexity"""
        complexity_data = {
            'cyclomatic_complexity': {},
            'cognitive_complexity': {},
            'nesting_depth': {},
            'average_complexity': 0,
            'max_complexity': 0,
            'complex_functions': []
        }
        
        # Analyze each function
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                name = node.name
                
                # Calculate cyclomatic complexity
                cyclomatic = self._calculate_cyclomatic_complexity(node)
                complexity_data['cyclomatic_complexity'][name] = cyclomatic
                
                # Calculate cognitive complexity
                cognitive = self._calculate_cognitive_complexity(node)
                complexity_data['cognitive_complexity'][name] = cognitive
                
                # Calculate nesting depth
                nesting = self._calculate_nesting_depth(node)
                complexity_data['nesting_depth'][name] = nesting
                
                # Track complex functions
                if cyclomatic > self.quality_standards['max_complexity']:
                    complexity_data['complex_functions'].append({
                        'name': name,
                        'cyclomatic_complexity': cyclomatic,
                        'cognitive_complexity': cognitive,
                        'line_number': node.lineno
                    })
        
        # Calculate averages
        if complexity_data['cyclomatic_complexity']:
            complexities = list(complexity_data['cyclomatic_complexity'].values())
            complexity_data['average_complexity'] = statistics.mean(complexities)
            complexity_data['max_complexity'] = max(complexities)
        
        return complexity_data
    
    def _analyze_style(self, content: str, tree: ast.AST) -> Dict[str, Any]:
        """Analyze code style and formatting"""
        style_issues = []
        lines = content.split('\n')
        
        # Check line length
        long_lines = []
        for i, line in enumerate(lines, 1):
            if len(line) > self.quality_standards['max_line_length']:
                long_lines.append({'line': i, 'length': len(line)})
        
        if long_lines:
            style_issues.append({
                'type': 'line_length',
                'severity': 'medium',
                'count': len(long_lines),
                'details': long_lines[:5]  # Show first 5
            })
        
        # Check naming conventions
        naming_issues = self._check_naming_conventions(tree)
        if naming_issues:
            style_issues.extend(naming_issues)
        
        # Check indentation consistency
        indentation_issues = self._check_indentation(lines)
        if indentation_issues:
            style_issues.append(indentation_issues)
        
        # Check for trailing whitespace
        trailing_whitespace = []
        for i, line in enumerate(lines, 1):
            if line.rstrip() != line:
                trailing_whitespace.append(i)
        
        if trailing_whitespace:
            style_issues.append({
                'type': 'trailing_whitespace',
                'severity': 'low',
                'count': len(trailing_whitespace),
                'lines': trailing_whitespace[:10]
            })
        
        # Use external tools if available
        external_issues = []
        if FLAKE8_AVAILABLE:
            external_issues.extend(self._run_flake8_analysis(content))
        
        if BLACK_AVAILABLE:
            external_issues.extend(self._run_black_analysis(content))
        
        return {
            'style_issues': style_issues,
            'external_tool_issues': external_issues,
            'style_score': self._calculate_style_score(style_issues),
            'formatting_suggestions': self._generate_formatting_suggestions(style_issues)
        }
    
    def _analyze_performance(self, tree: ast.AST, content: str) -> Dict[str, Any]:
        """Analyze performance-related issues"""
        performance_issues = []
        
        # Check for global variables
        global_vars = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                global_vars.extend(node.names)
        
        if global_vars:
            performance_issues.append({
                'type': 'global_variables',
                'severity': 'medium',
                'count': len(global_vars),
                'variables': global_vars
            })
        
        # Check for inefficient loops
        inefficient_loops = self._check_inefficient_loops(tree)
        if inefficient_loops:
            performance_issues.extend(inefficient_loops)
        
        # Check for repeated computations
        repeated_computations = self._check_repeated_computations(tree)
        if repeated_computations:
            performance_issues.extend(repeated_computations)
        
        # Check exception handling
        exception_issues = self._check_exception_handling(tree)
        if exception_issues:
            performance_issues.extend(exception_issues)
        
        # Check for memory-inefficient operations
        memory_issues = self._check_memory_efficiency(tree)
        if memory_issues:
            performance_issues.extend(memory_issues)
        
        return {
            'performance_issues': performance_issues,
            'performance_score': self._calculate_performance_score(performance_issues),
            'optimization_suggestions': self._generate_optimization_suggestions(performance_issues)
        }
    
    def _analyze_documentation(self, tree: ast.AST, content: str) -> Dict[str, Any]:
        """Analyze documentation quality"""
        doc_analysis = {
            'module_docstring': None,
            'function_docstrings': {},
            'class_docstrings': {},
            'missing_docstrings': [],
            'docstring_quality': {},
            'documentation_score': 0
        }
        
        # Check module docstring
        if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Str):
            doc_analysis['module_docstring'] = tree.body[0].value.s
        
        # Check function docstrings
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                docstring = ast.get_docstring(node)
                if docstring:
                    doc_analysis['function_docstrings'][node.name] = docstring
                    doc_analysis['docstring_quality'][node.name] = self._evaluate_docstring_quality(docstring)
                else:
                    doc_analysis['missing_docstrings'].append({
                        'type': 'function',
                        'name': node.name,
                        'line': node.lineno
                    })
            
            elif isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node)
                if docstring:
                    doc_analysis['class_docstrings'][node.name] = docstring
                    doc_analysis['docstring_quality'][node.name] = self._evaluate_docstring_quality(docstring)
                else:
                    doc_analysis['missing_docstrings'].append({
                        'type': 'class',
                        'name': node.name,
                        'line': node.lineno
                    })
        
        # Calculate documentation score
        total_functions_classes = len(doc_analysis['function_docstrings']) + len(doc_analysis['class_docstrings']) + len(doc_analysis['missing_docstrings'])
        documented_count = len(doc_analysis['function_docstrings']) + len(doc_analysis['class_docstrings'])
        
        if total_functions_classes > 0:
            doc_analysis['documentation_score'] = (documented_count / total_functions_classes) * 100
        
        return doc_analysis
    
    def _analyze_security(self, tree: ast.AST, content: str) -> Dict[str, Any]:
        """Analyze security-related issues"""
        security_issues = []
        
        # Check for dangerous functions
        dangerous_functions = ['eval', 'exec', 'compile', '__import__']
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in dangerous_functions:
                    security_issues.append({
                        'type': 'dangerous_function',
                        'severity': 'high',
                        'function': node.func.id,
                        'line': node.lineno
                    })
        
        # Check for hardcoded secrets (basic patterns)
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']'
        ]
        
        for pattern in secret_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_no = content[:match.start()].count('\n') + 1
                security_issues.append({
                    'type': 'hardcoded_secret',
                    'severity': 'high',
                    'pattern': pattern,
                    'line': line_no
                })
        
        # Check for SQL injection vulnerabilities
        sql_injection_patterns = [
            r'execute\s*\(\s*["\'][^"\']*%[^"\']*["\']',
            r'query\s*\(\s*["\'][^"\']*%[^"\']*["\']'
        ]
        
        for pattern in sql_injection_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_no = content[:match.start()].count('\n') + 1
                security_issues.append({
                    'type': 'sql_injection_risk',
                    'severity': 'high',
                    'line': line_no
                })
        
        return {
            'security_issues': security_issues,
            'security_score': self._calculate_security_score(security_issues),
            'security_recommendations': self._generate_security_recommendations(security_issues)
        }
    
    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for a function"""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With, ast.AsyncWith):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _calculate_cognitive_complexity(self, node: ast.AST) -> int:
        """Calculate cognitive complexity (simplified version)"""
        complexity = 0
        nesting_level = 0
        
        def visit_node(n, level):
            nonlocal complexity
            
            if isinstance(n, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1 + level
            elif isinstance(n, ast.ExceptHandler):
                complexity += 1 + level
            elif isinstance(n, (ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(n, ast.BoolOp):
                complexity += len(n.values) - 1
            
            # Increase nesting level for certain constructs
            if isinstance(n, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.With, ast.AsyncWith)):
                level += 1
            
            for child in ast.iter_child_nodes(n):
                visit_node(child, level)
        
        visit_node(node, 0)
        return complexity
    
    def _calculate_nesting_depth(self, node: ast.AST) -> int:
        """Calculate maximum nesting depth"""
        max_depth = 0
        
        def visit_node(n, depth):
            nonlocal max_depth
            max_depth = max(max_depth, depth)
            
            if isinstance(n, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.With, ast.AsyncWith, ast.Try)):
                depth += 1
            
            for child in ast.iter_child_nodes(n):
                visit_node(child, depth)
        
        visit_node(node, 0)
        return max_depth
    
    def _check_naming_conventions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Check naming conventions"""
        issues = []
        
        # Check function names (should be snake_case)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not re.match(r'^[a-z_][a-z0-9_]*$', node.name):
                    issues.append({
                        'type': 'function_naming',
                        'severity': 'medium',
                        'name': node.name,
                        'line': node.lineno,
                        'expected': 'snake_case'
                    })
            
            elif isinstance(node, ast.ClassDef):
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                    issues.append({
                        'type': 'class_naming',
                        'severity': 'medium',
                        'name': node.name,
                        'line': node.lineno,
                        'expected': 'PascalCase'
                    })
        
        return issues
    
    def _check_indentation(self, lines: List[str]) -> Optional[Dict[str, Any]]:
        """Check indentation consistency"""
        indentation_levels = []
        
        for line in lines:
            if line.strip():  # Skip empty lines
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces > 0:
                    indentation_levels.append(leading_spaces)
        
        if indentation_levels:
            # Check if all indentations are multiples of 4
            inconsistent = [level for level in indentation_levels if level % 4 != 0]
            if inconsistent:
                return {
                    'type': 'indentation_consistency',
                    'severity': 'medium',
                    'inconsistent_levels': list(set(inconsistent)),
                    'expected': 'multiples of 4 spaces'
                }
        
        return None
    
    def _check_inefficient_loops(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Check for inefficient loop patterns"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # Check for range(len()) pattern
                if (isinstance(node.iter, ast.Call) and 
                    isinstance(node.iter.func, ast.Name) and 
                    node.iter.func.id == 'range' and 
                    len(node.iter.args) == 1 and 
                    isinstance(node.iter.args[0], ast.Call) and 
                    isinstance(node.iter.args[0].func, ast.Name) and 
                    node.iter.args[0].func.id == 'len'):
                    
                    issues.append({
                        'type': 'inefficient_loop',
                        'severity': 'medium',
                        'pattern': 'range(len())',
                        'line': node.lineno,
                        'suggestion': 'Use enumerate() or iterate directly'
                    })
        
        return issues
    
    def _check_repeated_computations(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Check for repeated computations in loops"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                # Look for repeated function calls or attribute access
                calls_in_loop = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        calls_in_loop.append(ast.dump(child))
                
                # Count occurrences
                call_counts = Counter(calls_in_loop)
                repeated_calls = {call: count for call, count in call_counts.items() if count > 1}
                
                if repeated_calls:
                    issues.append({
                        'type': 'repeated_computation',
                        'severity': 'medium',
                        'line': node.lineno,
                        'repeated_calls': len(repeated_calls),
                        'suggestion': 'Cache repeated computations outside the loop'
                    })
        
        return issues
    
    def _check_exception_handling(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Check exception handling patterns"""
        issues = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                # Check for bare except clauses
                for handler in node.handlers:
                    if handler.type is None:
                        issues.append({
                            'type': 'bare_except',
                            'severity': 'high',
                            'line': handler.lineno,
                            'suggestion': 'Specify exception types'
                        })
                
                # Check for empty except blocks
                for handler in node.handlers:
                    if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
                        issues.append({
                            'type': 'empty_except',
                            'severity': 'medium',
                            'line': handler.lineno,
                            'suggestion': 'Add proper error handling or logging'
                        })
        
        return issues
    
    def _check_memory_efficiency(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Check for memory-inefficient operations"""
        issues = []
        
        for node in ast.walk(tree):
            # Check for list comprehensions that could be generator expressions
            if isinstance(node, ast.ListComp):
                # If the list is only used for iteration, suggest generator
                issues.append({
                    'type': 'list_comprehension_optimization',
                    'severity': 'low',
                    'line': node.lineno,
                    'suggestion': 'Consider using generator expression if only iterating'
                })
        
        return issues
    
    def _run_flake8_analysis(self, content: str) -> List[Dict[str, Any]]:
        """Run flake8 analysis if available"""
        # This is a simplified version - in practice, you'd run flake8 on the actual file
        return []
    
    def _run_black_analysis(self, content: str) -> List[Dict[str, Any]]:
        """Check if code is formatted according to Black"""
        try:
            formatted = black.format_str(content, mode=black.FileMode())
            if formatted != content:
                return [{
                    'type': 'black_formatting',
                    'severity': 'low',
                    'message': 'Code is not formatted according to Black'
                }]
        except:
            pass
        return []
    
    def _evaluate_docstring_quality(self, docstring: str) -> Dict[str, Any]:
        """Evaluate docstring quality"""
        quality = {
            'length': len(docstring),
            'has_description': bool(docstring.strip()),
            'has_parameters': 'Args:' in docstring or 'Parameters:' in docstring,
            'has_returns': 'Returns:' in docstring or 'Return:' in docstring,
            'has_examples': 'Example:' in docstring or 'Examples:' in docstring,
            'score': 0
        }
        
        # Calculate quality score
        score = 0
        if quality['has_description']:
            score += 25
        if quality['has_parameters']:
            score += 25
        if quality['has_returns']:
            score += 25
        if quality['has_examples']:
            score += 25
        
        quality['score'] = score
        return quality
    
    def _calculate_maintainability_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate overall maintainability score"""
        scores = []
        
        # Complexity score (0-100, lower complexity = higher score)
        avg_complexity = analysis['complexity_analysis']['average_complexity']
        complexity_score = max(0, 100 - (avg_complexity * 10))
        scores.append(complexity_score)
        
        # Style score
        style_score = analysis['style_analysis']['style_score']
        scores.append(style_score)
        
        # Performance score
        performance_score = analysis['performance_analysis']['performance_score']
        scores.append(performance_score)
        
        # Documentation score
        doc_score = analysis['documentation_analysis']['documentation_score']
        scores.append(doc_score)
        
        # Security score
        security_score = analysis['security_analysis']['security_score']
        scores.append(security_score)
        
        return statistics.mean(scores) if scores else 0
    
    def _calculate_style_score(self, style_issues: List[Dict[str, Any]]) -> float:
        """Calculate style score based on issues"""
        if not style_issues:
            return 100.0
        
        penalty = 0
        for issue in style_issues:
            if issue['severity'] == 'high':
                penalty += issue['count'] * 10
            elif issue['severity'] == 'medium':
                penalty += issue['count'] * 5
            else:
                penalty += issue['count'] * 2
        
        return max(0, 100 - penalty)
    
    def _calculate_performance_score(self, performance_issues: List[Dict[str, Any]]) -> float:
        """Calculate performance score based on issues"""
        if not performance_issues:
            return 100.0
        
        penalty = 0
        for issue in performance_issues:
            if issue['severity'] == 'high':
                penalty += 20
            elif issue['severity'] == 'medium':
                penalty += 10
            else:
                penalty += 5
        
        return max(0, 100 - penalty)
    
    def _calculate_security_score(self, security_issues: List[Dict[str, Any]]) -> float:
        """Calculate security score based on issues"""
        if not security_issues:
            return 100.0
        
        penalty = 0
        for issue in security_issues:
            if issue['severity'] == 'high':
                penalty += 30
            elif issue['severity'] == 'medium':
                penalty += 15
            else:
                penalty += 5
        
        return max(0, 100 - penalty)
    
    def _calculate_overall_grade(self, analysis: Dict[str, Any]) -> str:
        """Calculate overall grade based on maintainability score"""
        score = analysis['maintainability_score']
        
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _generate_suggestions(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate improvement suggestions"""
        suggestions = []
        
        # Complexity suggestions
        complex_functions = analysis['complexity_analysis']['complex_functions']
        for func in complex_functions:
            suggestions.append({
                'category': 'complexity',
                'priority': 'high',
                'title': f'Reduce complexity of function "{func["name"]}"',
                'description': f'Function has cyclomatic complexity of {func["cyclomatic_complexity"]}',
                'suggestion': 'Consider breaking down into smaller functions or simplifying logic'
            })
        
        # Style suggestions
        style_issues = analysis['style_analysis']['style_issues']
        for issue in style_issues:
            suggestions.append({
                'category': 'style',
                'priority': issue['severity'],
                'title': f'Fix {issue["type"]} issues',
                'description': f'Found {issue["count"]} instances',
                'suggestion': 'Follow PEP 8 style guidelines'
            })
        
        # Performance suggestions
        performance_issues = analysis['performance_analysis']['performance_issues']
        for issue in performance_issues:
            suggestions.append({
                'category': 'performance',
                'priority': issue['severity'],
                'title': f'Optimize {issue["type"]}',
                'description': issue.get('suggestion', 'Performance optimization needed'),
                'suggestion': issue.get('suggestion', 'Review and optimize this pattern')
            })
        
        # Documentation suggestions
        missing_docs = analysis['documentation_analysis']['missing_docstrings']
        if missing_docs:
            suggestions.append({
                'category': 'documentation',
                'priority': 'medium',
                'title': 'Add missing docstrings',
                'description': f'{len(missing_docs)} functions/classes lack documentation',
                'suggestion': 'Add comprehensive docstrings with parameters and return values'
            })
        
        return suggestions
    
    def _generate_formatting_suggestions(self, style_issues: List[Dict[str, Any]]) -> List[str]:
        """Generate formatting suggestions"""
        suggestions = []
        
        for issue in style_issues:
            if issue['type'] == 'line_length':
                suggestions.append('Break long lines into multiple lines')
            elif issue['type'] == 'trailing_whitespace':
                suggestions.append('Remove trailing whitespace')
            elif issue['type'] == 'indentation_consistency':
                suggestions.append('Use consistent indentation (4 spaces)')
        
        return suggestions
    
    def _generate_optimization_suggestions(self, performance_issues: List[Dict[str, Any]]) -> List[str]:
        """Generate optimization suggestions"""
        suggestions = []
        
        for issue in performance_issues:
            if 'suggestion' in issue:
                suggestions.append(issue['suggestion'])
        
        return suggestions
    
    def _generate_security_recommendations(self, security_issues: List[Dict[str, Any]]) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        for issue in security_issues:
            if issue['type'] == 'dangerous_function':
                recommendations.append(f'Avoid using {issue["function"]}() - consider safer alternatives')
            elif issue['type'] == 'hardcoded_secret':
                recommendations.append('Move secrets to environment variables or secure storage')
            elif issue['type'] == 'sql_injection_risk':
                recommendations.append('Use parameterized queries to prevent SQL injection')
        
        return recommendations
    
    def _generate_directory_recommendations(self, summary_stats: Dict[str, Any]) -> List[str]:
        """Generate recommendations for the entire directory"""
        recommendations = []
        
        if summary_stats['avg_complexity'] > 10:
            recommendations.append('Consider refactoring complex functions to improve maintainability')
        
        if summary_stats['avg_maintainability'] < 70:
            recommendations.append('Focus on improving code quality across the project')
        
        # Check grade distribution
        grade_dist = summary_stats['grade_distribution']
        if grade_dist.get('D', 0) + grade_dist.get('F', 0) > grade_dist.get('A', 0):
            recommendations.append('Many files have low quality grades - prioritize code improvements')
        
        return recommendations
    
    def generate_report(self, analysis: Dict[str, Any], format: str = 'json') -> str:
        """Generate a comprehensive report"""
        if format == 'json':
            return json.dumps(analysis, indent=2, default=str)
        elif format == 'html':
            return self._generate_html_report(analysis)
        elif format == 'markdown':
            return self._generate_markdown_report(analysis)
        else:
            return str(analysis)
    
    def _generate_html_report(self, analysis: Dict[str, Any]) -> str:
        """Generate HTML report"""
        html = f"""
        <html>
        <head>
            <title>Code Quality Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .score {{ font-size: 24px; font-weight: bold; color: #2e7d32; }}
                .grade {{ font-size: 48px; font-weight: bold; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .issue {{ margin: 10px 0; padding: 10px; background-color: #fff3cd; border-radius: 3px; }}
                .suggestion {{ margin: 10px 0; padding: 10px; background-color: #d4edda; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Code Quality Report</h1>
                <div class="score">Maintainability Score: {analysis.get('maintainability_score', 0):.1f}/100</div>
                <div class="grade">Grade: {analysis.get('overall_grade', 'N/A')}</div>
            </div>
            
            <div class="section">
                <h2>Basic Metrics</h2>
                <p>Lines of Code: {analysis.get('basic_metrics', {}).get('lines_of_code', 0)}</p>
                <p>Functions: {analysis.get('basic_metrics', {}).get('function_count', 0)}</p>
                <p>Classes: {analysis.get('basic_metrics', {}).get('class_count', 0)}</p>
            </div>
            
            <div class="section">
                <h2>Suggestions</h2>
                {''.join(f'<div class="suggestion"><strong>{s["title"]}</strong><br>{s["description"]}</div>' 
                        for s in analysis.get('suggestions', []))}
            </div>
        </body>
        </html>
        """
        return html
    
    def _generate_markdown_report(self, analysis: Dict[str, Any]) -> str:
        """Generate Markdown report"""
        md = f"""
# Code Quality Report

## Summary
- **Maintainability Score**: {analysis.get('maintainability_score', 0):.1f}/100
- **Overall Grade**: {analysis.get('overall_grade', 'N/A')}

## Basic Metrics
- **Lines of Code**: {analysis.get('basic_metrics', {}).get('lines_of_code', 0)}
- **Functions**: {analysis.get('basic_metrics', {}).get('function_count', 0)}
- **Classes**: {analysis.get('basic_metrics', {}).get('class_count', 0)}

## Suggestions
"""
        
        for suggestion in analysis.get('suggestions', []):
            md += f"### {suggestion['title']}\n"
            md += f"**Priority**: {suggestion['priority']}\n"
            md += f"**Description**: {suggestion['description']}\n"
            md += f"**Suggestion**: {suggestion['suggestion']}\n\n"
        
        return md


if __name__ == "__main__":
    # Example usage
    validator = CodeQualityValidator()
    
    # Analyze a single file
    print("🔍 Analyzing code quality...")
    analysis = validator.analyze_file("practice.py")
    
    if 'error' not in analysis:
        print(f"📊 Maintainability Score: {analysis['maintainability_score']:.1f}/100")
        print(f"🎯 Overall Grade: {analysis['overall_grade']}")
        print(f"💡 Suggestions: {len(analysis['suggestions'])}")
        
        # Generate report
        report = validator.generate_report(analysis, 'markdown')
        with open('code_quality_report.md', 'w') as f:
            f.write(report)
        print("📄 Report saved to code_quality_report.md")
    else:
        print(f"❌ Error: {analysis['error']}")
    
    # Analyze directory
    print("\n🔍 Analyzing directory...")
    dir_analysis = validator.analyze_directory(".")
    
    if 'error' not in dir_analysis:
        stats = dir_analysis['summary_stats']
        print(f"📁 Files analyzed: {stats['total_files']}")
        print(f"📊 Average complexity: {stats['avg_complexity']:.1f}")
        print(f"🎯 Average maintainability: {stats['avg_maintainability']:.1f}")
        print(f"📈 Grade distribution: {dict(stats['grade_distribution'])}") 