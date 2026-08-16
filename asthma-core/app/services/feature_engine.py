# -*- coding: utf-8 -*-
"""
SMILES → 特征自动计算引擎（V2 模型配套）
- 11 个 RDKit 拓扑特征 + LogP：与 V2 训练脚本
  (入血预测/cctcm2.0_v2/pu_blood_prediction_v2.py rdkit_fill_and_fingerprint)
  的定义逐项对齐，定义差异会导致预测失真，勿随意改动：
    nHet = 杂原子数(CalcNumHeteroatoms)；fChar = 净形式电荷(GetFormalCharge)；
    nRig = 总键数 - 可旋转键；Flex = 可旋转键 / 总键数（pkCSM 同型定义）；
    nStereo = CalcNumAtomStereoCenters
- 7 个 ADME 特征：RDKit 无法直接计算，留 NaN 由模型 imputer 填补
- Morgan 指纹 1024 位（radius=2）：V2 模型（ccTCM 1043 维 / HERB 1037 维）必需
- HERB 13 个描述符：11 个 RDKit 可算，Drug_likeness / OB_score 来自 HERB 库留 NaN
"""
import numpy as np
from typing import Optional, Dict
from rdkit import Chem
from rdkit.Chem import Descriptors, Crippen, rdMolDescriptors, QED
from rdkit import RDLogger

# 关闭 RDKit 冗余日志
RDLogger.DisableLog('rdApp.*')

# Morgan 指纹位数（与 V2 训练一致）
FP_BITS = 1024

# ==================== 19 维特征列名（与模型训练一致） ====================
CCTCM_FEATURE_COLS = [
    'LogS', 'LogD', 'LogP', 'Pgp-inhibitor', 'Pgp-substrate',
    'F(20%)', 'Caco-2 Permeability', 'MDCK Permeability (cm/s)',
    'Num. H-bond acceptors', 'Num. H-bond donors', 'TPSA',
    'Num. Rotatable bonds', 'Num. Rings', 'MaxRing', 'nHet',
    'fChar', 'nRig', 'Flex', 'nStereo'
]


# ==================== 辅助计算函数 ====================

def _max_ring_size(mol) -> float:
    """最大环大小（原子数）"""
    ring_info = mol.GetRingInfo()
    if not ring_info.AtomRings():
        return 0.0
    return float(max(len(r) for r in ring_info.AtomRings()))


# ==================== SMILES 解析 ====================

def parse_smiles(smiles: str):
    """
    解析 SMILES 字符串，返回 RDKit Mol 对象
    返回 None 表示解析失败
    """
    if not smiles or not isinstance(smiles, str):
        return None
    smiles = smiles.strip()
    if not smiles:
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol
    except Exception:
        return None


def validate_smiles(smiles: str) -> bool:
    """校验 SMILES 是否有效"""
    return parse_smiles(smiles) is not None


# ==================== 19 维特征计算 ====================

def compute_rdkit_features(mol) -> Dict[str, float]:
    """
    用 RDKit 计算 11 个拓扑特征 + LogP
    定义与 V2 训练脚本逐项对齐（rdkit_fill_and_fingerprint）
    """
    n_bonds = mol.GetNumBonds()
    n_rot = rdMolDescriptors.CalcNumRotatableBonds(mol)
    features = {
        # ---- 11 个拓扑特征 ----
        'Num. H-bond acceptors': float(rdMolDescriptors.CalcNumHBA(mol)),
        'Num. H-bond donors': float(rdMolDescriptors.CalcNumHBD(mol)),
        'TPSA': float(rdMolDescriptors.CalcTPSA(mol)),
        'Num. Rotatable bonds': float(n_rot),
        'Num. Rings': float(rdMolDescriptors.CalcNumRings(mol)),
        'MaxRing': _max_ring_size(mol),
        'nHet': float(rdMolDescriptors.CalcNumHeteroatoms(mol)),
        'fChar': float(Chem.GetFormalCharge(mol)),
        'nRig': float(n_bonds - n_rot),
        'Flex': (n_rot / n_bonds) if n_bonds > 0 else 0.0,
        'nStereo': float(rdMolDescriptors.CalcNumAtomStereoCenters(mol)),
    }

    # ---- LogP（RDKit Crippen 估算）----
    features['LogP'] = float(Crippen.MolLogP(mol))

    return features


def compute_adme_features(smiles: str) -> Dict[str, float]:
    """
    计算 7 个 ADME 特征
    RDKit 无法直接计算这些特征，返回 NaN
    模型 imputer 会用训练集中位数填补

    未来可通过安装 mordred / TDC / ADMETLab 等库来补全
    """
    return {
        'LogS': np.nan,
        'LogD': np.nan,
        'Pgp-inhibitor': np.nan,
        'Pgp-substrate': np.nan,
        'F(20%)': np.nan,
        'Caco-2 Permeability': np.nan,
        'MDCK Permeability (cm/s)': np.nan,
    }


def compute_all_19_features(smiles: str) -> Optional[Dict[str, float]]:
    """
    从 SMILES 计算 19 维特征向量

    参数:
        smiles: SMILES 结构式字符串

    返回:
        dict: 19 个特征名 → 数值的映射，None 表示 SMILES 解析失败
    """
    mol = parse_smiles(smiles)
    if mol is None:
        return None

    rdkit_features = compute_rdkit_features(mol)
    adme_features = compute_adme_features(smiles)

    # 合并，确保 19 个特征都有
    features = {}
    for col in CCTCM_FEATURE_COLS:
        if col in rdkit_features:
            features[col] = rdkit_features[col]
        elif col in adme_features:
            features[col] = adme_features[col]
        else:
            features[col] = np.nan

    return features


