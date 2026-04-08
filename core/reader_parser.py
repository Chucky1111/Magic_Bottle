"""
读者响应解析器
专门用于解析读者模块的响应，提取记忆和反馈内容
"""

import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ReaderParser:
    """读者响应解析器，专门解析读者模块的响应"""
    
    def __init__(self):
        """初始化读者解析器"""
        logger.info("ReaderParser已初始化")
    
    def parse_memerry_response(self, response: str) -> Dict[str, Any]:
        """
        解析记忆阶段的响应
        
        期望格式：
        <内容>
        <memerry>记忆点</memerry>
        <其他内容：备注或思考>...</其他内容：备注或思考>
        </内容>
        
        Args:
            response: 模型响应文本
            
        Returns:
            解析结果字典
        """
        result = {
            "success": False,
            "memerry": "",
            "notes": "",
            "raw_response": response
        }
        
        try:
            # 清理响应文本
            cleaned = self._clean_text(response)
            
            # 尝试提取<memerry>标签内容
            memerry_match = re.search(r'<memerry>(.*?)</memerry>', cleaned, re.DOTALL)
            if memerry_match:
                result["memerry"] = memerry_match.group(1).strip()
                result["success"] = True
            else:
                # 如果没有找到标签，尝试其他模式
                # 检查是否有"记忆点"或类似关键词
                memerry_patterns = [
                    r'记忆[：:]\s*(.*?)(?:\n\n|\n$|$)',
                    r'记忆点[：:]\s*(.*?)(?:\n\n|\n$|$)',
                    r'我的记忆[：:]\s*(.*?)(?:\n\n|\n$|$)',
                ]
                
                for pattern in memerry_patterns:
                    match = re.search(pattern, cleaned, re.DOTALL)
                    if match:
                        result["memerry"] = match.group(1).strip()
                        result["success"] = True
                        break
            
            # 尝试提取备注或思考
            notes_match = re.search(r'<其他内容：备注或思考>(.*?)</其他内容：备注或思考>', cleaned, re.DOTALL)
            if notes_match:
                result["notes"] = notes_match.group(1).strip()
            else:
                # 如果没有标签，尝试提取备注部分
                notes_sections = re.findall(r'备注[：:]\s*(.*?)(?:\n\n|\n$|$)', cleaned, re.DOTALL)
                if notes_sections:
                    result["notes"] = '\n'.join(notes_sections).strip()
            
            # 如果都没有提取到内容，使用清理后的文本作为记忆
            if not result["memerry"] and cleaned:
                # 截取前500字符作为记忆
                result["memerry"] = cleaned[:500].strip()
                result["success"] = True
                logger.warning("未找到标准格式的记忆内容，使用原始文本作为记忆")
            
            logger.debug(f"记忆解析结果: 成功={result['success']}, 记忆长度={len(result['memerry'])}")
            
        except Exception as e:
            logger.error(f"解析记忆响应失败: {e}")
            result["error"] = str(e)
        
        return result
    
    def parse_feedback_response(self, response: str) -> Dict[str, Any]:
        """
        解析反馈阶段的响应
        
        期望格式：
        <内容>
        <feedback>喊话内容1</feedback>
        <feedback>喊话内容2</feedback>
        <其他内容：备注或思考>...</其他内容：备注或思考>
        </内容>
        
        Args:
            response: 模型响应文本
            
        Returns:
            解析结果字典
        """
        result = {
            "success": False,
            "feedbacks": [],  # 反馈列表
            "notes": "",
            "raw_response": response
        }
        
        try:
            # 清理响应文本
            cleaned = self._clean_text(response)
            
            # 提取所有<feedback>标签内容
            feedback_matches = re.findall(r'<feedback>(.*?)</feedback>', cleaned, re.DOTALL)
            
            if feedback_matches:
                # 清理每个反馈内容
                feedbacks = []
                for fb in feedback_matches:
                    fb_clean = fb.strip()
                    if fb_clean:
                        feedbacks.append(fb_clean)
                
                result["feedbacks"] = feedbacks
                result["success"] = True
            else:
                # 如果没有找到标签，尝试其他模式
                # 检查是否有"喊话"或类似关键词
                feedback_patterns = [
                    r'喊话[：:]\s*(.*?)(?:\n\n|\n$|$)',
                    r'反馈[：:]\s*(.*?)(?:\n\n|\n$|$)',
                    r'建议[：:]\s*(.*?)(?:\n\n|\n$|$)',
                ]
                
                for pattern in feedback_patterns:
                    matches = re.findall(pattern, cleaned, re.DOTALL)
                    if matches:
                        feedbacks = [m.strip() for m in matches if m.strip()]
                        if feedbacks:
                            result["feedbacks"] = feedbacks
                            result["success"] = True
                            break
            
            # 尝试提取备注或思考
            notes_match = re.search(r'<其他内容：备注或思考>(.*?)</其他内容：备注或思考>', cleaned, re.DOTALL)
            if notes_match:
                result["notes"] = notes_match.group(1).strip()
            else:
                # 如果没有标签，尝试提取备注部分
                notes_sections = re.findall(r'备注[：:]\s*(.*?)(?:\n\n|\n$|$)', cleaned, re.DOTALL)
                if notes_sections:
                    result["notes"] = '\n'.join(notes_sections).strip()
            
            # 如果都没有提取到内容，尝试提取整个响应作为反馈
            if not result["feedbacks"] and cleaned:
                # 将整个响应作为一个反馈
                result["feedbacks"] = [cleaned[:300].strip()]  # 限制长度
                result["success"] = True
                logger.warning("未找到标准格式的反馈内容，使用原始文本作为反馈")
            
            logger.debug(f"反馈解析结果: 成功={result['success']}, 反馈数量={len(result['feedbacks'])}")
            
        except Exception as e:
            logger.error(f"解析反馈响应失败: {e}")
            result["error"] = str(e)
        
        return result
    
    def _clean_text(self, text: str) -> str:
        """
        清理文本，移除多余的空格和换行
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        if not text:
            return ""
        
        # 移除首尾空白
        cleaned = text.strip()
        
        # 合并多个连续换行
        cleaned = re.sub(r'\n\s*\n+', '\n\n', cleaned)
        
        # 移除多余的空格
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        
        return cleaned
    
    def extract_feedback_for_writer(self, feedbacks: List[str], chapter_num: int) -> str:
        """
        为写作模块提取格式化的反馈，包含章节定位信息
        
        Args:
            feedbacks: 反馈列表
            chapter_num: 反馈来源章节号
            
        Returns:
            格式化的反馈文本，适合写入data/feedback.txt
        """
        if not feedbacks:
            return "# 读者反馈\n# 暂无读者反馈"
        
        formatted = ["# 读者反馈"]
        
        for i, fb in enumerate(feedbacks, 1):
            # 清理反馈内容
            fb_clean = fb.strip()
            if not fb_clean:
                continue
            
            # 添加序号和章节定位信息
            formatted.append(f"\n## 反馈 {i}（来自第{chapter_num}章的读者）")
            formatted.append(fb_clean)
        
        return "\n".join(formatted)
    
    def combine_memerry(self, old_memerry: str, new_memerry: str, max_length: int = 2000) -> str:
        """
        合并新旧记忆，保持总长度不超过限制
        
        Args:
            old_memerry: 旧记忆
            new_memerry: 新记忆
            max_length: 最大长度限制
            
        Returns:
            合并后的记忆
        """
        if not new_memerry:
            return old_memerry
        
        if not old_memerry:
            # 如果新记忆太长，截断
            if len(new_memerry) > max_length:
                return new_memerry[:max_length] + "..."
            return new_memerry
        
        # 合并新旧记忆
        combined = f"{old_memerry}\n\n{new_memerry}"
        
        # 如果超过长度限制，截断旧部分
        if len(combined) > max_length:
            # 计算需要保留的新记忆长度
            new_len = len(new_memerry)
            available_len = max_length - new_len - 100  # 留出100字符给分隔符和省略号
            
            if available_len <= 0:
                # 如果新记忆已经超过限制，只保留新记忆
                if len(new_memerry) > max_length:
                    return new_memerry[:max_length] + "..."
                return new_memerry
            
            # 截断旧记忆
            truncated_old = old_memerry[:available_len] + "..."
            combined = f"{truncated_old}\n\n{new_memerry}"
        
        return combined