#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 output 目录中的章节文件导出为 EPUB 格式的书籍
"""

import os
import re
import glob
from datetime import datetime
from ebooklib import epub

def get_chapter_files(output_dir='output'):
    """获取所有章节文件并按章节号排序"""
    pattern = os.path.join(output_dir, '第*章_*.txt')
    files = glob.glob(pattern)
    
    # 提取章节号并排序
    def extract_chapter_number(filename):
        # 从文件名中提取章节号，格式：第X章_标题.txt
        basename = os.path.basename(filename)
        match = re.search(r'第(\d+)章', basename)
        if match:
            return int(match.group(1))
        return 0
    
    files.sort(key=extract_chapter_number)
    return files

def read_chapter_content(filepath):
    """读取章节文件内容"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

def extract_chapter_title(content, filepath):
    """从章节内容中提取标题"""
    # 查找 # 开头的标题行
    lines = content.split('\n')
    for line in lines:
        if line.startswith('# '):
            return line.strip('# ').strip()
    
    # 如果没有找到标题，从文件名中提取标题部分
    # 格式：第X章_标题.txt -> 提取"标题"
    basename = os.path.basename(filepath).replace('.txt', '')
    # 移除"第X章_"前缀
    match = re.search(r'第\d+章_(.+)', basename)
    if match:
        return match.group(1)
    return basename

def create_epub_book(chapter_files, output_path='novel.epub'):
    """创建 EPUB 书籍"""
    
    # 创建 EPUB 书籍对象
    book = epub.EpubBook()
    
    # 设置元数据
    book.set_identifier('deepnovelv3_lite')
    book.set_title('诸天行者：刘斗斗的麻烦日常')
    book.set_language('zh-CN')
    book.add_author('AI-Auto-Novelist')
    book.add_metadata('DC', 'description', '一个穿越诸天的无聊强者，只想安静喝酒，却总被麻烦找上门的故事。')
    
    # 添加封面
    # book.set_cover("cover.jpg", open('cover.jpg', 'rb').read())
    
    # 创建样式表
    style = '''
    @namespace epub "http://www.idpf.org/2007/ops";
    body {
        font-family: "Microsoft YaHei", "SimSun", serif;
        font-size: 1em;
        line-height: 1.6;
        text-align: justify;
        margin: 1em;
    }
    h1 {
        font-size: 1.5em;
        text-align: center;
        margin-top: 2em;
        margin-bottom: 1em;
        page-break-before: always;
    }
    h2 {
        font-size: 1.3em;
        text-align: center;
        margin-top: 1.5em;
        margin-bottom: 1em;
    }
    p {
        text-indent: 2em;
        margin: 0.5em 0;
    }
    .chapter {
        page-break-before: always;
    }
    '''
    
    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=style
    )
    book.add_item(nav_css)
    
    # 存储所有章节
    chapters = []
    
    # 处理每个章节文件
    for i, filepath in enumerate(chapter_files, 1):
        print(f"处理章节 {i}/{len(chapter_files)}: {os.path.basename(filepath)}")
        
        content = read_chapter_content(filepath)
        title = extract_chapter_title(content, filepath)
        
        # 创建章节
        chapter = epub.EpubHtml(
            title=title,
            file_name=f'chapter_{i:03d}.xhtml',
            lang='zh-CN'
        )
        
        # 格式化内容
        html_content = f'''
        <!DOCTYPE html>
        <html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
        <head>
            <title>{title}</title>
            <link rel="stylesheet" type="text/css" href="../style/nav.css"/>
        </head>
        <body>
            <div class="chapter">
                <h1>{title}</h1>
                {format_content_for_html(content)}
            </div>
        </body>
        </html>
        '''
        
        chapter.content = html_content
        book.add_item(chapter)
        chapters.append(chapter)
    
    # 定义目录结构
    book.toc = chapters
    
    # 添加导航文件
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # 定义阅读顺序
    book.spine = ['nav'] + chapters
    
    # 写入 EPUB 文件
    print(f"正在生成 EPUB 文件: {output_path}")
    epub.write_epub(output_path, book, {})
    print(f"EPUB 文件已生成: {output_path}")
    
    return output_path

def format_content_for_html(content):
    """将纯文本内容格式化为 HTML"""
    # 替换换行符为段落
    lines = content.split('\n')
    html_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 处理标题
        if line.startswith('# '):
            html_lines.append(f'<h1>{line[2:].strip()}</h1>')
        elif line.startswith('## '):
            html_lines.append(f'<h2>{line[3:].strip()}</h2>')
        # 处理代码块
        elif line.startswith('```'):
            continue  # 跳过代码块标记
        # 处理普通段落
        else:
            # 转义 HTML 特殊字符
            line = line.replace('&', '&').replace('<', '<').replace('>', '>')
            html_lines.append(f'<p>{line}</p>')
    
    return '\n'.join(html_lines)

def main():
    """主函数"""
    print("开始导出 output 目录内容为 EPUB...")
    
    # 获取章节文件
    chapter_files = get_chapter_files()
    print(f"找到 {len(chapter_files)} 个章节文件")
    
    if not chapter_files:
        print("错误: 未找到章节文件")
        print("请确保 output 目录中包含 '第X章_标题.txt' 格式的文件")
        return
    
    # 创建 EPUB 文件
    output_file = '诸天行者：刘斗斗的麻烦日常.epub'
    try:
        epub_path = create_epub_book(chapter_files, output_file)
        print(f"成功生成 EPUB 文件: {epub_path}")
        print(f"文件大小: {os.path.getsize(epub_path) / 1024 / 1024:.2f} MB")
    except Exception as e:
        print(f"生成 EPUB 文件时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()