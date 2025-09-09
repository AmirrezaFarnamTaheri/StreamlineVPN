#!/usr/bin/env python3
"""
backup.py
=========

Backup and restore script for StreamlineVPN.
"""

import os
import shutil
import json
import yaml
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import tarfile
import gzip

from streamline_vpn.utils.logging import get_logger

logger = get_logger(__name__)


class StreamlineVPNBackup:
    """Backup and restore functionality for StreamlineVPN."""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Important directories to backup
        self.directories = [
            "config",
            "data", 
            "logs",
            "output",
            "cache"
        ]
        
        # Important files to backup
        self.files = [
            "env.example",
            "requirements.txt",
            "pyproject.toml",
            "docker-compose.yml",
            "Dockerfile"
        ]
    
    def create_backup(self, name: str = None) -> str:
        """Create a backup of the system."""
        if not name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"streamline_backup_{timestamp}"
        
        backup_path = self.backup_dir / f"{name}.tar.gz"
        
        logger.info(f"Creating backup: {backup_path}")
        
        with tarfile.open(backup_path, "w:gz") as tar:
            # Add directories
            for dir_name in self.directories:
                dir_path = Path(dir_name)
                if dir_path.exists():
                    tar.add(dir_name, arcname=dir_name)
                    logger.info(f"Added directory: {dir_name}")
            
            # Add files
            for file_name in self.files:
                file_path = Path(file_name)
                if file_path.exists():
                    tar.add(file_name, arcname=file_name)
                    logger.info(f"Added file: {file_name}")
            
            # Add source code
            if Path("src").exists():
                tar.add("src", arcname="src")
                logger.info("Added source code")
            
            # Add tests
            if Path("tests").exists():
                tar.add("tests", arcname="tests")
                logger.info("Added tests")
            
            # Add documentation
            if Path("docs").exists():
                tar.add("docs", arcname="docs")
                logger.info("Added documentation")
        
        # Create backup metadata
        metadata = {
            "name": name,
            "created": datetime.now().isoformat(),
            "version": self.get_version(),
            "size": backup_path.stat().st_size,
            "directories": self.directories,
            "files": self.files
        }
        
        metadata_path = self.backup_dir / f"{name}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Backup created successfully: {backup_path}")
        logger.info(f"Backup size: {self.format_size(backup_path.stat().st_size)}")
        
        return str(backup_path)
    
    def restore_backup(self, backup_path: str, target_dir: str = ".") -> bool:
        """Restore from a backup."""
        backup_file = Path(backup_path)
        
        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        logger.info(f"Restoring from backup: {backup_path}")
        
        try:
            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(target_dir)
            
            logger.info("Backup restored successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups."""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.tar.gz"):
            metadata_file = backup_file.with_suffix("").with_suffix("_metadata.json")
            
            metadata = {}
            if metadata_file.exists():
                try:
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                except:
                    pass
            
            backup_info = {
                "file": str(backup_file),
                "name": metadata.get("name", backup_file.stem),
                "created": metadata.get("created", "Unknown"),
                "size": self.format_size(backup_file.stat().st_size),
                "version": metadata.get("version", "Unknown")
            }
            
            backups.append(backup_info)
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x["created"], reverse=True)
        
        return backups
    
    def cleanup_old_backups(self, keep_days: int = 30):
        """Clean up old backups."""
        logger.info(f"Cleaning up backups older than {keep_days} days")
        
        cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        removed_count = 0
        
        for backup_file in self.backup_dir.glob("*.tar.gz"):
            if backup_file.stat().st_mtime < cutoff_date:
                # Remove backup and metadata
                backup_file.unlink()
                
                metadata_file = backup_file.with_suffix("").with_suffix("_metadata.json")
                if metadata_file.exists():
                    metadata_file.unlink()
                
                removed_count += 1
                logger.info(f"Removed old backup: {backup_file.name}")
        
        logger.info(f"Cleaned up {removed_count} old backups")
    
    def export_config(self, output_file: str = None) -> str:
        """Export current configuration."""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"config_export_{timestamp}.yaml"
        
        export_path = Path(output_file)
        
        # Collect all configuration
        config_data = {
            "export_info": {
                "created": datetime.now().isoformat(),
                "version": self.get_version()
            },
            "sources": self.load_sources_config(),
            "environment": self.load_environment_config(),
            "database": self.export_database_data()
        }
        
        with open(export_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)
        
        logger.info(f"Configuration exported to: {export_path}")
        return str(export_path)
    
    def import_config(self, config_file: str) -> bool:
        """Import configuration from file."""
        config_path = Path(config_file)
        
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_file}")
            return False
        
        try:
            with open(config_path) as f:
                config_data = yaml.safe_load(f)
            
            # Import sources
            if "sources" in config_data:
                self.save_sources_config(config_data["sources"])
            
            # Import environment
            if "environment" in config_data:
                self.save_environment_config(config_data["environment"])
            
            # Import database data
            if "database" in config_data:
                self.import_database_data(config_data["database"])
            
            logger.info("Configuration imported successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False
    
    def load_sources_config(self) -> Dict[str, Any]:
        """Load sources configuration."""
        sources_file = Path("config/sources.yaml")
        
        if sources_file.exists():
            with open(sources_file) as f:
                return yaml.safe_load(f)
        
        return {}
    
    def save_sources_config(self, config: Dict[str, Any]):
        """Save sources configuration."""
        sources_file = Path("config/sources.yaml")
        sources_file.parent.mkdir(exist_ok=True)
        
        with open(sources_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
    
    def load_environment_config(self) -> Dict[str, str]:
        """Load environment configuration."""
        env_file = Path(".env")
        
        if env_file.exists():
            env_vars = {}
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
            return env_vars
        
        return {}
    
    def save_environment_config(self, config: Dict[str, str]):
        """Save environment configuration."""
        env_file = Path(".env")
        
        with open(env_file, 'w') as f:
            for key, value in config.items():
                f.write(f"{key}={value}\n")
    
    def export_database_data(self) -> Dict[str, Any]:
        """Export database data."""
        data = {}
        
        # Export jobs database
        jobs_db = Path("data/jobs.db")
        if jobs_db.exists():
            try:
                conn = sqlite3.connect(str(jobs_db))
                cursor = conn.cursor()
                
                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                for table_name, in tables:
                    cursor.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()
                    
                    # Get column names
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    data[table_name] = {
                        "columns": columns,
                        "rows": rows
                    }
                
                conn.close()
                
            except Exception as e:
                logger.error(f"Failed to export database: {e}")
        
        return data
    
    def import_database_data(self, data: Dict[str, Any]):
        """Import database data."""
        jobs_db = Path("data/jobs.db")
        jobs_db.parent.mkdir(exist_ok=True)
        
        try:
            conn = sqlite3.connect(str(jobs_db))
            cursor = conn.cursor()
            
            for table_name, table_data in data.items():
                # Create table if not exists
                columns = table_data["columns"]
                create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
                cursor.execute(create_sql)
                
                # Insert data
                for row in table_data["rows"]:
                    placeholders = ', '.join(['?' for _ in columns])
                    insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
                    cursor.execute(insert_sql, row)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to import database: {e}")
    
    def get_version(self) -> str:
        """Get current version."""
        try:
            with open("pyproject.toml") as f:
                for line in f:
                    if line.startswith("version ="):
                        return line.split("=")[1].strip().strip('"')
        except:
            pass
        
        return "Unknown"
    
    def format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"


def main():
    """Main backup function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='StreamlineVPN Backup Tool')
    parser.add_argument('action', choices=['create', 'restore', 'list', 'cleanup', 'export', 'import'],
                       help='Action to perform')
    parser.add_argument('--name', help='Backup name')
    parser.add_argument('--file', help='File path for restore/import')
    parser.add_argument('--keep-days', type=int, default=30, help='Days to keep backups')
    
    args = parser.parse_args()
    
    backup = StreamlineVPNBackup()
    
    if args.action == 'create':
        backup_path = backup.create_backup(args.name)
        print(f"Backup created: {backup_path}")
    
    elif args.action == 'restore':
        if not args.file:
            print("Error: --file required for restore")
            return
        
        if backup.restore_backup(args.file):
            print("Backup restored successfully")
        else:
            print("Failed to restore backup")
    
    elif args.action == 'list':
        backups = backup.list_backups()
        if backups:
            print("\nAvailable Backups:")
            print("-" * 80)
            for b in backups:
                print(f"{b['name']:<30} {b['created']:<20} {b['size']:<10} {b['version']}")
        else:
            print("No backups found")
    
    elif args.action == 'cleanup':
        backup.cleanup_old_backups(args.keep_days)
        print(f"Cleaned up backups older than {args.keep_days} days")
    
    elif args.action == 'export':
        export_path = backup.export_config()
        print(f"Configuration exported to: {export_path}")
    
    elif args.action == 'import':
        if not args.file:
            print("Error: --file required for import")
            return
        
        if backup.import_config(args.file):
            print("Configuration imported successfully")
        else:
            print("Failed to import configuration")


if __name__ == '__main__':
    main()
