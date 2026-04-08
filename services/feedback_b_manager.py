"""
反馈 B 管理器 - 负责管理读者 B 反馈的抽取和状态维护

功能：
1. 从 data/feedback_b.txt 读取和解析反馈（使用 --- 分隔符）
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


class FeedbackBManager:
    """反馈 B 管理器，负责读者 B 反馈的抽取和状态维护"""
    
    def __init__(self, feedback_file_path: str = "data/feedback_b.txt",
                 state_file_path: str = "data/feedback_b_state.json"):
        """
        初始化反馈 B 管理器
        
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
        解析反馈文件，提取所有反馈（使用 --- 分隔符）
        
        Returns:
            反馈列表，每个反馈包含 'index', 'content', 'raw', 'chapter' 字段
        """
        if not self.feedback_file_path.exists():
            logger.warning(f"反馈 B 文件不存在: {self.feedback_file_path}")
            return []
        
        try:
            with open(self.feedback_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 使用 '---' 作为分隔符
            # 去除首尾空白，按 '---' 分割，并过滤空字符串
            sections = [s.strip() for s in content.split('---') if s.strip()]
            
            feedbacks = []
            for idx, section in enumerate(sections, start=1):
                # 尝试从内容中提取章节号（例如“第X章”）
                chapter_num = 0
                chapter_match = re.search(r'第(\d+)章', section)
                if chapter_match:
                    chapter_num = int(chapter_match.group(1))
                
                # 提取第一行作为标题（如果有）
                lines = section.split('\n')
                header = lines[0].strip() if lines else ""
                
                feedbacks.append({
                    'index': idx,
                    'chapter': chapter_num,
                    'header': header,
                    'content': section,
                    'raw': section
                })
            
            logger.debug(f"从反馈 B 文件解析出 {len(feedbacks)} 条反馈（使用 --- 分隔符）")
            return feedbacks
            
        except Exception as e:
            logger.error(f"解析反馈 B 文件失败: {e}")
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
        
        logger.debug(f"可用反馈 B 数量: {len(available_feedbacks)} / {len(all_feedbacks)}")
        return available_feedbacks
    
    def pop_feedback(self) -> Optional[str]:
        """
        抽取一条反馈（按顺序），并从文件中移除
        
        Returns:
            抽取的反馈内容（原始文本），如果没有可用反馈则返回 None
        """
        available_feedbacks = self.get_available_feedbacks()
        
        if not available_feedbacks:
            logger.warning("没有可用的反馈 B")
            return None
        
        # 按索引排序，抽取第一条
        available_feedbacks.sort(key=lambda x: x['index'])
        feedback_to_use = available_feedbacks[0]
        feedback_index = feedback_to_use['index']
        chapter_num = feedback_to_use['chapter']
        
        logger.info(f"抽取反馈 B #{feedback_index}（来自第{chapter_num}章）: {feedback_to_use['header'][:50]}...")
        
        # 标记为已使用
        if feedback_index not in self.used_feedback_indices:
            self.used_feedback_indices.append(feedback_index)
            self._save_used_feedback()
        
        # 从文件中物理移除该反馈
        self._remove_feedback_from_file(feedback_index)
        
        # 返回原始反馈内容
        return feedback_to_use['content']
    
    def _remove_feedback_from_file(self, feedback_index: int) -> None:
        """
        从反馈文件中物理移除指定的反馈

        Args:
            feedback_index: 要移除的反馈索引（1‑based）
        """
        if not self.feedback_file_path.exists():
            logger.warning(f"反馈 B 文件不存在，无法移除反馈 #{feedback_index}")
            return

        try:
            # 解析当前所有反馈
            feedbacks = self.parse_feedback_file()
            if not feedbacks:
                logger.debug("反馈 B 文件为空，无需移除")
                return

            # 过滤掉要删除的反馈索引
            remaining_feedbacks = [fb for fb in feedbacks if fb['index'] != feedback_index]

            # 如果数量没有减少，说明指定索引不存在
            if len(remaining_feedbacks) == len(feedbacks):
                logger.warning(f"反馈 B #{feedback_index} 不存在于文件中，跳过移除")
                return

            # 构建新文件内容
            if remaining_feedbacks:
                # 按索引排序
                remaining_feedbacks.sort(key=lambda x: x['index'])
                # 使用 raw 字段（原始内容）
                sections = [fb['raw'] for fb in remaining_feedbacks]
                new_content = '\n\n---\n\n'.join(sections)
                new_content = new_content.strip()
            else:
                new_content = ""

            # 保存更新后的文件
            with open(self.feedback_file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            logger.info(f"已从反馈 B 文件中移除反馈 #{feedback_index}，剩余 {len(remaining_feedbacks)} 条反馈")

        except Exception as e:
            logger.error(f"从文件移除反馈 B 失败: {e}")
    
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
        logger.info("已重置已使用的反馈 B 记录")
    
    def resync_with_feedback_file(self) -> None:
        """
        重新同步已使用的反馈索引与反馈文件

        当反馈文件被外部更新（如添加新反馈）时调用此方法。
        它会：
        1. 解析当前反馈文件中的所有反馈
        2. 移除那些不存在于文件中的已使用索引
        3. 物理删除已使用但仍残留在文件中的反馈
        4. 保存更新后的状态
        """
        try:
            # 解析当前反馈文件中的所有反馈
            all_feedbacks = self.parse_feedback_file()
            if not all_feedbacks:
                logger.debug("反馈 B 文件为空，无需同步")
                return

            existing_indices = {fb['index'] for fb in all_feedbacks}

            # 过滤掉不存在于文件中的已使用索引
            original_count = len(self.used_feedback_indices)
            self.used_feedback_indices = [
                idx for idx in self.used_feedback_indices
                if idx in existing_indices
            ]

            # 物理删除已使用但仍残留在文件中的反馈
            # 这些反馈可能因为之前的删除失败而残留
            for idx in self.used_feedback_indices:
                self._remove_feedback_from_file(idx)

            # 保存更新后的状态
            self._save_used_feedback()

            removed_count = original_count - len(self.used_feedback_indices)
            if removed_count > 0:
                logger.info(f"重新同步反馈 B 状态: 移除了 {removed_count} 个不存在于文件中的已使用索引")
                logger.info(f"当前已使用索引: {self.used_feedback_indices}")
            else:
                logger.debug("反馈 B 状态同步完成，无需更改")

        except Exception as e:
            logger.error(f"重新同步反馈 B 状态失败: {e}")


# 单例实例，便于全局使用
_feedback_b_manager_instance = None

def get_feedback_b_manager() -> FeedbackBManager:
    """获取反馈 B 管理器单例实例"""
    global _feedback_b_manager_instance
    if _feedback_b_manager_instance is None:
        _feedback_b_manager_instance = FeedbackBManager()
    return _feedback_b_manager_instance