# Part 11: System/File Corruption Scanner Module
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
from pathlib import Path
import hashlib
import time
import threading
from typing import Dict, List, Tuple

class SystemFileCorruptionModule:
    def __init__(self, parent_notebook):
        # Create corruption scanner tab
        self.corruption_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.corruption_frame, text='File Integrity')
        
        # Create main display area
        self.output = scrolledtext.ScrolledText(self.corruption_frame, height=20)
        self.output.pack(padx=5, pady=5, fill='both', expand=True)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.corruption_frame, 
                                          variable=self.progress_var,
                                          maximum=100)
        self.progress_bar.pack(fill='x', padx=5, pady=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self.corruption_frame, 
                                    textvariable=self.status_var)
        self.status_label.pack(pady=5)
        
        # Create control panel
        self.create_control_panel()
        
        # Initialize variables
        self.scan_thread = None
        self.stop_scan = False
        self.corrupted_files = []
        
    def create_control_panel(self):
        # Control panel
        control_frame = ttk.Frame(self.corruption_frame)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        # Scan options
        scan_frame = ttk.LabelFrame(control_frame, text="Scan Options")
        scan_frame.pack(fill='x', padx=5, pady=5)
        
        # Quick scan button
        ttk.Button(scan_frame, text="Quick System Scan",
                  command=self.quick_system_scan).pack(side='left', padx=5)
        
        # Deep scan button
        ttk.Button(scan_frame, text="Deep System Scan",
                  command=self.deep_system_scan).pack(side='left', padx=5)
        
        # Custom scan button
        ttk.Button(scan_frame, text="Custom Directory Scan",
                  command=self.custom_directory_scan).pack(side='left', padx=5)
        
        # Repair options
        repair_frame = ttk.LabelFrame(control_frame, text="Repair Options")
        repair_frame.pack(fill='x', padx=5, pady=5)
        
        # Auto repair button
        ttk.Button(repair_frame, text="Auto Repair",
                  command=self.auto_repair).pack(side='left', padx=5)
        
        # Manual repair button
        ttk.Button(repair_frame, text="Manual Repair",
                  command=self.manual_repair).pack(side='left', padx=5)
        
        # Stop button
        ttk.Button(repair_frame, text="Stop",
                  command=self.stop_current_operation).pack(side='right', padx=5)

    def quick_system_scan(self):
        """Perform a quick system scan focusing on critical system files"""
        self.start_scan_thread(self._quick_system_scan)

    def _quick_system_scan(self):
        """Implementation of quick system scan"""
        self.update_status("Starting quick system scan...")
        critical_paths = [
            '/boot',
            '/etc',
            '/bin',
            '/sbin',
            '/lib',
            '/lib64'
        ]
        
        total_files = self.count_files(critical_paths)
        scanned_files = 0
        
        for path in critical_paths:
            if self.stop_scan:
                break
                
            self.update_output(f"\nScanning {path}...\n")
            
            for root, _, files in os.walk(path):
                for file in files:
                    if self.stop_scan:
                        break
                        
                    full_path = os.path.join(root, file)
                    self.check_file_integrity(full_path)
                    
                    scanned_files += 1
                    progress = (scanned_files / total_files) * 100
                    self.update_progress(progress)
        
        self.scan_complete()

    def deep_system_scan(self):
        """Perform a deep system scan checking all files"""
        self.start_scan_thread(self._deep_system_scan)

    def _deep_system_scan(self):
        """Implementation of deep system scan"""
        self.update_status("Starting deep system scan...")
        
        # Get list of mounted filesystems
        output = subprocess.getoutput("df --type=ext4 --type=xfs --type=btrfs -h")
        mount_points = [line.split()[-1] for line in output.splitlines()[1:]]
        
        total_files = self.count_files(mount_points)
        scanned_files = 0
        
        for mount_point in mount_points:
            if self.stop_scan:
                break
                
            self.update_output(f"\nScanning {mount_point}...\n")
            
            for root, _, files in os.walk(mount_point):
                for file in files:
                    if self.stop_scan:
                        break
                        
                    full_path = os.path.join(root, file)
                    self.check_file_integrity(full_path)
                    
                    scanned_files += 1
                    progress = (scanned_files / total_files) * 100
                    self.update_progress(progress)
        
        self.scan_complete()

    def custom_directory_scan(self):
        """Open dialog to select directory for scanning"""
        from tkinter import filedialog
        
        directory = filedialog.askdirectory(title="Select Directory to Scan")
        if directory:
            self.start_scan_thread(lambda: self._custom_directory_scan(directory))

    def _custom_directory_scan(self, directory: str):
        """Implementation of custom directory scan"""
        self.update_status(f"Scanning directory: {directory}")
        
        total_files = self.count_files([directory])
        scanned_files = 0
        
        for root, _, files in os.walk(directory):
            if self.stop_scan:
                break
                
            for file in files:
                if self.stop_scan:
                    break
                    
                full_path = os.path.join(root, file)
                self.check_file_integrity(full_path)
                
                scanned_files += 1
                progress = (scanned_files / total_files) * 100
                self.update_progress(progress)
        
        self.scan_complete()

    def check_file_integrity(self, filepath: str):
        """Check integrity of a single file"""
        try:
            # Skip symbolic links
            if os.path.islink(filepath):
                return
            
            # Basic file checks
            if not os.path.exists(filepath):
                self.report_corruption(filepath, "File missing")
                return
            
            if os.path.getsize(filepath) == 0:
                self.report_corruption(filepath, "Empty file")
                return
            
            # Try to read the file
            try:
                with open(filepath, 'rb') as f:
                    # Read first and last block to check accessibility
                    f.read(4096)
                    f.seek(-4096, 2)
                    f.read()
            except IOError as e:
                self.report_corruption(filepath, f"Read error: {str(e)}")
                return
            
            # For binary files, check for executable corruption
            if os.access(filepath, os.X_OK):
                output = subprocess.getoutput(f"file {filepath}")
                if "corrupt" in output.lower():
                    self.report_corruption(filepath, "Corrupt binary")
                    return
            
            # For text files, check for encoding issues
            if filepath.endswith(('.txt', '.conf', '.log', '.py', '.sh')):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        f.read()
                except UnicodeDecodeError:
                    self.report_corruption(filepath, "Invalid encoding")
                    return
                
        except Exception as e:
            self.report_corruption(filepath, f"Check failed: {str(e)}")

    def report_corruption(self, filepath: str, reason: str):
        """Report corrupted file"""
        self.corrupted_files.append((filepath, reason))
        self.update_output(f"Corruption detected: {filepath}\nReason: {reason}\n\n")

    def auto_repair(self):
        """Attempt to automatically repair corrupted files"""
        if not self.corrupted_files:
            messagebox.showinfo("Info", "No corrupted files found to repair")
            return
        
        self.start_scan_thread(self._auto_repair)

    def _auto_repair(self):
        """Implementation of auto repair"""
        self.update_status("Starting auto repair...")
        total = len(self.corrupted_files)
        
        for i, (filepath, reason) in enumerate(self.corrupted_files):
            if self.stop_scan:
                break
                
            self.update_output(f"\nAttempting to repair: {filepath}\n")
            
            # Try different repair strategies based on the type of corruption
            if reason == "Empty file":
                self.remove_empty_file(filepath)
            elif reason == "Corrupt binary":
                self.reinstall_package_for_file(filepath)
            elif reason == "Invalid encoding":
                self.fix_encoding(filepath)
            else:
                self.update_output(f"No automatic repair available for: {filepath}\n")
            
            progress = ((i + 1) / total) * 100
            self.update_progress(progress)
        
        self.scan_complete()

    def manual_repair(self):
        """Show dialog for manual repair options"""
        if not self.corrupted_files:
            messagebox.showinfo("Info", "No corrupted files found to repair")
            return
        
        ManualRepairDialog(self.corruption_frame, self.corrupted_files)

    def remove_empty_file(self, filepath: str):
        """Remove empty file and recreate if necessary"""
        try:
            os.remove(filepath)
            self.update_output(f"Removed empty file: {filepath}\n")
            
            # If it's a critical system file, try to restore from package
            if any(filepath.startswith(p) for p in ['/bin', '/sbin', '/lib']):
                self.reinstall_package_for_file(filepath)
                
        except Exception as e:
            self.update_output(f"Failed to remove file: {str(e)}\n")

    def reinstall_package_for_file(self, filepath: str):
        """Attempt to reinstall package containing the file"""
        try:
            # Find package owning the file
            output = subprocess.getoutput(f"dpkg -S {filepath}")
            if ":" in output:
                package = output.split(":")[0]
                
                # Reinstall package
                cmd = f"apt-get install --reinstall {package}"
                subprocess.run(['sudo', 'bash', '-c', cmd], check=True)
                
                self.update_output(f"Reinstalled package {package} for {filepath}\n")
            else:
                self.update_output(f"No package found for {filepath}\n")
                
        except Exception as e:
            self.update_output(f"Failed to reinstall package: {str(e)}\n")

    def fix_encoding(self, filepath: str):
        """Attempt to fix file encoding"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin1', 'ascii']
            content = None
            
            for encoding in encodings:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content:
                # Backup original file
                backup_path = filepath + '.bak'
                shutil.copy2(filepath, backup_path)
                
                # Write with UTF-8 encoding
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.update_output(f"Fixed encoding for {filepath}\n")
            else:
                self.update_output(f"Could not determine encoding for {filepath}\n")
                
        except Exception as e:
            self.update_output(f"Failed to fix encoding: {str(e)}\n")

    def count_files(self, paths: List[str]) -> int:
        """Count total files in given paths"""
        total = 0
        for path in paths:
            for root, _, files in os.walk(path):
                total += len(files)
        return total

    def start_scan_thread(self, target):
        """Start a new scan thread"""
        if self.scan_thread and self.scan_thread.is_alive():
            messagebox.showinfo("Info", "A scan is already in progress")
            return
        
        self.stop_scan = False
        self.corrupted_files = []
        self.output.delete(1.0, tk.END)
        self.progress_var.set(0)
        
        self.scan_thread = threading.Thread(target=target)
        self.scan_thread.start()

    def stop_current_operation(self):
        """Stop current scan or repair operation"""
        self.stop_scan = True
        self.update_status("Stopping operation...")

    def scan_complete(self):
        """Handle scan completion"""
        if self.stop_scan:
            self.update_status("Operation stopped")
        else:
            self.update_status("Operation complete")
            
        self.progress_var.set(100)
        
        if self.corrupted_files:
            messagebox.showwarning(
                "Scan Complete",
                f"Found {len(self.corrupted_files)} corrupted files"
            )
        else:
            messagebox.showinfo("Scan Complete", "No corruptions found")

    def update_status(self, message: str):
        """Update status label"""
        self.status_var.set(message)

    def update_output(self, message: str):
        """Update output text"""
        self.output.insert(tk.END, message)
        self.output.see(tk.END)

    def update_progress(self, value: float):
        """Update progress bar"""
        self.progress_var.set(value)

class ManualRepairDialog:
    """Dialog for manual repair options"""
    def __init__(self, parent, corrupted_files):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Manual Repair")
        self.dialog.geometry("600x400")
        
        # Create file list
        self.create_file_list(corrupted_files)
        
        # Create repair options
        self.create_repair_options()
        
        # Create buttons
        self.create_buttons()
        
        self.dialog.wait_window()

    def create_file_list(self, corrupted_files):
        """Create list of corrupted files"""
        list_frame = ttk.LabelFrame(self.dialog, text="Corrupted Files")
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.file_list = ttk.Treeview(
            list_frame,
            columns=('path', 'reason'),
            show='headings'
        )
        
        self.file_list.heading('path', text='File Path')
        self.file_list.heading('reason', text='Issue')
        
        # Add scrollbars
        y_scroll = ttk.Scrollbar(list_frame, orient='vertical', 
                                command=self.file_list.yview)
        x_scroll = ttk.Scrollbar(list_frame, orient='horizontal', 
                                command=self.file_list.xview)
        
        self.file_list.configure(yscrollcommand=y_scroll.set, 
                               xscrollcommand=x_scroll.set)
        
        # Pack everything
        self.file_list.pack(side='left', fill='both', expand=True)
        y_scroll.pack(side='right', fill='y')
        x_scroll.pack(side='bottom', fill='x')
        
        # Populate list
        for filepath, reason in corrupted_files:
            self.file_list.insert('', 'end', values=(filepath, reason))

    def create_repair_options(self):
        """Create repair options panel"""
        options_frame = ttk.LabelFrame(self.dialog, text="Repair Options")
        options_frame.pack(fill='x', padx=5, pady=5)
        
        # Delete file option
        ttk.Button(options_frame, text="Delete File",
                  command=self.delete_file).pack(side='left', padx=5)
        
        # Restore from backup option
        ttk.Button(options_frame, text="Restore from Backup",
                  command=self.restore_from_backup).pack(side='left', padx=5)
        
        # Reinstall package option
        ttk.Button(options_frame, text="Reinstall Package",
                  command=self.reinstall_package).pack(side='left', padx=5)
        
        # View/Edit file option
        ttk.Button(options_frame, text="View/Edit File",
                  command=self.view_edit_file).pack(side='left', padx=5)

    def create_buttons(self):
        """Create dialog buttons"""
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(button_frame, text="Close",
                  command=self.dialog.destroy).pack(side='right', padx=5)
        
        ttk.Button(button_frame, text="Refresh",
                  command=self.refresh_list).pack(side='right', padx=5)

    def delete_file(self):
        """Delete selected file"""
        selection = self.file_list.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a file")
            return
        
        filepath = self.file_list.item(selection[0])['values'][0]
        
        if messagebox.askyesno("Confirm", f"Delete {filepath}?"):
            try:
                os.remove(filepath)
                self.file_list.delete(selection[0])
                messagebox.showinfo("Success", "File deleted")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete file: {str(e)}")

    def restore_from_backup(self):
        """Restore file from backup"""
        selection = self.file_list.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a file")
            return
        
        filepath = self.file_list.item(selection[0])['values'][0]
        backup_path = filepath + '.bak'
        
        if not os.path.exists(backup_path):
            messagebox.showerror("Error", "No backup file found")
            return
        
        if messagebox.askyesno("Confirm", f"Restore from {backup_path}?"):
            try:
                shutil.copy2(backup_path, filepath)
                messagebox.showinfo("Success", "File restored from backup")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to restore: {str(e)}")

    def reinstall_package(self):
        """Reinstall package containing selected file"""
        selection = self.file_list.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a file")
            return
        
        filepath = self.file_list.item(selection[0])['values'][0]
        
        try:
            # Find package owning the file
            output = subprocess.getoutput(f"dpkg -S {filepath}")
            if ":" in output:
                package = output.split(":")[0]
                
                if messagebox.askyesno("Confirm", 
                                     f"Reinstall package {package}?"):
                    # Reinstall package
                    cmd = f"apt-get install --reinstall {package}"
                    subprocess.run(['sudo', 'bash', '-c', cmd], check=True)
                    messagebox.showinfo("Success", "Package reinstalled")
            else:
                messagebox.showerror("Error", "No package found for this file")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reinstall: {str(e)}")

    def view_edit_file(self):
        """Open file in text editor"""
        selection = self.file_list.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a file")
            return
        
        filepath = self.file_list.item(selection[0])['values'][0]
        
        try:
            # Try to open with default text editor
            subprocess.Popen(['xdg-open', filepath])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")

    def refresh_list(self):
        """Refresh the file list"""
        # Re-check all files in the list
        for item in self.file_list.get_children():
            filepath = self.file_list.item(item)['values'][0]
            if not os.path.exists(filepath):
                self.file_list.delete(item)