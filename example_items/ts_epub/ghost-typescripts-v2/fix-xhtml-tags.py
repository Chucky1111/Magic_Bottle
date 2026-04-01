#!/usr/bin/env python3
"""
修复XHTML文件中的XML合规性问题：
1. 转义代码块中类似HTML标签的文本（如<string>, <boolean>, <number>, <Array<string>>等）
2. 确保自闭合标签正确闭合（<br> -> <br/>）
3. 修复其他常见的XML问题
"""

import os
import re
import sys
from pathlib import Path

# 需要转义的类似标签的模式（在<code>或<pre>标签内）
# 这些是TypeScript/JavaScript中常见的类型语法，会被误认为XML标签
TAG_LIKE_PATTERNS = [
    # 基本类型
    r'<string>',
    r'<boolean>',
    r'<number>',
    r'<any>',
    r'<unknown>',
    r'<void>',
    r'<null>',
    r'<undefined>',
    r'<never>',
    r'<object>',
    r'<symbol>',
    r'<bigint>',
    
    # 泛型类型
    r'<Array<',
    r'<Promise<',
    r'<Map<',
    r'<Set<',
    r'<Record<',
    r'<Partial<',
    r'<Required<',
    r'<Readonly<',
    r'<Pick<',
    r'<Omit<',
    r'<Exclude<',
    r'<Extract<',
    r'<NonNullable<',
    r'<Parameters<',
    r'<ReturnType<',
    r'<InstanceType<',
    r'<ThisParameterType<',
    r'<OmitThisParameter<',
    r'<ThisType<',
    
    # 通用泛型模式 <T>, <K>, <V>, <U> 等
    r'<[A-Z]>',
    
    # HTML实体也需要转义，但已经是实体了
]

# 自闭合标签列表（XHTML中必须自闭合）
SELF_CLOSING_TAGS = [
    r'<br>',
    r'<br\s*/?>',  # 有些可能已经有斜杠但不规范
    r'<hr>',
    r'<img>',
    r'<input>',
    r'<meta>',
    r'<link>',
    r'<col>',
    r'<area>',
    r'<base>',
    r'<command>',
    r'<embed>',
    r'<keygen>',
    r'<param>',
    r'<source>',
    r'<track>',
    r'<wbr>',
]

def escape_tag_like_text(content):
    """转义代码块中类似HTML标签的文本"""
    # 首先处理<code>和<pre>标签内的内容
    # 使用更精确的方法：找到这些标签，只处理其内部内容
    
    # 简单的实现：先全局替换常见模式
    # 注意：这可能误伤实际HTML标签，但我们的模式很具体
    
    for pattern in TAG_LIKE_PATTERNS:
        # 转义尖括号
        escaped = pattern.replace('<', '&lt;').replace('>', '&gt;')
        # 使用单词边界确保不会匹配到实际标签
        content = re.sub(pattern, escaped, content)
    
    # 处理更复杂的泛型语法，如 Array<string>
    # 使用正则匹配 < 后跟字母数字，然后可能的 <...>，最后 >
    # 但只在代码块内
    
    return content

def fix_self_closing_tags(content):
    """修复自闭合标签"""
    # 将 <br> 替换为 <br/>
    content = re.sub(r'<br>', '<br/>', content)
    content = re.sub(r'<br\s*/?>', '<br/>', content)
    
    # 其他自闭合标签（项目中可能不多）
    content = re.sub(r'<hr>', '<hr/>', content)
    content = re.sub(r'<img>', '<img/>', content)
    content = re.sub(r'<input>', '<input/>', content)
    content = re.sub(r'<meta>', '<meta/>', content)
    content = re.sub(r'<link>', '<link/>', content)
    
    return content

def fix_code_blocks(content):
    """专门处理代码块中的类似标签问题"""
    # 找到所有<code>和<pre>标签
    # 由于嵌套可能复杂，使用更简单的方法：全局替换但确保不在HTML标签属性中
    
    # 替换类似标签的文本，但排除已经在转义实体中的
    # 匹配 < 后跟字母，然后可能的 <...>，然后 >，但不在属性值中
    
    # 简单实现：先处理明显的模式
    patterns = [
        (r'<string>', '&lt;string&gt;'),
        (r'<boolean>', '&lt;boolean&gt;'),
        (r'<number>', '&lt;number&gt;'),
        (r'<any>', '&lt;any&gt;'),
        (r'<unknown>', '&lt;unknown&gt;'),
        (r'<void>', '&lt;void&gt;'),
        (r'<null>', '&lt;null&gt;'),
        (r'<undefined>', '&lt;undefined&gt;'),
        (r'<never>', '&lt;never&gt;'),
        (r'<object>', '&lt;object&gt;'),
        (r'<symbol>', '&lt;symbol&gt;'),
        (r'<bigint>', '&lt;bigint&gt;'),
        
        # 泛型
        (r'<Array<', '&lt;Array&lt;'),
        (r'<Promise<', '&lt;Promise&lt;'),
        (r'<Map<', '&lt;Map&lt;'),
        (r'<Set<', '&lt;Set&lt;'),
        (r'<Record<', '&lt;Record&lt;'),
        
        # 注意：需要同时处理闭尖括号
        # 但这里只处理开标签，闭标签会在后面处理
    ]
    
    for pattern, replacement in patterns:
        content = content.replace(pattern, replacement)
    
    # 处理泛型闭标签
    content = content.replace('Array<string>', 'Array&lt;string&gt;')
    content = content.replace('Array<number>', 'Array&lt;number&gt;')
    content = content.replace('Array<boolean>', 'Array&lt;boolean&gt;')
    content = content.replace('Promise<string>', 'Promise&lt;string&gt;')
    content = content.replace('Promise<number>', 'Promise&lt;number&gt;')
    content = content.replace('Promise<boolean>', 'Promise&lt;boolean&gt;')
    
    # 处理其他常见的泛型模式
    # 使用正则匹配 <T> 其中T是大写字母
    content = re.sub(r'<([A-Z])>', r'&lt;\1&gt;', content)
    
    return content

def process_file(filepath):
    """处理单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # 修复自闭合标签
        content = fix_self_closing_tags(content)
        
        # 修复代码块中的类似标签
        content = fix_code_blocks(content)
        
        if content != original:
            print(f"修改: {filepath}")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        else:
            print(f"无需修改: {filepath}")
            return False
            
    except Exception as e:
        print(f"错误处理 {filepath}: {e}")
        return False

def main():
    # 遍历OEBPS目录下的所有.xhtml和.html文件
    oebps_dir = Path.cwd() / 'OEBPS'
    
    if not oebps_dir.exists():
        print(f"错误: OEBPS目录不存在: {oebps_dir}")
        sys.exit(1)
    
    xhtml_files = list(oebps_dir.rglob('*.xhtml')) + list(oebps_dir.rglob('*.html'))
    
    print(f"找到 {len(xhtml_files)} 个XHTML/HTML文件")
    
    modified_count = 0
    for filepath in xhtml_files:
        if process_file(filepath):
            modified_count += 1
    
    print(f"\n修改了 {modified_count} 个文件")
    
    # 验证修复后的文件
    print("\n验证XML结构...")
    for filepath in xhtml_files:
        # 使用xmllint验证
        import subprocess
        try:
            result = subprocess.run(
                ['xmllint', '--noout', str(filepath)],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                print(f"XML验证失败: {filepath}")
                print(result.stderr[:200])
        except Exception as e:
            print(f"验证时出错 {filepath}: {e}")

if __name__ == '__main__':
    main()