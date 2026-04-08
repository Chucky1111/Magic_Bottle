"""
文本处理器 - 实现小说文本的清理规则

规则：
1. 删除短引号：如果一组引号（单引号或双引号）包裹的是五个字以下且里面没有标点符号（比如逗号句号）的时候就把引号删除
2. 处理"不是...，..是..."句式：
   - 删除"不是...，而"，保留"是"和之后的内容
   - 删除"不是...，...是"，只保留"是"之后的内容，"是"也不要
3. 删除小括号包裹的内容：直接删除括号和内容
4. 处理"没有...没有...只有..."句式：
   - 删除所有"没有"打头的句子（整句删除）
   - 删除后句的"只有"，保留"只有"之后的内容
5. 删除Markdown强调语法：删除**内容**、*内容*、__内容__、_内容_等Markdown标记
"""

import re
import logging
import time
import json
from typing import List, Tuple, Optional
from pathlib import Path
from utils.sensitive_words import SensitiveWordFilter

logger = logging.getLogger(__name__)


class LayoutFormatter:
    """版式重排器 - 处理分段和空行规范化"""
    
    def __init__(self):
        """初始化版式重排器"""
        # 句子结束标点
        self.sentence_endings = {'。', '！', '？', '!', '?'}
        # 引号字符 - 包括各种引号和括号（去重）
        self.quotes = {'"', "'", '「', '」', '『', '』', '“', '”', '【', '】', '《', '》', '〈', '〉', '〔', '〕'}
        
    def normalize_paragraphs(self, text: str) -> str:
        """
        规范化段落空行
        
        1. 消除所有多余空行（连续多个空行变为无空行）
        2. 每段之间加一个空行
        3. 处理单独成行的引号：将只包含引号字符的行与前一个非空行合并
        """
        if not text:
            return text
        
        # 分割成行
        lines = text.split('\n')
        normalized_lines = []
        
        # 第一步：处理所有行，合并单独成行的引号
        i = 0
        while i < len(lines):
            line = lines[i]
            line_stripped = line.strip()
            
            if not line_stripped:  # 空行
                # 如果上一条不是空行，则保留一个空行占位符
                if normalized_lines and normalized_lines[-1] != '':
                    normalized_lines.append('')
                i += 1
            else:
                # 检查是否只包含引号字符
                if self._is_quote_only_line(line_stripped):
                    # 寻找前一个非空行
                    merged = False
                    for j in range(len(normalized_lines) - 1, -1, -1):
                        if normalized_lines[j] != '':
                            # 找到前一个非空行，将引号附加到其末尾
                            normalized_lines[j] = normalized_lines[j] + line_stripped
                            merged = True
                            break
                    if not merged:
                        # 没有前一个非空行，直接添加
                        normalized_lines.append(line)
                else:
                    normalized_lines.append(line)
                i += 1
        
        # 第二步：确保每段之间有一个空行
        result_lines = []
        for i, line in enumerate(normalized_lines):
            line_stripped = line.strip()
            if not line_stripped:  # 空行
                # 确保不会连续两个空行
                if not result_lines or result_lines[-1] != '':
                    result_lines.append('')
            else:
                # 非空行，直接添加
                result_lines.append(line)
                # 如果不是最后一行，且下一行不是空行，则添加一个空行
                if i + 1 < len(normalized_lines) and normalized_lines[i + 1].strip():
                    result_lines.append('')
        
        # 移除末尾多余的空行
        while result_lines and result_lines[-1] == '':
            result_lines.pop()
        
        return '\n'.join(result_lines)
    
    def _is_quote_only_line(self, line: str) -> bool:
        """
        检查一行是否只包含引号字符
        
        参数:
            line: 要检查的行（已去除首尾空白）
            
        返回:
            bool: 如果行只包含引号字符则返回True
        """
        # 引号字符集合 - 包括所有类型的引号
        quote_chars = {
            '"', "'",                       # 英文引号
            '「', '」', '『', '』',         # 中文引号
            '“', '”',                       # 中文双引号（U+201C, U+201D）
            '【', '】',                     # 中文括号
            '《', '》',                     # 中文书名号
            '〈', '〉',                     # 中文单书名号
            '〔', '〕',                     # 中文括号
            '"', '"',                       # 中文双引号（U+201C, U+201D）的另一种表示
        }
        
        # 检查每个字符是否都是引号字符
        for char in line:
            if char not in quote_chars:
                return False
        return True
    
    def split_into_paragraphs(self, text: str) -> str:
        """
        将文本按句子分段
        
        规则：
        1. 每遇到句号、感叹号、问号单独分一段
        2. 引号包裹内的内容要排除（因为是对话）
        3. 完整的对话内容不被分段，即使中间有句号
        4. 支持中文引号配对（"和"）
        """
        if not text:
            return text
        
        paragraphs = []
        current_paragraph = []
        in_quote = False
        quote_char = None
        i = 0
        
        # 定义引号配对
        quote_pairs = {
            '"': '"',      # 英文双引号配对相同字符
            "'": "'",      # 英文单引号配对相同字符
            '「': '」',    # 中文引号
            '」': '「',    # 中文引号（反向）
            '『': '』',    # 中文引号
            '』': '『',    # 中文引号（反向）
            '“': '”',      # 中文左双引号（U+201C）配对右双引号（U+201D）
            '”': '“',      # 中文右双引号（U+201D）配对左双引号（U+201C）
            '【': '】',    # 中文括号
            '】': '【',    # 中文括号（反向）
            '《': '》',    # 中文书名号
            '》': '《',    # 中文书名号（反向）
            '〈': '〉',    # 中文单书名号
            '〉': '〈',    # 中文单书名号（反向）
            '〔': '〕',    # 中文括号
            '〕': '〔',    # 中文括号（反向）
        }
        
        # 调试计数器
        debug_counter = 0
        
        while i < len(text):
            char = text[i]
            debug_counter += 1
            
            # 处理引号
            if char in self.quotes:
                if not in_quote:
                    # 进入引号
                    in_quote = True
                    quote_char = char
                elif char == quote_char or (quote_char in quote_pairs and char == quote_pairs[quote_char]):
                    # 退出引号：相同字符或配对字符
                    in_quote = False
                    quote_char = None
            
            current_paragraph.append(char)
            
            # 检查是否应该分段
            should_split = False
            
            # 只有在不在引号内时，才根据句子结束标点分段
            if char in self.sentence_endings and not in_quote:
                # 不在引号内的句子结束标点
                should_split = True
            elif char == '\n' and not in_quote:
                # 换行符也作为分段点，但引号内的换行符不分段
                should_split = True
            
            if should_split:
                # 完成当前段落
                paragraph_text = ''.join(current_paragraph).strip()
                if paragraph_text:
                    paragraphs.append(paragraph_text)
                current_paragraph = []
            
            i += 1
        
        # 处理最后一段
        if current_paragraph:
            paragraph_text = ''.join(current_paragraph).strip()
            if paragraph_text:
                paragraphs.append(paragraph_text)
        
        # 将段落组合，每段之间加空行
        result = '\n\n'.join(paragraphs)
        
        
        return result
    
    def reformat_layout(self, text: str) -> str:
        """
        完整的版式重排
        
        步骤：
        1. 按句子分段
        2. 规范化空行
        """
        if not text:
            return text
        
        # 先分段
        text = self.split_into_paragraphs(text)
        # 再规范化空行
        text = self.normalize_paragraphs(text)
        
        return text


