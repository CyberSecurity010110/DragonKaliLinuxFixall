# Part 20: Tweaks Module
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import subprocess
import os
import pwd
import grp
import shutil
import re
from pathlib import Path
from datetime import datetime
import json

class TweaksModule:
    def __init__(self, parent_notebook):
        # Create Tweaks tab
        self.tweaks_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.tweaks_frame, text='Tweaks')
        
        # Initialize variables
        self.current_user = os.getenv('USER')
        self.is_admin = os.getuid() == 0 or self.current_user in grp.getgrnam('sudo').gr_mem
        self.startup_logs = []
        
        # Create interface
        self.create_interface()
        
        # Load initial startup logs
        self.load_startup_logs()

    def create_interface(self):
        # Create notebook for different sections
        self.notebook = ttk.Notebook(self.tweaks_frame)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create tabs
        self.create_user_tweaks_tab()
        self.create_system_settings_tab()
        self.create_startup_logs_tab()
        self.create_appearance_tab()

    def create_user_tweaks_tab(self):
        """Create tab for user-specific tweaks"""
        user_frame = ttk.Frame(self.notebook)
        self.notebook.add(user_frame, text='User Tweaks')
        
        # Create scrollable frame
        canvas = tk.Canvas(user_frame)
        scrollbar = ttk.Scrollbar(user_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Sudo without password option
        sudo_frame = ttk.LabelFrame(scrollable_frame, text="Sudo Privileges")
        sudo_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(sudo_frame, 
                 text="Enable sudo without password for current user:").pack(pady=5)
        ttk.Button(sudo_frame, 
                  text="Configure Sudo Access",
                  command=self.configure_sudo).pack(pady=5)
        
        # Autologin option
        if self.is_admin:
            autologin_frame = ttk.LabelFrame(scrollable_frame, text="Automatic Login")
            autologin_frame.pack(fill='x', padx=5, pady=5)
            
            ttk.Label(autologin_frame, 
                     text="Enable automatic login at boot:").pack(pady=5)
            ttk.Button(autologin_frame, 
                      text="Configure Autologin",
                      command=self.configure_autologin).pack(pady=5)
        
        # Shell customization
        shell_frame = ttk.LabelFrame(scrollable_frame, text="Shell Customization")
        shell_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(shell_frame, 
                  text="Install Custom Bash Aliases",
                  command=self.install_bash_aliases).pack(pady=5)
        ttk.Button(shell_frame, 
                  text="Install Custom PS1 Prompt",
                  command=self.install_custom_prompt).pack(pady=5)
        
        # Keyboard shortcuts
        shortcut_frame = ttk.LabelFrame(scrollable_frame, text="Keyboard Shortcuts")
        shortcut_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(shortcut_frame, 
                  text="Add Custom Shortcuts",
                  command=self.configure_shortcuts).pack(pady=5)
        
        # Pack the scrollable area
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_system_settings_tab(self):
        """Create tab for system settings shortcuts"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text='System Settings')
        
        # Create grid of setting buttons
        settings = [
            ("Display Settings", "gnome-control-center display"),
            ("Date & Time Settings", "gnome-control-center datetime"),
            ("Network Settings", "gnome-control-center network"),
            ("Power Settings", "gnome-control-center power"),
            ("Sound Settings", "gnome-control-center sound"),
            ("Keyboard Settings", "gnome-control-center keyboard"),
            ("Mouse Settings", "gnome-control-center mouse"),
            ("Language Settings", "gnome-control-center region"),
            ("User Settings", "gnome-control-center user-accounts"),
            ("System Info", "gnome-control-center info-overview")
        ]
        
        for i, (name, command) in enumerate(settings):
            ttk.Button(settings_frame, 
                      text=name,
                      command=lambda cmd=command: self.run_command(cmd)).grid(
                          row=i//2, column=i%2, padx=5, pady=5, sticky='nsew'
                      )
        
        # Configure grid weights
        for i in range(5):
            settings_frame.grid_rowconfigure(i, weight=1)
        settings_frame.grid_columnconfigure(0, weight=1)
        settings_frame.grid_columnconfigure(1, weight=1)

    def create_startup_logs_tab(self):
        """Create tab for startup logs analysis"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text='Startup Logs')
        
        # Create top panel with buttons
        button_panel = ttk.Frame(logs_frame)
        button_panel.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(button_panel, 
                  text="Refresh Logs",
                  command=self.load_startup_logs).pack(side='left', padx=5)
        
        ttk.Button(button_panel, 
                  text="Analyze Issues",
                  command=self.analyze_startup_issues).pack(side='left', padx=5)
        
        ttk.Button(button_panel, 
                  text="Fix Selected Issues",
                  command=self.fix_startup_issues).pack(side='left', padx=5)
        
        # Create log display area
        log_container = ttk.Frame(logs_frame)
        log_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create treeview for logs
        self.log_tree = ttk.Treeview(log_container, 
                                    columns=('timestamp', 'type', 'message'),
                                    show='headings')
        
        self.log_tree.heading('timestamp', text='Timestamp')
        self.log_tree.heading('type', text='Type')
        self.log_tree.heading('message', text='Message')
        
        # Add scrollbars
        y_scroll = ttk.Scrollbar(log_container, orient='vertical',
                                command=self.log_tree.yview)
        x_scroll = ttk.Scrollbar(log_container, orient='horizontal',
                                command=self.log_tree.xview)
        
        self.log_tree.configure(yscrollcommand=y_scroll.set,
                              xscrollcommand=x_scroll.set)
        
        # Pack elements
        self.log_tree.pack(side='left', fill='both', expand=True)
        y_scroll.pack(side='right', fill='y')
        x_scroll.pack(side='bottom', fill='x')

    def create_appearance_tab(self):
        """Create tab for appearance settings"""
        appearance_frame = ttk.Frame(self.notebook)
        self.notebook.add(appearance_frame, text='Appearance')
        
        # Wallpaper section
        wallpaper_frame = ttk.LabelFrame(appearance_frame, text="Wallpaper")
        wallpaper_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(wallpaper_frame, 
                  text="Choose Wallpaper",
                  command=self.set_wallpaper).pack(pady=5)
        
        # Theme section
        theme_frame = ttk.LabelFrame(appearance_frame, text="Theme")
        theme_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(theme_frame, text="Select Theme:").pack(pady=5)
        themes = ['Default', 'Dark', 'Light']
        theme_var = tk.StringVar(value='Default')
        
        for theme in themes:
            ttk.Radiobutton(theme_frame, 
                          text=theme,
                          variable=theme_var,
                          value=theme,
                          command=lambda: self.set_theme(theme_var.get())).pack(pady=2)
        
        # Font settings
        font_frame = ttk.LabelFrame(appearance_frame, text="Font Settings")
        font_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(font_frame, 
                  text="Configure Fonts",
                  command=self.configure_fonts).pack(pady=5)

    def run_command(self, command: str, shell: bool = False) -> tuple:
        """Run system command and return output and error"""
        try:
            if shell:
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True)
            else:
                process = subprocess.Popen(command.split(), stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, text=True)
            output, error = process.communicate()
            return output.strip(), error.strip(), process.returncode
        except Exception as e:
            return "", str(e), 1

    def configure_sudo(self):
        """Configure sudo without password for current user"""
        try:
            # Check if user already has sudo without password
            sudoers_file = "/etc/sudoers"
            backup_file = f"{sudoers_file}.bak"
            
            # Create backup
            if not os.path.exists(backup_file):
                shutil.copy2(sudoers_file, backup_file)
            
            # Check current configuration
            with open(sudoers_file, 'r') as f:
                content = f.read()
                if f"{self.current_user} ALL=(ALL) NOPASSWD: ALL" in content:
                    messagebox.showinfo("Info", "Sudo without password is already configured")
                    return
            
            # Add configuration
            command = f'echo "{self.current_user} ALL=(ALL) NOPASSWD: ALL" | sudo EDITOR="tee -a" visudo'
            _, error, code = self.run_command(command, shell=True)
            
            if code == 0:
                messagebox.showinfo("Success", "Sudo without password configured successfully")
            else:
                messagebox.showerror("Error", f"Failed to configure sudo: {error}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to configure sudo: {str(e)}")

    def configure_autologin(self):
        """Configure automatic login for current user"""
        try:
            if not self.is_admin:
                messagebox.showerror("Error", "Admin privileges required")
                return
            
            # Configure GDM autologin
            gdm_config = "/etc/gdm3/custom.conf"
            
            # Create backup
            if not os.path.exists(f"{gdm_config}.bak"):
                shutil.copy2(gdm_config, f"{gdm_config}.bak")
            
            with open(gdm_config, 'r') as f:
                content = f.read()
            
            if '[daemon]' not in content:
                content = '[daemon]\n' + content
            
            # Add or update autologin configuration
            if 'AutomaticLogin=' not in content:
                content = content.replace('[daemon]',
                                       f'[daemon]\nAutomaticLogin={self.current_user}\nAutomaticLoginEnable=True')
            
            with open(gdm_config, 'w') as f:
                f.write(content)
            
            messagebox.showinfo("Success", "Automatic login configured successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to configure autologin: {str(e)}")

    def install_bash_aliases(self):
        """Install custom bash aliases"""
        try:
            aliases = """
# Custom aliases
alias ll='ls -la'
alias update='sudo apt update && sudo apt upgrade -y'
alias clean='sudo apt autoremove -y && sudo apt autoclean'
alias myip='curl ifconfig.me'
alias ports='netstat -tulanp'
alias meminfo='free -m -l -t'
alias cpuinfo='lscpu'
alias ping='ping -c 5'
alias www='python3 -m http.server 8000'
alias mkdir='mkdir -pv'
alias wget='wget -c'
"""
            
            aliases_file = os.path.expanduser("~/.bash_aliases")
            
            # Backup existing file
            if os.path.exists(aliases_file):
                shutil.copy2(aliases_file, f"{aliases_file}.bak")
            
            # Write new aliases
            with open(aliases_file, 'w') as f:
                f.write(aliases)
            
            messagebox.showinfo("Success", "Custom bash aliases installed successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install aliases: {str(e)}")

    def install_custom_prompt(self):
        """Install custom PS1 prompt"""
        try:
            custom_ps1 = """
# Custom PS1 prompt
export PS1='\\[\\033[01;32m\\]\\u@\\h\\[\\033[00m\\]:\\[\\033[01;34m\\]\\w\\[\\033[00m\\]\\$ '
"""
            
            bashrc = os.path.expanduser("~/.bashrc")
            
            # Backup existing file
            if not os.path.exists(f"{bashrc}.bak"):
                shutil.copy2(bashrc, f"{bashrc}.bak")
            
            # Add custom PS1
            with open(bashrc, 'a') as f:
                f.write(custom_ps1)
            
            messagebox.showinfo("Success", "Custom PS1 prompt installed successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install custom prompt: {str(e)}")

    def configure_shortcuts(self):
        """Configure custom keyboard shortcuts"""
        try:
            shortcuts = {
                "terminal": "<Control><Alt>t",
                "browser": "<Super>w",
                "file-manager": "<Super>e",
                "screenshot": "<Shift>Print",
            }
            
            for name, key in shortcuts.items():
                command = f"gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/{name}/ binding '{key}'"
                self.run_command(command, shell=True)
            
            messagebox.showinfo("Success", "Custom shortcuts configured successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to configure shortcuts: {str(e)}")

    def load_startup_logs(self):
        """Load and parse system startup logs"""
        try:
            # Clear existing logs
            self.log_tree.delete(*self.log_tree.get_children())
            self.startup_logs = []
            
            # Get journal logs since last boot
            output, _, _ = self.run_command("journalctl -b 0", shell=True)
            
            for line in output.splitlines():
                if any(level in line.upper() for level in ['ERROR', 'WARNING', 'FAIL']):
                    try:
                        # Parse log line
                        parts = line.split(' ', 3)
                        timestamp = ' '.join(parts[0:2])
                        
                        if 'ERROR' in line.upper():
                            log_type = 'ERROR'
                        elif 'WARNING' in line.upper():
                            log_type = 'WARNING'
                        else:
                            log_type = 'FAIL'
                        
                        message = parts[-1]
                        
                        # Add to tree and internal list
                        self.log_tree.insert('', 'end', values=(timestamp, log_type, message))
                        self.startup_logs.append({
                            'timestamp': timestamp,
                            'type': log_type,
                            'message': message
                        })
                    except:
                        continue
            
            # Color-code by type
            for item in self.log_tree.get_children():
                if self.log_tree.item(item)['values'][1] == 'ERROR':
                    self.log_tree.tag_configure('error', foreground='red')
                    self.log_tree.item(item, tags=('error',))
                elif self.log_tree.item(item)['values'][1] == 'WARNING':
                    self.log_tree.tag_configure('warning', foreground='orange')
                    self.log_tree.item(item, tags=('warning',))
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load startup logs: {str(e)}")

    def analyze_startup_issues(self):
        """Analyze startup logs for common issues"""
        try:
            issues = []
            solutions = []
            
            for log in self.startup_logs:
                message = log['message'].lower()
                
                # Missing modules
                if 'module not found' in message or 'failed to load module' in message:
                    module = re.search(r'module [\'"](.+?)[\'"]', message)
                    if module:
                        issues.append(f"Missing module: {module.group(1)}")
                        solutions.append(f"Try installing package containing {module.group(1)}")
                
                # Failed services
                elif 'failed to start' in message:
                    service = re.search(r'failed to start (.+?)\.', message)
                    if service:
                        issues.append(f"Failed service: {service.group(1)}")
                        solutions.append(f"Check service status and logs for {service.group(1)}")
                
                # Hardware issues
                elif any(x in message for x in ['firmware', 'hardware', 'driver']):
                    issues.append(f"Hardware/Driver issue: {log['message']}")
                    solutions.append("Check hardware connections and driver installation")
                
                # Permission issues
                elif 'permission denied' in message:
                    issues.append(f"Permission issue: {log['message']}")
                    solutions.append("Check file/directory permissions")
            
            if issues:
                # Show analysis results
                analysis_window = tk.Toplevel()
                analysis_window.title("Startup Issues Analysis")
                analysis_window.geometry("600x400")
                
                text_area = scrolledtext.ScrolledText(analysis_window)
                text_area.pack(fill='both', expand=True, padx=5, pady=5)
                
                text_area.insert(tk.END, "=== Startup Issues Analysis ===\n\n")
                for i, (issue, solution) in enumerate(zip(issues, solutions)):
                    text_area.insert(tk.END, f"Issue {i+1}:\n{issue}\n")
                    text_area.insert(tk.END, f"Suggested Solution:\n{solution}\n\n")
                
                text_area.configure(state='disabled')
            else:
                messagebox.showinfo("Analysis", "No significant issues found")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to analyze issues: {str(e)}")

    def fix_startup_issues(self):
        """Attempt to fix selected startup issues"""
        selection = self.log_tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select issues to fix")
            return
        
        try:
            fixed = []
            failed = []
            
            for item in selection:
                values = self.log_tree.item(item)['values']
                message = values[2].lower()
                
                # Try to fix common issues
                if 'module not found' in message:
                    # Try to install missing module
                    module = re.search(r'module [\'"](.+?)[\'"]', message)
                    if module:
                        cmd = f"sudo apt-get install -y {module.group(1)}*"
                        _, error, code = self.run_command(cmd, shell=True)
                        if code == 0:
                            fixed.append(f"Installed module {module.group(1)}")
                        else:
                            failed.append(f"Failed to install {module.group(1)}: {error}")
                
                elif 'failed to start' in message:
                    # Try to restart failed service
                    service = re.search(r'failed to start (.+?)\.', message)
                    if service:
                        cmd = f"sudo systemctl restart {service.group(1)}"
                        _, error, code = self.run_command(cmd, shell=True)
                        if code == 0:
                            fixed.append(f"Restarted service {service.group(1)}")
                        else:
                            failed.append(f"Failed to restart {service.group(1)}: {error}")
                
                elif 'permission denied' in message:
                    # Try to fix permissions
                    path = re.search(r'permission denied.*[\'"](.+?)[\'"]', message)
                    if path:
                        cmd = f"sudo chmod -R 644 {path.group(1)}"
                        _, error, code = self.run_command(cmd, shell=True)
                        if code == 0:
                            fixed.append(f"Fixed permissions for {path.group(1)}")
                        else:
                            failed.append(f"Failed to fix permissions: {error}")
            
            # Show results
            result = "Fix Results:\n\n"
            if fixed:
                result += "Successfully fixed:\n" + "\n".join(fixed) + "\n\n"
            if failed:
                result += "Failed to fix:\n" + "\n".join(failed)
            
            messagebox.showinfo("Results", result)
            
            # Refresh logs
            self.load_startup_logs()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fix issues: {str(e)}")

    def set_wallpaper(self):
        """Set system wallpaper"""
        try:
            file_path = filedialog.askopenfilename(
                title="Choose Wallpaper",
                filetypes=[
                    ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif"),
                    ("All files", "*.*")
                ]
            )
            
            if file_path:
                cmd = f"gsettings set org.gnome.desktop.background picture-uri 'file://{file_path}'"
                _, error, code = self.run_command(cmd, shell=True)
                
                if code == 0:
                    messagebox.showinfo("Success", "Wallpaper changed successfully")
                else:
                    messagebox.showerror("Error", f"Failed to change wallpaper: {error}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set wallpaper: {str(e)}")

    def set_theme(self, theme: str):
        """Set system theme"""
        try:
            if theme == 'Dark':
                self.run_command("gsettings set org.gnome.desktop.interface gtk-theme 'Adwaita-dark'")
            elif theme == 'Light':
                self.run_command("gsettings set org.gnome.desktop.interface gtk-theme 'Adwaita'")
            else:
                self.run_command("gsettings reset org.gnome.desktop.interface gtk-theme")
            
            messagebox.showinfo("Success", f"{theme} theme applied successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set theme: {str(e)}")

    def configure_fonts(self):
        """Configure system fonts"""
        try:
            # Launch font settings
            self.run_command("gnome-control-center font")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open font settings: {str(e)}")