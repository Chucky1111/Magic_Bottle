"""
上下文管理器 - 辅助函数模块
提供历史记录操作的辅助函数，不负责构建基准上下文
"""

import json
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ContextManager:
    """上下文管理器 - 辅助函数模块
    
    注意：基准上下文现在由 WarmupRunner 构建和管理
    这个类仅提供历史记录操作的辅助函数
    """
    
    def __init__(self):
        """初始化上下文管理器（简化版）"""
        logger.info("ContextManager已初始化（简化版）")
    
    @staticmethod
    def extract_chapter_messages(history: List[Dict[str, Any]], chapter_num: int) -> List[Dict[str, Any]]:
        """
        从历史记录中提取指定章节的所有消息
        
        Args:
            history: 完整的历史记录
            chapter_num: 章节号
            
        Returns:
            该章节的所有消息列表
        """
        chapter_messages = []
        
        for msg in history:
            if msg.get("chapter") == chapter_num:
                chapter_messages.append(msg)
        
        return chapter_messages
    
    @staticmethod
    def find_chapter_message_indices(history: List[Dict[str, Any]], chapter_num: int) -> List[int]:
        """
        查找指定章节消息在历史记录中的索引位置
        
        Args:
            history: 完整的历史记录
            chapter_num: 章节号
            
        Returns:
            索引位置列表
        """
        indices = []
        
        for i, msg in enumerate(history):
            if msg.get("chapter") == chapter_num:
                indices.append(i)
        
        return indices
    
    @staticmethod
    def get_base_context_from_history(history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从历史记录中提取基准上下文
        
        Args:
            history: 完整的历史记录
            
        Returns:
            基准上下文消息列表
        """
        base_context = []
        
        for msg in history:
            if msg.get("is_base_context", False):
                base_context.append(msg)
            else:
                break  # 遇到第一个非基准上下文消息时停止
        
        return base_context
    
    @staticmethod
    def get_base_context_length_from_history(history: List[Dict[str, Any]]) -> int:
        """
        从历史记录中获取基准上下文长度
        
        Args:
            history: 完整的历史记录
            
        Returns:
            基准上下文长度（消息数量）
        """
        length = 0
        for msg in history:
            if msg.get("is_base_context", False):
                length += 1
            else:
                break
        
        # 如果没有找到基准上下文，但历史记录不为空，假设第一条是系统消息
        if length == 0 and history:
            length = 1
        
        return length
    
    @staticmethod
    def validate_history_structure(history: List[Dict[str, Any]]) -> bool:
        """
        验证历史记录结构是否合理
        
        Args:
            history: 完整的历史记录
            
        Returns:
            bool: 历史记录结构是否合理
        """
        if not history:
            return False
        
        # 检查第一条消息是否为系统消息
        first_msg = history[0]
        if first_msg.get("role") != "system":
            logger.warning("历史记录第一条消息不是系统消息")
            return False
        
        # 检查所有消息都有必要的字段
        required_fields = ["role", "content", "timestamp", "chapter", "stage"]
        for i, msg in enumerate(history):
            for field in required_fields:
                if field not in msg:
                    logger.warning(f"历史记录第{i}条消息缺少字段: {field}")
                    return False
        
        return True
    
    @staticmethod
    def get_history_summary(history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取历史记录摘要信息
        
        Args:
            history: 完整的历史记录
            
        Returns:
            摘要信息字典
        """
        if not history:
            return {"total_messages": 0, "chapters": [], "stages": []}
        
        # 统计消息类型
        role_counts = {}
        chapter_counts = {}
        stage_counts = {}
        
        for msg in history:
            role = msg.get("role", "unknown")
            chapter = msg.get("chapter", 0)
            stage = msg.get("stage", "unknown")
            is_base = msg.get("is_base_context", False)
            
            role_counts[role] = role_counts.get(role, 0) + 1
            if chapter > 0:  # 章节0是系统/总结消息
                chapter_counts[chapter] = chapter_counts.get(chapter, 0) + 1
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
        
        # 获取基准上下文长度
        base_context_length = ContextManager.get_base_context_length_from_history(history)
        
        return {
            "total_messages": len(history),
            "base_context_length": base_context_length,
            "role_counts": role_counts,
            "chapters": sorted(chapter_counts.keys()),
            "chapter_counts": chapter_counts,
            "stage_counts": stage_counts,
        }