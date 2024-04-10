import os
import requests
import random
import time
import yaml

from aop.decorators import proxy_switcher_decorator

class ProxySwitcher:
    def __init__(self, config_path='config/config.yaml'):
        self.load_config(config_path)
        self.load_clash_host_config()  # 加载宿主机Clash配置
        # self.setup_system_proxy()

    def load_clash_host_config(self):
        # 指定宿主机Clash配置文件的路径
        clash_config_path = self.clash['clash_config_path']
        try:
            with open(clash_config_path, 'r', encoding='utf-8') as file:
                clash_config = yaml.safe_load(file)
            external_controller = clash_config.get('external-controller', '127.0.0.1:9090')
            self.clash['clash_host'], self.clash['clash_port'] = external_controller.split(':')
        except Exception as e:
            print(f"读取宿主机Clash配置文件时发生错误: {e}")


    def load_config(self, config_path):
        # 从YAML文件加载配置
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        
        self.system_proxy = config.get('system_proxy', {})
        self.clash = config['clash']
        self.ip_pool_host = config['network']['proxy']['ip_pool_host']
        self.ip_pool_port = config['network']['proxy']['ip_pool_port']
        self.ip_pool_size = config['network']['proxy']['ip_pool_size']
    @staticmethod
    def setup_system_proxy():
        # 获取默认路由网关地址, 宿主机 ip
        ip = os.popen("ip route show | grep -i default | awk '{ print $3}'").read().strip()
        # 设置代理，使用从YAML文件读取的配置
        ip = '127.0.0.1' if ip == '' else ip
        http_proxy = f'http://{ip}:7890'
        https_proxy = f'http://{ip}:7890'
        if http_proxy:
            os.environ["HTTP_PROXY"] = http_proxy
        if https_proxy:
            os.environ["HTTPS_PROXY"] = https_proxy

    def get_proxies(self):
        """
        从 Clash API 获取代理节点信息。
        """
        clash_api_url = f'http://{self.clash["clash_host"]}:{self.clash["clash_port"]}/proxies/{self.clash.get("selector","")}'
        try:
            response = requests.get(clash_api_url)
            proxies_info = response.json()
            return proxies_info
        except Exception as e:
            print(f"获取代理节点信息时发生错误: {e}")
            return {}
        
    def switch_proxy(self, proxies_info):
        """
        根据提供的代理信息切换到一个具有较低延迟的代理节点。
        """
        current_proxy = proxies_info['now']
        all_proxies = proxies_info['all'][5:]  # 移除 indx [0~4]，假设这部分包含了不可用的或特殊的代理节点

        # 排除当前节点
        if current_proxy in all_proxies:
            all_proxies.remove(current_proxy)

        new_proxy = ''
        selector_time = 0
        while selector_time < 8:
            new_proxy = random.choice(all_proxies)
            clash_api_url = f'http://{self.clash["clash_host"]}:{self.clash["clash_port"]}/proxies/{self.clash.get("selector","")}/delay'
            data = {"name": new_proxy, "timeout": 500, "url": "https://www.google.com"}
            response = requests.get(clash_api_url, params=data)
            if response.status_code == 200:
                delay = response.json()['delay']
                print(f"节点 {new_proxy} 延迟: {delay} ms")
                if delay < 400:
                    break
                # 等待 1 秒
                time.sleep(1)
            else:
                print(f"获取节点 {new_proxy} 延迟过高，延迟: {response.status_code}")
                selector_time += 1
        
        # 切换节点
        clash_api_url = f'http://{self.clash["clash_host"]}:{self.clash["clash_port"]}/proxies/{self.clash.get("selector","")}'
        data = {"name": new_proxy}
        response = requests.put(clash_api_url, json=data)
        if response.status_code == 204:
            print(f"成功切换代理节点: {current_proxy} -> {new_proxy}")
        else:
            print(f"切换代理节点失败: {response.status_code}")

    @proxy_switcher_decorator
    def switch_proxy_auto(self):
        """
        自动获取当前可用的代理节点并切换。
        """
        while True:
            proxies_info = self.get_proxies()
            if proxies_info:
                self.switch_proxy(proxies_info)
                break
            time.sleep(5)

    @proxy_switcher_decorator
    def get_proxy_from_api(self):
        os.environ["HTTP_PROXY"] = f'http://{self.ip_pool_host}:{self.ip_pool_port}'
        data = requests.get(f"http://{self.ip_pool_host}:{self.ip_pool_port}/get/").json()
        return data.get("proxy") if data else None
    
    @proxy_switcher_decorator
    def delete_proxy_from_api(self, proxy):
        requests.get(f"http://{self.ip_pool_host}:{self.ip_pool_port}/delete/?proxy={proxy}")


# 使用示例
ProxySwitcher.setup_system_proxy()
# proxy_switcher = ProxySwitcher()
# proxy_switcher.switch_proxy_auto()
