from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QPixmap

class WelcomePage(QWidget):
    def __init__(self, app_controller):
        super().__init__()
        self.app_controller = app_controller
        self.init_ui()
    
    def init_ui(self):
        # Set window properties
        self.setWindowTitle("Welcome to Loom Live")
        self.setMinimumWidth(1000)  # Increased width
        
        # Apply stylesheet
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f6ff;
                color: #2c3e50;
                font-family: 'Segoe UI', Arial;
            }
            QPushButton {
                background-color: #4a7bff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;  /* Reduced padding */
                font-weight: bold;
                font-size: 13px;  /* Smaller font */
            }
            QPushButton:hover {
                background-color: #3a6aee;
            }
            QPushButton#getStartedBtn {
                background-color: #2ecc71;
                font-size: 14px;  /* Smaller font */
                padding: 12px 24px;  /* Reduced padding */
            }
            QPushButton#getStartedBtn:hover {
                background-color: #27ae60;
            }
        """)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header with gradient background
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                      stop:0 #2c5ecc, stop:1 #4a7bff);
            padding: 25px;  /* Reduced padding */
        """)
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(30, 25, 30, 25)  # Reduced margins
        
        # Logo (if available)
        logo_layout = QHBoxLayout()
        
        try:
            logo_label = QLabel()
            logo_pixmap = QPixmap("icons/logo.png")
            logo_label.setPixmap(logo_pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))  # Smaller logo
            logo_layout.addWidget(logo_label)
        except:
            # If logo not available, use text instead
            logo_text = QLabel("LOOM LIVE")
            logo_text.setFont(QFont("Segoe UI", 20, QFont.Bold))  # Smaller font
            logo_text.setStyleSheet("color: white;")
            logo_layout.addWidget(logo_text)
        
        logo_layout.addStretch()
        header_layout.addLayout(logo_layout)
        
        # Add some space (reduced)
        header_layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # Welcome text
        welcome_label = QLabel("Welcome to Loom Live")
        welcome_label.setFont(QFont("Segoe UI", 28, QFont.Bold))  # Smaller font
        welcome_label.setStyleSheet("color: white;")
        header_layout.addWidget(welcome_label)
        
        # Subtitle
        subtitle_label = QLabel("Your intelligent virtual machine management solution")
        subtitle_label.setFont(QFont("Segoe UI", 14))  # Smaller font
        subtitle_label.setStyleSheet("color: #e0e0ff;")
        header_layout.addWidget(subtitle_label)
        
        main_layout.addWidget(header_widget, 1)
        
        # Content area
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            background-color: #f0f6ff;
            padding: 25px;  /* Reduced padding */
        """)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 25, 30, 25)  # Reduced margins
        content_layout.setSpacing(20)  # Reduced spacing
        
        # Features section
        features_label = QLabel("Key Features")
        features_label.setFont(QFont("Segoe UI", 18, QFont.Bold))  # Smaller font
        features_label.setStyleSheet("color: #2c5ecc;")
        content_layout.addWidget(features_label)
        
        # Feature items in a grid layout (2x2)
        features_grid = QHBoxLayout()
        features_grid.setSpacing(15)  # Reduced spacing
        
        # Feature items
        features = [
            ("🖥️", "Virtual Machine Integration", "Seamlessly connect and manage your virtual machines"),
            ("🔍", "OCR Capabilities", "Extract text from images with advanced OCR technology"),
            ("🔒", "Secure Database", "Store and retrieve data securely with Supabase integration"),
            ("📊", "Real-time Monitoring", "Monitor your system performance in real-time")
        ]
        
        # Create two columns for features
        left_column = QVBoxLayout()
        right_column = QVBoxLayout()
        
        for i, (icon, title, description) in enumerate(features):
            feature_widget = QWidget()
            feature_widget.setStyleSheet("""
                background-color: white;
                border-radius: 8px;
                padding: 15px;  /* Increased padding */
            """)
            feature_layout = QHBoxLayout(feature_widget)
            feature_layout.setContentsMargins(15, 15, 15, 15)  # Increased margins
            
            # Create a fixed-size container for the icon
            icon_container = QWidget()
            icon_container.setFixedSize(45, 45)  # Fixed size container
            icon_container_layout = QVBoxLayout(icon_container)
            icon_container_layout.setContentsMargins(0, 0, 0, 0)
            
            # Icon
            icon_label = QLabel(icon)
            icon_label.setFont(QFont("Segoe UI", 20))
            icon_label.setAlignment(Qt.AlignCenter)
            icon_container_layout.addWidget(icon_label)
            
            feature_layout.addWidget(icon_container)
            
            # Text
            text_layout = QVBoxLayout()
            text_layout.setSpacing(5)  # Reduced spacing
            
            title_label = QLabel(title)
            title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))  # Smaller font
            text_layout.addWidget(title_label)
            
            desc_label = QLabel(description)
            desc_label.setFont(QFont("Segoe UI", 9))  # Smaller font
            desc_label.setWordWrap(True)
            text_layout.addWidget(desc_label)
            
            feature_layout.addLayout(text_layout)
            
            # Add to appropriate column
            if i < 2:
                left_column.addWidget(feature_widget)
            else:
                right_column.addWidget(feature_widget)
        
        features_grid.addLayout(left_column)
        features_grid.addLayout(right_column)
        content_layout.addLayout(features_grid)
        
        # Get started button
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        
        get_started_btn = QPushButton("Get Started")
        get_started_btn.setObjectName("getStartedBtn")
        get_started_btn.setFixedWidth(200)
        get_started_btn.setFixedHeight(45)
        get_started_btn.setStyleSheet("""
            QPushButton#getStartedBtn {
                background-color: #2ecc71;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
                padding: 12px 24px;
            }
            QPushButton#getStartedBtn:hover {
                background-color: #27ae60;
            }
        """)
        get_started_btn.clicked.connect(self.on_get_started_clicked)
        button_layout.addWidget(get_started_btn)
        
        button_layout.addStretch(1)
        
        # Add some space before the button
        content_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        content_layout.addLayout(button_layout)
        
        # Add some space after the button
        content_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        main_layout.addWidget(content_widget, 2)
        
        # Set the main layout
        self.setLayout(main_layout)
    
    def on_get_started_clicked(self):
        # Mark first time launch as false
        self.app_controller.local_db.set_value("first_time_launch", "false")
        
        # Switch to configure page
        self.app_controller.switch_to_configure_page()