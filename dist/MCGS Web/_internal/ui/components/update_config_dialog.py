from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QMessageBox, QTabWidget, QWidget, QProgressBar, QGroupBox,
    QLineEdit, QDateEdit, QFormLayout, QApplication
)
from PyQt5.QtCore import Qt, QTimer, QDate
from PyQt5.QtGui import QFont
import requests
from datetime import datetime

class AdminTab(QWidget):
    def __init__(self, admin_db, logger):
        super().__init__()
        self.admin_db = admin_db
        self.logger = logger
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Info label
        info_label = QLabel("Please enter the admin database URL and API key.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Form layout for inputs
        form = QFormLayout()
        self.url_input = QLineEdit(self.admin_db.url)
        self.key_input = QLineEdit(self.admin_db.api_key)
        self.key_input.setEchoMode(QLineEdit.Password)
        
        form.addRow("Admin Database URL:", self.url_input)
        form.addRow("Admin API Key:", self.key_input)
        layout.addLayout(form)
        
        # Status label
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        
        # Test button
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self.test_connection)
        layout.addWidget(self.test_btn)
        
        layout.addStretch()
        
    def test_connection(self):
        url = self.url_input.text().strip()
        key = self.key_input.text().strip()
        
        if not url or not key:
            self.status_label.setText("Please enter both URL and API key")
            return False
            
        try:
            self.admin_db.set_credentials(url, key)
            response = self.admin_db.test_connection()
            if response:
                self.status_label.setText("Connected successfully")
                self.status_label.setStyleSheet("color: green")
                return True
            else:
                self.status_label.setText("Connection failed")
                self.status_label.setStyleSheet("color: red")
                return False
        except Exception as e:
            self.logger.error(f"Admin connection test error: {e}")
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setStyleSheet("color: red")
            return False

class ClientTab(QWidget):
    def __init__(self, admin_db, client_db,local_db, current_company, logger):
        super().__init__()
        self.admin_db = admin_db
        self.client_db = client_db
        self.current_company = current_company
        self.logger = logger
        # Fix local_db initialization
        self.local_db = local_db  # Direct reference to local_db
        self.setup_ui()
        
    def check_company_exists(self):
        """Check if company exists in admin database"""
        company_name = self.company_input.text().strip().replace(" ", "_")
        company_email = self.email_input.text().strip()
        client_url = self.url_input.text().strip()
        client_key = self.key_input.text().strip()
        
        try:
            # Get current values with safe fallback
            current_name = self.current_company.get("company_name", "")
            current_email = self.current_company.get("client_email", "")
            current_url = self.current_company.get("client_url", "")
            current_key = self.current_company.get("client_key", "")

            exists = False
            url_exits = False
            key_exists = False
            
            # Check if combination exists (excluding current company)
            if current_name!=company_name or current_email!=company_email:
                exists = self.admin_db.check_company_email_exists(company_name, company_email)
            
            if client_url!=current_url or client_key!=current_key:
                url_exits = self.admin_db.check_client_url_exists(client_url)
                key_exists = self.admin_db.check_client_key_exists(client_key)
        
            
            
            if exists or url_exits or key_exists:
                self.status_label.setText("Company with this name and email, url and key already exists")
                self.status_label.setStyleSheet("color: red")
                return True
            
            self.status_label.setText("Company name and email available")
            self.status_label.setStyleSheet("color: green")
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking company existence: {e}")
            self.status_label.setText(f"Error checking company: {str(e)}")
            self.status_label.setStyleSheet("color: red")
            return False
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        self.company_input = QLineEdit(self.current_company.get("company_name", "").replace("_", " "))
        self.email_input = QLineEdit(self.current_company.get("client_email", ""))
        self.url_input = QLineEdit(self.current_company.get("client_url", ""))
        self.key_input = QLineEdit(self.current_company.get("client_key", ""))
        self.key_input.setEchoMode(QLineEdit.Password)
        
        form.addRow("Company Name:", self.company_input)
        form.addRow("Email:", self.email_input)
        form.addRow("Client URL:", self.url_input)
        form.addRow("Client Key:", self.key_input)
        layout.addLayout(form)
        
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        
        # Add check company button
        btn_layout = QHBoxLayout()
        self.check_company_btn = QPushButton("Check Company")
        self.check_company_btn.clicked.connect(self.check_company_exists)
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self.test_connection)
        
        btn_layout.addWidget(self.check_company_btn)
        btn_layout.addWidget(self.test_btn)
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        
    def test_connection(self):
        url = self.url_input.text().strip()
        key = self.key_input.text().strip()
        
        if not url or not key:
            self.status_label.setText("Please enter both URL and key")
            return False
            
        try:
            self.client_db.set_credentials(url, key)
            response = self.client_db.test_connection()
            if response:
                self.status_label.setText("Connected successfully")
                self.status_label.setStyleSheet("color: green")
                return True
            else:
                self.status_label.setText("Connection failed")
                self.status_label.setStyleSheet("color: red")
                return False
        except Exception as e:
            self.logger.error(f"Client connection test error: {e}")
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setStyleSheet("color: red")
            return False

