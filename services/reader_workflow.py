"""
读者工作流 - 实现读者模块的线性对话流
沿用1-3-1架构，但阶段为memerry和feedback
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

from core.llm import LLMClient
from core.reader_parser import ReaderParser
from services.reader_state_manager import ReaderStateManager
from services.warmup_runner import WarmupRunner
from config.settings import settings

logger = logging.getLogger(__name__)


class ReaderWorkflow:
    """读者工作流 - 实现读者模块的线性对话流"""
    
    def __init__(self):
        """初始化读者工作流"""
        self.llm_client = LLMClient(config=settings.reader_llm.get_client_config())
        self.parser = ReaderParser()
        self.state_manager = ReaderStateManager()
        self.warmup_runner = WarmupRunner()  # 复用预热运行器
        
        # 加载世界观文件
        self.world_view_content = self._load_world_view()
        
        # 确保必要的目录存在
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # 初始化系统（检查是否需要运行读者预热）
        self._initialize_system()
        
        logger.info("ReaderWorkflow初始化完成")
    
    def _initialize_system(self) -> None:
        """初始化系统：检查是否需要运行读者预热流程"""
        reader_history_path = Path(self.state_manager.get_reader_history_file())
        
        # Case A: Fresh Start (全新启动)
        if not reader_history_path.exists() or reader_history_path.stat().st_size == 0:
            logger.info("检测到读者模块全新启动，开始运行读者预热流程...")
            
            # 运行读者预热
            self._run_reader_warmup(reader_history_path)
            
            logger.info("读者预热完成，准备开始处理章节")
    
    def _run_reader_warmup(self, history_path: Path) -> None:
        """
        运行读者预热流程
        
        Args:
            history_path: 历史记录文件路径
        """
        # 加载读者系统提示词
        system_content = self._load_reader_system_prompt()
        
        # 加载读者预热问题
        questions = self._parse_reader_warmup_questions()
        
        if not questions:
            logger.warning("没有找到读者预热问题，创建最小化历史记录")
            self._create_minimal_reader_history(history_path, system_content)
            return
        
        # 构建消息列表
        messages = [{"role": "system", "content": system_content}]
        
        # 依次处理每个问题
        for i, question in enumerate(questions, 1):
            try:
                logger.info(f"运行读者预热 Q{i}/{len(questions)}")
                
                # 添加当前问题到消息列表
                user_message = {"role": "user", "content": question}
                current_messages = messages + [user_message]
                
                # 调用 LLM
                response = self.llm_client.chat(current_messages)
                
                # 获取回答
                assistant_message = {"role": "assistant", "content": response}
                
                # 将问答对添加到消息列表
                messages.append(user_message)
                messages.append(assistant_message)
                
                logger.info(f"  读者预热 Q{i} 完成，回答长度: {len(response)} 字符")
                
                # 短暂暂停，避免 API 限流
                if i < len(questions):
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"运行读者预热 Q{i} 失败: {e}")
                continue
        
        # 保存历史记录
        self._save_reader_history(messages, history_path)
        
        # 设置基准上下文长度
        self.state_manager.set_base_context_length(len(messages))
        
        logger.info(f"读者预热流程完成，生成 {len(messages)} 条消息")
    
    def _create_minimal_reader_history(self, history_path: Path, system_content: str) -> None:
        """创建最小化读者历史记录（仅系统消息）"""
        history = [{
            "role": "system",
            "content": system_content,
            "timestamp": 0,
            "chapter": 0,
            "stage": "base",
            "is_base_context": True
        }]
        
        self._save_reader_history(history, history_path)
        self.state_manager.set_base_context_length(1)
        
        logger.info("创建最小化读者历史记录（仅系统消息）")
    
    def _save_reader_history(self, messages: List[Dict[str, Any]], history_path: Path) -> None:
        """保存读者历史记录"""
        try:
            history_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 转换为历史记录格式
            history = []
            for i, msg in enumerate(messages):
                history_msg = {
                    "role": msg["role"],
                    "content": msg["content"],
                    "timestamp": time.time() if i > 0 else 0,
                    "chapter": 0,
                    "stage": "base",
                    "is_base_context": True
                }
                history.append(history_msg)
            
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
            logger.info(f"读者历史记录已保存到: {history_path} ({len(history)} 条消息)")
            
        except Exception as e:
            logger.error(f"保存读者历史记录失败: {e}")
    
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
    
    def _load_reader_system_prompt(self) -> str:
        """加载读者系统提示词"""
        system_prompt_path = Path("prompts/reader/reader_system_prompt.txt")
        if not system_prompt_path.exists():
            logger.warning(f"读者系统提示词文件不存在: {system_prompt_path}")
            return "你是一位真实的网文读者，喜欢阅读各种故事。"
        
        try:
            with open(system_prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            logger.debug(f"读者系统提示词已加载，长度: {len(content)} 字符")
            return content
        except Exception as e:
            logger.error(f"加载读者系统提示词失败: {e}")
            return "你是一位真实的网文读者，喜欢阅读各种故事。"
    
    def _parse_reader_warmup_questions(self) -> List[str]:
        """解析读者预热问题"""
        warmup_file_path = Path("prompts/reader/reader_warmup.md")
        if not warmup_file_path.exists():
            logger.warning(f"读者预热文件不存在: {warmup_file_path}")
            return []
        
        try:
            with open(warmup_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换世界观占位符
            if self.world_view_content:
                content = content.replace("{{world_view}}", self.world_view_content)
            else:
                content = content.replace("{{world_view}}", "")
            
            # 使用 '---' 作为分隔符
            sections = content.split('---')
            
            questions = []
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                
                # 提取问题（去除可能的标题行）
                lines = section.split('\n')
                question_lines = []
                
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    question_lines.append(line)
                
                if question_lines:
                    question = ' '.join(question_lines)
                    questions.append(question)
            
            logger.info(f"从读者预热文件解析出 {len(questions)} 个问题")
            return questions
            
        except Exception as e:
            logger.error(f"解析读者预热文件失败: {e}")
            return []
    
    def _load_prompt_template(self, prompt_file: str) -> str:
        """加载提示词模板文件"""
        prompt_path = Path("prompts/reader") / prompt_file
        if not prompt_path.exists():
            # 尝试在prompts目录下查找
            prompt_path = Path("prompts") / prompt_file
            if not prompt_path.exists():
                raise FileNotFoundError(f"读者提示词文件不存在: {prompt_file}")
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _render_memerry_prompt(self, chapter_content: str) -> str:
        """渲染记忆阶段提示词"""
        try:
            template = self._load_prompt_template("reader_memerry.md")
        except FileNotFoundError:
            # 使用默认模板
            template = """# 记忆
