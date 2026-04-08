"""
小说写作系统主入口 - 集成读者模块和新的调试系统

新增功能：
1. 集成文件操作追踪系统
2. 集成状态一致性检查
3. 集成调试信息增强
4. 定期运行系统诊断

命令行参数：
  --ct, --target-chapter N  运行到第N章停止
  --cc, --chapters-count N  额外运行N章后停止
"""

import logging
import time
import sys
import threading
import argparse
from pathlib import Path
from datetime import datetime

from config.settings import settings
from services.workflow import ChatWorkflow
from services.reader_workflow import ReaderWorkflow
from services.reader_b_workflow import ReaderBWorkflow
from services.user_idea_manager import get_user_idea_manager

# 导入新的调试系统
try:
    from utils.debug_enhancer import get_global_debug_enhancer, set_debug_log_level
    from utils.file_tracker import get_global_file_tracker
    from utils.integration_tool import get_global_integrator, run_system_diagnostic
    from utils.state_consistency_checker import StateConsistencyChecker
    DEBUG_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入调试系统模块: {e}")
    print("将使用基本日志功能")
    DEBUG_SYSTEM_AVAILABLE = False


def setup_logging() -> None:
    """配置日志系统：输出到控制台和data/debug.log文件"""
    import logging
    from pathlib import Path
    
    # 确定日志级别
    log_level = getattr(logging, settings.log_level.upper()) if hasattr(settings, 'log_level') else logging.INFO
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] - %(message)s'
    )
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 移除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器
    log_file = Path("data") / "debug.log"
    log_file.parent.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 设置第三方库日志级别
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("tenacity").setLevel(logging.WARNING)


def run_periodic_diagnostics(interval_minutes: int = 30):
    """运行定期诊断任务（在后台线程中运行）"""
    if not DEBUG_SYSTEM_AVAILABLE:
        return
    
    def diagnostic_task():
        logger = logging.getLogger(__name__)
        while True:
            try:
                logger.info("运行定期系统诊断...")
                
                # 运行系统诊断
                diagnostic_results = run_system_diagnostic()
                
                # 如果发现问题，记录警告
                if diagnostic_results['error_count'] > 0:
                    logger.warning(f"系统诊断发现 {diagnostic_results['error_count']} 个错误")
                
                # 运行状态一致性检查
                checker = StateConsistencyChecker()
                report = checker.generate_report()
                
                if report.issues_found > 0:
                    logger.warning(f"状态一致性检查发现 {report.issues_found} 个问题")
                    
                    # 如果有可自动修复的问题，尝试修复
                    if report.summary['auto_fixable'] > 0:
                        logger.info(f"尝试自动修复 {report.summary['auto_fixable']} 个问题")
                        fix_results = checker.fix_issues(dry_run=False)
                        
                        if fix_results['successful_fixes'] > 0:
                            logger.info(f"成功修复 {fix_results['successful_fixes']} 个问题")
                
                # 保存调试记录（已禁用，避免生成多余JSON文件）
                # enhancer = get_global_debug_enhancer()
                # saved_path = enhancer.save_records()
                # logger.info(f"调试记录已保存到: {saved_path}")
                
            except Exception as e:
                logger.error(f"定期诊断任务失败: {e}")
            
            # 等待指定间隔
            time.sleep(interval_minutes * 60)
    
    # 启动后台线程
    thread = threading.Thread(target=diagnostic_task, name="DiagnosticThread", daemon=True)
    thread.start()
    return thread