class SystemTab(QWidget):
    def __init__(self, vm_manager, tesseract_checker, current_paths, logger):
        super().__init__()
        self.vm_manager = vm_manager
        self.tesseract_checker = tesseract_checker
        self.current_paths = current_paths
        self.logger = logger
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        self.vm_path = QLineEdit(self.current_paths.get("vm_path", ""))
        self.system_path = QLineEdit(self.current_paths.get("system_path", ""))
        self.tesseract_path = QLineEdit(self.current_paths.get("tesseract_path", ""))
        self.ip=QLabel("")
        
        form.addRow("VM Path:", self.vm_path)
        form.addRow("System Path:", self.system_path)
        form.addRow("Tesseract Path:", self.tesseract_path)
        layout.addLayout(form)
        
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        
        btn_layout = QHBoxLayout()
        self.test_vm_btn = QPushButton("Test VM")
        self.test_vm_btn.clicked.connect(self.test_vm)
        self.test_tesseract_btn = QPushButton("Test Tesseract")
        self.test_tesseract_btn.clicked.connect(self.test_tesseract)
        
        btn_layout.addWidget(self.test_vm_btn)
        btn_layout.addWidget(self.test_tesseract_btn)
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        
    def test_vm(self):
        vm_path = self.vm_path.text().strip()
        system_path = self.system_path.text().strip()
        
        if not vm_path or not system_path:
            self.status_label.setText("Please enter both paths")
            return False
            
        try:
            self.status_label.setText("Starting VM and checking status...")
            QApplication.processEvents()
            
            # First try to get IP (in case VM is already running)
            ip = self.vm_manager.run_vm_and_get_ip(system_path)
            if not ip:
                # Try starting VM
                self.status_label.setText("VM not running. Attempting to start...")
                QApplication.processEvents()
                
                if not self.vm_manager.start_vm(vm_path):
                    self.status_label.setText("Failed to start VM")
                    self.status_label.setStyleSheet("color: red")
                    return False
                
                # Wait a bit for VM to start
                QTimer.singleShot(5000, lambda: None)
                QApplication.processEvents()
                
                # Try getting IP again
                ip = self.vm_manager.get_vm_ip(vm_path)
            
            if ip:
                self.status_label.setText(f"VM running at IP: {ip[0]}")
                self.status_label.setStyleSheet("color: green")
                self.ip.setText(ip[0])
                return True
            else:
                self.status_label.setText("VM running but IP not found. Please check network configuration.")
                self.status_label.setStyleSheet("color: red")
                return False
                
        except Exception as e:
            self.logger.error(f"VM check error: {e}")
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setStyleSheet("color: red")
            return False
            
    def test_tesseract(self):
        path = self.tesseract_path.text().strip()
        
        if not path:
            self.status_label.setText("Please enter Tesseract path")
            return False
            
        try:
            result = self.tesseract_checker.check_tesseract(path)
            if result:
                self.status_label.setText("Tesseract check successful")
                self.status_label.setStyleSheet("color: green")
                return True
            else:
                self.status_label.setText("Tesseract check failed")
                self.status_label.setStyleSheet("color: red")
                return False
        except Exception as e:
            self.logger.error(f"Tesseract check error: {e}")
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setStyleSheet("color: red")
            return False

