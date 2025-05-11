from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class HelpPage:
    def __init__(self, main_page):
        self.main_page = main_page
        self.logger = main_page.logger

    def create_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Help title
        title = QLabel("Help & Support")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet("color: #2c3e50;")
        layout.addWidget(title)
        
        # Help content
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
        
        # Help information
        help_title = QLabel("Need Help?")
        help_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        help_title.setStyleSheet("color: #2c3e50;")
        content_layout.addWidget(help_title)
        
        help_text = QLabel("If you need assistance with MCGS Web, please contact our support team:")
        help_text.setWordWrap(True)
        content_layout.addWidget(help_text)
        
        contact_info = QLabel("Email: support@mcgs.com\nPhone: +1-800-MCGS-HELP")
        contact_info.setStyleSheet("font-weight: bold; margin-top: 10px;")
        content_layout.addWidget(contact_info)
        
        # Documentation section
        docs_title = QLabel("Documentation")
        docs_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        docs_title.setStyleSheet("color: #2c3e50; margin-top: 20px;")
        content_layout.addWidget(docs_title)
        
        docs_text = QLabel("Access our comprehensive documentation to learn more about MCGS Web features and functionality.")
        docs_text.setWordWrap(True)
        content_layout.addWidget(docs_text)
        
        # FAQ section
        faq_title = QLabel("Frequently Asked Questions")
        faq_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        faq_title.setStyleSheet("color: #2c3e50; margin-top: 20px;")
        content_layout.addWidget(faq_title)
        
        faq_text = QLabel("Find answers to common questions about MCGS Web.")
        faq_text.setWordWrap(True)
        content_layout.addWidget(faq_text)
        
        layout.addWidget(content)
        
        return page