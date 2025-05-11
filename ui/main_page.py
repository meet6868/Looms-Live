from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QStackedWidget, QSizePolicy, QSpacerItem, QMessageBox, QMenu,
    QApplication, QDialog
)
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap, QCursor
import os
import sys
from datetime import datetime

# Import components
from ui.components.sidebar_button import SidebarButton
from ui.components.status_manager import StatusManager
from ui.components.settings_manager import SettingsManager
from .page_manager import PageManager
from ui.components.password_dialog import PasswordDialog
from ui.components.status_dialog import StatusDialog
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt, QTimer
from ui.components.status_manager import StatusManager
from ui.components.settings_manager import SettingsManager
from ui.components.update_config_dialog import UpdateConfigDialog
from core.core_manager import CoreManager

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

class MainPage(QMainWindow):
    def __init__(self, app_controller):
        super().__init__()
        self.app_controller = app_controller
        self.admin_db = app_controller.admin_db
        self.client_db = app_controller.client_db
        self.local_db = app_controller.local_db
        self.logger = app_controller.logger
        
        # Create loading overlay
        self.loading_overlay = LoadingOverlay(self)
        
        # Sidebar properties
        self.sidebar_width = 250
        self.sidebar_collapsed_width = 85
        self.sidebar_expanded = True
        self.sidebar_buttons = []
        
        # Create UI element attributes
        self.status_indicator = None
        self.dashboard_status_label = None
        self.license_progress = None
        self.license_label = None
        self.vm_status_label = None
        self.machine_name_label = None
        
        # Initialize UI
        self.init_ui()
        
        # Initialize managers
        self.status_manager = StatusManager(self)
        self.page_manager = PageManager(self)
        self.settings_manager = SettingsManager(self)
        
        # Update pages with actual content
        
        
        # Start status check timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.status_manager.check_status)
        self.status_timer.start(90000)  # Check every minute
        self.init_status_checker()
        # Initial status check
        QTimer.singleShot(5000, self.delayed_startup)
        self.update_pages()
        # self.check_vm_status()

    def delayed_startup(self):
        """Delayed initialization of status and services"""
        try:
            self.status_manager.check_status()
            self.start_service()
        except Exception as e:
            self.logger.error(f"Error in delayed startup: {e}")

    def start_service(self):
        core_manager = CoreManager(self.local_db, self.client_db, self.logger)
        core_manager.start_monitoring()


    def show_loading(self, message="Loading..."):
        """Show loading overlay with custom message"""
        self.loading_overlay.loading_text.setText(message)
        self.loading_overlay.show()
        self.loading_overlay.raise_()
    
    def hide_loading(self):
        """Hide loading overlay"""
        self.loading_overlay.hide()
    
    def update_pages(self):
        """Update stacked widget with actual pages from page manager"""
        # Clear existing placeholder pages
        while self.stacked_widget.count() > 0:
            self.stacked_widget.removeWidget(self.stacked_widget.widget(0))
            
        # Create and add actual pages
        dashboard_page = self.page_manager.create_dashboard_page()
        reports_page = self.page_manager.create_reports_page()
        live_page = self.page_manager.create_live_page()
        settings_page = self.page_manager.create_settings_page()
        help_page = self.page_manager.create_help_page()
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(dashboard_page)
        self.stacked_widget.addWidget(reports_page)
        self.stacked_widget.addWidget(live_page)
        self.stacked_widget.addWidget(settings_page)
        self.stacked_widget.addWidget(help_page)
    
    def init_ui(self):
        """Initialize the user interface"""
        # Set window properties
        self.setWindowTitle("Loom Live")
        self.setMinimumSize(1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setStyleSheet("""
            #sidebar {
                background-color: #c3dadb;
                min-width: 70px;
                max-width: 250px;
            }
        """)
        self.sidebar.setMinimumWidth(self.sidebar_width)
        self.sidebar.setMaximumWidth(self.sidebar_width)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(10)
        
        # Logo
        logo_frame = QFrame()
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        
        logo_icon = QLabel()
        # Try different possible paths for the logo in the assets folder
        from utils.path_utils import get_icon_path
        logo_paths = [
            os.path.join(get_icon_path("logo.png")),
     
        ]
        
        logo_found = False
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                logo_pixmap = QPixmap(logo_path)
                logo_icon.setPixmap(logo_pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                logo_found = True
                break
                
        if not logo_found:
            self.logger.warning(f"Logo file not found in any of the expected locations")
            # Create a fallback colored rectangle
            fallback_pixmap = QPixmap(40, 40)
            fallback_pixmap.fill(Qt.blue)
            logo_icon.setPixmap(fallback_pixmap)
        
        # logo_layout.addWidget(logo_icon)
        self.logo_text = QLabel("Looms Live")
        self.logo_text.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.logo_text.setStyleSheet("color: black;")
        logo_layout.addWidget(self.logo_text)
        
        logo_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Toggle button
        toggle_btn = QPushButton()
        toggle_btn.setIcon(QIcon(get_icon_path("menu.png")))
        toggle_btn.setIconSize(QSize(20, 20))
        toggle_btn.setCursor(QCursor(Qt.PointingHandCursor))
        toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        toggle_btn.clicked.connect(self.toggle_sidebar)
        logo_layout.addWidget(toggle_btn)
        
        sidebar_layout.addWidget(logo_frame)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: rgba(255, 255, 255, 0.1);")
        sidebar_layout.addWidget(separator)
        
        # Navigation buttons
        self.create_sidebar_button("Dashboard", "dashboard.png", 0, sidebar_layout)
        self.create_sidebar_button("Reports", "report.png", 1, sidebar_layout)
        self.create_sidebar_button("Live", "live.png", 2, sidebar_layout)
        # self.create_sidebar_button("Settings", "setting.png", 3, sidebar_layout)
        # self.create_sidebar_button("Help", "help.png", 4, sidebar_layout)
        
        sidebar_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Logout button
        self.logout_btn = SidebarButton(get_icon_path("exit.png"), "Exit")
        self.logout_btn.clicked.connect(self.logout)
        sidebar_layout.addWidget(self.logout_btn)
        
        main_layout.addWidget(self.sidebar)
        
        # Content area
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Top bar
        top_bar = QFrame()
        top_bar.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom: 1px solid #e0e0e0;
            }
        """)
        top_bar.setFixedHeight(80)
        
        # Top bar layout modifications
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)
        
        # Company name on left
        company_name = self.local_db.get_value("company_name", "Loom")
        self.company_label = QLabel(company_name.replace("_", " "))
        self.company_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.company_label.setStyleSheet("color: #2c3e50;")
        top_layout.addWidget(self.company_label)
        
        # Add expanding spacer to push remaining items to right
        top_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Hidden loading label (right side)
        self.status_loading_label = QLabel("Checking system status...")
        self.status_loading_label.setStyleSheet("""
            QLabel {
                color: #f39c12;
                padding: 5px 10px;
                border-radius: 15px;
                background-color: #fef9e7;
                font-weight: bold;
                margin-right: 10px;
                height: 50px;
            }
        """)
        self.status_loading_label.hide()  # Initially hidden
        top_layout.addWidget(self.status_loading_label)
        
        # Status indicator (right side)
        self.status_indicator = QLabel("Checking Status...")
        self.status_indicator.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                padding: 5px 10px;
                border-radius: 15px;
                background-color: #f5f5f5;
                font-weight: bold;
                margin-right: 10px;
            }
        """)
        top_layout.addWidget(self.status_indicator)
        
        # Settings menu button (right side)
        settings_menu_btn = QPushButton()
        settings_icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "icons", "setting.png")
        if os.path.exists(settings_icon_path):
            settings_menu_btn.setIcon(QIcon(settings_icon_path))
        else:
            self.logger.warning(f"Settings icon not found at: {settings_icon_path}")
            # Create a fallback icon using a Unicode character
            settings_menu_btn.setText("⚙")
            settings_menu_btn.setFont(QFont("Segoe UI", 14))
        
        settings_menu_btn.setIconSize(QSize(20, 20))
        settings_menu_btn.setCursor(QCursor(Qt.PointingHandCursor))
        settings_menu_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 5px;
                padding: 5px;
                color: #2c3e50;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
            }
        """)
        settings_menu_btn.setToolTip("Settings")
        
        # Create dropdown menu
        settings_menu = QMenu(self)
        settings_menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 20px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #f5f5f5;
            }
        """)
        
        # Add menu actions
        status_action = settings_menu.addAction("System Status")
        status_action.triggered.connect(self.show_status_dialog)
        
        update_action = settings_menu.addAction("Update Configuration")
        update_action.triggered.connect(self.show_update_password_dialog)
        
        settings_menu_btn.setMenu(settings_menu)
        top_layout.addWidget(settings_menu_btn)
        
        content_layout.addWidget(top_bar)
        
        # Stacked widget for pages
        self.stacked_widget = QStackedWidget()
        
        # Create temporary placeholder pages (will be replaced later)
        for i in range(5):  # Dashboard, Reports, Live, Settings, Help
            placeholder = QWidget()
            placeholder_layout = QVBoxLayout(placeholder)
            placeholder_label = QLabel(f"Loading page {i+1}...")
            placeholder_label.setAlignment(Qt.AlignCenter)
            placeholder_layout.addWidget(placeholder_label)
            self.stacked_widget.addWidget(placeholder)
        
        content_layout.addWidget(self.stacked_widget)
        
        main_layout.addWidget(content_container)
    
    def create_sidebar_button(self, text, icon_path, page_index, layout):
        """Create a sidebar button and add it to the layout"""
        button = SidebarButton(icon_path, text)
        button.clicked.connect(lambda: self.switch_page(page_index))
        layout.addWidget(button)
        self.sidebar_buttons.append(button)
        
        # Set the first button as active
        if page_index == 0:
            button.setChecked(True)
    
    def switch_page(self, index):
        """Switch to the specified page index"""
        # Update button states
        for i, button in enumerate(self.sidebar_buttons):
            button.setChecked(i == index)
        
            if hasattr(button, 'set_active'):
                button.set_active(i == index)        
        # Switch page
        self.stacked_widget.setCurrentIndex(index)
    
    def toggle_sidebar(self):
        """Toggle sidebar between expanded and collapsed states"""
        target_width = self.sidebar_collapsed_width if self.sidebar_expanded else self.sidebar_width
        
        # Create animation
        self.animation = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self.animation.setDuration(250)
        self.animation.setStartValue(self.sidebar.width())
        self.animation.setEndValue(target_width)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Also animate maximum width
        self.animation2 = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.animation2.setDuration(250)
        self.animation2.setStartValue(self.sidebar.width())
        self.animation2.setEndValue(target_width)
        self.animation2.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Start animations
        self.animation.start()
        self.animation2.start()
        
        # Update state
        self.sidebar_expanded = not self.sidebar_expanded
        
        # Toggle logo text visibility
        if hasattr(self, 'logo_text'):
            self.logo_text.setVisible(self.sidebar_expanded)
        
        # Update button text visibility
        for button in self.sidebar_buttons:
            button.set_text_visible(self.sidebar_expanded)
        
        # Update exit button text visibility
        if hasattr(self, 'logout_btn'):
            self.logout_btn.set_text_visible(self.sidebar_expanded)
    
    def logout(self):
        """Log out and return to login page"""
        reply = QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Stop status timer
            self.status_timer.stop()
            QApplication.quit()
            
            # Return to login page
            # self.app_controller.show_login_page()
    
    def show_status_dialog(self):
        """Show system status dialog"""
        try:
            # Show loading label
            self.status_loading_label.setText("Loading status information...")
            self.status_loading_label.show()
            
            # Use QTimer to allow UI update
            QTimer.singleShot(100, self._show_status_dialog)
            
        except Exception as e:
            self.logger.error(f"Error showing status dialog from main page: {e}")
            QMessageBox.warning(self, "Error", f"Could not display status information: {e}")
            self.status_loading_label.hide()

    def _show_status_dialog(self):
        """Internal method to show status dialog after loading label is shown"""
        try:
            self.status_manager.show_status_dialog()
            # Hide loading label after dialog is shown
            self.status_loading_label.hide()
        except Exception as e:
            self.logger.error(f"Error in _show_status_dialog: {e}")
            self.status_loading_label.hide()

    def show_update_password_dialog(self):
        """Show configuration update dialog with password protection"""
        try:
            if PasswordDialog.get_password(self, self.admin_db, "Authentication Required", "Enter admin password to update configuration:"):
                from ui.components.update_config_dialog import UpdateConfigDialog
                dialog = UpdateConfigDialog(self)

                if dialog.exec_() == QDialog.Accepted:
                    # Refresh status after configuration update
                    self.status_manager.check_status()
                    QMessageBox.information(self, "Success", "Configuration updated successfully")
                    company_name = self.local_db.get_value("company_name", "Loom")
                    self.company_label.setText(company_name.replace("_", " "))
        except Exception as e:
            self.logger.error(f"Error showing update dialog: {e}")
            QMessageBox.warning(self, "Error", f"Could not show update dialog: {e}")
        
        # Remove the show_configuration_update method as it's now in the separate file
    
    

    def check_vm_status(self):
        """Check VM status and update UI"""
        try:
            # Get VM path from client_config table
            client_config = self.local_db.get_client_config()
            vm_path = client_config.get("vm_path", "")
            system_path = client_config.get("system_path", "")
            
            if not vm_path:
                if self.vm_status_label:
                    self.vm_status_label.setText("Not Configured")
                    self.vm_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                return
            
            # Create a VM check thread
            from ui.worker_threads import VMCheckThread
            from utils.vm_manager import VMManager
            
            vm_manager = VMManager(vm_path)
            self.vm_check_thread = VMCheckThread(vm_manager,system_path )
            self.vm_check_thread.check_result.connect(self.update_vm_status)
            self.vm_check_thread.start()
            
            # Update status to checking
            if self.vm_status_label:
                self.vm_status_label.setText("Checking...")
                self.vm_status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
                
        except Exception as e:
            self.logger.error(f"Error checking VM status: {e}")
            if self.vm_status_label:
                self.vm_status_label.setText("Error")
                self.vm_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
    
    def update_vm_status(self, success, message, ip):
        """Update VM status in UI based on check result"""
        try:
            if success:
                if ip:
                    if self.vm_status_label:
                        self.vm_status_label.setText(f"Running ({ip})")
                        self.vm_status_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
                else:
                    if self.vm_status_label:
                        self.vm_status_label.setText("Running (IP Unknown)")
                        self.vm_status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
            else:
                if self.vm_status_label:
                    self.vm_status_label.setText("Not Running")
                    self.vm_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                    
            # Save IP to local database if available
            if ip:
                self.local_db.set_value("vm_ip", ip)
                
        except Exception as e:
            self.logger.error(f"Error updating VM status: {e}")
            if self.vm_status_label:
                self.vm_status_label.setText("Error")
                self.vm_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        
        # Initialize status checker thread
        self.init_status_checker()
        
    def init_status_checker(self):
        """Initialize and start status checker thread"""
        try:
            from utils.vm_manager import VMManager
            self.vm_manager = VMManager()
            
            # Stop existing thread if running
            if hasattr(self, 'status_thread') and self.status_thread.isRunning():
                self.status_thread.stop()
                self.status_thread.wait()
            
            # Create and start status thread
            from ui.worker_threads import StatusCheckerThread
            self.status_thread = StatusCheckerThread(
                self.admin_db,
                self.client_db,
                self.local_db,
                self.vm_manager
            )
            
            # Connect signal before starting thread
            self.status_thread.status_updated.connect(self.update_status_ui)
            
            # Debug logging
            self.logger.info("Starting status checker thread")
            self.status_thread.start()
            
            # Store thread reference
            if hasattr(self.app_controller, 'active_threads'):
                if not hasattr(self.app_controller, '_active_threads'):
                    self.app_controller._active_threads = []
                self.app_controller._active_threads.append(self.status_thread)
                
        except Exception as e:
            self.logger.error(f"Error initializing status checker: {e}")
            
    def update_status_ui(self, status_data):
        """Update UI with status data from background thread"""
        try:
            # Log received status data
            # self.logger.info(f"Received status data: {status_data}")
            
            # Update system status indicator
            admin_connected = status_data.get('admin_connected', False)
            client_connected = status_data.get('client_connected', False)
            
            if admin_connected and client_connected:
                self.status_indicator.setText("System Online")
                self.status_indicator.setStyleSheet("""
                    QLabel {
                        color: white;
                        padding: 5px 10px;
                        border-radius: 15px;
                        background-color: #2ecc71;
                        font-weight: bold;
                    }
                """)
            elif admin_connected or client_connected:
                self.status_indicator.setText("Partial Connection")
                self.status_indicator.setStyleSheet("""
                    QLabel {
                        color: white;
                        padding: 5px 10px;
                        border-radius: 15px;
                        background-color: #f39c12;
                        font-weight: bold;
                    }
                """)
            else:
                self.status_indicator.setText("System Offline")
                self.status_indicator.setStyleSheet("""
                    QLabel {
                        color: white;
                        padding: 5px 10px;
                        border-radius: 15px;
                        background-color: #e74c3c;
                        font-weight: bold;
                    }
                """)
            
            # Update VM status if available
            if hasattr(self, 'vm_status_label') and self.vm_status_label:
                vm_status = status_data.get('vm_status', False)
                vm_ip = status_data.get('vm_ip', None)
                
                if vm_status and vm_ip:
                    self.vm_status_label.setText(f"Running ({vm_ip})")
                    self.vm_status_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
                elif vm_status:
                    self.vm_status_label.setText("Running (IP Unknown)")
                    self.vm_status_label.setStyleSheet("color: #f39c12; font-weight: bold;")
                else:
                    self.vm_status_label.setText("Not Running")
                    self.vm_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            
        except Exception as e:
            self.logger.error(f"Error updating status UI: {e}")
            if self.status_indicator:
                self.status_indicator.setText("Status Error")
                self.status_indicator.setStyleSheet("""
                    QLabel {
                        color: white;
                        padding: 5px 10px;
                        border-radius: 15px;
                        background-color: #e74c3c;
                        font-weight: bold;
                    }
                """)