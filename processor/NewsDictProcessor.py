import csv
import json
import os

import numpy as np
import torch
import yaml
from scraper.WebScraper import WebScraper
from utils.FileUtils import FileUtils
import logging

from utils.TextUtils import TextUtils
from utils.TorchUtils import TorchUtils
logging.basicConfig(level = logging.INFO,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NewsDictProcessor:
    def __init__(self, dict_path, domain=None, config_path='config/config.yaml'):
        self.dict_path = dict_path
        self.load_config(config_path)
        self.csv_path = FileUtils.remove_file_extension(dict_path) + '.csv'
        self.embedding_csv_path = FileUtils.remove_file_extension(dict_path) + '_embedding.csv'
        self.news_content_save_path = FileUtils.remove_file_extension(dict_path) + '_content.csv'
        self.web_scraper = WebScraper(domain)

    def load_config(self, config_path):
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        self.xpath_dict = config['news']['xpath_dict']
        self.scrap_img = config['news']['scrap_img']
        self.img_stop_keywords = config['news']['img_stop_keywords']
    def dict_to_csv(self):
        """将新闻字典转换为CSV文件"""
        if FileUtils.file_exists(self.csv_path):
            logger.info(f"CSV文件 {self.csv_path} 已存在")
            return
        dict_data = FileUtils.read_json_from_file(self.dict_path)
        csv_data = [['time', 'title', 'url']]
        for title, url in dict_data.items():
            time = url.split('/')[4]  # 假设URL结构中的时间部分可以如此获取
            if time is None or time=='':
                continue
            csv_data.append([time.strip(), TextUtils.clean_text(title.strip()), url.strip()])
        self._save_csv(csv_data, self.csv_path)

    def _save_csv(self, data, path):
        """保存数据到CSV文件"""
        if FileUtils.file_exists(path):
            logger.info(f"CSV文件 {path} 已存在")
            return
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(data)
        logger.info(f"CSV文件已保存至 {path}")

    # 以下为示例性的额外功能，具体实现依赖于你的需求
    def generate_embeddings_and_save(self):
        """生成新闻标题的嵌入向量并保存，这需要你自己实现嵌入向量的生成逻辑"""
        # 判断CSV文件是否存在
        if FileUtils.file_exists(self.embedding_csv_path):
            logger.info(f"嵌入向量文件 {self.embedding_csv_path} 已存在")
            return
        if not FileUtils.file_exists(self.csv_path):
            self.dict_to_csv()
        csv_data = FileUtils.read_csv_from_file(self.csv_path)
        titles = csv_data[1:]
        titles_embedding = TextUtils.batch_embedding_text_by_sentence_transformer([title for _, title, _ in titles])
        embeddings_list = [embedding.tolist() for embedding in titles_embedding]
        self.add_csv_column(csv_data, embeddings_list,'embedding')
        self._save_csv(csv_data, self.embedding_csv_path)
        logger.info(f"嵌入向量已保存至 {self.embedding_csv_path}")

    def add_csv_column(self, csv_data, embeddings_list, name):
        csv_data[0].append(name)
        for i, row in enumerate(csv_data[1:]):
            row.append(embeddings_list[i])

    
    # 根据输入的文本，计算与标题的相似度，并返回排序后的索引
    def calculate_similarity(self, text: str):
        """计算输入文本与标题的相似度，并返回排序后的索引"""
        if not os.path.exists(self.embedding_csv_path):
            logger.error(f"嵌入向量文件 {self.embedding_csv_path} 不存在，请先调用 generate_embeddings_and_save 方法生成")
            return
        csv_data = FileUtils.read_csv_from_file(self.embedding_csv_path)
        titles_embedding = [TorchUtils.convert_to_array(embedding) for _, _, _, embedding in csv_data[1:]]
        input_embedding = TextUtils.embedding_text_by_sentence_transformer(text)
        cosine_similarity = TextUtils.calculate_cosine_similarity_batch(input_embedding, titles_embedding)
        return TextUtils.sort_similarity_index(cosine_similarity)
    
    # 获得相关性最高的前 n 个新闻时间，标题和链接
    def get_most_similar_news(self, text: str, n=10):
        """获取与输入文本相关性最高的新闻标题和链接"""
        sorted_index = self.calculate_similarity(text)
        csv_data = FileUtils.read_csv_from_file(self.csv_path)
        csv_data = csv_data[1:]
        result = []
        for idx in sorted_index[:n]:
            result.append(csv_data[idx])
        return result
    
    # 爬取新闻内容
    def scrape_news_content(self, url, xpath, filiter_text=None, suffix=None):
        """爬取新闻内容"""
        urls, xpath = self.web_scraper.param_list_format(url, xpath)
        self.xpath.append(xpath)
        res = self.web_scraper.scrap_text_by_xpath(urls, self.xpath, filiter_text=filiter_text, merge_results=True)
        return res
    
    # 爬取指定 url 并保存新闻内容在一个 txt 文件中
    def scrape_and_save_news_content(self, url, xpath, filiter_text=None, save_path=None, suffix='content'):
        """爬取并保存新闻内容"""
        res = self.scrape_news_content(url, xpath, filiter_text, suffix)
        if save_path is None:
            save_path = FileUtils.remove_file_extension(self.dict_path) + f'_{suffix}.txt'
        FileUtils.save_json_to_file(save_path, res)
        return res
    
    # 爬取所有的新闻内容
    def scrape_and_save_all_news_of_domain(self, xpath_dict=None, filiter_text=None, remove_archive=False):
        csv_data = FileUtils.read_csv_from_file(self.csv_path)
        """爬取新闻内容"""
        urls = [data[2] for data in csv_data[1:]]
        # url https://web.archive.org/web/20240322101215/https://news.sina.com.cn/china/ 去掉 https://web.archive.org/web/20240322101215/
        if remove_archive:
            urls = self.web_scraper.remove_archive_prefix(urls)
        urls = self.web_scraper.param_list_format(urls)
        # 如果xpath为空，则使用默认的xpath
        if xpath_dict is not None:
            # list 合并
            self.xpath_dict = xpath_dict

        image_stop_keywords = self.img_stop_keywords
        contents = self.web_scraper.scrap_text_by_xpath(urls, self.xpath_dict, save_path=self.news_content_save_path,img_stop_keywords=image_stop_keywords)

        self.add_csv_column(csv_data, contents,'content')
        self._save_csv(csv_data, self.news_content_save_path)
        logger.info(f"新闻内容保存至 {self.news_content_save_path}")

    
    # 存储新闻内容
    def save_related_news_content(self, text):
        data = self.get_most_similar_news(text)
        # 爬取新闻内容
        urls = [i[2] for i in data]
        content = self.scrape_and_save_news_content(urls, '//*[@id="artibody"]', 'https://news.sina.com.cn/china/content')
        FileUtils.write_list_to_file(content)
        return content



# 使用示例
# 创建 NewsDictProcessor 实例
processor = NewsDictProcessor('data/news.sina.com.cn_china__dict.json', 'news.sina.com.cn/china')
# 将字典转换为CSV
processor.dict_to_csv()
# 获取所有新闻的内容
processor.scrape_and_save_all_news_of_domain()
# 生成嵌入向量并保存
processor.generate_embeddings_and_save()
# 计算相似度
processor.save_related_news_content('小米新闻发布会')




