#!/usr/bin/env python3
"""
修复<pre>和<code>标签的嵌套问题。
将<pre>&lt;code&gt;...&lt;/code&gt;</pre>恢复为<pre><code>...</code></pre>
同时确保<code>标签正确关闭。
"""

import re
import sys
from pathlib import Path

def fix_nested_tags(content):
    """修复<pre>和<code>标签的嵌套"""
    
    # 模式1：<pre>标签内包含转义的<code>开始标签
    # 匹配 <pre[^>]*>&lt;code&gt;（注意可能有属性）
    content = re.sub(r'(<pre\b[^>]*>)&lt;code&gt;', r'\1<code>', content, flags=re.IGNORECASE)
    
    # 模式2：<pre>标签内包含转义的</code>结束标签，后面跟着</pre>
    content = re.sub(r'&lt;/code&gt;(</pre>)', r'</code>\1', content, flags=re.IGNORECASE)
    
    # 模式3：<code>标签内包含转义的</code>（不应该发生，但以防万一）
    # 我们不处理这种情况
    
    # 模式4：<code>标签内包含转义的<code>标签（嵌套）需要保持转义
    # 但这种情况很少，暂时不处理
    
    # 修复自闭合标签
    content = content.replace('<br>', '<br/>')
    content = content.replace('<br />', '<br/>')
    content = content.replace('<br/>', '<br/>')
    
    # 修复未转义的&符号（除了实体）
    # 将&替换为&amp;，但跳过已有实体
    # 匹配 & 后面不是 (lt|gt|amp|quot|apos|#) 的情况
    content = re.sub(r'&(?!(lt|gt|amp|quot|apos|#)\b)', '&amp;', content)
    
    return content

def process_file(filepath):
    """处理单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # 修复嵌套标签
        content = fix_nested_tags(content)
        
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
        if process_file(filepath):
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
        for filepath, error in error_files[:20]:  # 只显示前20个
            print(f"  {filepath}: {error}")
    else:
        print("所有文件通过XML验证！")

if __name__ == '__main__':
    main()