"""
敏感词过滤器模块

功能：
1. 从配置文件加载敏感词词库
2. 支持普通敏感词和正则表达式敏感词
3. 提供文本替换方法
4. 支持词库热重载（可选）
"""

import re
import logging
import os
import time
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Union, Pattern

logger = logging.getLogger(__name__)


class SensitiveWordEntry:
    """敏感词条目"""
    
    def __init__(self, pattern: str, replacement: str = "***", is_regex: bool = False):
        """
        初始化敏感词条目
        
        参数:
            pattern: 敏感词或正则表达式模式
            replacement: 替换文本
            is_regex: 是否为正则表达式
        """
        self.pattern = pattern
        self.replacement = replacement
        self.is_regex = is_regex
        self.compiled_regex: Optional[Pattern] = None
        
        if is_regex:
            try:
                self.compiled_regex = re.compile(pattern)
            except re.error as e:
                logger.error(f"正则表达式编译失败 '{pattern}': {e}")
                # 降级为普通字符串匹配
                self.is_regex = False
    
    def match(self, text: str) -> bool:
        """检查文本是否匹配此敏感词"""
        if self.is_regex and self.compiled_regex:
            return bool(self.compiled_regex.search(text))
        else:
            return self.pattern in text
    
    def replace(self, text: str) -> str:
        """替换文本中的敏感词"""
        if self.is_regex and self.compiled_regex:
            return self.compiled_regex.sub(self.replacement, text)
        else:
            # 普通字符串替换（全部替换）
            return text.replace(self.pattern, self.replacement)
    
    def replace_all(self, text: str) -> str:
        """替换文本中所有出现的敏感词（与replace相同，但为清晰起见保留）"""
        return self.replace(text)


class SensitiveWordFilter:
    """敏感词过滤器"""
    
    def __init__(self, wordlist_path: Optional[Union[str, Path]] = None):
        """
        初始化敏感词过滤器
        
        参数:
            wordlist_path: 敏感词词库文件路径，默认为 config/sensitive_words.txt
        """
        if wordlist_path is None:
            # 默认路径
            base_dir = Path(__file__).parent.parent
            self.wordlist_path = base_dir / "config" / "sensitive_words.txt"
        else:
            self.wordlist_path = Path(wordlist_path)
        
        self.entries: List[SensitiveWordEntry] = []
        self.last_modified_time: float = 0
        self.load_wordlist()
    
    def load_wordlist(self) -> bool:
        """
        加载敏感词词库文件
        
        返回:
            bool: 是否成功加载
        """
        if not self.wordlist_path.exists():
            logger.warning(f"敏感词词库文件不存在: {self.wordlist_path}")
            return False
        
        try:
            # 检查文件修改时间
            current_mtime = os.path.getmtime(self.wordlist_path)
            if current_mtime == self.last_modified_time and self.entries:
                logger.debug("敏感词词库未修改，跳过重新加载")
                return True
            
            with open(self.wordlist_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            new_entries = []
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                
                # 解析行
                parts = line.split(',', 1)
                pattern = parts[0].strip()
                replacement = parts[1].strip() if len(parts) > 1 else "***"
                
                # 检查是否为正则表达式
                is_regex = False
                if pattern.startswith('regex:'):
                    is_regex = True
                    pattern = pattern[6:].strip()  # 移除 'regex:' 前缀
                
                # 创建条目
                try:
                    entry = SensitiveWordEntry(pattern, replacement, is_regex)
                    new_entries.append(entry)
                except Exception as e:
                    logger.error(f"第 {line_num} 行解析失败: {line} - {e}")
            
            self.entries = new_entries
            self.last_modified_time = current_mtime
            
            logger.info(f"加载敏感词词库: {self.wordlist_path}，共 {len(self.entries)} 个条目")
            return True
            
        except Exception as e:
            logger.error(f"加载敏感词词库失败: {e}")
            return False
    
    def reload_if_needed(self) -> bool:
        """检查文件是否修改，如果需要则重新加载"""
        if not self.wordlist_path.exists():
            return False
        
        current_mtime = os.path.getmtime(self.wordlist_path)
        if current_mtime != self.last_modified_time:
            logger.debug("检测到敏感词词库文件修改，重新加载")
            return self.load_wordlist()
        return True
    
    def filter_text(self, text: str, reload_before_filter: bool = False) -> str:
        """
        过滤文本中的敏感词
        
        参数:
            text: 原始文本
            reload_before_filter: 是否在过滤前重新加载词库（用于热重载）
        
        返回:
            str: 过滤后的文本
        """
        if reload_before_filter:
            self.reload_if_needed()
        
        if not self.entries:
            logger.debug("敏感词词库为空，跳过过滤")
            return text
        
        result = text
        # 按顺序应用所有敏感词规则
        # 注意：顺序可能重要，先应用正则表达式，再应用普通字符串？
        # 但为了简单起见，按加载顺序处理
        for entry in self.entries:
            if entry.match(result):
                # 记录匹配到的敏感词（用于调试）
                logger.debug(f"匹配到敏感词: {entry.pattern}，替换为: {entry.replacement}")
                result = entry.replace(result)
        
        return result
    
    def contains_sensitive_words(self, text: str) -> bool:
        """
        检查文本是否包含敏感词
        
        返回:
            bool: 如果包含敏感词则返回True
        """
        for entry in self.entries:
            if entry.match(text):
                return True
        return False
    
    def get_matches(self, text: str) -> List[Tuple[SensitiveWordEntry, int]]:
        """
        获取文本中匹配到的所有敏感词及其位置
        
        返回:
            List[Tuple[SensitiveWordEntry, int]]: 条目和匹配次数的列表
        """
        matches = []
        for entry in self.entries:
            if entry.is_regex and entry.compiled_regex:
                # 正则表达式匹配计数
                count = len(entry.compiled_regex.findall(text))
            else:
                # 普通字符串匹配计数
                count = text.count(entry.pattern)
            if count > 0:
                matches.append((entry, count))
        return matches


def create_default_filter() -> SensitiveWordFilter:
    """创建使用默认词库的过滤器"""
    return SensitiveWordFilter()


if __name__ == "__main__":
    # 测试代码
    import sys
    logging.basicConfig(level=logging.DEBUG)
    
    filter = SensitiveWordFilter()
    
    test_texts = [
        "这是一段包含政治敏感内容的文本。",
        "暴力场景不宜出现。",
        "银行卡号是 1234 5678 9012 3456。",
        "正常文本。",
    ]
    
    for test in test_texts:
        filtered = filter.filter_text(test)
        print(f"原始: {test}")
        print(f"过滤: {filtered}")
        print(f"包含敏感词: {filter.contains_sensitive_words(test)}")
        print()