import logging
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from modules import check_network, check_services, check_disk, log_cleanup, user_management, system_info, access_logs, check_firewall, check_network, customize_options, backup_restore
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
import subprocess
import os

logging.basicConfig(level=logging.DEBUG)

def run_command(command):
    """Run a shell command and return the output."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    logging.debug(f"Command: {command}")
    logging.debug(f"Return code: {result.returncode}")
    logging.debug(f"Output: {result.stdout.strip()}")
    logging.debug(f"Error: {result.stderr.strip()}")
    return result.returncode, result.stdout.strip(), result.stderr.strip()

def run_check_network():
    """Run comprehensive network check and repair."""
    success, message = check_network.check_network()
    if success:
        logging.info("Network is functioning correctly.")
    else:
        logging.error(f"Network issues detected: {message}")

def fix_permissions(path, user, group, permissions):
    """Fix permissions and ownership for a given path."""
    try:
        subprocess.run(['chown', f'{user}:{group}', path], check=True)
        subprocess.run(['chmod', permissions, path], check=True)
        logging.info(f"Fixed permissions for {path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to fix permissions for {path}: {e}")

def run_fix_permissions():
    """Fix file permissions and ownership."""
    logging.info("Fixing file permissions and ownership...")
    paths = {
        '/path/to/file1': ('root', 'root', '644'),
        '/path/to/file2': ('user', 'group', '755'),
        # Add more paths and their expected permissions
    }
    for path, (user, group, permissions) in paths.items():
        fix_permissions(path, user, group, permissions)

def scan_and_fix_corruptions():
    """Scan for file corruptions and attempt to fix them."""
    try:
        subprocess.run(['fsck', '-A', '-y'], check=True)
        logging.info("File system check completed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to complete file system check: {e}")

def run_scan_file_corruptions():
    """Scan for file corruptions and attempt to fix them."""
    logging.info("Scanning for file corruptions...")
    scan_and_fix_corruptions()

def fix_package_corruptions():
    """Fix package corruptions."""
    try:
        subprocess.run(['dpkg', '--configure', '-a'], check=True)
        subprocess.run(['apt-get', 'install', '-f'], check=True)
        logging.info("Package corruption fix completed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to fix package corruptions: {e}")

def run_fix_package_corruptions():
    """Fix package corruptions."""
    logging.info("Fixing package corruptions...")
    fix_package_corruptions()

def run_smart_configuration():
    """Smart configuration for unconfigured packages."""
    logging.info("Performing smart configuration...")
    try:
        subprocess.run(['dpkg-reconfigure', '-a'], check=True)
        logging.info("Smart configuration completed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to complete smart configuration: {e}")

def run_dependency_repair():
    """Repair dependency problems."""
    logging.info("Repairing dependency problems...")
    try:
        subprocess.run(['apt-get', 'check'], check=True)
        subprocess.run(['apt-get', 'install', '-f'], check=True)
        logging.info("Dependency repair completed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to repair dependencies: {e}")

def run_drive_management():
    """Manage drives (scan, mount, unmount)."""
    logging.info("Managing drives...")
    # Example: Scan for drives
    ret_code, output, error = run_command("lsblk")
    if ret_code == 0:
        logging.info(f"Drives:\n{output}")
    else:
        logging.error(f"Failed to list drives: {error}")

    # Example: Mount a drive
    # ret_code, output, error = run_command("mount /dev/sdX1 /mnt")
    # if ret_code == 0:
    #     logging.info("Drive mounted successfully.")
    # else:
    #     logging.error(f"Failed to mount drive: {error}")

    # Example: Unmount a drive
    # ret_code, output, error = run_command("umount /mnt")
    # if ret_code == 0:
    #     logging.info("Drive unmounted successfully.")
    # else:
    #     logging.error(f"Failed to unmount drive: {error}")

def run_tweaks():
    """Apply system tweaks."""
    logging.info("Applying system tweaks...")
    # Example: Remove the need for sudo password
    try:
        with open('/etc/sudoers.d/nopasswd', 'w') as f:
            f.write('%sudo ALL=(ALL) NOPASSWD:ALL\n')
        logging.info("Removed the need for sudo password.")
    except Exception as e:
        logging.error(f"Failed to remove the need for sudo password: {e}")

    # Example: Enable autologin
    try:
        with open('/etc/lightdm/lightdm.conf', 'a') as f:
            f.write('[Seat:*]\nautologin-user=your_username\n')
        logging.info("Enabled autologin.")
    except Exception as e:
        logging.error(f"Failed to enable autologin: {e}")

    # Example: Adjust resolution
    try:
        ret_code, output, error = run_command("xrandr --output HDMI-1 --mode 1920x1080")
        if ret_code == 0:
            logging.info("Resolution adjusted successfully.")
        else:
            logging.error(f"Failed to adjust resolution: {error}")
    except Exception as e:
        logging.error(f"Failed to adjust resolution: {e}")

def run_user_repair():
    """Repair user configurations and settings."""
    logging.info("Repairing user configurations and settings...")
    # Example: Fix user permissions
    try:
        subprocess.run(['chown', '-R', 'your_username:your_username', '/home/your_username'], check=True)
        logging.info("User permissions fixed.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to fix user permissions: {e}")

    # Example: Repair user settings
    # Implement logic to repair user settings
    # ...

def run_task_with_progress(task, *args):
    progress_bar.start()
    try:
        task(lambda progress: progress_bar.step(progress), *args)
    finally:
        progress_bar.stop()

def run_update_system():
    run_task_with_progress(update_system)

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
