import sys
import logging
from PyQt5.QtWidgets import QApplication, QStackedWidget
from database.local_db import LocalDatabase
from database.admin_db import AdminDatabase
from database.client_db import ClientDatabase
from ui.welcome_page import WelcomePage
from ui.configure_page import ConfigurePage
from ui.main_page import MainPage

class AppController:
    def __init__(self):
        # Set up logging
        self.setup_logging()
        
        # Initialize local database
        self.local_db = LocalDatabase()
        
        # Initialize admin and client databases (will be configured later)
        self.admin_db = AdminDatabase()
        self.client_db = ClientDatabase()
        
        # Create application
        self.app = QApplication(sys.argv)
        
        # Create main window
        self.main_window = QStackedWidget()
        self.main_window.setWindowTitle("Loom Live")
        self.main_window.setMinimumSize(1000, 700)  # Increased width, adjusted height
        
        # Determine which page to show
        self.determine_initial_page()
        
        # Show main window
        self.main_window.show()
        
        # Run application
        sys.exit(self.app.exec_())
    
    def setup_logging(self):
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("loom_live.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("LoomLive")
    
    def determine_initial_page(self):
        # Check if this is the first time launch
        first_time_launch = self.local_db.get_value("first_time_launch")
        
        if first_time_launch is None or first_time_launch == "true":
            # First time launch, show welcome page
            self.switch_to_welcome_page()
        else:
            # Check if configuration is complete
            configuration_complete = self.local_db.get_value("configuration_complete")
            
            if configuration_complete is None or configuration_complete == "false":
                # Configuration not complete, show configure page
                self.switch_to_configure_page()
            else:
                # Configuration complete, show main page
                self.switch_to_main_page()
    
    def switch_to_welcome_page(self):
        # Create welcome page
        welcome_page = WelcomePage(self)
        
        # Clear and add to stack
        self.main_window.setCurrentIndex(0)
        self.main_window.removeWidget(self.main_window.currentWidget())
        self.main_window.addWidget(welcome_page)
    
    def switch_to_configure_page(self):
        # Create configure page
        configure_page = ConfigurePage(self)
        
        # Clear and add to stack
        if self.main_window.count() > 0:
            self.main_window.removeWidget(self.main_window.currentWidget())
        self.main_window.addWidget(configure_page)
        self.main_window.setCurrentIndex(0)
    
    def switch_to_main_page(self):
        # Get database credentials from local database
        admin_config = self.local_db.get_admin_config()
        client_config = self.local_db.get_client_config()

        self.local_db.set_value("vm_running", "0")  
        self.local_db.set_core_value("client_service_status", "Stopped") 
        self.local_db.set_core_value("admin_service_status", "Stopped")
        # Configure admin database
        self.admin_db.set_credentials(admin_config.get("admin_url", ""), admin_config.get("admin_key", ""))
        self.admin_db.sync_company_data_to_local()
        
        # Configure client database
        self.client_db.set_credentials(client_config.get("client_url", ""), client_config.get("client_key", ""))
        
        # Create main page
        main_page = MainPage(self)
        
        # Clear and add to stack
        if self.main_window.count() > 0:
            self.main_window.removeWidget(self.main_window.currentWidget())
        self.main_window.addWidget(main_page)
        self.main_window.setCurrentIndex(0)