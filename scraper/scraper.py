import os
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import requests

# 创建dataset目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, 'dataset')

if not os.path.exists(DATASET_DIR):
    os.makedirs(DATASET_DIR)
    print(f"创建目录: {DATASET_DIR}")
else:
    print(f"目录已存在: {DATASET_DIR}")

# 配置Chrome选项
chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
# chrome_options.add_argument('--headless')  # 如果需要无头模式可以取消注释

# 初始化WebDriver
print("正在启动浏览器...")
driver = webdriver.Chrome(options=chrome_options)

# 打开目标页面
target_url = "http://gss.customs.gov.cn/clsouter2020/Home/TariffCommentarySearch"
print(f"正在加载页面: {target_url}")
driver.get(target_url)

# 等待页面加载完成
try:
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "grid"))
    )
    print("页面加载完成")
except Exception as e:
    print(f"页面加载超时: {e}")
    driver.quit()
    exit(1)

# 自动跳转到最后一页
print("正在跳转到最后一页...")
try:
    # 等待分页控件加载
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a[aria-label='末页']"))
    )
    
    # 查找最后一页的页码
    last_page_element = driver.find_element(By.CSS_SELECTOR, "a[aria-label='末页']")
    last_page = int(last_page_element.get_attribute("data-page"))
    
    # 跳转到最后一页
    driver.execute_script(f"$('#grid').data('kendoGrid').dataSource.page({last_page})")
    time.sleep(3)  # 等待页面加载
    print(f"已跳转到第 {last_page} 页")
except Exception as e:
    print(f"跳转到最后一页失败: {e}")

# 智能翻页控制逻辑
ch_items = []
page_num = last_page if 'last_page' in locals() else 1

while True:
    print(f"正在处理第 {page_num} 页...")
    
    # 等待表格加载完成
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#grid tbody tr"))
        )
    except Exception as e:
        print(f"等待表格加载超时: {e}")
        break
    
    # 获取当前页表格中的所有行
    table_rows = driver.find_elements(By.CSS_SELECTOR, "#grid tbody tr")
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
                
                ch_items.append({
                    'number': formatted_number,
                    'name': tariff_name,
                    'url': detail_url
                })
                
                print(f"找到符合条件的条目: {tariff_no} - {tariff_name}")
    
    # 如果当前页没有符合条件的内容，则停止翻页
    if not current_page_has_ch_items:
        print(f"第 {page_num} 页没有符合条件的内容，停止翻页")
        break
    
    # 向前翻页
    page_num -= 1
    if page_num < 1:
        print("已到达第一页，停止翻页")
        break
    
    print(f"正在跳转到第 {page_num} 页...")
    try:
        driver.execute_script(f"$('#grid').data('kendoGrid').dataSource.page({page_num})")
        time.sleep(3)  # 等待页面加载
    except Exception as e:
        print(f"跳转到第 {page_num} 页失败: {e}")
        break

print(f"总共找到 {len(ch_items)} 个符合条件的条目")

# 为每个条目创建子文件夹并下载网页内容
for item in ch_items:
    number = item['number']
    name = item['name']
    url = item['url']
    
    # 创建子文件夹
    folder_name = f"{number}-{name}"
    folder_path = os.path.join(DATASET_DIR, folder_name)
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"创建子文件夹: {folder_path}")
    else:
        print(f"子文件夹已存在: {folder_path}")
    
    # 下载网页内容
    try:
        print(f"正在下载: {url}")
        response = requests.get(url, timeout=30)
        response.encoding = 'utf-8'
        
        # 保存网页内容
        file_name = f"{number}-{name}.html"
        file_path = os.path.join(folder_path, file_name)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"成功保存: {file_path}")
    except Exception as e:
        print(f"下载失败 {url}: {e}")

# 关闭浏览器
driver.quit()
print("任务完成，浏览器已关闭")