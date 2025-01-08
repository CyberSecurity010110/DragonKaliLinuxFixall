# Part 6: NVIDIA GPU Management Module
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
import re
import json
from pathlib import Path
import shutil
from datetime import datetime
import requests
import platform

class NvidiaGPUModule:
    def __init__(self, parent_notebook):
        # Create NVIDIA GPU tab
        self.nvidia_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.nvidia_frame, text='NVIDIA GPU')
        
        # Create main display area
        self.output = scrolledtext.ScrolledText(self.nvidia_frame, height=20)
        self.output.pack(padx=5, pady=5, fill='both', expand=True)
        
        # Initialize GPU info
        self.gpu_info = {}
        self.driver_info = {}
        self.cuda_info = {}
        
        # Create control panel
        self.create_control_panel()
        
        # Initial GPU scan
        self.scan_gpu_status()

    def create_control_panel(self):
        control_frame = ttk.Frame(self.nvidia_frame)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        # Diagnostics section
        diag_frame = ttk.LabelFrame(control_frame, text="Diagnostics")
        diag_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(diag_frame, text="Scan GPU", 
                  command=self.scan_gpu_status).pack(side='left', padx=5)
        ttk.Button(diag_frame, text="Check Issues", 
                  command=self.check_gpu_issues).pack(side='left', padx=5)
        ttk.Button(diag_frame, text="Generate Report", 
                  command=self.generate_gpu_report).pack(side='left', padx=5)
        
        # Driver Operations
        driver_frame = ttk.LabelFrame(control_frame, text="Driver Operations")
        driver_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(driver_frame, text="Install/Update Driver", 
                  command=self.install_driver).pack(side='left', padx=5)
        ttk.Button(driver_frame, text="Install CUDA", 
                  command=self.install_cuda).pack(side='left', padx=5)
        ttk.Button(driver_frame, text="Optimize Settings", 
                  command=self.optimize_gpu_settings).pack(side='left', padx=5)

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

    def scan_gpu_status(self):
        """Perform comprehensive GPU status scan"""
        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, "=== NVIDIA GPU Status Scan ===\n\n")
        
        # Detect NVIDIA GPU
        self.detect_nvidia_gpu()
        
        # Check driver status
        self.check_driver_status()
        
        # Check CUDA installation
        self.check_cuda_status()
        
        # Check GPU performance
        self.check_gpu_performance()

    def detect_nvidia_gpu(self):
        """Detect NVIDIA GPU hardware"""
        self.output.insert(tk.END, "Detecting NVIDIA GPU...\n")
        
        # Try lspci first
        output, error, code = self.run_command("lspci | grep -i nvidia")
        if code == 0 and output:
            self.gpu_info['present'] = True
            self.gpu_info['pci_info'] = output.strip()
            self.output.insert(tk.END, f"Found NVIDIA GPU: {output.strip()}\n")
            
            # Get detailed GPU info using nvidia-smi if available
            output, error, code = self.run_command("nvidia-smi")
            if code == 0:
                self.parse_nvidia_smi(output)
            else:
                self.output.insert(tk.END, "nvidia-smi not available - driver might not be installed\n")
        else:
            self.gpu_info['present'] = False
            self.output.insert(tk.END, "No NVIDIA GPU detected\n")

    def parse_nvidia_smi(self, output):
        """Parse nvidia-smi output for detailed GPU information"""
        try:
            # Extract GPU model
            model_match = re.search(r"NVIDIA.*\((.*?)\)", output)
            if model_match:
                self.gpu_info['model'] = model_match.group(1)
            
            # Extract driver version
            driver_match = re.search(r"Driver Version: ([\d\.]+)", output)
            if driver_match:
                self.driver_info['version'] = driver_match.group(1)
            
            # Extract memory usage
            memory_match = re.search(r"(\d+)MiB\s*/\s*(\d+)MiB", output)
            if memory_match:
                used_mem, total_mem = memory_match.groups()
                self.gpu_info['memory'] = {
                    'total': int(total_mem),
                    'used': int(used_mem)
                }
            
            # Extract power usage if available
            power_match = re.search(r"(\d+)W\s*/\s*(\d+)W", output)
            if power_match:
                current_power, max_power = power_match.groups()
                self.gpu_info['power'] = {
                    'current': int(current_power),
                    'max': int(max_power)
                }
            
            self.output.insert(tk.END, "\nGPU Details:\n")
            self.output.insert(tk.END, f"Model: {self.gpu_info.get('model', 'Unknown')}\n")
            self.output.insert(tk.END, f"Driver: {self.driver_info.get('version', 'Not installed')}\n")
            
            if 'memory' in self.gpu_info:
                mem = self.gpu_info['memory']
                self.output.insert(tk.END, 
                    f"Memory: {mem['used']}MB / {mem['total']}MB\n")
            
            if 'power' in self.gpu_info:
                power = self.gpu_info['power']
                self.output.insert(tk.END, 
                    f"Power: {power['current']}W / {power['max']}W\n")
                
        except Exception as e:
            self.output.insert(tk.END, f"Error parsing nvidia-smi output: {str(e)}\n")

    def check_driver_status(self):
        """Check NVIDIA driver status"""
        self.output.insert(tk.END, "\nChecking driver status...\n")
        
        # Check if nvidia module is loaded
        output, error, code = self.run_command("lsmod | grep nvidia")
        if code == 0:
            self.driver_info['loaded'] = True
            self.output.insert(tk.END, "NVIDIA driver module is loaded\n")
        else:
            self.driver_info['loaded'] = False
            self.output.insert(tk.END, "NVIDIA driver module is not loaded\n")
        
        # Check available driver versions
        output, error, code = self.run_command(
            "apt-cache search nvidia-driver")
        if code == 0:
            available_drivers = []
            for line in output.splitlines():
                if "nvidia-driver-" in line:
                    version = line.split('-')[2]
                    if version.isdigit():
                        available_drivers.append(version)
            
            self.driver_info['available'] = sorted(available_drivers, 
                                                 key=lambda x: int(x))
            if available_drivers:
                self.output.insert(tk.END, 
                    f"Available driver versions: {', '.join(available_drivers)}\n")

    def check_cuda_status(self):
        """Check CUDA installation status"""
        self.output.insert(tk.END, "\nChecking CUDA status...\n")
        
        # Check CUDA version
        output, error, code = self.run_command("nvcc --version")
        if code == 0:
            version_match = re.search(r"release ([\d\.]+)", output)
            if version_match:
                self.cuda_info['version'] = version_match.group(1)
                self.output.insert(tk.END, 
                    f"CUDA version: {self.cuda_info['version']}\n")
        else:
            self.cuda_info['installed'] = False
            self.output.insert(tk.END, "CUDA is not installed\n")
        
        # Check CUDA paths
        cuda_paths = ['/usr/local/cuda', '/usr/local/cuda-*']
        found_paths = []
        for path_pattern in cuda_paths:
            for path in Path('/').glob(path_pattern[1:]):
                if path.exists():
                    found_paths.append(str(path))
        
        if found_paths:
            self.cuda_info['paths'] = found_paths
            self.output.insert(tk.END, 
                f"CUDA installations found in: {', '.join(found_paths)}\n")

    def check_gpu_performance(self):
        """Check GPU performance metrics"""
        if not self.gpu_info.get('present', False):
            return
        
        self.output.insert(tk.END, "\nChecking GPU performance...\n")
        
        # Get GPU utilization
        output, error, code = self.run_command(
            "nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader")
        if code == 0:
            try:
                utilization = int(output.strip().replace('%', ''))
                self.gpu_info['utilization'] = utilization
                self.output.insert(tk.END, f"GPU Utilization: {utilization}%\n")
            except ValueError:
                pass
        
        # Get temperature
        output, error, code = self.run_command(
            "nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader")
        if code == 0:
            try:
                temperature = int(output.strip())
                self.gpu_info['temperature'] = temperature
                self.output.insert(tk.END, f"GPU Temperature: {temperature}°C\n")
            except ValueError:
                pass

    def check_gpu_issues(self):
        """Check for common GPU issues"""
        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, "=== GPU Issue Analysis ===\n\n")
        
        issues_found = False
        
        # Check if GPU is detected but driver not loaded
        if self.gpu_info.get('present', False) and not self.driver_info.get('loaded', False):
            self.output.insert(tk.END, "⚠️ GPU detected but driver not loaded\n")
            issues_found = True
        
        # Check driver version compatibility
        if 'model' in self.gpu_info and 'version' in self.driver_info:
            if not self.check_driver_compatibility():
                self.output.insert(tk.END, "⚠️ Driver might not be optimal for GPU model\n")
                issues_found = True
        
        # Check temperature
        if 'temperature' in self.gpu_info:
            temp = self.gpu_info['temperature']
            if temp > 80:
                self.output.insert(tk.END, f"⚠️ High GPU temperature: {temp}°C\n")
                issues_found = True
        
        # Check memory usage
        if 'memory' in self.gpu_info:
            mem = self.gpu_info['memory']
            usage_percent = (mem['used'] / mem['total']) * 100
            if usage_percent > 90:
                self.output.insert(tk.END, 
                    f"⚠️ High memory usage: {usage_percent:.1f}%\n")
                issues_found = True
        
        # Check power usage
        if 'power' in self.gpu_info:
            power = self.gpu_info['power']
            if power['current'] > power['max'] * 0.9:
                self.output.insert(tk.END, 
                    "⚠️ GPU power usage near maximum\n")
                issues_found = True
        
        if not issues_found:
            self.output.insert(tk.END, "No major GPU issues detected.\n")

    def check_driver_compatibility(self):
        """Check if current driver is compatible with GPU"""
        try:
            # Get recommended driver version from NVIDIA website
            gpu_model = self.gpu_info['model']
            driver_version = self.driver_info['version']
            
            # This would need to be implemented with actual NVIDIA API
            # For now, we'll use a simple heuristic
            return True
        except Exception:
            return False

    def install_driver(self):
        """Install or update NVIDIA driver"""
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return
        
        try:
            self.output.delete(1.0, tk.END)
            self.output.insert(tk.END, "=== Installing NVIDIA Driver ===\n\n")
            
            # Backup current configuration
            self.backup_gpu_config()
            
            # Remove existing NVIDIA drivers
            self.output.insert(tk.END, "Removing existing NVIDIA drivers...\n")
            self.run_command("apt-get remove --purge '^nvidia-.*'")
            
            # Add graphics-drivers PPA
            self.output.insert(tk.END, "Adding graphics-drivers PPA...\n")
            self.run_command("add-apt-repository ppa:graphics-drivers/ppa -y")
            self.run_command("apt-get update")
            
            # Determine best driver version
            recommended_driver = self.get_recommended_driver()
            
            if recommended_driver:
                # Install driver
                self.output.insert(tk.END, 
                    f"Installing NVIDIA driver {recommended_driver}...\n")
                output, error, code = self.run_command(
                    f"apt-get install -y nvidia-driver-{recommended_driver}")
                
                if code != 0:
                    raise Exception(f"Driver installation failed: {error}")
                
                # Update initramfs
                self.output.insert(tk.END, "Updating initramfs...\n")
                self.run_command("update-initramfs -u")
                
                self.output.insert(tk.END, 
                    "Driver installation complete. Please reboot your system.\n")
            else:
                raise Exception("Could not determine recommended driver version")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install driver: {str(e)}")

    def backup_gpu_config(self):
        """Backup current GPU configuration"""
        try:
            backup_dir = Path.home() / "nvidia_backup"
            backup_dir.mkdir(exist_ok=True)
            
            # Backup xorg.conf if it exists
            xorg_conf = Path("/etc/X11/xorg.conf")
            if xorg_conf.exists():
                shutil.copy2(xorg_conf, 
                    backup_dir / f"xorg.conf.{datetime.now().strftime('%Y%m%d')}")
            
            # Backup NVIDIA settings
            output, error, code = self.run_command("nvidia-settings --save-rc")
            if code == 0:
                nvidia_rc = Path.home() / ".nvidia-settings-rc"
                if nvidia_rc.exists():
                    shutil.copy2(nvidia_rc, 
                        backup_dir / f"nvidia-settings-rc.{datetime.now().strftime('%Y%m%d')}")
            
            # Backup current driver info
            if self.driver_info:
                with open(backup_dir / f"driver_info_{datetime.now().strftime('%Y%m%d')}.json", 'w') as f:
                    json.dump(self.driver_info, f, indent=4)
            
            self.output.insert(tk.END, f"Configuration backed up to {backup_dir}\n")
            
        except Exception as e:
            raise Exception(f"Failed to backup configuration: {str(e)}")

    def get_recommended_driver(self):
        """Determine recommended driver version for GPU"""
        try:
            if not self.gpu_info.get('model'):
                raise Exception("GPU model not detected")
            
            # Get available drivers
            if not self.driver_info.get('available'):
                self.check_driver_status()
            
            available_drivers = self.driver_info.get('available', [])
            if not available_drivers:
                raise Exception("No available drivers found")
            
            # For newer GPUs, prefer latest driver
            latest_driver = max(available_drivers, key=lambda x: int(x))
            
            # Check if GPU is legacy
            gpu_model = self.gpu_info['model'].lower()
            legacy_keywords = ['gt 7', 'gtx 7', 'gt 6', 'gtx 6']
            is_legacy = any(kw in gpu_model for kw in legacy_keywords)
            
            if is_legacy:
                # For legacy GPUs, prefer stable driver (470 or 390 series)
                legacy_drivers = ['470', '390']
                for driver in legacy_drivers:
                    if driver in available_drivers:
                        return driver
            
            return latest_driver
            
        except Exception as e:
            self.output.insert(tk.END, f"Error determining recommended driver: {str(e)}\n")
            return None

    def install_cuda(self):
        """Install CUDA toolkit"""
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return
        
        try:
            self.output.delete(1.0, tk.END)
            self.output.insert(tk.END, "=== Installing CUDA Toolkit ===\n\n")
            
            # Check system compatibility
            if not self.check_cuda_compatibility():
                raise Exception("System not compatible with CUDA installation")
            
            # Get latest CUDA version
            cuda_version = self.get_latest_cuda_version()
            
            # Download CUDA installer
            self.output.insert(tk.END, f"Downloading CUDA {cuda_version}...\n")
            installer_path = self.download_cuda_installer(cuda_version)
            
            # Install CUDA
            self.output.insert(tk.END, "Installing CUDA...\n")
            output, error, code = self.run_command(f"sh {installer_path} --silent --toolkit")
            
            if code != 0:
                raise Exception(f"CUDA installation failed: {error}")
            
            # Set up environment variables
            self.setup_cuda_environment(cuda_version)
            
            self.output.insert(tk.END, "CUDA installation complete.\n")
            self.output.insert(tk.END, "Please reboot your system.\n")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install CUDA: {str(e)}")

    def check_cuda_compatibility(self):
        """Check if system is compatible with CUDA"""
        try:
            # Check GPU compatibility
            if not self.gpu_info.get('present'):
                raise Exception("No NVIDIA GPU detected")
            
            # Check driver compatibility
            if not self.driver_info.get('version'):
                raise Exception("NVIDIA driver not installed")
            
            # Check system requirements
            # Check gcc version
            output, error, code = self.run_command("gcc --version")
            if code != 0:
                raise Exception("GCC not installed")
            
            # Check kernel headers
            output, error, code = self.run_command("dpkg -l | grep linux-headers")
            if code != 0:
                raise Exception("Kernel headers not installed")
            
            return True
            
        except Exception as e:
            self.output.insert(tk.END, f"Compatibility check failed: {str(e)}\n")
            return False

    def get_latest_cuda_version(self):
        """Get latest compatible CUDA version"""
        try:
            # This would need to be implemented with actual NVIDIA API
            # For now, return a default version
            return "11.8"
        except Exception:
            return "11.8"  # fallback version

    def download_cuda_installer(self, version):
        """Download CUDA installer"""
        try:
            # Create download directory
            download_dir = Path.home() / "nvidia_installers"
            download_dir.mkdir(exist_ok=True)
            
            # Construct download URL (this would need to be updated with actual NVIDIA URLs)
            url = f"https://developer.nvidia.com/cuda-{version}-local-linux"
            
            # Download file
            installer_path = download_dir / f"cuda_{version}_linux.run"
            
            # This is a placeholder - actual implementation would need to use
            # NVIDIA's download API or web scraping
            self.output.insert(tk.END, 
                "Please download CUDA installer manually from NVIDIA website\n")
            
            return str(installer_path)
            
        except Exception as e:
            raise Exception(f"Failed to download CUDA installer: {str(e)}")

    def setup_cuda_environment(self, version):
        """Set up CUDA environment variables"""
        try:
            # Create or update CUDA profile
            profile_path = Path("/etc/profile.d/cuda.sh")
            
            cuda_profile = f"""
export PATH=/usr/local/cuda-{version}/bin${PATH:+:${PATH}}
export LD_LIBRARY_PATH=/usr/local/cuda-{version}/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
"""
            
            with open(profile_path, 'w') as f:
                f.write(cuda_profile)
            
            # Update ldconfig
            with open("/etc/ld.so.conf.d/cuda.conf", 'w') as f:
                f.write(f"/usr/local/cuda-{version}/lib64\n")
            
            self.run_command("ldconfig")
            
        except Exception as e:
            raise Exception(f"Failed to setup CUDA environment: {str(e)}")

    def optimize_gpu_settings(self):
        """Optimize GPU settings for performance"""
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return
        
        try:
            self.output.delete(1.0, tk.END)
            self.output.insert(tk.END, "=== Optimizing GPU Settings ===\n\n")
            
            # Create optimal xorg.conf
            self.create_optimal_xorg_conf()
            
            # Set optimal nvidia-settings
            self.set_optimal_nvidia_settings()
            
            # Configure power management
            self.configure_power_management()
            
            # Set up overclocking if supported
            self.setup_overclocking()
            
            self.output.insert(tk.END, "GPU optimization complete.\n")
            self.output.insert(tk.END, "Please reboot your system.\n")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to optimize GPU settings: {str(e)}")

    def create_optimal_xorg_conf(self):
        """Create optimal Xorg configuration"""
        try:
            self.output.insert(tk.END, "Creating optimal Xorg configuration...\n")
            
            # Generate new xorg.conf
            output, error, code = self.run_command("nvidia-xconfig --cool-bits=28")
            
            if code != 0:
                raise Exception(f"Failed to create xorg.conf: {error}")
            
            # Modify for optimal performance
            xorg_conf = Path("/etc/X11/xorg.conf")
            if xorg_conf.exists():
                with open(xorg_conf, 'r') as f:
                    config = f.read()
                
                # Add performance options
                if "Section \"Device\"" in config:
                    config = config.replace(
                        "Section \"Device\"",
                        """Section "Device"
    Option "RegistryDwords" "PerfLevelSrc=0x2222"
    Option "PowerMizerMode" "1"
    Option "TripleBuffer" "True"
    Option "UsePageAttributeTable" "True"
"""
                    )
                
                with open(xorg_conf, 'w') as f:
                    f.write(config)
            
        except Exception as e:
            raise Exception(f"Failed to optimize Xorg configuration: {str(e)}")

    def set_optimal_nvidia_settings(self):
        """Set optimal NVIDIA driver settings"""
        try:
            self.output.insert(tk.END, "Setting optimal NVIDIA settings...\n")
            
            # Performance mode
            self.run_command(
                "nvidia-settings -a '[gpu:0]/GpuPowerMizerMode=1'")
            
            # Maximum performance
            self.run_command(
                "nvidia-settings -a '[gpu:0]/GPUGraphicsClockOffset[3]=0'")
            self.run_command(
                "nvidia-settings -a '[gpu:0]/GPUMemoryTransferRateOffset[3]=0'")
            
            # Force full composition pipeline
            self.run_command(
                "nvidia-settings --assign CurrentMetaMode=\"nvidia-auto-select +0+0 { ForceFullCompositionPipeline = On }\"")
            
        except Exception as e:
            raise Exception(f"Failed to set optimal NVIDIA settings: {str(e)}")

    def configure_power_management(self):
        """Configure GPU power management"""
        try:
            self.output.insert(tk.END, "Configuring power management...\n")
            
            # Set maximum performance mode
            self.run_command(
                "nvidia-smi -pm 1")  # Enable persistent mode
            
            # Set power limit to maximum
            if 'power' in self.gpu_info:
                max_power = self.gpu_info['power']['max']
                self.run_command(
                    f"nvidia-smi -pl {max_power}")
            
        except Exception as e:
            raise Exception(f"Failed to configure power management: {str(e)}")

    def setup_overclocking(self):
        """Set up GPU overclocking if supported"""
        try:
            self.output.insert(tk.END, "Checking overclocking support...\n")
            
            # Check if overclocking is supported
            output, error, code = self.run_command(
                "nvidia-smi -q -d SUPPORTED_CLOCKS")
            
            if code == 0 and "Supported Clocks" in output:
                self.output.insert(tk.END, "GPU supports overclocking\n")
                
                # Enable overclocking
                self.run_command("nvidia-xconfig --cool-bits=28")
                self.run_command("nvidia-smi -pm 1")
                
                # Set conservative overclock
                self.run_command(
                    "nvidia-settings -a '[gpu:0]/GPUGraphicsClockOffset[3]=50'")
                self.run_command(
                    "nvidia-settings -a '[gpu:0]/GPUMemoryTransferRateOffset[3]=100'")
            else:
                self.output.insert(tk.END, "GPU does not support overclocking\n")
            
        except Exception as e:
            self.output.insert(tk.END, f"Failed to setup overclocking: {str(e)}\n")

    def generate_gpu_report(self):
        """Generate comprehensive GPU report"""
        try:
            filename = f"gpu_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(filename, 'w') as f:
                f.write("NVIDIA GPU Report\n")
                f.write("=" * 50 + "\n\n")
                
                # GPU Information
                f.write("GPU Information:\n")
                f.write("-" * 20 + "\n")
                if self.gpu_info:
                    for key, value in self.gpu_info.items():
                        f.write(f"{key}: {value}\n")
                
                # Driver Information
                f.write("\nDriver Information:\n")
                f.write("-" * 20 + "\n")
                if self.driver_info:
                    for key, value in self.driver_info.items():
                        f.write(f"{key}: {value}\n")
                
                # CUDA Information
                f.write("\nCUDA Information:\n")
                f.write("-" * 20 + "\n")
                if self.cuda_info:
                    for key, value in self.cuda_info.items():
                        f.write(f"{key}: {value}\n")
                
                # Performance Information
                f.write("\nPerformance Information:\n")
                f.write("-" * 20 + "\n")
                output, error, code = self.run_command("nvidia-smi --query-gpu=utilization.gpu,utilization.memory,temperature.gpu,power.draw,clocks.gr,clocks.mem --format=csv")
                if code == 0:
                    f.write(output)
                
                # Configuration Files
                f.write("\nConfiguration Files:\n")
                f.write("-" * 20 + "\n")
                
                # xorg.conf
                if Path("/etc/X11/xorg.conf").exists():
                    with open("/etc/X11/xorg.conf", 'r') as xorg:
                        f.write("\nxorg.conf:\n")
                        f.write(xorg.read())
                
                # nvidia-settings
                if Path.home().joinpath(".nvidia-settings-rc").exists():
                    with open(Path.home().joinpath(".nvidia-settings-rc"), 'r') as settings:
                        f.write("\nnvidia-settings:\n")
                        f.write(settings.read())
            
            messagebox.showinfo("Success", f"GPU report generated: {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")