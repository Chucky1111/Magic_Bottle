#!/usr/bin/env python3
"""
提示词日志查看工具
用于查看和分析提示词生成日志
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.prompt_logger import PromptLogger, PromptEventType, get_prompt_logger


class PromptLogViewer:
    """提示词日志查看器"""
    
    def __init__(self, log_file: str = "data/prompt_log.json"):
        """
        初始化日志查看器
        
        Args:
            log_file: 日志文件路径
        """
        self.log_file = Path(log_file)
        self.prompt_logger = get_prompt_logger()
    
    def show_recent_logs(self, count: int = 10, show_details: bool = False) -> None:
        """
        显示最近的日志条目
        
        Args:
            count: 显示的条目数量
            show_details: 是否显示详细信息
        """
        logs = self.prompt_logger.get_recent_logs(count)
        
        if not logs:
            print("没有日志条目")
            return
        
        print(f"显示最近的 {len(logs)} 条日志:")
        print("=" * 80)
        
        for i, log in enumerate(reversed(logs), 1):
            self._print_log_entry(log, i, show_details)
    
    def _print_log_entry(self, log: Dict[str, Any], index: int, show_details: bool) -> None:
        """打印单个日志条目"""
        timestamp = log.get("timestamp", "")
        chapter = log.get("chapter", "?")
        stage = log.get("stage", "?")
        event_type = log.get("event_type", "unknown")
        event_data = log.get("event_data", {})
        
        # 格式化时间戳
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            time_str = timestamp
        
        # 基本信息
        print(f"{index:3d}. [{time_str}] 第{chapter}章 {stage} - {event_type}")
        
        # 摘要信息
        summary = event_data.get("summary", "")
        if summary:
            print(f"     {summary}")
        
        # 详细信息
        if show_details:
            for key, value in event_data.items():
                if key != "summary":
                    if isinstance(value, dict):
                        print(f"     {key}:")
                        for sub_key, sub_value in value.items():
                            print(f"       {sub_key}: {sub_value}")
                    else:
                        print(f"     {key}: {value}")
        
        print()
    
    def filter_logs_by_chapter(self, chapter_num: int, show_details: bool = False) -> None:
        """
        按章节过滤日志
        
        Args:
            chapter_num: 章节号
            show_details: 是否显示详细信息
        """
        logs = self.prompt_logger.filter_logs_by_chapter(chapter_num)
        
        if not logs:
            print(f"第{chapter_num}章没有日志条目")
            return
        
        print(f"第{chapter_num}章的日志条目 ({len(logs)} 条):")
        print("=" * 80)
        
        for i, log in enumerate(reversed(logs), 1):
            self._print_log_entry(log, i, show_details)
    
    def filter_logs_by_event_type(self, event_type_str: str, show_details: bool = False) -> None:
        """
        按事件类型过滤日志
        
        Args:
            event_type_str: 事件类型字符串
            show_details: 是否显示详细信息
        """
        try:
            event_type = PromptEventType(event_type_str)
        except ValueError:
            print(f"无效的事件类型: {event_type_str}")
            print(f"可用的事件类型: {[e.value for e in PromptEventType]}")
            return
        
        logs = self.prompt_logger.filter_logs_by_event_type(event_type)
        
        if not logs:
            print(f"{event_type.value} 类型没有日志条目")
            return
        
        print(f"{event_type.value} 类型的日志条目 ({len(logs)} 条):")
        print("=" * 80)
        
        for i, log in enumerate(reversed(logs), 1):
            self._print_log_entry(log, i, show_details)
    
    def show_statistics(self) -> None:
        """显示日志统计信息"""
        stats = self.prompt_logger.get_statistics()
        
        print("提示词日志统计信息")
        print("=" * 80)
        print(f"总日志条目数: {stats['total_entries']}")
        
        # 按事件类型统计
        print("\n按事件类型统计:")
        for event_type, count in sorted(stats['by_event_type'].items()):
            print(f"  {event_type}: {count} 条")
        
        # 按章节统计
        print("\n按章节统计:")
        for chapter, count in sorted(stats['by_chapter'].items()):
            print(f"  第{chapter}章: {count} 条")
        
        # 按阶段统计
        print("\n按阶段统计:")
        for stage, count in sorted(stats['by_stage'].items()):
            print(f"  {stage}: {count} 条")
    
    def search_logs(self, keyword: str, show_details: bool = False) -> None:
        """
        搜索日志
        
        Args:
            keyword: 搜索关键词
            show_details: 是否显示详细信息
        """
        logs = self.prompt_logger.log_entries
        matching_logs = []
        
        for log in logs:
            # 在日志条目中搜索关键词
            log_str = json.dumps(log, ensure_ascii=False).lower()
            if keyword.lower() in log_str:
                matching_logs.append(log)
        
        if not matching_logs:
            print(f"没有找到包含 '{keyword}' 的日志条目")
            return
        
        print(f"找到 {len(matching_logs)} 条包含 '{keyword}' 的日志:")
        print("=" * 80)
        
        for i, log in enumerate(reversed(matching_logs), 1):
            self._print_log_entry(log, i, show_details)
    
    def show_sequence_injection_summary(self) -> None:
        """显示序列注入摘要"""
        logs = self.prompt_logger.filter_logs_by_event_type(PromptEventType.SEQUENCE_INJECTION)
        
        if not logs:
            print("没有序列注入日志")
            return
        
        print("序列注入摘要")
        print("=" * 80)
        
        # 按序列文件分组
        by_sequence_file = {}
        for log in logs:
            event_data = log.get("event_data", {})
            sequence_file = event_data.get("sequence_file", "unknown")
            module_index = event_data.get("module_index", -1)
            chapter = log.get("chapter", "?")
            stage = log.get("stage", "?")
            
            if sequence_file not in by_sequence_file:
                by_sequence_file[sequence_file] = {}
            
            if module_index not in by_sequence_file[sequence_file]:
                by_sequence_file[sequence_file][module_index] = []
            
            by_sequence_file[sequence_file][module_index].append({
                "chapter": chapter,
                "stage": stage,
                "module_length": event_data.get("module_length", 0)
            })
        
        # 显示摘要
        for sequence_file, modules in by_sequence_file.items():
            print(f"\n序列文件: {sequence_file}")
            total_injections = sum(len(chapters) for chapters in modules.values())
            print(f"  总注入次数: {total_injections}")
            
            for module_index, injections in sorted(modules.items()):
                print(f"  模块 {module_index}: {len(injections)} 次注入")
                
                # 显示最近几次注入
                recent_injections = injections[-5:]  # 显示最近5次
                for inj in recent_injections:
                    print(f"    第{inj['chapter']}章 {inj['stage']} ({inj['module_length']} 字符)")
    
    def show_prompt_simplification_summary(self) -> None:
        """显示提示词简化摘要"""
        logs = self.prompt_logger.filter_logs_by_event_type(PromptEventType.PROMPT_SIMPLIFICATION)
        
        if not logs:
            print("没有提示词简化日志")
            return
        
        print("提示词简化摘要")
        print("=" * 80)
        
        total_original = 0
        total_simplified = 0
        total_reduction = 0
        
        for log in logs:
            event_data = log.get("event_data", {})
            original_length = event_data.get("original_length", 0)
            simplified_length = event_data.get("simplified_length", 0)
            reduction_percent = event_data.get("reduction_percent", 0)
            
            total_original += original_length
            total_simplified += simplified_length
            total_reduction += reduction_percent
        
        avg_reduction = total_reduction / len(logs) if logs else 0
        
        print(f"总简化次数: {len(logs)}")
        print(f"总字符数: {total_original:,} -> {total_simplified:,}")
        print(f"平均减少: {avg_reduction:.1f}%")
        
        # 显示最近几次简化
        print("\n最近5次简化:")
        recent_logs = logs[-5:] if len(logs) > 5 else logs
        for log in recent_logs:
            event_data = log.get("event_data", {})
            chapter = log.get("chapter", "?")
            stage = log.get("stage", "?")
            original = event_data.get("original_length", 0)
            simplified = event_data.get("simplified_length", 0)
            reduction = event_data.get("reduction_percent", 0)
            
            print(f"  第{chapter}章 {stage}: {original:,} -> {simplified:,} 字符 (-{reduction:.1f}%)")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="提示词日志查看工具")
    parser.add_argument("--recent", type=int, default=0, 
                       help="显示最近的N条日志 (默认: 10)")
    parser.add_argument("--chapter", type=int, 
                       help="按章节过滤日志")
    parser.add_argument("--event-type", 
                       help="按事件类型过滤日志")
    parser.add_argument("--search", 
                       help="搜索包含关键词的日志")
    parser.add_argument("--stats", action="store_true",
                       help="显示统计信息")
    parser.add_argument("--sequence-summary", action="store_true",
                       help="显示序列注入摘要")
    parser.add_argument("--simplification-summary", action="store_true",
                       help="显示提示词简化摘要")
    parser.add_argument("--details", action="store_true",
                       help="显示详细信息")
    parser.add_argument("--clear", action="store_true",
                       help="清空所有日志")
    
    args = parser.parse_args()
    
    viewer = PromptLogViewer()
    
    try:
        if args.clear:
            confirm = input("确定要清空所有日志吗？(y/N): ")
            if confirm.lower() == 'y':
                viewer.prompt_logger.clear_logs()
                print("日志已清空")
            return
        
        if args.stats:
            viewer.show_statistics()
        elif args.sequence_summary:
            viewer.show_sequence_injection_summary()
        elif args.simplification_summary:
            viewer.show_prompt_simplification_summary()
        elif args.chapter:
            viewer.filter_logs_by_chapter(args.chapter, args.details)
        elif args.event_type:
            viewer.filter_logs_by_event_type(args.event_type, args.details)
        elif args.search:
            viewer.search_logs(args.search, args.details)
        else:
            count = args.recent if args.recent > 0 else 10
            viewer.show_recent_logs(count, args.details)
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())