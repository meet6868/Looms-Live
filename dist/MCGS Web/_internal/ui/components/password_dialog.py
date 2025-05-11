from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import requests

class PasswordDialog(QDialog):
    """Reusable dialog for password verification"""
    def __init__(self, parent, admin_db, title="Authentication Required", message="Enter admin password:"):
        super().__init__(parent)
        self.parent = parent
        self.admin_db = admin_db
        self.logger = parent.logger
        
        self.setWindowTitle(title)
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
        
        # Dialog layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Password field
        password_label = QLabel(message)
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
       # Default password
            
            # Verify password
            if password == update_password.strip():
                self.accept()
            else:
                QMessageBox.warning(self, "Authentication Failed", "Incorrect password. Please try again.")
        except Exception as e:
            self.logger.error(f"Error verifying password: {e}")
            QMessageBox.warning(self, "Error", f"Could not verify password: {e}")
    
    @staticmethod
    def get_password(parent, admin_db, title="Authentication Required", message="Enter admin password:"):
        """Static method to create and show a password dialog"""
        dialog = PasswordDialog(parent, admin_db, title, message)
        result = dialog.exec_()
        return result == QDialog.Accepted