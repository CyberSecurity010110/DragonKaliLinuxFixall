# Part 16: Linux Headers Management Module
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
from typing import Dict, List, Tuple, Set
import re
from datetime import datetime

class LinuxHeadersModule:
    def __init__(self, parent_notebook):
        # Create Linux Headers tab
        self.headers_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.headers_frame, text='Linux Headers')
        
        # Initialize variables
        self.current_kernel = None
        self.installed_headers = []
        self.recommended_headers = []
        self.problematic_headers = []
        
        # Create interface
        self.create_interface()
        
        # Initial scan
        self.scan_headers()

    def create_interface(self):
        # Main container
        main_container = ttk.Frame(self.headers_frame)
        main_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Left panel - Headers list
        left_panel = ttk.Frame(main_container)
        left_panel.pack(side='left', fill='both', expand=True, padx=5)
        
        # Headers list with tabs
        self.notebook = ttk.Notebook(left_panel)
        self.notebook.pack(fill='both', expand=True)
        
        # Installed headers tab
        installed_frame = ttk.Frame(self.notebook)
        self.notebook.add(installed_frame, text='Installed Headers')
        
        # Create treeview for installed headers
        self.installed_tree = ttk.Treeview(installed_frame,
                                         columns=('version', 'status', 'size'),
                                         show='headings')
        self.installed_tree.heading('version', text='Version')
        self.installed_tree.heading('status', text='Status')
        self.installed_tree.heading('size', text='Size')
        
        # Scrollbars for installed headers
        installed_y_scroll = ttk.Scrollbar(installed_frame, orient='vertical',
                                         command=self.installed_tree.yview)
        installed_x_scroll = ttk.Scrollbar(installed_frame, orient='horizontal',
                                         command=self.installed_tree.xview)
        
        self.installed_tree.configure(yscrollcommand=installed_y_scroll.set,
                                    xscrollcommand=installed_x_scroll.set)
        
        # Pack installed headers view
        self.installed_tree.pack(side='left', fill='both', expand=True)
        installed_y_scroll.pack(side='right', fill='y')
        installed_x_scroll.pack(side='bottom', fill='x')
        
        # Available headers tab
        available_frame = ttk.Frame(self.notebook)
        self.notebook.add(available_frame, text='Available Headers')
        
        # Create treeview for available headers
        self.available_tree = ttk.Treeview(available_frame,
                                         columns=('version', 'status'),
                                         show='headings')
        self.available_tree.heading('version', text='Version')
        self.available_tree.heading('status', text='Status')
        
        # Scrollbars for available headers
        available_y_scroll = ttk.Scrollbar(available_frame, orient='vertical',
                                         command=self.available_tree.yview)
        available_x_scroll = ttk.Scrollbar(available_frame, orient='horizontal',
                                         command=self.available_tree.xview)
        
        self.available_tree.configure(yscrollcommand=available_y_scroll.set,
                                    xscrollcommand=available_x_scroll.set)
        
        # Pack available headers view
        self.available_tree.pack(side='left', fill='both', expand=True)
        available_y_scroll.pack(side='right', fill='y')
        available_x_scroll.pack(side='bottom', fill='x')
        
        # Right panel - Controls and details
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side='right', fill='both', padx=5)
        
        # System information
        info_frame = ttk.LabelFrame(right_panel, text="System Information")
        info_frame.pack(fill='x', pady=5)
        
        self.kernel_label = ttk.Label(info_frame, text="Current Kernel: Scanning...")
        self.kernel_label.pack(fill='x', padx=5, pady=2)
        
        self.headers_label = ttk.Label(info_frame, text="Installed Headers: Scanning...")
        self.headers_label.pack(fill='x', padx=5, pady=2)
        
        # Control buttons
        control_frame = ttk.LabelFrame(right_panel, text="Header Controls")
        control_frame.pack(fill='x', pady=5)
        
        ttk.Button(control_frame, text="Scan Headers",
                  command=self.scan_headers).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(control_frame, text="Install Selected Headers",
                  command=self.install_selected_headers).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(control_frame, text="Remove Selected Headers",
                  command=self.remove_selected_headers).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(control_frame, text="Update Headers",
                  command=self.update_headers).pack(fill='x', padx=5, pady=2)
        
        # Quick actions
        action_frame = ttk.LabelFrame(right_panel, text="Quick Actions")
        action_frame.pack(fill='x', pady=5)
        
        ttk.Button(action_frame, text="Fix Missing Headers",
                  command=self.fix_missing_headers).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(action_frame, text="Clean Old Headers",
                  command=self.clean_old_headers).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(action_frame, text="Optimize Headers",
                  command=self.optimize_headers).pack(fill='x', padx=5, pady=2)
        
        # Details area
        details_frame = ttk.LabelFrame(right_panel, text="Details")
        details_frame.pack(fill='both', expand=True, pady=5)
        
        self.details_text = scrolledtext.ScrolledText(details_frame, height=10)
        self.details_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Bind selection events
        self.installed_tree.bind('<<TreeviewSelect>>', self.show_header_details)
        self.available_tree.bind('<<TreeviewSelect>>', self.show_header_details)

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

    def scan_headers(self):
        """Scan system for installed and available headers"""
        self.update_details("Scanning system headers...\n")
        
        try:
            # Get current kernel version
            output, _, _ = self.run_command("uname -r")
            self.current_kernel = output.strip()
            self.kernel_label.config(text=f"Current Kernel: {self.current_kernel}")
            
            # Clear existing items
            self.installed_tree.delete(*self.installed_tree.get_children())
            self.available_tree.delete(*self.available_tree.get_children())
            
            # Get installed headers
            output, _, _ = self.run_command("dpkg -l | grep linux-headers")
            self.installed_headers = []
            
            for line in output.splitlines():
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        version = parts[2].replace('linux-headers-', '')
                        status = parts[0]
                        
                        # Get size information
                        size_output, _, _ = self.run_command(
                            f"dpkg-query -W -f='${{Installed-Size}}' {parts[2]}"
                        )
                        size = f"{int(size_output.strip())/1024:.1f} MB"
                        
                        self.installed_headers.append(version)
                        self.installed_tree.insert('', 'end',
                                                 values=(version, status, size))
            
            self.headers_label.config(
                text=f"Installed Headers: {len(self.installed_headers)}"
            )
            
            # Get available headers
            output, _, _ = self.run_command("apt-cache search linux-headers")
            
            for line in output.splitlines():
                if 'linux-headers-' in line:
                    parts = line.split(' - ')
                    if len(parts) >= 2:
                        version = parts[0].replace('linux-headers-', '')
                        status = "Available"
                        
                        if version not in self.installed_headers:
                            self.available_tree.insert('', 'end',
                                                     values=(version, status))
            
            self.check_header_issues()
            self.update_details("Header scan completed.\n")
            
        except Exception as e:
            self.update_details(f"Error scanning headers: {str(e)}\n")
            messagebox.showerror("Error", f"Failed to scan headers: {str(e)}")

    def check_header_issues(self):
        """Check for potential header issues"""
        self.problematic_headers = []
        self.recommended_headers = []
        
        try:
            # Check if current kernel headers are installed
            current_headers = f"linux-headers-{self.current_kernel}"
            if current_headers not in self.installed_headers:
                self.recommended_headers.append(current_headers)
                self.update_details(
                    f"WARNING: Headers for current kernel {self.current_kernel} "
                    f"are not installed.\n"
                )
            
            # Check for very old headers
            kernel_versions = []
            for header in self.installed_headers:
                match = re.search(r'(\d+\.\d+\.\d+)', header)
                if match:
                    kernel_versions.append(match.group(1))
            
            if kernel_versions:
                kernel_versions.sort(reverse=True)
                latest_version = kernel_versions[0]
                
                for version in kernel_versions:
                    if self.version_difference(latest_version, version) > 2:
                        old_header = f"linux-headers-{version}"
                        self.problematic_headers.append(old_header)
            
            # Check for broken header installations
            output, _, _ = self.run_command("dpkg -l | grep linux-headers")
            for line in output.splitlines():
                if line.startswith('rc') or line.startswith('iU'):
                    parts = line.split()
                    if len(parts) >= 2:
                        self.problematic_headers.append(parts[1])
            
            if self.problematic_headers:
                self.update_details(
                    "Found problematic headers that should be removed:\n" +
                    "\n".join(self.problematic_headers) + "\n"
                )
            
            if self.recommended_headers:
                self.update_details(
                    "Recommended headers to install:\n" +
                    "\n".join(self.recommended_headers) + "\n"
                )
            
        except Exception as e:
            self.update_details(f"Error checking header issues: {str(e)}\n")

    def version_difference(self, ver1: str, ver2: str) -> float:
        """Calculate the difference between two version numbers"""
        try:
            v1_parts = [int(x) for x in ver1.split('.')]
            v2_parts = [int(x) for x in ver2.split('.')]
            
            v1 = v1_parts[0] + v1_parts[1]/100 + v1_parts[2]/10000
            v2 = v2_parts[0] + v2_parts[1]/100 + v2_parts[2]/10000
            
            return abs(v1 - v2)
        except:
            return 0

    def install_selected_headers(self):
        """Install selected headers"""
        selection = self.available_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "No headers selected for installation")
            return
        
        headers_to_install = []
        for item in selection:
            version = self.available_tree.item(item)['values'][0]
            headers_to_install.append(f"linux-headers-{version}")
        
        if messagebox.askyesno("Confirm",
                              f"Install the following headers?\n" +
                              "\n".join(headers_to_install)):
            try:
                for header in headers_to_install:
                    self.update_details(f"Installing {header}...\n")
                    output, error, code = self.run_command(f"sudo apt-get install -y {header}")
                    
                    if code == 0:
                        self.update_details(f"Successfully installed {header}\n")
                    else:
                        self.update_details(f"Failed to install {header}: {error}\n")
                
                self.scan_headers()
                
            except Exception as e:
                self.update_details(f"Error during installation: {str(e)}\n")
                messagebox.showerror("Error", f"Installation failed: {str(e)}")

    def remove_selected_headers(self):
        """Remove selected headers"""
        selection = self.installed_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "No headers selected for removal")
            return
        
        headers_to_remove = []
        for item in selection:
            version = self.installed_tree.item(item)['values'][0]
            headers_to_remove.append(f"linux-headers-{version}")
        
        # Check if trying to remove current kernel headers
        current_headers = f"linux-headers-{self.current_kernel}"
        if current_headers in headers_to_remove:
            if not messagebox.askyesno("Warning",
                                     "You are attempting to remove headers for your "
                                     "current kernel. This is not recommended. Continue?"):
                return
        
        if messagebox.askyesno("Confirm",
                              f"Remove the following headers?\n" +
                              "\n".join(headers_to_remove)):
            try:
                for header in headers_to_remove:
                    self.update_details(f"Removing {header}...\n")
                    output, error, code = self.run_command(
                        f"sudo apt-get remove -y {header}"
                    )
                    
                    if code == 0:
                        self.update_details(f"Successfully removed {header}\n")
                    else:
                        self.update_details(f"Failed to remove {header}: {error}\n")
                
                # Clean up
                self.run_command("sudo apt-get autoremove -y")
                self.run_command("sudo apt-get autoclean")
                
                self.scan_headers()
                
            except Exception as e:
                self.update_details(f"Error during removal: {str(e)}\n")
                messagebox.showerror("Error", f"Removal failed: {str(e)}")

    def update_headers(self):
        """Update all installed headers"""
        if messagebox.askyesno("Confirm", "Update all installed headers?"):
            try:
                self.update_details("Updating package lists...\n")
                output, error, code = self.run_command("sudo apt-get update")
                if code != 0:
                    raise Exception(f"Failed to update package lists: {error}")
                
                self.update_details("Upgrading headers...\n")
                output, error, code = self.run_command(
                    "sudo apt-get upgrade -y linux-headers-*"
                )
                if code == 0:
                    self.update_details("Headers updated successfully.\n")
                else:
                    self.update_details(f"Error updating headers: {error}\n")
                
                self.scan_headers()
                
            except Exception as e:
                self.update_details(f"Error during update: {str(e)}\n")
                messagebox.showerror("Error", f"Update failed: {str(e)}")

    def fix_missing_headers(self):
        """Fix missing or broken header installations"""
        try:
            self.update_details("Checking for missing headers...\n")
            
            # Check for current kernel headers
            current_headers = f"linux-headers-{self.current_kernel}"
            if current_headers not in self.installed_headers:
                if messagebox.askyesno("Fix Headers",
                                     f"Install headers for current kernel "
                                     f"({self.current_kernel})?"):
                    output, error, code = self.run_command(
                        f"sudo apt-get install -y {current_headers}"
                    )
                    if code == 0:
                        self.update_details(
                            f"Successfully installed {current_headers}\n"
                        )
                    else:
                        self.update_details(
                            f"Failed to install {current_headers}: {error}\n"
                        )
            
            # Fix broken installations
            self.update_details("Checking for broken installations...\n")
            output, error, code = self.run_command(
                "sudo dpkg --configure -a"
            )
            
            # Fix dependencies
            self.update_details("Fixing dependencies...\n")
            output, error, code = self.run_command(
                "sudo apt-get install -f -y"
            )
            
            # Clean up
            self.update_details("Cleaning up...\n")
            self.run_command("sudo apt-get autoremove -y")
            self.run_command("sudo apt-get autoclean")
            
            self.scan_headers()
            self.update_details("Header fixes completed.\n")
            
        except Exception as e:
            self.update_details(f"Error fixing headers: {str(e)}\n")
            messagebox.showerror("Error", f"Fix operation failed: {str(e)}")

    def clean_old_headers(self):
        """Remove old and unused headers"""
        try:
            self.update_details("Identifying old headers...\n")
            
            # Get list of installed kernels
            output, _, _ = self.run_command("dpkg --list | grep linux-image")
            installed_kernels = []
            for line in output.splitlines():
                if line.startswith('ii'):
                    parts = line.split()
                    if len(parts) >= 2:
                        kernel = parts[1].replace('linux-image-', '')
                        installed_kernels.append(kernel)
            
            # Identify headers to remove
            headers_to_remove = []
            for header in self.installed_headers:
                if header not in installed_kernels and \
                   f"linux-headers-{self.current_kernel}" not in header:
                    headers_to_remove.append(f"linux-headers-{header}")
            
            if headers_to_remove:
                if messagebox.askyesno("Clean Headers",
                                     f"Remove the following old headers?\n" +
                                     "\n".join(headers_to_remove)):
                    for header in headers_to_remove:
                        self.update_details(f"Removing {header}...\n")
                        output, error, code = self.run_command(
                            f"sudo apt-get remove -y {header}"
                        )
                        if code == 0:
                            self.update_details(f"Successfully removed {header}\n")
                        else:
                            self.update_details(f"Failed to remove {header}: {error}\n")
                    
                    # Clean up
                    self.run_command("sudo apt-get autoremove -y")
                    self.run_command("sudo apt-get autoclean")
            else:
                self.update_details("No old headers found to remove.\n")
            
            self.scan_headers()
            
        except Exception as e:
            self.update_details(f"Error cleaning headers: {str(e)}\n")
            messagebox.showerror("Error", f"Clean operation failed: {str(e)}")

    def optimize_headers(self):
        """Optimize header installations"""
        try:
            self.update_details("Optimizing headers...\n")
            
            # Fix any broken installations
            self.update_details("Fixing broken installations...\n")
            self.run_command("sudo dpkg --configure -a")
            
            # Update package lists
            self.update_details("Updating package lists...\n")
            self.run_command("sudo apt-get update")
            
            # Fix dependencies
            self.update_details("Fixing dependencies...\n")
            self.run_command("sudo apt-get install -f -y")
            
            # Remove unnecessary headers
            self.update_details("Removing unnecessary headers...\n")
            self.run_command("sudo apt-get autoremove -y")
            
            # Clean package cache
            self.update_details("Cleaning package cache...\n")
            self.run_command("sudo apt-get autoclean")
            
            # Update DKMS modules if present
            if os.path.exists("/usr/sbin/dkms"):
                self.update_details("Updating DKMS modules...\n")
                self.run_command("sudo dkms autoinstall")
            
            self.scan_headers()
            self.update_details("Header optimization completed.\n")
            
        except Exception as e:
            self.update_details(f"Error optimizing headers: {str(e)}\n")
            messagebox.showerror("Error", f"Optimization failed: {str(e)}")

    def show_header_details(self, event):
        """Show detailed information about the selected header"""
        current_tab = self.notebook.select()
        
        if current_tab == self.notebook.tabs()[0]:  # Installed headers
            selection = self.installed_tree.selection()
            if selection:
                version = self.installed_tree.item(selection[0])['values'][0]
                header_package = f"linux-headers-{version}"
                
                try:
                    # Get package details
                    output, _, _ = self.run_command(
                        f"dpkg -s {header_package}"
                    )
                    
                    # Get file list
                    files_output, _, _ = self.run_command(
                        f"dpkg -L {header_package}"
                    )
                    
                    details = (f"=== Header Package Details: {header_package} ===\n\n"
                              f"{output}\n\n"
                              f"=== Installed Files ===\n\n"
                              f"{files_output}")
                    
                    self.update_details(details)
                    
                except Exception as e:
                    self.update_details(f"Error getting header details: {str(e)}")
        
        else:  # Available headers
            selection = self.available_tree.selection()
            if selection:
                version = self.available_tree.item(selection[0])['values'][0]
                header_package = f"linux-headers-{version}"
                
                try:
                    # Get package details
                    output, _, _ = self.run_command(
                        f"apt-cache show {header_package}"
                    )
                    
                    details = (f"=== Available Header Package Details ===\n\n"
                              f"{output}")
                    
                    self.update_details(details)
                    
                except Exception as e:
                    self.update_details(f"Error getting header details: {str(e)}")

    def update_details(self, message: str):
        """Update details text area"""
        self.details_text.delete('1.0', tk.END)
        self.details_text.insert(tk.END, message)
        self.details_text.see(tk.END)