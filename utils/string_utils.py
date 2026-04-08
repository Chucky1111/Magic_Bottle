"""
字符串处理工具模块 - 提供统一的字符串处理功能

核心功能：
1. 文本清理和规范化
2. 字符串截断和格式化
3. 模板渲染
4. 字符串验证
5. 编码转换
"""

import re
import html
from typing import Optional, List, Dict, Any, Union, Callable
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def clean_text(text: str, remove_empty_lines: bool = True, strip_whitespace: bool = True) -> str:
    """
    清理文本
    
    Args:
        text: 原始文本
        remove_empty_lines: 是否移除空行
        strip_whitespace: 是否去除首尾空白字符
    
    Returns:
        清理后的文本
    """
    if not text:
        return ""
    
    # 去除首尾空白字符
    if strip_whitespace:
        text = text.strip()
    
    # 移除空行
    if remove_empty_lines:
        lines = [line for line in text.splitlines() if line.strip()]
        text = "\n".join(lines)
    
    return text


def truncate_text(
    text: str,
    max_length: int,
    ellipsis: str = "...",
    preserve_words: bool = True
) -> str:
    """
    截断文本到指定长度
    
    Args:
        text: 原始文本
        max_length: 最大长度
        ellipsis: 省略号字符串
        preserve_words: 是否尽量在单词边界处截断
    
    Returns:
        截断后的文本
    """
    if not text or max_length <= 0:
        return ""
    
    if len(text) <= max_length:
        return text
    
    # 计算实际可显示的长度（考虑省略号）
    display_length = max_length - len(ellipsis)
    if display_length <= 0:
        return ellipsis[:max_length]
    
    # 截断文本
    truncated = text[:display_length]
    
    # 如果需要在单词边界处截断
    if preserve_words:
        # 查找最后一个空格或标点符号
        last_boundary = max(
            truncated.rfind(' '),
            truncated.rfind('.'),
            truncated.rfind(','),
            truncated.rfind(';'),
            truncated.rfind(':'),
            truncated.rfind('!'),
            truncated.rfind('?')
        )
        
        if last_boundary > display_length * 0.5:  # 只在合理的位置截断
            truncated = truncated[:last_boundary].rstrip()
    
    return truncated + ellipsis


def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """
    清理文件名，移除非法字符
    
    Args:
        filename: 原始文件名
        max_length: 最大文件名长度
    
    Returns:
        清理后的文件名
    """
    if not filename:
        return "unnamed"
    
    # Windows 文件名非法字符: \ / : * ? " < > |
    # 同时去除首尾空格
    sanitized = re.sub(r'[\\/*?:"<>|]', '_', filename)
    
    # 去除首尾空格和点
    sanitized = sanitized.strip().strip('.')
    
    # 限制文件名长度
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # 确保文件名不为空
    if not sanitized or sanitized.isspace():
        sanitized = "unnamed"
    
    return sanitized


def escape_html(text: str) -> str:
    """
    HTML转义
    
    Args:
        text: 原始文本
    
    Returns:
        HTML转义后的文本
    """
    return html.escape(text)


def unescape_html(text: str) -> str:
    """
    HTML反转义
    
    Args:
        text: HTML转义后的文本
    
    Returns:
        反转义后的文本
    """
    return html.unescape(text)


def normalize_whitespace(text: str) -> str:
    """
    规范化空白字符
    
    Args:
        text: 原始文本
    
    Returns:
        规范化后的文本
    """
    # 替换多个连续空白字符为单个空格
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_lines(text: str, start_line: int = 0, end_line: Optional[int] = None) -> List[str]:
    """
    提取文本的指定行
    
    Args:
        text: 原始文本
        start_line: 起始行号（0-based）
        end_line: 结束行号（不包含），如果为None则提取到末尾
    
    Returns:
        提取的行列表
    """
    lines = text.splitlines()
    
    if start_line < 0:
        start_line = 0
    if start_line >= len(lines):
        return []
    
    if end_line is None:
        end_line = len(lines)
    elif end_line > len(lines):
        end_line = len(lines)
    
    return lines[start_line:end_line]


def count_words(text: str) -> int:
    """
    统计文本中的单词数
    
    Args:
        text: 文本
    
    Returns:
        单词数
    """
    if not text:
        return 0
    
    # 简单的单词分割（按空白字符）
    words = re.findall(r'\b\w+\b', text)
    return len(words)


