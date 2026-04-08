"""
Auditor工作流 - 实现章节质量审计和3-2-1重写流程
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

from core.llm import LLMClient
from core.auditor_parser import AuditorParser
from services.auditor_state_manager import AuditorStateManager

logger = logging.getLogger(__name__)


class AuditorWorkflow:
    """Auditor工作流 - 实现章节质量审计和重写流程"""
    
    def __init__(self):
        """初始化auditor工作流"""
        self.llm_client = LLMClient()
        self.parser = AuditorParser()
        self.state_manager = AuditorStateManager()
        
        # 确保必要的目录存在
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # 初始化系统（检查是否需要运行审计预热）
        self._initialize_system()
        
        logger.info("AuditorWorkflow初始化完成")
    
    def _initialize_system(self) -> None:
        """初始化系统：检查是否需要运行审计预热流程"""
        auditor_history_path = Path(self.state_manager.get_auditor_history_file())
        
        # Case A: Fresh Start (全新启动)
        if not auditor_history_path.exists() or auditor_history_path.stat().st_size == 0:
            logger.info("检测到auditor模块全新启动，开始运行审计预热流程...")
            
            # 运行审计预热
            self._run_auditor_warmup(auditor_history_path)
            
            logger.info("审计预热完成，准备开始审计章节")
    
    def _run_auditor_warmup(self, history_path: Path) -> None:
        """
        运行审计预热流程
        
        Args:
            history_path: 历史记录文件路径
        """
        import time
        
        # 加载审计系统提示词
        system_content = self._load_system_prompt()
        
        # 加载审计预热问题
        questions = self._parse_auditor_warmup_questions()
        
        if not questions:
            logger.warning("没有找到审计预热问题，创建最小化历史记录")
            self._create_minimal_auditor_history(history_path, system_content)
            return
        
        # 构建消息列表
        messages = [{"role": "system", "content": system_content}]
        
        # 依次处理每个问题
        for i, question in enumerate(questions, 1):
            try:
                logger.info(f"运行审计预热 Q{i}/{len(questions)}")
                
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
                
                logger.info(f"  审计预热 Q{i} 完成，回答长度: {len(response)} 字符")
                
                # 短暂暂停，避免 API 限流
                if i < len(questions):
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"运行审计预热 Q{i} 失败: {e}")
                continue
        
        # 保存历史记录
        self._save_auditor_history(messages, history_path)
        
        logger.info(f"审计预热流程完成，生成 {len(messages)} 条消息")
    
    def _create_minimal_auditor_history(self, history_path: Path, system_content: str) -> None:
        """创建最小化auditor历史记录（仅系统消息）"""
        import time
        
        history = [{
            "role": "system",
            "content": system_content,
            "timestamp": 0,
            "chapter": 0,
            "stage": "base",
            "is_base_context": True
        }]
        
        self._save_auditor_history(history, history_path)
        
        logger.info("创建最小化auditor历史记录（仅系统消息）")
    
    def _save_auditor_history(self, messages: List[Dict[str, Any]], history_path: Path) -> None:
        """保存auditor历史记录"""
        import time
        
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
            
            logger.info(f"Auditor历史记录已保存到: {history_path} ({len(history)} 条消息)")
            
        except Exception as e:
            logger.error(f"保存auditor历史记录失败: {e}")
    
    def _parse_auditor_warmup_questions(self) -> List[str]:
        """解析审计预热问题"""
        warmup_file_path = Path("prompts/Auditor/warmup.md")
        if not warmup_file_path.exists():
            logger.warning(f"审计预热文件不存在: {warmup_file_path}")
            return []
        
        try:
            with open(warmup_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
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
            
            logger.info(f"从审计预热文件解析出 {len(questions)} 个问题")
            return questions
            
        except Exception as e:
            logger.error(f"解析审计预热文件失败: {e}")
            return []
    
    def _load_system_prompt(self) -> str:
        """加载审计系统提示词"""
        system_prompt_path = Path("prompts/Auditor/system_prompt.txt")
        if not system_prompt_path.exists():
            logger.warning(f"审计系统提示词文件不存在: {system_prompt_path}")
            return "你是一位专业的小说质量审计员，负责审查AI生成的小说章节质量。"
        
        try:
            with open(system_prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            logger.debug(f"审计系统提示词已加载，长度: {len(content)} 字符")
            return content
        except Exception as e:
            logger.error(f"加载审计系统提示词失败: {e}")
            return "你是一位专业的小说质量审计员，负责审查AI生成的小说章节质量。"
    
    def _load_prompt_template(self, prompt_file: str) -> str:
        """加载提示词模板文件"""
        prompt_path = Path("prompts/Auditor") / prompt_file
        if not prompt_path.exists():
            raise FileNotFoundError(f"审计提示词文件不存在: {prompt_path}")
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _render_auditor_memerry_prompt(self, chapter_content: str) -> str:
        """渲染auditor记忆提示词"""
        try:
            template = self._load_prompt_template("auditor_memerry.md")
        except FileNotFoundError:
            # 使用默认模板
            template = """# 记忆
