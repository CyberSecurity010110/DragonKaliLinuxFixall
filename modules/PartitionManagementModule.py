# Part 8: Partition Management Module
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
import re
from pathlib import Path
import json
import threading
from datetime import datetime
import humanize

class PartitionManagementModule:
    def __init__(self, parent_notebook):
        # Create partition management tab
        self.partition_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.partition_frame, text='Partitions')
        
        # Initialize data structures
        self.disks = {}
        self.partitions = {}
        self.free_spaces = {}
        
        # Create UI
        self.create_interface()
        
        # Initial scan
        self.scan_disks()

    def create_interface(self):
        """Create the partition management interface"""
        # Create main paned window
        self.paned = ttk.PanedWindow(self.partition_frame, orient=tk.HORIZONTAL)
        self.paned.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create left panel (disk/partition list)
        self.left_frame = ttk.Frame(self.paned)
        self.paned.add(self.left_frame)
        
        # Create disk list
        disk_frame = ttk.LabelFrame(self.left_frame, text="Disks and Partitions")
        disk_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.disk_tree = ttk.Treeview(disk_frame, 
                                     columns=('size', 'used', 'type'),
                                     show='tree headings')
        self.disk_tree.heading('size', text='Size')
        self.disk_tree.heading('used', text='Used')
        self.disk_tree.heading('type', text='Type')
        self.disk_tree.pack(fill='both', expand=True)
        
        # Bind selection event
        self.disk_tree.bind('<<TreeviewSelect>>', self.on_select)
        
        # Create control buttons
        control_frame = ttk.Frame(self.left_frame)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(control_frame, text="Refresh", 
                  command=self.scan_disks).pack(side='left', padx=2)
        ttk.Button(control_frame, text="Create Partition", 
                  command=self.create_partition).pack(side='left', padx=2)
        ttk.Button(control_frame, text="Format", 
                  command=self.format_partition).pack(side='left', padx=2)
        ttk.Button(control_frame, text="Repair", 
                  command=self.repair_partition).pack(side='left', padx=2)
        
        # Create right panel (details and operations)
        self.right_frame = ttk.Frame(self.paned)
        self.paned.add(self.right_frame)
        
        # Create details view
        details_frame = ttk.LabelFrame(self.right_frame, text="Details")
        details_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.details_text = scrolledtext.ScrolledText(details_frame, 
                                                     wrap=tk.WORD,
                                                     height=20)
        self.details_text.pack(fill='both', expand=True)

    def scan_disks(self):
        """Scan system for disks and partitions"""
        try:
            self.disks.clear()
            self.partitions.clear()
            self.free_spaces.clear()
            self.disk_tree.delete(*self.disk_tree.get_children())
            
            # Get disk information using lsblk
            output = subprocess.check_output(
                ['lsblk', '-Jo', 'NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,LABEL'])
            disk_data = json.loads(output)
            
            for device in disk_data['blockdevices']:
                self.process_device(device)
            
            # Scan for free spaces
            self.scan_free_spaces()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan disks: {str(e)}")

    def process_device(self, device, parent=''):
        """Process disk device information"""
        name = device['name']
        size = device['size']
        dev_type = device['type']
        
        # Store device information
        device_info = {
            'name': name,
            'size': size,
            'type': dev_type,
            'fstype': device.get('fstype', ''),
            'mountpoint': device.get('mountpoint', ''),
            'label': device.get('label', '')
        }
        
        # Add to appropriate dictionary
        if dev_type == 'disk':
            self.disks[name] = device_info
            parent_id = self.disk_tree.insert('', 'end',
                                            text=name,
                                            values=(size, '', 'Disk'),
                                            tags=('disk',))
        else:
            self.partitions[name] = device_info
            self.disk_tree.insert(parent, 'end',
                                text=name,
                                values=(size, 
                                       device_info['mountpoint'], 
                                       device_info['fstype']),
                                tags=('partition',))
            parent_id = ''
        
        # Process children (partitions)
        if 'children' in device:
            for child in device['children']:
                self.process_device(child, parent_id)

    def scan_free_spaces(self):
        """Scan for unallocated spaces on disks"""
        try:
            for disk in self.disks:
                # Use parted to get free space information
                output = subprocess.check_output(
                    ['parted', '-s', f'/dev/{disk}', 'unit', 'B', 'print', 'free'])
                
                # Parse output for free spaces
                free_spaces = []
                lines = output.decode().split('\n')
                for line in lines:
                    if 'Free Space' in line:
                        parts = line.split()
                        start = int(parts[0].rstrip('B'))
                        end = int(parts[1].rstrip('B'))
                        size = end - start
                        if size > 1024 * 1024:  # Only show if larger than 1MB
                            free_spaces.append({
                                'start': start,
                                'end': end,
                                'size': size
                            })
                
                if free_spaces:
                    self.free_spaces[disk] = free_spaces
                    # Add free spaces to tree
                    disk_item = self.find_disk_item(disk)
                    if disk_item:
                        for i, space in enumerate(free_spaces):
                            size_str = humanize.naturalsize(space['size'])
                            self.disk_tree.insert(disk_item, 'end',
                                                text=f'Free Space {i+1}',
                                                values=(size_str, '', 'Free'),
                                                tags=('free',))
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan free spaces: {str(e)}")

    def find_disk_item(self, disk_name):
        """Find tree item for disk"""
        for item in self.disk_tree.get_children():
            if self.disk_tree.item(item)['text'] == disk_name:
                return item
        return None

    def on_select(self, event):
        """Handle selection in disk tree"""
        selection = self.disk_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        item_text = self.disk_tree.item(item)['text']
        item_tags = self.disk_tree.item(item)['tags']
        
        self.details_text.delete('1.0', tk.END)
        
        if 'disk' in item_tags:
            self.show_disk_details(item_text)
        elif 'partition' in item_tags:
            self.show_partition_details(item_text)
        elif 'free' in item_tags:
            self.show_free_space_details(item)

    def show_disk_details(self, disk_name):
        """Show detailed information about selected disk"""
        try:
            self.details_text.insert(tk.END, f"Disk: {disk_name}\n")
            self.details_text.insert(tk.END, "=" * 50 + "\n\n")
            
            # Get detailed disk information using hdparm
            output = subprocess.check_output(
                ['hdparm', '-I', f'/dev/{disk_name}'])
            self.details_text.insert(tk.END, output.decode())
            
            # Add partition table information
            output = subprocess.check_output(
                ['parted', '-s', f'/dev/{disk_name}', 'print'])
            self.details_text.insert(tk.END, "\nPartition Table:\n")
            self.details_text.insert(tk.END, "=" * 50 + "\n")
            self.details_text.insert(tk.END, output.decode())
            
        except Exception as e:
            self.details_text.insert(tk.END, f"Error getting disk details: {str(e)}")

    def show_partition_details(self, partition_name):
        """Show detailed information about selected partition"""
        try:
            partition = self.partitions[partition_name]
            self.details_text.insert(tk.END, f"Partition: {partition_name}\n")
            self.details_text.insert(tk.END, "=" * 50 + "\n\n")
            
            # Basic information
            self.details_text.insert(tk.END, f"Size: {partition['size']}\n")
            self.details_text.insert(tk.END, f"Type: {partition['fstype']}\n")
            self.details_text.insert(tk.END, f"Mount: {partition['mountpoint']}\n")
            self.details_text.insert(tk.END, f"Label: {partition['label']}\n\n")
            
            # Get filesystem information
            if partition['mountpoint']:
                output = subprocess.check_output(['df', '-h', partition['mountpoint']])
                self.details_text.insert(tk.END, "Filesystem Usage:\n")
                self.details_text.insert(tk.END, output.decode())
            
            # Get filesystem details
            if partition['fstype']:
                if partition['fstype'] in ['ext2', 'ext3', 'ext4']:
                    output = subprocess.check_output(
                        ['tune2fs', '-l', f"/dev/{partition_name}"])
                    self.details_text.insert(tk.END, "\nFilesystem Details:\n")
                    self.details_text.insert(tk.END, output.decode())
                
        except Exception as e:
            self.details_text.insert(tk.END, f"Error getting partition details: {str(e)}")

    def show_free_space_details(self, item):
        """Show information about free space"""
        disk_item = self.disk_tree.parent(item)
        disk_name = self.disk_tree.item(disk_item)['text']
        
        if disk_name in self.free_spaces:
            index = int(self.disk_tree.item(item)['text'].split()[-1]) - 1
            space = self.free_spaces[disk_name][index]
            
            self.details_text.insert(tk.END, "Free Space Information\n")
            self.details_text.insert(tk.END, "=" * 50 + "\n\n")
            self.details_text.insert(tk.END, f"Start: {space['start']} bytes\n")
            self.details_text.insert(tk.END, f"End: {space['end']} bytes\n")
            self.details_text.insert(tk.END, f"Size: {humanize.naturalsize(space['size'])}\n")

    def create_partition(self):
        """Create new partition in free space"""
        selection = self.disk_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a free space")
            return
        
        item = selection[0]
        if 'free' not in self.disk_tree.item(item)['tags']:
            messagebox.showinfo("Info", "Please select a free space")
            return
        
        # Get disk name
        disk_item = self.disk_tree.parent(item)
        disk_name = self.disk_tree.item(disk_item)['text']
        
        # Create partition dialog
        dialog = PartitionDialog(self.partition_frame, disk_name)
        if dialog.result:
            try:
                # Create partition
                self.create_partition_on_disk(disk_name, dialog.result)
                # Refresh display
                self.scan_disks()
                messagebox.showinfo("Success", "Partition created successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create partition: {str(e)}")

    def create_partition_on_disk(self, disk_name, settings):
        """Create partition with specified settings"""
        commands = [
            # Create partition
            ['parted', '-s', f'/dev/{disk_name}', 'mkpart', 
             settings['type'], settings['fs_type'],
             f"{settings['start']}MB", f"{settings['end']}MB"],
            
            # Format partition if requested
            ['mkfs', '-t', settings['fs_type'], f"/dev/{disk_name}{settings['number']}"]
        ]
        
        for cmd in commands:
            subprocess.check_call(cmd)

    def format_partition(self):
        """Format selected partition"""
        selection = self.disk_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a partition")
            return
        
        item = selection[0]
        if 'partition' not in self.disk_tree.item(item)['tags']:
            messagebox.showinfo("Info", "Please select a partition")
            return
        
        partition_name = self.disk_tree.item(item)['text']
        
        # Format dialog
        dialog = FormatDialog(self.partition_frame, partition_name)
        if dialog.result:
            try:
                # Format partition
                self.format_partition_with_settings(partition_name, dialog.result)
                # Refresh display
                self.scan_disks()
                messagebox.showinfo("Success", "Partition formatted successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to format partition: {str(e)}")

    def format_partition_with_settings(self, partition_name, settings):
        """Format partition with specified settings"""
        # Unmount if mounted
        partition = self.partitions[partition_name]
        if partition['mountpoint']:
            subprocess.check_call(['umount', partition['mountpoint']])
        
        # Format partition
        cmd = ['mkfs', '-t', settings['fs_type']]
        if settings['label']:
            if settings['fs_type'] in ['ext2', 'ext3', 'ext4']:
                cmd.extend(['-L', settings['label']])
            elif settings['fs_type'] == 'ntfs':
                cmd.extend(['-L', settings['label']])
        
        cmd.append(f"/dev/{partition_name}")
        subprocess.check_call(cmd)

    def repair_partition(self):
        """Repair selected partition"""
        selection = self.disk_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a partition")
            return
        
        item = selection[0]
        if 'partition' not in self.disk_tree.item(item)['tags']:
            messagebox.showinfo("Info", "Please select a partition")
            return
        
        partition_name = self.disk_tree.item(item)['text']
        partition = self.partitions[partition_name]
        
        # Create repair dialog
        repair_window = tk.Toplevel(self.partition_frame)
        repair_window.title(f"Repair Partition {partition_name}")
        repair_window.geometry("600x400")
        
        # Create repair options
        options_frame = ttk.LabelFrame(repair_window, text="Repair Options")
        options_frame.pack(fill='x', padx=5, pady=5)
        
        repair_type = tk.StringVar(value="check")
        ttk.Radiobutton(options_frame, text="Check only", 
                       variable=repair_type, value="check").pack(anchor='w')
        ttk.Radiobutton(options_frame, text="Auto-repair", 
                       variable=repair_type, value="repair").pack(anchor='w')
        ttk.Radiobutton(options_frame, text="Full check and repair", 
                       variable=repair_type, value="full").pack(anchor='w')
        
        # Create output display
        output_text = scrolledtext.ScrolledText(repair_window, height=15)
        output_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        def run_repair():
            try:
                # Unmount if mounted
                if partition['mountpoint']:
                    subprocess.check_call(['umount', partition['mountpoint']])
                
                repair_commands = {
                    'ext2': {
                        'check': ['e2fsck', '-n'],
                        'repair': ['e2fsck', '-p'],
                        'full': ['e2fsck', '-fyD']
                    },
                    'ext3': {
                        'check': ['e2fsck', '-n'],
                        'repair': ['e2fsck', '-p'],
                        'full': ['e2fsck', '-fyD']
                    },
                    'ext4': {
                        'check': ['e2fsck', '-n'],
                        'repair': ['e2fsck', '-p'],
                        'full': ['e2fsck', '-fyD']
                    },
                    'ntfs': {
                        'check': ['ntfsfix', '-n'],
                        'repair': ['ntfsfix'],
                        'full': ['ntfsfix', '-d']
                    },
                    'fat32': {
                        'check': ['fsck.fat', '-n'],
                        'repair': ['fsck.fat', '-a'],
                        'full': ['fsck.fat', '-vy']
                    }
                }
                
                fs_type = partition['fstype']
                if fs_type not in repair_commands:
                    raise Exception(f"Unsupported filesystem: {fs_type}")
                
                cmd = repair_commands[fs_type][repair_type.get()]
                cmd.append(f"/dev/{partition_name}")
                
                output_text.delete('1.0', tk.END)
                output_text.insert(tk.END, f"Running repair on {partition_name}...\n")
                output_text.insert(tk.END, f"Command: {' '.join(cmd)}\n\n")
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                
                # Read output in real-time
                for line in process.stdout:
                    output_text.insert(tk.END, line)
                    output_text.see(tk.END)
                    output_text.update()
                
                process.wait()
                
                if process.returncode == 0:
                    output_text.insert(tk.END, "\nRepair completed successfully!")
                else:
                    output_text.insert(tk.END, "\nRepair completed with errors!")
                
            except Exception as e:
                output_text.insert(tk.END, f"\nError during repair: {str(e)}")
        
        # Create control buttons
        button_frame = ttk.Frame(repair_window)
        button_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(button_frame, text="Start Repair", 
                  command=run_repair).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Close", 
                  command=repair_window.destroy).pack(side='right', padx=5)