def count_characters(text: str, include_whitespace: bool = True) -> int:
    """
    统计文本中的字符数
    
    Args:
        text: 文本
        include_whitespace: 是否包含空白字符
    
    Returns:
        字符数
    """
    if not text:
        return 0
    
    if include_whitespace:
        return len(text)
    else:
        return len(re.sub(r'\s', '', text))


def render_template(template: str, context: Dict[str, Any]) -> str:
    """
    渲染简单模板
    
    Args:
        template: 模板字符串，使用 {{key}} 作为占位符
        context: 上下文字典
    
    Returns:
        渲染后的字符串
    """
    if not template:
        return ""
    
    result = template
    
    # 替换所有占位符
    for key, value in context.items():
        placeholder = f"{{{{{key}}}}}"
        result = result.replace(placeholder, str(value))
    
    # 清理未替换的占位符
    result = re.sub(r'\{\{.*?\}\}', '', result)
    
    return result


def load_template(template_path: Union[str, Path]) -> str:
    """
    加载模板文件
    
    Args:
        template_path: 模板文件路径
    
    Returns:
        模板内容
    """
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"加载模板文件失败: {template_path} - {e}")
        return ""


def is_valid_email(email: str) -> bool:
    """
    验证电子邮件地址格式
    
    Args:
        email: 电子邮件地址
    
    Returns:
        是否有效
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_url(url: str) -> bool:
    """
    验证URL格式
    
    Args:
        url: URL
    
    Returns:
        是否有效
    """
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))


def extract_emails(text: str) -> List[str]:
    """
    从文本中提取电子邮件地址
    
    Args:
        text: 文本
    
    Returns:
        电子邮件地址列表
    """
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(pattern, text)


def extract_urls(text: str) -> List[str]:
    """
    从文本中提取URL
    
    Args:
        text: 文本
    
    Returns:
        URL列表
    """
    pattern = r'https?://[^\s/$.?#].[^\s]*'
    return re.findall(pattern, text)


def to_camel_case(text: str, delimiter: str = '_') -> str:
    """
    转换为驼峰命名法
    
    Args:
        text: 原始文本
        delimiter: 单词分隔符
    
    Returns:
        驼峰命名法的字符串
    """
    if not text:
        return ""
    
    parts = text.split(delimiter)
    return ''.join(part.capitalize() for part in parts if part)


def to_snake_case(text: str) -> str:
    """
    转换为蛇形命名法
    
    Args:
        text: 原始文本
    
    Returns:
        蛇形命名法的字符串
    """
    if not text:
        return ""
    
    # 插入下划线在大写字母前（除了第一个字符）
    result = re.sub(r'(?<!^)(?=[A-Z])', '_', text)
    return result.lower()


def generate_slug(text: str, max_length: int = 50) -> str:
    """
    生成URL友好的slug
    
    Args:
        text: 原始文本
        max_length: 最大长度
    
    Returns:
        slug字符串
    """
    if not text:
        return ""
    
    # 转换为小写
    slug = text.lower()
    
    # 替换非字母数字字符为连字符
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    
    # 去除首尾连字符
    slug = slug.strip('-')
    
    # 截断到指定长度
    if len(slug) > max_length:
        # 尽量在连字符处截断
        if '-' in slug[:max_length]:
            last_hyphen = slug[:max_length].rfind('-')
            if last_hyphen > 0:
                slug = slug[:last_hyphen]
        else:
            slug = slug[:max_length]
    
    return slug


# 预定义的字符串处理函数
clean = clean_text
truncate = truncate_text
sanitize = sanitize_filename
normalize = normalize_whitespace


# 示例用法
if __name__ == "__main__":
    # 示例1：文本清理
    dirty_text = "  Hello   World  \n\nThis is a test.  "
    cleaned = clean_text(dirty_text)
    print(f"清理后的文本: '{cleaned}'")
    
    # 示例2：文本截断
    long_text = "This is a very long text that needs to be truncated."
    truncated = truncate_text(long_text, 20)
    print(f"截断后的文本: '{truncated}'")
    
    # 示例3：文件名清理
    bad_filename = 'My/File:Name*.txt'
    good_filename = sanitize_filename(bad_filename)
    print(f"清理后的文件名: '{good_filename}'")
    
    # 示例4：模板渲染
    template = "Hello {{name}}, welcome to {{place}}!"
    context = {"name": "Alice", "place": "Wonderland"}
    rendered = render_template(template, context)
    print(f"渲染后的模板: '{rendered}'")
    
    # 示例5：生成slug
    title = "My Awesome Blog Post!"
    slug = generate_slug(title)
    print(f"生成的slug: '{slug}'")