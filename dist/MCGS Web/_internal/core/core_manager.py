import threading
import time
from .admin_service_manager import AdminServiceManager
from .client_service_manager import ClientServiceManager

class CoreManager:
    def __init__(self, local_db, client_db, logger):
        self.local_db = local_db
        self.client_db = client_db
        self.logger = logger
        self.admin_manager = AdminServiceManager(local_db, client_db, logger)
        self.client_manager = ClientServiceManager(local_db,client_db, logger)
        self.is_running = False
        self.monitor_thread = None
        
        # Initialize all statuses to Stopped on startup
        self.local_db.set_core_value("admin_service_status", "Stopped")
        self.client_db.set_core_value("admin_service_status", "Stopped")
        self.local_db.set_core_value("client_service_status", "Stopped")
        self.client_db.set_core_value("client_service_status", "Stopped")
        self.local_db.set_core_value("client_login_status", "Stopped")
        self.local_db.set_core_value("client_init_status", None)
    
    def start_monitoring(self):
        """Start the monitoring thread"""
        try:
            if not self.is_running:
                self.is_running = True
                self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
                self.monitor_thread.start()
                self.local_db.set_core_value("admin_service_status", "starting")
                self.client_db.set_core_value("admin_service_status", "starting")
                self.local_db.set_core_value("client_service_status", "starting")
                self.client_db.set_core_value("client_service_status", "starting")
                self.logger.info("Core monitoring started")
        except Exception as e:
            self.logger.error(f"Error starting monitoring: {str(e)}")
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.admin_manager.cleanup()
        self.logger.info("Core monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        admin_init_retry_time = 0
        last_status = None
        
        while self.is_running:
            try:
                # Check VM status
                vm_running = self.local_db.get_value("vm_running")
                if not vm_running or vm_running == "0":
                    self.logger.info("VM not running, waiting...")
                    if self.admin_manager.backend_driver:
                        self.admin_manager.cleanup()
                    self.client_manager.cleanup()
                    self.local_db.set_core_value("client_init_status", None)
                    self.local_db.set_core_value("client_login_status", "Stopped")
                    time.sleep(60)
                    continue

                # Initialize admin service if needed
                if not self.admin_manager.backend_driver:
                    if time.time() < admin_init_retry_time:
                        time.sleep(10)
                        continue
                        
                    self.logger.info("Initializing admin service...")
                    if not self.admin_manager.initialize_service():
                        self.logger.error("Failed to initialize admin service")
                        self.local_db.set_core_value("admin_service_status", "Error")
                        self.client_db.set_core_value("admin_service_status", "Error")
                        admin_init_retry_time = time.time() + 30
                        continue
                    else:
                        # Successfully initialized admin service, reset client status
                        self.local_db.set_core_value("client_init_status", None)
                        self.local_db.set_core_value("client_login_status", "Stopped")
                        time.sleep(5)  # Wait for admin service to stabilize

                # Get current admin status
                status = self.admin_manager.check_service_status()
                
                # Update admin status in databases
                self.local_db.set_core_value("admin_service_status", status)
                self.client_db.set_core_value("admin_service_status", status)
                
                if status == 'Error':
                    self.logger.error("Error checking admin service status")
                    self.admin_manager.cleanup()
                    self.client_manager.cleanup()
                    self.local_db.set_core_value("client_init_status", None)
                    self.local_db.set_core_value("client_login_status", "Error")
                    admin_init_retry_time = time.time() + 30
                    continue

                # Check client initialization status
                init_status = self.local_db.get_core_value("client_init_status")
                client_status = self.local_db.get_core_value("client_login_status")
                
                # Simplified initialization check
                should_initialize = (
                    status == "Running" and
                    (not self.client_manager.client_driver or client_status != "Running") and
                    init_status != "in_progress"
                )

                if should_initialize:
                    self.logger.info("Starting client initialization...")
                    if not self.client_manager.initialize_client():
                        self.logger.error("Failed to initialize client service")
                        self.local_db.set_core_value("client_init_status", "error")
                        time.sleep(30)
                        continue

                # Rest of the monitoring loop remains the same...
                if status == 'Stopped':
                    self.logger.info("Admin service stopped, attempting to start...")
                    if not self.admin_manager.start_service():
                        self.logger.error("Failed to start admin service")
                        self.local_db.set_core_value("admin_service_status", "Error")
                        self.client_db.set_core_value("admin_service_status", "Error")
                        admin_init_retry_time = time.time() + 30
                        continue

                # Check client initialization status
                init_status = self.local_db.get_core_value("client_init_status")
                client_status = self.local_db.get_core_value("client_login_status")
                
                # Only initialize if admin is running and client needs initialization
                should_initialize = (
                    status == "Running" and
                    (init_status in ["error", None] or client_status in ["Error", "Stopped", None]) and
                    init_status != "in_progress" and
                    not self.client_manager.client_driver
                )

                if should_initialize:
                    self.logger.info("Starting client initialization...")
                    if not self.client_manager.initialize_client():
                        self.logger.error("Failed to initialize client service")
                        self.local_db.set_core_value("client_login_status", "Error")
                        self.client_db.set_core_value("client_login_status", "Error")
                        self.local_db.set_core_value("client_init_status", "error")
                        time.sleep(30)  # Wait before retry
                        continue
                    else:
                        self.local_db.set_core_value("client_login_status", "Running")
                        self.client_db.set_core_value("client_login_status", "Running")
                        self.logger.info("Client service initialized successfully")
                
                # Update running status
                if status == "Running" and self.client_manager.client_driver:
                    self.local_db.set_core_value("client_login_status", "Running")
                    self.client_db.set_core_value("client_login_status", "Running")
                    self.logger.info("--------Client service Running--------")

                # Log status changes
                if status != last_status:
                    self.logger.info(f"Service status changed from {last_status} to {status}")
                    last_status = status
                
                time.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {str(e)}")
                self.local_db.set_core_value("admin_service_status", "Error")
                self.client_db.set_core_value("admin_service_status", "Error")
                self.local_db.set_core_value("client_init_status", "error")
                if self.admin_manager.backend_driver:
                    self.admin_manager.cleanup()
                admin_init_retry_time = time.time() + 60
                time.sleep(10)
                last_status = None
