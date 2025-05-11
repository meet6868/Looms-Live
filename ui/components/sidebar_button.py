from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QCursor
from utils.path_utils import get_icon_path

class SidebarButton(QPushButton):
    """Custom button for sidebar navigation"""
    def __init__(self, icon_path, text=""):
        super().__init__()
        self.text = text
        self.setIcon(QIcon(get_icon_path(icon_path)))
        self.setIconSize(QSize(35, 35))
        self.setText(text)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setMinimumHeight(50)
        self.update_style()

    def setChecked(self, checked):
        super().setChecked(checked)
        self.update_style()

    def update_style(self):
        base_style = """
            QPushButton {
                border: none;
                border-radius: 5px;
                padding: 10px;
                text-align: left;
                color: black;
                font-size: 14px;
                margin: 2px 5px;
            }
        """
        
        if self.isChecked():
            self.setStyleSheet(base_style + """
                QPushButton {
                    background-color: white;
                    padding: 10px;
                    

                }
            """)
        else:
            self.setStyleSheet(base_style + """
                QPushButton {
                    background-color: transparent;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.3);
                }
            """)

    def set_text_visible(self, visible):
        if visible:
            self.setText(self.text)
        else:
            self.setText("")