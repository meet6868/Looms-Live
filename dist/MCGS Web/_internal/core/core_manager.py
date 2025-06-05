import threading
import time
from .admin_service_manager import AdminServiceManager
from .client_service_manager import ClientServiceManager

status_lock = threading.Lock()

def safe_set_status(db, key, value):
    with status_lock:
        db.set_core_value(key, value)

class CoreManager:
    def __init__(self, local_db, client_db, logger):
        self.local_db = local_db
        self.client_db = client_db
        self.logger = logger
        self.admin_manager = AdminServiceManager(local_db, client_db, logger)
        self.client_manager = ClientServiceManager(local_db, client_db, logger)
        self.is_running = False
        self.monitor_thread = None

        # Initialize all statuses to Stopped on startup
        self.set_both_db("admin_service_status", "Stopped")
        self.set_both_db("client_service_status", "Stopped")
        safe_set_status(self.local_db, "client_login_status", "Stopped")
        safe_set_status(self.local_db, "client_init_status", None)

    def set_both_db(self, key, value):
        safe_set_status(self.local_db, key, value)
        self.client_db.set_core_value(key, value)

    def _safe_sleep(self, duration):
        """Sleep in short intervals so thread can stop quickly."""
        interval = 0.2
        elapsed = 0
        while self.is_running and elapsed < duration:
            time.sleep(interval)
            elapsed += interval

    def start_monitoring(self):
        try:
            if not self.is_running:
                self.is_running = True
                self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
                self.monitor_thread.start()
                self.set_both_db("admin_service_status", "starting")
                self.set_both_db("client_service_status", "starting")
                self.logger.info("Core monitoring started")
        except Exception as e:
            self.logger.exception("Error starting monitoring")

    def stop_monitoring(self):
        self.is_running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        self.monitor_thread = None
        self.admin_manager.cleanup()
        self.logger.info("Core monitoring stopped")

    def _monitor_loop(self):
        admin_init_retry_time = 0
        last_status = None

        while self.is_running:
            try:
                vm_running = self.local_db.get_value("vm_running")
                if not vm_running or vm_running == "0":
                    self.logger.info("VM not running, waiting...")
                    if self.admin_manager.backend_driver:
                        self.admin_manager.cleanup()
                    self.client_manager.cleanup()
                    safe_set_status(self.local_db, "client_init_status", None)
                    safe_set_status(self.local_db, "client_login_status", "Stopped")
                    self._safe_sleep(60)
                    continue

                if not self.admin_manager.backend_driver:
                    if time.time() < admin_init_retry_time:
                        self._safe_sleep(10)
                        continue

                    self.logger.info("Initializing admin service...")
                    if not self.admin_manager.initialize_service():
                        self.logger.error("Failed to initialize admin service")
                        self.set_both_db("admin_service_status", "Error")
                        admin_init_retry_time = time.time() + 30
                        continue
                    else:
                        safe_set_status(self.local_db, "client_init_status", None)
                        safe_set_status(self.local_db, "client_login_status", "Stopped")
                        self._safe_sleep(5)

                status = self.admin_manager.check_service_status()
                self.set_both_db("admin_service_status", status)

                if status == 'Error':
                    self.logger.error("Error checking admin service status")
                    self.admin_manager.cleanup()
                    self.client_manager.cleanup()
                    safe_set_status(self.local_db, "client_init_status", None)
                    safe_set_status(self.local_db, "client_login_status", "Error")
                    admin_init_retry_time = time.time() + 30
                    continue

                init_status = self.local_db.get_core_value("client_init_status")
                client_status = self.local_db.get_core_value("client_login_status")

                should_initialize = (
                    status == "Running" and
                    (not self.client_manager.client_driver) and
                    init_status not in ["in_progress", "completed"]
                )

                if should_initialize:
                    self.logger.info("Starting client initialization...")
                    if not self.client_manager.initialize_client():
                        self.logger.error("Failed to initialize client service")
                        safe_set_status(self.local_db, "client_init_status", "error")
                        self._safe_sleep(30)
                        continue

                if status == 'Stopped':
                    self.logger.info("Admin service stopped, attempting to start...")
                    if not self.admin_manager.start_service():
                        self.logger.error("Failed to start admin service")
                        self.set_both_db("admin_service_status", "Error")
                        admin_init_retry_time = time.time() + 30
                        continue

                init_status = self.local_db.get_core_value("client_init_status")
                client_status = self.local_db.get_core_value("client_login_status")

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
                        safe_set_status(self.local_db, "client_login_status", "Error")
                        self.client_db.set_core_value("client_login_status", "Error")
                        safe_set_status(self.local_db, "client_init_status", "error")
                        self._safe_sleep(30)
                        continue
                    else:
                        self.set_both_db("client_login_status", "Running")
                        self.logger.info("Client service initialized successfully")

                if status == "Running" and self.client_manager.client_driver:
                    self.set_both_db("client_login_status", "Running")
                    self.logger.info("--------Client service Running--------")

                if status != last_status:
                    self.logger.info(f"Service status changed from {last_status} to {status}")
                    last_status = status

                self._safe_sleep(10)

            except Exception as e:
                self.logger.exception("Error in monitor loop")
                self.set_both_db("admin_service_status", "Error")
                safe_set_status(self.local_db, "client_init_status", "error")
                if self.admin_manager.backend_driver:
                    self.admin_manager.cleanup()
                admin_init_retry_time = time.time() + 60
                self._safe_sleep(10)
                last_status = None
