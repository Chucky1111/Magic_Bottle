"""
Auditor响应解析器
专门用于解析审计模块的响应，提取审计结果和重写指导
"""

import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class AuditorParser:
    """Auditor响应解析器"""
    
    def __init__(self):
        """初始化解析器"""
        logger.info("AuditorParser已初始化")
    
    def parse_audit_response(self, response: str) -> Dict[str, Any]:
        """
        解析审计阶段的响应
        
        期望格式：
        <内容>
        <audit_result>通过/重写</audit_result>
        <issues>发现的问题</issues>
        <suggestions>改进建议</suggestions>
        <confidence>置信度分数</confidence>
        </内容>
        
        Args:
            response: 模型响应文本
            
        Returns:
            解析结果字典
        """
        result = {
            "success": False,
            "audit_result": "",  # "通过" 或 "重写"
            "issues": "",
            "suggestions": "",
            "confidence": 0,
            "raw_response": response
        }
        
        try:
            # 清理响应文本
            cleaned = self._clean_text(response)
            
            # 提取<audit_result>标签内容
            audit_result_match = re.search(r'<audit_result>(.*?)</audit_result>', cleaned, re.DOTALL)
            if audit_result_match:
                result["audit_result"] = audit_result_match.group(1).strip()
                result["success"] = True
            else:
                # 如果没有找到标签，尝试其他模式
                result_patterns = [
                    r'审计结果[：:]\s*(通过|重写)',
                    r'结论[：:]\s*(通过|重写)',
                    r'decision[：:]\s*(通过|重写)',
                ]
                
                for pattern in result_patterns:
                    match = re.search(pattern, cleaned, re.IGNORECASE)
                    if match:
                        result["audit_result"] = match.group(1).strip()
                        result["success"] = True
                        break
            
            # 提取<issues>标签内容
            issues_match = re.search(r'<issues>(.*?)</issues>', cleaned, re.DOTALL)
            if issues_match:
                result["issues"] = issues_match.group(1).strip()
            else:
                # 如果没有标签，尝试提取问题部分
                issues_sections = re.findall(r'问题[：:]\s*(.*?)(?:\n\n|\n$|$)', cleaned, re.DOTALL)
                if issues_sections:
                    result["issues"] = '\n'.join(issues_sections).strip()
            
            # 提取<suggestions>标签内容
            suggestions_match = re.search(r'<suggestions>(.*?)</suggestions>', cleaned, re.DOTALL)
            if suggestions_match:
                result["suggestions"] = suggestions_match.group(1).strip()
            else:
                # 如果没有标签，尝试提取建议部分
                suggestions_sections = re.findall(r'建议[：:]\s*(.*?)(?:\n\n|\n$|$)', cleaned, re.DOTALL)
                if suggestions_sections:
                    result["suggestions"] = '\n'.join(suggestions_sections).strip()
            
            # 提取<confidence>标签内容
            confidence_match = re.search(r'<confidence>(.*?)</confidence>', cleaned, re.DOTALL)
            if confidence_match:
                try:
                    result["confidence"] = int(confidence_match.group(1).strip())
                except ValueError:
                    result["confidence"] = 0
            else:
                # 尝试提取置信度分数
                confidence_patterns = [
                    r'置信度[：:]\s*(\d+)',
                    r'confidence[：:]\s*(\d+)',
                    r'分数[：:]\s*(\d+)',
                ]
                
                for pattern in confidence_patterns:
                    match = re.search(pattern, cleaned, re.IGNORECASE)
                    if match:
                        try:
                            result["confidence"] = int(match.group(1))
                        except ValueError:
                            pass
                        break
            
            # 验证审计结果
            if result["audit_result"] not in ["通过", "重写"]:
                logger.warning(f"无效的审计结果: {result['audit_result']}")
                # 尝试推断
                if "重写" in result["issues"] or "问题" in result["issues"]:
                    result["audit_result"] = "重写"
                else:
                    result["audit_result"] = "通过"
            
            logger.debug(f"审计解析结果: 成功={result['success']}, 结果={result['audit_result']}, 置信度={result['confidence']}")
            
        except Exception as e:
            logger.error(f"解析审计响应失败: {e}")
            result["error"] = str(e)
        
        return result
    
    def parse_rewrite_response(self, response: str) -> Dict[str, Any]:
        """
        解析重写阶段的响应
        
        期望格式：
        <内容>
        <rewrite_round>轮次/3</rewrite_round>
        <core_problems>核心问题</core_problems>
        <rewrite_direction>重写方向</rewrite_direction>
        <key_changes>关键改动点</key_changes>
        </内容>
        
        Args:
            response: 模型响应文本
            
        Returns:
            解析结果字典
        """
        result = {
            "success": False,
            "rewrite_round": 0,
            "core_problems": "",
            "rewrite_direction": "",
            "key_changes": "",
            "raw_response": response
        }
        
        try:
            # 清理响应文本
            cleaned = self._clean_text(response)
            
            # 提取<rewrite_round>标签内容
            round_match = re.search(r'<rewrite_round>(.*?)</rewrite_round>', cleaned, re.DOTALL)
            if round_match:
                round_text = round_match.group(1).strip()
                # 提取数字，如 "1/3" -> 1
                num_match = re.search(r'(\d+)/', round_text)
                if num_match:
                    result["rewrite_round"] = int(num_match.group(1))
                    result["success"] = True
            else:
                # 尝试提取轮次信息
                round_patterns = [
                    r'第\s*(\d+)\s*轮',
                    r'round\s*(\d+)',
                    r'轮次[：:]\s*(\d+)',
                ]
                
                for pattern in round_patterns:
                    match = re.search(pattern, cleaned, re.IGNORECASE)
                    if match:
                        result["rewrite_round"] = int(match.group(1))
                        result["success"] = True
                        break
            
            # 提取<core_problems>标签内容
            problems_match = re.search(r'<core_problems>(.*?)</core_problems>', cleaned, re.DOTALL)
            if problems_match:
                result["core_problems"] = problems_match.group(1).strip()
            else:
                # 如果没有标签，尝试提取核心问题部分
                problems_sections = re.findall(r'核心问题[：:]\s*(.*?)(?:\n\n|\n$|$)', cleaned, re.DOTALL)
                if problems_sections:
                    result["core_problems"] = '\n'.join(problems_sections).strip()
            
            # 提取<rewrite_direction>标签内容
            direction_match = re.search(r'<rewrite_direction>(.*?)</rewrite_direction>', cleaned, re.DOTALL)
            if direction_match:
                result["rewrite_direction"] = direction_match.group(1).strip()
            else:
                # 如果没有标签，尝试提取重写方向部分
                direction_sections = re.findall(r'重写方向[：:]\s*(.*?)(?:\n\n|\n$|$)', cleaned, re.DOTALL)
                if direction_sections:
                    result["rewrite_direction"] = '\n'.join(direction_sections).strip()
            
            # 提取<key_changes>标签内容
            changes_match = re.search(r'<key_changes>(.*?)</key_changes>', cleaned, re.DOTALL)
            if changes_match:
                result["key_changes"] = changes_match.group(1).strip()
            else:
                # 如果没有标签，尝试提取关键改动点部分
                changes_sections = re.findall(r'关键改动[：:]\s*(.*?)(?:\n\n|\n$|$)', cleaned, re.DOTALL)
                if changes_sections:
                    result["key_changes"] = '\n'.join(changes_sections).strip()
            
            logger.debug(f"重写解析结果: 成功={result['success']}, 轮次={result['rewrite_round']}")
            
        except Exception as e:
            logger.error(f"解析重写响应失败: {e}")
            result["error"] = str(e)
        
        return result
    
    def parse_confirm_response(self, response: str) -> Dict[str, Any]:
        """
        解析确认阶段的响应
        
        期望格式：
        <内容>
        <final_decision>通过/继续重写</final_decision>
        <problems_solved>已解决的问题</problems_solved>
        <new_issues>新出现的问题</new_issues>
        <overall_quality>整体质量评价</overall_quality>
        </内容>
        
        Args:
            response: 模型响应文本
            
        Returns:
            解析结果字典
        """
        result = {
            "success": False,
            "final_decision": "",  # "通过" 或 "继续重写"
            "problems_solved": "",
            "new_issues": "",
            "overall_quality": "",
            "raw_response": response
        }
        
        try:
            # 清理响应文本
            cleaned = self._clean_text(response)
            
            # 提取<final_decision>标签内容
            decision_match = re.search(r'<final_decision>(.*?)</final_decision>', cleaned, re.DOTALL)
            if decision_match:
                result["final_decision"] = decision_match.group(1).strip()
                result["success"] = True
            else:
                # 如果没有找到标签，尝试其他模式
                decision_patterns = [
                    r'最终决定[：:]\s*(通过|继续重写)',
                    r'结论[：:]\s*(通过|继续重写)',
                    r'decision[：:]\s*(通过|继续重写)',
                ]
                
                for pattern in decision_patterns:
                    match = re.search(pattern, cleaned, re.IGNORECASE)
                    if match:
                        result["final_decision"] = match.group(1).strip()
                        result["success"] = True
                        break
            
            # 提取<problems_solved>标签内容
            solved_match = re.search(r'<problems_solved>(.*?)</problems_solved>', cleaned, re.DOTALL)
            if solved_match:
                result["problems_solved"] = solved_match.group(1).strip()
            else:
                # 如果没有标签，尝试提取已解决问题部分
                solved_sections = re.findall(r'已解决[：:]\s*(.*?)(?:\n\n|\n$|$)', cleaned, re.DOTALL)
                if solved_sections:
                    result["problems_solved"] = '\n'.join(solved_sections).strip()
            
            # 提取<new_issues>标签内容
            new_issues_match = re.search(r'<new_issues>(.*?)</new_issues>', cleaned, re.DOTALL)
            if new_issues_match:
                result["new_issues"] = new_issues_match.group(1).strip()
            else:
                # 如果没有标签，尝试提取新问题部分
                new_issues_sections = re.findall(r'新问题[：:]\s*(.*?)(?:\n\n|\n$|$)', cleaned, re.DOTALL)
                if new_issues_sections:
                    result["new_issues"] = '\n'.join(new_issues_sections).strip()
            
            # 提取<overall_quality>标签内容
            quality_match = re.search(r'<overall_quality>(.*?)</overall_quality>', cleaned, re.DOTALL)
            if quality_match:
                result["overall_quality"] = quality_match.group(1).strip()
            else:
                # 如果没有标签，尝试提取质量评价部分
                quality_sections = re.findall(r'质量评价[：:]\s*(.*?)(?:\n\n|\n$|$)', cleaned, re.DOTALL)
                if quality_sections:
                    result["overall_quality"] = '\n'.join(quality_sections).strip()
            
            # 验证最终决定
            if result["final_decision"] not in ["通过", "继续重写"]:
                logger.warning(f"无效的最终决定: {result['final_decision']}")
                # 尝试推断
                if result["new_issues"] and "问题" in result["new_issues"]:
                    result["final_decision"] = "继续重写"
                else:
                    result["final_decision"] = "通过"
            
            logger.debug(f"确认解析结果: 成功={result['success']}, 决定={result['final_decision']}")
            
        except Exception as e:
            logger.error(f"解析确认响应失败: {e}")
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
    
    def validate_audit_result(self, result: Dict[str, Any]) -> bool:
        """
        验证审计结果
        
        Args:
            result: parse_audit_response返回的结果
            
        Returns:
            是否有效
        """
        if not result.get("success", False):
            return False
        
        if result.get("audit_result") not in ["通过", "重写"]:
            return False
        
        return True
    
    def parse_memerry_response(self, response: str) -> Dict[str, Any]:
        """
        解析记忆阶段的响应
        
        期望格式：
        <内容>
        <memerry>记忆内容</memerry>
        <other>其他备注</other>
        </内容>
        
        Args:
            response: 模型响应文本
            
        Returns:
            解析结果字典
        """
        result = {
            "success": False,
            "memerry": "",
            "other": "",
            "raw_response": response
        }
        
        try:
            # 清理响应文本
            cleaned = self._clean_text(response)
            
            # 提取<memerry>标签内容
            memerry_match = re.search(r'<memerry>(.*?)</memerry>', cleaned, re.DOTALL)
            if memerry_match:
                result["memerry"] = memerry_match.group(1).strip()
                result["success"] = True
            else:
                # 如果没有找到标签，尝试其他模式
                memerry_patterns = [
                    r'记忆[：:]\s*(.*?)(?:\n\n|\n$|$)',
                    r'memory[：:]\s*(.*?)(?:\n\n|\n$|$)',
                    r'印象[：:]\s*(.*?)(?:\n\n|\n$|$)',
                ]
                
                for pattern in memerry_patterns:
                    match = re.search(pattern, cleaned, re.DOTALL)
                    if match:
                        result["memerry"] = match.group(1).strip()
                        result["success"] = True
                        break
            
            # 提取<other>标签内容
            other_match = re.search(r'<other>(.*?)</other>', cleaned, re.DOTALL)
            if other_match:
                result["other"] = other_match.group(1).strip()
            else:
                # 如果没有标签，尝试提取其他备注部分
                other_sections = re.findall(r'备注[：:]\s*(.*?)(?:\n\n|\n$|$)', cleaned, re.DOTALL)
                if other_sections:
                    result["other"] = '\n'.join(other_sections).strip()
            
            logger.debug(f"记忆解析结果: 成功={result['success']}, 记忆长度={len(result['memerry'])} 字符")
            
        except Exception as e:
            logger.error(f"解析记忆响应失败: {e}")
            result["error"] = str(e)
        
        return result
    
    def combine_memerry(self, old_memory: str, new_memory: str) -> str:
        """
        合并记忆内容
        
        Args:
            old_memory: 旧记忆
            new_memory: 新记忆
            
        Returns:
            合并后的记忆
        """
        if not old_memory:
            return new_memory
        if not new_memory:
            return old_memory
        
        # 简单追加，用换行分隔
        return f"{old_memory}\n\n{new_memory}".strip()
    
    def extract_rewrite_instructions(self, audit_result: Dict[str, Any], rewrite_result: Dict[str, Any]) -> str:
        """
        提取重写指导
        
        Args:
            audit_result: 审计结果
            rewrite_result: 重写解析结果
            
        Returns:
            格式化的重写指导
        """
        instructions = []
        
        # 添加审计发现的问题
        if audit_result.get("issues"):
            instructions.append(f"审计发现的问题:\n{audit_result['issues']}")
        
        # 添加审计建议
        if audit_result.get("suggestions"):
            instructions.append(f"审计建议:\n{audit_result['suggestions']}")
        
        # 添加重写指导
        if rewrite_result.get("core_problems"):
            instructions.append(f"核心问题:\n{rewrite_result['core_problems']}")
        
        if rewrite_result.get("rewrite_direction"):
            instructions.append(f"重写方向:\n{rewrite_result['rewrite_direction']}")
        
        if rewrite_result.get("key_changes"):
            instructions.append(f"关键改动点:\n{rewrite_result['key_changes']}")
        
        return "\n\n".join(instructions) if instructions else "无具体重写指导"