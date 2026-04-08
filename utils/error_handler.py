"""
错误处理工具模块 - 提供统一的错误处理机制

核心功能：
1. 错误处理装饰器：统一处理函数异常
2. 重试装饰器：自动重试失败的操作
3. 错误上下文管理器：在上下文中处理错误
4. 错误类型定义：统一的错误类型
"""

import logging
import time
from typing import Any, Callable, Type, Optional, Union, Dict
from functools import wraps
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class AppError(Exception):
    """应用基础错误类"""
    
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details
        }


class ConfigError(AppError):
    """配置错误"""
    pass


class LLMError(AppError):
    """LLM API错误"""
    pass


class StorageError(AppError):
    """存储错误"""
    pass


class ValidationError(AppError):
    """验证错误"""
    pass


def with_error_handling(
    default_return: Any = None,
    log_level: str = "ERROR",
    catch_exceptions: Union[Type[Exception], tuple] = Exception,
    re_raise: bool = False,
    include_traceback: bool = False
):
    """
    错误处理装饰器：统一处理函数异常
    
    Args:
        default_return: 发生异常时返回的默认值
        log_level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        catch_exceptions: 要捕获的异常类型
        re_raise: 是否重新抛出异常
        include_traceback: 是否包含堆栈跟踪
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except catch_exceptions as e:
                # 获取日志函数
                log_func = getattr(logger, log_level.lower(), logger.error)
                
                # 构建日志消息
                func_name = func.__name__
                error_msg = f"函数 {func_name} 执行失败: {e}"
                
                if include_traceback:
                    log_func(error_msg, exc_info=True)
                else:
                    log_func(error_msg)
                
                if re_raise:
                    raise
                
                return default_return
        
        return wrapper
    return decorator


def with_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Union[Type[Exception], tuple] = Exception,
    log_retries: bool = True
):
    """
    重试装饰器：自动重试失败的操作
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff_factor: 退避因子（每次重试延迟乘以该因子）
        exceptions: 触发重试的异常类型
        log_retries: 是否记录重试日志
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):  # +1 包括第一次尝试
                try:
                    if attempt > 0 and log_retries:
                        logger.info(f"第 {attempt} 次重试 {func.__name__}...")
                    
                    return func(*args, **kwargs)
                
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        if log_retries:
                            logger.warning(
                                f"{func.__name__} 第 {attempt + 1} 次尝试失败: {e}. "
                                f"{current_delay:.1f}秒后重试..."
                            )
                        
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        # 最后一次尝试也失败了
                        logger.error(f"{func.__name__} 在 {max_retries + 1} 次尝试后仍然失败")
                        raise
            
            # 理论上不会执行到这里
            raise last_exception
        
        return wrapper
    return decorator


@contextmanager
def error_context(
    context_name: str,
    default_return: Any = None,
    log_level: str = "ERROR",
    catch_exceptions: Union[Type[Exception], tuple] = Exception
):
    """
    错误上下文管理器：在上下文中处理错误
    
    Args:
        context_name: 上下文名称（用于日志）
        default_return: 发生异常时返回的默认值
        log_level: 日志级别
        catch_exceptions: 要捕获的异常类型
    
    Yields:
        上下文管理器
    """
    try:
        yield
    except catch_exceptions as e:
        log_func = getattr(logger, log_level.lower(), logger.error)
        log_func(f"上下文 '{context_name}' 中发生错误: {e}")
        
        if default_return is not None:
            return default_return
        else:
            raise


def safe_execute(
    func: Callable,
    *args,
    default_return: Any = None,
    log_error: bool = True,
    error_message: Optional[str] = None,
    **kwargs
) -> Any:
    """
    安全执行函数：捕获异常并返回默认值
    
    Args:
        func: 要执行的函数
        *args: 函数位置参数
        default_return: 发生异常时返回的默认值
        log_error: 是否记录错误日志
        error_message: 自定义错误消息
        **kwargs: 函数关键字参数
    
    Returns:
        函数执行结果或默认值
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_error:
            msg = error_message or f"执行函数 {func.__name__} 失败"
            logger.error(f"{msg}: {e}")
        
        return default_return


def validate_not_none(value: Any, name: str, error_type: Type[Exception] = ValueError) -> None:
    """
    验证值不为None
    
    Args:
        value: 要验证的值
        name: 值名称（用于错误消息）
        error_type: 错误类型
    
    Raises:
        指定的错误类型: 如果值为None
    """
    if value is None:
        raise error_type(f"{name} 不能为None")


def validate_not_empty(value: Any, name: str, error_type: Type[Exception] = ValueError) -> None:
    """
    验证值不为空（适用于字符串、列表、字典等）
    
    Args:
        value: 要验证的值
        name: 值名称（用于错误消息）
        error_type: 错误类型
    
    Raises:
        指定的错误类型: 如果值为空
    """
    if not value:
        raise error_type(f"{name} 不能为空")


def validate_in_range(
    value: Union[int, float],
    name: str,
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    error_type: Type[Exception] = ValueError
) -> None:
    """
    验证值在指定范围内
    
    Args:
        value: 要验证的值
        name: 值名称（用于错误消息）
        min_value: 最小值（包含）
        max_value: 最大值（包含）
        error_type: 错误类型
    
    Raises:
        指定的错误类型: 如果值不在范围内
    """
    if min_value is not None and value < min_value:
        raise error_type(f"{name} ({value}) 不能小于 {min_value}")
    
    if max_value is not None and value > max_value:
        raise error_type(f"{name} ({value}) 不能大于 {max_value}")


# 预定义的错误处理装饰器
handle_errors = with_error_handling(default_return=None, log_level="ERROR")
handle_errors_silent = with_error_handling(default_return=None, log_level="DEBUG")
retry_on_failure = with_retry(max_retries=3, delay=1.0)
retry_on_network_error = with_retry(max_retries=5, delay=2.0, exceptions=(ConnectionError, TimeoutError))


# 示例用法
if __name__ == "__main__":
    # 示例1：使用错误处理装饰器
    @handle_errors
    def risky_function():
        raise ValueError("这是一个测试错误")
    
    # 示例2：使用重试装饰器
    @retry_on_failure
    def unreliable_function():
        import random
        if random.random() < 0.7:
            raise ConnectionError("随机失败")
        return "成功"
    
    # 示例3：使用错误上下文管理器
    with error_context("数据处理", default_return=[]):
        # 这里可能会抛出异常
        pass
    
    # 示例4：安全执行函数
    result = safe_execute(risky_function, default_return="默认值")
    print(f"安全执行结果: {result}")