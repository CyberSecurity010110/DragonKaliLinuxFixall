# modules/customize_options.py

import os

def change_hostname(new_hostname, progress_callback):
    try:
        print(f"Changing hostname to {new_hostname}...")
        progress_callback(50)
        os.system(f"sudo hostnamectl set-hostname {new_hostname}")
        os.system(f"echo {new_hostname} | sudo tee /etc/hostname")
        os.system(f"sudo sed -i 's/127.0.1.1.*/127.0.1.1 {new_hostname}/' /etc/hosts")
        progress_callback(100)
        print(f"Hostname changed to {new_hostname}.")
    except Exception as e:
        print(f"Error changing hostname: {e}")

def setup_static_ip(interface, ip_address, netmask, gateway, progress_callback):
    try:
        print(f"Setting up static IP on {interface}...")
        progress_callback(30)
        config = f"""
auto {interface}
iface {interface} inet static
    address {ip_address}
    netmask {netmask}
    gateway {gateway}
"""
        with open(f"/etc/network/interfaces.d/{interface}", "w") as file:
            file.write(config)
        os.system(f"sudo ifdown {interface} && sudo ifup {interface}")
        progress_callback(100)
        print(f"Static IP setup on {interface}.")
    except Exception as e:
        print(f"Error setting up static IP: {e}")

def configure_ssh(enable, progress_callback):
    try:
        if enable:
            print("Enabling SSH...")
            progress_callback(50)
            os.system("sudo systemctl enable ssh")
            os.system("sudo systemctl start ssh")
            progress_callback(100)
            print("SSH enabled.")
        else:
            print("Disabling SSH...")
            progress_callback(50)
            os.system("sudo systemctl stop ssh")
            os.system("sudo systemctl disable ssh")
            progress_callback(100)
            print("SSH disabled.")
    except Exception as e:
        print(f"Error configuring SSH: {e}")
