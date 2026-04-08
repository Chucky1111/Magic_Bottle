"""
用户灵感管理器 - 负责管理用户灵感文件的读取、注入和状态跟踪

核心功能：
1. 解析 `prompts/user_idea/` 目录下的灵感文件
2. 按 `---` 分隔符分割灵感条目
3. 跟踪已完成条目（标记为 `[已完成]`）
4. 在design和write阶段注入相同灵感内容
5. 自动标记已完成条目并重命名文件
6. 支持断点续传和状态持久化
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class IdeaStatus(Enum):
    """灵感条目状态"""
    PENDING = "pending"      # 未完成
    COMPLETED = "completed"  # 已完成


@dataclass
class IdeaEntry:
    """灵感条目"""
    content: str                   # 条目内容（不含状态标记）
    status: IdeaStatus             # 条目状态
    raw_content: str               # 原始内容（包含状态标记）
    index: int                     # 在文件中的索引位置


@dataclass
class IdeaFile:
    """灵感文件"""
    path: Path                     # 文件路径
    entries: List[IdeaEntry]       # 条目列表
    is_completed: bool = False     # 文件是否全部完成


class UserIdeaManager:
    """用户灵感管理器"""
    
    def __init__(self, state_manager=None, config=None):
        """
        初始化用户灵感管理器
        
        Args:
            state_manager: 状态管理器实例
            config: 配置对象
        """
        self.state_manager = state_manager
        self.config = config or {}
        self.idea_dir = Path(self.config.get("directory", "prompts/user_idea"))
        self.completed_prefix = self.config.get("completed_prefix", "completed_")
        self.max_retries = self.config.get("max_retries", 3)
        
        # 确保目录存在
        self.idea_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"用户灵感管理器初始化完成，目录: {self.idea_dir}")
    
    def get_available_files(self) -> List[Path]:
        """
        获取所有未完成的灵感文件
        
        Returns:
            未完成的灵感文件路径列表
        """
        if not self.idea_dir.exists():
            logger.warning(f"灵感目录不存在: {self.idea_dir}")
            return []
        
        available_files = []
        for file_path in self.idea_dir.glob("*.txt"):
            # 排除以 completed_ 开头的文件
            if not file_path.name.startswith(self.completed_prefix):
                available_files.append(file_path)
        
        logger.debug(f"找到 {len(available_files)} 个未完成灵感文件")
        return available_files
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((IOError, OSError))
    )
    def parse_idea_file(self, file_path: Path) -> IdeaFile:
        """
        解析灵感文件，返回结构化数据
        
        Args:
            file_path: 灵感文件路径
            
        Returns:
            IdeaFile 对象
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"读取灵感文件失败 {file_path}: {e}")
            raise
        
        # 按 --- 分割条目（支持多种分隔符格式）
        # 处理连续的换行和空白
        raw_sections = re.split(r'\n-{3,}\n', content.strip())
        
        entries = []
        for idx, section in enumerate(raw_sections):
            section = section.strip()
            if not section:
                continue
                
            # 检查是否已有 [已完成] 标记
            status = IdeaStatus.COMPLETED if section.startswith("[已完成]") else IdeaStatus.PENDING
            
            # 提取内容（去除状态标记和前后空白）
            if status == IdeaStatus.COMPLETED:
                # 移除 [已完成] 标记和后续可能的空格
                clean_content = re.sub(r'^\[已完成\]\s*', '', section, count=1).strip()
            else:
                clean_content = section.strip()
            
            entry = IdeaEntry(
                content=clean_content,
                status=status,
                raw_content=section,
                index=idx
            )
            entries.append(entry)
        
        # 检查文件是否全部完成
        is_completed = all(entry.status == IdeaStatus.COMPLETED for entry in entries)
        
        idea_file = IdeaFile(
            path=file_path,
            entries=entries,
            is_completed=is_completed
        )
        
        logger.debug(f"解析灵感文件 {file_path}: {len(entries)} 个条目，已完成: {is_completed}")
        return idea_file
    
    def get_next_idea(self, chapter_num: int, stage: str) -> Optional[Tuple[str, Path, int]]:
        """
        获取下一个未完成的灵感条目
        
        Args:
            chapter_num: 当前章节号
            stage: 当前阶段（design/write）
            
        Returns:
            (灵感内容, 文件路径, 条目索引) 或 None
        """
        available_files = self.get_available_files()
        if not available_files:
            logger.debug("没有可用的灵感文件")
            return None
        
        # 如果有状态管理器，获取注入历史，避免重复
        injected_history = {}
        if self.state_manager:
            injected_history = self.state_manager.get_user_idea_injections()
        
        for file_path in available_files:
            try:
                idea_file = self.parse_idea_file(file_path)
                if idea_file.is_completed:
                    continue
                
                for entry in idea_file.entries:
                    if entry.status == IdeaStatus.PENDING:
                        # 检查是否已经注入过（基于状态管理器记录）
                        file_key = str(file_path.relative_to(self.idea_dir))
                        if file_key in injected_history and entry.index in injected_history[file_key]:
                            logger.debug(f"条目已注入过: {file_key}[{entry.index}]，跳过")
                            continue
                        
                        logger.info(f"找到未完成灵感条目: {file_path.name}[{entry.index}]，内容长度: {len(entry.content)}")
                        return entry.content, file_path, entry.index
                        
            except Exception as e:
                logger.warning(f"处理灵感文件失败 {file_path}: {e}")
                continue
        
        logger.debug("所有灵感条目均已处理完成")
        return None
    
    def get_same_idea(self, chapter_num: int, stage: str) -> Optional[str]:
        """
        获取与design阶段相同的灵感内容（用于write阶段）
        
        基于状态管理器记录，获取当前章节正在使用的灵感条目
        
        Args:
            chapter_num: 当前章节号
            stage: 当前阶段（应为"write"）
            
        Returns:
            灵感内容或None
        """
        if not self.state_manager:
            logger.warning("没有状态管理器，无法获取相同的灵感内容")
            return None
        
        # 从状态管理器获取当前章节的灵感注入信息
        current_idea = self.state_manager.get_current_user_idea(chapter_num)
        if not current_idea:
            logger.debug(f"第{chapter_num}章没有正在使用的灵感")
            return None
        
        file_path = Path(self.idea_dir) / current_idea["file_name"]
        entry_index = current_idea["entry_index"]
        
        try:
            idea_file = self.parse_idea_file(file_path)
            if entry_index < len(idea_file.entries):
                entry = idea_file.entries[entry_index]
                return entry.content
        except Exception as e:
            logger.warning(f"获取相同灵感失败 {file_path}[{entry_index}]: {e}")
        
        return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((IOError, OSError))
    )
    def mark_idea_completed(self, file_path: Path, entry_index: int) -> bool:
        """
        标记灵感条目为已完成
        
        Args:
            file_path: 灵感文件路径
            entry_index: 条目索引
            
        Returns:
            是否成功标记
        """
        try:
            idea_file = self.parse_idea_file(file_path)
            if entry_index >= len(idea_file.entries):
                logger.error(f"条目索引超出范围: {file_path}[{entry_index}]，总条目数: {len(idea_file.entries)}")
                return False
            
            entry = idea_file.entries[entry_index]
            if entry.status == IdeaStatus.COMPLETED:
                logger.debug(f"条目已是已完成状态: {file_path}[{entry_index}]")
                return True
            
            # 更新条目状态
            idea_file.entries[entry_index].status = IdeaStatus.COMPLETED
            idea_file.entries[entry_index].raw_content = f"[已完成] {entry.content}"
            
            # 重新构建文件内容
            new_content = ""
            for i, entry in enumerate(idea_file.entries):
                if i > 0:
                    new_content += "\n---\n\n"
                new_content += entry.raw_content
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info(f"标记灵感条目为已完成: {file_path.name}[{entry_index}]")
            
            # 检查文件是否全部完成
            is_completed = all(e.status == IdeaStatus.COMPLETED for e in idea_file.entries)
            if is_completed:
                self._rename_completed_file(file_path)
            
            return True
            
        except Exception as e:
            logger.error(f"标记灵感条目失败 {file_path}[{entry_index}]: {e}")
            return False
    
    def _rename_completed_file(self, file_path: Path) -> bool:
        """
        重命名已全部完成的灵感文件（添加 completed_ 前缀）
        
        Args:
            file_path: 原始文件路径
            
        Returns:
            是否成功重命名
        """
        try:
            # 如果文件已经有 completed_ 前缀，直接返回 True（无需重命名）
            if file_path.name.startswith(self.completed_prefix):
                logger.debug(f"文件已有 {self.completed_prefix} 前缀: {file_path.name}，跳过重命名")
                return True
            
            new_name = f"{self.completed_prefix}{file_path.name}"
            new_path = file_path.parent / new_name
            
            # 检查新文件名是否已存在
            if new_path.exists():
                logger.warning(f"目标文件已存在: {new_path}，跳过重命名")
                return False
            
            file_path.rename(new_path)
            logger.info(f"重命名灵感文件: {file_path.name} -> {new_name}")
            return True
            
        except Exception as e:
            logger.error(f"重命名灵感文件失败 {file_path}: {e}")
            return False
    
    def check_and_rename_completed_files(self) -> List[Path]:
        """
        检查并重命名所有已完成的灵感文件
        
        Returns:
            已重命名的文件路径列表
        """
        renamed_files = []
        available_files = self.get_available_files()
        
        for file_path in available_files:
            try:
                idea_file = self.parse_idea_file(file_path)
                if idea_file.is_completed:
                    if self._rename_completed_file(file_path):
                        renamed_files.append(file_path)
            except Exception as e:
                logger.warning(f"检查文件完成状态失败 {file_path}: {e}")
                continue
        
        logger.info(f"检查完成，重命名了 {len(renamed_files)} 个文件")
        return renamed_files
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取灵感管理统计信息
        
        Returns:
            统计信息字典
        """
        available_files = self.get_available_files()
        completed_files = list(self.idea_dir.glob(f"{self.completed_prefix}*.txt"))
        
        total_entries = 0
        pending_entries = 0
        completed_entries = 0
        
        for file_path in available_files:
            try:
                idea_file = self.parse_idea_file(file_path)
                total_entries += len(idea_file.entries)
                pending_entries += sum(1 for e in idea_file.entries if e.status == IdeaStatus.PENDING)
                completed_entries += sum(1 for e in idea_file.entries if e.status == IdeaStatus.COMPLETED)
            except Exception as e:
                logger.warning(f"获取文件统计失败 {file_path}: {e}")
                continue
        
        return {
            "available_files": len(available_files),
            "completed_files": len(completed_files),
            "total_entries": total_entries,
            "pending_entries": pending_entries,
            "completed_entries": completed_entries,
            "completion_rate": completed_entries / total_entries if total_entries > 0 else 0.0
        }

    def get_collaborative_stats(self) -> Dict[str, Any]:
        """
        获取协同模式统计信息（用于自动规划章节数）
        
        Returns:
            协同模式统计信息字典
        """
        base_stats = self.get_stats()
        
        # 从配置获取协同模式参数
        collaborative_mode = self.config.get("collaborative_mode", False)
        auto_cc_enabled = self.config.get("auto_cc_enabled", True)
        min_chapters_per_idea = self.config.get("min_chapters_per_idea", 1)
        
        # 计算建议的章节数
        pending_entries = base_stats["pending_entries"]
        suggested_chapters = pending_entries * min_chapters_per_idea if pending_entries > 0 else 0
        
        return {
            **base_stats,
            "collaborative_mode_enabled": collaborative_mode,
            "auto_cc_enabled": auto_cc_enabled,
            "min_chapters_per_idea": min_chapters_per_idea,
            "suggested_chapters": suggested_chapters,
            "has_enough_ideas": pending_entries >= 1,
            "recommendation": {
                "should_use_collaborative_mode": collaborative_mode and auto_cc_enabled and pending_entries >= 1,
                "reason": f"发现 {pending_entries} 个待处理灵感，每个灵感分配 {min_chapters_per_idea} 章" if pending_entries >= 1 else "没有足够的待处理灵感",
                "suggested_cc": suggested_chapters
            }
        }

    def export_status_json(self, file_path: Path = None) -> Dict[str, Any]:
        """
        导出用户灵感状态到JSON格式，用于监控和调试
        
        Args:
            file_path: 输出文件路径（如果为None，则返回字典而不写入文件）
            
        Returns:
            状态字典
        """
        if file_path is None:
            file_path = Path("data/useridea_status.json")
        
        available_files = self.get_available_files()
        completed_files = list(self.idea_dir.glob(f"{self.completed_prefix}*.txt"))
        
        status_data = {
            "metadata": {
                "export_time": time.time(),
                "export_time_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "idea_dir": str(self.idea_dir),
                "completed_prefix": self.completed_prefix,
                "total_files": len(available_files) + len(completed_files)
            },
            "files": {}
        }
        
        # 处理未完成文件
        for file_path_obj in available_files:
            try:
                idea_file = self.parse_idea_file(file_path_obj)
                file_key = file_path_obj.name
                status_data["files"][file_key] = {
                    "path": str(file_path_obj),
                    "is_completed": idea_file.is_completed,
                    "total_entries": len(idea_file.entries),
                    "entries": []
                }
                
                for entry in idea_file.entries:
                    # 检查此条目是否已被注入过
                    injected = False
                    used_in_chapter = None
                    if self.state_manager:
                        injections = self.state_manager.get_user_idea_injections()
                        file_key_relative = str(file_path_obj.relative_to(self.idea_dir))
                        if file_key_relative in injections and entry.index in injections[file_key_relative]:
                            injected = True
                            # 尝试找到使用的章节
                            current_idea = self.state_manager.get_current_user_idea()
                            if current_idea and current_idea.get("file_name") == file_key_relative and current_idea.get("entry_index") == entry.index:
                                used_in_chapter = current_idea.get("chapter_num")
                    
                    status_data["files"][file_key]["entries"].append({
                        "index": entry.index,
                        "status": entry.status.value,
                        "content_preview": entry.content[:100] + "..." if len(entry.content) > 100 else entry.content,
                        "content_length": len(entry.content),
                        "injected": injected,
                        "used_in_chapter": used_in_chapter,
                        "marked_completed": entry.status == IdeaStatus.COMPLETED
                    })
            except Exception as e:
                logger.warning(f"导出文件状态失败 {file_path_obj}: {e}")
                status_data["files"][file_path_obj.name] = {"error": str(e)}
        
        # 处理已完成文件
        for file_path_obj in completed_files:
            file_key = file_path_obj.name
            status_data["files"][file_key] = {
                "path": str(file_path_obj),
                "is_completed": True,
                "total_entries": 0,  # 需要解析才能知道，但文件已重命名可能无法直接解析
                "entries": [],
                "note": "文件已重命名为completed_前缀，可能无法直接解析原始内容"
            }
        
        # 添加注入历史
        if self.state_manager:
            injections = self.state_manager.get_user_idea_injections()
            current_idea = self.state_manager.get_current_user_idea()
            status_data["injection_history"] = {
                "total_injected_entries": sum(len(indices) for indices in injections.values()),
                "injected_files": list(injections.keys()),
                "injections_by_file": injections,
                "current_idea": current_idea
            }
        
        # 写入文件
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"用户灵感状态已导出到: {file_path}")
        except Exception as e:
            logger.error(f"写入状态文件失败 {file_path}: {e}")
        
        return status_data


# 全局管理器实例
_global_user_idea_manager = None

def get_user_idea_manager(state_manager=None, config=None) -> UserIdeaManager:
    """
    获取全局用户灵感管理器实例（单例模式）
    
    Args:
        state_manager: 状态管理器实例
        config: 配置对象
        
    Returns:
        UserIdeaManager 实例
    """
    global _global_user_idea_manager
    if _global_user_idea_manager is None:
        _global_user_idea_manager = UserIdeaManager(state_manager, config)
    return _global_user_idea_manager