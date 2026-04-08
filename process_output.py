#!/usr/bin/env python3
"""
output目录文本处理器 - 主脚本

功能：
1. 监控output目录下的新章节文件
2. 应用文本处理规则：
   - 删除短引号（5个字以下且无标点）
   - 处理"不是...，..是..."句式
   - 删除小括号内容
3. 版式重排（默认启用）：
   - 按句子分段（句号、感叹号、问号）
   - 规范化空行（每段之间一个空行）
4. 状态持久化，支持断点续传

默认行为：持续监控output目录，每30秒检查一次新文件

使用方法：
1. 持续监控（默认）：python process_output.py
2. 单次处理：python process_output.py --once
3. 处理单个文件：python process_output.py --input output/第1章.txt --output output/第1章_processed.txt
4. 禁用版式重排：python process_output.py --no-reformat
"""

import sys
import logging
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from text_processor import FileMonitor, TextProcessor, setup_logging


def main():
    """主函数"""
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="output目录文本处理器 - 默认持续监控模式（每30秒检查一次）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
默认行为：持续监控output目录，每30秒检查一次新文件

示例：
  # 默认行为：持续监控（每30秒检查一次）
  python process_output.py
  
  # 单次处理所有新文件
  python process_output.py --once
  
  # 处理单个文件
  python process_output.py --input output/第1章.txt --output output/第1章_processed.txt
  
  # 禁用版式重排
  python process_output.py --no-reformat
  
  # 查看帮助
  python process_output.py --help
        """
    )
    
    parser.add_argument("--once", action="store_true",
                       help="单次处理模式（处理完所有新文件后退出）")
    parser.add_argument("--interval", type=int, default=30,
                       help="持续监控时的检查间隔（秒），默认30秒")
    parser.add_argument("--input", type=str,
                       help="单个文件处理模式：输入文件路径")
    parser.add_argument("--output", type=str,
                       help="单个文件处理模式：输出文件路径（默认覆盖原文件）")
    parser.add_argument("--watch-dir", type=str, default="output",
                       help="监控的目录，默认output")
    parser.add_argument("--output-dir", type=str,
                       default=r"output_processed",
                       help="输出目录，处理后的文件保存到此目录，默认不覆盖原文件")
    parser.add_argument("--no-reformat", action="store_true",
                       help="禁用版式重排功能")
    parser.add_argument("--no-sensitive-filter", action="store_true",
                       help="禁用敏感词过滤功能（默认启用）")
    parser.add_argument("--sensitive-wordlist", type=str,
                       help="指定敏感词词库文件路径（默认使用 config/sensitive_words.txt）")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="详细输出模式")
    
    args = parser.parse_args()
    
    # 配置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("启用详细日志模式")
    
    logger.info("=" * 60)
    logger.info("output目录文本处理器")
    logger.info("=" * 60)
    
    if args.input:
        # 单个文件处理模式
        enable_sensitive_filter = not args.no_sensitive_filter
        processor = TextProcessor(enable_sensitive_filter=enable_sensitive_filter,
                                  sensitive_wordlist_path=args.sensitive_wordlist)
        input_path = Path(args.input)
        output_path = Path(args.output) if args.output else None
        
        if not input_path.exists():
            logger.error(f"输入文件不存在: {input_path}")
            sys.exit(1)
        
        logger.info(f"处理单个文件: {input_path}")
        if output_path:
            logger.info(f"输出到: {output_path}")
        
        success = processor.process_file(input_path, output_path, reformat_layout=not args.no_reformat)
        
        if success:
            logger.info("文件处理成功")
            sys.exit(0)
        else:
            logger.error("文件处理失败")
            sys.exit(1)
    
    else:
        # 目录监控模式
        watch_dir = Path(args.watch_dir)
        output_dir = Path(args.output_dir) if args.output_dir else None
        
        if not watch_dir.exists():
            logger.warning(f"监控目录不存在: {watch_dir}，正在创建...")
            watch_dir.mkdir(parents=True, exist_ok=True)
        
        if output_dir:
            logger.info(f"输出目录: {output_dir.absolute()}")
            if not output_dir.exists():
                logger.warning(f"输出目录不存在: {output_dir}，正在创建...")
                output_dir.mkdir(parents=True, exist_ok=True)
        
        enable_sensitive_filter = not args.no_sensitive_filter
        monitor = FileMonitor(watch_dir, output_dir,
                              enable_sensitive_filter=enable_sensitive_filter,
                              sensitive_wordlist_path=args.sensitive_wordlist)
        
        if args.once:
            logger.info("执行单次处理模式")
            logger.info(f"监控目录: {watch_dir.absolute()}")
            
            processed = monitor.run_once(reformat_layout=not args.no_reformat)
            
            if processed > 0:
                logger.info(f"处理完成: {processed} 个文件")
            else:
                logger.info("没有新文件需要处理")
                
        else:
            logger.info("执行持续监控模式（默认）")
            logger.info(f"监控目录: {watch_dir.absolute()}")
            logger.info(f"检查间隔: {args.interval}秒")
            logger.info("按 Ctrl+C 停止")
            
            try:
                monitor.run_continuous(args.interval, reformat_layout=not args.no_reformat)
            except KeyboardInterrupt:
                logger.info("监控被用户中断")
            except Exception as e:
                logger.error(f"监控运行异常: {e}")
                sys.exit(1)


if __name__ == "__main__":
    main()
