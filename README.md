# HS编码数据抓取工具与AI Agent框架

本项目包含两个主要部分：
1. HS编码数据抓取工具（CHScraper.py和SCScraper.py）
2. 基于OpenAI的AI Agent框架

## AI Agent框架

基于OpenAI官方Python库的可扩展AI Agent框架，结合rich库实现美观的终端输出格式和typer库构建的命令行界面交互系统。

### 功能特性

- 模块化设计，支持动态添加属性和功能
- 基于OpenAI API的聊天完成接口封装
- 美观的终端输出格式（彩色文本、表格、进度条等）
- 直观易用的命令行界面
- 可扩展的Agent基类设计

### 安装要求

- Python 3.7+
- OpenAI API密钥

### 安装步骤

1. 克隆项目到本地：
   ```
   git clone <repository-url>
   cd hs-gen-cn
   ```

2. 安装依赖项：
   ```
   pip install -r requirements.txt
   ```

3. 设置OpenAI API密钥环境变量：
   ```bash
   # Windows (PowerShell)
   $env:OPENAI_API_KEY="your-api-key"
   
   # macOS/Linux
   export OPENAI_API_KEY="your-api-key"
   ```

### 使用方法

#### 命令行界面

```bash
# 启动交互式聊天会话
python agent.py chat

# 查看可用模型
python agent.py models

# 查看版本信息
python agent.py version
```

#### 编程接口

```python
from ai_agent import Agent, OpenAIClient

# 创建自定义Agent
class MyAgent(Agent):
    def __init__(self, name):
        super().__init__(name)
        self.openai_client = OpenAIClient()
    
    def process_input(self, user_input):
        # 实现自定义处理逻辑
        response = self.openai_client.chat_completion(
            messages=[{"role": "user", "content": user_input}],
            model="gpt-3.5-turbo"
        )
        return response

# 使用Agent
agent = MyAgent("MyCustomAgent")
response = agent.process_input("你好，世界！")
print(response)
```

#### 项目结构

```
ai_agent/
├── __init__.py          # 包初始化文件
├── base.py              # Agent基类定义
├── openai_client.py     # OpenAI API客户端封装
├── input_handler.py     # 用户输入处理机制
├── output_formatter.py  # 响应格式化输出系统
└── cli.py              # 命令行界面交互系统
```

## HS编码数据抓取工具

本项目包含两个主要的抓取工具：
1. CHScraper.py - 抓取CH开头的海关编码数据
2. SCScraper.py - 抓取4位数字子目编码数据

### 功能特点

#### CHScraper.py
- 抓取CH开头的海关编码数据
- 自动创建数据集目录
- 智能翻页抓取
- 自适应请求间隔避免被封

#### SCScraper.py
- 抓取4位数字子目编码数据
- 按子目号前两位数字分类存储
- 文件夹和文件按"子目号-子目条文"格式命名
- 保持与CHScraper.py兼容的核心功能

### 安装依赖

```bash
pip install -r requirements.txt
```

### 使用方法

#### CHScraper.py

```bash
python scraper/CHScraper.py
```

可选参数：
- `--dataset-dir` 指定数据集存储目录名 (默认: dataset)
- `--chromedriver-path` 指定chromedriver路径

#### SCScraper.py

```bash
python scraper/SCScraper.py
```

可选参数：
- `--dataset-dir` 指定数据集存储目录名 (默认: dataset)
- `--chromedriver-path` 指定chromedriver路径

### 数据存储结构

#### CHScraper.py
```
dataset/
├── 01-子目名称/
│   ├── 01-子目名称.html
│   └── 其他相关文件
├── 02-子目名称/
│   └── 02-子目名称.html
└── ...
```

#### SCScraper.py
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

### 注意事项

1. 需要安装Chrome浏览器和对应版本的chromedriver
2. 为避免被网站封禁，程序会自动调整请求间隔
3. 抓取过程可能需要较长时间，请耐心等待
4. 抓取的数据将保存在dataset目录中

## 许可证

MIT License
