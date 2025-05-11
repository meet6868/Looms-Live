from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import requests

class PasswordDialog(QDialog):
    """Dialog for password verification before configuration updates"""
    def __init__(self, parent, admin_db, callback):
        super().__init__(parent)
        self.admin_db = admin_db
        self.callback = callback
        self.logger = parent.logger
        
        self.setWindowTitle("Authentication Required")
        self.setFixedWidth(400)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: #2c3e50;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        # Dialog layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Password field
        password_label = QLabel("Enter admin password:")
        layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Password")
        layout.addWidget(self.password_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.verify_password)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
    
    def verify_password(self):
        """Verify the entered password against the admin database"""
        try:
            password = self.password_input.text()
            
            # Get update password from admin database
            update_password = None
            try:
                # Query settings table for update_password
                response = requests.get(
                    f"{self.admin_db.url}/rest/v1/settings",
                    headers={
                        "apikey": self.admin_db.api_key,
                        "Authorization": f"Bearer {self.admin_db.api_key}"
                    },
                    params={
                        "select": "value",
                        "key": "eq.update_password"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        update_password = data[0].get("value")
            except Exception as e:
                self.logger.error(f"Error getting update password: {e}")
            
            # If no password found, use default
            if not update_password:
                update_password = "admin123"  # Default password
            
            # Verify password
            if password == update_password:
                self.accept()
                if self.callback:
                    self.callback()
            else:
                QMessageBox.warning(self, "Authentication Failed", "Incorrect password. Please try again.")
        except Exception as e:
            self.logger.error(f"Error verifying password: {e}")
            QMessageBox.warning(self, "Error", f"Could not verify password: {e}")


class SettingsManager:
    """Manager for settings-related functionality"""
    def __init__(self, main_page):
        self.main_page = main_page
        self.app_controller = main_page.app_controller
        self.admin_db = main_page.admin_db
        self.client_db = main_page.client_db
        self.local_db = main_page.local_db
        self.logger = main_page.logger
    
    def show_update_password_dialog(self):
        """Show password dialog for update configuration"""
        try:
            dialog = PasswordDialog(self.main_page, self.admin_db, self.show_configuration_update)
            dialog.exec_()
        except Exception as e:
            self.logger.error(f"Error showing update password dialog: {e}")
            QMessageBox.warning(self.main_page, "Error", f"Could not show password dialog: {e}")
    
    def show_configuration_update(self):
        """Show configuration update dialog"""
        try:
            # Create configuration dialog similar to the configure page
            from ui.configure_page import ConfigurePage
            
            # Get existing configuration
            config_data = {
                "admin_url": self.admin_db.url,
                "admin_key": self.admin_db.api_key,
                "company_name": self.local_db.get_value("company_name", ""),
                "vm_path": self.local_db.get_value("vm_path", ""),
                "system_path": self.local_db.get_value("system_path", ""),
                "tesseract_path": self.local_db.get_value("tesseract_path", ""),
                "start_date": self.local_db.get_value("start_date", ""),
                "end_date": self.local_db.get_value("end_date", "")
            }
            
            # Create and show configuration dialog
            config_dialog = QDialog(self.main_page)
            config_dialog.setWindowTitle("Update Configuration")
            config_dialog.setMinimumSize(800, 600)
            
            # Create configure page inside dialog
            config_page = ConfigurePage(self.app_controller, config_data)
            
            # Dialog layout
            layout = QVBoxLayout(config_dialog)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(config_page)
            
            # Show dialog
            config_dialog.exec_()
            
            # Refresh status after configuration update
            self.main_page.check_status()
        except Exception as e:
            self.logger.error(f"Error showing configuration update: {e}")
            QMessageBox.warning(self.main_page, "Error", f"Could not show configuration update: {e}")