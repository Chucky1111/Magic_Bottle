"""
旧版配置系统 - 仅在新配置系统导入失败时使用
"""

import os
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Settings:
    """应用配置类"""
    
    # LLM API 配置
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o"
    
    # 重试机制配置
    max_retries: int = 5
    retry_delay: float = 1.0
    timeout_seconds: int = 30
    
    # 状态持久化配置
    state_file_path: str = "./state.json"
    project_data_dir: str = "./projects"
    
    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # 工作流配置
    max_context_length: int = 4000
    temperature: float = 0.7
    max_tokens: int = 2000
    
    def __post_init__(self):
        """初始化后加载环境变量"""
        self._load_from_env()
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        env_mappings = {
            "llm_api_key": "LLM_API_KEY",
            "llm_base_url": "LLM_BASE_URL",
            "llm_model": "LLM_MODEL",
            "max_retries": "MAX_RETRIES",
            "retry_delay": "RETRY_DELAY",
            "timeout_seconds": "TIMEOUT_SECONDS",
            "state_file_path": "STATE_FILE_PATH",
            "project_data_dir": "PROJECT_DATA_DIR",
            "log_level": "LOG_LEVEL",
            "log_file": "LOG_FILE",
            "max_context_length": "MAX_CONTEXT_LENGTH",
            "temperature": "TEMPERATURE",
            "max_tokens": "MAX_TOKENS",
        }
        
        # 首先尝试从.env文件加载
        env_file = ".env"
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            os.environ[key] = value
            except Exception as e:
                print(f"警告: 加载.env文件失败: {e}")
        
        # 从环境变量更新配置
        for attr, env_var in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # 类型转换
                current_type = type(getattr(self, attr))
                try:
                    if current_type == int:
                        setattr(self, attr, int(env_value))
                    elif current_type == float:
                        setattr(self, attr, float(env_value))
                    elif current_type == bool:
                        setattr(self, attr, env_value.lower() in ('true', '1', 'yes'))
                    else:
                        setattr(self, attr, env_value)
                except (ValueError, TypeError):
                    # 类型转换失败，保持默认值
                    pass
    
    def get_openai_client_config(self) -> dict:
        """获取OpenAI客户端配置"""
        return {
            "api_key": self.llm_api_key,
            "base_url": self.llm_base_url,
            "timeout": self.timeout_seconds,
        }
    
    def validate(self) -> bool:
        """验证配置是否有效"""
        if not self.llm_api_key:
            print("错误: LLM_API_KEY 未设置")
            return False
        
        if not self.llm_base_url:
            print("错误: LLM_BASE_URL 未设置")
            return False
        
        if not self.llm_model:
            print("错误: LLM_MODEL 未设置")
            return False
        
        if self.max_retries < 0:
            print("错误: MAX_RETRIES 必须大于等于0")
            return False
        
        if self.retry_delay <= 0:
            print("错误: RETRY_DELAY 必须大于0")
            return False
        
        return True
    
    def __str__(self) -> str:
        """返回配置的字符串表示（隐藏敏感信息）"""
        masked_key = self.llm_api_key[:8] + "..." + self.llm_api_key[-4:] if len(self.llm_api_key) > 12 else "***"
        
        return f"""配置信息:
  LLM配置:
    API密钥: {masked_key}
    基础URL: {self.llm_base_url}
    模型: {self.llm_model}
  
  重试配置:
    最大重试次数: {self.max_retries}
    重试延迟: {self.retry_delay}s
    超时时间: {self.timeout_seconds}s
  
  应用配置:
    状态文件: {self.state_file_path}
    项目目录: {self.project_data_dir}
    日志级别: {self.log_level}
    
  工作流配置:
    最大上下文长度: {self.max_context_length}
    温度参数: {self.temperature}
    最大输出token数: {self.max_tokens}"""
    
    def is_valid(self) -> bool:
        """检查配置是否有效（新方法）"""
        return self.validate()
    
    def get_summary(self) -> str:
        """获取配置摘要（新方法）"""
        return str(self)