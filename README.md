# HS编码数据抓取工具

本项目包含两个主要的抓取工具：
1. CHScraper.py - 抓取CH开头的海关编码数据
2. SCScraper.py - 抓取4位数字子目编码数据

## 功能特点

### CHScraper.py
- 抓取CH开头的海关编码数据
- 自动创建数据集目录
- 智能翻页抓取
- 自适应请求间隔避免被封

### SCScraper.py
- 抓取4位数字子目编码数据
- 按子目号前两位数字分类存储
- 文件夹和文件按"子目号-子目条文"格式命名
- 保持与CHScraper.py兼容的核心功能

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### CHScraper.py

```bash
python scraper/CHScraper.py
```

可选参数：
- `--dataset-dir` 指定数据集存储目录名 (默认: dataset)
- `--chromedriver-path` 指定chromedriver路径

### SCScraper.py

```bash
python scraper/SCScraper.py
```

可选参数：
- `--dataset-dir` 指定数据集存储目录名 (默认: dataset)
- `--chromedriver-path` 指定chromedriver路径

## 数据存储结构

### CHScraper.py
```
dataset/
├── 01-子目名称/
│   ├── 01-子目名称.html
│   └── 其他相关文件
├── 02-子目名称/
│   └── 02-子目名称.html
└── ...
```

### SCScraper.py
```
dataset/
├── 01/
│   ├── 0101-子目条文/
│   │   └── 0101-子目条文.html
│   └── 0102-子目条文/
│       └── 0102-子目条文.html
├── 02/
│   └── 0201-子目条文/
│       └── 0201-子目条文.html
└── ...
```

## 注意事项

1. 需要安装Chrome浏览器和对应版本的chromedriver
2. 为避免被网站封禁，程序会自动调整请求间隔
3. 抓取过程可能需要较长时间，请耐心等待
4. 抓取的数据将保存在dataset目录中

## 许可证

MIT License
