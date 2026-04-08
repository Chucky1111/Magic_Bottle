"""
提示词专用日志记录器
记录序列注入、提示词简化、模板渲染等关键事件
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class PromptEventType(str, Enum):
    """提示词事件类型枚举"""
    SEQUENCE_INJECTION = "sequence_injection"
    PROMPT_SIMPLIFICATION = "prompt_simplification"
    TEMPLATE_RENDERING = "template_rendering"
    STATE_CHANGE = "state_change"
    VARIABLE_REPLACEMENT = "variable_replacement"
    ERROR = "error"
    INFO = "info"
    AUDITOR_FEEDBACK_INJECTION = "auditor_feedback_injection"


class PromptLogger:
    """提示词专用日志记录器"""
    
    def __init__(self, log_file: str = "data/prompt_log.json", max_entries: int = 10000):
        """
        初始化提示词日志记录器
        
        Args:
            log_file: 日志文件路径
            max_entries: 最大日志条目数（防止日志文件过大）
        """
        self.log_file = Path(log_file)
        self.max_entries = max_entries
        self.log_entries: List[Dict[str, Any]] = []
        self.session_id = f"session_{int(time.time())}"
        
        # 确保目录存在
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载现有日志
        self._load_existing_logs()
        
        logger.info(f"提示词日志记录器初始化完成，日志文件: {self.log_file}")
    
    def _load_existing_logs(self) -> None:
        """加载现有的日志文件"""
        try:
            if self.log_file.exists() and self.log_file.stat().st_size > 0:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    self.log_entries = json.load(f)
                
                # 限制日志条目数量
                if len(self.log_entries) > self.max_entries:
                    self.log_entries = self.log_entries[-self.max_entries:]
                    logger.warning(f"日志条目超过限制，保留最近的 {self.max_entries} 条")
                
                logger.info(f"已加载 {len(self.log_entries)} 条现有日志条目")
            else:
                self.log_entries = []
                logger.info("没有现有日志文件，创建新的日志")
        except Exception as e:
            logger.error(f"加载日志文件失败: {e}")
            self.log_entries = []
    
    def _save_logs(self) -> None:
        """保存日志到文件"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.log_entries, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"日志已保存到 {self.log_file}，当前条目数: {len(self.log_entries)}")
        except Exception as e:
            logger.error(f"保存日志文件失败: {e}")
    
    def _add_log_entry(self, event_type: PromptEventType, chapter_num: int, 
                      stage: str, event_data: Dict[str, Any]) -> None:
        """
        添加日志条目
        
        Args:
            event_type: 事件类型
            chapter_num: 章节号
            stage: 阶段 (design/write/summary)
            event_data: 事件数据
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "chapter": chapter_num,
            "stage": stage,
            "event_type": event_type.value,
            "event_data": event_data,
            "metadata": {
                "session_id": self.session_id,
                "process_id": None  # 可以添加进程ID，但Windows上获取较复杂
            }
        }
        
        self.log_entries.append(log_entry)
        
        # 限制日志条目数量
        if len(self.log_entries) > self.max_entries:
            self.log_entries = self.log_entries[-self.max_entries:]
        
        # 异步保存（简化版：立即保存）
        self._save_logs()
        
        # 同时输出到标准日志
        logger.info(f"[PromptLog] {event_type.value} - 第{chapter_num}章 {stage}: {event_data.get('summary', '')}")
    
    def log_sequence_injection(self, chapter_num: int, stage: str, 
                              sequence_file: str, module_index: int,
                              module_length: int, module_preview: str = "") -> None:
        """
        记录序列注入事件
        
        Args:
            chapter_num: 章节号
            stage: 阶段 (design/write)
            sequence_file: 序列文件名
            module_index: 模块索引
            module_length: 模块长度（字符数）
            module_preview: 模块预览（前100字符）
        """
        event_data = {
            "sequence_file": sequence_file,
            "module_index": module_index,
            "module_length": module_length,
            "module_preview": module_preview[:100] + "..." if len(module_preview) > 100 else module_preview,
            "summary": f"注入序列 {sequence_file}[{module_index}] ({module_length} 字符)"
        }
        
        self._add_log_entry(PromptEventType.SEQUENCE_INJECTION, chapter_num, stage, event_data)
    
    def log_prompt_simplification(self, chapter_num: int, stage: str,
                                 original_length: int, simplified_length: int,
                                 reduction_percent: float) -> None:
        """
        记录提示词简化事件
        
        Args:
            chapter_num: 章节号
            stage: 阶段 (design/write)
            original_length: 原始长度
            simplified_length: 简化后长度
            reduction_percent: 减少百分比
        """
        event_data = {
            "original_length": original_length,
            "simplified_length": simplified_length,
            "reduction_percent": round(reduction_percent, 2),
            "summary": f"提示词简化: {original_length} -> {simplified_length} 字符 (-{reduction_percent:.1f}%)"
        }
        
        self._add_log_entry(PromptEventType.PROMPT_SIMPLIFICATION, chapter_num, stage, event_data)
    
    def log_template_rendering(self, chapter_num: int, stage: str,
                              template_file: str, variables: Dict[str, Any],
                              final_length: int) -> None:
        """
        记录模板渲染事件
        
        Args:
            chapter_num: 章节号
            stage: 阶段 (design/write/summary)
            template_file: 模板文件名
            variables: 替换的变量字典
            final_length: 最终提示词长度
        """
        # 清理变量值，避免日志过大
        cleaned_variables = {}
        for key, value in variables.items():
            if isinstance(value, str):
                if len(value) > 50:
                    cleaned_variables[key] = value[:50] + "..."
                else:
                    cleaned_variables[key] = value
            else:
                cleaned_variables[key] = str(value)
        
        event_data = {
            "template_file": template_file,
            "variables": cleaned_variables,
            "final_length": final_length,
            "summary": f"渲染模板 {template_file} -> {final_length} 字符"
        }
        
        self._add_log_entry(PromptEventType.TEMPLATE_RENDERING, chapter_num, stage, event_data)
    
    def log_state_change(self, chapter_num: int, stage: str,
                        old_state: Dict[str, Any], new_state: Dict[str, Any]) -> None:
        """
        记录状态变化事件
        
        Args:
            chapter_num: 章节号
            stage: 阶段
            old_state: 旧状态
            new_state: 新状态
        """
        # 找出变化的字段
        changed_fields = {}
        for key in set(old_state.keys()) | set(new_state.keys()):
            old_value = old_state.get(key)
            new_value = new_state.get(key)
            if old_value != new_value:
                changed_fields[key] = {
                    "old": old_value,
                    "new": new_value
                }
        
        event_data = {
            "changed_fields": changed_fields,
            "summary": f"状态变化: {len(changed_fields)} 个字段已更新"
        }
        
        self._add_log_entry(PromptEventType.STATE_CHANGE, chapter_num, stage, event_data)
    
    def log_variable_replacement(self, chapter_num: int, stage: str,
                                variable_name: str, original_value: str,
                                replaced_value: str) -> None:
        """
        记录变量替换事件
        
        Args:
            chapter_num: 章节号
            stage: 阶段
            variable_name: 变量名
            original_value: 原始值（模板中的占位符）
            replaced_value: 替换后的值
        """
        event_data = {
            "variable_name": variable_name,
            "original_value": original_value,
            "replaced_value": replaced_value[:100] + "..." if len(replaced_value) > 100 else replaced_value,
            "summary": f"变量替换: {variable_name} = {len(replaced_value)} 字符"
        }
        
        self._add_log_entry(PromptEventType.VARIABLE_REPLACEMENT, chapter_num, stage, event_data)
    
    def log_info(self, chapter_num: int, stage: str, message: str, details: Dict[str, Any] = None) -> None:
        """
        记录信息事件
        
        Args:
            chapter_num: 章节号
            stage: 阶段
            message: 信息消息
            details: 详细信息
        """
        event_data = {
            "message": message,
            "details": details or {},
            "summary": message
        }
        
        self._add_log_entry(PromptEventType.INFO, chapter_num, stage, event_data)
    
    def log_auditor_feedback_injection(self, chapter_num: int, stage: str,
                                      feedback_length: int, feedback_preview: str = "") -> None:
        """
        记录审计反馈注入事件

        Args:
            chapter_num: 章节号
            stage: 阶段 (design/write)
            feedback_length: 审计反馈长度（字符数）
            feedback_preview: 审计反馈预览（前100字符）
        """
        event_data = {
            "feedback_length": feedback_length,
            "feedback_preview": feedback_preview[:100] + "..." if len(feedback_preview) > 100 else feedback_preview,
            "summary": f"注入审计反馈 ({feedback_length} 字符)"
        }

        self._add_log_entry(PromptEventType.AUDITOR_FEEDBACK_INJECTION, chapter_num, stage, event_data)

    def log_feedback_usage(self, chapter_num: int, feedback_length: int, feedback_preview: str = "", feedback_type: str = "reader") -> None:
        """
        记录读者反馈使用事件

        Args:
            chapter_num: 章节号
            feedback_length: 读者反馈长度（字符数）
            feedback_preview: 读者反馈预览（前100字符）
            feedback_type: 反馈类型，可选值 "reader" 或 "reader_b"，默认为 "reader"
        """
        type_display = "读者反馈" if feedback_type == "reader" else "读者B反馈"
        event_data = {
            "feedback_length": feedback_length,
            "feedback_preview": feedback_preview[:100] + "..." if len(feedback_preview) > 100 else feedback_preview,
            "feedback_type": feedback_type,
            "summary": f"使用{type_display} ({feedback_length} 字符)"
        }

        self._add_log_entry(PromptEventType.INFO, chapter_num, "context", event_data)
    
    def log_error(self, chapter_num: int, stage: str, error_message: str,
                 error_details: Dict[str, Any] = None) -> None:
        """
        记录错误事件
        
        Args:
            chapter_num: 章节号
            stage: 阶段
            error_message: 错误消息
            error_details: 错误详情
        """
        event_data = {
            "error_message": error_message,
            "error_details": error_details or {},
            "summary": f"错误: {error_message}"
        }
        
        self._add_log_entry(PromptEventType.ERROR, chapter_num, stage, event_data)
    
    def get_recent_logs(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的日志条目
        
        Args:
            count: 返回的条目数量
            
        Returns:
            List[Dict[str, Any]]: 日志条目列表
        """
        return self.log_entries[-count:] if self.log_entries else []
    
    def filter_logs_by_chapter(self, chapter_num: int) -> List[Dict[str, Any]]:
        """
        按章节过滤日志
        
        Args:
            chapter_num: 章节号
            
        Returns:
            List[Dict[str, Any]]: 过滤后的日志条目
        """
        return [log for log in self.log_entries if log.get("chapter") == chapter_num]
    
    def filter_logs_by_event_type(self, event_type: PromptEventType) -> List[Dict[str, Any]]:
        """
        按事件类型过滤日志
        
        Args:
            event_type: 事件类型
            
        Returns:
            List[Dict[str, Any]]: 过滤后的日志条目
        """
        return [log for log in self.log_entries if log.get("event_type") == event_type.value]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取日志统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        if not self.log_entries:
            return {
                "total_entries": 0,
                "by_event_type": {},
                "by_chapter": {},
                "by_stage": {}
            }
        
        stats = {
            "total_entries": len(self.log_entries),
            "by_event_type": {},
            "by_chapter": {},
            "by_stage": {}
        }
        
        # 按事件类型统计
        for log in self.log_entries:
            event_type = log.get("event_type", "unknown")
            stats["by_event_type"][event_type] = stats["by_event_type"].get(event_type, 0) + 1
        
        # 按章节统计
        for log in self.log_entries:
            chapter = log.get("chapter", "unknown")
            stats["by_chapter"][chapter] = stats["by_chapter"].get(chapter, 0) + 1
        
        # 按阶段统计
        for log in self.log_entries:
            stage = log.get("stage", "unknown")
            stats["by_stage"][stage] = stats["by_stage"].get(stage, 0) + 1
        
        return stats
    
    def clear_logs(self) -> None:
        """清空所有日志"""
        self.log_entries = []
        self._save_logs()
        logger.info("提示词日志已清空")


# 单例实例
_prompt_logger_instance: Optional[PromptLogger] = None

def get_prompt_logger() -> PromptLogger:
    """获取提示词日志记录器单例实例"""
    global _prompt_logger_instance
    if _prompt_logger_instance is None:
        _prompt_logger_instance = PromptLogger()
    return _prompt_logger_instance