#!/usr/bin/env python3
"""
Enhanced Git Automation System
Comprehensive git workflows with auto-push, branch management, and safety checks
"""

import os
import sys
import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sqlite3
import logging

class GitAutomation:
    def __init__(self, repo_path=None):
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.db_path = self.repo_path / "practice_data" / "problems.db"
        self.config_path = self.repo_path / "practice_data" / "git_config.json"
        
        # Setup logging
        self.setup_logging()
        
        # Load configuration
        self.load_config()
        
        # Initialize git if needed
        self.ensure_git_repository()
    
    def setup_logging(self):
        """Setup logging for git operations"""
        log_dir = self.repo_path / "practice_data" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'git_automation.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self):
        """Load git automation configuration"""
        default_config = {
            "auto_push": True,
            "remote_name": "origin",
            "main_branch": "main",
            "commit_on_completion": True,
            "commit_on_milestone": True,
            "push_on_commit": True,
            "create_tags": True,
            "milestone_interval": 10,
            "max_commits_per_hour": 20,
            "safety_checks": True,
            "backup_before_push": True,
            "conflict_resolution": "auto",
            "commit_templates": {
                "problem_solved": "✅ Solved: {title} ({difficulty}) - {topic}",
                "milestone": "🏆 Milestone: {count} problems completed",
                "review_completed": "📚 Reviewed: {title} ({performance}) - {topic}",
                "session_complete": "🎯 Session complete: {count} problems in {time} minutes",
                "topic_mastery": "🎓 Topic mastery: {topic} ({count} problems)",
                "streak_milestone": "🔥 {days}-day streak milestone achieved"
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                self.logger.warning(f"Could not load git config: {e}")
        
        self.config = default_config
        self.save_config()
    
    def save_config(self):
        """Save git automation configuration"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def ensure_git_repository(self):
        """Ensure we're in a git repository and set up remotes"""
        try:
            # Check if already a git repo
            result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                                  cwd=self.repo_path, capture_output=True)
            
            if result.returncode != 0:
                self.logger.info("Initializing git repository...")
                subprocess.run(['git', 'init'], cwd=self.repo_path, check=True)
                
                # Set up initial configuration
                self._setup_git_config()
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error setting up git repository: {e}")
    
    def _setup_git_config(self):
        """Setup initial git configuration"""
        try:
            # Set user name and email if not already set
            result = subprocess.run(['git', 'config', 'user.name'], 
                                  cwd=self.repo_path, capture_output=True)
            if result.returncode != 0:
                subprocess.run(['git', 'config', 'user.name', 'Coding Practice Bot'], 
                             cwd=self.repo_path, check=True)
            
            result = subprocess.run(['git', 'config', 'user.email'], 
                                  cwd=self.repo_path, capture_output=True)
            if result.returncode != 0:
                subprocess.run(['git', 'config', 'user.email', 'practice@example.com'], 
                             cwd=self.repo_path, check=True)
            
            # Create initial commit if no commits exist
            result = subprocess.run(['git', 'rev-list', '--all'], 
                                  cwd=self.repo_path, capture_output=True)
            if not result.stdout.strip():
                self.logger.info("Creating initial commit...")
                subprocess.run(['git', 'add', '.'], cwd=self.repo_path, check=True)
                subprocess.run(['git', 'commit', '-m', '🚀 Initial commit: Coding practice system setup'], 
                             cwd=self.repo_path, check=True)
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error setting up git config: {e}")
    
    def check_safety_conditions(self) -> Tuple[bool, List[str]]:
        """Perform safety checks before committing/pushing"""
        if not self.config.get("safety_checks", True):
            return True, []
        
        issues = []
        
        try:
            # Check if we're on the right branch
            current_branch = self.get_current_branch()
            main_branch = self.config.get("main_branch", "main")
            
            if current_branch != main_branch:
                issues.append(f"Not on main branch (currently on: {current_branch})")
            
            # Check for uncommitted changes to critical files
            critical_files = ['.gitignore', 'README.md', 'requirements.txt']
            result = subprocess.run(['git', 'diff', '--name-only'] + critical_files, 
                                  cwd=self.repo_path, capture_output=True, text=True)
            
            if result.stdout.strip():
                issues.append("Uncommitted changes to critical files detected")
            
            # Check commit rate (prevent spam)
            if self._check_commit_rate_limit():
                issues.append("Too many commits in the last hour (rate limit)")
            
            # Check if remote exists for auto-push
            if self.config.get("auto_push", False):
                if not self._remote_exists():
                    issues.append("Auto-push enabled but no remote configured")
            
            return len(issues) == 0, issues
        
        except Exception as e:
            self.logger.error(f"Safety check failed: {e}")
            return False, [f"Safety check error: {e}"]
    
    def _check_commit_rate_limit(self) -> bool:
        """Check if we're committing too frequently"""
        try:
            max_commits = self.config.get("max_commits_per_hour", 20)
            since_time = (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
            
            result = subprocess.run([
                'git', 'log', '--since', since_time, '--oneline'
            ], cwd=self.repo_path, capture_output=True, text=True)
            
            commit_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            return commit_count >= max_commits
        
        except Exception:
            return False
    
    def _remote_exists(self) -> bool:
        """Check if a remote repository is configured"""
        try:
            remote_name = self.config.get("remote_name", "origin")
            result = subprocess.run(['git', 'remote', 'get-url', remote_name], 
                                  cwd=self.repo_path, capture_output=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def get_current_branch(self) -> str:
        """Get current git branch"""
        try:
            result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                                  cwd=self.repo_path, capture_output=True, text=True)
            return result.stdout.strip()
        except Exception:
            return "main"
    
    def commit_problem_solution(self, problem_title: str, difficulty: str, topic: str, 
                              additional_info: Dict = None) -> bool:
        """Commit a solved problem with enhanced metadata"""
        try:
            # Perform safety checks
            safe, issues = self.check_safety_conditions()
            if not safe and self.config.get("safety_checks", True):
                self.logger.warning(f"Safety checks failed: {', '.join(issues)}")
                if not self._prompt_user_override():
                    return False
            
            # Add all changes
            subprocess.run(['git', 'add', '.'], cwd=self.repo_path, check=True)
            
            # Create commit message
            template = self.config["commit_templates"]["problem_solved"]
            commit_message = template.format(
                title=problem_title,
                difficulty=difficulty.title(),
                topic=topic.title()
            )
            
            # Add additional context
            if additional_info:
                commit_message += f"\n\n"
                if additional_info.get('time_spent'):
                    commit_message += f"⏱️  Time spent: {additional_info['time_spent']} minutes\n"
                if additional_info.get('language'):
                    commit_message += f"💻 Language: {additional_info['language']}\n"
                if additional_info.get('approach'):
                    commit_message += f"🎯 Approach: {additional_info['approach']}\n"
                if additional_info.get('notes'):
                    commit_message += f"📝 Notes: {additional_info['notes']}\n"
            
            # Commit
            subprocess.run(['git', 'commit', '-m', commit_message], 
                         cwd=self.repo_path, check=True)
            
            self.logger.info(f"Committed: {problem_title}")
            
            # Check for milestones
            self._check_and_create_milestones()
            
            # Auto-push if enabled
            if self.config.get("push_on_commit", True):
                return self.push_to_remote()
            
            return True
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to commit problem solution: {e}")
            return False
    
    def commit_review_session(self, problem_title: str, performance: str, topic: str) -> bool:
        """Commit a spaced repetition review"""
        try:
            subprocess.run(['git', 'add', '.'], cwd=self.repo_path, check=True)
            
            template = self.config["commit_templates"]["review_completed"]
            commit_message = template.format(
                title=problem_title,
                performance=performance.title(),
                topic=topic.title()
            )
            
            subprocess.run(['git', 'commit', '-m', commit_message], 
                         cwd=self.repo_path, check=True)
            
            self.logger.info(f"Committed review: {problem_title}")
            
            if self.config.get("push_on_commit", True):
                return self.push_to_remote()
            
            return True
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to commit review: {e}")
            return False
    
    def commit_session_summary(self, session_stats: Dict) -> bool:
        """Commit a practice session summary"""
        try:
            subprocess.run(['git', 'add', '.'], cwd=self.repo_path, check=True)
            
            template = self.config["commit_templates"]["session_complete"]
            commit_message = template.format(
                count=session_stats.get('problems_solved', 0),
                time=session_stats.get('time_spent', 0)
            )
            
            # Add detailed stats
            commit_message += f"\n\n📊 Session Statistics:\n"
            commit_message += f"• Easy: {session_stats.get('easy_count', 0)}\n"
            commit_message += f"• Medium: {session_stats.get('medium_count', 0)}\n"
            commit_message += f"• Hard: {session_stats.get('hard_count', 0)}\n"
            commit_message += f"• Topics: {', '.join(session_stats.get('topics', []))}\n"
            
            subprocess.run(['git', 'commit', '-m', commit_message], 
                         cwd=self.repo_path, check=True)
            
            self.logger.info(f"Committed session summary")
            
            if self.config.get("push_on_commit", True):
                return self.push_to_remote()
            
            return True
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to commit session summary: {e}")
            return False
    
    def _check_and_create_milestones(self):
        """Check for milestones and create tags"""
        if not self.config.get("create_tags", True):
            return
        
        try:
            # Get total completed problems count
            total_completed = self._get_total_completed()
            milestone_interval = self.config.get("milestone_interval", 10)
            
            if total_completed > 0 and total_completed % milestone_interval == 0:
                self._create_milestone_tag(total_completed)
            
            # Check for streak milestones
            current_streak = self._get_current_streak()
            if current_streak > 0 and current_streak % 7 == 0:  # Weekly streak milestones
                self._create_streak_tag(current_streak)
        
        except Exception as e:
            self.logger.error(f"Error checking milestones: {e}")
    
    def _get_total_completed(self) -> int:
        """Get total number of completed problems from database"""
        try:
            if not self.db_path.exists():
                return 0
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(DISTINCT problem_id) FROM progress WHERE status = "completed"')
            count = cursor.fetchone()[0]
            conn.close()
            return count
        
        except Exception:
            return 0
    
    def _get_current_streak(self) -> int:
        """Get current practice streak"""
        try:
            if not self.db_path.exists():
                return 0
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get dates with completed problems
            cursor.execute('''
                SELECT DISTINCT DATE(completed_at) as date
                FROM progress 
                WHERE status = 'completed'
                ORDER BY date DESC
            ''')
            
            dates = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if not dates:
                return 0
            
            # Calculate streak
            streak = 0
            current_date = datetime.now().date()
            
            for date_str in dates:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                expected_date = current_date - timedelta(days=streak)
                
                if date_obj == expected_date:
                    streak += 1
                elif date_obj < expected_date:
                    break
            
            return streak
        
        except Exception:
            return 0
    
    def _create_milestone_tag(self, count: int):
        """Create a milestone git tag"""
        try:
            tag_name = f"milestone-{count}"
            message = f"🏆 Milestone: {count} problems completed"
            
            # Check if tag already exists
            result = subprocess.run(['git', 'tag', '-l', tag_name], 
                                  cwd=self.repo_path, capture_output=True, text=True)
            
            if not result.stdout.strip():
                subprocess.run(['git', 'tag', '-a', tag_name, '-m', message], 
                             cwd=self.repo_path, check=True)
                
                self.logger.info(f"Created milestone tag: {tag_name}")
                
                # Push tag if auto-push enabled
                if self.config.get("auto_push", False):
                    subprocess.run(['git', 'push', 'origin', tag_name], 
                                 cwd=self.repo_path, check=False)
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create milestone tag: {e}")
    
    def _create_streak_tag(self, streak: int):
        """Create a streak milestone tag"""
        try:
            tag_name = f"streak-{streak}d"
            message = f"🔥 {streak}-day practice streak achieved"
            
            # Check if tag already exists
            result = subprocess.run(['git', 'tag', '-l', tag_name], 
                                  cwd=self.repo_path, capture_output=True, text=True)
            
            if not result.stdout.strip():
                subprocess.run(['git', 'tag', '-a', tag_name, '-m', message], 
                             cwd=self.repo_path, check=True)
                
                self.logger.info(f"Created streak tag: {tag_name}")
                
                # Push tag if auto-push enabled
                if self.config.get("auto_push", False):
                    subprocess.run(['git', 'push', 'origin', tag_name], 
                                 cwd=self.repo_path, check=False)
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create streak tag: {e}")
    
    def push_to_remote(self, force: bool = False) -> bool:
        """Push commits to remote repository"""
        if not self.config.get("auto_push", False) and not force:
            return True
        
        try:
            # Check if remote exists
            if not self._remote_exists():
                self.logger.warning("No remote repository configured for auto-push")
                return False
            
            # Backup current state if enabled
            if self.config.get("backup_before_push", True):
                self._create_backup()
            
            # Pull latest changes first to handle conflicts
            remote_name = self.config.get("remote_name", "origin")
            main_branch = self.config.get("main_branch", "main")
            
            self.logger.info("Pulling latest changes from remote...")
            result = subprocess.run(['git', 'pull', remote_name, main_branch], 
                                  cwd=self.repo_path, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.warning(f"Pull failed: {result.stderr}")
                if not self._handle_pull_conflicts(result.stderr):
                    return False
            
            # Push changes
            self.logger.info("Pushing changes to remote...")
            result = subprocess.run(['git', 'push', remote_name, main_branch], 
                                  cwd=self.repo_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("Successfully pushed to remote")
                
                # Push tags as well
                subprocess.run(['git', 'push', remote_name, '--tags'], 
                             cwd=self.repo_path, check=False)
                
                return True
            else:
                self.logger.error(f"Push failed: {result.stderr}")
                return False
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to push to remote: {e}")
            return False
    
    def _handle_pull_conflicts(self, error_output: str) -> bool:
        """Handle merge conflicts during pull"""
        conflict_resolution = self.config.get("conflict_resolution", "auto")
        
        if "CONFLICT" in error_output:
            if conflict_resolution == "auto":
                # Try to resolve automatically
                try:
                    # Add conflicted files (accept theirs)
                    subprocess.run(['git', 'add', '.'], cwd=self.repo_path, check=True)
                    subprocess.run(['git', 'commit', '-m', '🔀 Auto-resolved merge conflicts'], 
                                 cwd=self.repo_path, check=True)
                    self.logger.info("Auto-resolved merge conflicts")
                    return True
                
                except subprocess.CalledProcessError:
                    self.logger.error("Failed to auto-resolve conflicts")
                    return False
            
            elif conflict_resolution == "skip":
                self.logger.warning("Skipping push due to conflicts")
                return False
            
            else:  # manual
                self.logger.error("Manual conflict resolution required")
                print("\n⚠️  MERGE CONFLICTS DETECTED")
                print("Please resolve conflicts manually and run:")
                print("  git add .")
                print("  git commit -m 'Resolved merge conflicts'")
                print("  git push origin main")
                return False
        
        return True
    
    def _create_backup(self):
        """Create a backup of current state before pushing"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_branch = f"backup_{timestamp}"
            
            subprocess.run(['git', 'branch', backup_branch], 
                         cwd=self.repo_path, check=True)
            
            self.logger.info(f"Created backup branch: {backup_branch}")
        
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to create backup: {e}")
    
    def _prompt_user_override(self) -> bool:
        """Prompt user to override safety checks"""
        try:
            response = input("Override safety checks and continue? (y/N): ").lower()
            return response in ['y', 'yes']
        except:
            return False
    
    def setup_remote_repository(self, remote_url: str, remote_name: str = "origin") -> bool:
        """Setup remote repository for auto-push"""
        try:
            # Remove existing remote if it exists
            subprocess.run(['git', 'remote', 'remove', remote_name], 
                         cwd=self.repo_path, capture_output=True)
            
            # Add new remote
            subprocess.run(['git', 'remote', 'add', remote_name, remote_url], 
                         cwd=self.repo_path, check=True)
            
            # Test connection
            result = subprocess.run(['git', 'remote', 'get-url', remote_name], 
                                  cwd=self.repo_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Remote repository configured: {remote_url}")
                
                # Update config
                self.config["remote_name"] = remote_name
                self.config["auto_push"] = True
                self.save_config()
                
                return True
            
            return False
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to setup remote repository: {e}")
            return False
    
    def get_repository_stats(self) -> Dict:
        """Get comprehensive repository statistics"""
        try:
            stats = {}
            
            # Total commits
            result = subprocess.run(['git', 'rev-list', '--count', 'HEAD'], 
                                  cwd=self.repo_path, capture_output=True, text=True)
            stats['total_commits'] = int(result.stdout.strip()) if result.returncode == 0 else 0
            
            # Commits in last 30 days
            since_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            result = subprocess.run(['git', 'rev-list', '--count', f'--since={since_date}', 'HEAD'], 
                                  cwd=self.repo_path, capture_output=True, text=True)
            stats['commits_last_30_days'] = int(result.stdout.strip()) if result.returncode == 0 else 0
            
            # Current branch
            stats['current_branch'] = self.get_current_branch()
            
            # Remote status
            stats['has_remote'] = self._remote_exists()
            stats['auto_push_enabled'] = self.config.get("auto_push", False)
            
            # Tags count
            result = subprocess.run(['git', 'tag'], 
                                  cwd=self.repo_path, capture_output=True, text=True)
            stats['total_tags'] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            return stats
        
        except Exception as e:
            self.logger.error(f"Failed to get repository stats: {e}")
            return {}
    
    def cleanup_old_backups(self, keep_count: int = 5):
        """Clean up old backup branches"""
        try:
            # Get all backup branches
            result = subprocess.run(['git', 'branch', '--list', 'backup_*'], 
                                  cwd=self.repo_path, capture_output=True, text=True)
            
            branches = [b.strip().replace('*', '').strip() for b in result.stdout.split('\n') if b.strip()]
            backup_branches = [b for b in branches if b.startswith('backup_')]
            
            if len(backup_branches) > keep_count:
                # Sort by date (assuming timestamp format)
                backup_branches.sort()
                
                # Delete oldest branches
                for branch in backup_branches[:-keep_count]:
                    subprocess.run(['git', 'branch', '-D', branch], 
                                 cwd=self.repo_path, check=True)
                    self.logger.info(f"Deleted old backup branch: {branch}")
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to cleanup old backups: {e}")

def integrate_with_practice_system():
    """Integration helper for the main practice system"""
    git_automation = GitAutomation()
    
    # Check if auto-push is properly configured
    if git_automation.config.get("auto_push", False):
        if not git_automation._remote_exists():
            print("\n⚠️  Auto-push is enabled but no remote repository is configured.")
            print("To setup auto-push to GitHub:")
            print("1. Create a repository on GitHub")
            print("2. Run: git remote add origin <your-repo-url>")
            print("3. Run: git push -u origin main")
            print("\nOr disable auto-push in practice_data/git_config.json")
    
    return git_automation

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Git Automation System")
    parser.add_argument('--setup-remote', help='Setup remote repository URL')
    parser.add_argument('--stats', action='store_true', help='Show repository statistics')
    parser.add_argument('--cleanup', action='store_true', help='Cleanup old backup branches')
    parser.add_argument('--test-push', action='store_true', help='Test push to remote')
    
    args = parser.parse_args()
    
    git_automation = GitAutomation()
    
    if args.setup_remote:
        success = git_automation.setup_remote_repository(args.setup_remote)
        print(f"Remote setup: {'✅ Success' if success else '❌ Failed'}")
    
    elif args.stats:
        stats = git_automation.get_repository_stats()
        print("\n📊 Repository Statistics:")
        print("=" * 40)
        for key, value in stats.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
    
    elif args.cleanup:
        git_automation.cleanup_old_backups()
        print("✅ Cleanup complete")
    
    elif args.test_push:
        success = git_automation.push_to_remote(force=True)
        print(f"Test push: {'✅ Success' if success else '❌ Failed'}")
    
    else:
        print("Git Automation System")
        print("Use --help for available options") 