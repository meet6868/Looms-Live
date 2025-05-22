from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from utils.forecast_extractor import ForecastDataExtractor
import time
import os
from datetime import datetime,timedelta
import threading
import re
import cv2


class ClientServiceManager:
    def __init__(self, local_db, client_db, logger):
        self.local_db = local_db
        self.client_db = client_db
        self.logger = logger
        self.client_driver = None
        self.client_status = 'Unknown'
        self.system_tabs = {}  # Store all tab references
        self.screenshot_thread = None
        self.upload_thread = None
        self.tab_monitor_thread = None
        self.is_capturing = False
        self.is_uploading = False
        self.is_monitoring_tabs = False
        # self.debug_folder = "e:\\MCGS\\MCGS Web\\debug"
        # self.tab_views_folder = os.path.join(self.debug_folder, "tab_views")
        self.reinit_thread = None
        self.is_reinit_running = False
        # # Create folders if they don't exist
        # for folder in [self.debug_folder, self.tab_views_folder]:
        #     if not os.path.exists(folder):
        #         os.makedirs(folder)

    def initialize_client(self):
        try:
            # Check initialization status
            init_status = self.local_db.get_core_value("client_init_status")
            if init_status == "in_progress":
                self.logger.info("Client initialization already in progress, skipping...")
                return False

            # Clear previous error status if exists
            if init_status == "error":
                self.local_db.set_core_value("client_init_status", None)
                time.sleep(1)

            # Set initialization status
            self.local_db.set_core_value("client_init_status", "in_progress")
            self.local_db.set_core_value("client_login_status", "starting")

            # Cleanup existing instance if any
            if self.client_driver:
                self.cleanup()
                time.sleep(2)

            # Set Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--force-device-scale-factor=1.5")
            chrome_options.add_argument("--window-size=1920,1080")
            # Add these options to suppress warnings
            chrome_options.add_argument("--log-level=3")  # Fatal only
            chrome_options.add_argument("--silent")
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            
            # Get VM IP from local database
            vm_ip = self.local_db.get_value("vm_ip")
            if not vm_ip:
                self.logger.error("VM IP not found in local database")
                self.update_client_status("Error")
                return False
                
            # Set client credentials
            machine_ip = f"{vm_ip}:9090"
            machine_url = f"http://{machine_ip}"
            machine_user = "红旗纺织"
            machine_password = "12345678"
            
            # Initialize new driver
            self.logger.info("Starting new client service...")
            try:
                service = Service(ChromeDriverManager().install())
                self.client_driver = webdriver.Chrome(service=service,options=chrome_options)
            except: 
                self.client_driver = webdriver.Chrome(options=chrome_options)
                self.logger.info("CromeDrive offile-----------------")
            self.client_driver.maximize_window()
            self.client_driver.get(machine_url)
           
            
            # Login process
            wait = WebDriverWait(self.client_driver, 30)
            inputs = wait.until(lambda d: d.find_elements(By.CLASS_NAME, "el-input__inner"))
            time.sleep(1)
            inputs[0].send_keys(machine_user)
            inputs[1].send_keys(machine_password)
            
            login_btn = wait.until(EC.element_to_be_clickable(
                (By.CLASS_NAME, "el-button.login-button.el-button--primary")))
            time.sleep(1)
            login_btn.click()
            
            # Check login status
            try:
                login_status = self.client_driver.find_element(
                    By.CSS_SELECTOR, "span.login-error-info")
                login_status_text = login_status.text.strip()
                
                if login_status_text == "服务器异常, 请联系管理员!":  # Original: 服务器异常, 请联系管理员!
                    self.logger.error("Client login failed: Server error")
                    self.update_client_status("Error")
                    return False
                    
            except Exception:
                # Login successful, initialize all tabs
                if self.setup_all_tabs():
                    self.logger.info("Client tabs initialized successfully")
                    self.local_db.set_core_value("client_init_status", "completed")
                    self.local_db.set_core_value("client_login_status", "Running")
                # self.update_client_status("Running")
                return True
                
        except Exception as e:
            self.logger.error(f"Error initializing client: {str(e)}")
            self.update_client_status("Error")
            self.local_db.set_core_value("client_init_status", "error")
            self.local_db.set_core_value("client_login_status", "Error")
            return False


    def setup_all_tabs(self):
        """Initialize all required tabs after successful login"""
        try:
            # Clear and reinitialize system_tabs
            self.system_tabs = {}
            
            # Store main tab reference
            self.system_tabs['main_tab'] = self.client_driver.current_window_handle
            self.local_db.set_tab('main_tab', self.system_tabs['main_tab'])
            
            # Define all required tabs with their URLs
            machine_ip = f"{self.local_db.get_value('vm_ip')}:9090"
            tabs_to_create = {
                'machine_tab': f"http://{machine_ip}/?graphic=view&windowscene=单台概览页",
                'report_tab': f"http://{machine_ip}/?graphic=view&windowscene=报表统计页",
                'overview_tab': f"http://{machine_ip}/?graphic=view&windowscene=上机概览预测"
            }
            
            # Create each tab
            for tab_key, tab_url in tabs_to_create.items():
                self.create_new_tab(tab_key, tab_url)
            
            # Create machine-specific tabs
            self.setup_machine_tabs()
            # self.capture_all_tab_screenshots()
            
            # Start screenshot management threads
            self.start_screenshot_management()
            
            # Wait for threads to initialize
            time.sleep(5)
            
            # Return to main tab
            self.client_driver.switch_to.window(self.system_tabs['main_tab'])
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up tabs: {str(e)}")
            self.stop_screenshot_management()
            return False

    def create_new_tab(self, tab_key, tab_url):
        try:
            current_handles = set(self.client_driver.window_handles)
            
            self.client_driver.execute_script("window.open('');")
            time.sleep(1)
            
            new_handles = set(self.client_driver.window_handles)
            new_tab = list(new_handles - current_handles)[0]
            
            self.client_driver.switch_to.window(new_tab)
            
            # Set window size and zoom settings
            self.client_driver.set_window_size(1920, 1080)
            self.client_driver.execute_script("""
                document.body.style.zoom = '100%';
                document.body.style.fontSize = '16px';
                var style = document.createElement('style');
                style.innerHTML = 'table, th, td { font-size: 16px !important; }';
                document.head.appendChild(style);
            """)
            
            # Navigate to URL
            self.client_driver.get(tab_url)
            time.sleep(2)
            
            # Verify tab is active and accessible
            try:
                current_url = self.client_driver.current_url
                if not current_url.startswith(tab_url.split('?')[0]):
                    raise Exception("Tab URL verification failed")
            except Exception as e:
                self.logger.error(f"Tab verification failed for {tab_key}: {str(e)}")
                return False
            
            # Store tab reference
            self.system_tabs[tab_key] = new_tab
            self.local_db.set_tab(tab_key, new_tab)
            
            self.logger.info(f"Created new tab: {tab_key} with handle: {new_tab}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating tab {tab_key}: {str(e)}")
            return False

    def setup_machine_tabs(self):
        try:
            self.client_driver.switch_to.window(self.system_tabs['machine_tab'])
            time.sleep(2)
            
            # Set window size and font settings for machine tab
            self.client_driver.set_window_size(1920, 1080)
            self.client_driver.execute_script("""
                document.body.style.zoom = '105%';
                document.body.style.fontSize = '16px';
                var style = document.createElement('style');
                style.innerHTML = 'table, th, td { font-size: 16px !important; }';
                document.head.appendChild(style);
            """)
            
            machine_labels = self.find_machine_labels()
            current_url = self.client_driver.current_url
            
            for label in machine_labels:
                try:
                    tab_key = f"machine_{label.strip()}"
                    self.client_driver.execute_script("window.open('');")
                    self.client_driver.execute_script("document.body.style.zoom='100%'")
                    new_tab = self.client_driver.window_handles[-1]
                    self.client_driver.switch_to.window(new_tab)
                    self.client_driver.set_window_size(1920, 1080) 
                    self.client_driver.get(current_url)
                    time.sleep(1)
                    
                    self.find_and_click_enter_buttons(label)
                    self.system_tabs[tab_key] = new_tab
                    self.local_db.set_tab(tab_key, new_tab)
                    self.logger.info(f"Created machine tab: {label}")
                    
                except Exception as e:
                    self.logger.error(f"Error creating tab for machine {label}: {str(e)}")
                    continue
            
            # Return to machine tab
            self.client_driver.switch_to.window(self.system_tabs['machine_tab'])
            return True
            
        except Exception as e:
            self.logger.error(f"Error in setup_machine_tabs: {str(e)}")
            return False

    def find_machine_labels(self):
        """Find all machine labels in the machine tab"""
        try:
            # Wait for machine list to be visible
            self.client_driver.switch_to.window(self.system_tabs['machine_tab'])
            all_elements = self.client_driver.find_elements(By.XPATH, "//*[contains(text(), 'M')]")
            print("In Mahcine Label")
            machine_labels = []
            for element in all_elements:
                text = element.text
                if re.match(r'^M\d+$', text):
                    machine_labels.append(text)
            # print(machine_labels)
            self.logger.debug(f"Found machine labels: {machine_labels}")
            return machine_labels
            
        except Exception as e:
            self.logger.error(f"Error finding machine labels: {str(e)}")
            return []

    def find_and_click_enter_buttons(self,label):
        m_buttons = self.client_driver.find_elements(By.XPATH, f"//button/span[contains(text(),'{label}')]/..")
        for button in m_buttons:
            parent_container = button.find_element(By.XPATH, "./..")
            parent_container = parent_container.find_element(By.XPATH, "./..")
            enter_button = parent_container.find_element(By.XPATH, ".//button/span[contains(text(), 'Enter')]/..")
            enter_button.click()
            time.sleep(1)

   

    def start_screenshot_management(self):
        """Start all screenshot related threads"""
        self.start_screenshot_capture()
        # self.start_screenshot_upload()
        self.start_data_extraction()
        # self.start_temp_data_upload()
        self.start_machine_data_sync()
        
        
        # Only start reinit thread if it's not already running
        if not self.reinit_thread and not self.is_reinit_running:
            self.is_reinit_running = True
            self.reinit_thread = threading.Thread(target=self._reinit_loop, daemon=True)
            self.reinit_thread.start()
            self.logger.info("Reinitialization monitoring started")

    def stop_screenshot_management(self):
        """Stop all screenshot related threads"""
        self.is_capturing = False
        self.is_uploading = False
        self.is_extracting = False
        self.is_temp_uploading = False
        self.is_reinit_running = False
       
        
        time.sleep(2)
        
        self.screenshot_thread = None
        self.upload_thread = None
        self.extraction_thread = None
        self.temp_upload_thread = None
        self.tab_monitor_thread = None
        self.reinit_thread = None
        
        self.logger.info("All monitoring threads stopped")

    def _reinit_loop(self):
        """Periodic reinitialization loop"""
        while self.is_reinit_running:
            try:
                admin_status = self.local_db.get_core_value("admin_service_status")
                init_status = self.local_db.get_core_value("client_init_status")
                
                if admin_status == "Running" and init_status != "in_progress":
                    self.logger.info("Starting scheduled reinitialization...")
                    
                    # Set initialization status before starting
                    self.local_db.set_core_value("client_init_status", "in_progress")
                    
                    # Stop screenshot capture
                    self.stop_screenshot_capture()
                    time.sleep(2)
                    
                    # Cleanup existing client
                    if self.client_driver:
                        try:
                            self.client_driver.quit()
                        except Exception as e:
                            self.logger.error(f"Error closing browser: {str(e)}")
                        finally:
                            self.client_driver = None
                    
                    self.system_tabs.clear()
                    time.sleep(5)
                    
                    # Reinitialize client service
                    self._skip_reinit = True
                    if self.initialize_client():
                        self.logger.info("Scheduled reinitialization completed successfully")
                        self.local_db.set_core_value("client_init_status", "completed")
                    else:
                        self.logger.error("Failed to reinitialize client service")
                        self.local_db.set_core_value("client_init_status", "error")
                        time.sleep(30)
                    self._skip_reinit = False
                
                # Sleep for interval
                time.sleep(300)
                
            except Exception as e:
                self.logger.error(f"Error in reinit loop: {str(e)}")
                self.local_db.set_core_value("client_init_status", "error")
                time.sleep(30)

    def start_screenshot_upload(self):
        """Start screenshot upload thread"""
        if not self.upload_thread:
            self.is_uploading = True
            self.upload_thread = threading.Thread(target=self._upload_loop, daemon=True)
            self.upload_thread.start()
            self.logger.info("Screenshot upload started")

    def stop_screenshot_upload(self):
        """Stop screenshot upload thread"""
        self.is_uploading = False
        if self.upload_thread:
            self.upload_thread.join(timeout=5)
            self.upload_thread = None
            self.logger.info("Screenshot upload stopped")


    def _upload_loop(self):
        """Continuous screenshot upload loop"""
        while self.is_uploading:
            try:
                pending_screenshots = self.local_db.get_pending_screenshots()
                for tab_key, image_data, timestamp in pending_screenshots:
                    try:
                        if not image_data:
                            continue
                            
                        # Upload to client DB
                        if self.client_db.store_screenshot(tab_key, image_data,timestamp):
                            # self.local_db.mark_screenshot_uploaded(tab_key, timestamp)
                            
                           
                            self.logger.info(f"Screenshot verified for {tab_key}")
                        else:
                            self.logger.error(f"Failed to upload {tab_key}")
                                    
                    except Exception as e:
                        self.logger.error(f"Error uploading {tab_key}: {str(e)}")
                        continue
                        
                # time.sleep()
                
            except Exception as e:
                self.logger.error(f"Error in upload loop: {str(e)}")
                time.sleep(10)


    def start_data_extraction(self):
        """Start data extraction thread"""
        if not hasattr(self, 'extraction_thread'):
            self.is_extracting = True
            self.extraction_thread = threading.Thread(target=self._extraction_loop, daemon=True)
            self.extraction_thread.start()
            self.logger.info("Data extraction started")

    def stop_data_extraction(self):
        """Stop data extraction thread"""
        self.is_extracting = False
        if hasattr(self, 'extraction_thread'):
            self.extraction_thread.join(timeout=5)
            self.extraction_thread = None

    def _extraction_loop(self):
        """Continuous data extraction loop"""
        tesseract_path = self.local_db.get_client_config().get('tesseract_path', "C:\Program Files\Tesseract-OCR\tesseract.exe")
        extractor = ForecastDataExtractor(tesseract_path)
        
        while self.is_extracting:
            try:
                pending_screenshots = self.local_db.get_pending_screenshots()
                
                for tab_key, image_data, timestamp in pending_screenshots:
                    try:
                        updated_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                        is_online = datetime.now() - updated_time < timedelta(minutes=1)
                        if is_online:
                            
                            # Process only machine tab screenshots
                            if not tab_key.startswith('machine_M'):
                                continue
                                
                            # Convert base64 string to bytes if needed
                            if isinstance(image_data, str):
                                import base64
                                image_data = base64.b64decode(image_data)
                                
                            # Convert bytes to numpy array for image processing
                            import numpy as np
                            nparr = np.frombuffer(image_data, np.uint8)
                            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                                
                            # Extract data using ForecastDataExtractor
                            data,text = extractor.extract_from_image(image)
                            # self.logger.info(f"{data}------------------")
                            # self.logger.info(f"{text}------------------")
                            if data and data.get('Loom_Num')!='':
                                # Store in temp_data
                                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                self.local_db.store_temp_data(data,tab_key,current_time)
                                
                                # Process machine data
                                try:
                                    loom_num = data.get('Loom_Num')
                                    shift_time = datetime.strptime(data['Start'][1], '%Y-%m-%d %H:%M:%S')
                                    current_date = shift_time.strftime('%Y-%m-%d')
                                    current_shift = data['Shift'][1]
                                    
                                    # Check machine data status
                                    status = self.local_db.get_machine_data_status(loom_num, current_date)
                                    shift_key = f'shift_{current_shift.lower()}'
                                    
                                    if not status or not status.get(shift_key):
                                        # Store machine data
                                        if self.local_db.store_machine_data(data):
                                            # Update status
                                            self.local_db.update_machine_data_status(
                                                loom_num,
                                                current_date,
                                                current_shift,
                                                True
                                            )
                                            self.logger.info(f"Machine data stored for {loom_num} shift {current_shift}")
                                    
                                except Exception as e:
                                    self.logger.error(f"Error processing machine data: {str(e)}")
                                
                                self.logger.info(f"Data extracted and stored for {tab_key}")
                                
                    except Exception as e:
                        self.logger.error(f"Error processing {tab_key}: {str(e)}")
                        continue
                
                time.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Error in extraction loop: {str(e)}")
                time.sleep(10)

    def start_temp_data_upload(self):
        """Start temp data upload thread"""
        if not hasattr(self, 'temp_upload_thread'):
            self.is_temp_uploading = True
            self.temp_upload_thread = threading.Thread(target=self._temp_upload_loop, daemon=True)
            self.temp_upload_thread.start()
            self.logger.info("Temp data upload started")

    def stop_temp_data_upload(self):
        """Stop temp data upload thread"""
        self.is_temp_uploading = False
        if hasattr(self, 'temp_upload_thread'):
            self.temp_upload_thread.join(timeout=5)
            self.temp_upload_thread = None

    def _temp_upload_loop(self):
        """Continuous temp data upload loop"""
        while self.is_temp_uploading:
            try:
                # Get all temp data
                temp_data = self.local_db.get_temp_data()
                
                if temp_data:
                    self.logger.debug(f"Found {len(temp_data)} temp records to upload")
                    for data in temp_data:
                        try:
                            self.logger.debug(f"Uploading temp data for Loom: {data.get('Loom_Num')}")
                            if self.client_db.store_temp_data(data):
                                self.logger.info(f"Successfully uploaded temp data for {data.get('Loom_Num')}")
                            else:
                                self.logger.error(f"Failed to upload temp data for {data.get('Loom_Num')}")
                        except Exception as e:
                            self.logger.error(f"Error uploading temp data: {str(e)}")
                            continue
                else:
                    self.logger.debug("No temp data found to upload")
                
                time.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Error in temp upload loop: {str(e)}")
                time.sleep(10)


    def start_screenshot_capture(self):
        """Start screenshot capture thread"""
        if not self.screenshot_thread:
            self.is_capturing = True
            self.screenshot_thread = threading.Thread(target=self._screenshot_loop, daemon=True)
            self.screenshot_thread.start()
            self.logger.info("Screenshot capture started")

    def stop_screenshot_capture(self):
        """Stop screenshot capture thread"""
        self.is_capturing = False
        if self.screenshot_thread:
            self.screenshot_thread.join(timeout=5)
            self.screenshot_thread = None

    def _screenshot_loop(self):
        """Continuous screenshot capture loop"""
        while self.is_capturing:
            try:
                # Create a copy of system_tabs to avoid dictionary size change during iteration
                tabs_to_capture = dict(self.system_tabs)
                for tab_key, tab_handle in tabs_to_capture.items():
                    try:
                        if not self.is_capturing:  # Check if we should stop
                            break
                            
                        # Switch to tab and verify connection
                        try:
                            self.client_driver.switch_to.window(tab_handle)
                            # self.client_driver.execute_script("document.body.style.zoom='110%'")
                            self.client_driver.set_window_position(0, 0)
                            self.client_driver.set_window_size(1920, 1080)
                            self.client_driver.execute_script("""document.body.style.fontSize = '50px';""")
                            time.sleep(1)

                        except Exception as e:
                            self.logger.error(f"Failed to switch to tab {tab_key}: {str(e)}")
                            continue
                        
                        # Take screenshot with timeout protection
                        try:
                            png_data = self.client_driver.get_screenshot_as_png()
                            if png_data:
                                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                self.local_db.set_tab_view(tab_key, png_data, current_time)
                                self.logger.info(f"Screenshot updated for {tab_key}")
                        except Exception as e:
                            self.logger.error(f"Screenshot failed for {tab_key}: {str(e)}")
                            continue
                            
                    except Exception as tab_error:
                        self.logger.error(f"Error processing {tab_key}: {str(tab_error)}")
                        continue
                
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in screenshot loop: {str(e)}")
                time.sleep(10)


    def update_client_status(self, status):
        """Update client service status"""
        try:
            self.client_status = status
            self.local_db.set_value('client_status', status)
            self.logger.info(f"Client status updated to: {status}")
        except Exception as e:
            self.logger.error(f"Error updating client status: {str(e)}")

   

    def cleanup(self):
        """Clean up resources"""
        try:
            # Stop all monitoring threads first
            self.is_capturing = False
            self.is_uploading = False
            self.is_monitoring_tabs = False
            self.is_reinit_running = False
            
            # Wait a moment for threads to stop
            time.sleep(1)
            
            # Close browser and clear tabs
            if self.client_driver:
                try:
                    self.client_driver.quit()
                except Exception as e:
                    self.logger.error(f"Error closing browser: {str(e)}")
                finally:
                    self.client_driver = None
            
            # Clear system tabs
            self.system_tabs.clear()
            
            # Reset thread references without joining
            self.screenshot_thread = None
            self.upload_thread = None
            self.tab_monitor_thread = None
            self.reinit_thread = None
            
            self.logger.info("Client service cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error in cleanup: {str(e)}")


    
            # print(f"Clicked Enter button for ",{label})

    def start_machine_data_sync(self):
        """Start machine data synchronization thread"""
        if not hasattr(self, 'sync_thread'):
            self.is_syncing = True
            self.sync_thread = threading.Thread(target=self._machine_data_sync_loop, daemon=True)
            self.sync_thread.start()
            self.logger.info("Machine data sync started")

    def stop_machine_data_sync(self):
        """Stop machine data synchronization thread"""
        self.is_syncing = False
        if hasattr(self, 'sync_thread'):
            self.sync_thread.join(timeout=5)
            self.sync_thread = None

    def _machine_data_sync_loop(self):
        """Continuous machine data synchronization loop"""
        while self.is_syncing:
            try:
                
                # Get last sync date from client DB
                last_sync = self.client_db.get_value('last_machine_data')
                current_date = datetime.now().strftime('%Y-%m-%d')
                
                if not last_sync:
                    # First time sync - get client config dates
                    config = self.local_db.get_client_config()
                    start_date = config.get('start_date', current_date)
                    # self.client_db.set_value('last_machine_data', current_date)
                    data_list = self.local_db.get_machine_data_by_date_range(start_date, current_date)
                else:
                    # Not first time - check if last sync is current date
                    if last_sync != current_date:
                        # Get data from last sync to current date
                        data_list = self.local_db.get_machine_data_by_date_range(last_sync, current_date)
                    else:
                        # Already synced today
                        data_list = []

                # Upload data if available
                if data_list:
                    if self.client_db.store_machine_data(data_list):
                        # Update last sync date
                        self.client_db.set_value('last_machine_data', current_date)
                        self.logger.info(f"Successfully synced machine data from {last_sync or 'start'} to {current_date}")
                
                # Wait before next sync
                time.sleep(300)  # 5 minutes

            except Exception as e:
                self.logger.error(f"Error in machine data sync loop: {str(e)}")
                time.sleep(60)  # Wait 1 minute on error

    