这是你对这本小说的印象：{{auditmemerry}}
请阅读这份内容：
{{draft}}

记录你对这一章的感受和对故事的记忆点。

**重要：必须严格按照以下格式回复，只使用指定的XML标签：**

<内容>
<memerry>在这里写下你对这一章的记忆点，包括情节、人物、情感反应等</memerry>
<other>其他备注或思考（可选）</other>
</内容>"""
        
        # 获取当前auditor记忆
        auditor_memory = self.state_manager.get_auditor_memory()
        
        # 替换模板变量
        prompt = template.replace("{{auditmemerry}}", auditor_memory)
        prompt = prompt.replace("{{draft}}", chapter_content)
        
        return prompt
    
    def _render_auditor_packet_prompt(self) -> str:
        """渲染auditor记忆整理提示词"""
        try:
            template = self._load_prompt_template("auditor_packet.md")
        except FileNotFoundError:
            # 使用默认模板
            template = """# 整理审计记忆
你的审计记忆：{{auditmemerry}}
你的记忆内容有点太多了，整理一下，留下你最近正在关注的和需要以后也想持续留意的长线。
格式：
<内容>
<memerry>喊话内容，不超过一百字，言简意赅，信息简洁明了</memerry>
<other>其它内容</other>
</内容>"""
        
        # 获取当前auditor记忆
        auditor_memory = self.state_manager.get_auditor_memory()
        
        # 替换模板变量
        prompt = template.replace("{{auditmemerry}}", auditor_memory)
        
        return prompt
    
    def _run_auditor_memory_packet(self, chapter_num: int) -> str:
        """
        运行auditor记忆整理，当记忆长度达到2000字符时调用
        
        Args:
            chapter_num: 当前章节号
            
        Returns:
            整理后的记忆内容
        """
        logger.info(f"开始整理auditor记忆 - 第{chapter_num}章，当前记忆长度: {len(self.state_manager.get_auditor_memory())} 字符")
        
        # 渲染整理记忆提示词
        packet_prompt = self._render_auditor_packet_prompt()
        
        # 构建消息列表（使用当前auditor历史记录）
        system_prompt = self._load_system_prompt()
        messages = self._get_messages_for_llm(system_prompt)
        messages.append({"role": "user", "content": packet_prompt})
        
        # 调用LLM
        try:
            response = self.llm_client.chat(messages)
        except Exception as e:
            logger.error(f"auditor记忆整理LLM调用失败: {e}")
            # 使用简化接口作为后备
            response = self.llm_client.simple_chat(
                user_message=packet_prompt,
                system_message=system_prompt
            )
        
        # 添加消息到auditor历史记录，标记为packet阶段，以便后续修剪时删除
        self.state_manager.add_to_auditor_history("user", packet_prompt, chapter_num, "packet")
        self.state_manager.add_to_auditor_history("assistant", response, chapter_num, "packet")
        
        # 解析响应（需要auditor_parser支持解析记忆响应）
        # 暂时使用简单解析
        import re
        memerry_match = re.search(r'<memerry>(.*?)</memerry>', response, re.DOTALL)
        
        if memerry_match:
            packed_memory = memerry_match.group(1).strip()
            logger.info(f"auditor记忆整理完成，整理后长度: {len(packed_memory)} 字符")
            return packed_memory
        else:
            logger.warning("auditor记忆整理解析失败，返回原始记忆")
            return self.state_manager.get_auditor_memory()
    
    def _render_audit_prompt(self, chapter_content: str, chapter_num: int) -> str:
        """渲染审计提示词"""
        try:
            template = self._load_prompt_template("audit_prompt.md")
        except FileNotFoundError:
            # 使用默认模板
            template = """# 章节质量审计

