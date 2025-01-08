# Part 10: Shell Configuration Management Module
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
import shutil
from pathlib import Path
import datetime
import difflib
from typing import Dict, List
import re

class ShellConfigModule:
    def __init__(self, parent_notebook):
        # Create shell config management tab
        self.shell_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.shell_frame, text='Shell Config')
        
        # Initialize paths and data structures
        self.config_files = {
            'bash': {
                'rc': Path.home() / '.bashrc',
                'profile': Path.home() / '.bash_profile',
                'aliases': Path.home() / '.bash_aliases'
            },
            'zsh': {
                'rc': Path.home() / '.zshrc',
                'profile': Path.home() / '.zprofile',
                'aliases': Path.home() / '.zsh_aliases'
            }
        }
        
        # Backup directory
        self.backup_dir = Path.home() / '.config' / 'shell_backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create interface
        self.create_interface()
        
        # Load initial configurations
        self.load_configurations()

    def create_interface(self):
        """Create the shell configuration management interface"""
        # Create main paned window
        self.paned = ttk.PanedWindow(self.shell_frame, orient=tk.HORIZONTAL)
        self.paned.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create left panel (file list and controls)
        self.left_frame = ttk.Frame(self.paned)
        self.paned.add(self.left_frame)
        
        # Create shell selection
        shell_frame = ttk.LabelFrame(self.left_frame, text="Shell Type")
        shell_frame.pack(fill='x', padx=5, pady=5)
        
        self.shell_var = tk.StringVar(value='bash')
        ttk.Radiobutton(shell_frame, text="Bash", 
                       variable=self.shell_var, 
                       value='bash', 
                       command=self.on_shell_change).pack(side='left', padx=5)
        ttk.Radiobutton(shell_frame, text="Zsh", 
                       variable=self.shell_var, 
                       value='zsh', 
                       command=self.on_shell_change).pack(side='left', padx=5)
        
        # Create file list
        file_frame = ttk.LabelFrame(self.left_frame, text="Configuration Files")
        file_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.file_list = ttk.Treeview(file_frame, 
                                     columns=('path', 'status'),
                                     show='headings',
                                     selectmode='browse')
        self.file_list.heading('path', text='File')
        self.file_list.heading('status', text='Status')
        self.file_list.pack(fill='both', expand=True)
        
        # Bind selection event
        self.file_list.bind('<<TreeviewSelect>>', self.on_file_select)
        
        # Create control buttons
        control_frame = ttk.Frame(self.left_frame)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(control_frame, text="Backup", 
                  command=self.backup_config).pack(side='left', padx=2)
        ttk.Button(control_frame, text="Restore", 
                  command=self.restore_config).pack(side='left', padx=2)
        ttk.Button(control_frame, text="Source", 
                  command=self.source_config).pack(side='left', padx=2)
        
        # Create right panel (editor and diff view)
        self.right_frame = ttk.Frame(self.paned)
        self.paned.add(self.right_frame)
        
        # Create notebook for editor and diff view
        self.notebook = ttk.Notebook(self.right_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Create editor tab
        editor_frame = ttk.Frame(self.notebook)
        self.notebook.add(editor_frame, text="Editor")
        
        self.editor = scrolledtext.ScrolledText(editor_frame, wrap=tk.NONE)
        self.editor.pack(fill='both', expand=True)
        
        # Create line numbers
        self.line_numbers = tk.Text(editor_frame, width=4, padx=3, takefocus=0,
                                  border=0, background='lightgray',
                                  state='disabled')
        self.line_numbers.pack(side='left', fill='y')
        
        # Bind editor events
        self.editor.bind('<Key>', self.on_editor_change)
        self.editor.bind('<Return>', self.update_line_numbers)
        self.editor.bind('<BackSpace>', self.update_line_numbers)
        
        # Create diff view tab
        diff_frame = ttk.Frame(self.notebook)
        self.notebook.add(diff_frame, text="Changes")
        
        self.diff_view = scrolledtext.ScrolledText(diff_frame, wrap=tk.NONE)
        self.diff_view.pack(fill='both', expand=True)
        
        # Create status bar
        self.status_var = tk.StringVar()
        ttk.Label(self.shell_frame, textvariable=self.status_var).pack(
            fill='x', padx=5, pady=5)
        
        # Create save button
        ttk.Button(self.right_frame, text="Save Changes", 
                  command=self.save_changes).pack(pady=5)

    def load_configurations(self):
        """Load shell configurations and update file list"""
        self.file_list.delete(*self.file_list.get_children())
        
        shell_type = self.shell_var.get()
        config_paths = self.config_files[shell_type]
        
        for config_type, path in config_paths.items():
            status = "Exists" if path.exists() else "Not Found"
            self.file_list.insert('', 'end', 
                                values=(config_type, status),
                                tags=(config_type,))

    def on_shell_change(self):
        """Handle shell type change"""
        self.load_configurations()
        self.clear_editor()

    def on_file_select(self, event):
        """Handle file selection"""
        selection = self.file_list.selection()
        if not selection:
            return
        
        config_type = self.file_list.item(selection[0])['tags'][0]
        shell_type = self.shell_var.get()
        file_path = self.config_files[shell_type][config_type]
        
        if file_path.exists():
            self.load_file_content(file_path)
        else:
            self.clear_editor()
            self.status_var.set(f"File not found: {file_path}")

    def load_file_content(self, file_path: Path):
        """Load file content into editor"""
        try:
            content = file_path.read_text()
            self.editor.delete('1.0', tk.END)
            self.editor.insert('1.0', content)
            self.update_line_numbers()
            self.status_var.set(f"Loaded: {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")

    def clear_editor(self):
        """Clear editor content"""
        self.editor.delete('1.0', tk.END)
        self.diff_view.delete('1.0', tk.END)
        self.update_line_numbers()

    def update_line_numbers(self, event=None):
        """Update line numbers in editor"""
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        
        count = self.editor.get('1.0', tk.END).count('\n')
        lines = '\n'.join(str(i) for i in range(1, count + 1))
        self.line_numbers.insert('1.0', lines)
        self.line_numbers.config(state='disabled')

    def on_editor_change(self, event=None):
        """Handle editor content changes"""
        self.update_line_numbers()
        self.update_diff_view()

    def update_diff_view(self):
        """Update diff view with changes"""
        selection = self.file_list.selection()
        if not selection:
            return
        
        config_type = self.file_list.item(selection[0])['tags'][0]
        shell_type = self.shell_var.get()
        file_path = self.config_files[shell_type][config_type]
        
        if not file_path.exists():
            return
        
        # Get original content
        original = file_path.read_text().splitlines()
        # Get current content
        current = self.editor.get('1.0', tk.END).splitlines()
        
        # Generate diff
        diff = difflib.unified_diff(original, current, 
                                  fromfile='Original',
                                  tofile='Modified')
        
        # Update diff view
        self.diff_view.delete('1.0', tk.END)
        for line in diff:
            if line.startswith('+'):
                self.diff_view.insert(tk.END, line + '\n', 'added')
            elif line.startswith('-'):
                self.diff_view.insert(tk.END, line + '\n', 'removed')
            else:
                self.diff_view.insert(tk.END, line + '\n')
        
        # Configure tags
        self.diff_view.tag_configure('added', foreground='green')
        self.diff_view.tag_configure('removed', foreground='red')

    def backup_config(self):
        """Backup selected configuration file"""
        selection = self.file_list.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a configuration file")
            return
        
        config_type = self.file_list.item(selection[0])['tags'][0]
        shell_type = self.shell_var.get()
        file_path = self.config_files[shell_type][config_type]
        
        if not file_path.exists():
            messagebox.showerror("Error", "File does not exist")
            return
        
        try:
            # Create backup filename with timestamp
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.backup_dir / f"{file_path.name}_{timestamp}.bak"
            
            # Copy file
            shutil.copy2(file_path, backup_path)
            
            self.status_var.set(f"Backup created: {backup_path}")
            messagebox.showinfo("Success", "Backup created successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create backup: {str(e)}")

    def restore_config(self):
        """Restore configuration from backup"""
        selection = self.file_list.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a configuration file")
            return
        
        config_type = self.file_list.item(selection[0])['tags'][0]
        shell_type = self.shell_var.get()
        file_path = self.config_files[shell_type][config_type]
        
        # Find available backups
        backups = list(self.backup_dir.glob(f"{file_path.name}_*.bak"))
        if not backups:
            messagebox.showinfo("Info", "No backups found")
            return
        
        # Create restore dialog
        dialog = RestoreDialog(self.shell_frame, backups)
        if dialog.result:
            try:
                # Restore selected backup
                shutil.copy2(dialog.result, file_path)
                self.load_file_content(file_path)
                self.status_var.set("Configuration restored successfully")
                messagebox.showinfo("Success", "Configuration restored")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to restore: {str(e)}")

    def source_config(self):
        """Source the configuration file"""
        selection = self.file_list.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a configuration file")
            return
        
        config_type = self.file_list.item(selection[0])['tags'][0]
        shell_type = self.shell_var.get()
        file_path = self.config_files[shell_type][config_type]
        
        if not file_path.exists():
            messagebox.showerror("Error", "File does not exist")
            return
        
        try:
            # Source the configuration
            if shell_type == 'bash':
                cmd = f"source {file_path}"
            else:  # zsh
                cmd = f"source {file_path}"
            
            # Execute in current shell
            subprocess.run(['bash', '-c', cmd], check=True)
            
            self.status_var.set("Configuration sourced successfully")
            messagebox.showinfo("Success", "Configuration sourced")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to source configuration: {str(e)}")

    def save_changes(self):
        """Save changes to configuration file"""
        selection = self.file_list.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a configuration file")
            return
        
        config_type = self.file_list.item(selection[0])['tags'][0]
        shell_type = self.shell_var.get()
        file_path = self.config_files[shell_type][config_type]
        
        try:
            # Create backup before saving
            self.backup_config()
            
            # Save changes
            content = self.editor.get('1.0', tk.END)
            file_path.write_text(content)
            
            self.status_var.set("Changes saved successfully")
            messagebox.showinfo("Success", "Changes saved")
            
            # Update diff view
            self.update_diff_view()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save changes: {str(e)}")

class RestoreDialog:
    """Dialog for selecting backup to restore"""
    def __init__(self, parent, backups):
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Restore Configuration")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Create backup list
        ttk.Label(self.dialog, text="Select backup to restore:").pack(pady=5)
        
        self.backup_list = ttk.Treeview(self.dialog, 
                                       columns=('date', 'size'),
                                       show='headings')
        self.backup_list.heading('date', text='Date')
        self.backup_list.heading('size', text='Size')
        self.backup_list.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Populate backup list
        for backup in backups:
            date = datetime.datetime.fromtimestamp(backup.stat().st_mtime)
            size = backup.stat().st_size
                
            # Format size for display
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size/1024:.1f} KB"
            else:
                size_str = f"{size/(1024*1024):.1f} MB"
            
            self.backup_list.insert('', 'end',
                                  values=(date.strftime('%Y-%m-%d %H:%M:%S'),
                                         size_str),
                                  tags=(str(backup),))
        
        # Create preview frame
        preview_frame = ttk.LabelFrame(self.dialog, text="Preview")
        preview_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, 
                                                    height=10, 
                                                    wrap=tk.NONE)
        self.preview_text.pack(fill='both', expand=True)
        
        # Bind selection event
        self.backup_list.bind('<<TreeviewSelect>>', self.on_backup_select)
        
        # Create buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="Restore", 
                  command=self.on_restore).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=self.dialog.destroy).pack(side='right', padx=5)
        
        # Wait for dialog to close
        self.dialog.wait_window()

    def on_backup_select(self, event):
        """Handle backup selection"""
        selection = self.backup_list.selection()
        if not selection:
            return
        
        # Get backup path from tags
        backup_path = Path(self.backup_list.item(selection[0])['tags'][0])
        
        try:
            # Load and display backup content
            content = backup_path.read_text()
            self.preview_text.delete('1.0', tk.END)
            self.preview_text.insert('1.0', content)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load backup: {str(e)}")

    def on_restore(self):
        """Handle restore button click"""
        selection = self.backup_list.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a backup to restore")
            return
        
        # Get backup path from tags
        self.result = Path(self.backup_list.item(selection[0])['tags'][0])
        self.dialog.destroy()

