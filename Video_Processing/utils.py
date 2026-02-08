"""
Utility script for maintenance and cleanup operations
"""

import os
import time
import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CleanupManager:
    """Manages cleanup of old files and directories"""
    
    def __init__(self, max_age_hours=24):
        self.max_age_hours = max_age_hours
        self.folders_to_clean = ['uploads', 'chunks', 'audio', 'processed']
    
    def cleanup_old_files(self):
        """Remove files older than max_age_hours"""
        cutoff_time = time.time() - (self.max_age_hours * 3600)
        total_deleted = 0
        total_freed_mb = 0
        
        for folder in self.folders_to_clean:
            if not os.path.exists(folder):
                continue
            
            logger.info(f"Cleaning {folder}...")
            
            for file_path in Path(folder).glob('**/*'):
                if file_path.is_file():
                    file_age = os.path.getmtime(file_path)
                    
                    if file_age < cutoff_time:
                        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                        try:
                            os.remove(file_path)
                            total_deleted += 1
                            total_freed_mb += file_size
                            logger.debug(f"Deleted: {file_path}")
                        except Exception as e:
                            logger.error(f"Error deleting {file_path}: {str(e)}")
        
        logger.info(f"Cleanup complete: {total_deleted} files deleted, {total_freed_mb:.2f} MB freed")
        return total_deleted, total_freed_mb
    
    def cleanup_session(self, session_id):
        """Remove all files for a specific session"""
        deleted = 0
        
        for folder in self.folders_to_clean:
            if not os.path.exists(folder):
                continue
            
            for file_path in Path(folder).glob(f'{session_id}*'):
                try:
                    os.remove(file_path)
                    deleted += 1
                    logger.info(f"Deleted session file: {file_path}")
                except Exception as e:
                    logger.error(f"Error deleting {file_path}: {str(e)}")
        
        return deleted
    
    def get_disk_usage(self):
        """Get disk usage statistics for processing folders"""
        stats = {}
        
        for folder in self.folders_to_clean:
            if not os.path.exists(folder):
                stats[folder] = {'size_mb': 0, 'file_count': 0}
                continue
            
            total_size = 0
            file_count = 0
            
            for file_path in Path(folder).glob('**/*'):
                if file_path.is_file():
                    total_size += os.path.getsize(file_path)
                    file_count += 1
            
            stats[folder] = {
                'size_mb': total_size / (1024 * 1024),
                'file_count': file_count
            }
        
        return stats


def run_cleanup(max_age_hours=24):
    """Run cleanup operation"""
    logger.info(f"Starting cleanup (max age: {max_age_hours} hours)")
    
    manager = CleanupManager(max_age_hours)
    
    # Show current disk usage
    logger.info("Current disk usage:")
    stats = manager.get_disk_usage()
    for folder, data in stats.items():
        logger.info(f"  {folder}: {data['size_mb']:.2f} MB ({data['file_count']} files)")
    
    # Run cleanup
    deleted, freed_mb = manager.cleanup_old_files()
    
    # Show new disk usage
    logger.info("\nDisk usage after cleanup:")
    stats = manager.get_disk_usage()
    for folder, data in stats.items():
        logger.info(f"  {folder}: {data['size_mb']:.2f} MB ({data['file_count']} files)")


def cleanup_all():
    """Remove all files from processing folders"""
    logger.warning("WARNING: This will delete ALL processed files!")
    confirm = input("Are you sure? (yes/no): ")
    
    if confirm.lower() != 'yes':
        logger.info("Cleanup cancelled")
        return
    
    folders = ['uploads', 'chunks', 'audio', 'processed']
    
    for folder in folders:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            os.makedirs(folder)
            logger.info(f"Cleaned {folder}/")
    
    logger.info("All files deleted")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--all':
            cleanup_all()
        elif sys.argv[1] == '--hours':
            hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            run_cleanup(hours)
        elif sys.argv[1] == '--stats':
            manager = CleanupManager()
            stats = manager.get_disk_usage()
            print("\nDisk Usage Statistics:")
            print("-" * 50)
            for folder, data in stats.items():
                print(f"{folder:15} {data['size_mb']:>10.2f} MB  {data['file_count']:>5} files")
        else:
            print("Usage:")
            print("  python utils.py --stats              # Show disk usage")
            print("  python utils.py --hours 24           # Clean files older than 24 hours")
            print("  python utils.py --all                # Delete all files")
    else:
        # Default: cleanup files older than 24 hours
        run_cleanup(24)