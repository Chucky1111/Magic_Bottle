#!/usr/bin/env python3
"""
转义代码块中的XML特殊字符
在<code>和<pre>标签内，转义<、>和&字符
"""

import re
import sys
from pathlib import Path

def escape_code_blocks(content):
    """转义<code>和<pre>标签内的XML特殊字符"""
    
    # 匹配<code>...</code>和<pre>...</pre>标签（包括属性）
    # 使用非贪婪匹配，但需要考虑嵌套（代码块内不应有嵌套的同名标签）
    pattern = r'(<(?:code|pre)\b[^>]*>)(.*?)(</(?:code|pre)>)'
    
    def escape_match(match):
        open_tag = match.group(1)
        inner_content = match.group(2)
        close_tag = match.group(3)
        
        # 转义inner_content中的特殊字符
        # 首先处理&（但跳过已经是实体的）
        # 简单方法：先替换&，但注意不要破坏已有实体
        # 将&替换为&amp;，但跳过后面跟着(lt|gt|amp|quot|apos|#)的&
        
        # 转义<
        inner_content = inner_content.replace('<', '&lt;')
        # 转义>
        inner_content = inner_content.replace('>', '&gt;')
        
        # 转义&，但跳过已经是实体的
        # 匹配&后面不是(lt|gt|amp|quot|apos|#)的
        # 使用负向前瞻
        import re
        inner_content = re.sub(r'&(?!(lt|gt|amp|quot|apos|#)\b)', '&amp;', inner_content)
        
        return open_tag + inner_content + close_tag
    
    # 使用re.DOTALL使.匹配换行符（因为代码块可能跨多行）
    result = re.sub(pattern, escape_match, content, flags=re.DOTALL | re.IGNORECASE)
    
    return result

def fix_file(filepath):
    """修复单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # 转义代码块
        content = escape_code_blocks(content)
        
        # 确保自闭合标签正确
        content = content.replace('<br>', '<br/>')
        content = content.replace('<br/>', '<br/>')  # 确保一致
        content = content.replace('<br />', '<br/>')
        
        if content != original:
            print(f"修复: {filepath}")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        else:
            print(f"无需修复: {filepath}")
            return False
            
    except Exception as e:
        print(f"错误处理 {filepath}: {e}")
        return False

def main():
    oebps_dir = Path.cwd() / 'OEBPS'
    
    if not oebps_dir.exists():
        print(f"错误: OEBPS目录不存在: {oebps_dir}")
        sys.exit(1)
    
    xhtml_files = list(oebps_dir.rglob('*.xhtml')) + list(oebps_dir.rglob('*.html'))
    
    print(f"找到 {len(xhtml_files)} 个文件")
    
    modified_count = 0
    for filepath in xhtml_files:
        if fix_file(filepath):
            modified_count += 1
    
    print(f"\n修复了 {modified_count} 个文件")
    
    # 验证修复
    print("\n验证XML结构...")
    error_files = []
    for filepath in xhtml_files:
        import subprocess
        try:
            result = subprocess.run(
                ['xmllint', '--noout', str(filepath)],
                capture_output=True,
                text=True,
                timeout=3
            )
            if result.returncode != 0:
                error_files.append((filepath, result.stderr[:200]))
        except Exception as e:
            error_files.append((filepath, str(e)))
    
    if error_files:
        print(f"\n{len(error_files)} 个文件仍有XML错误:")
        for filepath, error in error_files[:10]:  # 只显示前10个
            print(f"  {filepath}: {error}")
    else:
        print("所有文件通过XML验证！")

if __name__ == '__main__':
    main()