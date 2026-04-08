"""
状态管理器 - 负责维护"唯一真理源"
实现状态持久化和断点续传功能

新架构：支持滑动窗口章节管理
扩展：支持序列注入系统状态管理（简化版）
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from utils.file_lock import AtomicFileWriter, file_lock_context

logger = logging.getLogger(__name__)


class StateManager:
    """状态管理器，负责维护小说写作的状态"""
    
    def __init__(self, state_file_path: str = "data/state.json"):
        """
        初始化状态管理器
        
        Args:
            state_file_path: 状态文件路径
        """
        self.state_file_path = Path(state_file_path)
        self.state: Dict[str, Any] = {}
        self.atomic_writer = AtomicFileWriter(str(self.state_file_path))
        self.load_state()
    
    def load_state(self) -> None:
        """从JSON文件加载状态（使用文件锁保护）"""
        try:
            if self.state_file_path.exists():
                # 使用文件锁上下文读取文件
                with file_lock_context(str(self.state_file_path.with_suffix('.lock'))):
                    with open(self.state_file_path, 'r', encoding='utf-8') as f:
                        self.state = json.load(f)
                
                logger.info(f"状态已从 {self.state_file_path} 加载")
                
                # 向后兼容：如果缺少新字段，初始化它们
                if "window_chapters" not in self.state:
                    self.state["window_chapters"] = []
                if "stage" not in self.state:
                    self.state["stage"] = "design"
                if "base_context_length" not in self.state:
                    # 尝试从历史记录推断或使用默认值
                    self.state["base_context_length"] = 1  # 至少包含系统消息
                # 系统信息相关字段的向后兼容
                if "last_system_info_chapter" not in self.state:
                    self.state["last_system_info_chapter"] = 0
                if "next_system_info_interval" not in self.state:
                    self.state["next_system_info_interval"] = 0
                if "system_info_scheduled_chapters" not in self.state:
                    self.state["system_info_scheduled_chapters"] = []
                if "system_info_cycle_start" not in self.state:
                    self.state["system_info_cycle_start"] = 1
                if "system_info_cycle_length" not in self.state:
                    self.state["system_info_cycle_length"] = 15
                
                # 序列状态字段的向后兼容（简化版）
                if "sequence_state" not in self.state:
                    self.state["sequence_state"] = {
                        "design_index": 0,
                        "write_index": 0
                    }
                
                # 反馈上下文状态字段的向后兼容
                if "feedback_context" not in self.state:
                    self.state["feedback_context"] = {
                        "last_used_feedback_chapter": 0,
                        "last_used_feedback_index": 0,
                        "feedback_cycle_start": 1,
                        "feedback_cycle_length": 10  # 每10章更新一次反馈
                    }
                
                # 用户灵感注入状态字段的向后兼容
                if "user_idea_injections" not in self.state:
                    self.state["user_idea_injections"] = {}
                if "current_user_idea" not in self.state:
                    self.state["current_user_idea"] = {}
                
                # 总结状态计数器字段的向后兼容
                if "summary_status_counter" not in self.state:
                    self.state["summary_status_counter"] = 0
            else:
                # 初始化默认状态
                self.state = {
                    "chapter_num": 1,
                    "stage": "design",  # design | write | summary
                    "window_chapters": [],  # 当前窗口中的章节号列表，例如 [5, 6, 7]
                    "window_size": 3,  # 窗口大小，固定为3
                    "base_context_length": 1,  # 基准上下文长度（至少包含系统消息）
                    "last_system_info_chapter": 0,  # 上一次插入系统信息的章节号
                    "next_system_info_interval": 0,  # 下一次插入的间隔章节数（0表示未设置，保留用于向后兼容）
                    "system_info_scheduled_chapters": [],  # 计划插入系统信息的章节列表
                    "system_info_cycle_start": 1,  # 当前周期起始章节
                    "system_info_cycle_length": 15,  # 周期长度（15章）
                    # 序列状态（简化版）
                    "sequence_state": {
                        "design_index": 0,
                        "write_index": 0
                    },
                    # 反馈上下文状态
                    "feedback_context": {
                        "last_used_feedback_chapter": 0,
                        "last_used_feedback_index": 0,
                        "feedback_cycle_start": 1,
                        "feedback_cycle_length": 10  # 每10章更新一次反馈
                    },
                    # 用户灵感注入状态
                    "user_idea_injections": {},  # 格式: {"filename.txt": [0, 1, 2]} 记录已注入条目索引
                    "current_user_idea": {},     # 格式: {"file_name": "xxx", "entry_index": 0, "chapter_num": 1}
                    
                    # 总结状态计数器
                    "summary_status_counter": 0
                }
                self.save_state()
                logger.info(f"创建新的状态文件: {self.state_file_path}")
        except Exception as e:
            logger.error(f"加载状态失败: {e}")
            # 使用默认状态
            self.state = {
                "chapter_num": 1,
                "stage": "design",
                "window_chapters": [],
                "window_size": 3,
                "base_context_length": 1,
                "last_system_info_chapter": 0,
                "next_system_info_interval": 0,
                "system_info_scheduled_chapters": [],
                "system_info_cycle_start": 1,
                "system_info_cycle_length": 15,
                "sequence_state": {
                    "design_index": 0,
                    "write_index": 0
                },
                "feedback_context": {
                    "last_used_feedback_chapter": 0,
                    "last_used_feedback_index": 0,
                    "feedback_cycle_start": 1,
                    "feedback_cycle_length": 10
                },
                "user_idea_injections": {},
                "current_user_idea": {},
                "summary_status_counter": 0
            }
    
    def save_state(self) -> None:
        """保存状态到JSON文件（使用原子写入）"""
        try:
            # 确保目录存在
            self.state_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 使用原子文件写入器
            self.atomic_writer.write_json(self.state, indent=2, ensure_ascii=False)
            logger.debug(f"状态已原子保存到 {self.state_file_path}")
            
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
            raise
    
    def get_chapter_num(self) -> int:
        """获取当前章节号"""
        return self.state.get("chapter_num", 1)
    
    def set_chapter_num(self, chapter_num: int) -> None:
        """设置当前章节号"""
        self.state["chapter_num"] = chapter_num
        self.save_state()
    
    def get_stage(self) -> str:
        """获取当前阶段 (design | write | summary)"""
        return self.state.get("stage", "design")
    
    def set_stage(self, stage: str) -> None:
        """设置当前阶段"""
        valid_stages = ["design", "write", "summary"]
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
            logger.debug(f"章节 {chapter_num} 已添加到窗口: {window}")
    
    def get_window_size(self) -> int:
        """获取窗口大小"""
        return self.state.get("window_size", 3)
    
    def is_window_full(self) -> bool:
        """检查窗口是否已满"""
        return len(self.get_window_chapters()) >= self.get_window_size()
    
    def advance_stage(self) -> None:
        """状态流转逻辑（简化版，具体逻辑在workflow中实现）"""
        current_stage = self.get_stage()
        
        if current_stage == "design":
            self.set_stage("write")
        elif current_stage == "write":
            # 检查窗口是否已满
            if self.is_window_full():
                self.set_stage("summary")
            else:
                # 章节号+1，切换回design
                self.set_chapter_num(self.get_chapter_num() + 1)
                self.set_stage("design")
        elif current_stage == "summary":
            # summary阶段后，workflow会处理修剪逻辑
            # 这里只重置阶段
            self.set_stage("design")
    
    def get_base_context_length(self) -> int:
        """获取基准上下文长度"""
        return self.state.get("base_context_length", 1)
    
    def set_base_context_length(self, length: int) -> None:
        """设置基准上下文长度"""
        if length < 1:
            length = 1  # 至少包含系统消息
        self.state["base_context_length"] = length
        self.save_state()
        logger.debug(f"基准上下文长度已设置为: {length}")
    
    def get_last_system_info_chapter(self) -> int:
        """获取上一次插入系统信息的章节号"""
        return self.state.get("last_system_info_chapter", 0)
    
    def set_last_system_info_chapter(self, chapter_num: int) -> None:
        """设置上一次插入系统信息的章节号"""
        self.state["last_system_info_chapter"] = chapter_num
        self.save_state()
    
    def get_next_system_info_interval(self) -> int:
        """获取下一次插入系统信息的间隔章节数"""
        return self.state.get("next_system_info_interval", 0)
    
    def set_next_system_info_interval(self, interval: int) -> None:
        """设置下一次插入系统信息的间隔章节数"""
        self.state["next_system_info_interval"] = interval
        self.save_state()
    
    def get_system_info_scheduled_chapters(self) -> List[int]:
        """获取计划插入系统信息的章节列表"""
        return self.state.get("system_info_scheduled_chapters", [])
    
    def set_system_info_scheduled_chapters(self, chapters: List[int]) -> None:
        """设置计划插入系统信息的章节列表"""
        self.state["system_info_scheduled_chapters"] = chapters
        self.save_state()
    
    def get_system_info_cycle_start(self) -> int:
        """获取当前周期起始章节"""
        return self.state.get("system_info_cycle_start", 1)
    
    def set_system_info_cycle_start(self, start_chapter: int) -> None:
        """设置当前周期起始章节"""
        self.state["system_info_cycle_start"] = start_chapter
        self.save_state()
    
    def get_system_info_cycle_length(self) -> int:
        """获取周期长度"""
        return self.state.get("system_info_cycle_length", 15)
    
    def set_system_info_cycle_length(self, length: int) -> None:
        """设置周期长度"""
        self.state["system_info_cycle_length"] = length
        self.save_state()
    
    def update_system_info_insertion(self, current_chapter: int) -> None:
        """
        更新系统信息插入状态
        
        Args:
            current_chapter: 当前已插入系统信息的章节号
        """
        self.set_last_system_info_chapter(current_chapter)
        logger.debug(f"系统信息插入状态已更新: 章节 {current_chapter}")
    
    def check_and_update_cycle(self, current_chapter: int) -> bool:
        """
        检查并更新周期
        
        Args:
            current_chapter: 当前章节号
            
        Returns:
            如果进入新周期则返回True
        """
        cycle_start = self.get_system_info_cycle_start()
        cycle_length = self.get_system_info_cycle_length()
        
        # 计算当前章节是否超出当前周期
        if current_chapter >= cycle_start + cycle_length:
            # 进入新周期
            new_cycle_start = cycle_start + cycle_length
            self.set_system_info_cycle_start(new_cycle_start)
            self.set_system_info_scheduled_chapters([])  # 清空计划，将在新周期重新生成
            logger.info(f"进入新系统信息周期: {new_cycle_start}-{new_cycle_start + cycle_length - 1}")
            return True
        
        return False
    
    # ========== 序列状态管理方法（简化版） ==========
    
    def get_design_module_index(self) -> int:
        """
        获取设计模块索引（简单顺序轮换）
        
        Returns:
            int: 设计模块索引
        """
        sequence_state = self.state.get("sequence_state", {})
        return sequence_state.get("design_index", 0)
    
    def get_write_module_index(self) -> int:
        """
        获取写作模块索引（简单顺序轮换）
        
        Returns:
            int: 写作模块索引
        """
        sequence_state = self.state.get("sequence_state", {})
        return sequence_state.get("write_index", 0)
    
    def set_design_module_index(self, index: int) -> None:
        """设置设计模块索引"""
        if "sequence_state" not in self.state:
            self.state["sequence_state"] = {}
        self.state["sequence_state"]["design_index"] = index
        self.save_state()
        logger.debug(f"设计模块索引已设置为: {index}")
    
    def set_write_module_index(self, index: int) -> None:
        """设置写作模块索引"""
        if "sequence_state" not in self.state:
            self.state["sequence_state"] = {}
        self.state["sequence_state"]["write_index"] = index
        self.save_state()
        logger.debug(f"写作模块索引已设置为: {index}")
    
    def advance_design_module_index(self, module_count: int = 2) -> int:
        """
        推进设计模块索引（简单顺序轮换）
        
        Args:
            module_count: 模块总数
            
        Returns:
            int: 新的设计模块索引
        """
        current_index = self.get_design_module_index()
        next_index = (current_index + 1) % module_count
        self.set_design_module_index(next_index)
        logger.debug(f"设计模块索引推进: {current_index} -> {next_index}")
        return next_index
    
    def advance_write_module_index(self, module_count: int = 2) -> int:
        """
        推进写作模块索引（简单顺序轮换）
        
        Args:
            module_count: 模块总数
            
        Returns:
            int: 新的写作模块索引
        """
        current_index = self.get_write_module_index()
        next_index = (current_index + 1) % module_count
        self.set_write_module_index(next_index)
        logger.debug(f"写作模块索引推进: {current_index} -> {next_index}")
        return next_index
    
    def get_sequence_state_summary(self) -> Dict[str, Any]:
        """
        获取序列状态摘要
        
        Returns:
            Dict[str, Any]: 序列状态摘要
        """
        sequence_state = self.state.get("sequence_state", {})
        
        return {
            "design_index": self.get_design_module_index(),
            "write_index": self.get_write_module_index(),
            "sequence_state_exists": "sequence_state" in self.state
        }
    
    # ========== 反馈上下文状态管理方法 ==========
    
    def get_feedback_context(self) -> Dict[str, Any]:
        """
        获取反馈上下文状态
        
        Returns:
            Dict[str, Any]: 反馈上下文状态
        """
        return self.state.get("feedback_context", {
            "last_used_feedback_chapter": 0,
            "last_used_feedback_index": 0,
            "feedback_cycle_start": 1,
            "feedback_cycle_length": 10
        })
    
    def set_feedback_context(self, feedback_context: Dict[str, Any]) -> None:
        """设置反馈上下文状态"""
        self.state["feedback_context"] = feedback_context
        self.save_state()
    
    def get_last_used_feedback_chapter(self) -> int:
        """获取最后一次使用的反馈来源章节"""
        feedback_context = self.get_feedback_context()
        return feedback_context.get("last_used_feedback_chapter", 0)
    
    def set_last_used_feedback_chapter(self, chapter_num: int) -> None:
        """设置最后一次使用的反馈来源章节"""
        feedback_context = self.get_feedback_context()
        feedback_context["last_used_feedback_chapter"] = chapter_num
        self.set_feedback_context(feedback_context)
        logger.debug(f"最后使用的反馈章节已设置为: {chapter_num}")
    
    def get_last_used_feedback_index(self) -> int:
        """获取最后一次使用的反馈索引"""
        feedback_context = self.get_feedback_context()
        return feedback_context.get("last_used_feedback_index", 0)
    
    def set_last_used_feedback_index(self, index: int) -> None:
        """设置最后一次使用的反馈索引"""
        feedback_context = self.get_feedback_context()
        feedback_context["last_used_feedback_index"] = index
        self.set_feedback_context(feedback_context)
        logger.debug(f"最后使用的反馈索引已设置为: {index}")
    
    def get_feedback_cycle_start(self) -> int:
        """获取反馈周期起始章节"""
        feedback_context = self.get_feedback_context()
        return feedback_context.get("feedback_cycle_start", 1)
    
    def set_feedback_cycle_start(self, start_chapter: int) -> None:
        """设置反馈周期起始章节"""
        feedback_context = self.get_feedback_context()
        feedback_context["feedback_cycle_start"] = start_chapter
        self.set_feedback_context(feedback_context)
        logger.debug(f"反馈周期起始章节已设置为: {start_chapter}")
    
    def get_feedback_cycle_length(self) -> int:
        """获取反馈周期长度"""
        feedback_context = self.get_feedback_context()
        return feedback_context.get("feedback_cycle_length", 10)
    
    def set_feedback_cycle_length(self, length: int) -> None:
        """设置反馈周期长度"""
        feedback_context = self.get_feedback_context()
        feedback_context["feedback_cycle_length"] = length
        self.set_feedback_context(feedback_context)
        logger.debug(f"反馈周期长度已设置为: {length}")
    
    def should_update_feedback_for_chapter(self, current_chapter: int) -> bool:
        """
        检查是否应该为当前章节更新反馈
        
        Args:
            current_chapter: 当前章节号
            
        Returns:
            bool: 如果应该更新反馈则返回True
        """
        # 获取当前阶段
        current_stage = self.get_stage()
        
        # 只在summary阶段（上下文剪枝时）更新反馈
        # 这意味着反馈会在整个窗口周期（3章）内保持不变
        # 直到执行剪枝时才更换
        if current_stage == "summary":
            logger.info(f"第{current_chapter}章处于summary阶段（上下文剪枝），应该更新反馈")
            return True
        else:
            # 在design/write阶段不更新反馈，使用上次的反馈
            logger.debug(f"第{current_chapter}章处于{current_stage}阶段，不更新反馈")
            return False
    
    def update_feedback_usage(self, feedback_chapter: int, feedback_index: int) -> None:
        """
        更新反馈使用状态
        
        Args:
            feedback_chapter: 反馈来源章节
            feedback_index: 反馈索引
        """
        self.set_last_used_feedback_chapter(feedback_chapter)
        self.set_last_used_feedback_index(feedback_index)
        logger.info(f"反馈使用状态已更新: 章节 {feedback_chapter}, 索引 {feedback_index}")
    
    # ========== 用户灵感注入状态管理方法 ==========
    
    def get_user_idea_injections(self) -> Dict[str, List[int]]:
        """获取用户灵感注入历史
        
        Returns:
            字典格式: {"filename.txt": [0, 1, 2]} 记录已注入条目索引
        """
        return self.state.get("user_idea_injections", {})
    
    def set_user_idea_injections(self, injections: Dict[str, List[int]]) -> None:
        """设置用户灵感注入历史"""
        self.state["user_idea_injections"] = injections
        self.save_state()
    
    def add_user_idea_injection(self, file_name: str, entry_index: int) -> None:
        """添加用户灵感注入记录"""
        injections = self.get_user_idea_injections()
        if file_name not in injections:
            injections[file_name] = []
        
        if entry_index not in injections[file_name]:
            injections[file_name].append(entry_index)
            injections[file_name].sort()  # 保持排序
            self.set_user_idea_injections(injections)
            logger.debug(f"添加用户灵感注入记录: {file_name}[{entry_index}]")
    
    def get_current_user_idea(self, chapter_num: int = None) -> Dict[str, Any]:
        """获取当前章节正在使用的用户灵感
        
        Args:
            chapter_num: 章节号，如果为None则返回当前状态中的信息
            
        Returns:
            字典格式: {"file_name": "xxx", "entry_index": 0, "chapter_num": 1}
        """
        current_idea = self.state.get("current_user_idea", {})
        if chapter_num is not None:
            # 如果指定了章节号，检查是否匹配当前章节
            if current_idea.get("chapter_num") == chapter_num:
                return current_idea
            return {}
        return current_idea
    
    def set_current_user_idea(self, file_name: str, entry_index: int, chapter_num: int) -> None:
        """设置当前章节正在使用的用户灵感"""
        current_idea = {
            "file_name": file_name,
            "entry_index": entry_index,
            "chapter_num": chapter_num
        }
        self.state["current_user_idea"] = current_idea
        self.save_state()
        logger.info(f"设置当前用户灵感: 第{chapter_num}章使用 {file_name}[{entry_index}]")
    
    def clear_current_user_idea(self) -> None:
        """清除当前用户灵感记录（通常在章节完成后调用）"""
        if "current_user_idea" in self.state:
            del self.state["current_user_idea"]
            self.save_state()
            logger.debug("已清除当前用户灵感记录")
    
    # ========== 总结状态管理方法 ==========
    
    def get_next_summary_status(self) -> int:
        """获取下一个总结状态编号"""
        current = self.state.get("summary_status_counter", 0)
        next_status = current + 1
        self.state["summary_status_counter"] = next_status
        self.save_state()
        logger.debug(f"总结状态编号已递增: {current} -> {next_status}")
        return next_status
    
    def get_current_summary_status(self) -> int:
        """获取当前总结状态编号"""
        return self.state.get("summary_status_counter", 0)
    
    def get_state_summary(self) -> str:
        """获取状态摘要"""
        scheduled_chapters = self.get_system_info_scheduled_chapters()
        cycle_start = self.get_system_info_cycle_start()
        cycle_length = self.get_system_info_cycle_length()
        
        # 序列状态摘要
        sequence_summary = self.get_sequence_state_summary()
        
        # 反馈上下文状态摘要
        feedback_cycle_start = self.get_feedback_cycle_start()
        feedback_cycle_length = self.get_feedback_cycle_length()
        
        # 用户灵感注入状态摘要
        user_idea_injections = self.get_user_idea_injections()
        current_user_idea = self.get_current_user_idea()
        
        injection_summary = "无"
        if user_idea_injections:
            total_injected = sum(len(indices) for indices in user_idea_injections.values())
            injection_summary = f"{total_injected}个条目({len(user_idea_injections)}个文件)"
        
        current_idea_summary = "无"
        if current_user_idea:
            current_idea_summary = f"{current_user_idea.get('file_name', '未知')}[{current_user_idea.get('entry_index', 0)}]"
        
        return (
            f"章节: {self.get_chapter_num()}, "
            f"阶段: {self.get_stage()}, "
            f"窗口章节: {self.get_window_chapters()}, "
            f"窗口大小: {len(self.get_window_chapters())}/{self.get_window_size()}, "
            f"基准上下文长度: {self.get_base_context_length()}, "
            f"上次系统信息章节: {self.get_last_system_info_chapter()}, "
            f"计划插入章节: {scheduled_chapters if scheduled_chapters else '未设置'}, "
            f"系统信息周期: {cycle_start}-{cycle_start + cycle_length - 1}, "
            f"设计序列索引: {sequence_summary['design_index']}, "
            f"写作序列索引: {sequence_summary['write_index']}, "
            f"最后反馈章节: {self.get_last_used_feedback_chapter()}, "
            f"最后反馈索引: {self.get_last_used_feedback_index()}, "
            f"反馈周期: {feedback_cycle_start}-{feedback_cycle_start + feedback_cycle_length - 1}, "
            f"用户灵感注入: {injection_summary}, "
            f"当前用户灵感: {current_idea_summary}, "
            f"总结状态计数器: {self.get_current_summary_status()}"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """将状态转换为字典"""
        return self.state.copy()
    
    def from_dict(self, state_dict: Dict[str, Any]) -> None:
        """从字典加载状态"""
        self.state = state_dict
        self.save_state()