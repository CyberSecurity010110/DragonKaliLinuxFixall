# Part 19: System Information Module
import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import os
import platform
import psutil
import distro
import json
from datetime import datetime
import shutil
from typing import Dict, List

class SystemInformationModule:
    def __init__(self, parent_notebook):
        # Create System Information tab
        self.sysinfo_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.sysinfo_frame, text='System Information')
        
        # Create interface
        self.create_interface()
        
        # Initial info gathering
        self.refresh_info()

    def create_interface(self):
        # Create main container
        main_container = ttk.Frame(self.sysinfo_frame)
        main_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create top button panel
        button_panel = ttk.Frame(main_container)
        button_panel.pack(fill='x', padx=5, pady=5)
        
        # Add refresh button
        ttk.Button(button_panel, text="Refresh Information",
                  command=self.refresh_info).pack(side='left', padx=5)
        
        # Add export button
        ttk.Button(button_panel, text="Export Information",
                  command=self.export_info).pack(side='left', padx=5)
        
        # Create notebook for categorized information
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create tabs for different categories
        self.tabs = {
            'Overview': scrolledtext.ScrolledText(self.notebook),
            'Hardware': scrolledtext.ScrolledText(self.notebook),
            'Operating System': scrolledtext.ScrolledText(self.notebook),
            'Network': scrolledtext.ScrolledText(self.notebook),
            'Storage': scrolledtext.ScrolledText(self.notebook),
            'Performance': scrolledtext.ScrolledText(self.notebook)
        }
        
        # Add tabs to notebook
        for name, text_widget in self.tabs.items():
            self.notebook.add(text_widget, text=name)

    def run_command(self, command: str, shell: bool = False) -> str:
        """Run system command and return output"""
        try:
            if shell:
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True)
            else:
                process = subprocess.Popen(command.split(), stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, text=True)
            output, _ = process.communicate()
            return output.strip()
        except Exception as e:
            return f"Error: {str(e)}"

    def get_system_overview(self) -> str:
        """Get general system overview"""
        info = []
        info.append("=== System Overview ===\n")
        
        # Basic system information
        info.append(f"Hostname: {platform.node()}")
        info.append(f"OS: {distro.name(pretty=True)}")
        info.append(f"Kernel: {platform.release()}")
        info.append(f"Architecture: {platform.machine()}")
        info.append(f"Python Version: {platform.python_version()}")
        
        # Uptime
        uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        info.append(f"System Uptime: {str(uptime).split('.')[0]}")
        
        # Current resource usage
        info.append(f"\nCPU Usage: {psutil.cpu_percent()}%")
        info.append(f"Memory Usage: {psutil.virtual_memory().percent}%")
        info.append(f"Swap Usage: {psutil.swap_memory().percent}%")
        
        return "\n".join(info)

    def get_hardware_info(self) -> str:
        """Get detailed hardware information"""
        info = []
        info.append("=== Hardware Information ===\n")
        
        # CPU Information
        info.append("=== CPU ===")
        cpu_info = self.run_command("lscpu")
        for line in cpu_info.split('\n'):
            if any(x in line for x in ['Model name', 'Architecture', 'CPU(s)',
                                      'Thread(s) per core', 'Core(s) per socket',
                                      'CPU MHz', 'Cache']):
                info.append(line.strip())
        
        # Memory Information
        info.append("\n=== Memory ===")
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        info.append(f"Total RAM: {self.bytes_to_human(mem.total)}")
        info.append(f"Available RAM: {self.bytes_to_human(mem.available)}")
        info.append(f"Used RAM: {self.bytes_to_human(mem.used)} ({mem.percent}%)")
        info.append(f"Total Swap: {self.bytes_to_human(swap.total)}")
        info.append(f"Used Swap: {self.bytes_to_human(swap.used)} ({swap.percent}%)")
        
        # GPU Information
        info.append("\n=== Graphics ===")
        gpu_info = self.run_command("lspci | grep -i vga")
        info.append(gpu_info)
        
        # Additional GPU details from glxinfo if available
        glx_info = self.run_command("glxinfo | grep -i 'renderer\\|vendor'")
        if glx_info and 'Error' not in glx_info:
            info.append(glx_info)
        
        # USB Devices
        info.append("\n=== USB Devices ===")
        usb_info = self.run_command("lsusb")
        info.append(usb_info)
        
        return "\n".join(info)

    def get_os_info(self) -> str:
        """Get detailed operating system information"""
        info = []
        info.append("=== Operating System Information ===\n")
        
        # Distribution information
        info.append("=== Distribution ===")
        info.append(f"Name: {distro.name(pretty=True)}")
        info.append(f"Version: {distro.version(pretty=True)}")
        info.append(f"Codename: {distro.codename()}")
        
        # Kernel information
        info.append("\n=== Kernel ===")
        info.append(f"Kernel Version: {platform.release()}")
        info.append(f"Kernel Build: {platform.version()}")
        
        # System language and locale
        info.append("\n=== Language & Locale ===")
        locale_info = self.run_command("locale | grep LANG")
        info.append(locale_info)
        
        # Installed packages
        info.append("\n=== Package Information ===")
        pkg_count = self.run_command("dpkg --get-selections | wc -l")
        info.append(f"Installed Packages: {pkg_count}")
        
        # Desktop environment
        info.append("\n=== Desktop Environment ===")
        desktop = os.environ.get('XDG_CURRENT_DESKTOP', 'Not detected')
        info.append(f"Current Desktop: {desktop}")
        
        # System services
        info.append("\n=== System Services ===")
        service_count = self.run_command("systemctl list-units --type=service --state=running | grep .service | wc -l")
        info.append(f"Running Services: {service_count}")
        
        return "\n".join(info)

    def get_network_info(self) -> str:
        """Get network information"""
        info = []
        info.append("=== Network Information ===\n")
        
        # Network interfaces
        info.append("=== Network Interfaces ===")
        for interface, addresses in psutil.net_if_addrs().items():
            info.append(f"\nInterface: {interface}")
            for addr in addresses:
                if addr.family == psutil.AF_LINK:
                    info.append(f"MAC Address: {addr.address}")
                elif addr.family == 2:  # IPv4
                    info.append(f"IPv4 Address: {addr.address}")
                elif addr.family == 10:  # IPv6
                    info.append(f"IPv6 Address: {addr.address}")
        
        # Network statistics
        info.append("\n=== Network Statistics ===")
        net_io = psutil.net_io_counters()
        info.append(f"Bytes Sent: {self.bytes_to_human(net_io.bytes_sent)}")
        info.append(f"Bytes Received: {self.bytes_to_human(net_io.bytes_recv)}")
        
        # Network connections
        info.append("\n=== Active Connections ===")
        connections = len(psutil.net_connections())
        info.append(f"Active Connections: {connections}")
        
        # DNS information
        info.append("\n=== DNS Configuration ===")
        dns_info = self.run_command("cat /etc/resolv.conf | grep nameserver")
        info.append(dns_info)
        
        return "\n".join(info)

    def get_storage_info(self) -> str:
        """Get storage information"""
        info = []
        info.append("=== Storage Information ===\n")
        
        # Disk partitions
        info.append("=== Disk Partitions ===")
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                info.append(f"\nDevice: {partition.device}")
                info.append(f"Mountpoint: {partition.mountpoint}")
                info.append(f"Filesystem: {partition.fstype}")
                info.append(f"Total: {self.bytes_to_human(usage.total)}")
                info.append(f"Used: {self.bytes_to_human(usage.used)} ({usage.percent}%)")
                info.append(f"Free: {self.bytes_to_human(usage.free)}")
            except:
                continue
        
        # Disk information
        info.append("\n=== Physical Disks ===")
        disk_info = self.run_command("lsblk -d -o NAME,SIZE,TYPE,MODEL")
        info.append(disk_info)
        
        return "\n".join(info)

    def get_performance_info(self) -> str:
        """Get performance information"""
        info = []
        info.append("=== Performance Information ===\n")
        
        # CPU load
        info.append("=== CPU Load ===")
        cpu_times = psutil.cpu_times_percent()
        info.append(f"User CPU Usage: {cpu_times.user}%")
        info.append(f"System CPU Usage: {cpu_times.system}%")
        info.append(f"Idle CPU: {cpu_times.idle}%")
        
        # Load average
        load1, load5, load15 = psutil.getloadavg()
        info.append(f"\nLoad Average (1/5/15 min): {load1:.2f}, {load5:.2f}, {load15:.2f}")
        
        # Memory usage details
        info.append("\n=== Memory Usage Details ===")
        mem = psutil.virtual_memory()
        info.append(f"Total Memory: {self.bytes_to_human(mem.total)}")
        info.append(f"Available Memory: {self.bytes_to_human(mem.available)}")
        info.append(f"Used Memory: {self.bytes_to_human(mem.used)}")
        info.append(f"Memory Buffer: {self.bytes_to_human(mem.buffers)}")
        info.append(f"Memory Cache: {self.bytes_to_human(mem.cached)}")
        
        # Process information
        info.append("\n=== Process Information ===")
        info.append(f"Total Processes: {len(psutil.pids())}")
        
        # Top processes by CPU
        info.append("\n=== Top CPU Processes ===")
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                processes.append(proc.info)
            except:
                continue
        
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        for proc in processes[:5]:
            info.append(f"PID: {proc['pid']}, Name: {proc['name']}, "
                      f"CPU: {proc['cpu_percent']}%")
        
        return "\n".join(info)

    def bytes_to_human(self, bytes_: int) -> str:
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_ < 1024:
                return f"{bytes_:.2f} {unit}"
            bytes_ /= 1024
        return f"{bytes_:.2f} PB"

    def refresh_info(self):
        """Refresh all system information"""
        try:
            # Clear all tabs
            for text_widget in self.tabs.values():
                text_widget.delete('1.0', tk.END)
            
            # Update Overview tab
            self.tabs['Overview'].insert(tk.END, self.get_system_overview())
            
            # Update Hardware tab
            self.tabs['Hardware'].insert(tk.END, self.get_hardware_info())
            
            # Update Operating System tab
            self.tabs['Operating System'].insert(tk.END, self.get_os_info())
            
            # Update Network tab
            self.tabs['Network'].insert(tk.END, self.get_network_info())
            
            # Update Storage tab
            self.tabs['Storage'].insert(tk.END, self.get_storage_info())
            
            # Update Performance tab
            self.tabs['Performance'].insert(tk.END, self.get_performance_info())
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh information: {str(e)}")

    def export_info(self):
        """Export system information to a file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"system_info_{timestamp}.txt"
            
            with open(filename, 'w') as f:
                f.write("=== System Information Export ===\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for name, text_widget in self.tabs.items():
                    f.write(f"\n{'='*20} {name} {'='*20}\n\n")
                    f.write(text_widget.get('1.0', tk.END))
            
            messagebox.showinfo("Success", 
                              f"System information exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", 
                               f"Failed to export information: {str(e)}")