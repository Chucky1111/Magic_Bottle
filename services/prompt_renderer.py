"""
提示词渲染器 - 负责渲染各种提示词模板
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from services.feedback_b_manager import get_feedback_b_manager

logger = logging.getLogger(__name__)


class PromptRenderer:
    """提示词渲染器 - 负责渲染设计、写作、总结等阶段的提示词"""
    
    def __init__(self, state_manager, system_info_manager, sequence_manager,
                 prompt_logger, world_view_content: str = "", user_idea_manager=None):
        """
        初始化提示词渲染器
        
        Args:
            state_manager: 状态管理器实例
            system_info_manager: 系统信息管理器实例
            sequence_manager: 序列管理器实例
            prompt_logger: 提示词日志记录器实例
            world_view_content: 世界观内容
            user_idea_manager: 用户灵感管理器实例（可选）
        """
        self.state_manager = state_manager
        self.system_info_manager = system_info_manager
        self.sequence_manager = sequence_manager
        self.prompt_logger = prompt_logger
        self.world_view_content = world_view_content
        self.user_idea_manager = user_idea_manager
    
    def load_world_view(self) -> str:
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
    
    def load_system_prompt(self) -> str:
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
    
    def load_feedback_prompt_template(self) -> str:
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
    
    def load_prompt_template(self, prompt_file: str) -> str:
        """加载提示词模板文件"""
        prompt_path = Path("prompts") / prompt_file
        if not prompt_path.exists():
            raise FileNotFoundError(f"提示词文件不存在: {prompt_path}")
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def render_design_prompt(self) -> str:
        """渲染设计阶段提示词"""
        template = self.load_prompt_template("design.txt")
        
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
        
        # 用户灵感注入（design阶段）
        user_idea_content = ""
        user_idea_info = {}
        if self.user_idea_manager and self.user_idea_manager.state_manager:
            idea_result = self.user_idea_manager.get_next_idea(chapter_num, "design")
            if idea_result:
                user_idea_content, file_path, entry_index = idea_result
                user_idea_info = {
                    "file_name": file_path.name,
                    "entry_index": entry_index,
                    "content_length": len(user_idea_content)
                }
                logger.info(f"第{chapter_num}章design阶段注入用户灵感: {file_path.name}[{entry_index}]，长度: {len(user_idea_content)}")
                
                # 记录到状态管理器，以便write阶段使用相同灵感
                self.state_manager.set_current_user_idea(file_path.name, entry_index, chapter_num)
                
                # 添加注入记录（防止重复）
                self.state_manager.add_user_idea_injection(file_path.name, entry_index)
            else:
                logger.debug(f"第{chapter_num}章没有可用的用户灵感")
        else:
            logger.debug("用户灵感管理器未启用或缺少状态管理器")
        
        # 替换模板变量
        prompt = template.replace("{{chapter_num}}", str(chapter_num))
        prompt = prompt.replace("{{alert}}", alert if alert else "")
        prompt = prompt.replace("{{system_info}}", system_info if system_info else "")
        prompt = prompt.replace("{{design_body}}", design_body if design_body else "")
        prompt = prompt.replace("{{world_view}}", self.world_view_content if self.world_view_content else "")
        prompt = prompt.replace("{{user_idea}}", user_idea_content if user_idea_content else "")
        
        # 清理多余的占位符
        prompt = prompt.replace("{{alert}}", "")
        prompt = prompt.replace("{{system_info}}", "")
        prompt = prompt.replace("{{design_body}}", "")
        prompt = prompt.replace("{{world_view}}", "")
        prompt = prompt.replace("{{user_idea}}", "")
        
        # 记录模板渲染日志
        variables = {
            "chapter_num": chapter_num,
            "alert": alert if alert else "",
            "system_info_length": len(system_info) if system_info else 0,
            "design_body_length": len(design_body) if design_body else 0,
            "world_view_length": len(self.world_view_content) if self.world_view_content else 0,
            "user_idea_length": len(user_idea_content) if user_idea_content else 0,
            "user_idea_info": user_idea_info
        }
        
        self.prompt_logger.log_template_rendering(
            chapter_num=chapter_num,
            stage="design",
            template_file="design.txt",
            variables=variables,
            final_length=len(prompt)
        )
        
        return prompt
    
    def render_simple_design_prompt(self) -> str:
        """渲染简化的设计阶段提示词（用于历史记录）"""
        try:
            template = self.load_prompt_template("simple_design.txt")
        except FileNotFoundError:
            # 如果简化模板不存在，使用原始模板
            template = self.load_prompt_template("design.txt")
        
        # 获取当前章节号
        chapter_num = self.state_manager.get_chapter_num()
        
        # 简化的设计提示词不需要系统信息和序列模块
        # 只保留核心的章节号信息
        prompt = template.replace("{{chapter_num}}", str(chapter_num))
        
        # 清理多余的占位符
        prompt = prompt.replace("{{system_info}}", "")
        prompt = prompt.replace("{{design_body}}", "")
        
        return prompt
    
    def render_simple_write_prompt(self) -> str:
        """渲染简化的写作阶段提示词（用于历史记录）"""
        try:
            template = self.load_prompt_template("simple_write.txt")
        except FileNotFoundError:
            # 如果简化模板不存在，使用原始模板
            template = self.load_prompt_template("write.txt")
        
        # 获取当前章节号
        chapter_num = self.state_manager.get_chapter_num()
        
        # 替换模板变量
        # mid_chapter_num 继承 chapter_num 的值，实现同步
        prompt = template.replace("{{chapter_num}}", str(chapter_num))
        prompt = prompt.replace("{{mid_chapter_num}}", str(chapter_num))
        prompt = prompt.replace("{{write_body}}", "")
        
        return prompt
    
    def render_write_prompt(self) -> str:
        """渲染写作阶段提示词"""
        template = self.load_prompt_template("write.txt")
        
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
        
        # 获取读者 B 反馈
        feedback_b_manager = get_feedback_b_manager()
        feedback_b_content = feedback_b_manager.pop_feedback()
        if feedback_b_content is None:
            feedback_b_content = ""
        # 替换 feedback_b 变量（兼容两种拼写）
        prompt = prompt.replace("{{feedbacb_b}}", feedback_b_content)
        prompt = prompt.replace("{{feedback_b}}", feedback_b_content)
        
        # 记录读者 B 反馈使用日志
        if feedback_b_content:
            self.prompt_logger.log_feedback_usage(
                chapter_num=chapter_num,
                feedback_length=len(feedback_b_content),
                feedback_preview=feedback_b_content[:100] if feedback_b_content else "",
                feedback_type="reader_b"
            )
        
        # 用户灵感注入（write阶段，使用与design阶段相同的灵感）
        user_idea_content = ""
        user_idea_info = {}
        if self.user_idea_manager and self.user_idea_manager.state_manager:
            user_idea_content = self.user_idea_manager.get_same_idea(chapter_num, "write")
            if user_idea_content:
                user_idea_info = {
                    "content_length": len(user_idea_content)
                }
                logger.info(f"第{chapter_num}章write阶段注入用户灵感，长度: {len(user_idea_content)}")
            else:
                logger.debug(f"第{chapter_num}章write阶段没有对应的用户灵感（可能design阶段未注入）")
        else:
            logger.debug("用户灵感管理器未启用或缺少状态管理器")
        
        # 替换用户灵感变量
        prompt = prompt.replace("{{user_idea}}", user_idea_content if user_idea_content else "")
        
        # 清理多余的占位符
        prompt = prompt.replace("{{write_body}}", "")
        prompt = prompt.replace("{{world_view}}", "")
        prompt = prompt.replace("{{user_idea}}", "")
        
        # 记录模板渲染日志
        variables = {
            "chapter_num": chapter_num,
            "mid_chapter_num": chapter_num,
            "write_body_length": len(write_body) if write_body else 0,
            "world_view_length": len(self.world_view_content) if self.world_view_content else 0,
            "user_idea_length": len(user_idea_content) if user_idea_content else 0,
            "user_idea_info": user_idea_info
        }
        
        self.prompt_logger.log_template_rendering(
            chapter_num=chapter_num,
            stage="write",
            template_file="write.txt",
            variables=variables,
            final_length=len(prompt)
        )
        
        return prompt
    
    def render_summary_prompt(self) -> str:
        """渲染总结阶段提示词"""
        template = self.load_prompt_template("summary.txt")
        
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

    def render_summary_b_prompt(self) -> str:
        """渲染总结B阶段提示词（在常规总结之前调用）"""
        template = self.load_prompt_template("summary_b")
        
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
        
        # 替换模板变量（与常规总结使用相同的变量集）
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
        
        logger.info(f"总结B提示词已渲染: 窗口章节={window_chapters}, 下一章={next_chapter_1},{next_chapter_2}")
        
        return prompt

    def render_summary_c_prompt(self) -> str:
        """渲染总结C阶段提示词（在summary_b和常规总结之前调用）"""
        template = self.load_prompt_template("summary_c.txt")
        
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
        
        # 替换模板变量（与常规总结使用相同的变量集）
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
        
        logger.info(f"总结C提示词已渲染: 窗口章节={window_chapters}, 下一章={next_chapter_1},{next_chapter_2}")
        
        return prompt