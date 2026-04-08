"""
审计反馈提取器 - 从审计员历史记录中提取反馈并注入到创作流程
实现清晰、可维护的审计反馈集成
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AuditFeedback:
    """审计反馈数据类"""
    chapter_num: int
    audit_result: str  # "通过" 或 "重写"
    issues: str
    suggestions: str
    confidence: int
    timestamp: float
    stage: str = "audit"  # audit, rewrite, confirm
    
    def to_display_string(self) -> str:
        """转换为可显示的字符串格式"""
        if self.audit_result == "通过":
            if self.confidence >= 85:
                # 高置信度：只显示通过
                return f"【第{self.chapter_num}章审计通过】置信度：{self.confidence}%"
            else:
                # 中等置信度：显示关键问题摘要
                # 提取第一个问题或前50个字符
                if self.issues:
                    # 尝试提取第一个句子或前50字符
                    issues_text = self.issues.strip()
                    # 如果是中文，找句号、分号或逗号作为分隔
                    for sep in ['。', '；', '，', '.', ';', ',']:
                        if sep in issues_text:
                            first_issue = issues_text.split(sep)[0] + sep
                            break
                    else:
                        first_issue = issues_text[:50]
                    
                    # 限制长度
                    if len(first_issue) > 50:
                        first_issue = first_issue[:47] + "..."
                    
                    return f"【第{self.chapter_num}章审计通过】置信度：{self.confidence}% - 注意：{first_issue}"
                else:
                    return f"【第{self.chapter_num}章审计通过】置信度：{self.confidence}%"
        else:
            # 需要重写：显示问题和建议摘要
            issue_summary = self.issues[:50] + "..." if len(self.issues) > 50 else self.issues
            suggestion_summary = self.suggestions[:50] + "..." if len(self.suggestions) > 50 else self.suggestions
            return f"【第{self.chapter_num}章需要重写】问题：{issue_summary} 建议：{suggestion_summary} (置信度：{self.confidence}%)"


class AuditorFeedbackExtractor:
    """审计反馈提取器 - 从审计员历史记录中提取反馈"""
    
    def __init__(self, auditor_history_file: str = "data/auditor_history.json"):
        """
        初始化审计反馈提取器
        
        Args:
            auditor_history_file: 审计员历史记录文件路径
        """
        self.auditor_history_file = Path(auditor_history_file)
        self._ensure_directory_exists()
        
        logger.info(f"AuditorFeedbackExtractor初始化完成，历史文件: {self.auditor_history_file}")
    
    def _ensure_directory_exists(self) -> None:
        """确保目录存在"""
        self.auditor_history_file.parent.mkdir(parents=True, exist_ok=True)
    
    def load_auditor_history(self) -> List[Dict[str, Any]]:
        """加载审计员历史记录"""
        if not self.auditor_history_file.exists():
            logger.warning(f"审计员历史记录文件不存在: {self.auditor_history_file}")
            return []
        
        try:
            with open(self.auditor_history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            logger.debug(f"审计员历史记录已加载: {len(history)} 条消息")
            return history
        except Exception as e:
            logger.error(f"加载审计员历史记录失败: {e}")
            return []
    
    def extract_audit_feedback_from_message(self, message: Dict[str, Any]) -> Optional[AuditFeedback]:
        """
        从单条消息中提取审计反馈
        
        Args:
            message: 审计员历史记录中的消息
            
        Returns:
            AuditFeedback对象，如果无法提取则返回None
        """
        try:
            content = message.get("content", "")
            chapter_num = message.get("chapter", 0)
            stage = message.get("stage", "")
            timestamp = message.get("timestamp", 0)
            
            # 只处理审计阶段的消息
            if stage != "audit" or chapter_num == 0:
                return None
            
            # 使用正则表达式提取XML标签内容
            audit_result_match = re.search(r'<audit_result>(.*?)</audit_result>', content, re.DOTALL)
            issues_match = re.search(r'<issues>(.*?)</issues>', content, re.DOTALL)
            suggestions_match = re.search(r'<suggestions>(.*?)</suggestions>', content, re.DOTALL)
            confidence_match = re.search(r'<confidence>(\d+)</confidence>', content)
            
            if not all([audit_result_match, issues_match, suggestions_match, confidence_match]):
                logger.debug(f"第{chapter_num}章审计消息格式不完整，跳过")
                return None
            
            audit_result = audit_result_match.group(1).strip()
            issues = issues_match.group(1).strip()
            suggestions = suggestions_match.group(1).strip()
            
            try:
                confidence = int(confidence_match.group(1))
            except ValueError:
                confidence = 0
            
            return AuditFeedback(
                chapter_num=chapter_num,
                audit_result=audit_result,
                issues=issues,
                suggestions=suggestions,
                confidence=confidence,
                timestamp=timestamp,
                stage=stage
            )
            
        except Exception as e:
            logger.warning(f"提取审计反馈失败: {e}")
            return None
    
    def get_all_audit_feedback(self) -> List[AuditFeedback]:
        """获取所有章节的审计反馈"""
        history = self.load_auditor_history()
        feedback_list = []
        
        for message in history:
            feedback = self.extract_audit_feedback_from_message(message)
            if feedback:
                feedback_list.append(feedback)
        
        # 按章节号排序
        feedback_list.sort(key=lambda x: x.chapter_num)
        logger.info(f"提取到 {len(feedback_list)} 个章节的审计反馈")
        return feedback_list
    
    def get_recent_audit_feedback(self, max_chapters: int = 3) -> List[AuditFeedback]:
        """
        获取最近章节的审计反馈
        
        Args:
            max_chapters: 最多返回几个章节的反馈
            
        Returns:
            最近章节的审计反馈列表
        """
        all_feedback = self.get_all_audit_feedback()
        
        if not all_feedback:
            return []
        
        # 按章节号降序排序，取最近章节
        all_feedback.sort(key=lambda x: x.chapter_num, reverse=True)
        recent_feedback = all_feedback[:max_chapters]
        
        # 按章节号升序返回
        recent_feedback.sort(key=lambda x: x.chapter_num)
        
        logger.info(f"获取最近 {len(recent_feedback)} 个章节的审计反馈: 章节 {[f.chapter_num for f in recent_feedback]}")
        return recent_feedback
    
    def get_feedback_for_design_prompt(self, current_chapter: int, max_feedback_chapters: int = 3) -> str:
        """
        为设计阶段提示词生成审计反馈文本
        
        Args:
            current_chapter: 当前正在设计的章节号
            max_feedback_chapters: 最多包含几个章节的反馈
            
        Returns:
            格式化的审计反馈文本，如果没有反馈则返回空字符串
        """
        recent_feedback = self.get_recent_audit_feedback(max_feedback_chapters)
        
        if not recent_feedback:
            return ""
        
        # 过滤掉当前章节及之后的反馈（只保留之前的章节）
        past_feedback = [f for f in recent_feedback if f.chapter_num < current_chapter]
        
        if not past_feedback:
            return ""
        
        # 生成反馈文本
        feedback_lines = []
        for feedback in past_feedback:
            feedback_lines.append(feedback.to_display_string())
        
        feedback_text = "\n".join(feedback_lines)
        logger.info(f"为第{current_chapter}章设计阶段生成审计反馈，包含 {len(past_feedback)} 个章节的反馈")
        return feedback_text
    
    def get_critical_issues_summary(self, current_chapter: int) -> str:
        """
        获取关键问题摘要（针对需要重写的章节）
        
        Args:
            current_chapter: 当前章节号
            
        Returns:
            关键问题摘要文本
        """
        recent_feedback = self.get_recent_audit_feedback(max_chapters=5)
        
        # 只关注需要重写的章节
        rewrite_feedback = [f for f in recent_feedback 
                           if f.audit_result == "重写" and f.chapter_num < current_chapter]
        
        if not rewrite_feedback:
            return ""
        
        # 提取所有问题，去重并分类
        all_issues = []
        for feedback in rewrite_feedback:
            issues_text = feedback.issues.strip()
            if issues_text and issues_text not in all_issues:
                all_issues.append(issues_text)
        
        if not all_issues:
            return ""
        
        # 生成摘要
        if len(all_issues) == 1:
            summary = f"【审计提醒】最近章节发现需要改进的问题：{all_issues[0]}"
        else:
            issues_list = "\n".join([f"- {issue}" for issue in all_issues])
            summary = f"【审计提醒】最近章节发现以下需要改进的问题：\n{issues_list}"
        
        logger.info(f"为第{current_chapter}章生成关键问题摘要，包含 {len(all_issues)} 个问题")
        return summary
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取审计反馈统计信息"""
        all_feedback = self.get_all_audit_feedback()
        
        if not all_feedback:
            return {"total_chapters": 0, "passed": 0, "rewrite": 0, "avg_confidence": 0}
        
        total_chapters = len(all_feedback)
        passed_count = sum(1 for f in all_feedback if f.audit_result == "通过")
        rewrite_count = sum(1 for f in all_feedback if f.audit_result == "重写")
        
        if all_feedback:
            avg_confidence = sum(f.confidence for f in all_feedback) / len(all_feedback)
        else:
            avg_confidence = 0
        
        return {
            "total_chapters": total_chapters,
            "passed": passed_count,
            "rewrite": rewrite_count,
            "avg_confidence": round(avg_confidence, 1),
            "latest_chapter": max(f.chapter_num for f in all_feedback) if all_feedback else 0
        }


