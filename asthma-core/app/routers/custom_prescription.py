"""
自定义处方分析路由
- POST /analyze          计算自定义处方的化合物/靶点/雷达图/网络图
- POST /ai-report        流式生成 AI 智能分析报告（SSE）
- POST /existing-analyze 复用已有方剂 ID 生成结构化数据（供方剂详情页导出）
"""
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.db import get_db
from app.schemas import ResponseModel
from app.models.tables import (
    Prescription, Herb, Compound, Target,
    RelPrescriptionHerb, RelHerbCompound, RelCompoundTarget
)
from app.services.ai_service import (
    stream_chat, AIConfigError,
    SYSTEM_PROMPT, build_user_prompt,
)

router = APIRouter()


# ==================== 请求/响应模型 ====================

class HerbItem(BaseModel):
    """单味中药条目"""
    herb_id: str = Field(..., description="药材ID (ccTCM编号)")
    herb_name: str = Field(..., description="药材名称")
    dosage: str = Field(default="", description="剂量，如 9g")


class CustomPrescriptionRequest(BaseModel):
    """自定义处方分析请求"""
    prescription_name: str = Field(..., description="处方名称")
    herbs: List[HerbItem] = Field(..., min_items=1, description="中药列表")


class AIReportRequest(BaseModel):
    """AI 报告生成请求"""
    prescription_name: str
    herbs: List[HerbItem]
    min_prob: float = Field(default=0.5, ge=0, le=1)
    top_compounds: int = Field(default=10, ge=1, le=50)


class ExistingPrescriptionAIRequest(BaseModel):
    """已有方剂生成 AI 报告请求"""
    prescription_id: int
    min_prob: float = Field(default=0.5, ge=0, le=1)
    top_compounds: int = Field(default=10, ge=1, le=50)


# ==================== 核心计算逻辑 ====================

def _get_herbs_by_ids(db: Session, herb_ids: List[str]) -> List[Herb]:
    """通过 herb_id 列表获取药材"""
    return db.query(Herb).filter(Herb.id.in_(herb_ids)).all()


def _collect_compounds_for_herbs(
    db: Session,
    herb_ids: List[str],
    min_prob: float = 0.5,
):
    """
    收集给定药材列表下的所有化合物，按入血概率降序排列。
    返回 [(compound, herb), ...]
    """
    rows = (
        db.query(
            Compound,
            Herb.name.label("herb_name"),
        )
        .join(RelHerbCompound, RelHerbCompound.compound_id == Compound.id)
        .join(Herb, Herb.id == RelHerbCompound.herb_id)
        .filter(Herb.id.in_(herb_ids))
        .all()
    )

    # min_prob > 0 时过滤
    if min_prob > 0:
        rows = [r for r in rows if (r.Compound.prob_cctcm or 0) >= min_prob]

    # 按入血概率降序
    rows.sort(
        key=lambda r: r.Compound.prob_cctcm or 0,
        reverse=True,
    )
    return rows


def _compute_radar_scores(db: Session, herb_ids: List[str]) -> List[dict]:
    """按入血概率加权平均预计算 radar_* 字段"""
    compounds = (
        db.query(
            Compound.prob_cctcm,
            Compound.radar_anti_inflammatory,
            Compound.radar_immune_regulation,
            Compound.radar_airway_repair,
        )
        .join(RelHerbCompound, RelHerbCompound.compound_id == Compound.id)
        .join(Herb, Herb.id == RelHerbCompound.herb_id)
        .filter(Herb.id.in_(herb_ids))
        .filter(func.coalesce(Compound.prob_cctcm, 0) >= 0.5)
        .distinct()
        .all()
    )

    def weighted(pairs):
        if not pairs:
            return 0
        total_w = sum(w for _, w in pairs)
        if total_w == 0:
            return int(sum(s for s, _ in pairs) / len(pairs))
        return int(sum(s * w for s, w in pairs) / total_w)

    anti = weighted([(c.radar_anti_inflammatory, c.prob_cctcm or 0.5) for c in compounds if c.radar_anti_inflammatory is not None])
    immune = weighted([(c.radar_immune_regulation, c.prob_cctcm or 0.5) for c in compounds if c.radar_immune_regulation is not None])
    repair = weighted([(c.radar_airway_repair, c.prob_cctcm or 0.5) for c in compounds if c.radar_airway_repair is not None])

    return [
        {"efficacy_type": "抗炎效能", "count": anti},
        {"efficacy_type": "免疫调节", "count": immune},
        {"efficacy_type": "气道修复", "count": repair},
    ]


