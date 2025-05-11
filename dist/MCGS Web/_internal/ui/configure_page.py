import os
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, 
    QPushButton, QSpacerItem, QSizePolicy, QMessageBox, QDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from ui.admin_tab import AdminTabWidget
from ui.client_tab import ClientTabWidget
from ui.system_tab import SystemTabWidget
from ui.final_config_dialog import FinalConfigDialog
from utils.supabase_utils import diagnose_supabase_connection

class ConfigurePage(QWidget):
    def __init__(self, app_controller, admin_db, client_db, vm_manager, tesseract_checker, logger):
        super().__init__()
        self.app_controller = app_controller
        self.admin_db = admin_db
        self.client_db = client_db
        self.vm_manager = vm_manager
        self.tesseract_checker = tesseract_checker
        self.logger = logger
        self.config_data = {}
        self.init_ui()
        
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { 
                border: 1px solid #C0C0C0;
                background-color: #F0F0F0;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #E0E0E0;
                border: 1px solid #C0C0C0;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #F0F0F0;
                border-bottom: 1px solid #F0F0F0;
            }
            QTabBar::tab:hover:!selected {
                background-color: #E8E8E8;
            }
        """)
        
        # Create tabs
        self.admin_tab = AdminTabWidget(self, self.admin_db, self.logger)
        self.client_tab = ClientTabWidget(self, self.admin_db, self.client_db)
        self.system_tab = SystemTabWidget(self, self.vm_manager, self.tesseract_checker)
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.admin_tab, "Admin Database")
        self.tab_widget.addTab(self.client_tab, "Client Database")
        self.tab_widget.addTab(self.system_tab, "System Configuration")
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Add navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(0, 10, 0, 0)  # Add top margin for spacing
        
        # Add spacer to push buttons to the right
        nav_layout.addStretch()
        
        # Next button with improved visibility
        self.next_button = QPushButton("Next")
        self.next_button.setMinimumWidth(120)  # Wider button
        self.next_button.setMinimumHeight(40)  # Taller button
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14pt;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        self.next_button.clicked.connect(self.on_next_clicked)
        nav_layout.addWidget(self.next_button)
        
        # Add navigation layout to main layout
        main_layout.addLayout(nav_layout)
        
        # Set layout
        self.setLayout(main_layout)
        
        # Set window properties
        self.setWindowTitle("Configuration")
        self.resize(800, 600)  # Make window taller to ensure Next button is visible
    
    def on_next_clicked(self):
        """Handle next button click"""
        current_tab = self.tab_widget.currentIndex()
        
        # Admin tab
        if current_tab == 0:
            # Check if admin database is connected
            if not self.admin_db.connected:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Not Connected", 
                                   "Please connect to the admin database first.")
                return
            
            # Move to client tab
            self.tab_widget.setCurrentIndex(1)
            
        # Client tab
        elif current_tab == 1:
            # Check if client database is connected
            if not self.client_db.connected:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Not Connected", 
                                   "Please connect to the client database first.")
                return
            
            # Move to system tab
            self.tab_widget.setCurrentIndex(2)
            
        # System tab
        elif current_tab == 2:
            # Get system paths
            vm_path = self.system_tab.vm_path_input.text().strip()
            system_path = self.system_tab.system_path_input.text().strip()
            tesseract_path = self.system_tab.tesseract_path_input.text().strip()
            
            # Validate paths
            if not vm_path or not system_path or not tesseract_path:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Missing Information", 
                                   "Please enter all required paths.")
                return
            
            # Store paths in config_data
            self.config_data["vm_path"] = vm_path
            self.config_data["system_path"] = system_path
            self.config_data["tesseract_path"] = tesseract_path
            
            # Show final configuration dialog
            self.on_finish_clicked()
    
    def on_finish_clicked(self):
        """Handle finish button click"""
        # Show final configuration dialog
        final_dialog = FinalConfigDialog(self.config_data)
        if final_dialog.exec_() == QDialog.Accepted:
            # Update config with final values
            self.config_data["password"] = final_dialog.password
            self.config_data["start_date"] = final_dialog.start_date
            self.config_data["end_date"] = final_dialog.end_date
            
            
            
            # Log the configuration data
            self.logger.info(f"Configuration data: {self.config_data}")
            
            # Save to admin database
            self.save_configuration()
            
    def save_configuration(self):
        """Save the configuration to the admin database"""
        try:
            # Get company information from config_data
            company_name = self.config_data.get("company_name", "")
            client_email = self.config_data.get("client_email", "")
            client_url = self.config_data.get("client_url", "")
            client_key = self.config_data.get("client_key", "")
            vm_path = self.config_data.get("vm_path", "")
            system_path = self.config_data.get("system_path", "")
            tesseract_path = self.config_data.get("tesseract_path", "")
            password = self.config_data.get("password", "")
            start_date = self.config_data.get("start_date", "")
            end_date = self.config_data.get("end_date", "")
            ip=self.config_data.get("ip", "")[0]
            
            
            # Debug logging to check values
            self.logger.info(f"Saving configuration with: company_name={company_name}, client_email={client_email}, client_url={client_url}, client_key={client_key}")
            self.logger.info(f"System paths: vm_path={vm_path}, system_path={system_path}, tesseract_path={tesseract_path},IP={ip}")
            self.logger.info(f"License: start_date={start_date}, end_date={end_date}")
            
            # Make sure we have all required data
            if not all([company_name, client_email, client_url, client_key, vm_path, system_path, tesseract_path, password, start_date, end_date]):
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Missing Information", 
                                   "Please ensure all required fields are filled in.")
                return False
            
            # Create complete company data
            company_data = {
                "company_name": company_name,
                "client_email": client_email,
                "client_url": client_url,
                "client_key": client_key,
                "vm_path": vm_path,
                "system_path": system_path,
                "ip": ip,
                "tesseract_path": tesseract_path,
                "password": password,
                "start_date": start_date,
                "end_date": end_date
            }
            
            # Check if company already exists
            if self.admin_db.check_company_exists(company_name):
                # Update existing company
                success = self.admin_db.update_company(company_name, company_data)
            else:
                # Add new company
               

                success = self.admin_db.add_company(
                    company_name, 
                    client_email, 
                    client_url, 
                    client_key
                )
                
                # If successful, update with remaining data
                if success:
                    
                    success = self.admin_db.update_company(company_name,company_data,company_name,client_email)
                  
                    
                    client_success=self.app_controller.client_db.set_client_config(company_data)
                    if not client_success:
                        self.logger.error(f"Error saving configuration: {str(e)}")
                        return False

                    
                    # Save configuration to local database
                    self.app_controller.local_db.set_client_config(company_data)
                    self.app_controller.local_db.set_value("company_name",company_name)
                    self.app_controller.local_db.set_value("client_email",client_email)

            
            if not success:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Configuration Error", 
                               "Failed to save configuration to admin database.")
                return False
            
            # Show success message and summary
            self.show_configuration_summary()
            
            # Mark configuration as complete
            self.app_controller.local_db.set_value("configuration_complete", "true")
            
            # Update connection status
            self.app_controller.local_db.update_connection_status(
                admin_connected=1,
                client_connected=1,
                vm_running=1
            )
            
            # Switch to main page
            self.app_controller.switch_to_main_page()
            
            return True
        except Exception as e:
            self.logger.error(f"Error saving configuration: {str(e)}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Configuration Error", 
                           f"Failed to save configuration: {str(e)}")
            return False
            
    def show_configuration_summary(self):
        """Show a summary of the configuration"""
        from PyQt5.QtWidgets import QMessageBox
        
        summary = f"""
        <h3>Configuration Complete</h3>
        <p>The following configuration has been saved:</p>
        <ul>
            <li><b>Company Name:</b> {self.config_data.get('company_name', '')}</li>
            <li><b>Client Email:</b> {self.config_data.get('client_email', '')}</li>
            <li><b>License Period:</b> {self.config_data.get('start_date', '')} to {self.config_data.get('end_date', '')}</li>
        </ul>
        <p>You can now proceed to the main application.</p>
        """
        
        QMessageBox.information(self, "Configuration Complete", summary)
    
    def next_tab(self):
        """Move to the next tab"""
        current_index = self.tab_widget.currentIndex()
        
        # Check if we're on the admin tab and need to validate connection
        if current_index == 0:  # Admin Database tab
            # Check if admin database is connected
            if not self.admin_db.connected:
                QMessageBox.warning(
                    self,
                    "Not Connected",
                    "Please connect to the admin database first."
                )
                return
        
        # Check if we're on the client tab and need to validate connection
        elif current_index == 1:  # Client Database tab
            # Check if client database is connected
            if not self.client_db.connected:
                QMessageBox.warning(
                    self,
                    "Not Connected",
                    "Please connect to the client database first."
                )
                return
        
        # Move to the next tab
        next_index = current_index + 1
        if next_index < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(next_index)
            
            # Update buttons
            self.update_navigation_buttons()