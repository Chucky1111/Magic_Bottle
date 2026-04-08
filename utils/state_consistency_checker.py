"""
状态一致性检查模块 - 检测和修复文件系统与状态记录之间的不一致

核心功能：
1. 扫描output目录，检测文件重复、缺失、不一致问题
2. 对比文件系统状态与状态记录（history.json, state.json等）
3. 生成修复报告和建议
4. 提供自动修复功能（可选）
"""

import os
import json
import logging
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import shutil

from .file_tracker import get_global_file_tracker, FileOperationType, record_file_operation

logger = logging.getLogger(__name__)


@dataclass
class FileIssue:
    """文件问题记录"""
    issue_id: str
    issue_type: str  # duplicate, missing, inconsistent, corrupted
    severity: str  # critical, warning, info
    file_path: Path
    description: str
    details: Dict[str, Any]
    suggested_fix: Optional[str] = None
    auto_fixable: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['file_path'] = str(self.file_path)
        return data


@dataclass
class ConsistencyReport:
    """一致性检查报告"""
    timestamp: float
    directory: Path
    total_files: int
    issues_found: int
    issues: List[FileIssue]
    statistics: Dict[str, Any]
    summary: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['directory'] = str(self.directory)
        data['timestamp_iso'] = datetime.fromtimestamp(self.timestamp).isoformat()
        data['issues'] = [issue.to_dict() for issue in self.issues]
        return data


