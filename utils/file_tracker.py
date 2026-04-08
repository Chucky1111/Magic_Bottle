"""
文件操作追踪模块 - 监控所有文件系统操作

核心功能：
1. 记录所有文件操作（创建、读取、写入、删除、重命名）
2. 追踪操作时间戳、进程ID、调用堆栈
3. 检测文件操作冲突和竞争条件
4. 提供操作审计和调试信息
"""

import os
import time
import json
import logging
import threading
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class FileOperationType(Enum):
    """文件操作类型枚举"""
    READ = "read"
    WRITE = "write"
    CREATE = "create"
    DELETE = "delete"
    RENAME = "rename"
    MOVE = "move"
    COPY = "copy"
    OPEN = "open"
    CLOSE = "close"


@dataclass
class FileOperationRecord:
    """文件操作记录"""
    operation_id: str
    operation_type: FileOperationType
    file_path: Path
    timestamp: float
    process_id: int
    thread_id: int
    caller_stack: List[str]
    success: bool
    error_message: Optional[str] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    old_path: Optional[Path] = None
    new_path: Optional[Path] = None
    content_hash: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['operation_type'] = self.operation_type.value
        data['file_path'] = str(self.file_path)
        data['old_path'] = str(self.old_path) if self.old_path else None
        data['new_path'] = str(self.new_path) if self.new_path else None
        data['timestamp_iso'] = datetime.fromtimestamp(self.timestamp).isoformat()
        return data


