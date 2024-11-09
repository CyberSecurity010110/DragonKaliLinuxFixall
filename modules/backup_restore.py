# modules/backup_restore.py

import os
import shutil

def backup_directory(source, destination, progress_callback):
    try:
        print(f"Backing up {source} to {destination}...")
        progress_callback(50)
        shutil.copytree(source, destination)
        progress_callback(100)
        print(f"Backup of {source} to {destination} complete.")
    except Exception as e:
        print(f"Error backing up directory: {e}")

def restore_directory(source, destination, progress_callback):
    try:
        print(f"Restoring {source} to {destination}...")
        progress_callback(50)
        shutil.copytree(source, destination)
        progress_callback(100)
        print(f"Restore of {source} to {destination} complete.")
    except Exception as e:
        print(f"Error restoring directory: {e}")
