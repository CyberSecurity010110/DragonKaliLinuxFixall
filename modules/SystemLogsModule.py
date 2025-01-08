# Part 7: System Logs Management Module
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
import re
from pathlib import Path
from datetime import datetime, timedelta
import gzip
import json
import threading
from collections import defaultdict

class SystemLogsModule:
    def __init__(self, parent_notebook):
        # Create logs management tab
        self.logs_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.logs_frame, text='System Logs')
        
        # Create split view
        self.create_split_view()
        
        # Initialize log data
        self.log_files = {}
        self.log_descriptions = self.load_log_descriptions()
        
        # Populate initial log list
        self.scan_system_logs()

    def create_split_view(self):
        """Create split view with log list and content viewer"""
        # Create main paned window
        self.paned = ttk.PanedWindow(self.logs_frame, orient=tk.HORIZONTAL)
        self.paned.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create left panel (log list and controls)
        self.left_frame = ttk.Frame(self.paned)
        self.paned.add(self.left_frame)
        
        # Create search frame
        search_frame = ttk.LabelFrame(self.left_frame, text="Search")
        search_frame.pack(fill='x', padx=5, pady=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_logs)
        ttk.Entry(search_frame, textvariable=self.search_var).pack(
            fill='x', padx=5, pady=5)
        
        # Create log list
        list_frame = ttk.LabelFrame(self.left_frame, text="Log Files")
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.log_list = ttk.Treeview(list_frame, columns=('size', 'modified'),
                                    show='headings')
        self.log_list.heading('size', text='Size')
        self.log_list.heading('modified', text='Modified')
        self.log_list.pack(fill='both', expand=True)
        self.log_list.bind('<<TreeviewSelect>>', self.on_log_select)
        
        # Create right panel (log viewer)
        self.right_frame = ttk.Frame(self.paned)
        self.paned.add(self.right_frame)
        
        # Create viewer controls
        control_frame = ttk.Frame(self.right_frame)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(control_frame, text="Refresh", 
                  command=self.refresh_current_log).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Search Errors", 
                  command=self.search_errors).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Export", 
                  command=self.export_log).pack(side='left', padx=5)
        
        # Create log viewer
        self.log_viewer = scrolledtext.ScrolledText(self.right_frame, 
                                                   wrap=tk.WORD, 
                                                   width=80)
        self.log_viewer.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create status bar
        self.status_var = tk.StringVar()
        ttk.Label(self.right_frame, textvariable=self.status_var).pack(
            fill='x', padx=5, pady=5)

    def load_log_descriptions(self):
        """Load descriptions of common log files"""
        return {
            '/var/log/syslog': 'Main system log containing general system activity messages',
            '/var/log/auth.log': 'Authentication and security-related events',
            '/var/log/kern.log': 'Kernel messages and hardware-related events',
            '/var/log/dmesg': 'Boot-time hardware detection and driver initialization',
            '/var/log/dpkg.log': 'Package management activities (installations, updates)',
            '/var/log/apt/history.log': 'APT package manager history',
            '/var/log/apt/term.log': 'Detailed APT package manager operations',
            '/var/log/boot.log': 'System boot messages',
            '/var/log/faillog': 'Failed login attempts',
            '/var/log/Xorg.0.log': 'X Window System log',
            '/var/log/cups': 'Printer and printing-related logs',
            '/var/log/nginx': 'Nginx web server logs',
            '/var/log/apache2': 'Apache web server logs',
            '/var/log/mysql': 'MySQL/MariaDB database logs',
            '/var/log/postgresql': 'PostgreSQL database logs',
            '/var/log/mail.log': 'Mail server logs',
            '/var/log/ufw.log': 'Uncomplicated Firewall logs',
            '/var/log/cron.log': 'Cron job execution logs',
            '/var/log/wtmp': 'Login/logout history (binary file)',
            '/var/log/btmp': 'Failed login attempts (binary file)',
            '/var/log/secure': 'Security and authentication logs (some systems)',
            '/var/log/messages': 'General system messages (some systems)'
        }

    def scan_system_logs(self):
        """Scan system for log files"""
        self.log_files.clear()
        self.log_list.delete(*self.log_list.get_children())
        
        # Common log directories
        log_dirs = [
            '/var/log',
            '/var/log/apt',
            '/var/log/cups',
            '/var/log/nginx',
            '/var/log/apache2',
            '/var/log/mysql',
            '/var/log/postgresql'
        ]
        
        for dir_path in log_dirs:
            if os.path.exists(dir_path):
                self.scan_log_directory(dir_path)
        
        # Sort logs by modification time
        self.sort_logs()

    def scan_log_directory(self, dir_path):
        """Scan a directory for log files"""
        try:
            for entry in os.scandir(dir_path):
                if self.is_log_file(entry):
                    size = self.get_file_size(entry)
                    modified = self.get_file_modified(entry)
                    description = self.get_log_description(entry.path)
                    
                    self.log_files[entry.path] = {
                        'size': size,
                        'modified': modified,
                        'description': description
                    }
                    
                    self.log_list.insert('', 'end', 
                                       values=(size, modified),
                                       text=entry.path,
                                       tags=('log',))
        except PermissionError:
            pass

    def is_log_file(self, entry):
        """Check if file is a log file"""
        if entry.is_file():
            # Check extension
            if entry.name.endswith(('.log', '.txt', '.1', '.gz')):
                return True
            
            # Check if file is in our descriptions
            if entry.path in self.log_descriptions:
                return True
            
            # Check content (first line) for log-like format
            try:
                with open(entry.path, 'r') as f:
                    first_line = f.readline()
                    if re.match(r'^[\w\s:]+\[\d+\]|^\d{4}-\d{2}-\d{2}|^\w{3}\s+\d{1,2}\s+\d{2}:', first_line):
                        return True
            except (PermissionError, UnicodeDecodeError):
                pass
        
        return False

    def get_file_size(self, entry):
        """Get human-readable file size"""
        try:
            size = entry.stat().st_size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f"{size:.1f} {unit}"
                size /= 1024
            return f"{size:.1f} TB"
        except:
            return "N/A"

    def get_file_modified(self, entry):
        """Get file modification time"""
        try:
            mtime = datetime.fromtimestamp(entry.stat().st_mtime)
            return mtime.strftime("%Y-%m-%d %H:%M")
        except:
            return "N/A"

    def get_log_description(self, path):
        """Get description for log file"""
        # Check direct match
        if path in self.log_descriptions:
            return self.log_descriptions[path]
        
        # Check parent directory match
        parent = os.path.dirname(path)
        if parent in self.log_descriptions:
            return self.log_descriptions[parent]
        
        # Check pattern match
        for log_path, desc in self.log_descriptions.items():
            if path.startswith(log_path):
                return desc
        
        return "System log file"

    def sort_logs(self):
        """Sort logs by modification time"""
        items = [(self.log_list.item(item)["text"], item) 
                for item in self.log_list.get_children('')]
        
        items.sort(key=lambda x: self.log_files[x[0]]['modified'], reverse=True)
        
        for index, (path, item) in enumerate(items):
            self.log_list.move(item, '', index)

    def filter_logs(self, *args):
        """Filter log list based on search term"""
        search_term = self.search_var.get().lower()
        
        for item in self.log_list.get_children(''):
            path = self.log_list.item(item)["text"]
            description = self.log_files[path]['description'].lower()
            
            if search_term in path.lower() or search_term in description:
                self.log_list.item(item, tags=('visible',))
            else:
                self.log_list.item(item, tags=('hidden',))
        
        self.log_list.tag_configure('hidden', hide=True)
        self.log_list.tag_configure('visible', hide=False)

    def on_log_select(self, event):
        """Handle log selection"""
        selection = self.log_list.selection()
        if not selection:
            return
        
        path = self.log_list.item(selection[0])["text"]
        self.view_log(path)

    def view_log(self, path):
        """View contents of selected log file"""
        try:
            self.log_viewer.delete('1.0', tk.END)
            
            # Show file info
            info = self.log_files[path]
            self.log_viewer.insert(tk.END, f"File: {path}\n")
            self.log_viewer.insert(tk.END, f"Size: {info['size']}\n")
            self.log_viewer.insert(tk.END, f"Modified: {info['modified']}\n")
            self.log_viewer.insert(tk.END, f"Description: {info['description']}\n")
            self.log_viewer.insert(tk.END, "-" * 80 + "\n\n")
            
            # Read file content
            if path.endswith('.gz'):
                with gzip.open(path, 'rt') as f:
                    content = f.read()
            else:
                with open(path, 'r') as f:
                    content = f.read()
            
            self.log_viewer.insert(tk.END, content)
            
            self.status_var.set(f"Loaded: {path}")
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to read log file: {str(e)}")

    def refresh_current_log(self):
        """Refresh current log view"""
        selection = self.log_list.selection()
        if selection:
            path = self.log_list.item(selection[0])["text"]
            self.view_log(path)

    def search_errors(self):
        """Search current log for errors"""
        selection = self.log_list.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a log file first")
            return
        
        path = self.log_list.item(selection[0])["text"]
        
        try:
            # Common error patterns
            error_patterns = [
                r'error',
                r'fail',
                r'critical',
                r'emergency',
                r'alert',
                r'warning',
                r'exception',
                r'\bE\b'  # Common error indicator
            ]
            
            pattern = '|'.join(error_patterns)
            
            # Create results window
            results_window = tk.Toplevel(self.logs_frame)
            results_window.title(f"Errors in {os.path.basename(path)}")
            results_window.geometry("800x600")
            
            # Create results viewer
            results_viewer = scrolledtext.ScrolledText(results_window, 
                                                     wrap=tk.WORD)
            results_viewer.pack(fill='both', expand=True, padx=5, pady=5)
            
            # Search for errors
            if path.endswith('.gz'):
                with gzip.open(path, 'rt') as f:
                    content = f.read()
            else:
                with open(path, 'r') as f:
                    content = f.read()
            
            errors_found = False
            for line in content.splitlines():
                if re.search(pattern, line, re.IGNORECASE):
                    results_viewer.insert(tk.END, line + '\n')
                    errors_found = True
            
            if not errors_found:
                results_viewer.insert(tk.END, "No errors found in log file.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to search log file: {str(e)}")

    def export_log(self):
        """Export current log view"""
        selection = self.log_list.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a log file first")
            return
        
        path = self.log_list.item(selection[0])["text"]
        
        try:
            # Create export filename
            export_name = f"log_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(export_name, 'w') as f:
                # Write file info
                info = self.log_files[path]
                f.write(f"Log File Export\n")
                f.write(f"Original File: {path}\n")
                f.write(f"Size: {info['size']}\n")
                f.write(f"Modified: {info['modified']}\n")
                f.write(f"Description: {info['description']}\n")
                f.write("-" * 80 + "\n\n")
                
                # Write content
                if path.endswith('.gz'):
                    with gzip.open(path, 'rt') as log:
                        f.write(log.read())
                else:
                    with open(path, 'r') as log:
                        f.write(log.read())
            
            messagebox.showinfo("Success", f"Log exported to: {export_name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export log: {str(e)}")

    def analyze_log_patterns(self):
        """Analyze patterns in current log file"""
        selection = self.log_list.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a log file first")
            return
        
        path = self.log_list.item(selection[0])["text"]
        
        try:
            # Create analysis window
            analysis_window = tk.Toplevel(self.logs_frame)
            analysis_window.title(f"Log Analysis - {os.path.basename(path)}")
            analysis_window.geometry("900x700")
            
            # Create notebook for different analyses
            notebook = ttk.Notebook(analysis_window)
            notebook.pack(fill='both', expand=True, padx=5, pady=5)
            
            # Create analysis tabs
            self.create_frequency_analysis_tab(notebook, path)
            self.create_time_distribution_tab(notebook, path)
            self.create_error_summary_tab(notebook, path)
            self.create_ip_analysis_tab(notebook, path)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to analyze log: {str(e)}")

    def create_frequency_analysis_tab(self, notebook, path):
        """Create tab for frequency analysis"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Message Frequency")
        
        # Create tree view for frequency display
        tree = ttk.Treeview(tab, columns=('count', 'percentage'),
                           show='headings')
        tree.heading('count', text='Count')
        tree.heading('percentage', text='Percentage')
        tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Analyze frequencies
        try:
            message_counts = defaultdict(int)
            total_lines = 0
            
            if path.endswith('.gz'):
                opener = gzip.open
            else:
                opener = open
            
            with opener(path, 'rt') as f:
                for line in f:
                    total_lines += 1
                    # Extract message part (remove timestamp and process info)
                    message = re.sub(r'^.*?\]: ', '', line.strip())
                    message_counts[message] += 1
            
            # Sort by frequency
            sorted_messages = sorted(message_counts.items(), 
                                  key=lambda x: x[1], reverse=True)
            
            # Display top 100 messages
            for message, count in sorted_messages[:100]:
                percentage = (count / total_lines) * 100
                tree.insert('', 'end', values=(count, f"{percentage:.2f}%"),
                          text=message)
            
        except Exception as e:
            messagebox.showerror("Error", 
                               f"Failed to analyze message frequency: {str(e)}")

    def create_time_distribution_tab(self, notebook, path):
        """Create tab for time distribution analysis"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Time Distribution")
        
        # Create time distribution display
        canvas = tk.Canvas(tab, bg='white')
        canvas.pack(fill='both', expand=True, padx=5, pady=5)
        
        try:
            # Collect time data
            hour_counts = defaultdict(int)
            
            if path.endswith('.gz'):
                opener = gzip.open
            else:
                opener = open
            
            with opener(path, 'rt') as f:
                for line in f:
                    # Try to extract timestamp
                    timestamp_match = re.search(
                        r'\b(\d{2}):(\d{2}):\d{2}\b', line)
                    if timestamp_match:
                        hour = int(timestamp_match.group(1))
                        hour_counts[hour] += 1
            
            # Draw distribution graph
            self.draw_time_distribution(canvas, hour_counts)
            
        except Exception as e:
            messagebox.showerror("Error", 
                               f"Failed to analyze time distribution: {str(e)}")

    def draw_time_distribution(self, canvas, hour_counts):
        """Draw time distribution graph"""
        # Clear canvas
        canvas.delete('all')
        
        # Calculate dimensions
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        margin = 50
        bar_width = (width - 2 * margin) / 24
        
        # Draw axes
        canvas.create_line(margin, height - margin, 
                          width - margin, height - margin)  # X-axis
        canvas.create_line(margin, margin, 
                          margin, height - margin)  # Y-axis
        
        # Find maximum count for scaling
        max_count = max(hour_counts.values()) if hour_counts else 1
        
        # Draw bars
        for hour in range(24):
            count = hour_counts.get(hour, 0)
            bar_height = ((count / max_count) * 
                         (height - 2 * margin))
            
            x1 = margin + hour * bar_width
            y1 = height - margin - bar_height
            x2 = x1 + bar_width - 2
            y2 = height - margin
            
            canvas.create_rectangle(x1, y1, x2, y2, 
                                  fill='blue', outline='black')
            
            # Draw hour labels
            canvas.create_text(x1 + bar_width/2, height - margin + 15,
                             text=str(hour))
        
        # Draw count labels
        for i in range(5):
            y = height - margin - (i * (height - 2 * margin) / 4)
            count = int((i * max_count) / 4)
            canvas.create_text(margin - 20, y, text=str(count))

    def create_error_summary_tab(self, notebook, path):
        """Create tab for error summary"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Error Summary")
        
        # Create summary display
        summary = scrolledtext.ScrolledText(tab, wrap=tk.WORD)
        summary.pack(fill='both', expand=True, padx=5, pady=5)
        
        try:
            # Error categories
            error_categories = {
                'System': r'system|kernel|daemon',
                'Authentication': r'auth|login|password',
                'Network': r'network|connection|interface|eth|wlan',
                'Hardware': r'device|driver|hardware|usb|disk',
                'Application': r'segfault|crash|exception|error',
                'Security': r'security|firewall|permission|denied'
            }
            
            category_counts = defaultdict(int)
            error_examples = defaultdict(list)
            
            if path.endswith('.gz'):
                opener = gzip.open
            else:
                opener = open
            
            with opener(path, 'rt') as f:
                for line in f:
                    if re.search(r'error|fail|critical|emergency|alert|warning', 
                               line, re.IGNORECASE):
                        # Categorize error
                        for category, pattern in error_categories.items():
                            if re.search(pattern, line, re.IGNORECASE):
                                category_counts[category] += 1
                                if len(error_examples[category]) < 3:
                                    error_examples[category].append(line.strip())
            
            # Display summary
            summary.insert(tk.END, "Error Summary Report\n")
            summary.insert(tk.END, "=" * 50 + "\n\n")
            
            for category in error_categories:
                count = category_counts.get(category, 0)
                summary.insert(tk.END, f"{category} Errors: {count}\n")
                if count > 0:
                    summary.insert(tk.END, "Examples:\n")
                    for example in error_examples[category]:
                        summary.insert(tk.END, f"- {example}\n")
                summary.insert(tk.END, "\n")
            
        except Exception as e:
            messagebox.showerror("Error", 
                               f"Failed to create error summary: {str(e)}")

    def create_ip_analysis_tab(self, notebook, path):
        """Create tab for IP address analysis"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="IP Analysis")
        
        # Create IP analysis display
        tree = ttk.Treeview(tab, columns=('count', 'last_seen'),
                           show='headings')
        tree.heading('count', text='Count')
        tree.heading('last_seen', text='Last Seen')
        tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        try:
            # Collect IP addresses
            ip_data = defaultdict(lambda: {'count': 0, 'last_seen': None})
            ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            
            if path.endswith('.gz'):
                opener = gzip.open
            else:
                opener = open
            
            with opener(path, 'rt') as f:
                for line in f:
                    # Extract timestamp
                    timestamp_match = re.search(
                        r'\b\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\b', line)
                    if timestamp_match:
                        timestamp = datetime.strptime(
                            timestamp_match.group(), 
                            '%Y-%m-%d %H:%M:%S')
                    else:
                        timestamp = datetime.now()
                    
                    # Find IP addresses
                    for ip in re.finditer(ip_pattern, line):
                        ip_addr = ip.group()
                        ip_data[ip_addr]['count'] += 1
                        if (ip_data[ip_addr]['last_seen'] is None or 
                            timestamp > ip_data[ip_addr]['last_seen']):
                            ip_data[ip_addr]['last_seen'] = timestamp
            
            # Sort by count
            sorted_ips = sorted(ip_data.items(), 
                              key=lambda x: x[1]['count'], 
                              reverse=True)
            
            # Display IP data
            for ip, data in sorted_ips:
                last_seen = data['last_seen'].strftime('%Y-%m-%d %H:%M:%S')
                tree.insert('', 'end', 
                          values=(data['count'], last_seen),
                          text=ip)
            
        except Exception as e:
            messagebox.showerror("Error", 
                               f"Failed to analyze IP addresses: {str(e)}")

    def monitor_log_changes(self):
        """Monitor selected log file for changes"""
        selection = self.log_list.selection()
        if not selection:
            messagebox.showinfo("Info", "Please select a log file first")
            return
        
        path = self.log_list.item(selection[0])["text"]
        
        # Create monitor window
        monitor_window = tk.Toplevel(self.logs_frame)
        monitor_window.title(f"Log Monitor - {os.path.basename(path)}")
        monitor_window.geometry("800x600")
        
        # Create monitor display
        monitor_text = scrolledtext.ScrolledText(monitor_window, wrap=tk.WORD)
        monitor_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create stop button
        stop_var = tk.BooleanVar(value=False)
        ttk.Button(monitor_window, text="Stop Monitoring",
                  command=lambda: stop_var.set(True)).pack(pady=5)
        
        def monitor_thread():
            try:
                # Get initial file size
                size = os.path.getsize(path)
                
                while not stop_var.get():
                    new_size = os.path.getsize(path)
                    
                    if new_size > size:
                        # Read new content
                        with open(path, 'r') as f:
                            f.seek(size)
                            new_content = f.read()
                            
                            # Update display
                            monitor_text.insert(tk.END, new_content)
                            monitor_text.see(tk.END)
                        
                        size = new_size
                    
                    # Wait before next check
                    time.sleep(1)
                    
            except Exception as e:
                messagebox.showerror("Error", 
                                   f"Failed to monitor log: {str(e)}")
        
        # Start monitoring thread
        threading.Thread(target=monitor_thread, daemon=True).start()