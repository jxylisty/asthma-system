"""
化合物与算法路由
- GET /                             全量化合物列表（分页 + 搜索）
- GET /high-potential                双模型高潜化合物（PU Learning 成果展示）
- GET /{compound_id}                 化合物详情
- GET /{compound_id}/targets         化合物靶点列表
- GET /{compound_id}/radar           化合物疗效雷达图（GSEA 富集分析）
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.db import get_db
from app.schemas import (
    ResponseModel,
    HighPotentialCompound, HighPotentialData,
    CompoundDetailData,
    CompoundListItem, CompoundListData,
    TargetBrief,
    EfficacyRadarResponse
)
from app.models.tables import Compound, Target, RelCompoundTarget, RelHerbCompound, Herb
from app.services.pharmacology import async_get_efficacy_scores

router = APIRouter()


def _compute_rdkit_properties(smiles: str) -> dict:
    """使用 RDKit 从 SMILES 计算分子物理化学属性"""
    if not smiles:
        return {}
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors, rdMolDescriptors, Crippen

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return {}

        return {
            "hbd": Descriptors.NumHDonors(mol),
            "hba": Descriptors.NumHAcceptors(mol),
            "tpsa": round(Descriptors.TPSA(mol), 2),
            "rotatable_bonds": Descriptors.NumRotatableBonds(mol),
            "num_rings": rdMolDescriptors.CalcNumRings(mol),
            "num_aromatic_rings": rdMolDescriptors.CalcNumAromaticRings(mol),
            "num_heavy_atoms": mol.GetNumHeavyAtoms(),
            "molecular_formula": rdMolDescriptors.CalcMolFormula(mol),
        }
    except Exception:
        return {}


@router.get("")
async def get_compounds(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: str = Query("", description="化合物名称模糊搜索"),
    min_prob: float = Query(0, ge=0, le=1, description="最低入血概率阈值（0=不过滤）"),
    db: Session = Depends(get_db)
):
    """
    全量化合物列表（分页 + 搜索 + 概率过滤）
    按入血概率降序排列（ccTCM 模型 prob_cctcm）
    """
    base_query = db.query(Compound)

    # 名称模糊搜索
    if keyword.strip():
        base_query = base_query.filter(Compound.name.like(f"%{keyword}%"))

    # 概率过滤：min_prob > 0 时才过滤
    if min_prob > 0:
        base_query = base_query.filter(
            func.coalesce(Compound.prob_cctcm, 0) >= min_prob
        )

    total = base_query.count()

    # 按入血概率降序
    offset = (page - 1) * page_size
    compounds = base_query.order_by(
        func.coalesce(Compound.prob_cctcm, 0).desc()
    ).offset(offset).limit(page_size).all()

    items = []
    for c in compounds:
        blood_prob = c.prob_cctcm

        # 查询来源药材名称
        herb_names = (
            db.query(Herb.name)
            .join(RelHerbCompound, RelHerbCompound.herb_id == Herb.id)
            .filter(RelHerbCompound.compound_id == c.id)
            .all()
        )

        items.append(CompoundListItem(
            id=c.id,
            name=c.name,
            prob_cctcm=round(c.prob_cctcm, 4) if c.prob_cctcm is not None else None,
            prob_herb=round(c.prob_herb, 4) if c.prob_herb is not None else None,
            blood_prob=round(blood_prob, 4) if blood_prob is not None else None,
            blood_entry_probability=round(c.prob_cctcm, 4) if c.prob_cctcm is not None else None,
            asthma_related=c.asthma_related,
            smile_short=c.smile_short,
            smiles=c.smiles,               # 完整 SMILES
            target_count=c.target_count,
            herb_names=[h[0] for h in herb_names],
            mw=c.mw,
            logp=c.logp,
            tpsa=getattr(c, 'tpsa', None)
        ))

    data = CompoundListData(items=items, total=total, page=page, page_size=page_size)
    return ResponseModel(data=data)


@router.get("/high-potential")
async def get_high_potential_compounds(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    PU Learning 算法成果展示
    筛选入血概率 >= 0.85 的高潜化合物
    优先双模型 AND 逻辑，HERB 概率缺失时降级为单模型
    """
    # 优先：双模型均 >= 0.85
    base_query = db.query(Compound).filter(
        Compound.prob_cctcm >= 0.85,
        Compound.prob_herb >= 0.85
    )

    # 降级：如果双模型结果为空（HERB 概率缺失），改用 prob_cctcm >= 0.85
    if base_query.count() == 0:
        base_query = db.query(Compound).filter(
            Compound.prob_cctcm >= 0.85
        )

    total = base_query.count()

    # 按入血概率降序排列
    offset = (page - 1) * page_size
    compounds = base_query.order_by(
        func.coalesce(Compound.prob_cctcm, Compound.prob_herb, 0).desc()
    ).offset(offset).limit(page_size).all()

    items = [HighPotentialCompound(
        id=c.id,
        name=c.name,
        prob_cctcm=round(c.prob_cctcm, 4) if c.prob_cctcm is not None else None,
        prob_herb=round(c.prob_herb, 4) if c.prob_herb is not None else None,
        avg_prob=round(c.prob_cctcm, 4) if c.prob_cctcm is not None else None,
        blood_prob=round(c.prob_cctcm, 4) if c.prob_cctcm is not None else None,
        blood_entry_probability=round(c.prob_cctcm, 4) if c.prob_cctcm is not None else None,
        mw=c.mw,
        logp=c.logp
    ) for c in compounds]

    data = HighPotentialData(items=items, total=total, page=page, page_size=page_size)
    return ResponseModel(data=data)


