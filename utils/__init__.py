"""
工具模块包 - 提供各种通用工具函数

包含以下模块：
1. error_handler: 错误处理工具
2. file_utils: 文件操作工具
3. string_utils: 字符串处理工具
4. file_lock: 文件锁工具
5. system_info_manager: 系统信息管理
"""

from .error_handler import (
    AppError,
    ConfigError,
    LLMError,
    StorageError,
    ValidationError,
    with_error_handling,
    with_retry,
    error_context,
    safe_execute,
    validate_not_none,
    validate_not_empty,
    validate_in_range,
    handle_errors,
    handle_errors_silent,
    retry_on_failure,
    retry_on_network_error,
)

from .file_utils import (
    read_text_file,
    write_text_file,
    read_json_file,
    write_json_file,
    ensure_directory,
    copy_file,
    delete_file,
    atomic_write,
    get_file_size,
    get_file_hash,
    find_files,
    safe_read_text,
    safe_write_text,
    safe_read_json,
    safe_write_json,
    ensure_dir,
)

from .string_utils import (
    clean_text,
    truncate_text,
    sanitize_filename,
    escape_html,
    unescape_html,
    normalize_whitespace,
    extract_lines,
    count_words,
    count_characters,
    render_template,
    load_template,
    is_valid_email,
    is_valid_url,
    extract_emails,
    extract_urls,
    to_camel_case,
    to_snake_case,
    generate_slug,
    clean,
    truncate,
    sanitize,
    normalize,
)

from .file_lock import (
    FileLock,
    file_lock_context,
    AtomicFileWriter,
)

from .system_info_manager import SystemInfoManager

# 版本信息
__version__ = "1.0.0"
__author__ = "DeepNovelV3 Team"
__description__ = "DeepNovelV3 Lite 工具模块包"

# 导出所有工具函数
__all__ = [
    # 错误处理
    "AppError",
    "ConfigError",
    "LLMError",
    "StorageError",
    "ValidationError",
    "with_error_handling",
    "with_retry",
    "error_context",
    "safe_execute",
    "validate_not_none",
    "validate_not_empty",
    "validate_in_range",
    "handle_errors",
    "handle_errors_silent",
    "retry_on_failure",
    "retry_on_network_error",
    
    # 文件操作
    "read_text_file",
    "write_text_file",
    "read_json_file",
    "write_json_file",
    "ensure_directory",
    "copy_file",
    "delete_file",
    "atomic_write",
    "get_file_size",
    "get_file_hash",
    "find_files",
    "safe_read_text",
    "safe_write_text",
    "safe_read_json",
    "safe_write_json",
    "ensure_dir",
    
    # 字符串处理
    "clean_text",
    "truncate_text",
    "sanitize_filename",
    "escape_html",
    "unescape_html",
    "normalize_whitespace",
    "extract_lines",
    "count_words",
    "count_characters",
    "render_template",
    "load_template",
    "is_valid_email",
    "is_valid_url",
    "extract_emails",
    "extract_urls",
    "to_camel_case",
    "to_snake_case",
    "generate_slug",
    "clean",
    "truncate",
    "sanitize",
    "normalize",
    
    # 文件锁
    "FileLock",
    "file_lock_context",
    "AtomicFileWriter",
    
    # 系统信息管理
    "SystemInfoManager",
]