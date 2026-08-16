"""
PU Learning V2 模型加载与预测封装
- ccTCM 主力模型: cctcm_pu_model_v2.joblib（1043 维 = 19 特征 + Morgan 指纹 1024 位，
  RF300 + PU Bagging(1:1) × 30 轮，并集标签，工作阈值 0.56）
- HERB 兜底模型: herb_pu_model_v2.joblib（1037 维 = 13 描述符 + Morgan 指纹 1024 位，
  XGBoost + PU Bagging(1:5) × 30 轮，并集标签，工作阈值 0.62）

bundle 结构（joblib）: {model, scaler, imputer, feature_cols, config, test_metrics}
- 预处理顺序: imputer(中位数) → scaler → model.predict_proba
- 工作阈值存于 bundle['config']['threshold']

joblib 按模块名反序列化自定义 PU 类，pre-model/ 下同名瘦模块
（tune_cctcm_v2.py / pu_blood_prediction_herb_v2.py）提供类定义，
该目录已加入 sys.path，勿删除或重命名这些文件。
"""
import os
import sys
import threading
import numpy as np
import joblib
from typing import Optional

# ==================== 模型目录与 PU 类模块注册 ====================
_pre_model_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ml', 'pre-model'
)
if _pre_model_dir not in sys.path:
    sys.path.insert(0, _pre_model_dir)

# Morgan 指纹位数（与 feature_engine / 训练一致）
FP_BITS = 1024
# 无结构信息时（手动输入特征模式）的指纹回退：全零（训练时解析失败行同样为全零）
_ZERO_FP = np.zeros(FP_BITS, dtype=np.int8)

# ==================== ccTCM 手动输入/展示用特征列（19 维） ====================
CCTCM_FEATURE_COLS = [
    'LogS', 'LogD', 'LogP', 'Pgp-inhibitor', 'Pgp-substrate',
    'F(20%)', 'Caco-2 Permeability', 'MDCK Permeability (cm/s)',
    'Num. H-bond acceptors', 'Num. H-bond donors', 'TPSA',
    'Num. Rotatable bonds', 'Num. Rings', 'MaxRing', 'nHet',
    'fChar', 'nRig', 'Flex', 'nStereo'
]

# ==================== HERB 手动输入/展示用特征列（7 维，前端表单保持不变） ====================
# 完整 13 维特征见 feature_engine.HERB_FULL_FEATURE_COLS，
# 其余 6 个描述符由 SMILES 自动计算或 NaN → 中位数填补
HERB_FEATURE_COLS = [
    'MolWt', 'NumHAcceptors', 'NumHDonors',
    'MolLogP', 'NumRotatableBonds', 'Drug_likeness', 'OB_score'
]

# ==================== 模型懒加载（线程安全） ====================

_cctcm_bundle = None
_herb_bundle = None
_load_lock = threading.Lock()


def load_cctcm_model():
    """懒加载 ccTCM V2 模型 bundle（约 93MB，首次加载需数秒解压）"""
    global _cctcm_bundle
    if _cctcm_bundle is None:
        with _load_lock:
            if _cctcm_bundle is None:
                _cctcm_bundle = joblib.load(
                    os.path.join(_pre_model_dir, 'cctcm_pu_model_v2.joblib')
                )
    return _cctcm_bundle


def load_herb_model():
    """懒加载 HERB V2 模型 bundle（约 3.5MB）"""
    global _herb_bundle
    if _herb_bundle is None:
        with _load_lock:
            if _herb_bundle is None:
                _herb_bundle = joblib.load(
                    os.path.join(_pre_model_dir, 'herb_pu_model_v2.joblib')
                )
    return _herb_bundle


def get_model_threshold(model_name: str) -> float:
    """获取模型工作阈值（ccTCM 0.56 / HERB 0.62，来自 bundle config）"""
    if model_name.lower() == 'cctcm':
        bundle = load_cctcm_model()
    elif model_name.lower() == 'herb':
        bundle = load_herb_model()
    else:
        raise ValueError(f"不支持的模型: {model_name}")
    return float(bundle.get('config', {}).get('threshold', 0.5))


