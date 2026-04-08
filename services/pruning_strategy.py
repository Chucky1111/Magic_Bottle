"""
修剪策略模块 - 实现智能上下文修剪算法

核心职责：
1. 识别不同类型的消息（基准上下文、关键世界观、窗口章节等）
2. 执行修剪逻辑，保留必要消息，删除过期消息
3. 验证修剪结果，确保系统完整性
"""

import logging
import time
from typing import Dict, List, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型枚举"""
    BASE_CONTEXT = "base_context"      # 基准上下文（系统提示词 + 预热对话）
    CRITICAL_WORLDVIEW = "critical"    # 关键世界观消息
    WINDOW_CHAPTER = "window_chapter"  # 窗口章节消息
    SUMMARY = "summary"                # 总结消息
    TO_BE_REMOVED = "to_be_removed"    # 待删除消息
    OTHER = "other"                    # 其他消息


@dataclass
class MessageClassification:
    """消息分类结果"""
    message: Dict[str, Any]
    index: int
    message_type: MessageType
    chapter: int
    stage: str
    is_base_context: bool


class PruningStrategy:
    """修剪策略基类"""
    
    def __init__(self, base_context_length: int, critical_keywords: List[str] = None):
        """
        初始化修剪策略
        
        Args:
            base_context_length: 基准上下文长度
            critical_keywords: 关键世界观关键词列表
        """
        self.base_context_length = base_context_length
        self.critical_keywords = critical_keywords or [
            "主角叫刘斗斗",
            "书名叫《诸天：我跷着二郎腿镇压万界》"
        ]
    
    def classify_message(self, message: Dict[str, Any], index: int) -> MessageClassification:
        """
        分类单个消息
        
        Args:
            message: 消息字典
            index: 消息在历史记录中的索引
            
        Returns:
            MessageClassification: 消息分类结果
        """
        chapter = message.get("chapter", 0)
        stage = message.get("stage", "")
        is_base_context = message.get("is_base_context", False)
        content = message.get("content", "")
        
        # 检查是否为基准上下文
        if index < self.base_context_length:
            return MessageClassification(
                message=message,
                index=index,
                message_type=MessageType.BASE_CONTEXT,
                chapter=chapter,
                stage=stage,
                is_base_context=is_base_context
            )
        
        # 检查是否为关键世界观消息
        if any(keyword in content for keyword in self.critical_keywords):
            return MessageClassification(
                message=message,
                index=index,
                message_type=MessageType.CRITICAL_WORLDVIEW,
                chapter=chapter,
                stage=stage,
                is_base_context=is_base_context
            )
        
        # 检查是否为总结消息
        # 总结消息的特征：stage == "summary" 或者有 is_summary 标记
        # 注意：新的总结格式中 chapter 可能不是0，而是关联到具体章节
        is_summary = message.get("is_summary", False)
        if stage == "summary" or is_summary:
            return MessageClassification(
                message=message,
                index=index,
                message_type=MessageType.SUMMARY,
                chapter=chapter,
                stage=stage,
                is_base_context=is_base_context
            )
        
        # 默认类型为OTHER，具体类型由子类决定
        return MessageClassification(
            message=message,
            index=index,
            message_type=MessageType.OTHER,
            chapter=chapter,
            stage=stage,
            is_base_context=is_base_context
        )
    
    def prune(self, history: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """
        执行修剪逻辑（抽象方法）
        
        Args:
            history: 完整历史记录
            **kwargs: 其他参数
            
        Returns:
            List[Dict[str, Any]]: 修剪后的历史记录
        """
        raise NotImplementedError("子类必须实现prune方法")
    
    def validate_pruned_history(self, pruned_history: List[Dict[str, Any]], 
                               original_length: int) -> bool:
        """
        验证修剪后的历史记录
        
        Args:
            pruned_history: 修剪后的历史记录
            original_length: 原始历史记录长度
            
        Returns:
            bool: 验证是否通过
        """
        if not pruned_history:
            logger.warning("修剪后的历史记录为空")
            return False
        
        # 检查基准上下文是否保留
        if len(pruned_history) < self.base_context_length:
            logger.warning(f"修剪后历史记录长度({len(pruned_history)})小于基准上下文长度({self.base_context_length})")
            return False
        
        # 检查关键世界观消息是否保留
        has_critical = any(
            any(keyword in msg.get("content", "") for keyword in self.critical_keywords)
            for msg in pruned_history
        )
        if not has_critical:
            logger.warning("修剪后历史记录中缺少关键世界观消息")
            # 不返回False，因为可能确实没有关键世界观消息
        
        logger.info(f"修剪验证通过: {len(pruned_history)}/{original_length} 条消息")
        return True


class SlidingWindowPruner(PruningStrategy):
    """滑动窗口修剪器 - 实现三章窗口修剪逻辑"""
    
    def __init__(self, base_context_length: int, window_chapters: List[int], 
                 critical_keywords: List[str] = None):
        """
        初始化滑动窗口修剪器
        
        Args:
            base_context_length: 基准上下文长度
            window_chapters: 窗口章节列表 [chapter_1, chapter_2, chapter_3]
            critical_keywords: 关键世界观关键词列表
        """
        super().__init__(base_context_length, critical_keywords)
        
        if len(window_chapters) != 3:
            raise ValueError(f"窗口章节数量必须为3，实际为: {window_chapters}")
        
        self.window_chapters = window_chapters
        self.chapter_1, self.chapter_2, self.chapter_3 = window_chapters
        self.chapters_to_remove = [self.chapter_1, self.chapter_2]
    
    def classify_message(self, message: Dict[str, Any], index: int) -> MessageClassification:
        """
        分类单个消息（重写以包含窗口章节逻辑）
        """
        classification = super().classify_message(message, index)
        
        # 如果已经是特定类型，直接返回
        if classification.message_type != MessageType.OTHER:
            return classification
        
        chapter = classification.chapter
        
        # 检查是否为窗口章节消息
        if chapter == self.chapter_3:
            return MessageClassification(
                message=message,
                index=index,
                message_type=MessageType.WINDOW_CHAPTER,
                chapter=chapter,
                stage=classification.stage,
                is_base_context=classification.is_base_context
            )
        
        # 检查是否为待删除章节消息
        if chapter in self.chapters_to_remove:
            return MessageClassification(
                message=message,
                index=index,
                message_type=MessageType.TO_BE_REMOVED,
                chapter=chapter,
                stage=classification.stage,
                is_base_context=classification.is_base_context
            )
        
        # 其他消息（可能是旧的已修剪章节）
        return classification
    
    def _validate_summary_selection(self, summary_messages: List[MessageClassification],
                                   selected_summary: MessageClassification) -> bool:
        """
        验证总结消息选择是否合理

        Args:
            summary_messages: 所有总结消息列表（未排序）
            selected_summary: 选择的总结消息

        Returns:
            bool: 验证是否通过
        """
        if not summary_messages:
            return True

        if len(summary_messages) == 1:
            # 只有一条总结消息，无需验证
            return True

        # 模拟prune方法中的优先级逻辑来确定"正确"的选择
        # 优先级顺序：
        # 1. 当前窗口的总结（window_chapters == self.window_chapters）
        # 2. 上一个窗口的总结（窗口章节包含当前第三章）
        # 3. 按章节号排序的最新总结
        
        # 分类总结消息（与prune方法相同的逻辑）
        current_window_summary = None
        previous_window_summary = None
        other_summaries = []
        
        for classification in summary_messages:
            window_chapters = classification.message.get("window_chapters", [])
            
            # 检查是否为当前窗口的总结
            if window_chapters == self.window_chapters:
                current_window_summary = classification
                continue
            
            # 检查是否为上一个窗口的总结（窗口章节包含当前第三章）
            if len(window_chapters) == 3 and window_chapters[2] == self.chapter_3:
                previous_window_summary = classification
                continue
            
            # 其他总结
            other_summaries.append(classification)
        
        # 确定"正确"的选择（与prune方法相同的逻辑）
        correct_summary = None
        
        # 优先级1：当前窗口的总结
        if current_window_summary:
            correct_summary = current_window_summary
        
        # 优先级2：上一个窗口的总结
        elif previous_window_summary:
            correct_summary = previous_window_summary
        
        # 优先级3：按summary_chapter字段排序的最新总结
        else:
            # 对剩余总结按summary_chapter降序排序（关联章节号更大的更接近当前窗口）
            # 如果summary_chapter不存在，则使用timestamp作为后备
            other_summaries.sort(
                key=lambda c: (
                    c.message.get("summary_chapter", 0),  # 主要按关联章节号
                    c.message.get("timestamp", 0),  # 次要按时间戳
                    c.index,  # 索引
                    len(c.message.get("content", ""))  # 内容长度
                ),
                reverse=True  # 降序排列，最大的（最新的）在最前面
            )
            
            if other_summaries:
                correct_summary = other_summaries[0]
        
        # 如果没有找到正确的总结，说明有问题
        if not correct_summary:
            logger.error("验证逻辑错误：无法确定正确的总结选择")
            return False
        
        # 检查选择的总结是否正确
        if correct_summary.index != selected_summary.index:
            logger.error(f"总结选择验证失败: 选择的总结索引({selected_summary.index}) "
                        f"不是正确的选择({correct_summary.index})")
            
            # 记录详细信息用于调试
            logger.error("验证详情:")
            logger.error(f"  当前窗口章节: {self.window_chapters}")
            logger.error(f"  选择的总结: 索引={selected_summary.index}, 章节={selected_summary.chapter}, "
                        f"窗口章节={selected_summary.message.get('window_chapters', [])}")
            logger.error(f"  正确的总结: 索引={correct_summary.index}, 章节={correct_summary.chapter}, "
                        f"窗口章节={correct_summary.message.get('window_chapters', [])}")
            
            # 记录所有总结消息的信息
            logger.error("所有总结消息:")
            for i, msg in enumerate(summary_messages):
                chapter = msg.chapter
                timestamp = msg.message.get("timestamp", 0)
                index = msg.index
                content_len = len(msg.message.get("content", ""))
                window_chapters = msg.message.get("window_chapters", [])
                is_selected = msg.index == selected_summary.index
                is_correct = msg.index == correct_summary.index
                logger.error(f"  第{i+1}条: chapter={chapter}, timestamp={timestamp}, index={index}, "
                           f"content_len={content_len}, window_chapters={window_chapters}, "
                           f"selected={is_selected}, correct={is_correct}")
            
            return False

        # 检查时间戳是否合理（不应该有未来的时间戳）
        current_time = time.time()
        timestamps = [msg.message.get("timestamp", 0) for msg in summary_messages]
        future_summaries = [t for t in timestamps if t > current_time + 3600]  # 1小时容差

        if future_summaries:
            logger.warning(f"发现未来时间戳的总结消息: {future_summaries}")

        # 检查是否有相同章节号但选择了错误的总结
        same_chapter_messages = [msg for msg in summary_messages if msg.chapter == selected_summary.chapter]

        if len(same_chapter_messages) > 1:
            logger.warning(f"发现{len(same_chapter_messages)}条相同章节号的总结消息")
            # 在这种情况下，应该选择时间戳最大的
            max_timestamp = max(msg.message.get("timestamp", 0) for msg in same_chapter_messages)
            selected_timestamp = selected_summary.message.get("timestamp", 0)
            if abs(selected_timestamp - max_timestamp) > 0.001:
                logger.warning(f"相同章节号的总结中，没有选择时间戳最大的({max_timestamp})，而是选择了{selected_timestamp}")

        # 新增：验证总结内容是否与窗口章节相关
        if not self._validate_summary_content_relevance(selected_summary):
            logger.warning("总结内容与窗口章节关联性验证失败，但继续执行（可能是LLM生成问题）")

        logger.info(f"总结选择验证通过: 选择了正确的总结(章节{selected_summary.chapter})")
        return True

    def _validate_summary_content_relevance(self, summary: MessageClassification) -> bool:
        """
        验证总结内容是否与窗口章节相关

        Args:
            summary: 总结消息分类

        Returns:
            bool: 验证是否通过
        """
        content = summary.message.get("content", "")
        window_chapters = summary.message.get("window_chapters", [])
        
        if not window_chapters:
            # 没有window_chapters字段，无法验证
            return True
        
        # 检查总结内容是否提到窗口章节
        content_lower = content.lower()
        
        # 检查是否提到窗口章节号
        for chapter in window_chapters:
            if str(chapter) in content:
                return True
        
        # 检查是否提到常见的章节相关关键词
        chapter_keywords = ["第", "章", "章节", "单元", "故事", "情节", "人物"]
        if any(keyword in content_lower for keyword in chapter_keywords):
            return True
        
        # 检查内容长度是否合理（太短可能有问题）
        if len(content) < 100:
            logger.warning(f"总结内容过短: {len(content)} 字符，可能不是有效的总结")
            return False
        
        # 检查是否包含明显的错误模式（如完全重复的总结）
        # 这里可以添加更复杂的检查逻辑
        
        return True
    
    def prune(self, history: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """
        执行滑动窗口修剪逻辑
        
        Args:
            history: 完整历史记录
            **kwargs: 其他参数
            
        Returns:
            List[Dict[str, Any]]: 修剪后的历史记录
        """
        logger.info(f"开始滑动窗口修剪: 窗口章节={self.window_chapters}, 删除章节={self.chapters_to_remove}")
        
        # 分类所有消息
        classifications = []
        for i, msg in enumerate(history):
            classification = self.classify_message(msg, i)
            classifications.append(classification)
        
        # 按类型分组
        messages_by_type = {}
        for classification in classifications:
            msg_type = classification.message_type
            if msg_type not in messages_by_type:
                messages_by_type[msg_type] = []
            messages_by_type[msg_type].append(classification)
        
        # 构建新的历史记录（按优先级顺序）
        new_history = []
        
        # 1. 添加基准上下文消息
        base_messages = messages_by_type.get(MessageType.BASE_CONTEXT, [])
        for classification in base_messages:
            new_history.append(classification.message)
            logger.debug(f"保留基准上下文消息 {classification.index}: {classification.stage}")
        
        # 2. 添加关键世界观消息
        critical_messages = messages_by_type.get(MessageType.CRITICAL_WORLDVIEW, [])
        for classification in critical_messages:
            new_history.append(classification.message)
            logger.debug(f"保留关键世界观消息 {classification.index}: 第{classification.chapter}章 {classification.stage}")
        
        # 3. 添加第三章消息（只保留写作阶段）
        window_messages = messages_by_type.get(MessageType.WINDOW_CHAPTER, [])
        for classification in window_messages:
            # 只保留写作阶段消息，删除反思阶段消息
            if classification.stage == "write":
                new_history.append(classification.message)
                logger.debug(f"保留第三章写作消息 {classification.index}: 第{classification.chapter}章 {classification.stage}")
            else:
                logger.debug(f"删除第三章反思消息 {classification.index}: 第{classification.chapter}章 {classification.stage}")
        
        # 4. 处理总结消息 - 增强窗口关联性检查（支持同一窗口内多个总结）
        summary_messages = messages_by_type.get(MessageType.SUMMARY, [])
        if summary_messages:
            # 增强的排序逻辑：优先考虑窗口关联性
            # 1. 首先检查是否有关联到当前窗口的总结
            # 2. 其次检查是否有关联到包含当前第三章的窗口的总结
            # 3. 最后按章节号降序（新的总结章节号更大）
            # 4. 章节号相同时，按时间戳降序
            # 5. 时间戳相同时，按索引降序（后出现的优先）
            # 6. 最后按内容长度降序
            
            # 分类总结消息
            current_window_summaries = []   # 当前窗口的所有总结
            previous_window_summary = None  # 上一个窗口的总结（最多一个）
            other_summaries = []            # 其他总结
            
            for classification in summary_messages:
                window_chapters = classification.message.get("window_chapters", [])
                
                # 检查是否为当前窗口的总结
                if window_chapters == self.window_chapters:
                    current_window_summaries.append(classification)
                    logger.debug(f"找到当前窗口的总结: 索引{classification.index}, 窗口章节{window_chapters}")
                    continue
                
                # 检查是否为上一个窗口的总结（窗口章节包含当前第三章）
                if len(window_chapters) == 3 and window_chapters[2] == self.chapter_3:
                    # 只保留一个上一个窗口的总结（如果有多个，选择最新的）
                    if previous_window_summary is None:
                        previous_window_summary = classification
                        logger.debug(f"找到上一个窗口的总结: 索引{classification.index}, 窗口章节{window_chapters}")
                    else:
                        # 如果有多个上一个窗口的总结，选择状态编号最大的（最新的）
                        if classification.message.get("summary_status", 0) > previous_window_summary.message.get("summary_status", 0):
                            logger.debug(f"替换上一个窗口的总结: 旧索引{previous_window_summary.index} -> 新索引{classification.index}")
                            previous_window_summary = classification
                    continue
                
                # 其他总结
                other_summaries.append(classification)
            
            # 确定要保留的总结列表
            selected_summaries = []
            
            # 优先级1：当前窗口的所有总结
            if current_window_summaries:
                selected_summaries.extend(current_window_summaries)
                logger.info(f"保留当前窗口的所有总结: {len(current_window_summaries)} 条")
            
            # 优先级2：上一个窗口的总结（仅当没有当前窗口总结时）
            elif previous_window_summary:
                selected_summaries.append(previous_window_summary)
                logger.info(f"保留上一个窗口的总结: 索引{previous_window_summary.index}, 窗口章节{previous_window_summary.message.get('window_chapters', [])}")
            
            # 优先级3：按summary_chapter字段排序的最新总结
            else:
                # 对剩余总结按summary_chapter降序排序（关联章节号更大的更接近当前窗口）
                # 如果summary_chapter不存在，则使用timestamp作为后备
                other_summaries.sort(
                    key=lambda c: (
                        c.message.get("summary_chapter", 0),  # 主要按关联章节号
                        c.message.get("timestamp", 0),  # 次要按时间戳
                        c.index,  # 索引
                        len(c.message.get("content", ""))  # 内容长度
                    ),
                    reverse=True  # 降序排列，最大的（最新的）在最前面
                )
                
                if other_summaries:
                    selected_summaries.append(other_summaries[0])
                    summary_chapter = other_summaries[0].message.get("summary_chapter", 0)
                    window_chapters = other_summaries[0].message.get("window_chapters", [])
                    logger.info(f"保留关联章节最新的总结: 索引{other_summaries[0].index}, 关联章节{summary_chapter}, 窗口章节{window_chapters}")
                else:
                    logger.warning("没有找到可用的总结消息")
            
            # 如果找到了总结，添加到新历史记录
            if selected_summaries:
                # 验证选择是否合理（仅当选择单个总结时）
                if len(selected_summaries) == 1:
                    if not self._validate_summary_selection(summary_messages, selected_summaries[0]):
                        logger.warning("总结选择验证失败，但继续执行")
                
                for selected_summary in selected_summaries:
                    new_history.append(selected_summary.message)
                    logger.info(f"保留总结消息 {selected_summary.index} "
                               f"(chapter: {selected_summary.chapter}, "
                               f"window_chapters: {selected_summary.message.get('window_chapters', [])}, "
                               f"timestamp: {selected_summary.message.get('timestamp', 0)})")
                
                # 记录被删除的旧总结
                deleted_count = 0
                for classification in summary_messages:
                    if not any(classification.index == selected_summary.index for selected_summary in selected_summaries):
                        logger.debug(f"删除旧总结消息 {classification.index} "
                                   f"(chapter: {classification.chapter}, "
                                   f"window_chapters: {classification.message.get('window_chapters', [])}, "
                                   f"timestamp: {classification.message.get('timestamp', 0)})")
                        deleted_count += 1
                
                if deleted_count > 0:
                    logger.info(f"删除了 {deleted_count} 条旧总结消息")
            else:
                logger.warning("没有选择任何总结消息，可能存在问题")
        
        # 5. 记录待删除消息
        to_be_removed = messages_by_type.get(MessageType.TO_BE_REMOVED, [])
        for classification in to_be_removed:
            logger.debug(f"删除前两章消息 {classification.index}: 第{classification.chapter}章 {classification.stage}")
        
        # 6. 记录其他消息（旧的已修剪章节）
        other_messages = messages_by_type.get(MessageType.OTHER, [])
        for classification in other_messages:
            logger.debug(f"删除其他消息 {classification.index}: 第{classification.chapter}章 {classification.stage}")
        
        logger.info(f"修剪完成: 原始 {len(history)} 条 -> 保留 {len(new_history)} 条")
        return new_history
    
    def get_pruning_statistics(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取修剪统计信息
        
        Args:
            history: 完整历史记录
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        classifications = []
        for i, msg in enumerate(history):
            classification = self.classify_message(msg, i)
            classifications.append(classification)
        
        # 统计各类型消息数量
        stats = {
            "total_messages": len(history),
            "base_context_messages": 0,
            "critical_worldview_messages": 0,
            "window_chapter_messages": 0,
            "summary_messages": 0,
            "to_be_removed_messages": 0,
            "other_messages": 0
        }
        
        for classification in classifications:
            msg_type = classification.message_type
            if msg_type == MessageType.BASE_CONTEXT:
                stats["base_context_messages"] += 1
            elif msg_type == MessageType.CRITICAL_WORLDVIEW:
                stats["critical_worldview_messages"] += 1
            elif msg_type == MessageType.WINDOW_CHAPTER:
                stats["window_chapter_messages"] += 1
            elif msg_type == MessageType.SUMMARY:
                stats["summary_messages"] += 1
            elif msg_type == MessageType.TO_BE_REMOVED:
                stats["to_be_removed_messages"] += 1
            elif msg_type == MessageType.OTHER:
                stats["other_messages"] += 1
        
        return stats


class StatusBasedPruner(SlidingWindowPruner):
    """基于状态排序的修剪器"""
    
    def prune(self, history: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """基于状态编号选择总结（支持同一窗口内多个总结）"""
        
        logger.info(f"开始基于状态排序的修剪: 窗口章节={self.window_chapters}, 删除章节={self.chapters_to_remove}")
        
        # 分类所有消息
        classifications = []
        for i, msg in enumerate(history):
            classification = self.classify_message(msg, i)
            classifications.append(classification)
        
        # 按类型分组
        messages_by_type = {}
        for classification in classifications:
            msg_type = classification.message_type
            if msg_type not in messages_by_type:
                messages_by_type[msg_type] = []
            messages_by_type[msg_type].append(classification)
        
        # 构建新的历史记录（按优先级顺序）
        new_history = []
        
        # 1. 添加基准上下文消息
        base_messages = messages_by_type.get(MessageType.BASE_CONTEXT, [])
        for classification in base_messages:
            new_history.append(classification.message)
            logger.debug(f"保留基准上下文消息 {classification.index}: {classification.stage}")
        
        # 2. 添加关键世界观消息
        critical_messages = messages_by_type.get(MessageType.CRITICAL_WORLDVIEW, [])
        for classification in critical_messages:
            new_history.append(classification.message)
            logger.debug(f"保留关键世界观消息 {classification.index}: 第{classification.chapter}章 {classification.stage}")
        
        # 3. 添加第三章消息（只保留写作阶段）
        window_messages = messages_by_type.get(MessageType.WINDOW_CHAPTER, [])
        for classification in window_messages:
            # 只保留写作阶段消息，删除反思阶段消息
            if classification.stage == "write":
                new_history.append(classification.message)
                logger.debug(f"保留第三章写作消息 {classification.index}: 第{classification.chapter}章 {classification.stage}")
            else:
                logger.debug(f"删除第三章反思消息 {classification.index}: 第{classification.chapter}章 {classification.stage}")
        
        # 4. 处理总结消息 - 按状态编号排序，支持同一窗口内多个总结
        summary_messages = messages_by_type.get(MessageType.SUMMARY, [])
        if summary_messages:
            # 分类总结消息
            current_window_summaries = []   # 当前窗口的所有总结
            previous_window_summary = None  # 上一个窗口的总结（最多一个）
            other_summaries = []            # 其他总结
            
            for classification in summary_messages:
                window_chapters = classification.message.get("window_chapters", [])
                
                # 检查是否为当前窗口的总结
                if window_chapters == self.window_chapters:
                    current_window_summaries.append(classification)
                    logger.debug(f"找到当前窗口的总结: 索引{classification.index}, 窗口章节{window_chapters}")
                    continue
                
                # 检查是否为上一个窗口的总结（窗口章节包含当前第三章）
                if len(window_chapters) == 3 and window_chapters[2] == self.chapter_3:
                    # 只保留一个上一个窗口的总结（如果有多个，选择状态编号最大的）
                    if previous_window_summary is None:
                        previous_window_summary = classification
                    else:
                        if classification.message.get("summary_status", 0) > previous_window_summary.message.get("summary_status", 0):
                            previous_window_summary = classification
                    continue
                
                # 其他总结
                other_summaries.append(classification)
            
            # 确定要保留的总结列表
            selected_summaries = []
            
            # 优先级1：当前窗口的所有总结
            if current_window_summaries:
                # 按状态编号降序排序（可选，确保顺序一致）
                current_window_summaries.sort(
                    key=lambda c: c.message.get("summary_status", 0),
                    reverse=True
                )
                selected_summaries.extend(current_window_summaries)
                logger.info(f"保留当前窗口的所有总结: {len(current_window_summaries)} 条")
            
            # 优先级2：上一个窗口的总结（仅当没有当前窗口总结时）
            elif previous_window_summary:
                selected_summaries.append(previous_window_summary)
                logger.info(f"保留上一个窗口的总结: 索引{previous_window_summary.index}, 状态={previous_window_summary.message.get('summary_status', 0)}")
            
            # 优先级3：按状态编号排序的最新总结
            else:
                # 按状态编号降序排序（状态编号越大越新）
                other_summaries.sort(
                    key=lambda c: c.message.get("summary_status", 0),
                    reverse=True
                )
                
                if other_summaries:
                    selected_summaries.append(other_summaries[0])
                    summary_status = other_summaries[0].message.get("summary_status", 0)
                    window_chapters = other_summaries[0].message.get("window_chapters", [])
                    logger.info(f"保留状态最新的总结: 索引{other_summaries[0].index}, 状态={summary_status}, 窗口章节={window_chapters}")
                else:
                    logger.warning("没有找到可用的总结消息")
            
            # 如果找到了总结，添加到新历史记录
            if selected_summaries:
                # 验证选择是否合理（仅当选择单个总结时）
                if len(selected_summaries) == 1:
                    # 使用父类的验证方法
                    if not self._validate_summary_selection(summary_messages, selected_summaries[0]):
                        logger.warning("总结选择验证失败，但继续执行")
                
                for selected_summary in selected_summaries:
                    new_history.append(selected_summary.message)
                    logger.info(f"保留总结消息 {selected_summary.index} "
                               f"(状态: {selected_summary.message.get('summary_status', 0)}, "
                               f"窗口章节: {selected_summary.message.get('window_chapters', [])})")
                
                # 记录被删除的旧总结
                deleted_count = 0
                for classification in summary_messages:
                    if not any(classification.index == selected_summary.index for selected_summary in selected_summaries):
                        logger.debug(f"删除旧总结消息 {classification.index} "
                                   f"(状态: {classification.message.get('summary_status', 0)})")
                        deleted_count += 1
                
                if deleted_count > 0:
                    logger.info(f"删除了 {deleted_count} 条旧总结消息")
            else:
                logger.warning("没有选择任何总结消息，可能存在问题")
        
        # 5. 记录待删除消息
        to_be_removed = messages_by_type.get(MessageType.TO_BE_REMOVED, [])
        for classification in to_be_removed:
            logger.debug(f"删除前两章消息 {classification.index}: 第{classification.chapter}章 {classification.stage}")
        
        # 6. 记录其他消息（旧的已修剪章节）
        other_messages = messages_by_type.get(MessageType.OTHER, [])
        for classification in other_messages:
            logger.debug(f"删除其他消息 {classification.index}: 第{classification.chapter}章 {classification.stage}")
        
        logger.info(f"基于状态排序的修剪完成: 原始 {len(history)} 条 -> 保留 {len(new_history)} 条")
        return new_history


class PruningManager:
    """修剪管理器 - 协调修剪策略的执行"""
    
    def __init__(self, state_manager):
        """
        初始化修剪管理器
        
        Args:
            state_manager: 状态管理器实例
        """
        self.state_manager = state_manager
        self.pruner = None
    
    def create_pruner(self, window_chapters: List[int], use_status_based: bool = True) -> SlidingWindowPruner:
        """
        创建修剪器
        
        Args:
            window_chapters: 窗口章节列表
            use_status_based: 是否使用基于状态排序的修剪器
            
        Returns:
            SlidingWindowPruner: 修剪器实例
        """
        base_context_length = self.state_manager.get_base_context_length()
        if base_context_length <= 0:
            base_context_length = 1
        
        if use_status_based:
            self.pruner = StatusBasedPruner(
                base_context_length=base_context_length,
                window_chapters=window_chapters
            )
            logger.info("创建基于状态排序的修剪器")
        else:
            self.pruner = SlidingWindowPruner(
                base_context_length=base_context_length,
                window_chapters=window_chapters
            )
            logger.info("创建滑动窗口修剪器")
        
        return self.pruner
    
    def execute_pruning(self, history: List[Dict[str, Any]], window_chapters: List[int],
                       use_status_based: bool = True) -> List[Dict[str, Any]]:
        """
        执行修剪
        
        Args:
            history: 完整历史记录
            window_chapters: 窗口章节列表
            use_status_based: 是否使用基于状态排序的修剪器
            
        Returns:
            List[Dict[str, Any]]: 修剪后的历史记录
        """
        # 创建修剪器
        pruner = self.create_pruner(window_chapters, use_status_based)
        
        # 获取修剪统计信息
        stats = pruner.get_pruning_statistics(history)
        logger.info(f"修剪前统计: {stats}")
        
        # 执行修剪
        pruned_history = pruner.prune(history)
        
        # 验证修剪结果
        if not pruner.validate_pruned_history(pruned_history, len(history)):
            logger.warning("修剪验证失败，但继续执行")
        
        return pruned_history