import os
import sys

def get_db_path():
    """Get the database file path"""
    if getattr(sys, 'frozen', False):
        # If running as executable
        base_dir = os.path.join(os.getenv("APPDATA"), "Looms Live")
    else:
        # If running from source
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # base_dir = os.path.join(os.getenv("APPDATA"), "Looms Live")
    return os.path.join(base_dir, 'loom_live.db')

def get_app_root():
    """Get the root directory of the application"""
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle (exe)
        return sys._MEIPASS
    else:
        # If the application is run from Python interpreter
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_resource_path(*paths):
    """Get absolute path for resources (UI files, images, etc.)"""
    return os.path.join(get_app_root(), *paths)

def get_data_path(*paths):
    """Get path for data files (database, logs, etc.)"""
    if getattr(sys, 'frozen', False):
        # When bundled, store data in user's AppData folder
        app_data = os.path.join(os.environ['APPDATA'], 'MCGS Web')
        if not os.path.exists(app_data):
            os.makedirs(app_data)
        return os.path.join(app_data, *paths)
    else:
        # During development, store in project directory
        return os.path.join(get_app_root(), 'data', *paths)


def get_icon_path(icon_name):
    """Get the absolute path for icons"""
    if getattr(sys, 'frozen', False):
        # If running as executable
        base_path = sys._MEIPASS
    else:
        # If running from source
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'MCGS Web')
    
    icon_path = os.path.join(base_path, 'assets', 'icons', icon_name)
    
    # Ensure the icons directory exists
    if not os.path.exists(os.path.dirname(icon_path)):
        os.makedirs(os.path.dirname(icon_path), exist_ok=True)
    
    return icon_path