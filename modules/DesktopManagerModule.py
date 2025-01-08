# Part 13: Desktop Manager Module
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
import re
import pwd
import time
from pathlib import Path
from typing import Dict, List, Tuple

class DesktopManagerModule:
    def __init__(self, parent_notebook):
        # Create desktop manager tab
        self.dm_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.dm_frame, text='Desktop Manager')
        
        # Initialize variables
        self.display_managers = {
            'lightdm': 'LightDM',
            'gdm3': 'GNOME Display Manager',
            'sddm': 'Simple Desktop Display Manager',
            'xdm': 'X Display Manager',
            'slim': 'Simple Login Manager'
        }
        
        self.current_dm = None
        self.recommended_dm = 'lightdm'  # Default for Kali
        self.last_used_dm = None
        
        # Create interface
        self.create_interface()
        
        # Initial scan
        self.scan_display_managers()

    def create_interface(self):
        # Main container
        main_container = ttk.Frame(self.dm_frame)
        main_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Status panel
        status_frame = ttk.LabelFrame(main_container, text="Current Status")
        status_frame.pack(fill='x', padx=5, pady=5)
        
        # Current DM
        current_frame = ttk.Frame(status_frame)
        current_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(current_frame, text="Current DM:").pack(side='left')
        self.current_dm_var = tk.StringVar(value="Scanning...")
        ttk.Label(current_frame, textvariable=self.current_dm_var).pack(side='left', padx=5)
        
        # Recommended DM
        recommended_frame = ttk.Frame(status_frame)
        recommended_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(recommended_frame, text="Recommended DM:").pack(side='left')
        self.recommended_dm_var = tk.StringVar(value="LightDM")
        ttk.Label(recommended_frame, textvariable=self.recommended_dm_var).pack(side='left', padx=5)
        
        # Last Used DM
        last_used_frame = ttk.Frame(status_frame)
        last_used_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(last_used_frame, text="Last Used DM:").pack(side='left')
        self.last_used_dm_var = tk.StringVar(value="Scanning...")
        ttk.Label(last_used_frame, textvariable=self.last_used_dm_var).pack(side='left', padx=5)
        
        # Installed DMs List
        list_frame = ttk.LabelFrame(main_container, text="Installed Display Managers")
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.dm_list = ttk.Treeview(list_frame, columns=('name', 'status', 'default'),
                                   show='headings')
        self.dm_list.heading('name', text='Display Manager')
        self.dm_list.heading('status', text='Status')
        self.dm_list.heading('default', text='Default')
        
        # Scrollbar for DM list
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical',
                                command=self.dm_list.yview)
        self.dm_list.configure(yscrollcommand=scrollbar.set)
        
        self.dm_list.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Control panel
        control_frame = ttk.LabelFrame(main_container, text="Actions")
        control_frame.pack(fill='x', padx=5, pady=5)
        
        # Buttons
        ttk.Button(control_frame, text="Scan Display Managers",
                  command=self.scan_display_managers).pack(side='left', padx=5, pady=5)
        
        ttk.Button(control_frame, text="Fix Current DM",
                  command=self.fix_current_dm).pack(side='left', padx=5, pady=5)
        
        ttk.Button(control_frame, text="Switch to Recommended",
                  command=self.switch_to_recommended).pack(side='left', padx=5, pady=5)
        
        ttk.Button(control_frame, text="Remove Unnecessary DMs",
                  command=self.remove_unnecessary_dms).pack(side='left', padx=5, pady=5)
        
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

    def scan_display_managers(self):
        """Scan system for installed display managers and their status"""
        self.update_output("Scanning display managers...\n")
        
        # Clear current list
        self.dm_list.delete(*self.dm_list.get_children())
        
        # Check each display manager
        for dm_name, dm_title in self.display_managers.items():
            # Check if installed
            output, _, code = self.run_command(f"dpkg -l {dm_name}")
            if code == 0 and "ii" in output:
                # Check if running
                status_output, _, _ = self.run_command(f"systemctl is-active {dm_name}")
                status = "Running" if "active" in status_output else "Stopped"
                
                # Check if default
                default_output, _, _ = self.run_command("cat /etc/X11/default-display-manager")
                is_default = "Yes" if dm_name in default_output else "No"
                
                self.dm_list.insert('', 'end', values=(dm_title, status, is_default))
                
                if is_default == "Yes":
                    self.current_dm = dm_name
                    self.current_dm_var.set(dm_title)
        
        # Detect last used DM from logs
        self.detect_last_used_dm()
        
        self.update_output("Scan complete.\n")

    def detect_last_used_dm(self):
        """Detect last successfully used display manager from logs"""
        try:
            # Check auth.log for successful logins
            output, _, _ = self.run_command("grep 'session opened' /var/log/auth.log")
            
            # Find most recent login with display manager
            last_dm = None
            latest_timestamp = 0
            
            for line in output.splitlines():
                for dm_name in self.display_managers:
                    if dm_name in line.lower():
                        # Extract timestamp
                        try:
                            timestamp = time.mktime(time.strptime(line[:15], "%b %d %H:%M:%S"))
                            if timestamp > latest_timestamp:
                                latest_timestamp = timestamp
                                last_dm = dm_name
                        except:
                            continue
            
            if last_dm:
                self.last_used_dm = last_dm
                self.last_used_dm_var.set(self.display_managers[last_dm])
            else:
                self.last_used_dm_var.set("Unknown")
                
        except Exception as e:
            self.update_output(f"Error detecting last used DM: {str(e)}\n")
            self.last_used_dm_var.set("Error")

    def fix_current_dm(self):
        """Attempt to fix current display manager issues"""
        if not self.current_dm:
            messagebox.showerror("Error", "No display manager currently set")
            return
        
        self.update_output(f"Attempting to fix {self.current_dm}...\n")
        
        try:
            # Stop the service
            self.run_command(f"sudo systemctl stop {self.current_dm}")
            
            # Reconfigure package
            self.run_command(f"sudo dpkg-reconfigure {self.current_dm}")
            
            # Clear any corrupted config
            config_dir = f"/etc/{self.current_dm}"
            if os.path.exists(config_dir):
                backup_dir = f"{config_dir}_backup_{int(time.time())}"
                self.run_command(f"sudo cp -r {config_dir} {backup_dir}")
                self.update_output(f"Backed up configuration to {backup_dir}\n")
            
            # Reinstall package
            self.run_command(f"sudo apt-get install --reinstall {self.current_dm}")
            
            # Start service
            self.run_command(f"sudo systemctl start {self.current_dm}")
            
            # Update scan
            self.scan_display_managers()
            
            messagebox.showinfo("Success", "Display manager fix attempted")
            
        except Exception as e:
            self.update_output(f"Error fixing display manager: {str(e)}\n")
            messagebox.showerror("Error", f"Failed to fix display manager: {str(e)}")

    def switch_to_recommended(self):
        """Switch to the recommended display manager"""
        if messagebox.askyesno("Confirm", 
                             f"Switch to {self.display_managers[self.recommended_dm]}?"):
            try:
                # Install if not present
                self.run_command(f"sudo apt-get install -y {self.recommended_dm}")
                
                # Set as default
                self.run_command(
                    f"sudo update-alternatives --set x-display-manager "
                    f"/usr/sbin/{self.recommended_dm}"
                )
                
                # Reconfigure
                self.run_command(f"sudo dpkg-reconfigure {self.recommended_dm}")
                
                # Restart service
                self.run_command(f"sudo systemctl restart {self.recommended_dm}")
                
                # Update scan
                self.scan_display_managers()
                
                messagebox.showinfo("Success", "Switched to recommended display manager")
                
            except Exception as e:
                self.update_output(f"Error switching display manager: {str(e)}\n")
                messagebox.showerror("Error", 
                                   f"Failed to switch display manager: {str(e)}")

    def remove_unnecessary_dms(self):
        """Remove unnecessary display managers"""
        if not self.current_dm:
            messagebox.showerror("Error", "No display manager currently set")
            return
        
        # Get list of installed DMs except current
        unnecessary_dms = []
        for item in self.dm_list.get_children():
            values = self.dm_list.item(item)['values']
            dm_name = next(name for name, title in self.display_managers.items() 
                         if title == values[0])
            if dm_name != self.current_dm:
                unnecessary_dms.append(dm_name)
        
        if not unnecessary_dms:
            messagebox.showinfo("Info", "No unnecessary display managers found")
            return
        
        if messagebox.askyesno("Confirm", 
                              f"Remove unnecessary display managers?\n"
                              f"{', '.join(unnecessary_dms)}"):
            try:
                for dm in unnecessary_dms:
                    self.run_command(f"sudo apt-get remove --purge -y {dm}")
                
                # Update scan
                self.scan_display_managers()
                
                messagebox.showinfo("Success", "Removed unnecessary display managers")
                
            except Exception as e:
                self.update_output(f"Error removing display managers: {str(e)}\n")
                messagebox.showerror("Error", 
                                   f"Failed to remove display managers: {str(e)}")

    def update_output(self, message: str):
        """Update output text"""
        self.output.insert(tk.END, message)
        self.output.see(tk.END)