# modules/update_system.py

import os

def update_system(progress_callback):
    try:
        print("Updating system...")
        progress_callback(10)
        os.system("sudo apt update")
        progress_callback(50)
        os.system("sudo apt upgrade -y")
        progress_callback(100)
        print("System update complete.")
    except Exception as e:
        print(f"Error updating system: {e}")
