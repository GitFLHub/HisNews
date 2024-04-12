import re
import random
import time
from requests import Session, RequestException
from tqdm import tqdm
from urllib3 import Retry
from network.ProxySwitcher import ProxySwitcher
import logging
from lxml import etree 
from typing import Union, List
import yaml
from utils.TextUtils import TextUtils
from network.NetWorkHandler import NetWorkHandler
from utils.FileUtils import FileUtils


logging.basicConfig(level = logging.INFO,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
class WebScraper:
    def __init__(self,base_url, config_path='config/config.yaml'):
        self.request_counter = 0
        self.load_config(config_path)
        self.base_url = base_url
        self.netWorkHandler = NetWorkHandler()
        # Generate file_path based on base_url
        domain_specific_part = self.base_url.replace("https://", "").replace("/", "_").replace("*", "").replace(":", "").replace("?", "").replace("=", "").replace("&", "")
        self.file_path = f'./{domain_specific_part}_links.json'
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        self.processed_links_file = f'./data/{domain_specific_part}_processed_links.txt'  # 定义日志文件路径
        self.processed_links = self.get_processed_links()  # 读取已处理链接
        self.link_dict_path = f'./data/{domain_specific_part}_dict.json'  # 定义日志文件路径

    def get_processed_links(self):
        # 读取已处理链接
        return FileUtils.read_line_from_file(self.processed_links_file)
    def write_processed_link(self, link):
        if isinstance(link, str):
            link = [link]
        # 将已处理链接写入文件
        FileUtils.append_list_to_file(self.processed_links_file, link)

    def write_processed_data(self, data):
        # 将已获得的数据写入文件
        FileUtils.save_json_to_file(data, self.link_dict_path)

    def load_config(self, config_path):
        # 从YAML文件加载配置
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        self.need_switch_proxy = config.get('need_switch_proxy', False)
        self.filiter_text = config['scraper'].get('stop_words', [])
    @staticmethod
    def link_filter(links, stop_words):
        filtered_links = []
        for link in links:
            href = link.get('href')
            text = link.get_text().strip()
            if len(text) < 5 or not href or any(word in text for word in stop_words):
                continue
            filtered_links.append((text, href))
        return filtered_links
    
    def parse_conditions(self, conditions_str):
        """
        解析条件字符串，返回标签和条件列表。
        """
        res = {}
        # 判断是否有中括号，如果没有，则返回标签
        if '[' not in conditions_str:
            # 使用 tag 做key 和 conditions 做value
            return {tag: [] for tag in conditions_str.split(',')}
        # 如果有中括号，则解析条件, 例如 "a[href:in('example.com'),text:not in('Archive')],img[src:in('example.com')]"
        # 先分割中括号外的逗号
        for tag_conditions in re.split(re.compile(r',(?![^\[]*\])'), conditions_str):
            # 再分割中括号内的条件
            if '[' not in tag_conditions:
                 res[tag_conditions] = []
                 continue
            tag, conditions_part = tag_conditions.split('[', 1)
            conditions_part = conditions_part.rstrip(']')
            conditions = []
            # 分割小括号外的逗号 如 "href:in('example.com'),text:not in('Archive')" 中的 ),
            for condition in re.split(re.compile(r',(?![^\(]*\))'), conditions_part):
                attr, operation_value = condition.split(':', 1)
                operation, value = operation_value.split('(', 1)
                value = value.rstrip(')').replace("'", "").replace('"', '')
                # 如果 value 包含逗号，则需要转换成列表
                if ',' in value:
                    value = value.split(',')
                conditions.append({'attr': attr, 'operation': operation, 'value': value})
            res[tag] = conditions
        return res

    def filter_elements_by_tags(self, soup, tag_conditions_dict):
        """
        根据提供的标签和条件字典过滤整个文档的元素。
        """
        all_filtered_elements = {}

        for tag, conditions in tag_conditions_dict.items():
            # 针对每个标签，找到所有对应的元素
            elements = soup.find_all(tag)
            # 使用 filter_elements_of_tag 方法过滤这些元素
            filtered_elements = self.filter_elements_of_tag(elements, conditions)
            # 将过滤后的元素添加到最终结果列表
            all_filtered_elements[tag] = filtered_elements
        
        return all_filtered_elements

    def filter_elements_of_tag(self, elements, conditions):
        """
        根据提供的条件过滤元素列表。
        """
        filtered_elements = []

        for element in elements:
            match = True  # 假设当前元素满足所有条件
            for condition in conditions:
                attr = condition['attr']
                operation = condition['operation']
                condition_values = condition['value']  # 条件值，可能是一个值或值的列表
                # 获取元素的属性值或文本内容
                if attr == 'text':
                    element_value = element.get_text()
                else:
                    element_value = element.get(attr, "")
                # 处理单个值和列表值的情况
                if not isinstance(condition_values, list):
                    condition_values = [condition_values]  # 将单个值转换为列表以统一处理

                if operation in ['>', '<']:
                    try:
                        element_value = float(element_value)
                        condition_values = float(condition_values[0])
                    except ValueError:
                        # 如果转换失败，可以选择如何处理：这里选择跳过此条件
                        match = False
                        continue


                # 根据操作执行不同的过滤逻辑
                if operation == 'in':
                    match = element_value in condition_values
                elif operation == 'not in':
                    match = element_value not in condition_values
                elif operation == 'contains':
                    match = all(value in element_value for value in condition_values)
                elif operation == 'not contains':
                    match = all(value not in element_value for value in condition_values)
                elif operation == 'start with':
                    match = element_value.startswith(condition_values[0])
                elif operation == 'end with':
                    match = element_value.endswith(condition_values[0])
                elif operation == 're':
                    match = all(re.search(value, element_value) for value in condition_values)
                elif operation == '>':
                    match = float(element_value) > float(condition_values)
                elif operation == '<':
                    match = float(element_value) < float(condition_values)
                elif operation == '=':
                    match = element_value == condition_values
                if not match:
                    # 如果任一条件不满足，则当前元素不匹配
                    break
            if match:
                # 如果元素满足所有条件，将其添加到过滤后的列表中
                filtered_elements.append(element)
        return filtered_elements

    def scrape(self, url, tag_conditions, collect_key = 'text', collect_values=['href']):
        # 判断 url 是否为 字符串
        if isinstance(url, str):
           url = [url]
        links_dict = {}
        # 解析 tag_conditions 来进行筛选
        conditions = self.parse_conditions(tag_conditions)
        for u in tqdm(url, desc="Processing URLs") if len(url) > 5 else url:
            url_items = []
            soup = self.get_content_from_url(u)
            if soup is None:
                continue
            filtered_elements_dict = self.filter_elements_by_tags(soup, conditions)
            # 从筛选后的元素中提取链接或其他信息
            for tag, filtered_elements in filtered_elements_dict.items():
                element_dict_of_tag = {}
                for element in filtered_elements:
                    element_item = {}
                    key = element.get(collect_key, "") if collect_key != 'text' else element.get_text()
                    for value in collect_values:
                        element_item[key] = element.get_text() if value == 'text' else element.get(value, "")
                    if len(element_item.keys()) > 0:
                        url_items.append(element_item)
                element_dict_of_tag[tag] = url_items
            if len(element_dict_of_tag.keys()) > 0:
                links_dict[u] = element_dict_of_tag
        self.save_links_to_file(links_dict, self.file_path)
        msg = f"Scraping complete, {len(links_dict)} links saved to {self.file_path}"
        logger.info(msg=msg)
        return links_dict
    
    def extract_text(self, element: Union[etree._Element, List[etree._Element]]) -> Union[str, List[str]]:
        """
        递归地从 lxml.etree._Element 或 List[lxml.etree._Element] 中提取所有文本内容。
        
        参数:
            element: 单个 lxml.etree._Element 对象或它们的列表。
        
        返回:
            单个字符串或字符串列表，取决于输入是单个 Element 还是 Element 的列表。
        """
        if isinstance(element, list):
            # 处理元素列表
            text_list = [self.extract_text(child) for child in element]
            # 合并文本并返回
            return ' '.join(filter(None, text_list))
        elif isinstance(element, etree._Element):
            # 如果是注释 或者 a 标签，图片链接等，直接返回空字符串
            if isinstance(element, etree._Comment) or element.tag in ['a', 'img', 'script', 'style']:
                return ''
            # 处理单个元素
            text_list = [element.text] if element.text is not None else []
            
            # 递归处理所有子元素
            for child in element:
                text_list.append(self.extract_text(child))
            
            # 合并文本并返回
            return ' '.join(filter(None, text_list))
        else:
            return ''

    # 按行存储，检查行文件是否存在
    def scrap_text_by_xpath(self, urls, xpath_dict, save_path=None, with_img=True, img_stop_keywords=[]):
        # TODO: 删除这段代码
        urls = self.param_list_format(urls)
        scrap_res = []
        processed_url = [] 
        if save_path and FileUtils.file_exists(save_path):
            saveed_csv_data = FileUtils.read_csv_from_file_to_list(save_path)
            # 读取第一列数据
            processed_url = [row[0] for row in saveed_csv_data]

        # 如果文件不存在，创建一个 header 文件，第一列为 URL
        if save_path and not FileUtils.file_exists(save_path):
            FileUtils.save_csv_to_file([['URL'] + list(xpath_dict.keys()) + ([] if not with_img else ['image'])], save_path)

        batch_size = 12
        # 从 index 开始处理
        for i in tqdm(range(0, len(urls)), desc="Processing URLs") if len(urls) > 5 else range(0, len(urls)):
            if urls[i] in processed_url:
                continue
            u = urls[i]
            soup = self.netWorkHandler.get_content_from_url(u)
            if soup is None:
                # 添加空行
                scrap_res.append([u] + ['链接无法访问'] + [''] * (len(xpath_dict) - 1) + [''])
                continue
            text_list = []
            img_list = []
            # 遍历 xpath_dict
            for tag, xpaths in xpath_dict.items():
                item = ''
                for xpath in xpaths:
                    elements = soup.xpath(xpath)
                    text = TextUtils.clean_text(self.extract_text(elements))
                    # 尝试提取图片链接
                    if with_img and len(elements) > 0:
                        img_list += self.extract_imgs(soup, xpath, img_stop_keywords)
                    if not text:
                        text = ''
                    item += text
                text_list.append(item)
            # 记录 URL 和提取的各个字段 u,标题,时间,正文
            scrap_res.append([u] + text_list + [';'.join(img_list)])
            # scrap_res.append(text_list.join(' '))
            if (i+1) % batch_size == 0:
                # 每处理12个链接保存一次数据
                FileUtils.append_csv_to_file(scrap_res, save_path)
                scrap_res = []
        if len(scrap_res) > 0:
            # 保存剩余的数据
            FileUtils.append_csv_to_file(scrap_res, save_path)
            scrap_res = []

    def extract_imgs(self, soup, xpath, img_stop_keywords=[]):
        # 组装 img_xpath 如果 xpath 以 // p 结尾，则替换 p 为 img, 否则添加 //img
        img_xpath = xpath.replace('//p', '//img') if xpath.endswith('//p') else xpath + '//img'
        imgs = []
        elements = soup.xpath(img_xpath)
        imgs = [img.get('src') for img in elements if self.need_save_img(img, img_stop_keywords)]
        return imgs
    
    # 判断图片是否需要保存链接
    def need_save_img(self, img, img_stop_keywords):
        # 判断是否存在 src 属性，如果不存在，则跳过
        if img.get('src') == None or any(word in img.get('src') for word in img_stop_keywords):
            return False
        # 如果存在高度属性且高度小于 50：则跳过
        if img.get('height') != None:
            # 高度像素匹配 可能为 67.98px 或者 67px
            match = re.search(r'\d+(\.\d+)?', img.get('height'))
            if match and int(float(match.group())) < 50:
                return False
        return True
    def load_links_dict_from_json(self):
        return FileUtils.read_json_from_file(self.link_dict_path)

    def scrap_link_by_xpath(self, urls, xpaths, filiter_text=[]):
        self.filiter_text.append(filiter_text)
        urls = self.param_list_format(urls)
        xpaths = self.param_list_format(xpaths)
        links_dict = self.load_links_dict_from_json()  # 尝试加载已保存的链接字典
        times = 0
        processed_links_batch = []
        for u in tqdm(urls, desc="Processing URLs") if len(urls) > 5 else urls:
            if u in self.processed_links:
                continue  # 如果URL已处理，跳过
            times += 1
            try:
                soup = self.netWorkHandler.get_content_from_url(u)
                if soup is None:
                    continue
                for xpath in xpaths:
                    # 执行XPath查询找到链接
                    elements = soup.xpath(xpath)
                    for link in elements:
                        href = link.get('href')
                        text = link.text
                        text = text.strip() if text is not None else ''
                        if href and text !='' and text not in self.filiter_text:
                            if not href.startswith('http'):
                                href = 'https://web.archive.org/web/' + href
                            links_dict[text] = href
                processed_links_batch.append(u)
                if times % 12 == 0:
                    # 每处理12个链接保存一次数据
                    self.write_processed_data(links_dict)
                    self.write_processed_link(processed_links_batch)
                    processed_links_batch = []
            except Exception as e:
                print(f"Error processing {u}: {e}")
        if len(processed_links_batch) > 0:
            # 保存剩余的数据
            self.write_processed_data(links_dict)
            self.write_processed_link(processed_links_batch) 
            processed_links_batch = []
        return links_dict
    
    # 如果参数为空，则返回空列表，如果是字符串，则返回列表。返回 tuple,如果 params 只有一个参数，tuple 会被解包
    def param_list_format(self, param):
        if param is None:
            return []
        if isinstance(param, str):
            return [param]
        if isinstance(param, list):
            return param
    
    def remove_archive_prefix(self, urls):
        # 匹配 任意字符 + '连续 14 位数字/'，分割时间戳以后的部分
        timeStamp = re.compile(r'.*\d{14}/')
        # 如果url中包含时间戳，则取时间戳之后的部分
        urls = [re.sub(timeStamp, '', url) for url in urls]
        return urls

def test():
    url1 = 'https://web.archive.org/web/20180305154649/http://news.sina.com.cn/o/2018-03-05/doc-ifyrztfz8616083.shtml'
    url2 = 'https://web.archive.org/web/20180111065834/http://news.sina.com.cn/c/nd/2018-01-11/doc-ifyqnick5207416.shtml'
    url3 = 'https://web.archive.org/web/20180111065834/http://news.sina.com.cn/c/gat/2018-01-11/doc-ifyqqieu5713403.shtml'
    url4 = 'https://web.archive.org/web/20180130192503/http://news.sina.com.cn/c/nd/2018-01-31/doc-ifyqyqni5646905.shtml'
    sinaWebScrapper = WebScraper(url1)
    xpath_dict = {
        'title': ['//h1[@class="main-title"]'],
        'time': ['//div[@class="date-source"]'],
        'content': ['//div[@class="article"]//p']
    }
    urls = sinaWebScrapper.param_list_format([url1, url2, url3, url4])
    # urls = 'https://web.archive.org/web/20211223055947/https://www.ron.zone'
    links_dict = sinaWebScrapper.scrap_text_by_xpath(urls=urls, xpath_dict=xpath_dict, save_path='./data/sina_news_text.csv', with_img=True, img_stop_keywords=['logo', 'icon'])
    print(links_dict)

# if __name__ == '__main__':
#     test()