class StateConsistencyChecker:
    """状态一致性检查器"""
    
    def __init__(self, output_dir: Union[str, Path] = "output"):
        """
        初始化一致性检查器
        
        Args:
            output_dir: output目录路径
        """
        self.output_dir = Path(output_dir)
        self.state_dir = Path("data")
        self.issue_counter = 0
        
        # 确保目录存在
        self.output_dir.mkdir(exist_ok=True)
        self.state_dir.mkdir(exist_ok=True)
        
        logger.info(f"状态一致性检查器初始化完成，监控目录: {self.output_dir}")
    
    def _generate_issue_id(self) -> str:
        """生成问题ID"""
        self.issue_counter += 1
        timestamp = int(datetime.now().timestamp() * 1000)
        return f"issue_{timestamp}_{self.issue_counter}"
    
    def scan_output_directory(self) -> Tuple[List[Path], Dict[str, Any]]:
        """
        扫描output目录
        
        Returns:
            (文件列表, 统计信息)
        """
        files = list(self.output_dir.glob("*.txt"))
        
        # 统计信息
        stats = {
            'total_files': len(files),
            'file_sizes': {},
            'file_hashes': {},
            'chapter_numbers': [],
            'duplicate_chapters': {},
            'file_patterns': {}
        }
        
        # 分析文件
        for file_path in files:
            # 文件大小
            try:
                size = file_path.stat().st_size
                stats['file_sizes'][str(file_path)] = size
            except Exception:
                stats['file_sizes'][str(file_path)] = 0
            
            # 文件哈希
            try:
                file_hash = self._calculate_file_hash(file_path)
                stats['file_hashes'][str(file_path)] = file_hash
            except Exception:
                stats['file_hashes'][str(file_path)] = None
            
            # 提取章节号
            chapter_num = self._extract_chapter_number(file_path.name)
            if chapter_num:
                stats['chapter_numbers'].append(chapter_num)
                
                # 记录重复章节
                if chapter_num not in stats['duplicate_chapters']:
                    stats['duplicate_chapters'][chapter_num] = []
                stats['duplicate_chapters'][chapter_num].append(str(file_path))
            
            # 文件模式分析
            pattern = self._analyze_file_pattern(file_path.name)
            if pattern not in stats['file_patterns']:
                stats['file_patterns'][pattern] = 0
            stats['file_patterns'][pattern] += 1
        
        # 找出重复章节
        duplicate_stats = {}
        for chapter_num, file_list in stats['duplicate_chapters'].items():
            if len(file_list) > 1:
                duplicate_stats[chapter_num] = {
                    'count': len(file_list),
                    'files': file_list
                }
        
        stats['duplicate_chapters'] = duplicate_stats
        stats['unique_chapters'] = len(set(stats['chapter_numbers']))
        stats['has_duplicates'] = len(duplicate_stats) > 0
        
        return files, stats
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        hash_obj = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception:
            return "error"
    
    def _extract_chapter_number(self, filename: str) -> Optional[int]:
        """从文件名提取章节号"""
        # 匹配模式：第X章
        match = re.search(r'第(\d+)章', filename)
        if match:
            return int(match.group(1))
        
        # 匹配模式：chapter_X
        match = re.search(r'chapter[_\s]*(\d+)', filename, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # 匹配模式：纯数字开头
        match = re.search(r'^(\d+)', filename)
        if match:
            return int(match.group(1))
        
        return None
    
    def _analyze_file_pattern(self, filename: str) -> str:
        """分析文件命名模式"""
        # 检查是否包含章节号
        if re.search(r'第\d+章', filename):
            return "chinese_chapter_format"
        elif re.search(r'chapter[_\s]*\d+', filename, re.IGNORECASE):
            return "english_chapter_format"
        elif re.search(r'^\d+', filename):
            return "numeric_prefix"
        else:
            return "other_format"
    
    def check_state_files(self) -> Dict[str, Any]:
        """
        检查状态文件
        
        Returns:
            状态文件信息
        """
        state_info = {
            'files_exist': {},
            'files_valid': {},
            'content_summary': {}
        }
        
        # 检查关键状态文件
        state_files = [
            'state.json',
            'history.json',
            'reader_state.json',
            'reader_history.json',
            'feedback_state.json',
            'text_processor_state.json'
        ]
        
        for filename in state_files:
            file_path = self.state_dir / filename
            exists = file_path.exists()
            state_info['files_exist'][filename] = exists
            
            if exists:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = json.load(f)
                    
                    # 分析内容
                    if filename == 'state.json':
                        state_info['content_summary'][filename] = {
                            'chapter_num': content.get('chapter_num'),
                            'stage': content.get('stage'),
                            'window_size': content.get('window_size')
                        }
                    elif filename == 'history.json':
                        state_info['content_summary'][filename] = {
                            'total_entries': len(content),
                            'last_chapter': self._get_last_chapter_from_history(content)
                        }
                    elif filename == 'text_processor_state.json':
                        state_info['content_summary'][filename] = {
                            'processed_files': len(content.get('processed_files', [])),
                            'timestamp': content.get('timestamp')
                        }
                    else:
                        state_info['content_summary'][filename] = {
                            'has_content': len(content) > 0 if isinstance(content, list) else bool(content)
                        }
                    
                    state_info['files_valid'][filename] = True
                except Exception as e:
                    state_info['files_valid'][filename] = False
                    state_info['content_summary'][filename] = {'error': str(e)}
            else:
                state_info['files_valid'][filename] = False
                state_info['content_summary'][filename] = {'error': '文件不存在'}
        
        return state_info
    
    def _get_last_chapter_from_history(self, history: List[Dict]) -> Optional[int]:
        """从history中获取最后章节号"""
        last_chapter = 0
        for entry in history:
            chapter = entry.get('chapter', 0)
            if chapter > last_chapter:
                last_chapter = chapter
        return last_chapter if last_chapter > 0 else None
    
    def detect_issues(self) -> List[FileIssue]:
        """
        检测所有问题
        
        Returns:
            问题列表
        """
        issues = []
        
        # 扫描output目录
        files, stats = self.scan_output_directory()
        
        # 1. 检测重复章节文件
        for chapter_num, dup_info in stats['duplicate_chapters'].items():
            if dup_info['count'] > 1:
                issue = FileIssue(
                    issue_id=self._generate_issue_id(),
                    issue_type='duplicate',
                    severity='critical' if chapter_num <= 100 else 'warning',
                    file_path=Path(dup_info['files'][0]),
                    description=f"第{chapter_num}章有{dup_info['count']}个重复文件",
                    details={
                        'chapter': chapter_num,
                        'duplicate_count': dup_info['count'],
                        'files': dup_info['files'],
                        'file_hashes': {f: stats['file_hashes'].get(f) for f in dup_info['files']}
                    },
                    suggested_fix=f"保留最新的文件，删除其他重复文件。建议检查文件创建时间来确定哪个是最新版本。",
                    auto_fixable=True
                )
                issues.append(issue)
        
        # 2. 检测缺失的章节（基于连续编号）
        if stats['chapter_numbers']:
            min_chapter = min(stats['chapter_numbers'])
            max_chapter = max(stats['chapter_numbers'])
            
            expected_chapters = set(range(min_chapter, max_chapter + 1))
            actual_chapters = set(stats['chapter_numbers'])
            missing_chapters = expected_chapters - actual_chapters
            
            for chapter in sorted(missing_chapters):
                issue = FileIssue(
                    issue_id=self._generate_issue_id(),
                    issue_type='missing',
                    severity='warning',
                    file_path=self.output_dir / f"第{chapter}章_缺失.txt",
                    description=f"第{chapter}章文件缺失",
                    details={
                        'chapter': chapter,
                        'expected_range': f"{min_chapter}-{max_chapter}",
                        'surrounding_chapters': [
                            c for c in [chapter-1, chapter+1] 
                            if c in actual_chapters
                        ]
                    },
                    suggested_fix=f"检查是否第{chapter}章从未生成，或者生成后被意外删除。",
                    auto_fixable=False
                )
                issues.append(issue)
        
        # 3. 检查状态文件一致性
        state_info = self.check_state_files()
        
        # 检查state.json中的章节号与文件系统是否一致
        if state_info['files_exist']['state.json'] and state_info['files_valid']['state.json']:
            state_summary = state_info['content_summary']['state.json']
            state_chapter = state_summary.get('chapter_num')
            
            if state_chapter and stats['chapter_numbers']:
                max_file_chapter = max(stats['chapter_numbers'])
                
                if state_chapter > max_file_chapter + 1:
                    issue = FileIssue(
                        issue_id=self._generate_issue_id(),
                        issue_type='inconsistent',
                        severity='warning',
                        file_path=self.state_dir / "state.json",
                        description=f"状态记录章节({state_chapter})远超文件系统章节({max_file_chapter})",
                        details={
                            'state_chapter': state_chapter,
                            'max_file_chapter': max_file_chapter,
                            'difference': state_chapter - max_file_chapter
                        },
                        suggested_fix="可能状态文件未正确更新，或者有章节文件被删除。建议检查写作流程是否正常。",
                        auto_fixable=False
                    )
                    issues.append(issue)
        
        # 4. 检查text_processor_state.json是否存在
        if not state_info['files_exist']['text_processor_state.json']:
            issue = FileIssue(
                issue_id=self._generate_issue_id(),
                issue_type='missing_state',
                severity='warning',
                file_path=self.state_dir / "text_processor_state.json",
                description="文本处理器状态文件不存在",
                details={
                    'impact': "文本处理器无法记住已处理的文件，可能导致重复处理",
                    'likely_cause': "可能是首次运行，或者状态文件被删除"
                },
                suggested_fix="运行文本处理器时会自动创建此文件。可以手动运行: python process_output.py --once",
                auto_fixable=True
            )
            issues.append(issue)
        
        # 5. 检测空文件或极小文件
        for file_path, size in stats['file_sizes'].items():
            if size < 100:  # 小于100字节
                issue = FileIssue(
                    issue_id=self._generate_issue_id(),
                    issue_type='corrupted',
                    severity='warning',
                    file_path=Path(file_path),
                    description=f"文件过小，可能内容不完整: {size}字节",
                    details={
                        'file_size': size,
                        'threshold': 100,
                        'file_hash': stats['file_hashes'].get(file_path)
                    },
                    suggested_fix="检查文件内容是否完整，可能需要重新生成此章节。",
                    auto_fixable=False
                )
                issues.append(issue)
        
        return issues
    
    def generate_report(self) -> ConsistencyReport:
        """
        生成一致性检查报告
        
        Returns:
            一致性报告
        """
        # 扫描目录
        files, stats = self.scan_output_directory()
        
        # 检测问题
        issues = self.detect_issues()
        
        # 检查状态文件
        state_info = self.check_state_files()
        
        # 生成摘要
        summary = {
            'total_files': len(files),
            'issues_found': len(issues),
            'critical_issues': sum(1 for i in issues if i.severity == 'critical'),
            'warning_issues': sum(1 for i in issues if i.severity == 'warning'),
            'info_issues': sum(1 for i in issues if i.severity == 'info'),
            'auto_fixable': sum(1 for i in issues if i.auto_fixable),
            'state_files_status': {
                'total': len(state_info['files_exist']),
                'exist': sum(1 for v in state_info['files_exist'].values() if v),
                'valid': sum(1 for v in state_info['files_valid'].values() if v)
            },
            'chapter_range': {
                'min': min(stats['chapter_numbers']) if stats['chapter_numbers'] else None,
                'max': max(stats['chapter_numbers']) if stats['chapter_numbers'] else None,
                'unique': stats['unique_chapters']
            }
        }
        
        # 创建报告
        report = ConsistencyReport(
            timestamp=datetime.now().timestamp(),
            directory=self.output_dir,
            total_files=len(files),
            issues_found=len(issues),
            issues=issues,
            statistics={
                'file_stats': stats,
                'state_info': state_info
            },
            summary=summary
        )
        
        return report
    
    def fix_issues(self, issue_ids: Optional[List[str]] = None, dry_run: bool = True) -> Dict[str, Any]:
        """
        修复检测到的问题
        
        Args:
            issue_ids: 要修复的问题ID列表，如果为None则修复所有可自动修复的问题
            dry_run: 是否为试运行（不实际执行修复）
        
        Returns:
            修复结果
        """
        report = self.generate_report()
        fix_results = {
            'dry_run': dry_run,
            'total_issues': len(report.issues),
            'fixable_issues': sum(1 for i in report.issues if i.auto_fixable),
            'attempted_fixes': 0,
            'successful_fixes': 0,
            'failed_fixes': 0,
            'details': []
        }
        
        # 筛选要修复的问题
        issues_to_fix = []
        for issue in report.issues:
            if not issue.auto_fixable:
                continue
            
            if issue_ids is None or issue.issue_id in issue_ids:
                issues_to_fix.append(issue)
        
        # 执行修复
        for issue in issues_to_fix:
            fix_result = self._fix_single_issue(issue, dry_run)
            fix_results['attempted_fixes'] += 1
            
            if fix_result['success']:
                fix_results['successful_fixes'] += 1
            else:
                fix_results['failed_fixes'] += 1
            
            fix_results['details'].append(fix_result)
        
        return fix_results
    
    def _fix_single_issue(self, issue: FileIssue, dry_run: bool) -> Dict[str, Any]:
        """修复单个问题"""
        result = {
            'issue_id': issue.issue_id,
            'issue_type': issue.issue_type,
            'file_path': str(issue.file_path),
            'dry_run': dry_run,
            'success': False,
            'action': None,
            'error': None
        }
        
        try:
            if issue.issue_type == 'duplicate':
                # 修复重复文件问题
                result.update(self._fix_duplicate_issue(issue, dry_run))
            elif issue.issue_type == 'missing_state':
                # 修复缺失状态文件问题
                result.update(self._fix_missing_state_issue(issue, dry_run))
            else:
                result['error'] = f"不支持的问题类型: {issue.issue_type}"
                return result
            
            result['success'] = True
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"修复问题失败: {issue.issue_id}, 错误: {e}")
        
        return result
    
    def _fix_duplicate_issue(self, issue: FileIssue, dry_run: bool) -> Dict[str, Any]:
        """修复重复文件问题"""
        fix_result = {
            'action': 'delete_duplicate_files',
            'files_deleted': [],
            'files_kept': [],
            'details': {}
        }
        
        # 获取重复文件列表
        duplicate_files = issue.details.get('files', [])
        if len(duplicate_files) <= 1:
            fix_result['details']['error'] = "没有足够的重复文件需要修复"
            return fix_result
        
        # 根据文件修改时间确定保留哪个文件
        file_stats = []
        for file_path_str in duplicate_files:
            file_path = Path(file_path_str)
            try:
                mtime = file_path.stat().st_mtime
                size = file_path.stat().st_size
                file_stats.append({
                    'path': file_path,
                    'mtime': mtime,
                    'size': size,
                    'str_path': file_path_str
                })
            except Exception as e:
                logger.warning(f"无法获取文件状态: {file_path_str}, 错误: {e}")
        
        if not file_stats:
            fix_result['details']['error'] = "无法获取任何文件状态"
            return fix_result
        
        # 按修改时间排序，保留最新的文件
        file_stats.sort(key=lambda x: x['mtime'], reverse=True)
        file_to_keep = file_stats[0]['path']
        
        fix_result['files_kept'] = [str(file_to_keep)]
        fix_result['details']['kept_file_info'] = {
            'mtime': file_stats[0]['mtime'],
            'size': file_stats[0]['size']
        }
        
        # 删除其他重复文件
        for file_stat in file_stats[1:]:
            file_to_delete = file_stat['path']
            
            if not dry_run:
                try:
                    # 记录文件操作
                    record_file_operation(
                        FileOperationType.DELETE,
                        str(file_to_delete),
                        metadata={
                            'reason': 'duplicate_file_fix',
                            'issue_id': issue.issue_id,
                            'kept_file': str(file_to_keep)
                        }
                    )
                    
                    # 实际删除文件
                    file_to_delete.unlink()
                    fix_result['files_deleted'].append(str(file_to_delete))
                    logger.info(f"删除重复文件: {file_to_delete}")
                except Exception as e:
                    logger.error(f"删除文件失败: {file_to_delete}, 错误: {e}")
                    fix_result['details'].setdefault('delete_errors', []).append({
                        'file': str(file_to_delete),
                        'error': str(e)
                    })
            else:
                fix_result['files_deleted'].append(str(file_to_delete))
                logger.info(f"[试运行] 将删除重复文件: {file_to_delete}")
        
        fix_result['details']['total_duplicates'] = len(duplicate_files)
        fix_result['details']['deleted_count'] = len(fix_result['files_deleted'])
        
        return fix_result
    
    def _fix_missing_state_issue(self, issue: FileIssue, dry_run: bool) -> Dict[str, Any]:
        """修复缺失状态文件问题"""
        fix_result = {
            'action': 'create_missing_state_file',
            'file_created': None,
            'details': {}
        }
        
        file_path = issue.file_path
        
        if not dry_run:
            try:
                # 创建基本的状态文件结构
                state_content = {
                    'created_at': datetime.now().isoformat(),
                    'created_by': 'state_consistency_checker',
                    'processed_files': [],
                    'timestamp': datetime.now().timestamp()
                }
                
                # 记录文件操作
                record_file_operation(
                    FileOperationType.CREATE,
                    str(file_path),
                    metadata={
                        'reason': 'missing_state_file_fix',
                        'issue_id': issue.issue_id,
                        'content_type': 'json'
                    }
                )
                
                # 写入文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(state_content, f, ensure_ascii=False, indent=2)
                
                fix_result['file_created'] = str(file_path)
                logger.info(f"创建缺失的状态文件: {file_path}")
            except Exception as e:
                logger.error(f"创建状态文件失败: {file_path}, 错误: {e}")
                fix_result['details']['error'] = str(e)
        else:
            fix_result['file_created'] = str(file_path)
            logger.info(f"[试运行] 将创建缺失的状态文件: {file_path}")
        
        return fix_result
    
    def save_report(self, report: ConsistencyReport, filename: Optional[str] = None) -> Path:
        """
        保存报告到文件
        
        Args:
            report: 一致性报告
            filename: 文件名，如果为None则自动生成
            
        Returns:
            保存的文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"consistency_report_{timestamp}.json"
        
        report_path = self.state_dir / filename
        
        try:
            report_dict = report.to_dict()
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, ensure_ascii=False, indent=2)
            
            logger.info(f"一致性报告已保存: {report_path}")
            return report_path
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
            raise
    
    def print_report_summary(self, report: ConsistencyReport) -> None:
        """
        打印报告摘要
        
        Args:
            report: 一致性报告
        """
        print(f"一致性检查报告摘要:")
        print(f"  检查时间: {datetime.fromtimestamp(report.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  目录: {report.directory}")
        print(f"  总文件数: {report.total_files}")
        print(f"  发现问题数: {report.issues_found}")
        print(f"  严重问题: {report.summary.get('critical_issues', 0)}")
        print(f"  警告问题: {report.summary.get('warning_issues', 0)}")
        print(f"  可自动修复: {report.summary.get('auto_fixable', 0)}")
        
        if report.issues_found > 0:
            print("\n问题列表:")
            for i, issue in enumerate(report.issues, 1):
                print(f"  {i}. [{issue.severity.upper()}] {issue.description}")
                if issue.suggested_fix:
                    print(f"     建议修复: {issue.suggested_fix}")


def run_full_check(output_dir: str = "output", save_report: bool = True) -> ConsistencyReport:
    """
    运行完整的一致性检查
    
    Args:
        output_dir: output目录路径
        save_report: 是否保存报告
        
    Returns:
        一致性报告
    """
    checker = StateConsistencyChecker(output_dir)
    report = checker.generate_report()
    
    if save_report:
        checker.save_report(report)
    
    return report


def fix_duplicate_files(output_dir: str = "output", dry_run: bool = True) -> Dict[str, Any]:
    """
    修复重复文件
    
    Args:
        output_dir: output目录路径
        dry_run: 是否为试运行
        
    Returns:
        修复结果
    """
    checker = StateConsistencyChecker(output_dir)
    return checker.fix_issues(dry_run=dry_run)


if __name__ == "__main__":
    # 命令行接口
    import argparse
    
    parser = argparse.ArgumentParser(description="状态一致性检查工具")
    parser.add_argument("--check", action="store_true", help="运行一致性检查")
    parser.add_argument("--fix", action="store_true", help="修复检测到的问题")
    parser.add_argument("--dry-run", action="store_true", help="试运行（不实际执行修复）")
    parser.add_argument("--output-dir", default="output", help="output目录路径")
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if args.check:
        print("运行一致性检查...")
        report = run_full_check(args.output_dir, save_report=True)
        print(f"检查完成，发现 {report.issues_found} 个问题")
        
        # 打印问题摘要
        for issue in report.issues:
            print(f"  [{issue.severity.upper()}] {issue.description}")
    
    if args.fix:
        print("修复检测到的问题...")
        results = fix_duplicate_files(args.output_dir, dry_run=args.dry_run)
        print(f"修复完成: {results['successful_fixes']}/{results['attempted_fixes']} 成功")
        
        if args.dry_run:
            print("注意：这是试运行，未实际执行修复操作")