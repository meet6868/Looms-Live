from PyQt5.QtWidgets import QLabel, QMessageBox
from datetime import datetime
import subprocess  # Add this import
import os
from utils.vm_manager import VMManager  # Add this import
import threading

startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
class StatusManager:
    """Manager for system status functionality"""
    def __init__(self, main_page):
        self.main_page = main_page
        self.admin_db = main_page.admin_db
        self.client_db = main_page.client_db
        self.local_db = main_page.local_db
        self.logger = main_page.logger
        
        # References to UI elements
        self.status_indicator = main_page.status_indicator
        self.dashboard_status_label = main_page.dashboard_status_label
        # self.license_progress = main_page.license_progress
        self.license_label = main_page.license_label
    
    def check_status(self):
        """Check system status and update UI"""
        try:
            # Show loading indicator
            if hasattr(self.main_page, 'show_loading'):
                self.main_page.show_loading("Checking system status...")
            
            # Get company name first
            company_name = self.local_db.get_value("company_name")
            if not company_name:
                self.logger.error("Company name not found in local database")
                return

            # Check admin database connection
            admin_connected = False
            try:
                admin_connected = self.admin_db.test_connection()
            except Exception as e:
                self.logger.error(f"Error connecting to admin database: {e}")
            
            # Check client database connection
            client_connected = False
            try:
                client_connected = self.client_db.test_connection()
            except Exception as e:
                self.logger.error(f"Error connecting to client database: {e}")

            self.local_db.set_value("admin_connected", "1" if admin_connected else "0")
            self.local_db.set_value("client_connected", "1" if client_connected else "0")
            self.logger.info(f"Admin connected: {admin_connected} update to local database")
            self.logger.info(f"Client connected: {client_connected} update to local database")
            
            # Check VM status and start if needed
            # if client_connected and admin_connected:
            self.check_and_start_vm()
            
            # Update status indicator
            status_data = {
                    'admin_connected': admin_connected,
                    'client_connected': client_connected,
                    'system_status': 'online' if (admin_connected and client_connected) else 'offline',
            }

            self.main_page.update_status_ui(status_data)
            
            
            # Check license status
            self.check_license_status()

            if client_connected:
                falgs=["admin_connected","client_connected","vm_running","vm_ip","license_active","last_checked","configuration_complete","company_name","admin_url","admin_key"]
                for flag in falgs:
                    value=self.local_db.get_value(flag)
                    self.client_db.set_value(flag,value)
                    self.logger.info(f"Update {flag} to client database")
            # Hide loading indicator
            if hasattr(self.main_page, 'hide_loading'):
                self.main_page.hide_loading()
                
        except Exception as e:
            self.logger.error(f"Error checking status: {e}")
            if hasattr(self.main_page, 'hide_loading'):
                self.main_page.hide_loading()
    
    def check_and_start_vm(self):
        """Check VM status and start if not running"""
        try:
            # Get VM paths from configuration
            client_config = self.local_db.get_client_config()
            vmrun_path = client_config.get("vm_path", "")
            vmx_path = client_config.get("system_path", "")
            
            if not vmrun_path or not vmx_path:
                self.logger.error("VM paths not configured properly")
                return
            
            # Clean paths
            vmrun_path_clean = vmrun_path.replace('"', '')
            vmx_path_clean = vmx_path.replace('"', '')
            
            # Check if paths exist
            if not os.path.exists(vmrun_path_clean):
                self.logger.error(f"VMRun path does not exist: {vmrun_path_clean}")
                return
            if not os.path.exists(vmx_path_clean):
                self.logger.error(f"VMX path does not exist: {vmx_path_clean}")
                return
            
            # Check if VM is running
            self.logger.info("Checking if VM is running...")
            try:
                result = subprocess.run(
                    [vmrun_path_clean, "list"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    timeout=30,
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                is_running = vmx_path_clean in result.stdout
                self.logger.info(f"VM running status: {is_running}")
                self.local_db.set_value("vm_running", "1" if is_running else "0")
                
                if not is_running:
                    # Start VM in background thread
                    self.logger.info("VM not running, starting in background...")
                    self.start_vm_background(vmrun_path_clean, vmx_path_clean)
                else:
                    self.logger.info("VM is already running")
                    # Get VM IP in background
                    self.get_vm_ip_background(vmrun_path_clean, vmx_path_clean)
            except Exception as e:
                self.logger.error(f"Error checking VM status: {e}")
        except Exception as e:
            self.logger.error(f"Error in check_and_start_vm: {e}")

    def restart_vm_if_needed(self,vmrun_path, vmx_path, max_wait=30):
        """
        Check if VM is running, and restart it if needed.
        Args:
            vmrun_path (str): Full path to vmrun.exe
            vmx_path (str): Full path to the VMX file
            max_wait (int): Max wait time in seconds after restarting
        Returns:
            bool: True if VM is running and ready to get IP, False otherwise
        """
        try:
            # Clean paths
            vmrun_path = vmrun_path.strip('"')
            vmx_path = vmx_path.strip('"')
            
            # Check if VM is running
            result = subprocess.run(
                [vmrun_path, "list"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=30,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            is_running = vmx_path in result.stdout

            if is_running:
                print("VM is already running, attempting to get IP...")
                ip = self.get_vm_ip(vmrun_path, vmx_path)
                if ip:
                    print(f"VM IP found: {ip}")
                    return True
                else:
                    print("No IP found. Restarting VM...")
                    self.stop_vm(vmrun_path, vmx_path)
                    time.sleep(3)

            print("Starting VM...")
            self.start_vm(vmrun_path, vmx_path)
            time.sleep(10)

            # Try to get IP again
            for _ in range(max_wait // 5):
                ip = self.get_vm_ip(vmrun_path, vmx_path)
                if ip:
                    print(f"VM restarted successfully. IP: {ip}")
                    return True
                time.sleep(5)

            print("VM started but IP could not be retrieved.")
            return False

        except Exception as e:
            print(f"Error in VM restart logic: {e}")
            self.logger.error(f"Error Come during Rstarting Vm {e} ")
            return False

    def stop_vm(self,vmrun_path, vmx_path):
        subprocess.run(
            [vmrun_path, "stop", vmx_path, "soft"],
            capture_output=True,
            text=True
        )
        print("VM stopped")

    def start_vm(self,vmrun_path, vmx_path):
        subprocess.run(
            [vmrun_path, "start", vmx_path],
            capture_output=True,
            text=True
        )
        print("VM started")

    def get_vm_ip(self,vmrun_path, vmx_path):
        try:
            result = subprocess.run(
                [vmrun_path, "-T", "ws", "getGuestIPAddress", vmx_path, "-wait"],
                capture_output=True,
                text=True,
                timeout=30,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            ip = result.stdout.strip()
            if ip and ip != "0.0.0.0" and "Error" not in ip:
                return ip
            return None
        except Exception:
            return None

        
    def restart_vm_in_background(self, vmrun_path, vmx_path):
        """Run the restart_vm_if_needed function in a background thread"""
        try:
            thread = threading.Thread(
                target=self.restart_vm_if_needed,
                args=(vmrun_path, vmx_path),
                daemon=True
            )
            thread.start()
            self.logger.info("Started VM restart thread")
        except Exception as e: 
            self.logger.error(f"Error Come During Restarting VM {e}")
    
    def start_vm_background(self, vmrun_path, vmx_path):
        """Start VM in background thread"""
        
        try:
            vm_thread = threading.Thread(
                target=self._start_vm_thread,
                args=(vmrun_path, vmx_path),
                daemon=True
            )
            vm_thread.start()
            self.logger.info("Started VM background thread")
        except Exception as e: 
            self.logger.error(f"Error Come During starting VM {e}")
    
    
    def _start_vm_thread(self, vmrun_path, vmx_path):
        """VM start thread function"""
        try:
            # First check if VMware is running, if not start it
            self._ensure_vmware_running()
            
            # Start VM command
            start_cmd = [vmrun_path, "-T", "ws", "start", vmx_path]
            self.logger.info(f"Starting VM with command: {' '.join(start_cmd)}")
            
            # Run command
            result = subprocess.run(
                start_cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=120,# Longer timeout
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW  
            )
            
            self.logger.info(f"VM start output: {result.stdout}")
            if result.stderr:
                self.logger.error(f"VM start error: {result.stderr}")
            
            # Get VM IP in background
            self.get_vm_ip_background(vmrun_path, vmx_path)
            
        except Exception as e:
            self.logger.error(f"Error in VM start thread: {e}")
    
    def _ensure_vmware_running(self):
        """Ensure VMware is running"""
        try:
            # Check if VMware Workstation process is running
            vmware_process = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq vmware.exe"],
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if "vmware.exe" not in vmware_process.stdout:
                self.logger.info("VMware is not running, starting it...")
                
                # Get VMware installation path from registry
                import winreg
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\VMware, Inc.\VMware Workstation")
                    vmware_install_path = winreg.QueryValueEx(key, "InstallPath")[0]
                    vmware_exe = os.path.join(vmware_install_path, "vmware.exe")
                    
                    if os.path.exists(vmware_exe):
                        # Start VMware in background
                        subprocess.Popen(
                            [vmware_exe],
                            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                            start_new_session=True,
                            startupinfo=startupinfo
               
                        )
                        self.logger.info(f"Started VMware from {vmware_exe}")
                        
                        # Wait for VMware to initialize
                        import time
                        time.sleep(5)
                    else:
                        self.logger.warning(f"VMware executable not found at {vmware_exe}")
                except Exception as reg_error:
                    self.logger.error(f"Error getting VMware path from registry: {reg_error}")
                    # Try common installation paths
                    common_paths = [
                        r"C:\Program Files (x86)\VMware\VMware Workstation\vmware.exe",
                        r"C:\Program Files\VMware\VMware Workstation\vmware.exe"
                    ]
                    for path in common_paths:
                        if os.path.exists(path):
                            subprocess.Popen(
                                [path],
                                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                                start_new_session=True,
                                startupinfo=startupinfo
               
                            )
                            self.logger.info(f"Started VMware from {path}")
                            import time
                            time.sleep(5)
                            break
        except Exception as vm_check_error:
            self.logger.error(f"Error checking VMware process: {vm_check_error}")
    
    def get_vm_ip_background(self, vmrun_path, vmx_path, retries=5, delay=2):
        """Get VM IP address in background"""
        import threading
        
        ip_thread = threading.Thread(
            target=self._get_vm_ip_thread,
            args=(vmrun_path, vmx_path, retries, delay),
            daemon=True
        )
        ip_thread.start()
        self.logger.info("Started VM IP retrieval thread")
    
    def _get_vm_ip_thread(self, vmrun_path, vmx_path, retries=5, delay=2):
        """VM IP retrieval thread function"""
        import time
        
        for attempt in range(retries):
            try:
                self.logger.info(f"Attempting to get IP (try {attempt+1}/{retries})...")
                result = subprocess.run(
                    [vmrun_path, "-T", "ws", "getGuestIPAddress", vmx_path, "-wait"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    timeout=30,
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                ip = result.stdout.strip()
                self.logger.info(f"VM IP attempt {attempt+1}: {ip}")
                
                if ip and ip != "0.0.0.0" and "Error" not in ip:
                    self.local_db.set_value("vm_ip", ip)
                    self.local_db.set_value("vm_running", "1")
                    self.logger.info(f"Successfully got VM IP: {ip}")
                    return ip
                
                # Wait before next attempt
                time.sleep(delay)
            except Exception as e:
                self.logger.error(f"Error getting VM IP (attempt {attempt+1}): {e}")
                time.sleep(delay)
        
        # All attempts failed, use cached IP
        try:
            self.restart_vm_in_background(vmrun_path,vmx_path)
        except:
            self.logger.error("Error in restertin VM")
        saved_ip = self.local_db.get_value("vm_ip")

        if saved_ip:
            self.logger.info(f"Using cached VM IP: {saved_ip}")
            return saved_ip
        

        
        self.logger.warning("Could not get VM IP")
        return None
    
    def check_license_status(self):
        """Check license status and expiration date"""
        try:
            # Initialize variables
            license_active = False
            days_remaining = 0
            
            # Get license data from local database
            license_data = self.local_db.get_client_config()
            
            if not license_data:
                # Try getting dates directly if no config
                start_date_str = self.local_db.get_value("start_date")
                end_date_str = self.local_db.get_value("end_date")
            else:
                start_date_str = license_data.get('start_date')
                end_date_str = license_data.get('end_date')
            
            if end_date_str:
                # Parse dates and calculate remaining time
                expiry_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                current_date = datetime.now()
                days_remaining = (expiry_date - current_date).days
                
                if start_date_str:
                    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                    days_total = (expiry_date - start_date).days
                    days_passed = (current_date - start_date).days
                    percent_used = min(100, max(0, int((days_passed / days_total) * 100)))
                else:
                    # Fallback to 365-day calculation if no start date
                    total_days = 365
                    used_days = total_days - days_remaining
                    percent_used = min(100, max(0, int((used_days / total_days) * 100)))
                
                license_active = days_remaining > 0
                
            else:
                # No license data found
                if hasattr(self.main_page, 'license_label') and self.main_page.license_label:
                    self.license_label.setText("Not Found")
                    self.license_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                if hasattr(self.main_page, 'license_progress') and self.main_page.license_progress:
                    self.license_progress.setValue(100)
            
            # Store status in local database
            status_data = {
                "license_active": 1 if license_active else 0,
                "days_remaining": days_remaining,
                "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Update local database
            for key, value in status_data.items():
                self.local_db.set_value(key, str(value))
                self.logger.info(f"Updated {key} in local database: {value}")
                
        except Exception as e:
            self.logger.error(f"Error checking license status: {e}")
            if hasattr(self.main_page, 'license_label') and self.main_page.license_label:
                self.license_label.setText("Error")
                self.license_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            
       
    
    def show_status_dialog(self):
        """Show the system status dialog"""
        try:
            from ui.components.status_dialog import StatusDialog
            
            # Create and show the status dialog
            dialog = StatusDialog(self.main_page)
            
            # Make sure the dialog is properly initialized before showing it
            if hasattr(dialog, 'admin_status') and hasattr(dialog, 'client_status'):
                dialog.exec_()
            else:
                self.logger.error("Status dialog not properly initialized")
                QMessageBox.warning(self.main_page, "Error", "Could not display status information: Dialog initialization failed")
                
        except Exception as e:
            self.logger.error(f"Error showing status dialog: {e}")
            QMessageBox.warning(self.main_page, "Error", f"Could not display status information: {e}")

    def check_vm_subprocess(self, vm_path):
        """Check VM subprocess status"""
        try:
            # Get client configuration
            client_config = self.local_db.get_client_config()
            vmware_path = client_config.get("vm_path", 
                r"C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe")
            
            if not os.path.exists(vmware_path):
                self.logger.error(f"VMware path not found: {vmware_path}")
                return {
                    'running': False,
                    'ip': '',
                    'status': 'vmware_not_found'
                }
            
            if not vm_path:
                self.logger.error("VM path not found in client configuration")
                return {
                    'running': False,
                    'ip': '',
                    'status': 'not_configured'
                }
            
            # Initialize VM manager with correct path
            vm_manager = VMManager(vmrun_path=vmware_path)
            is_running, message = vm_manager.check_vm_running(vm_path)
            
            ip_address = ""
            if is_running:
                # Get IP if running
                ip_address = vm_manager.get_vm_ip(vm_path)
            
            return {
                'running': is_running,
                'ip': ip_address,
                'status': 'running' if is_running else 'stopped',
                'message': message
            }

            self.local_db.set_value("vm_running", "1" if is_running else "0")
            self.local_db.set_value("vm_ip", ip_address)
            self.logger.info("VM subprocess status updated in local database")
            
        except Exception as e:
            self.logger.error(f"Error checking VM subprocess: {e}")
            return {
                'running': False,
                'ip': '',
                'status': 'error'
            }
            
       