import sys
import os
import logging
import requests
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from database.local_db import LocalDatabase
from database.admin_db import AdminDatabase
from database.client_db import ClientDatabase
from ui.welcome_page import WelcomePage
from ui.configure_page import ConfigurePage
from ui.main_page import MainPage
from utils.logger import setup_logger
from app_controller import AppController
from utils.path_utils import get_icon_path
import threading
from utils.redis_manager import RedisManager

class LoomLive:
    def __init__(self):
        # Setup logger
        self.logger = setup_logger()
        self.logger.info("Application started")
        
        # Initialize local database
        self.local_db = LocalDatabase()
        self.local_db.initialize()
        
        # Initialize admin and client databases
        # Get credentials from local database if available
        admin_config = self.local_db.get_admin_config()
        self.admin_db = AdminDatabase(admin_config.get("admin_url", ""), 
                                     admin_config.get("admin_key", ""))
        
        # Get client credentials
        client_config = self.local_db.get_client_config() if hasattr(self.local_db, 'get_client_config') else {}
        client_url = client_config.get("client_url", "")
        client_key = client_config.get("client_key", "")
        self.client_db = ClientDatabase(client_url, client_key)
        
        # Initialize Redis manager
        self.redis_manager = RedisManager(self.local_db)
        self.redis_manager.start_upload()
        self.logger.info("Redis upload service started")
        
        # Track active threads
        self.active_threads = []
        
        # Check if first time launch
        is_first_time = self.local_db.get_value("first_time_launch", "true") == "true"
        
        # Initialize main application window
        if is_first_time:
            self.logger.info("First time launch detected, showing welcome page")
            self.current_window = WelcomePage(self)
        else:
            self.logger.info("Returning user detected, checking configurations")
            # Check if configuration is complete
            is_configured = self.local_db.get_value("configuration_complete", "false") == "true"
            
            if is_configured:
                self.logger.info("Configuration complete, showing main page")
                self.current_window = MainPage(self)
            else:
                self.logger.info("Configuration incomplete, showing configure page")
                # Create necessary dependencies for ConfigurePage
                from utils.vm_manager import VMManager
                from utils.tesseract_checker import TesseractChecker
                
                # Initialize dependencies
                vm_manager = VMManager()
                tesseract_checker = TesseractChecker()
                
                self.current_window = ConfigurePage(
                    self,  # app_controller
                    self.admin_db,
                    self.client_db,
                    vm_manager,
                    tesseract_checker,
                    self.logger
                )
        

        self.current_window.show()
    
    def switch_to_configure_page(self):
        self.logger.info("Switching to configure page")
        
        # Create necessary dependencies for ConfigurePage
        from utils.vm_manager import VMManager
        from utils.tesseract_checker import TesseractChecker
        
        # Initialize dependencies
        vm_manager = VMManager()
        tesseract_checker = TesseractChecker()
        
        # Close current window and create new one
        self.current_window.close()
        self.current_window = ConfigurePage(
            self,  # app_controller
            self.admin_db,
            self.client_db,
            vm_manager,
            tesseract_checker,
            self.logger
        )
        self.current_window.show()
    
    def switch_to_main_page(self):
        self.logger.info("Switching to main page")
        self.current_window.close()
        self.current_window = MainPage(self)
        self.current_window.show()

    
    def cleanup(self):
        """Clean up resources before application exit"""
        self.logger.info("Cleaning up resources")
        
        # Stop Redis manager
        if hasattr(self, 'redis_manager'):
            self.redis_manager.cleanup()
        
        # Stop all active threads
        for thread in self.active_threads:
            if thread.isRunning():
                thread.stop()
        
        # Close database connections
        if hasattr(self, 'admin_db'):
            self.admin_db.disconnect()
        
        if hasattr(self, 'client_db'):
            self.client_db.disconnect()
        
    


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for a modern look
    
    # Set application font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Set application icon
    
    app.setWindowIcon(QIcon(get_icon_path("logo.ico")))
    
    # Enable High DPI scaling
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    loom_live = LoomLive()
    
    # Clean up resources when the application is about to quit
    app.aboutToQuit.connect(loom_live.cleanup)
    
    sys.exit(app.exec_())

    
from app_controller import AppController

if __name__ == "__main__":
    app_controller = AppController()