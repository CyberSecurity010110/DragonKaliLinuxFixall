# Part 17: Flash Drive Format Module
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
from typing import Dict, List, Tuple, Set
import json
import pyudev
import dbus
import time
from pathlib import Path

class FlashDriveModule:
    def __init__(self, parent_notebook):
        # Create Flash Drive tab
        self.flash_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.flash_frame, text='Flash Drive Manager')
        
        # Initialize variables
        self.detected_drives = {}  # Dictionary to store drive information
        self.recommended_formats = {
            'Linux Compatible': 'ext4',
            'Universal': 'exFAT',
            'Windows Compatible': 'NTFS',
            'Small Drive (<4GB)': 'FAT32'
        }
        
        # Create interface
        self.create_interface()
        
        # Initialize udev monitor
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by('block')
        self.observer = pyudev.MonitorObserver(self.monitor, self.device_event)
        self.observer.start()
        
        # Initial scan
        self.scan_drives()

    def create_interface(self):
        # Main container
        main_container = ttk.Frame(self.flash_frame)
        main_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Left panel - Drive list
        left_panel = ttk.Frame(main_container)
        left_panel.pack(side='left', fill='both', expand=True, padx=5)
        
        # Drive list
        list_frame = ttk.LabelFrame(left_panel, text="Detected Flash Drives")
        list_frame.pack(fill='both', expand=True)
        
        # Create treeview for drives
        self.drives_tree = ttk.Treeview(list_frame,
                                      columns=('device', 'size', 'format', 'mount'),
                                      show='headings')
        self.drives_tree.heading('device', text='Device')
        self.drives_tree.heading('size', text='Size')
        self.drives_tree.heading('format', text='Format')
        self.drives_tree.heading('mount', text='Mount Point')
        
        # Scrollbars
        y_scroll = ttk.Scrollbar(list_frame, orient='vertical',
                                command=self.drives_tree.yview)
        x_scroll = ttk.Scrollbar(list_frame, orient='horizontal',
                                command=self.drives_tree.xview)
        
        self.drives_tree.configure(yscrollcommand=y_scroll.set,
                                 xscrollcommand=x_scroll.set)
        
        # Pack drive list
        self.drives_tree.pack(side='left', fill='both', expand=True)
        y_scroll.pack(side='right', fill='y')
        x_scroll.pack(side='bottom', fill='x')
        
        # Right panel - Controls and details
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side='right', fill='both', padx=5)
        
        # Format options
        format_frame = ttk.LabelFrame(right_panel, text="Format Options")
        format_frame.pack(fill='x', pady=5)
        
        # Format selection
        ttk.Label(format_frame, text="Select Format:").pack(fill='x', padx=5, pady=2)
        
        self.format_var = tk.StringVar()
        self.format_combo = ttk.Combobox(format_frame, textvariable=self.format_var)
        self.format_combo['values'] = list(self.recommended_formats.values())
        self.format_combo.set('ext4')
        self.format_combo.pack(fill='x', padx=5, pady=2)
        
        # Label entry
        ttk.Label(format_frame, text="Drive Label:").pack(fill='x', padx=5, pady=2)
        
        self.label_var = tk.StringVar()
        self.label_entry = ttk.Entry(format_frame, textvariable=self.label_var)
        self.label_entry.pack(fill='x', padx=5, pady=2)
        
        # Control buttons
        control_frame = ttk.LabelFrame(right_panel, text="Drive Controls")
        control_frame.pack(fill='x', pady=5)
        
        ttk.Button(control_frame, text="Scan Drives",
                  command=self.scan_drives).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(control_frame, text="Format Drive",
                  command=self.format_drive).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(control_frame, text="Mount Drive",
                  command=self.mount_drive).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(control_frame, text="Unmount Drive",
                  command=self.unmount_drive).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(control_frame, text="Check Drive Health",
                  command=self.check_drive_health).pack(fill='x', padx=5, pady=2)
        
        # Quick actions
        action_frame = ttk.LabelFrame(right_panel, text="Quick Actions")
        action_frame.pack(fill='x', pady=5)
        
        ttk.Button(action_frame, text="Fix Drive Errors",
                  command=self.fix_drive_errors).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(action_frame, text="Secure Erase",
                  command=self.secure_erase).pack(fill='x', padx=5, pady=2)
        
        # Details area
        details_frame = ttk.LabelFrame(right_panel, text="Details")
        details_frame.pack(fill='both', expand=True, pady=5)
        
        self.details_text = scrolledtext.ScrolledText(details_frame, height=10)
        self.details_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Bind selection event
        self.drives_tree.bind('<<TreeviewSelect>>', self.show_drive_details)

    def run_command(self, command: str, shell: bool = False) -> Tuple[str, str, int]:
        """Run command and return output, error, and return code"""
        try:
            if shell:
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True)
            else:
                process = subprocess.Popen(command.split(), stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, text=True)
            output, error = process.communicate()
            return output, error, process.returncode
        except Exception as e:
            return "", str(e), 1

    def is_flash_drive(self, device) -> bool:
        """Check if the device is a flash drive"""
        try:
            # Check if device is removable
            if not device.get('ID_BUS') == 'usb':
                return False
            
            # Check if it's a block device
            if device.get('DEVTYPE') != 'disk':
                return False
            
            # Check if it's not a USB hub or other USB device
            if device.get('ID_USB_DRIVER') in ['usb-storage', 'uas']:
                return True
            
            return False
            
        except Exception:
            return False

    def get_drive_info(self, device_path: str) -> Dict:
        """Get detailed information about a drive"""
        info = {}
        try:
            # Get size
            output, _, _ = self.run_command(f"lsblk -b {device_path}")
            for line in output.splitlines():
                if device_path.split('/')[-1] in line:
                    size_bytes = int(line.split()[3])
                    info['size'] = self.format_size(size_bytes)
            
            # Get format
            output, _, _ = self.run_command(f"blkid {device_path}")
            if output:
                if 'TYPE=' in output:
                    info['format'] = output.split('TYPE="')[1].split('"')[0]
                else:
                    info['format'] = 'Unknown'
            else:
                info['format'] = 'Unformatted'
            
            # Get mount point
            output, _, _ = self.run_command(f"lsblk -o MOUNTPOINT {device_path}")
            mount_point = None
            for line in output.splitlines():
                if line.strip() and not line.strip() == 'MOUNTPOINT':
                    mount_point = line.strip()
            info['mount'] = mount_point if mount_point else 'Not Mounted'
            
            return info
            
        except Exception as e:
            self.update_details(f"Error getting drive info: {str(e)}\n")
            return {'size': 'Unknown', 'format': 'Unknown', 'mount': 'Unknown'}

    def format_size(self, size_bytes: int) -> str:
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"

    def scan_drives(self):
        """Scan for connected flash drives"""
        try:
            self.drives_tree.delete(*self.drives_tree.get_children())
            self.detected_drives.clear()
            
            for device in self.context.list_devices(subsystem='block'):
                if self.is_flash_drive(device):
                    device_path = device.device_node
                    info = self.get_drive_info(device_path)
                    
                    self.detected_drives[device_path] = info
                    self.drives_tree.insert('', 'end',
                                          values=(device_path, info['size'],
                                                 info['format'], info['mount']))
            
            self.update_details("Drive scan completed.\n")
            
        except Exception as e:
            self.update_details(f"Error scanning drives: {str(e)}\n")
            messagebox.showerror("Error", f"Failed to scan drives: {str(e)}")

    def device_event(self, action, device):
        """Handle device plug/unplug events"""
        if self.is_flash_drive(device):
            if action == 'add':
                self.update_details(f"Flash drive connected: {device.device_node}\n")
            elif action == 'remove':
                self.update_details(f"Flash drive removed: {device.device_node}\n")
            
            # Rescan drives
            self.scan_drives()

    def format_drive(self):
        """Format the selected drive"""
        selection = self.drives_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "No drive selected")
            return
        
        device_path = self.drives_tree.item(selection[0])['values'][0]
        format_type = self.format_var.get()
        label = self.label_var.get()
        
        if messagebox.askyesno("Warning",
                              f"This will ERASE ALL DATA on {device_path}!\n"
                              f"Are you sure you want to format to {format_type}?"):
            try:
                # Unmount if mounted
                if self.detected_drives[device_path]['mount'] != 'Not Mounted':
                    self.unmount_drive()
                
                self.update_details(f"Formatting {device_path} as {format_type}...\n")
                
                # Format based on selected type
                if format_type == 'ext4':
                    cmd = f"sudo mkfs.ext4"
                    if label:
                        cmd += f" -L {label}"
                    cmd += f" {device_path}"
                elif format_type == 'exFAT':
                    cmd = f"sudo mkfs.exfat"
                    if label:
                        cmd += f" -n {label}"
                    cmd += f" {device_path}"
                elif format_type == 'NTFS':
                    cmd = f"sudo mkfs.ntfs -f"
                    if label:
                        cmd += f" -L {label}"
                    cmd += f" {device_path}"
                elif format_type == 'FAT32':
                    cmd = f"sudo mkfs.vfat"
                    if label:
                        cmd += f" -n {label}"
                    cmd += f" {device_path}"
                
                output, error, code = self.run_command(cmd)
                
                if code == 0:
                    self.update_details("Format completed successfully.\n")
                    self.scan_drives()
                else:
                    raise Exception(error)
                
            except Exception as e:
                self.update_details(f"Error formatting drive: {str(e)}\n")
                messagebox.showerror("Error", f"Format failed: {str(e)}")

    def mount_drive(self):
        """Mount the selected drive"""
        selection = self.drives_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "No drive selected")
            return
        
        device_path = self.drives_tree.item(selection[0])['values'][0]
        
        try:
            if self.detected_drives[device_path]['mount'] != 'Not Mounted':
                messagebox.showinfo("Info", "Drive is already mounted")
                return
            
            # Create mount point
            mount_point = f"/media/{os.getenv('USER')}/{Path(device_path).name}"
            os.makedirs(mount_point, exist_ok=True)
            
            # Mount drive
            cmd = f"sudo mount {device_path} {mount_point}"
            output, error, code = self.run_command(cmd)
            
            if code == 0:
                self.update_details(f"Drive mounted at {mount_point}\n")
                self.scan_drives()
            else:
                raise Exception(error)
            
        except Exception as e:
            self.update_details(f"Error mounting drive: {str(e)}\n")
            messagebox.showerror("Error", f"Mount failed: {str(e)}")

    def unmount_drive(self):
        """Unmount the selected drive"""
        selection = self.drives_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "No drive selected")
            return
        
        device_path = self.drives_tree.item(selection[0])['values'][0]
        
        try:
            if self.detected_drives[device_path]['mount'] == 'Not Mounted':
                messagebox.showinfo("Info", "Drive is not mounted")
                return
            
            # Unmount drive
            cmd = f"sudo umount {device_path}"
            output, error, code = self.run_command(cmd)
            
            if code == 0:
                self.update_details("Drive unmounted successfully.\n")
                self.scan_drives()
            else:
                raise Exception(error)
            
        except Exception as e:
            self.update_details(f"Error unmounting drive: {str(e)}\n")
            messagebox.showerror("Error", f"Unmount failed: {str(e)}")

    def check_drive_health(self):
        """Check health status of selected drive"""
        selection = self.drives_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "No drive selected")
            return
        
        device_path = self.drives_tree.item(selection[0])['values'][0]
        
        try:
            self.update_details(f"Checking health of {device_path}...\n")
            
            # Get SMART data if available
            output, error, code = self.run_command(f"sudo smartctl -a {device_path}")
            if code == 0 and "SMART support is: Available" in output:
                self.update_details("SMART Data:\n" + output + "\n")
                
                # Check for warnings
                if "SMART overall-health self-assessment test result: PASSED" in output:
                    self.update_details("Drive health status: GOOD\n")
                else:
                    self.update_details("Drive health status: WARNING - Issues detected\n")
            else:
                # Fallback to basic checks if SMART not available
                self.update_details("SMART data not available. Performing basic checks...\n")
                
                # Check for bad blocks
                output, error, code = self.run_command(f"sudo badblocks -n {device_path}")
                if code == 0 and not output.strip():
                    self.update_details("No bad blocks detected.\n")
                else:
                    self.update_details(f"Warning: Bad blocks found:\n{output}\n")
                
                # Check filesystem
                if self.detected_drives[device_path]['format'] in ['ext2', 'ext3', 'ext4']:
                    output, error, code = self.run_command(f"sudo e2fsck -n {device_path}")
                    if code == 0:
                        self.update_details("Filesystem check passed.\n")
                    else:
                        self.update_details(f"Filesystem issues detected:\n{error}\n")
            
        except Exception as e:
            self.update_details(f"Error checking drive health: {str(e)}\n")
            messagebox.showerror("Error", f"Health check failed: {str(e)}")

    def fix_drive_errors(self):
        """Attempt to fix common drive errors"""
        selection = self.drives_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "No drive selected")
            return
        
        device_path = self.drives_tree.item(selection[0])['values'][0]
        
        if messagebox.askyesno("Confirm",
                              f"Attempt to fix errors on {device_path}?"):
            try:
                # Unmount if mounted
                if self.detected_drives[device_path]['mount'] != 'Not Mounted':
                    self.unmount_drive()
                
                self.update_details(f"Attempting to fix errors on {device_path}...\n")
                
                # Check filesystem type and use appropriate tool
                fs_type = self.detected_drives[device_path]['format']
                
                if fs_type in ['ext2', 'ext3', 'ext4']:
                    cmd = f"sudo e2fsck -f -y {device_path}"
                elif fs_type == 'NTFS':
                    cmd = f"sudo ntfsfix {device_path}"
                elif fs_type in ['vfat', 'FAT32']:
                    cmd = f"sudo dosfsck -t -a {device_path}"
                elif fs_type == 'exFAT':
                    cmd = f"sudo exfatfsck -a {device_path}"
                else:
                    raise Exception(f"Unsupported filesystem: {fs_type}")
                
                output, error, code = self.run_command(cmd)
                
                if code == 0:
                    self.update_details("Filesystem repairs completed successfully.\n")
                else:
                    self.update_details(f"Warning: Issues found during repair:\n{error}\n")
                
                # Attempt to fix bad blocks
                self.update_details("Checking for bad blocks...\n")
                output, error, code = self.run_command(
                    f"sudo badblocks -w {device_path}"
                )
                
                if code == 0:
                    self.update_details("Bad blocks check/repair completed.\n")
                else:
                    self.update_details(f"Warning: Bad blocks found:\n{error}\n")
                
                self.scan_drives()
                
            except Exception as e:
                self.update_details(f"Error fixing drive: {str(e)}\n")
                messagebox.showerror("Error", f"Repair failed: {str(e)}")

    def secure_erase(self):
        """Perform secure erase of selected drive"""
        selection = self.drives_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "No drive selected")
            return
        
        device_path = self.drives_tree.item(selection[0])['values'][0]
        
        if messagebox.askyesno("Warning",
                              f"This will SECURELY ERASE ALL DATA on {device_path}!\n"
                              "This process cannot be undone!\n"
                              "Are you absolutely sure?"):
            try:
                # Unmount if mounted
                if self.detected_drives[device_path]['mount'] != 'Not Mounted':
                    self.unmount_drive()
                
                self.update_details(f"Starting secure erase of {device_path}...\n")
                
                # First pass: Write zeros
                self.update_details("Pass 1: Writing zeros...\n")
                cmd = f"sudo dd if=/dev/zero of={device_path} bs=4M status=progress"
                output, error, code = self.run_command(cmd, shell=True)
                
                # Second pass: Write random data
                self.update_details("Pass 2: Writing random data...\n")
                cmd = f"sudo dd if=/dev/urandom of={device_path} bs=4M status=progress"
                output, error, code = self.run_command(cmd, shell=True)
                
                # Final pass: Write zeros again
                self.update_details("Pass 3: Final zero pass...\n")
                cmd = f"sudo dd if=/dev/zero of={device_path} bs=4M status=progress"
                output, error, code = self.run_command(cmd, shell=True)
                
                self.update_details("Secure erase completed.\n")
                self.update_details("Recommend reformatting the drive now.\n")
                
                if messagebox.askyesno("Format Drive",
                                     "Would you like to format the drive now?"):
                    self.format_drive()
                
            except Exception as e:
                self.update_details(f"Error during secure erase: {str(e)}\n")
                messagebox.showerror("Error", f"Secure erase failed: {str(e)}")

    def show_drive_details(self, event):
        """Show detailed information about the selected drive"""
        selection = self.drives_tree.selection()
        if selection:
            device_path = self.drives_tree.item(selection[0])['values'][0]
            
            try:
                # Get detailed drive information
                output, _, _ = self.run_command(f"sudo udevadm info --query=all {device_path}")
                udev_info = output
                
                # Get partition information
                output, _, _ = self.run_command(f"sudo fdisk -l {device_path}")
                partition_info = output
                
                # Get filesystem information
                output, _, _ = self.run_command(f"sudo blkid {device_path}")
                fs_info = output
                
                details = (f"=== Drive Details: {device_path} ===\n\n"
                          f"Size: {self.detected_drives[device_path]['size']}\n"
                          f"Format: {self.detected_drives[device_path]['format']}\n"
                          f"Mount: {self.detected_drives[device_path]['mount']}\n\n"
                          f"=== Partition Information ===\n{partition_info}\n\n"
                          f"=== Filesystem Information ===\n{fs_info}\n\n"
                          f"=== Device Information ===\n{udev_info}\n")
                
                self.update_details(details)
                
            except Exception as e:
                self.update_details(f"Error getting drive details: {str(e)}")

    def update_details(self, message: str):
        """Update details text area"""
        self.details_text.delete('1.0', tk.END)
        self.details_text.insert(tk.END, message)
        self.details_text.see(tk.END)

    def __del__(self):
        """Cleanup when module is destroyed"""
        try:
            self.observer.stop()
        except:
            pass