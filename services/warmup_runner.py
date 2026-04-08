"""
预热运行器 - 负责处理"第一次接触"
在系统首次初始化时，调用 LLM 依次回答 warmup.md 中的 6 个问题
生成真实的现场问答，构成永久的 Context Anchor
"""

import logging
import time
from typing import List, Dict, Any
from pathlib import Path

from core.llm import LLMClient

logger = logging.getLogger(__name__)


class WarmupRunner:
    """预热运行器，负责执行真实的现场问答预热"""
    
    def __init__(self):
        """初始化预热运行器"""
        self.llm_client = LLMClient()
        self.warmup_file_path = Path("prompts/warmup.md")
        self.system_prompt_path = Path("prompts/system_prompt.txt")
        self.world_view_content = self._load_world_view()
        
    def _load_system_prompt(self) -> str:
        """加载系统提示词"""
        if not self.system_prompt_path.exists():
            logger.warning(f"系统提示词文件不存在: {self.system_prompt_path}")
            return "你是一位专业的小说作家。"
        
        try:
            with open(self.system_prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            logger.debug(f"系统提示词已加载，长度: {len(content)} 字符")
            return content
        except Exception as e:
            logger.error(f"加载系统提示词失败: {e}")
            return "你是一位专业的小说作家。"
    
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
    
    def _parse_warmup_questions(self) -> List[str]:
        """
        解析 warmup.md 文件，提取问题
        
        格式：使用 `---` 作为分隔符，split 出 6 个问题文本
        注意去除首尾空行
        """
        if not self.warmup_file_path.exists():
            logger.error(f"预热文件不存在: {self.warmup_file_path}")
            return []
        
        try:
            with open(self.warmup_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换世界观占位符
            if self.world_view_content:
                content = content.replace("{{world_view}}", self.world_view_content)
            else:
                content = content.replace("{{world_view}}", "")
            
            # 使用 '---' 作为分隔符
            sections = content.split('---')
            
            questions = []
            for i, section in enumerate(sections):
                # 去除首尾空白字符
                section = section.strip()
                
                # 跳过空章节
                if not section:
                    continue
                
                # 提取问题（去除可能的标题行）
                lines = section.split('\n')
                question_lines = []
                
                for line in lines:
                    line = line.strip()
                    # 跳过空行和以 '#' 开头的标题行
                    if not line or line.startswith('#'):
                        continue
                    question_lines.append(line)
                
                if question_lines:
                    question = ' '.join(question_lines)
                    questions.append(question)
            
            logger.info(f"从 {self.warmup_file_path} 解析出 {len(questions)} 个问题")
            return questions
            
        except Exception as e:
            logger.error(f"解析预热文件失败: {e}")
            return []
    
    def run_warmup(self) -> List[Dict[str, str]]:
        """
        运行预热流程
        
        Returns:
            包含 System Prompt + 12 条预热记录的完整消息列表
            格式: [{"role": "system", "content": "..."}, ...]
        """
        logger.info("开始运行预热流程...")
        
        # 1. 加载系统提示词
        system_content = self._load_system_prompt()
        system_message = {
            "role": "system",
            "content": system_content
        }
        
        # 2. 解析问题
        questions = self._parse_warmup_questions()
        if not questions:
            logger.error("没有找到预热问题，返回仅包含系统提示词的消息列表")
            return [system_message]
        
        logger.info(f"找到 {len(questions)} 个预热问题，开始依次调用 LLM...")
        
        # 3. 构建消息列表（从系统提示词开始）
        messages = [system_message]
        warmup_messages = []
        
        # 4. 依次处理每个问题
        for i, question in enumerate(questions, 1):
            try:
                # 打印进度
                question_preview = question[:50] + "..." if len(question) > 50 else question
                logger.info(f"运行预热 Q{i}/{len(questions)}: {question_preview}")
                
                # 添加当前问题到消息列表
                user_message = {"role": "user", "content": question}
                current_messages = messages + [user_message]
                
                # 调用 LLM（带上之前的对话历史，以便 LLM 知道之前的回答，保持连贯性）
                start_time = time.time()
                response = self.llm_client.chat(current_messages)
                elapsed_time = time.time() - start_time
                
                # 获取回答
                assistant_message = {"role": "assistant", "content": response}
                
                # 将问答对添加到消息列表（用于后续问题）
                messages.append(user_message)
                messages.append(assistant_message)
                
                # 同时添加到预热消息列表
                warmup_messages.append(user_message)
                warmup_messages.append(assistant_message)
                
                logger.info(f"  预热 Q{i} 完成，耗时: {elapsed_time:.2f}s，回答长度: {len(response)} 字符")
                
                # 短暂暂停，避免 API 限流
                if i < len(questions):
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"运行预热 Q{i} 失败: {e}")
                # 继续处理下一个问题，但记录错误
                continue
        
        # 5. 返回完整的消息列表
        logger.info(f"预热流程完成，生成 {len(messages)} 条消息")
        logger.debug(f"消息结构: 1 条系统消息 + {len(warmup_messages)} 条预热消息")
        
        return messages
    
    def run_warmup_and_save(self, history_path: Path) -> int:
        """
        运行预热流程并保存结果到历史记录文件
        
        Args:
            history_path: 历史记录文件路径
            
        Returns:
            base_context_length: 基准上下文的长度（消息数量）
        """
        # 运行预热
        messages = self.run_warmup()
        
        if len(messages) <= 1:  # 只有系统消息
            logger.error("预热流程失败，没有生成有效的预热对话")
            return 1
        
        # 转换为历史记录格式
        history = []
        for i, msg in enumerate(messages):
            history_msg = {
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": time.time() if i > 0 else 0,  # 系统消息时间戳为0
                "chapter": 0,
                "stage": "base",
                "is_base_context": True
            }
            history.append(history_msg)
        
        # 保存历史记录
        try:
            history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(history_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(history, f, ensure_ascii=False, indent=2)
            
            logger.info(f"预热历史记录已保存到: {history_path} ({len(history)} 条消息)")
            
            # 返回基准上下文的长度
            return len(history)
            
        except Exception as e:
            logger.error(f"保存预热历史记录失败: {e}")
            return 1  # 至少包含系统消息
    
    def get_warmup_summary(self) -> Dict[str, Any]:
        """获取预热摘要信息"""
        questions = self._parse_warmup_questions()
        system_content = self._load_system_prompt()
        
        return {
            "warmup_file_exists": self.warmup_file_path.exists(),
            "system_prompt_exists": self.system_prompt_path.exists(),
            "question_count": len(questions),
            "system_prompt_length": len(system_content),
            "questions_preview": [q[:50] + "..." if len(q) > 50 else q for q in questions[:3]]
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
    print("预热运行器测试")
    print("=" * 60)
    
    runner = WarmupRunner()
    
    # 显示摘要
    summary = runner.get_warmup_summary()
    print(f"预热文件存在: {summary['warmup_file_exists']}")
    print(f"系统提示词存在: {summary['system_prompt_exists']}")
    print(f"问题数量: {summary['question_count']}")
    print(f"系统提示词长度: {summary['system_prompt_length']} 字符")
    print(f"问题预览: {summary['questions_preview']}")
    
    if not summary['warmup_file_exists'] or not summary['system_prompt_exists']:
        print("缺少必要文件，退出测试")
        sys.exit(1)
    
    # 询问是否运行预热
    response = input("\n是否运行预热流程？这将调用 LLM API 6 次 (y/N): ").strip().lower()
    if response != 'y':
        print("跳过预热运行")
        sys.exit(0)
    
    # 运行预热
    print("\n开始运行预热流程...")
    messages = runner.run_warmup()
    
    print(f"\n预热完成，生成 {len(messages)} 条消息")
    print(f"消息结构:")
    print(f"  1. 系统消息: {len(messages[0]['content'])} 字符")
    print(f"  2. 预热对话: {len(messages)-1} 条消息")
    
    # 显示示例
    if len(messages) > 3:
        print("\n示例对话:")
        print(f"  Q: {messages[1]['content'][:100]}...")
        print(f"  A: {messages[2]['content'][:100]}...")


if __name__ == "__main__":
    main()