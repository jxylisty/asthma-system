"""
系统大屏路由
- GET /statistics  获取数据库总体统计
- GET /search      全局模糊搜索（防抖联想）
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import re

from pypinyin import lazy_pinyin, Style

from app.core.db import get_db
from app.schemas import ResponseModel, StatisticsData, SearchData, SearchItem
from app.models.tables import Prescription, Herb, Compound, Target, RelPrescriptionHerb

router = APIRouter()

def _is_pinyin_initials(text: str) -> bool:
    """检测输入是否为纯拼音首字母（全小写字母，长度≥1）"""
    return bool(re.match(r'^[a-z]{1,10}$', text))

def _get_pinyin_initials(text: str) -> str:
    """提取中文文本的拼音首字母"""
    return ''.join(lazy_pinyin(text, style=Style.FIRST_LETTER)).lower()

def _match_pinyin_initials(pattern: str, name: str) -> bool:
    """拼音首字母匹配：检查 name 的首字母序列是否以 pattern 开头或包含"""
    initials = _get_pinyin_initials(name)
    if initials.startswith(pattern):
        return True
    return False

def _do_like_match(db, model, field, pattern):
    """SQL LIKE 匹配封装"""
    return db.query(model).filter(field.like(pattern)).limit(10).all()


@router.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """获取数据库总体统计数据"""
    # 各表计数
    prescription_count = db.query(func.count(Prescription.id)).scalar()
    herb_count = db.query(func.count(Herb.id)).scalar()
    compound_count = db.query(func.count(Compound.id)).scalar()
    target_count = db.query(func.count(Target.gene)).scalar()

    # 高入血概率化合物数量（prob_cctcm > 0.8）
    high_prob_compound_count = db.query(func.count(Compound.id)).filter(
        Compound.prob_cctcm > 0.8
    ).scalar()

    data = StatisticsData(
        prescription_count=prescription_count,
        herb_count=herb_count,
        compound_count=compound_count,
        target_count=target_count,
        high_prob_compound_count=high_prob_compound_count
    )

    return ResponseModel(data=data)


@router.get("/search")
async def global_search(
    keyword: str = Query("", description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """
    全局模糊搜索：支持中文关键词 + 拼音首字母 + 药材名反查方剂
    每类最多返回 10 条
    """
    if not keyword.strip():
        return ResponseModel(data=SearchData(prescriptions=[], herbs=[], compounds=[]))

    kw = keyword.strip()
    pattern = f"%{kw}%"

    # 方剂搜索
    prescriptions = db.query(Prescription).filter(
        Prescription.name.like(pattern)
    ).limit(10).all()

    # 药材搜索
    herbs = db.query(Herb).filter(
        Herb.name.like(pattern)
    ).limit(10).all()

    # 化合物搜索
    compounds = db.query(Compound).filter(
        Compound.name.like(pattern)
    ).limit(10).all()

    # 拼音首字母匹配：如果常规搜索命中少且输入是拼音首字母，补充匹配
    if _is_pinyin_initials(kw):
        # 方剂拼音匹配（去重）
        existing_rx_ids = {p.id for p in prescriptions}
        all_rx = db.query(Prescription).all()
        for r in all_rx:
            if len(prescriptions) >= 10:
                break
            if r.id not in existing_rx_ids and _match_pinyin_initials(kw, r.name):
                prescriptions.append(r)
                existing_rx_ids.add(r.id)

        # 药材拼音匹配
        existing_herb_ids = {h.id for h in herbs}
        all_herbs = db.query(Herb).all()
        for h in all_herbs:
            if len(herbs) >= 10:
                break
            if h.id not in existing_herb_ids and _match_pinyin_initials(kw, h.name):
                herbs.append(h)
                existing_herb_ids.add(h.id)

        # 化合物拼音匹配
        existing_comp_ids = {c.id for c in compounds}
        all_compounds = db.query(Compound).all()
        for c in all_compounds:
            if len(compounds) >= 10:
                break
            if c.id not in existing_comp_ids and _match_pinyin_initials(kw, c.name):
                compounds.append(c)
                existing_comp_ids.add(c.id)

    # 药材名反查方剂：如果药材有匹配，找出含有这些药材的方剂（去重追加）
    if herbs:
        existing_rx_ids = {p.id for p in prescriptions}
        matched_herb_names = [h.name for h in herbs]
        if matched_herb_names:
            herb_ids = db.query(Herb.id).filter(Herb.name.in_(matched_herb_names)).subquery()
            rx_from_herbs = db.query(Prescription).join(
                RelPrescriptionHerb, RelPrescriptionHerb.prescription_id == Prescription.id
            ).filter(RelPrescriptionHerb.herb_name.in_(matched_herb_names)).limit(10).all()
            for r in rx_from_herbs:
                if len(prescriptions) >= 10:
                    break
                if r.id not in existing_rx_ids:
                    prescriptions.append(r)
                    existing_rx_ids.add(r.id)

    data = SearchData(
        prescriptions=[SearchItem(id=p.id, name=p.name) for p in prescriptions[:10]],
        herbs=[SearchItem(id=h.id, name=h.name) for h in herbs[:10]],
        compounds=[SearchItem(id=c.id, name=c.name) for c in compounds[:10]]
    )

    return ResponseModel(data=data)
