"""
状态数据模型
定义应用程序的状态数据结构
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class WorkflowStep(BaseModel):
    """工作流步骤"""
    step_id: str = Field(..., description="步骤ID")
    step_type: str = Field(..., description="步骤类型")
    status: str = Field("pending", description="状态: pending, in_progress, completed, failed")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    result: Optional[Dict[str, Any]] = Field(None, description="步骤结果")
    error: Optional[str] = Field(None, description="错误信息")


class ChapterState(BaseModel):
    """章节状态"""
    chapter_id: str = Field(..., description="章节ID")
    title: str = Field("未命名章节", description="章节标题")
    content: str = Field("", description="章节内容")
    status: str = Field("draft", description="状态: draft, writing, completed, revised")
    word_count: int = Field(0, description="字数统计")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class ProjectState(BaseModel):
    """项目状态"""
    project_id: str = Field(..., description="项目ID")
    title: str = Field("未命名项目", description="项目标题")
    description: Optional[str] = Field(None, description="项目描述")
    genre: Optional[str] = Field(None, description="作品类型")
    target_audience: Optional[str] = Field(None, description="目标读者")
    current_chapter: Optional[str] = Field(None, description="当前章节ID")
    chapters: List[ChapterState] = Field(default_factory=list, description="章节列表")
    characters: List[Dict[str, Any]] = Field(default_factory=list, description="角色列表")
    settings: Dict[str, Any] = Field(default_factory=dict, description="项目设置")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class SystemState(BaseModel):
    """系统状态"""
    current_project: Optional[str] = Field(None, description="当前项目ID")
    current_workflow: Optional[str] = Field(None, description="当前工作流")
    workflow_steps: List[WorkflowStep] = Field(default_factory=list, description="工作流步骤")
    last_activity: datetime = Field(default_factory=datetime.now, description="最后活动时间")
    total_api_calls: int = Field(0, description="总API调用次数")
    total_tokens_used: int = Field(0, description="总使用token数")
    session_id: str = Field(..., description="会话ID")


class AppState(BaseModel):
    """应用程序状态"""
    system: SystemState = Field(..., description="系统状态")
    projects: Dict[str, ProjectState] = Field(default_factory=dict, description="项目状态字典")
    settings: Dict[str, Any] = Field(default_factory=dict, description="应用设置")
    version: str = Field("1.0.0", description="状态版本")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }