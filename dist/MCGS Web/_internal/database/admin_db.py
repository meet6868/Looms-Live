import logging
import requests
import json
from datetime import datetime

class AdminDatabase:
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
        """Test connection to admin database"""
        if not self.url or not self.api_key:
            self.logger.error("Admin database credentials not set")
            self.connected = False
            return False
        
        try:
            self.logger.info(f"Testing connection to admin database at URL: {self.url}")
            
            # Make a simple request to test the connection
            response = requests.get(
                f"{self.url}/rest/v1/companies",
                headers={
                    "apikey": self.api_key,
                    "Authorization": f"Bearer {self.api_key}"
                }
            )
            
            # Log detailed response information
            self.logger.info(f"Admin DB connection test response: Status={response.status_code}, Content={response.text[:100]}")
            
            if response.status_code == 200:
                self.logger.info("Successfully connected to admin database")
                self.connected = True
                
                # Save credentials to local database
                self._save_credentials_to_local_db()
                self.sync_company_data_to_local()
                
                # Sync company data from admin to local database
                
                return True
            else:
                self.logger.error(f"Failed to connect to admin database: Status code {response.status_code}")
                self.connected = False
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting to admin database: {e}")
            self.connected = False
            return False
        except requests.exceptions.RequestException as e:
            self.connected = False
            self.logger.error(f"Error connecting to admin database: {e}")
            return False
        except Exception as e:
            self.connected = False
            self.logger.error(f"Unexpected error connecting to admin database: {e}")
            return False

    def _save_credentials_to_local_db(self):
        """Save admin database credentials to local SQLite database"""
        try:
            import sqlite3
            from pathlib import Path
            
            # Create database directory if it doesn't exist
            
            from utils.path_utils import get_db_path
            # Connect to SQLite database
            conn = sqlite3.connect(get_db_path())
            cursor = conn.cursor()
            
            # Check if admin_config table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admin_config'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # Create admin_config table
                cursor.execute('''
                CREATE TABLE admin_config (
                    id INTEGER PRIMARY KEY,
                    admin_url TEXT,
                    admin_key TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
            
            # Check if we're updating or inserting
            cursor.execute("SELECT COUNT(*) FROM admin_config")
            if cursor.fetchone()[0] > 0:
                # Update existing record
                cursor.execute(
                    "UPDATE admin_config SET admin_url = ?, admin_key = ?",
                    (self.url, self.api_key)
                )
            else:
                # Insert new record
                cursor.execute(
                    "INSERT INTO admin_config (admin_url, admin_key) VALUES (?, ?)",
                    (self.url, self.api_key)
                )
            
            # Also update the settings table for backward compatibility
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
            if cursor.fetchone() is not None:
                cursor.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    ("admin_url", self.url)
                )
                cursor.execute(
                    "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                    ("admin_key", self.api_key)
                )
            
            # Commit changes and close connection
            conn.commit()
            conn.close()
            
            self.logger.info("Admin credentials saved to local database")
            return True
        except Exception as e:
            self.logger.error(f"Error saving admin credentials to local database: {e}")
            return False
    
    def create_companies_table(self):
        """Create the companies table in the admin database"""
        try:
            self.logger.info("Creating companies table in admin database")
            
            # Define the SQL for creating the companies table
            sql = """
            CREATE TABLE IF NOT EXISTS companies (
                id SERIAL PRIMARY KEY,
                company_name TEXT NOT NULL,
                client_email TEXT,
                client_url TEXT,
                client_key TEXT,
                vm_path TEXT,
                system_path TEXT,
                ip_address TEXT,
                tesseract_path TEXT,
                password TEXT,
                start_date DATE,
                end_date DATE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(company_name, client_email),
                UNIQUE(client_url, client_key)
            );
            """
            
            # Execute the SQL using the Supabase REST API
            response = requests.post(
                f"{self.url}/rest/v1/rpc/execute_sql",
                headers={
                    "apikey": self.api_key,
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal"
                },
                data=json.dumps({"sql": sql})
            )
            
            if response.status_code == 200:
                self.logger.info("Companies table created successfully")
                return True
            else:
                self.logger.error(f"Failed to create companies table: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating companies table: {e}")
            return False
    
    def check_company_exists(self, company_name, current_company=None):
        """Check if a company name already exists in the admin database"""
        if not self.connected and not self.test_connection():
            return False
        
        try:
            # Format company names (replace spaces with underscores)
            formatted_name = company_name.replace(" ", "_")
            formatted_current = current_company.replace(" ", "_") if current_company else None
            
            headers = {
                "apikey": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Query excluding current company if provided
            if formatted_current:
                response = requests.get(
                    f"{self.url}/rest/v1/companies?and=(company_name.eq.{formatted_name},not.company_name.eq.{formatted_current})",
                    headers=headers
                )
            else:
                response = requests.get(
                    f"{self.url}/rest/v1/companies?company_name=eq.{formatted_name}",
                    headers=headers
                )
            
            if response.status_code == 200:
                data = response.json()
                return len(data) > 0
            else:
                self.logger.error(f"Failed to check company existence: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking company existence: {e}")
            return False
    
    def add_company(self, company_name, client_email, client_url, client_key):
        """
        Add a new company to the admin database
        
        Args:
            company_name (str): Name of the company
            client_email (str): Email of the client
            client_url (str): URL of the client database
            client_key (str): API key for the client database
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Log the attempt
            self.logger.info(f"Adding company {company_name} to admin database")
            
            # Check if we're connected
            if not self.connected and not self.test_connection():
                self.logger.error("Cannot add company: Not connected to admin database")
                return False
                
            # Format company name (replace spaces with underscores)
            formatted_name = company_name.replace(" ", "_")
            
            # Create the data to insert - using the correct column names from schema
            data = {
                "company_name": formatted_name,
                "client_email": client_email,
                "client_url": client_url,
                "client_key": client_key
            }
            
            # Insert the data using REST API
            headers = {
                "apikey": self.api_key,
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
            
            response = requests.post(
                f"{self.url}/rest/v1/companies",
                headers=headers,
                json=data
            )
            
            if response.status_code in [200, 201, 204]:
                self.logger.info(f"Successfully added company {company_name}")
                return True
            else:
                self.logger.error(f"Failed to add company: {response.status_code}, {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to add company: {str(e)}")
            return False
    
    def update_company(self, company_name, company_data,old_name,old_email):
        """Update an existing company in the admin database"""
        if not self.connected and not self.test_connection():
            return False
        
        try:
            # Format company name (replace spaces with underscores)
            formatted_name = company_name.replace(" ", "_")
            
            self.delete_company(old_name.replace(" ", "_"),old_email)

            # First get the company ID
            headers = {
                "apikey": self.api_key,
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
            
            # Get existing company data to get the ID
            check_response = requests.get(
                f"{self.url}/rest/v1/companies?company_name=eq.{formatted_name}",
                headers=headers
            )
            
            if check_response.status_code == 200:
                existing_data = check_response.json()
                
                # Prepare the data for admin database
                admin_data = {
                    "company_name": formatted_name,
                    "client_email": company_data.get("client_email"),
                    "client_url": company_data.get("client_url"),
                    "client_key": company_data.get("client_key"),
                    "vm_path": company_data.get("vm_path"),
                    "system_path": company_data.get("system_path"),
                    "tesseract_path": company_data.get("tesseract_path"),
                    "password": company_data.get("password"),
                    "ip": company_data.get("ip"),
                    "start_date": company_data.get("start_date"),
                    "end_date": company_data.get("end_date"),
                    "updated_at": datetime.now().isoformat()
                }
                
                if existing_data and len(existing_data) > 0:
                    # Update existing company using ID
                    company_id = existing_data[0]['id']
                    response = requests.patch(
                        f"{self.url}/rest/v1/companies?id=eq.{company_id}",
                        headers=headers,
                        json=admin_data
                    )
                else:
                    # Insert new company
                    response = requests.post(
                        f"{self.url}/rest/v1/companies",
                        headers=headers,
                        json=admin_data
                    )
                
                if response.status_code in [200, 201, 204]:
                    self.logger.info(f"Successfully {'updated' if existing_data else 'added'} company: {formatted_name}")
                    return True
                else:
                    self.logger.error(f"Failed to {'update' if existing_data else 'add'} company: {response.status_code}, {response.text}")
                    return False
            else:
                self.logger.error(f"Failed to check company existence: {check_response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating company: {e}")
            return False
    
    def get_license_data(self, company_name):
        """Get license data for a specific company"""
        try:
            response = requests.get(
                f"{self.url}/rest/v1/companies",
                headers={
                    "apikey": self.api_key,
                    "Authorization": f"Bearer {self.api_key}"
                },
                params={
                    "select": "start_date,end_date,status",
                    "company_name": f"eq.{company_name}"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return {
                        'start_date': data[0].get('start_date'),
                        'end_date': data[0].get('end_date'),
                        'status': data[0].get('status')
                    }
            return None
        except Exception as e:
            self.logger.error(f"Error getting license data: {e}")
            return None
    
    def get_company_data(self, company_name,client_email,multiple=False):
        """Get company data from the admin database"""
        if not self.connected and not self.test_connection():
            return None
        
        try:
            # Format company name (replace spaces with underscores)
            formatted_name = company_name.replace(" ", "_")
            
            headers = {
                "apikey": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Query the companies table for the company data
            response = requests.get(
                f"{self.url}/rest/v1/companies?and=(company_name.eq.{formatted_name},client_email.eq.{client_email})",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()

                if data and len(data) > 0:
                    if multiple:
                        return data
                    return data[0]
                return None
            else:
                self.logger.error(f"Failed to get company data: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting company data: {e}")
            return None
    
    def get_admin_password(self):
        """Get the admin password from the admin database"""
        if not self.connected and not self.test_connection():
            return None
        
        try:
            headers = {
                "apikey": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Query the settings table for the admin password
            response = requests.get(
                f"{self.url}/rest/v1/settings?key=eq.admin_password",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    print(data)
                    return data[0].get("value")
                return None
            else:
                self.logger.error(f"Failed to get admin password: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting admin password: {e}")
            return None

    def check_client_url_exists(self, client_url):
        """Check if a client URL already exists in the admin database"""
        if not self.connected and not self.test_connection():
            return False
        
        try:
            headers = {
                "apikey": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Query the companies table for the client URL
            response = requests.get(
                f"{self.url}/rest/v1/companies?client_url=eq.{client_url}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return len(data) > 0
            else:
                self.logger.error(f"Failed to check client URL existence: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking client URL existence: {e}")
            return False

    def check_client_key_exists(self, client_key):
        """Check if a client API key already exists in the admin database"""
        if not self.connected and not self.test_connection():
            return False
        
        try:
            headers = {
                "apikey": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Query the companies table for the client key
            response = requests.get(
                f"{self.url}/rest/v1/companies?client_key=eq.{client_key}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return len(data) > 0
            else:
                self.logger.error(f"Failed to check client key existence: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking client key existence: {e}")
            return False

    def check_company_email_exists(self, company_name, client_email, current_name=None, current_email=None):
        """Check if a company name and email combination already exists, excluding current company"""
        if not self.connected and not self.test_connection():
            return False
        
        try:
            headers = {
                "apikey": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Format company name (replace spaces with underscores)
            formatted_name = company_name.replace(" ", "_")
            
            # Build the query to check exact match of both name AND email
            if current_name and current_email:
                # Exclude current company from search
                query = f"{self.url}/rest/v1/companies?and=(company_name.eq.{formatted_name},client_email.eq.{client_email})"
                response = requests.get(query, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    # Return True only if found AND it's not the current company
                    return any(
                        company for company in data
                        if not (company.get('company_name') == current_name.replace(" ", "_") and 
                            company.get('client_email') == current_email)
                    )
            else:
                # For new company, check exact match of both
                query = f"{self.url}/rest/v1/companies?and=(company_name.eq.{formatted_name},client_email.eq.{client_email})"
                response = requests.get(query, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    return len(data) > 0
                    
            return False
                
        except Exception as e:
            self.logger.error(f"Error checking company and email existence: {e}")
            return False

    def check_client_credentials_exist(self, client_url, client_key):
        """Check if a client URL and API key combination already exists in the admin database"""
        if not self.connected and not self.test_connection():
            return False
        
        try:
            headers = {
                "apikey": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Make sure URL starts with https://
            if client_url and not client_url.startswith("http://") and not client_url.startswith("https://"):
                client_url = "https://" + client_url
            
            # Query the companies table for the client URL and key combination
            response = requests.get(
                f"{self.url}/rest/v1/companies?client_url=eq.{client_url}&client_key=eq.{client_key}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return len(data) > 0
            else:
                self.logger.error(f"Failed to check client credentials existence: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking client credentials existence: {e}")
            return False

    def create_settings_table(self):
        """Create the settings table in the admin database"""
        try:
            self.logger.info("Creating settings table in admin database")
            
            # Define the SQL for creating the settings table with updated_at column
            sql = """
            CREATE TABLE IF NOT EXISTS settings (
                id SERIAL PRIMARY KEY,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            # Execute the SQL using the Supabase REST API
            response = requests.post(
                f"{self.url}/rest/v1/rpc/execute_sql",
                headers={
                    "apikey": self.api_key,
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal"
                },
                data=json.dumps({"sql": sql})
            )
            
            if response.status_code == 200:
                self.logger.info("Settings table created successfully")
                return True
            else:
                self.logger.error(f"Failed to create settings table: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating settings table: {e}")
            return False

    def disconnect(self):
        """Disconnect from the admin database"""
        try:
            self.connected = False
            self.logger.info("Disconnected from admin database")
            return True
        except Exception as e:
            self.logger.error(f"Error disconnecting from admin database: {e}")
            return False

    def sync_company_data_to_local(self):
        """Sync company data from admin database to local database during connection test"""
        try:
            from database.local_db import LocalDatabase
            local_db = LocalDatabase()
            
            # Get company name from settings
            company_name = local_db.get_value("company_name")
            client_email = local_db.get_value("client_email")
            
            if company_name and client_email:
                # Get company data from admin database
                company_data = self.get_company_data(company_name,client_email)
                if company_data:
                    # Prepare data for local database
                    local_config = {
                        "company_name": company_data.get("company_name", ""),
                        "client_email": company_data.get("client_email", ""),
                        "client_url": company_data.get("client_url", ""),
                        "client_key": company_data.get("client_key", ""),
                        "vm_path": company_data.get("vm_path", ""),
                        "ip": company_data.get("ip", ""), 
                        "system_path": company_data.get("system_path", ""),
                        "tesseract_path": company_data.get("tesseract_path", ""),
                        "password": company_data.get("password", ""),
                        "start_date": company_data.get("start_date", ""),
                        "end_date": company_data.get("end_date", "")
                    }
                    
                    # Update client_config table
                    local_db.set_client_config(local_config)
                    local_db.set_value("client_email", local_config.get("client_email", ""))
                    from database.client_db import ClientDatabase
                    client_db = ClientDatabase()
                    client_db.set_credentials(local_config.get("client_url", ""), local_config.get("client_key", ""))
                    
                    if client_db.test_connection():
                        client_db.set_client_config(local_config)
                    
                    # Update company name in settings table
                    local_db.set_value("company_name", local_config["company_name"])
                    
                    self.logger.info("Successfully synced company data to local database")
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Error syncing company data: {e}")

    def delete_company(self, company_name,client_email):
        """Delete a company from the admin database"""
        if not self.connected and not self.test_connection():
            return False
        
        try:
            # Format company name
            formatted_name = company_name.replace(" ", "_")
            
            headers = {
                "apikey": self.api_key,
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
            
            # Delete the company
            response = requests.delete(
                f"{self.url}/rest/v1/companies?and=(company_name.eq.{formatted_name},client_email.eq.{client_email})",
                headers=headers
            )
            
            if response.status_code in [200, 201, 204]:
                self.logger.info(f"Successfully deleted company: {company_name}")
                return True
            else:
                self.logger.error(f"Failed to delete company: {response.status_code}, {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting company: {str(e)}")
            return False
