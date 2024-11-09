# modules/check_firewall.py

import os

def check_firewall_status(progress_callback):
    try:
        print("Checking firewall status...")
        progress_callback(50)
        os.system("sudo ufw status")
        progress_callback(100)
        print("Firewall status check complete.")
    except Exception as e:
        print(f"Error checking firewall status: {e}")
