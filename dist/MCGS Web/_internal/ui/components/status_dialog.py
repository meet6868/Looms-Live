from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGridLayout, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon
from datetime import datetime
import os
from utils.vm_manager import VMManager  # Add this import
import subprocess

class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 150);
            }
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.spinner = QProgressBar()
        self.spinner.setMaximumWidth(200)
        self.spinner.setTextVisible(False)
        self.spinner.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2ecc71;
                border-radius: 5px;
                background-color: transparent;
                height: 10px;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
            }
        """)
        layout.addWidget(self.spinner)
        
        self.loading_text = QLabel("Loading...")
        layout.addWidget(self.loading_text, alignment=Qt.AlignCenter)
        
        self.progress = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(30)
        
        self.hide()
    
    def update_progress(self):
        self.progress = (self.progress + 1) % 101
        self.spinner.setValue(self.progress)
    
    def showEvent(self, event):
        self.setGeometry(self.parent.rect())
        self.progress = 0
        self.timer.start(30)
    
    def hideEvent(self, event):
        self.timer.stop()

class StatusDialog(QDialog):
    def __init__(self, main_page):
        super().__init__(main_page)
        self.main_page = main_page
        self.admin_db = main_page.admin_db
        self.client_db = main_page.client_db
        self.local_db = main_page.local_db
        self.logger = main_page.logger
        
        
        # Create loading overlay
        self.loading_overlay = LoadingOverlay(self)
        
        # Initialize UI
        self.setup_ui()
        
        # Add status check timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.refresh_status)
        self.status_timer.start(300000)  # 5 minutes
        
        # Initial status check
        self.refresh_status()
        main_page.status_loading_label.hide()
    
    def show_loading(self, message="Loading...", use_overlay=False):
        """Show loading overlay with message"""
        if use_overlay and hasattr(self, 'loading_overlay'):
            self.loading_overlay.loading_text.setText(message)
            self.loading_overlay.show()
            self.loading_overlay.raise_()
        # If not using overlay, we'll just update the status text directly
    
    def hide_loading(self):
        """Hide loading overlay"""
        if hasattr(self, 'loading_overlay'):
            self.loading_overlay.hide()
    
    def setup_ui(self):
        self.setWindowTitle("System Status")
        self.setFixedSize(550, 700)  # Increased height to accommodate all content
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2c3e50, stop:1 #3498db);
                border-radius: 10px;
            }
            QLabel {
                color: white;
                min-width: 120px;
            }
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 20, 15, 20)  # Reduced margins to maximize space
        layout.setSpacing(15)  # Reduced spacing between elements
        
        # Title with icon
        title_layout = QHBoxLayout()
        title = QLabel("System Status")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet("color: #ecf0f1;")
        title_layout.addWidget(title)
        layout.addLayout(title_layout)
        
        # Status cards layout
        cards_layout = QVBoxLayout()
        cards_layout.setSpacing(10)  # Reduced spacing between cards
        
        # Database status card
        db_card = QWidget()
        db_card.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 10px;  /* Reduced padding */
            }
        """)
        db_layout = QVBoxLayout(db_card)
        db_layout.setContentsMargins(10, 5, 10, 5)  # Reduced internal margins
        db_layout.setSpacing(10)  # Reduced spacing
        
        # Admin & Client DB status with improved visibility
        self.admin_status = self.create_status_item("Admin Database", "Connected")
        self.client_status = self.create_status_item("Client Database", "Connected")
        db_layout.addWidget(self.admin_status)
        db_layout.addWidget(self.client_status)
        cards_layout.addWidget(db_card)
        
        # VM Status with animation and text status
        vm_card = QWidget()
        vm_card.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 10px;  /* Reduced padding */
            }
        """)
        vm_layout = QVBoxLayout(vm_card)
        vm_layout.setContentsMargins(10, 5, 10, 5)  # Reduced internal margins
        vm_layout.setSpacing(8)  # Reduced spacing
        
        vm_title = QLabel("Virtual Machine Status")
        vm_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        vm_layout.addWidget(vm_title)
        
        # Add VM status text label with adjusted visibility
        self.vm_status_text = QLabel("Checking VM status...")
        self.vm_status_text.setStyleSheet("color: #f39c12; font-weight: bold; font-size: 14px;")
        self.vm_status_text.setAlignment(Qt.AlignCenter)
        self.vm_status_text.setMinimumHeight(25)
        self.vm_status_text.setWordWrap(True)  # Enable word wrap to prevent text cutoff
        vm_layout.addWidget(self.vm_status_text)
        
        # Improved VM status progress bar
        self.vm_status = QProgressBar()
        self.vm_status.setTextVisible(False)
        self.vm_status.setFixedHeight(15)  # Fixed height
        self.vm_status.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2ecc71;
                border-radius: 5px;
                background-color: rgba(0, 0, 0, 0.2);
                min-width: 350px;
                max-width: 350px;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
            }
        """)
        vm_layout.addWidget(self.vm_status, 0, Qt.AlignCenter)
        
        # Add VM IP address display with adjusted visibility
        self.vm_ip_label = QLabel("IP Address: Checking...")
        self.vm_ip_label.setStyleSheet("color: #ecf0f1; font-size: 13px; font-weight: bold;")
        self.vm_ip_label.setAlignment(Qt.AlignCenter)
        self.vm_ip_label.setMinimumHeight(25)
        self.vm_ip_label.setWordWrap(True)  # Enable word wrap to prevent text cutoff
        vm_layout.addWidget(self.vm_ip_label)
        
        # Add VM status animation timer
        self.vm_timer = QTimer(self)
        self.vm_timer.timeout.connect(self.update_vm_animation)
        self.vm_timer.start(50)
        
        cards_layout.addWidget(vm_card)
        
        # License status with circular progress
        license_card = QWidget()
        license_card.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                padding: 10px;  /* Reduced padding */
            }
        """)
        license_layout = QVBoxLayout(license_card)
        license_layout.setContentsMargins(10, 5, 10, 5)  # Reduced internal margins
        license_layout.setSpacing(8)  # Reduced spacing
        
        license_title = QLabel("License Status")
        license_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        license_layout.addWidget(license_title)
        
        # Add license expiry date display with adjusted visibility
        self.license_expiry = QLabel("Expiry Date: Checking...")
        self.license_expiry.setStyleSheet("font-size: 13px; color: #ecf0f1; font-weight: bold;")
        self.license_expiry.setAlignment(Qt.AlignCenter)
        self.license_expiry.setMinimumHeight(25)
        self.license_expiry.setWordWrap(True)  # Enable word wrap to prevent text cutoff
        license_layout.addWidget(self.license_expiry)
        
        self.license_days = QLabel("Checking license...")
        self.license_days.setStyleSheet("font-size: 14px; color: #2ecc71; font-weight: bold;")
        self.license_days.setAlignment(Qt.AlignCenter)
        self.license_days.setMinimumHeight(25)
        self.license_days.setWordWrap(True)  # Enable word wrap to prevent text cutoff
        license_layout.addWidget(self.license_days)
        
        # Add license progress bar with adjusted visibility
        self.license_progress = QProgressBar()
        self.license_progress.setTextVisible(False)
        self.license_progress.setFixedHeight(15)  # Fixed height
        self.license_progress.setFixedWidth(350)  # Fixed width to match VM progress bar
        self.license_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2ecc71;
                border-radius: 5px;
                background-color: rgba(0, 0, 0, 0.2);
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
            }
        """)
        license_layout.addWidget(self.license_progress, 0, Qt.AlignCenter)
        
        cards_layout.addWidget(license_card)
        
        layout.addLayout(cards_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 5, 0, 0)  # Reduced margins
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_status)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("background-color: #e74c3c;")
        
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

    def update_vm_animation(self):
        """Update VM status animation"""
        value = self.vm_status.value()
        value = (value + 2) % 100
        self.vm_status.setValue(value)
    
    def create_status_item(self, label_text, initial_status):
        """Create a status item widget"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(10)  # Reduced spacing
        
        label = QLabel(label_text)
        label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        label.setMinimumWidth(120)  # Set minimum width
        label.setMaximumWidth(150)  # Set maximum width
        
        status = QLabel(initial_status)
        status.setStyleSheet("color: #2ecc71; font-weight: bold;")
        status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # Right-aligned
        
        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(status)
        
        # Store status label for updates
        container.status_label = status
        container.update_status = lambda connected: self.update_item_status(container.status_label, connected)
        
        return container
    
    def update_item_status(self, label, connected):
        """Update status label text and style"""
        label.setText("Connected" if connected else "Disconnected")
        label.setStyleSheet(
            "color: #2ecc71; font-weight: bold;" if connected else 
            "color: #e74c3c; font-weight: bold;"
        )

    def refresh_status(self):
        """Refresh all status information"""
        try:
            # Update UI to show refreshing status directly in the VM status text
            self.vm_status_text.setText("Refreshing status...")
            self.vm_status_text.setStyleSheet("color: #f39c12; font-weight: bold; background-color: transparent;")
            self.vm_ip_label.setText("IP Address: Checking...")
            self.vm_ip_label.setStyleSheet("color: #f39c12; font-size: 13px; font-weight: bold; background-color: transparent;")
            
            # Hide start VM button if it exists
            if hasattr(self, 'start_vm_btn'):
                self.start_vm_btn.hide()
                
            # Process events to update UI immediately
            from PyQt5.QtCore import QCoreApplication
            QCoreApplication.processEvents()
            
            # Get client configuration
            client_config = self.local_db.get_client_config()
            vmrun_path = client_config.get("vm_path", "")
            vmx_path = client_config.get("system_path", "")
            
            # Debug VM paths
            self.logger.info(f"VM Run Path: {vmrun_path}")
            self.logger.info(f"VMX Path: {vmx_path}")
            
            # Update database connections
            admin_connected = self.admin_db.test_connection()
            client_connected = self.client_db.test_connection()
            
            # Update admin and client status using container methods
            if hasattr(self.admin_status, 'update_status'):
                self.admin_status.update_status(admin_connected)
            if hasattr(self.client_status, 'update_status'):
                self.client_status.update_status(client_connected)
            
            # VM Status check - Improved VM check logic
            if vmrun_path and vmx_path:
                self.logger.info("Starting VM status check...")
                try:
                    # Check if VM is running
                    self.vm_status_text.setText("Checking VM status...")
                    self.vm_status_text.setStyleSheet("color: #f39c12; font-weight: bold;")
                    
                    # Ensure paths exist and remove any quotes
                    vmrun_path = vmrun_path.strip('"')
                    vmx_path = vmx_path.strip('"')
                    
                    # Ensure vmrun_path and vmx_path exist
                    if not os.path.exists(vmrun_path):
                        self.logger.error(f"VMRun path does not exist: {vmrun_path}")
                        self.vm_status_text.setText("VMRun path not found!")
                        self.vm_status_text.setStyleSheet("color: #e74c3c; font-weight: bold;")
                        self.vm_ip_label.setText("IP Address: Not available")
                        self.vm_ip_label.setStyleSheet("color: #e74c3c; font-size: 13px; font-weight: bold;")
                    elif not os.path.exists(vmx_path):
                        self.logger.error(f"VMX path does not exist: {vmx_path}")
                        self.vm_status_text.setText("VMX file not found!")
                        self.vm_status_text.setStyleSheet("color: #e74c3c; font-weight: bold;")
                        self.vm_ip_label.setText("IP Address: Not available")
                        self.vm_ip_label.setStyleSheet("color: #e74c3c; font-size: 13px; font-weight: bold;")
                    else:
                        # Both paths exist, continue with VM check
                        self.logger.info(f"Running command: '{vmrun_path}' list")
                        
                        try:
                            # 清理路径
                            vmrun_path_clean = vmrun_path.replace('"', '')
                            
                            # 使用列表形式的命令
                            cmd = [vmrun_path_clean, "list"]
                            self.logger.info(f"执行命令: {' '.join(cmd)}")
                            
                            # 不使用shell=True
                            result = subprocess.run(
                                cmd,
                                capture_output=True,
                                text=True,
                                encoding='utf-8',
                                errors='ignore',
                                timeout=30
                            )
                            
                            # Record output for debugging
                            self.logger.info(f"VM list output: {result.stdout}")
                            if result.stderr:
                                self.logger.error(f"VM list error: {result.stderr}")
                            
                            # Check if VM is running
                            is_running = vmx_path in result.stdout
                            self.logger.info(f"VM running status: {is_running}")
                            
                            if is_running:
                                self.vm_status_text.setText("VM is running")
                                self.vm_status_text.setStyleSheet("color: #2ecc71; font-weight: bold;")
                                
                                # Get VM IP address with multiple attempts
                                try:
                                    # 清理路径
                                    vmrun_path_clean = vmrun_path.replace('"', '')
                                    vmx_path_clean = vmx_path.replace('"', '')
                                    
                                    # Define max attempts - increase to 10
                                    max_attempts = 10
                                    ip = None
                                    
                                    # Try multiple times to get IP
                                    for attempt in range(max_attempts):
                                        self.vm_ip_label.setText(f"IP Address: Checking ({attempt+1}/{max_attempts})...")
                                        self.vm_ip_label.setStyleSheet("color: #f39c12; font-size: 13px; font-weight: bold;")
                                        
                                        # Process events to update UI
                                        from PyQt5.QtCore import QCoreApplication
                                        QCoreApplication.processEvents()
                                        
                                        # 使用列表形式的命令
                                        ip_cmd = [vmrun_path_clean, "-T", "ws", "getGuestIPAddress", vmx_path_clean, "-wait"]
                                        self.logger.info(f"Getting IP with command (attempt {attempt+1}): {' '.join(ip_cmd)}")
                                        
                                        # 不使用shell=True
                                        ip_result = subprocess.run(
                                            ip_cmd,
                                            capture_output=True,
                                            text=True,
                                            encoding='utf-8',
                                            errors='ignore',
                                            timeout=30
                                        )
                                        
                                        ip = ip_result.stdout.strip()
                                        self.logger.info(f"VM IP attempt {attempt+1}: {ip}")
                                        
                                        if ip and ip != "0.0.0.0" and "Error" not in ip:
                                            self.local_db.set_value("vm_ip", ip)
                                            self.vm_ip_label.setText(f"IP Address: {ip}")
                                            self.vm_ip_label.setStyleSheet("color: #2ecc71; font-size: 13px; font-weight: bold;")
                                            self.logger.info(f"Successfully got VM IP on attempt {attempt+1}: {ip}")
                                            break
                                        
                                        # Wait a bit before next attempt
                                        import time
                                        time.sleep(3)
                                    
                                    # After all attempts, if still no IP, use cached or show not available
                                    if not ip or ip == "0.0.0.0" or "Error" in str(ip):
                                        saved_ip = self.local_db.get_value("vm_ip")
                                        if saved_ip:
                                            self.vm_ip_label.setText(f"IP Address: {saved_ip} (cached)")
                                            self.vm_ip_label.setStyleSheet("color: #f39c12; font-size: 13px; font-weight: bold;")
                                            self.logger.info(f"Using cached VM IP after failed attempts: {saved_ip}")
                                        else:
                                            self.vm_ip_label.setText("IP Address: Could not retrieve IP")
                                            self.vm_ip_label.setStyleSheet("color: #e74c3c; font-size: 13px; font-weight: bold;")
                                            self.logger.warning("VM IP not available after multiple attempts")
                                except Exception as e:
                                    self.logger.error(f"Error getting VM IP: {e}")
                                    # Try from local database get last saved IP
                                    saved_ip = self.local_db.get_value("vm_ip")
                                    if saved_ip:
                                        self.vm_ip_label.setText(f"IP Address: {saved_ip} (cached)")
                                        self.vm_ip_label.setStyleSheet("color: #f39c12; font-size: 13px; font-weight: bold;")
                                        self.logger.info(f"Using cached VM IP: {saved_ip}")
                                    else:
                                        self.vm_ip_label.setText("IP Address: Error getting IP")
                                        self.vm_ip_label.setStyleSheet("color: #e74c3c; font-size: 13px; font-weight: bold;")
                            else:
                                self.vm_status_text.setText("VM is not running")
                                self.vm_status_text.setStyleSheet("color: #e74c3c; font-weight: bold;")
                                self.vm_ip_label.setText("IP Address: VM not running")
                                self.vm_ip_label.setStyleSheet("color: #e74c3c; font-size: 13px; font-weight: bold;")
                                
                                # Start VM automatically
                                self.start_vm()
                        except Exception as e:
                            self.logger.error(f"Error executing VM list command: {e}")
                            self.vm_status_text.setText(f"Error checking VM: {str(e)[:30]}...")
                            self.vm_status_text.setStyleSheet("color: #e74c3c; font-weight: bold;")
                            self.vm_ip_label.setText("IP Address: Not available")
                            self.vm_ip_label.setStyleSheet("color: #e74c3c; font-size: 13px; font-weight: bold;")
                except subprocess.TimeoutExpired:
                    self.logger.error("VM list command timed out")
                    self.vm_status_text.setText("VM list command timed out")
                    self.vm_status_text.setStyleSheet("color: #e74c3c; font-weight: bold;")
            else:
                self.logger.warning("VM paths not configured properly")
                self.vm_status_text.setText("VM paths not configured")
                self.vm_status_text.setStyleSheet("color: #e74c3c; font-weight: bold;")
                self.vm_ip_label.setText("IP Address: Not available")
                self.vm_ip_label.setStyleSheet("color: #e74c3c; font-size: 13px; font-weight: bold;")
            
            # License status update - Add more logging
            self.logger.info("Starting license status check...")
            company_name = self.local_db.get_value("company_name")
            client_email=self.local_db.get_value("client_email")
            self.logger.info(f"Client email from local DB: {client_email}")
            self.logger.info(f"Company name from local DB: {company_name}")
            
            if company_name:
                try:
                    if admin_connected:
                        self.logger.info(f"Fetching license data for company: {company_name}")
                        license_data = self.admin_db.get_company_data(company_name,client_email)
                        self.logger.info(f"License data received: {license_data}")
                    
                    else:

                        self.logger.info(f"Fetching license data for company from local: {company_name}")
                        license_data = self.local_db.get_client_config()
                        self.logger.info(f"License data received from local db: {license_data}")
                    
                    if license_data and 'end_date' in license_data:
                        start_date = datetime.strptime(license_data.get('start_date', '2023-01-01'), "%Y-%m-%d")
                        end_date = datetime.strptime(license_data['end_date'], "%Y-%m-%d")
                        days_remaining = (end_date - datetime.now()).days
                        total_days = (end_date - start_date).days
                        
                        self.logger.info(f"License: Start={start_date}, End={end_date}, Days remaining={days_remaining}")
                        
                        # Calculate percentage of license remaining
                        if total_days > 0:
                            percent_remaining = min(100, max(0, (days_remaining / total_days) * 100))
                        else:
                            percent_remaining = 0
                        
                        # Update license progress bar
                        self.license_progress.setValue(int(percent_remaining))
                        
                        # Set color based on days remaining
                        if days_remaining > 30:
                            status_color = "#2ecc71"  # Green
                        elif days_remaining > 0:
                            status_color = "#f39c12"  # Orange
                        else:
                            status_color = "#e74c3c"  # Red
                        
                        # Update license progress bar color
                        self.license_progress.setStyleSheet(f"""
                            QProgressBar {{
                                border: 2px solid {status_color};
                                border-radius: 5px;
                                background-color: rgba(0, 0, 0, 0.2);
                                height: 10px;
                            }}
                            QProgressBar::chunk {{
                                background-color: {status_color};
                            }}
                        """)
                        
                        # Update license text with creative display
                        if days_remaining > 365:
                            years = days_remaining // 365
                            remaining_days = days_remaining % 365
                            self.license_days.setText(f"{years}y, {remaining_days}d remaining")
                        elif days_remaining > 0:
                            self.license_days.setText(f"{days_remaining}d remaining")
                        else:
                            self.license_days.setText("EXPIRED!")
                        
                        # Update expiry date with "Expiry Date:" prefix
                        formatted_date = end_date.strftime('%d %b %Y')
                        self.logger.info(f"Setting expiry date display to: {formatted_date}")
                        self.license_expiry.setText(f"Expiry Date: {formatted_date}")
                        self.license_expiry.setStyleSheet("font-size: 13px; color: #ecf0f1; font-weight: bold;")
                    else:
                        self.logger.warning(f"Invalid license data received: {license_data}")
                        self.license_days.setText("License Not Found")
                        self.license_days.setStyleSheet("font-size: 14px; color: #e74c3c; font-weight: bold;")
                        self.license_expiry.setText("Expiry Date: Unknown")
                        self.license_progress.setValue(0)
                except Exception as e:
                    self.logger.error(f"Error processing license data: {e}")
                    self.license_days.setText("Error checking license")
                    self.license_days.setStyleSheet("font-size: 14px; color: #e74c3c; font-weight: bold;")
                    self.license_expiry.setText("Expiry Date: Error")
            else:
                self.logger.warning(f"Cannot check license: admin_connected={admin_connected}, company_name={company_name}")
                self.license_days.setText("Cannot check license")
                self.license_days.setStyleSheet("font-size: 14px; color: #f39c12; font-weight: bold;")
                self.license_expiry.setText("Expiry Date: Unknown")
            
            self.hide_loading()
            
        except Exception as e:
            self.logger.error(f"Error refreshing status: {e}")
            self.hide_loading()
            
            # Update database connections using the container's update_status method
            if hasattr(self.admin_status, 'update_status'):
                self.admin_status.update_status(self.admin_db.test_connection())
            if hasattr(self.client_status, 'update_status'):
                self.client_status.update_status(self.client_db.test_connection())

    def start_vm(self):
        """Start the virtual machine"""
        try:
            # Get client configuration
            client_config = self.local_db.get_client_config()
            vmrun_path = client_config.get("vm_path", "")
            vmx_path = client_config.get("system_path", "")
            
            if not vmrun_path or not vmx_path:
                self.logger.error("VM paths not configured properly")
                self.vm_status_text.setText("VM paths not configured")
                self.vm_status_text.setStyleSheet("color: #e74c3c; font-weight: bold;")
                return
                
            # Clean paths
            vmrun_path_clean = vmrun_path.replace('"', '')
            vmx_path_clean = vmx_path.replace('"', '')
            
            # Update status
            self.vm_status_text.setText("Starting VM...")
            self.vm_status_text.setStyleSheet("color: #f39c12; font-weight: bold;")
            
            # Process events to update UI
            from PyQt5.QtCore import QCoreApplication
            QCoreApplication.processEvents()
            
            # First check if VMware is running, if not start it
            try:
                # Check if VMware Workstation process is running
                vmware_process = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq vmware.exe"],
                    capture_output=True,
                    text=True
                )
                
                if "vmware.exe" not in vmware_process.stdout:
                    self.logger.info("VMware is not running, starting it...")
                    self.vm_status_text.setText("Starting VMware...")
                    
                    # Get VMware installation path from registry
                    import winreg
                    try:
                        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\VMware, Inc.\VMware Workstation")
                        vmware_install_path = winreg.QueryValueEx(key, "InstallPath")[0]
                        vmware_exe = os.path.join(vmware_install_path, "vmware.exe")
                        
                        if os.path.exists(vmware_exe):
                            # Start VMware in background
                            subprocess.Popen([vmware_exe], 
                                            creationflags=subprocess.CREATE_NO_WINDOW,
                                            start_new_session=True)
                            self.logger.info(f"Started VMware from {vmware_exe}")
                            
                            # Wait for VMware to initialize
                            self.vm_status_text.setText("Waiting for VMware to start...")
                            QCoreApplication.processEvents()
                            import time
                            time.sleep(5)
                        else:
                            self.logger.warning(f"VMware executable not found at {vmware_exe}")
                    except Exception as reg_error:
                        self.logger.error(f"Error getting VMware path from registry: {reg_error}")
                        # Try common installation paths
                        common_paths = [
                            r"C:\Program Files (x86)\VMware\VMware Workstation\vmware.exe",
                            r"C:\Program Files\VMware\VMware Workstation\vmware.exe"
                        ]
                        for path in common_paths:
                            if os.path.exists(path):
                                subprocess.Popen([path], 
                                                creationflags=subprocess.CREATE_NO_WINDOW,
                                                start_new_session=True)
                                self.logger.info(f"Started VMware from {path}")
                                import time
                                time.sleep(5)
                                break
            except Exception as vm_check_error:
                self.logger.error(f"Error checking VMware process: {vm_check_error}")
            
            # Start VM command
            start_cmd = [vmrun_path_clean, "-T", "ws", "start", vmx_path_clean]
            self.logger.info(f"Starting VM with command: {' '.join(start_cmd)}")
            
            # Show starting status in UI
            self.vm_status_text.setText("Starting VM (this may take a minute)...")
            self.vm_status_text.setStyleSheet("color: #f39c12; font-weight: bold;")
            QCoreApplication.processEvents()
            
            # Use QTimer instead of threading for better Qt integration
            self.start_vm_process(vmrun_path_clean, vmx_path_clean)
            
        except Exception as e:
            self.logger.error(f"Error starting VM: {e}")
            self.vm_status_text.setText(f"Error starting VM: {str(e)[:30]}...")
            self.vm_status_text.setStyleSheet("color: #e74c3c; font-weight: bold;")
    
    def start_vm_process(self, vmrun_path, vmx_path):
        """Start VM process using QProcess for better Qt integration"""
        from PyQt5.QtCore import QProcess
        
        # Create QProcess
        self.vm_process = QProcess()
        
        # Connect signals
        self.vm_process.finished.connect(lambda exit_code, exit_status: self.vm_start_finished(exit_code, exit_status, vmrun_path, vmx_path))
        self.vm_process.errorOccurred.connect(self.vm_start_error)
        
        # Start process
        self.vm_process.start(vmrun_path, ["-T", "ws", "start", vmx_path])
    
    def vm_start_finished(self, exit_code, exit_status, vmrun_path, vmx_path):
        """Handle VM start process completion"""
        from PyQt5.QtCore import QProcess
        
        if exit_status == QProcess.NormalExit and exit_code == 0:
            self.logger.info("VM started successfully")
            self.vm_status_text.setText("VM started, getting IP...")
            self.vm_status_text.setStyleSheet("color: #2ecc71; font-weight: bold;")
            
            # Start IP retrieval attempts
            self.get_vm_ip(vmrun_path, vmx_path)
        else:
            stderr = self.vm_process.readAllStandardError().data().decode('utf-8', errors='ignore')
            stdout = self.vm_process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
            self.logger.error(f"VM start failed with code {exit_code}. Stdout: {stdout}, Stderr: {stderr}")
            
            # Check if VM is already running (common error)
            if "is already running" in stdout or "is already running" in stderr:
                self.logger.info("VM is already running, proceeding to get IP")
                self.vm_status_text.setText("VM is already running, getting IP...")
                self.vm_status_text.setStyleSheet("color: #2ecc71; font-weight: bold;")
                self.get_vm_ip(vmrun_path, vmx_path)
            else:
                self.vm_status_text.setText(f"Error starting VM: Exit code {exit_code}")
                self.vm_status_text.setStyleSheet("color: #e74c3c; font-weight: bold;")
    
    def vm_start_error(self, error):
        """Handle VM start process errors"""
        from PyQt5.QtCore import QProcess
        
        error_messages = {
            QProcess.FailedToStart: "Failed to start VM process",
            QProcess.Crashed: "VM process crashed",
            QProcess.Timedout: "VM process timed out",
            QProcess.WriteError: "Write error in VM process",
            QProcess.ReadError: "Read error in VM process",
            QProcess.UnknownError: "Unknown error in VM process"
        }
        
        error_msg = error_messages.get(error, f"Process error {error}")
        self.logger.error(f"VM start error: {error_msg}")
        self.vm_status_text.setText(f"Error: {error_msg}")
        self.vm_status_text.setStyleSheet("color: #e74c3c; font-weight: bold;")

    def get_vm_ip(self, vmrun_path, vmx_path, attempt=1, max_attempts=10):
        """Get VM IP address with multiple attempts"""
        try:
            # Update status
            self.vm_ip_label.setText(f"IP Address: Checking ({attempt}/{max_attempts})...")
            self.vm_ip_label.setStyleSheet("color: #f39c12; font-size: 13px; font-weight: bold;")
            
            # Process events to update UI
            from PyQt5.QtCore import QCoreApplication
            QCoreApplication.processEvents()
            
            # IP command
            ip_cmd = [vmrun_path, "-T", "ws", "getGuestIPAddress", vmx_path, "-wait"]
            self.logger.info(f"Getting IP with command (attempt {attempt}): {' '.join(ip_cmd)}")
            
            # Run command
            ip_result = subprocess.run(
                ip_cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=30
            )
            
            ip = ip_result.stdout.strip()
            self.logger.info(f"VM IP attempt {attempt}: {ip}")
            
            if ip and ip != "0.0.0.0" and "Error" not in ip:
                # Success - save and display IP
                self.local_db.set_value("vm_ip", ip)
                self.vm_ip_label.setText(f"IP Address: {ip}")
                self.vm_ip_label.setStyleSheet("color: #2ecc71; font-size: 13px; font-weight: bold;")
                self.logger.info(f"Successfully got VM IP on attempt {attempt}: {ip}")
                self.vm_status_text.setText("VM is running")
                self.vm_status_text.setStyleSheet("color: #2ecc71; font-weight: bold;")
            elif attempt < max_attempts:
                # Try again after delay
                QTimer.singleShot(3000, lambda: self.get_vm_ip(vmrun_path, vmx_path, attempt + 1, max_attempts))
            else:
                # All attempts failed, use cached IP if available
                saved_ip = self.local_db.get_value("vm_ip")
                if saved_ip:
                    self.vm_ip_label.setText(f"IP Address: {saved_ip} (cached)")
                    self.vm_ip_label.setStyleSheet("color: #f39c12; font-size: 13px; font-weight: bold;")
                    self.logger.info(f"Using cached VM IP after failed attempts: {saved_ip}")
                else:
                    self.vm_ip_label.setText("IP Address: Could not retrieve IP")
                    self.vm_ip_label.setStyleSheet("color: #e74c3c; font-size: 13px; font-weight: bold;")
                    self.logger.warning("VM IP not available after multiple attempts")
                
                # Update VM status
                self.vm_status_text.setText("VM is running (IP unknown)")
                self.vm_status_text.setStyleSheet("color: #f39c12; font-weight: bold;")
                
        except Exception as e:
            self.logger.error(f"Error getting VM IP on attempt {attempt}: {e}")
            
            if attempt < max_attempts:
                # Try again after delay
                QTimer.singleShot(3000, lambda: self.get_vm_ip(vmrun_path, vmx_path, attempt + 1, max_attempts))
            else:
                # All attempts failed with error
                saved_ip = self.local_db.get_value("vm_ip")
                if saved_ip:
                    self.vm_ip_label.setText(f"IP Address: {saved_ip} (cached)")
                    self.vm_ip_label.setStyleSheet("color: #f39c12; font-size: 13px; font-weight: bold;")
                else:
                    self.vm_ip_label.setText("IP Address: Error getting IP")
                    self.vm_ip_label.setStyleSheet("color: #e74c3c; font-size: 13px; font-weight: bold;")

    # Remove duplicate start_vm function here
    
    def create_loading_overlay(self):
        """Create loading overlay for the dialog"""
        self.loading_overlay = LoadingOverlay(self)
        self.loading_overlay.resize(self.size())
        self.loading_overlay.hide()

    