#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
全功能交互式CLI客户端，用于管理kb.py知识库系统
"""

import os
import sys
import argparse
from typing import Optional
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kb import kb

try:
    from prompt_toolkit import prompt
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False
    def prompt(*args, **kwargs):
        return input(kwargs.get('message', ''))


class KBCLI:
    """知识库CLI客户端主类"""
    
    def __init__(self, kb_path: Optional[str] = None):
        """
        初始化CLI客户端
        
        Args:
            kb_path: 知识库路径，如果为None则使用当前目录
        """
        self.kb_path = kb_path or os.getcwd()
        self.vkb = None
        self._ensure_kb_exists()
        self.command_history_file = os.path.join(self.kb_path, ".cli_history")
        
        # 设置命令补全
        self.commands = ['list', 'delete', 'query', 'help', 'quit', 'exit']
        self.command_completer = WordCompleter(self.commands, ignore_case=True) if HAS_PROMPT_TOOLKIT else None
    
    def _ensure_kb_exists(self):
        """确保知识库存在，如果不存在则提示创建"""
        try:
            self.vkb = kb(self.kb_path)
            if self.vkb.is_new:
                print(f"在路径 '{self.kb_path}' 未找到现有知识库。")
                if self._confirm("是否创建新的知识库？"):
                    self._create_kb()
                else:
                    print("操作已取消。")
                    sys.exit(0)
        except Exception as e:
            print(f"初始化知识库时出错: {e}")
            sys.exit(1)
    
    def _create_kb(self):
        """创建新的知识库"""
        try:
            chunk_size = input("请输入文本分块大小 (默认500): ").strip()
            chunk_size = int(chunk_size) if chunk_size else 500
            
            model = input("请输入嵌入模型名称 (默认sentence-transformers/all-MiniLM-L6-v2): ").strip()
            model = model if model else "sentence-transformers/all-MiniLM-L6-v2"
            
            collection_name = input("请输入集合名称 (默认default_collection): ").strip()
            collection_name = collection_name if collection_name else "default_collection"
            
            self.vkb.create(chunk_size=chunk_size, model=model, name=collection_name)
            print("知识库创建成功！")
        except Exception as e:
            print(f"创建知识库时出错: {e}")
            sys.exit(1)
    
    def _confirm(self, prompt: str) -> bool:
        """
        请求用户确认
        
        Args:
            prompt: 提示信息
            
        Returns:
            用户确认结果
        """
        while True:
            response = input(f"{prompt} (y/n): ").strip().lower()
            if response in ['y', 'yes', '是']:
                return True
            elif response in ['n', 'no', '否']:
                return False
            else:
                print("请输入 'y' 或 'n'")
    
    def list_files(self):
        """列出知识库中的所有文件"""
        try:
            files = self.vkb.list()
            if not files:
                print("知识库中没有文件。")
                return
            
            print(f"\n知识库中共有 {len(files)} 个文件:")
            print("-" * 100)
            print(f"{'文件ID':<36} {'源文件名':<20} {'Chunk数':<8} {'大小':<10} {'修改时间':<20}")
            print("-" * 100)
            
            # 获取源文件的实际路径以获取文件信息
            source_files_info = {}
            chroma_path = os.path.join(self.kb_path, "chroma")
            # 遍历知识库目录下的文件来获取文件信息
            if os.path.exists(self.kb_path):
                for root, dirs, files_in_dir in os.walk(self.kb_path):
                    # 跳过chroma目录
                    if chroma_path in root:
                        continue
                    for file_name in files_in_dir:
                        file_path = os.path.join(root, file_name)
                        try:
                            stat = os.stat(file_path)
                            source_files_info[file_name] = {
                                'size': stat.st_size,
                                'mtime': stat.st_mtime
                            }
                        except:
                            # 如果无法获取文件信息，跳过
                            pass
            
            for file in files:
                source_file = file['source_file']
                size_str = "N/A"
                mtime_str = "N/A"
                
                # 尝试获取文件大小和修改时间
                if source_file in source_files_info:
                    file_info = source_files_info[source_file]
                    size_str = f"{file_info['size']} bytes"
                    # 格式化修改时间
                    import time
                    mtime_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_info['mtime']))
                
                print(f"{file['file_id']:<36} {source_file:<20} {file['chunk_count']:<8} {size_str:<10} {mtime_str:<20}")
        except Exception as e:
            print(f"列出文件时出错: {e}")
    
    def delete_file(self):
        """删除知识库中的指定文件"""
        try:
            files = self.vkb.list()
            if not files:
                print("知识库中没有文件可删除。")
                return
            
            # 显示文件列表
            print("\n当前知识库中的文件:")
            for i, file in enumerate(files):
                print(f"{i+1}. {file['source_file']} (ID: {file['file_id']})")
            
            # 获取用户选择
            choice = input("\n请选择要删除的文件编号 (或输入文件ID): ").strip()
            
            if not choice:
                print("操作已取消。")
                return
            
            # 查找要删除的文件
            file_to_delete = None
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(files):
                    file_to_delete = files[idx]
            else:
                # 按文件ID查找
                for file in files:
                    if file['file_id'] == choice:
                        file_to_delete = file
                        break
            
            if not file_to_delete:
                print("无效的选择。")
                return
            
            # 确认删除
            if not self._confirm(f"确定要删除文件 '{file_to_delete['source_file']}' 吗？"):
                print("操作已取消。")
                return
            
            # 执行删除
            deleted_count = self.vkb.delItem(file_to_delete['file_id'])
            print(f"已删除文件 '{file_to_delete['source_file']}'，共删除 {deleted_count} 个chunks。")
            
        except Exception as e:
            print(f"删除文件时出错: {e}")
    
    def query_knowledge_base(self):
        """查询知识库中的内容"""
        try:
            # 获取查询文本
            query_text = input("\n请输入查询内容: ").strip()
            if not query_text:
                print("查询内容不能为空。")
                return
            
            # 获取返回结果数量
            top_k_input = input("请输入返回结果数量 (默认5): ").strip()
            top_k = 5
            if top_k_input:
                try:
                    top_k = int(top_k_input)
                    if top_k <= 0:
                        print("结果数量必须大于0，使用默认值5。")
                        top_k = 5
                except ValueError:
                    print("无效的数字，使用默认值5。")
            
            # 获取过滤条件
            print("\n可选: 添加过滤条件")
            print("例如: section=11 或 chapter=45")
            print("留空表示不过滤")
            where_input = input("请输入过滤条件 (格式 key=value): ").strip()
            
            # 解析过滤条件
            where = None
            if where_input:
                try:
                    key, value = where_input.split('=')
                    key = key.strip()
                    value = value.strip()
                    # 尝试转换为数字
                    if value.isdigit():
                        value = int(value)
                    where = {key: value}
                except ValueError:
                    print("过滤条件格式不正确，将不使用过滤条件。")
            
            # 执行查询
            print("\n正在查询...")
            results = self.vkb.query(query_text, top_k=top_k, where=where)
            
            # 显示结果
            if not results:
                print("未找到相关结果。")
                return
            
            print(f"\n找到 {len(results)} 个相关结果:")
            print("=" * 80)
            for i, result in enumerate(results, 1):
                print(f"\n{i}. 文本内容:")
                print(result['text'])
                print("\n元数据:")
                for key, value in result['metadata'].items():
                    print(f"  {key}: {value}")
                print("-" * 80)
                
        except Exception as e:
            print(f"查询时出错: {e}")
    
    def show_menu(self):
        """显示主菜单"""
        print("\n" + "="*50)
        print("知识库管理系统")
        print("="*50)
        print(f"当前知识库路径: {self.kb_path}")
        print("\n可用命令:")
        print("  1. list     - 列出所有文件")
        print("  2. delete   - 删除文件")
        print("  3. query    - 查询知识库内容")
        print("  4. help     - 显示帮助信息")
        print("  5. quit     - 退出程序")
        print("\n输入命令或对应数字执行操作:")
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """
知识库管理系统 CLI 客户端使用说明:

