"""
应用配置管理模块 - 使用pydantic-settings进行现代化配置管理

核心特性：
1. 类型安全的配置验证
2. 环境变量自动加载（支持.env文件）
3. 配置项分组和文档
4. 配置验证和默认值
5. 配置热重载支持
"""

import os
from typing import Optional, List, Dict, Any
from pathlib import Path
from enum import Enum
from datetime import datetime

from pydantic import Field, validator, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(str, Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LLMProvider(str, Enum):
    """LLM提供商枚举"""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    AZURE = "azure"
    CUSTOM = "custom"


class LLMConfig(BaseSettings):
    """LLM配置组"""
    
    provider: LLMProvider = Field(
        default=LLMProvider.DEEPSEEK,
        description="LLM提供商"
    )
    
    api_key: SecretStr = Field(
        default=SecretStr(""),
        description="API密钥",
        env="LLM_API_KEY"
    )
    
    base_url: str = Field(
        default="https://api.deepseek.com",
        description="API基础URL"
    )
    
    model: str = Field(
        default="deepseek-chat",
        description="模型名称"
    )
    
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="温度参数（0.0-2.0）"
    )
    
    max_tokens: int = Field(
        default=2000,
        ge=1,
        le=32000,
        description="最大输出token数"
    )
    
    timeout_seconds: int = Field(
        default=30,
        ge=1,
        description="API调用超时时间（秒）"
    )
    
    max_retries: int = Field(
        default=5,
        ge=0,
        description="最大重试次数"
    )
    
    retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        description="重试延迟（秒）"
    )
    
    enable_thinking: bool = Field(
        default=False,
        description="是否启用DeepSeek思考模式（需要手动通过extra_body参数开启）"
    )
    
    @validator("base_url")
    def validate_base_url(cls, v):
        """验证base_url格式"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("base_url必须以http://或https://开头")
        return v.rstrip("/")
    
    def get_client_config(self) -> Dict[str, Any]:
        """获取LLM客户端配置"""
        config = {
            "api_key": self.api_key.get_secret_value(),
            "base_url": self.base_url,
            "timeout": self.timeout_seconds,
            "max_retries": self.max_retries,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        # 如果需要启用思考模式，添加配置
        if self.enable_thinking:
            config["enable_thinking"] = True
            config["extra_body"] = {"thinking": {"type": "enabled"}}
        
        return config


class StorageConfig(BaseSettings):
    """存储配置组"""
    
    data_dir: Path = Field(
        default=Path("./data"),
        description="数据目录路径"
    )
    
    output_dir: Path = Field(
        default=Path("./output"),
        description="输出目录路径"
    )
    
    state_file: Path = Field(
        default=Path("./data/state.json"),
        description="状态文件路径"
    )
    
    history_file: Path = Field(
        default=Path("./data/history.json"),
        description="历史记录文件路径"
    )
    
    feedback_file: Path = Field(
        default=Path("./data/feedback.txt"),
        description="反馈文件路径"
    )
    
    @validator("data_dir", "output_dir", pre=True)
    def validate_and_create_dirs(cls, v):
        """验证目录路径并创建目录"""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def ensure_directories(self) -> None:
        """确保所有必要的目录存在"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


class LoggingConfig(BaseSettings):
    """日志配置组"""
    
    level: LogLevel = Field(
        default=LogLevel.INFO,
        description="日志级别"
    )
    
    file: Optional[Path] = Field(
        default=None,
        description="日志文件路径（如不设置则输出到控制台）"
    )
    
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )
    
    max_file_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="日志文件最大大小（字节）"
    )
    
    backup_count: int = Field(
        default=5,
        description="日志备份文件数量"
    )


class WorkflowConfig(BaseSettings):
    """工作流配置组"""
    
    max_context_tokens: int = Field(
        default=128000,
        ge=1000,
        description="最大上下文token数"
    )
    
    window_size: int = Field(
        default=3,
        ge=1,
        le=10,
        description="窗口大小（章节数）"
    )
    
    base_context_preserve_ratio: float = Field(
        default=0.1,
        ge=0.01,
        le=0.5,
        description="基准上下文保留比例"
    )
    
    system_info_cycle_length: int = Field(
        default=15,
        ge=5,
        le=50,
        description="系统信息插入周期长度（章节数）"
    )
    
    system_info_insertions_per_cycle: int = Field(
        default=6,
        ge=1,
        le=20,
        description="每个周期内系统信息插入次数"
    )
    
    feedback_alert_interval: int = Field(
        default=10,
        ge=1,
        description="反馈提醒间隔（章节数）"
    )
    
    @validator("system_info_insertions_per_cycle")
    def validate_insertions_per_cycle(cls, v, values):
        """验证每个周期的插入次数不超过周期长度"""
        cycle_length = values.get("system_info_cycle_length", 15)
        if v > cycle_length:
            raise ValueError(f"每个周期的插入次数({v})不能超过周期长度({cycle_length})")
        return v


