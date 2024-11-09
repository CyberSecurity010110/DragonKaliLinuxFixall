# modules/check_services.py

import os

def check_service_status(service_name, progress_callback):
    try:
        print(f"Checking status of {service_name} service...")
        progress_callback(50)
        os.system(f"systemctl status {service_name}")
        progress_callback(100)
        print(f"Status check of {service_name} service complete.")
    except Exception as e:
        print(f"Error checking service status: {e}")
