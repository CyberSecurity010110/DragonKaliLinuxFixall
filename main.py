# main.py

import logging
import tkinter as tk
from modules import check_network
from tkinter import ttk, simpledialog, messagebox
from modules.update_system import update_system
from modules.check_network import check_network
from modules.cleanup_system import cleanup_system
from modules.check_disk import check_disk_usage
from modules.check_services import check_service_status
from modules.check_firewall import check_firewall_status
from modules.system_info import system_info
from modules.log_cleanup import cleanup_logs
from modules.user_management import add_user, remove_user
from modules.backup_restore import backup_directory, restore_directory
from modules.access_logs import access_log
from modules.customize_options import change_hostname, setup_static_ip, configure_ssh

def run_check_network():
    """Run comprehensive network check and repair."""
    success, message = check_network.check_network()
    if success:
        logging.info("Network is functioning correctly.")
    else:
        logging.error(f"Network issues detected: {message}")

def run_task_with_progress(task, *args):
    progress_bar.start()
    try:
        task(lambda progress: progress_bar.step(progress), *args)
    finally:
        progress_bar.stop()

def run_update_system():
    run_task_with_progress(update_system)

def run_check_network():
    run_task_with_progress(check_network)

def run_cleanup_system():
    run_task_with_progress(cleanup_system)

def run_check_disk_usage():
    run_task_with_progress(check_disk_usage)

def run_check_service_status():
    service_name = simpledialog.askstring("Input", "Enter the service name:")
    if service_name:
        run_task_with_progress(check_service_status, service_name)

def run_check_firewall_status():
    run_task_with_progress(check_firewall_status)

def run_system_info():
    run_task_with_progress(system_info)

def run_cleanup_logs():
    run_task_with_progress(cleanup_logs)

def run_add_user():
    username = simpledialog.askstring("Input", "Enter the username to add:")
    if username:
        run_task_with_progress(add_user, username)

def run_remove_user():
    username = simpledialog.askstring("Input", "Enter the username to remove:")
    if username:
        run_task_with_progress(remove_user, username)

def run_backup_directory():
    source = simpledialog.askstring("Input", "Enter the source directory:")
    destination = simpledialog.askstring("Input", "Enter the destination directory:")
    if source and destination:
        run_task_with_progress(backup_directory, source, destination)

def run_restore_directory():
    source = simpledialog.askstring("Input", "Enter the source directory:")
    destination = simpledialog.askstring("Input", "Enter the destination directory:")
    if source and destination:
        run_task_with_progress(restore_directory, source, destination)

def run_access_log():
    log_path = simpledialog.askstring("Input", "Enter the log file path:")
    if log_path:
        run_task_with_progress(access_log, log_path)

def run_change_hostname():
    new_hostname = simpledialog.askstring("Input", "Enter the new hostname:")
    if new_hostname:
        run_task_with_progress(change_hostname, new_hostname)

def run_setup_static_ip():
    interface = simpledialog.askstring("Input", "Enter the network interface (e.g., eth0):")
    ip_address = simpledialog.askstring("Input", "Enter the static IP address:")
    netmask = simpledialog.askstring("Input", "Enter the netmask:")
    gateway = simpledialog.askstring("Input", "Enter the gateway:")
    if interface and ip_address and netmask and gateway:
        run_task_with_progress(setup_static_ip, interface, ip_address, netmask, gateway)

def run_configure_ssh():
    enable = messagebox.askyesno("SSH Configuration", "Do you want to enable SSH?")
    run_task_with_progress(configure_ssh, enable)

def main():
    global progress_bar

    root = tk.Tk()
    root.title("Kali Fix-All Tool")

    tk.Button(root, text="Update System", command=run_update_system).pack(pady=5)
    tk.Button(root, text="Check Network", command=run_check_network).pack(pady=5)
    tk.Button(root, text="Cleanup System", command=run_cleanup_system).pack(pady=5)
    tk.Button(root, text="Check Disk Usage", command=run_check_disk_usage).pack(pady=5)
    tk.Button(root, text="Check Service Status", command=run_check_service_status).pack(pady=5)
    tk.Button(root, text="Check Firewall Status", command=run_check_firewall_status).pack(pady=5)
    tk.Button(root, text="System Information", command=run_system_info).pack(pady=5)
    tk.Button(root, text="Cleanup Logs", command=run_cleanup_logs).pack(pady=5)
    tk.Button(root, text="Add User", command=run_add_user).pack(pady=5)
    tk.Button(root, text="Remove User", command=run_remove_user).pack(pady=5)
    tk.Button(root, text="Backup Directory", command=run_backup_directory).pack(pady=5)
    tk.Button(root, text="Restore Directory", command=run_restore_directory).pack(pady=5)
    tk.Button(root, text="Access Log", command=run_access_log).pack(pady=5)
    tk.Button(root, text="Change Hostname", command=run_change_hostname).pack(pady=5)
    tk.Button(root, text="Setup Static IP", command=run_setup_static_ip).pack(pady=5)
    tk.Button(root, text="Configure SSH", command=run_configure_ssh).pack(pady=5)
    tk.Button(root, text="Exit", command=root.quit).pack(pady=5)

    progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
    progress_bar.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