# ==================== Morgan 指纹（V2 模型必需） ====================

def morgan_fp(mol) -> np.ndarray:
    """
    计算 1024 位 Morgan 指纹（radius=2），与 V2 训练一致。
    入参为 RDKit Mol 对象；失败/无效分子返回全零。
    """
    if mol is None:
        return np.zeros(FP_BITS, dtype=np.int8)
    fp = rdMolDescriptors.GetMorganFingerprintAsBitVect(mol, 2, nBits=FP_BITS)
    return np.array(fp, dtype=np.int8)


# ==================== HERB 13 维描述符（V2） ====================

# HERB 模型完整特征列（13 描述符；Drug_likeness / OB_score 来自 HERB 库，无数据时 NaN）
HERB_FULL_FEATURE_COLS = [
    'MolWt', 'NumHAcceptors', 'NumHDonors', 'MolLogP',
    'NumRotatableBonds', 'Drug_likeness', 'OB_score',
    'TPSA', 'MolMR', 'FractionCSP3',
    'NumAromaticRings', 'NumAliphaticRings', 'QED'
]


def compute_herb_features(mol) -> Optional[Dict[str, float]]:
    """
    用 RDKit 计算 HERB V2 模型的 13 个描述符。
    定义与训练脚本 compute_extended_features 对齐。
    Drug_likeness / OB_score 来自 HERB 数据库，无数据时为 NaN
    （由模型 imputer 中位数填补，预测偏保守，属正常兜底模式）。
    返回 None 表示分子无效。
    """
    if mol is None:
        return None
    return {
        'MolWt': float(Descriptors.MolWt(mol)),
        'NumHAcceptors': float(rdMolDescriptors.CalcNumHBA(mol)),
        'NumHDonors': float(rdMolDescriptors.CalcNumHBD(mol)),
        'MolLogP': float(Crippen.MolLogP(mol)),
        'NumRotatableBonds': float(rdMolDescriptors.CalcNumRotatableBonds(mol)),
        'Drug_likeness': np.nan,
        'OB_score': np.nan,
        'TPSA': float(Descriptors.TPSA(mol)),
        'MolMR': float(Descriptors.MolMR(mol)),
        'FractionCSP3': float(Descriptors.FractionCSP3(mol)),
        'NumAromaticRings': float(Descriptors.NumAromaticRings(mol)),
        'NumAliphaticRings': float(Descriptors.NumAliphaticRings(mol)),
        'QED': float(QED.qed(mol)),
    }


def features_to_vector(features: Dict[str, float]) -> np.ndarray:
    """将特征 dict 转换为按 CCTCM_FEATURE_COLS 顺序排列的 numpy 向量"""
    vec = np.array([[features.get(col, np.nan) for col in CCTCM_FEATURE_COLS]],
                   dtype=float)
    # 将 inf 替换为 nan
    vec = np.where(np.isinf(vec), np.nan, vec)
    return vec


def validate_features(features: Dict[str, float]) -> bool:
    """校验特征字典是否包含所有 19 个特征名"""
    return all(col in features for col in CCTCM_FEATURE_COLS)


# ==================== 特征分类（前端展示用） ====================

RDKIT_TOPOLOGY_KEYS = [
    'Num. H-bond acceptors', 'Num. H-bond donors', 'TPSA',
    'Num. Rotatable bonds', 'Num. Rings', 'MaxRing', 'nHet',
    'fChar', 'nRig', 'Flex', 'nStereo'
]

ADME_KEYS = [
    'LogS', 'LogD', 'LogP', 'Pgp-inhibitor', 'Pgp-substrate',
    'F(20%)', 'Caco-2 Permeability', 'MDCK Permeability (cm/s)'
]


# ==================== ADME 校准 ====================

def apply_adme_overrides(features: Dict[str, float],
                         overrides: Dict[str, Optional[float]]) -> Dict[str, float]:
    """
    用用户提供的实验值覆盖 ADME 特征的算法推算值

    参数:
        features: 原始 19 维特征 dict
        overrides: 用户校准值，key 为特征名，value 为数值或 None（不清除）

    返回:
        更新后的特征 dict
    """
    if not overrides:
        return features

    result = dict(features)
    for key, val in overrides.items():
        if key in result and val is not None:
            result[key] = float(val)
    return result

CORE_DISPLAY_FEATURES = [
    ('LogP', 'LogP（脂水分配系数）', ''),
    ('TPSA', '拓扑极性表面积', 'Å²'),
    ('Num. H-bond acceptors', '氢键受体数', ''),
    ('Num. H-bond donors', '氢键供体数', ''),
    ('nHet', '杂原子数', ''),
    ('Num. Rings', '环数', ''),
]


def get_core_features(features: Dict[str, float]) -> list:
    """提取核心展示特征（前端紧凑展示用）"""
    result = []
    for key, label, unit in CORE_DISPLAY_FEATURES:
        result.append({
            'name': key,
            'label': label,
            'unit': unit,
            'value': features.get(key, None)
        })
    return result


# ==================== 分子量（MW）计算（前端展示用） ====================

def compute_mw(smiles: str) -> Optional[float]:
    """计算分子量"""
    mol = parse_smiles(smiles)
    if mol is None:
        return None
    return round(Descriptors.MolWt(mol), 2)
