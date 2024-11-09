# modules/check_network.py

import os

def check_network(progress_callback):
    try:
        print("Checking network connection...")
        progress_callback(50)
        response = os.system("ping -c 4 google.com")
        if response == 0:
            print("Network is up.")
        else:
            print("Network is down. Restarting network service...")
            os.system("sudo systemctl restart NetworkManager")
        progress_callback(100)
    except Exception as e:
        print(f"Error checking network: {e}")
