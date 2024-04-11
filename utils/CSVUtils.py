'''
Descripttion: 
version: 
Author: FengLei
Date: 2024-04-10 13:44:02
LastEditors: Please set LastEditors
LastEditTime: 2024-04-10 14:10:36
'''

class CSVUtils():
    def __init__(self):
        pass

    # 删除指定列名为空的行
    @staticmethod
    def remove_empty_rows_by_column(data, column_names):
        # 读取列名
        header = data[0]
        # 获取列索引
        column_index = [header.index(column_name) for column_name in column_names]
        # 删除字段为空的行
        data = [row for row in data if all([row[idx] for idx in column_index])]
        return data

    
    
