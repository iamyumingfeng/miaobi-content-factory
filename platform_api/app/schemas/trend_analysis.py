"""
AIGC趋势分析 Schema (trend_analysis.py)

包含趋势分析相关的 Pydantic 模型。

Author: Claude Code
Date: 2025
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, date
from enum import Enum

from .common import BaseSchema


class TimeDimension(str, Enum):
    """时间维度"""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class CompareType(str, Enum):
    """对比类型"""
    NONE = "none"
    CHAIN = "chain"  # 环比
    YEAR = "year"    # 同比


class ContentType(str, Enum):
    """内容类型"""
    ALL = "all"
    IMAGE_TEXT = "image_text"  # 图文
    VIDEO = "video"            # 视频


class TrendDataPoint(BaseModel):
    """
    趋势数据点
    """
    date: str = Field(..., description="日期/周期标识 YYYY-MM-DD 或 YYYY-Wxx")
    generated: int = Field(..., description="生成数量")
    distributed: int = Field(..., description="分发数量")
    published: int = Field(..., description="发布数量")
    success_rate: float = Field(..., description="成功率")


class ComparisonData(BaseModel):
    """
    对比数据
    """
    current: int = Field(..., description="当前周期值")
    previous: int = Field(..., description="上期/去年同期值")
    change: int = Field(..., description="变化量")
    change_rate: float = Field(..., description="变化率（百分比）")


class GenerationTrendResponse(BaseModel):
    """
    内容生成趋势响应
    """
    data: List[TrendDataPoint] = Field(..., description="趋势数据点列表")
    total: int = Field(..., description="总生成量")
    avg_daily: float = Field(..., description="日均生成量")
    max_daily: int = Field(..., description="单日最大生成量")
    compare: Optional[ComparisonData] = Field(default=None, description="同比/环比对比")


class DistributionTrendResponse(BaseModel):
    """
    内容分发趋势响应
    """
    data: List[TrendDataPoint] = Field(..., description="趋势数据点列表")
    total_distributed: int = Field(..., description="总分发量")
    total_published: int = Field(..., description="总发布量")
    distribution_rate: float = Field(..., description="分发率")
    publish_rate: float = Field(..., description="发布率")
    distributed_compare: Optional[ComparisonData] = Field(default=None, description="分发量对比")
    published_compare: Optional[ComparisonData] = Field(default=None, description="发布量对比")


class OperatorTrendItem(BaseModel):
    """
    创作管理员趋势数据项
    """
    operator_id: int = Field(..., description="创作管理员ID")
    operator_name: str = Field(..., description="创作管理员名称")
    generated: int = Field(..., description="生成数量")
    distributed: int = Field(..., description="分发数量")
    published: int = Field(..., description="发布数量")


class OperatorTrendResponse(BaseModel):
    """
    创作管理员趋势响应
    """
    data: List[OperatorTrendItem] = Field(..., description="各创作管理员趋势数据")


class PublishTrendResponse(BaseModel):
    """
    内容发布趋势响应（合并生成和分发趋势）
    """
    data: List[TrendDataPoint] = Field(..., description="趋势数据点列表")
    total_generated: int = Field(..., description="总生成/接收数量")
    total_published: int = Field(..., description="总发布数量")
    success_rate: float = Field(..., description="成功率（百分比）")
    generated_compare: Optional[ComparisonData] = Field(default=None, description="生成量对比")
    published_compare: Optional[ComparisonData] = Field(default=None, description="发布量对比")


class TrendAnalysisFilterOptions(BaseModel):
    """
    趋势分析筛选选项
    """
    operators: List[Dict[str, Any]] = Field(..., description="创作管理员列表")
    content_types: List[Dict[str, str]] = Field(..., description="内容类型选项")
    dimensions: List[Dict[str, str]] = Field(..., description="时间维度选项")
