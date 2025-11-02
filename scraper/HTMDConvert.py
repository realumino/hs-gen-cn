#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML to Markdown Converter
将HTML文件转换为Markdown格式，保留原始结构和内容

此模块提供了将HTML文件转换为Markdown格式的功能，支持作为独立脚本运行或作为模块导入使用。

主要功能：
1. convert_html_to_markdown(html_content, filename="") - 将HTML内容转换为Markdown格式
2. convert_file(html_file_path, md_file_path=None) - 转换单个HTML文件为Markdown文件
3. convert_multiple_files(html_files, output_dir=None) - 批量转换多个HTML文件
4. scan_and_convert_html_files(directory=".") - 扫描目录并转换所有HTML文件

使用方法：
1. 作为模块导入：
   from html_to_md_converter import convert_file, convert_multiple_files
   
2. 作为独立脚本运行：
   python html_to_md_converter.py
   或
   python html_to_md_converter.py [directory]
"""

import os
import sys
import glob
from bs4 import BeautifulSoup
import re
from typing import List, Optional


def clean_text(text):
    """清理文本中的多余空白字符"""
    if not text:
        return ""
    # 将多个连续的空白字符替换为单个空格
    text = re.sub(r'\s+', ' ', text)
    # 去除首尾空白
    return text.strip()


def convert_html_to_markdown(html_content, filename=""):
    """
    将HTML内容转换为Markdown格式
    
    Args:
        html_content (str): HTML文件内容
        filename (str): 文件名（用于标题）
        
    Returns:
        str: Markdown格式内容
    """
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 存储Markdown内容
    md_lines = []
    
    # 添加文件名作为主标题（如果提供）
    if filename:
        md_lines.append(f"# {os.path.splitext(filename)[0]}")
        md_lines.append("")  # 空行
    
    # 提取主要内容区域（ticketsForm div）
    content_div = soup.find('div', id='ticketsForm')
    if not content_div:
        content_div = soup.body if soup.body else soup
    
    # 处理表格内容
    table = content_div.find('table')
    if table:
        # 只获取顶级表格的直接子行，避免处理嵌套表格的内容
        # 使用children属性只获取直接子元素，然后过滤出tr元素
        rows = [child for child in table.children if child.name == 'tr']
        if not rows:
            # 如果没有直接子行，退回到原来的方法（但仍然只处理顶级表格）
            rows = table.find_all('tr', recursive=False)
            
        for row in rows:
            cells = row.find_all(['td'], recursive=False)
            if len(cells) >= 2:
                label_cell = cells[0]
                content_cell = cells[1]
                
                # 获取标签文本
                label_text = clean_text(label_cell.get_text())
                if label_text:
                    md_lines.append(f"## {label_text}")
                    md_lines.append("")
                
                # 处理内容单元格
                process_content_cell(content_cell, md_lines)
    
    return '\n'.join(md_lines)


def process_table(table, md_lines):
    """
    处理表格元素，转换为Markdown格式的表格
    
    Args:
        table: BeautifulSoup表格元素
        md_lines: Markdown行列表
    """
    # 获取所有行
    rows = table.find_all('tr')
    if not rows:
        return
    
    # 提取表头和表体
    thead = table.find('thead')
    tbody = table.find('tbody')
    
    # 存储表格数据
    table_data = []
    max_cols = 0
    
    # 处理表头
    header_rows = thead.find_all('tr') if thead else []
    for row in header_rows:
        row_data = []
        cells = row.find_all(['td', 'th'])
        for cell in cells:
            cell_text = clean_text(cell.get_text())
            # 获取单元格的 colspan 和 rowspan 属性
            colspan = int(cell.get('colspan', 1))
            rowspan = int(cell.get('rowspan', 1))
            row_data.append({
                'text': cell_text,
                'colspan': colspan,
                'rowspan': rowspan
            })
        if row_data:
            table_data.append(row_data)
            max_cols = max(max_cols, len(row_data))
    
    # 处理表体
    body_rows = tbody.find_all('tr') if tbody else rows[len(header_rows):]
    for row in body_rows:
        row_data = []
        cells = row.find_all(['td', 'th'])
        for cell in cells:
            cell_text = clean_text(cell.get_text())
            # 获取单元格的 colspan 和 rowspan 属性
            colspan = int(cell.get('colspan', 1))
            rowspan = int(cell.get('rowspan', 1))
            row_data.append({
                'text': cell_text,
                'colspan': colspan,
                'rowspan': rowspan
            })
        if row_data:
            table_data.append(row_data)
            max_cols = max(max_cols, len(row_data))
    
    # 如果没有提取到表格数据，直接返回
    if not table_data or max_cols == 0:
        return
    
    # 转换为Markdown表格
    # 添加空行分隔
    md_lines.append("")
    
    # 创建表头分隔符行
    separator_row = "| " + " | ".join(["---"] * max_cols) + " |"
    
    # 添加表格行
    for i, row_data in enumerate(table_data):
        # 构建行文本
        row_texts = []
        for cell_data in row_data:
            row_texts.append(cell_data['text'])
        
        # 补齐列数
        while len(row_texts) < max_cols:
            row_texts.append("")
        
        # 创建Markdown行
        md_row = "| " + " | ".join(row_texts) + " |"
        md_lines.append(md_row)
        
        # 在表头后添加分隔符行
        if i == len(header_rows) - 1 and header_rows:
            md_lines.append(separator_row)
    
    # 添加空行分隔
    md_lines.append("")


def process_content_cell(cell, md_lines):
    """
    处理内容单元格，转换为Markdown格式
    
    Args:
        cell: BeautifulSoup元素
        md_lines: Markdown行列表
    """
    # 处理所有子元素
    for element in cell.children:
        if element.name == 'h1':
            # 处理标题
            text = clean_text(element.get_text())
            if text:
                md_lines.append(f"# {text}")
                md_lines.append("")
        elif element.name == 'p':
            # 处理段落
            text = clean_text(element.get_text())
            if text:
                # 检查是否为居中标题
                style = element.get('style', '')
                if 'text-align:center' in style or 'text-align: center' in style:
                    # 检查字体大小确定标题级别
                    if 'font-size:24px' in style:
                        md_lines.append(f"# {text}")
                    elif 'font-size:23px' in style:
                        md_lines.append(f"## {text}")
                    else:
                        md_lines.append(f"### {text}")
                else:
                    md_lines.append(text)
                md_lines.append("")
        elif element.name == 'span':
            # 处理span元素
            text = clean_text(element.get_text())
            if text:
                # 检查字体样式确定重要性
                style = element.get('style', '')
                if 'font-family:黑体' in style or 'font-family: 黑体' in style:
                    # 黑体通常表示重要文本或小标题
                    if len(text) < 20:  # 较短的黑体文本可能是标题
                        md_lines.append(f"### {text}")
                        md_lines.append("")
                    else:
                        md_lines.append(f"**{text}**")  # 加粗重要文本
                else:
                    md_lines.append(text)
        elif element.name == 'div':
            # 递归处理div元素及其子元素
            process_content_cell(element, md_lines)
        elif element.name == 'table':
                process_table(element, md_lines)
        elif element.name == 'br':
            # 换行
            md_lines.append("")


def convert_file(html_file_path, md_file_path=None):
    """
    转换单个HTML文件为Markdown文件
    
    Args:
        html_file_path (str): HTML文件路径
        md_file_path (str): 输出Markdown文件路径，默认为同名.md文件
    """
    # 如果没有指定输出路径，则使用默认路径
    if md_file_path is None:
        md_file_path = os.path.splitext(html_file_path)[0] + '.md'
    
    # 读取HTML文件
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # 转换为Markdown
    md_content = convert_html_to_markdown(html_content, os.path.basename(html_file_path))
    
    # 写入Markdown文件
    with open(md_file_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"成功转换: {html_file_path} -> {md_file_path}")


def convert_multiple_files(html_files, output_dir=None):
    """
    批量转换多个HTML文件
    
    Args:
        html_files (list): HTML文件路径列表
        output_dir (str): 输出目录，默认为与源文件相同目录
    """
    for html_file in html_files:
        if output_dir:
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            filename = os.path.basename(html_file)
            md_file_path = os.path.join(output_dir, os.path.splitext(filename)[0] + '.md')
        else:
            md_file_path = None  # 使用默认路径
        
        try:
            convert_file(html_file, md_file_path)
        except Exception as e:
            print(f"转换失败: {html_file} - {str(e)}")


def scan_and_convert_html_files(directory=".", output_dir=None):
    """
    扫描指定目录并转换所有HTML文件为Markdown格式
    
    Args:
        directory (str): 要扫描的目录路径，默认为当前目录
        output_dir (str): 输出目录路径，默认为与源文件相同目录
    """
    # 确保目录路径存在
    if not os.path.exists(directory):
        raise FileNotFoundError(f"目录不存在: {directory}")
    
    # 查找所有HTML文件
    html_pattern = os.path.join(directory, "*.html")
    html_files = glob.glob(html_pattern)
    
    if not html_files:
        print(f"在目录 '{directory}' 中未找到HTML文件")
        return
    
    print(f"找到 {len(html_files)} 个HTML文件")
    
    # 批量转换文件
    convert_multiple_files(html_files, output_dir)
    
    print("所有文件转换完成！")


def main():
    """主函数"""
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        # 使用命令行指定的目录
        directory = sys.argv[1]
        # 可选的输出目录
        output_dir = sys.argv[2] if len(sys.argv) > 2 else directory
    else:
        # 默认使用脚本所在目录
        directory = script_dir
        output_dir = script_dir
    
    try:
        scan_and_convert_html_files(directory, output_dir)
    except Exception as e:
        print(f"转换过程中出现错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()