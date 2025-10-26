#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ChroSelHandler.py - Chrome和Selenium管理器
用于管理所有的Selenium库调用和chromedriver配置
"""

import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


class ChroHand:
    """Chrome浏览器配置管理器"""
    
    def __init__(self, chromedriver_path=None):
        """
        初始化Chrome浏览器配置管理器
        
        :param chromedriver_path: chromedriver路径
        """
        self.chromedriver_path = chromedriver_path
        self.chrome_options = Options()
        self._set_default_options()
    
    def _set_default_options(self):
        """设置默认的Chrome选项"""
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        # 如果需要无头模式可以取消下面这行注释
        # self.chrome_options.add_argument('--headless')
    
    def add_option(self, option):
        """
        添加Chrome选项
        
        :param option: 要添加的选项
        """
        self.chrome_options.add_argument(option)
    
    def get_options(self):
        """
        获取Chrome选项
        
        :return: Chrome选项对象
        """
        return self.chrome_options
    
    def get_service(self):
        """
        获取Chrome服务对象
        
        :return: Service对象或None（如果未指定chromedriver路径）
        """
        if self.chromedriver_path:
            return Service(self.chromedriver_path)
        return None


class SelHand:
    """Selenium操作管理器"""
    
    def __init__(self, chro_hand=None):
        """
        初始化Selenium操作管理器
        
        :param chro_hand: ChroHand实例
        """
        self.chro_hand = chro_hand if chro_hand else ChroHand()
        self.driver = None
    
    def init_webdriver(self):
        """
        初始化WebDriver
        
        :return: WebDriver实例
        """
        print("正在启动浏览器...")
        service = self.chro_hand.get_service()
        options = self.chro_hand.get_options()
        
        if service:
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            self.driver = webdriver.Chrome(options=options)
        
        return self.driver
    
    def load_page(self, url):
        """
        加载指定页面
        
        :param url: 要加载的页面URL
        """
        print(f"正在加载页面: {url}")
        self.driver.get(url)
    
    def wait_for_element(self, by, value, timeout=30):
        """
        等待元素出现
        
        :param by: 定位方式
        :param value: 定位值
        :param timeout: 超时时间（秒）
        :return: WebElement对象
        """
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            print(f"等待元素超时: {e}")
            raise e
    
    def find_elements(self, by, value):
        """
        查找多个元素
        
        :param by: 定位方式
        :param value: 定位值
        :return: WebElement列表
        """
        return self.driver.find_elements(by, value)
    
    def find_element(self, by, value):
        """
        查找单个元素
        
        :param by: 定位方式
        :param value: 定位值
        :return: WebElement对象
        """
        return self.driver.find_element(by, value)
    
    def execute_script(self, script):
        """
        执行JavaScript脚本
        
        :param script: 要执行的JavaScript代码
        :return: 脚本执行结果
        """
        return self.driver.execute_script(script)
    
    def close_browser(self):
        """关闭浏览器"""
        if self.driver:
            self.driver.quit()
            print("浏览器已关闭")
    
    def get_driver(self):
        """
        获取WebDriver实例
        
        :return: WebDriver实例
        """
        return self.driver