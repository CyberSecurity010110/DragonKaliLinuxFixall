# modules/system_info.py

import os

def system_info(progress_callback):
    try:
        print("Gathering system information...")
        progress_callback(30)
        os.system("uname -a")
        os.system("lsb_release -a")
        progress_callback(60)
        os.system("free -h")
        progress_callback(100)
        print("System information gathered.")
    except Exception as e:
        print(f"Error gathering system information: {e}")
