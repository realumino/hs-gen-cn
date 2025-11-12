# HS-GEN-CN

HS编码生成器（中国版）

## 项目结构

- `scraper/`: 爬虫相关代码
- `vector-kb/`: 向量知识库
- `agent/`: 智能查询代理

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用说明

### 1. 初始化知识库

```python
from vector_kb.kb import kb

# 创建知识库实例
knowledge_base = kb("./vector-kb/vkb")

# 如果是新知识库，需要初始化
knowledge_base.create(chunk_size=500, model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
```

### 2. 添加文档到知识库

```python
# 添加文档
file_id = knowledge_base.addItem("./vector-kb/sample_docs/维生素E说明.txt", {"section": "11"})
```

### 3. 使用智能查询代理

```python
from agent import Agent

# 创建 Agent 实例
p = Agent()

# 设置知识库路径
p.set_kb("./vector-kb/vkb")

# 设置 API 端点和密钥
p.set_endpoint("http://127.0.0.1:11434")  # 示例端点，实际使用时请替换为正确的端点
p.set_api_key("sk-xxxx")  # 示例密钥，实际使用时请替换为正确的密钥

# 设置系统提示词
p.set_system_prompt("你是一个知识检索智能体，能够多轮检索后生成答案。")

# 执行查询
answer = p.ask("请解释量子叠加原理在量子计算中的应用")
print(answer)
```

## 许可证

MIT