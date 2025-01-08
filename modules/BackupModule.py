import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import subprocess
import os
from pathlib import Path
import shutil
import datetime
import threading
import json

class BackupModule:
    def __init__(self, parent_notebook):
        # Create backup tab
        self.backup_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.backup_frame, text='Backups')
        
        # Backup configuration
        self.backup_config = {
            'source_paths': [],
            'destination': '',
            'compression': 'none',  # none, zip, tar, tar.gz, tar.bz2, 7z
            'delete_original': False,
            'create_subfolder': True
        }
        
        # Available compression formats
        self.compression_formats = {
            'None': 'none',
            'ZIP': 'zip',
            'TAR': 'tar',
            'TAR.GZ': 'tar.gz',
            'TAR.BZ2': 'tar.bz2',
            '7Z': '7z'
        }
        
        # Create main interface
        self.create_interface()
        
        # Initialize status variables
        self.backup_thread = None
        self.stop_backup = False
    
    def create_interface(self):
        # Create main container
        main_container = ttk.Frame(self.backup_frame)
        main_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Left panel - Source selection
        left_panel = ttk.LabelFrame(main_container, text="Source")
        left_panel.pack(side='left', fill='both', expand=True, padx=5)
        
        # Source list
        self.source_list = ttk.Treeview(left_panel,
                                        columns=('path', 'type'),
                                        show='headings')
        self.source_list.heading('path', text='Path')
        self.source_list.heading('type', text='Type')
        
        # Scrollbars for source list
        source_y_scroll = ttk.Scrollbar(left_panel, orient='vertical',
                                        command=self.source_list.yview)
        source_x_scroll = ttk.Scrollbar(left_panel, orient='horizontal',
                                        command=self.source_list.xview)
        
        self.source_list.configure(yscrollcommand=source_y_scroll.set,
                                   xscrollcommand=source_x_scroll.set)
        
        # Pack source list and scrollbars
        self.source_list.pack(side='left', fill='both', expand=True)
        source_y_scroll.pack(side='right', fill='y')
        source_x_scroll.pack(side='bottom', fill='x')
        
        # Source buttons
        source_btn_frame = ttk.Frame(left_panel)
        source_btn_frame.pack(fill='x', pady=5)
        
        ttk.Button(source_btn_frame, text="Add File",
                   command=self.add_file).pack(side='left', padx=2)
        
        ttk.Button(source_btn_frame, text="Add Directory",
                   command=self.add_directory).pack(side='left', padx=2)
        
        ttk.Button(source_btn_frame, text="Remove",
                   command=self.remove_source).pack(side='left', padx=2)
        
        # Right panel - Backup configuration
        right_panel = ttk.LabelFrame(main_container, text="Backup Configuration")
        right_panel.pack(side='right', fill='both', padx=5)
        
        # Destination selection
        dest_frame = ttk.Frame(right_panel)
        dest_frame.pack(fill='x', pady=5)
        
        ttk.Label(dest_frame, text="Destination:").pack(side='left')
        
        self.dest_var = tk.StringVar()
        
        ttk.Entry(dest_frame, textvariable=self.dest_var,
                  width=30).pack(side='left', padx=5)
        
        ttk.Button(dest_frame, text="Browse",
                   command=self.select_destination).pack(side='left')
        
        # Compression selection
        comp_frame = ttk.Frame(right_panel)
        comp_frame.pack(fill='x', pady=5)
        
        ttk.Label(comp_frame, text="Compression:").pack(side='left')
        
        self.comp_var = tk.StringVar(value='None')
        
        comp_menu = ttk.OptionMenu(comp_frame, self.comp_var, 'None',
                                   *self.compression_formats.keys())
        
        comp_menu.pack(side='left', padx=5)
        
        # Additional options
        options_frame = ttk.Frame(right_panel)
        options_frame.pack(fill='x', pady=5)
        
        self.delete_var = tk.BooleanVar()
        
        ttk.Checkbutton(options_frame, text="Delete original after backup",
                        variable=self.delete_var).pack(anchor='w')
        
        self.subfolder_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(options_frame, text="Create dated subfolder",
                        variable=self.subfolder_var).pack(anchor='w')
        
        # Progress frame
        progress_frame = ttk.LabelFrame(self.backup_frame, text="Progress")
        progress_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        
        self.progress_bar = ttk.Progressbar(progress_frame,
                                            variable=self.progress_var,
                                            maximum=100)
        
        self.progress_bar.pack(fill='x', padx=5, pady=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        
        self.status_label = ttk.Label(progress_frame,
                                      textvariable=self.status_var)
        
        self.status_label.pack(pady=5)
        
        # Output text
        self.output = scrolledtext.ScrolledText(progress_frame, height=10)
        
        self.output.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Control buttons
        btn_frame = ttk.Frame(self.backup_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Start Backup",
                   command=self.start_backup).pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text="Stop",
                   command=self.stop_current_operation).pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text="Clear",
                   command=self.clear_all).pack(side='right', padx=5)
    
    def add_file(self):
        """Add file to source list"""
        files = filedialog.askopenfilenames(title="Select Files to Backup")
        
        for file in files:
            if file not in self.backup_config['source_paths']:
                self.backup_config['source_paths'].append(file)
                
                self.source_list.insert('', 'end',
                                        values=(file, 'File'))
    
    def add_directory(self):
        """Add directory to source list"""
        directory = filedialog.askdirectory(title="Select Directory to Backup")
        
        if directory:
            if directory not in self.backup_config['source_paths']:
                self.backup_config['source_paths'].append(directory)
                
                self.source_list.insert('', 'end',
                                        values=(directory, 'Directory'))
    
    def remove_source(self):
        """Remove selected source from list"""
        selection = self.source_list.selection()
        
        if not selection:
            return
        
        for item in selection:
            path = self.source_list.item(item)['values'][0]
            
            self.backup_config['source_paths'].remove(path)
            
            self.source_list.delete(item)
    
    def select_destination(self):
        """Select backup destination directory"""
        directory = filedialog.askdirectory(title="Select Backup Destination")
        
        if directory:
            self.dest_var.set(directory)
            
            self.backup_config['destination'] = directory
    
    def start_backup(self):
        """Start backup operation"""
        
        if not self.backup_config['source_paths']:
            messagebox.showwarning("Warning", "No source files/directories selected")
            
            return
        
        if not self.dest_var.get():
            messagebox.showwarning("Warning", "No destination selected")
            
            return
        
        # Update configuration
        self.backup_config.update({
            'destination': self.dest_var.get(),
            'compression': self.compression_formats[self.comp_var.get()],
            'delete_original': self.delete_var.get(),
            'create_subfolder': self.subfolder_var.get()
        })
        
        # Start backup thread
        self.stop_backup = False
        
        self.backup_thread = threading.Thread(target=self._perform_backup)
        
        self.backup_thread.start()
    
    def _perform_backup(self):
        """Perform the actual backup operation"""
        
        try:
            # Create destination directory if needed
            dest_base = self.backup_config['destination']
            
            if self.backup_config['create_subfolder']:
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                
                dest_base = os.path.join(dest_base, f"backup_{timestamp}")
                
                os.makedirs(dest_base, exist_ok=True)
            
            total_size = self._calculate_total_size()
            
            processed_size = 0
            
            for source in self.backup_config['source_paths']:
                if self.stop_backup:
                    break
                
                source_path = Path(source)
                
                if source_path.is_file():
                    processed_size += self._backup_file(source_path, dest_base)
                    
                else:
                    processed_size += self._backup_directory(source_path, dest_base)
            
            progress = (processed_size / total_size) * 100
            
            self.update_progress(progress)
            
            if not self.stop_backup:
                self.update_status("Backup completed successfully")
                
                messagebox.showinfo("Success", "Backup completed successfully")
        
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            
            messagebox.showerror("Error", f"Backup failed: {str(e)}")
    
    def _backup_file(self, source: Path, dest_base: str) -> int:
        """Backup a single file"""
        
        try:
            # Create relative path structure in destination
            rel_path = source.name
            
            dest_path = os.path.join(dest_base, rel_path)
            
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            # Copy file
            self.update_status(f"Copying {source}")
            
            shutil.copy2(source, dest_path)
            
            # Handle compression if needed
            if self.backup_config['compression'] != 'none':
                dest_path = self._compress_file(dest_path)
            
            # Delete original if requested
            if self.backup_config['delete_original']:
                os.remove(source)
                
                return source.stat().st_size
        
        except Exception as e:
            self.update_output(f"Error backing up {source}: {str(e)}\n")
            
            return 0
    
    def _backup_directory(self, source: Path, dest_base: str) -> int:
        """Backup a directory"""
        
        total_size = 0
        
        try:
            for root, _, files in os.walk(source):
                if self.stop_backup:
                    break
                
                root_path = Path(root)
                
                for file in files:
                    if self.stop_backup:
                        break
                    
                    file_path = root_path / file
                    
                    rel_path = file_path.relative_to(source)
                    
                    dest_path = os.path.join(dest_base, str(rel_path))
                    
                    # Ensure destination directory exists
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    
                    # Copy file
                    self.update_status(f"Copying {file_path}")
                    
                    shutil.copy2(file_path, dest_path)
                    
                    # Handle compression if needed
                    if self.backup_config['compression'] != 'none':
                        dest_path = self._compress_file(dest_path)
                        
                        total_size += file_path.stat().st_size
                    
                    # Delete original if requested
                    if (self.backup_config['delete_original']
                            and not self.stop_backup):
                        shutil.rmtree(source)
        
        except Exception as e:
            self.update_output(f"Error backing up directory {source}: {str(e)}\n")
            
            return total_size
    
    def _compress_file(self, filepath: str) -> str:
        """Compress a file using selected compression method"""
        
        try:
            compression = self.backup_config['compression']
            
            if compression == 'zip':
                return self._compress_zip(filepath)
                
            elif compression == 'tar':
                return self._compress_tar(filepath)
                
            elif compression == 'tar.gz':
                return self._compress_tar_gz(filepath)
                
            elif compression == 'tar.bz2':
                return self._compress_tar_bz2(filepath)
                
            elif compression == '7z':
                return self._compress_7z(filepath)
        
        except Exception as e:
            self.update_output(f"Compression failed for {filepath}: {str(e)}\n")
            
            return filepath
    
    def _compress_zip(self, filepath: str) -> str:
        """Compress file using ZIP"""
        
        import zipfile
        
        compressed_path = filepath + '.zip'
        
        with zipfile.ZipFile(compressed_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(filepath, os.path.basename(filepath))
            
            os.remove(filepath)
            
            return compressed_path
    
    def _compress_tar(self, filepath: str) -> str:
        """Compress file using TAR"""
        
        import tarfile
        
        compressed_path = filepath + '.tar'
        
        with tarfile.open(compressed_path, 'w') as tar:
            tar.add(filepath, arcname=os.path.basename(filepath))
            
            os.remove(filepath)
            
            return compressed_path
    
    def _compress_tar_gz(self, filepath: str) -> str:
        """Compress file using TAR.GZ"""
        
        import tarfile
        
        compressed_path = filepath + '.tar.gz'
        
        with tarfile.open(compressed_path, 'w:gz') as tar:
            tar.add(filepath, arcname=os.path.basename(filepath))
            
            os.remove(filepath)
            
            return compressed_path
    
    def _compress_tar_bz2(self, filepath: str) -> str:
        """Compress file using TAR.BZ2"""
        
        import tarfile
        
        compressed_path = filepath + '.tar.bz2'
        
        with tarfile.open(compressed_path, 'w:bz2') as tar:
            tar.add(filepath, arcname=os.path.basename(filepath))
            
            os.remove(filepath)
            
            return compressed_path
    
    def _compress_7z(self, filepath: str) -> str:
        """Compress file using 7z"""
        
        compressed_path = filepath + '.7z'
        
        try:
            # Check if 7z is installed
            if subprocess.call(['which', '7z'], stdout=subprocess.PIPE) != 0:
                raise Exception("7z is not installed. Please install p7zip-full package.")
            
            # Compress file
            subprocess.run(['7z', 'a', compressed_path, filepath],
                           check=True, capture_output=True)
            
            os.remove(filepath)
            
            return compressed_path
        
        except subprocess.CalledProcessError as e:
            raise Exception(f"7z compression failed: {e.stderr.decode()}")
    
    def _calculate_total_size(self) -> int:
        """Calculate total size of all source files"""
        
        total_size = 0
        
        for source in self.backup_config['source_paths']:
            source_path = Path(source)
            
            if source_path.is_file():
                total_size += source_path.stat().st_size
                
            else:
                for root, _, files in os.walk(source):
                    for file in files:
                        file_path = Path(root) / file
                        
                        total_size += file_path.stat().st_size
        
        return total_size
    
    def stop_current_operation(self):
        """Stop current backup operation"""
        
        if self.backup_thread and self.backup_thread.is_alive():
            self.stop_backup = True
            
            self.update_status("Stopping backup operation...")
            
        else:
            messagebox.showinfo("Info", "No backup operation in progress")
    
    def clear_all(self):
        """Clear all selections and reset interface"""
        
        self.backup_config['source_paths'] = []
        
        self.source_list.delete(*self.source_list.get_children())
        
        self.dest_var.set('')
        
        self.comp_var.set('None')
        
        self.delete_var.set(False)
        
        self.subfolder_var.set(True)
        
        self.progress_var.set(0)
        
        self.status_var.set("Ready")
        
        self.output.delete(1.0, tk.END)
    
    def update_status(self, message: str):
        """Update status label"""
        
        self.status_var.set(message)
        
        self.update_output(f"{message}\n")
    
    def update_output(self, message: str):
        """Update output text"""
        
        self.output.insert(tk.END, message)
        
        self.output.see(tk.END)
    
    def update_progress(self, value: float):
        """Update progress bar"""
        
        self.progress_var.set(value)
        
        self.backup_frame.update_idletasks()
    
    def save_config(self):
        """Save backup configuration to file"""
        
        config_path = Path.home() / '.kali_fixall' / 'backup_config.json'
        
        config_path.parent.mkdir(exist_ok=True)
        
        config = {
            'last_destination': self.backup_config['destination'],
            'compression': self.comp_var.get(),
            'delete_original': self.delete_var.get(),
            'create_subfolder': self.subfolder_var.get()
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f)
    
    def load_config(self):
        """Load backup configuration from file"""
        
        config_path = Path.home() / '.kali_fixall' / 'backup_config.json'
        
        if config_path.exists():
            
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    
                    self.dest_var.set(config.get('last_destination', ''))
                    
                    self.comp_var.set(config.get('compression', 'None'))
                    
                    self.delete_var.set(config.get('delete_original', False))
                    
                    self.subfolder_var.set(config.get('create_subfolder', True))
            
            except Exception as e:
                self.update_output(f"Error loading config: {str(e)}\n")
    
    def __del__(self):
        """Save configuration when module is destroyed"""
        
        try:
            self.save_config()
        
        except:
            pass