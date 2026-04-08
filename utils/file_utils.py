"""
文件操作工具模块 - 提供统一的文件操作功能

核心功能：
1. 安全的文件读写操作
2. JSON文件操作
3. 目录管理
4. 文件锁和并发控制
5. 文件验证和清理
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, BinaryIO, TextIO
from contextlib import contextmanager
import logging

from .error_handler import with_error_handling, safe_execute, StorageError

logger = logging.getLogger(__name__)


@with_error_handling(default_return=None, log_level="ERROR")
def read_text_file(filepath: Union[str, Path], encoding: str = "utf-8") -> Optional[str]:
    """
    安全读取文本文件
    
    Args:
        filepath: 文件路径
        encoding: 文件编码
    
    Returns:
        文件内容字符串，如果读取失败则返回None
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        logger.warning(f"文件不存在: {filepath}")
        return None
    
    if not filepath.is_file():
        logger.warning(f"路径不是文件: {filepath}")
        return None
    
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        logger.error(f"文件编码错误: {filepath}")
        # 尝试其他常见编码
        for alt_encoding in ['gbk', 'gb2312', 'latin-1']:
            try:
                with open(filepath, 'r', encoding=alt_encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        raise StorageError(f"无法解码文件: {filepath}")


@with_error_handling(default_return=False, log_level="ERROR")
def write_text_file(
    filepath: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
    ensure_dir: bool = True
) -> bool:
    """
    安全写入文本文件
    
    Args:
        filepath: 文件路径
        content: 要写入的内容
        encoding: 文件编码
        ensure_dir: 是否确保目录存在
    
    Returns:
        是否成功写入
    """
    filepath = Path(filepath)
    
    if ensure_dir:
        filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # 使用临时文件实现原子写入
    temp_file = None
    try:
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            encoding=encoding,
            delete=False,
            dir=filepath.parent,
            prefix=f".{filepath.name}.",
            suffix=".tmp"
        )
        
        # 写入内容
        temp_file.write(content)
        temp_file.flush()
        temp_file.close()
        
        # 原子性地重命名临时文件为目标文件
        os.replace(temp_file.name, filepath)
        
        logger.debug(f"文件已写入: {filepath} ({len(content)} 字符)")
        return True
        
    except Exception as e:
        # 清理临时文件
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        raise StorageError(f"写入文件失败: {filepath}", details={"error": str(e)})
    
    finally:
        if temp_file and not temp_file.closed:
            temp_file.close()


@with_error_handling(default_return=None, log_level="ERROR")
def read_json_file(filepath: Union[str, Path], encoding: str = "utf-8") -> Optional[Any]:
    """
    安全读取JSON文件
    
    Args:
        filepath: 文件路径
        encoding: 文件编码
    
    Returns:
        JSON解析后的数据，如果读取失败则返回None
    """
    content = read_text_file(filepath, encoding)
    if content is None:
        return None
    
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误: {filepath} - {e}")
        raise StorageError(f"JSON解析失败: {filepath}", details={"error": str(e)})


@with_error_handling(default_return=False, log_level="ERROR")
def write_json_file(
    filepath: Union[str, Path],
    data: Any,
    encoding: str = "utf-8",
    indent: int = 2,
    ensure_ascii: bool = False,
    ensure_dir: bool = True
) -> bool:
    """
    安全写入JSON文件
    
    Args:
        filepath: 文件路径
        data: 要写入的数据
        encoding: 文件编码
        indent: JSON缩进
        ensure_ascii: 是否确保ASCII编码
        ensure_dir: 是否确保目录存在
    
    Returns:
        是否成功写入
    """
    try:
        json_str = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
        return write_text_file(filepath, json_str, encoding, ensure_dir)
    except (TypeError, ValueError) as e:
        logger.error(f"JSON序列化错误: {filepath} - {e}")
        raise StorageError(f"JSON序列化失败: {filepath}", details={"error": str(e)})


@with_error_handling(default_return=False, log_level="ERROR")
def ensure_directory(dirpath: Union[str, Path]) -> bool:
    """
    确保目录存在
    
    Args:
        dirpath: 目录路径
    
    Returns:
        是否成功创建或确认目录存在
    """
    dirpath = Path(dirpath)
    
    if dirpath.exists():
        if not dirpath.is_dir():
            logger.error(f"路径已存在但不是目录: {dirpath}")
            return False
        return True
    
    try:
        dirpath.mkdir(parents=True, exist_ok=True)
        logger.debug(f"目录已创建: {dirpath}")
        return True
    except Exception as e:
        logger.error(f"创建目录失败: {dirpath} - {e}")
        return False