@router.get("/{compound_id}")
async def get_compound_detail(
    compound_id: str,
    db: Session = Depends(get_db)
):
    """获取化合物详细信息（含双模型入血概率 + 来源药材列表）"""
    compound = db.query(Compound).filter(Compound.id == compound_id).first()
    if not compound:
        return ResponseModel(code=404, message="化合物不存在", data=None)

    # 查询来源药材列表（通过中间表）
    herb_names = (
        db.query(Herb.name)
        .join(RelHerbCompound, RelHerbCompound.herb_id == Herb.id)
        .filter(RelHerbCompound.compound_id == compound_id)
        .all()
    )

    blood_prob = compound.prob_cctcm

    # RDKit 计算分子物理化学属性
    rdkit_props = _compute_rdkit_properties(compound.smiles)

    data = CompoundDetailData(
        id=compound.id,
        name=compound.name,
        prob_cctcm=round(compound.prob_cctcm, 4) if compound.prob_cctcm is not None else None,
        prob_herb=round(compound.prob_herb, 4) if compound.prob_herb is not None else None,
        blood_prob=round(blood_prob, 4) if blood_prob is not None else None,
        blood_entry_probability=round(compound.prob_cctcm, 4) if compound.prob_cctcm is not None else None,
        asthma_related=compound.asthma_related,
        herb_names=[h[0] for h in herb_names],
        smiles=compound.smiles,
        smile_short=compound.smile_short,
        mw=compound.mw,
        logp=compound.logp,
        hbd=rdkit_props.get("hbd"),
        hba=rdkit_props.get("hba"),
        tpsa=rdkit_props.get("tpsa"),
        rotatable_bonds=rdkit_props.get("rotatable_bonds"),
        num_rings=rdkit_props.get("num_rings"),
        num_aromatic_rings=rdkit_props.get("num_aromatic_rings"),
        num_heavy_atoms=rdkit_props.get("num_heavy_atoms"),
        molecular_formula=rdkit_props.get("molecular_formula"),
        radar_anti_inflammatory=compound.radar_anti_inflammatory,
        radar_immune_regulation=compound.radar_immune_regulation,
        radar_airway_repair=compound.radar_airway_repair,
        target_count=compound.target_count
    )

    return ResponseModel(data=data)


