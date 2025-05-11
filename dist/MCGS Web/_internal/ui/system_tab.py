from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, 
    QPushButton, QGroupBox, QProgressBar, QSpacerItem, QSizePolicy,
    QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

from ui.worker_threads import VMCheckThread, TesseractCheckThread
from ui.final_config_dialog import FinalConfigDialog
import time

class SystemTabWidget(QWidget):
    def __init__(self, parent, vm_manager, tesseract_checker):
        super().__init__()
        self.parent = parent
        self.vm_manager = vm_manager
        self.tesseract_checker = tesseract_checker
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
            padding: 10px;
        """)
        instructions_layout = QHBoxLayout(instructions_widget)
        
        info_icon = QLabel("🖥️")
        info_icon.setFont(QFont("Segoe UI", 16))
        instructions_layout.addWidget(info_icon)
        
        instructions = QLabel(
            "Please configure the system paths and settings. "
            "These settings will be used to connect to your virtual machine and OCR system."
        )
        instructions.setWordWrap(True)
        instructions.setFont(QFont("Segoe UI", 10))
        instructions_layout.addWidget(instructions)
        
        layout.addWidget(instructions_widget)
        
        # VM Configuration Group
        vm_group = QGroupBox("Virtual Machine Configuration")
        vm_group.setStyleSheet("""
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
        vm_layout = QFormLayout()
        vm_layout.setVerticalSpacing(15)
        vm_layout.setHorizontalSpacing(20)
        
        # VM Path
        vm_path_layout = QHBoxLayout()
        self.vm_path_input = QLineEdit()
        self.vm_path_input.setPlaceholderText("Path to your VM file")
        vm_path_layout.addWidget(self.vm_path_input)
        
        vm_browse_button = QPushButton("Browse")
        vm_browse_button.clicked.connect(self.browse_vm_path)
        vm_browse_button.setMaximumWidth(100)
        vm_path_layout.addWidget(vm_browse_button)
        
        vm_layout.addRow("<b>VM Path:</b>", vm_path_layout)
        
        # System Path
        system_path_layout = QHBoxLayout()
        self.system_path_input = QLineEdit()
        self.system_path_input.setPlaceholderText("Path to your system folder")
        system_path_layout.addWidget(self.system_path_input)
        
        system_browse_button = QPushButton("Browse")
        system_browse_button.clicked.connect(self.browse_system_path)
        system_browse_button.setMaximumWidth(100)
        system_path_layout.addWidget(system_browse_button)
        
        vm_layout.addRow("<b>System Path:</b>", system_path_layout)
        
        # VM Status
        self.vm_status_label = QLabel("VM not checked")
        self.vm_status_label.setStyleSheet("color: #e74c3c;")
        vm_layout.addRow("<b>VM Status:</b>", self.vm_status_label)
        
        # Check VM button
        check_vm_button = QPushButton("Check VM")
        check_vm_button.setStyleSheet("""
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
        check_vm_button.setIcon(QIcon("icons/vm.png"))  # Add an icon if available
        check_vm_button.clicked.connect(self.check_vm)
        vm_layout.addRow("", check_vm_button)
        
        # IP Address
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("IP will be detected automatically")
        self.ip_input.setReadOnly(True)
        self.ip_input.setStyleSheet("""
            background-color: #f8f9fa;
            color: #7f8c8d;
        """)
        vm_layout.addRow("<b>IP Address:</b>", self.ip_input)
        
        vm_group.setLayout(vm_layout)
        layout.addWidget(vm_group)
        
        # Tesseract Configuration Group
        tesseract_group = QGroupBox("OCR Configuration")
        tesseract_group.setStyleSheet("""
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
        tesseract_layout = QFormLayout()
        tesseract_layout.setVerticalSpacing(15)
        tesseract_layout.setHorizontalSpacing(20)
        
        # Tesseract Path
        tesseract_path_layout = QHBoxLayout()
        self.tesseract_path_input = QLineEdit()
        self.tesseract_path_input.setPlaceholderText("Path to tesseract.exe")
        tesseract_path_layout.addWidget(self.tesseract_path_input)
        
        tesseract_browse_button = QPushButton("Browse")
        tesseract_browse_button.clicked.connect(self.browse_tesseract_path)
        tesseract_browse_button.setMaximumWidth(100)
        tesseract_path_layout.addWidget(tesseract_browse_button)
        
        tesseract_layout.addRow("<b>Tesseract Path:</b>", tesseract_path_layout)
        
        # Tesseract Status
        self.tesseract_status_label = QLabel("Tesseract not checked")
        self.tesseract_status_label.setStyleSheet("color: #e74c3c;")
        tesseract_layout.addRow("<b>Tesseract Status:</b>", self.tesseract_status_label)
        
        # Check Tesseract button
        check_tesseract_button = QPushButton("Check Tesseract")
        check_tesseract_button.setStyleSheet("""
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
        check_tesseract_button.setIcon(QIcon("icons/ocr.png"))  # Add an icon if available
        check_tesseract_button.clicked.connect(self.check_tesseract)
        tesseract_layout.addRow("", check_tesseract_button)
        
        tesseract_group.setLayout(tesseract_layout)
        layout.addWidget(tesseract_group)
        
        # Add spacer at the bottom to push everything up
        layout.addStretch(1)
        
        # Remove the inner Next button - we'll use the one in the parent window
        
        self.setLayout(layout)
    
    def browse_vm_path(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select VMware Executable", "", "Executable Files (*.exe);;All Files (*)"
        )
        if file_path:
            self.vm_path_input.setText(file_path)
            # Update VM manager with new vmrun path
            self.vm_manager.vmrun_path = file_path
    
    def browse_system_path(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select VM Configuration File", "", "VMware Configuration Files (*.vmx);;All Files (*)"
        )
        if file_path:
            self.system_path_input.setText(file_path)
    
    def browse_tesseract_path(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Tesseract Executable", "", "Executable Files (*.exe);;All Files (*)"
        )
        if file_path:
            self.tesseract_path_input.setText(file_path)
    
    def check_vm(self):
        """Check VM status"""
        vm_path = self.vm_path_input.text().strip()
        system_path = self.system_path_input.text().strip()
        
        if not vm_path:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Missing Information", "Please enter the VMware executable path.")
            return
            
        if not system_path:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Missing Information", "Please enter the VM configuration (.vmx) file path.")
            return
            
        if not vm_path.lower().endswith('.exe'):
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Invalid Path", "VM Path should point to vmrun.exe file.")
            return
            
        if not system_path.lower().endswith('.vmx'):
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Invalid Path", "System Path should point to a .vmx file.")
            return
        
        self.vm_status_label.setText("Checking VM...")
        
        # Update VM manager with the vmrun path and check VM
        try:
            self.vm_manager.vmrun_path = vm_path
            self.on_vm_checked(True, "VM check started")
            is_running, message = self.vm_manager.run_vm_and_get_ip(system_path)
            
            
            if is_running:
                # Get IP if VM is running
                ip_address = self.vm_manager.get_vm_ip(system_path)
                self.on_vm_checked(True, "VM is running", ip_address)
            else:
                self.vm_manager.start_vm(system_path)
                time.sleep(10)  # Wait for VM to fully boot
                ip_address = self.vm_manager.get_vm_ip(system_path)
                self.on_vm_checked(False, message)

                
        except Exception as e:
            self.parent.logger.error(f"Error checking VM: {str(e)}")
            self.on_vm_checked(False, str(e))
    
    def on_vm_checked(self, success, message, ip=None):
        from PyQt5.QtWidgets import QMessageBox
        if success:
            self.vm_status_label.setText("VM is running")
            self.vm_status_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
            
            if ip:
                self.ip_input.setText(ip[0])
                self.ip_input.setStyleSheet("color: #2c3e50; background-color: #e8f0ff; font-weight: bold;")
                self.parent.config_data["ip"] = ip
                
                # Show static IP message
                QMessageBox.information(self, "IP Address Detected", 
                                        f"VM IP address detected: {ip}\n\nPlease ensure this IP is static.")
            else:
                self.vm_status_label.setText("VM is running, but IP could not be detected")
                self.vm_status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
        else:
            self.vm_status_label.setText(f"VM check failed: {message}")
            self.vm_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
    
    def check_tesseract(self):
        tesseract_path = self.tesseract_path_input.text().strip()
        
        if not tesseract_path:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Missing Information", "Please enter the Tesseract path.")
            return
        
        self.tesseract_status_label.setText("Checking Tesseract...")
        
        # Create a worker thread to check Tesseract
        self.tesseract_check_thread = TesseractCheckThread(self.tesseract_checker, tesseract_path)
        self.tesseract_check_thread.check_result.connect(self.on_tesseract_checked)
        self.tesseract_check_thread.start()
    
    def on_tesseract_checked(self, success, message):
        if success:
            self.tesseract_status_label.setText(f"Tesseract is available: {message}")
            self.tesseract_status_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
        else:
            self.tesseract_status_label.setText(f"Tesseract check failed: {message}")
            self.tesseract_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
    
    def on_next_clicked(self):
        """Handle next button click"""
        vm_path = self.vm_path_input.text().strip()
        system_path = self.system_path_input.text().strip()
        tesseract_path = self.tesseract_path_input.text().strip()
        
        # Validate paths
        if not vm_path or not system_path or not tesseract_path:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Missing Information", 
                               "Please enter all required paths.")
            return
        
        # Store paths in parent's config_data
        self.parent.config_data["vm_path"] = vm_path
        self.parent.config_data["system_path"] = system_path
        self.parent.config_data["tesseract_path"] = tesseract_path
        
        # Call parent's on_finish_clicked method
        self.parent.on_finish_clicked()
        ip = self.ip_input.text().strip()
        
        if not vm_path or not system_path or not tesseract_path:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Missing Information", 
                                "Please enter all system paths.")
            return
        
        # Store configuration data in parent
        self.parent.config_data["vm_path"] = vm_path
        self.parent.config_data["system_path"] = system_path
        self.parent.config_data["tesseract_path"] = tesseract_path
        
        if ip:
            self.parent.config_data["ip"] = ip
        
        # Show final configuration dialog to set password and dates
        self.show_final_config_dialog()
    
    def show_final_config_dialog(self):
        """Show final configuration dialog to set password and dates"""
        dialog = FinalConfigDialog(self.parent.config_data)
        if dialog.exec_():
            # Get values from dialog
            self.parent.config_data["password"] = dialog.password
            self.parent.config_data["start_date"] = dialog.start_date
            self.parent.config_data["end_date"] = dialog.end_date
            
            # Now show the configuration summary
            self.show_config_summary()
    
    def show_config_summary(self):
        """Show configuration summary dialog"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Configuration Summary")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Configuration Summary")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c5ecc; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Company info
        company_name = self.parent.config_data.get("company_name", "Not set")
        client_email = self.parent.config_data.get("client_email", "Not set")
        
        company_info = QLabel(f"<b>Company:</b> {company_name}<br><b>Email:</b> {client_email}")
        company_info.setStyleSheet("background-color: #e8f0ff; padding: 10px; border-radius: 5px;")
        layout.addWidget(company_info)
        
        # Database info
        admin_url = self.parent.config_data.get("admin_url", "Not set")
        client_url = self.parent.config_data.get("client_url", "Not set")
        
        db_info = QLabel(f"<b>Admin Database:</b> {admin_url}<br><b>Client Database:</b> {client_url}")
        db_info.setStyleSheet("background-color: #e8f0ff; padding: 10px; border-radius: 5px;")
        layout.addWidget(db_info)
        
        # System info
        vm_path = self.parent.config_data.get("vm_path", "Not set")
        system_path = self.parent.config_data.get("system_path", "Not set")
        tesseract_path = self.parent.config_data.get("tesseract_path", "Not set")
        ip = self.parent.config_data.get("ip", "Not detected")
        
        system_info = QLabel(f"<b>VM Path:</b> {vm_path}<br><b>System Path:</b> {system_path}<br>"
                             f"<b>Tesseract Path:</b> {tesseract_path}<br><b>IP Address:</b> {ip}")
        system_info.setStyleSheet("background-color: #e8f0ff; padding: 10px; border-radius: 5px;")
        system_info.setWordWrap(True)
        layout.addWidget(system_info)
        
        # License info
        start_date = self.parent.config_data.get("start_date", "Not set")
        end_date = self.parent.config_data.get("end_date", "Not set")
        password = self.parent.config_data.get("password", "Not set")
        
        license_info = QLabel(f"<b>License Start:</b> {start_date}<br><b>License End:</b> {end_date}<br>"
                             f"<b>Password:</b> {'*' * len(password) if password else 'Not set'}")
        license_info.setStyleSheet("background-color: #e8f0ff; padding: 10px; border-radius: 5px;")
        layout.addWidget(license_info)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.finish_configuration(dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def finish_configuration(self, dialog):
        """Finish configuration and close dialog"""
        dialog.accept()
        
        # Save all configuration data to the admin database
        self.save_configuration_to_database()
        
        # Call parent's method to handle finish
        if hasattr(self.parent, 'finish_configuration'):
            self.parent.finish_configuration()
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "Configuration Complete", 
                              "Configuration has been saved successfully.")
    
    def save_configuration_to_database(self):
        """Save all configuration data to the admin database"""
        try:
            # Make sure admin database is connected
            if not hasattr(self.parent, 'admin_db') or not self.parent.admin_db.connected:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Database Error", 
                                   "Not connected to admin database. Configuration will be saved locally only.")
                return
            
            # Prepare data for saving
            company_data = {
                "company_name": self.parent.config_data.get("company_name", ""),
                "client_email": self.parent.config_data.get("client_email", ""),
                "client_url": self.parent.config_data.get("client_url", ""),
                "client_key": self.parent.config_data.get("client_key", ""),
                "vm_path": self.parent.config_data.get("vm_path", ""),
                "system_path": self.parent.config_data.get("system_path", ""),
                "tesseract_path": self.parent.config_data.get("tesseract_path", ""),
                "ip_address": self.parent.config_data.get("ip", ""),
                "password": self.parent.config_data.get("password", ""),
                "start_date": self.parent.config_data.get("start_date", ""),
                "end_date": self.parent.config_data.get("end_date", ""),
                "created_at": "NOW()"
            }
            
            # Save to admin database
            success = self.parent.admin_db.add_company(company_data)
            
            if not success:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Database Error", 
                                   "Failed to save configuration to admin database. Check the logs for details.")
        
        except Exception as e:
            import logging
            logging.getLogger("LoomLive").error(f"Error saving configuration to database: {str(e)}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", 
                               f"An error occurred while saving configuration: {str(e)}")