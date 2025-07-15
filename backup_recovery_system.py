#!/usr/bin/env python3
"""
Advanced Backup and Recovery System
Provides automated backups, versioning, disaster recovery, and data integrity checks
"""

import os
import shutil
import json
import sqlite3
import hashlib
import tarfile
import gzip
import threading
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass
from enum import Enum
import tempfile

try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

try:
    import dropbox
    DROPBOX_AVAILABLE = True
except ImportError:
    DROPBOX_AVAILABLE = False

class BackupType(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"

class BackupStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class BackupConfig:
    """Configuration for backup operations"""
    backup_directory: str
    retention_days: int = 30
    compression: bool = True
    encryption: bool = False
    cloud_storage: bool = False
    cloud_provider: str = "aws"
    max_backup_size: int = 1024 * 1024 * 1024  # 1GB default
    backup_schedule: str = "daily"
    verify_integrity: bool = True

@dataclass
class BackupMetadata:
    """Metadata for backup operations"""
    backup_id: str
    backup_type: BackupType
    timestamp: datetime
    file_count: int
    total_size: int
    checksum: str
    status: BackupStatus
    error_message: Optional[str] = None
    files_included: List[str] = None

class BackupRecoverySystem:
    """Advanced backup and recovery system"""
    
    def __init__(self, config: BackupConfig):
        self.config = config
        self.backup_dir = Path(config.backup_directory)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Initialize metadata database
        self.metadata_db = self.backup_dir / "backup_metadata.db"
        self._init_metadata_db()
        
        # Initialize cloud storage if enabled
        self.cloud_client = None
        if config.cloud_storage:
            self.cloud_client = self._init_cloud_storage()
        
        # Backup scheduler
        self.scheduler_thread = None
        self.scheduler_running = False
        
        # File monitoring
        self.file_monitor = FileMonitor()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for backup operations"""
        logger = logging.getLogger('backup_recovery')
        logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = self.backup_dir / "backup.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _init_metadata_db(self):
        """Initialize metadata database"""
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backups (
                backup_id TEXT PRIMARY KEY,
                backup_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                file_count INTEGER NOT NULL,
                total_size INTEGER NOT NULL,
                checksum TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                files_included TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_versions (
                file_path TEXT NOT NULL,
                backup_id TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                modified_time TEXT NOT NULL,
                PRIMARY KEY (file_path, backup_id),
                FOREIGN KEY (backup_id) REFERENCES backups (backup_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recovery_operations (
                recovery_id TEXT PRIMARY KEY,
                backup_id TEXT NOT NULL,
                recovery_type TEXT NOT NULL,
                target_directory TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL,
                files_recovered INTEGER DEFAULT 0,
                error_message TEXT,
                FOREIGN KEY (backup_id) REFERENCES backups (backup_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _init_cloud_storage(self):
        """Initialize cloud storage client"""
        if not self.config.cloud_storage:
            return None
        
        if self.config.cloud_provider == "aws" and AWS_AVAILABLE:
            try:
                return boto3.client('s3')
            except Exception as e:
                self.logger.error(f"Failed to initialize AWS S3 client: {e}")
                return None
        
        elif self.config.cloud_provider == "dropbox" and DROPBOX_AVAILABLE:
            try:
                # You would need to configure Dropbox API key
                # return dropbox.Dropbox(access_token)
                pass
            except Exception as e:
                self.logger.error(f"Failed to initialize Dropbox client: {e}")
                return None
        
        return None
    
    def create_backup(self, source_paths: List[str], backup_type: BackupType = BackupType.FULL) -> str:
        """Create a backup of specified paths"""
        backup_id = self._generate_backup_id()
        
        try:
            self.logger.info(f"Starting {backup_type.value} backup: {backup_id}")
            
            # Update status to running
            self._update_backup_status(backup_id, BackupStatus.RUNNING)
            
            # Determine files to backup
            files_to_backup = self._get_files_to_backup(source_paths, backup_type)
            
            if not files_to_backup:
                self.logger.warning(f"No files to backup for {backup_id}")
                self._update_backup_status(backup_id, BackupStatus.COMPLETED)
                return backup_id
            
            # Create backup archive
            backup_path = self._create_backup_archive(backup_id, files_to_backup)
            
            # Calculate checksum
            checksum = self._calculate_checksum(backup_path)
            
            # Get backup size
            backup_size = os.path.getsize(backup_path)
            
            # Store metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                backup_type=backup_type,
                timestamp=datetime.now(),
                file_count=len(files_to_backup),
                total_size=backup_size,
                checksum=checksum,
                status=BackupStatus.COMPLETED,
                files_included=files_to_backup
            )
            
            self._store_backup_metadata(metadata)
            
            # Upload to cloud if enabled
            if self.config.cloud_storage and self.cloud_client:
                self._upload_to_cloud(backup_path, backup_id)
            
            # Verify backup integrity
            if self.config.verify_integrity:
                if not self._verify_backup_integrity(backup_path, checksum):
                    raise Exception("Backup integrity verification failed")
            
            self.logger.info(f"Backup completed successfully: {backup_id}")
            return backup_id
            
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            self._update_backup_status(backup_id, BackupStatus.FAILED, str(e))
            raise
    
    def restore_backup(self, backup_id: str, target_directory: str, 
                      selective_restore: Optional[List[str]] = None) -> str:
        """Restore a backup to specified directory"""
        recovery_id = self._generate_recovery_id()
        
        try:
            self.logger.info(f"Starting restore operation: {recovery_id}")
            
            # Get backup metadata
            metadata = self._get_backup_metadata(backup_id)
            if not metadata:
                raise Exception(f"Backup {backup_id} not found")
            
            # Find backup file
            backup_path = self.backup_dir / f"{backup_id}.tar.gz"
            if not backup_path.exists():
                # Try to download from cloud
                if self.config.cloud_storage and self.cloud_client:
                    backup_path = self._download_from_cloud(backup_id)
                else:
                    raise Exception(f"Backup file not found: {backup_path}")
            
            # Verify backup integrity
            if self.config.verify_integrity:
                if not self._verify_backup_integrity(backup_path, metadata.checksum):
                    raise Exception("Backup integrity verification failed")
            
            # Create target directory
            target_path = Path(target_directory)
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Extract backup
            files_restored = self._extract_backup(backup_path, target_path, selective_restore)
            
            # Record recovery operation
            self._record_recovery_operation(recovery_id, backup_id, "full", 
                                          target_directory, files_restored)
            
            self.logger.info(f"Restore completed successfully: {recovery_id}")
            return recovery_id
            
        except Exception as e:
            self.logger.error(f"Restore failed: {e}")
            self._record_recovery_operation(recovery_id, backup_id, "full", 
                                          target_directory, 0, str(e))
            raise
    
    def list_backups(self, backup_type: Optional[BackupType] = None, 
                    days: Optional[int] = None) -> List[BackupMetadata]:
        """List available backups"""
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()
        
        query = "SELECT * FROM backups WHERE 1=1"
        params = []
        
        if backup_type:
            query += " AND backup_type = ?"
            params.append(backup_type.value)
        
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            query += " AND timestamp >= ?"
            params.append(cutoff_date.isoformat())
        
        query += " ORDER BY timestamp DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        backups = []
        for row in rows:
            backup = BackupMetadata(
                backup_id=row[0],
                backup_type=BackupType(row[1]),
                timestamp=datetime.fromisoformat(row[2]),
                file_count=row[3],
                total_size=row[4],
                checksum=row[5],
                status=BackupStatus(row[6]),
                error_message=row[7],
                files_included=json.loads(row[8]) if row[8] else None
            )
            backups.append(backup)
        
        conn.close()
        return backups
    
    def delete_backup(self, backup_id: str, delete_from_cloud: bool = True) -> bool:
        """Delete a backup"""
        try:
            # Delete local backup file
            backup_path = self.backup_dir / f"{backup_id}.tar.gz"
            if backup_path.exists():
                backup_path.unlink()
            
            # Delete from cloud if enabled
            if delete_from_cloud and self.config.cloud_storage and self.cloud_client:
                self._delete_from_cloud(backup_id)
            
            # Delete metadata
            conn = sqlite3.connect(self.metadata_db)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM file_versions WHERE backup_id = ?", (backup_id,))
            cursor.execute("DELETE FROM backups WHERE backup_id = ?", (backup_id,))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Backup deleted: {backup_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete backup {backup_id}: {e}")
            return False
    
    def cleanup_old_backups(self) -> int:
        """Clean up old backups based on retention policy"""
        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
        
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT backup_id FROM backups WHERE timestamp < ?", 
                      (cutoff_date.isoformat(),))
        old_backups = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        deleted_count = 0
        for backup_id in old_backups:
            if self.delete_backup(backup_id):
                deleted_count += 1
        
        self.logger.info(f"Cleaned up {deleted_count} old backups")
        return deleted_count
    
    def verify_all_backups(self) -> Dict[str, bool]:
        """Verify integrity of all backups"""
        backups = self.list_backups()
        results = {}
        
        for backup in backups:
            backup_path = self.backup_dir / f"{backup.backup_id}.tar.gz"
            if backup_path.exists():
                results[backup.backup_id] = self._verify_backup_integrity(
                    backup_path, backup.checksum
                )
            else:
                results[backup.backup_id] = False
        
        return results
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """Get backup statistics"""
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()
        
        # Basic statistics
        cursor.execute("SELECT COUNT(*) FROM backups")
        total_backups = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM backups WHERE status = 'completed'")
        successful_backups = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(total_size) FROM backups WHERE status = 'completed'")
        total_size = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT AVG(total_size) FROM backups WHERE status = 'completed'")
        avg_size = cursor.fetchone()[0] or 0
        
        # Recent activity
        cursor.execute("""
            SELECT COUNT(*) FROM backups 
            WHERE timestamp >= datetime('now', '-7 days')
        """)
        recent_backups = cursor.fetchone()[0]
        
        # Backup type distribution
        cursor.execute("SELECT backup_type, COUNT(*) FROM backups GROUP BY backup_type")
        type_distribution = dict(cursor.fetchall())
        
        # Status distribution
        cursor.execute("SELECT status, COUNT(*) FROM backups GROUP BY status")
        status_distribution = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_backups': total_backups,
            'successful_backups': successful_backups,
            'success_rate': (successful_backups / total_backups * 100) if total_backups > 0 else 0,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'average_size_mb': avg_size / (1024 * 1024),
            'recent_backups_7_days': recent_backups,
            'type_distribution': type_distribution,
            'status_distribution': status_distribution
        }
    
    def start_scheduled_backups(self, source_paths: List[str]):
        """Start scheduled backup operations"""
        if self.scheduler_running:
            self.logger.warning("Scheduler already running")
            return
        
        self.scheduler_running = True
        
        # Schedule based on configuration
        if self.config.backup_schedule == "daily":
            schedule.every().day.at("02:00").do(
                self._scheduled_backup, source_paths, BackupType.INCREMENTAL
            )
            schedule.every().sunday.at("01:00").do(
                self._scheduled_backup, source_paths, BackupType.FULL
            )
        elif self.config.backup_schedule == "hourly":
            schedule.every().hour.do(
                self._scheduled_backup, source_paths, BackupType.INCREMENTAL
            )
        
        # Schedule cleanup
        schedule.every().day.at("03:00").do(self.cleanup_old_backups)
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        self.logger.info("Scheduled backups started")
    
    def stop_scheduled_backups(self):
        """Stop scheduled backup operations"""
        self.scheduler_running = False
        schedule.clear()
        self.logger.info("Scheduled backups stopped")
    
    def _generate_backup_id(self) -> str:
        """Generate unique backup ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"backup_{timestamp}_{os.urandom(4).hex()}"
    
    def _generate_recovery_id(self) -> str:
        """Generate unique recovery ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"recovery_{timestamp}_{os.urandom(4).hex()}"
    
    def _get_files_to_backup(self, source_paths: List[str], backup_type: BackupType) -> List[str]:
        """Get list of files to backup based on type"""
        all_files = []
        
        for source_path in source_paths:
            path = Path(source_path)
            if path.is_file():
                all_files.append(str(path))
            elif path.is_dir():
                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        all_files.append(str(file_path))
        
        if backup_type == BackupType.FULL:
            return all_files
        
        elif backup_type == BackupType.INCREMENTAL:
            # Get files modified since last backup
            last_backup = self._get_last_backup()
            if not last_backup:
                return all_files
            
            return self._get_modified_files_since(all_files, last_backup.timestamp)
        
        elif backup_type == BackupType.DIFFERENTIAL:
            # Get files modified since last full backup
            last_full_backup = self._get_last_full_backup()
            if not last_full_backup:
                return all_files
            
            return self._get_modified_files_since(all_files, last_full_backup.timestamp)
        
        return all_files
    
    def _get_modified_files_since(self, files: List[str], timestamp: datetime) -> List[str]:
        """Get files modified since specified timestamp"""
        modified_files = []
        
        for file_path in files:
            try:
                file_stat = os.stat(file_path)
                file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
                if file_mtime > timestamp:
                    modified_files.append(file_path)
            except OSError:
                continue
        
        return modified_files
    
    def _create_backup_archive(self, backup_id: str, files: List[str]) -> Path:
        """Create backup archive"""
        backup_path = self.backup_dir / f"{backup_id}.tar.gz"
        
        with tarfile.open(backup_path, "w:gz" if self.config.compression else "w") as tar:
            for file_path in files:
                try:
                    tar.add(file_path, arcname=os.path.relpath(file_path))
                except Exception as e:
                    self.logger.warning(f"Failed to add {file_path} to backup: {e}")
        
        return backup_path
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _verify_backup_integrity(self, backup_path: Path, expected_checksum: str) -> bool:
        """Verify backup integrity using checksum"""
        try:
            actual_checksum = self._calculate_checksum(backup_path)
            return actual_checksum == expected_checksum
        except Exception as e:
            self.logger.error(f"Integrity verification failed: {e}")
            return False
    
    def _extract_backup(self, backup_path: Path, target_path: Path, 
                       selective_files: Optional[List[str]] = None) -> int:
        """Extract backup archive"""
        files_restored = 0
        
        with tarfile.open(backup_path, "r:gz" if self.config.compression else "r") as tar:
            members = tar.getmembers()
            
            if selective_files:
                # Filter members based on selective restore
                members = [m for m in members if any(sf in m.name for sf in selective_files)]
            
            for member in members:
                try:
                    tar.extract(member, target_path)
                    files_restored += 1
                except Exception as e:
                    self.logger.warning(f"Failed to extract {member.name}: {e}")
        
        return files_restored
    
    def _store_backup_metadata(self, metadata: BackupMetadata):
        """Store backup metadata in database"""
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO backups 
            (backup_id, backup_type, timestamp, file_count, total_size, 
             checksum, status, error_message, files_included)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metadata.backup_id,
            metadata.backup_type.value,
            metadata.timestamp.isoformat(),
            metadata.file_count,
            metadata.total_size,
            metadata.checksum,
            metadata.status.value,
            metadata.error_message,
            json.dumps(metadata.files_included) if metadata.files_included else None
        ))
        
        conn.commit()
        conn.close()
    
    def _get_backup_metadata(self, backup_id: str) -> Optional[BackupMetadata]:
        """Get backup metadata from database"""
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM backups WHERE backup_id = ?", (backup_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if not row:
            return None
        
        return BackupMetadata(
            backup_id=row[0],
            backup_type=BackupType(row[1]),
            timestamp=datetime.fromisoformat(row[2]),
            file_count=row[3],
            total_size=row[4],
            checksum=row[5],
            status=BackupStatus(row[6]),
            error_message=row[7],
            files_included=json.loads(row[8]) if row[8] else None
        )
    
    def _get_last_backup(self) -> Optional[BackupMetadata]:
        """Get last backup metadata"""
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM backups 
            WHERE status = 'completed' 
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
        row = cursor.fetchone()
        
        conn.close()
        
        if not row:
            return None
        
        return BackupMetadata(
            backup_id=row[0],
            backup_type=BackupType(row[1]),
            timestamp=datetime.fromisoformat(row[2]),
            file_count=row[3],
            total_size=row[4],
            checksum=row[5],
            status=BackupStatus(row[6]),
            error_message=row[7],
            files_included=json.loads(row[8]) if row[8] else None
        )
    
    def _get_last_full_backup(self) -> Optional[BackupMetadata]:
        """Get last full backup metadata"""
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM backups 
            WHERE status = 'completed' AND backup_type = 'full'
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
        row = cursor.fetchone()
        
        conn.close()
        
        if not row:
            return None
        
        return BackupMetadata(
            backup_id=row[0],
            backup_type=BackupType(row[1]),
            timestamp=datetime.fromisoformat(row[2]),
            file_count=row[3],
            total_size=row[4],
            checksum=row[5],
            status=BackupStatus(row[6]),
            error_message=row[7],
            files_included=json.loads(row[8]) if row[8] else None
        )
    
    def _update_backup_status(self, backup_id: str, status: BackupStatus, error_message: str = None):
        """Update backup status in database"""
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE backups 
            SET status = ?, error_message = ? 
            WHERE backup_id = ?
        """, (status.value, error_message, backup_id))
        
        conn.commit()
        conn.close()
    
    def _record_recovery_operation(self, recovery_id: str, backup_id: str, 
                                 recovery_type: str, target_directory: str, 
                                 files_recovered: int, error_message: str = None):
        """Record recovery operation in database"""
        conn = sqlite3.connect(self.metadata_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO recovery_operations 
            (recovery_id, backup_id, recovery_type, target_directory, 
             timestamp, status, files_recovered, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            recovery_id,
            backup_id,
            recovery_type,
            target_directory,
            datetime.now().isoformat(),
            "completed" if not error_message else "failed",
            files_recovered,
            error_message
        ))
        
        conn.commit()
        conn.close()
    
    def _upload_to_cloud(self, backup_path: Path, backup_id: str):
        """Upload backup to cloud storage"""
        if not self.cloud_client:
            return
        
        try:
            if self.config.cloud_provider == "aws":
                bucket_name = os.environ.get('AWS_BACKUP_BUCKET', 'code-practice-backups')
                self.cloud_client.upload_file(
                    str(backup_path), 
                    bucket_name, 
                    f"backups/{backup_id}.tar.gz"
                )
                self.logger.info(f"Backup uploaded to AWS S3: {backup_id}")
        except Exception as e:
            self.logger.error(f"Failed to upload backup to cloud: {e}")
    
    def _download_from_cloud(self, backup_id: str) -> Path:
        """Download backup from cloud storage"""
        if not self.cloud_client:
            raise Exception("Cloud client not available")
        
        backup_path = self.backup_dir / f"{backup_id}.tar.gz"
        
        try:
            if self.config.cloud_provider == "aws":
                bucket_name = os.environ.get('AWS_BACKUP_BUCKET', 'code-practice-backups')
                self.cloud_client.download_file(
                    bucket_name, 
                    f"backups/{backup_id}.tar.gz",
                    str(backup_path)
                )
                self.logger.info(f"Backup downloaded from AWS S3: {backup_id}")
                return backup_path
        except Exception as e:
            self.logger.error(f"Failed to download backup from cloud: {e}")
            raise
    
    def _delete_from_cloud(self, backup_id: str):
        """Delete backup from cloud storage"""
        if not self.cloud_client:
            return
        
        try:
            if self.config.cloud_provider == "aws":
                bucket_name = os.environ.get('AWS_BACKUP_BUCKET', 'code-practice-backups')
                self.cloud_client.delete_object(
                    Bucket=bucket_name, 
                    Key=f"backups/{backup_id}.tar.gz"
                )
                self.logger.info(f"Backup deleted from AWS S3: {backup_id}")
        except Exception as e:
            self.logger.error(f"Failed to delete backup from cloud: {e}")
    
    def _scheduled_backup(self, source_paths: List[str], backup_type: BackupType):
        """Perform scheduled backup"""
        try:
            backup_id = self.create_backup(source_paths, backup_type)
            self.logger.info(f"Scheduled backup completed: {backup_id}")
        except Exception as e:
            self.logger.error(f"Scheduled backup failed: {e}")
    
    def _run_scheduler(self):
        """Run the backup scheduler"""
        while self.scheduler_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


