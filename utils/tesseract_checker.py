import os
import subprocess
import logging

class TesseractChecker:
    def __init__(self):
        self.logger = logging.getLogger("LoomLive")
    
    def check_tesseract(self, tesseract_path):
        """Check if Tesseract OCR is available at the specified path"""
        if not tesseract_path or not tesseract_path.strip():
            self.logger.error("Tesseract path is empty")
            return False, "Tesseract path is not specified"
        
        try:
            self.logger.info(f"Checking Tesseract at: {tesseract_path}")
            
            # Check if the file exists
            if not os.path.isfile(tesseract_path):
                self.logger.error(f"Tesseract executable not found at: {tesseract_path}")
                return False, "Tesseract executable not found"
            
            # Try to run Tesseract with --version to check if it works
            result = subprocess.run([tesseract_path, "--version"], 
                                   capture_output=True, 
                                   text=True, 
                                   timeout=5)
            
            if result.returncode == 0 and "tesseract" in result.stdout.lower():
                version = result.stdout.split('\n')[0]
                self.logger.info(f"Tesseract is available: {version}")
                return True, version
            else:
                self.logger.error("Tesseract check failed")
                return False, "Tesseract check failed"
            
        except subprocess.TimeoutExpired:
            self.logger.error("Tesseract check timed out")
            return False, "Tesseract check timed out"
        except Exception as e:
            self.logger.error(f"Error checking Tesseract: {e}")
            return False, f"Error checking Tesseract: {str(e)}"