1. 路径管理:
   - 默认使用当前工作目录作为知识库路径
   - 可通过命令行参数 -p 或 --path 指定其他路径

2. 知识库检测与创建:
   - 自动检测指定路径是否存在知识库
   - 如不存在会提示是否创建新的知识库

3. 文件管理操作:
   - list: 列出知识库中的所有文件，显示文件ID、源文件名和chunk数
   - delete: 删除指定文件，提供交互式选择和二次确认
   - query: 查询知识库内容，支持关键词搜索和元数据过滤

4. 查询功能:
   - 输入自然语言查询内容
   - 可指定返回结果数量
   - 可添加过滤条件（如 section=11 或 chapter=45）

5. 交互式操作:
   - 在主菜单中输入命令或对应数字执行操作
   - 支持连续操作，直到用户选择退出

6. 命令补全和历史记录:
   - 支持Tab键命令补全（需要安装prompt_toolkit）
   - 支持命令历史记录（需要安装prompt_toolkit）

7. 错误处理:
   - 对各种异常情况提供友好的错误提示
   - 对用户输入进行验证

示例用法:
  python cli_client.py           # 使用当前目录
  python cli_client.py -p /path/to/kb  # 指定知识库路径

安装prompt_toolkit以获得更好的交互体验:
  pip install prompt_toolkit
        """
        print(help_text)
    
    def _get_user_input(self, prompt_text: str = "\n> ") -> str:
        """
        获取用户输入，支持命令补全和历史记录
        
        Args:
            prompt_text: 提示文本
            
        Returns:
            用户输入的命令
        """
        if HAS_PROMPT_TOOLKIT:
            try:
                return prompt(
                    prompt_text,
                    completer=self.command_completer,
                    history=FileHistory(self.command_history_file),
                    auto_suggest=AutoSuggestFromHistory(),
                    enable_history_search=True
                ).strip().lower()
            except:
                # 如果prompt_toolkit出现问题，回退到普通input
                pass
        
        # 普通input方式
        return input(prompt_text).strip().lower()
    
    def run(self):
        """运行CLI客户端主循环"""
        print(f"欢迎使用知识库管理系统!")
        print(f"知识库路径: {self.kb_path}")
        
        if not HAS_PROMPT_TOOLKIT:
            print("\n提示: 安装 prompt_toolkit 可获得命令补全和历史记录功能:")
            print("  pip install prompt_toolkit")
        
        while True:
            try:
                self.show_menu()
                command = self._get_user_input()
                
                if command in ['1', 'list']:
                    self.list_files()
                elif command in ['2', 'delete']:
                    self.delete_file()
                elif command in ['3', 'query']:
                    self.query_knowledge_base()
                elif command in ['4', 'help', 'h']:
                    self.show_help()
                elif command in ['5', 'quit', 'q', 'exit']:
                    print("感谢使用知识库管理系统，再见!")
                    break
                elif command == '':
                    # 空命令，继续循环
                    continue
                else:
                    print(f"未知命令: {command}。输入 'help' 查看可用命令。")
                    
            except KeyboardInterrupt:
                print("\n\n程序被用户中断。")
                break
            except EOFError:
                print("\n\n程序结束。")
                break
            except Exception as e:
                print(f"发生未预期的错误: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="知识库管理系统CLI客户端")
    parser.add_argument('-p', '--path', help='知识库路径，默认为当前目录')
    
    args = parser.parse_args()
    
    # 创建并运行CLI客户端
    cli = KBCLI(args.path)
    cli.run()


if __name__ == "__main__":
    main()