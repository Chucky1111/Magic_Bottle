"""
读者状态管理器 - 负责维护读者模块的状态
实现状态持久化和断点续传功能
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ReaderStateManager:
    """读者状态管理器，负责维护读者模块的状态"""
    
    def __init__(self, state_file_path: str = "data/reader_state.json"):
        """
        初始化读者状态管理器
        
        Args:
            state_file_path: 状态文件路径
        """
        self.state_file_path = Path(state_file_path)
        self.state: Dict[str, Any] = {}
        self.load_state()
    
    def load_state(self) -> None:
        """从JSON文件加载状态"""
        try:
            if self.state_file_path.exists():
                with open(self.state_file_path, 'r', encoding='utf-8') as f:
                    self.state = json.load(f)
                logger.info(f"读者状态已从 {self.state_file_path} 加载")
                
                # 向后兼容：如果缺少新字段，初始化它们
                if "last_processed_chapter" not in self.state:
                    self.state["last_processed_chapter"] = 0
                if "reader_memory" not in self.state:
                    self.state["reader_memory"] = ""
                if "stage" not in self.state:
                    self.state["stage"] = "memerry"  # memerry | feedback
                if "window_chapters" not in self.state:
                    self.state["window_chapters"] = []
                if "window_size" not in self.state:
                    self.state["window_size"] = 3
                if "base_context_length" not in self.state:
                    self.state["base_context_length"] = 1
            else:
                # 初始化默认状态
                self.state = {
                    "last_processed_chapter": 0,  # 最后处理的章节号
                    "reader_memory": "",  # 读者记忆内容
                    "stage": "memerry",  # 当前阶段: memerry | feedback
                    "window_chapters": [],  # 当前窗口中的章节号列表
                    "window_size": 3,  # 窗口大小，固定为3
                    "base_context_length": 1,  # 基准上下文长度
                    "reader_history_file": "data/reader_history.json",  # 读者历史记录文件
                }
                self.save_state()
                logger.info(f"创建新的读者状态文件: {self.state_file_path}")
        except Exception as e:
            logger.error(f"加载读者状态失败: {e}")
            # 使用默认状态
            self.state = {
                "last_processed_chapter": 0,
                "reader_memory": "",
                "stage": "memerry",
                "window_chapters": [],
                "window_size": 3,
                "base_context_length": 1,
                "reader_history_file": "data/reader_history.json",
            }
    
    def save_state(self) -> None:
        """保存状态到JSON文件"""
        try:
            self.state_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
            logger.debug(f"读者状态已保存到 {self.state_file_path}")
        except Exception as e:
            logger.error(f"保存读者状态失败: {e}")
            raise
    
    def get_last_processed_chapter(self) -> int:
        """获取最后处理的章节号"""
        return self.state.get("last_processed_chapter", 0)
    
    def set_last_processed_chapter(self, chapter_num: int) -> None:
        """设置最后处理的章节号"""
        self.state["last_processed_chapter"] = chapter_num
        self.save_state()
    
    def get_reader_memory(self) -> str:
        """获取读者记忆内容"""
        return self.state.get("reader_memory", "")
    
    def set_reader_memory(self, memory: str) -> None:
        """设置读者记忆内容"""
        self.state["reader_memory"] = memory
        self.save_state()
    
    def get_stage(self) -> str:
        """获取当前阶段 (memerry | feedback)"""
        return self.state.get("stage", "memerry")
    
    def set_stage(self, stage: str) -> None:
        """设置当前阶段"""
        valid_stages = ["memerry", "feedback"]
        if stage not in valid_stages:
            raise ValueError(f"无效的阶段: {stage}，有效值为: {valid_stages}")
        self.state["stage"] = stage
        self.save_state()
    
    def get_window_chapters(self) -> List[int]:
        """获取当前窗口中的章节号列表"""
        return self.state.get("window_chapters", [])
    
    def set_window_chapters(self, chapters: List[int]) -> None:
        """设置窗口章节列表"""
        self.state["window_chapters"] = chapters
        self.save_state()
    
    def add_to_window(self, chapter_num: int) -> None:
        """添加章节到窗口"""
        window = self.get_window_chapters()
        if chapter_num not in window:
            window.append(chapter_num)
            # 保持窗口大小不超过window_size
            window_size = self.state.get("window_size", 3)
            if len(window) > window_size:
                window = window[-window_size:]
            self.set_window_chapters(window)
            logger.debug(f"读者窗口添加章节 {chapter_num}: {window}")
    
    def get_window_size(self) -> int:
        """获取窗口大小"""
        return self.state.get("window_size", 3)
    
    def is_window_full(self) -> bool:
        """检查窗口是否已满"""
        return len(self.get_window_chapters()) >= self.get_window_size()
    
    def clear_window(self) -> None:
        """清空窗口章节"""
        self.state["window_chapters"] = []
        self.save_state()
        logger.debug("读者窗口已清空")
    
    def get_base_context_length(self) -> int:
        """获取基准上下文长度"""
        return self.state.get("base_context_length", 1)
    
    def set_base_context_length(self, length: int) -> None:
        """设置基准上下文长度"""
        if length < 1:
            length = 1  # 至少包含系统消息
        self.state["base_context_length"] = length
        self.save_state()
        logger.debug(f"读者基准上下文长度已设置为: {length}")
    
    def get_reader_history_file(self) -> str:
        """获取读者历史记录文件路径"""
        return self.state.get("reader_history_file", "data/reader_history.json")
    
    def advance_stage(self) -> None:
        """状态流转逻辑"""
        current_stage = self.get_stage()
        
        if current_stage == "memerry":
            self.set_stage("feedback")
        elif current_stage == "feedback":
            # 反馈完成后，重置为记忆阶段
            self.set_stage("memerry")
    
    def get_state_summary(self) -> str:
        """获取状态摘要"""
        return (
            f"最后处理章节: {self.get_last_processed_chapter()}, "
            f"阶段: {self.get_stage()}, "
            f"窗口章节: {self.get_window_chapters()}, "
            f"窗口大小: {len(self.get_window_chapters())}/{self.get_window_size()}, "
            f"记忆长度: {len(self.get_reader_memory())} 字符"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """将状态转换为字典"""
        return self.state.copy()
    
    def from_dict(self, state_dict: Dict[str, Any]) -> None:
        """从字典加载状态"""
        self.state = state_dict
        self.save_state()