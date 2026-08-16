"""
入血预测路由
- GET  /models                    获取模型列表及特征描述（前端动态渲染表单）
- POST /predict/cctcm             ccTCM 模型预测（手动输入特征）
- POST /predict/herb              HERB 模型预测（手动输入特征）
- POST /predict/smiles            SMILES 自动计算特征并预测（单条）
- POST /predict/smiles/batch      批量 SMILES 预测
- POST /predict/smiles/upload     文件上传批量预测（.xlsx/.csv）
- GET  /predict/smiles/download/{task_id}  下载批量预测结果文件
"""
import os
import uuid
import tempfile
import pandas as pd
from datetime import datetime, timedelta
from fastapi import APIRouter, UploadFile, File
from app.schemas import (
    ResponseModel, FeatureFieldInfo, ModelInfoData,
    PredictRequest, PredictResultData,
    SmilesPredictRequest, SmilesPredictResultData,
    BatchSmilesPredictRequest, BatchSmilesPredictResultData
)
from app.services.ml import (
    predict_cctcm, predict_herb, predict_smiles, predict_smiles_batch,
    get_model_threshold, CCTCM_FEATURE_COLS, HERB_FEATURE_COLS
)
from app.services.feature_engine import (
    compute_mw, get_core_features, validate_smiles
)

router = APIRouter()


# ==================== 特征中文映射 ====================

CCTCM_FEATURE_LABELS = {
    'LogS': ('LogS（溶解度）', 'log mol/L'),
    'LogD': ('LogD（分布系数）', 'pH7.4'),
    'LogP': ('LogP（脂水分配系数）', ''),
    'Pgp-inhibitor': ('P-糖蛋白抑制剂', '0/1'),
    'Pgp-substrate': ('P-糖蛋白底物', '0/1'),
    'F(20%)': ('20%吸收分数', '%'),
    'Caco-2 Permeability': ('Caco-2 渗透性', 'cm/s'),
    'MDCK Permeability (cm/s)': ('MDCK 渗透性', 'cm/s'),
    'Num. H-bond acceptors': ('氢键受体数', ''),
    'Num. H-bond donors': ('氢键供体数', ''),
    'TPSA': ('拓扑极性表面积', 'Å²'),
    'Num. Rotatable bonds': ('可旋转键数', ''),
    'Num. Rings': ('环数', ''),
    'MaxRing': ('最大环大小', ''),
    'nHet': ('杂原子数', ''),
    'fChar': ('形式电荷', ''),
    'nRig': ('刚性键数', ''),
    'Flex': ('柔韧性', ''),
    'nStereo': ('立体中心数', ''),
}

HERB_FEATURE_LABELS = {
    'MolWt': ('分子量', 'Da'),
    'NumHAcceptors': ('氢键受体数', ''),
    'NumHDonors': ('氢键供体数', ''),
    'MolLogP': ('LogP', ''),
    'NumRotatableBonds': ('可旋转键数', ''),
    'Drug_likeness': ('类药性评分', ''),
    'OB_score': ('口服生物利用度评分', ''),
}


def prob_to_level(prob: float, threshold: float = None) -> str:
    """
    概率转等级标签。
    V2 模型按工作阈值动态分档：≥ threshold+0.2 高 / ≥ threshold 中 / 其余低；
    未提供阈值时沿用旧固定分档（≥0.85 高 / ≥0.5 中）。
    """
    if threshold is not None:
        if prob >= threshold + 0.2:
            return "高"
        elif prob >= threshold:
            return "中"
        else:
            return "低"
    if prob >= 0.85:
        return "高"
    elif prob >= 0.5:
        return "中"
    else:
        return "低"