class PartitionDialog:
    """Dialog for creating new partition"""
    def __init__(self, parent, disk_name):
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Create New Partition")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Create form
        ttk.Label(self.dialog, text="Partition Type:").pack(pady=5)
        self.type_var = tk.StringVar(value="primary")
        ttk.Radiobutton(self.dialog, text="Primary", 
                       variable=self.type_var, 
                       value="primary").pack()
        ttk.Radiobutton(self.dialog, text="Logical", 
                       variable=self.type_var, 
                       value="logical").pack()
        
        ttk.Label(self.dialog, text="Filesystem Type:").pack(pady=5)
        self.fs_var = tk.StringVar(value="ext4")
        fs_types = ['ext4', 'ext3', 'ext2', 'ntfs', 'fat32']
        ttk.Combobox(self.dialog, textvariable=self.fs_var, 
                    values=fs_types).pack()
        
        ttk.Label(self.dialog, text="Start (MB):").pack(pady=5)
        self.start_var = tk.StringVar()
        ttk.Entry(self.dialog, textvariable=self.start_var).pack()
        
        ttk.Label(self.dialog, text="End (MB):").pack(pady=5)
        self.end_var = tk.StringVar()
        ttk.Entry(self.dialog, textvariable=self.end_var).pack()
        
        ttk.Label(self.dialog, text="Partition Number:").pack(pady=5)
        self.number_var = tk.StringVar()
        ttk.Entry(self.dialog, textvariable=self.number_var).pack()
        
        # Create buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', pady=20)
        
        ttk.Button(button_frame, text="Create", 
                  command=self.on_create).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=self.dialog.destroy).pack(side='right', padx=5)
        
        # Wait for dialog to close
        self.dialog.wait_window()

    def on_create(self):
        """Handle create button click"""
        try:
            self.result = {
                'type': self.type_var.get(),
                'fs_type': self.fs_var.get(),
                'start': float(self.start_var.get()),
                'end': float(self.end_var.get()),
                'number': int(self.number_var.get())
            }
            self.dialog.destroy()
        except ValueError as e:
            messagebox.showerror("Error", "Please enter valid numbers")