class TextProcessor:
    """文本处理器类"""
    
    def __init__(self, enable_sensitive_filter: bool = True, sensitive_wordlist_path: Optional[str] = None):
        """初始化文本处理器
        
        参数:
            enable_sensitive_filter: 是否启用敏感词过滤
            sensitive_wordlist_path: 敏感词词库文件路径，默认为 config/sensitive_words.txt
        """
        # 编译正则表达式以提高性能
        self.short_quote_pattern = re.compile(r'["\'「」]([^"\'「」，。！？；]{1,5})["\'「」]')
        self.parentheses_pattern = re.compile(r'[（(][^）)]*[）)]')
        
        # 规则2的复杂模式
        # 匹配 "不是...，...是..." 句式
        self.not_is_pattern = re.compile(
            r'不是([^，。！？；]{1,20})，([^，。！？；]{0,3})是([^，。！？；]*)'
        )
        
        # 规则4：匹配 "没有...没有...只有..." 句式
        # 匹配两个或更多"没有"打头的句子，后面跟着"只有"打头的句子
        self.no_no_only_pattern = re.compile(
            r'没有[^，。！？；]*[，、。]?\s*没有[^，。！？；]*[，、。]?\s*[^。！？；]*只有([^。！？；]*)'
        )
        
        # 规则5：匹配Markdown强调语法
        # 匹配 **内容**、*内容*、__内容__、_内容_
        self.markdown_emphasis_pattern = re.compile(
            r'(\*\*|\*|__|_)([^\*\n_]+?)\1'
        )
        
        # 版式重排器
        self.layout_formatter = LayoutFormatter()
        
        # 敏感词过滤器
        self.enable_sensitive_filter = enable_sensitive_filter
        if enable_sensitive_filter:
            try:
                self.sensitive_filter = SensitiveWordFilter(sensitive_wordlist_path)
                logger.info(f"敏感词过滤器已启用，词库路径: {self.sensitive_filter.wordlist_path}")
            except Exception as e:
                logger.error(f"初始化敏感词过滤器失败: {e}")
                self.enable_sensitive_filter = False
                self.sensitive_filter = None
        else:
            self.sensitive_filter = None
        
    def process_short_quotes(self, text: str) -> str:
        """
        规则1：删除短引号
        
        条件：
        1. 引号包裹的内容在5个字以下（不含标点）
        2. 内容中没有标点符号（逗号、句号等）
        3. 引号可以是单引号、双引号或中文引号
        """
        # 定义所有引号对（左引号，右引号）
        quote_pairs = [
            ('"', '"'),                    # 英文双引号
            ("'", "'"),                    # 英文单引号
            ('\u201c', '\u201d'),          # 中文双引号（左双引号U+201C，右双引号U+201D）
            ('\u2018', '\u2019'),          # 中文单引号
            ('「', '」'),                  # 中文引号
            ('『', '』'),                  # 中文引号
            ('《', '》'),                  # 中文引号
            ('〈', '〉'),                  # 中文引号
        ]
        
        # 遍历所有引号对
        for left_quote, right_quote in quote_pairs:
            # 构建正则表达式：左引号 + 内容（不包含右引号） + 右引号
            pattern = re.escape(left_quote) + r'([^' + re.escape(right_quote) + r']{1,20})' + re.escape(right_quote)
            
            def replace_callback(match, lq=left_quote, rq=right_quote):
                content = match.group(1)  # 引号内的内容
                # 检查是否包含中文字符，如果不包含则保留引号（规则仅针对中文）
                if not re.search(r'[\u4e00-\u9fff]', content):
                    return match.group(0)
                # 检查内容长度（中文字符计数）
                chinese_chars = re.findall(r'[\u4e00-\u9fff]', content)
                if len(chinese_chars) <= 10:
                    # 检查是否包含标点符号（中文和英文标点）
                    if not re.search(r'[，。！？；、…—\.\,\!\?\;\:\"\'\“\”]', content):
                        # 删除引号，保留内容
                        return content
                # 不符合条件，保留原样
                return match.group(0)
            
            text = re.sub(pattern, replace_callback, text)
        
        return text
    
    def process_not_is_pattern(self, text: str) -> str:
        """
        规则2：处理"不是...，..是..."句式

        两种处理方式：
        1. 删除"不是...，而"，保留"是"和之后的内容
        2. 删除"不是...，...是"，只保留"是"之后的内容，"是"也不要

        实现逻辑：
        - 匹配"不是A，B是C"模式
        - 如果B是"而"、"而是"、"反而是"等三个字以内包含"是"的词
        - 则删除"不是A，B"，保留"是C"
        - 否则删除"不是A，B是"，保留"C"
        """
        # 允许的中间词语集合（保留"是"）
        allowed_middle_words = {"而", "而是", "反而是", "却是", "不过是"}

        # 更灵活的正则表达式，匹配各种变体
        patterns = [
            # 模式0: 跨行句式 "不是...。是..."
            r'不是([^。]*)。\s*是([^。]*)',
            # 模式1: 不是A，B是C (B在3个字以内且包含"是")
            r'不是([^，。！？；]{1,30})，([^，。！？；]{0,3}是)([^，。！？；]*)',
            # 模式2: 不是A，B是C (B在3个字以内但不一定包含"是")
            r'不是([^，。！？；]{1,30})，([^，。！？；]{1,3})是([^，。！？；]*)',
            # 模式3: 不是A，是C (没有中间部分)
            r'不是([^，。！？；]{1,30})，是([^，。！？；]*)',
        ]

        for pattern in patterns:
            def replace_callback(match):
                groups = match.groups()
                if len(groups) == 3:
                    # 模式1或2: 不是A，B是C
                    not_part, middle_part, is_part = groups
                    # 检查中间部分是否在允许的词语集合中
                    if middle_part in allowed_middle_words:
                        # 情况1：删除"不是...，而"，保留"是"和之后的内容
                        return f"是{is_part}"
                    else:
                        # 情况2：删除"不是...，...是"，只保留"是"之后的内容
                        return is_part
                elif len(groups) == 2:
                    # 模式3: 不是A，是C
                    not_part, is_part = groups
                    # 直接保留"是"之后的内容（删除"是"）
                    return is_part
                return match.group(0)

            text = re.sub(pattern, replace_callback, text)

        return text

    def process_dialog_not_pattern(self, text: str) -> str:
        """
        处理对话中“不是...。”句式删除
        模式： “不是...。”说话者，“是...”
        删除第一个引号及其内容，保留说话者和第二个引号。
        示例：
            “不是普通漏水。”林晚压低声音，“是从天花板渗下来的水珠...”
            → 林晚压低声音，“从天花板渗下来的水珠...”
        """
        # 匹配中文全角引号、英文半角引号
        # 模式：引号 + 不是...句号 + 引号 + 说话者 + 引号 + 内容 + 引号
        # 使用非贪婪匹配
        pattern = re.compile(
            r'[“"](不是[^“"]*?[。！？])[”"]'   # 第一个引号及内容
            r'([^“"]*?)'                     # 说话者
            r'[“"]([^“"]*?)[”"]'             # 第二个引号及内容
        )
        def replace(match):
            speaker = match.group(2)
            second_content = match.group(3)
            # 保留说话者和第二个引号（使用中文引号）
            return speaker + '“' + second_content + '”'
        text = re.sub(pattern, replace, text)
        return text

    def remove_parentheses(self, text: str) -> str:
        """
        规则3：删除小括号包裹的内容

        直接删除括号和内容，包括：
        - 中文括号：（内容）
        - 英文括号：(内容)
        支持嵌套括号：递归删除最内层括号
        """
        # 处理中文括号
        while True:
            # 查找最内层的括号对：不包含其他括号的括号对
            match = re.search(r'[（][^（）]*[）]', text)
            if not match:
                break
            text = text[:match.start()] + text[match.end():]

        # 处理英文括号
        while True:
            match = re.search(r'\([^()]*\)', text)
            if not match:
                break
            text = text[:match.start()] + text[match.end():]

        return text
    
    def process_no_no_only_pattern(self, text: str) -> str:
        """
        规则4：处理"没有...没有...只有..."句式
        
        处理方式：
        1. 删除所有"没有"打头的句子（整句删除）
        2. 删除后句的"只有"，保留"只有"之后的内容
        
        示例：
        "没有白光，没有眩晕，更没有引导精灵。只有眼前一黑，像熬夜熬狠了突然断片。"
        → "眼前一黑，像熬夜熬狠了突然断片。"
        """
        # 定义多个模式来匹配不同的变体
        patterns = [
            # 模式1：没有A，没有B，只有C
            r'没有[^，。！？；]*[，、。]?\s*没有[^，。！？；]*[，、。]?\s*[^。！？；]*只有([^。！？；]*)',
            # 模式2：没有A，没有B，更没有C。只有D
            r'没有[^，。！？；]*[，、。]?\s*没有[^，。！？；]*[，、。]?\s*更没有[^，。！？；]*[。！？]\s*只有([^。！？；]*)',
            # 模式3：没有A，没有B。只有C
            r'没有[^，。！？；]*[，、。]?\s*没有[^，。！？；]*[。！？]\s*只有([^。！？；]*)',
            # 模式4：没有A、没有B、只有C
            r'没有[^，。！？；]*[、，]?\s*没有[^，。！？；]*[、，]?\s*只有([^。！？；]*)',
        ]
        
        for pattern in patterns:
            def replace_callback(match):
                # 提取"只有"之后的内容
                only_content = match.group(1).strip()
                # 如果内容以标点开头，去掉开头的标点
                if only_content and only_content[0] in '，、。！？；':
                    only_content = only_content[1:].strip()
                return only_content
            
            text = re.sub(pattern, replace_callback, text)
        
        return text
    
    def remove_markdown_emphasis(self, text: str) -> str:
        """
        规则5：删除Markdown强调语法
        
        删除以下Markdown标记，但保留内容：
        1. **内容** - 粗体
        2. *内容* - 斜体
        3. __内容__ - 粗体（下划线）
        4. _内容_ - 斜体（下划线）
        
        注意：支持处理嵌套情况，如**粗体中的*斜体***
        """
        # 使用贪婪匹配处理所有标记类型
        # 先处理双标记，再处理单标记，使用贪婪匹配确保处理嵌套
        
        # 定义标记模式（贪婪匹配）
        patterns = [
            (r'\*\*(.*?)\*\*', r'\1'),   # **内容** - 贪婪匹配
            (r'__(.*?)__', r'\1'),       # __内容__ - 贪婪匹配
            (r'\*(.*?)\*', r'\1'),       # *内容* - 贪婪匹配
            (r'_(.*?)_', r'\1'),         # _内容_ - 贪婪匹配
        ]
        
        # 多次迭代处理，确保所有标记都被删除
        for pattern, replacement in patterns:
            # 多次应用直到没有变化
            while True:
                new_text = re.sub(pattern, replacement, text)
                if new_text == text:
                    break
                text = new_text
        
        return text

    def normalize_punctuation(self, text: str) -> str:
        """
        将半角标点符号转换为全角（中文排版常用）。
        注意：引号转换较复杂，此处仅处理基本标点。
        排除数字上下文中的点号（如小数点、百分比）。
        """
        # 半角到全角的映射表（排除点号，单独处理）
        half_to_full = {
            ',': '，',
            '!': '！',
            '?': '？',
            ';': '；',
            ':': '：',
            '(': '（',
            ')': '）',
            '[': '【',
            ']': '】',
            '<': '《',
            '>': '》',
            '"': '“',   # 简单处理，不区分左右
            "'": '‘',
        }
        # 保护数字上下文中的点号：前后都是数字的情况
        temp_marker = '\uE001'
        protected = re.sub(r'(?<=\d)\.(?=\d)', temp_marker, text)
        
        # 应用其他标点转换
        trans_table = str.maketrans(half_to_full)
        converted = protected.translate(trans_table)
        
        # 将剩余的点号转换为句号
        converted = re.sub(r'\.', '。', converted)
        
        # 恢复被保护的点号
        result = converted.replace(temp_marker, '.')
        return result

    def process_text(self, text: str, reformat_layout: bool = True) -> str:
        """
        应用所有文本处理规则
        
        参数:
            text: 原始文本
            reformat_layout: 是否进行版式重排
            
        返回:
            处理后的文本
        """
        if not text:
            return text
        
        original_length = len(text)
        
        # 按行处理，保留换行符
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            if not line.strip():  # 空行
                processed_lines.append(line)
                continue
                
            # 按顺序应用规则
            processed_line = self.remove_markdown_emphasis(line)
            processed_line = self.process_short_quotes(processed_line)
            processed_line = self.process_not_is_pattern(processed_line)
            processed_line = self.process_dialog_not_pattern(processed_line)
            processed_line = self.remove_parentheses(processed_line)
            processed_line = self.process_no_no_only_pattern(processed_line)

            # 清理多余的空格（但保留行内的正常空格）
            processed_line = re.sub(r'[ \t]+', ' ', processed_line).strip()
            processed_lines.append(processed_line)
        
        # 重新组合文本，保留原始换行结构
        text = '\n'.join(processed_lines)

        # 处理跨行句式（如“不是...。是...”）
        text = self.process_not_is_pattern(text)

        # 标点符号全角化
        text = self.normalize_punctuation(text)
        
        # 敏感词过滤
        if self.enable_sensitive_filter and self.sensitive_filter:
            text = self.sensitive_filter.filter_text(text)
        
        # 版式重排
        if reformat_layout:
            text = self.layout_formatter.reformat_layout(text)
        
        # 修复段落首行缩进问题：删除每行开头的空格和制表符
        # 但保留空行
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.strip():  # 非空行
                # 删除行首的空格和制表符
                cleaned_line = re.sub(r'^[ \t]+', '', line)
                cleaned_lines.append(cleaned_line)
            else:
                # 空行保持不变
                cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        processed_length = len(text)
        if original_length != processed_length:
            logger.debug(f"文本处理: {original_length} -> {processed_length} 字符")
        
        return text
    
    def process_file(self, input_path: Path, output_path: Optional[Path] = None,
                    reformat_layout: bool = True) -> bool:
        """
        处理整个文件
        
        参数:
            input_path: 输入文件路径
            output_path: 输出文件路径（如果为None，则覆盖原文件）
            reformat_layout: 是否进行版式重排
            
        返回:
            bool: 处理是否成功
        """
        try:
            # 读取文件
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 处理文本
            processed_content = self.process_text(content, reformat_layout)
            
            # 确定输出路径
            if output_path is None:
                output_path = input_path
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            
            logger.info(f"文件处理完成: {input_path} -> {output_path}")
            logger.info(f"原始长度: {len(content)} 字符, 处理后: {len(processed_content)} 字符")
            
            return True
            
        except Exception as e:
            logger.error(f"处理文件失败 {input_path}: {e}")
            return False