def main() -> None:
    """主函数"""
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='小说写作系统')
    parser.add_argument('--ct', '--target-chapter', type=int, help='目标停止章节')
    parser.add_argument('--cc', '--chapters-count', type=int, help='额外运行的章节数')
    args = parser.parse_args()
    
    print("=" * 80)
    print("小说写作系统 v3.0 - 集成读者模块和调试系统")
    print("=" * 80)
    
    # 配置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 初始化调试系统
    if DEBUG_SYSTEM_AVAILABLE:
        print("[OK] 调试系统已启用")
        print(f"   日志级别: {settings.log_level}")
        print(f"   日志文件: {settings.log_file or '控制台输出'}")
        
        # 初始化调试组件
        try:
            enhancer = get_global_debug_enhancer()
            tracker = get_global_file_tracker()
            integrator = get_global_integrator()
            
            # 记录系统启动
            enhancer.record_state_change(
                state_type="system_startup",
                old_value="stopped",
                new_value="started",
                metadata={"timestamp": datetime.now().isoformat()}
            )
            
            print("[OK] 调试组件初始化完成")
            # 强制设置调试日志级别为 CRITICAL，抑制所有日志输出
            set_debug_log_level('CRITICAL')
        except Exception as e:
            logger.warning(f"调试组件初始化失败: {e}")
            print(f"[WARNING] 调试组件初始化失败: {e}")
    else:
        print("[WARNING] 调试系统未启用，使用基本日志功能")
    
    print("-" * 80)
    
    # 验证配置
    if not settings.validate():
        print("配置验证失败，请检查环境变量和配置文件")
        sys.exit(1)
    
    print(settings)
    print("-" * 80)
    
    # 运行初始系统诊断（已禁用）
    # if DEBUG_SYSTEM_AVAILABLE:
    #     try:
    #         print("运行初始系统诊断...")
    #         diagnostic_results = run_system_diagnostic()
    #
    #         if diagnostic_results['overall_status'] == 'healthy':
    #             print("✅ 系统诊断: 健康")
    #         else:
    #             print(f"⚠️  系统诊断: {diagnostic_results['overall_status']}")
    #             print(f"   发现 {diagnostic_results['error_count']} 个错误")
    #
    #         # 保存诊断报告
    #         integrator = get_global_integrator()
    #         saved_path = integrator.save_diagnostic_report(diagnostic_results)
    #         print(f"   诊断报告: {saved_path}")
    #
    #     except Exception as e:
    #         logger.warning(f"初始系统诊断失败: {e}")
    #         print(f"⚠️  初始系统诊断失败: {e}")
    
    print("-" * 80)
    
    def graceful_stop(reason: str) -> None:
        """优雅停止程序，模拟 Ctrl+C 中断处理"""
        print(f"\n\n程序达到停止条件: {reason}")
        
        # 保存最终状态
        if DEBUG_SYSTEM_AVAILABLE:
            try:
                enhancer = get_global_debug_enhancer()
                enhancer.record_state_change(
                    state_type="system_shutdown",
                    old_value="running",
                    new_value="stopped",
                    metadata={"reason": reason, "timestamp": datetime.now().isoformat()}
                )
                
                # 保存最后的调试记录（已禁用，避免生成多余JSON文件）
                # saved_path = enhancer.save_records()
                # print(f"调试记录已保存到: {saved_path}")
            except Exception as e:
                logger.warning(f"保存调试记录失败: {e}")
        
        print("状态已自动保存，下次启动将从断点继续")
        sys.exit(0)
    
    try:
        # 初始化工作流
        writer = ChatWorkflow()
        reader = ReaderWorkflow()
        reader_b = ReaderBWorkflow()
        
        print("系统初始化完成，开始执行工作流...")
        print("写作模块: 设计 -> 写作 -> 总结 (1-3-1架构)")
        print("读者模块: 记忆 -> 反馈 (平行运行)")
        print("调试系统: 文件追踪 + 状态检查 + 调试增强")
        print("审计模块: 已禁用")
        print("按 Ctrl+C 停止程序")
        print("-" * 80)
        
        # 启动定期诊断任务（已禁用）
        # if DEBUG_SYSTEM_AVAILABLE:
        #     diagnostic_thread = run_periodic_diagnostics(interval_minutes=30)
        #     print("✅ 定期诊断任务已启动 (每30分钟运行一次)")
        
        # 显示初始状态
        writer_status = writer.get_status()
        reader_status = reader.get_status()
        reader_b_status = reader_b.get_status()
        
        print(f"\n初始状态:")
        print(f"  写作: 第{writer_status['current_chapter']}章, 阶段: {writer_status['current_stage']}")
        print(f"  读者: 最后处理章节: {reader_status['last_processed_chapter']}, 阶段: {reader_status['current_stage']}")
        print(f"  读者 B: 最后处理章节: {reader_b_status['last_processed_chapter']}, 阶段: {reader_b_status['current_stage']}")
        
        # 计算停止章节
        current_chapter = writer_status['current_chapter']
        stop_chapter = None
        
        # 参数优先级：--ct > --cc > 协同模式 > 默认逻辑
        if args.ct is not None:
            stop_chapter = args.ct
            print(f"目标停止章节: {stop_chapter}")
        elif args.cc is not None:
            stop_chapter = current_chapter + args.cc
            print(f"额外运行 {args.cc} 章，停止章节: {stop_chapter}")
        else:
            # 检查用户协同模式
            if settings.user_idea.collaborative_mode and settings.user_idea.auto_cc_enabled:
                try:
                    # 获取用户灵感管理器实例
                    user_idea_manager = get_user_idea_manager()
                    stats = user_idea_manager.get_collaborative_stats()
                    
                    if stats["recommendation"]["should_use_collaborative_mode"]:
                        suggested_chapters = stats["recommendation"]["suggested_cc"]
                        stop_chapter = current_chapter + suggested_chapters
                        print(f"用户协同模式已启用: 发现 {stats['pending_entries']} 个待处理灵感，每个灵感分配 {stats['min_chapters_per_idea']} 章")
                        print(f"自动规划 {suggested_chapters} 章，停止章节: {stop_chapter}")
                    else:
                        print(f"用户协同模式已启用但灵感不足: {stats['recommendation']['reason']}")
                except Exception as e:
                    logger.warning(f"用户协同模式处理失败: {e}")
                    print(f"警告: 用户协同模式处理失败，回退到默认逻辑")
            
            # 如果协同模式未启用或没有足够灵感，使用默认逻辑
            if stop_chapter is None:
                if current_chapter <= 30:
                    stop_chapter = 30
                    print(f"使用默认停止章节: {stop_chapter}")
                else:
                    print("未指定停止条件，将无限运行")
        
        # 主循环
        step_count = 0
        while True:
            # 调度检查：如果启用了时间调度且不在时间窗口内，则等待或退出
            if settings.scheduler.enabled:
                while not settings.scheduler.is_within_window():
                    print(f"\n当前时间不在运行窗口内 ({settings.scheduler.time_window})，等待...")
                    if settings.scheduler.pause_behavior == "exit":
                        graceful_stop(f"时间窗口外，优雅退出")
                    # 休眠一段时间后重�?                    time.sleep(settings.scheduler.check_interval_seconds)
            step_count += 1
            print(f"\n步骤 #{step_count}")
            
            # 第一步：执行写作步骤
            print("1. 执行写作步骤...")
            writer_success = writer.run_step()
            
            if not writer_success:
                logger.error("写作步骤执行失败，等待后重试...")
                time.sleep(5)  # 等待5秒后重试
                continue
            
            # 第二步：检查是否有新章节，执行读者步骤
            print("2. 检查读者模块...")
            reader_success = reader.run_step()
            
            if reader_success:
                print("  读者模块已处理新章节")
            else:
                print("  读者模块：无新章节需要处理")
            
            # 第三步：检查是否有新章节，执行读者 B 步骤
            print("3. 检查读者 B 模块...")
            reader_b_success = reader_b.run_step()
            
            if reader_b_success:
                print("  读者 B 模块已处理新章节")
            else:
                print("  读者 B 模块：无新章节需要处理")
            
            # 显示当前状态
            writer_status = writer.get_status()
            reader_status = reader.get_status()
            reader_b_status = reader_b.get_status()
            
            print(f"\n当前状态:")
            print(f"  写作: 第{writer_status['current_chapter']}章, 阶段: {writer_status['current_stage']}, 窗口: {writer_status['window_chapters']}")
            print(f"  读者: 最后处理章节: {reader_status['last_processed_chapter']}, 阶段: {reader_status['current_stage']}, 记忆长度: {reader_status['reader_memory_length']}字符")
            print(f"  读者 B: 最后处理章节: {reader_b_status['last_processed_chapter']}, 阶段: {reader_b_status['current_stage']}, 记忆长度: {reader_b_status['reader_memory_length']}字符")
            
            # 每10步记录一次调试信息（已禁用）
            # if DEBUG_SYSTEM_AVAILABLE and step_count % 10 == 0:
            #     try:
            #         enhancer = get_global_debug_enhancer()
            #         enhancer.record_state_change(
            #             state_type="workflow_progress",
            #             old_value=f"step_{step_count-10}",
            #             new_value=f"step_{step_count}",
            #             metadata={
            #                 "writer_chapter": writer_status['current_chapter'],
            #                 "reader_chapter": reader_status['last_processed_chapter'],
            #                 "step_count": step_count
            #             }
            #         )
            #     except Exception as e:
            #         logger.warning(f"记录调试信息失败: {e}")
            
            # 检查是否达到停止章节
            current_chapter = writer_status['current_chapter']
            if stop_chapter is not None and current_chapter == stop_chapter:
                graceful_stop(f"达到预设停止章节 {stop_chapter}")
            
            # 短暂暂停，避免API限流
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        
        # 保存最终状态
        if DEBUG_SYSTEM_AVAILABLE:
            try:
                enhancer = get_global_debug_enhancer()
                enhancer.record_state_change(
                    state_type="system_shutdown",
                    old_value="running",
                    new_value="stopped",
                    metadata={"reason": "user_interrupt", "timestamp": datetime.now().isoformat()}
                )
                
                # 保存最后的调试记录（已禁用，避免生成多余JSON文件）
                # saved_path = enhancer.save_records()
                # print(f"调试记录已保存到: {saved_path}")
            except Exception as e:
                logger.warning(f"保存调试记录失败: {e}")
        
        print("状态已自动保存，下次启动将从断点继续")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"程序发生未捕获的异常: {e}", exc_info=True)
        
        # 记录异常到调试系统
        if DEBUG_SYSTEM_AVAILABLE:
            try:
                enhancer = get_global_debug_enhancer()
                enhancer.record_state_change(
                    state_type="system_crash",
                    old_value="running",
                    new_value="crashed",
                    metadata={"error": str(e), "timestamp": datetime.now().isoformat()}
                )
                
                # 保存崩溃时的调试记录（已禁用，避免生成多余JSON文件）
                # saved_path = enhancer.save_records()
                # print(f"崩溃调试记录已保存到: {saved_path}")
            except Exception as e2:
                logger.warning(f"保存崩溃调试记录失败: {e2}")
        
        print(f"\n程序异常退出: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()