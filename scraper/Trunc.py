#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def truncate_filename(filename, max_length=200):
    """
    截断文件名以符合Windows和Linux的文件名长度限制，并移除Windows不允许的特殊字符
    取Windows(260)和Linux(255)中最小者减去4，即251个字符
    
    Windows不允许的字符: < > : " / \ | ? *
    
    :param filename: 原始文件名
    :param max_length: 最大字符数
    :return: 截断并清理后的文件名
    """
    # 移除Windows不允许的特殊字符
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    
    # 清理文件名开头和结尾的空格
    filename = filename.strip()
    
    # 如果文件名为空，返回默认名称
    if not filename:
        filename = "unnamed"
    
    if len(filename) <= max_length:
        return filename
    
    # 保留文件扩展名（如果有的话）
    if '.' in filename and not filename.startswith('.'):
        name_part, ext_part = filename.rsplit('.', 1)
        ext_part = '.' + ext_part
        
        # 计算文件名部分的最大长度
        max_name_length = max_length - len(ext_part)
        if max_name_length > 0:
            truncated_name = name_part[:max_name_length]
            return truncated_name + ext_part
        else:
            # 如果扩展名本身就超过了最大长度，则只返回截断的扩展名
            return ext_part[:max_length]
    else:
        # 没有扩展名的情况
        return filename[:max_length]