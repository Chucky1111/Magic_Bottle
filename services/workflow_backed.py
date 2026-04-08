"""
工作流逻辑 - 主控逻辑
实现带复杂上下文管理的 Chatbot 线性对话流

核心特性：
1. System Prompt 永远置顶
2. Warmup 预热对话永久存入历史记录前端（真实现场问答）
3. 基于轮次的滑动窗口修剪逻辑
"""

import json
import logging
import random
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

from core.llm import LLMClient
from core.parser import ContentParser
from services.state_manager import StateManager
from services.warmup_runner import WarmupRunner
from services.feedback_manager import FeedbackManager
from services.pruning_strategy import PruningManager
from services.sequence_manager import SequenceManager, get_sequence_manager
from services.prompt_logger import PromptLogger, get_prompt_logger
from services.snapshot_manager import get_snapshot_manager
from utils.system_info_manager import SystemInfoManager
from utils.content_similarity import get_content_similarity_checker
# 审计反馈提取器已移除

logger = logging.getLogger(__name__)


class ChatWorkflow:
    """聊天工作流 - 实现线性对话流系统"""
    
    def __init__(self):
        """初始化聊天工作流"""
        self.llm_client = LLMClient()
        self.parser = ContentParser()
        self.state_manager = StateManager()
        self.warmup_runner = WarmupRunner()
        self.feedback_manager = FeedbackManager()
        self.system_info_manager = SystemInfoManager()
        self.pruning_manager = PruningManager(self.state_manager)
        self.sequence_manager = get_sequence_manager()
        self.prompt_logger = get_prompt_logger()
        
        # 加载世界观文件
        self.world_view_content = self._load_world_view()
        
        # 确保必要的目录存在
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # 初始化系统（检查是否需要运行预热）
        self._initialize_system()
        
        logger.info("ChatWorkflow初始化完成")
    
    def _initialize_system(self) -> None:
        """初始化系统：检查是否需要运行预热流程"""
        history_path = Path("data/history.json")
        state_path = Path("data/state.json")
        
        # Case A: Fresh Start (全新启动)
        if not history_path.exists() or history_path.stat().st_size == 0:
            logger.info("检测到全新启动，开始运行预热流程...")
            
            # 运行预热并保存历史记录
            base_context_length = self.warmup_runner.run_warmup_and_save(history_path)
            
            if base_context_length > 1:  # 成功生成预热对话
                # 在状态中记录基准上下文长度
                self.state_manager.set_base_context_length(base_context_length)
                
                # 初始化状态
                self.state_manager.set_chapter_num(1)
                self.state_manager.set_stage("design")
                self.state_manager.set_window_chapters([])
                
                logger.info(f"预热完成，基准上下文长度: {base_context_length}")
                logger.info("系统已初始化，准备开始第1章设计")
            else:
                logger.error("预热流程失败，使用最小化配置")
                # 创建最小化历史记录
                self._create_minimal_history(history_path)
                self.state_manager.set_base_context_length(1)  # 只有系统消息
        
        # Case B: Resume (恢复运行)
        else:
            logger.info("检测到现有历史记录，恢复运行...")
            
            # 加载历史记录
            history = self._load_history()
            
            # 检查状态中是否有基准上下文长度记录
            if self.state_manager.get_base_context_length() == 0:
                # 尝试从历史记录中推断基准上下文长度
                base_context_length = self._infer_base_context_length(history)
                self.state_manager.set_base_context_length(base_context_length)
                logger.info(f"推断基准上下文长度: {base_context_length}")
            
            logger.info(f"恢复状态: {self.state_manager.get_state_summary()}")
    
    def _create_minimal_history(self, history_path: Path) -> None:
        """创建最小化历史记录（仅系统消息）"""
        # 加载系统提示词
        system_prompt_path = Path("prompts/system_prompt.txt")
        system_content = ""
        if system_prompt_path.exists():
            with open(system_prompt_path, 'r', encoding='utf-8') as f:
                system_content = f.read().strip()
        
        history = [{
            "role": "system",
            "content": system_content if system_content else "你是一位专业的小说作家。",
            "timestamp": 0,
            "chapter": 0,
            "stage": "base",
            "is_base_context": True
        }]
        
        with open(history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        logger.info("创建最小化历史记录（仅系统消息）")
    
    def _infer_base_context_length(self, history: List[Dict[str, Any]]) -> int:
        """从历史记录中推断基准上下文长度"""
        # 查找最后一个 is_base_context=True 的消息
        base_context_length = 0
        for i, msg in enumerate(history):
            if msg.get("is_base_context", False):
                base_context_length = i + 1
            else:
                break
        
        # 如果没有找到，假设第一条消息是系统消息
        if base_context_length == 0 and history:
            base_context_length = 1
        
        return base_context_length
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """加载历史记录"""
        history_path = Path("data/history.json")
        
        if not history_path.exists():
            return []
        
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
            return history
        except Exception as e:
            logger.error(f"加载历史记录失败: {e}")
            return []
    
    def _save_history(self, history: List[Dict[str, Any]]) -> None:
        """保存历史记录"""
        history_path = Path("data/history.json")
        
        try:
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            logger.debug(f"历史记录已保存: {len(history)} 条消息")
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")
    
    def _get_current_generation_cycle(self) -> str:
        """获取当前生成周期标识
        
        返回格式: "cycle_{chapter_num}_{timestamp}"
        用于标识总结生成的周期，便于调试和追踪
        """
        chapter_num = self.state_manager.get_chapter_num()
        timestamp = int(time.time())
        return f"cycle_{chapter_num}_{timestamp}"
    
    def _add_summary_to_history(self, content: str, summary_chapter: int, window_chapters: List[int]) -> None:
        """添加总结消息到历史记录（特殊处理）
        
        Args:
            content: 总结内容
            summary_chapter: 总结关联的章节号（通常是窗口中的最大章节）
            window_chapters: 窗口章节列表
        """
        history = self._load_history()
        
        # 获取下一个总结状态编号
        summary_status = self.state_manager.get_next_summary_status()
        
        # 生成窗口ID
        window_id = f"window_{window_chapters[0]}_{window_chapters[1]}_{window_chapters[2]}" if len(window_chapters) == 3 else "window_unknown"
        
        message = {
            "role": "assistant",
            "content": content,
            "timestamp": time.time(),
            "chapter": 0,  # 修复：总结消息的章节号始终为0，避免影响修剪逻辑
            "stage": "summary",
            "is_base_context": False,
            "is_summary": True,  # 标记为总结消息
            "window_chapters": window_chapters,  # 记录总结的是哪些章节
            "summary_chapter": summary_chapter,  # 记录关联的章节号，用于调试
            "summary_status": summary_status,  # 新增：总结状态编号
            "window_id": window_id,  # 新增：窗口ID
            "generation_cycle": self._get_current_generation_cycle()  # 新增：生成周期标识
        }
        
        history.append(message)
        self._save_history(history)
        
        logger.info(f"总结消息已添加: 状态={summary_status}, 窗口={window_chapters}, 周期={message['generation_cycle']}, 关联章节={summary_chapter}")
    
    def _add_to_history(self, role: str, content: str, chapter_num: int, stage: str,
                       simplify_user_prompt: bool = False) -> None:
        """添加消息到历史记录
        
        Args:
            role: 消息角色 (user/assistant)
            content: 消息内容
            chapter_num: 章节号
            stage: 阶段 (design/write/summary)
            simplify_user_prompt: 是否简化用户提示词（仅对user角色有效）
        """
        history = self._load_history()
        
        # 如果是用户消息且需要简化，使用简化版本
        if role == "user" and simplify_user_prompt:
            if stage == "design":
                simplified_content = self._render_simple_design_prompt()
            elif stage == "write":
                simplified_content = self._render_simple_write_prompt()
            elif stage == "summary":
                # 总结阶段不需要简化
                simplified_content = content
            else:
                simplified_content = content
            
            # 记录简化信息
            original_length = len(content)
            simplified_length = len(simplified_content)
            reduction_percent = 0
            if original_length > 0:
                reduction_percent = (original_length - simplified_length) / original_length * 100
            
            logger.debug(f"用户提示词已简化: {original_length} -> {simplified_length} 字符")
            
            # 记录提示词简化日志
            self.prompt_logger.log_prompt_simplification(
                chapter_num=chapter_num,
                stage=stage,
                original_length=original_length,
                simplified_length=simplified_length,
                reduction_percent=reduction_percent
            )
            
            content = simplified_content
        
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "chapter": chapter_num,
            "stage": stage,
            "is_base_context": False
        }
        
        history.append(message)
        self._save_history(history)
        
        logger.debug(f"历史记录已添加: {role} - 第{chapter_num}章 - {stage}")
        
        # 如果是用户消息，尝试更新历史记录中对应的用户消息
        if role == "assistant":
            self._update_user_prompt_in_history(chapter_num, stage)
    
    def _load_world_view(self) -> str:
        """加载世界观文件内容"""
        world_view_path = Path("world_view.txt")
        if not world_view_path.exists():
            logger.warning(f"世界观文件不存在: {world_view_path}")
            return ""
        
        try:
            with open(world_view_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            logger.debug(f"世界观文件已加载，长度: {len(content)} 字符")
            return content
        except Exception as e:
            logger.error(f"加载世界观文件失败: {e}")
            return ""
    
    def _load_system_prompt(self) -> str:
        """加载系统提示词"""
        system_prompt_path = Path("prompts/system_prompt.txt")
        if not system_prompt_path.exists():
            logger.warning(f"系统提示词文件不存在: {system_prompt_path}")
            return "你是一位专业的小说作家。"

        try:
            with open(system_prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            logger.debug(f"系统提示词已加载，长度: {len(content)} 字符")
            return content
        except Exception as e:
            logger.error(f"加载系统提示词失败: {e}")
            return "你是一位专业的小说作家。"
    
    def _load_feedback_prompt_template(self) -> str:
        """加载反馈提示词模板"""
        feedback_prompt_path = Path("prompts/feedback_system_prompt.txt")
        if not feedback_prompt_path.exists():
            logger.warning(f"反馈提示词模板文件不存在: {feedback_prompt_path}")
            # 返回默认模板
            return "【读者反馈】\n{{feedback_content}}\n\n请参考以上读者反馈进行创作。"
        
        try:
            with open(feedback_prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            logger.debug(f"反馈提示词模板已加载，长度: {len(content)} 字符")
            return content
        except Exception as e:
            logger.error(f"加载反馈提示词模板失败: {e}")
            # 返回默认模板
            return "【读者反馈】\n{{feedback_content}}\n\n请参考以上读者反馈进行创作。"
    
    def _load_prompt_template(self, prompt_file: str) -> str:
        """加载提示词模板文件"""
        prompt_path = Path("prompts") / prompt_file
        if not prompt_path.exists():
            raise FileNotFoundError(f"提示词文件不存在: {prompt_path}")
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _render_design_prompt(self) -> str:
        """渲染设计阶段提示词"""
        template = self._load_prompt_template("design.txt")
        
        # 获取当前章节号
        chapter_num = self.state_manager.get_chapter_num()
        
        # 注意：读者反馈现在通过_get_messages_for_llm()方法在所有阶段都插入
        # 设计阶段提示词中不再需要单独注入读者反馈
        
        # 检查是否需要提醒（每10章）
        alert = ""
        if chapter_num % 10 == 0:
            alert = "【重要提醒】这是第10章的倍数章节，请特别注意情节发展和伏笔安排。"
        
        # 处理系统信息插入逻辑（新逻辑：15章内随机5-6次插入）
        system_info = ""
        
        # 检查并更新周期
        is_new_cycle = self.state_manager.check_and_update_cycle(chapter_num)
        
        # 获取计划插入的章节列表
        scheduled_chapters = self.state_manager.get_system_info_scheduled_chapters()
        
        # 如果没有计划或进入新周期，生成新的计划
        if not scheduled_chapters or is_new_cycle:
            cycle_start = self.state_manager.get_system_info_cycle_start()
            cycle_length = self.state_manager.get_system_info_cycle_length()
            scheduled_chapters = self.system_info_manager.generate_scheduled_chapters(
                start_chapter=cycle_start,
                cycle_length=cycle_length
            )
            self.state_manager.set_system_info_scheduled_chapters(scheduled_chapters)
        
        # 检查当前章节是否需要插入系统信息
        if self.system_info_manager.should_insert_system_info(chapter_num, scheduled_chapters):
            random_info = self.system_info_manager.get_random_system_info()
            if random_info:
                system_info = random_info
                # 更新状态
                self.state_manager.update_system_info_insertion(chapter_num)
                logger.info(f"第{chapter_num}章插入系统信息: {system_info}")
                
                # 从计划列表中移除已插入的章节（可选，为了清晰度）
                # 我们保留计划列表，因为可能需要在同一章节插入多次（虽然不太可能）
            else:
                logger.warning("没有可用的系统信息，跳过插入")
        
        # 序列注入：获取设计序列模块
        design_body = ""
        try:
            # 获取当前设计模块索引
            design_index = self.state_manager.get_design_module_index()
            design_body = self.sequence_manager.get_module("design_body.md", design_index)
            logger.info(f"第{chapter_num}章使用设计序列模块 {design_index}: {len(design_body)} 字符")
            
            # 记录序列注入日志
            self.prompt_logger.log_sequence_injection(
                chapter_num=chapter_num,
                stage="design",
                sequence_file="design_body.md",
                module_index=design_index,
                module_length=len(design_body),
                module_preview=design_body[:100] if design_body else ""
            )
            
            # 推进设计模块索引（简单顺序轮换）
            module_count = self.sequence_manager.get_module_count("design_body.md")
            if module_count > 0:
                old_index = design_index
                new_index = self.state_manager.advance_design_module_index(module_count)
                
                # 记录状态变化日志
                self.prompt_logger.log_state_change(
                    chapter_num=chapter_num,
                    stage="design",
                    old_state={"design_index": old_index},
                    new_state={"design_index": new_index}
                )
                
                logger.debug(f"设计模块索引已推进: {design_index} -> {self.state_manager.get_design_module_index()}")
        except FileNotFoundError:
            logger.warning("设计序列文件不存在: design_body.md")
            self.prompt_logger.log_error(
                chapter_num=chapter_num,
                stage="design",
                error_message="设计序列文件不存在: design_body.md"
            )
        except Exception as e:
            logger.warning(f"加载设计序列模块失败: {e}")
            self.prompt_logger.log_error(
                chapter_num=chapter_num,
                stage="design",
                error_message=f"加载设计序列模块失败: {str(e)}"
            )
        
        # 替换模板变量
        prompt = template.replace("{{chapter_num}}", str(chapter_num))
        prompt = prompt.replace("{{alert}}", alert if alert else "")
        prompt = prompt.replace("{{system_info}}", system_info if system_info else "")
        prompt = prompt.replace("{{design_body}}", design_body if design_body else "")
        prompt = prompt.replace("{{world_view}}", self.world_view_content if self.world_view_content else "")
        
        # 清理多余的占位符
        prompt = prompt.replace("{{alert}}", "")
        prompt = prompt.replace("{{system_info}}", "")
        prompt = prompt.replace("{{design_body}}", "")
        prompt = prompt.replace("{{world_view}}", "")
        
        # 记录模板渲染日志
        variables = {
            "chapter_num": chapter_num,
            "alert": alert if alert else "",
            "system_info_length": len(system_info) if system_info else 0,
            "design_body_length": len(design_body) if design_body else 0,
            "world_view_length": len(self.world_view_content) if self.world_view_content else 0
        }
        
        self.prompt_logger.log_template_rendering(
            chapter_num=chapter_num,
            stage="design",
            template_file="design.txt",
            variables=variables,
            final_length=len(prompt)
        )
        
        return prompt
    
    def _render_simple_design_prompt(self) -> str:
        """渲染简化的设计阶段提示词（用于历史记录）"""
        try:
            template = self._load_prompt_template("simple_design.txt")
        except FileNotFoundError:
            # 如果简化模板不存在，使用原始模板
            template = self._load_prompt_template("design.txt")
        
        # 获取当前章节号
        chapter_num = self.state_manager.get_chapter_num()
        
        # 简化的设计提示词不需要系统信息和序列模块
        # 只保留核心的章节号信息
        prompt = template.replace("{{chapter_num}}", str(chapter_num))
        
        # 清理多余的占位符
        prompt = prompt.replace("{{system_info}}", "")
        prompt = prompt.replace("{{design_body}}", "")
        
        return prompt
    
    def _render_simple_write_prompt(self) -> str:
        """渲染简化的写作阶段提示词（用于历史记录）"""
        try:
            template = self._load_prompt_template("simple_write.txt")
        except FileNotFoundError:
            # 如果简化模板不存在，使用原始模板
            template = self._load_prompt_template("write.txt")
        
        # 获取当前章节号
        chapter_num = self.state_manager.get_chapter_num()
        
        # 替换模板变量
        # mid_chapter_num 继承 chapter_num 的值，实现同步
        prompt = template.replace("{{chapter_num}}", str(chapter_num))
        prompt = prompt.replace("{{mid_chapter_num}}", str(chapter_num))
        prompt = prompt.replace("{{write_body}}", "")
        
        return prompt
    
    def _render_write_prompt(self) -> str:
        """渲染写作阶段提示词"""
        template = self._load_prompt_template("write.txt")
        
        # 获取当前章节号
        chapter_num = self.state_manager.get_chapter_num()
        
        # 序列注入：获取写作序列模块
        write_body = ""
        try:
            # 获取当前写作模块索引
            write_index = self.state_manager.get_write_module_index()
            write_body = self.sequence_manager.get_module("write_body.md", write_index)
            logger.info(f"第{chapter_num}章使用写作序列模块 {write_index}: {len(write_body)} 字符")
            
            # 记录序列注入日志
            self.prompt_logger.log_sequence_injection(
                chapter_num=chapter_num,
                stage="write",
                sequence_file="write_body.md",
                module_index=write_index,
                module_length=len(write_body),
                module_preview=write_body[:100] if write_body else ""
            )
            
            # 推进写作模块索引（简单顺序轮换）
            module_count = self.sequence_manager.get_module_count("write_body.md")
            if module_count > 0:
                old_index = write_index
                new_index = self.state_manager.advance_write_module_index(module_count)
                
                # 记录状态变化日志
                self.prompt_logger.log_state_change(
                    chapter_num=chapter_num,
                    stage="write",
                    old_state={"write_index": old_index},
                    new_state={"write_index": new_index}
                )
                
                logger.debug(f"写作模块索引已推进: {write_index} -> {self.state_manager.get_write_module_index()}")
        except FileNotFoundError:
            logger.warning("写作序列文件不存在: write_body.md")
            self.prompt_logger.log_error(
                chapter_num=chapter_num,
                stage="write",
                error_message="写作序列文件不存在: write_body.md"
            )
        except Exception as e:
            logger.warning(f"加载写作序列模块失败: {e}")
            self.prompt_logger.log_error(
                chapter_num=chapter_num,
                stage="write",
                error_message=f"加载写作序列模块失败: {str(e)}"
            )
        
        # 替换模板变量
        # mid_chapter_num 继承 chapter_num 的值，实现同步
        prompt = template.replace("{{chapter_num}}", str(chapter_num))
        prompt = prompt.replace("{{mid_chapter_num}}", str(chapter_num))
        prompt = prompt.replace("{{write_body}}", write_body if write_body else "")
        prompt = prompt.replace("{{world_view}}", self.world_view_content if self.world_view_content else "")
        
        # 清理多余的占位符
        prompt = prompt.replace("{{write_body}}", "")
        prompt = prompt.replace("{{world_view}}", "")
        
        # 记录模板渲染日志
        variables = {
            "chapter_num": chapter_num,
            "mid_chapter_num": chapter_num,
            "write_body_length": len(write_body) if write_body else 0,
            "world_view_length": len(self.world_view_content) if self.world_view_content else 0
        }
        
        self.prompt_logger.log_template_rendering(
            chapter_num=chapter_num,
            stage="write",
            template_file="write.txt",
            variables=variables,
            final_length=len(prompt)
        )
        
        return prompt
    
    def _render_summary_prompt(self) -> str:
        """渲染总结阶段提示词"""
        template = self._load_prompt_template("summary.txt")
        
        # 获取窗口章节
        window_chapters = self.state_manager.get_window_chapters()
        if len(window_chapters) != 3:
            logger.warning(f"窗口章节数量不正确: {window_chapters}，应为3章")
            # 使用默认值
            window_chapters = [0, 0, 0]
        
        chapter_1, chapter_2, chapter_3 = window_chapters
        
        # 计算下一章
        next_chapter_1 = chapter_3 + 1
        next_chapter_2 = chapter_3 + 2
        
        # 替换模板变量
        prompt = template.replace("{{window_chapters}}", str(window_chapters))
        prompt = prompt.replace("{{chapter_1}}", str(chapter_1))
        prompt = prompt.replace("{{chapter_2}}", str(chapter_2))
        prompt = prompt.replace("{{chapter_3}}", str(chapter_3))
        prompt = prompt.replace("{{next_chapter_1}}", str(next_chapter_1))
        prompt = prompt.replace("{{next_chapter_2}}", str(next_chapter_2))
        prompt = prompt.replace("{{world_view}}", self.world_view_content if self.world_view_content else "")
        
        # 清理多余的占位符
        prompt = prompt.replace("{{window_chapters}}", str(window_chapters))
        prompt = prompt.replace("{{chapter_1}}", str(chapter_1))
        prompt = prompt.replace("{{chapter_2}}", str(chapter_2))
        prompt = prompt.replace("{{chapter_3}}", str(chapter_3))
        prompt = prompt.replace("{{next_chapter_1}}", str(next_chapter_1))
        prompt = prompt.replace("{{next_chapter_2}}", str(next_chapter_2))
        prompt = prompt.replace("{{world_view}}", "")
        
        logger.info(f"总结提示词已渲染: 窗口章节={window_chapters}, 下一章={next_chapter_1},{next_chapter_2}")
        
        return prompt
    
    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """
        清理文件名，移除非法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名，非法字符替换为下划线
        """
        # Windows 文件名非法字符: \ / : * ? " < > |
        # 同时去除首尾空格
        import re
        # 替换非法字符为下划线
        sanitized = re.sub(r'[\\/*?:"<>|]', '_', filename)
        # 去除首尾空格和点
        sanitized = sanitized.strip().strip('.')
        # 限制文件名长度（避免过长的标题）
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        return sanitized
    
    def _write_chapter_file(self, title: str, body: str) -> str:
        """写入章节文件"""
        chapter_num = self.state_manager.get_chapter_num()
        
        # 清理标题，用于文件名
        clean_title = self._sanitize_filename(title)
        if not clean_title or clean_title.isspace():
            clean_title = "无题"
        
        # 生成文件名：第{N}章_{title}.txt
        filename = f"第{chapter_num}章_{clean_title}.txt"
        filepath = self.output_dir / filename
        
        # 写入文件：只写入正文内容，不包含标题标记
        # 因为标题已经在文件名中体现了
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(body)
        
        logger.info(f"章节已保存: {filepath}")
        return str(filepath)
    
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
            feedback_path = Path("data/feedback.txt")
            if feedback_path.exists():
                try:
                    with open(feedback_path, 'r', encoding='utf-8') as f:
                        feedback = f.read().strip()
                        if feedback:
                            logger.info(f"使用后备方案读取反馈文件: {len(feedback)} 字符")
                except Exception as read_error:
                    logger.warning(f"后备方案读取反馈文件也失败: {read_error}")
        
        return feedback
    
    def _get_messages_for_llm(self) -> List[Dict[str, str]]:
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
        full_history = self._load_history()
        
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
                feedback_template = self._load_feedback_prompt_template()
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
                self._add_to_history(
                    role="system",
                    content=feedback_message_content,
                    chapter_num=0,
                    stage="feedback",
                    simplify_user_prompt=False
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
    
    def _execute_pruning(self) -> None:
        """
        执行修剪逻辑 - 使用PruningManager进行模块化修剪
        
        当 state.stage 进入 "summary" 时执行：
        1. 生成总结并存入历史
        2. 执行修剪：删除窗口中前两章的所有记录，保留第三章 + 总结 + 关键世界观消息
        3. 更新状态
        
        核心原则：就是一个聊天列表，隔一会儿删两组，然后再作为上下文
        """
        logger.info("开始执行修剪逻辑 - 使用模块化修剪策略")
        
        # 获取当前窗口章节
        window_chapters = self.state_manager.get_window_chapters()
        if len(window_chapters) != 3:
            logger.error(f"窗口章节数量不正确: {window_chapters}，应为3章")
            return
        
        chapter_1, chapter_2, chapter_3 = window_chapters  # 示例: [5, 6, 7]
        
        # 加载完整历史记录
        full_history = self._load_history()
        
        # 在修剪前保存完整历史记录快照
        try:
            snapshot_manager = get_snapshot_manager()
            
            # 获取修剪统计信息
            pruning_stats = {}
            if hasattr(self.pruning_manager, 'get_pruning_statistics'):
                pruning_stats = self.pruning_manager.get_pruning_statistics(full_history)
            
            # 获取状态信息
            state_info = {
                "chapter_num": self.state_manager.get_chapter_num(),
                "stage": self.state_manager.get_stage(),
                "window_chapters": window_chapters,
                "base_context_length": self.state_manager.get_base_context_length(),
                "state_summary": self.state_manager.get_state_summary()
            }
            
            # 保存快照
            snapshot_path = snapshot_manager.save_snapshot_before_pruning(
                full_history=full_history,
                window_chapters=window_chapters,
                pruning_stats=pruning_stats,
                state_info=state_info
            )
            
            if snapshot_path:
                logger.info(f"修剪前快照已保存: {snapshot_path}")
            else:
                logger.warning("修剪前快照保存失败，但继续执行修剪")
                
        except Exception as e:
            logger.error(f"保存修剪前快照失败: {e}")
            logger.warning("快照保存失败，但继续执行修剪逻辑")
        
        # 使用PruningManager执行修剪（默认使用基于状态排序的修剪器）
        try:
            pruned_history = self.pruning_manager.execute_pruning(full_history, window_chapters, use_status_based=True)
        except Exception as e:
            logger.error(f"修剪执行失败: {e}")
            # 降级方案：使用原始修剪逻辑
            logger.warning("使用降级方案：原始修剪逻辑")
            pruned_history = self._execute_pruning_fallback(full_history, window_chapters)
        
        # 保存修剪后的历史记录
        self._save_history(pruned_history)
        
        # 更新状态
        # window_chapters 从 [5, 6, 7] 变为 []（重置为空窗口，让下一轮重新开始累积）
        self.state_manager.set_window_chapters([])
        
        # chapter_num + 1 (从7变为8)
        new_chapter_num = self.state_manager.get_chapter_num() + 1
        self.state_manager.set_chapter_num(new_chapter_num)
        
        # stage 重置为 "design"
        self.state_manager.set_stage("design")
        
        logger.info(f"修剪完成: 删除了章节 [{chapter_1}, {chapter_2}]，保留章节 {chapter_3}")
        logger.info(f"状态更新: 章节号 {new_chapter_num}，窗口章节 []（已重置）")
        logger.info(f"历史记录长度: {len(full_history)} -> {len(pruned_history)}")
        
        # 验证修剪后的历史记录
        self._validate_pruned_history_simple(pruned_history, chapter_3)
    
    def _execute_pruning_fallback(self, full_history: List[Dict[str, Any]],
                                 window_chapters: List[int]) -> List[Dict[str, Any]]:
        """
        降级方案：原始修剪逻辑（当PruningManager失败时使用）
        
        Args:
            full_history: 完整历史记录
            window_chapters: 窗口章节列表 [chapter_1, chapter_2, chapter_3]
            
        Returns:
            List[Dict[str, Any]]: 修剪后的历史记录
        """
        logger.warning("使用降级修剪方案")
        
        if len(window_chapters) != 3:
            raise ValueError(f"窗口章节数量必须为3，实际为: {window_chapters}")
        
        chapter_1, chapter_2, chapter_3 = window_chapters
        chapters_to_remove = [chapter_1, chapter_2]
        
        # 获取基准上下文长度
        base_context_length = self.state_manager.get_base_context_length()
        if base_context_length <= 0:
            base_context_length = 1
        
        # 识别关键世界观消息
        critical_messages_indices = []
        for i, msg in enumerate(full_history):
            content = msg.get("content", "")
            if "主角叫刘斗斗" in content or "书名叫《诸天：我跷着二郎腿镇压万界》" in content:
                critical_messages_indices.append(i)
        
        # 分类消息
        summary_messages = []
        other_messages = []
        
        for i, msg in enumerate(full_history):
            chapter = msg.get("chapter", 0)
            stage = msg.get("stage", "")
            
            # 基准上下文
            if i < base_context_length:
                other_messages.append((i, msg, "base_context"))
                continue
            
            # 关键世界观消息
            if i in critical_messages_indices:
                other_messages.append((i, msg, "critical"))
                continue
            
            # 第三章消息
            if chapter == chapter_3:
                other_messages.append((i, msg, "chapter_3"))
                continue
            
            # 总结消息
            # 使用与主修剪策略一致的识别规则：
            # 1. stage == "summary" 或者
            # 2. is_summary == True
            is_summary = msg.get("is_summary", False)
            if stage == "summary" or is_summary:
                summary_messages.append((i, msg))
                continue
            
            # 反馈消息（待删除）
            # 反馈消息的标记是 stage="feedback"，章节号为0
            # 在剪枝时应该删除反馈消息，不保留到下一个窗口周期
            if stage == "feedback":
                logger.debug(f"删除反馈消息 {i}: 第{chapter}章 {stage}")
                continue
            
            # 前两章消息（待删除）
            if chapter in chapters_to_remove:
                logger.debug(f"删除前两章消息 {i}: 第{chapter}章 {stage}")
                continue
            
            # 其他消息（待删除）
            logger.debug(f"删除其他消息 {i}: 第{chapter}章 {stage}")
        
        # 构建新的历史记录
        new_history = []
        
        # 添加基准上下文
        for i, msg, msg_type in other_messages:
            if msg_type == "base_context":
                new_history.append(msg)
        
        # 添加关键世界观消息
        for i, msg, msg_type in other_messages:
            if msg_type == "critical":
                new_history.append(msg)
        
        # 添加第三章消息（只保留写作阶段）
        for i, msg, msg_type in other_messages:
            if msg_type == "chapter_3":
                # 只保留写作阶段消息，删除反思阶段消息
                if msg.get("stage") == "write":
                    new_history.append(msg)
                    logger.debug(f"保留第三章写作消息 {i}: 第{msg.get('chapter', 0)}章 {msg.get('stage', '')}")
                else:
                    logger.debug(f"删除第三章反思消息 {i}: 第{msg.get('chapter', 0)}章 {msg.get('stage', '')}")
        
        # 只保留最新的总结消息
        if summary_messages:
            summary_messages.sort(key=lambda x: x[1].get("timestamp", 0))
            latest_summary_index, latest_summary_msg = summary_messages[-1]
            new_history.append(latest_summary_msg)
        
        return new_history
    
    def _validate_pruned_history_simple(self, history: List[Dict[str, Any]],
                                       retained_chapter: int) -> None:
        """
        简化验证：检查修剪后的历史记录是否包含必要元素
        
        Args:
            history: 修剪后的历史记录
            retained_chapter: 保留的章节号
        """
        logger.info("验证修剪后的历史记录...")
        
        # 获取基准上下文长度
        base_context_length = self.state_manager.get_base_context_length()
        if base_context_length <= 0:
            base_context_length = 1
        
        # 检查基准上下文
        if len(history) < base_context_length:
            logger.warning(f"修剪后历史记录长度({len(history)})小于基准上下文长度({base_context_length})")
        
        # 检查关键世界观消息
        has_critical = False
        for msg in history:
            content = msg.get("content", "")
            if "主角叫刘斗斗" in content or "书名叫《诸天：我跷着二郎腿镇压万界》" in content:
                has_critical = True
                break
        
        if has_critical:
            logger.info("修剪后历史记录中包含关键世界观消息")
        else:
            logger.warning("修剪后历史记录中缺少关键世界观消息！")
        
        # 检查第三章消息
        chapter_messages = [msg for msg in history if msg.get("chapter", 0) == retained_chapter]
        logger.info(f"修剪后保留的第{retained_chapter}章消息数量: {len(chapter_messages)}")
        
        # 检查总结
        # 使用与主修剪策略一致的识别规则：
        # 1. stage == "summary" 或者
        # 2. is_summary == True
        summary_messages = []
        for msg in history:
            stage = msg.get("stage", "")
            is_summary = msg.get("is_summary", False)
            if stage == "summary" or is_summary:
                summary_messages.append(msg)
        logger.info(f"修剪后保留的总结消息数量: {len(summary_messages)}")
        
        logger.info("历史记录验证完成")
    
    def _update_user_prompt_in_history(self, chapter_num: int, stage: str) -> None:
        """更新历史记录中的用户提示词为简化版本
        
        在LLM回复后，将对应的用户提示词替换为简化版本
        """
        history = self._load_history()
        if not history:
            return
        
        # 查找最近的对应用户消息
        user_message_index = -1
        for i in range(len(history) - 1, -1, -1):
            msg = history[i]
            if (msg.get("role") == "user" and
                msg.get("chapter") == chapter_num and
                msg.get("stage") == stage):
                user_message_index = i
                break
        
        if user_message_index == -1:
            logger.debug(f"未找到第{chapter_num}章{stage}阶段的用户消息")
            return
        
        # 生成简化提示词
        if stage == "design":
            simplified_prompt = self._render_simple_design_prompt()
        elif stage == "write":
            simplified_prompt = self._render_simple_write_prompt()
        else:
            # 其他阶段不简化
            return
        
        # 更新用户消息
        original_content = history[user_message_index]["content"]
        history[user_message_index]["content"] = simplified_prompt
        
        # 保存历史记录
        self._save_history(history)
        
        logger.info(f"已简化第{chapter_num}章{stage}阶段的用户提示词: {len(original_content)} -> {len(simplified_prompt)} 字符")
    
    def update_chapter_content_in_history(self, chapter_num: int, new_content: str) -> bool:
        """更新历史记录中指定章节的内容
        
        Args:
            chapter_num: 章节号
            new_content: 新的章节内容
            
        Returns:
            bool: 是否成功更新
        """
        history = self._load_history()
        if not history:
            logger.warning(f"历史记录为空，无法更新第{chapter_num}章内容")
            return False
        
        # 查找该章节的assistant消息（写作阶段）
        updated_count = 0
        for i, msg in enumerate(history):
            if (msg.get("role") == "assistant" and
                msg.get("chapter") == chapter_num and
                msg.get("stage") == "write"):
                
                # 更新内容
                original_content = msg["content"]
                msg["content"] = new_content
                updated_count += 1
                
                logger.info(f"更新第{chapter_num}章历史记录内容: 位置 {i}")
        
        if updated_count > 0:
            # 保存更新后的历史记录
            self._save_history(history)
            logger.info(f"成功更新第{chapter_num}章历史记录: {updated_count} 条消息")
            return True
        else:
            logger.warning(f"未找到第{chapter_num}章写作阶段的assistant消息")
            return False
    
    def get_chapter_content_from_history(self, chapter_num: int) -> Optional[str]:
        """从历史记录中获取指定章节的内容
        
        Args:
            chapter_num: 章节号
            
        Returns:
            Optional[str]: 章节内容，如果未找到则返回None
        """
        history = self._load_history()
        if not history:
            return None
        
        # 查找该章节的assistant消息（写作阶段）
        for i in range(len(history) - 1, -1, -1):
            msg = history[i]
            if (msg.get("role") == "assistant" and
                msg.get("chapter") == chapter_num and
                msg.get("stage") == "write"):
                return msg["content"]
        
        return None
    
    def run_design_phase(self) -> None:
        """执行设计阶段"""
        chapter_num = self.state_manager.get_chapter_num()
        logger.info(f"开始设计阶段 - 第{chapter_num}章")
        
        # 渲染提示词
        prompt = self._render_design_prompt()
        
        # 构建消息列表
        messages = self._get_messages_for_llm()
        messages.append({"role": "user", "content": prompt})
        
        # 调用LLM
        try:
            response = self.llm_client.chat(messages)
        except Exception as e:
            logger.error(f"设计阶段LLM调用失败: {e}")
            # 使用简化接口作为后备
            system_prompt = self._load_system_prompt()
            response = self.llm_client.simple_chat(
                user_message=prompt,
                system_message=system_prompt
            )
        
        # 保存到历史记录（用户消息不简化，等待LLM回复后再简化）
        self._add_to_history("user", prompt, chapter_num, "design", simplify_user_prompt=False)
        self._add_to_history("assistant", response, chapter_num, "design")
        
        # 状态切换到write
        self.state_manager.set_stage("write")
        
        logger.info("设计阶段完成")
    
    def generate_chapter_content(self) -> Dict[str, str]:
        """生成章节内容（作为中间变量，不写入文件）
        
        如果检测到内容与最近章节过度相似，会自动重新生成，最多重试3次。
        
        Returns:
            Dict[str, str]: 包含标题和正文的字典
        """
        chapter_num = self.state_manager.get_chapter_num()
        logger.info(f"生成章节内容 - 第{chapter_num}章")
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            # 渲染提示词
            prompt = self._render_write_prompt()
            
            # 构建消息列表
            messages = self._get_messages_for_llm()
            messages.append({"role": "user", "content": prompt})
            
            # 调用LLM
            try:
                response = self.llm_client.chat(messages)
            except Exception as e:
                logger.error(f"写作阶段LLM调用失败: {e}")
                # 使用简化接口作为后备
                system_prompt = self._load_system_prompt()
                response = self.llm_client.simple_chat(
                    user_message=prompt,
                    system_message=system_prompt
                )
            
            # 保存到历史记录（用户消息不简化，等待LLM回复后再简化）
            self._add_to_history("user", prompt, chapter_num, "write", simplify_user_prompt=False)
            self._add_to_history("assistant", response, chapter_num, "write")
            
            # 解析响应
            parsed = self.parser.parse_response(response)
            
            if not parsed.get("success", False):
                logger.warning("解析响应失败，尝试使用原始文本")
                # 使用原始响应作为正文，但进行清理
                parsed["clean_body"] = self.parser._clean_text(response)
                parsed["clean_title"] = f"第{chapter_num}章"
                logger.info("使用原始文本作为正文（已清理）")
            
            # 获取清理后的标题和正文
            # 优先使用 clean_title 和 clean_body，如果不存在则使用 title 和 body
            title = parsed.get("clean_title", parsed.get("title", f"第{chapter_num}章"))
            body = parsed.get("clean_body", parsed.get("body", ""))
            
            # 如果标题为空，使用默认标题
            if not title or title.isspace():
                title = f"第{chapter_num}章"
            
            # 如果正文为空，记录警告但继续
            if not body or body.isspace():
                logger.warning(f"第{chapter_num}章正文内容为空或仅包含空白字符")
                body = f"第{chapter_num}章内容为空。"
            
            # 检查内容是否与最近章节过度相似
            is_too_similar = self._check_content_similarity(body, chapter_num)
            
            if not is_too_similar:
                # 相似度检查通过，返回结果
                logger.info(f"第{chapter_num}章内容生成成功，相似度检查通过")
                return {
                    "title": title,
                    "body": body,
                    "chapter_num": chapter_num,
                    "retry_count": retry_count
                }
            else:
                # 内容过度相似，需要重新生成
                retry_count += 1
                logger.warning(f"第{chapter_num}章内容过度相似，正在重新生成 (第{retry_count}次重试)")
                
                # 从历史记录中删除刚刚生成的用户和助手消息
                self._remove_last_write_messages(chapter_num)
                
                # 如果达到最大重试次数，记录警告并返回当前内容
                if retry_count >= max_retries:
                    logger.warning(f"第{chapter_num}章已达到最大重试次数({max_retries})，使用当前内容")
                    return {
                        "title": title,
                        "body": body,
                        "chapter_num": chapter_num,
                        "retry_count": retry_count,
                        "warning": "内容相似度较高，但已达到最大重试次数"
                    }
        
        # 理论上不会执行到这里，但为了安全起见
        logger.error(f"第{chapter_num}章内容生成失败")
        return {
            "title": f"第{chapter_num}章",
            "body": f"第{chapter_num}章内容生成失败。",
            "chapter_num": chapter_num,
            "retry_count": retry_count,
            "error": "内容生成失败"
        }
    
    def _remove_last_write_messages(self, chapter_num: int) -> None:
        """从历史记录中删除指定章节的写作阶段消息
        
        Args:
            chapter_num: 章节号
        """
        history = self._load_history()
        if not history:
            return
        
        # 查找要删除的消息索引
        indices_to_remove = []
        for i in range(len(history) - 1, -1, -1):
            msg = history[i]
            if (msg.get("chapter") == chapter_num and
                msg.get("stage") == "write"):
                indices_to_remove.append(i)
        
        # 删除消息（从后往前删除，避免索引变化）
        indices_to_remove.sort(reverse=True)
        for idx in indices_to_remove:
            if 0 <= idx < len(history):
                removed_msg = history.pop(idx)
                logger.debug(f"删除历史记录消息: 第{chapter_num}章 {removed_msg.get('role')} {removed_msg.get('stage')}")
        
        # 保存更新后的历史记录
        self._save_history(history)
        logger.info(f"已删除第{chapter_num}章的写作阶段消息: {len(indices_to_remove)} 条")
    
    def _check_content_similarity(self, new_content: str, chapter_num: int) -> bool:
        """检查新章节内容是否与最近章节过度相似，如果过度相似则触发重新生成
        
        Args:
            new_content: 新章节内容
            chapter_num: 当前章节号
            
        Returns:
            bool: True表示内容过度相似需要重新生成，False表示相似度检查通过
        """
        try:
            # 获取内容相似度检查器
            similarity_checker = get_content_similarity_checker(similarity_threshold=0.65)
            
            # 获取最近章节的内容
            recent_chapters = []
            
            # 从历史记录中获取最近3章的内容
            history = self._load_history()
            for msg in history:
                if msg.get("role") == "assistant" and msg.get("stage") == "write":
                    msg_chapter = msg.get("chapter", 0)
                    # 只获取当前章节之前的章节
                    if 0 < msg_chapter < chapter_num:
                        recent_chapters.append({
                            "chapter_num": msg_chapter,
                            "content": msg.get("content", "")
                        })
            
            # 按章节号降序排序，获取最近的章节
            recent_chapters.sort(key=lambda x: x["chapter_num"], reverse=True)
            recent_chapters = recent_chapters[:3]  # 只检查最近3章
            
            if not recent_chapters:
                logger.info(f"第{chapter_num}章: 没有找到最近章节用于相似度检查")
                return False
            
            # 检查相似度
            is_too_similar, max_similarity, most_similar_chapter = similarity_checker.check_chapter_similarity(
                new_content, recent_chapters
            )
            
            if is_too_similar:
                logger.warning(f"第{chapter_num}章内容与第{most_similar_chapter}章过度相似: 相似度={max_similarity:.2f}")
                
                # 分析内容多样性
                diversity_analysis = similarity_checker.analyze_content_diversity(new_content)
                logger.warning(f"内容多样性分析: 长度={diversity_analysis['length']}, "
                             f"独特词汇={diversity_analysis['unique_words']}, "
                             f"多样性分数={diversity_analysis['diversity_score']:.2f}")
                
                # 触发重新生成
                logger.warning(f"第{chapter_num}章内容过度相似，将触发重新生成")
                return True
            else:
                logger.info(f"第{chapter_num}章内容相似度检查通过: 最高相似度={max_similarity:.2f} (阈值=0.65)")
                return False
                
        except Exception as e:
            logger.warning(f"内容相似度检查失败: {e}")
            # 检查失败时不触发重新生成，继续执行
            return False
    
    def write_chapter_to_file(self, title: str, body: str, chapter_num: int = None) -> str:
        """将章节内容写入文件
        
        Args:
            title: 章节标题
            body: 章节正文
            chapter_num: 章节号（如果为None，使用当前状态中的章节号）
            
        Returns:
            str: 文件路径
        """
        if chapter_num is None:
            chapter_num = self.state_manager.get_chapter_num()
        
        filepath = self._write_chapter_file(title, body)
        
        # 添加章节到窗口
        self.state_manager.add_to_window(chapter_num)
        current_window = self.state_manager.get_window_chapters()
        logger.info(f"窗口状态: {current_window} (大小: {len(current_window)}/{self.state_manager.get_window_size()})")
        
        # 检查窗口是否已满
        if self.state_manager.is_window_full():
            logger.info(f"窗口已满，触发总结阶段: {current_window}")
            self.state_manager.set_stage("summary")
        else:
            # 章节号+1，切换回design
            self.state_manager.set_chapter_num(chapter_num + 1)
            self.state_manager.set_stage("design")
            logger.info(f"窗口未满，继续下一章: 第{chapter_num + 1}章")
        
        logger.info(f"章节已写入文件: {filepath}")
        return filepath
    
    def run_write_phase(self) -> None:
        """执行写作阶段（兼容旧版本，直接写入文件）"""
        chapter_content = self.generate_chapter_content()
        self.write_chapter_to_file(
            title=chapter_content["title"],
            body=chapter_content["body"],
            chapter_num=chapter_content["chapter_num"]
        )
        logger.info("写作阶段完成")
    
    def run_summary_phase(self) -> None:
        """执行总结阶段"""
        logger.info("开始总结阶段")
        
        # 获取当前窗口状态
        window_chapters = self.state_manager.get_window_chapters()
        logger.info(f"总结阶段窗口章节: {window_chapters}")
        
        # 渲染提示词
        prompt = self._render_summary_prompt()
        
        # 构建消息列表
        messages = self._get_messages_for_llm()
        messages.append({"role": "user", "content": prompt})
        
        # 调用LLM
        try:
            response = self.llm_client.chat(messages)
        except Exception as e:
            logger.error(f"总结阶段LLM调用失败: {e}")
            # 使用简化接口作为后备
            system_prompt = self._load_system_prompt()
            response = self.llm_client.simple_chat(
                user_message=prompt,
                system_message=system_prompt
            )
        
        # 保存到历史记录
        # 总结消息的章节号设置为窗口中的最大章节号，这样可以根据章节号排序
        # 例如：窗口章节[4,5,6]，则总结的章节号设为6
        summary_chapter = 0
        if window_chapters:
            summary_chapter = max(window_chapters)
            logger.info(f"总结消息关联到章节 {summary_chapter} (窗口最大章节)")
        
        # 保存用户消息
        self._add_to_history("user", prompt, 0, "summary", simplify_user_prompt=False)
        
        # 保存助手消息（总结），使用自定义的_add_summary_to_history方法
        self._add_summary_to_history(response, summary_chapter, window_chapters)
        
        logger.info(f"总结已生成并保存到历史记录，长度: {len(response)} 字符，关联章节: {summary_chapter}")
        
        # 执行修剪逻辑
        self._execute_pruning()
        
        logger.info("总结阶段完成")
    
    def run_step(self) -> bool:
        """
        执行一步操作
        
        Returns:
            bool: 是否继续执行下一步
        """
        try:
            current_stage = self.state_manager.get_stage()
            logger.info(f"当前状态: {self.state_manager.get_state_summary()}")
            
            if current_stage == "design":
                self.run_design_phase()
            elif current_stage == "write":
                self.run_write_phase()
            elif current_stage == "summary":
                self.run_summary_phase()
            else:
                logger.error(f"未知的阶段: {current_stage}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"执行步骤时发生错误: {e}", exc_info=True)
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        history = self._load_history()
        base_context_length = self.state_manager.get_base_context_length()
        
        # 获取系统信息相关状态
        system_info_count = len(self.system_info_manager.get_all_system_info())
        last_system_info_chapter = self.state_manager.get_last_system_info_chapter()
        scheduled_chapters = self.state_manager.get_system_info_scheduled_chapters()
        cycle_start = self.state_manager.get_system_info_cycle_start()
        cycle_length = self.state_manager.get_system_info_cycle_length()
        current_chapter = self.state_manager.get_chapter_num()
        
        # 计算当前周期内的相对位置
        cycle_position = current_chapter - cycle_start + 1
        in_current_cycle = 1 <= cycle_position <= cycle_length
        
        # 检查当前章节是否在计划中
        should_insert_now = current_chapter in scheduled_chapters
        
        # 计算当前周期内剩余的插入次数
        remaining_insertions = 0
        if scheduled_chapters:
            remaining_insertions = len([ch for ch in scheduled_chapters if ch >= current_chapter])
        
        return {
            "state": self.state_manager.to_dict(),
            "history_length": len(history),
            "base_context_length": base_context_length,
            "recent_history_length": len(history) - base_context_length,
            "window_chapters": self.state_manager.get_window_chapters(),
            "window_full": self.state_manager.is_window_full(),
            "current_chapter": current_chapter,
            "current_stage": self.state_manager.get_stage(),
            "system_info": {
                "available_count": system_info_count,
                "last_inserted_chapter": last_system_info_chapter,
                "scheduled_chapters": scheduled_chapters,
                "cycle_start": cycle_start,
                "cycle_length": cycle_length,
                "cycle_position": cycle_position if in_current_cycle else None,
                "in_current_cycle": in_current_cycle,
                "should_insert_now": should_insert_now,
                "remaining_insertions_in_cycle": remaining_insertions,
                "total_scheduled_in_cycle": len(scheduled_chapters) if scheduled_chapters else 0
            }
        }