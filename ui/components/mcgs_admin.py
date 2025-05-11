from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from database.local_db import LocalDatabase
from database.client_db import ClientDatabase


class MCGSAdmin():
    def __init__(self):
        self.local_db=LocalDatabase()
        self.client_db=ClientDatabase()