这是你对这本小说的印象：{{auditmemerry}}
请阅读这份内容：
{{chapter_content}}

审计这一章的质量，检查情节连贯性、人物塑造、文笔质量。

**重要：必须严格按照以下格式回复，只使用指定的XML标签：**

<内容>
<audit_result>通过/重写</audit_result>
<issues>发现的问题，言简意赅</issues>
<suggestions>改进建议，言简意赅</suggestions>
<confidence>0-100之间的置信度分数</confidence>
</内容>"""
        
        # 获取auditor记忆
        auditor_memory = self.state_manager.get_auditor_memory()
        
        # 替换模板变量
        prompt = template.replace("{{auditmemerry}}", auditor_memory)
        prompt = prompt.replace("{{chapter_content}}", chapter_content)
        
        return prompt
    
    def _render_rewrite_prompt(self, audit_issues: str, rewrite_round: int) -> str:
        """渲染重写提示词"""
        try:
            template = self._load_prompt_template("rewrite_prompt.md")
        except FileNotFoundError:
            # 使用默认模板
            template = """# 章节重写指导

审计发现的问题：{{audit_issues}}
这是3-2-1重写流程的第{{rewrite_round}}轮。

基于以上问题，提供具体的重写指导。

**重要：必须严格按照以下格式回复，只使用指定的XML标签：**

<内容>
<rewrite_round>{{rewrite_round}}/3</rewrite_round>
<core_problems>核心问题，言简意赅</core_problems>
<rewrite_direction>重写方向，言简意赅</rewrite_direction>
<key_changes>关键改动点，言简意赅</key_changes>
</内容>"""
        
        # 替换模板变量
        prompt = template.replace("{{audit_issues}}", audit_issues)
        prompt = prompt.replace("{{rewrite_round}}", str(rewrite_round))
        
        return prompt
    
    def _render_confirm_prompt(self, audit_issues: str, rewrite_instructions: str, rewritten_content: str) -> str:
        """渲染确认提示词"""
        try:
            template = self._load_prompt_template("confirm_prompt.md")
        except FileNotFoundError:
            # 使用默认模板
            template = """# 重写确认

原始章节的问题：{{audit_issues}}
重写指导：{{rewrite_instructions}}
重写后的章节：{{rewritten_content}}

这是3-2-1重写流程的第3轮，需要确认重写质量。

**重要：必须严格按照以下格式回复，只使用指定的XML标签：**

