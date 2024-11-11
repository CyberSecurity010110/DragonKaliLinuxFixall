import os
import subprocess
import logging
from datetime import datetime
from shutil import copyfile

logging.basicConfig(level=logging.DEBUG)

def backup_file(file_path):
    """Backup the specified file."""
    backup_path = f"{file_path}.bak_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    copyfile(file_path, backup_path)
    logging.info(f"Backup created: {backup_path}")
    return backup_path

def run_command(command):
    """Run a shell command and return the output."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    logging.debug(f"Command: {command}")
    logging.debug(f"Return code: {result.returncode}")
    logging.debug(f"Output: {result.stdout.strip()}")
    logging.debug(f"Error: {result.stderr.strip()}")
    return result.returncode, result.stdout.strip(), result.stderr.strip()

def check_ethernet_connection():
    """Check if the Ethernet connection is up."""
    logging.info("Checking Ethernet connection...")
    ret_code, output, error = run_command("ethtool eth0")
    if ret_code != 0:
        logging.error(f"Ethernet check failed: {error}")
        return False, error
    if "Link detected: yes" in output:
        logging.info("Ethernet connection is up.")
        return True, "Ethernet connection is up."
    else:
        logging.warning("Ethernet connection is down.")
        return False, "Ethernet connection is down."

def check_network_services():
    """Check the status of network services."""
    logging.info("Checking network services...")
    services = ["NetworkManager", "networking"]
    service_status = {}
    for service in services:
        ret_code, output, error = run_command(f"systemctl is-active {service}")
        service_status[service] = output
        logging.info(f"{service} status: {output}")
    return service_status

def restart_network_services():
    """Restart network services."""
    logging.info("Restarting network services...")
    services = ["NetworkManager", "networking"]
    for service in services:
        ret_code, output, error = run_command(f"systemctl restart {service}")
        if ret_code == 0:
            logging.info(f"{service} restarted successfully.")
        else:
            logging.error(f"Failed to restart {service}: {error}")

def check_ip_configuration():
    """Check IP configuration."""
    logging.info("Checking IP configuration...")
    ret_code, output, error = run_command("ip addr show")
    if ret_code != 0:
        logging.error(f"IP configuration check failed: {error}")
        return False, error
    logging.info(f"IP configuration:\n{output}")
    return True, output

def renew_dhcp_lease():
    """Renew DHCP lease."""
    logging.info("Renewing DHCP lease...")
    ret_code, output, error = run_command("dhclient -r && dhclient")
    if ret_code == 0:
        logging.info("DHCP lease renewed successfully.")
        return True, "DHCP lease renewed successfully."
    else:
        logging.error(f"Failed to renew DHCP lease: {error}")
        return False, error

def check_network():
    """Comprehensive network check and repair."""
    logging.info("Starting comprehensive network check...")

    # Check Ethernet connection
    eth_status, eth_message = check_ethernet_connection()
    if not eth_status:
        logging.warning(eth_message)
        logging.info("Attempting to restart network services...")
        restart_network_services()
        eth_status, eth_message = check_ethernet_connection()
        if not eth_status:
            logging.error("Failed to resolve Ethernet connection issue.")
            return False, eth_message

    # Check network services
    service_status = check_network_services()
    for service, status in service_status.items():
        if status != "active":
            logging.warning(f"{service} is not active. Attempting to restart...")
            restart_network_services()
            service_status = check_network_services()
            if service_status[service] != "active":
                logging.error(f"Failed to resolve {service} issue.")
                return False, f"{service} is not active"

    # Check IP configuration
    ip_status, ip_message = check_ip_configuration()
    if not ip_status:
        logging.warning(ip_message)
        logging.info("Attempting to renew DHCP lease...")
        renew_status, renew_message = renew_dhcp_lease()
        if not renew_status:
            logging.error("Failed to renew DHCP lease.")
            return False, renew_message

    logging.info("Network check completed successfully.")
    return True, "Network check completed successfully."

if __name__ == "__main__":
    success, message = check_network()
    if success:
        logging.info("Network is functioning correctly.")
    else:
        logging.error(f"Network issues detected: {message}")