@with_error_handling(default_return=False, log_level="ERROR")
def copy_file(
    src: Union[str, Path],
    dst: Union[str, Path],
    overwrite: bool = False
) -> bool:
    """
    安全复制文件
    
    Args:
        src: 源文件路径
        dst: 目标文件路径
        overwrite: 是否覆盖已存在的文件
    
    Returns:
        是否成功复制
    """
    src_path = Path(src)
    dst_path = Path(dst)
    
    if not src_path.exists():
        logger.error(f"源文件不存在: {src_path}")
        return False
    
    if not src_path.is_file():
        logger.error(f"源路径不是文件: {src_path}")
        return False
    
    if dst_path.exists():
        if overwrite:
            logger.warning(f"目标文件已存在，将被覆盖: {dst_path}")
        else:
            logger.error(f"目标文件已存在: {dst_path}")
            return False
    
    # 确保目标目录存在
    ensure_directory(dst_path.parent)
    
    try:
        shutil.copy2(src_path, dst_path)
        logger.debug(f"文件已复制: {src_path} -> {dst_path}")
        return True
    except Exception as e:
        logger.error(f"复制文件失败: {src_path} -> {dst_path} - {e}")
        return False


@with_error_handling(default_return=False, log_level="ERROR")
def delete_file(filepath: Union[str, Path], missing_ok: bool = True) -> bool:
    """
    安全删除文件
    
    Args:
        filepath: 文件路径
        missing_ok: 如果文件不存在是否视为成功
    
    Returns:
        是否成功删除
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        if missing_ok:
            return True
        else:
            logger.warning(f"文件不存在: {filepath}")
            return False
    
    if not filepath.is_file():
        logger.error(f"路径不是文件: {filepath}")
        return False
    
    try:
        filepath.unlink()
        logger.debug(f"文件已删除: {filepath}")
        return True
    except Exception as e:
        logger.error(f"删除文件失败: {filepath} - {e}")
        return False


@contextmanager
def atomic_write(
    filepath: Union[str, Path],
    mode: str = 'w',
    encoding: str = 'utf-8',
    **kwargs
):
    """
    原子写入文件的上下文管理器
    
    Args:
        filepath: 文件路径
        mode: 文件模式
        encoding: 文件编码
        **kwargs: 传递给open函数的其他参数
    
    Yields:
        文件对象
    """
    filepath = Path(filepath)
    temp_file = None
    
    try:
        # 确保目录存在
        ensure_directory(filepath.parent)
        
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(
            mode=mode,
            encoding=encoding,
            delete=False,
            dir=filepath.parent,
            prefix=f".{filepath.name}.",
            suffix=".tmp",
            **kwargs
        )
        
        yield temp_file
        
        # 刷新并关闭文件
        temp_file.flush()
        os.fsync(temp_file.fileno())
        temp_file.close()
        
        # 原子性地重命名
        os.replace(temp_file.name, filepath)
        
        logger.debug(f"原子写入完成: {filepath}")
        
    except Exception:
        # 发生异常时清理临时文件
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        raise
    
    finally:
        if temp_file and not temp_file.closed:
            temp_file.close()


def get_file_size(filepath: Union[str, Path]) -> Optional[int]:
    """
    获取文件大小（字节）
    
    Args:
        filepath: 文件路径
    
    Returns:
        文件大小（字节），如果获取失败则返回None
    """
    return safe_execute(
        lambda p: Path(p).stat().st_size,
        filepath,
        default_return=None,
        error_message=f"获取文件大小失败: {filepath}"
    )


def get_file_hash(filepath: Union[str, Path], algorithm: str = "md5") -> Optional[str]:
    """
    获取文件哈希值
    
    Args:
        filepath: 文件路径
        algorithm: 哈希算法（md5, sha1, sha256）
    
    Returns:
        文件哈希值，如果获取失败则返回None
    """
    import hashlib
    
    def compute_hash():
        hash_obj = hashlib.new(algorithm)
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    
    return safe_execute(
        compute_hash,
        default_return=None,
        error_message=f"计算文件哈希失败: {filepath}"
    )


def find_files(
    directory: Union[str, Path],
    pattern: str = "*",
    recursive: bool = True
) -> List[Path]:
    """
    查找匹配模式的文件
    
    Args:
        directory: 目录路径
        pattern: 文件模式（glob语法）
        recursive: 是否递归查找
    
    Returns:
        匹配的文件路径列表
    """
    directory = Path(directory)
    
    if not directory.exists():
        logger.warning(f"目录不存在: {directory}")
        return []
    
    if not directory.is_dir():
        logger.warning(f"路径不是目录: {directory}")
        return []
    
    try:
        if recursive:
            return list(directory.rglob(pattern))
        else:
            return list(directory.glob(pattern))
    except Exception as e:
        logger.error(f"查找文件失败: {directory}/{pattern} - {e}")
        return []


# 预定义的文件操作函数
safe_read_text = read_text_file
safe_write_text = write_text_file
safe_read_json = read_json_file
safe_write_json = write_json_file
ensure_dir = ensure_directory


# 示例用法
if __name__ == "__main__":
    # 示例1：安全读写文本文件
    test_file = Path("test.txt")
    safe_write_text(test_file, "Hello, World!")
    content = safe_read_text(test_file)
    print(f"读取的内容: {content}")
    
    # 示例2：安全读写JSON文件
    test_json = Path("test.json")
    data = {"name": "Test", "value": 123}
    safe_write_json(test_json, data)
    loaded_data = safe_read_json(test_json)
    print(f"读取的JSON数据: {loaded_data}")
    
    # 示例3：原子写入
    with atomic_write(test_file) as f:
        f.write("原子写入的内容")
    
    # 清理测试文件
    delete_file(test_file)
    delete_file(test_json)