"""
调试信息增强模块 - 提供详细的调试信息和追踪功能

核心功能：
1. 增强日志系统，提供更详细的上下文信息
2. 追踪函数调用和参数
3. 记录关键操作的时间戳和调用堆栈
4. 提供调试信息收集和报告功能
5. 支持日志级别动态调整
"""

import os
import json
import logging
import inspect
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
import traceback
from functools import wraps

from .file_tracker import get_global_file_tracker, FileOperationType, record_file_operation

logger = logging.getLogger(__name__)


@dataclass
class DebugContext:
    """调试上下文信息"""
    timestamp: float
    thread_id: int
    process_id: int
    function_name: str
    module_name: str
    file_path: str
    line_number: int
    args: Dict[str, Any] = field(default_factory=dict)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    return_value: Any = None
    exception: Optional[str] = None
    duration_ms: float = 0.0
    call_stack: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['timestamp_iso'] = datetime.fromtimestamp(self.timestamp).isoformat()
        return data


@dataclass
class DebugRecord:
    """调试记录"""
    record_id: str
    context: DebugContext
    operation_type: str  # function_call, file_operation, state_change, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'record_id': self.record_id,
            'context': self.context.to_dict(),
            'operation_type': self.operation_type,
            'metadata': self.metadata
        }


class DebugEnhancer:
    """调试信息增强器"""
    
    def __init__(self, log_level: str = "DEBUG", max_records: int = 1000):
        """
        初始化调试增强器
        
        Args:
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
            max_records: 最大记录数
        """
        self.log_level = getattr(logging, log_level.upper())
        self.max_records = max_records
        self.records: List[DebugRecord] = []
        self.record_counter = 0
        self.lock = threading.RLock()
        
        # 设置日志级别
        self._setup_logging()
        
        # logger.info(f"调试信息增强器初始化完成，日志级别: {log_level}")
        logger.setLevel(logging.CRITICAL)
    
    def _setup_logging(self):
        """设置日志配置（已禁用，避免干扰主日志系统）"""
        pass
    
    def _generate_record_id(self) -> str:
        """生成记录ID"""
        with self.lock:
            self.record_counter += 1
            timestamp = int(time.time() * 1000)
            return f"debug_{timestamp}_{self.record_counter}"
    
    def _get_caller_info(self, depth: int = 2) -> Tuple[str, str, str, int]:
        """获取调用者信息"""
        try:
            frame = inspect.currentframe()
            for _ in range(depth):
                if frame:
                    frame = frame.f_back
            
            if frame:
                info = inspect.getframeinfo(frame)
                # 从文件名提取模块名
                filename = info.filename
                module_name = Path(filename).stem
                
                # 尝试获取模块全名
                try:
                    module = inspect.getmodule(frame)
                    if module and hasattr(module, '__name__'):
                        module_name = module.__name__
                except Exception:
                    pass
                
                return info.function, filename, module_name, info.lineno
        except Exception as e:
            logger.debug(f"获取调用者信息失败: {e}")
        
        return "unknown", "unknown", "unknown", 0
    
    def create_context(self, args: tuple, kwargs: dict, depth: int = 3) -> DebugContext:
        """创建调试上下文"""
        # 获取调用者信息
        function_name, file_path, module_name, line_number = self._get_caller_info(depth)
        
        # 获取调用堆栈（限制深度）
        stack = traceback.extract_stack(limit=10)
        call_stack = [f"{frame.filename}:{frame.lineno} in {frame.name}" for frame in stack[:-depth]]
        
        # 创建上下文
        context = DebugContext(
            timestamp=time.time(),
            thread_id=threading.get_ident(),
            process_id=os.getpid(),
            function_name=function_name,
            module_name=module_name,
            file_path=file_path,
            line_number=line_number,
            args=self._sanitize_args(args),
            kwargs=self._sanitize_kwargs(kwargs),
            call_stack=call_stack
        )
        
        return context
    
    def _sanitize_args(self, args: tuple) -> Dict[str, Any]:
        """清理参数，移除敏感信息"""
        sanitized = {}
        for i, arg in enumerate(args):
            key = f"arg_{i}"
            
            # 处理不同类型的参数
            if isinstance(arg, (str, int, float, bool, type(None))):
                sanitized[key] = arg
            elif isinstance(arg, (list, tuple)):
                sanitized[key] = f"{type(arg).__name__}[{len(arg)}]"
            elif isinstance(arg, dict):
                sanitized[key] = f"dict[{len(arg)}]"
            elif hasattr(arg, '__class__'):
                sanitized[key] = f"{arg.__class__.__name__} object"
            else:
                sanitized[key] = str(type(arg))
        
        return sanitized
    
    def _sanitize_kwargs(self, kwargs: dict) -> Dict[str, Any]:
        """清理关键字参数，移除敏感信息"""
        sanitized = {}
        
        # 敏感关键词（可能包含API密钥、密码等）
        sensitive_keywords = ['key', 'secret', 'password', 'token', 'api_key', 'auth']
        
        for key, value in kwargs.items():
            # 检查是否为敏感关键词
            is_sensitive = any(sensitive in key.lower() for sensitive in sensitive_keywords)
            
            if is_sensitive:
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, (str, int, float, bool, type(None))):
                sanitized[key] = value
            elif isinstance(value, (list, tuple)):
                sanitized[key] = f"{type(value).__name__}[{len(value)}]"
            elif isinstance(value, dict):
                sanitized[key] = f"dict[{len(value)}]"
            elif hasattr(value, '__class__'):
                sanitized[key] = f"{value.__class__.__name__} object"
            else:
                sanitized[key] = str(type(value))
        
        return sanitized
    
    def record_function_call(self, func: Callable) -> Callable:
        """装饰器：记录函数调用"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 创建上下文
            context = self.create_context(args, kwargs, depth=4)
            
            # 记录开始时间
            start_time = time.time()
            
            try:
                # 执行函数
                result = func(*args, **kwargs)
                
                # 更新上下文
                context.duration_ms = (time.time() - start_time) * 1000
                context.return_value = self._sanitize_return_value(result)
                
                # 创建记录
                record = DebugRecord(
                    record_id=self._generate_record_id(),
                    context=context,
                    operation_type='function_call',
                    metadata={
                        'function': func.__name__,
                        'module': func.__module__,
                        'success': True
                    }
                )
                
                # 添加记录
                self.add_record(record)
                
                # 记录日志
                logger.debug(f"函数调用: {func.__name__} - 耗时: {context.duration_ms:.2f}ms - 成功")
                
                return result
                
            except Exception as e:
                # 更新上下文
                context.duration_ms = (time.time() - start_time) * 1000
                context.exception = str(e)
                
                # 创建记录
                record = DebugRecord(
                    record_id=self._generate_record_id(),
                    context=context,
                    operation_type='function_call',
                    metadata={
                        'function': func.__name__,
                        'module': func.__module__,
                        'success': False,
                        'exception_type': type(e).__name__
                    }
                )
                
                # 添加记录
                self.add_record(record)
                
                # 记录日志
                logger.error(f"函数调用: {func.__name__} - 耗时: {context.duration_ms:.2f}ms - 失败: {e}")
                
                raise
        
        return wrapper
    
    def _sanitize_return_value(self, value: Any) -> Any:
        """清理返回值"""
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        elif isinstance(value, (list, tuple)):
            return f"{type(value).__name__}[{len(value)}]"
        elif isinstance(value, dict):
            return f"dict[{len(value)}]"
        elif hasattr(value, '__class__'):
            return f"{value.__class__.__name__} object"
        else:
            return str(type(value))
    
    def add_record(self, record: DebugRecord):
        """添加调试记录"""
        with self.lock:
            self.records.append(record)
            
            # 限制记录数量
            if len(self.records) > self.max_records:
                self.records = self.records[-self.max_records:]
    
    def record_file_operation(self, operation_type: str, file_path: Union[str, Path], 
                             success: bool, metadata: Optional[Dict[str, Any]] = None):
        """记录文件操作"""
        # 创建上下文
        context = self.create_context((), {}, depth=3)
        
        # 创建记录
        record = DebugRecord(
            record_id=self._generate_record_id(),
            context=context,
            operation_type='file_operation',
            metadata={
                'operation': operation_type,
                'file_path': str(file_path),
                'success': success,
                **(metadata or {})
            }
        )
        
        # 添加记录
        self.add_record(record)
        
        # 记录日志
        if success:
            logger.debug(f"文件操作: {operation_type} - {file_path}")
        else:
            logger.warning(f"文件操作失败: {operation_type} - {file_path}")
    
    def record_state_change(self, state_type: str, old_value: Any, new_value: Any, 
                           metadata: Optional[Dict[str, Any]] = None):
        """记录状态变化"""
        # 创建上下文
        context = self.create_context((), {}, depth=3)
        
        # 创建记录
        record = DebugRecord(
            record_id=self._generate_record_id(),
            context=context,
            operation_type='state_change',
            metadata={
                'state_type': state_type,
                'old_value': str(old_value),
                'new_value': str(new_value),
                **(metadata or {})
            }
        )
        
        # 添加记录
        self.add_record(record)
        
        # 记录日志
        logger.info(f"状态变化: {state_type} - {old_value} -> {new_value}")
    
    def get_records(self, filter_type: Optional[str] = None, 
                   limit: Optional[int] = None) -> List[DebugRecord]:
        """获取调试记录"""
        with self.lock:
            records = self.records
            
            # 过滤记录
            if filter_type:
                records = [r for r in records if r.operation_type == filter_type]
            
            # 限制数量
            if limit:
                records = records[-limit:]
            
            return records
    
    def get_summary(self) -> Dict[str, Any]:
        """获取调试摘要"""
        with self.lock:
            total_records = len(self.records)
            
            # 按操作类型统计
            type_counts = {}
            for record in self.records:
                op_type = record.operation_type
                type_counts[op_type] = type_counts.get(op_type, 0) + 1
            
            # 按成功/失败统计
            success_counts = {}
            for record in self.records:
                if 'success' in record.metadata:
                    success = record.metadata['success']
                    success_counts[success] = success_counts.get(success, 0) + 1
            
            # 获取最近记录的时间范围
            if self.records:
                first_time = min(r.context.timestamp for r in self.records)
                last_time = max(r.context.timestamp for r in self.records)
                time_range = last_time - first_time
            else:
                first_time = last_time = time_range = 0
            
            return {
                'total_records': total_records,
                'type_counts': type_counts,
                'success_counts': success_counts,
                'time_range_seconds': time_range,
                'first_record_time': datetime.fromtimestamp(first_time).isoformat() if first_time else None,
                'last_record_time': datetime.fromtimestamp(last_time).isoformat() if last_time else None,
                'memory_usage_mb': len(json.dumps([r.to_dict() for r in self.records])) / (1024 * 1024)
            }
    
    def save_records(self, output_path: Optional[Union[str, Path]] = None) -> Path:
        """保存调试记录到文件（已禁用，避免生成多余JSON文件）"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path("data") / f"debug_records_{timestamp}.json"
        else:
            output_path = Path(output_path)
        # 不实际写入文件，仅返回路径
        # logger.info(f"调试记录已保存到: {output_path}")
        return output_path
    
    def clear_records(self):
        """清空调试记录"""
        with self.lock:
            self.records.clear()
            logger.info("调试记录已清空")
    
    def set_log_level(self, level: str):
        """设置日志级别"""
        self.log_level = getattr(logging, level.upper())
        
        # 更新根日志器级别
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # 更新所有处理器级别
        for handler in root_logger.handlers:
            handler.setLevel(self.log_level)
        
        logger.info(f"日志级别已设置为: {level}")
    
    def print_summary(self):
        """打印调试摘要"""
        summary = self.get_summary()
        
        print("\n" + "="*80)
        print("调试信息摘要")
        print("="*80)
        
        print(f"总记录数: {summary['total_records']}")
        print(f"时间范围: {summary['time_range_seconds']:.2f}秒")
        
        if summary['first_record_time']:
            print(f"最早记录: {summary['first_record_time']}")
        if summary['last_record_time']:
            print(f"最新记录: {summary['last_record_time']}")
        
        print(f"内存使用: {summary['memory_usage_mb']:.2f} MB")
        
        # 操作类型统计
        if summary['type_counts']:
            print("\n操作类型统计:")
            for op_type, count in sorted(summary['type_counts'].items()):
                print(f"  {op_type}: {count}")
        
        # 成功/失败统计
        if summary['success_counts']:
            print("\n成功/失败统计:")
            for success, count in sorted(summary['success_counts'].items()):
                status = "成功" if success else "失败"
                print(f"  {status}: {count}")
        
        print("="*80)


