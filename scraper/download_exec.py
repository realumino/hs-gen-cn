#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import random
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class DownloadExec:
    """专门负责执行文件下载任务的类"""
    
    def __init__(self, base_dataset_path, min_interval=5, max_interval=30, base_interval=10):
        """
        初始化DownloadExec实例
        
        :param base_dataset_path: 基础数据集路径
        :param min_interval: 最小请求间隔(秒)
        :param max_interval: 最大请求间隔(秒)
        :param base_interval: 基础请求间隔(秒)
        """
        self.base_dataset_path = base_dataset_path
        self.session = self._create_session()
        self.last_request_time = 0
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.base_interval = base_interval
        self.adaptive_factor = 1.0  # 自适应因子
        self.consecutive_failures = 0  # 连续失败次数
    
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
        """
        下载单个条目内容
        
        :param item: 包含number, name, url的字典
        :return: 下载是否成功
        """
        number = item['number']
        name = item['name']
        url = item['url']
        
        # 创建子文件夹
        folder_name = f"{number}-{name}"
        folder_path = os.path.join(self.base_dataset_path, folder_name)
        
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
            
            # 动态等待间隔
            print(f"等待 {wait_time:.1f} 秒后继续下一个下载...")
            time.sleep(wait_time)
            
            return True
            
        except Exception as e:
            print(f"下载失败 {url}: {e}")
            
            # 计算失败后的等待时间
            wait_time = self._calculate_wait_time(success=False)
            self.last_request_time = time.time()
            
            # 动态等待间隔
            print(f"等待 {wait_time:.1f} 秒后继续下一个下载...")
            time.sleep(wait_time)
            
            return False