这是你对这本小说的印象：{{readermemerry}}
请阅读这份内容：
{{draft}}
记录你的感受和对故事的记忆点
格式：
<内容>
<memerry>记忆点</memerry>
<其他内容：备注或思考>其它内容</其他内容：备注或思考>
</内容>"""
        
        # 获取当前读者记忆
        reader_memory = self.state_manager.get_reader_memory()
        
        # 替换模板变量
        prompt = template.replace("{{readermemerry}}", reader_memory)
        prompt = prompt.replace("{{draft}}", chapter_content)
        prompt = prompt.replace("{{world_view}}", self.world_view_content if self.world_view_content else "")
        
        return prompt
    
    def _render_feedback_prompt(self, window_chapters: List[int]) -> str:
        """渲染反馈阶段提示词，基于读者记忆和窗口章节"""
        try:
            template = self._load_prompt_template("reader_feedback.md")
        except FileNotFoundError:
            # 使用默认模板
            template = """# 写给作者的话
基于你对最近三章的记忆，给作者提供反馈：
{{readermemerry}}

请基于以上记忆，给作者提供具体的反馈：
1. 剧情节奏是否合适？
2. 人物塑造是否鲜明？
3. 有没有你特别关注的伏笔或情节？
4. 有什么建议或改进意见？

**重要：必须严格按照以下格式回复，只使用指定的XML标签：**

<内容>
<feedback>第一条反馈，不超过100字，言简意赅</feedback>
<feedback>第二条反馈，不超过100字，言简意赅</feedback>
<feedback>第三条反馈，不超过100字，言简意赅</feedback>
<other>其他备注或思考（可选）</other>
</内容>

