"""
序列管理器 - 负责加载和管理序列文件（简化版）
实现简单的顺序轮换注入
"""

import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class SequenceManager:
    """序列管理器，负责管理设计/写作序列文件（简化版）"""
    
    def __init__(self, sequences_dir: str = "prompts/squences"):
        """
        初始化序列管理器
        
        Args:
            sequences_dir: 序列文件目录
        """
        self.sequences_dir = Path(sequences_dir)
        self.sequences_cache: Dict[str, List[str]] = {}
        
        # 确保目录存在
        self.sequences_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"序列管理器初始化完成，目录: {self.sequences_dir}")
    
    def load_sequence(self, sequence_file: str) -> List[str]:
        """
        加载序列文件，返回模块列表
        
        Args:
            sequence_file: 序列文件名（如 "design_body.md"）
            
        Returns:
            List[str]: 模块内容列表
            
        Raises:
            FileNotFoundError: 序列文件不存在
        """
        file_path = self.sequences_dir / sequence_file
        
        if not file_path.exists():
            logger.error(f"序列文件不存在: {file_path}")
            raise FileNotFoundError(f"序列文件不存在: {file_path}")
        
        # 检查缓存
        cache_key = str(file_path)
        if cache_key in self.sequences_cache:
            logger.debug(f"从缓存加载序列: {sequence_file}")
            return self.sequences_cache[cache_key]
        
        # 读取并解析文件
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 使用 "---" 分隔符分割模块
            # 简单分割，假设 "---" 是单独一行的分隔符
            lines = content.strip().split('\n')
            modules = []
            current_module = []
            
            for line in lines:
                if line.strip() == '---':
                    # 遇到分隔符，保存当前模块
                    if current_module:
                        modules.append('\n'.join(current_module).strip())
                        current_module = []
                else:
                    current_module.append(line)
            
            # 添加最后一个模块
            if current_module:
                modules.append('\n'.join(current_module).strip())
            
            if not modules:
                logger.warning(f"序列文件 {sequence_file} 没有找到有效模块")
                modules = [""]  # 返回一个空模块作为后备
            
            # 更新缓存
            self.sequences_cache[cache_key] = modules
            
            logger.info(f"加载序列文件 {sequence_file}: {len(modules)} 个模块")
            return modules
            
        except Exception as e:
            logger.error(f"加载序列文件失败 {sequence_file}: {e}")
            raise
    
    def get_module(self, sequence_file: str, module_index: int) -> str:
        """
        获取指定序列文件的指定模块
        
        Args:
            sequence_file: 序列文件名
            module_index: 模块索引（0-based）
            
        Returns:
            str: 模块内容
            
        Raises:
            IndexError: 模块索引越界
            FileNotFoundError: 序列文件不存在
        """
        modules = self.load_sequence(sequence_file)
        
        if not modules:
            logger.warning(f"序列文件 {sequence_file} 没有模块")
            return ""
        
        if module_index < 0 or module_index >= len(modules):
            logger.warning(f"模块索引越界: {sequence_file}[{module_index}]，可用范围: 0-{len(modules)-1}")
            # 回退到第一个模块
            return modules[0]
        
        return modules[module_index]
    
    def get_module_count(self, sequence_file: str) -> int:
        """
        获取序列文件的模块数量
        
        Args:
            sequence_file: 序列文件名
            
        Returns:
            int: 模块数量，如果文件不存在返回0
        """
        try:
            modules = self.load_sequence(sequence_file)
            return len(modules)
        except FileNotFoundError:
            return 0
        except Exception as e:
            logger.error(f"获取模块数量失败 {sequence_file}: {e}")
            return 0
    
    def get_next_module_index(self, sequence_file: str, current_index: int) -> int:
        """
        获取下一个模块索引（简单顺序轮换）
        
        Args:
            sequence_file: 序列文件名
            current_index: 当前索引
            
        Returns:
            int: 下一个模块索引
        """
        module_count = self.get_module_count(sequence_file)
        if module_count == 0:
            return 0
        
        # 简单顺序轮换：0 -> 1 -> 0 -> 1 ...
        return (current_index + 1) % module_count
    
    def clear_cache(self) -> None:
        """清空序列缓存"""
        self.sequences_cache.clear()
        logger.info("序列缓存已清空")
    
    def get_sequence_info(self, sequence_file: str) -> Dict[str, Any]:
        """
        获取序列文件信息
        
        Args:
            sequence_file: 序列文件名
            
        Returns:
            Dict[str, Any]: 序列信息
        """
        try:
            modules = self.load_sequence(sequence_file)
            file_path = self.sequences_dir / sequence_file
            
            return {
                "file_name": sequence_file,
                "file_path": str(file_path),
                "module_count": len(modules),
                "modules_preview": [m[:100] + "..." if len(m) > 100 else m for m in modules],
                "total_chars": sum(len(m) for m in modules)
            }
        except Exception as e:
            logger.error(f"获取序列信息失败 {sequence_file}: {e}")
            return {
                "file_name": sequence_file,
                "error": str(e)
            }


# 单例实例
_sequence_manager_instance: Optional[SequenceManager] = None

def get_sequence_manager() -> SequenceManager:
    """获取序列管理器单例实例"""
    global _sequence_manager_instance
    if _sequence_manager_instance is None:
        _sequence_manager_instance = SequenceManager()
    return _sequence_manager_instance