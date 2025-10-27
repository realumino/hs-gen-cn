#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import random
import argparse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from DownloadExec import DownloadExec
from ChroSelHandler import ChroHand, SelHand
from Trunc import truncate_filename


class SSScraper:
    def __init__(self, dataset_dir='dataset', chromedriver_path=None):
        """
        初始化SSScraper实例
        
        :param dataset_dir: 数据集存储目录名
        :param chromedriver_path: chromedriver路径
        """
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.dataset_dir = dataset_dir
        self.dataset_path = os.path.join(self.base_dir, '..', dataset_dir)
        self.target_url = "http://gss.customs.gov.cn/clsouter2020/Home/TariffCommentarySearch"
        self.ch_items = []
        
        # 初始化Chrome和Selenium管理器
        self.chro_hand = ChroHand(chromedriver_path)
        self.sel_hand = SelHand(self.chro_hand)
        self.driver = None
        
        # 初始化下载执行器
        self.download_exec = DownloadExec(self.dataset_path)
    
    def create_dataset_directory(self):
        """创建数据集目录"""
        if not os.path.exists(self.dataset_path):
            os.makedirs(self.dataset_path)
            print(f"创建目录: {self.dataset_path}")
        else:
            print(f"目录已存在: {self.dataset_path}")
    
    def init_webdriver(self):
        """初始化WebDriver"""
        self.driver = self.sel_hand.init_webdriver()
    
    def load_page(self):
        """加载目标页面"""
        self.sel_hand.load_page(self.target_url)
        
        # 等待页面加载完成
        try:
            self.sel_hand.wait_for_element(By.ID, "grid", 30)
            print("页面加载完成")
        except Exception as e:
            print(f"页面加载超时: {e}")
            self.sel_hand.close_browser()
            exit(1)
    
    def go_to_last_page(self):
        """获取总页数但不跳转到最后一页"""
        print("正在获取总页数...")
        try:
            # 等待分页控件加载
            self.sel_hand.wait_for_element(By.CSS_SELECTOR, "a[aria-label='末页']", 10)
            
            # 查找最后一页的页码
            last_page_element = self.sel_hand.find_element(By.CSS_SELECTOR, "a[aria-label='末页']")
            last_page = int(last_page_element.get_attribute("data-page"))
            
            print(f"总共有 {last_page} 页")
            return last_page
        except Exception as e:
            print(f"获取总页数失败: {e}")
            return 1
    
    def scrape_pages(self, last_page):
        """智能翻页抓取数据，从第一页开始顺序抓取"""
        page_num = 1  # 从第一页开始
        
        while page_num <= last_page:
            print(f"正在处理第 {page_num} 页...")
            
            # 跳转到指定页码
            try:
                self.sel_hand.execute_script(f"$('#grid').data('kendoGrid').dataSource.page({page_num})")
                time.sleep(3)  # 等待页面加载
            except Exception as e:
                print(f"跳转到第 {page_num} 页失败: {e}")
                break
            
            # 等待表格加载完成
            try:
                self.sel_hand.wait_for_element(By.CSS_SELECTOR, "#grid tbody tr", 10)
            except Exception as e:
                print(f"等待表格加载超时: {e}")
                break
            
            # 获取当前页表格中的所有行
            table_rows = self.sel_hand.find_elements(By.CSS_SELECTOR, "#grid tbody tr")
            print(f"第 {page_num} 页找到 {len(table_rows)} 行数据")
            
            # 检查当前页是否有符合条件的内容
            current_page_has_sc_items = False
            
            # 从前向后遍历
            for i in range(len(table_rows)):
                row = table_rows[i]
                cells = row.find_elements(By.TAG_NAME, "td")
                
                if len(cells) >= 2:
                    tariff_no = cells[0].text.strip()
                    tariff_name = cells[1].text.strip()
                    
                    # 修改筛选逻辑：仅保留子目号列为4位数字的条目
                    if re.match(r'^\d{4}$', tariff_no):
                        current_page_has_sc_items = True
                        
                        # 提取数字部分作为子目号
                        sc_number = tariff_no
                        
                        # 根据子目号列的前两位数字确定子目录
                        prefix = sc_number[:2]
                        
                        # 查找dataset目录中是否存在名称以prefix开头的文件夹
                        sub_dir = None
                        if os.path.exists(self.dataset_path):
                            for item in os.listdir(self.dataset_path):
                                item_path = os.path.join(self.dataset_path, item)
                                if os.path.isdir(item_path) and item.startswith(prefix):
                                    sub_dir = item_path
                                    break
                        
                        # 如果未找到符合条件的文件夹，则跳过此条目
                        if sub_dir is None:
                            print(f"警告: 未找到以'{prefix}'开头的章节目录，跳过条目 {sc_number} - {tariff_name}")
                            continue
                        
                        print(f"找到匹配的章节目录: {sub_dir}")
                        
                        # 文件夹命名格式为"子目号列-子目条文"
                        folder_name = f"{sc_number}-{tariff_name}"
                        # 截断文件夹名以符合操作系统限制
                        folder_name = truncate_filename(folder_name)
                        folder_path = os.path.join(sub_dir, folder_name)
                        
                        # 创建条目文件夹
                        if not os.path.exists(folder_path):
                            os.makedirs(folder_path)
                            print(f"创建条目文件夹: {folder_path}")
                        else:
                            print(f"条目文件夹已存在: {folder_path}")
                        
                        # 构造完整链接
                        base_url = "http://gss.customs.gov.cn"
                        detail_url = f"{base_url}/CLSouter2020/Home/TariffCommentaryDisplay?TariffNo={tariff_no}"
                        
                        # 创建条目信息
                        item = {
                            'number': sc_number,
                            'name': tariff_name,
                            'url': detail_url
                        }
                        
                        print(f"找到符合条件的条目: {tariff_no} - {tariff_name}")
                        
                        # 文件命名格式为"子目号列-子目条文.html"
                        file_name = f"{sc_number}-{tariff_name}.html"
                        # 截断文件名以符合操作系统限制
                        file_name = truncate_filename(file_name)
                        
                        # 检查文件是否已存在，如果存在则跳过下载
                        file_path = os.path.join(folder_path, file_name)
                        if os.path.exists(file_path):
                            print(f"文件已存在，跳过下载: {file_path}")
                        else:
                            # 使用DownloadExec类下载该条目
                            self.download_exec.download_single_item(item, folder_path, file_name)
            
            # 向后翻页
            page_num = page_num + 1
            
            # 如果当前页没有符合条件的内容，继续翻页
            if not current_page_has_sc_items:
                print(f"第 {page_num-1} 页没有符合条件的内容，继续翻页")
                break
        
        print("所有条目处理完成")
    
    def close_browser(self):
        """关闭浏览器"""
        self.sel_hand.close_browser()
    
    def run(self):
        """运行完整的抓取流程"""
        try:
            self.create_dataset_directory()
            self.init_webdriver()
            self.load_page()
            last_page = self.go_to_last_page()
            self.scrape_pages(last_page)  # 从第一页开始顺序抓取
        finally:
            self.close_browser()
            print("任务完成")


def main():
    parser = argparse.ArgumentParser(description='中国海关子目数据抓取工具')
    parser.add_argument('--dataset-dir', default='dataset', help='数据集存储目录名 (默认: dataset)')
    parser.add_argument('--chromedriver-path', help='chromedriver路径')
    
    args = parser.parse_args()
    
    scraper = SSScraper(dataset_dir=args.dataset_dir, chromedriver_path=args.chromedriver_path)
    scraper.run()


if __name__ == "__main__":
    main()