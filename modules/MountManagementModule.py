# Part 9: Mount Management Module
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
import re
from pathlib import Path
import json
import threading
from datetime import datetime
import psutil
import yaml

class MountManagementModule:
    def __init__(self, parent_notebook):
        # Create mount management tab
        self.mount_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.mount_frame, text='Mount Manager')
        
        # Initialize data structures
        self.mounted_points = {}
        self.available_devices = {}
        self.mount_history = []
        
        # Load mount configurations
        self.load_mount_configs()
        
        # Create interface
        self.create_interface()
        
        # Initial scan
        self.scan_mounts()

    def create_interface(self):
        """Create the mount management interface"""
        # Create main paned window
        self.paned = ttk.PanedWindow(self.mount_frame, orient=tk.HORIZONTAL)
        self.paned.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create left panel (mounted devices)
        self.left_frame = ttk.LabelFrame(self.paned, text="Mounted Devices")
        self.paned.add(self.left_frame)
        
        # Create mounted devices list
        self.mounted_tree = ttk.Treeview(
            self.left_frame,
            columns=('mountpoint', 'type', 'options'),
            show='headings'
        )
        self.mounted_tree.heading('mountpoint', text='Mount Point')
        self.mounted_tree.heading('type', text='Type')
        self.mounted_tree.heading('options', text='Options')
        self.mounted_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create unmount button frame
        unmount_frame = ttk.Frame(self.left_frame)
        unmount_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(unmount_frame, text="Unmount", 
                  command=self.unmount_selected).pack(side='left', padx=2)
        ttk.Button(unmount_frame, text="Force Unmount", 
                  command=lambda: self.unmount_selected(force=True)).pack(
                      side='left', padx=2)
        
        # Create right panel (available devices)
        self.right_frame = ttk.Frame(self.paned)
        self.paned.add(self.right_frame)
        
        # Create available devices frame
        available_frame = ttk.LabelFrame(self.right_frame, text="Available Devices")
        available_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.available_tree = ttk.Treeview(
            available_frame,
            columns=('size', 'type', 'label'),
            show='headings'
        )
        self.available_tree.heading('size', text='Size')
        self.available_tree.heading('type', text='Type')
        self.available_tree.heading('label', text='Label')
        self.available_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create mount controls
        mount_frame = ttk.Frame(self.right_frame)
        mount_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(mount_frame, text="Mount", 
                  command=self.mount_selected).pack(side='left', padx=2)
        ttk.Button(mount_frame, text="Mount with Options", 
                  command=self.mount_with_options).pack(side='left', padx=2)
        ttk.Button(mount_frame, text="Quick Mount", 
                  command=self.quick_mount).pack(side='left', padx=2)
        
        # Create refresh button
        ttk.Button(self.right_frame, text="Refresh", 
                  command=self.scan_mounts).pack(pady=5)
        
        # Create status bar
        self.status_var = tk.StringVar()
        ttk.Label(self.mount_frame, textvariable=self.status_var).pack(
            fill='x', padx=5, pady=5)

    def load_mount_configs(self):
        """Load mount configurations from file"""
        try:
            config_file = Path.home() / '.config' / 'mount_configs.yaml'
            if config_file.exists():
                with open(config_file) as f:
                    self.mount_configs = yaml.safe_load(f)
            else:
                self.mount_configs = {
                    'default_options': {
                        'ext4': 'defaults,noatime',
                        'ntfs': 'defaults,nls=utf8,umask=0022',
                        'vfat': 'defaults,utf8=true,umask=0022',
                        'exfat': 'defaults,noatime'
                    },
                    'mount_points': {
                        'removable': '/media/USER',
                        'network': '/mnt/network'
                    },
                    'auto_mount': {
                        'enabled': True,
                        'types': ['ext4', 'ntfs', 'vfat', 'exfat']
                    }
                }
                # Save default config
                config_file.parent.mkdir(parents=True, exist_ok=True)
                with open(config_file, 'w') as f:
                    yaml.dump(self.mount_configs, f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configurations: {str(e)}")
            self.mount_configs = {}

    def scan_mounts(self):
        """Scan system for mounted devices and available devices"""
        try:
            # Clear existing data
            self.mounted_points.clear()
            self.available_devices.clear()
            self.mounted_tree.delete(*self.mounted_tree.get_children())
            self.available_tree.delete(*self.available_tree.get_children())
            
            # Get mounted devices
            partitions = psutil.disk_partitions(all=True)
            for partition in partitions:
                self.mounted_points[partition.device] = {
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'opts': partition.opts
                }
                self.mounted_tree.insert('', 'end',
                                       values=(partition.mountpoint,
                                              partition.fstype,
                                              partition.opts))
            
            # Get available devices
            self.scan_available_devices()
            
            self.status_var.set("Scan completed successfully")
            
        except Exception as e:
            self.status_var.set(f"Error during scan: {str(e)}")
            messagebox.showerror("Error", f"Failed to scan mounts: {str(e)}")

    def scan_available_devices(self):
        """Scan for available devices that can be mounted"""
        try:
            # Get list of all block devices
            output = subprocess.check_output(
                ['lsblk', '-Jo', 'NAME,SIZE,TYPE,FSTYPE,LABEL,MOUNTPOINT'])
            devices = json.loads(output)['blockdevices']
            
            for device in devices:
                self.process_device(device)
            
        except Exception as e:
            messagebox.showerror("Error", 
                               f"Failed to scan available devices: {str(e)}")

    def process_device(self, device):
        """Process device information"""
        # Skip if device is already mounted
        if device.get('mountpoint'):
            return
        
        # Skip if device is not a partition or has no filesystem
        if device['type'] != 'part' or not device.get('fstype'):
            return
        
        # Add to available devices
        name = device['name']
        self.available_devices[name] = {
            'size': device['size'],
            'fstype': device['fstype'],
            'label': device.get('label', '')
        }
        
        self.available_tree.insert('', 'end',
                                 values=(device['size'],
                                        device['fstype'],
                                        device.get('label', '')),
                                 text=name)

    def mount_selected(self):
        """Mount selected device"""
        selection = self.available_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a device to mount")
            return
        
        device_name = self.available_tree.item(selection[0])['text']
        device_info = self.available_devices[device_name]
        
        # Create mount dialog
        dialog = MountDialog(self.mount_frame, device_name, device_info)
        if dialog.result:
            try:
                self.mount_device(device_name, dialog.result)
                self.scan_mounts()
                messagebox.showinfo("Success", "Device mounted successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to mount device: {str(e)}")

    def mount_device(self, device_name, mount_info):
        """Mount device with specified options"""
        # Create mount point if it doesn't exist
        os.makedirs(mount_info['mountpoint'], exist_ok=True)
        
        # Build mount command
        cmd = ['mount']
        if mount_info['options']:
            cmd.extend(['-o', mount_info['options']])
        cmd.extend([f"/dev/{device_name}", mount_info['mountpoint']])
        
        # Execute mount command
        subprocess.check_call(cmd)
        
        # Add to mount history
        self.mount_history.append({
            'device': device_name,
            'mountpoint': mount_info['mountpoint'],
            'timestamp': datetime.now().isoformat()
        })

    def unmount_selected(self, force=False):
        """Unmount selected mounted device"""
        selection = self.mounted_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a mount point to unmount")
            return
        
        mountpoint = self.mounted_tree.item(selection[0])['values'][0]
        
        try:
            # Build unmount command
            cmd = ['umount']
            if force:
                cmd.append('-f')
            cmd.append(mountpoint)
            
            # Execute unmount command
            subprocess.check_call(cmd)
            
            self.scan_mounts()
            messagebox.showinfo("Success", "Device unmounted successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to unmount device: {str(e)}")

    def mount_with_options(self):
        """Mount selected device with custom options"""
        selection = self.available_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a device to mount")
            return
        
        device_name = self.available_tree.item(selection[0])['text']
        device_info = self.available_devices[device_name]
        
        # Create advanced mount dialog
        dialog = AdvancedMountDialog(self.mount_frame, device_name, device_info)
        if dialog.result:
            try:
                self.mount_device(device_name, dialog.result)
                self.scan_mounts()
                messagebox.showinfo("Success", "Device mounted successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to mount device: {str(e)}")

    def quick_mount(self):
        """Quickly mount selected device with default options"""
        selection = self.available_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a device to mount")
            return
        
        device_name = self.available_tree.item(selection[0])['text']
        device_info = self.available_devices[device_name]
        
        try:
            # Generate mount point
            label = device_info['label'] or device_name
            mountpoint = os.path.join(
                self.mount_configs['mount_points']['removable'].replace(
                    'USER', os.getenv('USER')),
                label
            )
            
            # Get default options for filesystem type
            options = self.mount_configs['default_options'].get(
                device_info['fstype'], 'defaults')
            
            # Mount device
            self.mount_device(device_name, {
                'mountpoint': mountpoint,
                'options': options
            })
            
            self.scan_mounts()
            messagebox.showinfo("Success", "Device mounted successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to mount device: {str(e)}")

class MountDialog:
    """Basic dialog for mounting devices"""
    def __init__(self, parent, device_name, device_info):
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Mount Device {device_name}")
        self.dialog.geometry("400x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Create form
        ttk.Label(self.dialog, text="Mount Point:").pack(pady=5)
        self.mountpoint_var = tk.StringVar()
        ttk.Entry(self.dialog, textvariable=self.mountpoint_var).pack(fill='x', padx=5)
        
        ttk.Label(self.dialog, text="Options:").pack(pady=5)
        self.options_var = tk.StringVar(value="defaults")
        ttk.Entry(self.dialog, textvariable=self.options_var).pack(fill='x', padx=5)
        
        # Create buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', pady=20)
        
        ttk.Button(button_frame, text="Mount", 
                  command=self.on_mount).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=self.dialog.destroy).pack(side='right', padx=5)
        
        # Wait for dialog to close
        self.dialog.wait_window()

    def on_mount(self):
        """Handle mount button click"""
        if not self.mountpoint_var.get():
            messagebox.showerror("Error", "Please specify a mount point")
            return
        
        self.result = {
            'mountpoint': self.mountpoint_var.get(),
            'options': self.options_var.get()
        }
        self.dialog.destroy()

class AdvancedMountDialog:
    """Advanced dialog for mounting devices with more options"""
    def __init__(self, parent, device_name, device_info):
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Advanced Mount - {device_name}")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Create notebook for options
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Basic options tab
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="Basic")
        
        ttk.Label(basic_frame, text="Mount Point:").pack(pady=5)
        self.mountpoint_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.mountpoint_var).pack(fill='x', padx=5)
        
        # Mount options
        options_frame = ttk.LabelFrame(basic_frame, text="Mount Options")
        options_frame.pack(fill='x', padx=5, pady=5)
        
        # Common options
        self.read_only = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="Read Only", 
                       variable=self.read_only).pack(anchor='w')
        
        self.noexec = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="No Execute", 
                       variable=self.noexec).pack(anchor='w')
        
        self.nosuid = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="No SUID", 
                       variable=self.nosuid).pack(anchor='w')
        
        self.nodev = tk.BooleanVar()
        ttk.Checkbutton(options_frame, text="No Device Files", 
                       variable=self.nodev).pack(anchor='w')
        
        # Advanced options tab
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="Advanced")
        
        # Filesystem specific options
        fs_frame = ttk.LabelFrame(advanced_frame, text="Filesystem Options")
        fs_frame.pack(fill='x', padx=5, pady=5)
        
        self.fs_options = {
            'ext4': {
                'journal_data': tk.BooleanVar(),
                'acl': tk.BooleanVar(),
                'user_xattr': tk.BooleanVar()
            },
            'ntfs': {
                'compression': tk.BooleanVar(),
                'big_writes': tk.BooleanVar(),
                'ignore_case': tk.BooleanVar()
            },
            'vfat': {
                'shortname': tk.StringVar(value='mixed'),
                'codepage': tk.StringVar(value='437'),
                'iocharset': tk.StringVar(value='utf8')
            }
        }
        
        # Create filesystem specific controls based on device type
        fs_type = device_info['fstype']
        if fs_type in self.fs_options:
            for opt_name, opt_var in self.fs_options[fs_type].items():
                if isinstance(opt_var, tk.BooleanVar):
                    ttk.Checkbutton(fs_frame, text=opt_name.replace('_', ' ').title(),
                                  variable=opt_var).pack(anchor='w')
                else:
                    ttk.Label(fs_frame, text=f"{opt_name.replace('_', ' ').title()}:").pack(
                        anchor='w')
                    ttk.Entry(fs_frame, textvariable=opt_var).pack(fill='x', padx=5)
        
        # Performance options tab
        perf_frame = ttk.Frame(notebook)
        notebook.add(perf_frame, text="Performance")
        
        # Buffer options
        buffer_frame = ttk.LabelFrame(perf_frame, text="Buffer Settings")
        buffer_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(buffer_frame, text="Data Mode:").pack(anchor='w')
        self.data_mode = tk.StringVar(value='ordered')
        ttk.Radiobutton(buffer_frame, text="Ordered", 
                       variable=self.data_mode, 
                       value='ordered').pack(anchor='w')
        ttk.Radiobutton(buffer_frame, text="Writeback", 
                       variable=self.data_mode, 
                       value='writeback').pack(anchor='w')
        ttk.Radiobutton(buffer_frame, text="Journal", 
                       variable=self.data_mode, 
                       value='journal').pack(anchor='w')
        
        # Custom options
        custom_frame = ttk.LabelFrame(advanced_frame, text="Custom Options")
        custom_frame.pack(fill='x', padx=5, pady=5)
        
        self.custom_options = tk.StringVar()
        ttk.Entry(custom_frame, textvariable=self.custom_options).pack(
            fill='x', padx=5, pady=5)
        
        # Create buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="Mount", 
                  command=self.on_mount).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=self.dialog.destroy).pack(side='right', padx=5)
        
        # Wait for dialog to close
        self.dialog.wait_window()

    def build_mount_options(self, fs_type):
        """Build mount options string based on selected options"""
        options = []
        
        # Add basic options
        if self.read_only.get():
            options.append('ro')
        if self.noexec.get():
            options.append('noexec')
        if self.nosuid.get():
            options.append('nosuid')
        if self.nodev.get():
            options.append('nodev')
        
        # Add filesystem specific options
        if fs_type in self.fs_options:
            for opt_name, opt_var in self.fs_options[fs_type].items():
                if isinstance(opt_var, tk.BooleanVar) and opt_var.get():
                    options.append(opt_name)
                elif isinstance(opt_var, tk.StringVar) and opt_var.get():
                    options.append(f"{opt_name}={opt_var.get()}")
        
        # Add performance options
        if self.data_mode.get() != 'ordered':
            options.append(f"data={self.data_mode.get()}")
        
        # Add custom options
        if self.custom_options.get():
            options.extend(self.custom_options.get().split(','))
        
        return ','.join(options) if options else 'defaults'

    def on_mount(self):
        """Handle mount button click"""
        if not self.mountpoint_var.get():
            messagebox.showerror("Error", "Please specify a mount point")
            return
        
        self.result = {
            'mountpoint': self.mountpoint_var.get(),
            'options': self.build_mount_options(device_info['fstype'])
        }
        self.dialog.destroy()
