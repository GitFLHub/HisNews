
from archive.ArchiveHandler import ArchiveHandler
from scraper.WebScraper import WebScraper
from utils.FileUtils import FileUtils


def main():
    # 1. 获取可用的URL
    url = 'https://news.sina.com.cn/china/'
    archive = ArchiveHandler(url)
    urls, file_path = archive.check_and_update_urls_file()
    # 2. 遍历 Url 获取 a 标签
    sinaWebScrapper = WebScraper(url)
    xpath = "//a"
    fliter_text = ['XXXX']
    links_dict = sinaWebScrapper.scrap_link_by_xpath(urls, xpath, filiter_text=fliter_text)
    file_path = FileUtils.remove_file_extension(file_path)
    a_file_path = f'{file_path}_a_links.json'
    FileUtils.save_json_to_file(links_dict, a_file_path)


if __name__ == '__main__':
    main()
