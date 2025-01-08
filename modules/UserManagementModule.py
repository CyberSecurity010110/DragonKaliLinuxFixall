# Part 3: User Management Module
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import os
import pwd
import grp
import spwd
import crypt
from pathlib import Path
import re

class UserManagementModule:
    def __init__(self, parent_notebook):
        # Create user management tab
        self.user_frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.user_frame, text='User Management')
        
        # Create split view
        self.create_split_view()
        
        # Initialize user data
        self.users_data = {}
        self.groups_data = {}
        
        # Create control panels
        self.create_control_panel()
        
        # Initial scan
        self.scan_users()

    def create_split_view(self):
        # Create PanedWindow for split view
        self.paned = ttk.PanedWindow(self.user_frame, orient=tk.HORIZONTAL)
        self.paned.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Left side - User list
        left_frame = ttk.Frame(self.paned)
        self.user_tree = ttk.Treeview(left_frame, columns=('UID', 'GID', 'Home'), 
                                    show='headings')
        self.user_tree.heading('UID', text='UID')
        self.user_tree.heading('GID', text='GID')
        self.user_tree.heading('Home', text='Home Directory')
        self.user_tree.pack(fill='both', expand=True)
        self.user_tree.bind('<<TreeviewSelect>>', self.on_user_select)
        
        # Right side - User details
        right_frame = ttk.Frame(self.paned)
        self.details_text = scrolledtext.ScrolledText(right_frame, height=15)
        self.details_text.pack(fill='both', expand=True)
        
        self.paned.add(left_frame)
        self.paned.add(right_frame)

    def create_control_panel(self):
        control_frame = ttk.Frame(self.user_frame)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        # User Operations
        user_ops_frame = ttk.LabelFrame(control_frame, text="User Operations")
        user_ops_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(user_ops_frame, text="Add User", 
                  command=self.show_add_user_dialog).pack(side='left', padx=5)
        ttk.Button(user_ops_frame, text="Delete User", 
                  command=self.delete_user).pack(side='left', padx=5)
        ttk.Button(user_ops_frame, text="Reset Password", 
                  command=self.show_reset_password_dialog).pack(side='left', padx=5)
        
        # Permission Operations
        perm_ops_frame = ttk.LabelFrame(control_frame, text="Permission Operations")
        perm_ops_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(perm_ops_frame, text="Make Admin", 
                  command=self.make_admin).pack(side='left', padx=5)
        ttk.Button(perm_ops_frame, text="Remove Admin", 
                  command=self.remove_admin).pack(side='left', padx=5)
        ttk.Button(perm_ops_frame, text="Fix Home Permissions", 
                  command=self.fix_home_permissions).pack(side='left', padx=5)

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

    def scan_users(self):
        # Clear existing data
        self.user_tree.delete(*self.user_tree.get_children())
        self.users_data.clear()
        
        try:
            # Get all users
            for user in pwd.getpwall():
                if 1000 <= user.pw_uid < 60000:  # Regular users
                    self.users_data[user.pw_name] = {
                        'uid': user.pw_uid,
                        'gid': user.pw_gid,
                        'home': user.pw_dir,
                        'shell': user.pw_shell,
                        'groups': self.get_user_groups(user.pw_name)
                    }
                    
                    self.user_tree.insert('', 'end', text=user.pw_name, 
                                        values=(user.pw_uid, user.pw_gid, user.pw_dir))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan users: {str(e)}")

    def get_user_groups(self, username):
        groups = []
        for group in grp.getgrall():
            if username in group.gr_mem:
                groups.append(group.gr_name)
        return groups

    def on_user_select(self, event):
        selection = self.user_tree.selection()
        if not selection:
            return
            
        item = self.user_tree.item(selection[0])
        username = item['text']
        user_data = self.users_data.get(username)
        
        if user_data:
            self.details_text.delete(1.0, tk.END)
            self.details_text.insert(tk.END, f"Username: {username}\n")
            self.details_text.insert(tk.END, f"UID: {user_data['uid']}\n")
            self.details_text.insert(tk.END, f"GID: {user_data['gid']}\n")
            self.details_text.insert(tk.END, f"Home: {user_data['home']}\n")
            self.details_text.insert(tk.END, f"Shell: {user_data['shell']}\n")
            self.details_text.insert(tk.END, f"Groups: {', '.join(user_data['groups'])}\n")
            
            # Check admin status
            is_admin = 'sudo' in user_data['groups'] or 'wheel' in user_data['groups']
            self.details_text.insert(tk.END, f"Admin: {'Yes' if is_admin else 'No'}\n")
            
            # Check home directory
            home_path = Path(user_data['home'])
            if home_path.exists():
                self.details_text.insert(tk.END, "Home Directory: Exists\n")
                # Check permissions
                try:
                    stat = home_path.stat()
                    self.details_text.insert(tk.END, 
                        f"Home Permissions: {stat.st_mode & 0o777:o}\n")
                except Exception as e:
                    self.details_text.insert(tk.END, 
                        f"Error checking home permissions: {str(e)}\n")
            else:
                self.details_text.insert(tk.END, "Home Directory: Missing\n")

    def show_add_user_dialog(self):
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return
            
        dialog = tk.Toplevel(self.user_frame)
        dialog.title("Add User")
        dialog.geometry("300x200")
        
        ttk.Label(dialog, text="Username:").pack(pady=5)
        username_entry = ttk.Entry(dialog)
        username_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Password:").pack(pady=5)
        password_entry = ttk.Entry(dialog, show="*")
        password_entry.pack(pady=5)
        
        make_admin_var = tk.BooleanVar()
        ttk.Checkbutton(dialog, text="Make Administrator", 
                       variable=make_admin_var).pack(pady=5)
        
        def add_user():
            username = username_entry.get()
            password = password_entry.get()
            
            if not username or not password:
                messagebox.showerror("Error", "Username and password required")
                return
                
            if not re.match("^[a-z][-a-z0-9]*$", username):
                messagebox.showerror("Error", "Invalid username format")
                return
                
            try:
                # Create user
                output, error, code = self.run_command(
                    f"useradd -m -s /bin/bash {username}")
                if code != 0:
                    raise Exception(error)
                
                # Set password
                proc = subprocess.Popen(['chpasswd'], stdin=subprocess.PIPE)
                proc.communicate(f"{username}:{password}".encode())
                
                if make_admin_var.get():
                    output, error, code = self.run_command(
                        f"usermod -aG sudo {username}")
                    if code != 0:
                        raise Exception(error)
                
                messagebox.showinfo("Success", "User added successfully")
                dialog.destroy()
                self.scan_users()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add user: {str(e)}")
        
        ttk.Button(dialog, text="Add User", command=add_user).pack(pady=20)

    def delete_user(self):
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return
            
        selection = self.user_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user")
            return
            
        username = self.user_tree.item(selection[0])['text']
        
        # Check if it's the last admin
        if self.is_last_admin(username):
            messagebox.showerror("Error", "Cannot delete the last administrator")
            return
            
        if messagebox.askyesno("Confirm", f"Delete user {username}?"):
            try:
                output, error, code = self.run_command(f"userdel -r {username}")
                if code != 0:
                    raise Exception(error)
                    
                messagebox.showinfo("Success", "User deleted successfully")
                self.scan_users()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete user: {str(e)}")

    def is_last_admin(self, username):
        admin_count = 0
        for user_data in self.users_data.values():
            if 'sudo' in user_data['groups'] or 'wheel' in user_data['groups']:
                admin_count += 1
        return admin_count == 1 and ('sudo' in self.users_data[username]['groups'] or 
                                   'wheel' in self.users_data[username]['groups'])

    def show_reset_password_dialog(self):
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return
            
        selection = self.user_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user")
            return
            
        username = self.user_tree.item(selection[0])['text']
        
        dialog = tk.Toplevel(self.user_frame)
        dialog.title("Reset Password")
        dialog.geometry("300x150")
        
        ttk.Label(dialog, text="New Password:").pack(pady=5)
        password_entry = ttk.Entry(dialog, show="*")
        password_entry.pack(pady=5)
        
        def reset_password():
            password = password_entry.get()
            if not password:
                messagebox.showerror("Error", "Password required")
                return
                
            try:
                proc = subprocess.Popen(['chpasswd'], stdin=subprocess.PIPE)
                proc.communicate(f"{username}:{password}".encode())
                
                messagebox.showinfo("Success", "Password reset successfully")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reset password: {str(e)}")
        
        ttk.Button(dialog, text="Reset Password", command=reset_password).pack(pady=20)

    def make_admin(self):
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return
            
        selection = self.user_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user")
            return
            
        username = self.user_tree.item(selection[0])['text']
        
        try:
            output, error, code = self.run_command(f"usermod -aG sudo {username}")
            if code != 0:
                raise Exception(error)
                
            messagebox.showinfo("Success", "User is now an administrator")
            self.scan_users()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to grant admin rights: {str(e)}")

    def remove_admin(self):
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return
            
        selection = self.user_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user")
            return
            
        username = self.user_tree.item(selection[0])['text']
        
        if self.is_last_admin(username):
            messagebox.showerror("Error", "Cannot remove the last administrator")
            return
            
        try:
            output, error, code = self.run_command(f"gpasswd -d {username} sudo")
            if code != 0:
                raise Exception(error)
                
            messagebox.showinfo("Success", "Admin rights removed")
            self.scan_users()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove admin rights: {str(e)}")

    def fix_home_permissions(self):
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return
            
        selection = self.user_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user")
            return
            
        username = self.user_tree.item(selection[0])['text']
        user_data = self.users_data.get(username)
        
        if not user_data:
            return
            
        try:
            home_path = Path(user_data['home'])
            if not home_path.exists():
                output, error, code = self.run_command(f"mkdir -p {home_path}")
                if code != 0:
                    raise Exception(error)
            
            # Set ownership
            output, error, code = self.run_command(
                f"chown -R {username}:{user_data['gid']} {home_path}")
            if code != 0:
                raise Exception(error)
                
            # Set permissions
            output, error, code = self.run_command(f"chmod 750 {home_path}")
            if code != 0:
                raise Exception(error)
                
            messagebox.showinfo("Success", "Home directory permissions fixed")
            self.scan_users()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fix permissions: {str(e)}")

    def check_password_expiry(self, username):
        try:
            shadow = spwd.getspnam(username)
            if shadow.sp_max > 0:  # Password expiration is enabled
                last_change = shadow.sp_lstchg * 86400  # Convert to seconds
                max_age = shadow.sp_max * 86400
                current_time = time.time()
                
                if current_time > (last_change + max_age):
                    return "Expired"
                else:
                    days_left = int((last_change + max_age - current_time) / 86400)
                    return f"Expires in {days_left} days"
            return "Never expires"
        except Exception:
            return "Unknown"

    def check_account_status(self, username):
        try:
            output, error, code = self.run_command(f"passwd -S {username}")
            if code == 0:
                status = output.split()[1]
                return {
                    'P': 'Active',
                    'L': 'Locked',
                    'NP': 'No password',
                }.get(status, 'Unknown')
            return "Unknown"
        except Exception:
            return "Unknown"

    def lock_account(self):
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return
            
        selection = self.user_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user")
            return
            
        username = self.user_tree.item(selection[0])['text']
        
        try:
            output, error, code = self.run_command(f"passwd -l {username}")
            if code != 0:
                raise Exception(error)
                
            messagebox.showinfo("Success", "Account locked successfully")
            self.scan_users()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to lock account: {str(e)}")

    def unlock_account(self):
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return
            
        selection = self.user_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user")
            return
            
        username = self.user_tree.item(selection[0])['text']
        
        try:
            output, error, code = self.run_command(f"passwd -u {username}")
            if code != 0:
                raise Exception(error)
                
            messagebox.showinfo("Success", "Account unlocked successfully")
            self.scan_users()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to unlock account: {str(e)}")

    def set_password_expiry(self):
        if os.geteuid() != 0:
            messagebox.showerror("Error", "Root privileges required")
            return
            
        selection = self.user_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user")
            return
            
        username = self.user_tree.item(selection[0])['text']
        
        dialog = tk.Toplevel(self.user_frame)
        dialog.title("Set Password Expiry")
        dialog.geometry("300x150")
        
        ttk.Label(dialog, text="Days until expiry (0 for never):").pack(pady=5)
        days_entry = ttk.Entry(dialog)
        days_entry.pack(pady=5)
        
        def set_expiry():
            try:
                days = int(days_entry.get())
                if days < 0:
                    raise ValueError("Days must be non-negative")
                    
                output, error, code = self.run_command(f"chage -M {days} {username}")
                if code != 0:
                    raise Exception(error)
                    
                messagebox.showinfo("Success", "Password expiry set successfully")
                dialog.destroy()
                self.scan_users()
                
            except ValueError as e:
                messagebox.showerror("Error", "Invalid number of days")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to set password expiry: {str(e)}")
        
        ttk.Button(dialog, text="Set Expiry", command=set_expiry).pack(pady=20)

    def export_user_report(self):
        try:
            filename = f"user_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as f:
                f.write("User Management Report\n")
                f.write("=" * 50 + "\n\n")
                
                for username, data in self.users_data.items():
                    f.write(f"Username: {username}\n")
                    f.write(f"UID: {data['uid']}\n")
                    f.write(f"GID: {data['gid']}\n")
                    f.write(f"Home: {data['home']}\n")
                    f.write(f"Shell: {data['shell']}\n")
                    f.write(f"Groups: {', '.join(data['groups'])}\n")
                    f.write(f"Account Status: {self.check_account_status(username)}\n")
                    f.write(f"Password Status: {self.check_password_expiry(username)}\n")
                    f.write("\n")
                
            messagebox.showinfo("Success", f"Report exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export report: {str(e)}")

                
            messagebox.show