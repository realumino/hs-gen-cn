# hs-gen-cn
搜集中国海关数据，利用大模型自动生成HS编号

## 爬虫工具

此项目包含一个用于从中国海关网站抓取进出口税则商品及品目注释的爬虫工具。

### 功能

1. 自动打开浏览器并加载目标页面
2. 从数据表格尾部开始向上查找符合条件的条目（格式为CHxx）
3. 提取子目号、条文内容和详细链接
4. 为每个条目创建独立文件夹并下载网页内容
5. 流式处理模式：找到一个条目后立即下载，无需等待所有条目查找完成

### 使用方法

1. 确保已安装Python 3.7+
2. 安装依赖包：
   ```
   pip install selenium requests
   ```
3. 下载ChromeDriver
4. 运行爬虫：
   ```
   python scraper/scraper.py
   ```
   
   或者使用自定义参数：
   ```
   python scraper/scraper.py --dataset-dir "my_dataset" --chromedriver-path "C:\path\to\chromedriver.exe"
   ```
   
   参数说明：
   - `--dataset-dir`: 指定数据集存储目录（默认为scraper/dataset）
   - `--chromedriver-path`: 指定ChromeDriver的路径（默认会在系统PATH中查找）

### 输出结构

爬虫会在`scraper/dataset`目录下创建以下结构：

```
dataset/
├── 01-子目条文名称/
│   └── 01-子目条文名称.html
├── 02-子目条文名称/
│   └── 02-子目条文名称.html
└── ...
```

### 注意事项

1. 爬虫会自动创建dataset目录
2. 如果需要无头模式运行（不显示浏览器窗口），请修改scraper.py中的options.add_argument('--headless=new')行，取消注释该行
3. 爬虫会处理CH1-CH99格式的所有条目
4. 默认情况下，ChromeDriver需要在系统PATH中可找到，或者可以通过--chromedriver-path参数指定
5. 爬虫采用流式处理模式，找到一个条目后立即下载，提高了下载过程的稳定性和可中断性
