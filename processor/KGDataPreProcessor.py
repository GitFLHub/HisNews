'''
Descripttion: 
version: 
Author: FengLei
Date: 2024-04-10 13:46:48
LastEditors: Please set LastEditors
LastEditTime: 2024-04-10 14:13:44
'''
import yaml
from utils.CSVUtils import CSVUtils
from utils.FileUtils import FileUtils


class KGDataPreProcessor():
    def __init__(self, ori_data_path, config_path='config/config.yaml'):
        self.ori_data_path = ori_data_path
        self.load_config(config_path)

    def load_config(self, config_path):
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            self.kg_data_path = config['kgdata_preprocessor']['kg_data_path']

    def clean_news_data(self):
        # 1. 读取csv文件
        data = FileUtils.read_csv_from_file_to_list(self.ori_data_path,skip_header=False)
        # 2. 清洗数据
        data = CSVUtils.remove_empty_rows_by_column(data, ['content', 'title', 'time'])
        # 3. 保存数据

        # 3.1 获取文件名
        filename = FileUtils.get_filename_from_path(self.ori_data_path)
        FileUtils.save_csv_to_file(data, self.kg_data_path + filename + '_cleaned.csv')


if __name__ == '__main__':
    KGDataPreProcessor('data\chatchat\chatchat_news_content.csv').clean_news_data()

        