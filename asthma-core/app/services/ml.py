"""
PU Learning 模型加载与预测封装
- ccTCM 模型：19 维特征，PUBaggingClassifier
- HERB 模型：7 维特征，PUAsymmetricBagging
加载 joblib 模型需要先注册自定义类到 sys.modules
"""
import os
import sys
import numpy as np
import joblib
from typing import Optional

# ==================== 注册自定义 PU Learning 类到 sys.modules ====================
# joblib 反序列化时需要找到这些类，将它们注册到 sys.modules

from sklearn.base import BaseEstimator, ClassifierMixin, clone
from sklearn.ensemble import RandomForestClassifier


class PUBaggingClassifier(BaseEstimator, ClassifierMixin):
    """ccTCM 模型使用的 PU Bagging 分类器（1:1 对称抽样）"""

    def __init__(self, base_estimator=None, n_estimators=10, random_state=42):
        self.base_estimator = base_estimator
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.estimators_ = []

    def fit(self, X, y):
        rng = np.random.RandomState(self.random_state)
        pos_idx = np.where(y == 1)[0]
        unlabeled_idx = np.where(y == 0)[0]
        n_positive = len(pos_idx)
        n_sample = min(n_positive, len(unlabeled_idx))
        self.estimators_ = []
        for i in range(self.n_estimators):
            sampled_unlabeled = rng.choice(unlabeled_idx, size=n_sample, replace=False)
            train_idx = np.concatenate([pos_idx, sampled_unlabeled])
            X_train = X[train_idx]
            y_train = y[train_idx].copy()
            estimator = clone(self.base_estimator)
            estimator.fit(X_train, y_train)
            self.estimators_.append(estimator)
        return self

    def predict_proba(self, X):
        probas = np.zeros((X.shape[0], 2))
        for est in self.estimators_:
            probas += est.predict_proba(X)
        probas /= len(self.estimators_)
        return probas

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)


class PUAsymmetricBagging(BaseEstimator, ClassifierMixin):
    """HERB 模型使用的非对称 PU Bagging 分类器（1:3 抽样）"""

    def __init__(self, base_estimator=None, n_estimators=10, ratio=3, random_state=42):
        self.base_estimator = base_estimator
        self.n_estimators = n_estimators
        self.ratio = ratio
        self.random_state = random_state
        self.estimators_ = []

    def fit(self, X, y):
        rng = np.random.RandomState(self.random_state)
        pos_idx = np.where(y == 1)[0]
        unlabeled_idx = np.where(y == 0)[0]
        n_positive = len(pos_idx)
        n_sample = min(n_positive * self.ratio, len(unlabeled_idx))
        self.estimators_ = []
        for i in range(self.n_estimators):
            sampled_unlabeled = rng.choice(unlabeled_idx, size=n_sample, replace=False)
            train_idx = np.concatenate([pos_idx, sampled_unlabeled])
            X_train = X[train_idx]
            y_train = y[train_idx].copy()
            estimator = clone(self.base_estimator)
            estimator.fit(X_train, y_train)
            self.estimators_.append(estimator)
        return self

    def predict_proba(self, X):
        probas = np.zeros((X.shape[0], 2))
        for est in self.estimators_:
            probas += est.predict_proba(X)
        probas /= len(self.estimators_)
        return probas

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)


# 注册到 __main__ 模块，使 joblib.load 能找到这些类
sys.modules['__main__'].PUBaggingClassifier = PUBaggingClassifier
sys.modules['__main__'].PUAsymmetricBagging = PUAsymmetricBagging

# ==================== ccTCM 特征列定义（19 维） ====================
CCTCM_FEATURE_COLS = [
    'LogS', 'LogD', 'LogP', 'Pgp-inhibitor', 'Pgp-substrate',
    'F(20%)', 'Caco-2 Permeability', 'MDCK Permeability (cm/s)',
    'Num. H-bond acceptors', 'Num. H-bond donors', 'TPSA',
    'Num. Rotatable bonds', 'Num. Rings', 'MaxRing', 'nHet',
    'fChar', 'nRig', 'Flex', 'nStereo'
]

# ==================== HERB 特征列定义（7 维） ====================
HERB_FEATURE_COLS = [
    'MolWt', 'NumHAcceptors', 'NumHDonors',
    'MolLogP', 'NumRotatableBonds', 'Drug_likeness', 'OB_score'
]

# ==================== 模型懒加载 ====================

_pre_model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ml', 'pre-model')

_cctcm_model: Optional[PUBaggingClassifier] = None
_cctcm_scaler = None
_cctcm_imputer = None

_herb_model: Optional[PUAsymmetricBagging] = None
_herb_scaler = None
_herb_imputer = None


def load_cctcm_model():
    """
    懒加载 ccTCM PU Learning 模型（19维，含 scaler 和 imputer）

    打包文件 cctcm_pu_model.joblib 包含：
      - model:       PU Bagging 分类器
      - scaler:      StandardScaler（训练集拟合）
      - imputer:     SimpleImputer(median)（训练集拟合）
      - feature_cols: 特征列名列表
    """
    global _cctcm_model, _cctcm_scaler, _cctcm_imputer
    if _cctcm_model is not None:
        return _cctcm_model, _cctcm_scaler, _cctcm_imputer

    bundle_path = os.path.join(_pre_model_dir, 'cctcm_pu_model.joblib')
    bundle = joblib.load(bundle_path)
    _cctcm_model = bundle['model']
    _cctcm_scaler = bundle['scaler']
    _cctcm_imputer = bundle['imputer']

    return _cctcm_model, _cctcm_scaler, _cctcm_imputer