**注意：**
1. 只使用`<feedback>`和`<other>`标签，不要使用其他标签
2. 每条反馈不超过100字，提供1-3条关键反馈
3. 反馈要具体，基于实际章节内容
4. `<feedback>`标签内的内容将作为读者反馈被保存"""
        
        # 获取当前读者记忆
        reader_memory = self.state_manager.get_reader_memory()
        
        # 替换模板变量
        prompt = template.replace("{{readermemerry}}", reader_memory)
        
        return prompt
    
    def _render_packet_prompt(self) -> str:
        """渲染整理记忆提示词"""
        try:
            template = self._load_prompt_template("reader_packet.md")
        except FileNotFoundError:
            # 使用默认模板
            template = """# 整理记忆
你的读者记忆：{{readermemerry}}
你的记忆内容有点太多了，整理一下，留下你最近正在关注的和需要以后也留意的长线。
格式：
<内容>
<memerry>喊话内容，不超过一百字，言简意赅，信息简洁明了</memerry>
<other>其它内容</other>
</内容>"""
        
        # 获取当前读者记忆
        reader_memory = self.state_manager.get_reader_memory()
        
        # 替换模板变量
        prompt = template.replace("{{readermemerry}}", reader_memory)
        prompt = prompt.replace("{{world_view}}", self.world_view_content if self.world_view_content else "")
        prompt = prompt.replace("{{world_view}}", self.world_view_content if self.world_view_content else "")
        
        return prompt
    
    def _run_memory_packet(self, chapter_num: int) -> str:
        """
        运行记忆整理，当记忆长度达到2000字符时调用
        
        Args:
            chapter_num: 当前章节号
            
        Returns:
            整理后的记忆内容
        """
        logger.info(f"开始整理读者记忆 - 第{chapter_num}章，当前记忆长度: {len(self.state_manager.get_reader_memory())} 字符")
        
        # 渲染整理记忆提示词
        packet_prompt = self._render_packet_prompt()
        
        # 构建消息列表（使用当前读者历史记录）
        messages = self._get_messages_for_llm()
        messages.append({"role": "user", "content": packet_prompt})
        
        # 调用LLM
        try:
            response = self.llm_client.chat(messages)
        except Exception as e:
            logger.error(f"记忆整理LLM调用失败: {e}")
            # 使用简化接口作为后备
            system_prompt = self._load_reader_system_prompt()
            response = self.llm_client.simple_chat(
                user_message=packet_prompt,
                system_message=system_prompt
            )
        
        # 保存到读者历史记录，标记为packet阶段，以便后续修剪时删除
        self._add_to_reader_history("user", packet_prompt, chapter_num, "packet")
        self._add_to_reader_history("assistant", response, chapter_num, "packet")
        
        # 解析响应
        parsed = self.parser.parse_memerry_response(response)
        
        if parsed.get("success", False):
            # 返回整理后的记忆
            packed_memory = parsed["memerry"]
            logger.info(f"记忆整理完成，整理后长度: {len(packed_memory)} 字符")
            return packed_memory
        else:
            logger.warning("记忆整理解析失败，返回原始记忆")
            return self.state_manager.get_reader_memory()
    
    def _get_latest_chapter_content(self) -> Optional[str]:
        """获取最新章节内容"""
        # 获取output目录下所有章节文件
        chapter_files = list(self.output_dir.glob("第*章_*.txt"))
        if not chapter_files:
            logger.warning("output目录中没有找到章节文件")
            return None
        
        # 按修改时间排序，获取最新的文件
        latest_file = max(chapter_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"读取最新章节文件: {latest_file.name}, 长度: {len(content)} 字符")
            return content
            
        except Exception as e:
            logger.error(f"读取章节文件失败: {e}")
            return None
    
    def _get_window_chapters_content(self, window_chapters: List[int]) -> str:
        """获取窗口章节的内容摘要"""
        if not window_chapters:
            return "暂无章节内容"
        
        content_parts = []
        
        for chapter_num in window_chapters:
            # 查找对应章节文件
            chapter_files = list(self.output_dir.glob(f"第{chapter_num}章_*.txt"))
            if not chapter_files:
                continue
            
            chapter_file = chapter_files[0]
            try:
                with open(chapter_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 取前200字符作为摘要
                summary = content[:200] + "..." if len(content) > 200 else content
                content_parts.append(f"第{chapter_num}章摘要: {summary}")
                
            except Exception as e:
                logger.error(f"读取第{chapter_num}章内容失败: {e}")
                content_parts.append(f"第{chapter_num}章: 读取失败")
        
        return "\n\n".join(content_parts)
    
    def _get_chapter_number_from_filename(self, filename: str) -> int:
        """从文件名中提取章节号"""
        import re
        match = re.search(r'第(\d+)章', filename)
        if match:
            return int(match.group(1))
        return 0
    
    def _get_messages_for_llm(self) -> List[Dict[str, str]]:
        """
        构建发送给LLM的消息列表
        
        返回格式: [{"role": "system", "content": "..."}, ...]
        包含基准上下文 + 当前窗口内的历史对话
        """
        # 加载读者历史记录
        history_path = Path(self.state_manager.get_reader_history_file())
        if not history_path.exists():
            return []
        
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except Exception as e:
            logger.error(f"加载读者历史记录失败: {e}")
            return []
        
        # 转换为OpenAI格式
        messages = []
        for msg in history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        logger.debug(f"构建了 {len(messages)} 条读者消息给LLM")
        return messages
    
    def _add_to_reader_history(self, role: str, content: str, chapter_num: int, stage: str) -> None:
        """添加消息到读者历史记录"""
        history_path = Path(self.state_manager.get_reader_history_file())
        
        # 加载现有历史记录
        history = []
        if history_path.exists():
            try:
                with open(history_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except Exception as e:
                logger.error(f"加载读者历史记录失败: {e}")
        
        # 添加新消息
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "chapter": chapter_num,
            "stage": stage,
            "is_base_context": False
        }
        
        history.append(message)
        
        # 保存历史记录
        try:
            history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"读者历史记录已添加: {role} - 第{chapter_num}章 - {stage}")
            
        except Exception as e:
            logger.error(f"保存读者历史记录失败: {e}")
    
    def _save_memerry_to_file(self, memerry_content: str) -> None:
        """保存读者记忆到prompts/reader/memerry.txt文件（覆盖写入）"""
        memerry_path = Path("prompts/reader/memerry.txt")
        
        try:
            memerry_path.parent.mkdir(parents=True, exist_ok=True)
            with open(memerry_path, 'w', encoding='utf-8') as f:
                f.write(memerry_content)
            
            logger.info(f"读者记忆已保存到: {memerry_path}, 长度: {len(memerry_content)} 字符")
            
        except Exception as e:
            logger.error(f"保存读者记忆失败: {e}")
    
    def _save_feedback_to_file(self, feedbacks: List[str], chapter_num: int) -> None:
        """保存反馈到data/feedback.txt文件，包含章节信息"""
        feedback_path = Path("data/feedback.txt")
        
        try:
            feedback_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 读取现有反馈（如果有）
            existing_feedback = ""
            if feedback_path.exists():
                with open(feedback_path, 'r', encoding='utf-8') as f:
                    existing_feedback = f.read().strip()
            
            # 解析现有反馈以确定下一个索引
            next_index = 1
            if existing_feedback and "## 反馈" in existing_feedback:
                # 使用正则表达式查找所有反馈索引
                import re
                index_matches = re.findall(r'##\s*反馈\s*(\d+)', existing_feedback)
                if index_matches:
                    # 找到最大索引并加1
                    max_index = max(int(idx) for idx in index_matches)
                    next_index = max_index + 1
            
            # 格式化新反馈，使用正确的索引
            formatted_lines = []
            if not existing_feedback or existing_feedback.isspace():
                # 文件为空，添加标题
                formatted_lines.append("# 读者反馈")
            elif not existing_feedback.startswith("# 读者反馈"):
                # 文件有内容但没有标题，添加标题
                formatted_lines.append("# 读者反馈")
                formatted_lines.append("")  # 空行
            
            # 添加现有内容（如果有）
            if existing_feedback and not existing_feedback.isspace():
                formatted_lines.append(existing_feedback)
            
            # 添加新反馈
            for i, fb in enumerate(feedbacks, next_index):
                fb_clean = fb.strip()
                if not fb_clean:
                    continue
                
                # 确保前面有空行
                if formatted_lines and not formatted_lines[-1].endswith('\n\n'):
                    formatted_lines.append("")
                
                formatted_lines.append(f"## 反馈 {i}（来自第{chapter_num}章的读者）")
                formatted_lines.append(fb_clean)
            
            # 写入文件
            with open(feedback_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(formatted_lines))
            
            logger.info(f"读者反馈已保存到: {feedback_path}, 反馈数量: {len(feedbacks)}, 来自第{chapter_num}章，起始索引: {next_index}")
            
        except Exception as e:
            logger.error(f"保存读者反馈失败: {e}")
    
    def run_memerry_phase(self, chapter_content: str, chapter_num: int) -> None:
        """执行记忆阶段"""
        logger.info(f"开始记忆阶段 - 第{chapter_num}章")
        
        # 渲染提示词
        prompt = self._render_memerry_prompt(chapter_content)
        
        # 构建消息列表
        messages = self._get_messages_for_llm()
        messages.append({"role": "user", "content": prompt})
        
        # 调用LLM
        try:
            response = self.llm_client.chat(messages)
        except Exception as e:
            logger.error(f"记忆阶段LLM调用失败: {e}")
            # 使用简化接口作为后备
            system_prompt = self._load_reader_system_prompt()
            response = self.llm_client.simple_chat(
                user_message=prompt,
                system_message=system_prompt
            )
        
        # 保存到读者历史记录
        self._add_to_reader_history("user", prompt, chapter_num, "memerry")
        self._add_to_reader_history("assistant", response, chapter_num, "memerry")
        
        # 解析响应
        parsed = self.parser.parse_memerry_response(response)
        
        if parsed.get("success", False):
            # 更新读者记忆
            old_memory = self.state_manager.get_reader_memory()
            new_memory = parsed["memerry"]
            combined_memory = self.parser.combine_memerry(old_memory, new_memory)
            
            # 检查记忆长度是否达到2000字符，如果是则整理记忆
            if len(combined_memory) >= 2000:
                logger.info(f"读者记忆达到 {len(combined_memory)} 字符，触发记忆整理")
                packed_memory = self._run_memory_packet(chapter_num)
                # 使用整理后的记忆
                self.state_manager.set_reader_memory(packed_memory)
                # 保存整理后的记忆到文件
                self._save_memerry_to_file(packed_memory)
                logger.info(f"记忆整理完成，整理后长度: {len(packed_memory)} 字符")
            else:
                # 未达到2000字符，使用合并后的记忆
                self.state_manager.set_reader_memory(combined_memory)
                # 保存记忆到文件 prompts\reader\memerry.txt（覆盖写入）
                self._save_memerry_to_file(combined_memory)
                logger.info(f"记忆阶段完成，记忆长度: {len(combined_memory)} 字符，已保存到文件")
        else:
            logger.warning("记忆解析失败，保留原有记忆")
        
        # 添加章节到窗口
        self.state_manager.add_to_window(chapter_num)
        
        # 检查窗口是否已满，如果满则切换到feedback阶段
        if self.state_manager.is_window_full():
            self.state_manager.set_stage("feedback")
            logger.info(f"窗口已满（{self.state_manager.get_window_chapters()}），准备进入反馈阶段")
        else:
            # 窗口未满，继续memerry阶段
            self.state_manager.set_stage("memerry")
            logger.info(f"窗口未满（{self.state_manager.get_window_chapters()}），继续记忆阶段")
        
        # 更新最后处理的章节号
        self.state_manager.set_last_processed_chapter(chapter_num)
        
        logger.info("记忆阶段完成")
    
    def _execute_pruning(self) -> None:
        """
        执行读者历史记录修剪逻辑
        
        当窗口满时执行反馈阶段后调用：
        1. 删除窗口中前两章的所有记录，保留第三章
        2. 保留基准上下文（系统提示词 + 预热对话）
        3. 删除packet阶段的问答对（记忆整理对话）
        4. 保留最新的反馈消息（如果有）
        """
        logger.info("开始执行读者历史记录修剪逻辑")
        
        # 获取当前窗口章节
        window_chapters = self.state_manager.get_window_chapters()
        if len(window_chapters) != 3:
            logger.error(f"读者窗口章节数量不正确: {window_chapters}，应为3章")
            return
        
        chapter_1, chapter_2, chapter_3 = window_chapters  # 示例: [5, 6, 7]
        
        # 加载完整读者历史记录
        history_path = Path(self.state_manager.get_reader_history_file())
        if not history_path.exists():
            logger.warning("读者历史记录文件不存在，跳过修剪")
            return
        
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                full_history = json.load(f)
        except Exception as e:
            logger.error(f"加载读者历史记录失败: {e}")
            return
        
        # 获取基准上下文长度
        base_context_length = self.state_manager.get_base_context_length()
        if base_context_length <= 0:
            base_context_length = 1  # 至少包含系统消息
        
        # 从历史记录中物理删除：
        # 1. 前两章的所有记录
        # 2. packet阶段的问答对（记忆整理对话）
        chapters_to_remove = [chapter_1, chapter_2]
        
        new_history = []
        for i, msg in enumerate(full_history):
            chapter = msg.get("chapter", 0)
            is_base = msg.get("is_base_context", False)
            stage = msg.get("stage", "")
            
            # 情况1：保留基准上下文（系统提示词 + 预热对话）
            if i < base_context_length:
                new_history.append(msg)
                logger.debug(f"保留读者基准上下文消息 {i}: {msg.get('stage', 'base')}")
                continue
            
            # 情况2：保留第三章的所有记录（除了packet阶段）
            if chapter == chapter_3:
                # 检查是否为packet阶段，如果是则删除
                if stage == "packet":
                    logger.debug(f"删除读者packet阶段消息 {i}: 第{chapter}章 {stage}")
                    continue  # 跳过，不添加
                new_history.append(msg)
                logger.debug(f"保留读者第三章消息 {i}: 第{chapter}章 {stage}")
                continue
            
            # 情况3：删除前两章的所有记录
            if chapter in chapters_to_remove:
                logger.debug(f"删除读者前两章消息 {i}: 第{chapter}章 {stage}")
                continue  # 跳过，不添加
            
            # 情况4：删除其他章节的packet阶段消息
            if stage == "packet":
                logger.debug(f"删除读者packet阶段消息 {i}: 第{chapter}章 {stage}")
                continue  # 跳过，不添加
            
            # 情况5：其他消息（可能是旧的已修剪章节）也删除
            # 这样可以确保上下文干净
            logger.debug(f"删除读者其他消息 {i}: 第{chapter}章 {stage}")
        
        # 保存修剪后的历史记录
        try:
            history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(new_history, f, ensure_ascii=False, indent=2)
            
            logger.info(f"读者历史记录修剪完成: 删除了章节 {chapters_to_remove} 和所有packet阶段消息，保留章节 {chapter_3}")
            logger.info(f"读者历史记录长度: {len(full_history)} -> {len(new_history)}")
            
        except Exception as e:
            logger.error(f"保存修剪后的读者历史记录失败: {e}")
    
    def run_feedback_phase(self, chapter_num: int) -> None:
        """执行反馈阶段（只在窗口满时调用）"""
        logger.info(f"开始反馈阶段 - 第{chapter_num}章")
        
        # 获取窗口章节
        window_chapters = self.state_manager.get_window_chapters()
        logger.info(f"反馈阶段基于窗口章节: {window_chapters}")
        
        # 渲染提示词（传入窗口章节信息）
        prompt = self._render_feedback_prompt(window_chapters)
        
        # 构建消息列表
        messages = self._get_messages_for_llm()
        messages.append({"role": "user", "content": prompt})
        
        # 调用LLM
        try:
            response = self.llm_client.chat(messages)
        except Exception as e:
            logger.error(f"反馈阶段LLM调用失败: {e}")
            # 使用简化接口作为后备
            system_prompt = self._load_reader_system_prompt()
            response = self.llm_client.simple_chat(
                user_message=prompt,
                system_message=system_prompt
            )
        
        # 保存到读者历史记录
        self._add_to_reader_history("user", prompt, chapter_num, "feedback")
        self._add_to_reader_history("assistant", response, chapter_num, "feedback")
        
        # 解析响应
        parsed = self.parser.parse_feedback_response(response)
        
        if parsed.get("success", False):
            # 保存反馈到文件，传递当前章节号
            self._save_feedback_to_file(parsed["feedbacks"], chapter_num)
            
            logger.info(f"反馈阶段完成，生成 {len(parsed['feedbacks'])} 条反馈，来自第{chapter_num}章")
        else:
            logger.warning("反馈解析失败，未生成有效反馈")
        
        # 更新最后处理的章节号
        self.state_manager.set_last_processed_chapter(chapter_num)
        
        # 执行修剪逻辑
        self._execute_pruning()
        
        # 清空窗口，重新开始积累
        self.state_manager.clear_window()
        
        # 状态切换回memerry
        self.state_manager.set_stage("memerry")
        
        logger.info("反馈阶段完成，窗口已清空")
    
    def should_process_chapter(self, chapter_num: int) -> bool:
        """
        检查是否应该处理指定章节
        
        Args:
            chapter_num: 章节号
            
        Returns:
            如果应该处理则返回True
        """
        last_processed = self.state_manager.get_last_processed_chapter()
        
        # 检查是否应该处理指定章节
        if chapter_num > last_processed:
            return True
        
        return False
    
    def get_latest_chapter_info(self) -> Optional[Dict[str, Any]]:
        """
        获取最新章节信息
        
        Returns:
            最新章节信息字典，包含章节号和内容
        """
        # 获取output目录下所有章节文件
        chapter_files = list(self.output_dir.glob("第*章_*.txt"))
        if not chapter_files:
            return None
        
        # 按文件名中的章节号排序
        def extract_chapter_num(filename: str) -> int:
            import re
            match = re.search(r'第(\d+)章', filename)
            return int(match.group(1)) if match else 0
        
        # 按章节号排序
        sorted_files = sorted(chapter_files, key=lambda f: extract_chapter_num(f.name))
        
        # 获取最新的文件（章节号最大的）
        latest_file = sorted_files[-1]
        chapter_num = extract_chapter_num(latest_file.name)
        
        # 检查是否已经处理过
        if not self.should_process_chapter(chapter_num):
            return None
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "chapter_num": chapter_num,
                "content": content,
                "filename": latest_file.name
            }
            
        except Exception as e:
            logger.error(f"读取章节文件失败: {e}")
            return None
    
    def run_step(self) -> bool:
        """
        执行读者模块的一步操作
        
        Returns:
            bool: 是否执行了操作（有新的章节需要处理）
        """
        try:
            # 检查是否有新的章节需要处理
            chapter_info = self.get_latest_chapter_info()
            if not chapter_info:
                logger.debug("没有新的章节需要处理")
                return False
            
            chapter_num = chapter_info["chapter_num"]
            chapter_content = chapter_info["content"]
            
            logger.info(f"开始处理第{chapter_num}章 - 读者模块")
            
            current_stage = self.state_manager.get_stage()
            logger.info(f"读者当前状态: {self.state_manager.get_state_summary()}")
            
            if current_stage == "memerry":
                self.run_memerry_phase(chapter_content, chapter_num)
            elif current_stage == "feedback":
                self.run_feedback_phase(chapter_num)
            else:
                logger.error(f"未知的读者阶段: {current_stage}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"执行读者步骤时发生错误: {e}", exc_info=True)
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取读者工作流状态"""
        # 获取读者历史记录长度
        history_path = Path(self.state_manager.get_reader_history_file())
        history_length = 0
        if history_path.exists():
            try:
                with open(history_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                history_length = len(history)
            except:
                pass
        
        return {
            "state": self.state_manager.to_dict(),
            "history_length": history_length,
            "base_context_length": self.state_manager.get_base_context_length(),
            "window_chapters": self.state_manager.get_window_chapters(),
            "window_full": self.state_manager.is_window_full(),
            "last_processed_chapter": self.state_manager.get_last_processed_chapter(),
            "current_stage": self.state_manager.get_stage(),
            "reader_memory_length": len(self.state_manager.get_reader_memory()),
        }


def main():
    """测试函数"""
    import sys
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("读者工作流测试")
    print("=" * 60)
    
    workflow = ReaderWorkflow()
    
    # 显示状态
    status = workflow.get_status()
    print(f"读者状态: {status['state']}")
    print(f"最后处理章节: {status['last_processed_chapter']}")
    print(f"当前阶段: {status['current_stage']}")
    print(f"读者记忆长度: {status['reader_memory_length']} 字符")
    
    # 检查是否有新章节
    chapter_info = workflow.get_latest_chapter_info()
    if chapter_info:
        print(f"\n发现新章节: 第{chapter_info['chapter_num']}章")
        print(f"文件: {chapter_info['filename']}")
        print(f"内容长度: {len(chapter_info['content'])} 字符")
        
        # 询问是否运行读者模块
        response = input("\n是否运行读者模块处理此章节？ (y/N): ").strip().lower()
        if response == 'y':
            print("\n开始运行读者模块...")
            success = workflow.run_step()
            if success:
                print("读者模块执行成功")
                new_status = workflow.get_status()
                print(f"更新后的最后处理章节: {new_status['last_processed_chapter']}")
            else:
                print("读者模块执行失败")
    else:
        print("\n没有发现需要处理的新章节")
    
    print("\n测试完成")


if __name__ == "__main__":
    main()
