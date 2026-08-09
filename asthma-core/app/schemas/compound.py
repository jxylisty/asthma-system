"""
化合物模块 Schema
"""
from pydantic import BaseModel
from typing import Dict, List, Optional


class HighPotentialCompound(BaseModel):
    id: str
    name: str
    prob_cctcm: Optional[float] = None
    prob_herb: Optional[float] = None
    avg_prob: Optional[float] = None  # (prob_cctcm + prob_herb) / 2
    blood_prob: Optional[float] = None  # 同 blood_entry_probability，兼容前端字段名
    blood_entry_probability: Optional[float] = None  # V2 数据库入血概率
    mw: Optional[float] = None
    logp: Optional[float] = None


class HighPotentialData(BaseModel):
    items: List[HighPotentialCompound]
    total: int
    page: int
    page_size: int


class CompoundListItem(BaseModel):
    """全量化合物列表条目"""
    id: str
    name: str
    prob_cctcm: Optional[float] = None
    prob_herb: Optional[float] = None
    blood_prob: Optional[float] = None  # blood_entry_probability
    blood_entry_probability: Optional[float] = None
    asthma_related: Optional[bool] = None
    smile_short: Optional[str] = None
    smiles: Optional[str] = None          # 完整 SMILES（用于复制）
    target_count: Optional[int] = None
    herb_names: List[str] = []          # 来源药材列表
    mw: Optional[float] = None
    logp: Optional[float] = None
    tpsa: Optional[float] = None       # 拓扑极性表面积


class CompoundListData(BaseModel):
    """全量化合物列表（分页）"""
    items: List[CompoundListItem]
    total: int
    page: int
    page_size: int


class CompoundDetailData(BaseModel):
    """化合物详细信息"""
    id: str
    name: str
    prob_cctcm: Optional[float] = None
    prob_herb: Optional[float] = None
    blood_prob: Optional[float] = None
    blood_entry_probability: Optional[float] = None
    asthma_related: Optional[bool] = None
    herb_names: List[str] = []     # 来源药材列表
    smiles: Optional[str] = None
    smile_short: Optional[str] = None
    mw: Optional[float] = None
    logp: Optional[float] = None
    # RDKit 计算的分子属性
    hbd: Optional[int] = None              # 氢键供体数 (H-Bond Donors)
    hba: Optional[int] = None              # 氢键受体数 (H-Bond Acceptors)
    tpsa: Optional[float] = None           # 拓扑极性表面积 (TPSA)
    rotatable_bonds: Optional[int] = None  # 可旋转键数
    num_rings: Optional[int] = None        # 环数
    num_aromatic_rings: Optional[int] = None  # 芳香环数
    num_heavy_atoms: Optional[int] = None  # 重原子数
    molecular_formula: Optional[str] = None   # 分子式
    #
    radar_anti_inflammatory: Optional[float] = None
    radar_immune_regulation: Optional[float] = None
    radar_airway_repair: Optional[float] = None
    target_count: Optional[int] = None


class TargetBrief(BaseModel):
    gene: str
    target_type: Optional[str] = None
    species: Optional[str] = None
    asthma_related: Optional[bool] = None
    source_db: Optional[str] = None
    network_centrality: Optional[float] = None
    activity_type: Optional[str] = None
    activity_value: Optional[float] = None
    activity_unit: Optional[str] = None
    reference: Optional[str] = None


class EfficacyRadarResponse(BaseModel):
    """化合物疗效雷达图响应（GSEA 富集分析结果）"""
    id: str
    compound_name: str
    gene_count: int              # 参与分析的基因数
    scores: Dict[str, int] = {}  # {"抗炎效能": 82, "免疫调节": 65, "气道修复": 48}
    # 扁平字段，方便前端直接访问
    anti_inflammatory: int = 0   # 抗炎效能评分
    immune_regulation: int = 0   # 免疫调节评分
    airway_repair: int = 0       # 气道修复评分
    fallback: bool = False       # True 表示 GSEA 异常降级，分数为经验默认值
