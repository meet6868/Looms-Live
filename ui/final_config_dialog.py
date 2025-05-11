from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QLineEdit, 
    QPushButton, QDialogButtonBox, QDateEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

class FinalConfigDialog(QDialog):
    def __init__(self, config_data=None):
        super().__init__()
        self.config_data = config_data or {}
        self.password = ""
        self.start_date = ""
        self.end_date = ""
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Final Configuration")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Set Password and License Dates")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c5ecc; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Instructions
        instructions = QLabel(
            "Please set a password for the application and specify the license start and end dates."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("margin-bottom: 15px;")
        layout.addWidget(instructions)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(15)
        form_layout.setHorizontalSpacing(20)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("<b>Password:</b>", self.password_input)
        
        # Confirm Password
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("<b>Confirm Password:</b>", self.confirm_password_input)
        
        # Start Date
        self.start_date_input = QDateEdit()
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QDate.currentDate())
        form_layout.addRow("<b>License Start Date:</b>", self.start_date_input)
        
        # End Date
        self.end_date_input = QDateEdit()
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDate(QDate.currentDate().addYears(1))
        form_layout.addRow("<b>License End Date:</b>", self.end_date_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def validate_and_accept(self):
        """Validate inputs before accepting"""
        from PyQt5.QtWidgets import QMessageBox
        
        # Check passwords
        password = self.password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()
        
        if not password:
            QMessageBox.warning(self, "Missing Information", "Please enter a password.")
            return
        
        if password != confirm_password:
            QMessageBox.warning(self, "Password Mismatch", "Passwords do not match.")
            return
        
        # Check dates
        start_date = self.start_date_input.date()
        end_date = self.end_date_input.date()
        
        if start_date > end_date:
            QMessageBox.warning(self, "Invalid Dates", "End date must be after start date.")
            return
        
        # Store values
        self.password = password
        self.start_date = start_date.toString("yyyy-MM-dd")
        self.end_date = end_date.toString("yyyy-MM-dd")
        
        # Accept dialog
        self.accept()