def _predict_bundle(bundle: dict, features: dict, fp: np.ndarray):
    """
    按 bundle 的 feature_cols 组装单行特征矩阵：
    提供的特征填入，未提供的特征列保持 NaN（由 imputer 中位数填补），
    指纹列 FP_0..FP_1023 填入 fp 数组。
    返回 (入血概率, 工作阈值)
    """
    cols = bundle['feature_cols']
    col_idx = {c: i for i, c in enumerate(cols)}
    X = np.full((1, len(cols)), np.nan, dtype=float)

    for key, val in features.items():
        i = col_idx.get(key)
        if i is not None and val is not None:
            try:
                X[0, i] = float(val)
            except (TypeError, ValueError):
                pass

    for j in range(FP_BITS):
        i = col_idx.get(f'FP_{j}')
        if i is not None:
            X[0, i] = fp[j]

    X = np.where(np.isinf(X), np.nan, X)
    X = bundle['scaler'].transform(bundle['imputer'].transform(X))
    prob = float(bundle['model'].predict_proba(X)[0, 1])
    thr = float(bundle.get('config', {}).get('threshold', 0.5))
    return prob, thr


def predict_cctcm(features: dict) -> float:
    """
    使用 ccTCM V2 模型预测入血概率（手动输入特征模式，无 SMILES）。
    features: dict，key 为 19 个特征名（CCTCM_FEATURE_COLS），value 为数值，
    未提供的特征 NaN → 训练集中位数；指纹无结构信息按全零处理。
    返回：入血概率 [0, 1]
    """
    prob, _ = _predict_bundle(load_cctcm_model(), features, _ZERO_FP)
    return prob


def predict_herb(features: dict) -> float:
    """
    使用 HERB V2 模型预测入血概率（手动输入特征模式，无 SMILES）。
    features: dict，key 为 HERB_FEATURE_COLS 中的特征名；
    其余 6 个描述符（TPSA/MolMR/FractionCSP3/环数×2/QED）无 SMILES 不可算，
    NaN → 中位数；指纹按全零处理。
    返回：入血概率 [0, 1]
    """
    prob, _ = _predict_bundle(load_herb_model(), features, _ZERO_FP)
    return prob


# ==================== SMILES 自动预测 ====================

def predict_smiles_batch(smiles_list: list, model_name: str = "cctcm") -> list:
    """
    批量 SMILES 预测（矩阵化：所有行一次性过 imputer/scaler/模型，
    比逐条调用快 1-2 个数量级，ccTCM 500 条约 10-30 秒）。

    返回与输入等长的列表，每项为 predict_smiles 的结果 dict；
    无效 SMILES 的项为 None（由调用方决定如何标记错误）。
    """
    from app.services.feature_engine import (
        parse_smiles, compute_all_19_features, compute_herb_features,
        morgan_fp, RDKIT_TOPOLOGY_KEYS, ADME_KEYS
    )

    if model_name.lower() == "cctcm":
        bundle = load_cctcm_model()
    elif model_name.lower() == "herb":
        bundle = load_herb_model()
    else:
        raise ValueError(f"不支持的模型: {model_name}")

    cols = bundle['feature_cols']
    col_idx = {c: i for i, c in enumerate(cols)}

    mols = [parse_smiles(s) for s in smiles_list]
    valid_idx = [i for i, m in enumerate(mols) if m is not None]

    results = [None] * len(smiles_list)
    if not valid_idx:
        return results

    X = np.full((len(valid_idx), len(cols)), np.nan, dtype=float)
    feats_list = []
    for row, i in enumerate(valid_idx):
        mol = mols[i]
        if model_name.lower() == "cctcm":
            feats = compute_all_19_features(smiles_list[i])
        else:
            feats = compute_herb_features(mol)
        if feats is None:
            feats = {}
        feats_list.append(feats)
        for key, val in feats.items():
            j = col_idx.get(key)
            if j is not None and val is not None:
                try:
                    X[row, j] = float(val)
                except (TypeError, ValueError):
                    pass
        fp = morgan_fp(mol)
        for b in range(FP_BITS):
            j = col_idx.get(f'FP_{b}')
            if j is not None:
                X[row, j] = fp[b]

    X = np.where(np.isinf(X), np.nan, X)
    X = bundle['scaler'].transform(bundle['imputer'].transform(X))
    probs = bundle['model'].predict_proba(X)[:, 1]
    thr = float(bundle.get('config', {}).get('threshold', 0.5))

    for row, i in enumerate(valid_idx):
        feats = feats_list[row]
        prob = float(probs[row])
        if model_name.lower() == "cctcm":
            rdkit_topology = {k: feats.get(k) for k in RDKIT_TOPOLOGY_KEYS}
            adme_feats = {k: feats.get(k) for k in ADME_KEYS if k in feats}
        else:
            rdkit_topology = {}
            adme_feats = {}
        results[i] = {
            'probability': prob,
            'threshold': thr,
            'pred': int(prob >= thr),
            'features_computed': feats,
            'rdkit_topology': rdkit_topology,
            'adme_features': adme_feats,
            'adme_estimated': True,
        }
    return results