<内容>
<final_decision>通过/继续重写</final_decision>
<problems_solved>已解决的问题，言简意赅</problems_solved>
<new_issues>新出现的问题（如果有），言简意赅</new_issues>
<overall_quality>整体质量评价，言简意赅</overall_quality>
</内容>"""
        
        # 替换模板变量
        prompt = template.replace("{{audit_issues}}", audit_issues)
        prompt = prompt.replace("{{rewrite_instructions}}", rewrite_instructions)
        prompt = prompt.replace("{{rewritten_content}}", rewritten_content)
        
        return prompt
    
    def _get_messages_for_llm(self, system_prompt: str) -> List[Dict[str, str]]:
        """
        构建发送给LLM的消息列表
        
        Args:
            system_prompt: 系统提示词
            
        Returns:
            消息列表
        """
        # 加载auditor历史记录
        history_path = Path(self.state_manager.get_auditor_history_file())
        if not history_path.exists():
            # 没有历史记录，只返回系统提示词
            return [{"role": "system", "content": system_prompt}]
        
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            # 转换为OpenAI格式
            messages = []
            for msg in history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            logger.debug(f"构建了 {len(messages)} 条auditor消息给LLM")
            return messages
            
        except Exception as e:
            logger.error(f"加载auditor历史记录失败: {e}")
            # 返回系统提示词作为后备
            return [{"role": "system", "content": system_prompt}]
    
    def _get_latest_chapter_info(self) -> Optional[Dict[str, Any]]:
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
        
        # 检查是否应该审计
        if not self.state_manager.should_audit_chapter(chapter_num):
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
    
    def _write_rewritten_chapter(self, chapter_num: int, content: str) -> str:
        """
        写入重写后的章节文件
        
        Args:
            chapter_num: 章节号
            content: 章节内容
            
        Returns:
            文件路径
        """
        # 生成文件名：第{N}章_重写.txt
        filename = f"第{chapter_num}章_重写.txt"
        filepath = self.output_dir / filename
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"重写章节已保存: {filepath}")
        return str(filepath)
    
    def run_audit_phase(self, chapter_content: str, chapter_num: int) -> Dict[str, Any]:
        """
        执行审计阶段（使用窗口管理：第3章才执行记忆）
        
        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            
        Returns:
            审计结果
        """
        logger.info(f"开始审计阶段 - 第{chapter_num}章")
        
        # 1. 添加章节到窗口
        self.state_manager.add_to_window(chapter_num)
        logger.info(f"审计窗口章节: {self.state_manager.get_window_chapters()}")
        
        # 2. 首先运行审计阶段
        # 渲染审计提示词
        prompt = self._render_audit_prompt(chapter_content, chapter_num)
        
        # 构建消息列表
        system_prompt = self._load_system_prompt()
        messages = self._get_messages_for_llm(system_prompt)
        messages.append({"role": "user", "content": prompt})
        
        # 调用LLM
        try:
            response = self.llm_client.chat(messages)
        except Exception as e:
            logger.error(f"审计阶段LLM调用失败: {e}")
            # 使用简化接口作为后备
            response = self.llm_client.simple_chat(
                user_message=prompt,
                system_message=system_prompt
            )
        
        # 添加消息到auditor历史记录
        self.state_manager.add_to_auditor_history("user", prompt, chapter_num, "audit")
        self.state_manager.add_to_auditor_history("assistant", response, chapter_num, "audit")
        
        # 解析响应
        parsed = self.parser.parse_audit_response(response)
        
        if parsed.get("success", False):
            # 更新状态
            self.state_manager.update_state(
                audit_result=parsed["audit_result"],
                audit_issues=parsed["issues"]
            )
            
            logger.info(f"审计完成: 结果={parsed['audit_result']}, 置信度={parsed['confidence']}")
            
            # 如果需要重写，开始重写流程
            if parsed["audit_result"] == "重写":
                self.state_manager.start_rewrite(parsed["issues"])
                logger.info(f"第{chapter_num}章需要重写，开始3-2-1重写流程")
            else:
                # 审计通过，完成审计
                self.state_manager.finalize_audit(passed=True)
                logger.info(f"第{chapter_num}章审计通过")
        else:
            logger.warning("审计解析失败，默认通过")
            # 默认通过，避免阻塞流程
            self.state_manager.update_state(
                audit_result="通过",
                audit_issues="审计解析失败，默认通过"
            )
            self.state_manager.finalize_audit(passed=True)
        
        # 3. 检查是否应该运行记忆阶段（第3章才运行）
        should_run_memory = self.state_manager.should_run_memory_phase()
        logger.info(f"第{chapter_num}章是否应该运行记忆阶段: {should_run_memory}")
        
        if should_run_memory:
            # 运行auditor记忆阶段
            self._run_auditor_memory_phase(chapter_content, chapter_num)
            
            # 执行上下文剪枝（3-2-1逻辑：删除前两章，保留第三章）
            logger.info(f"第{chapter_num}章是窗口的第3章，执行上下文剪枝")
            self.state_manager.prune_auditor_history()
            
            # 清空窗口，为下一个窗口做准备
            self.state_manager.clear_window()
            logger.info("审计窗口已清空，准备下一个窗口")
        else:
            logger.info(f"第{chapter_num}章不是窗口的第3章，跳过记忆阶段和剪枝")
        
        return parsed
    
    def _save_auditor_memory_to_file(self, memerry_content: str) -> None:
        """保存审计记忆到prompts/Auditor/auditor_memerry.txt文件（覆盖写入）"""
        memerry_path = Path("prompts/Auditor/auditor_memerry.txt")
        
        try:
            memerry_path.parent.mkdir(parents=True, exist_ok=True)
            with open(memerry_path, 'w', encoding='utf-8') as f:
                f.write(memerry_content)
            
            logger.info(f"审计记忆已保存到: {memerry_path}, 长度: {len(memerry_content)} 字符")
            
        except Exception as e:
            logger.error(f"保存审计记忆失败: {e}")
    
    def _run_auditor_memory_phase(self, chapter_content: str, chapter_num: int) -> None:
        """
        运行auditor记忆阶段
        
        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
        """
        logger.info(f"开始auditor记忆阶段 - 第{chapter_num}章")
        
        # 渲染记忆提示词
        prompt = self._render_auditor_memerry_prompt(chapter_content)
        
        # 构建消息列表
        system_prompt = self._load_system_prompt()
        messages = self._get_messages_for_llm(system_prompt)
        messages.append({"role": "user", "content": prompt})
        
        # 调用LLM
        try:
            response = self.llm_client.chat(messages)
        except Exception as e:
            logger.error(f"auditor记忆阶段LLM调用失败: {e}")
            # 使用简化接口作为后备
            response = self.llm_client.simple_chat(
                user_message=prompt,
                system_message=system_prompt
            )
        
        # 添加消息到auditor历史记录，标记为memerry阶段
        self.state_manager.add_to_auditor_history("user", prompt, chapter_num, "memerry")
        self.state_manager.add_to_auditor_history("assistant", response, chapter_num, "memerry")
        
        # 解析响应
        parsed = self.parser.parse_memerry_response(response)
        
        if parsed.get("success", False):
            new_memory = parsed["memerry"]
            old_memory = self.state_manager.get_auditor_memory()
            
            # 合并记忆
            combined_memory = self.parser.combine_memerry(old_memory, new_memory)
            
            # 检查记忆长度是否达到2000字符，如果是则整理记忆
            if len(combined_memory) >= 2000:
                logger.info(f"auditor记忆达到 {len(combined_memory)} 字符，触发记忆整理")
                packed_memory = self._run_auditor_memory_packet(chapter_num)
                # 使用整理后的记忆
                self.state_manager.set_auditor_memory(packed_memory)
                # 保存整理后的记忆到文件
                self._save_auditor_memory_to_file(packed_memory)
                logger.info(f"auditor记忆整理完成，整理后长度: {len(packed_memory)} 字符")
            else:
                # 未达到2000字符，使用合并后的记忆
                self.state_manager.set_auditor_memory(combined_memory)
                # 保存记忆到文件
                self._save_auditor_memory_to_file(combined_memory)
                logger.info(f"auditor记忆阶段完成，记忆长度: {len(combined_memory)} 字符，已保存到文件")
        else:
            logger.warning("auditor记忆解析失败，保留原有记忆")
    
    def run_rewrite_phase(self, chapter_content: str, chapter_num: int) -> Dict[str, Any]:
        """
        执行重写阶段
        
        Args:
            chapter_content: 原始章节内容
            chapter_num: 章节号
            
        Returns:
            重写结果
        """
        rewrite_round = self.state_manager.state.rewrite_round
        logger.info(f"开始重写阶段 - 第{chapter_num}章，第{rewrite_round}轮")
        
        # 获取审计问题
        audit_issues = self.state_manager.state.audit_issues
        
        # 渲染提示词
        prompt = self._render_rewrite_prompt(audit_issues, rewrite_round)
        
        # 构建消息列表
        system_prompt = self._load_system_prompt()
        messages = self._get_messages_for_llm(system_prompt)
        messages.append({"role": "user", "content": prompt})
        
        # 调用LLM
        try:
            response = self.llm_client.chat(messages)
        except Exception as e:
            logger.error(f"重写阶段LLM调用失败: {e}")
            # 使用简化接口作为后备
            response = self.llm_client.simple_chat(
                user_message=prompt,
                system_message=system_prompt
            )
        
        # 添加消息到auditor历史记录
        self.state_manager.add_to_auditor_history("user", prompt, chapter_num, f"rewrite_{rewrite_round}")
        self.state_manager.add_to_auditor_history("assistant", response, chapter_num, f"rewrite_{rewrite_round}")
        
        # 解析响应
        parsed = self.parser.parse_rewrite_response(response)
        
        if parsed.get("success", False):
            # 更新状态
            rewrite_instructions = self.parser.extract_rewrite_instructions(
                {"issues": audit_issues, "suggestions": ""},
                parsed
            )
            
            self.state_manager.update_state(
                rewrite_instructions=rewrite_instructions
            )
            
            logger.info(f"重写指导生成完成 - 第{rewrite_round}轮")
            
            # 如果是第2轮，需要实际重写章节
            if rewrite_round == 2:
                # 这里可以调用写作模块进行重写
                # 暂时使用原始内容作为占位
                rewritten_content = f"【第{chapter_num}章重写版 - 基于审计指导】\n\n{chapter_content}"
                self.state_manager.complete_rewrite(rewritten_content)
                # 保存重写后的章节
                self._write_rewritten_chapter(chapter_num, rewritten_content)
            else:
                # 推进到下一轮
                self.state_manager.advance_rewrite_round()
        
        return parsed
    
    def run_confirm_phase(self, chapter_num: int) -> Dict[str, Any]:
        """
        执行确认阶段
        
        Args:
            chapter_num: 章节号
            
        Returns:
            确认结果
        """
        logger.info(f"开始确认阶段 - 第{chapter_num}章")
        
        # 获取相关数据
        audit_issues = self.state_manager.state.audit_issues
        rewrite_instructions = self.state_manager.state.rewrite_instructions
        rewritten_content = self.state_manager.state.rewritten_content
        
        # 渲染提示词
        prompt = self._render_confirm_prompt(audit_issues, rewrite_instructions, rewritten_content)
        
        # 构建消息列表
        system_prompt = self._load_system_prompt()
        messages = self._get_messages_for_llm(system_prompt)
        messages.append({"role": "user", "content": prompt})
        
        # 调用LLM
        try:
            response = self.llm_client.chat(messages)
        except Exception as e:
            logger.error(f"确认阶段LLM调用失败: {e}")
            # 使用简化接口作为后备
            response = self.llm_client.simple_chat(
                user_message=prompt,
                system_message=system_prompt
            )
        
        # 添加消息到auditor历史记录
        self.state_manager.add_to_auditor_history("user", prompt, chapter_num, "confirm")
        self.state_manager.add_to_auditor_history("assistant", response, chapter_num, "confirm")
        
        # 解析响应
        parsed = self.parser.parse_confirm_response(response)
        
        if parsed.get("success", False):
            # 更新状态
            if parsed["final_decision"] == "通过":
                self.state_manager.finalize_audit(passed=True)
                logger.info(f"第{chapter_num}章重写确认通过")
            else:
                # 需要继续重写，重置到第1轮
                self.state_manager.update_state(
                    rewrite_round=1,
                    current_stage="rewriting",
                    new_issues=parsed.get("new_issues", "")
                )
                logger.info(f"第{chapter_num}章需要继续重写")
        
        return parsed
    
    def run_step(self) -> bool:
        """
        执行auditor模块的一步操作
        
        Returns:
            bool: 是否执行了操作（有新的章节需要处理）
        """
        try:
            # 检查是否有新的章节需要处理
            chapter_info = self._get_latest_chapter_info()
            if not chapter_info:
                logger.debug("没有新的章节需要审计")
                return False
            
            chapter_num = chapter_info["chapter_num"]
            chapter_content = chapter_info["content"]
            
            logger.info(f"开始处理第{chapter_num}章 - auditor模块")
            
            # 如果是新章节，重置状态
            if self.state_manager.state.current_stage == "idle":
                self.state_manager.reset_for_new_chapter(chapter_num)
            
            current_stage = self.state_manager.state.current_stage
            
            if current_stage == "auditing":
                self.run_audit_phase(chapter_content, chapter_num)
            elif current_stage == "rewriting":
                self.run_rewrite_phase(chapter_content, chapter_num)
            elif current_stage == "confirming":
                self.run_confirm_phase(chapter_num)
            else:
                logger.error(f"未知的auditor阶段: {current_stage}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"执行auditor步骤时发生错误: {e}", exc_info=True)
            return False
    
    def _render_version_select_prompt(self, version_1: str, version_2: str, version_3: str = "") -> str:
        """渲染版本选择提示词"""
        try:
            template = self._load_prompt_template("version_select_prompt.md")
        except FileNotFoundError:
            # 使用默认模板
            template = """# 版本选择决策

