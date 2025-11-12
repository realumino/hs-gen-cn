#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动将指定文件夹中的所有文件添加到知识库的程序
"""

import os
import re
from kb import kb


def extract_metadata_from_filename(filename):
    """
    根据文件名自动提取metadata信息
    
    规则:
    - 若文件名仅包含两个数字：section设为该两个数字，chapter设为空值，is_section_db和is_chapter_db均设为false
    - 若文件名包含四个数字：section设为前两个数字，chapter设为后两个数字，is_section_db和is_chapter_db均设为false
    - 若文件名为"SectionDB.csv"：section设为空值，is_section_db设为True
    - 若文件名为"SectionXXChapterDB.csv"（其中XX为具体数字）：section设为XX，is_chapter_db设为True
    """
    # 去掉文件扩展名
    basename = os.path.splitext(filename)[0]
    
    # 特殊情况：SectionDB.csv
    if basename == "SectionDB":
        return {
            "section": "",
            "chapter": "",
            "is_section_db": True,
            "is_chapter_db": False
        }
    
    # 特殊情况：SectionXXChapterDB.csv
    section_chapter_pattern = r"Section(\d{2})ChapterDB"
    match = re.match(section_chapter_pattern, basename)
    if match:
        section_num = match.group(1)
        return {
            "section": section_num,
            "chapter": "",
            "is_section_db": False,
            "is_chapter_db": True
        }
    
    # 提取文件名中的数字
    digits = re.findall(r'\d', basename)
    digit_string = ''.join(digits)
    
    # 若文件名仅包含两个数字
    if len(digit_string) == 2:
        return {
            "section": digit_string,
            "chapter": "",
            "is_section_db": False,
            "is_chapter_db": False
        }
    
    # 若文件名包含四个数字
    elif len(digit_string) >= 4:
        section = digit_string[:2]
        chapter = digit_string[2:4]
        return {
            "section": section,
            "chapter": chapter,
            "is_section_db": False,
            "is_chapter_db": False
        }
    
    # 默认情况
    return {
        "section": "",
        "chapter": "",
        "is_section_db": False,
        "is_chapter_db": False
    }


def add_all_files_to_kb(folder_path, kb_instance):
    """
    遍历指定文件夹中的所有文件，并将其添加到知识库中
    
    Args:
        folder_path: 要遍历的文件夹路径
        kb_instance: 知识库实例
    """
    # 遍历文件夹中的所有文件
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 跳过properties.json和chroma目录中的文件
            if file == "properties.json" or "chroma" in root:
                continue
                
            file_path = os.path.join(root, file)
            print(f"正在处理文件: {file_path}")
            
            try:
                # 提取metadata
                metadata = extract_metadata_from_filename(file)
                print(f"提取的metadata: {metadata}")
                
                # 添加文件到知识库
                file_id = kb_instance.addItem(file_path, metadata)
                print(f"文件已成功添加到知识库，文件ID: {file_id}")
            except Exception as e:
                print(f"处理文件 {file_path} 时出错: {str(e)}")


def main():
    """
    主函数：初始化知识库并添加所有文件
    """
    # 定义知识库路径和模型路径
    kb_path = "C:\\Users\\or7uk\\Desktop\\新增資料夾 (2)\\kb"
    model_path = r"C:\Users\or7uk\bge-large-zh-v1.5"
    
    # 初始化知识库
    print("正在初始化知识库...")
    knowledge_base = kb(kb_path)
    
    # 如果是新知识库，则创建它（设置chunk大小为450）
    if knowledge_base.is_new:
        print("创建新的知识库...")
        knowledge_base.create(chunk_size=450, model=model_path, name="hs_code")
    else:
        print("使用现有的知识库...")
        # 确保collection已正确初始化
        if knowledge_base.collection is None:
            print("重新初始化知识库collection...")
            knowledge_base.collection = knowledge_base.client.get_or_create_collection(name="hs_code")
    
    # 指定要处理的文件夹路径
    folder_path = "C:\\Users\\or7uk\\Desktop\\新增資料夾 (2)\\FLAT"
    
    # 添加所有文件到知识库
    print(f"开始处理文件夹: {folder_path}")
    add_all_files_to_kb(folder_path, knowledge_base)
    
    print("所有文件已处理完毕！")


if __name__ == "__main__":
    main()