@router.get("/models")
async def get_model_info():
    """
    获取两个 PU Learning 模型的信息及特征描述
    前端据此动态渲染输入表单
    """
    cctcm_features = [
        FeatureFieldInfo(
            name=col,
            label=CCTCM_FEATURE_LABELS.get(col, (col, ''))[0],
            unit=CCTCM_FEATURE_LABELS.get(col, (col, ''))[1] or None,
        )
        for col in CCTCM_FEATURE_COLS
    ]

    herb_features = [
        FeatureFieldInfo(
            name=col,
            label=HERB_FEATURE_LABELS.get(col, (col, ''))[0],
            unit=HERB_FEATURE_LABELS.get(col, (col, ''))[1] or None,
        )
        for col in HERB_FEATURE_COLS
    ]

    data = [
        ModelInfoData(
            model_name="cctcm",
            description="ccTCM 三表融合 PU Learning 模型 V2（19维特征 + Morgan指纹，对称抽样 1:1，工作阈值 0.56）",
            feature_count=len(CCTCM_FEATURE_COLS),
            features=cctcm_features
        ),
        ModelInfoData(
            model_name="herb",
            description="HERB 中药数据库 PU Learning 模型 V2（7维输入特征，服务端自动补算描述符与Morgan指纹，非对称抽样 1:5，工作阈值 0.62）",
            feature_count=len(HERB_FEATURE_COLS),
            features=herb_features
        )
    ]

    return ResponseModel(data=data)


@router.post("/predict/cctcm")
async def predict_with_cctcm(req: PredictRequest):
    """
    使用 ccTCM PU Learning 模型预测未知化合物的入血概率
    用户需填写 19 个特征值，未填写的特征将使用训练集中位数填补
    """
    try:
        prob = predict_cctcm(req.features)
    except Exception as e:
        return ResponseModel(code=500, message=f"ccTCM 模型预测失败: {str(e)}", data=None)

    threshold = get_model_threshold('cctcm')
    data = PredictResultData(
        compound_name=req.compound_name,
        model_name="ccTCM PU Learning",
        probability=round(prob, 4),
        level=prob_to_level(prob, threshold),
        features_used=list(req.features.keys()),
        threshold=round(threshold, 4),
        pred=int(prob >= threshold)
    )

    return ResponseModel(data=data)


@router.post("/predict/herb")
async def predict_with_herb(req: PredictRequest):
    """
    使用 HERB PU Learning 模型预测未知化合物的入血概率
    用户需填写 7 个特征值，未填写的特征将使用训练集中位数填补
    """
    try:
        prob = predict_herb(req.features)
    except Exception as e:
        return ResponseModel(code=500, message=f"HERB 模型预测失败: {str(e)}", data=None)

    threshold = get_model_threshold('herb')
    data = PredictResultData(
        compound_name=req.compound_name,
        model_name="HERB PU Learning",
        probability=round(prob, 4),
        level=prob_to_level(prob, threshold),
        features_used=list(req.features.keys()),
        threshold=round(threshold, 4),
        pred=int(prob >= threshold)
    )

    return ResponseModel(data=data)


# ==================== SMILES 自动预测 ====================

# 临时文件存储目录
_TEMP_DIR = os.path.join(tempfile.gettempdir(), "smiles_batch_results")
os.makedirs(_TEMP_DIR, exist_ok=True)


def _build_smiles_result(smiles: str, compound_name: str,
                         model_name: str, prob: float,
                         features_computed: dict,
                         rdkit_topology: dict = None,
                         adme_features: dict = None,
                         adme_estimated: bool = True,
                         threshold: float = None,
                         pred: int = None) -> SmilesPredictResultData:
    """构建 SMILES 预测结果对象"""
    mw = compute_mw(smiles)
    core_feats = get_core_features(features_computed)

    # 将 NaN 转为 None 以便 JSON 序列化
    import math

    def _clean_nan(d):
        if not d:
            return {}
        result = {}
        for k, v in d.items():
            if isinstance(v, float) and math.isnan(v):
                result[k] = None
            else:
                result[k] = v
        return result

    clean_features = _clean_nan(features_computed)
    clean_rdkit = _clean_nan(rdkit_topology or {})
    clean_adme = _clean_nan(adme_features or {})

    return SmilesPredictResultData(
        smiles=smiles,
        compound_name=compound_name,
        model_name=model_name,
        probability=round(prob, 4),
        level=prob_to_level(prob, threshold),
        mw=mw,
        features_computed=clean_features,
        rdkit_topology_features=clean_rdkit,
        adme_features=clean_adme,
        adme_estimated=adme_estimated,
        threshold=round(threshold, 4) if threshold is not None else None,
        pred=pred,
        core_features=[
            {
                'name': f['name'],
                'label': f['label'],
                'unit': f['unit'],
                'value': f['value'] if not (isinstance(f.get('value'), float)
                            and math.isnan(f.get('value', 0))) else None
            }
            for f in core_feats
        ]
    )


