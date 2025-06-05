import time
from PyQt5.QtCore import QThread, pyqtSignal

class AdminConnectionTestThread(QThread):
    connection_result = pyqtSignal(bool, str)
    
    def __init__(self, url, api_key):
        super().__init__()
        self.url = url
        self.api_key = api_key
        self.is_running = True
    
    def run(self):
        try:
            # Update the import statement in your worker_threads.py file
            from database.admin_db import AdminDatabase  # Changed from admin_database
            # Create a temporary AdminDatabase instance to test connection
            admin_db = AdminDatabase(self.url, self.api_key)
            if self.is_running and admin_db.test_connection():
                self.connection_result.emit(True, "Connection successful")
            else:
                self.connection_result.emit(False, "Connection failed")
        except Exception as e:
            if self.is_running:
                self.connection_result.emit(False, str(e))
    
    def stop(self):
        self.is_running = False
        self.wait()  # Wait for the thread to finish


class ClientConnectionTestThread(QThread):
    connection_result = pyqtSignal(bool, str)
    
    def __init__(self, url, api_key):
        super().__init__()
        self.url = url
        self.api_key = api_key
        self.is_running = True
    
    def run(self):
        try:
            from database.client_db import ClientDatabase
            client_db = ClientDatabase(self.url, self.api_key)
            if self.is_running and client_db.test_connection():
                self.connection_result.emit(True, "Connection successful")
            else:
                self.connection_result.emit(False, "Connection failed")
        except Exception as e:
            if self.is_running:
                self.connection_result.emit(False, str(e))
    
    def stop(self):
        self.is_running = False
        self.wait()  # Wait for the thread to finish


class CompanyNameCheckThread(QThread):
    check_result = pyqtSignal(bool, str)
    
    def __init__(self, admin_db, company_name, client_email="", client_url="", client_key=""):
        super().__init__()
        self.admin_db = admin_db
        self.company_name = company_name
        self.client_email = client_email
        self.client_url = client_url
        self.client_key = client_key
    
    def run(self):
        try:
            # First check if company name + email combination exists
            if self.client_email:
                company_email_exists = self.admin_db.check_company_email_exists(
                    self.company_name, self.client_email
                )
                if company_email_exists:
                    self.check_result.emit(True, "Company name and email combination already exists")
                    return
            
            # If company name doesn't exist with this email, check if URL + key combination exists
            if self.client_url and self.client_key:
                client_combo_exists = self.admin_db.check_client_credentials_exist(
                    self.client_url, self.client_key
                )
                if client_combo_exists:
                    self.check_result.emit(True, "Database URL and API Key combination already in use")
                    return
            
            # If we get here, nothing exists
            self.check_result.emit(False, "Available")
            
        except Exception as e:
            import logging
            logging.getLogger("LoomLive").error(f"Error checking company name: {str(e)}")
            # In case of error, assume it exists to be safe
            self.check_result.emit(True, "Error checking availability")


class VMCheckThread(QThread):
    check_result = pyqtSignal(bool, str, object)
    
    def __init__(self, vm_manager, vm_path):
        super().__init__()
        self.vm_manager = vm_manager
        self.vm_path = vm_path
    
    def run(self):
        try:
            # Check if VM is running
            running, message = self.vm_manager.check_vm_running(self.vm_path)
            
            if not running:
                # Try to start VM
                success, message = self.vm_manager.start_vm(self.vm_path)
                
                if not success:
                    self.check_result.emit(False, message, None)
                    return
                
                # Give VM some time to start
                time.sleep(30)
            
            # Multiple attempts to get VM IP
            ip = None
            for attempt in range(5):
                ip, message = self.vm_manager.get_vm_ip(self.vm_path)
                if ip and ip != "0.0.0.0":
                    break
                time.sleep(10)  # 10 seconds between attempts
            
            if ip and ip != "0.0.0.0":
                # Try SSH login to verify IP is available
                try:
                    import paramiko
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(ip, port=22, username="ubuntu", password="1234", timeout=10)
                    ssh.close()
                    self.check_result.emit(True, "VM is running and SSH connection successful", ip)
                except Exception as e:
                    self.check_result.emit(True, f"VM is running, but SSH connection failed: {str(e)}", ip)
            else:
                self.check_result.emit(True, "VM is running, but IP could not be detected", None)
        except Exception as e:
            self.check_result.emit(False, str(e), None)


