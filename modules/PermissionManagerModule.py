# Part 14: Permission Manager Module
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
import stat
import pwd
import grp
from pathlib import Path
from typing import Dict, List, Tuple, Set
import re

class PermissionManagerModule:
    def __init__(self, parent_notebook):
        # Create permission manager tab
        self.perm_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.perm_frame, text='Permission Manager')
        
        # Initialize variables
        self.system_paths = {
            '/bin': {'mode': 0o755, 'user': 'root', 'group': 'root'},
            '/sbin': {'mode': 0o755, 'user': 'root', 'group': 'root'},
            '/usr/bin': {'mode': 0o755, 'user': 'root', 'group': 'root'},
            '/usr/sbin': {'mode': 0o755, 'user': 'root', 'group': 'root'},
            '/etc': {'mode': 0o755, 'user': 'root', 'group': 'root'},
            '/home': {'mode': 0o755, 'user': 'root', 'group': 'root'},
            '/var': {'mode': 0o755, 'user': 'root', 'group': 'root'},
            '/tmp': {'mode': 0o1777, 'user': 'root', 'group': 'root'},
            '/var/tmp': {'mode': 0o1777, 'user': 'root', 'group': 'root'},
            '/root': {'mode': 0o700, 'user': 'root', 'group': 'root'},
            '/etc/shadow': {'mode': 0o640, 'user': 'root', 'group': 'shadow'},
            '/etc/gshadow': {'mode': 0o640, 'user': 'root', 'group': 'shadow'},
            '/etc/passwd': {'mode': 0o644, 'user': 'root', 'group': 'root'},
            '/etc/group': {'mode': 0o644, 'user': 'root', 'group': 'root'},
            '/var/log': {'mode': 0o755, 'user': 'root', 'group': 'root'}
        }
        
        # Special file patterns that need specific permissions
        self.special_patterns = {
            r'/etc/.*\.conf$': {'mode': 0o644, 'user': 'root', 'group': 'root'},
            r'/etc/cron\.d/.*': {'mode': 0o644, 'user': 'root', 'group': 'root'},
            r'/etc/cron\.(daily|weekly|monthly)/.*': {'mode': 0o755, 'user': 'root', 'group': 'root'},
            r'/usr/local/bin/.*': {'mode': 0o755, 'user': 'root', 'group': 'root'},
            r'/var/log/.*\.log$': {'mode': 0o640, 'user': 'root', 'group': 'adm'}
        }
        
        # Create interface
        self.create_interface()
        
    def create_interface(self):
        # Main container
        main_container = ttk.Frame(self.perm_frame)
        main_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Control panel
        control_frame = ttk.LabelFrame(main_container, text="Permission Management")
        control_frame.pack(fill='x', padx=5, pady=5)
        
        # Scan buttons
        scan_frame = ttk.Frame(control_frame)
        scan_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(scan_frame, text="Scan System Permissions",
                  command=self.scan_system_permissions).pack(side='left', padx=5)
        
        ttk.Button(scan_frame, text="Scan User Permissions",
                  command=self.scan_user_permissions).pack(side='left', padx=5)
        
        ttk.Button(scan_frame, text="Quick Fix Common Issues",
                  command=self.quick_fix_permissions).pack(side='left', padx=5)
        
        # Fix buttons
        fix_frame = ttk.Frame(control_frame)
        fix_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(fix_frame, text="Fix System Permissions",
                  command=self.fix_system_permissions).pack(side='left', padx=5)
        
        ttk.Button(fix_frame, text="Fix User Permissions",
                  command=self.fix_user_permissions).pack(side='left', padx=5)
        
        ttk.Button(fix_frame, text="Fix SUID/SGID",
                  command=self.fix_suid_sgid).pack(side='left', padx=5)
        
        # Results view
        results_frame = ttk.LabelFrame(main_container, text="Permission Issues")
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.results_tree = ttk.Treeview(results_frame,
                                       columns=('path', 'current', 'expected', 'issue'),
                                       show='headings')
        
        self.results_tree.heading('path', text='Path')
        self.results_tree.heading('current', text='Current')
        self.results_tree.heading('expected', text='Expected')
        self.results_tree.heading('issue', text='Issue')
        
        # Scrollbars for results
        y_scroll = ttk.Scrollbar(results_frame, orient='vertical',
                               command=self.results_tree.yview)
        x_scroll = ttk.Scrollbar(results_frame, orient='horizontal',
                               command=self.results_tree.xview)
        
        self.results_tree.configure(yscrollcommand=y_scroll.set,
                                  xscrollcommand=x_scroll.set)
        
        # Pack results view
        self.results_tree.pack(side='left', fill='both', expand=True)
        y_scroll.pack(side='right', fill='y')
        x_scroll.pack(side='bottom', fill='x')
        
        # Output area
        self.output = scrolledtext.ScrolledText(main_container, height=10)
        self.output.pack(fill='both', expand=True, padx=5, pady=5)

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

    def scan_system_permissions(self):
        """Scan system paths for permission issues"""
        self.clear_results()
        self.update_output("Scanning system permissions...\n")
        
        for path, expected in self.system_paths.items():
            if os.path.exists(path):
                try:
                    stat_info = os.stat(path)
                    current_mode = stat.S_IMODE(stat_info.st_mode)
                    current_user = pwd.getpwuid(stat_info.st_uid).pw_name
                    current_group = grp.getgrgid(stat_info.st_gid).gr_name
                    
                    issues = []
                    
                    # Check mode
                    if current_mode != expected['mode']:
                        issues.append("Mode mismatch")
                    
                    # Check owner
                    if current_user != expected['user']:
                        issues.append("Owner mismatch")
                    
                    # Check group
                    if current_group != expected['group']:
                        issues.append("Group mismatch")
                    
                    if issues:
                        current = f"{oct(current_mode)} {current_user}:{current_group}"
                        expected_str = f"{oct(expected['mode'])} {expected['user']}:{expected['group']}"
                        self.add_result(path, current, expected_str, ", ".join(issues))
                
                except Exception as e:
                    self.update_output(f"Error checking {path}: {str(e)}\n")
        
        self.update_output("System permission scan complete.\n")

    def scan_user_permissions(self):
        """Scan user home directories for permission issues"""
        self.clear_results()
        self.update_output("Scanning user permissions...\n")
        
        try:
            # Get all user home directories
            with open('/etc/passwd', 'r') as f:
                for line in f:
                    if not line.startswith('#'):
                        fields = line.strip().split(':')
                        if len(fields) >= 6:
                            username = fields[0]
                            home_dir = fields[5]
                            
                            if os.path.exists(home_dir):
                                # Check home directory permissions
                                stat_info = os.stat(home_dir)
                                current_mode = stat.S_IMODE(stat_info.st_mode)
                                current_user = pwd.getpwuid(stat_info.st_uid).pw_name
                                current_group = grp.getgrgid(stat_info.st_gid).gr_name
                                
                                # Expected permissions for home directory
                                expected_mode = 0o755 if username == 'root' else 0o700
                                
                                if (current_mode != expected_mode or 
                                    current_user != username):
                                    current = f"{oct(current_mode)} {current_user}:{current_group}"
                                    expected = f"{oct(expected_mode)} {username}:{username}"
                                    self.add_result(home_dir, current, expected,
                                                  "Incorrect home directory permissions")
                                
                                # Check .ssh directory if exists
                                ssh_dir = os.path.join(home_dir, '.ssh')
                                if os.path.exists(ssh_dir):
                                    stat_info = os.stat(ssh_dir)
                                    current_mode = stat.S_IMODE(stat_info.st_mode)
                                    
                                    if current_mode != 0o700:
                                        current = f"{oct(current_mode)} {current_user}:{current_group}"
                                        expected = f"0o700 {username}:{username}"
                                        self.add_result(ssh_dir, current, expected,
                                                      "Incorrect .ssh directory permissions")
        
        except Exception as e:
            self.update_output(f"Error scanning user permissions: {str(e)}\n")
        
        self.update_output("User permission scan complete.\n")

    def quick_fix_permissions(self):
        """Quick fix for common permission issues"""
        if messagebox.askyesno("Confirm", "Run quick fix for common permission issues?"):
            try:
                # Fix /tmp permissions
                self.run_command("sudo chmod 1777 /tmp")
                
                # Fix /var/tmp permissions
                self.run_command("sudo chmod 1777 /var/tmp")
                
                # Fix shadow file permissions
                self.run_command("sudo chmod 640 /etc/shadow")
                self.run_command("sudo chmod 640 /etc/gshadow")
                
                # Fix passwd and group file permissions
                self.run_command("sudo chmod 644 /etc/passwd")
                self.run_command("sudo chmod 644 /etc/group")
                
                # Fix home directory permissions
                self.run_command("sudo chmod 755 /home")
                
                # Fix /var/log permissions
                self.run_command("sudo chmod 755 /var/log")
                
                messagebox.showinfo("Success", "Quick fix completed")
                self.scan_system_permissions()
                
            except Exception as e:
                self.update_output(f"Error during quick fix: {str(e)}\n")
                messagebox.showerror("Error", f"Quick fix failed: {str(e)}")

    def fix_system_permissions(self):
        """Fix system permission issues"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "No items selected")
            return
        
        if messagebox.askyesno("Confirm", "Fix selected permission issues?"):
            for item in selection:
                values = self.results_tree.item(item)['values']
                path = values[0]
                expected = values[2]
                
                try:
                    # Parse expected permissions
                    mode_str, owner_str = expected.split(' ')
                    mode = int(mode_str, 8)
                    user, group = owner_str.split(':')
                    
                    # Fix permissions
                    os.chmod(path, mode)
                    self.run_command(f"sudo chown {user}:{group} {path}")
                    
                    self.update_output(f"Fixed permissions for {path}\n")
                    
                except Exception as e:
                    self.update_output(f"Error fixing {path}: {str(e)}\n")
            
            # Refresh scan
            self.scan_system_permissions()

    def fix_user_permissions(self):
        """Fix user permission issues"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "No items selected")
            return
        
        if messagebox.askyesno("Confirm", "Fix selected user permission issues?"):
            for item in selection:
                values = self.results_tree.item(item)['values']
                path = values[0]
                expected = values[2]
                
                try:
                    # Parse expected permissions
                    mode_str, owner_str = expected.split(' ')
                    mode = int(mode_str, 8)
                    user, group = owner_str.split(':')
                    
                    # Fix permissions
                    os.chmod(path, mode)
                    self.run_command(f"sudo chown {user}:{group} {path}")
                    
                    self.update_output(f"Fixed permissions for {path}\n")
                    
                except Exception as e:
                    self.update_output(f"Error fixing {path}: {str(e)}\n")
            
            # Refresh scan
            self.scan_user_permissions()

    def fix_suid_sgid(self):
        """Fix SUID/SGID permissions"""
        self.update_output("Scanning for inappropriate SUID/SGID bits...\n")
        
        # Known legitimate SUID/SGID files
        legitimate_suid = {
            '/usr/bin/sudo',
            '/usr/bin/passwd',
            '/usr/bin/chfn',
            '/usr/bin/chsh',
            '/usr/bin/gpasswd',
            '/usr/bin/newgrp',
            '/bin/su',
            '/bin/mount',
            '/bin/umount',
            '/usr/bin/pkexec'
        }
        
        try:
            # Find all SUID/SGID files
            output, _, _ = self.run_command(
                "find / -type f \( -perm -4000 -o -perm -2000 \) 2>/dev/null"
            )
            
            suspicious_files = []
            for file_path in output.splitlines():
                if file_path not in legitimate_suid:
                    suspicious_files.append(file_path)
            
            if suspicious_files:
                # Add to results tree
                for file_path in suspicious_files:
                    try:
                        stat_info = os.stat(file_path)
                        current_mode = stat.S_IMODE(stat_info.st_mode)
                        current_user = pwd.getpwuid(stat_info.st_uid).pw_name
                        current_group = grp.getgrgid(stat_info.st_gid).gr_name
                        
                        # Remove SUID/SGID bits for expected mode
                        expected_mode = current_mode & ~(stat.S_ISUID | stat.S_ISGID)
                        
                        current = f"{oct(current_mode)} {current_user}:{current_group}"
                        expected = f"{oct(expected_mode)} {current_user}:{current_group}"
                        
                        self.add_result(file_path, current, expected,
                                      "Suspicious SUID/SGID bit")
                        
                    except Exception as e:
                        self.update_output(f"Error checking {file_path}: {str(e)}\n")
                
                if messagebox.askyesno("Suspicious SUID/SGID",
                                     f"Found {len(suspicious_files)} files with "
                                     f"suspicious SUID/SGID bits. Remove these bits?"):
                    for file_path in suspicious_files:
                        try:
                            # Remove SUID/SGID bits
                            current_mode = os.stat(file_path).st_mode
                            new_mode = current_mode & ~(stat.S_ISUID | stat.S_ISGID)
                            os.chmod(file_path, new_mode)
                            
                            self.update_output(f"Removed SUID/SGID bits from {file_path}\n")
                            
                        except Exception as e:
                            self.update_output(
                                f"Error removing SUID/SGID bits from {file_path}: {str(e)}\n"
                            )
            else:
                self.update_output("No suspicious SUID/SGID files found.\n")
                messagebox.showinfo("Info", "No suspicious SUID/SGID files found")
        
        except Exception as e:
            self.update_output(f"Error scanning SUID/SGID: {str(e)}\n")
            messagebox.showerror("Error", f"SUID/SGID scan failed: {str(e)}")

    def check_special_patterns(self):
        """Check files matching special patterns"""
        self.update_output("Checking special file patterns...\n")
        
        for pattern, expected in self.special_patterns.items():
            try:
                # Find files matching pattern
                command = f"find / -type f -regex '{pattern}' 2>/dev/null"
                output, _, _ = self.run_command(command, shell=True)
                
                for file_path in output.splitlines():
                    try:
                        stat_info = os.stat(file_path)
                        current_mode = stat.S_IMODE(stat_info.st_mode)
                        current_user = pwd.getpwuid(stat_info.st_uid).pw_name
                        current_group = grp.getgrgid(stat_info.st_gid).gr_name
                        
                        if (current_mode != expected['mode'] or
                            current_user != expected['user'] or
                            current_group != expected['group']):
                            
                            current = f"{oct(current_mode)} {current_user}:{current_group}"
                            expected_str = f"{oct(expected['mode'])} {expected['user']}:{expected['group']}"
                            
                            self.add_result(file_path, current, expected_str,
                                          "Pattern-specific permission mismatch")
                    
                    except Exception as e:
                        self.update_output(f"Error checking {file_path}: {str(e)}\n")
            
            except Exception as e:
                self.update_output(f"Error processing pattern {pattern}: {str(e)}\n")

    def clear_results(self):
        """Clear results tree"""
        self.results_tree.delete(*self.results_tree.get_children())

    def add_result(self, path: str, current: str, expected: str, issue: str):
        """Add result to tree"""
        self.results_tree.insert('', 'end', values=(path, current, expected, issue))

    def update_output(self, message: str):
        """Update output text"""
        self.output.insert(tk.END, message)
        self.output.see(tk.END)

    def verify_home_permissions(self):
        """Verify and fix home directory permissions"""
        self.update_output("Verifying home directory permissions...\n")
        
        try:
            # Get all users
            users = [entry.name for entry in os.scandir('/home')]
            
            for username in users:
                home_dir = f"/home/{username}"
                if os.path.isdir(home_dir):
                    try:
                        stat_info = os.stat(home_dir)
                        current_mode = stat.S_IMODE(stat_info.st_mode)
                        current_user = pwd.getpwuid(stat_info.st_uid).pw_name
                        current_group = grp.getgrgid(stat_info.st_gid).gr_name
                        
                        # Check if permissions are correct (700 for user homes)
                        if current_mode != 0o700 or current_user != username:
                            if messagebox.askyesno("Fix Home Permissions",
                                                 f"Fix permissions for {home_dir}?"):
                                os.chmod(home_dir, 0o700)
                                self.run_command(f"sudo chown {username}:{username} {home_dir}")
                                self.update_output(f"Fixed permissions for {home_dir}\n")
                    
                    except Exception as e:
                        self.update_output(f"Error processing {home_dir}: {str(e)}\n")
        
        except Exception as e:
            self.update_output(f"Error verifying home permissions: {str(e)}\n")

    def check_world_writable(self):
        """Check for world-writable files and directories"""
        self.update_output("Checking for world-writable files...\n")
        
        try:
            # Find world-writable files
            output, _, _ = self.run_command(
                "find / -type f -perm -002 ! -path '/proc/*' ! -path '/sys/*' 2>/dev/null"
            )
            
            for file_path in output.splitlines():
                try:
                    stat_info = os.stat(file_path)
                    current_mode = stat.S_IMODE(stat_info.st_mode)
                    current_user = pwd.getpwuid(stat_info.st_uid).pw_name
                    current_group = grp.getgrgid(stat_info.st_gid).gr_name
                    
                    # Remove world-writable bit for expected mode
                    expected_mode = current_mode & ~0o002
                    
                    current = f"{oct(current_mode)} {current_user}:{current_group}"
                    expected = f"{oct(expected_mode)} {current_user}:{current_group}"
                    
                    self.add_result(file_path, current, expected,
                                  "World-writable file")
                
                except Exception as e:
                    self.update_output(f"Error checking {file_path}: {str(e)}\n")
        
        except Exception as e:
            self.update_output(f"Error checking world-writable files: {str(e)}\n")

    def fix_all_permissions(self):
        """Fix all detected permission issues"""
        if not self.results_tree.get_children():
            messagebox.showinfo("Info", "No permission issues detected")
            return
        
        if messagebox.askyesno("Confirm", "Fix all detected permission issues?"):
            for item in self.results_tree.get_children():
                values = self.results_tree.item(item)['values']
                path = values[0]
                expected = values[2]
                
                try:
                    # Parse expected permissions
                    mode_str, owner_str = expected.split(' ')
                    mode = int(mode_str, 8)
                    user, group = owner_str.split(':')
                    
                    # Fix permissions
                    os.chmod(path, mode)
                    self.run_command(f"sudo chown {user}:{group} {path}")
                    
                    self.update_output(f"Fixed permissions for {path}\n")
                    
                except Exception as e:
                    self.update_output(f"Error fixing {path}: {str(e)}\n")
            
            # Refresh scans
            self.scan_system_permissions()
            self.scan_user_permissions()