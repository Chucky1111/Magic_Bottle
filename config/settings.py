"""
应用配置管理模块 - 向后兼容的包装器

此模块提供与旧版本兼容的配置接口，同时使用新的pydantic-settings配置系统。
"""

import warnings
from typing import Optional, Dict, Any
from pathlib import Path

# 导入新的配置系统
try:
    from .settings_v2 import settings as new_settings
    from .settings_v2 import LLMProvider, LogLevel
except ImportError:
    # 如果新配置系统不可用，回退到旧系统
    warnings.warn("无法导入新的配置系统，使用旧的配置系统", ImportWarning)
    from .settings_legacy import Settings as LegacySettings
    new_settings = LegacySettings()


class Settings:
    """向后兼容的配置类"""
    
    def __init__(self):
        self._new_settings = new_settings
    
    @property
    def llm_api_key(self) -> str:
        """获取LLM API密钥"""
        return self._new_settings.llm.api_key.get_secret_value()
    
    @llm_api_key.setter
    def llm_api_key(self, value: str):
        """设置LLM API密钥"""
        from pydantic import SecretStr
        self._new_settings.llm.api_key = SecretStr(value)
    
    @property
    def reader_llm(self):
        """获取reader_llm配置"""
        return self._new_settings.reader_llm
    
    @property
    def writer_llm(self):
        """获取writer_llm配置"""
        return self._new_settings.writer_llm
    
    @property
    def llm_base_url(self) -> str:
        """获取LLM基础URL"""
        return self._new_settings.llm.base_url
    
    @property
    def llm_model(self) -> str:
        """获取LLM模型"""
        return self._new_settings.llm.model
    
    @property
    def max_retries(self) -> int:
        """获取最大重试次数"""
        return self._new_settings.llm.max_retries
    
    @property
    def retry_delay(self) -> float:
        """获取重试延迟"""
        return self._new_settings.llm.retry_delay
    
    @property
    def timeout_seconds(self) -> int:
        """获取超时时间"""
        return self._new_settings.llm.timeout_seconds
    
    @property
    def state_file_path(self) -> str:
        """获取状态文件路径"""
        return str(self._new_settings.storage.state_file)
    
    @property
    def project_data_dir(self) -> str:
        """获取项目数据目录"""
        return str(self._new_settings.storage.data_dir)
    
    @property
    def log_level(self) -> str:
        """获取日志级别"""
        return self._new_settings.logging.level.value
    
    @property
    def log_file(self) -> Optional[str]:
        """获取日志文件路径"""
        log_file = self._new_settings.logging.file
        return str(log_file) if log_file else None
    
    @property
    def max_context_length(self) -> int:
        """获取最大上下文长度"""
        return self._new_settings.workflow.max_context_tokens
    
    @property
    def temperature(self) -> float:
        """获取温度参数"""
        return self._new_settings.llm.temperature
    
    @property
    def max_tokens(self) -> int:
        """获取最大输出token数"""
        return self._new_settings.llm.max_tokens
    
    @property
    def enable_thinking(self) -> bool:
        """是否启用DeepSeek思考模式"""
        return self._new_settings.llm.enable_thinking
    
    @property
    def scheduler(self):
        """获取调度配置"""
        return self._new_settings.scheduler
    
    @property
    def user_idea(self):
        """获取用户灵感配置"""
        return self._new_settings.user_idea
    
    def get_openai_client_config(self) -> dict:
        """获取OpenAI客户端配置（向后兼容）"""
        return {
            "api_key": self.llm_api_key,
            "base_url": self.llm_base_url,
            "timeout": self.timeout_seconds,
        }
    
    def validate(self) -> bool:
        """验证配置是否有效"""
        return self._new_settings.is_valid()
    
    def __str__(self) -> str:
        """返回配置的字符串表示"""
        return self._new_settings.get_summary()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（向后兼容）"""
        config_dict = {
            "llm_api_key": self.llm_api_key,
            "llm_base_url": self.llm_base_url,
            "llm_model": self.llm_model,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "timeout_seconds": self.timeout_seconds,
            "state_file_path": self.state_file_path,
            "project_data_dir": self.project_data_dir,
            "log_level": self.log_level,
            "log_file": self.log_file,
            "max_context_length": self.max_context_length,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        # 添加新配置字段（如果存在）
        if hasattr(self, 'enable_thinking'):
            config_dict["enable_thinking"] = self.enable_thinking
        
        return config_dict


# 全局配置实例
settings = Settings()

# 导出兼容性函数
def get_settings() -> Settings:
    """获取配置实例"""
    return settings

def validate_config() -> bool:
    """验证配置"""
    return settings.validate()

def print_config_summary():
    """打印配置摘要"""
    print(settings)