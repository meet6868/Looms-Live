from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QProgressBar, QMessageBox, QLineEdit, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import requests
import json
import os
from datetime import datetime

class UpdateCheckThread(QThread):
    """Thread for checking for updates in the background"""
    update_found = pyqtSignal(dict)
    no_update = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, admin_db, current_version):
        super().__init__()
        self.admin_db = admin_db
        self.current_version = current_version
    
    def run(self):
        try:
            # Query admin database for latest version
            response = requests.get(
                f"{self.admin_db.url}/rest/v1/updates",
                headers={
                    "apikey": self.admin_db.api_key,
                    "Authorization": f"Bearer {self.admin_db.api_key}"
                },
                params={
                    "select": "*",
                    "order": "version.desc",
                    "limit": 1
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    latest_version = data[0].get("version")
                    
                    # Compare versions (simple string comparison for now)
                    if latest_version > self.current_version:
                        self.update_found.emit(data[0])
                    else:
                        self.no_update.emit()
                else:
                    self.no_update.emit()
            else:
                self.error.emit(f"Error checking for updates: {response.status_code}")
        except Exception as e:
            self.error.emit(f"Error checking for updates: {e}")

class UpdateDialog(QDialog):
    """Dialog for checking for updates and updating the application"""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.admin_db = parent.admin_db
        self.client_db = parent.client_db
        self.local_db = parent.local_db
        self.logger = parent.logger
        
        # Get current version
        self.current_version = self.local_db.get_value("version", "1.0.0")
        
        self.setWindowTitle("Check for Updates")
        self.setMinimumSize(500, 300)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #2c3e50;
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
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        
        self.init_ui()
        self.check_for_updates()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Check for Updates")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        layout.addWidget(title)
        
        # Current version
        current_version_layout = QHBoxLayout()
        current_version_label = QLabel("Current Version:")
        current_version_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        current_version_layout.addWidget(current_version_label)
        
        current_version_value = QLabel(self.current_version)
        current_version_layout.addWidget(current_version_value)
        current_version_layout.addStretch()
        
        layout.addLayout(current_version_layout)
        
        # Status frame
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(15, 15, 15, 15)
        
        self.status_label = QLabel("Checking for updates...")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 5px;
            }
        """)
        status_layout.addWidget(self.progress_bar)
        
        # Update details (hidden initially)
        self.update_details = QFrame()
        self.update_details.setVisible(False)
        update_details_layout = QVBoxLayout(self.update_details)
        
        latest_version_layout = QHBoxLayout()
        latest_version_label = QLabel("Latest Version:")
        latest_version_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        latest_version_layout.addWidget(latest_version_label)
        
        self.latest_version_value = QLabel("")
        latest_version_layout.addWidget(self.latest_version_value)
        latest_version_layout.addStretch()
        
        update_details_layout.addLayout(latest_version_layout)
        
        release_date_layout = QHBoxLayout()
        release_date_label = QLabel("Release Date:")
        release_date_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        release_date_layout.addWidget(release_date_label)
        
        self.release_date_value = QLabel("")
        release_date_layout.addWidget(self.release_date_value)
        release_date_layout.addStretch()
        
        update_details_layout.addLayout(release_date_layout)
        
        changes_label = QLabel("Changes:")
        changes_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        update_details_layout.addWidget(changes_label)
        
        self.changes_text = QLabel("")
        self.changes_text.setWordWrap(True)
        self.changes_text.setStyleSheet("background-color: #f9f9f9; padding: 10px; border-radius: 5px;")
        update_details_layout.addWidget(self.changes_text)
        
        status_layout.addWidget(self.update_details)
        
        layout.addWidget(status_frame)
        
        # Password input for update (hidden initially)
        self.password_frame = QFrame()
        self.password_frame.setVisible(False)
        password_layout = QVBoxLayout(self.password_frame)
        
        password_label = QLabel("Enter admin password to update:")
        password_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Password")
        password_layout.addWidget(self.password_input)
        
        layout.addWidget(self.password_frame)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.update_btn = QPushButton("Update")
        self.update_btn.setIcon(QIcon("icons/update.png"))
        self.update_btn.setEnabled(False)
        self.update_btn.clicked.connect(self.start_update)
        button_layout.addWidget(self.update_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def check_for_updates(self):
        """Check for updates in a background thread"""
        self.update_thread = UpdateCheckThread(self.admin_db, self.current_version)
        self.update_thread.update_found.connect(self.on_update_found)
        self.update_thread.no_update.connect(self.on_no_update)
        self.update_thread.error.connect(self.on_update_error)
        self.update_thread.start()
    
    def on_update_found(self, update_data):
        """Handle when an update is found"""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.status_label.setText("Update Available!")
        self.status_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
        
        # Show update details
        self.update_details.setVisible(True)
        self.latest_version_value.setText(update_data.get("version", "Unknown"))
        
        # Format release date
        release_date = update_data.get("release_date")
        if release_date:
            try:
                date_obj = datetime.strptime(release_date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%B %d, %Y")
                self.release_date_value.setText(formatted_date)
            except:
                self.release_date_value.setText(release_date)
        else:
            self.release_date_value.setText("Unknown")
        
        # Set changes text
        changes = update_data.get("changes", "No change information available.")
        self.changes_text.setText(changes)
        
        # Enable update button and show password input
        self.update_btn.setEnabled(True)
        self.password_frame.setVisible(True)
        
        # Store update data for later
        self.update_data = update_data
    
    def on_no_update(self):
        """Handle when no update is found"""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.status_label.setText("You are using the latest version.")
        self.status_label.setStyleSheet("color: #2c3e50;")
    
    def on_update_error(self, error_message):
        """Handle update check errors"""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Error checking for updates")
        self.status_label.setStyleSheet("color: #e74c3c;")
        self.logger.error(error_message)
    
    def start_update(self):
        """Start the update process after password verification"""
        password = self.password_input.text()
        if not password:
            QMessageBox.warning(self, "Password Required", "Please enter the admin password to continue.")
            return
        
        try:
            # Verify password from admin database
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
                # Password correct, start update
                self.perform_update()
            else:
                QMessageBox.warning(self, "Authentication Failed", "Incorrect password. Please try again.")
        except Exception as e:
            self.logger.error(f"Error verifying update password: {e}")
            QMessageBox.warning(self, "Error", f"Could not verify password: {e}")
    
    def perform_update(self):
        """Perform the actual update process"""
        try:
            # This is a placeholder for the actual update process
            # In a real implementation, you would download and install the update
            
            # Show update in progress
            self.status_label.setText("Updating... Please wait.")
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.update_btn.setEnabled(False)
            self.close_btn.setEnabled(False)
            self.password_frame.setVisible(False)
            
            # Simulate update process (in a real app, this would be a separate thread)
            QMessageBox.information(
                self,
                "Update Simulation",
                "In a real application, this would download and install the update.\n\n"
                "For this demo, we'll just update the version number in the local database."
            )
            
            # Update version in local database
            new_version = self.update_data.get("version")
            if new_version:
                self.local_db.set_value("version", new_version)
                self.logger.info(f"Updated version to {new_version}")
            
            # Update complete
            self.status_label.setText("Update completed successfully!")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            self.close_btn.setEnabled(True)
            
            # Prompt for restart
            restart = QMessageBox.question(
                self,
                "Update Complete",
                "The update has been installed successfully. The application needs to restart to apply the changes. Restart now?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if restart == QMessageBox.Yes:
                # Restart application
                self.parent.logout()
            
        except Exception as e:
            self.logger.error(f"Error performing update: {e}")
            self.status_label.setText("Update failed!")
            self.status_label.setStyleSheet("color: #e74c3c;")
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.close_btn.setEnabled(True)
            
            QMessageBox.critical(self, "Update Failed", f"Could not complete the update: {e}")