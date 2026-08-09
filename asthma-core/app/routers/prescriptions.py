"""
方剂分析路由
- GET /                   方剂列表（分页）
- GET /{id}               方剂详情 + 药材列表
- GET /{id}/network       Cytoscape.js 拓扑图数据
- GET /{id}/radar         疗效雷达图数据（GSEA 富集分析）
- GET /{id}/compounds     方剂入血化合物列表
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import re

from app.core.db import get_db
from app.schemas import (
    ResponseModel,
    PrescriptionBrief, PrescriptionListData,
    PrescriptionDetailData, HerbBrief, PrescriptionStats,
    CytoNode, CytoEdge, NetworkData,
    RadarItem,
    PrescriptionCompoundItem, PrescriptionCompoundsData
)
from app.models.tables import (
    Prescription, Herb, Compound, Target,
    RelPrescriptionHerb, RelHerbCompound, RelCompoundTarget
)
from app.services.pharmacology import async_get_efficacy_scores

router = APIRouter()


def _clean_herb_names(rels):
    """拆分 '桂枝/大枣/麻黄' 这类组合名，去重并保持顺序"""
    seen = set()
    result = []
    for r in rels:
        if not getattr(r, 'herb_name', None):
            continue
        for part in re.split(r'[/、,，]', r.herb_name):
            name = part.strip()
            if name and name not in seen:
                seen.add(name)
                result.append(name)
    return result


def _extract_dosage(usage):
    """从用法用量文本中提取克数区间，如 '3～9g。' -> '3～9g'"""
    if not usage:
        return None
    m = re.search(r'(\d+(?:\.\d+)?\s*[～~－—-]\s*\d+(?:\.\d+)?\s*g)', usage)
    if m:
        return m.group(1).replace(' ', '')
    m = re.search(r'(\d+(?:\.\d+)?\s*g)', usage)
    if m:
        return m.group(1).replace(' ', '')
    return None


def _resolve_dosages(db, herb_names, rels=None):
    """为药材名称列表解析剂量：优先方剂级精确剂量 → 回退药材标准用量"""
    dosages = []
    if not herb_names:
        return dosages
    # 方剂级精确剂量优先（仅使用单味药材条目，忽略 '款冬花/细辛' 这种组合行）
    rel_map = {}
    if rels:
        for r in rels:
            hname = getattr(r, 'herb_name', None)
            dosage = getattr(r, 'dosage', None)
            if hname and dosage and '/' not in hname and '、' not in hname:
                rel_map[hname.strip()] = dosage
    herb_map = {h.name: h.dosage for h in db.query(Herb).filter(Herb.name.in_(herb_names)).all()}
    for name in herb_names:
        if name in rel_map:
            dosages.append(rel_map[name])  # 精确剂量
        else:
            standard = herb_map.get(name)
            if standard:
                extracted = _extract_dosage(standard)
                # 如果提取出的仍是范围（含～），而 Excel 中该方剂没有此药材剂量 → 标记为未解析
                if '～' in extracted and name not in rel_map:
                    extracted = '—'
                dosages.append(extracted)
            else:
                dosages.append('—')
    return dosages


def _get_herbs_by_prescription(db: Session, prescription_id: int):
    """
    通过 herb_name 关联 Herb 表获取方剂下的药材列表。
    V2 的 rel_prescription_herb.herb_id 可能存的是旧数字ID，
    因此统一通过 herb_name 字段匹配 Herb.name。
    """
    herb_name_rows = (
        db.query(RelPrescriptionHerb.herb_name)
        .filter(RelPrescriptionHerb.prescription_id == prescription_id)
        .filter(RelPrescriptionHerb.herb_name.isnot(None))
        .filter(RelPrescriptionHerb.herb_name != "")
        .all()
    )
    herb_names = [r[0] for r in herb_name_rows]
    if not herb_names:
        return []
    return db.query(Herb).filter(Herb.name.in_(herb_names)).all()


@router.get("")
async def get_prescriptions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: str = Query("", description="方剂名称模糊搜索"),
    db: Session = Depends(get_db)
):
    """获取方剂列表（支持分页 + 搜索）"""
    base_query = db.query(Prescription)

    # 名称模糊搜索
    if keyword.strip():
        base_query = base_query.filter(Prescription.name.like(f"%{keyword}%"))

    total = base_query.count()
    offset = (page - 1) * page_size

    items = base_query.offset(offset).limit(page_size).all()

    prescription_items = []
    for p in items:
        # 药材关联：拆分组合名 + 剂量回退
        rels = db.query(RelPrescriptionHerb).filter(
            RelPrescriptionHerb.prescription_id == p.id
        ).all()
        herb_names = _clean_herb_names(rels)
        herb_dosages = _resolve_dosages(db, herb_names, rels)
        herb_count = len(herb_names)

        # 入血成分数 & 哮喘靶点数 —— 通过拆分后的 herb_name 匹配
        herb_id_sub = db.query(Herb.id).filter(
            Herb.name.in_(herb_names)
        ).subquery()
        comp_sub = db.query(RelHerbCompound.compound_id).filter(
            RelHerbCompound.herb_id.in_(herb_id_sub)
        ).subquery()
        blood_count = db.query(func.count(Compound.id)).filter(
            Compound.id.in_(comp_sub),
            func.coalesce(Compound.blood_entry_probability, 0) >= 0.5
        ).scalar() or 0
        target_count = db.query(func.count(func.distinct(RelCompoundTarget.target_gene))).filter(
            RelCompoundTarget.compound_id.in_(comp_sub)
        ).join(Target, RelCompoundTarget.target_gene == Target.gene).filter(
            Target.asthma_related == True
        ).scalar() or 0

        prescription_items.append(PrescriptionBrief(
            id=p.id, name=p.name,
            core_effect=p.core_effect, indication_type=None,
            herb_count=herb_count,
            herb_names=herb_names,
            herb_dosages=herb_dosages,
            blood_compound_count=blood_count,
            asthma_target_count=target_count
        ))

    data = PrescriptionListData(
        items=prescription_items,
        total=total,
        page=page,
        page_size=page_size
    )

    return ResponseModel(data=data)


@router.get("/{prescription_id}")
async def get_prescription_detail(
    prescription_id: int,
    db: Session = Depends(get_db)
):
    """获取方剂基础信息 + 包含的药材列表"""
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        return ResponseModel(code=404, message="方剂不存在", data=None)

    # 通过 herb_name 关联获取药材列表（rel_prescription_herb.herb_id 可能是旧数字ID）
    herbs = _get_herbs_by_prescription(db, prescription_id)

    # 拆分组合名并去重，保持与列表页一致的展示
    rels = db.query(RelPrescriptionHerb).filter(
        RelPrescriptionHerb.prescription_id == prescription_id
    ).all()
    clean_names = _clean_herb_names(rels)
    name_to_herb = {h.name: h for h in herbs}

    herbs_out = []
    for name in clean_names:
        herb = name_to_herb.get(name)
        rph = None
        if herb:
            rph = db.query(RelPrescriptionHerb).filter(
                RelPrescriptionHerb.prescription_id == prescription_id,
                (RelPrescriptionHerb.herb_id == herb.id) |
                (RelPrescriptionHerb.herb_name == herb.name)
            ).first()
        dosage = None
        if rph and getattr(rph, 'dosage', None):
            dosage = rph.dosage
        elif herb:
            dosage = _extract_dosage(herb.dosage)
        herbs_out.append(HerbBrief(
            id=herb.id if herb else '',
            name=name,
            functions=herb.functions if herb else None,
            dosage=dosage
        ))

    # 计算统计摘要
    herb_ids = [h.id for h in name_to_herb.values() if h]
    comp_sub = db.query(RelHerbCompound.compound_id).filter(
        RelHerbCompound.herb_id.in_(herb_ids)
    ).subquery()
    blood_count = db.query(func.count(Compound.id)).filter(
        Compound.id.in_(comp_sub),
        Compound.blood_entry_probability >= 0.5
    ).scalar() or 0
    target_count = db.query(func.count(func.distinct(RelCompoundTarget.target_gene))).filter(
        RelCompoundTarget.compound_id.in_(comp_sub)
    ).scalar() or 0
    asthma_target_count = db.query(func.count(func.distinct(RelCompoundTarget.target_gene))).filter(
        RelCompoundTarget.compound_id.in_(comp_sub)
    ).join(Target, RelCompoundTarget.target_gene == Target.gene).filter(
        Target.asthma_related == True
    ).scalar() or 0

    stats = PrescriptionStats(
        blood_compound_count=blood_count,
        asthma_target_count=asthma_target_count or target_count,
        pathway_count=12  # 固定值（后续可从 KEGG 富集计算）
    )

    data = PrescriptionDetailData(
        id=prescription.id,
        name=prescription.name,
        description=prescription.description,
        core_effect=prescription.core_effect,
        indication_type=None,
        herbs=herbs_out,
        stats=stats
    )

    return ResponseModel(data=data)


@router.get("/{prescription_id}/network")
async def get_prescription_network(
    prescription_id: int,
    min_prob: float = Query(0.5, ge=0, le=1, description="最低入血概率阈值"),
    asthma_only: bool = Query(False, description="仅显示哮喘相关靶点"),
    max_compounds: int = Query(30, ge=1, le=200, description="最多展示化合物数量（按概率降序）"),
    max_targets_per_compound: int = Query(10, ge=1, le=100, description="每个化合物最多展示靶点数"),
    db: Session = Depends(get_db)
):
    """
    核心拓扑图数据接口
    查询 方剂→药材→化合物→靶点 完整层级，返回 Cytoscape.js 格式
    入血概率使用 V2 的 blood_entry_probability
    asthma_only=True 时仅返回哮喘相关靶点节点
    为避免节点过多导致前端卡顿，对化合物和靶点数量做上限控制
    """
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        return ResponseModel(code=404, message="方剂不存在", data=None)

    nodes = []
    edges = []
    node_ids = set()   # O(1) 去重
    edge_keys = set()  # O(1) 去重

    # 1. 方剂节点
    p_node_id = f"P_{prescription.id}"
    nodes.append(CytoNode(id=p_node_id, label=prescription.name, category="prescription"))
    node_ids.add(p_node_id)

    # 2. 药材节点（通过 herb_name 关联 Herb 表）
    herbs = _get_herbs_by_prescription(db, prescription_id)

    # 3. 收集所有符合条件的化合物，按入血概率降序排列，取 top N
    all_compounds = []
    for herb in herbs:
        for compound in herb.compounds:
            blood_prob = compound.blood_entry_probability
            if blood_prob is None or blood_prob < min_prob:
                continue
            all_compounds.append((compound, herb, blood_prob))

    # 按入血概率降序排列，取前 max_compounds 个
    all_compounds.sort(key=lambda x: x[2], reverse=True)
    selected_compounds = all_compounds[:max_compounds]

    for compound, herb, blood_prob in selected_compounds:
        h_node_id = f"H_{herb.id}"
        if h_node_id not in node_ids:
            nodes.append(CytoNode(id=h_node_id, label=herb.name, category="herb"))
            node_ids.add(h_node_id)
        ek = f"{p_node_id}->{h_node_id}"
        if ek not in edge_keys:
            edges.append(CytoEdge(source=p_node_id, target=h_node_id, category="p2h"))
            edge_keys.add(ek)

        c_node_id = f"C_{compound.id}"
        if c_node_id not in node_ids:
            nodes.append(CytoNode(
                id=c_node_id, label=compound.name,
                category="compound", prob=round(blood_prob, 4)
            ))
            node_ids.add(c_node_id)
        ek = f"{h_node_id}->{c_node_id}"
        if ek not in edge_keys:
            edges.append(CytoEdge(source=h_node_id, target=c_node_id, category="h2c"))
            edge_keys.add(ek)

        # 4. 靶点节点 - 优先哮喘相关，限制每化合物靶点数
        targets = list(compound.targets)
        if asthma_only:
            targets = [t for t in targets if t.asthma_related]

        # 哮喘相关靶点优先，然后按基因名排序
        targets.sort(key=lambda t: (not (t.asthma_related or False), t.gene))
        targets = targets[:max_targets_per_compound]

        for target in targets:
            t_node_id = f"T_{target.gene}"
            if t_node_id not in node_ids:
                nodes.append(CytoNode(
                    id=t_node_id, label=target.gene, category="target",
                    asthma_related=target.asthma_related
                ))
                node_ids.add(t_node_id)
            ek = f"{c_node_id}->{t_node_id}"
            if ek not in edge_keys:
                edges.append(CytoEdge(source=c_node_id, target=t_node_id, category="c2t"))
                edge_keys.add(ek)

    data = NetworkData(nodes=nodes, edges=edges)
    return ResponseModel(data=data)


@router.get("/{prescription_id}/radar")
async def get_prescription_radar(
    prescription_id: int,
    db: Session = Depends(get_db)
):
    """
    疗效雷达图数据（基于预计算 compound.radar_* 字段聚合）

    策略：
      1. 查询方剂下所有入血化合物（blood_entry_probability >= 0.5）
      2. 按 blood_entry_probability 加权平均 3 个疗效维度分数
      3. 若预计算字段全为 NULL，降级到 GSEA 富集分析
    """
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        return ResponseModel(code=404, message="方剂不存在", data=None)

    # 查询方剂下所有化合物及其预计算雷达评分
    compounds = (
        db.query(
            Compound.blood_entry_probability,
            Compound.radar_anti_inflammatory,
            Compound.radar_immune_regulation,
            Compound.radar_airway_repair,
        )
        .join(RelHerbCompound, RelHerbCompound.compound_id == Compound.id)
        .join(Herb, Herb.id == RelHerbCompound.herb_id)
        .join(RelPrescriptionHerb, RelPrescriptionHerb.herb_name == Herb.name)
        .filter(RelPrescriptionHerb.prescription_id == prescription_id)
        .filter(func.coalesce(Compound.blood_entry_probability, 0) >= 0.5)
        .distinct()
        .all()
    )

    if not compounds:
        # 降级1：无入血化合物，尝试所有化合物
        compounds = (
            db.query(
                Compound.blood_entry_probability,
                Compound.radar_anti_inflammatory,
                Compound.radar_immune_regulation,
                Compound.radar_airway_repair,
            )
            .join(RelHerbCompound, RelHerbCompound.compound_id == Compound.id)
            .join(Herb, Herb.id == RelHerbCompound.herb_id)
            .join(RelPrescriptionHerb, RelPrescriptionHerb.herb_name == Herb.name)
            .filter(RelPrescriptionHerb.prescription_id == prescription_id)
            .distinct()
            .all()
        )

    # 按入血概率加权平均预计算雷达分数
    anti_scores = [(c.radar_anti_inflammatory, c.blood_entry_probability or 0.5) for c in compounds if c.radar_anti_inflammatory is not None]
    immune_scores = [(c.radar_immune_regulation, c.blood_entry_probability or 0.5) for c in compounds if c.radar_immune_regulation is not None]
    repair_scores = [(c.radar_airway_repair, c.blood_entry_probability or 0.5) for c in compounds if c.radar_airway_repair is not None]

    def weighted_avg(pairs):
        if not pairs:
            return None
        total_w = sum(w for _, w in pairs)
        if total_w == 0:
            return int(sum(s for s, _ in pairs) / len(pairs))
        return int(sum(s * w for s, w in pairs) / total_w)

    anti = weighted_avg(anti_scores)
    immune = weighted_avg(immune_scores)
    repair = weighted_avg(repair_scores)

    # 预计算字段有值 → 直接返回
    if anti is not None or immune is not None or repair is not None:
        data = [
            RadarItem(efficacy_type="抗炎效能", count=anti or 0),
            RadarItem(efficacy_type="免疫调节", count=immune or 0),
            RadarItem(efficacy_type="气道修复", count=repair or 0),
        ]
        return ResponseModel(data=data)

    # 降级2：预计算字段全为 NULL，使用 GSEA 富集分析
    gene_rows = (
        db.query(Target.gene)
        .join(RelCompoundTarget, RelCompoundTarget.target_gene == Target.gene)
        .join(Compound, Compound.id == RelCompoundTarget.compound_id)
        .join(RelHerbCompound, RelHerbCompound.compound_id == Compound.id)
        .join(Herb, Herb.id == RelHerbCompound.herb_id)
        .join(RelPrescriptionHerb, RelPrescriptionHerb.herb_name == Herb.name)
        .filter(RelPrescriptionHerb.prescription_id == prescription_id)
        .distinct()
        .all()
    )
    gene_list = [r[0] for r in gene_rows if r[0]]

    if not gene_list:
        return ResponseModel(data=[])

    result = await async_get_efficacy_scores(gene_list)
    result.pop("fallback", None)

    data = [RadarItem(efficacy_type=k, count=v) for k, v in result.items()]
    return ResponseModel(data=data)


@router.get("/{prescription_id}/compounds")
async def get_prescription_compounds(
    prescription_id: int,
    min_prob: float = Query(0.5, ge=0, le=1, description="最低入血概率阈值"),
    db: Session = Depends(get_db)
):
    """
    获取方剂下的入血化合物列表
    多表 JOIN：方剂→药材→化合物，按入血概率降序排列
    V2：rel_prescription_herb 通过 herb_name 关联 Herb
    """
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        return ResponseModel(code=404, message="方剂不存在", data=None)

    # 多表 JOIN 查询：方剂→药材→化合物
    # 概率过滤逻辑：min_prob > 0 时才过滤（NULL 概率的化合物保留，视为未预测）
    base_query = (
        db.query(
            Compound.id,
            Compound.name,
            Compound.prob_cctcm,
            Compound.prob_herb,
            Compound.blood_entry_probability,
            Herb.name.label("herb_name")
        )
        .join(RelHerbCompound, RelHerbCompound.compound_id == Compound.id)
        .join(Herb, Herb.id == RelHerbCompound.herb_id)
        .join(RelPrescriptionHerb, RelPrescriptionHerb.herb_name == Herb.name)
        .filter(RelPrescriptionHerb.prescription_id == prescription_id)
    )

    # min_prob > 0 时过滤低概率化合物（NULL 视为 0，低于阈值则排除）
    if min_prob > 0:
        base_query = base_query.filter(
            func.coalesce(Compound.blood_entry_probability, 0) >= min_prob
        )

    query = base_query.order_by(func.coalesce(Compound.blood_entry_probability, 0).desc())

    results = query.all()

    # 去重（同一化合物可能来自多味药材，保留第一个来源）
    seen = set()
    items = []
    for row in results:
        if row.id in seen:
            continue
        seen.add(row.id)
        items.append(PrescriptionCompoundItem(
            id=row.id,
            name=row.name,
            prob_cctcm=round(row.prob_cctcm, 4) if row.prob_cctcm is not None else None,
            prob_herb=round(row.prob_herb, 4) if row.prob_herb is not None else None,
            blood_prob=round(row.blood_entry_probability, 4) if row.blood_entry_probability is not None else None,
            blood_entry_probability=round(row.blood_entry_probability, 4) if row.blood_entry_probability is not None else None,
            herb_name=row.herb_name
        ))

    data = PrescriptionCompoundsData(items=items, total=len(items))
    return ResponseModel(data=data)
