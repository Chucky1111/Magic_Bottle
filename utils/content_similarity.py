"""
内容相似度检测工具
用于检测章节内容是否过度相似，避免重复内容生成
"""

import logging
import re
from typing import List, Dict, Any, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class ContentSimilarityChecker:
    """内容相似度检查器"""
    
    def __init__(self, similarity_threshold: float = 0.65):
        """
        初始化内容相似度检查器
        
        Args:
            similarity_threshold: 相似度阈值，超过此阈值认为内容过度相似
        """
        self.similarity_threshold = similarity_threshold
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度
        
        Args:
            text1: 第一个文本
            text2: 第二个文本
            
        Returns:
            float: 相似度分数（0.0-1.0）
        """
        if not text1 or not text2:
            return 0.0
        
        # 清理文本：去除空白字符和标点符号
        text1_clean = self._clean_text(text1)
        text2_clean = self._clean_text(text2)
        
        # 如果清理后的文本太短，直接返回0
        if len(text1_clean) < 50 or len(text2_clean) < 50:
            return 0.0
        
        # 使用SequenceMatcher计算相似度
        similarity = SequenceMatcher(None, text1_clean, text2_clean).ratio()
        
        return similarity
    
    def _clean_text(self, text: str) -> str:
        """
        清理文本：去除标点符号、多余空白，转换为小写
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        # 转换为小写
        text = text.lower()
        
        # 去除标点符号
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)
        
        # 去除多余空白
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def check_chapter_similarity(self, new_content: str, recent_chapters: List[Dict[str, Any]], 
                                max_recent_chapters: int = 3) -> Tuple[bool, float, int]:
        """
        检查新章节内容与最近章节的相似度
        
        Args:
            new_content: 新章节内容
            recent_chapters: 最近章节列表，每个元素包含{"chapter_num": int, "content": str}
            max_recent_chapters: 最多检查多少个最近章节
            
        Returns:
            Tuple[bool, float, int]: (是否过度相似, 最高相似度, 最相似的章节号)
        """
        if not new_content:
            return False, 0.0, 0
        
        # 限制检查的章节数量
        chapters_to_check = recent_chapters[-max_recent_chapters:]
        
        max_similarity = 0.0
        most_similar_chapter = 0
        
        for chapter_info in chapters_to_check:
            chapter_num = chapter_info.get("chapter_num", 0)
            chapter_content = chapter_info.get("content", "")
            
            if not chapter_content:
                continue
            
            similarity = self.calculate_similarity(new_content, chapter_content)
            
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_chapter = chapter_num
        
        # 检查是否超过阈值
        is_too_similar = max_similarity > self.similarity_threshold
        
        if is_too_similar:
            logger.warning(f"检测到内容过度相似: 与第{most_similar_chapter}章相似度={max_similarity:.2f} > 阈值{self.similarity_threshold}")
        
        return is_too_similar, max_similarity, most_similar_chapter
    
    def find_duplicate_patterns(self, text: str, min_pattern_length: int = 50) -> List[Tuple[str, int]]:
        """
        查找文本中的重复模式
        
        Args:
            text: 要检查的文本
            min_pattern_length: 最小模式长度
            
        Returns:
            List[Tuple[str, int]]: 重复模式列表，每个元素为(模式内容, 重复次数)
        """
        if len(text) < min_pattern_length * 2:
            return []
        
        patterns = []
        text_length = len(text)
        
        # 从最大可能长度开始检查
        for pattern_length in range(min(text_length // 2, 200), min_pattern_length - 1, -1):
            for start in range(0, text_length - pattern_length * 2 + 1):
                pattern = text[start:start + pattern_length]
                
                # 检查模式是否在后续文本中重复出现
                count = 1
                search_start = start + pattern_length
                
                while True:
                    found_pos = text.find(pattern, search_start)
                    if found_pos == -1:
                        break
                    
                    count += 1
                    search_start = found_pos + pattern_length
                
                # 如果重复次数大于1，记录模式
                if count > 1:
                    # 检查是否已经包含更长的模式
                    is_subpattern = False
                    for existing_pattern, _ in patterns:
                        if pattern in existing_pattern and len(pattern) < len(existing_pattern):
                            is_subpattern = True
                            break
                    
                    if not is_subpattern:
                        patterns.append((pattern, count))
        
        # 按重复次数降序排序
        patterns.sort(key=lambda x: x[1], reverse=True)
        
        return patterns[:5]  # 返回前5个重复模式
    
    def analyze_content_diversity(self, content: str) -> Dict[str, Any]:
        """
        分析内容多样性
        
        Args:
            content: 要分析的内容
            
        Returns:
            Dict[str, Any]: 多样性分析结果
        """
        if not content:
            return {
                "length": 0,
                "unique_words": 0,
                "sentence_count": 0,
                "duplicate_patterns": [],
                "diversity_score": 0.0
            }
        
        # 计算基本统计信息
        length = len(content)
        
        # 分割为单词（中文按字符，英文按单词）
        words = re.findall(r'[\u4e00-\u9fff]|[a-zA-Z]+', content)
        unique_words = len(set(words))
        
        # 分割为句子
        sentences = re.split(r'[。！？.!?]', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)
        
        # 查找重复模式
        duplicate_patterns = self.find_duplicate_patterns(content)
        
        # 计算多样性分数（简化版）
        word_diversity = unique_words / max(len(words), 1)
        sentence_diversity = sentence_count / max(length / 100, 1)  # 每100字符的句子数
        
        # 惩罚重复模式
        pattern_penalty = 0.0
        for pattern, count in duplicate_patterns:
            pattern_penalty += (len(pattern) * count) / length
        
        diversity_score = (word_diversity * 0.4 + sentence_diversity * 0.6) * (1.0 - min(pattern_penalty, 0.5))
        
        return {
            "length": length,
            "unique_words": unique_words,
            "sentence_count": sentence_count,
            "duplicate_patterns": duplicate_patterns,
            "diversity_score": min(max(diversity_score, 0.0), 1.0)
        }


def get_content_similarity_checker(similarity_threshold: float = 0.65) -> ContentSimilarityChecker:
    """
    获取内容相似度检查器实例（单例模式）
    
    Args:
        similarity_threshold: 相似度阈值
        
    Returns:
        ContentSimilarityChecker: 内容相似度检查器实例
    """
    if not hasattr(get_content_similarity_checker, "_instance"):
        get_content_similarity_checker._instance = ContentSimilarityChecker(similarity_threshold)
    
    return get_content_similarity_checker._instance