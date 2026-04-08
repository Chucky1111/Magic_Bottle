"""
健壮的LLM API客户端
使用Tenacity实现高级重试机制，支持OpenAI兼容接口
"""

import logging
import time
from typing import List, Dict, Any, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryCallState
)
import openai
from openai import (
    OpenAIError,
    RateLimitError,
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    BadRequestError
)

from config.settings import settings


logger = logging.getLogger(__name__)


class TokenEstimator:
    """精确的token估算器"""
    
    def __init__(self):
        self._encoding = None
        self._has_tiktoken = False
        self._initialize_encoding()
    
    def _initialize_encoding(self):
        """初始化编码器，尝试使用tiktoken，失败时使用后备方案"""
        try:
            import tiktoken
            # 使用cl100k_base编码，这是GPT-4/GPT-3.5使用的编码
            self._encoding = tiktoken.get_encoding("cl100k_base")
            self._has_tiktoken = True
            logger.info("Token估算器: 使用tiktoken进行精确token估算")
        except ImportError:
            self._has_tiktoken = False
            logger.warning("Token估算器: tiktoken未安装，使用后备估算方案")
        except Exception as e:
            self._has_tiktoken = False
            logger.warning(f"Token估算器: 初始化tiktoken失败: {e}，使用后备估算方案")
    
    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的token数量
        
        Args:
            text: 要估算的文本
            
        Returns:
            估算的token数量
        """
        if not text:
            return 0
        
        if self._has_tiktoken and self._encoding:
            try:
                return len(self._encoding.encode(text))
            except Exception as e:
                logger.warning(f"使用tiktoken估算token失败: {e}，切换到后备方案")
        
        # 后备方案：根据中英文字符进行估算
        # 中文：平均每个字符约2.5个token
        # 英文：平均每个单词约1.3个token，每个单词约5个字符
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        
        # 估算：中文每个字符2.5个token，英文每5个字符1.3个token
        estimated_tokens = int(chinese_chars * 2.5 + other_chars * 1.3 / 5)
        
        # 确保至少1个token
        return max(estimated_tokens, 1)
    
    def estimate_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        估算消息列表的总token数
        
        Args:
            messages: OpenAI格式的消息列表
            
        Returns:
            总token数估算
        """
        total_tokens = 0
        
        for msg in messages:
            # 每条消息有固定的开销（角色标记等）
            total_tokens += 4  # 每条消息的基础开销
            
            # 估算内容token
            content = msg.get('content', '')
            total_tokens += self.estimate_tokens(content)
            
            # 如果有name字段，额外估算
            if 'name' in msg:
                total_tokens += self.estimate_tokens(msg['name'])
        
        return total_tokens


def log_retry_attempt(retry_state: RetryCallState) -> None:
    """记录重试尝试的日志函数"""
    attempt_number = retry_state.attempt_number
    max_attempts = settings.max_retries
    wait_time = retry_state.next_action.sleep if retry_state.next_action else 0
    
    if retry_state.outcome and retry_state.outcome.failed:
        exception = retry_state.outcome.exception()
        logger.warning(
            f"API Error ({type(exception).__name__}), "
            f"retrying in {wait_time:.1f}s... "
            f"Attempt {attempt_number}/{max_attempts}"
        )


