import logging
import os
import sys
from datetime import datetime

def setup_logger():
    # Get the base directory for logs
    log_root = os.path.join(os.getenv("APPDATA"), "Looms Live")
    # Create logs directory
    log_dir = os.path.join(log_root, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建日志记录器
    logger = logging.getLogger("LoomLive")
    logger.setLevel(logging.DEBUG)
    
    # 创建控制台处理程序，并指定编码为 utf-8
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    # console_handler.stream.reconfigure(encoding='utf-8')  # 确保控制台输出使用 utf-8 编码
        # Safely reconfigure encoding
    if console_handler.stream and hasattr(console_handler.stream, 'reconfigure'):
        console_handler.stream.reconfigure(encoding='utf-8')
    
    # 创建文件处理程序，并指定编码为 utf-8
    log_file = os.path.join(log_dir, f"loom_live_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')  # 指定文件编码为 utf-8
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # 添加处理程序到记录器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger