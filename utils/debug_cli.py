"""
调试系统命令行工具 - 提供完整的日志和调试功能

功能：
1. 运行系统诊断
2. 检查状态一致性
3. 修复检测到的问题
4. 查看调试记录
5. 设置日志级别
6. 监控文件操作
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.integration_tool import (
    run_system_diagnostic, 
    fix_system_issues, 
    check_consistency_and_fix,
    get_global_integrator
)
from utils.state_consistency_checker import (
    StateConsistencyChecker, 
    run_full_check, 
    fix_duplicate_files
)
from utils.debug_enhancer import (
    get_global_debug_enhancer,
    save_debug_records,
    print_debug_summary,
    set_debug_log_level
)
from utils.file_tracker import get_global_file_tracker

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """设置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def cmd_diagnostic(args):
    """运行系统诊断"""
    print("运行系统诊断...")
    
    integrator = get_global_integrator()
    diagnostic_results = integrator.run_diagnostic()
    integrator.print_diagnostic_summary(diagnostic_results)
    
    if args.save:
        saved_path = integrator.save_diagnostic_report(diagnostic_results)
        print(f"诊断报告已保存到: {saved_path}")
    
    return 0


def cmd_check_consistency(args):
    """检查状态一致性"""
    print("检查状态一致性...")
    
    checker = StateConsistencyChecker()
    report = checker.generate_report()
    saved_path = checker.save_report(report)
    
    print(f"检查完成:")
    print(f"  文件总数: {report.total_files}")
    print(f"  发现问题: {report.issues_found}")
    print(f"  严重问题: {report.summary['critical_issues']}")
    print(f"  可自动修复: {report.summary['auto_fixable']}")
    print(f"  报告路径: {saved_path}")
    
    if args.fix and report.summary['auto_fixable'] > 0:
        print(f"\n尝试修复 {report.summary['auto_fixable']} 个可自动修复的问题...")
        fix_results = checker.fix_issues(dry_run=not args.execute)
        
        if args.execute:
            print(f"修复完成:")
            print(f"  尝试修复: {fix_results['attempted_fixes']}")
            print(f"  成功修复: {fix_results['successful_fixes']}")
            print(f"  失败修复: {fix_results['failed_fixes']}")
        else:
            print("试运行模式（不实际执行修复）:")
            for detail in fix_results.get('details', []):
                print(f"  计划操作: {detail.get('action', 'unknown')} - {detail.get('file_path', 'unknown')}")
    
    return 0


def cmd_fix_issues(args):
    """修复系统问题"""
    print("修复系统问题...")
    
    fix_results = fix_system_issues(dry_run=not args.execute)
    
    if fix_results['success']:
        print("修复操作完成:")
        for action in fix_results.get('actions', []):
            action_type = action.get('type', 'unknown')
            status = action.get('status', 'unknown')
            print(f"  {action_type}: {status}")
        
        if not args.execute:
            print("\n注意: 这是试运行模式，未实际执行修复操作")
            print("使用 --execute 参数实际执行修复")
    else:
        print(f"修复失败: {fix_results.get('error', '未知错误')}")
        return 1
    
    return 0


def cmd_debug_info(args):
    """查看调试信息"""
    enhancer = get_global_debug_enhancer()
    
    if args.summary:
        print("调试信息摘要:")
        enhancer.print_summary()
    
    if args.save:
        saved_path = save_debug_records()
        print(f"调试记录已保存到: {saved_path}")
    
    if args.clear:
        enhancer.clear_records()
        print("调试记录已清空")
    
    return 0


def cmd_file_operations(args):
    """查看文件操作记录"""
    tracker = get_global_file_tracker()
    
    operations = tracker.get_operations(limit=args.limit)
    
    print(f"文件操作记录 (最近 {len(operations)} 条):")
    print("-" * 100)
    
    for i, op in enumerate(operations, 1):
        print(f"{i}. {op.get('timestamp_iso', '未知时间')}")
        print(f"   操作: {op.get('operation_type', '未知')}")
        print(f"   文件: {op.get('file_path', '未知')}")
        print(f"   状态: {'成功' if op.get('success') else '失败'}")
        
        metadata = op.get('metadata', {})
        if metadata:
            print(f"   元数据: {metadata}")
        
        print()
    
    if args.save:
        saved_path = tracker.save_operations()
        print(f"文件操作记录已保存到: {saved_path}")
    
    return 0


def cmd_log_level(args):
    """设置日志级别"""
    set_debug_log_level(args.level)
    print(f"日志级别已设置为: {args.level}")
    return 0


def cmd_monitor(args):
    """监控文件操作"""
    print("开始监控文件操作...")
    print("按 Ctrl+C 停止监控")
    print("-" * 60)
    
    tracker = get_global_file_tracker()
    enhancer = get_global_debug_enhancer()
    
    try:
        import time
        last_count = len(tracker.get_operations())
        
        while True:
            # 获取当前操作记录
            operations = tracker.get_operations()
            current_count = len(operations)
            
            # 如果有新操作，显示它们
            if current_count > last_count:
                new_ops = operations[last_count:current_count]
                for op in new_ops:
                    timestamp = op.get('timestamp_iso', '未知时间').split('T')[1][:8]
                    op_type = op.get('operation_type', '未知')
                    file_path = Path(op.get('file_path', '未知')).name
                    status = "✓" if op.get('success') else "✗"
                    
                    print(f"[{timestamp}] {status} {op_type:10} {file_path}")
                
                last_count = current_count
            
            # 等待
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        print("\n监控已停止")
    
    return 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="调试系统命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行系统诊断
  python debug_cli.py diagnostic
  
  # 检查状态一致性并修复
  python debug_cli.py check-consistency --fix --execute
  
  # 查看调试信息
  python debug_cli.py debug-info --summary --save
  
  # 监控文件操作
  python debug_cli.py monitor --interval 1
  
  # 设置日志级别
  python debug_cli.py log-level --level DEBUG
        """
    )
    
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="详细输出模式")
    
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # diagnostic 命令
    diagnostic_parser = subparsers.add_parser("diagnostic", help="运行系统诊断")
    diagnostic_parser.add_argument("--save", action="store_true",
                                  help="保存诊断报告")
    diagnostic_parser.set_defaults(func=cmd_diagnostic)
    
    # check-consistency 命令
    check_parser = subparsers.add_parser("check-consistency", help="检查状态一致性")
    check_parser.add_argument("--fix", action="store_true",
                             help="尝试修复检测到的问题")
    check_parser.add_argument("--execute", action="store_true",
                             help="实际执行修复（默认试运行）")
    check_parser.set_defaults(func=cmd_check_consistency)
    
    # fix-issues 命令
    fix_parser = subparsers.add_parser("fix-issues", help="修复系统问题")
    fix_parser.add_argument("--execute", action="store_true",
                           help="实际执行修复（默认试运行）")
    fix_parser.set_defaults(func=cmd_fix_issues)
    
    # debug-info 命令
    debug_parser = subparsers.add_parser("debug-info", help="查看调试信息")
    debug_parser.add_argument("--summary", action="store_true",
                             help="显示调试摘要")
    debug_parser.add_argument("--save", action="store_true",
                             help="保存调试记录")
    debug_parser.add_argument("--clear", action="store_true",
                             help="清空调试记录")
    debug_parser.set_defaults(func=cmd_debug_info)
    
    # file-ops 命令
    file_parser = subparsers.add_parser("file-ops", help="查看文件操作记录")
    file_parser.add_argument("--limit", type=int, default=20,
                            help="显示记录数量限制")
    file_parser.add_argument("--save", action="store_true",
                            help="保存操作记录")
    file_parser.set_defaults(func=cmd_file_operations)
    
    # log-level 命令
    log_parser = subparsers.add_parser("log-level", help="设置日志级别")
    log_parser.add_argument("--level", type=str, default="INFO",
                           choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                           help="日志级别")
    log_parser.set_defaults(func=cmd_log_level)
    
    # monitor 命令
    monitor_parser = subparsers.add_parser("monitor", help="监控文件操作")
    monitor_parser.add_argument("--interval", type=float, default=1.0,
                               help="监控间隔（秒）")
    monitor_parser.set_defaults(func=cmd_monitor)
    
    # 解析参数
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.verbose)
    
    # 执行命令
    if hasattr(args, 'func'):
        try:
            return args.func(args)
        except Exception as e:
            logger.error(f"命令执行失败: {e}", exc_info=args.verbose)
            return 1
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