def _collect_targets(db: Session, compound_ids: List[str], asthma_only: bool = False, limit: int = 50):
    """收集化合物对应的靶点"""
    query = (
        db.query(
            Target.gene,
            Target.asthma_related,
            RelCompoundTarget.activity_type,
            RelCompoundTarget.activity_value,
            RelCompoundTarget.activity_unit,
            RelCompoundTarget.network_centrality,
            RelCompoundTarget.source_db,
            Compound.name.label("compound_name"),
        )
        .join(RelCompoundTarget, RelCompoundTarget.target_gene == Target.gene)
        .join(Compound, Compound.id == RelCompoundTarget.compound_id)
        .filter(Compound.id.in_(compound_ids))
    )
    if asthma_only:
        query = query.filter(Target.asthma_related == True)

    rows = query.all()
    # 哮喘相关优先
    rows.sort(key=lambda r: (not (r.asthma_related or False), r.gene))
    return rows[:limit]


# ==================== 路由：结构化数据分析 ====================

@router.post("/analyze")
async def analyze_custom_prescription(
    req: CustomPrescriptionRequest,
    min_prob: float = Query(0.5, ge=0, le=1),
    db: Session = Depends(get_db),
):
    """
    计算自定义处方的结构化分析数据：
    - Top 入血化合物列表
    - 雷达图分数
    - 核心靶点列表
    - 基本统计信息
    """
    herb_ids = [h.herb_id for h in req.herbs]
    herbs = _get_herbs_by_ids(db, herb_ids)

    if not herbs:
        return ResponseModel(code=404, message="未找到匹配的药材，请检查药材ID", data=None)

    # 药材信息
    herb_info = [
        {
            "id": h.id,
            "name": h.name,
            "nature": h.nature,
            "flavor": h.flavor,
            "meridians": h.meridians,
            "functions": h.functions,
            "category": h.category,
            "dosage": next((hr.dosage for hr in req.herbs if hr.herb_id == h.id), ""),
        }
        for h in herbs
    ]

    # 化合物
    compound_rows = _collect_compounds_for_herbs(db, herb_ids, min_prob=min_prob)
    compounds = []
    for r in compound_rows[:50]:  # 最多 50 个
        c = r.Compound
        compounds.append({
            "id": c.id,
            "name": c.name,
            "smiles": c.smiles,
            "mw": c.mw,
            "logp": c.logp,
            "prob_cctcm": round(c.prob_cctcm, 4) if c.prob_cctcm is not None else None,
            "prob_herb": round(c.prob_herb, 4) if c.prob_herb is not None else None,
            "blood_prob": round(c.prob_cctcm, 4) if c.prob_cctcm is not None else None,
            "asthma_related": c.asthma_related,
            "herb_name": r.herb_name,
        })

    # 雷达图
    radar = _compute_radar_scores(db, herb_ids)

    # 靶点
    compound_ids = list({c["id"] for c in compounds})
    target_rows = _collect_targets(db, compound_ids, asthma_only=False, limit=50)
    targets = []
    seen_genes = set()
    for r in target_rows:
        if r.gene in seen_genes:
            continue
        seen_genes.add(r.gene)
        targets.append({
            "gene": r.gene,
            "asthma_related": r.asthma_related,
            "activity_type": r.activity_type,
            "activity_value": r.activity_value,
            "activity_unit": r.activity_unit,
            "source_db": r.source_db,
            "compound_name": r.compound_name,
        })

    # 统计
    stats = {
        "herb_count": len(herbs),
        "compound_count": len(compounds),
        "target_count": len(targets),
        "asthma_target_count": sum(1 for t in targets if t["asthma_related"]),
        "high_prob_compound_count": sum(1 for c in compounds if (c["blood_prob"] or 0) >= 0.7),
    }

    return ResponseModel(data={
        "prescription_name": req.prescription_name,
        "herbs": herb_info,
        "compounds": compounds,
        "radar": radar,
        "targets": targets,
        "stats": stats,
    })