你是一个专业的文学编辑，需要从多个重写版本中选择最佳版本。

## 背景信息
这是你对这本小说的印象：{{auditmemerry}}

## 版本列表
以下是同一章节的{{version_count}}个重写版本：

**版本1（最旧版本）：**
```
{{version_1}}
```

**版本2（中间版本）：**
```
{{version_2}}
```

{{version_3_section}}

## 选择标准
请基于以下标准评估每个版本：
1. **情节连贯性**：与之前章节的衔接是否自然
2. **人物塑造**：人物行为是否一致，性格是否鲜明
3. **文笔质量**：语言是否流畅，描写是否生动
4. **创新性**：是否有新的创意或突破
5. **问题解决**：是否解决了之前版本的问题

## 决策要求
你必须从以上版本中选择一个最佳版本。

**重要：必须严格按照以下格式回复，只使用指定的XML标签：**

<内容>
<selected_version>1/2/3</selected_version>
<reasoning>选择理由，不超过150字</reasoning>
<version_1_score>0-100之间的评分</version_1_score>
<version_2_score>0-100之间的评分</version_2_score>
<version_3_score>0-100之间的评分</version_3_score>
</内容>

**注意：**
- `<selected_version>`标签内只能是"1"、"2"或"3"
- 如果没有版本3，请将`<version_3_score>`设为0
- 评分应反映版本的整体质量
- 保持回复简洁，专注于关键差异"""
        
        # 获取auditor记忆
        auditor_memory = self.state_manager.get_auditor_memory()
        
        # 确定版本数量
        version_count = 2
        version_3_section = ""
        
        if version_3:
            version_count = 3
            version_3_section = f"""**版本3（最新版本）：**
