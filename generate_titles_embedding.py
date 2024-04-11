

import json
from turtle import pd

import numpy as np
from utils.FileUtils import FileUtils
from utils.TextUtils import TextUtils


def main():
    # 读取字典，将字典转化为csv文件
    # 1. 读取字典
    dict_path = 'data/news.sina.com.cn_china__dict copy.json'
    dict_data = FileUtils.read_json_from_file(dict_path)
    # 2. 将字典转化为csv文件
    csv_path = dict_path.replace('.json', '.csv')
    # key: title, value: url, 转化为列表 时间，标题，url
    csv_data = []
    # 添加标题行
    csv_data.append(['time', 'title', 'url'])
    for key, url in dict_data.items():
        time = url.split('/')[4]
        csv_data.append([time, key, url])

    # 3. 保存csv文件
    FileUtils.save_csv_to_file(csv_data, csv_path)

    # 读取 csv 文件，生成标题的embedding
    # 1. 读取csv文件
    csv_data = FileUtils.read_csv_from_file_to_list(csv_path)
    # 2. 生成标题的embedding
    titles = csv_data[1:]  # 去掉标题行

    titles_embedding = []
    for time, title, url in titles:
        title_embedding = TextUtils.embedding_text_by_sentence_transformer(title)
        titles_embedding.append(title_embedding)

    # 将每个嵌入向量转换为列表形式，并存储在一个新的列表中
    embeddings_list = [embedding.tolist() for embedding in titles_embedding]

    # 3. 保存标题的embedding
    embedding_path = dict_path.replace('.json', '_embedding.csv')
    csv_data[0].append('embedding')
    for i, row in enumerate(csv_data[1:]):
        row.append(embeddings_list[i])
    FileUtils.save_csv_to_file(csv_data, embedding_path)


def convert_to_array(x):
    try:
        # 假设每个元素是 JSON 编码的
        return np.array(json.loads(x))
    except:
        # 如果转换失败，返回 None 或适当的默认值
        return None
    
def read_news_csv():
    # 使用默认的 dtype 读取数据，对于数组列先作为字符串读入
    news_data = pd.read_csv('data/links_with_embeddings_sentences_bert.csv', dtype={'date': str, 'title': str, 'link': str, 'embedding': str})
    # 过滤掉 链接包含 video 的新闻
    news_data = news_data[~news_data['link'].str.contains('video')]
    # 将字符串转换为 numpy 数组
    news_data['title_embedding'] = news_data['title_embedding'].apply(convert_to_array)

    return news_data

