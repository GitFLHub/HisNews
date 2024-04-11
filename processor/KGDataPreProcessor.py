'''
Descripttion: 
version: 
Author: FengLei
Date: 2024-04-10 13:46:48
LastEditors: Please set LastEditors
LastEditTime: 2024-04-11 15:56:39
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
            self.kg_split_path = config['kgdata_preprocessor']['kg_split_path']

    def clean_news_data(self, column_names):
        # 1. 读取csv文件
        data = FileUtils.read_csv_from_file_to_list(self.ori_data_path,skip_header=False)
        # 2. 清洗数据
        data = CSVUtils.remove_empty_rows_by_column(data, column_names)
        # 3. 保存数据

        # 3.1 获取文件名
        filename = FileUtils.get_filename_from_path(self.ori_data_path)
        FileUtils.save_csv_to_file(data, self.kg_data_path + filename + '_cleaned.csv')

    # 删除列
    def remove_columns(self, column_names):
        # 1. 读取csv文件
        data = FileUtils.read_csv_from_file_to_list(self.ori_data_path, skip_header=False)
        # 获取列的索引
        header_row = data[0]
        column_idxs = [header_row.index(column_name) for column_name in column_names]
        
        # 2. 删除列
        for idx in sorted(column_idxs, reverse=True):
            # 遍历每一行，删除指定列
            for row in data:
                del row[idx]

        # 3. 保存数据
        # 3.1 获取文件名
        filename = FileUtils.get_filename_from_path(self.ori_data_path)
        FileUtils.save_csv_to_file(data, self.kg_data_path + filename + '_removed.csv')

    # 删除列
    def remove_column_by_name(self, data, column_names):
        # 读取列名
        header = data[0]
        # 获取列索引
        column_index = [header.index(column_name) for column_name in column_names]
        # 清除列
        for idx in column_index:
            for row in data:
                row.pop(idx)
        return data
    
    def split_data(self):
        # 读取csv文件
        data = FileUtils.read_csv_from_file_to_dict(self.ori_data_path)
        file_counter = 1  # 计数器，用于追踪新文件编号
        filename_base = FileUtils.get_filename_from_path(self.ori_data_path)
        file_size_limit = 1  # 文件大小限制为 5MB
        
        current_file_index = 1
        text = ""

        # 创建空文件
        FileUtils.save_txt_to_file("", f"{self.kg_split_path}{filename_base}_{current_file_index:02d}.md")
        
        for row in data:
            title = FileUtils.normalize_filename(row['title'])
            content = row['content']
            date = row['time']
            url = row['URL']
            # 构建文本内容
            text += "### Title: " + title + "\n" + "#### Date: " + date + "\n" + "[link](" + url + ")\n" + "#### Content: " + "\n" + content
            # 追加到当前文件
            FileUtils.save_txt_to_file(text, f"{self.kg_split_path}{filename_base}_{current_file_index:02d}.md")
            # 判断文件大小
            file_size = FileUtils.get_file_size(f"{self.kg_split_path}{filename_base}_{current_file_index:02d}.md", 'MB')
            if file_size > file_size_limit:
                # 超过限制，创建新文件
                current_file_index += 1
                FileUtils.save_txt_to_file("", f"{self.kg_split_path}{filename_base}_{current_file_index:02d}.md")
                text = ""
        
        # 处理剩余的内容
        if text:
            FileUtils.save_txt_to_file(text, f"{self.kg_split_path}{filename_base}_{current_file_index:02d}.md")


        

if __name__ == '__main__':
    # KGDataPreProcessor('data\chatchat\chatchat_news_content.csv').clean_news_data(['content', 'title', 'time'])
    # KGDataPreProcessor('data\kg\chatchat_news_content.csv_cleaned.csv').remove_columns(['URL'])
    KGDataPreProcessor('data\kg\chatchat_news_content.csv_cleaned.csv').split_data()
    # AI 在时间轴上带你串历史事件。内容由AI自动生成，不代表本平台立场。如有侵权，请联系删除。
        