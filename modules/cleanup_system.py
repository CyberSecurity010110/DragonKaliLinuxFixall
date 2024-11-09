# modules/cleanup_system.py

import os

def cleanup_system(progress_callback):
    try:
        print("Cleaning up system...")
        progress_callback(30)
        os.system("sudo apt autoremove -y")
        progress_callback(60)
        os.system("sudo apt autoclean -y")
        progress_callback(100)
        print("System cleanup complete.")
    except Exception as e:
        print(f"Error cleaning up system: {e}")
