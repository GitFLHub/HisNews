# 封装了一系列对 archive.org 的操作
import os
from network.NetWorkHandler import NetWorkHandler
from utils.FileUtils import FileUtils
import yaml
class ArchiveHandler:
    def __init__(self, param_url, file_path='', config_path='config/config.yaml'):
        self.param_url = param_url
        self.file_path = file_path
        self.config_path = config_path
        self.netWorkHandler = NetWorkHandler()
        self.load_config()
        if file_path == '':
            self.file_path = f'./data/{NetWorkHandler.get_domian_from_url(param_url)}_{NetWorkHandler.get_path_from_url(param_url)}_urls.txt'

    def check_and_update_urls_file(self):
        # 检查文件是否存在
        if os.path.exists(self.file_path):
            # 文件存在，检查是否需要更新
            local_latest_timestamp,existing_time_stamps = self.get_local_latest_timestamp()
            remote_latest_timestamp = self.get_remote_latest_timestamp()
            new_entries_needed = local_latest_timestamp != remote_latest_timestamp
            if new_entries_needed:
                # 需要更新：添加新的时间戳链接到文件
                print("发现新的时间戳，正在更新文件...")
                self.update_urls_file(local_latest_timestamp, remote_latest_timestamp)
                return self.get_time_stamps_url_from_file(), self.file_path
            else:
                # 不需要更新，直接返回现有的时间戳链接
                print("时间戳链接已是最新，无需更新。")
                return existing_time_stamps, self.file_path
        else:
            # 文件不存在，按照原有逻辑获取时间戳链接并保存
            print("URL记录文件不存在，正在创建并保存最新的时间戳链接...")
            time_stamps = self.get_avaliable_time_stamps()
            urls = self.get_avaliable_urls(time_stamps)
            self.save_urls_file(urls)
            return urls, self.file_path

    def update_urls_file(self, local_latest_timestamp, remote_latest_timestamp):
        # 获取需要添加的时间戳链接
        new_time_stamps = self.get_new_time_stamps(local_latest_timestamp, remote_latest_timestamp)
        # 读取现有的时间戳链接
        existing_time_stamps = FileUtils.read_line_from_file(self.file_path)
        # 添加新的时间戳链接
        new_time_stamps_urls = self.get_avaliable_urls(new_time_stamps)
        existing_time_stamps.extend(new_time_stamps_urls)
        # 保存到文件
        self.save_urls_file(existing_time_stamps)

    def get_new_time_stamps(self, local_latest_timestamp, remote_latest_timestamp):
        # 比较时间戳大小
        if int(local_latest_timestamp) >= int(remote_latest_timestamp):
            return []
        # 获取新的时间戳
        years = self.get_year_list(self.sparkline_url, self.param_url, local_latest_timestamp)
        dates = self.get_month_day_list(self.calendarcaptures_url, self.param_url, years, local_latest_timestamp)
        time_stamps = self.get_time_stamps(self.calendarcaptures_url, self.param_url, dates, local_latest_timestamp)
        return time_stamps



    def load_config(self):
        with open(self.config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        self.sparkline_url = config['archive']['sparkline_url']
        self.calendarcaptures_url = config['archive']['calendarcaptures_url']
        self.perfix = config['data']['perfix']

    def get_year_list(self, url, params_url, timstamp=None):
        fliter_year = 0 if timstamp is None else int(timstamp[:4])
        params = {
            "output": "json",
            "url": params_url,
            "collection": "web"

        }
        json = self.netWorkHandler.send_custom_post_request_with_retry_proxy(url, params)
        # 如果 json 为 None
        if json is None:
            return []
        # 获取年份列表
        year_list = []
        for key in json['years']:
            if int(key) < fliter_year:
                continue
            year_list.append(key)
        return year_list
    
    def get_month_day_list(self, url, params_url, years, timstamp=None):
        fliter_year = 0 if timstamp is None else int(timstamp[:4])
        fliter_month_day = 0 if timstamp is None else int(timstamp[4:8])
        dates = []
        for year in years:
            params = {
                "url": params_url,
                "date": year,
                "groupby": "day"
            }
            json = self.netWorkHandler.send_custom_post_request_with_retry_proxy(url, params)
            # 获取月日列表
            if json is None:
                continue
            for item in json['items']:
                month_day = str(item[0])
                # 不足四位前面补0
                if len(month_day) < 4:
                    month_day = '0'*(4 - len(month_day)) + month_day
                if int(year) == fliter_year and int(month_day) < fliter_month_day:
                    continue
                dates.append(year+month_day)
        return dates
    
    def get_time_stamps(self, url, params_url, dates, timstamp=None):
        fliter_year = 0 if timstamp is None else int(timstamp[:4])
        fliter_month_day = 0 if timstamp is None else int(timstamp[4:8])
        fliter_time_stamp = 0 if timstamp is None else int(timstamp[8:])
        time_stamps = []
        for date in dates:
            params = {
                "url": params_url,
                "date": date
            }
            json = self.netWorkHandler.send_custom_post_request_with_retry_proxy(url, params)
            if json is None:
                continue
            # 获取时间戳
            for item in json['items']:
                stamp = str(item[0])
                # 不足六位用 0 在前面补零
                if len(stamp) < 6:
                    stamp = '0'*(6 - len(stamp)) + stamp
                # fliter_month_day 不足四位前面补0
                datestr = str(fliter_year)+ '0'*(4 - len(str(fliter_month_day))) + str(fliter_month_day)
                if date == datestr and int(stamp) <= fliter_time_stamp:
                    continue
                time_stamps.append(date+stamp)
        return time_stamps
    
    def get_local_latest_timestamp(self):
        try:
            timestamps_urls = FileUtils.read_line_from_file(self.file_path)
            # 假设时间戳已经按照一定的顺序（例如升序）保存，最新的时间戳在文件的最后一行
            latest_timestamps = [int(url.split('/')[4]) for url in timestamps_urls]
            # 时间戳按照大小排序
            return str(max(latest_timestamps)), timestamps_urls
        except FileNotFoundError:
            print(f"文件 {self.file_path} 不存在。")
            return None
        except IndexError:
            print(f"文件 {self.file_path} 是空的。")
            return None
        
    def get_remote_latest_timestamp(self):
        # 获取年份
        years = self.get_year_list(self.sparkline_url, self.param_url)
        if not years:
            return None
        # 获取最后一个年份的月日列表
        yeas = years[-1]
        dates = self.get_month_day_list(self.calendarcaptures_url, self.param_url, [yeas])
        if not dates:
            return None
        # 获取最后一个月日的时间戳列表
        date = dates[-1]
        time_stamps = self.get_time_stamps(self.calendarcaptures_url, self.param_url, [date])
        if not time_stamps:
            return None
        return time_stamps[-1]

    
    def get_avaliable_time_stamps(self):
        years = self.get_year_list(self.sparkline_url, self.param_url)
        dates = self.get_month_day_list(self.calendarcaptures_url, self.param_url, years)
        time_stamps = self.get_time_stamps(self.calendarcaptures_url, self.param_url, dates)
        return time_stamps
    
    def save_urls_file(self, urls):
        FileUtils.write_list_to_file(self.file_path, urls)

    def get_avaliable_urls(self, time_stamps):
        file_lines = []
        for i in range(len(time_stamps)):
            file_lines.append(self.format(time_stamps, i))
        return file_lines

    def format(self, time_stamps, i):
        return f'https://web.archive.org/web/{time_stamps[i]}/{self.param_url}'


    def get_time_stamps_url_from_file(self):
        # 从文件中读取时间戳
        time_stamps = FileUtils.read_line_from_file(self.file_path)
        return time_stamps
    
    def search_avaliable_urls(self):
        # 如果文件存在，直接读链接
        if os.path.exists(self.file_path):
            return self.get_time_stamps_url_from_file(), self.file_path
        time_stamps = self.get_avaliable_time_stamps()
        urls = self.get_avaliable_urls(time_stamps)
        self.save_urls_file(urls)
        return urls, self.file_path




