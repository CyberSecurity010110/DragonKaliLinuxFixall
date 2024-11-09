# modules/check_disk.py

import os

def check_disk_usage(progress_callback):
    try:
        print("Checking disk usage...")
        progress_callback(50)
        os.system("df -h")
        progress_callback(100)
        print("Disk usage check complete.")
    except Exception as e:
        print(f"Error checking disk usage: {e}")