# ==================== 路由：AI 报告（流式 SSE） ====================

def _format_compounds_md(compounds: list) -> str:
    """把化合物列表格式化为 Markdown 表格"""
    if not compounds:
        return "（暂无符合条件的化合物数据）"

    header = "| 排名 | 化合物名称 | 来源中药 | ccTCM 2.0 | HERB 2.0 | 分子量 | LogP | 哮喘相关 |\n"
    sep = "|------|-----------|---------|-----------|---------|-------|------|---------|\n"
    rows = []
    for i, c in enumerate(compounds, 1):
        pcc = f"{c['prob_cctcm']*100:.1f}%" if c.get('prob_cctcm') is not None else "未预测"
        phb = f"{c['prob_herb']*100:.1f}%" if c.get('prob_herb') is not None else "无"
        mw = f"{c['mw']:.1f}" if c.get('mw') is not None else "—"
        lp = f"{c['logp']:.2f}" if c.get('logp') is not None else "—"
        ast = "是" if c.get('asthma_related') else "否"
        rows.append(
            f"| {i} | {c['name']} | {c.get('herb_name', '—')} | {pcc} | {phb} | {mw} | {lp} | {ast} |"
        )
    return header + sep + "\n".join(rows)


def _format_targets_md(targets: list) -> str:
    """把靶点列表格式化为 Markdown 表格"""
    if not targets:
        return "（暂无符合条件的靶点数据）"

    header = "| 靶点基因 | 哮喘相关 | 活性类型 | 活性值 | 单位 | 来源化合物 | 来源数据库 |\n"
    sep = "|---------|---------|---------|--------|------|-----------|------------|\n"
    rows = []
    for t in targets:
        ast = "是" if t.get('asthma_related') else "否"
        at = t.get('activity_type') or "—"
        av = f"{t['activity_value']:.2f}" if t.get('activity_value') is not None else "—"
        au = t.get('activity_unit') or "—"
        cn = t.get('compound_name') or "—"
        sd = t.get('source_db') or "—"
        rows.append(f"| {t['gene']} | {ast} | {at} | {av} | {au} | {cn} | {sd} |")
    return header + sep + "\n".join(rows)


def _format_herbs_text(herbs: list) -> str:
    """把药材列表格式化为文本"""
    return "、".join(
        f"{h['name']}" + (f" {h.get('dosage', '')}" if h.get('dosage') else "")
        for h in herbs
    )


async def _generate_ai_report_stream(
    prescription_name: str,
    herbs_data: list,
    compounds: list,
    targets: list,
    api_key: str,
    provider: str,
    base_url: str,
    model: str,
    min_prob: float,
):
    """生成 SSE 流：先发送结构化数据快照，再流式发送 AI 文本"""
    # 1) 先发送结构化数据快照（前端可据此渲染图表）
    snapshot = {
        "type": "snapshot",
        "data": {
            "prescription_name": prescription_name,
            "herbs": herbs_data,
            "compounds": compounds,
            "targets": targets,
        },
    }
    yield f"data: {json.dumps(snapshot, ensure_ascii=False)}\n\n"

    # 2) 构建 Prompt
    herbs_text = _format_herbs_text(herbs_data)
    compounds_md = _format_compounds_md(compounds[:15])  # Top 15
    targets_md = _format_targets_md(targets[:30])
    user_prompt = build_user_prompt(prescription_name, herbs_text, compounds_md, targets_md)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    # 3) 流式发送 AI 文本
    try:
        async for delta in stream_chat(
            messages=messages,
            api_key=api_key,
            provider=provider,
            base_url=base_url,
            model=model,
        ):
            chunk = {"type": "delta", "content": delta}
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        # 结束标记
        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
    except AIConfigError as e:
        err = {"type": "error", "code": e.code, "message": e.message}
        yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n"
    except Exception as e:
        err = {"type": "error", "code": "unknown", "message": f"AI 生成异常：{str(e)}"}
        yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n"


