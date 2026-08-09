"""
药材模块 Schema
"""
from pydantic import BaseModel
from typing import List, Optional


class HerbListItem(BaseModel):
    """药材列表条目"""
    id: str
    name: str
    functions: Optional[str] = None
    pinyin: Optional[str] = None
    category: Optional[str] = None
    asthma_related: Optional[bool] = None
    nature: Optional[str] = None
    flavor: Optional[str] = None
    meridians: Optional[str] = None
    family: Optional[str] = None
    compound_count: Optional[int] = None


class HerbListData(BaseModel):
    """药材列表（分页）"""
    items: List[HerbListItem]
    total: int
    page: int
    page_size: int


class PrescriptionMini(BaseModel):
    id: int
    name: str


class HerbDetailData(BaseModel):
    id: str
    name: str
    functions: Optional[str] = None
    pinyin: Optional[str] = None
    alias: Optional[str] = None
    latin_name: Optional[str] = None
    category: Optional[str] = None
    category_desc: Optional[str] = None
    nature: Optional[str] = None
    flavor: Optional[str] = None
    meridians: Optional[str] = None
    medicinal_part: Optional[str] = None
    family: Optional[str] = None
    dosage: Optional[str] = None
    toxicity: Optional[str] = None
    contraindication: Optional[str] = None
    asthma_related: Optional[bool] = None
    asthma_functions: Optional[str] = None
    source: Optional[str] = None
    characteristics: Optional[str] = None
    identification: Optional[str] = None
    processing: Optional[str] = None
    storage: Optional[str] = None
    image: Optional[str] = None
    compound_count: Optional[int] = None
    prescriptions: List[PrescriptionMini] = []


class CompoundBrief(BaseModel):
    id: str
    name: str
    prob_cctcm: Optional[float] = None
    prob_herb: Optional[float] = None
    blood_prob: Optional[float] = None  # blood_entry_probability
    blood_entry_probability: Optional[float] = None
    mw: Optional[float] = None
    logp: Optional[float] = None


class CompoundListData(BaseModel):
    items: List[CompoundBrief]
    total: int
    page: int
    page_size: int
