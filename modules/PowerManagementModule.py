# Part 4: Power Management Module
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
import psutil
import dbus
from pathlib import Path
import json

class PowerManagementModule:
    def __init__(self, parent_notebook):
        # Create power management tab
        self.power_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.power_frame, text='Power Management')
        
        # Create main display area
        self.output = scrolledtext.ScrolledText(self.power_frame, height=20)
        self.output.pack(padx=5, pady=5, fill='both', expand=True)
        
        # Initialize variables
        self.de_type = None  # Desktop Environment type
        self.power_manager = None
        
        # Create control panel
        self.create_control_panel()
        
        # Detect desktop environment and power management system
        self.detect_environment()

    def create_control_panel(self):
        control_frame = ttk.Frame(self.power_frame)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        # Diagnostics section
        diag_frame = ttk.LabelFrame(control_frame, text="Diagnostics")
        diag_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(diag_frame, text="Check Power Status", 
                  command=self.check_power_status).pack(side='left', padx=5)
        ttk.Button(diag_frame, text="Scan for Issues", 
                  command=self.scan_power_issues).pack(side='left', padx=5)
        
        # Power Management Controls
        power_frame = ttk.LabelFrame(control_frame, text="Power Controls")
        power_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(power_frame, text="Reset Power Manager", 
                  command=self.reset_power_manager).pack(side='left', padx=5)
        ttk.Button(power_frame, text="Fix Configuration", 
                  command=self.fix_power_config).pack(side='left', padx=5)

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

    def detect_environment(self):
        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, "Detecting desktop environment...\n")
        
        # Check common desktop environment variables
        desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        session = os.environ.get('DESKTOP_SESSION', '').lower()
        
        if 'xfce' in desktop or 'xfce' in session:
            self.de_type = 'xfce'
            self.power_manager = 'xfce4-power-manager'
        elif 'gnome' in desktop or 'gnome' in session:
            self.de_type = 'gnome'
            self.power_manager = 'gnome-power-manager'
        elif 'kde' in desktop or 'kde' in session:
            self.de_type = 'kde'
            self.power_manager = 'powerdevil'
        else:
            self.de_type = 'unknown'
            self.power_manager = None
        
        self.output.insert(tk.END, f"Detected environment: {self.de_type}\n")
        self.output.insert(tk.END, f"Power manager: {self.power_manager}\n")

    def check_power_status(self):
        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, "=== Power Status Check ===\n\n")
        
        # Check battery status
        self.check_battery()
        
        # Check power manager status
        self.check_power_manager_status()
        
        # Check power policies
        self.check_power_policies()

    def check_battery(self):
        self.output.insert(tk.END, "Checking battery status...\n")
        
        battery = psutil.sensors_battery()
        if battery:
            self.output.insert(tk.END, f"Battery present: Yes\n")
            self.output.insert(tk.END, f"Battery percentage: {battery.percent}%\n")
            self.output.insert(tk.END, 
                f"Power plugged in: {'Yes' if battery.power_plugged else 'No'}\n")
            
            # Check ACPI
            output, error, code = self.run_command("acpi -V")
            if code == 0:
                self.output.insert(tk.END, f"\nACPI Information:\n{output}\n")
        else:
            self.output.insert(tk.END, "No battery detected (desktop system)\n")

    def check_power_manager_status(self):
        self.output.insert(tk.END, "\nChecking power manager status...\n")
        
        if not self.power_manager:
            self.output.insert(tk.END, "No power manager detected!\n")
            return
        
        # Check if power manager is running
        output, error, code = self.run_command(f"pgrep {self.power_manager}")
        if code == 0:
            self.output.insert(tk.END, f"{self.power_manager} is running\n")
            
            # Get specific power manager information
            if self.de_type == 'xfce':
                self.check_xfce_power()
            elif self.de_type == 'gnome':
                self.check_gnome_power()
            elif self.de_type == 'kde':
                self.check_kde_power()
        else:
            self.output.insert(tk.END, f"{self.power_manager} is not running!\n")

    def check_xfce_power(self):
        try:
            output, error, code = self.run_command(
                "xfconf-query -c xfce4-power-manager -l")
            if code == 0:
                self.output.insert(tk.END, "\nXFCE Power Manager Settings:\n")
                for line in output.splitlines():
                    if any(key in line.lower() for key in ['battery', 'critical', 'sleep']):
                        value, _, _ = self.run_command(
                            f"xfconf-query -c xfce4-power-manager -p {line}")
                        self.output.insert(tk.END, f"{line}: {value.strip()}\n")
        except Exception as e:
            self.output.insert(tk.END, f"Error checking XFCE power settings: {str(e)}\n")

    def check_gnome_power(self):
        try:
            output, error, code = self.run_command(
                "gsettings list-recursively org.gnome.settings-daemon.plugins.power")
            if code == 0:
                self.output.insert(tk.END, "\nGNOME Power Settings:\n")
                self.output.insert(tk.END, output)
        except Exception as e:
            self.output.insert(tk.END, f"Error checking GNOME power settings: {str(e)}\n")

    def check_kde_power(self):
        try:
            # Try to get PowerDevil status through D-Bus
            bus = dbus.SessionBus()
            power_devil = bus.get_object('org.kde.Solid.PowerManagement',
                                       '/org/kde/Solid/PowerManagement')
            self.output.insert(tk.END, "\nKDE Power Management Status:\n")
            
            # Get current power profile
            profile = power_devil.Get('', 'CurrentProfile')
            self.output.insert(tk.END, f"Current Profile: {profile}\n")
            
        except Exception as e:
            self.output.insert(tk.END, f"Error checking KDE power settings: {str(e)}\n")

    def check_power_policies(self):
        self.output.insert(tk.END, "\nChecking power policies...\n")
        
        # Check system power policies
        output, error, code = self.run_command("systemctl show -p HandleLidSwitch")
        if code == 0:
            self.output.insert(tk.END, f"Lid switch handling: {output}")
        
        # Check sleep settings
        output, error, code = self.run_command("systemctl show sleep.target")
        if code == 0:
            self.output.insert(tk.END, f"Sleep configuration:\n{output}\n")

    def scan_power_issues(self):
        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, "=== Scanning for Power Management Issues ===\n\n")
        
        issues_found = False
        
        # Check if power manager is installed
        if self.power_manager:
            output, error, code = self.run_command(f"which {self.power_manager}")
            if code != 0:
                self.output.insert(tk.END, 
                    f"Issue: Power manager {self.power_manager} is not installed\n")
                issues_found = True
        
        # Check if power manager is running
        if self.power_manager:
            output, error, code = self.run_command(f"pgrep {self.power_manager}")
            if code != 0:
                self.output.insert(tk.END, 
                    f"Issue: Power manager {self.power_manager} is not running\n")
                issues_found = True
        
        # Check ACPI
        output, error, code = self.run_command("acpi -V")
        if code != 0:
            self.output.insert(tk.END, "Issue: ACPI tools not installed or not working\n")
            issues_found = True
        
        # Check for common configuration files
        config_paths = {
            'xfce': '~/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-power-manager.xml',
            'gnome': '~/.config/dconf/user',
            'kde': '~/.config/powermanagementprofilesrc'
        }
        
        if self.de_type in config_paths:
            config_path = Path(os.path.expanduser(config_paths[self.de_type]))
            if not config_path.exists():
                self.output.insert(tk.END, 
                    f"Issue: Power management configuration file missing: {config_path}\n")
                issues_found = True
        
        if not issues_found:
            self.output.insert(tk.END, "No major power management issues detected.\n")

    def reset_power_manager(self):
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return
        
        if not self.power_manager:
            messagebox.showerror("Error", "No power manager detected")
            return
        
        try:
            # Stop the power manager
            output, error, code = self.run_command(f"systemctl stop {self.power_manager}")
            if code != 0:
                raise Exception(error)
            
            # Remove configuration files based on DE
            if self.de_type == 'xfce':
                config_path = Path(os.path.expanduser(
                    '~/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-power-manager.xml'))
                if config_path.exists():
                    config_path.unlink()
            elif self.de_type == 'gnome':
                self.run_command(
                    "dconf reset -f /org/gnome/settings-daemon/plugins/power/")
            elif self.de_type == 'kde':
                config_path = Path(os.path.expanduser(
                    '~/.config/powermanagementprofilesrc'))
                if config_path.exists():
                    config_path.unlink()
            
            # Start the power manager
            output, error, code = self.run_command(f"systemctl start {self.power_manager}")
            if code != 0:
                raise Exception(error)
            
            messagebox.showinfo("Success", "Power manager reset successfully")
            self.check_power_status()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset power manager: {str(e)}")

    def fix_power_config(self):
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return
        
        try:
            # Install missing components
            if not self.power_manager:
                if self.de_type == 'xfce':
                    self.run_command("apt-get install -y xfce4-power-manager")
                elif self.de_type == 'gnome':
                    self.run_command("apt-get install -y gnome-power-manager")
                elif self.de_type == 'kde':
                    self.run_command("apt-get install -y powerdevil")
            
            # Install ACPI tools
            self.run_command("apt-get install -y acpi acpid")
            
            # Enable and start services
            services = ['acpid']
            if self.power_manager:
                services.append(self.power_manager)
            
            for service in services:
                self.run_command(f"systemctl enable {service}")
                self.run_command(f"systemctl start {service}")
            
            # Apply default power settings based on DE
            if self.de_type == 'xfce':
                self.apply_xfce_defaults()
            elif self.de_type == 'gnome':
                self.apply_gnome_defaults()
            elif self.de_type == 'kde':
                self.apply_kde_defaults()
            
            messagebox.showinfo("Success", "Power configuration fixed successfully")
            self.check_power_status()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fix power configuration: {str(e)}")

    def apply_xfce_defaults(self):
        defaults = {
            '/xfce4-power-manager/on-battery/critical-power-level': '10',
            '/xfce4-power-manager/on-battery/critical-power-action': '1',
            '/xfce4-power-manager/on-ac/dpms-enabled': 'true',
            '/xfce4-power-manager/on-battery/dpms-enabled': 'true'
        }
        
        for key, value in defaults.items():
            self.run_command(f"xfconf-query -c xfce4-power-manager -p {key} -s {value}")

    def apply_gnome_defaults(self):
        defaults = {
            'org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type': 'suspend',
            'org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type': 'suspend',
            'org.gnome.settings-daemon.plugins.power critical-battery-action': 'suspend'
        }
        
        for key, value in defaults.items():
            self.run_command(f"gsettings set {key} {value}")

    def apply_kde_defaults(self):
        # KDE power management profiles are stored in powermanagementprofilesrc
        config_path = Path(os.path.expanduser('~/.config/powermanagementprofilesrc'))
        
        default_config = """[AC]
idleTime=300000
suspendThenHibernate=false
suspendType=1

[Battery]
idleTime=120000
suspendThenHibernate=false
suspendType=1

[LowBattery]
idleTime=60000
suspendThenHibernate=false
suspendType=1
"""
        
        with open(config_path, 'w') as f:
            f.write(default_config)
        
        # Reload KDE power management
        self.run_command("qdbus org.kde.Solid.PowerManagement /org/kde/Solid/PowerManagement reload")

    def export_power_report(self):
        """Generate a detailed power management report"""
        try:
            filename = f"power_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as f:
                f.write("Power Management Report\n")
                f.write("=" * 50 + "\n\n")
                
                # System Information
                f.write("System Information:\n")
                f.write(f"Desktop Environment: {self.de_type}\n")
                f.write(f"Power Manager: {self.power_manager}\n\n")
                
                # Battery Information
                battery = psutil.sensors_battery()
                if battery:
                    f.write("Battery Status:\n")
                    f.write(f"Percentage: {battery.percent}%\n")
                    f.write(f"Plugged In: {battery.power_plugged}\n")
                    
                    # ACPI Details
                    output, error, code = self.run_command("acpi -V")
                    if code == 0:
                        f.write("\nACPI Information:\n")
                        f.write(output)
                
                # Power Manager Configuration
                f.write("\nPower Manager Configuration:\n")
                if self.de_type == 'xfce':
                    output, error, code = self.run_command(
                        "xfconf-query -c xfce4-power-manager -l")
                    if code == 0:
                        f.write(output)
                elif self.de_type == 'gnome':
                    output, error, code = self.run_command(
                        "gsettings list-recursively org.gnome.settings-daemon.plugins.power")
                    if code == 0:
                        f.write(output)
                elif self.de_type == 'kde':
                    if os.path.exists(os.path.expanduser('~/.config/powermanagementprofilesrc')):
                        with open(os.path.expanduser('~/.config/powermanagementprofilesrc')) as conf:
                            f.write(conf.read())
                
                # System Power Policies
                f.write("\nSystem Power Policies:\n")
                output, error, code = self.run_command("systemctl show -p HandleLidSwitch")
                if code == 0:
                    f.write(output)
                
            messagebox.showinfo("Success", f"Power report exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export power report: {str(e)}")

    def check_power_saving_services(self):
        """Check status of power-related services"""
        self.output.insert(tk.END, "\nChecking power-related services...\n")
        
        services = [
            'acpid',
            'thermald',
            'tlp',
            'powertop',
            self.power_manager
        ]
        
        for service in services:
            if service:
                output, error, code = self.run_command(f"systemctl is-active {service}")
                status = output.strip() if code == 0 else "inactive"
                self.output.insert(tk.END, f"{service}: {status}\n")

    def optimize_power_settings(self):
        """Apply optimized power settings"""
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return
            
        try:
            # Install power management tools if not present
            self.run_command("apt-get install -y tlp powertop")
            
            # Enable and start TLP
            self.run_command("systemctl enable tlp")
            self.run_command("systemctl start tlp")
            
            # Run PowerTOP autotune
            self.run_command("powertop --auto-tune")
            
            # Apply specific optimizations based on DE
            if self.de_type == 'xfce':
                self.optimize_xfce_power()
            elif self.de_type == 'gnome':
                self.optimize_gnome_power()
            elif self.de_type == 'kde':
                self.optimize_kde_power()
            
            messagebox.showinfo("Success", "Power settings optimized successfully")
            self.check_power_status()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to optimize power settings: {str(e)}")

    def optimize_xfce_power(self):
        """Apply optimized power settings for XFCE"""
        optimized_settings = {
            '/xfce4-power-manager/on-battery/brightness-level': '30',
            '/xfce4-power-manager/on-battery/dpms-on-battery-sleep': '300',
            '/xfce4-power-manager/on-battery/dpms-on-battery-off': '600',
            '/xfce4-power-manager/on-ac/dpms-on-ac-sleep': '600',
            '/xfce4-power-manager/on-ac/dpms-on-ac-off': '1200'
        }
        
        for key, value in optimized_settings.items():
            self.run_command(f"xfconf-query -c xfce4-power-manager -p {key} -s {value}")

    def optimize_gnome_power(self):
        """Apply optimized power settings for GNOME"""
        optimized_settings = {
            'org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout': '2700',
            'org.gnome.settings-daemon.plugins.power sleep-inactive-battery-timeout': '900',
            'org.gnome.settings-daemon.plugins.power ambient-enabled': 'true',
            'org.gnome.settings-daemon.plugins.power idle-dim': 'true'
        }
        
        for key, value in optimized_settings.items():
            self.run_command(f"gsettings set {key} {value}")

    def optimize_kde_power(self):
        """Apply optimized power settings for KDE"""
        optimized_config = """
        [AC]
        idleTime=600000
        suspendThenHibernate=true
        suspendType=1
        [Battery]
        idleTime=300000
        suspendThenHibernate=true
        suspendType=1
        [LowBattery]
        idleTime=60000
        suspendThenHibernate=true
        suspendType=1
        """

        config_path = Path(os.path.expanduser('~/.config/powermanagementprofilesrc'))

        # Create parent directories if they don't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(config_path, 'w') as f:
                f.write(optimized_config)

            # Reload KDE power management settings
            self.run_command("qdbus org.kde.Solid.PowerManagement /org/kde/Solid/PowerManagement reload")
            return True
        except Exception as e:
            print(f"Error optimizing KDE power settings: {str(e)}")
            return False