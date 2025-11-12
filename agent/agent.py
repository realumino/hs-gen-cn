import os
import sys
from typing import List, Dict, Any, Optional
from openai import OpenAI, Agent as OpenAIAgent
from openai.agents import tool

# 将 vector-kb 目录添加到 Python 路径中
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'vector-kb'))

# 导入知识库模块
from kb import kb


class Agent:
    def __init__(self):
        self.endpoint = None
        self.api_key = None
        self.system_prompt = "你是一个知识检索智能体。当用户提出问题时，请遵循以下规则：\n1. 先生成关键词并调用 kb_query 工具；\n2. 若结果不充分，请根据 metadata 信息缩小范围并再次调用；\n3. 当你认为信息已充分时，生成最终答案。"
        self.kb_path = None
        self.kb_instance = None
        self.max_rounds = 3
        self.verbose = False
        
    def set_endpoint(self, endpoint: str):
        """设置 API 模型的访问端点"""
        self.endpoint = endpoint
        
    def set_api_key(self, key: str):
        """设置模型 API Key"""
        self.api_key = key
        
    def set_system_prompt(self, prompt: str):
        """设置系统提示词"""
        self.system_prompt = prompt
        
    def set_kb(self, path: str):
        """设置知识库路径"""
        self.kb_path = path
        self.kb_instance = kb(path)

        @tool
        def kb_query(text: str, top_k: int = 5, where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
            """查询本地知识库内容"""
            if self.verbose:
                print(f"调用 kb_query: text={text}, top_k={top_k}, where={where}")
            return self.kb_instance.query(text, top_k, where)

        self.kb_query = kb_query
        
    def set_max_rounds(self, rounds: int):
        """设置最大递归深度"""
        self.max_rounds = rounds
        
    def set_verbose(self, verbose: bool):
        """设置日志模式"""
        self.verbose = verbose
        
    def ask(self, text: str) -> str:
        """单接口查询"""
        if not self.endpoint or not self.api_key:
            raise ValueError("请先设置 API 端点和密钥")
            
        if not self.kb_instance:
            raise ValueError("请先设置知识库路径")
            
        # 初始化 OpenAI 客户端
        client = OpenAI(
            base_url=self.endpoint,
            api_key=self.api_key
        )
        
        # 创建 Agent 实例
        agent = OpenAIAgent(
            instructions=self.system_prompt,
            tools=[self.kb_query],
            client=client
        )
        
        # 执行查询
        response = agent.run(task=text)
        
        # 返回最终答案
        return response.result.content if response.result else "未能生成答案"