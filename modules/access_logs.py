# modules/access_logs.py

import os

def access_log(log_path, progress_callback):
    try:
        print(f"Accessing log file: {log_path}")
        progress_callback(50)
        os.system(f"cat {log_path}")
        progress_callback(100)
        print(f"Log file {log_path} accessed.")
    except Exception as e:
        print(f"Error accessing log file: {e}")
