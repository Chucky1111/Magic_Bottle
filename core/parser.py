"""
健壮的内容解析器
使用正则表达式解析LLM返回的XML-like格式内容
避免使用xml.etree或BeautifulSoup，提高容错性
"""

import re
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ContentParser:
    """
    内容解析器，用于解析LLM返回的XML-like格式响应
    
    支持格式：
    <情绪画面>...</情绪画面>
    <解读>...</解读>
    <内容>
        <title>...</title>
        <chapter>...</chapter>
        <其他内容>...</其他内容>
    </内容>
    """
    
    # 正则表达式模式
    PATTERNS = {
        # 外层标签（使用非贪婪匹配）
        'mood_scene': re.compile(r'<情绪画面>\s*(.*?)\s*</情绪画面>', re.DOTALL),
        'analysis': re.compile(r'<解读>\s*(.*?)\s*</解读>', re.DOTALL),
        'content_block': re.compile(r'<内容>\s*(.*?)\s*</内容>', re.DOTALL),
        'content_block_en': re.compile(r'<content>\s*(.*?)\s*</content>', re.DOTALL),  # 英文标签支持
        
        # 内层标签（在content_block中匹配）
        'title': re.compile(r'<title>\s*(.*?)\s*</title>', re.DOTALL),
        'chapter': re.compile(r'<chapter>\s*(.*?)\s*</chapter>', re.DOTALL),
        'other_content': re.compile(r'<其他内容>\s*(.*?)\s*</其他内容>', re.DOTALL),
        'other_content_en': re.compile(r'<other>\s*(.*?)\s*</other>', re.DOTALL),  # 英文other标签支持
    }
    
    @staticmethod
    def _extract_with_pattern(pattern: re.Pattern, text: str, default: str = "") -> str:
        """
        使用正则表达式提取内容
        
        Args:
            pattern: 正则表达式模式
            text: 要搜索的文本
            default: 未找到时的默认值
            
        Returns:
            提取的内容或默认值
        """
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
        return default
    
    @staticmethod
    def _clean_text(text: str) -> str:
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
        text = text.strip()
        
        # 将多个连续换行合并为两个换行
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        
        # 移除行首尾的多余空格
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text
    
    @staticmethod
    def _preprocess_text(text: str) -> str:
        """
        预处理文本，去除markdown代码块标记和其他噪声
        
        Args:
            text: 原始文本
            
        Returns:
            预处理后的文本
        """
        if not text:
            return ""
        
        # 去除常见的markdown代码块标记
        # 匹配 ```xml ... ``` 或 ``` ... ```
        text = re.sub(r'^```(?:xml)?\s*\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'\n```\s*$', '', text, flags=re.MULTILINE)
        
        # 去除行内的代码块标记（如果存在）
        text = re.sub(r'```(?:xml)?', '', text)
        
        # 去除可能存在的XML声明
        text = re.sub(r'^<\?xml[^>]*>\s*', '', text, flags=re.MULTILINE)
        
        return text
    
    def parse_response(self, text: str) -> Dict[str, Optional[str]]:
        """
        解析LLM响应文本
        
        Args:
            text: LLM返回的原始文本，可能包含XML-like标签
        
        Returns:
            解析后的字典，包含以下键：
            - mood_scene: 情绪画面内容
            - analysis: 解读内容
            - title: 标题（仅文本，去除标签）
            - body: 正文（chapter内容，仅文本，去除标签）
            - clean_title: 清理后的标题文本（去除标签和多余空格）
            - clean_body: 清理后的正文文本（去除标签和多余空格）
            - raw_content: 整个<内容>块
            - other_content: 其他内容
            - success: 是否成功解析到主要内容
        """
        logger.debug(f"开始解析响应文本，长度: {len(text)} 字符")
        
        # 初始化结果字典
        result = {
            'mood_scene': '',
            'analysis': '',
            'title': '',
            'body': '',
            'clean_title': '',
            'clean_body': '',
            'raw_content': '',
            'other_content': '',
            'success': False
        }
        
        try:
            # 0. 预处理文本，去除markdown代码块标记
            preprocessed_text = self._preprocess_text(text)
            if preprocessed_text != text:
                logger.debug("已对文本进行预处理，去除markdown代码块标记")
            
            # 1. 提取外层标签
            result['mood_scene'] = self._clean_text(
                self._extract_with_pattern(self.PATTERNS['mood_scene'], preprocessed_text)
            )
            
            result['analysis'] = self._clean_text(
                self._extract_with_pattern(self.PATTERNS['analysis'], preprocessed_text)
            )
            
            # 2. 提取整个<内容>块（支持中文和英文标签）
            content_block = self._extract_with_pattern(self.PATTERNS['content_block'], preprocessed_text)
            if not content_block:
                # 尝试英文标签
                content_block = self._extract_with_pattern(self.PATTERNS['content_block_en'], preprocessed_text)
                logger.debug("使用英文标签 <content> 提取内容块")
            
            result['raw_content'] = self._clean_text(content_block)
            
            if content_block:
                # 3. 在<内容>块中提取内层标签
                raw_title = self._extract_with_pattern(self.PATTERNS['title'], content_block)
                raw_body = self._extract_with_pattern(self.PATTERNS['chapter'], content_block)
                
                # 如果正文为空，尝试备用策略：匹配未闭合的 <chapter> 标签
                if not raw_body.strip():
                    # 备用模式：匹配 <chapter> 后到下一个开始标签之前的所有内容
                    fallback_pattern = re.compile(r'<chapter>\s*(.*?)(?=\s*<(?:/chapter|other|content|\w+)|\Z)', re.DOTALL)
                    fallback_match = fallback_pattern.search(content_block)
                    if fallback_match:
                        raw_body = fallback_match.group(1).strip()
                        logger.debug("使用备用策略提取未闭合 <chapter> 标签的内容")
                    else:
                        # 如果还是空，尝试提取 <chapter> 后到 <other> 之前的内容
                        # 查找 <chapter> 的开始位置
                        chapter_start = content_block.find('<chapter>')
                        if chapter_start != -1:
                            chapter_start += len('<chapter>')
                            # 查找 <other> 的开始位置
                            other_start = content_block.find('<other>')
                            if other_start == -1:
                                other_start = content_block.find('</content>')
                            if other_start == -1:
                                other_start = len(content_block)
                            raw_body = content_block[chapter_start:other_start].strip()
                            logger.debug("使用简单截取方式提取 <chapter> 内容")
                
                # 清理标题和正文
                result['title'] = raw_title
                result['body'] = raw_body
                result['clean_title'] = self._clean_text(raw_title)
                result['clean_body'] = self._clean_text(raw_body)
                
                # 提取其他内容（支持中文和英文标签）
                other_content = self._extract_with_pattern(self.PATTERNS['other_content'], content_block)
                if not other_content:
                    other_content = self._extract_with_pattern(self.PATTERNS['other_content_en'], content_block)
                    logger.debug("使用英文标签 <other> 提取其他内容")
                
                result['other_content'] = self._clean_text(other_content)
            else:
                # 如果没有找到<内容>块，尝试直接在整个文本中搜索<title>和<chapter>
                logger.debug("未找到<内容>块，尝试直接搜索<title>和<chapter>标签")
                raw_title = self._extract_with_pattern(self.PATTERNS['title'], preprocessed_text)
                raw_body = self._extract_with_pattern(self.PATTERNS['chapter'], preprocessed_text)
                
                if raw_title or raw_body:
                    result['title'] = raw_title
                    result['body'] = raw_body
                    result['clean_title'] = self._clean_text(raw_title)
                    result['clean_body'] = self._clean_text(raw_body)
                    logger.debug("直接搜索找到标题或正文")
            
            # 4. 检查是否成功解析到主要内容
            # 如果找到了body或title，认为解析成功
            if result['body'] or result['title']:
                result['success'] = True
                logger.info(f"成功解析响应，标题: {result['clean_title'][:50] if result['clean_title'] else '无标题'}...")
            else:
                logger.warning("未找到主要内容（body或title），解析结果可能不完整")
                
                # 尝试备用解析策略：如果没有找到标准标签，尝试提取整个文本作为body
                if preprocessed_text.strip() and not result['body']:
                    logger.info("尝试备用解析策略：使用整个文本作为body")
                    result['body'] = preprocessed_text
                    result['clean_body'] = self._clean_text(preprocessed_text)
                    result['success'] = True
            
            # 5. 记录解析统计
            stats = {
                'has_mood_scene': bool(result['mood_scene']),
                'has_analysis': bool(result['analysis']),
                'has_title': bool(result['title']),
                'has_body': bool(result['body']),
                'clean_title_length': len(result['clean_title']),
                'clean_body_length': len(result['clean_body']),
                'used_english_tags': bool(content_block and not self._extract_with_pattern(self.PATTERNS['content_block'], preprocessed_text))
            }
            logger.debug(f"解析统计: {stats}")
            
        except Exception as e:
            logger.error(f"解析响应时发生错误: {type(e).__name__}: {e}")
            # 即使出错，也返回已有的结果
        
        return result
    
    def parse_nested_content(self, text: str, outer_tag: str, inner_tags: list) -> Dict[str, str]:
        """
        解析嵌套标签内容
        
        Args:
            text: 原始文本
            outer_tag: 外层标签名
            inner_tags: 内层标签名列表
            
        Returns:
            包含内层标签内容的字典
        """
        result = {}
        
        # 构建外层标签的正则表达式
        outer_pattern = re.compile(
            f'<{outer_tag}>\\s*(.*?)\\s*</{outer_tag}>',
            re.DOTALL
        )
        
        outer_match = outer_pattern.search(text)
        if not outer_match:
            return result
        
        outer_content = outer_match.group(1)
        
        # 提取内层标签
        for tag in inner_tags:
            inner_pattern = re.compile(
                f'<{tag}>\\s*(.*?)\\s*</{tag}>',
                re.DOTALL
            )
            inner_match = inner_pattern.search(outer_content)
            result[tag] = self._clean_text(inner_match.group(1)) if inner_match else ""
        
        return result
    
    @staticmethod
    def validate_parsed_result(result: Dict[str, Optional[str]]) -> Tuple[bool, str]:
        """
        验证解析结果
        
        Args:
            result: parse_response返回的结果字典
            
        Returns:
            (是否有效, 错误信息)
        """
        if not result.get('success', False):
            return False, "解析未成功"
        
        if not result.get('body', '').strip():
            return False, "正文内容为空"
        
        # 检查是否有明显的问题
        body = result.get('body', '')
        if len(body) < 10:  # 正文太短
            return False, f"正文内容过短: {len(body)} 字符"
        
        # 检查是否包含明显的错误标记
        error_keywords = ['错误', '无法', '抱歉', '对不起', 'error', 'sorry']
        for keyword in error_keywords:
            if keyword.lower() in body.lower():
                return True, f"警告: 正文可能包含错误提示 '{keyword}'"
        
        return True, "验证通过"
    
    def extract_all_tags(self, text: str) -> Dict[str, list]:
        """
        提取文本中所有标签及其内容
        
        Args:
            text: 原始文本
            
        Returns:
            字典，键为标签名，值为该标签的所有出现内容列表
        """
        # 查找所有标签
        tag_pattern = re.compile(r'<(\w+)>\s*(.*?)\s*</\1>', re.DOTALL)
        matches = tag_pattern.findall(text)
        
        result = {}
        for tag_name, tag_content in matches:
            if tag_name not in result:
                result[tag_name] = []
            result[tag_name].append(self._clean_text(tag_content))
        
        return result