@router.post("/predict/smiles")
async def predict_with_smiles(req: SmilesPredictRequest):
    """
    输入 SMILES 结构式，后端自动计算 19 维特征并预测入血概率
    """
    # 校验 SMILES
    if not req.smiles or not req.smiles.strip():
        return ResponseModel(code=422, message="SMILES 不能为空", data=None)

    if not validate_smiles(req.smiles):
        return ResponseModel(code=422, message="SMILES 解析失败，请检查结构式格式", data=None)

    try:
        result = predict_smiles(req.smiles, req.model_name, adme_overrides=req.adme_overrides)
    except ValueError as e:
        return ResponseModel(code=422, message=str(e), data=None)
    except Exception as e:
        return ResponseModel(code=500, message=f"预测失败: {str(e)}", data=None)

    data = _build_smiles_result(
        smiles=req.smiles.strip(),
        compound_name=req.compound_name or "",
        model_name=req.model_name,
        prob=result['probability'],
        features_computed=result['features_computed'],
        rdkit_topology=result.get('rdkit_topology'),
        adme_features=result.get('adme_features'),
        adme_estimated=result.get('adme_estimated', True),
        threshold=result.get('threshold'),
        pred=result.get('pred')
    )

    return ResponseModel(data=data)


@router.post("/predict/smiles/batch")
async def batch_predict_smiles(req: BatchSmilesPredictRequest):
    """
    批量 SMILES 预测（JSON 数组方式）
    """
    if not req.smiles_list:
        return ResponseModel(code=422, message="SMILES 列表不能为空", data=None)

    if len(req.smiles_list) > 500:
        return ResponseModel(code=422, message="单次批量预测最多 500 条", data=None)

    # 矩阵化批量预测（V2 大模型逐条调用过慢）
    try:
        batch_results = predict_smiles_batch(req.smiles_list, req.model_name)
    except ValueError as e:
        return ResponseModel(code=422, message=str(e), data=None)
    except Exception as e:
        return ResponseModel(code=500, message=f"批量预测失败: {str(e)}", data=None)

    results = []
    errors = []
    compound_names = req.compound_names or []

    for idx, r in enumerate(batch_results):
        smiles = req.smiles_list[idx]
        cname = compound_names[idx] if idx < len(compound_names) else ""
        if r is None:
            errors.append({"smiles": smiles, "compound_name": cname, "error": "SMILES 解析失败"})
            continue
        results.append(_build_smiles_result(
            smiles=smiles.strip(), compound_name=cname,
            model_name=req.model_name, prob=r['probability'],
            features_computed=r['features_computed'],
            rdkit_topology=r.get('rdkit_topology'),
            adme_features=r.get('adme_features'),
            adme_estimated=r.get('adme_estimated', True),
            threshold=r.get('threshold'),
            pred=r.get('pred')
        ))

    data = BatchSmilesPredictResultData(
        total=len(req.smiles_list),
        success=len(results),
        failed=len(errors),
        results=results,
        errors=errors
    )

    return ResponseModel(data=data)