class LLMClient:
    """
    健壮的LLM客户端，封装OpenAI兼容API调用
    
    特性：
    1. 使用Tenacity实现指数退避+随机抖动的重试机制
    2. 智能重试：仅对网络错误、限流、服务器错误重试
    3. 详细的日志记录，包括重试信息
    4. 统一的chat接口
    5. 自适应超时和性能监控
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化LLM客户端
        
        Args:
            config: 可选的配置字典，包含以下键：
                - api_key: API密钥
                - base_url: 基础URL
                - timeout: 超时时间（秒）
                - max_retries: 最大重试次数
                - model: 模型名称
                - temperature: 温度参数
                - max_tokens: 最大输出token数
                - max_context_length: 最大上下文token数
                - enable_thinking: 是否启用DeepSeek思考模式
                - extra_body: 额外的API请求体参数
                如果未提供，则使用全局配置
        """
        if config is None:
            # 使用全局配置（向后兼容）
            client_config = settings.get_openai_client_config()
            self.model = settings.llm_model
            self.timeout_seconds = settings.timeout_seconds
            self.max_retries = settings.max_retries
            self.temperature = settings.temperature
            self.max_tokens = settings.max_tokens
            self.max_context_length = settings.max_context_length
            self.enable_thinking = settings.enable_thinking
            self.extra_body = None
        else:
            # 使用提供的配置
            client_config = {
                "api_key": config.get("api_key", ""),
                "base_url": config.get("base_url", "https://api.deepseek.com"),
                "timeout": config.get("timeout", 30),
            }
            self.model = config.get("model", "deepseek-chat")
            self.timeout_seconds = config.get("timeout", 30)
            self.max_retries = config.get("max_retries", 5)
            self.temperature = config.get("temperature", 0.7)
            self.max_tokens = config.get("max_tokens", 2000)
            self.max_context_length = config.get("max_context_length", settings.max_context_length)
            self.enable_thinking = config.get("enable_thinking", False)
            self.extra_body = config.get("extra_body")
        
        # 如果启用思考模式但未提供extra_body，自动设置
        if self.enable_thinking and not self.extra_body:
            self.extra_body = {"thinking": {"type": "enabled"}}
        
        self.client = openai.OpenAI(**client_config)
        
        # 初始化token估算器
        self.token_estimator = TokenEstimator()
        
        # 性能监控
        self.call_count = 0
        self.total_response_time = 0.0
        self.last_error_time = 0.0
        
        thinking_status = "已启用" if self.enable_thinking else "已禁用"
        logger.info(
            f"LLMClient初始化完成 - "
            f"Model: {self.model}, "
            f"Base URL: {client_config.get('base_url', 'default')}, "
            f"Max Retries: {self.max_retries}, "
            f"Timeout: {self.timeout_seconds}s, "
            f"思考模式: {thinking_status}"
        )
    
    @retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_random_exponential(
            multiplier=settings.retry_delay,
            min=settings.retry_delay,
            max=120  # 最大等待120秒，给API更多恢复时间
        ),
        retry=retry_if_exception_type(
            (RateLimitError, APIConnectionError, APITimeoutError, APIStatusError)
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=log_retry_attempt,
        reraise=True
    )
    def _call_api(self, messages: List[Dict[str, str]], **kwargs) -> Any:
        """
        内部API调用方法，包含重试逻辑
        
        Args:
            messages: OpenAI格式的消息列表
            **kwargs: 其他API参数
            
        Returns:
            OpenAI API响应
            
        Raises:
            OpenAIError: API调用失败
            BadRequestError: 400错误（不重试）
        """
        try:
            start_time = time.time()
            
            # 计算自适应超时时间
            # 基础超时 + 根据消息长度增加的时间
            base_timeout = kwargs.get('timeout', self.timeout_seconds)
            
            # 使用token估算器精确估算token数
            estimated_prompt_tokens = self.token_estimator.estimate_messages_tokens(messages)
            
            # 自适应超时：每1000token增加5秒
            adaptive_timeout = base_timeout + (estimated_prompt_tokens // 1000) * 5
            # 但不超过300秒（5分钟）
            adaptive_timeout = min(adaptive_timeout, 300)
            
            if adaptive_timeout > base_timeout:
                logger.debug(f"自适应超时: {adaptive_timeout}s (基于{estimated_prompt_tokens}估算token)")
            
            # 自适应max_tokens逻辑
            # 基础max_tokens来自配置
            base_max_tokens = kwargs.get('max_tokens', self.max_tokens)
            
            # 根据上下文长度调整max_tokens
            # 如果上下文很长，减少输出token以避免总token超限
            model_max_context = self.max_context_length  # 使用配置的最大上下文长度
            
            # 计算可用token：模型最大上下文 - 估算的提示token - 安全边际
            # 安全边际包括：响应格式开销、系统消息开销等
            safety_margin = 1500  # 增加安全边际，确保不会超限
            available_tokens = model_max_context - estimated_prompt_tokens - safety_margin
            
            # 使用较小的值：配置的max_tokens或可用token
            adaptive_max_tokens = min(base_max_tokens, available_tokens)
            
            # 确保至少有一定数量的输出token，但不超过可用token
            min_output_tokens = 500
            if available_tokens > min_output_tokens:
                adaptive_max_tokens = max(adaptive_max_tokens, min_output_tokens)
            else:
                # 如果可用token很少，使用更小的值
                adaptive_max_tokens = max(adaptive_max_tokens, 100)
                logger.warning(f"可用token较少: {available_tokens}，设置max_tokens为: {adaptive_max_tokens}")
            
            if adaptive_max_tokens != base_max_tokens:
                logger.debug(f"自适应max_tokens: {adaptive_max_tokens} (基于{estimated_prompt_tokens}估算提示token，模型最大上下文: {model_max_context})")
            
            # 准备API调用参数
            api_kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get('temperature', self.temperature),
                "max_tokens": adaptive_max_tokens,
                "timeout": adaptive_timeout,
                "frequency_penalty": kwargs.get('frequency_penalty', 0.5),  # 增加重复惩罚强度
                "presence_penalty": kwargs.get('presence_penalty', 0.5)    # 增加重复惩罚强度
            }
            
            # 处理思考模式参数
            # 优先级：kwargs中的extra_body > self.extra_body
            extra_body = kwargs.get('extra_body')
            if extra_body is None and self.extra_body:
                extra_body = self.extra_body
            
            if extra_body:
                api_kwargs["extra_body"] = extra_body
            
            response = self.client.chat.completions.create(**api_kwargs)
            
            elapsed_time = time.time() - start_time
            
            # 更新性能监控
            self.call_count += 1
            self.total_response_time += elapsed_time
            
            # 记录成功调用
            if response.usage:
                # 记录实际token使用与估算的对比
                actual_prompt_tokens = response.usage.prompt_tokens
                estimation_error = abs(actual_prompt_tokens - estimated_prompt_tokens)
                error_percentage = (estimation_error / actual_prompt_tokens * 100) if actual_prompt_tokens > 0 else 0
                
                logger.info(
                    f"API调用成功 - "
                    f"耗时: {elapsed_time:.2f}s, "
                    f"Tokens: {response.usage.total_tokens} "
                    f"(Prompt: {actual_prompt_tokens}, "
                    f"Completion: {response.usage.completion_tokens}), "
                    f"估算误差: {error_percentage:.1f}%"
                )
                
                # 如果估算误差过大，记录警告
                if error_percentage > 20:
                    logger.warning(f"Token估算误差较大: {error_percentage:.1f}% (估算: {estimated_prompt_tokens}, 实际: {actual_prompt_tokens})")
            else:
                logger.info(f"API调用成功 - 耗时: {elapsed_time:.2f}s")
            
            # 如果响应时间过长，记录警告
            if elapsed_time > 30:
                logger.warning(f"API响应时间较长: {elapsed_time:.2f}s，考虑优化上下文长度")
            
            return response
            
        except BadRequestError as e:
            # 400错误通常是提示词问题，不应该重试
            logger.error(f"Bad Request (不重试): {e}")
            raise
        except (RateLimitError, APIConnectionError, APITimeoutError, APIStatusError) as e:
            # 这些错误会触发重试
            logger.warning(f"可重试错误: {type(e).__name__}: {e}")
            raise
        except OpenAIError as e:
            # 其他OpenAI错误
            logger.error(f"OpenAI API错误: {type(e).__name__}: {e}")
            raise
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        统一的聊天接口
        
        Args:
            messages: OpenAI格式的消息列表
                Example: [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello!"}
                ]
            **kwargs: 可选参数
                - temperature: 温度参数
                - max_tokens: 最大token数
                - timeout: 超时时间
                - require_complete_response: 是否需要完整响应（默认True）
                - extra_body: 额外的API请求体参数，用于启用DeepSeek思考模式等特殊功能
                
        Returns:
            模型生成的文本内容
            
        Raises:
            OpenAIError: API调用失败
            ValueError: 响应为空或不完整
        """
        # 验证消息格式
        if not messages:
            raise ValueError("消息列表不能为空")
        
        for msg in messages:
            if 'role' not in msg or 'content' not in msg:
                raise ValueError("消息必须包含'role'和'content'字段")
        
        try:
            response = self._call_api(messages, **kwargs)
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("模型返回了空内容")
            
            # 检查响应是否完整
            require_complete = kwargs.get('require_complete_response', True)
            if require_complete and self._is_response_incomplete(content):
                logger.warning(f"检测到可能不完整的响应，长度: {len(content)} 字符")
                # 记录响应预览用于调试
                preview = content[:200] + "..." if len(content) > 200 else content
                logger.debug(f"响应预览: {preview}")
                
                # 检查是否因为max_tokens限制而被截断
                if response.usage and response.usage.completion_tokens >= kwargs.get('max_tokens', self.max_tokens) * 0.9:
                    logger.warning("响应可能因达到max_tokens限制而被截断")
                    raise ValueError(f"响应可能不完整（达到token限制）: {response.usage.completion_tokens}/{kwargs.get('max_tokens', settings.max_tokens)} tokens")
            
            return content
            
        except Exception as e:
            logger.error(f"聊天请求失败: {type(e).__name__}: {e}")
            raise
    
    def _is_response_incomplete(self, content: str) -> bool:
        """
        检查响应是否完整
        
        启发式规则：
        1. 检查是否以明显的截断标记结束
        2. 检查常见XML标签是否闭合
        3. 检查是否以完整句子结束（可选）
        
        Args:
            content: 要检查的文本内容
            
        Returns:
            如果响应可能不完整则返回True
        """
        if not content:
            return False
        
        trimmed = content.strip()
        if not trimmed:
            return False
        
        # 规则1: 检查是否以明显的截断标记结束
        truncation_indicators = ['...', '……', '---', '***', '[截断]', '[未完]', '[TO BE CONTINUED]']
        for indicator in truncation_indicators:
            if trimmed.endswith(indicator):
                logger.debug(f"检测到截断标记: {indicator}")
                return True
        
        # 规则2: 检查常见XML标签是否闭合（简化版）
        # 只检查我们关心的标签，不进行复杂的栈匹配
        import re
        
        # 检查<chapter>标签
        chapter_open = len(re.findall(r'<chapter>', content, re.IGNORECASE))
        chapter_close = len(re.findall(r'</chapter>', content, re.IGNORECASE))
        if chapter_open > chapter_close:
            logger.debug(f"<chapter>标签未闭合: 开{chapter_open}/闭{chapter_close}")
            return True
        
        # 检查<title>标签
        title_open = len(re.findall(r'<title>', content, re.IGNORECASE))
        title_close = len(re.findall(r'</title>', content, re.IGNORECASE))
        if title_open > title_close:
            logger.debug(f"<title>标签未闭合: 开{title_open}/闭{title_close}")
            return True
        
        # 检查<内容>标签（中文）
        content_cn_open = len(re.findall(r'<内容>', content))
        content_cn_close = len(re.findall(r'</内容>', content))
        if content_cn_open > content_cn_close:
            logger.debug(f"<内容>标签未闭合: 开{content_cn_open}/闭{content_cn_close}")
            return True
        
        # 规则3: 对于非XML内容，检查是否以完整句子结束
        # 如果内容很短或者明显是XML格式，跳过这个检查
        if len(trimmed) > 100 and '<' not in trimmed and '>' not in trimmed:
            last_char = trimmed[-1]
            sentence_enders = ['。', '.', '！', '!', '？', '?', '"', "'", '」', '》', '”', '》']
            if last_char not in sentence_enders:
                # 检查是否以换行结束
                if not trimmed.endswith('\n'):
                    logger.debug(f"可能以不完整句子结束: 最后一个字符'{last_char}'")
                    return True
        
        return False
    
    def simple_chat(self, user_message: str, system_message: Optional[str] = None, **kwargs) -> str:
        """
        简化版的聊天接口
        
        Args:
            user_message: 用户消息
            system_message: 系统消息（可选）
            **kwargs: 其他参数传递给chat方法
            
        Returns:
            模型生成的文本内容
        """
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": user_message})
        
        return self.chat(messages, **kwargs)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns:
            包含性能统计的字典
        """
        avg_response_time = 0.0
        if self.call_count > 0:
            avg_response_time = self.total_response_time / self.call_count
        
        return {
            "call_count": self.call_count,
            "total_response_time": self.total_response_time,
            "average_response_time": avg_response_time,
            "model": self.model,
            "last_error_time": self.last_error_time
        }
    
    def test_connection(self, test_message: str = "Hello, are you online?") -> Dict[str, Any]:
        """
        测试API连接
        
        Args:
            test_message: 测试消息
            
        Returns:
            包含测试结果的字典
        """
        try:
            start_time = time.time()
            
            response = self.simple_chat(
                user_message=test_message,
                system_message="You are a helpful assistant. Respond briefly.",
                max_tokens=50
            )
            
            elapsed_time = time.time() - start_time
            
            return {
                "success": True,
                "response": response,
                "response_time": elapsed_time,
                "model": self.model,
                "base_url": self.client.base_url
            }
            
        except Exception as e:
            # 记录错误时间
            self.last_error_time = time.time()
            
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "model": self.model,
                "base_url": self.client.base_url
            }