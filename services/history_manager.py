"""
历史记录管理器 - 负责历史记录的加载、保存和基本操作
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class HistoryManager:
    """历史记录管理器 - 处理历史记录的持久化操作"""
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化历史记录管理器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.history_path = self.data_dir / "history.json"
    
    def load_history(self) -> List[Dict[str, Any]]:
        """加载历史记录"""
        if not self.history_path.exists():
            return []
        
        try:
            with open(self.history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
            return history
        except Exception as e:
            logger.error(f"加载历史记录失败: {e}")
            return []
    
    def save_history(self, history: List[Dict[str, Any]]) -> None:
        """保存历史记录"""
        try:
            with open(self.history_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            logger.debug(f"历史记录已保存: {len(history)} 条消息")
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")
    
    def add_message(self, role: str, content: str, chapter_num: int, stage: str,
                   is_base_context: bool = False, **extra_fields) -> None:
        """
        添加消息到历史记录（基础版本）
        
        Args:
            role: 消息角色 (user/assistant/system)
            content: 消息内容
            chapter_num: 章节号
            stage: 阶段 (design/write/summary/base/feedback)
            is_base_context: 是否为基准上下文
            **extra_fields: 额外的字段
        """
        history = self.load_history()
        
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "chapter": chapter_num,
            "stage": stage,
            "is_base_context": is_base_context,
            **extra_fields
        }
        
        history.append(message)
        self.save_history(history)
        logger.debug(f"历史记录已添加: {role} - 第{chapter_num}章 - {stage}")
    
    def add_summary_message(self, content: str, summary_chapter: int, 
                           window_chapters: List[int], summary_status: int,
                           generation_cycle: str) -> None:
        """
        添加总结消息到历史记录（特殊处理）
        
        Args:
            content: 总结内容
            summary_chapter: 总结关联的章节号（通常是窗口中的最大章节）
            window_chapters: 窗口章节列表
            summary_status: 总结状态编号
            generation_cycle: 生成周期标识
        """
        history = self.load_history()
        
        # 生成窗口ID
        window_id = f"window_{window_chapters[0]}_{window_chapters[1]}_{window_chapters[2]}" if len(window_chapters) == 3 else "window_unknown"
        
        message = {
            "role": "assistant",
            "content": content,
            "timestamp": time.time(),
            "chapter": 0,  # 修复：总结消息的章节号始终为0，避免影响修剪逻辑
            "stage": "summary",
            "is_base_context": False,
            "is_summary": True,  # 标记为总结消息
            "window_chapters": window_chapters,  # 记录总结的是哪些章节
            "summary_chapter": summary_chapter,  # 记录关联的章节号，用于调试
            "summary_status": summary_status,  # 新增：总结状态编号
            "window_id": window_id,  # 新增：窗口ID
            "generation_cycle": generation_cycle  # 新增：生成周期标识
        }
        
        history.append(message)
        self.save_history(history)
        
        logger.info(f"总结消息已添加: 状态={summary_status}, 窗口={window_chapters}, "
                   f"周期={generation_cycle}, 关联章节={summary_chapter}")
    
    def infer_base_context_length(self, history: List[Dict[str, Any]] = None) -> int:
        """
        从历史记录中推断基准上下文长度
        
        Args:
            history: 历史记录（如果为None，则从文件加载）
            
        Returns:
            int: 基准上下文长度
        """
        if history is None:
            history = self.load_history()
        
        # 查找最后一个 is_base_context=True 的消息
        base_context_length = 0
        for i, msg in enumerate(history):
            if msg.get("is_base_context", False):
                base_context_length = i + 1
            else:
                break
        
        # 如果没有找到，假设第一条消息是系统消息
        if base_context_length == 0 and history:
            base_context_length = 1
        
        return base_context_length
    
    def create_minimal_history(self, system_content: str = None) -> None:
        """
        创建最小化历史记录（仅系统消息）
        
        Args:
            system_content: 系统提示词内容，如果为None则使用默认
        """
        if system_content is None:
            system_content = "你是一位专业的小说作家。"
        
        history = [{
            "role": "system",
            "content": system_content,
            "timestamp": 0,
            "chapter": 0,
            "stage": "base",
            "is_base_context": True
        }]
        
        self.save_history(history)
        logger.info("创建最小化历史记录（仅系统消息）")
    
    def update_user_prompt(self, chapter_num: int, stage: str, 
                          simplified_prompt: str) -> bool:
        """
        更新历史记录中的用户提示词为简化版本
        
        Args:
            chapter_num: 章节号
            stage: 阶段 (design/write)
            simplified_prompt: 简化后的提示词
            
        Returns:
            bool: 是否成功更新
        """
        history = self.load_history()
        if not history:
            return False
        
        # 查找最近的对应用户消息
        user_message_index = -1
        for i in range(len(history) - 1, -1, -1):
            msg = history[i]
            if (msg.get("role") == "user" and
                msg.get("chapter") == chapter_num and
                msg.get("stage") == stage):
                user_message_index = i
                break
        
        if user_message_index == -1:
            logger.debug(f"未找到第{chapter_num}章{stage}阶段的用户消息")
            return False
        
        # 更新用户消息
        original_content = history[user_message_index]["content"]
        history[user_message_index]["content"] = simplified_prompt
        
        self.save_history(history)
        logger.info(f"已简化第{chapter_num}章{stage}阶段的用户提示词: "
                   f"{len(original_content)} -> {len(simplified_prompt)} 字符")
        return True
    
    def update_chapter_content(self, chapter_num: int, new_content: str) -> bool:
        """
        更新历史记录中指定章节的内容
        
        Args:
            chapter_num: 章节号
            new_content: 新的章节内容
            
        Returns:
            bool: 是否成功更新
        """
        history = self.load_history()
        if not history:
            logger.warning(f"历史记录为空，无法更新第{chapter_num}章内容")
            return False
        
        # 查找该章节的assistant消息（写作阶段）
        updated_count = 0
        for i, msg in enumerate(history):
            if (msg.get("role") == "assistant" and
                msg.get("chapter") == chapter_num and
                msg.get("stage") == "write"):
                
                # 更新内容
                original_content = msg["content"]
                msg["content"] = new_content
                updated_count += 1
                
                logger.info(f"更新第{chapter_num}章历史记录内容: 位置 {i}")
        
        if updated_count > 0:
            # 保存更新后的历史记录
            self.save_history(history)
            logger.info(f"成功更新第{chapter_num}章历史记录: {updated_count} 条消息")
            return True
        else:
            logger.warning(f"未找到第{chapter_num}章写作阶段的assistant消息")
            return False
    
    def get_chapter_content(self, chapter_num: int) -> Optional[str]:
        """
        从历史记录中获取指定章节的内容
        
        Args:
            chapter_num: 章节号
            
        Returns:
            Optional[str]: 章节内容，如果未找到则返回None
        """
        history = self.load_history()
        if not history:
            return None
        
        # 查找该章节的assistant消息（写作阶段）
        for i in range(len(history) - 1, -1, -1):
            msg = history[i]
            if (msg.get("role") == "assistant" and
                msg.get("chapter") == chapter_num and
                msg.get("stage") == "write"):
                return msg["content"]
        
        return None
    
    def remove_write_messages(self, chapter_num: int) -> int:
        """
        从历史记录中删除指定章节的写作阶段消息
        
        Args:
            chapter_num: 章节号
            
        Returns:
            int: 删除的消息数量
        """
        history = self.load_history()
        if not history:
            return 0
        
        # 查找要删除的消息索引
        indices_to_remove = []
        for i in range(len(history) - 1, -1, -1):
            msg = history[i]
            if (msg.get("chapter") == chapter_num and
                msg.get("stage") == "write"):
                indices_to_remove.append(i)
        
        # 删除消息（从后往前删除，避免索引变化）
        indices_to_remove.sort(reverse=True)
        removed_count = 0
        for idx in indices_to_remove:
            if 0 <= idx < len(history):
                removed_msg = history.pop(idx)
                logger.debug(f"删除历史记录消息: 第{chapter_num}章 "
                           f"{removed_msg.get('role')} {removed_msg.get('stage')}")
                removed_count += 1
        
        if removed_count > 0:
            self.save_history(history)
            logger.info(f"已删除第{chapter_num}章的写作阶段消息: {removed_count} 条")
        
        return removed_count
    
    def get_history_summary(self) -> Dict[str, Any]:
        """
        获取历史记录摘要信息
        
        Returns:
            Dict[str, Any]: 摘要信息字典
        """
        history = self.load_history()
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
        base_context_length = self.infer_base_context_length(history)
        
        return {
            "total_messages": len(history),
            "base_context_length": base_context_length,
            "role_counts": role_counts,
            "chapters": sorted(chapter_counts.keys()),
            "chapter_counts": chapter_counts,
            "stage_counts": stage_counts,
        }