"""
项目数据模型
定义项目相关的数据结构
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Character(BaseModel):
    """角色模型"""
    id: str = Field(..., description="角色ID")
    name: str = Field(..., description="角色姓名")
    role: str = Field("", description="角色定位")
    personality: Dict[str, Any] = Field(default_factory=dict, description="性格特征")
    background: str = Field("", description="背景故事")
    appearance: str = Field("", description="外貌描述")
    relationships: List[Dict[str, Any]] = Field(default_factory=list, description="人际关系")


class PlotPoint(BaseModel):
    """情节节点"""
    id: str = Field(..., description="节点ID")
    title: str = Field(..., description="节点标题")
    description: str = Field("", description="节点描述")
    chapter_id: Optional[str] = Field(None, description="所属章节ID")
    order: int = Field(0, description="顺序")
    type: str = Field("event", description="类型: event, conflict, resolution, climax")


class WorldSetting(BaseModel):
    """世界观设定"""
    time_period: Optional[str] = Field(None, description="时代背景")
    location: Optional[str] = Field(None, description="主要地点")
    magic_system: Optional[str] = Field(None, description="魔法/异能体系")
    technology_level: Optional[str] = Field(None, description="科技水平")
    social_structure: Optional[str] = Field(None, description="社会结构")
    key_locations: List[Dict[str, Any]] = Field(default_factory=list, description="关键地点")


class ChapterOutline(BaseModel):
    """章节大纲"""
    chapter_id: str = Field(..., description="章节ID")
    title: str = Field("未命名章节", description="章节标题")
    summary: str = Field("", description="章节概要")
    plot_points: List[PlotPoint] = Field(default_factory=list, description="情节节点")
    characters_involved: List[str] = Field(default_factory=list, description="涉及角色")
    estimated_length: int = Field(0, description="预计字数")
    status: str = Field("planned", description="状态: planned, writing, completed")


class ProjectData(BaseModel):
    """项目数据模型"""
    # 基础信息
    id: str = Field(..., description="项目ID")
    title: str = Field("未命名项目", description="项目标题")
    description: Optional[str] = Field(None, description="项目描述")
    genre: str = Field("", description="作品类型")
    target_audience: Optional[str] = Field(None, description="目标读者")
    inspiration: Optional[str] = Field(None, description="创作灵感")
    
    # 创作设定
    writing_style: Dict[str, Any] = Field(default_factory=dict, description="写作风格")
    tone: str = Field("", description="作品基调")
    perspective: str = Field("第三人称", description="叙事视角")
    
    # 内容元素
    characters: List[Character] = Field(default_factory=list, description="角色列表")
    world_settings: WorldSetting = Field(default_factory=WorldSetting, description="世界观设定")
    plot_outline: List[PlotPoint] = Field(default_factory=list, description="情节大纲")
    chapter_outlines: List[ChapterOutline] = Field(default_factory=list, description="章节大纲")
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    status: str = Field("active", description="状态: active, archived, completed")
    version: str = Field("1.0", description="数据版本")
    
    # 统计信息
    total_chapters: int = Field(0, description="总章节数")
    completed_chapters: int = Field(0, description="已完成章节数")
    total_word_count: int = Field(0, description="总字数")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def update_statistics(self) -> None:
        """更新统计信息"""
        self.total_chapters = len(self.chapter_outlines)
        self.completed_chapters = sum(
            1 for chapter in self.chapter_outlines 
            if chapter.status == "completed"
        )
        self.total_word_count = sum(
            chapter.estimated_length for chapter in self.chapter_outlines
        )
        self.updated_at = datetime.now()