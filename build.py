import PyInstaller.__main__
import os
import shutil
from PyQt5.QtCore import QLibraryInfo
print(QLibraryInfo.location(QLibraryInfo.PluginsPath))

def build_exe():
    # Clean previous build
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')

    # Define project paths
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Ensure paths use correct separators and are absolute
    assets_path = os.path.join(base_path, 'assets', 'icons')
    ui_path = os.path.join(base_path, 'ui')
    utils_path = os.path.join(base_path, 'utils')
    database_path = os.path.join(base_path, 'database')
    core_path = os.path.join(base_path, 'core')
    icon_path = os.path.join(base_path, 'assets', 'icons', 'logo.ico')

    # Verify paths exist
    for path in [assets_path, ui_path, utils_path, database_path, core_path]:
        if not os.path.exists(path):
            os.makedirs(path)
    
    # PyInstaller arguments with corrected paths
    args = [
        os.path.join(base_path, 'main.py'),
        '--name=MCGS Web',
        '--windowed',
        f'--icon={icon_path}',
        
        # Add data files with absolute paths
        f'--add-data={assets_path};assets/icons',
        f'--add-data={ui_path};ui',
        f'--add-data={utils_path};utils',
        f'--add-data={database_path};database',
        f'--add-data={core_path};core',
        
        # Hidden imports
        '--hidden-import=PyQt5',
        '--hidden-import=sqlite3',
        '--hidden-import=requests',
        '--hidden-import=pandas',
        '--hidden-import=xlsxwriter',
        '--hidden-import=logging',
        '--hidden-import=datetime',
        '--hidden-import=json',
        '--hidden-import=sys',
        '--hidden-import=os',
        '--hidden-import=threading',
        '--hidden-import=queue',
        
        
        # Output directory (use absolute paths)
        f'--distpath={os.path.join(base_path, "dist")}',
        f'--workpath={os.path.join(base_path, "build")}',
        f'--specpath={os.path.join(base_path, "build")}',
        
        # Additional options
        '--clean',
        '--noconfirm',
        '--debug=all',  # Add debug information
    ]
    plugin_base = os.path.join(base_path, 'venv', 'Lib', 'site-packages', 'PyQt5', 'Qt5', 'plugins')

    args.extend([
        f'--add-binary={os.path.join(plugin_base, "platforms")};PyQt5/Qt5/plugins/platforms',
        f'--add-binary={os.path.join(plugin_base, "styles")};PyQt5/Qt5/plugins/styles',
    ])


    try:
        PyInstaller.__main__.run(args)
        print("Build completed! Executable can be found in the dist folder.")
    except Exception as e:
        print(f"Error during build: {str(e)}")
        print("Full error details:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    build_exe()