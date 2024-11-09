# modules/log_cleanup.py

import os

def cleanup_logs(progress_callback):
    try:
        print("Cleaning up log files...")
        progress_callback(50)
        os.system("sudo journalctl --vacuum-time=2weeks")
        progress_callback(100)
        print("Log cleanup complete.")
    except Exception as e:
        print(f"Error cleaning up logs: {e}")
