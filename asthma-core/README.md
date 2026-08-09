# 东方智喘 - 后端 API 服务

> 基于入血预测的中医治疗儿童哮喘作用机制分析系统 · FastAPI 后端

## 项目简介

本系统是省级重点大创项目"东方智喘"的后端服务，核心业务为**基于 AI 入血预测的中医治疗儿童哮喘机制分析**。系统整合了 PU Learning 双模型（ccTCM + HERB）入血预测、GSEA 富集分析、网络药理学拓扑等算法，为前端（Vue3 + ECharts）提供完整的数据支撑。

## 技术栈

- **框架**：FastAPI 0.104
- **ORM**：SQLAlchemy 2.0 + SQLite3
- **数据校验**：Pydantic 2.5
- **ML 推理**：scikit-learn + joblib（PU Learning 模型）
- **富集分析**：gseapy 0.10.8（Enrichr GSEA）
- **异步封装**：asyncio.to_thread（防止阻塞事件循环）

## 目录结构

```
asthma-core/
├── run.py                        # 启动入口
├── requirements.txt              # Python 依赖
├── .gitignore
└── app/
    ├── main.py                   # FastAPI 应用入口 + 全局异常捕获 + CORS
    ├── core/
    │   ├── config.py             # 配置常量（数据库路径、CORS 域名）
    │   └── db.py                 # SQLAlchemy 引擎 + get_db 依赖注入
    ├── models/
    │   └── tables.py             # ORM 模型定义（Prescription/Herb/Compound/Target）
    ├── schemas/
    │   ├── common.py             # 统一响应 ResponseModel
    │   ├── system.py             # 系统大屏相关
    │   ├── prescription.py       # 方剂分析相关
    │   ├── herb.py               # 中药材相关
    │   ├── compound.py           # 化合物相关
    │   └── prediction.py         # 入血预测相关
    ├── routers/
    │   ├── system.py             # /api/v1/system
    │   ├── prescriptions.py      # /api/v1/prescriptions
    │   ├── herbs.py              # /api/v1/herbs
    │   ├── compounds.py          # /api/v1/compounds
    │   └── prediction.py         # /api/v1/prediction
    ├── services/
    │   ├── pharmacology.py       # GSEA 富集分析（Enrichr + 动态归一化 + LRU 缓存）
    │   └── ml.py                 # PU Learning 模型加载与预测
    └── ml/
        └── pre-model/            # 训练好的 joblib 模型文件
            ├── cctcm_pu_model.joblib   # ccTCM 模型（含 scaler/imputer）
            └── herb_pu_model.joblib    # HERB 模型（含 scaler/imputer）
```

## 快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 下载数据库文件
#    从 GitHub Release 下载 asthma_v2.db.zip
#    解压到 data/asthma_v2.db

# 3. 配置环境变量（可选）
cp .env.example .env
# 编辑 .env 填入 JWT_SECRET_KEY

# 4. 启动服务
python run.py
```

服务启动后访问：
- API 文档（Swagger）：http://localhost:8000/docs
- API 文档（ReDoc）：http://localhost:8000/redoc

## API 接口总览

### 统一响应格式

所有接口统一返回：

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

异常时 `code` 为 422（参数错误）或 500（服务器错误），`data` 为 `null`。

### 1. 系统大屏模块 `/api/v1/system`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/statistics` | 数据库总体统计（方剂/药材/化合物/靶点/高概率化合物数） |
| GET | `/search?keyword=麻黄` | 全局模糊搜索（方剂+药材+化合物，防抖联想） |

### 2. 方剂分析模块 `/api/v1/prescriptions`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 方剂列表（分页） |
| GET | `/{id}` | 方剂详情 + 药材列表 |
| GET | `/{id}/network?min_prob=0.7` | Cytoscape.js 拓扑图数据（方剂→药材→化合物→靶点） |
| GET | `/{id}/radar` | 疗效雷达图（按 efficacy_type 分组计数） |

### 3. 中药材模块 `/api/v1/herbs`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/{id}` | 药材详情 |
| GET | `/{id}/compounds` | 药材化合物列表（按入血概率降序） |

### 4. 化合物与算法模块 `/api/v1/compounds`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/high-potential` | 双模型高潜化合物（prob_cctcm≥0.85 且 prob_herb≥0.85） |
| GET | `/{pubchem_cid}/targets` | 化合物靶点列表 |
| GET | `/{pubchem_cid}/radar` | 化合物疗效雷达图（GSEA 富集分析，实时请求 Enrichr） |

### 5. 入血预测模块 `/api/v1/prediction`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/models` | 获取模型信息 + 特征列表（前端动态渲染表单） |
| POST | `/predict/cctcm` | ccTCM 模型预测（19维特征） |
| POST | `/predict/herb` | HERB 模型预测（7维特征） |

## 核心算法说明

### PU Learning 入血预测

系统部署了两个 PU Learning 模型，用于预测中药化合物是否能入血（进入血液循环）：

| 模型 | 特征维度 | 分类器 | 抽样策略 | 特征来源 |
|------|---------|--------|---------|---------|
| ccTCM | 19维 | PUBaggingClassifier | 1:1 对称 | ccTCM 2.0 数据库（LogS/LogP/Caco-2/TPSA 等） |
| HERB | 7维 | PUAsymmetricBagging | 1:3 非对称 | HERB 数据库（MolWt/LogP/Drug_likeness/OB_score 等） |

预测流程：`特征输入 → SimpleImputer(median) → StandardScaler → predict_proba → 入血概率`

### GSEA 富集分析

化合物疗效雷达图基于实时 GSEA（Gene Set Enrichment Analysis）：

1. 查询化合物靶点基因列表
2. 调用 Enrichr（KEGG_2021_Human + GO_Biological_Process_2021）
3. 按关键词映射为 3 个疗效维度：**抗炎效能** / **免疫调节** / **气道修复**
4. 动态归一化为 0-100 雷达图分数

性能优化：LRU 缓存（64条）+ `asyncio.to_thread` 异步封装

### 网络药理学拓扑

方剂→药材→化合物→靶点四层网络，支持入血概率阈值过滤（`min_prob`），返回 Cytoscape.js 格式的 nodes/edges。节点去重采用 `set()` 实现 O(1) 查找。

## 全局异常处理

| 异常类型 | 业务 code | 说明 |
|---------|----------|------|
| RequestValidationError | 422 | 参数校验失败 |
| SQLAlchemyError | 500 | 数据库错误 |
| Exception（兜底） | 500 | 未预期异常 |

## 环境依赖

- Python >= 3.10
- SQLite3 数据库文件（`data/asthma_v2.db`，从 [Releases](../../releases) 下载）
- scikit-learn（PU Learning 模型推理）
- 网络（GSEA 需访问 Enrichr API）

## License

本项目为省级重点大创项目，仅供学术研究使用。
