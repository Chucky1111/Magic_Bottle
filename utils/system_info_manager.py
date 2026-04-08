"""
系统信息管理器 - 负责管理随机系统信息的插入
实现从 data/system_info.txt 随机抽取一行，并在指定章节间隔插入
"""

import random
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class SystemInfoManager:
    """系统信息管理器"""
    
    def __init__(self, system_info_file: str = "data/system_info.txt"):
        """
        初始化系统信息管理器
        
        Args:
            system_info_file: 系统信息文件路径
        """
        self.system_info_file = Path(system_info_file)
        self.system_info_lines: List[str] = []
        self._load_system_info()
    
    def _load_system_info(self) -> None:
        """加载系统信息文件"""
        try:
            if not self.system_info_file.exists():
                logger.warning(f"系统信息文件不存在: {self.system_info_file}")
                self.system_info_lines = []
                return
            
            with open(self.system_info_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
                self.system_info_lines = lines
            
            logger.info(f"已加载 {len(self.system_info_lines)} 条系统信息")
            
        except Exception as e:
            logger.error(f"加载系统信息文件失败: {e}")
            self.system_info_lines = []
    
    def get_random_system_info(self) -> Optional[str]:
        """
        随机获取一条系统信息
        
        Returns:
            随机系统信息字符串，如果没有系统信息则返回None
        """
        if not self.system_info_lines:
            return None
        
        return random.choice(self.system_info_lines)
    
    def should_insert_system_info(
        self,
        current_chapter: int,
        scheduled_chapters: List[int]
    ) -> bool:
        """
        判断当前章节是否需要插入系统信息（新逻辑）
        
        新逻辑：在15章内随机选择5-6个章节插入系统信息
        
        Args:
            current_chapter: 当前章节号
            scheduled_chapters: 已计划的插入章节列表
            
        Returns:
            如果当前章节需要插入系统信息则返回True
        """
        return current_chapter in scheduled_chapters
    
    def generate_scheduled_chapters(self, start_chapter: int = 1, cycle_length: int = 15) -> List[int]:
        """
        生成计划插入系统信息的章节列表
        
        在15章内随机选择5-6个章节插入系统信息
        
        Args:
            start_chapter: 起始章节号
            cycle_length: 周期长度（默认15章）
            
        Returns:
            计划插入系统信息的章节号列表（排序后）
        """
        # 随机选择插入次数：5或6次
        insert_count = random.choice([5, 6])
        
        # 在1到cycle_length之间随机选择insert_count个不重复的章节
        # 注意：这里生成的是相对位置（1-based）
        relative_positions = random.sample(range(1, cycle_length + 1), insert_count)
        
        # 转换为绝对章节号
        scheduled_chapters = [start_chapter + pos - 1 for pos in sorted(relative_positions)]
        
        logger.info(f"生成系统信息插入计划: 在章节 {start_chapter}-{start_chapter + cycle_length - 1} 中，将在以下章节插入: {scheduled_chapters}")
        return scheduled_chapters
    
    def generate_random_interval(self, min_chapters: int = 1, max_chapters: int = 15) -> int:
        """
        生成随机间隔章节数（保留用于向后兼容）
        
        Args:
            min_chapters: 最小间隔章节数
            max_chapters: 最大间隔章节数
            
        Returns:
            随机生成的间隔章节数
        """
        return random.randint(min_chapters, max_chapters)
    
    def get_all_system_info(self) -> List[str]:
        """获取所有系统信息"""
        return self.system_info_lines.copy()
    
    def add_system_info(self, info: str) -> None:
        """
        添加新的系统信息到文件
        
        Args:
            info: 要添加的系统信息
        """
        try:
            # 确保目录存在
            self.system_info_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 读取现有内容
            existing_lines = []
            if self.system_info_file.exists():
                with open(self.system_info_file, 'r', encoding='utf-8') as f:
                    existing_lines = [line.strip() for line in f if line.strip()]
            
            # 添加新行
            existing_lines.append(info.strip())
            
            # 写入文件
            with open(self.system_info_file, 'w', encoding='utf-8') as f:
                for line in existing_lines:
                    f.write(line + '\n')
            
            # 重新加载
            self._load_system_info()
            logger.info(f"已添加系统信息: {info}")
            
        except Exception as e:
            logger.error(f"添加系统信息失败: {e}")
            raise