class SchedulerConfig(BaseSettings):
    """调度配置组"""
    
    enabled: bool = Field(
        default=False,
        description="是否启用时间调度"
    )
    
    time_window: str = Field(
        default="00:00-23:59",
        description="运行时间窗口，格式 HH:MM-HH:MM，例如 09:00-18:00"
    )
    
    check_interval_seconds: int = Field(
        default=60,
        ge=5,
        le=3600,
        description="检查时间窗口的间隔秒数"
    )
    
    pause_behavior: str = Field(
        default="sleep",
        description="窗口外暂停行为：sleep（休眠等待）或 exit（优雅退出）"
    )
    
    @validator("time_window")
    def validate_time_window(cls, v):
        """验证时间窗口格式"""
        import re
        pattern = r'^([0-1]?[0-9]|2[0-3]):([0-5][0-9])-([0-1]?[0-9]|2[0-3]):([0-5][0-9])$'
        if not re.match(pattern, v):
            raise ValueError("时间窗口格式必须为 HH:MM-HH:MM，例如 09:00-18:00")
        # 确保开始时间早于结束时间（允许跨夜）
        # 我们只做格式验证，逻辑上可以跨夜
        return v
    
    def is_within_window(self, dt: Optional[datetime] = None) -> bool:
        """检查给定时间是否在时间窗口内
        
        Args:
            dt: 要检查的datetime对象，默认为当前本地时间
            
        Returns:
            如果在窗口内返回True，否则返回False
        """
        if not self.enabled:
            return True  # 调度未启用，始终允许运行
        
        from datetime import datetime as dt_cls
        if dt is None:
            dt = dt_cls.now()
        
        # 解析时间窗口
        start_str, end_str = self.time_window.split('-')
        start_hour, start_minute = map(int, start_str.split(':'))
        end_hour, end_minute = map(int, end_str.split(':'))
        
        # 创建今天的开始和结束时间
        start_time = dt.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        end_time = dt.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
        
        # 处理跨夜情况（结束时间早于开始时间）
        if end_time < start_time:
            # 窗口跨越午夜，例如 22:00-06:00
            # 当前时间在开始时间之后或结束时间之前
            return dt >= start_time or dt <= end_time
        else:
            # 正常窗口
            return start_time <= dt <= end_time
    
    def get_next_window_start(self, dt: Optional[datetime] = None) -> datetime:
        """获取下一个窗口开始时间
        
        Args:
            dt: 参考时间，默认为当前时间
            
        Returns:
            下一个窗口开始的datetime对象
        """
        from datetime import datetime as dt_cls, timedelta
        if dt is None:
            dt = dt_cls.now()
        
        # 解析时间窗口
        start_str, _ = self.time_window.split('-')
        start_hour, start_minute = map(int, start_str.split(':'))
        
        # 今天的开始时间
        start_today = dt.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        
        if dt < start_today:
            # 今天窗口尚未开始
            return start_today
        else:
            # 今天窗口已过，返回明天的窗口开始时间
            return start_today + timedelta(days=1)


class UserIdeaConfig(BaseSettings):
    """用户灵感配置组"""
    
    enabled: bool = Field(
        default=True,
        description="是否启用用户灵感注入功能"
    )
    
    collaborative_mode: bool = Field(
        default=False,
        description="是否启用用户协同模式（根据灵感数量自动规划章节）"
    )
    
    auto_cc_enabled: bool = Field(
        default=True,
        description="协同模式下是否自动计算--cc参数（额外章节数）"
    )
    
    min_chapters_per_idea: int = Field(
        default=1,
        ge=1,
        le=10,
        description="协同模式下每个灵感分配的最小章节数"
    )
    
    directory: Path = Field(
        default=Path("./prompts/user_idea"),
        description="灵感文件目录路径"
    )
    
    completed_prefix: str = Field(
        default="completed_",
        description="已完成文件前缀"
    )
    
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="文件操作最大重试次数"
    )
    
    @validator("directory", pre=True)
    def validate_and_create_dir(cls, v):
        """验证目录路径并创建目录"""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path