def load_herb_model():
    """懒加载 HERB PU Learning 模型（7维，含 scaler 和 imputer）"""
    global _herb_model, _herb_scaler, _herb_imputer
    if _herb_model is not None:
        return _herb_model, _herb_scaler, _herb_imputer

    model_path = os.path.join(_pre_model_dir, 'herb_pu_model.joblib')
    bundle = joblib.load(model_path)
    _herb_model = bundle['model']
    _herb_scaler = bundle['scaler']
    _herb_imputer = bundle['imputer']

    return _herb_model, _herb_scaler, _herb_imputer


def predict_cctcm(features: dict) -> float:
    """
    使用 ccTCM 模型预测入血概率
    features: dict，key 为特征名（CCTCM_FEATURE_COLS），value 为数值
    返回：入血概率 [0, 1]
    """
    model, scaler, imputer = load_cctcm_model()

    # 按特征列顺序构建特征向量
    X = np.array([[features.get(col, np.nan) for col in CCTCM_FEATURE_COLS]], dtype=float)
    X = np.where(np.isinf(X), np.nan, X)

    # 预处理：imputer → scaler
    X_imputed = imputer.transform(X)
    X_scaled = scaler.transform(X_imputed)

    # 预测
    prob = model.predict_proba(X_scaled)[0, 1]
    return float(prob)


def predict_herb(features: dict) -> float:
    """
    使用 HERB 模型预测入血概率
    features: dict，key 为特征名（HERB_FEATURE_COLS），value 为数值
    返回：入血概率 [0, 1]
    """
    model, scaler, imputer = load_herb_model()

    # 按特征列顺序构建特征向量
    X = np.array([[features.get(col, np.nan) for col in HERB_FEATURE_COLS]], dtype=float)
    X = np.where(np.isinf(X), np.nan, X)

    # 预处理：imputer → scaler
    X_imputed = imputer.transform(X)
    X_scaled = scaler.transform(X_imputed)

    # 预测
    prob = model.predict_proba(X_scaled)[0, 1]
    return float(prob)


# ==================== SMILES 自动预测 ====================

def predict_smiles(smiles: str, model_name: str = "cctcm",
                   adme_overrides: Optional[dict] = None) -> dict:
    """
    从 SMILES 自动计算特征并预测入血概率

    参数:
        smiles: SMILES 结构式
        model_name: 模型名 ("cctcm" 或 "herb")
        adme_overrides: 可选，用户校准的 ADME 实验值 {特征名: 数值}

    返回:
        dict: {
            'probability': float,
            'features_computed': dict,
            'rdkit_topology': dict,
            'adme_features': dict,
            'adme_estimated': bool
        }
    """
    from app.services.feature_engine import (
        parse_smiles, compute_all_19_features, compute_rdkit_features,
        compute_mw, apply_adme_overrides,
        RDKIT_TOPOLOGY_KEYS, ADME_KEYS
    )
    import numpy as np

    # 解析 SMILES
    mol = parse_smiles(smiles)
    if mol is None:
        raise ValueError("SMILES 解析失败，请检查输入的结构式")

    # 初始化前端展示用的分类特征（HERB 模型用不到，设空值）
    rdkit_topology = {}
    adme_feats = {}
    adme_estimated = True

    # 根据模型选择特征
    if model_name.lower() == "cctcm":
        features = compute_all_19_features(smiles)
        if features is None:
            raise ValueError("特征计算失败")

        # 应用 ADME 校准值（如果用户提供了）
        if adme_overrides:
            features = apply_adme_overrides(features, adme_overrides)
            adme_estimated = False

        feature_cols = CCTCM_FEATURE_COLS
        model, scaler, imputer = load_cctcm_model()

        # 提取分类特征供前端展示
        rdkit_topology = {k: features.get(k) for k in RDKIT_TOPOLOGY_KEYS}
        adme_feats = {k: features.get(k) for k in ADME_KEYS if k in features}

    elif model_name.lower() == "herb":
        rdkit_feat = compute_rdkit_features(mol)
        mw = compute_mw(smiles)
        features = {
            'MolWt': float(mw) if mw else np.nan,
            'NumHAcceptors': rdkit_feat.get('Num. H-bond acceptors', np.nan),
            'NumHDonors': rdkit_feat.get('Num. H-bond donors', np.nan),
            'MolLogP': rdkit_feat.get('LogP', np.nan),
            'NumRotatableBonds': rdkit_feat.get('Num. Rotatable bonds', np.nan),
            'Drug_likeness': np.nan,
            'OB_score': np.nan,
        }
        feature_cols = HERB_FEATURE_COLS
        model, scaler, imputer = load_herb_model()
    else:
        raise ValueError(f"不支持的模型: {model_name}")

    # 构建特征向量
    X = np.array([[features.get(col, np.nan) for col in feature_cols]], dtype=float)
    X = np.where(np.isinf(X), np.nan, X)

    # 预处理：imputer → scaler
    X_imputed = imputer.transform(X)
    X_scaled = scaler.transform(X_imputed)

    # 预测
    prob = model.predict_proba(X_scaled)[0, 1]

    return {
        'probability': float(prob),
        'features_computed': features,
        'rdkit_topology': rdkit_topology if model_name.lower() == "cctcm" else {},
        'adme_features': adme_feats if model_name.lower() == "cctcm" else {},
        'adme_estimated': adme_estimated if model_name.lower() == "cctcm" else True,
    }
