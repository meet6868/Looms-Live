import logging
import requests
import json
from datetime import datetime

class ClientDatabase:
    def __init__(self, url=None, api_key=None):
        self.url = url
        self.api_key = api_key
        self.logger = logging.getLogger("LoomLive")
        self.connected = False
    
    def set_credentials(self, url, api_key):
        """Set the Supabase URL and API key"""
        self.url = url
        self.api_key = api_key
        self.connected = False
    
    def test_connection(self):
        """Test connection to client database"""
        if not self.url or not self.api_key:
            self.logger.error("Client database credentials not set")
            return False
        
        try:
            self.logger.info(f"Testing connection to client database at URL: {self.url}")
            
            # Make a simple request to test the connection
            response = requests.get(
                f"{self.url}/rest/v1/client_config",
                headers={
                    "apikey": self.api_key,
                    "Authorization": f"Bearer {self.api_key}"
                }
            )
            
            # Log detailed response information
            self.logger.info(f"Client DB connection test response: Status={response.status_code}, Content={response.text[:100]}")
            
            if response.status_code == 200:
                self.connected = True
                self.logger.info("Successfully connected to client database")
                return True
            elif response.status_code == 404:
                # Table might not exist, try to create it
                self.logger.info("Client_config table not found, attempting to create it")
                if self.create_client_config_table():
                    self.connected = True
                    self.logger.info("Successfully created client_config table and connected")
                    return True
                else:
                    self.connected = False
                    return False
            else:
                self.connected = False
                self.logger.error(f"Failed to connect to client database: {response.status_code}")
                self.logger.error(f"Response details: {response.text[:200]}")
                return False
        except requests.exceptions.RequestException as e:
            self.connected = False
            self.logger.error(f"Error connecting to client database: {e}")
            return False
        except Exception as e:
            self.connected = False
            self.logger.error(f"Unexpected error connecting to client database: {e}")
            return False
            
    
    
            
    def _save_credentials_to_local_db(self):
        """Save client database credentials to local SQLite database"""
        try:
            import sqlite3
            from pathlib import Path
            
            # Create database directory if it doesn't exist
            
            from utils.path_utils import get_db_path

            # Connect to SQLite database
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            
            # Create settings table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Save client URL and key
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))",
                ("client_url", self.url)
            )
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))",
                ("client_key", self.api_key)
            )
            
            # Commit changes and close connection
            conn.commit()
            conn.close()
            
            self.logger.info("Client credentials saved to local database")
            return True
        except Exception as e:
            self.logger.error(f"Error saving client credentials to local database: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the admin database"""
        try:
            self.connected = False
            self.logger.info("Disconnected from client database")
            return True
        except Exception as e:
            self.logger.error(f"Error disconnecting from client database: {e}")
            return False

    def set_value(self, key, value):
        """Set or update a key-value pair in Supabase settings table"""
        try:

            if not self.connected and not self.test_connection():
                self.logger.debug(f"Error Not Coonected Clinet Db")
                return False

            self.logger.debug(f"Setting key '{key}' to '{value}' in Supabase")

            # First, try to upsert (insert or update)
            response = requests.post(
                f"{self.url}/rest/v1/settings",
                headers={
                    "apikey": self.api_key,
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Prefer": "resolution=merge-duplicates"
                },
                json={"key": key, "value": value}
            )

            if response.status_code in [200, 201, 204]:
                self.logger.info(f"Successfully set key in Client Db")
                return True
            else:
                self.logger.error(f"Failed to set value: {response.status_code}, {response.text}")
                return False

        except Exception as e:
            self.logger.error(f"Error setting value in Supabase: {str(e)}")
            return False


    def get_value(self, key, default=None):
        """Retrieve a value from the Supabase settings table"""
        if not self.connected and not self.test_connection():
            self.logger.debug(f"Error Not Coonected Clinet Db")
            return default

        try:
            self.logger.debug(f"Getting key '{key}' from Supabase")

            response = requests.get(
                f"{self.url}/rest/v1/settings?key=eq.{key}",
                headers={
                    "apikey": self.api_key,
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json"
                }
            )

            if response.status_code == 200:
                data = response.json()
                if data:
                    self.logger.info(f"Found key {key}: {data[0]['value']}")
                    return data[0]["value"]
                else:
                    self.logger.warning(f"Key {key} not found, returning default")
                    return default
            else:
                self.logger.error(f"Failed to retrieve key: {response.status_code}, {response.text}")
                return default

        except Exception as e:
            self.logger.error(f"Error getting value from Supabase: {str(e)}")
            return default


    def clear_client_config(self):
        """Clear all data from client_config table"""
        try:
            if not self.connected and not self.test_connection():
                self.logger.error("Not connected to client database")
                return False
    
            response = requests.delete(
                f"{self.url}/rest/v1/client_config?id=gt.0",  # Delete where id greater than 0 (all records)
                headers={
                    "apikey": self.api_key,
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
    
            if response.status_code in [200, 201, 204]:
                self.logger.info("Successfully cleared client_config table")
                return True
            else:
                self.logger.error(f"Failed to clear client_config: {response.status_code}, {response.text}")
                return False
    
        except Exception as e:
            self.logger.error(f"Error clearing client_config table: {str(e)}")
            return False
    
    def set_client_config(self, config_data):
        """Insert new company configuration data"""
        try:
            if not self.connected and not self.test_connection():
                self.logger.error("Not connected to client database")
                return False
    
            # First clear existing data
            if not self.clear_client_config():
                self.logger.error("Failed to clear existing configuration")
                return False
            # Insert new configuration
            response = requests.post(
                f"{self.url}/rest/v1/client_config",
                headers={
                    "apikey": self.api_key,
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal"
                },
                json=config_data
            )
    
            if response.status_code in [200, 201, 204]:
                self.logger.info("Successfully set new client configuration")
                return True
            else:
                self.logger.error(f"Failed to set client configuration: {response.status_code}, {response.text}")
                return False
    
        except Exception as e:
            self.logger.error(f"Error setting client configuration: {str(e)}")
            return False


    def set_core_value(self, key, value):
        """Set value in core table"""
        try:
            if not self.connected and not self.test_connection():
                self.logger.error("Not connected to client database")
                return False
    
            response = requests.post(
                f"{self.url}/rest/v1/core",
                headers={
                    "apikey": self.api_key,
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Prefer": "resolution=merge-duplicates"  # This enables upsert
                },
                json={
                    "key": key,
                    "value": value,
                    "updated_at": datetime.now().isoformat()
                }
            )
    
            if response.status_code in [200, 201, 204]:
                return True
            else:
                self.logger.error(f"Failed to set core value: {response.status_code}, {response.text}")
                return False
    
        except Exception as e:
            self.logger.error(f"Error setting core value: {str(e)}")
            return False

    def get_core_value(self, key):
        """Get value from core table"""
        try:
            if not self.connected and not self.test_connection():
                self.logger.error("Not connected to client database")
                return None
    
            response = requests.get(
                f"{self.url}/rest/v1/core",
                headers={
                    "apikey": self.api_key,
                    "Authorization": f"Bearer {self.api_key}",
                },
                params={
                    "key": f"eq.{key}",
                    "select": "value"
                }
            )
    
            if response.status_code == 200:
                results = response.json()
                return results[0]["value"] if results else None
            else:
                self.logger.error(f"Failed to get core value: {response.status_code}, {response.text}")
                return None
    
        except Exception as e:
            self.logger.error(f"Error getting core value: {str(e)}")
            return None

    def store_screenshot(self, tab_key, image_data, timestamp):
        """Store or update screenshot in client database"""
        try:
            if not self.connected and not self.test_connection():
                self.logger.error("Not connected to client database")
                return False

            # First try to get existing record
            response = requests.get(
                f"{self.url}/rest/v1/screenshots",
                headers={
                    "apikey": self.api_key,
                    "Authorization": f"Bearer {self.api_key}"
                },
                params={
                    "tab_key": f"eq.{tab_key}"
                }
            )
            
            if response.status_code == 200 and response.json():
                # Update existing record
                response = requests.patch(
                    f"{self.url}/rest/v1/screenshots?tab_key=eq.{tab_key}",
                    headers={
                        "apikey": self.api_key,
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "Prefer": "return=minimal"
                    },
                    json={
                        "image_data": image_data,
                        "updated_at": timestamp
                    }
                )
            else:
                # Create new record
                response = requests.post(
                    f"{self.url}/rest/v1/screenshots",
                    headers={
                        "apikey": self.api_key,
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "Prefer": "return=minimal"
                    },
                    json={
                        "tab_key": tab_key,
                        "image_data": image_data,
                        "updated_at": timestamp,
                        "created_at": timestamp  # Use passed timestamp for consistency
                    }
                )
            
            if response.status_code in [200, 201, 204]:
                # Verify the data was stored with the correct timestamp
                verify_response = requests.get(
                    f"{self.url}/rest/v1/screenshots",
                    headers={
                        "apikey": self.api_key,
                        "Authorization": f"Bearer {self.api_key}"
                    },
                    params={
                        "tab_key": f"eq.{tab_key}",
                        "updated_at": f"eq.{timestamp}"  # Use passed timestamp for verification
                    }
                )
                
                if verify_response.status_code == 200 and verify_response.json():
                    self.logger.info(f"Screenshot verified in client DB for tab: {tab_key}")
                    return True
                
                self.logger.error(f"Screenshot verification failed for {tab_key}. Response: {verify_response.text}")
                return False
            else:
                self.logger.error(f"Failed to store screenshot: {response.status_code}, {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error storing screenshot: {str(e)}")
            return False

    def get_screenshot(self, tab_key):
        """Get latest screenshot for a tab"""
        try:
            if not self.connected and not self.test_connection():
                return None
                
            response = requests.get(
                f"{self.url}/rest/v1/screenshots",
                headers={
                    "apikey": self.api_key,
                    "Authorization": f"Bearer {self.api_key}"
                },
                params={
                    "tab_key": f"eq.{tab_key}",
                    "select": "image_data,updated_at",
                    "order": "updated_at.desc",
                    "limit": 1
                }
            )
            
            if response.status_code == 200:
                results = response.json()
                if results and len(results) > 0:
                    self.logger.debug(f"Retrieved screenshot for {tab_key} from {results[0].get('updated_at')}")
                    return results[0].get("image_data")
                self.logger.warning(f"No screenshot found for {tab_key}")
                return None
            else:
                self.logger.error(f"Failed to get screenshot: {response.status_code}, {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting screenshot: {str(e)}")
            return None

    def store_temp_data(self, data):
        """Store temporary data in client database"""
        try:
            if not self.connected and not self.test_connection():
                self.logger.error("Not connected to client database")
                return False

            # Map of original keys to lowercase database column names
            column_mapping = {
                'Device_Name': 'device_name',
                'Loom_Num': 'loom_num',
                'Weaving_Length': 'weaving_length',
                'Weaving_Forecast': 'weaving_forecast',
                "Cut_Length": "cut_length",
                'Warp_Remain': 'warp_remain',
                'Warp_Length': 'warp_length',
                'Warp_Forecast': 'warp_forecast',
                'Production_Quantity': 'production_quantity',
                'Production_FabricLength': 'production_fabriclength',
                'Speed': 'speed',
                'Efficiency': 'efficiency',
                'Pre_Production_Quantity': 'pre_production_quantity',
                'Pre_Production_FabricLength': 'pre_production_fabriclength',
                'Pre_Speed': 'pre_speed',
                'Pre_Efficiency': 'pre_efficiency',
                'Shift': 'shift',

            }

            # Transform data using the mapping
            transformed_data = {}
            for k, v in data.items():
                if k in column_mapping:
                    transformed_data[column_mapping[k]] = v

            # Delete existing record if it exists
            delete_response = requests.delete(
                f"{self.url}/rest/v1/temp_data",
                headers={
                    "apikey": self.api_key,
                    "Authorization": f"Bearer {self.api_key}"
                },
                params={
                    "loom_num": f"eq.{transformed_data.get('loom_num')}"
                }
            )

            # Insert new record
            response = requests.post(
                f"{self.url}/rest/v1/temp_data",
                headers={
                    "apikey": self.api_key,
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=transformed_data
            )
            
            if response.status_code in [200, 201, 204]:
                self.logger.info(f"Successfully stored temp data for Loom: {transformed_data.get('loom_num')}")
                return True
            else:
                self.logger.error(f"Failed to store temp data: {response.status_code}, {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error storing temp data in client DB: {e}")
            return False

    def get_temp_data(self, loom_num=None):
        """Get temporary data from client database"""
        try:
            url = f"{self.url}/rest/v1/temp_data"
            if loom_num:
                url += f"?Loom_Num=eq.{loom_num}"
            
            response = requests.get(
                url,
                headers={
                    "apikey": self.api_key,
                    "Authorization": f"Bearer {self.api_key}"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data[0] if loom_num and data else data
            return None
        except Exception as e:
            self.logger.error(f"Error getting temp data from client DB: {e}")
            return None

    def store_machine_data(self, data_list):
        """Store machine data in client database"""
        try:
            if not self.connected and not self.test_connection():
                return False

            # Convert data to lowercase keys
            lowercase_data_list = []
            for data in data_list:
                lowercase_data = {k.lower(): v for k, v in data.items()}
                lowercase_data_list.append(lowercase_data)

            # Delete existing data for each loom number and its date range
            if lowercase_data_list:
                # Group data by loom number
                loom_data = {}
                for data in lowercase_data_list:
                    loom_num = data['loom_num']
                    if loom_num not in loom_data:
                        loom_data[loom_num] = {'dates': []}
                    loom_data[loom_num]['dates'].append(data['date'])

                # Delete data for each loom number within its date range
                for loom_num, data in loom_data.items():
                    start_date = min(data['dates'])
                    end_date = max(data['dates'])
                    
                    delete_response = requests.delete(
                        f"{self.url}/rest/v1/machine_data",
                        headers={
                            "apikey": self.api_key,
                            "Authorization": f"Bearer {self.api_key}"
                        },
                        params={
                            "date": f"gte.{start_date}",
                            "date": f"lte.{end_date}",
                            "loom_num": f"eq.{loom_num}"
                        }
                    )

            # Insert new data
            response = requests.post(
                f"{self.url}/rest/v1/machine_data",
                headers={
                    "apikey": self.api_key,
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal"
                },
                json=lowercase_data_list
            )

            if response.status_code in [200, 201, 204]:
                return True
            else:
                self.logger.error(f"Failed to store machine data: {response.status_code}, {response.text}")
                return False

        except Exception as e:
            self.logger.error(f"Error storing machine data: {str(e)}")
            return False