class Settings(BaseSettings):
    """主配置类"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )
    
    # 配置分组
    llm: LLMConfig = Field(default_factory=LLMConfig)
    reader_llm: LLMConfig = Field(default_factory=LLMConfig)
    writer_llm: LLMConfig = Field(default_factory=LLMConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    user_idea: UserIdeaConfig = Field(default_factory=UserIdeaConfig)

    # 应用元数据
    app_name: str = Field(
        default="DeepNovelV3 Lite",
        description="应用名称"
    )
    
    app_version: str = Field(
        default="1.0.0",
        description="应用版本"
    )
    
    debug_mode: bool = Field(
        default=False,
        description="调试模式"
    )
    
    def __init__(self, **kwargs):
        """初始化配置并确保目录存在"""
        super().__init__(**kwargs)
        self.storage.ensure_directories()
    
    def validate_configuration(self) -> List[str]:
        """
        验证配置并返回错误信息列表
        
        Returns:
            List[str]: 错误信息列表，空列表表示配置有效
        """
        errors = []
        
        # 验证LLM配置（向后兼容，检查默认llm配置）
        if not self.llm.api_key.get_secret_value():
            errors.append("LLM API密钥未设置")
        
        # 验证reader_llm配置（如果有API密钥）
        if self.reader_llm.api_key.get_secret_value():
            try:
                # 验证base_url格式
                if not self.reader_llm.base_url.startswith(("http://", "https://")):
                    errors.append("reader_llm基础URL必须以http://或https://开头")
            except Exception as e:
                errors.append(f"reader_llm配置验证失败: {e}")
        
        # 验证writer_llm配置（如果有API密钥）
        if self.writer_llm.api_key.get_secret_value():
            try:
                if not self.writer_llm.base_url.startswith(("http://", "https://")):
                    errors.append("writer_llm基础URL必须以http://或https://开头")
            except Exception as e:
                errors.append(f"writer_llm配置验证失败: {e}")
        
        # 验证存储目录可写
        try:
            test_file = self.storage.data_dir / ".test_write"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            errors.append(f"数据目录不可写: {e}")
        
        # 验证工作流配置
        if self.workflow.window_size < 1:
            errors.append("窗口大小必须大于0")
        
        return errors
    
    def is_valid(self) -> bool:
        """检查配置是否有效"""
        return len(self.validate_configuration()) == 0
    
    def to_safe_dict(self) -> Dict[str, Any]:
        """转换为安全的字典（隐藏敏感信息）"""
        config_dict = self.model_dump()
        
        # 隐藏API密钥
        def hide_api_key(api_key: str) -> str:
            if api_key and len(api_key) > 8:
                return f"{api_key[:4]}...{api_key[-4:]}"
            return api_key
        
        # 处理llm配置
        if "llm" in config_dict and "api_key" in config_dict["llm"]:
            config_dict["llm"]["api_key"] = hide_api_key(config_dict["llm"]["api_key"])
        
        # 处理reader_llm配置
        if "reader_llm" in config_dict and "api_key" in config_dict["reader_llm"]:
            config_dict["reader_llm"]["api_key"] = hide_api_key(config_dict["reader_llm"]["api_key"])
        
        # 处理writer_llm配置
        if "writer_llm" in config_dict and "api_key" in config_dict["writer_llm"]:
            config_dict["writer_llm"]["api_key"] = hide_api_key(config_dict["writer_llm"]["api_key"])
        
        return config_dict
    
    def get_summary(self) -> str:
        """获取配置摘要"""
        errors = self.validate_configuration()
        
        summary = f"""
{self.app_name} v{self.app_version} 配置摘要
{'=' * 50}

默认LLM配置 (向后兼容):
  提供商: {self.llm.provider.value}
  模型: {self.llm.model}
  API密钥: {'已设置' if self.llm.api_key.get_secret_value() else '未设置'}
  基础URL: {self.llm.base_url}
  温度: {self.llm.temperature}
  超时: {self.llm.timeout_seconds}s
  重试: {self.llm.max_retries}次

Reader LLM配置 (reader_llm):
  提供商: {self.reader_llm.provider.value}
  模型: {self.reader_llm.model}
  API密钥: {'已设置' if self.reader_llm.api_key.get_secret_value() else '未设置'}
  基础URL: {self.reader_llm.base_url}
  温度: {self.reader_llm.temperature}
  超时: {self.reader_llm.timeout_seconds}s
  重试: {self.reader_llm.max_retries}次

Writer LLM配置 (writer_llm):
  提供商: {self.writer_llm.provider.value}
  模型: {self.writer_llm.model}
  API密钥: {'已设置' if self.writer_llm.api_key.get_secret_value() else '未设置'}
  基础URL: {self.writer_llm.base_url}
  温度: {self.writer_llm.temperature}
  超时: {self.writer_llm.timeout_seconds}s
  重试: {self.writer_llm.max_retries}次

存储配置:
  数据目录: {self.storage.data_dir}
  输出目录: {self.storage.output_dir}
  状态文件: {self.storage.state_file}
  历史文件: {self.storage.history_file}

日志配置:
  级别: {self.logging.level.value}
  文件: {self.logging.file or '控制台'}
  格式: {self.logging.format[:50]}...

工作流配置:
  最大上下文: {self.workflow.max_context_tokens} tokens
  窗口大小: {self.workflow.window_size}章
  系统信息周期: {self.workflow.system_info_cycle_length}章
  反馈提醒间隔: {self.workflow.feedback_alert_interval}章

应用配置:
  调试模式: {self.debug_mode}
  配置验证: {'通过' if self.is_valid() else '失败'}
"""
        
        if errors:
            summary += f"\n配置错误:\n"
            for error in errors:
                summary += f"  - {error}\n"
        
        return summary


# 全局配置实例
settings = Settings()

# 向后兼容的别名
def get_settings() -> Settings:
    """获取配置实例（向后兼容）"""
    return settings