# 全局调试增强器实例
_global_debug_enhancer: Optional[DebugEnhancer] = None


def get_global_debug_enhancer() -> DebugEnhancer:
    """获取全局调试增强器实例"""
    global _global_debug_enhancer
    if _global_debug_enhancer is None:
        _global_debug_enhancer = DebugEnhancer()
    return _global_debug_enhancer


def debug_function(func: Callable) -> Callable:
    """便捷装饰器：调试函数调用"""
    enhancer = get_global_debug_enhancer()
    return enhancer.record_function_call(func)


def record_debug_file_operation(operation_type: str, file_path: Union[str, Path],
                               success: bool, metadata: Optional[Dict[str, Any]] = None):
    """便捷函数：记录文件操作"""
    enhancer = get_global_debug_enhancer()
    enhancer.record_file_operation(operation_type, file_path, success, metadata)


def record_debug_state_change(state_type: str, old_value: Any, new_value: Any,
                             metadata: Optional[Dict[str, Any]] = None):
    """便捷函数：记录状态变化"""
    enhancer = get_global_debug_enhancer()
    enhancer.record_state_change(state_type, old_value, new_value, metadata)


def save_debug_records(output_path: Optional[Union[str, Path]] = None) -> str:
    """便捷函数：保存调试记录"""
    enhancer = get_global_debug_enhancer()
    saved_path = enhancer.save_records(output_path)
    return str(saved_path)


