# Part 18: Device Management Module
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
from typing import Dict, List, Tuple, Set
import json
import pyudev
import dbus
import time
import re
from pathlib import Path
import requests
import shutil

class DeviceManagementModule:
    def __init__(self, parent_notebook):
        # Create Device Management tab
        self.device_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.device_frame, text='Device Management')
        
        # Initialize variables
        self.detected_devices = {}  # Dictionary to store device information
        self.problem_devices = {}   # Dictionary to store problematic devices
        self.driver_cache = {}      # Cache for driver information
        self.device_categories = [
            'Network', 'Graphics', 'Audio', 'Storage', 'USB', 'Bluetooth',
            'Input', 'Printer', 'Camera', 'Other'
        ]
        
        # Create interface
        self.create_interface()
        
        # Initialize udev monitor
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.observer = pyudev.MonitorObserver(self.monitor, self.device_event)
        self.observer.start()
        
        # Initial scan
        self.scan_devices()

    def create_interface(self):
        # Main container with paned window
        self.paned = ttk.PanedWindow(self.device_frame, orient=tk.HORIZONTAL)
        self.paned.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Left panel - Device list
        left_panel = ttk.Frame(self.paned)
        self.paned.add(left_panel, weight=1)
        
        # Category filter
        filter_frame = ttk.LabelFrame(left_panel, text="Filter by Category")
        filter_frame.pack(fill='x', padx=5, pady=5)
        
        self.category_var = tk.StringVar(value="All")
        for category in ['All'] + self.device_categories:
            ttk.Radiobutton(filter_frame, text=category,
                           variable=self.category_var,
                           value=category,
                           command=self.filter_devices).pack(anchor='w', padx=5)
        
        # Device list
        list_frame = ttk.LabelFrame(left_panel, text="Detected Devices")
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create treeview for devices
        self.devices_tree = ttk.Treeview(list_frame,
                                       columns=('device', 'status', 'driver'),
                                       show='headings')
        self.devices_tree.heading('device', text='Device')
        self.devices_tree.heading('status', text='Status')
        self.devices_tree.heading('driver', text='Driver')
        
        # Add status icons
        self.status_icons = {
            'ok': '✓',
            'warning': '⚠',
            'error': '✗',
            'unknown': '?'
        }
        
        # Scrollbars
        y_scroll = ttk.Scrollbar(list_frame, orient='vertical',
                                command=self.devices_tree.yview)
        x_scroll = ttk.Scrollbar(list_frame, orient='horizontal',
                                command=self.devices_tree.xview)
        
        self.devices_tree.configure(yscrollcommand=y_scroll.set,
                                  xscrollcommand=x_scroll.set)
        
        # Pack device list
        self.devices_tree.pack(side='left', fill='both', expand=True)
        y_scroll.pack(side='right', fill='y')
        x_scroll.pack(side='bottom', fill='x')
        
        # Right panel with notebook
        right_panel = ttk.Frame(self.paned)
        self.paned.add(right_panel, weight=1)
        
        # Create notebook for different sections
        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill='both', expand=True)
        
        # Details tab
        self.details_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.details_frame, text='Details')
        
        self.details_text = scrolledtext.ScrolledText(self.details_frame)
        self.details_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Problems tab
        self.problems_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.problems_frame, text='Problems')
        
        self.problems_text = scrolledtext.ScrolledText(self.problems_frame)
        self.problems_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Actions tab
        self.actions_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.actions_frame, text='Actions')
        
        # Action buttons
        ttk.Button(self.actions_frame, text="Scan Devices",
                  command=self.scan_devices).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(self.actions_frame, text="Fix Selected Device",
                  command=self.fix_device).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(self.actions_frame, text="Update Driver",
                  command=self.update_driver).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(self.actions_frame, text="Remove Driver",
                  command=self.remove_driver).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(self.actions_frame, text="Reset Device",
                  command=self.reset_device).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(self.actions_frame, text="Fix All Problems",
                  command=self.fix_all_problems).pack(fill='x', padx=5, pady=2)
        
        # Bind selection event
        self.devices_tree.bind('<<TreeviewSelect>>', self.show_device_details)

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

    def scan_devices(self):
        """Scan system for all devices and their status"""
        try:
            self.update_details("Scanning devices...\n")
            self.devices_tree.delete(*self.devices_tree.get_children())
            self.detected_devices.clear()
            self.problem_devices.clear()
            
            # Get PCI devices
            self.scan_pci_devices()
            
            # Get USB devices
            self.scan_usb_devices()
            
            # Get network devices
            self.scan_network_devices()
            
            # Get audio devices
            self.scan_audio_devices()
            
            # Get input devices
            self.scan_input_devices()
            
            # Check for driver issues
            self.check_driver_issues()
            
            # Update problems tab
            self.update_problems_tab()
            
            self.update_details("Device scan completed.\n")
            
        except Exception as e:
            self.update_details(f"Error scanning devices: {str(e)}\n")
            messagebox.showerror("Error", f"Failed to scan devices: {str(e)}")

    def scan_pci_devices(self):
        """Scan PCI devices"""
        try:
            output, _, _ = self.run_command("lspci -v")
            current_device = None
            
            for line in output.splitlines():
                if not line.startswith('\t'):
                    # New device
                    if current_device:
                        self.add_device_to_list(current_device)
                    current_device = {
                        'id': line.split()[0],
                        'name': ' '.join(line.split()[2:]),
                        'type': self.categorize_device(' '.join(line.split()[2:])),
                        'driver': 'Unknown',
                        'status': 'unknown',
                        'details': [line]
                    }
                elif current_device:
                    current_device['details'].append(line)
                    if 'Kernel driver in use:' in line:
                        current_device['driver'] = line.split('Kernel driver in use:')[1].strip()
                        current_device['status'] = 'ok'
                    elif 'Kernel modules:' in line:
                        current_device['modules'] = line.split('Kernel modules:')[1].strip()
            
            # Add last device
            if current_device:
                self.add_device_to_list(current_device)
                
        except Exception as e:
            self.update_details(f"Error scanning PCI devices: {str(e)}\n")

    def scan_usb_devices(self):
        """Scan USB devices"""
        try:
            output, _, _ = self.run_command("lsusb -v")
            current_device = None
            
            for line in output.splitlines():
                if line.startswith('Bus'):
                    # New device
                    if current_device:
                        self.add_device_to_list(current_device)
                    current_device = {
                        'id': line.split()[5],
                        'name': ' '.join(line.split()[6:]),
                        'type': 'USB',
                        'driver': 'Unknown',
                        'status': 'unknown',
                        'details': [line]
                    }
                elif current_device and line.strip():
                    current_device['details'].append(line)
                    if 'Driver=' in line:
                        current_device['driver'] = line.split('Driver=')[1].strip()
                        current_device['status'] = 'ok'
            
            # Add last device
            if current_device:
                self.add_device_to_list(current_device)
                
        except Exception as e:
            self.update_details(f"Error scanning USB devices: {str(e)}\n")

    def scan_network_devices(self):
        """Scan network devices"""
        try:
            output, _, _ = self.run_command("ip link show")
            
            for line in output.splitlines():
                if not line.startswith(' '):
                    device_info = {
                        'id': line.split(':')[0],
                        'name': line.split(':')[1].split('@')[0].strip(),
                        'type': 'Network',
                        'driver': 'Unknown',
                        'status': 'unknown',
                        'details': [line]
                    }
                    
                    # Get driver information
                    driver_path = f"/sys/class/net/{device_info['name']}/device/driver"
                    if os.path.exists(driver_path):
                        device_info['driver'] = os.path.basename(os.readlink(driver_path))
                        device_info['status'] = 'ok'
                    
                    self.add_device_to_list(device_info)
                    
        except Exception as e:
            self.update_details(f"Error scanning network devices: {str(e)}\n")

    def scan_audio_devices(self):
        """Scan audio devices"""
        try:
            output, _, _ = self.run_command("aplay -l")
            
            for line in output.splitlines():
                if line.startswith('card '):
                    device_info = {
                        'id': line.split()[1],
                        'name': ' '.join(line.split()[3:]).strip('[]'),
                        'type': 'Audio',
                        'driver': 'Unknown',
                        'status': 'unknown',
                        'details': [line]
                    }
                    
                    # Get driver information
                    driver_output, _, _ = self.run_command(
                        f"cat /proc/asound/card{device_info['id']}/id"
                    )
                    if driver_output:
                        device_info['driver'] = driver_output.strip()
                        device_info['status'] = 'ok'
                    
                    self.add_device_to_list(device_info)
                    
        except Exception as e:
            self.update_details(f"Error scanning audio devices: {str(e)}\n")

    def scan_input_devices(self):
        """Scan input devices"""
        try:
            output, _, _ = self.run_command("cat /proc/bus/input/devices")
            current_device = None
            
            for line in output.splitlines():
                if line.startswith('I:'):
                    # New device
                    if current_device:
                        self.add_device_to_list(current_device)
                    current_device = {
                        'id': line.split('=')[1].strip(),
                        'name': 'Unknown',
                        'type': 'Input',
                        'driver': 'Unknown',
                        'status': 'unknown',
                        'details': [line]
                    }
                elif current_device:
                    current_device['details'].append(line)
                    if line.startswith('N:'):
                        current_device['name'] = line.split('=')[1].strip('"')
                    elif line.startswith('H:'):
                        current_device['driver'] = line.split('=')[1].strip()
                        current_device['status'] = 'ok'
            
            # Add last device
            if current_device:
                self.add_device_to_list(current_device)
                
        except Exception as e:
            self.update_details(f"Error scanning input devices: {str(e)}\n")

    def categorize_device(self, device_name: str) -> str:
        """Categorize device based on its name"""
        name_lower = device_name.lower()
        
        if any(x in name_lower for x in ['network', 'ethernet', 'wireless', 'wifi']):
            return 'Network'
        elif any(x in name_lower for x in ['vga', 'display', '3d', 'graphics']):
            return 'Graphics'
        elif any(x in name_lower for x in ['audio', 'sound', 'multimedia']):
            return 'Audio'
        elif any(x in name_lower for x in ['usb']):
            return 'USB'
        elif any(x in name_lower for x in ['bluetooth']):
            return 'Bluetooth'
        elif any(x in name_lower for x in ['storage', 'ahci', 'raid', 'ide']):
            return 'Storage'
        elif any(x in name_lower for x in ['input', 'keyboard', 'mouse']):
            return 'Input'
        elif any(x in name_lower for x in ['printer']):
            return 'Printer'
        elif any(x in name_lower for x in ['camera', 'webcam']):
            return 'Camera'
        else:
            return 'Other'

    def add_device_to_list(self, device_info: Dict):
        """Add device to the list and check for problems"""
        device_id = device_info['id']
        self.detected_devices[device_id] = device_info
        
        # Check device status
        if device_info['driver'] == 'Unknown':
            device_info['status'] = 'error'
            self.problem_devices[device_id] = {
                'type': 'missing_driver',
                'device': device_info
            }
        elif self.check_driver_problems(device_info):
            device_info['status'] = 'warning'
            self.problem_devices[device_id] = {
                'type': 'driver_issue',
                'device': device_info
            }
        
        # Add to treeview
        status_icon = self.status_icons[device_info['status']]
        self.devices_tree.insert('', 'end',
                               values=(f"{device_info['name']}",
                                     f"{status_icon} {device_info['status']}",
                                     device_info['driver']))

    def check_driver_problems(self, device_info: Dict) -> bool:
        """Check for common driver problems"""
        try:
            # Check dmesg for errors related to this device
            output, _, _ = self.run_command(f"dmesg | grep -i {device_info['driver']}")
            if 'error' in output.lower() or 'fail' in output.lower():
                return True
            
            # Check if driver is blacklisted
            output, _, _ = self.run_command("cat /etc/modprobe.d/*.conf")
            if device_info['driver'] in output:
                return True
            
            # Check if driver is properly loaded
            output, _, _ = self.run_command("lsmod")
            if device_info['driver'] not in output:
                return True
            
            return False
            
        except Exception:
            return False

    def check_driver_issues(self):
        """Check for driver issues across all devices"""
        try:
            # Check kernel logs for device issues
            output, _, _ = self.run_command("dmesg | grep -i 'fail\|error\|warn'")
            
            for line in output.splitlines():
                for device_id, device_info in self.detected_devices.items():
                    if device_info['driver'] in line or device_info['name'] in line:
                        if device_id not in self.problem_devices:
                            device_info['status'] = 'warning'
                            self.problem_devices[device_id] = {
                                'type': 'kernel_log_issue',
                                'device': device_info,
                                'message': line
                            }
            
            # Check for missing firmware
            output, _, _ = self.run_command("dmesg | grep -i 'firmware'")
            
            for line in output.splitlines():
                if 'failed to load' in line.lower():
                    for device_id, device_info in self.detected_devices.items():
                        if device_info['driver'] in line or device_info['name'] in line:
                            if device_id not in self.problem_devices:
                                device_info['status'] = 'warning'
                                self.problem_devices[device_id] = {
                                    'type': 'missing_firmware',
                                    'device': device_info,
                                    'message': line
                                }
            
        except Exception as e:
            self.update_details(f"Error checking driver issues: {str(e)}\n")

    def update_problems_tab(self):
        """Update the problems tab with current issues"""
        self.problems_text.delete('1.0', tk.END)
        
        if not self.problem_devices:
            self.problems_text.insert(tk.END, "No device problems detected.\n")
            return
        
        self.problems_text.insert(tk.END, "=== Device Problems ===\n\n")
        
        for device_id, problem in self.problem_devices.items():
            device_info = problem['device']
            self.problems_text.insert(tk.END,
                                    f"Device: {device_info['name']}\n"
                                    f"Type: {problem['type']}\n"
                                    f"Driver: {device_info['driver']}\n")
            
            if 'message' in problem:
                self.problems_text.insert(tk.END, f"Message: {problem['message']}\n")
            
            self.problems_text.insert(tk.END, "\n")

    def fix_device(self):
        """Attempt to fix selected device"""
        selection = self.devices_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "No device selected")
            return
        
        device_name = self.devices_tree.item(selection[0])['values'][0]
        device_info = None
        
        # Find device info
        for info in self.detected_devices.values():
            if info['name'] == device_name:
                device_info = info
                break
        
        if not device_info:
            return
        
        try:
            self.update_details(f"Attempting to fix {device_name}...\n")
            
            if device_info['status'] == 'error':
                # Try to find and install missing driver
                self.find_and_install_driver(device_info)
            elif device_info['status'] == 'warning':
                # Try to fix driver issues
                self.fix_driver_issues(device_info)
            
            # Rescan devices
            self.scan_devices()
            
        except Exception as e:
            self.update_details(f"Error fixing device: {str(e)}\n")
            messagebox.showerror("Error", f"Fix failed: {str(e)}")

    def find_and_install_driver(self, device_info: Dict):
        """Find and install appropriate driver for device"""
        try:
            self.update_details("Searching for available drivers...\n")
            
            # Search in apt cache
            output, _, _ = self.run_command(
                f"apt-cache search {device_info['name']} | grep -i driver"
            )
            
            potential_drivers = []
            for line in output.splitlines():
                if any(x in line.lower() for x in ['driver', 'module']):
                    potential_drivers.append(line.split(' - ')[0])
            
            if potential_drivers:
                if messagebox.askyesno("Install Drivers",
                                     f"Found potential drivers:\n" +
                                     "\n".join(potential_drivers) +
                                     "\n\nAttempt to install?"):
                    for driver in potential_drivers:
                        self.update_details(f"Installing {driver}...\n")
                        output, error, code = self.run_command(
                            f"sudo apt-get install -y {driver}"
                        )
                        
                        if code == 0:
                            self.update_details(f"Successfully installed {driver}\n")
                        else:
                            self.update_details(f"Failed to install {driver}: {error}\n")
            
            # Check for proprietary drivers
            output, _, _ = self.run_command("ubuntu-drivers devices")
            if device_info['name'] in output:
                self.update_details("Proprietary drivers available.\n")
                if messagebox.askyesno("Install Drivers",
                                     "Install recommended proprietary drivers?"):
                    output, error, code = self.run_command(
                        "sudo ubuntu-drivers autoinstall"
                    )
                    if code == 0:
                        self.update_details("Proprietary drivers installed.\n")
                    else:
                        self.update_details(f"Failed to install drivers: {error}\n")
            
        except Exception as e:
            raise Exception(f"Error finding drivers: {str(e)}")

    def fix_driver_issues(self, device_info: Dict):
        """Attempt to fix driver issues"""
        try:
            # Unload and reload driver
            self.update_details(f"Reloading {device_info['driver']}...\n")
            self.run_command(f"sudo modprobe -r {device_info['driver']}")
            time.sleep(1)
            output, error, code = self.run_command(
                f"sudo modprobe {device_info['driver']}"
            )
            
            if code != 0:
                raise Exception(f"Failed to reload driver: {error}")
            
            # Check for and install missing firmware
            self.update_details("Checking for missing firmware...\n")
            output, _, _ = self.run_command("dmesg | grep -i firmware")
            
            if 'failed to load' in output.lower():
                # Try to install firmware
                output, error, code = self.run_command(
                    "sudo apt-get install -y linux-firmware"
                )
                
                if code == 0:
                    self.update_details("Firmware package installed.\n")
                else:
                    self.update_details(f"Failed to install firmware: {error}\n")
            
            # Update module dependencies
            self.update_details("Updating module dependencies...\n")
            self.run_command("sudo depmod -a")
            
            # Update initramfs
            self.update_details("Updating initramfs...\n")
            self.run_command("sudo update-initramfs -u")
            
        except Exception as e:
            raise Exception(f"Error fixing driver issues: {str(e)}")

    def update_driver(self):
        """Update driver for selected device"""
        selection = self.devices_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "No device selected")
            return
        
        device_name = self.devices_tree.item(selection[0])['values'][0]
        device_info = None
        
        # Find device info
        for info in self.detected_devices.values():
            if info['name'] == device_name:
                device_info = info
                break
        
        if not device_info:
            return
        
        try:
            self.update_details(f"Updating driver for {device_name}...\n")
            
            # Check for updates
            self.run_command("sudo apt-get update")
            
            # Try to upgrade the driver package
            if device_info['driver'] != 'Unknown':
                output, error, code = self.run_command(
                    f"sudo apt-get install --only-upgrade {device_info['driver']}-*"
                )
                
                if code == 0:
                    self.update_details("Driver updated successfully.\n")
                else:
                    self.update_details(f"Failed to update driver: {error}\n")
            
            # Rescan devices
            self.scan_devices()
            
        except Exception as e:
            self.update_details(f"Error updating driver: {str(e)}\n")
            messagebox.showerror("Error", f"Update failed: {str(e)}")

    def remove_driver(self):
        """Remove driver for selected device"""
        selection = self.devices_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "No device selected")
            return
        
        device_name = self.devices_tree.item(selection[0])['values'][0]
        device_info = None
        
        # Find device info
        for info in self.detected_devices.values():
            if info['name'] == device_name:
                device_info = info
                break
        
        if not device_info:
            return
        
        if messagebox.askyesno("Confirm",
                              f"Remove driver for {device_name}?\n"
                              "This may make the device unusable until "
                              "a new driver is installed."):
            try:
                self.update_details(f"Removing driver for {device_name}...\n")
                
                if device_info['driver'] != 'Unknown':
                    # Unload driver
                    self.run_command(f"sudo modprobe -r {device_info['driver']}")
                    
                    # Remove driver package
                    output, error, code = self.run_command(
                        f"sudo apt-get remove -y {device_info['driver']}-*"
                    )
                    
                    if code == 0:
                        self.update_details("Driver removed successfully.\n")
                    else:
                        self.update_details(f"Failed to remove driver: {error}\n")
                
                # Rescan devices
                self.scan_devices()
                
            except Exception as e:
                self.update_details(f"Error removing driver: {str(e)}\n")
                messagebox.showerror("Error", f"Removal failed: {str(e)}")

    def reset_device(self):
        """Reset selected device"""
        selection = self.devices_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "No device selected")
            return
        
        device_name = self.devices_tree.item(selection[0])['values'][0]
        device_info = None
        
        # Find device info
        for info in self.detected_devices.values():
            if info['name'] == device_name:
                device_info = info
                break
        
        if not device_info:
            return
        
        try:
            self.update_details(f"Resetting {device_name}...\n")
            
            # Reset USB device if applicable
            if device_info['type'] == 'USB':
                self.reset_usb_device(device_info)
            
            # Reset PCI device if applicable
            elif device_info['type'] in ['Network', 'Graphics', 'Audio']:
                self.reset_pci_device(device_info)
            
            # Rescan devices
            self.scan_devices()
            
        except Exception as e:
            self.update_details(f"Error resetting device: {str(e)}\n")
            messagebox.showerror("Error", f"Reset failed: {str(e)}")

    def reset_usb_device(self, device_info: Dict):
        """Reset USB device"""
        try:
            # Find USB port
            output, _, _ = self.run_command("lsusb")
            
            for line in output.splitlines():
                if device_info['id'] in line:
                    bus = line.split()[1]
                    device = line.split()[3].rstrip(':')
                    
                    # Reset device
                    self.run_command(
                        f"sudo usbreset /dev/bus/usb/{bus}/{device}"
                    )
                    break
            
        except Exception as e:
            raise Exception(f"Error resetting USB device: {str(e)}")

    def reset_pci_device(self, device_info: Dict):
        """Reset PCI device"""
        try:
            # Find PCI slot
            output, _, _ = self.run_command("lspci -n")
            
            for line in output.splitlines():
                if device_info['id'] in line:
                    slot = line.split()[0]
                    
                    # Reset device
                    self.run_command(
                        f"sudo setpci -s {slot} COMMAND=0x0"
                    )
                    time.sleep(1)
                    self.run_command(
                        f"sudo setpci -s {slot} COMMAND=0x3"
                    )
                    break
            
        except Exception as e:
            raise Exception(f"Error resetting PCI device: {str(e)}")

    def fix_all_problems(self):
        """Attempt to fix all detected problems"""
        if not self.problem_devices:
            messagebox.showinfo("Info", "No problems detected")
            return
        
        if messagebox.askyesno("Confirm",
                              "Attempt to fix all detected problems?"):
            try:
                self.update_details("Attempting to fix all problems...\n")
                
                for device_id, problem in self.problem_devices.items():
                    device_info = problem['device']
                    self.update_details(f"\nFixing {device_info['name']}...\n")
                    
                    if problem['type'] == 'missing_driver':
                        self.find_and_install_driver(device_info)
                    elif problem['type'] == 'driver_issue':
                        self.fix_driver_issues(device_info)
                    elif problem['type'] == 'missing_firmware':
                        # Install firmware packages
                        self.update_details("Installing firmware packages...\n")
                        self.run_command("sudo apt-get install -y linux-firmware")
                        self.run_command("sudo apt-get install -y firmware-linux-nonfree")
                    elif problem['type'] == 'kernel_log_issue':
                        # Reload driver and update dependencies
                        if device_info['driver'] != 'Unknown':
                            self.update_details(f"Reloading {device_info['driver']}...\n")
                            self.run_command(f"sudo modprobe -r {device_info['driver']}")
                            time.sleep(1)
                            self.run_command(f"sudo modprobe {device_info['driver']}")
                
                # Update module dependencies
                self.update_details("\nUpdating module dependencies...\n")
                self.run_command("sudo depmod -a")
                
                # Update initramfs
                self.update_details("Updating initramfs...\n")
                self.run_command("sudo update-initramfs -u")
                
                # Rescan devices
                self.scan_devices()
                
                self.update_details("\nAll fixes attempted. Please check device status.\n")
                
            except Exception as e:
                self.update_details(f"Error fixing problems: {str(e)}\n")
                messagebox.showerror("Error", f"Fix all failed: {str(e)}")

    def filter_devices(self):
        """Filter devices by category"""
        category = self.category_var.get()
        
        # Clear current view
        self.devices_tree.delete(*self.devices_tree.get_children())
        
        # Add filtered devices
        for device_info in self.detected_devices.values():
            if category == 'All' or device_info['type'] == category:
                status_icon = self.status_icons[device_info['status']]
                self.devices_tree.insert('', 'end',
                                       values=(f"{device_info['name']}",
                                              f"{status_icon} {device_info['status']}",
                                              device_info['driver']))

    def show_device_details(self, event):
        """Show detailed information about the selected device"""
        selection = self.devices_tree.selection()
        if selection:
            device_name = self.devices_tree.item(selection[0])['values'][0]
            
            # Find device info
            device_info = None
            for info in self.detected_devices.values():
                if info['name'] == device_name:
                    device_info = info
                    break
            
            if device_info:
                # Clear details
                self.details_text.delete('1.0', tk.END)
                
                # Basic info
                self.details_text.insert(tk.END,
                                       f"=== Device Details ===\n\n"
                                       f"Name: {device_info['name']}\n"
                                       f"ID: {device_info['id']}\n"
                                       f"Type: {device_info['type']}\n"
                                       f"Driver: {device_info['driver']}\n"
                                       f"Status: {device_info['status']}\n\n")
                
                # Module information if available
                if 'modules' in device_info:
                    self.details_text.insert(tk.END,
                                           f"Available Modules: {device_info['modules']}\n\n")
                
                # Raw details
                self.details_text.insert(tk.END, "=== Raw Information ===\n\n")
                for detail in device_info['details']:
                    self.details_text.insert(tk.END, f"{detail}\n")
                
                # Additional checks
                self.show_additional_details(device_info)

    def show_additional_details(self, device_info: Dict):
        """Show additional device-specific details"""
        self.details_text.insert(tk.END, "\n=== Additional Information ===\n\n")
        
        try:
            # Check kernel messages
            output, _, _ = self.run_command(f"dmesg | grep -i '{device_info['name']}'")
            if output:
                self.details_text.insert(tk.END, "Recent Kernel Messages:\n")
                self.details_text.insert(tk.END, output + "\n\n")
            
            # Check loaded modules
            if device_info['driver'] != 'Unknown':
                output, _, _ = self.run_command(f"lsmod | grep {device_info['driver']}")
                if output:
                    self.details_text.insert(tk.END, "Module Information:\n")
                    self.details_text.insert(tk.END, output + "\n\n")
            
            # Device-specific information
            if device_info['type'] == 'Network':
                self.show_network_details(device_info)
            elif device_info['type'] == 'Graphics':
                self.show_graphics_details(device_info)
            elif device_info['type'] == 'Audio':
                self.show_audio_details(device_info)
            elif device_info['type'] == 'Storage':
                self.show_storage_details(device_info)
            
        except Exception as e:
            self.details_text.insert(tk.END, f"Error getting additional details: {str(e)}\n")

    def show_network_details(self, device_info: Dict):
        """Show network device specific details"""
        try:
            self.details_text.insert(tk.END, "Network Interface Details:\n")
            
            # Get IP information
            output, _, _ = self.run_command(f"ip addr show")
            for line in output.splitlines():
                if device_info['name'] in line:
                    self.details_text.insert(tk.END, line + "\n")
            
            # Get link status
            output, _, _ = self.run_command(f"ethtool {device_info['name']}")
            self.details_text.insert(tk.END, "\nLink Status:\n" + output + "\n")
            
        except Exception as e:
            self.details_text.insert(tk.END, f"Error getting network details: {str(e)}\n")

    def show_graphics_details(self, device_info: Dict):
        """Show graphics device specific details"""
        try:
            self.details_text.insert(tk.END, "Graphics Card Details:\n")
            
            # Get OpenGL information
            output, _, _ = self.run_command("glxinfo | grep -i 'renderer\\|version'")
            self.details_text.insert(tk.END, output + "\n")
            
            # Get resolution information
            output, _, _ = self.run_command("xrandr")
            self.details_text.insert(tk.END, "\nDisplay Information:\n" + output + "\n")
            
        except Exception as e:
            self.details_text.insert(tk.END, f"Error getting graphics details: {str(e)}\n")

    def show_audio_details(self, device_info: Dict):
        """Show audio device specific details"""
        try:
            self.details_text.insert(tk.END, "Audio Device Details:\n")
            
            # Get ALSA information
            output, _, _ = self.run_command("aplay -l")
            self.details_text.insert(tk.END, output + "\n")
            
            # Get PulseAudio information
            output, _, _ = self.run_command("pactl list")
            self.details_text.insert(tk.END, "\nPulseAudio Information:\n" + output + "\n")
            
        except Exception as e:
            self.details_text.insert(tk.END, f"Error getting audio details: {str(e)}\n")

    def show_storage_details(self, device_info: Dict):
        """Show storage device specific details"""
        try:
            self.details_text.insert(tk.END, "Storage Device Details:\n")
            
            # Get device information
            output, _, _ = self.run_command(f"sudo hdparm -I {device_info['name']}")
            self.details_text.insert(tk.END, output + "\n")
            
            # Get SMART information
            output, _, _ = self.run_command(f"sudo smartctl -a {device_info['name']}")
            self.details_text.insert(tk.END, "\nSMART Information:\n" + output + "\n")
            
        except Exception as e:
            self.details_text.insert(tk.END, f"Error getting storage details: {str(e)}\n")

    def update_details(self, message: str):
        """Update details text area"""
        self.details_text.insert(tk.END, message)
        self.details_text.see(tk.END)
        self.details_text.update()

    def device_event(self, action, device):
        """Handle device plug/unplug events"""
        if action in ['add', 'remove']:
            self.update_details(f"Device {action}: {device.device_node}\n")
            self.scan_devices()

    def __del__(self):
        """Cleanup when module is destroyed"""
        try:
            self.observer.stop()
        except:
            pass