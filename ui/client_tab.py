from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, 
    QPushButton, QGroupBox, QProgressBar, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

from ui.worker_threads import (
    ClientConnectionTestThread, CompanyNameCheckThread, 
    CompanyEmailCheckThread, URLKeyCheckThread
)

class ClientTabWidget(QWidget):
    def __init__(self, parent, admin_db, client_db):
        super().__init__()
        self.parent = parent
        self.admin_db = admin_db
        self.client_db = client_db
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Instructions with icon
        instructions_widget = QWidget()
        instructions_widget.setStyleSheet("""
            background-color: #e8f0ff;
            border-radius: 8px;
            padding: 15px;
        """)
        instructions_layout = QHBoxLayout(instructions_widget)
        instructions_layout.setContentsMargins(10, 10, 10, 10)
        
        info_icon = QLabel("🏢")
        info_icon.setFont(QFont("Segoe UI", 16))
        info_icon.setFixedWidth(30)
        instructions_layout.addWidget(info_icon)
        
        instructions = QLabel(
            "Please enter the company name and client database credentials. "
            "The company name will be checked against the admin database."
        )
        instructions.setWordWrap(True)
        instructions.setFont(QFont("Segoe UI", 10))
        instructions_layout.addWidget(instructions)
        
        layout.addWidget(instructions_widget)
        
        # Form layout
        form_widget = QWidget()
        form_widget.setStyleSheet("""
            background-color: white;
            border-radius: 8px;
            padding: 20px;
        """)
        form_layout = QFormLayout(form_widget)
        form_layout.setVerticalSpacing(15)
        form_layout.setHorizontalSpacing(30)
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form_layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Company name with status beside it
        company_name_container = QWidget()
        company_name_layout = QHBoxLayout(company_name_container)
        company_name_layout.setContentsMargins(0, 0, 0, 0)
        company_name_layout.setSpacing(10)
        
        self.company_name_input = QLineEdit()
        self.company_name_input.setMinimumWidth(300)
        self.company_name_input.setPlaceholderText("Your Company Name")
        self.company_name_input.textChanged.connect(self.on_company_name_changed)
        company_name_layout.addWidget(self.company_name_input)
        
        self.company_name_status = QLabel("")
        self.company_name_status.setMinimumWidth(100)
        company_name_layout.addWidget(self.company_name_status)
        
        form_layout.addRow("<b>Company Name:</b>", company_name_container)
        
        # Client email
        self.client_email_input = QLineEdit()
        self.client_email_input.setMinimumWidth(400)
        self.client_email_input.setPlaceholderText("client@example.com")
        self.client_email_input.setEnabled(False)
        form_layout.addRow("<b>Client Email:</b>", self.client_email_input)
        
        # Client URL
        self.client_url_input = QLineEdit()
        self.client_url_input.setMinimumWidth(400)
        self.client_url_input.setPlaceholderText("https://your-client-project.supabase.co")
        self.client_url_input.setEnabled(False)
        self.client_url_input.textChanged.connect(self.on_client_credentials_changed)
        form_layout.addRow("<b>Client Database URL:</b>", self.client_url_input)
        
        # Client API Key
        self.client_key_input = QLineEdit()
        self.client_key_input.setMinimumWidth(400)
        self.client_key_input.setPlaceholderText("your-client-supabase-api-key")
        self.client_key_input.setEchoMode(QLineEdit.Password)
        self.client_key_input.setEnabled(False)
        self.client_key_input.textChanged.connect(self.on_client_credentials_changed)
        form_layout.addRow("<b>Client API Key:</b>", self.client_key_input)
        
        # Add URL + Key status label
        self.url_key_status = QLabel("")
        self.url_key_status.setMinimumWidth(100)
        form_layout.addRow("", self.url_key_status)
        
        layout.addWidget(form_widget)
        
        # Connection status
        status_group = QGroupBox("Connection Status")
        status_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #b8c6db;
                border-radius: 8px;
                margin-top: 12px;
                font-weight: bold;
                background-color: #e8f0ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #2c5ecc;
            }
        """)
        status_layout = QVBoxLayout()
        
        self.client_status_label = QLabel("Not connected")
        self.client_status_label.setFont(QFont("Segoe UI", 10))
        self.client_status_label.setStyleSheet("color: #e74c3c;")
        status_layout.addWidget(self.client_status_label)
        
        self.client_progress_bar = QProgressBar()
        self.client_progress_bar.setRange(0, 0)  # Indeterminate progress
        self.client_progress_bar.setVisible(False)
        status_layout.addWidget(self.client_progress_bar)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Test connection button
        test_button_container = QWidget()
        test_button_layout = QHBoxLayout(test_button_container)
        test_button_layout.setContentsMargins(0, 10, 0, 0)
        
        test_button = QPushButton("Test Connection")
        test_button.setIcon(QIcon("icons/connect.png"))  # Add an icon if available
        test_button.setStyleSheet("""
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
        test_button.clicked.connect(self.test_client_connection)
        test_button_layout.addWidget(test_button)
        test_button_layout.addStretch()  # Push button to the left
        
        layout.addWidget(test_button_container)
        
        # Add spacer at the bottom to push everything up
        layout.addStretch(1)
        
        self.setLayout(layout)
    
    def on_client_credentials_changed(self):
        """Handle changes to client credentials"""
        # Reset connection status when credentials change
        self.client_status_label.setText("Not connected")
        self.client_status_label.setStyleSheet("color: #e74c3c;")
        self.client_db.connected = False
        
        # Check URL + key combination
        client_url = self.client_url_input.text().strip()
        client_key = self.client_key_input.text().strip()
        
        if client_url and client_key:
            self.check_url_key_combination()
    
    def check_url_key_combination(self):
        """Check if URL + key combination exists"""
        client_url = self.client_url_input.text().strip()
        client_key = self.client_key_input.text().strip()
        
        if not client_url or not client_key:
            self.url_key_status.setText("")
            return
        
        self.url_key_status.setText("Checking URL and key combination...")
        
        # Create a worker thread to check URL + key
        from ui.worker_threads import URLKeyCheckThread
        self.url_key_check_thread = URLKeyCheckThread(
            self.admin_db, client_url, client_key
        )
        self.url_key_check_thread.check_result.connect(self.on_url_key_checked)
        self.url_key_check_thread.start()
    
    def on_url_key_checked(self, exists, message):
        """Handle URL + key check result"""
        if exists:
            self.url_key_status.setText("URL and key combination already exists in database")
            self.url_key_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
        else:
            self.url_key_status.setText("URL and key combination available")
            self.url_key_status.setStyleSheet("color: #2ecc71; font-weight: bold;")
        
        # Check availability of client credentials if company name is available
        company_name = self.company_name_input.text().strip()
        client_url = self.client_url_input.text().strip()
        client_key = self.client_key_input.text().strip()
        
        if company_name and (client_url or client_key):
            # Create a worker thread to check client credentials
            self.company_check_thread = CompanyNameCheckThread(
                self.admin_db, 
                company_name,
                client_url,
                client_key
            )
            self.company_check_thread.check_result.connect(self.on_company_name_changed)
            self.company_check_thread.start()
    
    def on_company_name_changed(self):
        """Handle changes to company name"""
        company_name = self.company_name_input.text().strip()
        
        if not company_name:
            self.company_name_status.setText("")
            self.client_email_input.setEnabled(False)
            self.client_url_input.setEnabled(False)
            self.client_key_input.setEnabled(False)
            return
        
        # Enable email input without checking company name alone
        self.company_name_status.setText("Enter client email")
        self.company_name_status.setStyleSheet("color: #2c5ecc; font-weight: bold;")
        self.client_email_input.setEnabled(True)
        
        # Connect the email change handler - PyQt5 doesn't have isConnected()
        # Instead, we'll use a try/except block to safely connect the signal
        try:
            # Disconnect first to avoid multiple connections
            self.client_email_input.textChanged.disconnect(self.on_client_email_changed)
        except:
            # If it wasn't connected, that's fine
            pass
        
        # Now connect it
        self.client_email_input.textChanged.connect(self.on_client_email_changed)
        
        # If email is already entered, check the combination
        client_email = self.client_email_input.text().strip()
        if client_email:
            self.check_company_email_combination(company_name, client_email)
    
    def on_client_email_changed(self):
        """Handle changes to client email"""
        company_name = self.company_name_input.text().strip()
        client_email = self.client_email_input.text().strip()
        
        if not client_email:
            if hasattr(self, 'company_email_status'):
                self.company_email_status.setText("")
            return
        
        # Check company name + email combination
        self.check_company_email_combination(company_name, client_email)
    
    def check_company_email_combination(self, company_name, client_email):
        """Check if company name + email combination exists"""
        # Add the company_email_status label if it doesn't exist
        if not hasattr(self, 'company_email_status'):
            self.company_email_status = QLabel("")
            self.company_email_status.setStyleSheet("color: #e74c3c;")
            # Find the form layout
            for child in self.findChildren(QWidget):
                if hasattr(child, 'layout') and isinstance(child.layout(), QFormLayout):
                    child.layout().addRow("", self.company_email_status)
                    break
        
        self.company_email_status.setText("Checking company and email combination...")
        
        # Create a worker thread to check company name + email
        from ui.worker_threads import CompanyEmailCheckThread
        self.company_email_check_thread = CompanyEmailCheckThread(
            self.admin_db, company_name, client_email
        )
        self.company_email_check_thread.check_result.connect(self.on_company_email_checked)
        self.company_email_check_thread.start()
    
    def on_company_email_checked(self, exists, message):
        """Handle company name + email check result"""
        if exists:
            self.company_email_status.setText(f"Company and email combination already exists: {message}")
            self.company_email_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.client_url_input.setEnabled(False)
            self.client_key_input.setEnabled(False)
        else:
            self.company_email_status.setText("Company and email combination available")
            self.company_email_status.setStyleSheet("color: #2ecc71; font-weight: bold;")
            self.client_url_input.setEnabled(True)
            self.client_key_input.setEnabled(True)
    
    def on_client_url_changed(self):
        """Handle changes to client URL"""
        self.check_url_key_combination()
    
    def on_client_key_changed(self):
        """Handle changes to client API key"""
        self.check_url_key_combination()
    
    def check_url_key_combination(self):
        """Check if URL + key combination exists"""
        client_url = self.client_url_input.text().strip()
        client_key = self.client_key_input.text().strip()
        
        if not client_url or not client_key:
            self.url_key_status.setText("")
            return
        
        self.url_key_status.setText("Checking URL and key combination...")
        
        # Create a worker thread to check URL + key
        self.url_key_check_thread = URLKeyCheckThread(
            self.admin_db, client_url, client_key
        )
        self.url_key_check_thread.check_result.connect(self.on_url_key_checked)
        self.url_key_check_thread.start()
    
    def on_url_key_checked(self, exists, message):
        """Handle URL + key check result"""
        if exists:
            self.url_key_status.setText(f"URL and key combination already exists: {message}")
            self.url_key_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
            # Notify parent that validation failed
            if hasattr(self.parent, 'update_next_button'):
                self.parent.update_next_button(False)
        else:
            self.url_key_status.setText("URL and key combination available")
            self.url_key_status.setStyleSheet("color: #2ecc71; font-weight: bold;")
            # Notify parent that validation succeeded
            if hasattr(self.parent, 'update_next_button'):
                self.parent.update_next_button(True)
    
    def test_client_connection(self):
        client_url = self.client_url_input.text().strip()
        client_key = self.client_key_input.text().strip()
        
        if not client_url or not client_key:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Missing Information", 
                               "Please enter both the client database URL and API key.")
            return
        
        # Show progress
        self.client_status_label.setText("Testing connection...")
        self.client_progress_bar.setVisible(True)
        
        # Create a worker thread to test connection
        self.client_test_thread = ClientConnectionTestThread(client_url, client_key)
        self.client_test_thread.connection_result.connect(self.on_client_connection_tested)
        self.client_test_thread.start()
    
    def on_client_connection_tested(self, success, message):
        self.client_progress_bar.setVisible(False)
        
        if success:
            self.client_status_label.setText("Connected successfully")
            self.client_status_label.setStyleSheet("color: green;")
            
            # Format company name (replace spaces with underscores) for storage
            formatted_company_name = self.company_name_input.text().strip().replace(" ", "_")
            
            # Store client credentials in parent
            self.parent.config_data["company_name"] = formatted_company_name
            self.parent.config_data["client_email"] = self.client_email_input.text().strip()
            self.parent.config_data["client_url"] = self.client_url_input.text().strip()
            self.parent.config_data["client_key"] = self.client_key_input.text().strip()
            
            # Get IP address from URL
            import re
            import socket
            url = self.client_url_input.text().strip()
            ip = ""
            try:
                # Extract hostname from URL
                hostname = re.search(r'https?://([^/:]+)', url)
                if hostname:
                    hostname = hostname.group(1)
                    # Get IP address from hostname
                    ip = socket.gethostbyname(hostname)
            except:
                # If we can't get the IP, use an empty string
                ip = ""
            
            # Store IP address with the correct field name
            self.parent.config_data["ip"] = ip
            
            # Set up client database connection and explicitly set connected status
            self.client_db.set_credentials(self.parent.config_data["client_url"], 
                                          self.parent.config_data["client_key"])
            self.client_db.connected = True
        else:
            from PyQt5.QtWidgets import QMessageBox
            self.client_status_label.setText(f"Connection failed: {message}")
            self.client_status_label.setStyleSheet("color: red;")
            self.client_db.connected = False
            
            QMessageBox.warning(self, "Connection Error", 
                               f"Failed to connect to client database: {message}")

    def on_test_connection(self):
            """Test connection to client database"""
            url = self.client_url_input.text().strip()
            key = self.client_key_input.text().strip()
            
            if not url or not key:
                self.client_status_label.setText("Please enter URL and API key")
                self.client_status_label.setStyleSheet("color: #e74c3c;")
                return
            
            # Show progress bar
            self.client_progress_bar.setVisible(True)
            
            # Create thread to test connection
            self.client_test_thread = ClientConnectionTestThread(url, key)
            self.client_test_thread.connection_result.connect(self.on_client_connection_result)
            self.client_test_thread.start()
        
    def on_client_connection_result(self, success, message):
        self.client_progress_bar.setVisible(False)
        
        if success:
            self.client_status_label.setText("Connection successful")
            self.client_status_label.setStyleSheet("color: #2ecc71;")
            
            # Save credentials to client_db
            self.client_db.set_credentials(self.client_url_input.text().strip(), 
                                          self.client_key_input.text().strip())
            self.client_db.create_client_setting_table()
            # Update parent's client_db
            self.parent.client_db = self.client_db
        else:
            self.client_status_label.setText(f"Connection failed: {message}")
            self.client_status_label.setStyleSheet("color: #e74c3c;")
        
        # Stop the thread properly
        if hasattr(self, 'client_test_thread') and self.client_test_thread.isRunning():
            self.client_test_thread.stop()
        self.client_progress_bar.setVisible(False)
        
        if success:
            self.client_status_label.setText("Connected successfully")
            self.client_status_label.setStyleSheet("color: #2ecc71;")
            
            # Set client database credentials
            self.client_db.set_credentials(
                self.client_url_input.text().strip(),
                self.client_key_input.text().strip()
            )
            self.client_db.connected = True
            
            # Format company name (replace spaces with underscores) for storage
            formatted_company_name = self.company_name_input.text().strip().replace(" ", "_")
            
            # Store in parent's config_data
            self.parent.config_data["client_url"] = self.client_url_input.text().strip()
            self.parent.config_data["client_key"] = self.client_key_input.text().strip()
            self.parent.config_data["client_email"] = self.client_email_input.text().strip()
            self.parent.config_data["company_name"] = formatted_company_name
            
            # Get IP address from URL
            import re
            import socket
            url = self.client_url_input.text().strip()
            ip = ""
            try:
                # Extract hostname from URL
                hostname = re.search(r'https?://([^/:]+)', url)
                if hostname:
                    hostname = hostname.group(1)
                    # Get IP address from hostname
                    ip = socket.gethostbyname(hostname)
            except:
                # If we can't get the IP, use an empty string
                ip = ""
            
            # Store IP address
            self.parent.config_data["ip"] = ip
        else:
            self.client_status_label.setText(f"Connection failed: {message}")
            self.client_status_label.setStyleSheet("color: #e74c3c;")
            self.client_db.connected = False
            
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Connection Error", 
                                f"Failed to connect to client database: {message}")