```
{version_3}
```"""
        
        # 替换模板变量
        prompt = template.replace("{{auditmemerry}}", auditor_memory)
        prompt = prompt.replace("{{version_count}}", str(version_count))
        prompt = prompt.replace("{{version_1}}", version_1)
        prompt = prompt.replace("{{version_2}}", version_2)
        prompt = prompt.replace("{{version_3_section}}", version_3_section)
        
        return prompt
    
    def run_version_selection(self, chapter_num: int) -> Dict[str, Any]:
        """
        运行版本选择工作流
        
        Args:
            chapter_num: 章节号
            
        Returns:
            版本选择结果
        """
        logger.info(f"开始版本选择工作流 - 第{chapter_num}章")
        
        # 检查是否有足够版本进行选择
        if not self.state_manager.has_enough_versions():
            logger.warning(f"版本数量不足，无法进行版本选择。当前版本数: {self.state_manager.get_version_count()}")
            
            # 如果没有足够版本，使用默认选择（第3个版本或最新版本）
            default_version_num = self.state_manager.get_default_version_num()
            if default_version_num > 0:
                self.state_manager.select_version(default_version_num)
                logger.info(f"使用默认版本选择: 版本{default_version_num}")
                
                return {
                    "success": True,
                    "selected_version": default_version_num,
                    "reasoning": "版本数量不足，使用默认选择",
                    "version_1_score": 0,
                    "version_2_score": 0,
                    "version_3_score": 0,
                    "is_default": True
                }
            else:
                logger.error("没有可用版本，版本选择失败")
                return {
                    "success": False,
                    "error": "没有可用版本",
                    "selected_version": 0
                }
        
        # 获取版本列表
        versions = self.state_manager.get_versions()
        version_count = len(versions)
        
        logger.info(f"开始版本选择，共有{version_count}个版本")
        
        # 准备版本内容
        version_1 = versions[0] if version_count >= 1 else ""
        version_2 = versions[1] if version_count >= 2 else ""
        version_3 = versions[2] if version_count >= 3 else ""
        
        # 渲染版本选择提示词
        prompt = self._render_version_select_prompt(version_1, version_2, version_3)
        
        # 构建消息列表
        system_prompt = self._load_system_prompt()
        messages = self._get_messages_for_llm(system_prompt)
        messages.append({"role": "user", "content": prompt})
        
        # 调用LLM
        try:
            response = self.llm_client.chat(messages)
        except Exception as e:
            logger.error(f"版本选择LLM调用失败: {e}")
            # 使用简化接口作为后备
            response = self.llm_client.simple_chat(
                user_message=prompt,
                system_message=system_prompt
            )
        
        # 添加消息到auditor历史记录
        self.state_manager.add_to_auditor_history("user", prompt, chapter_num, "version_select")
        self.state_manager.add_to_auditor_history("assistant", response, chapter_num, "version_select")
        
        # 解析响应
        parsed = self._parse_version_select_response(response)
        
        if parsed.get("success", False):
            selected_version = parsed["selected_version"]
            
            # 验证选择的版本是否有效
            if 1 <= selected_version <= version_count:
                self.state_manager.select_version(selected_version)
                logger.info(f"版本选择完成: 选择版本{selected_version}")
                
                # 执行上下文剪枝
                self.state_manager.prune_auditor_history()
                logger.info("auditor历史记录剪枝完成")
            else:
                logger.warning(f"选择的版本号无效: {selected_version}，使用默认选择")
                default_version_num = self.state_manager.get_default_version_num()
                self.state_manager.select_version(default_version_num)
                parsed["selected_version"] = default_version_num
                parsed["is_default"] = True
        else:
            logger.warning("版本选择解析失败，使用默认选择")
            default_version_num = self.state_manager.get_default_version_num()
            self.state_manager.select_version(default_version_num)
            parsed = {
                "success": True,
                "selected_version": default_version_num,
                "reasoning": "解析失败，使用默认选择",
                "version_1_score": 0,
                "version_2_score": 0,
                "version_3_score": 0,
                "is_default": True
            }
        
        return parsed
    
    def _parse_version_select_response(self, response: str) -> Dict[str, Any]:
        """
        解析版本选择响应
        
        Args:
            response: LLM响应文本
            
        Returns:
            解析后的版本选择结果
        """
        import re
        
        try:
            # 提取selected_version
            version_match = re.search(r'<selected_version>(\d+)</selected_version>', response)
            if not version_match:
                return {"success": False, "error": "未找到selected_version标签"}
            
            selected_version = int(version_match.group(1))
            
            # 提取reasoning
            reasoning_match = re.search(r'<reasoning>(.*?)</reasoning>', response, re.DOTALL)
            reasoning = reasoning_match.group(1).strip() if reasoning_match else ""
            
            # 提取评分
            score_1_match = re.search(r'<version_1_score>(\d+)</version_1_score>', response)
            score_2_match = re.search(r'<version_2_score>(\d+)</version_2_score>', response)
            score_3_match = re.search(r'<version_3_score>(\d+)</version_3_score>', response)
            
            score_1 = int(score_1_match.group(1)) if score_1_match else 0
            score_2 = int(score_2_match.group(1)) if score_2_match else 0
            score_3 = int(score_3_match.group(1)) if score_3_match else 0
            
            return {
                "success": True,
                "selected_version": selected_version,
                "reasoning": reasoning,
                "version_1_score": score_1,
                "version_2_score": score_2,
                "version_3_score": score_3,
                "is_default": False
            }
            
        except Exception as e:
            logger.error(f"解析版本选择响应失败: {e}")
            return {"success": False, "error": f"解析失败: {str(e)}"}
    
    def add_version_to_history(self, version_content: str) -> None:
        """
        添加版本到版本历史
        
        Args:
            version_content: 版本内容
        """
        self.state_manager.add_version(version_content)
        
        # 检查版本数量是否达到上限（3个）
        version_count = self.state_manager.get_version_count()
        if version_count >= 3:
            logger.info(f"版本数量达到上限({version_count})，触发版本选择")
            
            # 获取当前章节号
            chapter_num = self.state_manager.state.last_audited_chapter
            if chapter_num > 0:
                # 运行版本选择
                self.run_version_selection(chapter_num)
            else:
                logger.warning("无法确定章节号，跳过版本选择")
    
    def get_status(self) -> Dict[str, Any]:
        """获取auditor工作流状态"""
        # 获取auditor历史记录摘要
        history_summary = self.state_manager.get_auditor_history_summary()
        
        # 获取版本信息
        version_count = self.state_manager.get_version_count()
        selected_version = self.state_manager.state.selected_version
        selected_version_content = self.state_manager.get_selected_version_content()
        
        return {
            "state": self.state_manager.get_state_summary(),
            "last_audited_chapter": self.state_manager.state.last_audited_chapter,
            "current_stage": self.state_manager.state.current_stage,
            "rewrite_round": self.state_manager.state.rewrite_round,
            "needs_rewrite": self.state_manager.state.needs_rewrite,
            "rewrite_completed": self.state_manager.state.rewrite_completed,
            "auditor_history": history_summary,
            "auditor_history_length": self.state_manager.get_auditor_history_length(),
            "version_info": {
                "version_count": version_count,
                "selected_version": selected_version,
                "selected_version_content_length": len(selected_version_content),
                "has_enough_versions": self.state_manager.has_enough_versions(),
                "max_versions": self.state_manager.state.max_versions
            }
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
    print("Auditor工作流测试")
    print("=" * 60)
    
    workflow = AuditorWorkflow()
    
    # 显示状态
    status = workflow.get_status()
    print(f"Auditor状态: {status['state']}")
    print(f"最后审计章节: {status['last_audited_chapter']}")
    print(f"当前阶段: {status['current_stage']}")
    
    # 检查是否有新章节
