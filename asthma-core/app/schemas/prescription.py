"""
方剂模块 Schema
"""
from pydantic import BaseModel
from typing import List, Optional


class PrescriptionBrief(BaseModel):
    id: int
    name: str
    core_effect: Optional[str] = None
    indication_type: Optional[str] = None
    herb_count: Optional[int] = None
    herb_names: List[str] = []               # 药材名称列表（预览用）
    herb_dosages: List[str] = []             # 药材剂量列表（预览用）
    blood_compound_count: int = 0            # 入血成分数
    asthma_target_count: int = 0             # 哮喘靶点数


class PrescriptionListData(BaseModel):
    items: List[PrescriptionBrief]
    total: int
    page: int
    page_size: int


class HerbBrief(BaseModel):
    id: str
    name: str
    functions: Optional[str] = None
    dosage: Optional[str] = None


class PrescriptionStats(BaseModel):
    """方剂统计摘要（供雷达图区域展示）"""
    blood_compound_count: int = 0   # 入血化合物总数
    asthma_target_count: int = 0    # 哮喘相关靶点数
    pathway_count: int = 0          # 富集通路数


class PrescriptionDetailData(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    core_effect: Optional[str] = None
    indication_type: Optional[str] = None
    herbs: List[HerbBrief] = []
    stats: Optional[PrescriptionStats] = None


# Cytoscape 网络拓扑
class CytoNode(BaseModel):
    id: str
    label: str
    category: str
    prob: Optional[float] = None  # 化合物节点才有
    asthma_related: Optional[bool] = None  # 靶点节点才有


class CytoEdge(BaseModel):
    source: str
    target: str
    category: str  # p2h / h2c / c2t
    activity: Optional[float] = None  # c2t 边才有


class NetworkData(BaseModel):
    nodes: List[CytoNode]
    edges: List[CytoEdge]


# 雷达图
class RadarItem(BaseModel):
    efficacy_type: str
    count: int


# 方剂入血化合物列表
class PrescriptionCompoundItem(BaseModel):
    """方剂下的入血化合物条目"""
    id: str
    name: str
    prob_cctcm: Optional[float] = None
    prob_herb: Optional[float] = None
    blood_prob: Optional[float] = None  # blood_entry_probability
    blood_entry_probability: Optional[float] = None
    herb_name: Optional[str] = None     # 来源药材名称


class PrescriptionCompoundsData(BaseModel):
    """方剂入血化合物列表"""
    items: List[PrescriptionCompoundItem]
    total: int