class TesseractCheckThread(QThread):
    check_result = pyqtSignal(bool, str)
    
    def __init__(self, tesseract_checker, tesseract_path):
        super().__init__()
        self.tesseract_checker = tesseract_checker
        self.tesseract_path = tesseract_path
    
    def run(self):
        try:
            version = self.tesseract_checker.check_tesseract(self.tesseract_path)
            if version:
                self.check_result.emit(True, f"Version {version}")
            else:
                self.check_result.emit(False, "Could not determine version")
        except Exception as e:
            self.check_result.emit(False, str(e))


class CompanyEmailCheckThread(QThread):
    check_result = pyqtSignal(bool, str)
    
    def __init__(self, admin_db, company_name, client_email):
        super().__init__()
        self.admin_db = admin_db
        self.company_name = company_name
        self.client_email = client_email
    
    def run(self):
        try:
            exists = self.admin_db.check_company_email_exists(
                self.company_name, self.client_email
            )
            self.check_result.emit(exists, "This combination is already registered")
        except Exception as e:
            import logging
            logging.getLogger("LoomLive").error(f"Error checking company email: {str(e)}")
            self.check_result.emit(True, f"Error: {str(e)}")

class URLKeyCheckThread(QThread):
    check_result = pyqtSignal(bool, str)
    
    def __init__(self, admin_db, client_url, client_key):
        super().__init__()
        self.admin_db = admin_db
        self.client_url = client_url
        self.client_key = client_key
    
    def run(self):
        try:
            exists = self.admin_db.check_client_credentials_exist(
                self.client_url, self.client_key
            )
            self.check_result.emit(exists, "This combination is already registered")
        except Exception as e:
            import logging
            logging.getLogger("LoomLive").error(f"Error checking URL and key: {str(e)}")
            self.check_result.emit(True, f"Error: {str(e)}")


from PyQt5.QtCore import QThread, pyqtSignal

from datetime import datetime
import time
import logging

class StatusCheckerThread(QThread):
    status_updated = pyqtSignal(dict)
    
    def __init__(self, admin_db, client_db, local_db, vm_manager):
        super().__init__()
        self.admin_db = admin_db
        self.client_db = client_db
        self.local_db = local_db
        self.vm_manager = vm_manager
        self.running = True
        self.logger = logging.getLogger("LoomLive")

    def run(self):
        while self.running:
            try:
                # Check database connections
                admin_connected = False
                client_connected = False
                
                try:
                    admin_connected = self.admin_db.test_connection()
                    self.logger.info(f"Admin DB connection: {admin_connected}")
                except Exception as admin_e:
                    self.logger.error(f"Admin DB connection error: {admin_e}")
                
                try:
                    client_connected = self.client_db.test_connection()
                    self.logger.info(f"Client DB connection: {client_connected}")
                except Exception as client_e:
                    self.logger.error(f"Client DB connection error: {client_e}")


                admin_serevice=self.local_db.get_value("admin_service_status")
                client_service=self.local_db.get_value("client_service_status")
                # Prepare status data
                status_data = {
                    'admin_connected': admin_connected,
                    'client_connected': client_connected,
                    'admin_service_status': admin_serevice,
                    'client_service_status': client_service,
                    'system_status': 'online' if (admin_connected and client_connected) else 'offline',
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                self.logger.info(f"Emitting status data: {status_data}")
                self.status_updated.emit(status_data)
                
            except Exception as e:
                self.logger.error(f"Error in status checker thread: {e}")
                # Emit error status
                self.status_updated.emit({
                    'admin_connected': False,
                    'client_connected': False,
                    'system_status': 'error'
                })
            
            # Wait before next check
            time.sleep(30)

    def stop(self):
        self.running = False
        self.wait()