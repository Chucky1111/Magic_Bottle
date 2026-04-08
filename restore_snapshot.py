#!/usr/bin/env python3
"""
定点重启模块 - 从历史快照恢复状态和历史记录

用法:
    python restore_snapshot.py [--snapshot SNAPSHOT_FILE] [--chapter CHAPTER] [--stage STAGE] [--no-history] [--dry-run]

示例:
    python restore_snapshot.py --snapshot data/history_snapes/snapshot_20260124_153811_ch25-26-27.json
    python restore_snapshot.py --chapter 26 --stage design  # 交互式选择快照
    python restore_snapshot.py  # 完全交互模式
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
SNAPSHOT_DIR = PROJECT_ROOT / "data" / "history_snapes"
STATE_FILE = PROJECT_ROOT / "data" / "state.json"
HISTORY_FILE = PROJECT_ROOT / "data" / "history.json"
BACKUP_SUFFIX = ".bak"


def list_snapshots() -> List[Path]:
    """列出所有快照文件"""
    if not SNAPSHOT_DIR.exists():
        return []
    snapshots = sorted(SNAPSHOT_DIR.glob("snapshot_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return snapshots


def select_snapshot_interactively(snapshots: List[Path]) -> Optional[Path]:
    """交互式选择快照"""
    if not snapshots:
        print("未找到任何快照文件。")
        return None
    print("可用的快照文件:")
    for i, snapshot in enumerate(snapshots, 1):
        stat = snapshot.stat()
        size_kb = stat.st_size / 1024
        print(f"  {i:2d}. {snapshot.name} ({size_kb:.1f} KB, 修改时间: {stat.st_mtime})")
    while True:
        try:
            choice = input(f"请选择快照 (1-{len(snapshots)}) 或输入 'q' 退出: ").strip()
            if choice.lower() == 'q':
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(snapshots):
                return snapshots[idx]
            else:
                print(f"无效的选择，请输入 1 到 {len(snapshots)} 之间的数字。")
        except ValueError:
            print("请输入数字。")


def load_snapshot(snapshot_path: Path) -> Optional[Dict[str, Any]]:
    """加载快照文件"""
    try:
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"加载快照失败: {e}")
        return None


def backup_file(file_path: Path) -> bool:
    """备份文件"""
    if not file_path.exists():
        return True
    backup_path = file_path.with_suffix(file_path.suffix + BACKUP_SUFFIX)
    try:
        shutil.copy2(file_path, backup_path)
        print(f"已备份 {file_path.name} 到 {backup_path.name}")
        return True
    except Exception as e:
        print(f"备份 {file_path.name} 失败: {e}")
        return False


def restore_state(state_info: Dict[str, Any], target_chapter: Optional[int] = None, target_stage: Optional[str] = None) -> bool:
    """
    恢复状态到 state.json
    
    Args:
        state_info: 快照中的 state_info 字典
        target_chapter: 目标章节号（如果为 None 则使用 state_info 中的 chapter_num）
        target_stage: 目标阶段（如果为 None 则使用 state_info 中的 stage）
    """
    if not STATE_FILE.parent.exists():
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 加载当前状态（如果存在）
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                current_state = json.load(f)
        except Exception as e:
            print(f"加载当前状态失败，将使用默认状态: {e}")
            current_state = {}
    else:
        current_state = {}
    
    # 确定要使用的章节和阶段
    chapter_num = target_chapter if target_chapter is not None else state_info.get("chapter_num", 1)
    stage = target_stage if target_stage is not None else state_info.get("stage", "design")
    
    # 更新关键字段
    # 注意：我们只更新 state_info 中存在的字段，其他字段保持不变
    updated = False
    if "chapter_num" in state_info or target_chapter is not None:
        current_state["chapter_num"] = chapter_num
        updated = True
    if "stage" in state_info or target_stage is not None:
        if stage not in ["design", "write", "summary"]:
            print(f"警告: 阶段 '{stage}' 无效，使用 'design'")
            stage = "design"
        current_state["stage"] = stage
        updated = True
    if "window_chapters" in state_info:
        current_state["window_chapters"] = state_info["window_chapters"]
        updated = True
    if "base_context_length" in state_info:
        current_state["base_context_length"] = state_info["base_context_length"]
        updated = True
    
    # 确保必需的字段存在（向后兼容）
    if "window_size" not in current_state:
        current_state["window_size"] = 3
    if "last_system_info_chapter" not in current_state:
        current_state["last_system_info_chapter"] = 0
    if "system_info_scheduled_chapters" not in current_state:
        current_state["system_info_scheduled_chapters"] = []
    if "system_info_cycle_start" not in current_state:
        current_state["system_info_cycle_start"] = 1
    if "system_info_cycle_length" not in current_state:
        current_state["system_info_cycle_length"] = 15
    if "sequence_state" not in current_state:
        current_state["sequence_state"] = {"design_index": 0, "write_index": 0}
    if "feedback_context" not in current_state:
        current_state["feedback_context"] = {
            "last_used_feedback_chapter": 0,
            "last_used_feedback_index": 0,
            "feedback_cycle_start": 1,
            "feedback_cycle_length": 10
        }
    if "summary_status_counter" not in current_state:
        current_state["summary_status_counter"] = 0
    
    # 保存状态
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(current_state, f, ensure_ascii=False, indent=2)
        print(f"状态已更新: 章节={current_state['chapter_num']}, 阶段={current_state['stage']}, 窗口章节={current_state.get('window_chapters', [])}")
        return True
    except Exception as e:
        print(f"保存状态失败: {e}")
        return False


def restore_history(full_history: List[Dict[str, Any]]) -> bool:
    """恢复历史记录到 history.json"""
    if not HISTORY_FILE.parent.exists():
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(full_history, f, ensure_ascii=False, indent=2)
        print(f"历史记录已恢复: {len(full_history)} 条消息")
        return True
    except Exception as e:
        print(f"保存历史记录失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="从历史快照恢复状态和历史记录")
    parser.add_argument("--snapshot", type=str, help="快照文件路径（如 data/history_snapes/snapshot_*.json）")
    parser.add_argument("--chapter", type=int, help="目标章节号（覆盖快照中的章节）")
    parser.add_argument("--stage", type=str, choices=["design", "write", "summary"], help="目标阶段（覆盖快照中的阶段）")
    parser.add_argument("--no-history", action="store_true", help="不恢复历史记录，仅更新状态")
    parser.add_argument("--dry-run", action="store_true", help="只显示将要执行的操作，不实际修改文件")
    args = parser.parse_args()
    
    print("=== 定点重启模块 ===")
    
    # 确定快照文件
    snapshot_path = None
    if args.snapshot:
        snapshot_path = Path(args.snapshot)
        if not snapshot_path.exists():
            print(f"错误: 快照文件不存在: {snapshot_path}")
            sys.exit(1)
    else:
        snapshots = list_snapshots()
        if not snapshots:
            print("错误: 未找到任何快照文件。")
            sys.exit(1)
        if len(snapshots) == 1:
            snapshot_path = snapshots[0]
            print(f"使用唯一快照: {snapshot_path.name}")
        else:
            snapshot_path = select_snapshot_interactively(snapshots)
            if snapshot_path is None:
                print("已取消。")
                sys.exit(0)
    
    # 加载快照
    snapshot_data = load_snapshot(snapshot_path)
    if snapshot_data is None:
        sys.exit(1)
    
    # 提取数据
    metadata = snapshot_data.get("metadata", {})
    state_info = snapshot_data.get("state_info", {})
    full_history = snapshot_data.get("full_history", [])
    
    print(f"快照信息: {metadata.get('description', '无描述')}")
    print(f"原始历史长度: {metadata.get('original_history_length', len(full_history))}")
    print(f"状态信息: 章节={state_info.get('chapter_num', 'N/A')}, 阶段={state_info.get('stage', 'N/A')}")
    
    # 确定目标章节和阶段
    target_chapter = args.chapter
    target_stage = args.stage
    if target_chapter is None:
        target_chapter = state_info.get("chapter_num")
    if target_stage is None:
        target_stage = state_info.get("stage", "design")
    
    print(f"目标: 章节={target_chapter}, 阶段={target_stage}")
    
    if args.dry_run:
        print("干跑模式: 不修改文件。")
        print("将执行以下操作:")
        print(f"  1. 备份现有 state.json 和 history.json")
        print(f"  2. 更新 state.json: chapter_num={target_chapter}, stage={target_stage}")
        if not args.no_history:
            print(f"  3. 恢复历史记录: {len(full_history)} 条消息")
        else:
            print("  3. 跳过历史记录恢复")
        sys.exit(0)
    
    # 备份现有文件
    print("备份现有文件...")
    if not backup_file(STATE_FILE):
        print("警告: 状态备份失败，继续执行。")
    if not args.no_history and not backup_file(HISTORY_FILE):
        print("警告: 历史记录备份失败，继续执行。")
    
    # 恢复状态
    print("恢复状态...")
    if not restore_state(state_info, target_chapter, target_stage):
        print("错误: 状态恢复失败。")
        sys.exit(1)
    
    # 恢复历史记录
    if not args.no_history:
        print("恢复历史记录...")
        if not restore_history(full_history):
            print("错误: 历史记录恢复失败。")
            sys.exit(1)
    else:
        print("跳过历史记录恢复（用户指定 --no-history）")
    
    print("=== 恢复完成 ===")
    print("注意: 请确保状态与历史记录一致。")
    print("下一步: 运行 main.py 继续写作。")


if __name__ == "__main__":
    main()