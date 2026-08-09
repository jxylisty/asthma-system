"""
预测模块 Schema
"""
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any


class FeatureFieldInfo(BaseModel):
    """单个特征字段描述，供前端动态渲染表单"""
    name: str           # 字段名（英文）
    label: str          # 中文显示名
    unit: Optional[str] = None  # 单位
    default: Optional[float] = None  # 默认值/参考值


class ModelInfoData(BaseModel):
    """模型信息 + 特征列表，供前端动态生成输入表单"""
    model_config = ConfigDict(protected_namespaces=())
    model_name: str
    description: str
    feature_count: int
    features: List[FeatureFieldInfo]


class PredictRequest(BaseModel):
    """预测请求：化合物名 + 特征字典"""
    compound_name: str
    features: dict  # {特征名: 数值}


class PredictResultData(BaseModel):
    """预测结果"""
    model_config = ConfigDict(protected_namespaces=())
    compound_name: str
    model_name: str
    probability: float  # 入血概率 [0, 1]
    level: str          # 高/中/低
    features_used: List[str]  # 实际使用的特征列


# ==================== SMILES 预测 Schema ====================

class SmilesPredictRequest(BaseModel):
    """SMILES 预测请求"""
    model_config = ConfigDict(protected_namespaces=())
    smiles: str
    model_name: str = "cctcm"  # cctcm / herb
    compound_name: Optional[str] = None  # 可选的化合物名称
    adme_overrides: Optional[Dict[str, Optional[float]]] = None  # 用户校准的 ADME 实验值


class SmilesPredictResultData(BaseModel):
    """SMILES 预测结果"""
    model_config = ConfigDict(protected_namespaces=())
    smiles: str
    compound_name: Optional[str] = None
    model_name: str
    probability: float
    level: str
    mw: Optional[float] = None  # 分子量
    features_computed: Dict[str, Any] = {}  # 全 19 维特征快照
    core_features: List[Dict[str, Any]] = []  # 核心展示特征
    # 以下两个字段用于前端分类展示
    rdkit_topology_features: Dict[str, Any] = {}  # 11 个 RDKit 拓扑特征（只读）
    adme_features: Dict[str, Any] = {}  # 7 个 ADME 特征（可校准）
    adme_estimated: bool = True  # ADME 是否为算法推算（True=推算，False=用户已校准）


class BatchSmilesPredictRequest(BaseModel):
    """批量 SMILES 预测请求"""
    model_config = ConfigDict(protected_namespaces=())
    smiles_list: List[str]
    model_name: str = "cctcm"
    compound_names: Optional[List[str]] = None  # 可选的化合物名称列表


class BatchSmilesPredictResultData(BaseModel):
    """批量 SMILES 预测结果"""
    model_config = ConfigDict(protected_namespaces=())
    total: int
    success: int
    failed: int
    results: List[SmilesPredictResultData]
    errors: List[Dict[str, Any]] = []  # 失败详情