class FileTracker:
    """文件操作追踪器"""
    
    def __init__(self, log_file: Optional[Path] = None, enabled: bool = True):
        """
        初始化文件追踪器
        
        Args:
            log_file: 日志文件路径，如果为None则不保存到文件
            enabled: 是否启用追踪
        """
        self.enabled = enabled
        self.log_file = Path(log_file) if log_file else None
        self.operations: List[FileOperationRecord] = []
        self.lock = threading.RLock()
        self.operation_counter = 0
        
        # 文件锁追踪
        self.file_locks: Dict[Path, threading.Lock] = {}
        self.lock_tracker: Dict[Path, Dict[str, Any]] = {}
        
        # 配置
        self.max_operations_in_memory = 10000
        self.auto_save_interval = 100
        
        # 确保日志目录存在
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"文件操作追踪器初始化完成，启用状态: {enabled}")
    
    def _generate_operation_id(self) -> str:
        """生成操作ID"""
        with self.lock:
            self.operation_counter += 1
            timestamp = int(time.time() * 1000)
            return f"op_{timestamp}_{self.operation_counter}_{os.getpid()}"
    
    def _get_caller_stack(self, depth: int = 5) -> List[str]:
        """获取调用堆栈"""
        stack = []
        for frame_info in traceback.extract_stack()[:-depth]:
            filename = Path(frame_info.filename).name
            stack.append(f"{filename}:{frame_info.lineno} ({frame_info.name})")
        return stack
    
    def _calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """计算文件哈希"""
        try:
            if not file_path.exists():
                return None
            
            hash_obj = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception:
            return None
    
    def _calculate_content_hash(self, content: Union[str, bytes]) -> Optional[str]:
        """计算内容哈希"""
        try:
            if isinstance(content, str):
                content = content.encode('utf-8')
            return hashlib.md5(content).hexdigest()
        except Exception:
            return None
    
    def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """获取文件信息"""
        try:
            stat = file_path.stat()
            return {
                'size': stat.st_size,
                'mtime': stat.st_mtime,
                'ctime': stat.st_ctime,
                'exists': file_path.exists()
            }
        except Exception:
            return {'exists': False}
    
    def record_operation(
        self,
        operation_type: FileOperationType,
        file_path: Union[str, Path],
        success: bool = True,
        error_message: Optional[str] = None,
        old_path: Optional[Union[str, Path]] = None,
        new_path: Optional[Union[str, Path]] = None,
        content: Optional[Union[str, bytes]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FileOperationRecord:
        """
        记录文件操作
        
        Args:
            operation_type: 操作类型
            file_path: 文件路径
            success: 是否成功
            error_message: 错误信息
            old_path: 旧路径（用于重命名/移动）
            new_path: 新路径（用于重命名/移动）
            content: 写入的内容
            metadata: 额外元数据
        
        Returns:
            操作记录
        """
        if not self.enabled:
            return None
        
        file_path = Path(file_path)
        old_path = Path(old_path) if old_path else None
        new_path = Path(new_path) if new_path else None
        
        # 获取文件信息
        file_info = self._get_file_info(file_path)
        file_size = file_info.get('size') if file_info['exists'] else None
        file_hash = self._calculate_file_hash(file_path) if file_info['exists'] else None
        
        # 计算内容哈希
        content_hash = None
        if content is not None:
            content_hash = self._calculate_content_hash(content)
        
        # 创建操作记录
        record = FileOperationRecord(
            operation_id=self._generate_operation_id(),
            operation_type=operation_type,
            file_path=file_path,
            timestamp=time.time(),
            process_id=os.getpid(),
            thread_id=threading.get_ident(),
            caller_stack=self._get_caller_stack(),
            success=success,
            error_message=error_message,
            file_size=file_size,
            file_hash=file_hash,
            old_path=old_path,
            new_path=new_path,
            content_hash=content_hash,
            metadata=metadata or {}
        )
        
        # 添加到内存记录
        with self.lock:
            self.operations.append(record)
            
            # 自动保存到文件
            if self.log_file and len(self.operations) % self.auto_save_interval == 0:
                self._save_to_file()
            
            # 限制内存中的记录数量
            if len(self.operations) > self.max_operations_in_memory:
                self.operations = self.operations[-self.max_operations_in_memory:]
        
        # 记录到日志
        log_level = logging.INFO if success else logging.ERROR
        logger.log(log_level, 
                  f"文件操作: {operation_type.value} {file_path} "
                  f"{'成功' if success else '失败'} (ID: {record.operation_id})")
        
        return record
    
    def _save_to_file(self) -> bool:
        """保存操作记录到文件"""
        try:
            with self.lock:
                if not self.log_file:
                    return False
                
                # 转换为可序列化的字典
                records = [op.to_dict() for op in self.operations]
                
                # 写入文件
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'timestamp': time.time(),
                        'total_operations': len(records),
                        'operations': records
                    }, f, ensure_ascii=False, indent=2)
                
                logger.debug(f"保存了 {len(records)} 个操作记录到 {self.log_file}")
                return True
                
        except Exception as e:
            logger.error(f"保存操作记录失败: {e}")
            return False
    
    def load_from_file(self) -> bool:
        """从文件加载操作记录"""
        try:
            with self.lock:
                if not self.log_file or not self.log_file.exists():
                    return False
                
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 转换回操作记录对象
                self.operations = []
                for op_data in data.get('operations', []):
                    record = FileOperationRecord(
                        operation_id=op_data['operation_id'],
                        operation_type=FileOperationType(op_data['operation_type']),
                        file_path=Path(op_data['file_path']),
                        timestamp=op_data['timestamp'],
                        process_id=op_data['process_id'],
                        thread_id=op_data['thread_id'],
                        caller_stack=op_data['caller_stack'],
                        success=op_data['success'],
                        error_message=op_data.get('error_message'),
                        file_size=op_data.get('file_size'),
                        file_hash=op_data.get('file_hash'),
                        old_path=Path(op_data['old_path']) if op_data.get('old_path') else None,
                        new_path=Path(op_data['new_path']) if op_data.get('new_path') else None,
                        content_hash=op_data.get('content_hash'),
                        metadata=op_data.get('metadata', {})
                    )
                    self.operations.append(record)
                
                logger.info(f"从 {self.log_file} 加载了 {len(self.operations)} 个操作记录")
                return True
                
        except Exception as e:
            logger.error(f"加载操作记录失败: {e}")
            return False
    
    def get_operations(
        self,
        file_path: Optional[Union[str, Path]] = None,
        operation_type: Optional[FileOperationType] = None,
        limit: Optional[int] = None,
        since: Optional[float] = None
    ) -> List[FileOperationRecord]:
        """
        获取操作记录
        
        Args:
            file_path: 过滤特定文件
            operation_type: 过滤特定操作类型
            limit: 限制返回数量
            since: 过滤时间戳之后的操作
        
        Returns:
            操作记录列表
        """
        with self.lock:
            filtered = self.operations.copy()
            
            if file_path:
                file_path = Path(file_path)
                filtered = [op for op in filtered if op.file_path == file_path]
            
            if operation_type:
                filtered = [op for op in filtered if op.operation_type == operation_type]
            
            if since:
                filtered = [op for op in filtered if op.timestamp >= since]
            
            if limit:
                filtered = filtered[-limit:]
            
            return filtered
    
    def get_file_history(self, file_path: Union[str, Path]) -> List[FileOperationRecord]:
        """获取文件的完整操作历史"""
        return self.get_operations(file_path=file_path)
    
    def detect_conflicts(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        检测文件操作冲突
        
        Args:
            file_path: 文件路径
        
        Returns:
            冲突列表
        """
        file_path = Path(file_path)
        operations = self.get_file_history(file_path)
        
        conflicts = []
        for i in range(len(operations) - 1):
            op1 = operations[i]
            op2 = operations[i + 1]
            
            # 检测写入-写入冲突
            if (op1.operation_type == FileOperationType.WRITE and 
                op2.operation_type == FileOperationType.WRITE and
                abs(op1.timestamp - op2.timestamp) < 1.0):  # 1秒内
                conflicts.append({
                    'type': 'write_write_conflict',
                    'operation1': op1.operation_id,
                    'operation2': op2.operation_id,
                    'timestamp1': op1.timestamp,
                    'timestamp2': op2.timestamp,
                    'time_diff': abs(op1.timestamp - op2.timestamp),
                    'description': f"快速连续写入冲突: {op1.operation_id} 和 {op2.operation_id}"
                })
            
            # 检测删除后写入
            if (op1.operation_type == FileOperationType.DELETE and 
                op2.operation_type == FileOperationType.WRITE and
                abs(op1.timestamp - op2.timestamp) < 0.5):  # 0.5秒内
                conflicts.append({
                    'type': 'delete_write_conflict',
                    'operation1': op1.operation_id,
                    'operation2': op2.operation_id,
                    'timestamp1': op1.timestamp,
                    'timestamp2': op2.timestamp,
                    'time_diff': abs(op1.timestamp - op2.timestamp),
                    'description': f"删除后立即写入: {op1.operation_id} 删除, {op2.operation_id} 写入"
                })
        
        return conflicts
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            total = len(self.operations)
            successful = sum(1 for op in self.operations if op.success)
            failed = total - successful
            
            # 按操作类型统计
            type_counts = {}
            for op in self.operations:
                type_name = op.operation_type.value
                type_counts[type_name] = type_counts.get(type_name, 0) + 1
            
            # 按文件统计
            file_counts = {}
            for op in self.operations:
                file_str = str(op.file_path)
                file_counts[file_str] = file_counts.get(file_str, 0) + 1
            
            return {
                'total_operations': total,
                'successful_operations': successful,
                'failed_operations': failed,
                'success_rate': successful / total if total > 0 else 0,
                'operation_type_counts': type_counts,
                'file_operation_counts': dict(sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
                'time_range': {
                    'start': min(op.timestamp for op in self.operations) if self.operations else None,
                    'end': max(op.timestamp for op in self.operations) if self.operations else None
                }
            }
    
    def clear(self) -> None:
        """清空操作记录"""
        with self.lock:
            self.operations.clear()
            logger.info("操作记录已清空")
    
    @contextmanager
    def track_operation(self, operation_type: FileOperationType, file_path: Union[str, Path], **kwargs):
        """
        跟踪操作的上下文管理器
        
        Args:
            operation_type: 操作类型
            file_path: 文件路径
            **kwargs: 传递给record_operation的额外参数
        """
        if not self.enabled:
            yield
            return
        
        file_path = Path(file_path)
        success = False
        error_message = None
        
        try:
            yield
            success = True
        except Exception as e:
            error_message = str(e)
            raise
        finally:
            self.record_operation(
                operation_type=operation_type,
                file_path=file_path,
                success=success,
                error_message=error_message,
                **kwargs
            )
    
    def wrap_file_operation(self, func: Callable) -> Callable:
        """
        包装文件操作函数，自动追踪
        
        Args:
            func: 要包装的函数
        
        Returns:
            包装后的函数
        """
        if not self.enabled:
            return func
        
        def wrapped(*args, **kwargs):
            # 尝试从参数中推断文件路径和操作类型
            file_path = None
            operation_type = None
            
            # 检查参数
            for arg in args:
                if isinstance(arg, (str, Path)):
                    potential_path = Path(arg)
                    if potential_path.suffix:  # 有后缀，可能是文件
                        file_path = potential_path
                        break
            
            # 检查关键字参数
            if not file_path:
                for key, value in kwargs.items():
                    if 'file' in key.lower() or 'path' in key.lower():
                        if isinstance(value, (str, Path)):
                            file_path = Path(value)
                            break
            
            # 根据函数名推断操作类型
            func_name = func.__name__.lower()
            if 'read' in func_name:
                operation_type = FileOperationType.READ
            elif 'write' in func_name:
                operation_type = FileOperationType.WRITE
            elif 'delete' in func_name or 'remove' in func_name:
                operation_type = FileOperationType.DELETE
            elif 'create' in func_name:
                operation_type = FileOperationType.CREATE
            elif 'rename' in func_name or 'move' in func_name:
                operation_type = FileOperationType.RENAME
            elif 'copy' in func_name:
                operation_type = FileOperationType.COPY
            else:
                operation_type = FileOperationType.OPEN
            
            success = False
            error_message = None
            result = None
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error_message = str(e)
                raise
            finally:
                if file_path and operation_type:
                    self.record_operation(
                        operation_type=operation_type,
                        file_path=file_path,
                        success=success,
                        error_message=error_message,
                        metadata={
                            'function': func.__name__,
                            'args': str(args),
                            'kwargs': str(kwargs)
                        }
                    )
        
        return wrapped


# 全局文件追踪器实例
_global_file_tracker: Optional[FileTracker] = None


def get_global_file_tracker() -> FileTracker:
    """获取全局文件追踪器实例"""
    global _global_file_tracker
    if _global_file_tracker is None:
        _global_file_tracker = FileTracker(
            log_file=Path("data/file_operations_log.json"),
            enabled=True
        )
    return _global_file_tracker


def enable_file_tracking(enabled: bool = True) -> None:
    """启用或禁用文件追踪"""
    tracker = get_global_file_tracker()
    tracker.enabled = enabled
    logger.info(f"文件追踪已{'启用' if enabled else '禁用'}")


def record_file_operation(
    operation_type: FileOperationType,
    file_path: Union[str, Path],
    **kwargs
) -> Optional[FileOperationRecord]:
    """记录文件操作（便捷函数）"""
    tracker = get_global_file_tracker()
    return tracker.record_operation(operation_type, file_path, **kwargs)


@contextmanager
def track_file_operation(operation_type: FileOperationType, file_path: Union[str, Path], **kwargs):
    """跟踪文件操作的上下文管理器（便捷函数）"""
    tracker = get_global_file_tracker()
    with tracker.track_operation(operation_type, file_path, **kwargs):
        yield


def get_file_operations(**kwargs) -> List[FileOperationRecord]:
    """获取文件操作记录（便捷函数）"""
    tracker = get_global_file_tracker()
    return tracker.get_operations(**kwargs)


def analyze_file_conflicts(directory: Union[str, Path] = "output") -> Dict[str, Any]:
    """
    分析目录中的文件冲突
    
    Args:
        directory: 要分析的目录
    
    Returns:
        冲突分析报告
    """
    directory = Path(directory)
    tracker = get_global_file_tracker()
    
    # 获取目录中的所有文件
    files = list(directory.glob("*.txt"))
    
    conflicts_report = {
        'directory': str(directory),
        'total_files': len(files),
        'duplicate_files': [],
        'conflict_operations': [],
        'statistics': tracker.get_statistics()
    }
    
    # 检测重复文件（基于文件名模式）
    file_groups = {}
    for file_path in files:
        # 提取章节号
        match = re.search(r'第(\d+)章', file_path.name)
        if match:
            chapter_num = int(match.group(1))
            if chapter_num not in file_groups:
                file_groups[chapter_num] = []
            file_groups[chapter_num].append(file_path)
    
    # 找出有重复章节号的文件
    for chapter_num, file_list in file_groups.items():
        if len(file_list) > 1:
            conflicts_report['duplicate_files'].append({
                'chapter': chapter_num,
                'files': [str(f) for f in file_list],
                'count': len(file_list)
            })
    
    # 检测文件操作冲突
    for file_path in files:
        conflicts = tracker.detect_conflicts(file_path)
        if conflicts:
            conflicts_report['conflict_operations'].append({
                'file': str(file_path),
                'conflicts': conflicts
            })
    
    return conflicts_report


def generate_debug_report() -> Dict[str, Any]:
    """生成调试报告"""
    tracker = get_global_file_tracker()
    
    report = {
        'timestamp': time.time(),
        'timestamp_iso': datetime.now().isoformat(),
        'tracker_enabled': tracker.enabled,
        'statistics': tracker.get_statistics(),
        'recent_operations': [
            op.to_dict() for op in tracker.get_operations(limit=20)
        ],
        'output_directory_analysis': analyze_file_conflicts("output")
    }
    
    return report


def save_debug_report(file_path: Union[str, Path] = "data/debug_report.json") -> bool:
    """保存调试报告到文件"""
    try:
        report = generate_debug_report()
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"调试报告已保存到: {file_path}")
        return True
    except Exception as e:
        logger.error(f"保存调试报告失败: {e}")
        return False


# 导入正则表达式模块
import re


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 测试文件追踪器
    tracker = FileTracker(log_file="test_file_operations.json")
    
    # 测试记录操作
    test_file = Path("test_file.txt")
    
    # 记录创建操作
    with tracker.track_operation(FileOperationType.CREATE, test_file):
        test_file.write_text("测试内容")
    
    # 记录读取操作
    with tracker.track_operation(FileOperationType.READ, test_file):
        content = test_file.read_text()
    
    # 记录写入操作
    with tracker.track_operation(FileOperationType.WRITE, test_file):
        test_file.write_text("更新后的内容")
    
    # 记录删除操作
    with tracker.track_operation(FileOperationType.DELETE, test_file):
        test_file.unlink(missing_ok=True)
    
    # 获取统计信息
    stats = tracker.get_statistics()
    print(f"操作统计: {stats}")
    
    # 保存到文件
    tracker._save_to_file()
    
    print("文件追踪器测试完成")