def predict_smiles(smiles: str, model_name: str = "cctcm",
                   adme_overrides: Optional[dict] = None) -> dict:
    """
    从 SMILES 自动计算特征（含 Morgan 指纹）并用 V2 模型预测入血概率

    参数:
        smiles: SMILES 结构式
        model_name: 模型名 ("cctcm" 或 "herb")
        adme_overrides: 可选，用户校准的 ADME 实验值 {特征名: 数值}（仅 ccTCM）

    返回:
        dict: {
            'probability': float,        # 入血概率
            'threshold': float,          # 模型工作阈值
            'pred': int,                 # 1=预测入血（prob >= threshold）
            'features_computed': dict,   # 特征快照（ccTCM 19 维 / HERB 13 维）
            'rdkit_topology': dict,      # ccTCM 拓扑特征（前端展示用）
            'adme_features': dict,       # ccTCM ADME 特征（前端展示用）
            'adme_estimated': bool       # ADME 是否为算法推算
        }
    """
    from app.services.feature_engine import (
        parse_smiles, compute_all_19_features, compute_herb_features,
        morgan_fp, apply_adme_overrides, RDKIT_TOPOLOGY_KEYS, ADME_KEYS
    )

    mol = parse_smiles(smiles)
    if mol is None:
        raise ValueError("SMILES 解析失败，请检查输入的结构式")

    fp = morgan_fp(mol)

    if model_name.lower() == "cctcm":
        features = compute_all_19_features(smiles)
        if features is None:
            raise ValueError("特征计算失败")

        adme_estimated = True
        if adme_overrides:
            features = apply_adme_overrides(features, adme_overrides)
            adme_estimated = False

        rdkit_topology = {k: features.get(k) for k in RDKIT_TOPOLOGY_KEYS}
        adme_feats = {k: features.get(k) for k in ADME_KEYS if k in features}
        bundle = load_cctcm_model()

    elif model_name.lower() == "herb":
        features = compute_herb_features(mol)
        if features is None:
            raise ValueError("特征计算失败")
        rdkit_topology = {}
        adme_feats = {}
        adme_estimated = True
        bundle = load_herb_model()

    else:
        raise ValueError(f"不支持的模型: {model_name}")

    prob, thr = _predict_bundle(bundle, features, fp)

    return {
        'probability': prob,
        'threshold': thr,
        'pred': int(prob >= thr),
        'features_computed': features,
        'rdkit_topology': rdkit_topology,
        'adme_features': adme_feats,
        'adme_estimated': adme_estimated,
    }
