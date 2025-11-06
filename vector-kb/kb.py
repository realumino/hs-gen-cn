import os
import json
import uuid
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import PyPDF2
from docx import Document


class kb:
    """
    基于 Chroma 的持久化向量知识库存储系统
    """
    """
    基于 Chroma 的持久化向量知识库存储系统
    """
    
    def __init__(self, path: str):
        """
        初始化知识库
        
        Args:
            path: 知识库存储路径
        """
        self.path = path
        self.is_new = not os.path.exists(path)
        
        # 创建路径如果不存在
        if self.is_new:
            os.makedirs(path, exist_ok=True)
            
        # 初始化 Chroma 客户端
        chroma_path = os.path.join(path, "chroma")
        self.client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 初始化属性
        self.properties = {}
        self._model = None
        self.collection = None
        
        # 如果不是新知识库，尝试加载配置
        properties_path = os.path.join(path, "properties.json")
        if not self.is_new and os.path.exists(properties_path):
            with open(properties_path, 'r', encoding='utf-8') as f:
                self.properties = json.load(f)
            # 获取已存在的 collection
            if 'name' in self.properties:
                try:
                    self.collection = self.client.get_collection(name=self.properties['name'])
                except Exception:
                    # 如果获取失败，将在 create 方法中创建
                    pass
    
    def create(self, chunk_size: int, model: str, name: str = 'default_collection'):
        """
        仅在新建知识库时调用
        
        Args:
            chunk_size: 每个文本分块的字数
            model: 使用的 embedding 模型名称
            name: collection 名称
        """
        if not self.is_new:
            print("已存在知识库，跳过初始化")
            return
            
        # 写入并保存 properties.json
        self.properties = {
            "name": name,
            "chunk_size": chunk_size,
            "model": model
        }
        
        properties_path = os.path.join(self.path, "properties.json")
        with open(properties_path, 'w', encoding='utf-8') as f:
            json.dump(self.properties, f, ensure_ascii=False, indent=2)
        
        # 创建新的 collection
        self.collection = self.client.get_or_create_collection(name=name)
    
    def _load_embedding_model(self):
        """
        从 properties.json 中读取模型名称并加载模型
        """
        if self._model is not None:
            return self._model
            
        if 'model' not in self.properties:
            raise ValueError("模型信息未在 properties.json 中找到")
            
        model_name = self.properties['model']
        self._model = SentenceTransformer(model_name)
        return self._model
    
    def _embedding(self, texts: List[str]) -> List[List[float]]:
        """
        使用模型对文本列表进行向量化
        
        Args:
            texts: 文本列表
            
        Returns:
            对应的向量数组
        """
        if self._model is None:
            self._load_embedding_model()
            
        return self._model.encode(texts, normalize_embeddings=True).tolist()
    
    def _parser(self, filepath: str) -> List[str]:
        """
        负责读取文件内容并切分为多个 chunk
        
        Args:
            filepath: 文件路径
            
        Returns:
            字符串列表，每个元素是一个文本块
        """
        # 获取文件扩展名
        _, ext = os.path.splitext(filepath)
        ext = ext.lower()
        
        # 读取文件内容
        content = ""
        if ext == '.txt':
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        elif ext == '.pdf':
            with open(filepath, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text()
        elif ext == '.docx':
            doc = Document(filepath)
            content = ""
            for paragraph in doc.paragraphs:
                content += paragraph.text + "\n"
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
        
        # 获取分块大小
        chunk_size = self.properties.get('chunk_size', 500)
        
        # 分块处理
        chunks = []
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size].strip()
            if chunk:  # 只添加非空块
                chunks.append(chunk)
                
        return chunks
    
    def addItem(self, filepath: str, metadata: Dict[str, Any]):
        """
        用于添加单个文件内容到知识库
        
        Args:
            filepath: 文件路径
            metadata: 文件元数据
                section: 两位数字（必须）
                chapter: 两位数字（可选）
                is_detailed: bool 值（可选）
        """
        # 验证必要元数据
        if 'section' not in metadata:
            raise ValueError("必须提供 section 元数据")
        
        # 解析文件
        chunks = self._parser(filepath)
        
        # 向量化
        embeddings = self._embedding(chunks)
        
        # 准备数据
        ids = []
        metadatas = []
        source_file = os.path.basename(filepath)
        
        # 为整个文件生成唯一标识符
        file_id = str(uuid.uuid4())
        
        for i, chunk in enumerate(chunks):
            # 为每个 chunk 生成唯一 id
            chunk_id = f"{file_id}_{source_file}_{i}"
            ids.append(chunk_id)
            
            # 构建元数据
            chunk_metadata = metadata.copy()
            chunk_metadata['source_file'] = source_file
            chunk_metadata['chunk_index'] = i
            chunk_metadata['file_id'] = file_id  # 添加文件唯一标识符
            
            metadatas.append(chunk_metadata)
        
        # 添加到 Chroma
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        
        return file_id  # 返回文件ID，便于后续操作
      
    def delItem(self, file_id: str):
          """
          根据文件ID删除知识库中的文件内容
          
          Args:
              file_id: 文件唯一标识符，由addItem方法返回
          """
          # 查询所有属于该文件的chunks
          results = self.collection.get(
              where={"file_id": file_id}
          )
          
          # 如果找到了匹配的chunks，则删除它们
          if results and results['ids']:
              self.collection.delete(ids=results['ids'])
              return len(results['ids'])  # 返回删除的chunk数量
          else:
              return 0  # 没有找到匹配的文件
      
    def query(self, text: str, top_k: int = 5, where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        输入自然语言查询字符串
        
        Args:
            text: 查询文本
            top_k: 返回结果数量
            where: metadata 过滤条件，例如 {"section": "11"} 或 {"chapter": "45"}
            
        Returns:
            结构化结果列表
        """
        # 向量化查询文本
        query_embedding = self._embedding([text])[0]
        
        # 构建查询参数
        query_params = {
            "query_embeddings": [query_embedding],
            "n_results": top_k
        }
        
        # 如果提供了 where 条件，则添加到查询参数中
        if where is not None:
            query_params["where"] = where
        
        # 执行查询
        results = self.collection.query(**query_params)
        
        # 构建返回结果
        formatted_results = []
        for i in range(len(results['ids'][0])):
            result = {
                "text": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
            }
            formatted_results.append(result)
            
        return formatted_results