class FileMonitor:
    """文件监控器 - 监控目录下的新章节文件"""
    
    def __init__(self, watch_dir: Path = Path("output"), output_dir: Optional[Path] = None,
                 enable_sensitive_filter: bool = True, sensitive_wordlist_path: Optional[str] = None):
        """
        初始化文件监控器
        
        参数:
            watch_dir: 监控的目录路径
            output_dir: 输出目录路径（如果为None，则覆盖原文件）
            enable_sensitive_filter: 是否启用敏感词过滤
            sensitive_wordlist_path: 敏感词词库文件路径
        """
        self.watch_dir = watch_dir
        self.output_dir = output_dir
        self.processor = TextProcessor(enable_sensitive_filter=enable_sensitive_filter,
                                       sensitive_wordlist_path=sensitive_wordlist_path)
        self.processed_files = set()
        
        # 确保目录存在
        self.watch_dir.mkdir(exist_ok=True)
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 状态文件路径
        self.state_file = Path("data/text_processor_state.json")
        
        logger.info(f"文件监控器初始化完成，监控目录: {watch_dir}")
        if self.output_dir:
            logger.info(f"输出目录: {output_dir}")
    
    def load_state(self) -> None:
        """加载已处理文件的状态"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    self.processed_files = set(state.get("processed_files", []))
                logger.info(f"加载状态: 已处理 {len(self.processed_files)} 个文件")
        except Exception as e:
            logger.warning(f"加载状态失败: {e}")
            self.processed_files = set()
    
    def save_state(self) -> None:
        """保存已处理文件的状态"""
        try:
            state = {
                "processed_files": list(self.processed_files),
                "timestamp": time.time()
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            logger.debug("状态已保存")
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
    
    def get_new_files(self) -> List[Path]:
        """获取需要处理的新文件"""
        new_files = []
        
        try:
            # 获取目录下所有.txt文件
            for file_path in self.watch_dir.glob("*.txt"):
                if file_path.name not in self.processed_files:
                    new_files.append(file_path)
            
            # 按文件名排序（通常是按章节顺序）
            new_files.sort(key=lambda x: x.name)
            
        except Exception as e:
            logger.error(f"扫描目录失败: {e}")
        
        return new_files
    
    def process_new_files(self, reformat_layout: bool = True) -> int:
        """
        处理所有新文件
        
        参数:
            reformat_layout: 是否进行版式重排
            
        返回:
            int: 处理的文件数量
        """
        new_files = self.get_new_files()
        
        if not new_files:
            logger.info("没有发现新文件需要处理")
            return 0
        
        logger.info(f"发现 {len(new_files)} 个新文件需要处理")
        
        processed_count = 0
        for file_path in new_files:
            logger.info(f"处理文件: {file_path.name}")
            
            # 确定输出路径
            if self.output_dir:
                # 保存到输出目录，保持相同文件名
                output_path = self.output_dir / file_path.name
            else:
                # 覆盖原文件
                output_path = None
            
            # 处理文件
            success = self.processor.process_file(file_path, output_path, reformat_layout=reformat_layout)
            
            if success:
                self.processed_files.add(file_path.name)
                processed_count += 1
                logger.info(f"文件处理成功: {file_path.name}")
            else:
                logger.error(f"文件处理失败: {file_path.name}")
        
        # 保存状态
        if processed_count > 0:
            self.save_state()
        
        return processed_count
    
    def run_once(self, reformat_layout: bool = True) -> int:
        """
        运行一次监控和处理
        
        参数:
            reformat_layout: 是否进行版式重排
            
        返回:
            int: 处理的文件数量
        """
        self.load_state()
        processed_count = self.process_new_files(reformat_layout=reformat_layout)
        return processed_count
    
    def run_continuous(self, interval_seconds: int = 10, reformat_layout: bool = True) -> None:
        """
        持续运行监控
        
        参数:
            interval_seconds: 检查间隔（秒）
            reformat_layout: 是否进行版式重排
        """
        import time
        
        logger.info(f"开始持续监控，检查间隔: {interval_seconds}秒")
        logger.info("按 Ctrl+C 停止")
        
        try:
            while True:
                processed = self.run_once(reformat_layout=reformat_layout)
                if processed > 0:
                    logger.info(f"本轮处理完成: {processed} 个文件")
                else:
                    logger.debug("没有新文件需要处理")
                
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("监控被用户中断")
        except Exception as e:
            logger.error(f"监控运行异常: {e}")


def setup_logging() -> None:
    """配置日志"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 控制台日志
    import sys
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # 配置根日志器
    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler]
    )


if __name__ == "__main__":
    import sys
    import time
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description="小说文本处理器")
    parser.add_argument("--mode", choices=["once", "continuous"], default="once",
                       help="运行模式: once(单次) 或 continuous(持续监控)")
    parser.add_argument("--interval", type=int, default=10,
                       help="持续监控时的检查间隔（秒）")
    parser.add_argument("--input", type=str, help="单个文件处理模式：输入文件路径")
    parser.add_argument("--output", type=str, help="单个文件处理模式：输出文件路径")
    
    args = parser.parse_args()
    
    if args.input:
        # 单个文件处理模式
        processor = TextProcessor()
        input_path = Path(args.input)
        output_path = Path(args.output) if args.output else None
        
        if not input_path.exists():
            logger.error(f"输入文件不存在: {input_path}")
            sys.exit(1)
        
        success = processor.process_file(input_path, output_path)
        sys.exit(0 if success else 1)
    
    else:
        # 目录监控模式
        monitor = FileMonitor()
        
        if args.mode == "once":
            logger.info("执行单次处理模式")
            processed = monitor.run_once()
            logger.info(f"处理完成: {processed} 个文件")
        else:
            logger.info("执行持续监控模式")
            monitor.run_continuous(args.interval)