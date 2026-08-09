"""
中药材路由
- GET /                   药材列表（分页 + 多维筛选）
- GET /filter-options     获取筛选选项（药性/药味/归经/分类的可用值）
- GET /{id}               药材详情 + 所属方剂
- GET /{id}/compounds     药材包含的化合物列表（按入血概率降序）
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.core.db import get_db
from app.schemas import (
    ResponseModel,
    HerbListItem, HerbListData,
    HerbDetailData, PrescriptionMini,
    CompoundBrief, CompoundListData
)
from app.models.tables import Herb

router = APIRouter()


def _parse_multi(val: str) -> list:
    """将逗号分隔字符串解析为列表"""
    if not val or not val.strip():
        return []
    return [v.strip() for v in val.split(",") if v.strip()]


@router.get("")
async def get_herbs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: str = Query("", description="名称/拼音模糊搜索"),
    nature: str = Query("", description="药性筛选(逗号分隔: 寒,热,温,凉,平)"),
    flavor: str = Query("", description="药味筛选(逗号分隔: 辛,甘,酸,苦,咸)"),
    meridians: str = Query("", description="归经筛选(逗号分隔: 肺,脾,肾...)"),
    category: str = Query("", description="功效分类筛选(逗号分隔)"),
    asthma_related: bool = Query(None, description="是否哮喘相关"),
    min_compound_count: int = Query(0, ge=0, description="最小化合物数量"),
    db: Session = Depends(get_db)
):
    """获取药材列表（支持分页 + 多维筛选）"""
    query = db.query(Herb)

    # 名称/拼音模糊搜索
    kw = keyword.strip()
    if kw:
        query = query.filter(or_(
            Herb.name.like(f"%{kw}%"),
            Herb.pinyin.like(f"%{kw}%")
        ))

    # 药性筛选（IN）
    nature_list = _parse_multi(nature)
    if nature_list:
        query = query.filter(Herb.nature.in_(nature_list))

    # 药味筛选（每味 LIKE 匹配，因 flavor 字段可能含多味如"辛、苦"）
    flavor_list = _parse_multi(flavor)
    if flavor_list:
        query = query.filter(or_(*[Herb.flavor.like(f"%{f}%") for f in flavor_list]))

    # 归经筛选（LIKE 匹配，因 meridians 字段如"肺;肾"）
    meridian_list = _parse_multi(meridians)
    if meridian_list:
        query = query.filter(or_(*[Herb.meridians.like(f"%{m}%") for m in meridian_list]))

    # 功效分类筛选（IN）
    category_list = _parse_multi(category)
    if category_list:
        query = query.filter(Herb.category.in_(category_list))

    # 哮喘相关
    if asthma_related is not None:
        query = query.filter(Herb.asthma_related == asthma_related)

    # 最小化合物数量
    if min_compound_count > 0:
        query = query.filter(Herb.compound_count >= min_compound_count)

    total = query.count()
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    data = HerbListData(
        items=[HerbListItem(
            id=h.id, name=h.name, functions=h.functions,
            pinyin=h.pinyin, category=h.category,
            asthma_related=h.asthma_related,
            nature=h.nature, flavor=h.flavor,
            meridians=h.meridians, family=h.family,
            compound_count=h.compound_count
        ) for h in items],
        total=total,
        page=page,
        page_size=page_size
    )

    return ResponseModel(data=data)


@router.get("/filter-options")
async def get_filter_options(db: Session = Depends(get_db)):
    """获取药材筛选选项（药性/药味/归经/功效分类的可用值列表）"""
    natures = [r[0] for r in db.query(Herb.nature).filter(Herb.nature.isnot(None)).distinct().all() if r[0]]
    flavors = [r[0] for r in db.query(Herb.flavor).filter(Herb.flavor.isnot(None)).distinct().all() if r[0]]
    categories = [r[0] for r in db.query(Herb.category).filter(Herb.category.isnot(None)).distinct().all() if r[0]]

    # 归经字段可能含多个值（如"肺;肾"），需拆分去重
    raw_meridians = [r[0] for r in db.query(Herb.meridians).filter(Herb.meridians.isnot(None)).distinct().all() if r[0]]
    meridian_set = set()
    for m in raw_meridians:
        for part in m.replace("、", ";").replace("，", ";").split(";"):
            part = part.strip()
            if part:
                meridian_set.add(part)
    meridians = sorted(meridian_set)

    return ResponseModel(data={
        "natures": sorted(natures),
        "flavors": sorted(flavors),
        "meridians": meridians,
        "categories": sorted(categories)
    })


@router.get("/{herb_id}")
async def get_herb_detail(
    herb_id: str,
    db: Session = Depends(get_db)
):
    """获取单味药材详细信息 + 所属方剂列表"""
    herb = db.query(Herb).filter(Herb.id == herb_id).first()
    if not herb:
        return ResponseModel(code=404, message="药材不存在", data=None)

    # 通过 relationship 获取所属方剂
    prescriptions = herb.prescriptions

    data = HerbDetailData(
        id=herb.id,
        name=herb.name,
        functions=herb.functions,
        pinyin=herb.pinyin,
        alias=herb.alias,
        latin_name=herb.latin_name,
        category=herb.category,
        category_desc=herb.category_desc,
        nature=herb.nature,
        flavor=herb.flavor,
        meridians=herb.meridians,
        medicinal_part=herb.medicinal_part,
        family=herb.family,
        dosage=herb.dosage,
        toxicity=herb.toxicity,
        contraindication=herb.contraindication,
        asthma_related=herb.asthma_related,
        asthma_functions=herb.asthma_functions,
        source=herb.source,
        characteristics=herb.characteristics,
        identification=herb.identification,
        processing=herb.processing,
        storage=herb.storage,
        image=herb.image,
        compound_count=herb.compound_count,
        prescriptions=[PrescriptionMini(id=p.id, name=p.name) for p in prescriptions]
    )

    return ResponseModel(data=data)


@router.get("/{herb_id}/compounds")
async def get_herb_compounds(
    herb_id: str,
    db: Session = Depends(get_db)
):
    """
    获取该药材包含的化合物列表
    按入血概率降序排列（V2 使用 blood_entry_probability）
    """
    herb = db.query(Herb).filter(Herb.id == herb_id).first()
    if not herb:
        return ResponseModel(code=404, message="药材不存在", data=None)

    # 通过 relationship 获取化合物
    compounds = herb.compounds

    # 构建返回数据，按入血概率降序排列
    compound_items = []
    for c in compounds:
        blood_prob = c.blood_entry_probability
        compound_items.append({
            "id": c.id,
            "name": c.name,
            "prob_cctcm": c.prob_cctcm,
            "prob_herb": c.prob_herb,
            "blood_prob": round(blood_prob, 4) if blood_prob is not None else None,
            "blood_entry_probability": round(c.blood_entry_probability, 4) if c.blood_entry_probability is not None else None,
            "mw": c.mw,
            "logp": c.logp
        })

    # 按入血概率降序排列（None 排最后）
    compound_items.sort(key=lambda x: x["blood_prob"] if x["blood_prob"] is not None else -1, reverse=True)

    return ResponseModel(data=compound_items)
