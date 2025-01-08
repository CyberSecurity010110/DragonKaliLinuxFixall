# Part 1: Imports and Base Setup
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
import sys
import pwd
import grp
import re
from pathlib import Path
import shutil
import datetime
import socket
import netifaces
import psutil

class NetworkModule:
    def __init__(self, parent_notebook):
        # Create network tab
        self.network_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.network_frame, text='Network')
        
        # Create main display area
        self.output = scrolledtext.ScrolledText(self.network_frame, height=20)
        self.output.pack(padx=5, pady=5, fill='both', expand=True)
        
        # Create control panel
        self.create_control_panel()
        
        # Initialize status variables
        self.interfaces = {}
        self.services = [
            'NetworkManager',
            'wpa_supplicant',
            'bluetooth',
            'ssh',
            'networking'
        ]

    def create_control_panel(self):
        # Button panel
        btn_frame = ttk.Frame(self.network_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        # Scan section
        scan_frame = ttk.LabelFrame(btn_frame, text="Diagnostics")
        scan_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(scan_frame, text="Full Network Scan", 
                  command=self.full_network_scan).pack(side='left', padx=5)
        ttk.Button(scan_frame, text="Quick Status Check", 
                  command=self.quick_status_check).pack(side='left', padx=5)
        
        # Service control section
        service_frame = ttk.LabelFrame(btn_frame, text="Service Control")
        service_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(service_frame, text="Restart NetworkManager", 
                  command=lambda: self.restart_service('NetworkManager')).pack(side='left', padx=5)
        ttk.Button(service_frame, text="Restart All Services", 
                  command=self.restart_all_services).pack(side='left', padx=5)

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

    def full_network_scan(self):
        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, "=== Starting Full Network Scan ===\n\n")
        
        # Check physical interfaces
        self.scan_physical_interfaces()
        
        # Check wireless interfaces
        self.scan_wireless_interfaces()
        
        # Check network services
        self.scan_network_services()
        
        # Check connectivity
        self.check_connectivity()
        
        # Check DNS
        self.check_dns()
        
        self.output.insert(tk.END, "\n=== Network Scan Complete ===\n")

    def scan_physical_interfaces(self):
        self.output.insert(tk.END, "Checking Physical Interfaces:\n")
        
        # Get all network interfaces
        interfaces = netifaces.interfaces()
        
        for iface in interfaces:
            try:
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:  # Has IPv4
                    ip = addrs[netifaces.AF_INET][0]['addr']
                    self.output.insert(tk.END, f"\n{iface}:\n")
                    self.output.insert(tk.END, f"  IP: {ip}\n")
                    
                    # Get interface status
                    output, _, _ = self.run_command(f"ip link show {iface}")
                    if "UP" in output:
                        self.output.insert(tk.END, "  Status: UP\n")
                    else:
                        self.output.insert(tk.END, "  Status: DOWN\n")
                        
            except Exception as e:
                self.output.insert(tk.END, f"  Error checking {iface}: {str(e)}\n")

    def scan_wireless_interfaces(self):
        self.output.insert(tk.END, "\nChecking Wireless Interfaces:\n")
        
        output, error, code = self.run_command("iwconfig")
        if code == 0:
            self.output.insert(tk.END, output)
        else:
            self.output.insert(tk.END, f"Error checking wireless interfaces: {error}\n")

    def scan_network_services(self):
        self.output.insert(tk.END, "\nChecking Network Services:\n")
        
        for service in self.services:
            output, error, code = self.run_command(f"systemctl status {service}")
            status = "Running" if code == 0 else "Stopped/Error"
            self.output.insert(tk.END, f"{service}: {status}\n")

    def check_connectivity(self):
        self.output.insert(tk.END, "\nChecking Internet Connectivity:\n")
        
        # Test local network
        gateway = netifaces.gateways()['default'].get(netifaces.AF_INET)
        if gateway:
            output, _, code = self.run_command(f"ping -c 1 {gateway[0]}")
            if code == 0:
                self.output.insert(tk.END, "Local Network: Connected\n")
            else:
                self.output.insert(tk.END, "Local Network: Failed\n")
        
        # Test internet connectivity
        output, _, code = self.run_command("ping -c 1 8.8.8.8")
        if code == 0:
            self.output.insert(tk.END, "Internet Connectivity: Connected\n")
        else:
            self.output.insert(tk.END, "Internet Connectivity: Failed\n")

    def check_dns(self):
        self.output.insert(tk.END, "\nChecking DNS Resolution:\n")
        
        try:
            socket.gethostbyname("www.google.com")
            self.output.insert(tk.END, "DNS Resolution: Working\n")
        except:
            self.output.insert(tk.END, "DNS Resolution: Failed\n")

    def restart_service(self, service_name):
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return
            
        self.output.insert(tk.END, f"\nRestarting {service_name}...\n")
        output, error, code = self.run_command(f"systemctl restart {service_name}")
        
        if code == 0:
            self.output.insert(tk.END, f"{service_name} restarted successfully\n")
        else:
            self.output.insert(tk.END, f"Error restarting {service_name}: {error}\n")

    def restart_all_services(self):
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return
            
        self.output.insert(tk.END, "\nRestarting all network services...\n")
        
        for service in self.services:
            self.restart_service(service)

    def quick_status_check(self):
        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, "=== Quick Network Status Check ===\n\n")
        
        # Check main interface status
        default_iface = netifaces.gateways()['default'].get(netifaces.AF_INET, [None])[1]
        if default_iface:
            self.output.insert(tk.END, f"Main Interface: {default_iface}\n")
            
            # Get IP address
            addrs = netifaces.ifaddresses(default_iface)
            if netifaces.AF_INET in addrs:
                ip = addrs[netifaces.AF_INET][0]['addr']
                self.output.insert(tk.END, f"IP Address: {ip}\n")
        
        # Quick connectivity test
        output, _, code = self.run_command("ping -c 1 8.8.8.8")
        status = "Connected" if code == 0 else "Disconnected"
        self.output.insert(tk.END, f"Internet Status: {status}\n")
        
        # NetworkManager status
        output, _, code = self.run_command("systemctl is-active NetworkManager")
        status = "Running" if code == 0 else "Stopped"
        self.output.insert(tk.END, f"NetworkManager: {status}\n")