"""
集成工具 - 将新的日志和调试系统集成到现有系统中

核心功能：
1. 集成文件操作追踪到现有文件处理流程
2. 集成状态一致性检查到主程序
3. 集成调试信息增强到关键函数
4. 创建定期检查任务
5. 提供诊断和修复功能
"""

import os
import sys
import logging
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# 导入新模块
from .file_tracker import get_global_file_tracker, FileOperationType, record_file_operation
from .state_consistency_checker import StateConsistencyChecker, run_full_check, fix_duplicate_files
from .debug_enhancer import get_global_debug_enhancer, debug_function, record_enhanced_file_operation

logger = logging.getLogger(__name__)


class SystemIntegrator:
    """系统集成器"""
    
    def __init__(self):
        """初始化系统集成器"""
        self.file_tracker = get_global_file_tracker()
        self.debug_enhancer = get_global_debug_enhancer()
        self.consistency_checker = StateConsistencyChecker()
        
        logger.info("系统集成器初始化完成")
    
    def setup_logging_integration(self):
        """设置日志集成"""
        # 设置调试增强器的日志级别
        self.debug_enhancer.set_log_level("DEBUG")
        
        # 记录集成开始
        self.debug_enhancer.record_state_change(
            state_type="system_integration",
            old_value="not_integrated",
            new_value="integrated",
            metadata={"timestamp": datetime.now().isoformat()}
        )
        
        logger.info("日志集成设置完成")
    
    def instrument_file_operations(self):
        """仪表化文件操作"""
        # 这里可以添加对现有文件操作函数的装饰器
        # 例如：装饰 text_processor.py 中的关键函数
        
        logger.info("文件操作仪表化准备完成")
        return True
    
    def create_periodic_check_task(self, interval_seconds: int = 300):
        """创建定期检查任务"""
        # 这个函数应该在单独的线程中运行
        def periodic_check():
            while True:
                try:
                    # 运行一致性检查
                    report = run_full_check(save_report=True)
                    
                    # 记录检查结果
                    self.debug_enhancer.record_state_change(
                        state_type="periodic_consistency_check",
                        old_value="pending",
                        new_value="completed",
                        metadata={
                            "issues_found": report.issues_found,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                    
                    # 如果有可修复的问题，记录警告
                    if report.summary['auto_fixable'] > 0:
                        logger.warning(f"发现 {report.summary['auto_fixable']} 个可自动修复的问题")
                    
                except Exception as e:
                    logger.error(f"定期检查失败: {e}")
                    self.debug_enhancer.record_state_change(
                        state_type="periodic_consistency_check",
                        old_value="pending",
                        new_value="failed",
                        metadata={"error": str(e)}
                    )
                
                # 等待指定间隔
                time.sleep(interval_seconds)
        
        logger.info(f"创建定期检查任务，间隔: {interval_seconds}秒")
        return periodic_check
    
    def run_diagnostic(self) -> Dict[str, Any]:
        """运行系统诊断"""
        diagnostic_results = {
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "issues": [],
            "recommendations": []
        }
        
        # 1. 检查文件追踪器
        try:
            file_ops = self.file_tracker.get_operations(limit=10)
            # 转换为可序列化的字典
            serializable_ops = []
            for op in file_ops[:3] if file_ops else []:
                if hasattr(op, 'to_dict'):
                    serializable_ops.append(op.to_dict())
                else:
                    # 如果是字典，直接使用
                    if isinstance(op, dict):
                        serializable_ops.append(op)
                    else:
                        # 转换为基本字典
                        serializable_ops.append({
                            'type': str(type(op)),
                            'repr': repr(op)[:100]
                        })
            
            diagnostic_results["components"]["file_tracker"] = {
                "status": "healthy",
                "recent_operations": len(file_ops),
                "sample": serializable_ops
            }
        except Exception as e:
            diagnostic_results["components"]["file_tracker"] = {
                "status": "error",
                "error": str(e)
            }
            diagnostic_results["issues"].append("文件追踪器初始化失败")
        
        # 2. 检查调试增强器
        try:
            debug_summary = self.debug_enhancer.get_summary()
            diagnostic_results["components"]["debug_enhancer"] = {
                "status": "healthy",
                "total_records": debug_summary["total_records"],
                "type_counts": debug_summary["type_counts"]
            }
        except Exception as e:
            diagnostic_results["components"]["debug_enhancer"] = {
                "status": "error",
                "error": str(e)
            }
            diagnostic_results["issues"].append("调试增强器初始化失败")
        
        # 3. 运行一致性检查
        try:
            report = self.consistency_checker.generate_report()
            diagnostic_results["components"]["consistency_checker"] = {
                "status": "healthy",
                "issues_found": report.issues_found,
                "critical_issues": report.summary["critical_issues"],
                "auto_fixable": report.summary["auto_fixable"]
            }
            
            # 记录发现的问题
            for issue in report.issues[:5]:  # 只记录前5个问题
                diagnostic_results["issues"].append({
                    "type": issue.issue_type,
                    "severity": issue.severity,
                    "description": issue.description,
                    "auto_fixable": issue.auto_fixable
                })
        except Exception as e:
            diagnostic_results["components"]["consistency_checker"] = {
                "status": "error",
                "error": str(e)
            }
            diagnostic_results["issues"].append("一致性检查器初始化失败")
        
        # 4. 检查关键目录
        critical_dirs = ["output", "data", "utils"]
        for dir_name in critical_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists():
                diagnostic_results["components"][f"directory_{dir_name}"] = {
                    "status": "exists",
                    "file_count": len(list(dir_path.glob("*"))) if dir_path.is_dir() else 0
                }
            else:
                diagnostic_results["components"][f"directory_{dir_name}"] = {
                    "status": "missing"
                }
                diagnostic_results["issues"].append(f"关键目录缺失: {dir_name}")
                diagnostic_results["recommendations"].append(f"创建目录: {dir_name}")
        
        # 5. 检查状态文件
        state_files = ["state.json", "history.json", "text_processor_state.json"]
        for filename in state_files:
            file_path = Path("data") / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = json.load(f)
                    diagnostic_results["components"][f"state_file_{filename}"] = {
                        "status": "valid",
                        "size": file_path.stat().st_size
                    }
                except Exception as e:
                    diagnostic_results["components"][f"state_file_{filename}"] = {
                        "status": "corrupted",
                        "error": str(e)
                    }
                    diagnostic_results["issues"].append(f"状态文件损坏: {filename}")
            else:
                diagnostic_results["components"][f"state_file_{filename}"] = {
                    "status": "missing"
                }
                if filename != "text_processor_state.json":  # 这个文件可能不存在是正常的
                    diagnostic_results["issues"].append(f"状态文件缺失: {filename}")
        
        # 生成总体状态
        error_count = sum(1 for comp in diagnostic_results["components"].values() 
                         if comp.get("status") in ["error", "missing", "corrupted"])
        
        diagnostic_results["overall_status"] = "healthy" if error_count == 0 else "degraded"
        diagnostic_results["error_count"] = error_count
        
        # 记录诊断结果
        self.debug_enhancer.record_state_change(
            state_type="system_diagnostic",
            old_value="not_run",
            new_value=diagnostic_results["overall_status"],
            metadata={
                "error_count": error_count,
                "issues_found": len(diagnostic_results["issues"])
            }
        )
        
        return diagnostic_results
    
    def fix_detected_issues(self, dry_run: bool = True) -> Dict[str, Any]:
        """修复检测到的问题"""
        fix_results = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": dry_run,
            "actions": [],
            "success": False
        }
        
        try:
            # 1. 运行一致性检查
            report = self.consistency_checker.generate_report()
            
            # 2. 修复可自动修复的问题
            if report.summary['auto_fixable'] > 0:
                fix_result = self.consistency_checker.fix_issues(dry_run=dry_run)
                
                fix_results["consistency_fix"] = fix_result
                fix_results["actions"].append({
                    "type": "consistency_fix",
                    "attempted": fix_result["attempted_fixes"],
                    "successful": fix_result["successful_fixes"]
                })
            
            # 3. 创建缺失的目录
            missing_dirs = []
            for dir_name in ["output", "data", "utils"]:
                dir_path = Path(dir_name)
                if not dir_path.exists():
                    missing_dirs.append(dir_name)
                    if not dry_run:
                        dir_path.mkdir(exist_ok=True)
                        fix_results["actions"].append({
                            "type": "create_directory",
                            "directory": dir_name,
                            "status": "created"
                        })
            
            if missing_dirs and dry_run:
                fix_results["actions"].append({
                    "type": "create_directory",
                    "directories": missing_dirs,
                    "status": "planned"
                })
            
            # 4. 创建缺失的状态文件
            state_files = ["text_processor_state.json"]
            for filename in state_files:
                file_path = Path("data") / filename
                if not file_path.exists():
                    if not dry_run:
                        try:
                            # 创建初始状态
                            initial_state = {
                                "timestamp": time.time(),
                                "processed_files": [],
                                "last_processed_chapter": 0,
                                "total_processed": 0
                            }
                            
                            with open(file_path, 'w', encoding='utf-8') as f:
                                json.dump(initial_state, f, ensure_ascii=False, indent=2)
                            
                            fix_results["actions"].append({
                                "type": "create_state_file",
                                "file": filename,
                                "status": "created"
                            })
                        except Exception as e:
                            fix_results["actions"].append({
                                "type": "create_state_file",
                                "file": filename,
                                "status": "failed",
                                "error": str(e)
                            })
                    else:
                        fix_results["actions"].append({
                            "type": "create_state_file",
                            "file": filename,
                            "status": "planned"
                        })
            
            fix_results["success"] = True
            
            # 记录修复操作
            self.debug_enhancer.record_state_change(
                state_type="system_fix",
                old_value="issues_present",
                new_value="issues_fixed" if not dry_run else "issues_planned",
                metadata={
                    "dry_run": dry_run,
                    "actions": fix_results["actions"]
                }
            )
            
        except Exception as e:
            fix_results["error"] = str(e)
            fix_results["success"] = False
            
            logger.error(f"修复问题失败: {e}")
            self.debug_enhancer.record_state_change(
                state_type="system_fix",
                old_value="issues_present",
                new_value="failed",
                metadata={"error": str(e)}
            )
        
        return fix_results
    
    def save_diagnostic_report(self, diagnostic_results: Dict[str, Any], 
                              output_path: Optional[Path] = None) -> Path:
        """保存诊断报告"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path("data") / f"diagnostic_report_{timestamp}.json"
        
        # 确保目录存在
        output_path.parent.mkdir(exist_ok=True)
        
        # 保存报告
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(diagnostic_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"诊断报告已保存到: {output_path}")
        return output_path
    
    def print_diagnostic_summary(self, diagnostic_results: Dict[str, Any]):
        """打印诊断摘要"""
        print("\n" + "="*80)
        print("系统诊断摘要")
        print("="*80)
        
        print(f"诊断时间: {diagnostic_results['timestamp']}")
        print(f"总体状态: {diagnostic_results['overall_status'].upper()}")
        print(f"错误数量: {diagnostic_results['error_count']}")
        
        # 组件状态
        print("\n组件状态:")
        for comp_name, comp_info in diagnostic_results["components"].items():
            status = comp_info.get("status", "unknown")
            # 使用ASCII符号避免编码问题
            status_symbol = "[OK]" if status in ["healthy", "exists", "valid"] else "[ERROR]"
            print(f"  {status_symbol} {comp_name}: {status}")
        
        # 问题列表
        if diagnostic_results["issues"]:
            print("\n发现问题:")
            for i, issue in enumerate(diagnostic_results["issues"], 1):
                if isinstance(issue, dict):
                    print(f"  {i}. [{issue.get('severity', 'unknown').upper()}] {issue.get('description', '未知问题')}")
                else:
                    print(f"  {i}. {issue}")
        
        # 建议列表
        if diagnostic_results["recommendations"]:
            print("\n建议操作:")
            for i, recommendation in enumerate(diagnostic_results["recommendations"], 1):
                print(f"  {i}. {recommendation}")
        
        print("="*80)


# 全局集成器实例
_global_integrator: Optional[SystemIntegrator] = None


def get_global_integrator() -> SystemIntegrator:
    """获取全局集成器实例"""
    global _global_integrator
    if _global_integrator is None:
        _global_integrator = SystemIntegrator()
    return _global_integrator


# 便捷函数
def run_system_diagnostic() -> Dict[str, Any]:
    """运行系统诊断"""
    integrator = get_global_integrator()
    return integrator.run_diagnostic()


def fix_system_issues(dry_run: bool = True) -> Dict[str, Any]:
    """修复系统问题"""
    integrator = get_global_integrator()
    return integrator.fix_detected_issues(dry_run)


def check_consistency_and_fix(dry_run: bool = True) -> Dict[str, Any]:
    """检查一致性并修复"""
    # 运行一致性检查
    checker = StateConsistencyChecker()
    report = checker.generate_report()
    
    # 保存报告
    saved_path = checker.save_report(report)
    
    # 如果有可修复的问题，尝试修复
    if report.summary['auto_fixable'] > 0:
        fix_results = checker.fix_issues(dry_run=dry_run)
        return {
            "check_completed": True,
            "issues_found": report.issues_found,
            "auto_fixable": report.summary['auto_fixable'],
            "fix_results": fix_results,
            "report_path": str(saved_path)
        }
    else:
        return {
            "check_completed": True,
            "issues_found": report.issues_found,
            "auto_fixable": 0,
            "message": "没有可自动修复的问题",
            "report_path": str(saved_path)
        }


# 主函数：测试集成工具
def main():
    """测试集成工具"""
    print("测试系统集成工具...")
    
    # 获取集成器
    integrator = get_global_integrator()
    
    # 运行诊断
    print("\n1. 运行系统诊断...")
    diagnostic_results = integrator.run_diagnostic()
    integrator.print_diagnostic_summary(diagnostic_results)
    
    # 保存诊断报告
    saved_path = integrator.save_diagnostic_report(diagnostic_results)
    print(f"\n诊断报告已保存到: {saved_path}")
    
    # 试运行修复
    print("\n2. 试运行修复（不实际执行）...")
    fix_results = integrator.fix_detected_issues(dry_run=True)
    
    if fix_results["success"]:
        print("修复计划生成成功")
        for action in fix_results.get("actions", []):
            print(f"  计划操作: {action}")
    else:
        print(f"修复计划生成失败: {fix_results.get('error', '未知错误')}")
    
    # 检查一致性
    print("\n3. 检查一致性...")
    consistency_results = check_consistency_and_fix(dry_run=True)
    print(f"发现问题: {consistency_results['issues_found']}")
    print(f"可自动修复: {consistency_results['auto_fixable']}")
    
    print("\n测试完成！")


if __name__ == "__main__":
    main()