class FileMonitor:
    """Monitor file changes for incremental backups"""
    
    def __init__(self):
        self.watched_files = {}
        self.changes = []
    
    def add_watch(self, file_path: str):
        """Add file to watch list"""
        try:
            stat = os.stat(file_path)
            self.watched_files[file_path] = {
                'mtime': stat.st_mtime,
                'size': stat.st_size,
                'checksum': self._calculate_file_checksum(file_path)
            }
        except OSError:
            pass
    
    def check_changes(self) -> List[str]:
        """Check for file changes"""
        changed_files = []
        
        for file_path, old_info in self.watched_files.items():
            try:
                stat = os.stat(file_path)
                if (stat.st_mtime != old_info['mtime'] or 
                    stat.st_size != old_info['size']):
                    
                    new_checksum = self._calculate_file_checksum(file_path)
                    if new_checksum != old_info['checksum']:
                        changed_files.append(file_path)
                        
                        # Update watched file info
                        self.watched_files[file_path] = {
                            'mtime': stat.st_mtime,
                            'size': stat.st_size,
                            'checksum': new_checksum
                        }
            except OSError:
                # File might have been deleted
                changed_files.append(file_path)
        
        return changed_files
    
    def _calculate_file_checksum(self, file_path: str) -> str:
        """Calculate file checksum"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return ""


def main():
    """Example usage of backup and recovery system"""
    # Configuration
    config = BackupConfig(
        backup_directory="./backups",
        retention_days=30,
        compression=True,
        encryption=False,
        cloud_storage=False,
        backup_schedule="daily",
        verify_integrity=True
    )
    
    # Initialize backup system
    backup_system = BackupRecoverySystem(config)
    
    # Create a full backup
    print("🔄 Creating full backup...")
    backup_id = backup_system.create_backup(
        source_paths=["./practice_data", "./problem-solving"],
        backup_type=BackupType.FULL
    )
    print(f"✅ Backup created: {backup_id}")
    
    # List backups
    print("\n📋 Available backups:")
    backups = backup_system.list_backups()
    for backup in backups:
        print(f"  {backup.backup_id} - {backup.backup_type.value} - {backup.timestamp}")
    
    # Get statistics
    print("\n📊 Backup statistics:")
    stats = backup_system.get_backup_statistics()
    print(f"  Total backups: {stats['total_backups']}")
    print(f"  Success rate: {stats['success_rate']:.1f}%")
    print(f"  Total size: {stats['total_size_mb']:.1f} MB")
    
    # Verify backups
    print("\n🔍 Verifying backups...")
    verification_results = backup_system.verify_all_backups()
    for backup_id, is_valid in verification_results.items():
        status = "✅ Valid" if is_valid else "❌ Invalid"
        print(f"  {backup_id}: {status}")
    
    print("\n🎉 Backup and recovery system demonstration completed!")


if __name__ == "__main__":
    main() 