def get_debug_summary() -> Dict[str, Any]:
    """便捷函数：获取调试摘要"""
    enhancer = get_global_debug_enhancer()
    return enhancer.get_summary()


def print_debug_summary():
    """便捷函数：打印调试摘要"""
    enhancer = get_global_debug_enhancer()
    enhancer.print_summary()


def set_debug_log_level(level: str):
    """便捷函数：设置调试日志级别"""
    enhancer = get_global_debug_enhancer()
    enhancer.set_log_level(level)


# 集成文件追踪器的增强版本
class EnhancedFileTracker:
    """增强的文件追踪器，结合调试信息"""
    
    def __init__(self):
        self.debug_enhancer = get_global_debug_enhancer()
        self.file_tracker = get_global_file_tracker()
    
    def record_operation(self, operation_type: FileOperationType, file_path: Union[str, Path],
                        success: bool, metadata: Optional[Dict[str, Any]] = None):
        """记录文件操作（增强版本）"""
        # 记录到文件追踪器
        self.file_tracker.record_operation(operation_type, file_path, success, metadata)
        
        # 记录到调试增强器
        self.debug_enhancer.record_file_operation(
            operation_type.value, file_path, success, metadata
        )
        
        # 额外记录详细上下文
        if operation_type in [FileOperationType.DELETE, FileOperationType.RENAME]:
            # 对于删除和重命名操作，记录更多信息
            try:
                file_path_obj = Path(file_path)
                if file_path_obj.exists():
                    stat = file_path_obj.stat()
                    extra_metadata = {
                        'file_size': stat.st_size,
                        'file_mtime': stat.st_mtime,
                        'file_exists': True
                    }
                else:
                    extra_metadata = {'file_exists': False}
                
                if metadata:
                    metadata.update(extra_metadata)
                else:
                    metadata = extra_metadata
                
                # 记录详细操作
                self.debug_enhancer.record_state_change(
                    state_type='file_system',
                    old_value=f"文件存在: {file_path_obj.exists()}",
                    new_value=f"操作: {operation_type.value}",
                    metadata=metadata
                )
            except Exception as e:
                logger.warning(f"无法获取文件详细信息 {file_path}: {e}")
    
    def get_operations(self, filter_type: Optional[FileOperationType] = None,
                      limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取文件操作记录"""
        return self.file_tracker.get_operations(filter_type, limit)
    
    def save_operations(self, output_path: Optional[Union[str, Path]] = None) -> Path:
        """保存文件操作记录"""
        return self.file_tracker.save_operations(output_path)


# 创建全局增强文件追踪器实例
_global_enhanced_file_tracker: Optional[EnhancedFileTracker] = None


def get_global_enhanced_file_tracker() -> EnhancedFileTracker:
    """获取全局增强文件追踪器实例"""
    global _global_enhanced_file_tracker
    if _global_enhanced_file_tracker is None:
        _global_enhanced_file_tracker = EnhancedFileTracker()
    return _global_enhanced_file_tracker


def record_enhanced_file_operation(operation_type: FileOperationType,
                                  file_path: Union[str, Path],
                                  success: bool,
                                  metadata: Optional[Dict[str, Any]] = None):
    """便捷函数：记录增强的文件操作"""
    tracker = get_global_enhanced_file_tracker()
    tracker.record_operation(operation_type, file_path, success, metadata)


# 主函数：测试调试增强器
def main():
    """测试调试增强器"""
    print("测试调试信息增强模块...")
    
    # 获取调试增强器
    enhancer = get_global_debug_enhancer()
    
    # 测试记录各种操作
    enhancer.record_file_operation("create", "test.txt", True)
    enhancer.record_file_operation("delete", "test.txt", False, {"reason": "file_not_found"})
    enhancer.record_state_change("chapter", 42, 43, {"trigger": "auto_increment"})
    
    # 测试装饰器
    @debug_function
    def test_function(x, y, secret_key="***"):
        """测试函数"""
        time.sleep(0.01)
        return x + y
    
    # 调用测试函数
    try:
        result = test_function(10, 20, secret_key="my_secret")
        print(f"测试函数结果: {result}")
    except Exception as e:
        print(f"测试函数异常: {e}")
    
    # 打印摘要
    enhancer.print_summary()
    
    # 保存记录
    saved_path = enhancer.save_records()
    print(f"调试记录已保存到: {saved_path}")
    
    print("测试完成！")


if __name__ == "__main__":
    main()
