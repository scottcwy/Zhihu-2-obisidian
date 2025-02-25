"""
知乎收藏夹导出工具 - 工具函数
Copyright (c) 2025 [Your Name]
Licensed under the MIT License
"""

import re

def filter_title_str(title):
    """过滤文件名中的非法字符
    
    Args:
        title: 原始标题
        
    Returns:
        str: 过滤后的标题，可以用作文件名
    """
    # 替换 Windows 文件名中的非法字符
    title = re.sub(r'[<>:"/\\|?*]', '_', title)
    # 移除前后空格
    title = title.strip()
    # 如果标题为空，使用默认名称
    return title or 'untitled'