class FormatDialog:
    """Dialog for formatting partition"""
    def __init__(self, parent, partition_name):
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Format Partition {partition_name}")
        self.dialog.geometry("400x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Create form
        ttk.Label(self.dialog, text="Filesystem Type:").pack(pady=5)
        self.fs_var = tk.StringVar(value="ext4")
        fs_types = ['ext4', 'ext3', 'ext2', 'ntfs', 'fat32']
        ttk.Combobox(self.dialog, textvariable=self.fs_var, 
                    values=fs_types).pack()
        
        ttk.Label(self.dialog, text="Label (optional):").pack(pady=5)
        self.label_var = tk.StringVar()
        ttk.Entry(self.dialog, textvariable=self.label_var).pack()
        
        # Create buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', pady=20)
        
        ttk.Button(button_frame, text="Format", 
                  command=self.on_format).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=self.dialog.destroy).pack(side='right', padx=5)
        
        # Wait for dialog to close
        self.dialog.wait_window()

    def on_format(self):
        """Handle format button click"""
        if messagebox.askyesno("Confirm Format", 
                             "Are you sure you want to format this partition? "
                             "All data will be lost!"):
            self.result = {
                'fs_type': self.fs_var.get(),
                'label': self.label_var.get()
            }
            self.dialog.destroy()