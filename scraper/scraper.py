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
        
        # 初始化请求会话和反爬虫配置
        self.session = self._create_session()
        self.last_request_time = 0
        self.min_interval = 5  # 最小请求间隔(秒)
        self.max_interval = 30  # 最大请求间隔(秒)
        self.base_interval = 10  # 基础请求间隔(秒)
        self.adaptive_factor = 1.0  # 自适应因子
        self.consecutive_failures = 0  # 连续失败次数
    
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
                        
                        # 立即下载该条目
                        self.download_single_item(item)
            
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
    
    def _create_session(self):
        """创建带有重试机制和反爬虫策略的会话"""
        session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

    def _get_random_user_agent(self):
        """生成随机User-Agent"""
        user_agents = [
            # Chrome浏览器
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            # Firefox浏览器
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
            # Safari浏览器
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            # Edge浏览器
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        ]
        return random.choice(user_agents)

    def _get_headers(self):
        """生成完整的请求头信息"""
        return {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': 'http://gss.customs.gov.cn/',
        }

    def _calculate_wait_time(self, success=True, response_time=None):
        """计算动态等待时间"""
        if success:
            self.consecutive_failures = 0
            # 根据响应时间调整等待间隔
            if response_time:
                if response_time < 2:  # 响应很快
                    self.adaptive_factor = max(0.5, self.adaptive_factor * 0.9)
                elif response_time > 10:  # 响应很慢
                    self.adaptive_factor = min(2.0, self.adaptive_factor * 1.2)
        else:
            self.consecutive_failures += 1
            # 连续失败时增加等待时间
            self.adaptive_factor = min(3.0, self.adaptive_factor * 1.5)
        
        # 计算动态间隔
        dynamic_interval = self.base_interval * self.adaptive_factor
        
        # 确保在最小和最大间隔之间
        wait_time = max(self.min_interval, min(dynamic_interval, self.max_interval))
        
        # 添加随机抖动避免规律性
        wait_time += random.uniform(-1, 1)
        
        return max(self.min_interval, wait_time)

    def _wait_before_request(self):
        """在请求前等待适当的时间"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_interval:
            wait_time = self.min_interval - time_since_last_request
            print(f"等待 {wait_time:.1f} 秒后继续...")
            time.sleep(wait_time)

    def download_single_item(self, item):
        """下载单个条目内容"""
        number = item['number']
        name = item['name']
        url = item['url']
        
        # 创建子文件夹
        folder_name = f"{number}-{name}"
        folder_path = os.path.join(self.dataset_path, folder_name)
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"创建子文件夹: {folder_path}")
        else:
            print(f"子文件夹已存在: {folder_path}")
        
        # 请求前等待
        self._wait_before_request()
        
        # 下载网页内容
        try:
            print(f"正在下载: {url}")
            start_time = time.time()
            
            response = self.session.get(
                url, 
                timeout=30,
                headers=self._get_headers()
            )
            
            response_time = time.time() - start_time
            response.encoding = 'utf-8'
            
            # 检查响应状态
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")
            
            # 保存网页内容
            file_name = f"{number}-{name}.html"
            file_path = os.path.join(folder_path, file_name)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"成功保存: {file_path} (响应时间: {response_time:.2f}秒)")
            
            # 计算下一次等待时间
            wait_time = self._calculate_wait_time(success=True, response_time=response_time)
            self.last_request_time = time.time()
            
        except Exception as e:
            print(f"下载失败 {url}: {e}")
            
            # 计算失败后的等待时间
            wait_time = self._calculate_wait_time(success=False)
            self.last_request_time = time.time()
        
        # 动态等待间隔
        print(f"等待 {wait_time:.1f} 秒后继续下一个下载...")
        time.sleep(wait_time)
    
    def download_content(self):
        """为每个条目创建子文件夹并下载网页内容（保持兼容性）"""
        for item in self.ch_items:
            self.download_single_item(item)
    
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
            # download_content方法不再需要调用，因为条目会在scrape_pages中立即下载
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