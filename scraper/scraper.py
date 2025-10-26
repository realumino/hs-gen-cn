#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import random
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from download_exec import DownloadExec


class HSScraper:
    def __init__(self, dataset_dir='dataset', chromedriver_path=None):
        """
        初始化HSScraper实例
        
        :param dataset_dir: 数据集存储目录名
        :param chromedriver_path: chromedriver路径
        """
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.dataset_dir = dataset_dir
        self.dataset_path = os.path.join(self.base_dir, '..', dataset_dir)
        self.chromedriver_path = chromedriver_path
        self.driver = None
        self.target_url = "http://gss.customs.gov.cn/clsouter2020/Home/TariffCommentarySearch"
        self.ch_items = []
        
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
        print("正在启动浏览器...")
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        # chrome_options.add_argument('--headless')  # 如果需要无头模式可以取消注释
        
        # 如果指定了chromedriver路径，则使用指定路径
        if self.chromedriver_path:
            service = Service(self.chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            self.driver = webdriver.Chrome(options=chrome_options)
    
    def load_page(self):
        """加载目标页面"""
        print(f"正在加载页面: {self.target_url}")
        self.driver.get(self.target_url)
        
        # 等待页面加载完成
        try:
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.ID, "grid"))
            )
            print("页面加载完成")
        except Exception as e:
            print(f"页面加载超时: {e}")
            self.driver.quit()
            exit(1)
    
    def go_to_last_page(self):
        """跳转到最后一页"""
        print("正在跳转到最后一页...")
        try:
            # 等待分页控件加载
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[aria-label='末页']"))
            )
            
            # 查找最后一页的页码
            last_page_element = self.driver.find_element(By.CSS_SELECTOR, "a[aria-label='末页']")
            last_page = int(last_page_element.get_attribute("data-page"))
            
            # 跳转到最后一页
            self.driver.execute_script(f"$('#grid').data('kendoGrid').dataSource.page({last_page})")
            time.sleep(3)  # 等待页面加载
            print(f"已跳转到第 {last_page} 页")
            return last_page
        except Exception as e:
            print(f"跳转到最后一页失败: {e}")
            return 1
    
    def scrape_pages(self, last_page):
        """智能翻页抓取数据"""
        page_num = last_page
        
        while True:
            print(f"正在处理第 {page_num} 页...")
            
            # 等待表格加载完成
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#grid tbody tr"))
                )
            except Exception as e:
                print(f"等待表格加载超时: {e}")
                break
            
            # 获取当前页表格中的所有行
            table_rows = self.driver.find_elements(By.CSS_SELECTOR, "#grid tbody tr")
            print(f"第 {page_num} 页找到 {len(table_rows)} 行数据")
            
            # 检查当前页是否有符合条件的内容
            current_page_has_ch_items = False
            
            # 从尾部开始向上遍历
            for i in range(len(table_rows)-1, -1, -1):
                row = table_rows[i]
                cells = row.find_elements(By.TAG_NAME, "td")
                
                if len(cells) >= 2:
                    tariff_no = cells[0].text.strip()
                    tariff_name = cells[1].text.strip()
                    
                    # 检查是否符合CHxx格式
                    if re.match(r'^CH\d{1,2}$', tariff_no):
                        current_page_has_ch_items = True
                        
                        # 提取数字部分
                        ch_number = tariff_no[2:]  # 去掉'CH'前缀
                        
                        # 格式化数字部分（一位数前面补0）
                        formatted_number = ch_number.zfill(2)
                        
                        # 构造完整链接
                        base_url = "http://gss.customs.gov.cn"
                        detail_url = f"{base_url}/CLSouter2020/Home/TariffCommentaryDisplay?TariffNo={tariff_no}"
                        
                        # 创建条目信息
                        item = {
                            'number': formatted_number,
                            'name': tariff_name,
                            'url': detail_url
                        }
                        
                        print(f"找到符合条件的条目: {tariff_no} - {tariff_name}")
                        
                        # 使用DownloadExec类下载该条目
                        self.download_exec.download_single_item(item)
            
            # 如果当前页没有符合条件的内容，则停止翻页
            if not current_page_has_ch_items:
                print(f"第 {page_num} 页没有符合条件的内容，停止翻页")
                break
            
            # 向前翻页
            page_num = page_num - 1
            if page_num < 1:
                print("已到达第一页，停止翻页")
                break
            
            print(f"正在跳转到第 {page_num} 页...")
            try:
                self.driver.execute_script(f"$('#grid').data('kendoGrid').dataSource.page({page_num})")
                time.sleep(3)  # 等待页面加载
            except Exception as e:
                print(f"跳转到第 {page_num} 页失败: {e}")
                break
        
        print("所有条目处理完成")
    
    def close_browser(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            print("浏览器已关闭")
    
    def run(self):
        """运行完整的抓取流程"""
        try:
            self.create_dataset_directory()
            self.init_webdriver()
            self.load_page()
            last_page = self.go_to_last_page()
            self.scrape_pages(last_page)
        finally:
            self.close_browser()
            print("任务完成")


def main():
    parser = argparse.ArgumentParser(description='中国海关HS编码数据抓取工具')
    parser.add_argument('--dataset-dir', default='dataset', help='数据集存储目录名 (默认: dataset)')
    parser.add_argument('--chromedriver-path', help='chromedriver路径')
    
    args = parser.parse_args()
    
    scraper = HSScraper(dataset_dir=args.dataset_dir, chromedriver_path=args.chromedriver_path)
    scraper.run()


if __name__ == "__main__":
    main()