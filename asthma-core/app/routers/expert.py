"""
专家模式路由（算法性能展示）
- GET /metrics            模型评估指标（ROC/PR曲线数据 + 特征权重热力图）
- GET /feature-importance  特征重要性排名

⚠️ 当前数据为预计算/经验值，后续可从模型评估脚本自动生成并存入数据库
"""
from fastapi import APIRouter
from app.schemas import ResponseModel

router = APIRouter()


# ==================== 预计算的模型评估数据 ====================
# 说明：以下数据应由训练脚本（入血预测/pu_blood_prediction_*.py）评估后导出
# 目前使用经验值占位，后续可迁移到数据库表或 JSON 文件管理

# ROC 曲线数据 [FPR, TPR]
ROC_DATA = {
    "pu_learning": {
        "auc": 0.98,
        "points": [
            [0, 0], [0.05, 0.45], [0.1, 0.72], [0.15, 0.85], [0.2, 0.9],
            [0.3, 0.94], [0.4, 0.96], [0.5, 0.97], [0.6, 0.98], [0.8, 0.99], [1, 1]
        ]
    },
    "traditional_svm": {
        "auc": 0.72,
        "points": [
            [0, 0], [0.1, 0.25], [0.2, 0.4], [0.3, 0.52], [0.4, 0.62],
            [0.5, 0.7], [0.6, 0.76], [0.7, 0.82], [0.8, 0.88], [0.9, 0.94], [1, 1]
        ]
    }
}

# PR 曲线数据 [Recall, Precision]
PR_DATA = {
    "pu_learning": {
        "auprc": 0.985,
        "points": [
            [1, 0.92], [0.95, 0.94], [0.9, 0.95], [0.8, 0.96], [0.7, 0.97],
            [0.6, 0.975], [0.5, 0.98], [0.4, 0.985], [0.3, 0.99], [0.2, 0.995], [0.1, 0.998]
        ]
    },
    "traditional_svm": {
        "auprc": 0.82,
        "points": [
            [1, 0.6], [0.9, 0.65], [0.8, 0.68], [0.7, 0.72], [0.6, 0.75],
            [0.5, 0.78], [0.4, 0.82], [0.3, 0.85], [0.2, 0.9], [0.1, 0.95]
        ]
    }
}

# 特征权重热力图数据
# [compound_index, feature_index, weight_value]
HEATMAP_FEATURES = ['MW分子量', 'LogP脂水分配系数', 'TPSA拓扑极性表面积', 'HBD氢键供体', 'HBA氢键受体']
HEATMAP_COMPOUNDS = ['麻黄碱', '黄芩苷', '苦杏仁苷', '次黄嘌呤', '槲皮素']
HEATMAP_DATA = [
    [0, 0, 0.85], [0, 1, 0.72], [0, 2, 0.45], [0, 3, 0.91], [0, 4, 0.38],
    [1, 0, 0.62], [1, 1, 0.88], [1, 2, 0.75], [1, 3, 0.55], [1, 4, 0.92],
    [2, 0, 0.45], [2, 1, 0.38], [2, 2, 0.82], [2, 3, 0.65], [2, 4, 0.78],
    [3, 0, 0.72], [3, 1, 0.55], [3, 2, 0.42], [3, 3, 0.88], [3, 4, 0.62],
    [4, 0, 0.38], [4, 1, 0.92], [4, 2, 0.68], [4, 3, 0.42], [4, 4, 0.85]
]

# 特征重要性排名
FEATURE_IMPORTANCE = [
    {"feature": "LogP（脂水分配系数）", "importance": 0.28, "model": "ccTCM"},
    {"feature": "TPSA（拓扑极性表面积）", "importance": 0.22, "model": "ccTCM"},
    {"feature": "MW（分子量）", "importance": 0.18, "model": "ccTCM"},
    {"feature": "HBA（氢键受体数）", "importance": 0.15, "model": "ccTCM"},
    {"feature": "HBD（氢键供体数）", "importance": 0.10, "model": "ccTCM"},
    {"feature": "可旋转键数", "importance": 0.07, "model": "ccTCM"},
    {"feature": "MolLogP", "importance": 0.30, "model": "HERB"},
    {"feature": "MolWt", "importance": 0.25, "model": "HERB"},
    {"feature": "NumHAcceptors", "importance": 0.20, "model": "HERB"},
    {"feature": "NumHDonors", "importance": 0.15, "model": "HERB"},
    {"feature": "NumRotatableBonds", "importance": 0.10, "model": "HERB"},
]


@router.get("/metrics")
async def get_expert_metrics():
    """
    获取算法性能评估数据
    返回 ROC 曲线、PR 曲线、特征权重热力图的预计算数据

    TODO: 后续可改为从数据库或评估报告文件中读取
    """
    data = {
        "roc": {
            "pu_learning": ROC_DATA["pu_learning"],
            "traditional_svm": ROC_DATA["traditional_svm"]
        },
        "pr": {
            "pu_learning": PR_DATA["pu_learning"],
            "traditional_svm": PR_DATA["traditional_svm"]
        },
        "heatmap": {
            "features": HEATMAP_FEATURES,
            "compounds": HEATMAP_COMPOUNDS,
            "data": HEATMAP_DATA
        }
    }

    return ResponseModel(data=data)


@router.get("/feature-importance")
async def get_feature_importance():
    """
    获取双模型特征重要性排名
    用于展示 PU Learning 模型的可解释性
    """
    return ResponseModel(data=FEATURE_IMPORTANCE)
