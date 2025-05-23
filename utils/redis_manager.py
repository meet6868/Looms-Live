from upstash_redis import Redis
import json
import base64
import threading
import time
import logging
import cv2
import numpy as np
import boto3
from database.local_db import LocalDatabase
from base64 import b64decode, b64encode
from datetime import datetime
from io import BytesIO
import sys

class RedisManager:
    def __init__(self, local_db, port=6380):
        self.logger = logging.getLogger("LoomLive")
        self.local_db = local_db
        self.upstash_redis = Redis(
            url="https://on-snapper-37126.upstash.io",
            token="AZEGAAIjcDEyNDFkMDA1ZGYxYWM0MDhlOThmZTYzYjllNjZkY2Q3ZHAxMA"
        )
        self.upload_thread = None
        self.is_uploading = False
        self.port = port
 

        # AWS S3 Configuration
        self.s3 = boto3.client(
            's3',
            aws_access_key_id='AKIAYCZSUSO6C4RNWGNA',
            aws_secret_access_key='uu5v26+3PezNaAQsUzKsCElWsXKa7hz3qzkqnW91',
            region_name='ap-northeast-1'  # e.g. 'us-east-1'
        )
        self.bucket_name = 'looms-live'  

        self.temp_upload_thread = None
        self.view_upload_thread = None
        self.is_temp_uploading = False
        self.is_view_uploading = False

    def start_upload(self):
        """Start both upload threads"""
        self.start_temp_upload()
        self.start_view_upload()
        self.logger.info("Both Redis upload threads started")

    def start_temp_upload(self):
        """Start the temp data upload thread"""
        if not self.temp_upload_thread:
            self.is_temp_uploading = True
            self.temp_upload_thread = threading.Thread(target=self._temp_upload_loop, daemon=True)
            self.temp_upload_thread.start()
            self.logger.info("Temp data upload thread started")

    def start_view_upload(self):
        """Start the view data upload thread"""
        if not self.view_upload_thread:
            self.is_view_uploading = True
            self.view_upload_thread = threading.Thread(target=self._view_upload_loop, daemon=True)
            self.view_upload_thread.start()
            self.logger.info("View data upload thread started")

    def stop_upload(self):
        """Stop both upload threads"""
        self.is_temp_uploading = False
        self.is_view_uploading = False
        
        if self.temp_upload_thread:
            self.temp_upload_thread.join(timeout=5)
            self.temp_upload_thread = None
        
        if self.view_upload_thread:
            self.view_upload_thread.join(timeout=5)
            self.view_upload_thread = None
        
        self.logger.info("All upload threads stopped")

    def _temp_upload_loop(self):
        while self.is_temp_uploading:
            try:
                company_name = self.local_db.get_value('company_name')
                client_email = self.local_db.get_value('client_email')

                temp_data = self.local_db.get_temp_data()
                if temp_data:
                    try:
                        enriched_temp_data = {
                            "company_name": company_name,
                            "client_email": client_email,
                            "data": temp_data,
                            "timestamp": time.time()
                        }
                        temp_key = f"temp_data:{company_name}:{client_email}"
                        self.upstash_redis.set(temp_key, json.dumps(enriched_temp_data))
                        self.logger.info(f"Uploaded temp data for {company_name}/{client_email}")
                    except Exception as e:
                        self.logger.error(f"Error uploading temp data: {e}")

                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in temp data upload loop: {e}")
                time.sleep(5)

   

    def _view_upload_loop(self):
        MAX_REDIS_SIZE = 10 * 1024 * 1024  # 10 MB
        while self.is_view_uploading:
            try:
                company_name = self.local_db.get_value('company_name')
                client_email = self.local_db.get_value('client_email')
                screenshots = self.local_db.get_pending_screenshots()
                base_key = f"view:{company_name}:{client_email}"
                groups = []
                group_data = {}
                current_group_size = 0
                group_index = 1

                def flush_group():
                    nonlocal group_index, group_data, current_group_size
                    if not group_data:
                        return
                    group_key = f"{base_key}:group{group_index}"
                    try:
                        json_data = json.dumps(group_data)
                        self.upstash_redis.set(group_key, json_data)
                        self.logger.info(f"Uploaded group {group_index} to Redis: {group_key}")
                        groups.append(f"group{group_index}")  # Store only 'group1', 'group2', etc.
                    except Exception as e:
                        self.logger.error(f"Failed to upload group to Redis: {e}")
                    group_index += 1
                    group_data = {}
                    current_group_size = 0

                for tab_key, image_base64, timestamp in screenshots:
                    try:
                        if isinstance(image_base64, bytes):
                            image_base64 = image_base64.decode("utf-8")
                        if image_base64.startswith("data:image"):
                            image_base64 = image_base64.split(",", 1)[1]
                        
                        image_bytes = b64decode(image_base64.encode('utf-8'))
                        nparr = np.frombuffer(image_bytes, np.uint8)
                        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        
                        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 60]
                        _, compressed_img = cv2.imencode('.jpg', img, encode_params)
                        compressed_base64 = b64encode(compressed_img).decode('utf-8')

                        entry = {
                            "image_data": compressed_base64,
                            "updated_at": timestamp
                        }

                        test_group = dict(group_data)
                        test_group[tab_key] = entry
                        test_json = json.dumps(test_group)

                        if sys.getsizeof(test_json) > MAX_REDIS_SIZE:
                            flush_group()

                        group_data[tab_key] = entry
                        current_group_size = sys.getsizeof(json.dumps(group_data))

                    except Exception as e:
                        self.logger.error(f"Error processing tab screenshot for {tab_key}: {e}")

                # Flush any remaining group
                flush_group()

                # Upload the index (group list)
                if groups:
                    try:
                        self.upstash_redis.set(base_key, json.dumps({"groups": groups}))
                        self.logger.info(f"Uploaded view group index to Redis: {base_key}")
                    except Exception as e:
                        self.logger.error(f"Failed to upload view group index to Redis: {e}")

                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Error in view data upload loop: {e}")
                time.sleep(5)
   
  

    def compress_screenshot(self, image_base64: str) -> bytes:
        try:
            image_bytes = b64decode(image_base64.encode('ascii'))
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
            success, compressed_img = cv2.imencode('.jpg', img, encode_params)

            if success:
                return compressed_img.tobytes()
            return image_bytes
        except Exception as e:
            self.logger.error(f"Error compressing image: {e}")
            return b64decode(image_base64.encode('ascii'))

    # def upload_to_s3(self, image_base64: str, company: str, email: str, tab_key: str) -> str:
    #     try:
    #         if isinstance(image_base64, bytes):
    #             image_base64 = image_base64.decode("utf-8")
    #         if image_base64.startswith("data:image"):
    #             image_base64 = image_base64.split(",", 1)[1]
            
    #         image_bytes = b64decode(image_base64.encode('utf-8'))

    #         filename = f"{tab_key}.jpg"  # No timestamp to overwrite same key
    #         key = f"{company}/{email}/{filename}"

    #         self.s3.upload_fileobj(BytesIO(image_bytes), self.bucket_name, key)
    #         presigned_url = self.s3.generate_presigned_url(
    #             ClientMethod='get_object',
    #             Params={
    #                 'Bucket': self.bucket_name,
    #                 'Key': key
    #             },
    #             ExpiresIn=3600  # seconds
    #         )

    #         return presigned_url
    #     except Exception as e:
    #         self.logger.error(f"Failed to upload image to S3: {e}")
    #         return ""


 
