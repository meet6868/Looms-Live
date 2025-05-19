import redis
from upstash_redis import Redis
import json
import base64
import threading
import time
import logging
import cv2
import numpy as np
from database.local_db import LocalDatabase
from base64 import b64decode, b64encode

class RedisManager:
    def __init__(self, local_db, port=6380):
        self.logger = logging.getLogger("LoomLive")
        self.local_db = local_db
        self.redis_client = None
        self.upstash_redis = Redis(
            url="https://on-snapper-37126.upstash.io",
            token="AZEGAAIjcDEyNDFkMDA1ZGYxYWM0MDhlOThmZTYzYjllNjZkY2Q3ZHAxMA"
        )
        self.upload_thread = None
        self.is_uploading = False
        self.port = 6379
        self.connect()

    def connect(self):
        """Connect to Redis server"""
        try:
            # Local Redis for temporary storage
            self.redis_client = redis.Redis(host='localhost', port=self.port, db=0)
            self.redis_client.ping()
            self.logger.info(f"Successfully connected to Redis on port {self.port}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            return False

    def start_upload(self):
        """Start the Redis upload thread"""
        if not self.upload_thread:
            self.is_uploading = True
            self.upload_thread = threading.Thread(target=self._upload_loop, daemon=True)
            self.upload_thread.start()
            self.logger.info("Redis upload thread started")

    def stop_upload(self):
        """Stop the Redis upload thread"""
        self.is_uploading = False
        if self.upload_thread:
            self.upload_thread.join(timeout=5)
            self.upload_thread = None
            self.logger.info("Redis upload thread stopped")

    def compress_screenshot(self, image_base64: str) -> str:
        try:
            # Decode base64 to bytes
            image_bytes = b64decode(image_base64.encode('ascii'))
            
            # Convert to numpy array for OpenCV
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Compress image
            encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
            success, compressed_img = cv2.imencode('.jpg', img, encode_params)
            
            if success:
                # Convert back to base64
                compressed_base64 = b64encode(compressed_img.tobytes()).decode('utf-8')
                return f"data:image/jpeg;base64,{compressed_base64}"
                
            return image_base64
        except Exception as e:
            self.logger.error(f"Error compressing image: {e}")
            return image_base64

    def _upload_loop(self):
        """Main upload loop"""
        while self.is_uploading:
            try:
                if not self.redis_client:
                    if not self.connect():
                        time.sleep(5)
                        continue

                # Upload temp data to Upstash Redis
                company_name = self.local_db.get_value('company_name')
                client_email = self.local_db.get_value('client_email')
                        
                temp_data = self.local_db.get_temp_data()
                if temp_data:
                    try:
                        # Add company and client info to temp data
                       
                        enriched_temp_data = {
                            "company_name": company_name,
                            "client_email": client_email,
                            "data": temp_data,
                            "timestamp": time.time()
                        }
                        
                        # Upload to Upstash Redis
                        key = f"temp_data:{company_name}:{client_email}"
                        self.upstash_redis.set(key, json.dumps(enriched_temp_data))
                        self.logger.info(f"Upstash Redis: Uploaded temp data for {company_name}")
                    except Exception as e:
                        self.logger.error(f"Error uploading temp data to Upstash Redis: {e}")

                # TODO: Future AWS S3 Integration for tab views
                # tab_views = self.local_db.get_pending_screenshots()
                # for tab_key, image_data, timestamp in tab_views:
                #     try:
                #         # 1. Upload image to S3
                #         # 2. Get S3 URL
                #         # 3. Create data structure with company_name and client_email
                #         # 4. Upload to Upstash Redis
                #         pass

                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Error in Redis upload loop: {e}")
                time.sleep(5)

    def cleanup(self):
        """Cleanup Redis resources"""
        self.stop_upload()
        if self.redis_client:
            try:
                self.redis_client.close()
            except:
                pass