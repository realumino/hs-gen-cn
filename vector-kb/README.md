# 向量知识库 (Vector Knowledge Base)

基于 Chroma 和 SentenceTransformer 的持久化向量知识库存储系统。

## 功能特性

- 支持多种文件格式（.txt, .pdf, .docx）的解析和向量化存储
- 基于 Chroma 的持久化向量数据库
- 使用 SentenceTransformer 进行文本向量化
- 支持相似度检索和元数据管理

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 初始化知识库

```python
from kb import kb

# 创建新的知识库
vkb = kb(path="./vkb")
vkb.create(chunk_size=500, model="sentence-transformers/all-MiniLM-L6-v2")
```

### 2. 添加文件到知识库

```python
# 添加单个文件，并获取文件ID
file_id = vkb.addItem(
    filepath="./docs/商品归类说明.txt", 
    metadata={
        "section": "11", 
        "chapter": "45", 
        "is_detailed": True
    }
)
print(f"文件已添加，文件ID: {file_id}")
```

### 3. 删除文件内容

```python
# 根据文件ID删除文件内容
deleted_count = vkb.delItem(file_id)
print(f"已删除 {deleted_count} 个chunks")
```

### 4. 查询知识库

```python
# 查询相关内容
results = vkb.query("维生素E相关的原料药", top_k=5)
for result in results:
    print(f"Text: {result['text']}")
    print(f"Metadata: {result['metadata']}")
    print(f"Distance: {result['distance']}")
    print("---")
```

## 类接口说明

### kb(path: str)

初始化知识库对象。

**参数:**
- `path`: 知识库存储路径

### create(chunk_size: int, model: str, name: str = 'default_collection')

创建新的知识库（仅在新路径时调用）。

**参数:**
- `chunk_size`: 文本分块大小
- `model`: SentenceTransformer 模型名称
- `name`: Collection 名称

### addItem(filepath: str, metadata: dict)

添加文件到知识库。

**参数:**
- `filepath`: 文件路径
- `metadata`: 文件元数据（必须包含 section 字段）

### query(text: str, top_k: int = 5, where: Optional[Dict[str, Any]] = None)

查询相似内容。

**参数:**
- `text`: 查询文本
- `top_k`: 返回结果数量
- `where`: metadata 过滤条件，例如 `{"section": "11"}` 或 `{"chapter": "45"}`

**返回:**
```python
[
    {
        "text": "...chunk内容...",
        "metadata": {...},
        "distance": 0.12
    },
    ...
]
```

**示例:**
```python
# 查询所有 section 为 "11" 的内容
results = vkb.query("维生素E相关的原料药", top_k=5, where={"section": "11"})

# 查询所有 chapter 为 "45" 且 is_detailed 为 True 的内容
results = vkb.query("商品归类规则", top_k=5, where={"chapter": "45", "is_detailed": True})
```

### delItem(file_id: str)

根据文件ID删除知识库中的文件内容。

**参数:**
- `file_id`: 文件唯一标识符，由addItem方法返回

**返回:**
- 删除的chunk数量

## 目录结构

```
./vkb/
│
├── properties.json        # 存储模型名、chunk大小、collection名
├── chroma/                # Chroma 内部数据目录
└── ...
```