# 单例模式，确保全局只有一个实例
_auditor_feedback_extractor_instance = None

def get_auditor_feedback_extractor() -> AuditorFeedbackExtractor:
    """获取审计反馈提取器单例实例"""
    global _auditor_feedback_extractor_instance
    if _auditor_feedback_extractor_instance is None:
        _auditor_feedback_extractor_instance = AuditorFeedbackExtractor()
    return _auditor_feedback_extractor_instance


if __name__ == "__main__":
    """测试函数"""
    import sys
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("审计反馈提取器测试")
    print("=" * 60)
    
    extractor = AuditorFeedbackExtractor()
    
    # 测试获取所有反馈
    all_feedback = extractor.get_all_audit_feedback()
    print(f"提取到 {len(all_feedback)} 个章节的审计反馈")
    
    for feedback in all_feedback:
        print(f"  第{feedback.chapter_num}章: {feedback.audit_result} (置信度: {feedback.confidence}%)")
    
    # 测试获取最近反馈
    recent_feedback = extractor.get_recent_audit_feedback(max_chapters=3)
    print(f"\n最近 {len(recent_feedback)} 个章节的反馈:")
    for feedback in recent_feedback:
        print(f"  {feedback.to_display_string()}")
    
    # 测试设计阶段反馈
    current_chapter = 3
    design_feedback = extractor.get_feedback_for_design_prompt(current_chapter)
    print(f"\n第{current_chapter}章设计阶段反馈:")
    print(design_feedback if design_feedback else "  无审计反馈")
    
    # 测试统计信息
    stats = extractor.get_statistics()
    print(f"\n审计统计:")
    print(f"  总章节数: {stats['total_chapters']}")
    print(f"  通过: {stats['passed']}")
    print(f"  需要重写: {stats['rewrite']}")
    print(f"  平均置信度: {stats['avg_confidence']}%")
    print(f"  最新章节: {stats['latest_chapter']}")