class SummaryTab(QWidget):
    def __init__(self, current_data):
        super().__init__()
        self.current_data = current_data
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Add validation status section
        status_group = QGroupBox("Validation Status")
        status_layout = QVBoxLayout()
        
        self.admin_status = QLabel("❌ Admin Connection")
        self.client_status = QLabel("❌ Client Connection")
        self.company_status = QLabel("❌ Company Validation")
        self.vm_status = QLabel("❌ VM Configuration")
        self.tesseract_status = QLabel("❌ Tesseract Configuration")
        
        status_layout.addWidget(self.admin_status)
        status_layout.addWidget(self.client_status)
        status_layout.addWidget(self.company_status)
        status_layout.addWidget(self.vm_status)
        status_layout.addWidget(self.tesseract_status)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Password section
        pass_group = QGroupBox("Update Password")
        pass_layout = QHBoxLayout()
        self.password_input = QLineEdit(self.current_data.get("password", ""))
        self.password_input.setEchoMode(QLineEdit.Password)
        show_pass_btn = QPushButton("Show")
        show_pass_btn.setCheckable(True)
        show_pass_btn.toggled.connect(
            lambda checked: self.password_input.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )
        pass_layout.addWidget(self.password_input)
        pass_layout.addWidget(show_pass_btn)
        pass_group.setLayout(pass_layout)
        layout.addWidget(pass_group)
        
        # Dates section
        dates_group = QGroupBox("License Dates")
        dates_layout = QFormLayout()
        
        self.start_date = QDateEdit()
        self.end_date = QDateEdit()
        
        # Set minimum dates
        today = QDate.currentDate()
        self.start_date.setMinimumDate(today)
        self.end_date.setMinimumDate(today)
        
        # Set existing dates if available
        if self.current_data.get("start_date"):
            self.start_date.setDate(
                QDate.fromString(self.current_data["start_date"], "yyyy-MM-dd")
            )
        if self.current_data.get("end_date"):
            self.end_date.setDate(
                QDate.fromString(self.current_data["end_date"], "yyyy-MM-dd")
            )
            
        dates_layout.addRow("Start Date:", self.start_date)
        dates_layout.addRow("End Date:", self.end_date)
        dates_group.setLayout(dates_layout)
        layout.addWidget(dates_group)
        
        layout.addStretch()

    def update_status(self, validation_flags):
        """Update validation status indicators"""
        self.admin_status.setText("✅ Admin Connection" if validation_flags['admin_tested'] else "❌ Admin Connection")
        self.client_status.setText("✅ Client Connection" if validation_flags['client_tested'] else "❌ Client Connection")
        self.company_status.setText("✅ Company Validation" if validation_flags['company_tested'] else "❌ Company Validation")
        self.vm_status.setText("✅ VM Configuration" if validation_flags['vm_tested'] else "❌ VM Configuration")
        self.tesseract_status.setText("✅ Tesseract Configuration" if validation_flags['tesseract_tested'] else "❌ Tesseract Configuration")


class UpdateConfigDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        # Get required managers and databases
        self.admin_db = parent.admin_db
        self.client_db = parent.client_db
        self.local_db = parent.local_db
        self.logger = parent.logger
        
        # Initialize required managers
        from utils.vm_manager import VMManager
        from utils.tesseract_checker import TesseractChecker
        
        # Get current configuration
        self.client_config = self.local_db.get_client_config()
        
        # Initialize managers
        self.vm_manager = VMManager(self.client_config.get("vm_path", ""))
        self.tesseract_checker = TesseractChecker()
        
        self.setWindowTitle("Update Configuration")
        self.setMinimumSize(800, 600)
        
        # Initialize validation flags
        self.validation_flags = {
            'admin_tested': False,
            'client_tested': False,
            'company_tested': False,
            'vm_tested': False,
            'tesseract_tested': False
        }
        
        self.setup_ui()

    def setup_ui(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.admin_tab = AdminTab(self.admin_db, self.logger)
        self.client_tab = ClientTab(self.admin_db, self.client_db, self.local_db,self.client_config, self.logger)
        self.system_tab = SystemTab(self.vm_manager, self.tesseract_checker, self.client_config, self.logger)
        self.summary_tab = SummaryTab(self.client_config)
        
        # Add tabs
        self.tabs.addTab(self.admin_tab, "Admin Database")
        self.tabs.addTab(self.client_tab, "Client Database")
        self.tabs.addTab(self.system_tab, "System Configuration")
        self.tabs.addTab(self.summary_tab, "Summary")
        
        layout.addWidget(self.tabs)
        
        # Add navigation buttons
        nav_layout = QHBoxLayout()
        self.setup_navigation_buttons(nav_layout)
        layout.addLayout(nav_layout)
        
        # Connect signals
        self.connect_validation_signals()
        self.tabs.currentChanged.connect(self.update_navigation)
        self.update_navigation(0)

    def setup_navigation_buttons(self, layout):
        """Setup navigation and save buttons"""
        self.prev_btn = QPushButton("Previous")
        self.next_btn = QPushButton("Next")
        self.save_btn = QPushButton("Save Configuration")
        
        self.prev_btn.clicked.connect(self.previous_tab)
        self.next_btn.clicked.connect(self.next_tab)
        self.save_btn.clicked.connect(self.save_configuration)
        
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14pt;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self.save_btn.setEnabled(False)
        
        layout.addWidget(self.prev_btn)
        layout.addWidget(self.next_btn)
        layout.addWidget(self.save_btn)

    def next_tab(self):
        """Move to next tab"""
        current = self.tabs.currentIndex()
        if current < self.tabs.count() - 1:
            self.tabs.setCurrentIndex(current + 1)

    def previous_tab(self):
        """Move to previous tab"""
        current = self.tabs.currentIndex()
        if current > 0:
            self.tabs.setCurrentIndex(current - 1)

    def update_navigation(self, index):
        """Update navigation buttons based on current tab"""
        self.prev_btn.setVisible(index > 0)
        self.prev_btn.setEnabled(index > 0)
        
        is_last_tab = index == self.tabs.count() - 1
        self.next_btn.setVisible(not is_last_tab)
        self.next_btn.setEnabled(not is_last_tab)
        
        self.save_btn.setVisible(is_last_tab)
        
        # Update summary tab when switching to it
        if is_last_tab:
            self.summary_tab.update_status(self.validation_flags)

    def connect_validation_signals(self):
        """Connect signals for validation tracking"""
        # Admin tab validations
        self.admin_tab.test_btn.clicked.connect(
            lambda: self.set_validation_flag('admin_tested', self.admin_tab.test_connection())
        )
        self.admin_tab.url_input.textChanged.connect(lambda: self.set_validation_flag('admin_tested', False))
        self.admin_tab.key_input.textChanged.connect(lambda: self.set_validation_flag('admin_tested', False))
        
        # Client tab validations
        self.client_tab.test_btn.clicked.connect(
            lambda: self.set_validation_flag('client_tested', self.client_tab.test_connection())
        )
        self.client_tab.check_company_btn.clicked.connect(
            lambda: self.set_validation_flag('company_tested', not self.client_tab.check_company_exists())
        )
        
        # Reset client validation flags on input change
        self.client_tab.company_input.textChanged.connect(lambda: self.set_validation_flag('company_tested', False))
        self.client_tab.email_input.textChanged.connect(lambda: self.set_validation_flag('company_tested', False))
        self.client_tab.url_input.textChanged.connect(lambda: [
            self.set_validation_flag('client_tested', False),
            self.set_validation_flag('company_tested', False)
        ])
        self.client_tab.key_input.textChanged.connect(lambda: [
            self.set_validation_flag('client_tested', False),
            self.set_validation_flag('company_tested', False)
        ])
        
        # System tab validations
        self.system_tab.test_vm_btn.clicked.connect(
            lambda: self.set_validation_flag('vm_tested', self.system_tab.test_vm())
        )
        self.system_tab.test_tesseract_btn.clicked.connect(
            lambda: self.set_validation_flag('tesseract_tested', self.system_tab.test_tesseract())
        )
        
        # Reset system validation flags on input change
        self.system_tab.vm_path.textChanged.connect(lambda: self.set_validation_flag('vm_tested', False))
        self.system_tab.system_path.textChanged.connect(lambda: self.set_validation_flag('vm_tested', False))
        self.system_tab.tesseract_path.textChanged.connect(lambda: self.set_validation_flag('tesseract_tested', False))

    def set_validation_flag(self, flag_name, value):
        """Set validation flag and update save button state"""
        self.validation_flags[flag_name] = value
        self.update_save_button_state()
        self.summary_tab.update_status(self.validation_flags)

    def update_save_button_state(self):
        """Enable save button only if all validations pass"""
        self.save_btn.setEnabled(all(self.validation_flags.values()))

    
    def save_configuration(self):
        """Save configuration if all validations pass"""
        if not all(self.validation_flags.values()):
            missing = [k for k, v in self.validation_flags.items() if not v]
            QMessageBox.warning(self, "Validation Required", 
                              f"Please complete all validations:\n" + 
                              "\n".join(f"- {k.replace('_', ' ').title()}" for k in missing))
            return
            
        try:
            config_data = self.collect_config_data()
            old_company_name = self.local_db.get_value("company_name", "")
            old_email_name=self.local_db.get_value("clint_email","")
            company_name = config_data.get("company_name", "").strip()
            if not company_name:
                raise Exception("Company name is required")
            admin_save_success = self.admin_db.update_company(
                company_name, 
                config_data,
                old_name=old_company_name,
                old_email=old_email_name
            )
            clint_save_success = self.client_db.set_client_config(config_data)
            
            # Save to local database
            if admin_save_success and clint_save_success:
                if not self.local_db.clear_client_config():
                    raise Exception("Failed to clear existing configuration")
                if not self.local_db.set_client_config(config_data):
                    raise Exception("Failed to save configuration to local database")
                self.local_db.set_value("company_name", config_data.get("company_name", ""))
                self.local_db.set_value("admin_url", config_data.get("admin_url", ""))
                self.local_db.set_value("admin_key", config_data.get("admin_key", ""))
                self.local_db.set_value("vm_ip", config_data.get("vm_ip", ""))
                self.client_db.set_credentials(config_data.get("client_url", ""),config_data.get("client_key", ""))
                if self.client_db.test_connection():
                    self.client_db.set_client_config(config_data)
                else:
                    self.logger.error("Failed to save configuration to client database")
                    raise Exception("Failed to save configuration to client database")
                
            # Save to admin database
            
            
            # Show success message
            success_msg = "Configuration saved successfully:\n\n"
            success_msg += f"Company: {config_data['company_name']}\n"
            success_msg += f"Email: {config_data['client_email']}\n"
            success_msg += f"License: {config_data['start_date']} to {config_data['end_date']}\n"
            success_msg += f"\nLocal database: Saved successfully"
            success_msg += f"\nAdmin database: {'Updated successfully' if admin_save_success else 'Update failed'}"
            
            QMessageBox.information(self, "Save Status", success_msg)
            super().accept()
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            QMessageBox.warning(self, "Error", f"Could not save configuration:\n{str(e)}")

    def collect_config_data(self):
        """Collect all configuration data from tabs"""
        try:
            config_data = {
                # Admin configuration
                "admin_url": self.admin_tab.url_input.text().strip(),
                "admin_key": self.admin_tab.key_input.text().strip(),
                
                # Client configuration
                "company_name": self.client_tab.company_input.text().strip().replace(" ", "_"),
                "client_email": self.client_tab.email_input.text().strip(),
                "client_url": self.client_tab.url_input.text().strip(),
                "client_key": self.client_tab.key_input.text().strip(),
                
                
                # System configuration
                "vm_path": self.system_tab.vm_path.text().strip(),
                "ip":self.system_tab.ip.text().strip(),
                "system_path": self.system_tab.system_path.text().strip(),
                "tesseract_path": self.system_tab.tesseract_path.text().strip(),
                
                # Summary configuration
                "password": self.summary_tab.password_input.text().strip(),
                "start_date": self.summary_tab.start_date.date().toString("yyyy-MM-dd"),
                "end_date": self.summary_tab.end_date.date().toString("yyyy-MM-dd")
            }
            
            return config_data
            
        except Exception as e:
            self.logger.error(f"Error collecting configuration data: {e}")
            raise Exception(f"Failed to collect configuration data: {e}")

