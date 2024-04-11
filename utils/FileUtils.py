'''
Descripttion: 
version: 
Author: FengLei
Date: 2024-04-09 09:59:51
LastEditors: Please set LastEditors
LastEditTime: 2024-04-11 15:38:35
'''
import os
import json
import logging
import csv
import re
logging.basicConfig(level = logging.INFO,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
class FileUtils:
    @staticmethod
    def read_file(file_path):
        with open(file_path, 'r') as file:
            return file.read()
        
    @staticmethod
    def save_json_to_file(data, file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    # 按行读取文件      
    @staticmethod
    def read_line_from_file(file_path, encoding='utf-8', strip=True, unique=False):
        # 如果文件不存在，返回空列表
        if not os.path.exists(file_path):
            return []
        with open(file_path, 'r', encoding='utf-8') as f:
            links = f.readlines()
        if strip:
            # 去除换行符
            links = [link.strip() for link in links]
        if unique:
            # 去重
            links = list(set(links))
        return links
    
    # 将列表按行写入文件
    @staticmethod
    def write_list_to_file(file_path, data_list):
        with open(file_path, 'w') as f:
            for item in data_list:
                f.write(f"{item}\n")
        msg = f"file save to {file_path}"
        logger.info(msg=msg)

    # 追加行
    @staticmethod
    def append_list_to_file(file_path, data_list):
        with open(file_path, 'a') as f:
            for item in data_list:
                f.write(f"{item}\n")

    @staticmethod
    def remove_file_extension(file_path):
        # 从右侧分割一次，基于最后一个'.'
        base_path, _ = file_path.rsplit('.', 1)
        return base_path
    
    @staticmethod
    def read_json_from_file(file_path):
        # 判断文件是否存在
        if not os.path.exists(file_path):
            return {}
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    
    @staticmethod
    def file_exists(file_path):
        return os.path.exists(file_path)
    
    @staticmethod 
    def save_csv_to_file(data, file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(data)
        logger.info(f"CSV文件已保存至 {file_path}")

    @staticmethod
    def append_csv_to_file(data, file_path):
        with open(file_path, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(data)
        logger.info(f"CSV文件已追加至 {file_path}")

    @staticmethod
    def read_csv_from_file_to_list(file_path, skip_header=True):
        if not os.path.exists(file_path):
            return []
        with open(file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            if skip_header and reader:
                next(reader)
            return list(reader)

    @staticmethod
    def read_csv_from_file_to_dict(file_path):
        if not os.path.exists(file_path):
            return {}
        with open(file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            return list(reader)

    @staticmethod
    def save_txt_to_file(data, file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(data)
        logger.info(f"TXT文件已保存至 {file_path}")
            
        
    @staticmethod
    def get_filename_from_path(file_path):
        return os.path.basename(file_path)
    
    @staticmethod # 规范文件名，去除特殊字符 如 / \ : * ? " < > |
    def normalize_filename(file_path):
        return re.sub(r'[\/:*?"<>|]', '', file_path)
    
    @staticmethod # 获取文件大小 单位默认 KB
    def get_file_size(file_path, unit='KB'):
        size = os.path.getsize(file_path)
        if unit == 'KB':
            return size / 1024
        elif unit == 'MB':
            return size / 1024 / 1024
        elif unit == 'GB':
            return size / 1024 / 1024 / 1024
        else:
            return size
