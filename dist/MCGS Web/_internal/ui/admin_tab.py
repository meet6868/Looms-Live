from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, 
    QPushButton, QGroupBox, QProgressBar, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

from ui.worker_threads import AdminConnectionTestThread

class AdminTabWidget(QWidget):
    def __init__(self, parent, admin_db, logger):
        super().__init__()
        self.parent = parent
        self.admin_db = admin_db
        self.logger = logger
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)  # Increase spacing between main elements
        
        # Info label
        info_label = QLabel("Please enter the admin database URL and API key. This database will be used to store and retrieve company information.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("background-color: #E6F3FF; padding: 10px; border-radius: 4px;")
        layout.addWidget(info_label)
        
        # Form layout for inputs
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(10)
        form_layout.setHorizontalSpacing(15)
        form_layout.setContentsMargins(0, 10, 0, 10)
        
        # Admin URL
        self.admin_url_label = QLabel("Admin Database URL:")
        self.admin_url_input = QLineEdit()
        self.admin_url_input.setPlaceholderText("https://your-project.supabase.co")
        form_layout.addRow(self.admin_url_label, self.admin_url_input)
        
        # Admin API Key
        self.admin_key_label = QLabel("Admin API Key:")
        self.admin_key_input = QLineEdit()
        self.admin_key_input.setPlaceholderText("your-api-key")
        self.admin_key_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow(self.admin_key_label, self.admin_key_input)
        
        # Add form to layout
        layout.addLayout(form_layout)
        
        # Connection status group
        status_group = QGroupBox("Connection Status")
        status_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        status_layout = QVBoxLayout()
        status_layout.setContentsMargins(10, 15, 10, 10)
        
        self.connection_status = QLabel("Not connected")
        self.connection_status.setStyleSheet("padding: 5px;")
        status_layout.addWidget(self.connection_status)
        
        # Progress bar for connection test
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Testing connection...")
        self.progress_bar.hide()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
                margin: 0.5px;
            }
        """)
        status_layout.addWidget(self.progress_bar)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Test connection button in its own container
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 10, 0, 0)
        
        self.test_button = QPushButton("Test Connection")
        self.test_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.test_button.clicked.connect(self.on_test_connection)
        button_layout.addWidget(self.test_button)
        button_layout.addStretch()  # Push button to the left
        
        layout.addWidget(button_container)
        
        # Add spacer at the bottom to push everything up
        layout.addStretch(1)
        
        self.setLayout(layout)
        
        # Load saved values if available
        self.load_saved_values()

    def on_test_connection(self):
        url = self.admin_url_input.text().strip()
        api_key = self.admin_key_input.text().strip()
        
        if not url or not api_key:
            self.connection_status.setText("Please enter URL and API key")
            self.connection_status.setStyleSheet("color: red; padding: 5px;")
            return
        
        # Show progress bar
        self.progress_bar.show()
        self.test_button.setEnabled(False)
        
        # Create a worker thread to test connection
        self.test_thread = AdminConnectionTestThread(url, api_key)
        self.test_thread.connection_result.connect(self.on_connection_result)
        self.test_thread.start()

    def on_connection_result(self, success, message):
        self.progress_bar.hide()
        self.test_button.setEnabled(True)
        
        if success:
            self.connection_status.setText("Connection successful")
            self.connection_status.setStyleSheet("color: green; padding: 5px;")
            
            # Save credentials to admin_db
            self.admin_db.set_credentials(self.admin_url_input.text().strip(), 
                                         self.admin_key_input.text().strip())
            
            # Update connection status in the database
            self.admin_db.connected = True
            
            # Update parent's admin_db
            self.parent.admin_db = self.admin_db
            
            # Store connection status in local database
            try:
                from database.local_db import LocalDatabase
                local_db = LocalDatabase()
                local_db.set_value("admin_db_connected", "true")
            except Exception as e:
                self.logger.error(f"Error storing connection status: {e}")
        else:
            self.connection_status.setText(f"Connection failed: {message}")
            self.connection_status.setStyleSheet("color: red; padding: 5px;")
            
            # Update connection status in the database
            self.admin_db.connected = False
            
            # Store connection status in local database
            try:
                from database.local_db import LocalDatabase
                local_db = LocalDatabase()
                local_db.set_value("admin_db_connected", "false")
            except Exception as e:
                self.logger.error(f"Error storing connection status: {e}")
        
        # Stop the thread properly
        if hasattr(self, 'test_thread') and self.test_thread.isRunning():
            self.test_thread.stop()
            
    def load_saved_values(self):
        """Load saved admin database credentials if available"""
        try:
            # Try to get saved credentials from the admin_db object
            if hasattr(self.admin_db, 'url') and self.admin_db.url:
                self.admin_url_input.setText(self.admin_db.url)
            
            if hasattr(self.admin_db, 'api_key') and self.admin_db.api_key:
                self.admin_key_input.setText(self.admin_db.api_key)
                
            # Check if there's an active connection
            if hasattr(self.admin_db, 'connected') and self.admin_db.connected:
                self.connection_status.setText("Connected successfully")
                self.connection_status.setStyleSheet("color: green; padding: 5px;")
            
        except Exception as e:
            self.logger.error(f"Error loading saved admin database values: {str(e)}")