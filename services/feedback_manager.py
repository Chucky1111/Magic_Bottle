"""
反馈管理器 - 负责管理读者反馈的抽取和状态维护

功能：
1. 从 data/feedback.txt 读取和解析反馈
2. 抽取一条反馈（按顺序）
3. 从文件中移除已使用的反馈（pop机制）
4. 状态持久化，避免重复使用
"""

import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class FeedbackManager:
    """反馈管理器，负责读者反馈的抽取和状态维护"""
    
    def __init__(self, feedback_file_path: str = "data/feedback.txt",
                 state_file_path: str = "data/feedback_state.json"):
        """
        初始化反馈管理器
        
        Args:
            feedback_file_path: 反馈文件路径
            state_file_path: 反馈状态文件路径（用于记录已使用的反馈）
        """
        self.feedback_file_path = Path(feedback_file_path)
        self.state_file_path = Path(state_file_path)
        self.used_feedback_indices: List[int] = []
        
        # 确保目录存在
        self.feedback_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载已使用的反馈索引
        self._load_used_feedback()
    
    def _load_used_feedback(self) -> None:
        """从状态文件加载已使用的反馈索引"""
        try:
            if self.state_file_path.exists():
                with open(self.state_file_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                # 从状态中获取已使用的反馈索引
                if "used_feedback_indices" in state:
                    self.used_feedback_indices = state["used_feedback_indices"]
                    logger.debug(f"已加载 {len(self.used_feedback_indices)} 个已使用的反馈索引")
                else:
                    self.used_feedback_indices = []
                    logger.debug("状态文件中没有已使用的反馈索引记录")
            else:
                logger.debug("状态文件不存在，初始化空的已使用反馈列表")
                self.used_feedback_indices = []
                
        except Exception as e:
            logger.error(f"加载已使用反馈索引失败: {e}")
            self.used_feedback_indices = []
    
    def _save_used_feedback(self) -> None:
        """保存已使用的反馈索引到状态文件"""
        try:
            # 先加载现有状态，避免覆盖其他字段
            state = {}
            if self.state_file_path.exists():
                with open(self.state_file_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
            
            # 更新已使用的反馈索引
            state["used_feedback_indices"] = self.used_feedback_indices
            
            # 保存状态
            self.state_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"已保存 {len(self.used_feedback_indices)} 个已使用的反馈索引到状态文件")
            
        except Exception as e:
            logger.error(f"保存已使用反馈索引失败: {e}")
    
    def parse_feedback_file(self) -> List[Dict[str, Any]]:
        """
        解析反馈文件，提取所有反馈
        
        Returns:
            反馈列表，每个反馈包含 'index', 'header', 'content', 'raw', 'chapter' 字段
        """
        if not self.feedback_file_path.exists():
            logger.warning(f"反馈文件不存在: {self.feedback_file_path}")
            return []
        
        try:
            with open(self.feedback_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 使用正则表达式匹配反馈
            # 新格式：## 反馈 N（来自第X章的读者）\n内容
            # 也兼容旧格式：## 反馈 N\n内容
            feedback_pattern = r'##\s*反馈\s*(\d+)(?:\s*（来自第(\d+)章的读者）)?\s*\n(.*?)(?=\n##\s*反馈\s*\d+|$)'
            matches = re.findall(feedback_pattern, content, re.DOTALL)
            
            feedbacks = []
            for match in matches:
                index = int(match[0])
                chapter_str = match[1]  # 可能为空
                feedback_content = match[2].strip()
                
                # 提取章节号（如果有）
                chapter_num = int(chapter_str) if chapter_str else 0
                
                # 提取标题（第一行）
                lines = feedback_content.split('\n')
                header = lines[0].strip() if lines else ""
                
                # 构建原始格式
                if chapter_num > 0:
                    raw = f"## 反馈 {index}（来自第{chapter_num}章的读者）\n{feedback_content}"
                else:
                    raw = f"## 反馈 {index}\n{feedback_content}"
                
                feedbacks.append({
                    'index': index,
                    'chapter': chapter_num,
                    'header': header,
                    'content': feedback_content,
                    'raw': raw
                })
            
            logger.debug(f"从文件解析出 {len(feedbacks)} 条反馈")
            return feedbacks
            
        except Exception as e:
            logger.error(f"解析反馈文件失败: {e}")
            return []
    
    def get_available_feedbacks(self) -> List[Dict[str, Any]]:
        """
        获取所有可用的反馈（排除已使用的）
        
        Returns:
            可用的反馈列表
        """
        all_feedbacks = self.parse_feedback_file()
        
        # 过滤掉已使用的反馈
        available_feedbacks = [
            fb for fb in all_feedbacks 
            if fb['index'] not in self.used_feedback_indices
        ]
        
        logger.debug(f"可用反馈数量: {len(available_feedbacks)} / {len(all_feedbacks)}")
        return available_feedbacks
    
    def pop_feedback(self) -> Optional[str]:
        """
        抽取一条反馈（按顺序），并从文件中移除
        
        Returns:
            抽取的反馈内容（包含章节定位信息），如果没有可用反馈则返回 None
        """
        available_feedbacks = self.get_available_feedbacks()
        
        if not available_feedbacks:
            logger.warning("没有可用的反馈")
            return None
        
        # 按索引排序，抽取第一条
        available_feedbacks.sort(key=lambda x: x['index'])
        feedback_to_use = available_feedbacks[0]
        feedback_index = feedback_to_use['index']
        chapter_num = feedback_to_use['chapter']
        
        logger.info(f"抽取反馈 #{feedback_index}（来自第{chapter_num}章）: {feedback_to_use['header'][:50]}...")
        
        # 标记为已使用
        if feedback_index not in self.used_feedback_indices:
            self.used_feedback_indices.append(feedback_index)
            self._save_used_feedback()
        
        # 从文件中物理移除该反馈
        self._remove_feedback_from_file(feedback_index)
        
        # 返回包含章节定位信息的完整反馈
        # 如果反馈有章节信息，返回带章节定位的格式
        if chapter_num > 0:
            return f"## 反馈 {feedback_index}（来自第{chapter_num}章的读者）\n{feedback_to_use['content']}"
        else:
            return f"## 反馈 {feedback_index}\n{feedback_to_use['content']}"
    
    def _remove_feedback_from_file(self, feedback_index: int) -> None:
        """
        从反馈文件中物理移除指定的反馈

        Args:
            feedback_index: 要移除的反馈索引
        """
        if not self.feedback_file_path.exists():
            logger.warning(f"反馈文件不存在，无法移除反馈 #{feedback_index}")
            return

        try:
            # 解析当前所有反馈
            feedbacks = self.parse_feedback_file()
            if not feedbacks:
                logger.debug("反馈文件为空，无需移除")
                return

            # 过滤掉要删除的反馈索引
            remaining_feedbacks = [fb for fb in feedbacks if fb['index'] != feedback_index]

            # 如果数量没有减少，说明指定索引不存在
            if len(remaining_feedbacks) == len(feedbacks):
                logger.warning(f"反馈 #{feedback_index} 不存在于文件中，跳过移除")
                return

            # 构建新文件内容
            lines = ["# 读者反馈"]
            if remaining_feedbacks:
                # 按索引排序（可选）
                remaining_feedbacks.sort(key=lambda x: x['index'])
                for fb in remaining_feedbacks:
                    lines.append("")  # 反馈间空行
                    lines.append(fb['raw'])

            new_content = "\n".join(lines)
            if not new_content.endswith("\n"):
                new_content += "\n"

            # 保存更新后的文件
            with open(self.feedback_file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            logger.info(f"已从反馈文件中移除反馈 #{feedback_index}，剩余 {len(remaining_feedbacks)} 条反馈")

        except Exception as e:
            logger.error(f"从文件移除反馈失败: {e}")
    
    def get_feedback_count(self) -> Tuple[int, int]:
        """
        获取反馈统计
        
        Returns:
            (总反馈数, 可用反馈数) 的元组
        """
        all_feedbacks = self.parse_feedback_file()
        available_feedbacks = self.get_available_feedbacks()
        
        return len(all_feedbacks), len(available_feedbacks)
    
    def reset_used_feedback(self) -> None:
        """重置已使用的反馈记录（用于测试或重新开始）"""
        self.used_feedback_indices = []
        self._save_used_feedback()
        logger.info("已重置已使用的反馈记录")
    
    def resync_with_feedback_file(self) -> None:
        """
        重新同步已使用的反馈索引与反馈文件
        
        当反馈文件被外部更新（如添加新反馈）时调用此方法。
        它会：
        1. 解析当前反馈文件中的所有反馈
        2. 检查是否需要完全重置状态（如果反馈章节与当前写作章节差距过大）
        3. 移除那些不存在于文件中的已使用索引
        4. 保存更新后的状态
        """
        try:
            # 解析当前反馈文件中的所有反馈
            all_feedbacks = self.parse_feedback_file()
            if not all_feedbacks:
                logger.debug("反馈文件为空，无需同步")
                return
            
            existing_indices = {fb['index'] for fb in all_feedbacks}
            existing_chapters = {fb['chapter'] for fb in all_feedbacks}
            
            # 尝试获取当前写作章节号，用于智能判断
            current_writing_chapter = 0
            try:
                state_path = Path("data/state.json")
                if state_path.exists():
                    with open(state_path, 'r', encoding='utf-8') as f:
                        writing_state = json.load(f)
                    current_writing_chapter = writing_state.get("chapter_num", 0)
            except Exception:
                pass  # 如果无法获取写作章节，不影响主要逻辑
            
            # 特殊情况：如果所有反馈都是同一章
            if len(existing_chapters) == 1:
                feedback_chapter = next(iter(existing_chapters))
                
                # 情况1：反馈章节比当前写作章节新很多（>10章）
                # 这可能意味着反馈文件被完全替换为新章节的反馈
                if current_writing_chapter > 0 and feedback_chapter - current_writing_chapter > 10:
                    logger.info(f"检测到反馈文件已更新为第{feedback_chapter}章的新反馈（当前写作第{current_writing_chapter}章），重置已使用状态")
                    self.used_feedback_indices = []
                    self._save_used_feedback()
                    return
                
                # 情况2：反馈章节比当前写作章节旧很多（>10章）
                # 这可能意味着反馈文件需要更新，残留的旧反馈应该被清理
                elif current_writing_chapter > 0 and current_writing_chapter - feedback_chapter > 10:
                    logger.info(f"检测到反馈文件中的反馈（第{feedback_chapter}章）比当前写作章节（第{current_writing_chapter}章）旧很多，建议添加新反馈")
                    # 不自动重置状态，但记录警告
                    logger.warning(f"反馈文件可能包含过时的反馈（第{feedback_chapter}章），而当前已写到第{current_writing_chapter}章")
            
            # 正常情况：过滤掉不存在于文件中的已使用索引
            original_count = len(self.used_feedback_indices)
            
            # 首先，移除不存在于文件中的索引
            self.used_feedback_indices = [
                idx for idx in self.used_feedback_indices
                if idx in existing_indices
            ]
            
            # 其次，检查并移除过时的反馈索引
            # 如果当前写作章节有效，移除那些章节号比当前写作章节旧很多的反馈索引
            if current_writing_chapter > 0:
                # 获取所有反馈的章节信息映射
                feedback_chapter_map = {fb['index']: fb['chapter'] for fb in all_feedbacks}
                
                # 找出过时的反馈索引（章节差距 > 10章）
                outdated_indices = []
                for idx in self.used_feedback_indices:
                    if idx in feedback_chapter_map:
                        fb_chapter = feedback_chapter_map[idx]
                        if fb_chapter > 0 and current_writing_chapter - fb_chapter > 10:
                            outdated_indices.append(idx)
                
                # 移除过时的反馈索引
                if outdated_indices:
                    logger.info(f"检测到 {len(outdated_indices)} 个过时的反馈索引（章节差距 > 10章），将其从已使用列表中移除: {outdated_indices}")
                    self.used_feedback_indices = [
                        idx for idx in self.used_feedback_indices
                        if idx not in outdated_indices
                    ]
                    # 物理删除过时的反馈文件内容
                    for idx in outdated_indices:
                        self._remove_feedback_from_file(idx)
            
            # 保存更新后的状态
            self._save_used_feedback()
            
            removed_count = original_count - len(self.used_feedback_indices)
            if removed_count > 0:
                logger.info(f"重新同步反馈状态: 移除了 {removed_count} 个不存在于文件中的已使用索引")
                logger.info(f"当前已使用索引: {self.used_feedback_indices}")
            else:
                logger.debug("反馈状态同步完成，无需更改")
                
        except Exception as e:
            logger.error(f"重新同步反馈状态失败: {e}")


# 单例实例，便于全局使用
_feedback_manager_instance = None

def get_feedback_manager() -> FeedbackManager:
    """获取反馈管理器单例实例"""
    global _feedback_manager_instance
    if _feedback_manager_instance is None:
        _feedback_manager_instance = FeedbackManager()
    return _feedback_manager_instance