@router.post("/predict/smiles/upload")
async def upload_and_predict(
    file: UploadFile = File(...),
    model_name: str = "cctcm"
):
    """
    上传 .xlsx / .csv 文件，自动检测 SMILES 列并批量预测
    返回 task_id 供下载结果
    """
    if not file.filename:
        return ResponseModel(code=422, message="文件名为空", data=None)

    # 读取文件
    content = await file.read()
    try:
        if file.filename.lower().endswith('.csv'):
            import io
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.lower().endswith(('.xlsx', '.xls')):
            import io
            df = pd.read_excel(io.BytesIO(content))
        else:
            return ResponseModel(code=422, message="仅支持 .csv 和 .xlsx 格式", data=None)
    except Exception as e:
        return ResponseModel(code=422, message=f"文件解析失败: {str(e)}", data=None)

    # 检测 SMILES 列（不区分大小写）
    smiles_col = None
    for col in df.columns:
        if str(col).strip().lower() in ('smiles', 'smile', 'smiles结构式', '结构式', 'smiles结构'):
            smiles_col = col
            break

    if smiles_col is None:
        return ResponseModel(
            code=422,
            message="未找到 SMILES 列。请确保文件包含名为 'SMILES' 的列（不区分大小写）",
            data=None
        )

    # 提取 SMILES 列
    smiles_list = df[smiles_col].dropna().astype(str).str.strip()
    smiles_list = smiles_list[smiles_list != ''].tolist()

    if not smiles_list:
        return ResponseModel(code=422, message="SMILES 列为空", data=None)

    # 批量预测
    results = []
    compound_names = []

    # 尝试获取化合物名列
    name_col = None
    for col in df.columns:
        if str(col).strip().lower() in ('name', 'compound', '名称', '化合物', '化合物名称', 'compound_name'):
            name_col = col
            break

    for idx, row in df.iterrows():
        s = str(row[smiles_col]).strip() if pd.notna(row[smiles_col]) else ""
        n = str(row[name_col]).strip() if name_col and pd.notna(row.get(name_col)) else ""
        if s:
            smiles_list.append(s)
            compound_names.append(n)

    # 去重保留顺序
    seen = set()
    unique_smiles = []
    unique_names = []
    for s, n in zip(smiles_list, compound_names):
        if s not in seen:
            seen.add(s)
            unique_smiles.append(s)
            unique_names.append(n)

    # 矩阵化批量预测（V2 大模型逐条调用过慢）
    try:
        batch_results = predict_smiles_batch(unique_smiles, model_name)
    except ValueError as e:
        return ResponseModel(code=422, message=str(e), data=None)
    except Exception as e:
        return ResponseModel(code=500, message=f"批量预测失败: {str(e)}", data=None)

    pred_results = []
    errors = []
    for idx, r in enumerate(batch_results):
        smiles = unique_smiles[idx]
        cname = unique_names[idx] if idx < len(unique_names) else ""
        if r is None:
            errors.append({
                'smiles': smiles,
                'compound_name': cname,
                'error': 'SMILES 解析失败'
            })
            continue
        pred_results.append({
            'smiles': smiles,
            'compound_name': cname,
            'probability': round(r['probability'], 4),
            'level': prob_to_level(r['probability'], r.get('threshold')),
            'mw': compute_mw(smiles),
            'threshold': round(r['threshold'], 4) if r.get('threshold') is not None else None,
            'pred': r.get('pred'),
        })

    # 合并到原 DataFrame
    prob_map = {}
    level_map = {}
    mw_map = {}
    for r in pred_results:
        if r:
            prob_map[r['smiles']] = r['probability']
            level_map[r['smiles']] = r['level']
            mw_map[r['smiles']] = r['mw']

    df['预测入血概率'] = df[smiles_col].astype(str).str.strip().map(
        lambda s: prob_map.get(s, None)
    )
    df['预测等级'] = df[smiles_col].astype(str).str.strip().map(
        lambda s: level_map.get(s, None)
    )
    df['分子量MW'] = df[smiles_col].astype(str).str.strip().map(
        lambda s: mw_map.get(s, None)
    )

    # 生成结果文件
    task_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_filename = f"batch_predict_{timestamp}_{task_id}.xlsx"
    result_path = os.path.join(_TEMP_DIR, result_filename)
    df.to_excel(result_path, index=False)

    # 同时生成 CSV
    csv_path = result_path.replace('.xlsx', '.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    data = {
        'task_id': task_id,
        'total': len(unique_smiles),
        'success': len([r for r in pred_results if r]),
        'failed': len(errors),
        'errors': errors[:20],  # 只返回前 20 个错误
        'download_filename_xlsx': result_filename,
        'download_filename_csv': result_filename.replace('.xlsx', '.csv'),
        'preview': pred_results[:10],  # 前 10 条预览
    }

    return ResponseModel(data=data)


@router.get("/predict/smiles/download/{filename}")
async def download_result(filename: str):
    """下载批量预测结果文件"""
    from fastapi.responses import FileResponse

    # 安全检查：防止路径遍历
    if '/' in filename or '\\' in filename or '..' in filename:
        return ResponseModel(code=422, message="非法文件名", data=None)

    file_path = os.path.join(_TEMP_DIR, filename)
    if not os.path.exists(file_path):
        return ResponseModel(code=404, message="文件不存在或已过期，请重新上传预测", data=None)

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )
