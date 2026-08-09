"""
系统大屏模块 Schema
"""
from pydantic import BaseModel
from typing import Any, List


class StatisticsData(BaseModel):
    prescription_count: int
    herb_count: int
    compound_count: int
    target_count: int
    high_prob_compound_count: int  # prob_cctcm > 0.8


class SearchItem(BaseModel):
    id: Any
    name: str


class SearchData(BaseModel):
    prescriptions: List[SearchItem]
    herbs: List[SearchItem]
    compounds: List[SearchItem]