@router.get("/{compound_id}/structure")
async def get_compound_3d_structure(
    compound_id: str,
    db: Session = Depends(get_db)
):
    """生成 3D 分子结构 MOL block（供 3Dmol.js 渲染）"""
    compound = db.query(Compound).filter(Compound.id == compound_id).first()
    if not compound or not compound.smiles:
        return ResponseModel(code=404, message="无可用 SMILES", data=None)

    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem

        mol = Chem.MolFromSmiles(compound.smiles)
        if mol is None:
            return ResponseModel(code=422, message="SMILES 解析失败", data=None)

        mol = Chem.AddHs(mol)
        # 生成 3D 坐标
        result = AllChem.EmbedMolecule(mol, AllChem.ETKDG())
        if result != 0:
            # ETKDG 失败，尝试随机嵌入
            result = AllChem.EmbedMolecule(mol, useRandomCoords=True)
            if result != 0:
                return ResponseModel(code=500, message="3D 坐标生成失败", data=None)

        # 力场优化
        try:
            AllChem.MMFFOptimizeMolecule(mol, maxIters=200)
        except Exception:
            pass  # MMFF 优化失败不影响 MOL block 生成

        molblock = Chem.MolToMolBlock(mol)
        return ResponseModel(data={"molblock": molblock, "smiles": compound.smiles})
    except Exception as e:
        return ResponseModel(code=500, message=f"3D 结构生成异常: {str(e)}", data=None)


@router.get("/{compound_id}/targets")
async def get_compound_targets(
    compound_id: str,
    db: Session = Depends(get_db)
):
    """获取特定化合物作用的靶点列表"""
    # 验证化合物是否存在
    compound = db.query(Compound).filter(Compound.id == compound_id).first()
    if not compound:
        return ResponseModel(code=404, message="化合物不存在", data=None)

    # 直接 JOIN rel_compound_target + target 表，获取完整活性数据
    results = db.query(RelCompoundTarget, Target).join(
        Target, RelCompoundTarget.target_gene == Target.gene
    ).filter(RelCompoundTarget.compound_id == compound_id).all()

    data = [TargetBrief(
        gene=t.gene,
        target_type=t.target_type,
        species=t.species,
        asthma_related=t.asthma_related,
        source_db=rct.source_db,
        network_centrality=rct.network_centrality,
        activity_type=rct.activity_type,
        activity_value=rct.activity_value,
        activity_unit=rct.activity_unit,
        reference=rct.reference
    ) for rct, t in results]

    return ResponseModel(data=data)


@router.get("/{compound_id}/radar")
async def get_compound_efficacy_radar(
    compound_id: str,
    db: Session = Depends(get_db)
):
    """
    化合物疗效雷达图接口

    策略：
      1. 优先返回数据库预计算的 radar_* 字段（快速、稳定）
      2. 预计算字段全为 NULL 时，降级到 GSEA 富集分析
    """
    # 查询化合物
    compound = db.query(Compound).filter(Compound.id == compound_id).first()
    if not compound:
        return ResponseModel(code=404, message="化合物不存在", data=None)

    # 优先使用预计算雷达评分
    pre_anti = compound.radar_anti_inflammatory
    pre_immune = compound.radar_immune_regulation
    pre_repair = compound.radar_airway_repair

    if pre_anti is not None or pre_immune is not None or pre_repair is not None:
        scores = {
            "抗炎效能": int(pre_anti) if pre_anti is not None else 0,
            "免疫调节": int(pre_immune) if pre_immune is not None else 0,
            "气道修复": int(pre_repair) if pre_repair is not None else 0,
        }
        gene_count = compound.target_count or 0
        data = EfficacyRadarResponse(
            id=compound.id,
            compound_name=compound.name,
            gene_count=gene_count,
            scores=scores,
            anti_inflammatory=scores["抗炎效能"],
            immune_regulation=scores["免疫调节"],
            airway_repair=scores["气道修复"],
            fallback=False
        )
        return ResponseModel(data=data)

    # 降级：预计算字段为空，使用 GSEA 富集分析
    targets = compound.targets
    gene_list = [t.gene for t in targets if t.gene]

    if not gene_list:
        gene_list = ["TNF", "IL6", "IL4", "PTGS2", "MMP9"]

    result = await async_get_efficacy_scores(gene_list)
    is_fallback = result.pop("fallback", False)

    data = EfficacyRadarResponse(
        id=compound.id,
        compound_name=compound.name,
        gene_count=len(gene_list),
        scores=result,
        anti_inflammatory=result.get("抗炎效能", 0),
        immune_regulation=result.get("免疫调节", 0),
        airway_repair=result.get("气道修复", 0),
        fallback=is_fallback
    )

    return ResponseModel(data=data)
