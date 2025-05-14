import sqlite3
import os
import logging
from datetime import datetime
from utils.path_utils import get_db_path

class LocalDatabase:
    def __init__(self, db_path="loom_live.db"):
        self.db_path = get_db_path()
        self.logger = logging.getLogger("LoomLive")
        
    
    def initialize(self):
        """Initialize the database and create tables if they don't exist"""
        self.logger.info("Initializing local database")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create settings table for key-value pairs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            # Create client_config table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS client_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT,
                    client_email TEXT,
                    client_url TEXT,
                    client_key TEXT,
                    vm_path TEXT,
                    system_path TEXT,
                    ip TEXT,
                    tesseract_path TEXT,
                    password TEXT,
                    start_date TEXT,
                    end_date TEXT
                )
            ''')
            
            # Create admin_config table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_url TEXT,
                    admin_key TEXT
                )
            ''')
            
            # Create connection_status table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS connection_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_db_connected INTEGER,
                    client_db_connected INTEGER,
                    vm_running INTEGER,
                    last_checked TEXT
                )
            ''')
            
            # Create tabs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tabs (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Create Machine data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS machine_data (
                    date TEXT,
                    Device_Name TEXT,
                    Loom_Num TEXT,
                    A_start TEXT,
                    A_End TEXT,
                    A_Production_FabricLength REAL,
                    A_Production_Quantity INTEGER,
                    A_Speed REAL,
                    A_Efficiency REAL,
                    A_TotalTime INTEGER,
                    A_H1Time INTEGER,
                    A_H2Time INTEGER,
                    A_WarpTime INTEGER,
                    A_OtherTime INTEGER,
                    B_start TEXT,
                    B_End TEXT,
                    B_Production_FabricLength REAL,
                    B_Production_Quantity INTEGER,
                    B_Speed REAL,
                    B_Efficiency REAL,
                    B_TotalTime INTEGER,
                    B_H1Time INTEGER,
                    B_H2Time INTEGER,
                    B_WarpTime INTEGER,
                    B_OtherTime INTEGER,
                    Total_Production_FabricLength REAL,
                    Total_Production_Quantity INTEGER,
                    Avg_Speed REAL,
                    Avg_Efficiency REAL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (date, Device_Name, Loom_Num)
                );
            ''')

            # Create temp data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS temp_data (
                    Device_Name TEXT,
                    Loom_Num TEXT PRIMARY KEY,
                    Weaving_Length TEXT,
                    Cut_Length TEXT,
                    Weaving_Forecast TEXT,
                    Warp_Remain TEXT,
                    Warp_Length TEXT,
                    Warp_Forecast TEXT,
                    Production_Quantity INTEGER,
                    Production_FabricLength REAL,
                    Speed REAL,
                    Efficiency REAL,
                    Pre_Production_Quantity INTEGER,
                    Pre_Production_FabricLength REAL,
                    Pre_Speed REAL,
                    Pre_Efficiency REAL,
                    Shift TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')   
            # Create tab_views table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tab_views (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')


            cursor.execute('''
               CREATE TABLE IF NOT EXISTS machine_data_status (
                    loom_num TEXT,
                    date TEXT,
                    shift_a BOOLEAN DEFAULT FALSE,
                    shift_b BOOLEAN DEFAULT FALSE,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (loom_num, date)
                )
            ''')


            
            conn.commit()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS core (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')


            
            # Set default values if this is the first run
            cursor.execute("SELECT COUNT(*) FROM settings WHERE key = 'first_time_launch'")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", 
                              ("first_time_launch", "true"))
            
            conn.commit()

            self.set_core_default_values()
            self.set_setting_default_values()

            self.logger.info("Local database initialized successfully")
            
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization error: {e}")
        finally:
            if conn:
                conn.close()
    
    def set_value(self, key, value):
        """Set a key-value pair in the settings table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", 
                          (key, value))
            
            conn.commit()
            self.logger.debug(f"Set value: {key}={value}")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Error setting value: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_value(self, key, default=None):
        """Get a value from the settings table by key"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            return default
        except sqlite3.Error as e:
            self.logger.error(f"Error getting value: {e}")
            return default
        finally:
            if conn:
                conn.close()
    
    def set_client_config(self, config_data):
        """Save client configuration data to local database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if we're updating or inserting
            cursor.execute("SELECT COUNT(*) FROM client_config")
            if cursor.fetchone()[0] > 0:
                # Update existing record
                cursor.execute('''
                    UPDATE client_config SET 
                    company_name = ?, client_email = ?, client_url = ?, client_key = ?,
                    vm_path = ?, system_path = ?,ip=? ,tesseract_path = ?,
                    password = ?, start_date = ?, end_date = ?
                    WHERE id = 1
                ''', (
                    config_data.get('company_name', ''),
                    config_data.get('client_email', ''),
                    config_data.get('client_url', ''),
                    config_data.get('client_key', ''),
                    config_data.get('vm_path', ''),
                    config_data.get('system_path', ''),
                    config_data.get('ip', ''),
                    config_data.get('tesseract_path', ''),
                    config_data.get('password', ''),
                    config_data.get('start_date', ''),
                    config_data.get('end_date', '')
                ))
            else:
                # Insert new record
                cursor.execute('''
                    INSERT INTO client_config (
                    company_name, client_email, client_url, client_key,
                    vm_path, system_path,ip, tesseract_path,
                    password, start_date, end_date)
                    VALUES (?, ?, ?, ?,?, ?, ?, ?, ?, ?, ?)
                ''', (
                    config_data.get('company_name', ''),
                    config_data.get('client_email', ''),
                    config_data.get('client_url', ''),
                    config_data.get('client_key', ''),
                    config_data.get('vm_path', ''),
                    config_data.get('system_path', ''),
                    config_data.get('ip', ''),
                    config_data.get('tesseract_path', ''),
                    config_data.get('password', ''),
                    config_data.get('start_date', ''),
                    config_data.get('end_date', '')
                ))
            
            conn.commit()
            self.logger.info("Client configuration saved successfully to local database")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Error saving client config to local database: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_client_config(self):
        """Get client configuration data"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM client_config LIMIT 1")
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            return {}
        except sqlite3.Error as e:
            self.logger.error(f"Error getting client config: {e}")
            return {}
        finally:
            if conn:
                conn.close()
    
    def save_admin_config(self, admin_url, admin_key):
        """Save admin database configuration"""
        try:
            # Validate and clean the admin_url
            if admin_url:
                # Remove any whitespace, newlines or carriage returns
                admin_url = admin_url.strip()
                
                # Ensure URL starts with http:// or https://
                if not (admin_url.startswith('http://') or admin_url.startswith('https://')):
                    admin_url = 'https://' + admin_url
                    
                # Validate URL format (basic check)
                if '\n' in admin_url or '\r' in admin_url:
                    admin_url = admin_url.split('\n')[0].strip()
                    self.logger.warning(f"Admin URL contained newlines, cleaned to: {admin_url}")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if the admin_config table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admin_config'")
            if not cursor.fetchone():
                # Create the table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE admin_config (
                        id INTEGER PRIMARY KEY,
                        admin_url TEXT,
                        admin_key TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            
            # Check if we're updating or inserting
            cursor.execute("SELECT COUNT(*) FROM admin_config")
            
            if cursor.fetchone()[0] > 0:
                # Simple update without using updated_at column
                cursor.execute(
                    "UPDATE admin_config SET admin_url = ?, admin_key = ?",
                    (admin_url, admin_key)
                )
            else:
                # Simple insert without using updated_at column
                cursor.execute(
                    "INSERT INTO admin_config (admin_url, admin_key) VALUES (?, ?)",
                    (admin_url, admin_key)
                )
            
            conn.commit()
            self.logger.info("Admin database configuration saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error saving admin credentials to local database: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_admin_config(self):
        """Get admin database configuration"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT admin_url, admin_key FROM admin_config LIMIT 1")
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            return {"admin_url": "", "admin_key": ""}
        except sqlite3.Error as e:
            self.logger.error(f"Error getting admin config: {e}")
            return {"admin_url": "", "admin_key": ""}
        finally:
            if conn:
                conn.close()
    
    def update_connection_status(self, admin_connected, client_connected, vm_running):
        """Update connection status information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Check if we're updating or inserting
            cursor.execute("SELECT COUNT(*) FROM connection_status")
            if cursor.fetchone()[0] > 0:
                # Update existing record
                cursor.execute('''
                    UPDATE connection_status SET 
                    admin_db_connected = ?, client_db_connected = ?, 
                    vm_running = ?, last_checked = ?
                    WHERE id = 1
                ''', (admin_connected, client_connected, vm_running, now))
            else:
                # Insert new record
                cursor.execute('''
                    INSERT INTO connection_status 
                    (admin_db_connected, client_db_connected, vm_running, last_checked)
                    VALUES (?, ?, ?, ?)
                ''', (admin_connected, client_connected, vm_running, now))
            
            conn.commit()
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Error updating connection status: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_connection_status(self):
        """Get connection status information"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM connection_status LIMIT 1")
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            return {
                "admin_db_connected": 0,
                "client_db_connected": 0,
                "vm_running": 0,
                "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except sqlite3.Error as e:
            self.logger.error(f"Error getting connection status: {e}")
            return {
                "admin_db_connected": 0,
                "client_db_connected": 0,
                "vm_running": 0,
                "last_checked": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        finally:
            if conn:
                conn.close()
    
    def clear_client_config(self):
        """Clear all data from client_config table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM client_config")
            conn.commit()
            
            self.logger.info("Client configuration cleared successfully")
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Error clearing client config: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def set_core_value(self, key, value):
        """Set value in core table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT OR REPLACE INTO core (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, value,now))
            conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error setting core value: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_core_value(self, key):
        """Get value from core table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM core WHERE key = ?", (key,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Error getting core value: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()

    def set_core_default_values(self):
        """Set default values for core table"""
        default_values = {
            "client_service_status": "Unknown",
            "admin_service_status": "Unknown",
            "client_login_status": "Unknown",   
        }
        for key, value in default_values.items():
            self.set_core_value(key, value)

    def set_setting_default_values(self):
        """Set default values for settings table"""
        default_values = {
            "admin_connected": "0",
            "client_connected": "0",
            "vm_running": "0",
        }
        for key, value in default_values.items():
            self.set_value(key, value)

    def set_tab(self, key, value):
        """Set value in tabs table with automatic timestamp update"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Use UTC timestamp for consistency
            current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                INSERT OR REPLACE INTO tabs (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, value, current_time))
            
            conn.commit()
            conn.close()
            self.logger.debug(f"Tab value set - Key: {key}, Time: {current_time}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting tab value for {key}: {str(e)}")
            return False

    def get_pending_screenshots(self):
        """Get screenshots that haven't been uploaded to client DB"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all screenshots, prioritizing machine tabs
            cursor.execute('''
                SELECT key, value, updated_at 
                FROM tab_views 
                WHERE key LIKE 'machine_%' OR key IN ('main_tab', 'machine_tab', 'report_tab', 'overview_tab')
                ORDER BY 
                    CASE 
                        WHEN key LIKE 'machine_M%' THEN 1
                        ELSE 2
                    END,
                    updated_at DESC
            ''')
            
            results = cursor.fetchall()
            
            # Log the number of screenshots found
            if results:
                self.logger.info(f"Found {len(results)} screenshots to process")
                self.logger.debug(f"Screenshot keys: {[r[0] for r in results]}")
            else:
                self.logger.warning("No screenshots found in tab_views")
            
            conn.close()
            return results
            
        except Exception as e:
            self.logger.error(f"Error getting pending screenshots: {str(e)}")
            return []

    def set_tab_view(self, key, screenshot_data, timestamp=None):
        """Store screenshot data in base64 format"""
        try:
            import base64
            
            # If screenshot_data is bytes (from selenium), encode it
            if isinstance(screenshot_data, bytes):
                screenshot_data = base64.b64encode(screenshot_data).decode('utf-8')
            
            if timestamp is None:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verify data before storing
            if not screenshot_data:
                self.logger.error(f"Empty screenshot data for {key}")
                return False
                
            cursor.execute('''
                INSERT OR REPLACE INTO tab_views (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, screenshot_data, timestamp))
            
            conn.commit()
            conn.close()
            
            # Log successful storage
            self.logger.debug(f"Stored screenshot for {key} at {timestamp}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting tab view for {key}: {str(e)}")
            return False

    def get_tab_view(self, key):
        """Get the latest view data (image and timestamp) for a specific key"""
        conn = None # Initialize conn to None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT value, updated_at 
                FROM tab_views 
                WHERE key = ? 
                ORDER BY updated_at DESC LIMIT 1
            """, (key,))
            result = cursor.fetchone()
            
            if result:
                # Return a dictionary matching the expected format
                return {'image_data': result[0], 'updated_at': result[1]}
            else:
                self.logger.debug(f"No tab view found for key: {key}")
                return None # Return None if no data found for the key
            
        except sqlite3.Error as e:
            self.logger.error(f"Error getting tab view for key '{key}': {e}")
            return None # Return None on database error
        except Exception as e:
            self.logger.error(f"Unexpected error getting tab view for key '{key}': {e}")
            return None # Return None on other errors
        finally:
            if conn:
                conn.close()

    def mark_screenshot_uploaded(self, key, timestamp):
        """Update screenshot timestamp after upload"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            new_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                UPDATE tab_views 
                SET updated_at = ? 
                WHERE key = ? AND updated_at = ?
            ''', (new_timestamp, key, timestamp))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"Error updating screenshot timestamp: {str(e)}")
            return False

    def get_tab(self, key):
        """Get value from tabs table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM tabs WHERE key = ?', (key,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Error getting tab value for {key}: {str(e)}")
            return None

    def get_all_tabs(self):
        """Get all tab handles from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT key, value FROM tabs WHERE key NOT LIKE "url_%"')
            results = cursor.fetchall()
            conn.close()
            return {key: value for key, value in results}
        except Exception as e:
            self.logger.error(f"Error getting all tabs: {str(e)}")
            return {}

    def get_machine_view(self, machine_key):
        """Get the latest view data for a specific machine"""
        try:

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT value, updated_at 
                FROM tab_views 
                WHERE key = ? 
                ORDER BY updated_at DESC LIMIT 1
            """, (machine_key,))
            result = cursor.fetchone()
            
            if result:
                return {'image_data': result[0], 'updated_at': result[1]}
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting machine view for {machine_key}: {str(e)}")
            return None

    def get_machine_list(self):
        try:
            # Ensure database is initialized
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT key 
                FROM tab_views 
                WHERE key LIKE 'machine_M%'
                ORDER BY key ASC
            """)
            
            machines = [row[0] for row in cursor.fetchall()]
            return machines
            
        except Exception as e:
            self.logger.error(f"Error getting machine list: {str(e)}")
            return []

    
    def get_machine_data_status(self, loom_num, date):
        query = "SELECT * FROM machine_data_status WHERE loom_num = ? AND date = ?"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query, (loom_num, date))
        result = cursor.fetchone()
        if result:
            return {
                'loom_num': result[0],
                'date': result[1],
                'shift_a': bool(result[2]),
                'shift_b': bool(result[3]),
                'updated_at': result[4]
            }
        return None
    
    def update_machine_data_status(self, loom_num, date, shift, status):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        shift_column = f'shift_{shift.lower()}'
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = f"""
        INSERT INTO machine_data_status (loom_num, date, {shift_column}, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(loom_num, date) DO UPDATE SET
        {shift_column} = ?,
        updated_at = ?
        """
        cursor.execute(query, (loom_num, date, status, current_time, status, current_time))
        conn.commit()
    
    def store_machine_data(self, data):
        try:
            loom_num = data.get('Loom_Num')
            # Add safety checks for required data
            if not all(key in data for key in ['Start', 'Shift', 'End', 'Production_FabricLength', 
                                             'Production_Quantity', 'Speed', 'Efficiency', 
                                             'TotalTimes', 'H1Times', 'H2Times', 'WarpTimes', 'OtherTimes']):
                self.logger.error("Missing required data fields")
                return False

            # Safely get values with default empty lists
            shift_time = datetime.strptime(data.get('Start', [[],['']])[1], '%Y-%m-%d %H:%M:%S')
            current_date = shift_time.strftime('%Y-%m-%d')
            current_shift = data.get('Shift', [[],['']])[1]
            
            # Prepare shift-specific data with safe access
            shift_prefix = f"{current_shift}_"
            base_data = {
                'date': current_date,
                'Device_Name': data.get('Device_Name', ''),
                'Loom_Num': loom_num,
                f'{shift_prefix}start': data.get('Start', [[],['']])[1],
                f'{shift_prefix}End': data.get('End', [[],['']])[1],
                f'{shift_prefix}Production_FabricLength': data.get('Production_FabricLength', [[],['0']])[1],
                f'{shift_prefix}Production_Quantity': data.get('Production_Quantity', [[],['0']])[1],
                f'{shift_prefix}Speed': data.get('Speed', [[],['0']])[1],
                f'{shift_prefix}Efficiency': data.get('Efficiency', [[],['0']])[1],
                f'{shift_prefix}TotalTime': data.get('TotalTimes', [[],['0']])[1],
                f'{shift_prefix}H1Time': data.get('H1Times', [[],['0']])[1],
                f'{shift_prefix}H2Time': data.get('H2Times', [[],['0']])[1],
                f'{shift_prefix}WarpTime': data.get('WarpTimes', [[],['0']])[1],
                f'{shift_prefix}OtherTime': data.get('OtherTimes', [[],['0']])[1]
            }
    
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get column names from the table
            cursor.execute("PRAGMA table_info(machine_data)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Check if record exists
            cursor.execute("SELECT * FROM machine_data WHERE date = ? AND Loom_Num = ?", 
                         (current_date, loom_num))
            existing_row = cursor.fetchone()
    
            if existing_row:
                # Convert tuple to dictionary using column names
                existing_data = dict(zip(columns, existing_row))
                print(existing_data,"*"*10,data,"*"*100)  
                # Update existing record
                set_clauses = [f"{k} = ?" for k in base_data.keys()]
                query = f"""
                UPDATE machine_data SET 
                {', '.join(set_clauses)}"""
                values = list(base_data.values())
                
                # Check if other shift exists to compute totals
                other_shift = 'B' if current_shift == 'A' else 'A'
                other_prefix = f"{other_shift}_"
                other_fabric_length = existing_data.get(f'{other_prefix}Production_FabricLength')
                
                if other_fabric_length is not None:
                    # Compute totals with 2 decimal places
                    total_fabric = round(float(base_data[f'{shift_prefix}Production_FabricLength']) + \
                                 float(other_fabric_length), 2)
                    total_quantity = int(base_data[f'{shift_prefix}Production_Quantity']) + \
                                   int(existing_data[f'{other_prefix}Production_Quantity'])
                    avg_speed = round((float(base_data[f'{shift_prefix}Speed']) + \
                              float(existing_data[f'{other_prefix}Speed'])) / 2, 2)
                    avg_efficiency = round((float(base_data[f'{shift_prefix}Efficiency']) + \
                                   float(existing_data[f'{other_prefix}Efficiency'])) / 2, 2)
                    
                    # Add computed values with correct SQL syntax
                    query += """,
                        Total_Production_FabricLength = ?,
                        Total_Production_Quantity = ?,
                        Avg_Speed = ?,
                        Avg_Efficiency = ?"""
                    values.extend([total_fabric, total_quantity, avg_speed, avg_efficiency])
                
                # Add WHERE clause at the end
                query += " WHERE date = ? AND Loom_Num = ?"
                values.extend([current_date, loom_num])

            else:
                # Insert new record
                columns = ', '.join(base_data.keys())
                placeholders = ', '.join(['?' for _ in base_data])
                query = f"INSERT INTO machine_data ({columns}) VALUES ({placeholders})"
                values = list(base_data.values())
    
            cursor.execute(query, values)
            conn.commit()
            return True
    
        except Exception as e:
            self.logger.error(f"Error storing machine data: {str(e)}")
            return False

    def store_temp_data(self, data,tab_key):
        """Store temporary machine data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

           
            query = """INSERT OR REPLACE INTO temp_data (
                Device_Name, Loom_Num, Weaving_Length, Cut_Length,
                Weaving_Forecast, Warp_Remain, Warp_Length, Warp_Forecast,
                Production_Quantity, Production_FabricLength, Speed, Efficiency,
                Pre_Production_Quantity, Pre_Production_FabricLength, Pre_Speed,
                Pre_Efficiency, Shift,updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)"""
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(query, (
                data['Device_Name'], data['Loom_Num'],
                data['Weaving_Length'], data['Cut_Length'],
                data['Weaving_Forecast'], data['Warp_Remain'],
                data['Warp_Length'], data['Warp_Forecast'],
                data['Production_Quantity'][0], data['Production_FabricLength'][0],
                data['Speed'][0], data['Efficiency'][0],
                data['Production_Quantity'][1], data['Production_FabricLength'][1],
                data['Speed'][1], data['Efficiency'][1],
                data['Shift'][0],now
            ))
            conn.commit()
            return True
            
        except Exception as e:
            # print(f"Error storing temp data: {str(e)}")
            # conn = sqlite3.connect(self.db_path)
            # cursor = conn.cursor()
            
            # query = """INSERT OR REPLACE INTO temp_data (
            #     Device_Name, Loom_Num, Weaving_Length, Cut_Length,
            #     Weaving_Forecast, Warp_Remain, Warp_Length, Warp_Forecast,
            #     Production_Quantity, Production_FabricLength, Speed, Efficiency,
            #     Pre_Production_Quantity, Pre_Production_FabricLength, Pre_Speed,
            #     Pre_Efficiency, Shift,updated_at
            # ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)"""
            # now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # loom_num = tab_key.split("_")[1]
            # device_name= "HQF000"+loom_num[1]
            # cursor.execute(query, (
            #     device_name, loom_num,
            #     0, 0, 0, 0, 0, 0,
            #     0, 0, 0, 0,
            #     0, 0, 0, 0,
            #     '', now
            # ))
            # conn.commit()
            self.logger.error(f"Error storing temp data,{tab_key}: {e},Data to store: {data}, Tab Key: {tab_key}")
            return False
        finally:
            if conn:
                conn.close()

    def get_temp_data(self, loom_num=None):
        """Get temporary data for a specific loom or all looms"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if loom_num:
                cursor.execute("SELECT * FROM temp_data WHERE Loom_Num = ?", (loom_num,))
                result = cursor.fetchone()
                return dict(zip([col[0] for col in cursor.description], result)) if result else None
            else:
                cursor.execute("SELECT * FROM temp_data")
                results = cursor.fetchall()
                return [dict(zip([col[0] for col in cursor.description], row)) for row in results]
        except Exception as e:
            self.logger.error(f"Error getting temp data: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_machine_numbers(self):
        """Get list of unique machine numbers"""
        try:
            query = "SELECT DISTINCT Loom_Num FROM machine_data ORDER BY Loom_Num"
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query)
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting machine numbers: {str(e)}")
            return []
    
    def get_machine_data(self, filters):
        """Get machine data based on filters"""
        try:
            query = "SELECT * FROM machine_data WHERE 1=1"
            params = []
    
            if filters.get('date_range'):
                query += " AND date BETWEEN ? AND ?"
                params.extend([
                    filters['start_date'].strftime('%Y-%m-%d'),
                    filters['end_date'].strftime('%Y-%m-%d')
                ])
            else:
                query += " AND date =?"
                params.append(filters['start_date'].strftime('%Y-%m-%d'))
    
            if filters.get('machine'):
                query += " AND Loom_Num = ?"
                params.append(filters['machine'])
    
            query += " ORDER BY date DESC, Loom_Num"
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            
            result = []
            for row in cursor.fetchall():
                data = {}
                for i, col in enumerate(columns):
                    # Convert None to 0 for numeric columns
                    if row[i] is None:
                        if col in ['A_Production_FabricLength', 'B_Production_FabricLength',
                                  'Total_Production_FabricLength', 'A_Speed', 'B_Speed',
                                  'Avg_Speed', 'A_Efficiency', 'B_Efficiency', 'Avg_Efficiency']:
                            data[col] = 0.0
                        elif col in ['A_Production_Quantity', 'B_Production_Quantity',
                                    'Total_Production_Quantity']:
                            data[col] = 0
                        else:
                            data[col] = ''
                    else:
                        data[col] = row[i]
                result.append(data)
    
            return result
    
        except Exception as e:
            self.logger.error(f"Error getting machine data: {str(e)}")
            return []

    def get_machine_data_by_date_range(self, start_date, end_date):
        """Get machine data for a date range"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM machine_data 
                WHERE date >= ? AND date <= ?
                ORDER BY date ASC
            """, (start_date, end_date))
            
            columns = [description[0] for description in cursor.description]
            results = cursor.fetchall()
            
            data_list = []
            for row in results:
                data_dict = dict(zip(columns, row))
                data_list.append(data_dict)
                
            return data_list
            
        except Exception as e:
            self.logger.error(f"Error getting machine data by date range: {str(e)}")
            return []

