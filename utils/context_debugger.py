"""
上下文调试模块 - 专门追踪和调试上下文管理问题

核心功能：
1. 追踪history.json中的上下文变化
2. 检测上下文错位问题（如第114章包含前6章内容）
3. 分析窗口章节管理
4. 提供上下文修复功能
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class ContextIssue:
    """上下文问题记录"""
    issue_id: str
    issue_type: str  # chapter_mismatch, window_error, content_repeat, etc.
    severity: str  # critical, warning, info
    chapter_num: int
    description: str
    details: Dict[str, Any]
    suggested_fix: Optional[str] = None
    auto_fixable: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        return data


@dataclass
class ContextAnalysis:
    """上下文分析结果"""
    timestamp: float
    history_file: Path
    total_entries: int
    issues_found: int
    issues: List[ContextIssue]
    statistics: Dict[str, Any]
    summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['history_file'] = str(self.history_file)
        data['timestamp_iso'] = datetime.fromtimestamp(self.timestamp).isoformat()
        data['issues'] = [issue.to_dict() for issue in self.issues]
        return data


class ContextDebugger:
    """上下文调试器"""
    
    def __init__(self, history_path: Union[str, Path] = "data/history.json"):
        """
        初始化上下文调试器
        
        Args:
            history_path: history.json文件路径
        """
        self.history_path = Path(history_path)
        self.issue_counter = 0
        
        logger.info(f"上下文调试器初始化完成，监控文件: {self.history_path}")
    
    def _generate_issue_id(self) -> str:
        """生成问题ID"""
        self.issue_counter += 1
        timestamp = int(datetime.now().timestamp() * 1000)
        return f"context_issue_{timestamp}_{self.issue_counter}"
    
    def load_history(self) -> List[Dict[str, Any]]:
        """加载history.json"""
        try:
            if not self.history_path.exists():
                logger.warning(f"history.json文件不存在: {self.history_path}")
                return []
            
            with open(self.history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            if not isinstance(history, list):
                logger.error(f"history.json格式错误，应为列表，实际为: {type(history)}")
                return []
            
            logger.info(f"成功加载history.json，共 {len(history)} 条记录")
            return history
            
        except Exception as e:
            logger.error(f"加载history.json失败: {e}")
            return []
    
    def analyze_chapter_consistency(self, history: List[Dict[str, Any]]) -> List[ContextIssue]:
        """分析章节一致性"""
        issues = []
        
        # 按章节分组
        chapters = {}
        for i, entry in enumerate(history):
            chapter = entry.get('chapter', 0)
            stage = entry.get('stage', 'unknown')
            is_summary = entry.get('is_summary', False)
            
            if chapter not in chapters:
                chapters[chapter] = []
            
            chapters[chapter].append({
                'index': i,
                'stage': stage,
                'is_summary': is_summary,
                'content_preview': self._get_content_preview(entry.get('content', ''))
            })
        
        # 检查每个章节的条目
        for chapter_num, entries in chapters.items():
            if chapter_num == 0:
                continue  # 跳过第0章（基础上下文）
            
            # 检查是否有summary条目
            summary_entries = [e for e in entries if e['is_summary']]
            write_entries = [e for e in entries if e['stage'] == 'write']
            design_entries = [e for e in entries if e['stage'] == 'design']
            
            # 问题1: 章节号跳跃
            expected_chapters = set(range(1, max(chapters.keys()) + 1))
            actual_chapters = set(chapters.keys())
            missing_chapters = expected_chapters - actual_chapters
            
            for missing in missing_chapters:
                if missing > 0:
                    issue = ContextIssue(
                        issue_id=self._generate_issue_id(),
                        issue_type='missing_chapter',
                        severity='warning',
                        chapter_num=missing,
                        description=f"第{missing}章在history中缺失",
                        details={
                            'expected_range': f"1-{max(chapters.keys())}",
                            'surrounding_chapters': [
                                c for c in [missing-1, missing+1] 
                                if c in actual_chapters
                            ]
                        },
                        suggested_fix=f"检查第{missing}章是否从未生成，或者生成后被意外删除",
                        auto_fixable=False
                    )
                    issues.append(issue)
            
            # 问题2: summary内容与章节不匹配
            for summary_entry in summary_entries:
                content = history[summary_entry['index']].get('content', '')
                if self._is_early_chapter_content(content, chapter_num):
                    issue = ContextIssue(
                        issue_id=self._generate_issue_id(),
                        issue_type='content_mismatch',
                        severity='critical',
                        chapter_num=chapter_num,
                        description=f"第{chapter_num}章的summary包含早期章节内容",
                        details={
                            'entry_index': summary_entry['index'],
                            'content_preview': summary_entry['content_preview'][:200],
                            'detected_early_chapters': self._detect_early_chapter_references(content)
                        },
                        suggested_fix=f"检查第{chapter_num}章的上下文管理，可能窗口章节设置错误",
                        auto_fixable=False
                    )
                    issues.append(issue)
            
            # 问题3: 检查窗口章节一致性
            for entry in entries:
                if 'window_chapters' in history[entry['index']]:
                    window = history[entry['index']]['window_chapters']
                    if window and max(window) < chapter_num - 10:
                        # 窗口章节远小于当前章节
                        issue = ContextIssue(
                            issue_id=self._generate_issue_id(),
                            issue_type='window_mismatch',
                            severity='warning',
                            chapter_num=chapter_num,
                            description=f"第{chapter_num}章的窗口章节({window})与当前章节差距过大",
                            details={
                                'entry_index': entry['index'],
                                'window_chapters': window,
                                'current_chapter': chapter_num,
                                'max_window_gap': chapter_num - max(window)
                            },
                            suggested_fix="检查上下文修剪策略，窗口可能未正确更新",
                            auto_fixable=False
                        )
                        issues.append(issue)
        
        return issues
    
    def _get_content_preview(self, content: str, max_length: int = 100) -> str:
        """获取内容预览"""
        if not content:
            return ""
        
        # 移除HTML/XML标签
        clean_content = re.sub(r'<[^>]+>', ' ', content)
        clean_content = re.sub(r'\s+', ' ', clean_content).strip()
        
        if len(clean_content) > max_length:
            return clean_content[:max_length] + "..."
        
        return clean_content
    
    def _is_early_chapter_content(self, content: str, current_chapter: int) -> bool:
        """检查内容是否包含早期章节内容"""
        # 检测早期章节的典型模式
        early_indicators = [
            r'第[1-6]章',  # 第1-6章引用
            r'酒馆遭遇',  # 早期情节
            r'学者女.*信息源',  # 早期角色描述
            r'守钟人.*地面巡逻队',  # 早期势力描述
            r'地下石阶通道',  # 早期地点
            r'单元规划.*进度审视',  # 早期规划格式
        ]
        
        for pattern in early_indicators:
            if re.search(pattern, content):
                return True
        
        # 检查是否包含前6章的典型词汇
        early_keywords = ['酒馆', '地痞混混', '守钟人', '碎片钥匙', '钟楼下', '地下通道']
        content_lower = content.lower()
        
        keyword_count = sum(1 for keyword in early_keywords if keyword in content_lower)
        
        # 如果包含多个早期关键词，且当前章节>10，则可能有问题
        if keyword_count >= 3 and current_chapter > 10:
            return True
        
        return False
    
    def _detect_early_chapter_references(self, content: str) -> List[int]:
        """检测内容中引用的早期章节"""
        chapters = set()
        
        # 查找章节引用
        chapter_matches = re.findall(r'第(\d+)章', content)
        for match in chapter_matches:
            try:
                chapter_num = int(match)
                if chapter_num < 20:  # 认为是早期章节
                    chapters.add(chapter_num)
            except ValueError:
                pass
        
        return sorted(list(chapters))
    
    def analyze_window_management(self, history: List[Dict[str, Any]]) -> List[ContextIssue]:
        """分析窗口章节管理"""
        issues = []
        
        window_entries = [i for i, entry in enumerate(history) 
                         if 'window_chapters' in entry and entry.get('is_summary', False)]
        
        for idx in window_entries:
            entry = history[idx]
            chapter = entry.get('chapter', 0)
            window = entry.get('window_chapters', [])
            
            if not window:
                continue
            
            # 检查窗口是否包含当前章节
            if chapter not in window:
                issue = ContextIssue(
                    issue_id=self._generate_issue_id(),
                    issue_type='window_exclusion',
                    severity='warning',
                    chapter_num=chapter,
                    description=f"第{chapter}章的summary窗口({window})不包含当前章节",
                    details={
                        'entry_index': idx,
                        'window_chapters': window,
                        'current_chapter': chapter
                    },
                    suggested_fix="窗口章节应包含当前章节",
                    auto_fixable=True
                )
                issues.append(issue)
            
            # 检查窗口连续性
            if len(window) > 1:
                sorted_window = sorted(window)
                expected = list(range(sorted_window[0], sorted_window[-1] + 1))
                if sorted_window != expected:
                    issue = ContextIssue(
                        issue_id=self._generate_issue_id(),
                        issue_type='window_discontinuity',
                        severity='warning',
                        chapter_num=chapter,
                        description=f"第{chapter}章的summary窗口({window})不连续",
                        details={
                            'entry_index': idx,
                            'window_chapters': window,
                            'sorted_window': sorted_window,
                            'expected_continuous': expected
                        },
                        suggested_fix="窗口章节应该是连续的",
                        auto_fixable=True
                    )
                    issues.append(issue)
            
            # 检查窗口大小
            window_size = len(window)
            if window_size < 3:
                issue = ContextIssue(
                    issue_id=self._generate_issue_id(),
                    issue_type='window_too_small',
                    severity='info',
                    chapter_num=chapter,
                    description=f"第{chapter}章的summary窗口过小({window_size}章)",
                    details={
                        'entry_index': idx,
                        'window_chapters': window,
                        'window_size': window_size
                    },
                    suggested_fix="考虑增大窗口大小以提供更多上下文",
                    auto_fixable=False
                )
                issues.append(issue)
        
        return issues
    
    def analyze_content_patterns(self, history: List[Dict[str, Any]]) -> List[ContextIssue]:
        """分析内容模式"""
        issues = []
        
        # 按章节和阶段分组内容
        content_hashes = {}
        
        for i, entry in enumerate(history):
            chapter = entry.get('chapter', 0)
            stage = entry.get('stage', 'unknown')
            content = entry.get('content', '')
            
            if not content or chapter == 0:
                continue
            
            # 计算内容哈希
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            key = f"{chapter}_{stage}"
            
            if key not in content_hashes:
                content_hashes[key] = []
            
            content_hashes[key].append({
                'index': i,
                'hash': content_hash,
                'preview': self._get_content_preview(content, 50)
            })
        
        # 检查重复内容
        hash_to_entries = {}
        for key, entries in content_hashes.items():
            for entry in entries:
                if entry['hash'] not in hash_to_entries:
                    hash_to_entries[entry['hash']] = []
                hash_to_entries[entry['hash']].append({
                    'key': key,
                    'index': entry['index'],
                    'preview': entry['preview']
                })
        
        for content_hash, entries in hash_to_entries.items():
            if len(entries) > 1:
                # 相同内容出现在多个位置
                chapters = [e['key'].split('_')[0] for e in entries]
                unique_chapters = set(chapters)
                
                if len(unique_chapters) > 1:
                    # 相同内容出现在不同章节
                    issue = ContextIssue(
                        issue_id=self._generate_issue_id(),
                        issue_type='content_duplicate',
                        severity='critical',
                        chapter_num=int(chapters[0]),
                        description=f"相同内容出现在多个章节: {', '.join(chapters)}",
                        details={
                            'content_hash': content_hash,
                            'locations': entries,
                            'preview': entries[0]['preview']
                        },
                        suggested_fix="检查内容生成逻辑，避免重复内容",
                        auto_fixable=False
                    )
                    issues.append(issue)
        
        return issues
    
    def run_analysis(self) -> ContextAnalysis:
        """运行完整分析"""
        history = self.load_history()
        
        if not history:
            logger.warning("history.json为空或加载失败，无法进行分析")
            return ContextAnalysis(
                timestamp=datetime.now().timestamp(),
                history_file=self.history_path,
                total_entries=0,
                issues_found=0,
                issues=[],
                statistics={},
                summary={'status': 'empty_history'}
            )
        
        # 运行各种分析
        chapter_issues = self.analyze_chapter_consistency(history)
        window_issues = self.analyze_window_management(history)
        content_issues = self.analyze_content_patterns(history)
        
        all_issues = chapter_issues + window_issues + content_issues
        
        # 统计信息
        total_entries = len(history)
        chapters = set(entry.get('chapter', 0) for entry in history)
        stages = set(entry.get('stage', 'unknown') for entry in history)
        
        # 按章节统计
        chapter_stats = {}
        for chapter in chapters:
            if chapter == 0:
                continue
            chapter_entries = [e for e in history if e.get('chapter', 0) == chapter]
            chapter_stats[chapter] = {
                'total_entries': len(chapter_entries),
                'stages': list(set(e.get('stage', 'unknown') for e in chapter_entries)),  # 转换为列表
                'has_summary': any(e.get('is_summary', False) for e in chapter_entries)
            }
        
        # 生成摘要
        summary = {
            'total_entries': total_entries,
            'total_chapters': len(chapters) - 1,  # 排除第0章
            'issues_found': len(all_issues),
            'critical_issues': sum(1 for i in all_issues if i.severity == 'critical'),
            'warning_issues': sum(1 for i in all_issues if i.severity == 'warning'),
            'info_issues': sum(1 for i in all_issues if i.severity == 'info'),
            'chapter_range': {
                'min': min(chapters) if chapters else 0,
                'max': max(chapters) if chapters else 0
            },
            'stage_distribution': {stage: sum(1 for e in history if e.get('stage') == stage)
                                  for stage in stages}
        }
        
        # 创建分析结果
        analysis = ContextAnalysis(
            timestamp=datetime.now().timestamp(),
            history_file=self.history_path,
            total_entries=total_entries,
            issues_found=len(all_issues),
            issues=all_issues,
            statistics={
                'chapter_stats': chapter_stats,
                'stage_distribution': summary['stage_distribution']
            },
            summary=summary
        )
        
        return analysis
    
    def save_analysis_report(self, analysis: ContextAnalysis, 
                            output_path: Optional[Union[str, Path]] = None) -> Path:
        """保存分析报告"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path("data") / f"context_analysis_{timestamp}.json"
        else:
            output_path = Path(output_path)
        
        # 确保目录存在
        output_path.parent.mkdir(exist_ok=True)
        
        # 转换为字典并保存
        analysis_dict = analysis.to_dict()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_dict, f, ensure_ascii=False, indent=2)
        
        logger.info(f"上下文分析报告已保存到: {output_path}")
        return output_path
    
    def print_analysis_summary(self, analysis: ContextAnalysis):
        """打印分析摘要"""
        print("\n" + "="*80)
        print("上下文分析报告")
        print("="*80)
        
        print(f"分析时间: {datetime.fromtimestamp(analysis.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"分析文件: {analysis.history_file}")
        print(f"总记录数: {analysis.total_entries}")
        print(f"总章节数: {analysis.summary['total_chapters']}")
        print(f"发现问题: {analysis.issues_found}")
        
        # 按严重程度统计
        critical = sum(1 for i in analysis.issues if i.severity == 'critical')
        warning = sum(1 for i in analysis.issues if i.severity == 'warning')
        info = sum(1 for i in analysis.issues if i.severity == 'info')
        
        print(f"严重问题: {critical}")
        print(f"警告问题: {warning}")
        print(f"信息问题: {info}")
        
        # 章节范围
        if analysis.summary['chapter_range']['max'] > 0:
            print(f"章节范围: {analysis.summary['chapter_range']['min']} - {analysis.summary['chapter_range']['max']}")
        
        # 阶段分布
        print("\n阶段分布:")
        for stage, count in analysis.summary['stage_distribution'].items():
            print(f"  {stage}: {count}")
        
        # 打印关键问题
        if analysis.issues:
            print("\n关键问题列表:")
            for i, issue in enumerate(analysis.issues, 1):
                if issue.severity in ['critical', 'warning']:
                    print(f"{i}. [{issue.severity.upper()}] 第{issue.chapter_num}章: {issue.description}")
                    if issue.suggested_fix:
                        print(f"   建议修复: {issue.suggested_fix}")
        
        print("="*80)
    
    def fix_window_issues(self, analysis: ContextAnalysis, dry_run: bool = True) -> Dict[str, Any]:
        """修复窗口章节问题"""
        fix_results = {
            'dry_run': dry_run,
            'total_issues': len(analysis.issues),
            'window_issues': sum(1 for i in analysis.issues if i.issue_type.startswith('window')),
            'attempted_fixes': 0,
            'successful_fixes': 0,
            'failed_fixes': 0,
            'details': []
        }
        
        # 加载history
        history = self.load_history()
        if not history:
            fix_results['error'] = "无法加载history.json"
            return fix_results
        
        modified = False
        
        for issue in analysis.issues:
            if not issue.auto_fixable:
                continue
            
            if issue.issue_type == 'window_exclusion':
                # 修复窗口不包含当前章节的问题
                entry_idx = issue.details['entry_index']
                chapter = issue.chapter_num
                window = issue.details['window_chapters']
                
                if chapter not in window:
                    new_window = sorted(window + [chapter])
                    
                    if dry_run:
                        fix_results['details'].append({
                            'issue_id': issue.issue_id,
                            'action': 'planned',
                            'description': f"计划将第{chapter}章添加到窗口{window}中",
                            'new_window': new_window
                        })
                    else:
                        try:
                            history[entry_idx]['window_chapters'] = new_window
                            modified = True
                            fix_results['details'].append({
                                'issue_id': issue.issue_id,
                                'action': 'fixed',
                                'description': f"已将第{chapter}章添加到窗口中",
                                'old_window': window,
                                'new_window': new_window
                            })
                            fix_results['successful_fixes'] += 1
                        except Exception as e:
                            fix_results['details'].append({
                                'issue_id': issue.issue_id,
                                'action': 'failed',
                                'error': str(e)
                            })
                            fix_results['failed_fixes'] += 1
                    
                    fix_results['attempted_fixes'] += 1
            
            elif issue.issue_type == 'window_discontinuity':
                # 修复窗口不连续的问题
                entry_idx = issue.details['entry_index']
                window = issue.details['window_chapters']
                expected = issue.details['expected_continuous']
                
                if dry_run:
                    fix_results['details'].append({
                        'issue_id': issue.issue_id,
                        'action': 'planned',
                        'description': f"计划修复不连续窗口{window}",
                        'new_window': expected
                    })
                else:
                    try:
                        history[entry_idx]['window_chapters'] = expected
                        modified = True
                        fix_results['details'].append({
                            'issue_id': issue.issue_id,
                            'action': 'fixed',
                            'description': f"已修复窗口连续性",
                            'old_window': window,
                            'new_window': expected
                        })
                        fix_results['successful_fixes'] += 1
                    except Exception as e:
                        fix_results['details'].append({
                            'issue_id': issue.issue_id,
                            'action': 'failed',
                            'error': str(e)
                        })
                        fix_results['failed_fixes'] += 1
                
                fix_results['attempted_fixes'] += 1
        
        # 保存修改
        if modified and not dry_run:
            try:
                backup_path = self.history_path.with_suffix('.json.backup')
                import shutil
                shutil.copy2(self.history_path, backup_path)
                logger.info(f"已创建备份: {backup_path}")
                
                with open(self.history_path, 'w', encoding='utf-8') as f:
                    json.dump(history, f, ensure_ascii=False, indent=2)
                
                fix_results['saved'] = True
                fix_results['backup_path'] = str(backup_path)
                logger.info(f"已保存修改后的history.json")
            except Exception as e:
                fix_results['error'] = f"保存修改失败: {e}"
                fix_results['saved'] = False
        
        return fix_results


# 便捷函数
def analyze_context(history_path: str = "data/history.json") -> ContextAnalysis:
    """便捷函数：分析上下文"""
    debugger = ContextDebugger(history_path)
    return debugger.run_analysis()


def save_context_analysis(analysis: ContextAnalysis, output_path: Optional[str] = None) -> str:
    """便捷函数：保存上下文分析"""
    debugger = ContextDebugger()
    saved_path = debugger.save_analysis_report(analysis, output_path)
    return str(saved_path)


def print_context_summary(analysis: ContextAnalysis):
    """便捷函数：打印上下文摘要"""
    debugger = ContextDebugger()
    debugger.print_analysis_summary(analysis)


def fix_context_issues(history_path: str = "data/history.json", dry_run: bool = True) -> Dict[str, Any]:
    """便捷函数：修复上下文问题"""
    debugger = ContextDebugger(history_path)
    analysis = debugger.run_analysis()
    return debugger.fix_window_issues(analysis, dry_run)


# 主函数：测试上下文调试器
def main():
    """测试上下文调试器"""
    print("测试上下文调试模块...")
    
    # 创建调试器
    debugger = ContextDebugger()
    
    # 运行分析
    print("\n1. 运行上下文分析...")
    analysis = debugger.run_analysis()
    debugger.print_analysis_summary(analysis)
    
    # 保存分析报告
    saved_path = debugger.save_analysis_report(analysis)
    print(f"\n分析报告已保存到: {saved_path}")
    
    # 试运行修复
    print("\n2. 试运行修复窗口问题（不实际执行）...")
    fix_results = debugger.fix_window_issues(analysis, dry_run=True)
    
    if fix_results['window_issues'] > 0:
        print(f"发现 {fix_results['window_issues']} 个窗口问题")
        for detail in fix_results.get('details', []):
            print(f"  计划修复: {detail.get('description', '未知')}")
    else:
        print("未发现可自动修复的窗口问题")
    
    print("\n测试完成！")


if __name__ == "__main__":
    main()
