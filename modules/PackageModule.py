# Part 2: Package Management Module
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
import sys
import apt
import apt_pkg
from pathlib import Path
import datetime

class PackageModule:
    def __init__(self, parent_notebook):
        # Create package management tab
        self.package_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.package_frame, text='Package Management')
        
        # Create main display area
        self.output = scrolledtext.ScrolledText(self.package_frame, height=20)
        self.output.pack(padx=5, pady=5, fill='both', expand=True)
        
        # Create control panels
        self.create_control_panel()
        
        # Initialize apt cache
        self.cache = None
        self.init_apt_cache()

    def create_control_panel(self):
        # Main control panel
        control_frame = ttk.Frame(self.package_frame)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        # Scan and Diagnostics section
        scan_frame = ttk.LabelFrame(control_frame, text="Diagnostics")
        scan_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(scan_frame, text="Scan for Issues", 
                  command=self.scan_packages).pack(side='left', padx=5)
        ttk.Button(scan_frame, text="Check Dependencies", 
                  command=self.check_dependencies).pack(side='left', padx=5)
        
        # Repair section
        repair_frame = ttk.LabelFrame(control_frame, text="Repair Options")
        repair_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(repair_frame, text="Fix Broken Packages", 
                  command=self.fix_broken_packages).pack(side='left', padx=5)
        ttk.Button(repair_frame, text="Reconfigure Packages", 
                  command=self.reconfigure_packages).pack(side='left', padx=5)
        ttk.Button(repair_frame, text="Clean Package Cache", 
                  command=self.clean_package_cache).pack(side='left', padx=5)

    def init_apt_cache(self):
        try:
            self.cache = apt.Cache()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize APT cache: {str(e)}")

    def run_command(self, command, shell=False):
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

    def scan_packages(self):
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return

        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, "=== Starting Package Scan ===\n\n")
        
        # Check dpkg status
        self.output.insert(tk.END, "Checking dpkg status...\n")
        output, error, code = self.run_command("dpkg --audit")
        if code == 0 and not output.strip():
            self.output.insert(tk.END, "No package integrity issues found.\n")
        else:
            self.output.insert(tk.END, f"Issues found:\n{output}\n{error}\n")
        
        # Check for broken packages
        self.output.insert(tk.END, "\nChecking for broken packages...\n")
        output, error, code = self.run_command("apt-get check")
        if code == 0:
            self.output.insert(tk.END, "No broken packages found.\n")
        else:
            self.output.insert(tk.END, f"Broken packages found:\n{error}\n")
        
        # Check for held packages
        self.output.insert(tk.END, "\nChecking for held packages...\n")
        output, error, _ = self.run_command("apt-mark showhold")
        if output.strip():
            self.output.insert(tk.END, f"Held packages:\n{output}\n")
        else:
            self.output.insert(tk.END, "No held packages found.\n")

    def check_dependencies(self):
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return

        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, "=== Checking Package Dependencies ===\n\n")
        
        # Update package cache
        self.output.insert(tk.END, "Updating package cache...\n")
        output, error, code = self.run_command("apt-get update")
        if code != 0:
            self.output.insert(tk.END, f"Error updating cache:\n{error}\n")
            return
        
        # Check for missing dependencies
        self.output.insert(tk.END, "\nChecking for missing dependencies...\n")
        output, error, code = self.run_command("apt-get --dry-run -f install")
        if "0 upgraded, 0 newly installed" in output:
            self.output.insert(tk.END, "No missing dependencies found.\n")
        else:
            self.output.insert(tk.END, f"Dependencies need fixing:\n{output}\n")

    def fix_broken_packages(self):
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return

        if messagebox.askyesno("Confirm", "This will attempt to fix broken packages. Continue?"):
            self.output.delete(1.0, tk.END)
            self.output.insert(tk.END, "=== Fixing Broken Packages ===\n\n")
            
            # First, try dpkg configure
            self.output.insert(tk.END, "Configuring unconfigured packages...\n")
            output, error, _ = self.run_command("dpkg --configure -a")
            self.output.insert(tk.END, output + error + "\n")
            
            # Then, fix missing dependencies
            self.output.insert(tk.END, "Fixing dependencies...\n")
            output, error, _ = self.run_command("apt-get -f install")
            self.output.insert(tk.END, output + error + "\n")
            
            # Finally, try to resolve any remaining issues
            self.output.insert(tk.END, "Running final checks...\n")
            output, error, code = self.run_command("apt-get check")
            if code == 0:
                self.output.insert(tk.END, "All package issues resolved.\n")
            else:
                self.output.insert(tk.END, "Some issues remain. Manual intervention may be required.\n")

    def reconfigure_packages(self):
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return

        # Get list of packages that need reconfiguration
        output, error, _ = self.run_command("dpkg -l | grep '^rc'")
        packages_to_reconfigure = []
        
        if output:
            lines = output.splitlines()
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    packages_to_reconfigure.append(parts[1])
        
        if packages_to_reconfigure:
            if messagebox.askyesno("Confirm", 
                                 f"Found {len(packages_to_reconfigure)} packages to reconfigure. Continue?"):
                self.output.delete(1.0, tk.END)
                self.output.insert(tk.END, "=== Reconfiguring Packages ===\n\n")
                
                for package in packages_to_reconfigure:
                    self.output.insert(tk.END, f"Reconfiguring {package}...\n")
                    output, error, _ = self.run_command(f"dpkg-reconfigure {package}")
                    self.output.insert(tk.END, output + error + "\n")
        else:
            messagebox.showinfo("Info", "No packages need reconfiguration")

    def clean_package_cache(self):
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return

        if messagebox.askyesno("Confirm", "This will clean the package cache. Continue?"):
            self.output.delete(1.0, tk.END)
            self.output.insert(tk.END, "=== Cleaning Package Cache ===\n\n")
            
            # Clean apt cache
            self.output.insert(tk.END, "Cleaning APT cache...\n")
            output, error, _ = self.run_command("apt-get clean")
            self.output.insert(tk.END, output + error + "\n")
            
            # Remove old downloaded archive files
            self.output.insert(tk.END, "Removing old archive files...\n")
            output, error, _ = self.run_command("apt-get autoclean")
            self.output.insert(tk.END, output + error + "\n")
            
            # Remove automatically installed packages that are no longer needed
            self.output.insert(tk.END, "Removing unused packages...\n")
            output, error, _ = self.run_command("apt-get autoremove")
            self.output.insert(tk.END, output + error + "\n")