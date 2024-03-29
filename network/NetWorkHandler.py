import random
import time
import re
import requests
from requests.adapters import HTTPAdapter
from requests.cookies import RequestsCookieJar
from urllib3.util.retry import Retry
import yaml
from lxml import etree
from network.ProxySwitcher import ProxySwitcher

class NetWorkHandler:
    def __init__(self, config_path='config/config.yaml'):
        self.config_path = config_path
        self.headers, self.cookies = self.get_request_header()
        self.request_counter = 0
        self.proxySwitcher = ProxySwitcher()

    def get_request_header(self):
        with open(self.config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        headers = config['network']['headers']
        cookies = RequestsCookieJar()
        cookies.update(config['network']['cookies'])
        self.max_request_tims = config['network']['max_request_tims']
        return headers, cookies
    
    def send_custom_post_request_with_retry_proxy(self, url, params=None, max_retries=3):
        self.dynamic_switch()
        retries = 0
        while retries < max_retries:
            try:
                time.sleep(random.randint(1, 3))  # 随机延迟，减少被识别的风险
                response = requests.post(url, headers=self.headers, cookies=self.cookies, params=params, timeout=10)
                if response.status_code == 200:
                    print("请求成功。" + str(params))
                    return response.json()  # 返回响应的JSON数据
                else:
                    print(f"请求失败，状态码: {response.status_code}。正在尝试重试...")
            except requests.RequestException as e:
                print(f"请求发生异常: {e}。正在尝试重试...")
            
            retries += 1  # 增加重试次数
            if retries == max_retries:
                print("已达到最大尝试次数，停止重试。")
                return None
        return None  # 在所有尝试失败后返回None

    def dynamic_switch(self):
        if self.request_counter >= 15:
            self.proxySwitcher.switch_proxy_auto()  # 确保ProxySwitcher有switch_proxy_auto方法
            self.request_counter = 0
        self.request_counter += 1

    @staticmethod
    def pick_charset(html):
        charset = None
        m = re.compile('<meta .*(http-equiv="?Content-Type"?.*)?charset="?([a-zA-Z0-9_-]+)"?', re.I).search(html)
        if m and m.lastindex == 2:
            charset = m.group(2).lower()
        return charset

    def get_content_from_url(self, url):
        self.dynamic_switch()
        try:
            response = requests.get(url, headers=self.headers, cookies=self.cookies, timeout=10)  
            response.encoding = NetWorkHandler.pick_charset(response.text)
            if response:
                tree = etree.HTML(response.text)
                time.sleep(random.randint(1, 3))
                return tree
            else:
                return None
        except requests.RequestException as e:
            print(f"Error requesting {url}: {e}")
            return None
    @staticmethod
    def get_domian_from_url(url):
        res = ''
        res = url.split('//')[1].split('/')[0] if url.startswith('http') else url.split('/')[0]
        return res.replace('.', '_')
        
    # 获取域名后的路径
    @staticmethod
    def get_path_from_url(url):
        path = url.split('//')[1].split('/', 1)[1] if url.startswith('http') else url.split('/', 1)[1]
        return path.replace('/', '_')
