# Part 15: Services Management Module
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
from typing import Dict, List, Tuple, Set
import json
from pathlib import Path
import time

class ServicesManagementModule:
    def __init__(self, parent_notebook):
        # Create services management tab
        self.services_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.services_frame, text='Services Manager')
        
        # Initialize variables
        self.essential_services = {
            'networking': 'Network connectivity',
            'ssh': 'SSH server',
            'postgresql': 'PostgreSQL Database (needed for Metasploit)',
            'apache2': 'Apache Web Server',
            'mysql': 'MySQL Database',
            'bluetooth': 'Bluetooth service',
            'cups': 'Printing system',
            'avahi-daemon': 'Service discovery',
            'NetworkManager': 'Network management',
            'systemd-resolved': 'DNS resolution',
            'ufw': 'Uncomplicated Firewall',
            'cron': 'Task scheduler',
            'rsyslog': 'System logging',
            'dbus': 'System message bus',
            'lightdm': 'Display manager'
        }
        
        # Services that should not run by default
        self.optional_services = {
            'tor': 'Tor anonymous network',
            'docker': 'Container service',
            'virtualbox': 'VirtualBox service',
            'cups': 'Printing service',
            'samba': 'Windows file sharing',
            'nfs-server': 'Network file system'
        }
        
        # Create interface
        self.create_interface()
        
        # Initial scan
        self.scan_services()

    def create_interface(self):
        # Main container
        main_container = ttk.Frame(self.services_frame)
        main_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Left panel - Service list
        left_panel = ttk.Frame(main_container)
        left_panel.pack(side='left', fill='both', expand=True, padx=5)
        
        # Service list with tabs
        self.notebook = ttk.Notebook(left_panel)
        self.notebook.pack(fill='both', expand=True)
        
        # All services tab
        all_frame = ttk.Frame(self.notebook)
        self.notebook.add(all_frame, text='All Services')
        
        # Create treeview for all services
        self.all_tree = ttk.Treeview(all_frame, columns=('name', 'status', 'description'),
                                    show='headings')
        self.all_tree.heading('name', text='Service Name')
        self.all_tree.heading('status', text='Status')
        self.all_tree.heading('description', text='Description')
        
        # Scrollbars for all services
        all_y_scroll = ttk.Scrollbar(all_frame, orient='vertical',
                                   command=self.all_tree.yview)
        all_x_scroll = ttk.Scrollbar(all_frame, orient='horizontal',
                                   command=self.all_tree.xview)
        
        self.all_tree.configure(yscrollcommand=all_y_scroll.set,
                              xscrollcommand=all_x_scroll.set)
        
        # Pack all services view
        self.all_tree.pack(side='left', fill='both', expand=True)
        all_y_scroll.pack(side='right', fill='y')
        all_x_scroll.pack(side='bottom', fill='x')
        
        # Essential services tab
        essential_frame = ttk.Frame(self.notebook)
        self.notebook.add(essential_frame, text='Essential Services')
        
        # Create treeview for essential services
        self.essential_tree = ttk.Treeview(essential_frame,
                                         columns=('name', 'status', 'description'),
                                         show='headings')
        self.essential_tree.heading('name', text='Service Name')
        self.essential_tree.heading('status', text='Status')
        self.essential_tree.heading('description', text='Description')
        
        # Scrollbars for essential services
        essential_y_scroll = ttk.Scrollbar(essential_frame, orient='vertical',
                                         command=self.essential_tree.yview)
        essential_x_scroll = ttk.Scrollbar(essential_frame, orient='horizontal',
                                         command=self.essential_tree.xview)
        
        self.essential_tree.configure(yscrollcommand=essential_y_scroll.set,
                                    xscrollcommand=essential_x_scroll.set)
        
        # Pack essential services view
        self.essential_tree.pack(side='left', fill='both', expand=True)
        essential_y_scroll.pack(side='right', fill='y')
        essential_x_scroll.pack(side='bottom', fill='x')
        
        # Right panel - Controls and details
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side='right', fill='both', padx=5)
        
        # Control buttons
        control_frame = ttk.LabelFrame(right_panel, text="Service Controls")
        control_frame.pack(fill='x', pady=5)
        
        ttk.Button(control_frame, text="Scan Services",
                  command=self.scan_services).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(control_frame, text="Start Selected",
                  command=self.start_selected_service).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(control_frame, text="Stop Selected",
                  command=self.stop_selected_service).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(control_frame, text="Restart Selected",
                  command=self.restart_selected_service).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(control_frame, text="Enable Selected",
                  command=self.enable_selected_service).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(control_frame, text="Disable Selected",
                  command=self.disable_selected_service).pack(fill='x', padx=5, pady=2)
        
        # Quick actions
        action_frame = ttk.LabelFrame(right_panel, text="Quick Actions")
        action_frame.pack(fill='x', pady=5)
        
        ttk.Button(action_frame, text="Fix Essential Services",
                  command=self.fix_essential_services).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(action_frame, text="Optimize Services",
                  command=self.optimize_services).pack(fill='x', padx=5, pady=2)
        
        ttk.Button(action_frame, text="Clean Service Status",
                  command=self.clean_service_status).pack(fill='x', padx=5, pady=2)
        
        # Service details
        details_frame = ttk.LabelFrame(right_panel, text="Service Details")
        details_frame.pack(fill='both', expand=True, pady=5)
        
        self.details_text = scrolledtext.ScrolledText(details_frame, height=10)
        self.details_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Bind selection events
        self.all_tree.bind('<<TreeviewSelect>>', self.show_service_details)
        self.essential_tree.bind('<<TreeviewSelect>>', self.show_service_details)

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

    def scan_services(self):
        """Scan all services and update the interface"""
        # Clear existing items
        self.all_tree.delete(*self.all_tree.get_children())
        self.essential_tree.delete(*self.essential_tree.get_children())
        
        try:
            # Get all services
            output, _, _ = self.run_command("systemctl list-units --type=service --all")
            
            for line in output.splitlines():
                if '.service' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        service_name = parts[0].replace('.service', '')
                        status = parts[2]
                        description = ' '.join(parts[4:])
                        
                        # Add to all services tree
                        self.all_tree.insert('', 'end',
                                           values=(service_name, status, description))
                        
                        # Add to essential services tree if applicable
                        if service_name in self.essential_services:
                            self.essential_tree.insert('', 'end',
                                                     values=(service_name, status,
                                                            self.essential_services[service_name]))
            
            self.update_details("Service scan completed successfully.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan services: {str(e)}")
            self.update_details(f"Error scanning services: {str(e)}")

    def get_selected_service(self) -> str:
        """Get the currently selected service name"""
        current_tab = self.notebook.select()
        if current_tab == self.notebook.tabs()[0]:  # All services tab
            selection = self.all_tree.selection()
        else:  # Essential services tab
            selection = self.essential_tree.selection()
            
        if selection:
            if current_tab == self.notebook.tabs()[0]:
                return self.all_tree.item(selection[0])['values'][0]
            else:
                return self.essential_tree.item(selection[0])['values'][0]
        return None

    def start_selected_service(self):
        """Start the selected service"""
        service = self.get_selected_service()
        if service:
            try:
                output, error, code = self.run_command(f"sudo systemctl start {service}")
                if code == 0:
                    self.update_details(f"Successfully started {service}")
                    self.scan_services()
                else:
                    self.update_details(f"Failed to start {service}: {error}")
            except Exception as e:
                self.update_details(f"Error starting {service}: {str(e)}")
        else:
            messagebox.showinfo("Info", "No service selected")

    def stop_selected_service(self):
        """Stop the selected service"""
        service = self.get_selected_service()
        if service:
            if service in self.essential_services:
                if not messagebox.askyesno("Warning",
                                         f"{service} is an essential service. "
                                         f"Are you sure you want to stop it?"):
                    return
            
            try:
                output, error, code = self.run_command(f"sudo systemctl stop {service}")
                if code == 0:
                    self.update_details(f"Successfully stopped {service}")
                    self.scan_services()
                else:
                    self.update_details(f"Failed to stop {service}: {error}")
            except Exception as e:
                self.update_details(f"Error stopping {service}: {str(e)}")
        else:
            messagebox.showinfo("Info", "No service selected")

    def restart_selected_service(self):
        """Restart the selected service"""
        service = self.get_selected_service()
        if service:
            try:
                output, error, code = self.run_command(f"sudo systemctl restart {service}")
                if code == 0:
                    self.update_details(f"Successfully restarted {service}")
                    self.scan_services()
                else:
                    self.update_details(f"Failed to restart {service}: {error}")
            except Exception as e:
                self.update_details(f"Error restarting {service}: {str(e)}")
        else:
            messagebox.showinfo("Info", "No service selected")

    def enable_selected_service(self):
        """Enable the selected service"""
        service = self.get_selected_service()
        if service:
            try:
                output, error, code = self.run_command(f"sudo systemctl enable {service}")
                if code == 0:
                    self.update_details(f"Successfully enabled {service}")
                    self.scan_services()
                else:
                    self.update_details(f"Failed to enable {service}: {error}")
            except Exception as e:
                self.update_details(f"Error enabling {service}: {str(e)}")
        else:
            messagebox.showinfo("Info", "No service selected")

    def disable_selected_service(self):
        """Disable the selected service"""
        service = self.get_selected_service()
        if service:
            if service in self.essential_services:
                if not messagebox.askyesno("Warning",
                                         f"{service} is an essential service. "
                                         f"Are you sure you want to disable it?"):
                    return
            
            try:
                output, error, code = self.run_command(f"sudo systemctl disable {service}")
                if code == 0:
                    self.update_details(f"Successfully disabled {service}")
                    self.scan_services()
                else:
                    self.update_details(f"Failed to disable {service}: {error}")
            except Exception as e:
                self.update_details(f"Error disabling {service}: {str(e)}")
        else:
            messagebox.showinfo("Info", "No service selected")

    def fix_essential_services(self):
        """Check and fix essential services"""
        if messagebox.askyesno("Confirm",
                              "This will check and attempt to fix all essential services. Continue?"):
            self.update_details("Checking essential services...\n")
            
            for service, description in self.essential_services.items():
                try:
                    # Check service status
                    output, _, code = self.run_command(f"systemctl is-active {service}")
                    
                    if "inactive" in output or "failed" in output:
                        self.update_details(f"Fixing {service}...\n")
                        
                        # Try to start the service
                        _, error, code = self.run_command(f"sudo systemctl start {service}")
                        if code == 0:
                            self.update_details(f"Successfully started {service}\n")
                        else:
                            # If start fails, try to fix common issues
                            self.fix_service_issues(service)
                    
                except Exception as e:
                    self.update_details(f"Error checking {service}: {str(e)}\n")
            
            self.scan_services()
            self.update_details("Essential services check completed.\n")

    def fix_service_issues(self, service: str):
        """Attempt to fix common service issues"""
        try:
            # Get service status for debugging
            output, _, _ = self.run_command(f"systemctl status {service}")
            self.update_details(f"Service status:\n{output}\n")
            
             # Reset failed state
            self.run_command(f"sudo systemctl reset-failed {service}")
            
            # Reload daemon
            self.run_command("sudo systemctl daemon-reload")
            
            # Check configuration
            _, error, code = self.run_command(f"sudo systemctl show {service}")
            if code != 0:
                self.update_details(f"Configuration error in {service}: {error}\n")
                
                # Try to reinstall the service package
                if messagebox.askyesno("Fix Service",
                                     f"Attempt to reinstall {service} package?"):
                    self.run_command(f"sudo apt-get install --reinstall {service}")
            
            # Check dependencies
            output, _, _ = self.run_command(f"systemctl list-dependencies {service}")
            for line in output.splitlines():
                if "failed" in line:
                    dep_service = line.split()[-1].replace('.service', '')
                    self.update_details(f"Fixing dependency {dep_service}...\n")
                    self.fix_service_issues(dep_service)
            
            # Final restart attempt
            _, error, code = self.run_command(f"sudo systemctl restart {service}")
            if code == 0:
                self.update_details(f"Successfully restarted {service}\n")
            else:
                self.update_details(f"Failed to restart {service}: {error}\n")
                
        except Exception as e:
            self.update_details(f"Error fixing {service}: {str(e)}\n")

    def optimize_services(self):
        """Optimize system services"""
        if messagebox.askyesno("Confirm",
                              "This will optimize system services. Continue?"):
            self.update_details("Optimizing services...\n")
            
            try:
                # Disable unnecessary services
                for service in self.optional_services:
                    output, _, _ = self.run_command(f"systemctl is-active {service}")
                    if "active" in output:
                        if messagebox.askyesno("Optimize",
                                             f"Stop optional service {service}?"):
                            self.run_command(f"sudo systemctl stop {service}")
                            self.run_command(f"sudo systemctl disable {service}")
                            self.update_details(f"Disabled {service}\n")
                
                # Clean up service files
                self.run_command("sudo systemctl daemon-reload")
                
                # Remove obsolete service files
                output, _, _ = self.run_command("systemctl list-unit-files --state=masked")
                for line in output.splitlines():
                    if '.service' in line:
                        service = line.split()[0]
                        if messagebox.askyesno("Optimize",
                                             f"Unmask service {service}?"):
                            self.run_command(f"sudo systemctl unmask {service}")
                            self.update_details(f"Unmasked {service}\n")
                
                self.scan_services()
                self.update_details("Service optimization completed.\n")
                
            except Exception as e:
                self.update_details(f"Error during optimization: {str(e)}\n")

    def clean_service_status(self):
        """Clean up service status and reset failed services"""
        if messagebox.askyesno("Confirm",
                              "This will clean up service status and reset failed services. Continue?"):
            self.update_details("Cleaning service status...\n")
            
            try:
                # Reset failed state for all services
                self.run_command("sudo systemctl reset-failed")
                
                # Reload systemd manager
                self.run_command("sudo systemctl daemon-reexec")
                
                # Clean up runtime directory
                self.run_command("sudo systemctl clean-runtime")
                
                # Reload all unit files
                self.run_command("sudo systemctl daemon-reload")
                
                self.scan_services()
                self.update_details("Service status cleanup completed.\n")
                
            except Exception as e:
                self.update_details(f"Error during status cleanup: {str(e)}\n")

    def show_service_details(self, event):
        """Show detailed information about the selected service"""
        service = self.get_selected_service()
        if service:
            try:
                # Get service details
                output, _, _ = self.run_command(f"systemctl status {service}")
                
                # Get service configuration
                config_output, _, _ = self.run_command(f"systemctl show {service}")
                
                # Get service dependencies
                dep_output, _, _ = self.run_command(f"systemctl list-dependencies {service}")
                
                details = (f"=== Service Details: {service} ===\n\n"
                          f"{output}\n\n"
                          f"=== Configuration ===\n\n"
                          f"{config_output}\n\n"
                          f"=== Dependencies ===\n\n"
                          f"{dep_output}")
                
                self.update_details(details)
                
            except Exception as e:
                self.update_details(f"Error getting service details: {str(e)}")

    def update_details(self, message: str):
        """Update details text area"""
        self.details_text.delete('1.0', tk.END)
        self.details_text.insert(tk.END, message)
        self.details_text.see(tk.END)

    def get_service_recommendations(self) -> Dict[str, str]:
        """Get service recommendations based on system state"""
        recommendations = {}
        
        try:
            # Check essential services
            for service, description in self.essential_services.items():
                output, _, _ = self.run_command(f"systemctl is-active {service}")
                if "inactive" in output or "failed" in output:
                    recommendations[service] = f"Essential service {service} is not running"
            
            # Check for conflicting services
            running_services = []
            output, _, _ = self.run_command("systemctl list-units --type=service --state=running")
            for line in output.splitlines():
                if '.service' in line:
                    running_services.append(line.split()[0].replace('.service', ''))
            
            # Check for known conflicts
            if 'apache2' in running_services and 'nginx' in running_services:
                recommendations['web_server'] = "Both Apache and Nginx are running"
            
            # Check for resource-intensive services
            for service in running_services:
                output, _, _ = self.run_command(f"systemctl status {service}")
                if "high-memory" in output.lower() or "high-cpu" in output.lower():
                    recommendations[service] = f"Service {service} is using high resources"
            
        except Exception as e:
            self.update_details(f"Error getting recommendations: {str(e)}\n")
        
        return recommendations

    def show_recommendations(self):
        """Show service recommendations"""
        recommendations = self.get_service_recommendations()
        
        if recommendations:
            message = "=== Service Recommendations ===\n\n"
            for service, recommendation in recommendations.items():
                message += f"• {service}: {recommendation}\n"
            
            self.update_details(message)
            
            if messagebox.askyesno("Recommendations",
                                 "Apply recommended fixes?"):
                self.apply_recommendations(recommendations)
        else:
            self.update_details("No service recommendations at this time.\n")

    def apply_recommendations(self, recommendations: Dict[str, str]):
        """Apply recommended fixes"""
        for service, _ in recommendations.items():
            try:
                if service in self.essential_services:
                    self.update_details(f"Fixing essential service {service}...\n")
                    self.fix_service_issues(service)
                elif service == 'web_server':
                    if messagebox.askyesno("Web Server Conflict",
                                         "Stop Nginx and keep Apache?"):
                        self.run_command("sudo systemctl stop nginx")
                        self.run_command("sudo systemctl disable nginx")
                    else:
                        self.run_command("sudo systemctl stop apache2")
                        self.run_command("sudo systemctl disable apache2")
                else:
                    self.update_details(f"Optimizing service {service}...\n")
                    self.run_command(f"sudo systemctl restart {service}")
            
            except Exception as e:
                self.update_details(f"Error applying fix for {service}: {str(e)}\n")
        
        self.scan_services()