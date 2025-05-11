import subprocess
import time
import paramiko
import logging
import os
import sys
import time

startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
class VMManager:
    def __init__(self, vmrun_path=None, ssh_port=22):
        # Set default vmrun path
        self.vmrun_path = vmrun_path
        self.ssh_port = ssh_port
        self.logger = logging.getLogger("LoomLive.VMManager")
    
    def check_vm_running(self, vmx_path):
        """Check if VM is running"""
        try:
            result = subprocess.run(
                [self.vmrun_path, "list"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            is_running = vmx_path in result.stdout
            return is_running, "VM is running" if is_running else "VM is not running"
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Error checking VM status: {e}")
            return False, f"Error checking VM status: {e}"
        except Exception as e:
            self.logger.error(f"Unexpected error checking VM status: {e}")
            return False, f"Unexpected error: {e}"
    
    def start_vm(self, vmx_path):
        """Start VM using vmrun.exe"""
        try:
            self.logger.info(f"Starting VM: {self.vmrun_path} start {vmx_path} nogui")
            
            # Execute vmrun command to start VM
            subprocess.run(
                [self.vmrun_path, 'start', vmx_path, 'nogui'],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                errors='ignore',
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            self.logger.info(f"VM started successfully: {vmx_path}")
            return True, "VM started successfully"
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to start VM: {e}")
            return False, f"Failed to start VM: {e}"
        except Exception as e:
            self.logger.error(f"Error starting VM: {e}")
            return False, f"Error starting VM: {e}"
    
    def stop_vm(self, vmx_path, hard=False):
        """Stop VM"""
        try:
            # Check if VM is running
            is_running, _ = self.check_vm_running(vmx_path)
            if not is_running:
                return True, "VM is already stopped"
            
            # Stop VM
            cmd = [self.vmrun_path, "stop", vmx_path]
            if hard:
                cmd.append("hard")
            
            self.logger.info(f"Stopping VM: {' '.join(cmd)}")
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                errors='ignore',
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True, "VM stopped successfully"
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to stop VM: {e}")
            return False, f"Failed to stop VM: {e}"
        except Exception as e:
            self.logger.error(f"Unexpected error stopping VM: {e}")
            return False, f"Unexpected error: {e}"
    
    def get_vm_ip(self, vm_path, wait=True, retries=10, delay=10):
        """Get the IP address of a running VM"""
        try:
            for attempt in range(retries):
                self.logger.info(f"Attempting to get IP (try {attempt+1}/{retries})...")
                cmd = [self.vmrun_path, "getGuestIPAddress", vm_path]
                if wait:
                    cmd.append("-wait")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NO_WINDOW

                )
                
                if result.returncode == 0 and result.stdout:
                    ip = result.stdout.strip()
                    if ip and ip != "0.0.0.0":
                        self.logger.info(f"Got IP: {ip}")
                        return ip, "Success"
                
                self.logger.info(f"IP not available yet, waiting {delay} seconds...")
                time.sleep(delay)
            
            return None, "Failed to get IP after multiple attempts"
        except Exception as e:
            self.logger.error(f"Error getting VM IP: {str(e)}")
            return None, f"Error getting VM IP: {str(e)}"

    def run_vm_and_get_ip(self, vmx_path, username=None, password=None):
        """Start VM and get IP address"""
        try:
            # Validate VMX path
            if not os.path.exists(vmx_path):
                self.logger.error(f"VMX file not found: {vmx_path}")
                return None, f"VMX file not found: {vmx_path}"
            
            # Check if VM is running
            is_running, _ = self.check_vm_running(vmx_path)
            if not is_running:
                # Start VM
                success, message = self.start_vm(vmx_path)
                if not success:
                    return None, message
                
                # Wait for VM to fully boot
                self.logger.info("Waiting for VM to boot...")
                time.sleep(30)  # Increased boot wait time
            
            # Get IP (with increased retries and delay)
            self.logger.info("Getting VM IP address...")
            ip, message = self.get_vm_ip(vmx_path, wait=True, retries=15, delay=20)
            if not ip:
                return None, message
            
            # Check SSH login
            if username and password:
                self.logger.info("Checking SSH login...")
                success, message = self.check_ssh_login(ip, username, password, retries=5, delay=10)
                if not success:
                    return ip, f"Got IP ({ip}) but SSH login failed: {message}"
            
            return ip, f"VM is ready with IP: {ip}"
        except Exception as e:
            self.logger.error(f"Error in run_vm_and_get_ip: {e}")
            return None, f"Error: {e}"
    
    def check_ssh_login(self, ip, username, password, retries=5, delay=5):
        """Check SSH login"""
        try:
            for attempt in range(retries):
                self.logger.info(f"Trying SSH login... (try {attempt+1}/{retries})")
                try:
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(ip, port=self.ssh_port, username=username, password=password, timeout=10)
                    self.logger.info("SSH login successful")
                    ssh.close()
                    return True, "SSH login successful"
                except Exception as e:
                    self.logger.warning(f"SSH login failed: {e}")
                    time.sleep(delay)
            
            return False, "SSH login failed after multiple attempts"
        except Exception as e:
            self.logger.error(f"Unexpected error checking SSH login: {e}")
            return False, f"Unexpected error: {e}"