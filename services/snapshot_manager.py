"""
快照管理器 - 负责在上下文剪枝前保存完整历史记录快照

核心功能：
1. 在修剪前保存完整历史记录到 data/history_snapes/ 目录
2. 保存修剪决策的元数据（窗口章节、修剪时间、统计信息等）
3. 提供快照查询和恢复功能（用于调试和观测）
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class HistorySnapshotManager:
    """历史记录快照管理器"""
    
    def __init__(self, snapshot_dir: str = "data/history_snapes"):
        """
        初始化快照管理器
        
        Args:
            snapshot_dir: 快照保存目录
        """
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"历史快照管理器已初始化，快照目录: {self.snapshot_dir}")
    
    def save_snapshot_before_pruning(self, 
                                   full_history: List[Dict[str, Any]], 
                                   window_chapters: List[int],
                                   pruning_stats: Dict[str, Any],
                                   state_info: Dict[str, Any]) -> str:
        """
        在修剪前保存完整历史记录快照
        
        Args:
            full_history: 完整的原始历史记录
            window_chapters: 窗口章节列表 [chapter_1, chapter_2, chapter_3]
            pruning_stats: 修剪统计信息
            state_info: 状态信息
            
        Returns:
            str: 快照文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 生成描述性文件名
        if window_chapters and len(window_chapters) == 3:
            chapter_1, chapter_2, chapter_3 = window_chapters
            filename = f"snapshot_{timestamp}_ch{chapter_1}-{chapter_2}-{chapter_3}.json"
        else:
            filename = f"snapshot_{timestamp}.json"
        
        snapshot_path = self.snapshot_dir / filename
        
        # 构建快照数据
        snapshot_data = {
            "metadata": {
                "timestamp": timestamp,
                "save_time": datetime.now().isoformat(),
                "unix_timestamp": time.time(),
                "window_chapters": window_chapters,
                "original_history_length": len(full_history),
                "description": f"修剪前快照 - 窗口章节: {window_chapters}"
            },
            "pruning_decision": {
                "chapters_to_remove": window_chapters[:2] if len(window_chapters) >= 2 else [],
                "chapter_to_retain": window_chapters[2] if len(window_chapters) >= 3 else None,
                "pruning_stats": pruning_stats
            },
            "state_info": state_info,
            "full_history": full_history
        }
        
        # 保存快照
        try:
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                json.dump(snapshot_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"历史快照已保存: {snapshot_path}")
            logger.info(f"快照详情: {len(full_history)} 条消息, 窗口章节: {window_chapters}")
            
            # 记录统计信息
            self._log_snapshot_statistics(full_history, window_chapters)
            
            return str(snapshot_path)
            
        except Exception as e:
            logger.error(f"保存历史快照失败: {e}")
            return ""
    
    def _log_snapshot_statistics(self, history: List[Dict[str, Any]], window_chapters: List[int]) -> None:
        """记录快照统计信息"""
        if not history:
            return
        
        # 统计消息类型
        role_counts = {}
        chapter_counts = {}
        stage_counts = {}
        base_context_count = 0
        
        for msg in history:
            role = msg.get("role", "unknown")
            chapter = msg.get("chapter", 0)
            stage = msg.get("stage", "unknown")
            is_base = msg.get("is_base_context", False)
            
            role_counts[role] = role_counts.get(role, 0) + 1
            if chapter > 0:  # 章节0是系统/总结消息
                chapter_counts[chapter] = chapter_counts.get(chapter, 0) + 1
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
            if is_base:
                base_context_count += 1
        
        # 统计窗口章节消息
        window_message_count = 0
        if window_chapters:
            for msg in history:
                chapter = msg.get("chapter", 0)
                if chapter in window_chapters:
                    window_message_count += 1
        
        logger.info(f"快照统计: 总消息数={len(history)}, 基准上下文={base_context_count}")
        logger.info(f"角色分布: {role_counts}")
        logger.info(f"章节分布: {sorted(chapter_counts.keys())[-5:] if chapter_counts else []} (最近5章)")
        logger.info(f"窗口章节消息数: {window_message_count}")
    
    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """获取最新的快照"""
        snapshots = list(self.snapshot_dir.glob("snapshot_*.json"))
        if not snapshots:
            return None
        
        latest_snapshot = max(snapshots, key=lambda p: p.stat().st_mtime)
        
        try:
            with open(latest_snapshot, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载最新快照失败: {e}")
            return None
    
    def list_snapshots(self) -> List[Dict[str, Any]]:
        """列出所有快照信息"""
        snapshots = []
        for snapshot_file in self.snapshot_dir.glob("snapshot_*.json"):
            try:
                stat = snapshot_file.stat()
                snapshots.append({
                    "filename": snapshot_file.name,
                    "path": str(snapshot_file),
                    "size": stat.st_size,
                    "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
            except Exception as e:
                logger.warning(f"获取快照信息失败 {snapshot_file}: {e}")
        
        # 按修改时间排序（最新的在前）
        snapshots.sort(key=lambda x: x["modified_time"], reverse=True)
        return snapshots
    
    def get_snapshot_by_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """根据文件名获取快照"""
        snapshot_path = self.snapshot_dir / filename
        if not snapshot_path.exists():
            return None
        
        try:
            with open(snapshot_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载快照 {filename} 失败: {e}")
            return None
    
    def compare_snapshots(self, snapshot1_file: str, snapshot2_file: str) -> Dict[str, Any]:
        """比较两个快照的差异"""
        snapshot1 = self.get_snapshot_by_filename(snapshot1_file)
        snapshot2 = self.get_snapshot_by_filename(snapshot2_file)
        
        if not snapshot1 or not snapshot2:
            return {"error": "快照不存在"}
        
        history1 = snapshot1.get("full_history", [])
        history2 = snapshot2.get("full_history", [])
        
        # 计算基本差异
        diff = {
            "snapshot1": {
                "filename": snapshot1_file,
                "length": len(history1),
                "timestamp": snapshot1.get("metadata", {}).get("timestamp", "")
            },
            "snapshot2": {
                "filename": snapshot2_file,
                "length": len(history2),
                "timestamp": snapshot2.get("metadata", {}).get("timestamp", "")
            },
            "differences": {
                "length_diff": len(history2) - len(history1),
                "chapters_removed": [],
                "messages_removed": 0,
                "messages_added": 0
            }
        }
        
        # 分析章节变化
        chapters1 = set(msg.get("chapter", 0) for msg in history1)
        chapters2 = set(msg.get("chapter", 0) for msg in history2)
        
        removed_chapters = chapters1 - chapters2
        added_chapters = chapters2 - chapters1
        
        if removed_chapters:
            diff["differences"]["chapters_removed"] = sorted(list(removed_chapters))
        
        if added_chapters:
            diff["differences"]["chapters_added"] = sorted(list(added_chapters))
        
        return diff


# 全局实例
_snapshot_manager_instance = None

def get_snapshot_manager() -> HistorySnapshotManager:
    """获取快照管理器单例实例"""
    global _snapshot_manager_instance
    if _snapshot_manager_instance is None:
        _snapshot_manager_instance = HistorySnapshotManager()
    return _snapshot_manager_instance