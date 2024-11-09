# modules/user_management.py

import os

def add_user(username, progress_callback):
    try:
        print(f"Adding user {username}...")
        progress_callback(50)
        os.system(f"sudo adduser {username}")
        progress_callback(100)
        print(f"User {username} added.")
    except Exception as e:
        print(f"Error adding user: {e}")

def remove_user(username, progress_callback):
    try:
        print(f"Removing user {username}...")
        progress_callback(50)
        os.system(f"sudo deluser {username}")
        progress_callback(100)
        print(f"User {username} removed.")
    except Exception as e:
        print(f"Error removing user: {e}")