class ShellConfigAnalyzer:
    """Utility class for analyzing shell configurations"""
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.content = None
        self.load_config()

    def load_config(self):
        """Load configuration file content"""
        try:
            self.content = self.config_path.read_text()
        except Exception:
            self.content = ""

    def analyze_aliases(self) -> Dict[str, str]:
        """Analyze and extract aliases"""
        aliases = {}
        for line in self.content.splitlines():
            if line.strip().startswith('alias'):
                try:
                    # Extract alias name and command
                    match = re.match(r'alias\s+(\w+)=[\'"](.+)[\'"]', line.strip())
                    if match:
                        aliases[match.group(1)] = match.group(2)
                except Exception:
                    continue
        return aliases

    def analyze_paths(self) -> List[str]:
        """Analyze and extract PATH modifications"""
        paths = []
        for line in self.content.splitlines():
            if 'PATH' in line and ('export' in line or 'PATH=' in line):
                try:
                    # Extract path additions
                    match = re.search(r'PATH=([^#\n]+)', line)
                    if match:
                        paths.extend(match.group(1).split(':'))
                except Exception:
                    continue
        return [p for p in paths if p and '$PATH' not in p]

    def analyze_environment_vars(self) -> Dict[str, str]:
        """Analyze and extract environment variables"""
        env_vars = {}
        for line in self.content.splitlines():
            if line.strip().startswith('export'):
                try:
                    # Extract variable name and value
                    match = re.match(r'export\s+(\w+)=[\'"]?([^\'"]+)[\'"]?', 
                                   line.strip())
                    if match:
                        env_vars[match.group(1)] = match.group(2)
                except Exception:
                    continue
        return env_vars

    def analyze_functions(self) -> List[str]:
        """Analyze and extract function definitions"""
        functions = []
        in_function = False
        current_function = []
        
        for line in self.content.splitlines():
            if re.match(r'\w+\s*\(\)\s*{', line.strip()):
                in_function = True
                current_function = [line]
            elif in_function:
                current_function.append(line)
                if line.strip() == '}':
                    functions.append('\n'.join(current_function))
                    in_function = False
                    current_function = []
        
        return functions

    def get_summary(self) -> Dict:
        """Get a summary of the configuration"""
        return {
            'aliases': len(self.analyze_aliases()),
            'paths': len(self.analyze_paths()),
            'env_vars': len(self.analyze_environment_vars()),
            'functions': len(self.analyze_functions()),
            'total_lines': len(self.content.splitlines()),
            'size': len(self.content),
            'last_modified': datetime.datetime.fromtimestamp(
                self.config_path.stat().st_mtime)
        }

    def suggest_optimizations(self) -> List[str]:
        """Suggest possible optimizations"""
        suggestions = []
        
        # Check for duplicate PATH additions
        paths = self.analyze_paths()
        if len(paths) != len(set(paths)):
            suggestions.append("Found duplicate PATH additions")
        
        # Check for large number of aliases
        aliases = self.analyze_aliases()
        if len(aliases) > 50:
            suggestions.append("Large number of aliases - consider organizing them")
        
        # Check for long functions
        functions = self.analyze_functions()
        for func in functions:
            if len(func.splitlines()) > 25:
                suggestions.append(f"Long function found - consider refactoring")
                break
        
        # Check file size
        if len(self.content) > 10000:
            suggestions.append("Large configuration file - consider splitting")
        
        return suggestions				