"""
文件锁工具 - 提供跨平台的文件锁机制
防止多个进程同时读写同一文件导致数据损坏
"""

import os
import time
import logging
import threading
from pathlib import Path
from typing import Optional, ContextManager
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class FileLock:
    """
    跨平台文件锁实现
    
    使用文件锁机制确保同一时间只有一个进程/线程可以访问文件
    支持超时和重试机制
    """
    
    def __init__(self, lock_file: str, timeout: float = 30.0, retry_interval: float = 0.1):
        """
        初始化文件锁
        
        Args:
            lock_file: 锁文件路径
            timeout: 获取锁的超时时间（秒）
            retry_interval: 重试间隔（秒）
        """
        self.lock_file = Path(lock_file)
        self.timeout = timeout
        self.retry_interval = retry_interval
        self._lock_acquired = False
        self._thread_lock = threading.RLock()  # 线程级锁，防止同一进程内竞争
        
    def acquire(self, blocking: bool = True) -> bool:
        """
        获取文件锁
        
        Args:
            blocking: 是否阻塞等待
            
        Returns:
            是否成功获取锁
        """
        with self._thread_lock:
            if self._lock_acquired:
                return True  # 已经持有锁
            
            start_time = time.time()
            
            while True:
                try:
                    # 尝试创建锁文件（原子操作）
                    fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                    os.close(fd)
                    
                    # 写入当前进程信息（用于调试）
                    with open(self.lock_file, 'w') as f:
                        import socket
                        import getpass
                        f.write(f"pid: {os.getpid()}\n")
                        f.write(f"host: {socket.gethostname()}\n")
                        f.write(f"user: {getpass.getuser()}\n")
                        f.write(f"time: {time.time()}\n")
                    
                    self._lock_acquired = True
                    logger.debug(f"文件锁已获取: {self.lock_file}")
                    return True
                    
                except (OSError, IOError):
                    # 锁文件已存在，表示其他进程持有锁
                    if not blocking:
                        return False
                    
                    # 检查是否超时
                    if time.time() - start_time > self.timeout:
                        logger.warning(f"获取文件锁超时: {self.lock_file} (超时时间: {self.timeout}s)")
                        return False
                    
                    # 检查锁文件是否过期（防止死锁）
                    if self._is_lock_stale():
                        logger.warning(f"检测到过期的锁文件，强制清除: {self.lock_file}")
                        self._force_release()
                        continue
                    
                    # 等待后重试
                    time.sleep(self.retry_interval)
    
    def release(self) -> None:
        """释放文件锁"""
        with self._thread_lock:
            if not self._lock_acquired:
                return
            
            try:
                if self.lock_file.exists():
                    os.unlink(self.lock_file)
                self._lock_acquired = False
                logger.debug(f"文件锁已释放: {self.lock_file}")
            except (OSError, IOError) as e:
                logger.warning(f"释放文件锁失败: {self.lock_file}, 错误: {e}")
    
    def _is_lock_stale(self, max_age: float = 300.0) -> bool:
        """
        检查锁文件是否过期
        
        Args:
            max_age: 最大年龄（秒），超过此时间认为锁已过期
            
        Returns:
            锁是否过期
        """
        if not self.lock_file.exists():
            return False
        
        try:
            # 读取锁文件中的时间戳
            with open(self.lock_file, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith('time:'):
                        lock_time = float(line.split(':')[1].strip())
                        if time.time() - lock_time > max_age:
                            return True
        except (ValueError, IOError, IndexError):
            pass
        
        # 如果无法读取时间，检查文件修改时间
        try:
            file_age = time.time() - self.lock_file.stat().st_mtime
            return file_age > max_age
        except (OSError, IOError):
            return False
    
    def _force_release(self) -> None:
        """强制释放锁（清除锁文件）"""
        try:
            if self.lock_file.exists():
                os.unlink(self.lock_file)
        except (OSError, IOError) as e:
            logger.warning(f"强制清除锁文件失败: {self.lock_file}, 错误: {e}")
    
    def __enter__(self) -> 'FileLock':
        """上下文管理器入口"""
        self.acquire(blocking=True)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器出口"""
        self.release()
    
    @property
    def locked(self) -> bool:
        """检查是否持有锁"""
        return self._lock_acquired


@contextmanager
def file_lock_context(lock_file: str, timeout: float = 30.0) -> ContextManager[FileLock]:
    """
    文件锁上下文管理器
    
    Args:
        lock_file: 锁文件路径
        timeout: 获取锁的超时时间
        
    Yields:
        FileLock实例
    """
    lock = FileLock(lock_file, timeout)
    try:
        if lock.acquire(blocking=True):
            yield lock
        else:
            raise TimeoutError(f"获取文件锁超时: {lock_file}")
    finally:
        lock.release()


def with_file_lock(lock_file: str, timeout: float = 30.0):
    """
    文件锁装饰器
    
    Args:
        lock_file: 锁文件路径
        timeout: 获取锁的超时时间
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with file_lock_context(lock_file, timeout):
                return func(*args, **kwargs)
        return wrapper
    return decorator


class AtomicFileWriter:
    """
    原子文件写入器
    
    确保文件写入的原子性，防止写入过程中被其他进程读取到不完整数据
    """
    
    def __init__(self, file_path: str, lock_timeout: float = 30.0):
        """
        初始化原子文件写入器
        
        Args:
            file_path: 目标文件路径
            lock_timeout: 文件锁超时时间
        """
        self.file_path = Path(file_path)
        self.temp_file = self.file_path.with_suffix('.tmp')
        self.lock_file = self.file_path.with_suffix('.lock')
        self.lock_timeout = lock_timeout
    
    @contextmanager
    def write_context(self):
        """
        原子写入上下文管理器
        
        使用方式:
            with atomic_writer.write_context() as f:
                f.write("content")
        """
        with file_lock_context(str(self.lock_file), self.lock_timeout):
            try:
                # 写入临时文件
                with open(self.temp_file, 'w', encoding='utf-8') as f:
                    yield f
                
                # 原子重命名（在支持原子重命名的系统上）
                self.temp_file.replace(self.file_path)
                logger.debug(f"原子写入完成: {self.file_path}")
                
            except Exception as e:
                # 清理临时文件
                if self.temp_file.exists():
                    try:
                        self.temp_file.unlink()
                    except OSError:
                        pass
                raise e
    
    def write_json(self, data, indent: int = 2, ensure_ascii: bool = False):
        """
        原子写入JSON数据
        
        Args:
            data: 要写入的数据
            indent: JSON缩进
            ensure_ascii: 是否确保ASCII编码
        """
        import json
        with self.write_context() as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
    
    def write_text(self, text: str):
        """
        原子写入文本数据
        
        Args:
            text: 要写入的文本
        """
        with self.write_context() as f:
            f.write(text)