def _parse_ai_headers(
    x_ai_api_key: Optional[str],
    x_ai_provider: Optional[str],
    x_ai_base_url: Optional[str],
    x_ai_model: Optional[str],
) -> tuple[str, str, str, str]:
    """从请求头解析 AI 配置"""
    return (
        x_ai_api_key or "",
        (x_ai_provider or "deepseek").lower(),
        x_ai_base_url or "",
        x_ai_model or "",
    )


@router.post("/ai-report")
async def generate_custom_ai_report(
    req: AIReportRequest,
    x_ai_api_key: Optional[str] = Header(None, alias="X-AI-API-Key"),
    x_ai_provider: Optional[str] = Header(None, alias="X-AI-Provider"),
    x_ai_base_url: Optional[str] = Header(None, alias="X-AI-Base-URL"),
    x_ai_model: Optional[str] = Header(None, alias="X-AI-Model"),
    db: Session = Depends(get_db),
):
    """流式生成自定义处方 AI 报告（SSE）"""
    api_key, provider, base_url, model = _parse_ai_headers(
        x_ai_api_key, x_ai_provider, x_ai_base_url, x_ai_model
    )

    if not api_key:
        return ResponseModel(
            code=400,
            message="未配置 AI API Key，请在系统设置中填写后再生成报告",
            data=None,
        )

    herb_ids = [h.herb_id for h in req.herbs]
    herbs = _get_herbs_by_ids(db, herb_ids)
    if not herbs:
        return ResponseModel(code=404, message="未找到匹配的药材", data=None)

    herbs_data = [
        {
            "id": h.id,
            "name": h.name,
            "nature": h.nature,
            "flavor": h.flavor,
            "meridians": h.meridians,
            "functions": h.functions,
            "category": h.category,
            "dosage": next((hr.dosage for hr in req.herbs if hr.herb_id == h.id), ""),
        }
        for h in herbs
    ]

    compound_rows = _collect_compounds_for_herbs(db, herb_ids, min_prob=req.min_prob)
    compounds = [
        {
            "id": r.Compound.id,
            "name": r.Compound.name,
            "mw": r.Compound.mw,
            "logp": r.Compound.logp,
            "prob_cctcm": round(r.Compound.prob_cctcm, 4) if r.Compound.prob_cctcm is not None else None,
            "prob_herb": round(r.Compound.prob_herb, 4) if r.Compound.prob_herb is not None else None,
            "blood_prob": round(r.Compound.prob_cctcm, 4) if r.Compound.prob_cctcm is not None else None,
            "asthma_related": r.Compound.asthma_related,
            "herb_name": r.herb_name,
        }
        for r in compound_rows[:req.top_compounds]
    ]

    compound_ids = list({c["id"] for c in compounds})
    target_rows = _collect_targets(db, compound_ids, asthma_only=False, limit=30)
    targets = []
    seen_genes = set()
    for r in target_rows:
        if r.gene in seen_genes:
            continue
        seen_genes.add(r.gene)
        targets.append({
            "gene": r.gene,
            "asthma_related": r.asthma_related,
            "activity_type": r.activity_type,
            "activity_value": r.activity_value,
            "activity_unit": r.activity_unit,
            "source_db": r.source_db,
            "compound_name": r.compound_name,
        })

    return StreamingResponse(
        _generate_ai_report_stream(
            prescription_name=req.prescription_name,
            herbs_data=herbs_data,
            compounds=compounds,
            targets=targets,
            api_key=api_key,
            provider=provider,
            base_url=base_url,
            model=model,
            min_prob=req.min_prob,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ==================== 路由：已有方剂生成 AI 报告 ====================

@router.post("/existing-ai-report")
async def generate_existing_ai_report(
    req: ExistingPrescriptionAIRequest,
    x_ai_api_key: Optional[str] = Header(None, alias="X-AI-API-Key"),
    x_ai_provider: Optional[str] = Header(None, alias="X-AI-Provider"),
    x_ai_base_url: Optional[str] = Header(None, alias="X-AI-Base-URL"),
    x_ai_model: Optional[str] = Header(None, alias="X-AI-Model"),
    db: Session = Depends(get_db),
):
    """已有方剂生成 AI 报告（供方剂详情页导出使用）"""
    api_key, provider, base_url, model = _parse_ai_headers(
        x_ai_api_key, x_ai_provider, x_ai_base_url, x_ai_model
    )

    if not api_key:
        return ResponseModel(
            code=400,
            message="未配置 AI API Key，请在系统设置中填写后再生成报告",
            data=None,
        )

    prescription = db.query(Prescription).filter(Prescription.id == req.prescription_id).first()
    if not prescription:
        return ResponseModel(code=404, message="方剂不存在", data=None)

    # 复用 prescriptions.py 的 herb_name 关联逻辑
    herb_name_rows = (
        db.query(RelPrescriptionHerb.herb_name)
        .filter(RelPrescriptionHerb.prescription_id == req.prescription_id)
        .filter(RelPrescriptionHerb.herb_name.isnot(None))
        .filter(RelPrescriptionHerb.herb_name != "")
        .all()
    )
    herb_names = [r[0] for r in herb_name_rows]
    herbs = db.query(Herb).filter(Herb.name.in_(herb_names)).all() if herb_names else []

    if not herbs:
        return ResponseModel(code=404, message="该方剂未关联到药材数据", data=None)

    herbs_data = [
        {
            "id": h.id,
            "name": h.name,
            "nature": h.nature,
            "flavor": h.flavor,
            "meridians": h.meridians,
            "functions": h.functions,
            "category": h.category,
            "dosage": "",
        }
        for h in herbs
    ]

    herb_ids = [h.id for h in herbs]
    compound_rows = _collect_compounds_for_herbs(db, herb_ids, min_prob=req.min_prob)
    compounds = [
        {
            "id": r.Compound.id,
            "name": r.Compound.name,
            "mw": r.Compound.mw,
            "logp": r.Compound.logp,
            "prob_cctcm": round(r.Compound.prob_cctcm, 4) if r.Compound.prob_cctcm is not None else None,
            "prob_herb": round(r.Compound.prob_herb, 4) if r.Compound.prob_herb is not None else None,
            "blood_prob": round(r.Compound.prob_cctcm, 4) if r.Compound.prob_cctcm is not None else None,
            "asthma_related": r.Compound.asthma_related,
            "herb_name": r.herb_name,
        }
        for r in compound_rows[:req.top_compounds]
    ]

    compound_ids = list({c["id"] for c in compounds})
    target_rows = _collect_targets(db, compound_ids, asthma_only=False, limit=30)
    targets = []
    seen_genes = set()
    for r in target_rows:
        if r.gene in seen_genes:
            continue
        seen_genes.add(r.gene)
        targets.append({
            "gene": r.gene,
            "asthma_related": r.asthma_related,
            "activity_type": r.activity_type,
            "activity_value": r.activity_value,
            "activity_unit": r.activity_unit,
            "source_db": r.source_db,
            "compound_name": r.compound_name,
        })

    return StreamingResponse(
        _generate_ai_report_stream(
            prescription_name=prescription.name,
            herbs_data=herbs_data,
            compounds=compounds,
            targets=targets,
            api_key=api_key,
            provider=provider,
            base_url=base_url,
            model=model,
            min_prob=req.min_prob,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
