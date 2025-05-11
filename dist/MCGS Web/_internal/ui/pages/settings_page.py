from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class SettingsPage:
    def __init__(self, main_page):
        self.main_page = main_page
        self.logger = main_page.logger

    def create_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Settings title
        title = QLabel("Settings")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)
        
        # Settings content
        content = QFrame()
        content.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Settings placeholder
        settings_label = QLabel("Settings functionality will be implemented in a future update.")
        settings_label.setAlignment(Qt.AlignCenter)
        settings_label.setStyleSheet("color: #7f8c8d; font-size: 16px;")
        content_layout.addWidget(settings_label)
        
        layout.addWidget(content)
        
        return page