from PyQt5.QtWidgets import QWidget
from .pages.dashboard_page import DashboardPage
from .pages.reports_page import ReportsPage
from .pages.live_page import LivePage
from .pages.settings_page import SettingsPage
from .pages.data_page import DataPage
from .pages.help_page import HelpPage

class PageManager:
    """Manager for creating and handling different pages"""
    def __init__(self, main_page):
        self.main_page = main_page
        self.logger = main_page.logger
    
    def create_dashboard_page(self):
        """Create the dashboard page"""
        return DashboardPage(self.main_page).create_page()
    
    def create_reports_page(self):
        """Create the reports page"""
        return ReportsPage(self.main_page).create_page()
    
    def create_live_page(self):
        """Create the analytics page"""
        return LivePage(self.main_page).create_page()
    
    def create_data_page(self):
        """Create the settings page"""
        return DataPage(self.main_page).create_page()
    
    def create_help_page(self):
        """Create the help page"""
        return HelpPage(self.main_page).create_page()