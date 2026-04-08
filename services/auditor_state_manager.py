"""
Auditor状态管理器
负责管理审计模块的状态持久化和恢复
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


from dataclasses import dataclass, asdict, field
from typing import List

@dataclass
class AuditorState:
    """Auditor状态数据类"""
    last_audited_chapter: int = 0  # 最后审计的章节号
    current_stage: str = "idle"    # 当前阶段: idle, auditing, rewriting, confirming, version_selecting
    rewrite_round: int = 0         # 重写轮次 (1, 2, 3)
    current_chapter: int = 0       # 当前正在处理的章节号
    audit_result: str = ""         # 审计结果: "通过" 或 "重写"
    audit_issues: str = ""         # 审计发现的问题
    rewrite_instructions: str = "" # 重写指导
    rewritten_content: str = ""    # 重写后的内容
    needs_rewrite: bool = False    # 是否需要重写
    rewrite_completed: bool = False # 重写是否完成
    auditor_history_file: str = "data/auditor_history.json"  # Auditor历史记录文件
    auditor_memory: str = ""       # Auditor记忆内容
    version_history: List[str] = field(default_factory=list)  # 版本历史列表
    max_versions: int = 3          # 最大版本数
    selected_version: int = 0      # 选择的版本号 (1-3)，0表示未选择
    window_chapters: List[int] = field(default_factory=list)  # 窗口章节列表
    window_size: int = 3           # 窗口大小，固定为3
    should_run_memory: bool = False # 是否应该运行记忆阶段（第3章才运行）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditorState':
        """从字典创建实例"""
        return cls(**data)


class AuditorStateManager:
    """Auditor状态管理器"""
    
    def __init__(self, state_file: str = "data/auditor_state.json"):
        """
        初始化状态管理器
        
        Args:
            state_file: 状态文件路径
        """
        self.state_file = Path(state_file)
        self.state = AuditorState()
        
        # 确保目录存在
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载现有状态
        self._load_state()
        
        logger.info("AuditorStateManager初始化完成")
    
    def _load_state(self) -> None:
        """加载状态"""
        if not self.state_file.exists():
            logger.info("未找到auditor状态文件，使用默认状态")
            return
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.state = AuditorState.from_dict(data)
            logger.info(f"auditor状态已加载: {self.state}")
        except Exception as e:
            logger.error(f"加载auditor状态失败: {e}")
            # 使用默认状态
            self.state = AuditorState()
    
    def _save_state(self) -> None:
        """保存状态"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state.to_dict(), f, ensure_ascii=False, indent=2)
            logger.debug("auditor状态已保存")
        except Exception as e:
            logger.error(f"保存auditor状态失败: {e}")
    
    def update_state(self, **kwargs) -> None:
        """
        更新状态
        
        Args:
            **kwargs: 要更新的状态字段
        """
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
            else:
                logger.warning(f"尝试更新不存在的状态字段: {key}")
        
        # 自动保存
        self._save_state()
    
    def reset_for_new_chapter(self, chapter_num: int) -> None:
        """
        为新章节重置状态
        
        Args:
            chapter_num: 章节号
        """
        self.state = AuditorState(
            last_audited_chapter=chapter_num,
            current_stage="auditing",
            rewrite_round=0,
            current_chapter=chapter_num,
            audit_result="",
            audit_issues="",
            rewrite_instructions="",
            rewritten_content="",
            needs_rewrite=False,
            rewrite_completed=False
        )
        self._save_state()
        logger.info(f"auditor状态已重置为第{chapter_num}章审计")
    
    def start_rewrite(self, issues: str) -> None:
        """
        开始重写流程
        
        Args:
            issues: 审计发现的问题
        """
        self.state.current_stage = "rewriting"
        self.state.rewrite_round = 1
        self.state.audit_issues = issues
        self.state.needs_rewrite = True
        self._save_state()
        logger.info(f"开始重写流程，第{self.state.rewrite_round}轮")
    
    def advance_rewrite_round(self) -> None:
        """推进重写轮次"""
        if self.state.rewrite_round < 3:
            self.state.rewrite_round += 1
            self._save_state()
            logger.info(f"重写轮次推进到第{self.state.rewrite_round}轮")
        else:
            logger.warning("重写轮次已达到最大值3")
    
    def complete_rewrite(self, rewritten_content: str) -> None:
        """
        完成重写
        
        Args:
            rewritten_content: 重写后的内容
        """
        self.state.rewritten_content = rewritten_content
        self.state.current_stage = "confirming"
        self._save_state()
        logger.info("重写完成，进入确认阶段")
    
    def finalize_audit(self, passed: bool) -> None:
        """
        完成审计
        
        Args:
            passed: 是否通过
        """
        if passed:
            self.state.current_stage = "idle"
            self.state.rewrite_completed = True
            logger.info(f"第{self.state.current_chapter}章审计通过")
        else:
            # 如果未通过，重置重写状态
            self.state.current_stage = "rewriting"
            self.state.rewrite_round = 1
            logger.info(f"第{self.state.current_chapter}章需要继续重写")
        
        self._save_state()
    
    def get_state_summary(self) -> Dict[str, Any]:
        """获取状态摘要"""
        return {
            "last_audited_chapter": self.state.last_audited_chapter,
            "current_stage": self.state.current_stage,
            "rewrite_round": self.state.rewrite_round,
            "current_chapter": self.state.current_chapter,
            "needs_rewrite": self.state.needs_rewrite,
            "rewrite_completed": self.state.rewrite_completed,
            "audit_result": self.state.audit_result,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（兼容性）"""
        return self.state.to_dict()
    
    def should_audit_chapter(self, chapter_num: int) -> bool:
        """
        检查是否应该审计指定章节
        
        Args:
            chapter_num: 章节号
            
        Returns:
            如果应该审计则返回True
        """
        # 如果章节号大于最后审计的章节，且当前没有在处理其他章节
        if chapter_num > self.state.last_audited_chapter and self.state.current_stage == "idle":
            return True
        
        # 如果正在处理该章节，继续处理
        if chapter_num == self.state.current_chapter and self.state.current_stage != "idle":
            return True
        
        return False
    
    def get_auditor_history_file(self) -> str:
        """获取Auditor历史记录文件路径"""
        return self.state.auditor_history_file
    
    def add_to_auditor_history(self, role: str, content: str, chapter_num: int, stage: str) -> None:
        """
        添加消息到Auditor历史记录
        
        Args:
            role: 角色 (user, assistant, system)
            content: 消息内容
            chapter_num: 章节号
            stage: 阶段 (audit, rewrite, confirm)
        """
        import json
        import time
        from pathlib import Path
        
        history_path = Path(self.get_auditor_history_file())
        
        # 加载现有历史记录
        history = []
        if history_path.exists():
            try:
                with open(history_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except Exception as e:
                logger.error(f"加载Auditor历史记录失败: {e}")
        
        # 添加新消息
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "chapter": chapter_num,
            "stage": stage,
            "is_base_context": False
        }
        
        history.append(message)
        
        # 保存历史记录
        try:
            history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"Auditor历史记录已添加: {role} - 第{chapter_num}章 - {stage}")
            
        except Exception as e:
            logger.error(f"保存Auditor历史记录失败: {e}")
    
    def get_auditor_history_length(self) -> int:
        """获取Auditor历史记录长度"""
        import json
        from pathlib import Path
        
        history_path = Path(self.get_auditor_history_file())
        if not history_path.exists():
            return 0
        
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
            return len(history)
        except Exception as e:
            logger.error(f"获取Auditor历史记录长度失败: {e}")
            return 0
    
    def get_auditor_memory(self) -> str:
        """获取Auditor记忆内容"""
        return self.state.auditor_memory
    
    def set_auditor_memory(self, memory: str) -> None:
        """设置Auditor记忆内容"""
        self.state.auditor_memory = memory
        self._save_state()
        logger.debug(f"Auditor记忆已更新，长度: {len(memory)} 字符")
    
    def add_version(self, version_content: str) -> None:
        """
        添加版本到版本历史
        
        Args:
            version_content: 版本内容
        """
        # 添加到版本历史
        self.state.version_history.append(version_content)
        
        # 保持版本数量不超过最大值
        if len(self.state.version_history) > self.state.max_versions:
            # 删除最旧的版本
            self.state.version_history = self.state.version_history[-self.state.max_versions:]
        
        self._save_state()
        logger.info(f"版本已添加，当前版本数: {len(self.state.version_history)}/{self.state.max_versions}")
    
    def get_versions(self) -> List[str]:
        """获取版本历史"""
        return self.state.version_history.copy()
    
    def get_version_count(self) -> int:
        """获取版本数量"""
        return len(self.state.version_history)
    
    def has_enough_versions(self) -> bool:
        """检查是否有足够版本进行选择（至少2个）"""
        return len(self.state.version_history) >= 2
    
    def select_version(self, version_num: int) -> None:
        """
        选择版本
        
        Args:
            version_num: 版本号 (1-3)
        """
        if 1 <= version_num <= len(self.state.version_history):
            self.state.selected_version = version_num
            self._save_state()
            logger.info(f"已选择版本 {version_num}")
        else:
            logger.warning(f"无效的版本号: {version_num}，版本历史长度: {len(self.state.version_history)}")
    
    def get_selected_version_content(self) -> str:
        """获取选择的版本内容"""
        if 1 <= self.state.selected_version <= len(self.state.version_history):
            return self.state.version_history[self.state.selected_version - 1]
        return ""
    
    def get_default_version_num(self) -> int:
        """获取默认版本号（最近的第三个版本或最新版本）"""
        if len(self.state.version_history) == 0:
            return 0
        
        # 如果有3个或更多版本，默认选择第3个（最新）
        if len(self.state.version_history) >= 3:
            return 3
        # 否则选择最新版本
        return len(self.state.version_history)
    
    def prune_auditor_history(self) -> None:
        """
        执行auditor历史记录剪枝，采用与reader系统相同的3-2-1逻辑
        
        当窗口满时（3章）执行剪枝：
        1. 删除窗口中前两章的所有记录，保留第三章
        2. 保留基准上下文（系统提示词 + 预热对话）
        3. 删除packet阶段的问答对（记忆整理对话）
        4. 保留最新的确认/版本选择消息（如果有）
        """
        logger.info("开始执行auditor历史记录剪枝（3-2-1逻辑）")
        
        history_path = Path(self.get_auditor_history_file())
        if not history_path.exists():
            logger.warning("auditor历史记录文件不存在，跳过剪枝")
            return
        
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                full_history = json.load(f)
        except Exception as e:
            logger.error(f"加载auditor历史记录失败: {e}")
            return
        
        # 获取所有章节号（排除章节0的系统消息）
        chapters = sorted(set(msg.get("chapter", 0) for msg in full_history if msg.get("chapter", 0) > 0))
        
        if len(chapters) < 3:
            logger.info(f"章节数不足3章 ({len(chapters)})，跳过剪枝")
            return
        
        # 确定窗口章节：最近3章
        # 例如：章节列表为 [1, 2, 3, 4, 5]，则窗口章节为 [3, 4, 5]
        # 但根据3-2-1逻辑，我们应该删除前两章(3,4)，保留第5章
        # 然而审计系统没有窗口管理，所以我们需要模拟窗口逻辑
        
        # 获取最近3章
        recent_chapters = chapters[-3:] if len(chapters) >= 3 else chapters
        if len(recent_chapters) != 3:
            logger.info(f"最近章节数不足3章 ({len(recent_chapters)})，跳过剪枝")
            return
        
        chapter_1, chapter_2, chapter_3 = recent_chapters  # 示例: [3, 4, 5]
        
        # 获取基准上下文长度（系统消息 + 预热对话）
        # 在auditor系统中，基准上下文是章节0的所有消息
        base_context_length = 0
        for i, msg in enumerate(full_history):
            if msg.get("chapter", 0) == 0 and msg.get("is_base_context", False):
                base_context_length = i + 1
            else:
                break
        
        if base_context_length <= 0:
            base_context_length = 1  # 至少包含系统消息
        
        logger.info(f"剪枝配置: 删除章节 {chapter_1}, {chapter_2}，保留章节 {chapter_3}，基准上下文长度: {base_context_length}")
        
        # 从历史记录中物理删除：
        # 1. 前两章的所有记录
        # 2. packet阶段的问答对（记忆整理对话）
        chapters_to_remove = [chapter_1, chapter_2]
        
        new_history = []
        for i, msg in enumerate(full_history):
            chapter = msg.get("chapter", 0)
            is_base = msg.get("is_base_context", False)
            stage = msg.get("stage", "")
            
            # 情况1：保留基准上下文（系统提示词 + 预热对话）
            if i < base_context_length:
                new_history.append(msg)
                logger.debug(f"保留auditor基准上下文消息 {i}: {msg.get('stage', 'base')}")
                continue
            
            # 情况2：保留第三章的所有记录（除了packet阶段）
            if chapter == chapter_3:
                # 检查是否为packet阶段，如果是则删除
                if stage == "packet":
                    logger.debug(f"删除auditor packet阶段消息 {i}: 第{chapter}章 {stage}")
                    continue  # 跳过，不添加
                new_history.append(msg)
                logger.debug(f"保留auditor第三章消息 {i}: 第{chapter}章 {stage}")
                continue
            
            # 情况3：删除前两章的所有记录
            if chapter in chapters_to_remove:
                logger.debug(f"删除auditor前两章消息 {i}: 第{chapter}章 {stage}")
                continue  # 跳过，不添加
            
            # 情况4：删除其他章节的packet阶段消息
            if stage == "packet":
                logger.debug(f"删除auditor packet阶段消息 {i}: 第{chapter}章 {stage}")
                continue  # 跳过，不添加
            
            # 情况5：其他消息（可能是旧的已修剪章节）也删除
            # 这样可以确保上下文干净
            logger.debug(f"删除auditor其他消息 {i}: 第{chapter}章 {stage}")
        
        # 保存修剪后的历史记录
        try:
            history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(new_history, f, ensure_ascii=False, indent=2)
            
            logger.info(f"auditor历史记录修剪完成: 删除了章节 {chapters_to_remove} 和所有packet阶段消息，保留章节 {chapter_3}")
            logger.info(f"auditor历史记录长度: {len(full_history)} -> {len(new_history)}")
            
        except Exception as e:
            logger.error(f"保存修剪后的auditor历史记录失败: {e}")
    
    def reset_state(self) -> None:
        """
        重置状态到初始值
        
        注意：这会清除所有状态，包括版本历史和记忆
        """
        self.state = AuditorState()
        self._save_state()
        logger.info("auditor状态已重置")
    
    def get_window_chapters(self) -> List[int]:
        """获取窗口章节列表"""
        return self.state.window_chapters.copy()
    
    def set_window_chapters(self, chapters: List[int]) -> None:
        """设置窗口章节列表"""
        self.state.window_chapters = chapters.copy()
        self._save_state()
        logger.debug(f"审计窗口章节已设置: {chapters}")
    
    def add_to_window(self, chapter_num: int) -> None:
        """添加章节到窗口"""
        window = self.get_window_chapters()
        if chapter_num not in window:
            window.append(chapter_num)
            # 保持窗口大小不超过window_size
            if len(window) > self.state.window_size:
                window = window[-self.state.window_size:]
            self.set_window_chapters(window)
            logger.debug(f"审计窗口添加章节 {chapter_num}: {window}")
    
    def get_window_size(self) -> int:
        """获取窗口大小"""
        return self.state.window_size
    
    def is_window_full(self) -> bool:
        """检查窗口是否已满"""
        return len(self.get_window_chapters()) >= self.get_window_size()
    
    def clear_window(self) -> None:
        """清空窗口章节"""
        self.state.window_chapters = []
        self._save_state()
        logger.debug("审计窗口已清空")
    
    def should_run_memory_phase(self) -> bool:
        """检查是否应该运行记忆阶段（第3章才运行）"""
        # 如果窗口已满（3章），则运行记忆阶段
        if self.is_window_full():
            # 检查是否是第3章（窗口中的最后一章）
            window_chapters = self.get_window_chapters()
            if len(window_chapters) == 3:
                # 第3章才运行记忆阶段
                self.state.should_run_memory = True
                return True
        
        self.state.should_run_memory = False
        return False
    
    def get_should_run_memory(self) -> bool:
        """获取是否应该运行记忆阶段"""
        return self.state.should_run_memory
    
    def set_should_run_memory(self, should_run: bool) -> None:
        """设置是否应该运行记忆阶段"""
        self.state.should_run_memory = should_run
        self._save_state()
    
    def get_auditor_history_summary(self) -> Dict[str, Any]:
        """获取Auditor历史记录摘要"""
        import json
        from pathlib import Path
        
        history_path = Path(self.get_auditor_history_file())
        if not history_path.exists():
            return {"total_messages": 0, "chapters": [], "stages": []}
        
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            # 统计信息
            chapters = sorted(set(msg.get("chapter", 0) for msg in history))
            stages = sorted(set(msg.get("stage", "") for msg in history if msg.get("stage")))
            
            return {
                "total_messages": len(history),
                "chapters": chapters,
                "stages": stages,
                "last_chapter": max(chapters) if chapters else 0,
                "last_stage": stages[-1] if stages else ""
            }
        except Exception as e:
            logger.error(f"获取Auditor历史记录摘要失败: {e}")
            return {"total_messages": 0, "chapters": [], "stages": []}