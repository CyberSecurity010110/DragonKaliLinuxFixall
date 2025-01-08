#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import logging
from datetime import datetime

# Import all modules
from NetworkModule import NetworkModule
from PackageModule import PackageModule
from UserManagementModule import UserManagementModule
from PowerManagementModule import PowerManagementModule
from KernelManagementModule import KernelManagementModule
from NvidiaGPUModule import NvidiaGPUModule
from SystemLogsModule import SystemLogsModule
from PartitionManagementModule import PartitionManagementModule
from MountManagementModule import MountManagementModule
from ShellConfigModule import ShellConfigModule
from SystemFileCorruptionModule import SystemFileCorruptionModule
from BackupModule import BackupModule
from DesktopManagerModule import DesktopManagerModule
from PermissionManagerModule import PermissionManagerModule
from ServicesManagementModule import ServicesManagementModule
from LinuxHeadersModule import LinuxHeadersModule
from FlashDriveModule import FlashDriveModule
from DeviceManagementModule import DeviceManagementModule
from SystemInformationModule import SystemInformationModule
from TweaksModule import TweaksModule

class KaliLinuxFixAll:
    def __init__(self):
        # Check if running as root
        if os.geteuid() != 0:
            messagebox.showerror("Error", "This program must be run as root (sudo)")
            sys.exit(1)

        # Setup logging
        self.setup_logging()

        # Create main window
        self.root = tk.Tk()
        self.root.title("Kali Linux Fix All")
        self.root.geometry("1024x768")
        
        # Set icon if available
        try:
            self.root.iconbitmap("kali_icon.ico")
        except:
            pass

        # Create main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill='both', expand=True)

        # Create menu bar
        self.create_menu()

        # Create notebook for modules
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Initialize modules
        self.initialize_modules()

        # Create status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Bind events
        self.bind_events()

    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = "/var/log/kali-fix-all"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        log_file = f"{log_dir}/kali-fix-all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("KaliFixAll")

    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save Log", command=self.save_log)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_application)
        menubar.add_cascade(label="File", menu=file_menu)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Check System", command=self.check_system)
        tools_menu.add_command(label="System Backup", command=self.system_backup)
        tools_menu.add_command(label="Fix Common Issues", command=self.fix_common_issues)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def initialize_modules(self):
        """Initialize all modules"""
        try:
            self.modules = {
                'Network': NetworkModule(self.notebook),
                'Package Management': PackageModule(self.notebook),
                'User Management': UserManagementModule(self.notebook),
                'Power Management': PowerManagementModule(self.notebook),
                'Kernel Management': KernelManagementModule(self.notebook),
                'NVIDIA GPU': NvidiaGPUModule(self.notebook),
                'System Logs': SystemLogsModule(self.notebook),
                'Partition Management': PartitionManagementModule(self.notebook),
                'Mount Management': MountManagementModule(self.notebook),
                'Shell Configuration': ShellConfigModule(self.notebook),
                'System File Check': SystemFileCorruptionModule(self.notebook),
                'Backup': BackupModule(self.notebook),
                'Desktop Manager': DesktopManagerModule(self.notebook),
                'Permission Manager': PermissionManagerModule(self.notebook),
                'Services Management': ServicesManagementModule(self.notebook),
                'Linux Headers': LinuxHeadersModule(self.notebook),
                'Flash Drive': FlashDriveModule(self.notebook),
                'Device Management': DeviceManagementModule(self.notebook),
                'System Information': SystemInformationModule(self.notebook),
                'Tweaks': TweaksModule(self.notebook)
            }
            self.logger.info("All modules initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing modules: {str(e)}")
            messagebox.showerror("Error", f"Failed to initialize modules: {str(e)}")

    def bind_events(self):
        """Bind various events"""
        self.root.protocol("WM_DELETE_WINDOW", self.quit_application)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def on_tab_changed(self, event):
        """Handle tab change events"""
        current_tab = self.notebook.select()
        tab_text = self.notebook.tab(current_tab, "text")
        self.status_bar.config(text=f"Current module: {tab_text}")
        self.logger.info(f"Switched to module: {tab_text}")

    def save_log(self):
        """Save current session log"""
        try:
            filename = f"kali-fix-all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            with open(filename, 'w') as f:
                # Get logs from logging handler
                for handler in self.logger.handlers:
                    if isinstance(handler, logging.FileHandler):
                        with open(handler.baseFilename, 'r') as log_file:
                            f.write(log_file.read())
            messagebox.showinfo("Success", f"Log saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving log: {str(e)}")
            messagebox.showerror("Error", f"Failed to save log: {str(e)}")

    def check_system(self):
        """Perform system check across all modules"""
        try:
            self.logger.info("Starting system check...")
            issues = []
            
            for name, module in self.modules.items():
                if hasattr(module, 'check_status'):
                    module_issues = module.check_status()
                    if module_issues:
                        issues.extend([f"[{name}] {issue}" for issue in module_issues])

            if issues:
                result = "System Check Results:\n\n" + "\n".join(issues)
                messagebox.showwarning("System Check", result)
            else:
                messagebox.showinfo("System Check", "No issues found")
            
            self.logger.info("System check completed")
        except Exception as e:
            self.logger.error(f"Error during system check: {str(e)}")
            messagebox.showerror("Error", f"System check failed: {str(e)}")

    def system_backup(self):
        """Quick access to backup module"""
        self.notebook.select(self.notebook.children[list(self.notebook.children.keys())[11]])

    def fix_common_issues(self):
        """Attempt to fix common system issues"""
        if messagebox.askyesno("Confirm", "Attempt to fix common system issues?"):
            try:
                self.logger.info("Starting common issues fix...")
                fixed = []
                
                # Run fix methods from relevant modules
                for name, module in self.modules.items():
                    if hasattr(module, 'fix_common_issues'):
                        result = module.fix_common_issues()
                        if result:
                            fixed.extend([f"[{name}] {fix}" for fix in result])

                if fixed:
                    result = "Fixed Issues:\n\n" + "\n".join(fixed)
                    messagebox.showinfo("Fix Results", result)
                else:
                    messagebox.showinfo("Fix Results", "No issues fixed")
                
                self.logger.info("Common issues fix completed")
            except Exception as e:
                self.logger.error(f"Error fixing common issues: {str(e)}")
                messagebox.showerror("Error", f"Failed to fix issues: {str(e)}")

    def show_documentation(self):
        """Show program documentation"""
        doc_text = """
Kali Linux Fix All - System Maintenance and Repair Tool

This tool provides a comprehensive set of utilities for maintaining,
repairing, and optimizing your Kali Linux system.

Modules:
- Network Management
- Package Management
- User Management
- Power Management
- Kernel Management
- NVIDIA GPU Management
- System Logs
- Partition Management
- Mount Management
- Shell Configuration
- System File Check
- Backup
- Desktop Manager
- Permission Manager
- Services Management
- Linux Headers
- Flash Drive
- Device Management
- System Information
- Tweaks

For detailed documentation, visit:
https://github.com/yourusername/kali-linux-fix-all
"""
        doc_window = tk.Toplevel(self.root)
        doc_window.title("Documentation")
        doc_window.geometry("600x400")
        
        text_widget = tk.Text(doc_window, wrap=tk.WORD)
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', doc_text)
        text_widget.config(state='disabled')

    def show_about(self):
        """Show about dialog"""
        about_text = """
Kali Linux Fix All v1.0

A comprehensive system maintenance and repair tool
for Kali Linux systems.

Created by: Your Name
License: GPL v3
"""
        messagebox.showinfo("About", about_text)

    def quit_application(self):
        """Clean up and quit application"""
        if messagebox.askyesno("Quit", "Are you sure you want to quit?"):
            self.logger.info("Application shutting down...")
            try:
                # Cleanup modules
                for module in self.modules.values():
                    if hasattr(module, '__del__'):
                        module.__del__()
            except:
                pass
            self.root.quit()

def main():
    try:
        app = KaliLinuxFixAll()
        app.root.mainloop()
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        messagebox.showerror("Fatal Error", f"Application failed to start: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()