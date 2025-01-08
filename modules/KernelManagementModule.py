# Part 5: Kernel Management Module
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
import re
import json
from pathlib import Path
import psutil
import shutil
from datetime import datetime

class KernelManagementModule:
    def __init__(self, parent_notebook):
        # Create kernel management tab
        self.kernel_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.kernel_frame, text='Kernel Management')
        
        # Create main display area
        self.output = scrolledtext.ScrolledText(self.kernel_frame, height=20)
        self.output.pack(padx=5, pady=5, fill='both', expand=True)
        
        # Initialize kernel info
        self.kernel_info = {}
        self.available_kernels = []
        
        # Create control panel
        self.create_control_panel()
        
        # Initial kernel scan
        self.scan_kernel_status()

    def create_control_panel(self):
        control_frame = ttk.Frame(self.kernel_frame)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        # Diagnostics section
        diag_frame = ttk.LabelFrame(control_frame, text="Diagnostics")
        diag_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(diag_frame, text="Scan Kernel Status", 
                  command=self.scan_kernel_status).pack(side='left', padx=5)
        ttk.Button(diag_frame, text="Check for Issues", 
                  command=self.check_kernel_issues).pack(side='left', padx=5)
        ttk.Button(diag_frame, text="Generate Report", 
                  command=self.generate_kernel_report).pack(side='left', padx=5)
        
        # Kernel Operations
        kernel_frame = ttk.LabelFrame(control_frame, text="Kernel Operations")
        kernel_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(kernel_frame, text="Update Kernel", 
                  command=self.update_kernel).pack(side='left', padx=5)
        ttk.Button(kernel_frame, text="Fix Issues", 
                  command=self.fix_kernel_issues).pack(side='left', padx=5)
        ttk.Button(kernel_frame, text="Manage Parameters", 
                  command=self.show_kernel_params).pack(side='left', padx=5)

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

    def scan_kernel_status(self):
        """Perform a comprehensive kernel status scan"""
        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, "=== Kernel Status Scan ===\n\n")
        
        # Get current kernel version
        current_kernel = os.uname().release
        self.kernel_info['current'] = current_kernel
        self.output.insert(tk.END, f"Current Kernel: {current_kernel}\n")
        
        # Get available kernels
        self.scan_available_kernels()
        
        # Check kernel modules
        self.check_kernel_modules()
        
        # Check kernel parameters
        self.check_kernel_parameters()
        
        # Check kernel logs
        self.check_kernel_logs()

    def scan_available_kernels(self):
        """Scan for all installed and available kernels"""
        self.output.insert(tk.END, "\nScanning available kernels...\n")
        
        # Get installed kernels
        output, error, code = self.run_command("dpkg --list | grep linux-image")
        if code == 0:
            installed_kernels = []
            for line in output.splitlines():
                if "linux-image" in line:
                    kernel_version = line.split()[2].replace("linux-image-", "")
                    installed_kernels.append(kernel_version)
            
            self.kernel_info['installed'] = installed_kernels
            self.output.insert(tk.END, f"Installed kernels: {', '.join(installed_kernels)}\n")
        
        # Check available kernel updates
        output, error, code = self.run_command("apt-cache search linux-image")
        if code == 0:
            available_kernels = []
            for line in output.splitlines():
                if "linux-image" in line and not "unsigned" in line:
                    kernel_version = line.split()[0].replace("linux-image-", "")
                    available_kernels.append(kernel_version)
            
            self.kernel_info['available'] = available_kernels
            self.output.insert(tk.END, f"Available kernels: {', '.join(available_kernels)}\n")

    def check_kernel_modules(self):
        """Check loaded kernel modules and their status"""
        self.output.insert(tk.END, "\nChecking kernel modules...\n")
        
        # Get loaded modules
        output, error, code = self.run_command("lsmod")
        if code == 0:
            modules = []
            for line in output.splitlines()[1:]:  # Skip header
                module_name = line.split()[0]
                modules.append(module_name)
            
            self.kernel_info['modules'] = modules
            self.output.insert(tk.END, f"Loaded modules: {len(modules)}\n")
            
            # Check for common problematic modules
            problematic = self.check_problematic_modules(modules)
            if problematic:
                self.output.insert(tk.END, "Potentially problematic modules:\n")
                for mod in problematic:
                    self.output.insert(tk.END, f"- {mod}\n")

    def check_problematic_modules(self, modules):
        """Check for known problematic modules"""
        known_issues = {
            'nouveau': 'NVIDIA open-source driver (might conflict with proprietary)',
            'iwlwifi': 'Intel wireless (check for firmware issues)',
            'r8169': 'Realtek ethernet (might need firmware update)'
        }
        
        problematic = []
        for module in modules:
            if module in known_issues:
                problematic.append(f"{module} - {known_issues[module]}")
        
        return problematic

    def check_kernel_parameters(self):
        """Check current kernel parameters"""
        self.output.insert(tk.END, "\nChecking kernel parameters...\n")
        
        # Get current parameters
        output, error, code = self.run_command("cat /proc/cmdline")
        if code == 0:
            self.kernel_info['parameters'] = output.strip()
            self.output.insert(tk.END, f"Boot parameters: {output}\n")
            
            # Check for common parameters
            params = output.split()
            self.check_important_parameters(params)

    def check_important_parameters(self, params):
        """Check for important kernel parameters"""
        important_params = {
            'quiet': 'Quiet boot',
            'splash': 'Boot splash screen',
            'nomodeset': 'Disable kernel mode setting',
            'acpi': 'ACPI support'
        }
        
        for param in important_params:
            if param in ' '.join(params):
                self.output.insert(tk.END, f"Found {param}: {important_params[param]}\n")

    def check_kernel_logs(self):
        """Check kernel logs for issues"""
        self.output.insert(tk.END, "\nChecking kernel logs...\n")
        
        # Get recent kernel messages
        output, error, code = self.run_command("journalctl -k -p err..emerg --since '24 hours ago'")
        if code == 0:
            errors = output.splitlines()
            self.kernel_info['recent_errors'] = errors
            
            if errors:
                self.output.insert(tk.END, f"Found {len(errors)} kernel errors in last 24 hours:\n")
                for error in errors[:5]:  # Show only first 5 errors
                    self.output.insert(tk.END, f"- {error}\n")
            else:
                self.output.insert(tk.END, "No kernel errors found in last 24 hours\n")

    def check_kernel_issues(self):
        """Comprehensive check for kernel issues"""
        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, "=== Kernel Issue Analysis ===\n\n")
        
        issues_found = False
        
        # Check kernel version
        current_kernel = os.uname().release
        latest_kernel = self.get_latest_available_kernel()
        
        if latest_kernel and current_kernel < latest_kernel:
            self.output.insert(tk.END, "⚠️ Kernel update available\n")
            self.output.insert(tk.END, f"Current: {current_kernel}\n")
            self.output.insert(tk.END, f"Latest: {latest_kernel}\n\n")
            issues_found = True
        
        # Check kernel panic settings
        self.check_kernel_panic_settings()
        
        # Check for common hardware issues
        self.check_hardware_compatibility()
        
        # Check memory management
        self.check_memory_management()
        
        # Check I/O scheduling
        self.check_io_scheduling()
        
        if not issues_found:
            self.output.insert(tk.END, "No major kernel issues detected.\n")

    def get_latest_available_kernel(self):
        """Get the latest available kernel version"""
        output, error, code = self.run_command(
            "apt-cache search linux-image | grep generic")
        if code == 0:
            versions = []
            for line in output.splitlines():
                if "linux-image" in line and not "unsigned" in line:
                    version = line.split()[0].replace("linux-image-", "")
                    if re.match(r'\d+\.\d+\.\d+', version):
                        versions.append(version)
            
            if versions:
                return max(versions)
        return None

    def check_kernel_panic_settings(self):
        """Check kernel panic settings"""
        try:
            with open('/proc/sys/kernel/panic', 'r') as f:
                panic_timeout = f.read().strip()
                if panic_timeout == '0':
                    self.output.insert(tk.END, 
                        "⚠️ Kernel panic timeout is disabled\n")
        except Exception:
            self.output.insert(tk.END, 
                "Unable to check kernel panic settings\n")

    def check_hardware_compatibility(self):
        """Check for hardware compatibility issues"""
        # Check for hardware errors in dmesg
        output, error, code = self.run_command(
            "dmesg | grep -i 'error\\|fail\\|incompatible'")
        if code == 0 and output:
            self.output.insert(tk.END, "\nPotential hardware issues found:\n")
            for line in output.splitlines()[:5]:  # Show first 5 issues
                self.output.insert(tk.END, f"- {line}\n")

    def check_memory_management(self):
        """Check memory management settings"""
        try:
            with open('/proc/sys/vm/swappiness', 'r') as f:
                swappiness = int(f.read().strip())
                if swappiness > 60:
                    self.output.insert(tk.END, 
                        "\n⚠️ High swappiness value might impact performance\n")
                    self.output.insert(tk.END, 
                        f"Current swappiness: {swappiness}\n")
        except Exception:
            self.output.insert(tk.END, 
                "Unable to check memory management settings\n")

    def check_io_scheduling(self):
        """Check I/O scheduler settings"""
        try:
            schedulers = []
            for disk in os.listdir('/sys/block'):
                if disk.startswith(('sd', 'nvme', 'hd')):
                    scheduler_path = f"/sys/block/{disk}/queue/scheduler"
                    if os.path.exists(scheduler_path):
                        with open(scheduler_path, 'r') as f:
                            schedulers.append((disk, f.read().strip()))
            
            if schedulers:
                self.output.insert(tk.END, "\nI/O Schedulers:\n")
                for disk, scheduler in schedulers:
                    self.output.insert(tk.END, f"{disk}: {scheduler}\n")
        except Exception:
            self.output.insert(tk.END, 
                "Unable to check I/O scheduler settings\n")

    def update_kernel(self):
        """Update the kernel to the latest version"""
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return
        
        try:
            # Update package list
            self.output.delete(1.0, tk.END)
            self.output.insert(tk.END, "Updating package list...\n")
            output, error, code = self.run_command("apt-get update")
            if code != 0:
                raise Exception(f"Failed to update package list: {error}")
            
            # Check for kernel updates
            self.output.insert(tk.END, "Checking for kernel updates...\n")
            output, error, code = self.run_command(
                "apt-get --just-print upgrade | grep linux-image")
            
            if "linux-image" in output:
                if messagebox.askyesno("Update Available", 
                    "Kernel update available. Do you want to proceed?"):
                    # Backup current kernel
                    self.backup_current_kernel()
                    
                    # Perform update
                    self.output.insert(tk.END, "Installing kernel update...\n")
                    output, error, code = self.run_command(
                        "apt-get install -y linux-image-generic linux-headers-generic")
                    if code != 0:
                        raise Exception(f"Failed to install kernel update: {error}")
                    
                    self.output.insert(tk.END, "Kernel updated successfully.\n")
                    self.output.insert(tk.END, 
                        "Please reboot your system to use the new kernel.\n")
            else:
                self.output.insert(tk.END, "No kernel updates available.\n")
        
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def backup_current_kernel(self):
        """Backup current kernel configuration"""
        try:
            backup_dir = Path.home() / "kernel_backup"
            backup_dir.mkdir(exist_ok=True)
            
            # Backup kernel config
            shutil.copy2('/boot/config-' + os.uname().release, 
                        backup_dir / f"config-{datetime.now().strftime('%Y%m%d')}")
            
            # Backup modules
            shutil.copytree('/lib/modules/' + os.uname().release,
                           backup_dir / f"modules-{datetime.now().strftime('%Y%m%d')}")
            
            self.output.insert(tk.END, f"Kernel backup created in {backup_dir}\n")
        
        except Exception as e:

            self.output.insert(tk.END, f"Failed to create kernel backup: {str(e)}\n")

    def fix_kernel_issues(self):
        """Attempt to fix detected kernel issues"""
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return
        
        try:
            self.output.delete(1.0, tk.END)
            self.output.insert(tk.END, "=== Attempting to fix kernel issues ===\n\n")
            
            # Fix module issues
            self.fix_module_issues()
            
            # Fix memory management
            self.fix_memory_management()
            
            # Fix I/O scheduling
            self.fix_io_scheduling()
            
            # Fix kernel parameters
            self.fix_kernel_parameters()
            
            # Update initramfs
            self.output.insert(tk.END, "Updating initramfs...\n")
            output, error, code = self.run_command("update-initramfs -u")
            if code != 0:
                raise Exception(f"Failed to update initramfs: {error}")
            
            self.output.insert(tk.END, "Kernel fixes applied successfully.\n")
            self.output.insert(tk.END, "Please reboot your system for changes to take effect.\n")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fix kernel issues: {str(e)}")

    def fix_module_issues(self):
        """Fix kernel module issues"""
        self.output.insert(tk.END, "Checking and fixing module issues...\n")
        
        # Check for missing firmware
        output, error, code = self.run_command("dmesg | grep -i 'firmware'")
        if "firmware" in output and "failed" in output.lower():
            self.output.insert(tk.END, "Installing missing firmware packages...\n")
            self.run_command("apt-get install -y linux-firmware firmware-linux-free")
        
        # Rebuild module dependencies
        self.output.insert(tk.END, "Rebuilding module dependencies...\n")
        output, error, code = self.run_command("depmod -a")
        if code != 0:
            raise Exception(f"Failed to rebuild module dependencies: {error}")

    def fix_memory_management(self):
        """Fix memory management settings"""
        self.output.insert(tk.END, "Optimizing memory management settings...\n")
        
        try:
            # Set optimal swappiness
            with open('/proc/sys/vm/swappiness', 'w') as f:
                f.write('60')
            
            # Set optimal cache pressure
            with open('/proc/sys/vm/vfs_cache_pressure', 'w') as f:
                f.write('50')
            
            # Make settings persistent
            sysctl_conf = Path('/etc/sysctl.d/99-sysctl.conf')
            with open(sysctl_conf, 'a') as f:
                f.write('\n# Optimized memory management settings\n')
                f.write('vm.swappiness=60\n')
                f.write('vm.vfs_cache_pressure=50\n')
            
            self.output.insert(tk.END, "Memory management settings optimized.\n")
            
        except Exception as e:
            raise Exception(f"Failed to optimize memory management: {str(e)}")

    def fix_io_scheduling(self):
        """Fix I/O scheduler settings"""
        self.output.insert(tk.END, "Optimizing I/O scheduler settings...\n")
        
        try:
            for disk in os.listdir('/sys/block'):
                if disk.startswith(('sd', 'nvme', 'hd')):
                    scheduler_path = f"/sys/block/{disk}/queue/scheduler"
                    if os.path.exists(scheduler_path):
                        # Set to deadline for SSDs, CFQ for HDDs
                        is_ssd = self.check_if_ssd(disk)
                        scheduler = "none" if is_ssd else "cfq"
                        
                        with open(scheduler_path, 'w') as f:
                            f.write(scheduler)
            
            self.output.insert(tk.END, "I/O scheduler settings optimized.\n")
            
        except Exception as e:
            raise Exception(f"Failed to optimize I/O scheduler: {str(e)}")

    def check_if_ssd(self, disk):
        """Check if a disk is SSD"""
        try:
            # Check rotation rate - 0 typically means SSD
            rot_path = f"/sys/block/{disk}/queue/rotational"
            if os.path.exists(rot_path):
                with open(rot_path, 'r') as f:
                    return f.read().strip() == '0'
        except Exception:
            pass
        return False

    def fix_kernel_parameters(self):
        """Fix kernel parameters"""
        self.output.insert(tk.END, "Optimizing kernel parameters...\n")
        
        try:
            # Read current GRUB config
            with open('/etc/default/grub', 'r') as f:
                grub_config = f.read()
            
            # Optimize parameters
            params = {
                'GRUB_CMDLINE_LINUX_DEFAULT': 'quiet splash',
                'GRUB_CMDLINE_LINUX': 'intel_idle.max_cstate=1 processor.max_cstate=1'
            }
            
            # Update GRUB config
            for key, value in params.items():
                pattern = f"{key}=.*"
                replacement = f'{key}="{value}"'
                if re.search(pattern, grub_config):
                    grub_config = re.sub(pattern, replacement, grub_config)
                else:
                    grub_config += f'\n{replacement}\n'
            
            # Write updated config
            with open('/etc/default/grub', 'w') as f:
                f.write(grub_config)
            
            # Update GRUB
            output, error, code = self.run_command("update-grub")
            if code != 0:
                raise Exception(f"Failed to update GRUB: {error}")
            
            self.output.insert(tk.END, "Kernel parameters optimized.\n")
            
        except Exception as e:
            raise Exception(f"Failed to optimize kernel parameters: {str(e)}")

    def show_kernel_params(self):
        """Show and edit kernel parameters"""
        params_window = tk.Toplevel(self.kernel_frame)
        params_window.title("Kernel Parameters")
        params_window.geometry("600x400")
        
        # Create parameter display
        param_frame = ttk.Frame(params_window)
        param_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create scrolled text widget for parameters
        param_text = scrolledtext.ScrolledText(param_frame, height=15)
        param_text.pack(fill='both', expand=True)
        
        # Load current parameters
        try:
            with open('/proc/cmdline', 'r') as f:
                current_params = f.read().strip()
            param_text.insert('1.0', current_params)
        except Exception as e:
            param_text.insert('1.0', f"Error loading parameters: {str(e)}")
        
        def save_parameters():
            """Save modified kernel parameters"""
            if os.geteuid() != 0:
                messagebox.showerror("Error", "Root privileges required")
                return
            
            try:
                new_params = param_text.get('1.0', tk.END).strip()
                
                # Update GRUB configuration
                with open('/etc/default/grub', 'r') as f:
                    grub_config = f.read()
                
                # Update GRUB_CMDLINE_LINUX_DEFAULT
                grub_config = re.sub(
                    r'GRUB_CMDLINE_LINUX_DEFAULT=.*',
                    f'GRUB_CMDLINE_LINUX_DEFAULT="{new_params}"',
                    grub_config
                )
                
                with open('/etc/default/grub', 'w') as f:
                    f.write(grub_config)
                
                # Update GRUB
                output, error, code = self.run_command("update-grub")
                if code != 0:
                    raise Exception(f"Failed to update GRUB: {error}")
                
                messagebox.showinfo("Success", 
                    "Kernel parameters updated. Please reboot for changes to take effect.")
                params_window.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save parameters: {str(e)}")
        
        # Add save button
        ttk.Button(param_frame, text="Save Changes", 
                  command=save_parameters).pack(pady=5)

    def generate_kernel_report(self):
        """Generate a comprehensive kernel report"""
        try:
            filename = f"kernel_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(filename, 'w') as f:
                f.write("Kernel Management Report\n")
                f.write("=" * 50 + "\n\n")
                
                # System Information
                f.write("System Information:\n")
                f.write("-" * 20 + "\n")
                f.write(f"Current Kernel: {os.uname().release}\n")
                f.write(f"System: {os.uname().system}\n")
                f.write(f"Machine: {os.uname().machine}\n\n")
                
                # Kernel Parameters
                f.write("Kernel Parameters:\n")
                f.write("-" * 20 + "\n")
                with open('/proc/cmdline', 'r') as cmdline:
                    f.write(cmdline.read() + "\n\n")
                
                # Module Information
                f.write("Loaded Modules:\n")
                f.write("-" * 20 + "\n")
                output, error, code = self.run_command("lsmod")
                if code == 0:
                    f.write(output + "\n")
                
                # Memory Information
                f.write("Memory Management:\n")
                f.write("-" * 20 + "\n")
                with open('/proc/meminfo', 'r') as meminfo:
                    f.write(meminfo.read() + "\n")
                
                # Kernel Messages
                f.write("Recent Kernel Messages:\n")
                f.write("-" * 20 + "\n")
                output, error, code = self.run_command(
                    "dmesg | tail -n 50")
                if code == 0:
                    f.write(output + "\n")
            
            messagebox.showinfo("Success", f"Kernel report generated: {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")