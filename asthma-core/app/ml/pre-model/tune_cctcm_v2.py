# -*- coding: utf-8 -*-
"""
ccTCM V2 PU Learning 模型类的部署副本（瘦模块）。

来源：入血预测/cctcm2.0_v2/tune_cctcm_v2.py 的 PUAsymmetricBagging 类，
逐字复制。joblib 模型（cctcm_pu_model_v2.joblib）按模块名
`tune_cctcm_v2.PUAsymmetricBagging` 反序列化，本文件必须以该模块名可导入。
若上游类定义变更并重训模型，需同步更新此副本。
"""
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin, clone


class PUAsymmetricBagging(BaseEstimator, ClassifierMixin):
    """每轮全部正样本 + ratio 倍数量未标记样本；ratio=1 ≡ V1/V2 等量抽样。"""

    def __init__(self, base_estimator=None, n_estimators=10, ratio=1, random_state=42):
        self.base_estimator = base_estimator
        self.n_estimators = n_estimators
        self.ratio = ratio
        self.random_state = random_state
        self.estimators_ = []

    def fit(self, X, y):
        rng = np.random.RandomState(self.random_state)
        pos_idx = np.where(y == 1)[0]
        unlabeled_idx = np.where(y == 0)[0]
        n_sample = min(len(pos_idx) * self.ratio, len(unlabeled_idx))
        self.estimators_ = []
        for i in range(self.n_estimators):
            sampled = rng.choice(unlabeled_idx, size=n_sample, replace=False)
            train_idx = np.concatenate([pos_idx, sampled])
            est = clone(self.base_estimator)
            est.fit(X[train_idx], y[train_idx])
            self.estimators_.append(est)
        return self

    def predict_proba(self, X):
        probas = np.zeros((X.shape[0], 2))
        for est in self.estimators_:
            probas += est.predict_proba(X)
        probas /= len(self.estimators_)
        return probas

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)
