from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import threading
import subprocess
import platform
status_lock = threading.Lock()
def safe_set_status(db, key, value):
    with status_lock:
        db.set_core_value(key, value)

# 添加翻译字典
TRANSLATIONS = {
    "启动": "Start",
    "停止": "Stop",
    "运行中": "Running",
    "已停止": "Stopped",
    "处理中...": "Processing...",
}

class AdminServiceManager:
    def __init__(self, local_db, client_db, logger):
        self.local_db = local_db
        self.client_db = client_db
        self.logger = logger
        self.backend_driver = None
        self.backend_status = 'Unknown'
        self.start_flag = False

    def kill_chrome_and_driver(self):
        if platform.system() == "Windows":
            try:
                subprocess.call('taskkill /f /im chromedriver.exe', shell=True)
                # subprocess.call('taskkill /f /im chrome.exe', shell=True)
                self.logger.info("Killed existing ChromeDriver and Chrome processes.")
            except Exception as e:
                self.logger.error(f"Error killing processes: {e}")
        else:
            try:
                subprocess.call("pkill -f chromedriver", shell=True)
                subprocess.call("pkill -f chrome", shell=True)
                self.logger.info("Killed existing ChromeDriver and Chrome processes.")
            except Exception as e:
                self.logger.error(f"Error killing processes: {e}")
        
    def initialize_service(self):
        try:
            self.kill_chrome_and_driver()
            # Set Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-cache")
            chrome_options.add_argument("--disable-application-cache")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            chrome_options.add_argument("--force-device-scale-factor=1.5")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-infobars")
            
            # Get VM IP from local database
            vm_ip = self.local_db.get_value("vm_ip")
            if not vm_ip:
                self.logger.error("VM IP not found in local database")
                return False

            safe_set_status(self.local_db,"admin_service_status", "Processing...")
            self.client_db.set_core_value("admin_service_status", "Processing...")
                
            # Set backend credentials
            backend_ip = f"{vm_ip}:9089"
            backend_url = f"http://{backend_ip}"
            backend_user = "admin"
            backend_password = "4006007062"
            
            # Initialize driver
            # self.backend_driver = webdriver.Chrome(options=chrome_options)
            

            try:
                service = Service(ChromeDriverManager().install())
                self.backend_driver = webdriver.Chrome(service=service,options=chrome_options)
            except: 
                self.backend_driver = webdriver.Chrome(options=chrome_options)
                self.logger.info("CromeDrive offile-----------------")
                
            self.backend_driver.get(backend_url)
            

            
            # Login
            wait = WebDriverWait(self.backend_driver, 20)
            inputs = wait.until(lambda d: d.find_elements(By.CLASS_NAME, "el-input__inner"))
            inputs[0].send_keys(backend_user)
            inputs[1].send_keys(backend_password)
            
            login_btn = wait.until(EC.element_to_be_clickable(
                (By.CLASS_NAME, "el-button.login-button.el-button--primary")))
            login_btn.click()

            

            
            wait.until(EC.invisibility_of_element(
                (By.CLASS_NAME, "el-button.login-button.el-button--primary"))) 
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing admin service: {str(e)}")
            self.backend_driver.quit()
            safe_set_status(self.local_db,"admin_service_status", "Error")
            self.client_db.set_core_value("admin_service_status", "Error")
            return False
            return False
            
    def check_service_status(self):
        try:
            if not self.backend_driver:
                return 'Not Initialized'
            
            # Refresh the page to get current status
            self.backend_driver.refresh()
            
            # Wait for status cell to be present after refresh
           
            wait = WebDriverWait(self.backend_driver, 10)
            status_cell = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "td.el-table_1_column_5.is-center")))
            
            status_text = status_cell.text.strip()
            translated_status = TRANSLATIONS.get(status_text, status_text)
            
            if translated_status == "Stopped" and self.backend_status == "Running":
                self.start_flag = True
                self.logger.info(f"Service stopped externally. Current status: {translated_status}")
            
            self.backend_status = translated_status
            
            # Update status in databases
            
            
            return translated_status
            
        except Exception as e:
            self.logger.error(f"Error checking service status: {str(e)}")
            # If we can't access the page, assume there's an error with the connection
            self.backend_driver.quit()
            self.backend_driver = None
            return 'Error'
            
    def start_service(self):
        try:
            if self.backend_status == 'Stopped':
                # 使用中文按钮文本查找元素
                button = self.backend_driver.find_element(
                    By.XPATH, "//button[normalize-space()='启动']")
                button.click()
                time.sleep(2)  # 等待状态更新
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error starting service: {str(e)}")
            return False
            
    def cleanup(self):
        if self.backend_driver:
            try:
                self.backend_driver.quit()
            except:
                pass