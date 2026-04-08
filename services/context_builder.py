"""
上下文构建器 - 负责构建LLM消息上下文
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class ContextBuilder:
    """上下文构建器 - 构建发送给LLM的消息列表"""
    
    def __init__(self, state_manager, feedback_manager, prompt_logger, 
                 history_manager, prompt_renderer):
        """
        初始化上下文构建器
        
        Args:
            state_manager: 状态管理器实例
            feedback_manager: 反馈管理器实例
            prompt_logger: 提示词日志记录器实例
            history_manager: 历史记录管理器实例
            prompt_renderer: 提示词渲染器实例
        """
        self.state_manager = state_manager
        self.feedback_manager = feedback_manager
        self.prompt_logger = prompt_logger
        self.history_manager = history_manager
        self.prompt_renderer = prompt_renderer
    
    def build_messages(self) -> List[Dict[str, str]]:
        """
        构建发送给LLM的消息列表
        
        返回格式: [{"role": "system", "content": "..."}, ...]
        实现智能上下文修剪，确保不超过上下文限制
        
        优先级：
        1. 基准上下文（系统提示词 + 预热对话） - 必须保留
        2. 读者反馈（作为特殊的系统消息） - 在基准上下文之后插入
        3. 关键世界观设定消息（第11条BASE消息） - 必须保留
        4. 最近的对话（当前窗口内的章节） - 优先保留
        5. 其他历史消息 - 按时间顺序保留，直到达到限制
        """
        # 加载完整历史记录
        full_history = self.history_manager.load_history()
        
        if not full_history:
            return []
        
        # 获取基准上下文长度
        base_context_length = self.state_manager.get_base_context_length()
        if base_context_length <= 0:
            base_context_length = 1  # 至少包含系统消息
        
        # 识别关键世界观设定消息（第11条BASE消息）
        # 查找包含"主角叫刘斗斗"或"书名叫《诸天：我跷着二郎腿镇压万界》"的消息
        critical_messages_indices = []
        for i, msg in enumerate(full_history):
            content = msg.get("content", "")
            if "主角叫刘斗斗" in content or "书名叫《诸天：我跷着二郎腿镇压万界》" in content:
                critical_messages_indices.append(i)
                logger.debug(f"识别到关键世界观消息索引: {i}")
        
        # 获取当前窗口章节
        window_chapters = self.state_manager.get_window_chapters()
        current_chapter = self.state_manager.get_chapter_num()
        
        # 估算token数并构建消息列表
        messages = []
        total_estimated_tokens = 0
        max_context_tokens = 128000  # DeepSeek Chat的最大上下文
        
        # 安全边际：保留10%的上下文用于输出
        max_prompt_tokens = int(max_context_tokens * 0.9)
        
        # 辅助函数：估算消息的token数
        def estimate_tokens(text: str) -> int:
            # 粗略估算：1个token≈4个字符
            return len(text) // 4
        
        # 第一阶段：添加基准上下文（必须保留）
        for i in range(min(base_context_length, len(full_history))):
            msg = full_history[i]
            msg_tokens = estimate_tokens(msg.get("content", ""))
            
            if total_estimated_tokens + msg_tokens <= max_prompt_tokens:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
                total_estimated_tokens += msg_tokens
                logger.debug(f"添加基准上下文消息 {i}: {msg_tokens} tokens")
            else:
                logger.warning(f"基准上下文消息 {i} 超出token限制，跳过")
        
        # 第二阶段：添加读者反馈（作为特殊的系统消息）
        feedback_content = self._get_feedback_for_context()
        if feedback_content:
            feedback_tokens = estimate_tokens(feedback_content)
            
            if total_estimated_tokens + feedback_tokens <= max_prompt_tokens:
                # 使用模板渲染反馈消息
                feedback_template = self.prompt_renderer.load_feedback_prompt_template()
                feedback_message_content = feedback_template.replace("{{feedback_content}}", feedback_content)
                
                # 创建反馈消息，使用system角色，但标记为反馈上下文
                feedback_message = {
                    "role": "system",
                    "content": feedback_message_content,
                    "is_feedback_context": True
                }
                messages.append(feedback_message)
                total_estimated_tokens += feedback_tokens
                logger.info(f"添加读者反馈消息: {feedback_tokens} tokens")
                
                # 新增：保存反馈到历史记录，标记为feedback阶段
                # 章节号设为0，表示不属于特定章节
                # 使用特殊的stage="feedback"标记，便于在剪枝时识别和删除
                self.history_manager.add_message(
                    role="system",
                    content=feedback_message_content,
                    chapter_num=0,
                    stage="feedback",
                    is_base_context=False,
                    is_feedback_context=True
                )
                logger.info(f"读者反馈已保存到历史记录，标记为feedback阶段")
            else:
                logger.warning(f"读者反馈超出token限制，跳过")
        
        # 第三阶段：添加关键世界观设定消息（必须保留）
        for idx in critical_messages_indices:
            if idx < base_context_length:  # 已经在基准上下文中
                continue
                
            msg = full_history[idx]
            msg_tokens = estimate_tokens(msg.get("content", ""))
            
            if total_estimated_tokens + msg_tokens <= max_prompt_tokens:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
                total_estimated_tokens += msg_tokens
                logger.debug(f"添加关键世界观消息 {idx}: {msg_tokens} tokens")
            else:
                logger.warning(f"关键世界观消息 {idx} 超出token限制，强制添加（可能超过限制）")
                # 强制添加，即使超过限制
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
                total_estimated_tokens += msg_tokens
        
        # 第四阶段：添加当前窗口章节的消息（优先保留）
        window_message_indices = []
        for i, msg in enumerate(full_history):
            chapter = msg.get("chapter", 0)
            if chapter in window_chapters:
                window_message_indices.append(i)
        
        # 按时间顺序添加窗口消息
        for idx in window_message_indices:
            if idx < base_context_length or idx in critical_messages_indices:
                continue  # 已经添加过了
                
            msg = full_history[idx]
            msg_tokens = estimate_tokens(msg.get("content", ""))
            
            if total_estimated_tokens + msg_tokens <= max_prompt_tokens:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
                total_estimated_tokens += msg_tokens
                logger.debug(f"添加窗口消息 {idx} (第{msg.get('chapter', 0)}章): {msg_tokens} tokens")
            else:
                logger.debug(f"窗口消息 {idx} 超出token限制，跳过")
        
        # 第五阶段：添加其他历史消息（按时间顺序，直到达到限制）
        for i, msg in enumerate(full_history):
            # 跳过已经添加的消息
            if i < base_context_length or i in critical_messages_indices or i in window_message_indices:
                continue
                
            msg_tokens = estimate_tokens(msg.get("content", ""))
            
            if total_estimated_tokens + msg_tokens <= max_prompt_tokens:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
                total_estimated_tokens += msg_tokens
                logger.debug(f"添加其他历史消息 {i}: {msg_tokens} tokens")
            else:
                # 达到限制，停止添加
                logger.debug(f"达到token限制 ({total_estimated_tokens}/{max_prompt_tokens})，停止添加更多消息")
                break
        
        logger.info(f"构建了 {len(messages)} 条消息给LLM，估算 {total_estimated_tokens} tokens")
        logger.debug(f"消息构成: {len(messages)} 条，基准上下文: {min(base_context_length, len(full_history))} 条，反馈: {1 if feedback_content else 0} 条，关键世界观: {len(critical_messages_indices)} 条，窗口消息: {len(window_message_indices)} 条")
        
        return messages
    
    def _get_feedback_for_context(self) -> str:
        """
        获取用于上下文的读者反馈
        
        返回:
            str: 读者反馈内容，如果没有可用反馈则返回空字符串
        """
        chapter_num = self.state_manager.get_chapter_num()
        
        # 检查是否需要更新反馈（每10章更新一次）
        should_update = self.state_manager.should_update_feedback_for_chapter(chapter_num)
        
        if not should_update:
            # 使用上次的反馈
            last_feedback_chapter = self.state_manager.get_last_used_feedback_chapter()
            last_feedback_index = self.state_manager.get_last_used_feedback_index()
            
            if last_feedback_chapter > 0:
                logger.info(f"第{chapter_num}章使用上次的反馈（来自第{last_feedback_chapter}章，索引{last_feedback_index}）")
                return ""  # 返回空字符串，表示使用上次的反馈（在消息构建时会处理）
        
        # 需要获取新的反馈
        feedback = ""
        try:
            # 先重新同步反馈状态，确保已使用索引与当前文件一致
            self.feedback_manager.resync_with_feedback_file()
            
            # 获取可用反馈列表
            available_feedbacks = self.feedback_manager.get_available_feedbacks()
            
            if available_feedbacks:
                # 使用pop机制抽取一条反馈
                feedback = self.feedback_manager.pop_feedback()
                if feedback:
                    # 获取反馈索引（pop_feedback会返回反馈内容，但我们需要知道是哪个索引）
                    # 这里简化处理：假设pop_feedback返回的就是最新抽取的反馈
                    # 实际实现中，FeedbackManager应该提供获取当前已使用索引的方法
                    logger.info(f"第{chapter_num}章抽取到新的读者反馈: {feedback[:50]}...")
                    
                    # 更新状态中的反馈使用信息
                    # 这里简化处理：使用章节号作为反馈来源标识
                    self.state_manager.set_last_used_feedback_chapter(chapter_num)
                    # 索引信息需要从FeedbackManager获取
                    # 暂时设置为1，表示使用了反馈
                    self.state_manager.set_last_used_feedback_index(1)
                    
                    # 记录反馈使用日志
                    self.prompt_logger.log_feedback_usage(
                        chapter_num=chapter_num,
                        feedback_length=len(feedback),
                        feedback_preview=feedback[:100] if feedback else ""
                    )
                else:
                    logger.info(f"第{chapter_num}章没有可用的读者反馈")
            else:
                logger.info(f"第{chapter_num}章没有可用的读者反馈")
        except Exception as e:
            logger.warning(f"抽取读者反馈失败: {e}")
            # 后备方案：尝试读取整个反馈文件
            feedback_path = self.history_manager.data_dir / "feedback.txt"
            if feedback_path.exists():
                try:
                    with open(feedback_path, 'r', encoding='utf-8') as f:
                        feedback = f.read().strip()
                        if feedback:
                            logger.info(f"使用后备方案读取反馈文件: {len(feedback)} 字符")
                except Exception as read_error:
                    logger.warning(f"后备方案读取反馈文件也失败: {read_error}")
        
        return feedback