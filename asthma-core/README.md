# 东方智喘 - 后端 API 服务

> 基于入血预测的中医治疗儿童哮喘作用机制分析系统 · FastAPI 后端

## 项目简介

本系统是重点大创项目"东方智喘"的后端服务，核心业务为**基于 AI 入血预测的中医治疗儿童哮喘机制分析**。系统整合了 PU Learning 双模型（ccTCM V2 + HERB V2）入血预测、RDKit 特征引擎、GSEA 富集分析、网络药理学拓扑与 AI 大模型报告，为前端（Vue3 + ECharts）提供完整的数据支撑。

## 技术栈

- **框架**：FastAPI 0.104 + Uvicorn
- **ORM**：SQLAlchemy 2.0 + SQLite3
- **数据校验**：Pydantic 2.5
- **ML 推理**：scikit-learn + XGBoost + joblib（PU Learning 模型）、RDKit（特征计算 + 分子结构）
- **富集分析**：gseapy 0.10.8（Enrichr GSEA）
- **认证**：python-jose（JWT）+ passlib/bcrypt
- **AI 报告**：httpx（OpenAI/DeepSeek Chat Completions 兼容，SSE 流式）

## 目录结构

```
asthma-core/
├── run.py                        # 启动入口
├── requirements.txt
├── render.yaml                   # Render 云端部署配置（lite 模型）
├── .env.example
├── data/
│   └── asthma_v2.db              # SQLite 数据库（Release 分发，不入 Git）
├── scripts/
│   ├── repurify_probabilities.py # 概率重算迁移脚本（dry-run/apply）
│   └── reports/                  # 迁移审计 CSV
└── app/
    ├── main.py                   # FastAPI 入口 + CORS + 全局异常捕获
    ├── core/
    │   ├── config.py             # 配置常量（数据库路径、CORS 域名、JWT）
    │   └── db.py                 # SQLAlchemy 引擎 + get_db 依赖注入
    ├── models/tables.py          # ORM 模型（Prescription/Herb/Compound/Target/User）
    ├── schemas/                  # Pydantic 请求/响应模型
    │   ├── common.py             # 统一响应 ResponseModel
    │   ├── system.py / prescription.py / herb.py / compound.py
    │   └── prediction.py / auth.py / expert.py
    ├── routers/                  # 8 个路由模块
    │   ├── auth.py               # /api/v1/auth       注册/登录/JWT
    │   ├── system.py             # /api/v1/system     统计/全局搜索
    │   ├── prescriptions.py      # /api/v1/prescriptions 方剂分析
    │   ├── custom_prescription.py# /api/v1/prescriptions 自定义处方 + AI 报告
    │   ├── herbs.py              # /api/v1/herbs      药材
    │   ├── compounds.py          # /api/v1/compounds  化合物与算法
    │   ├── prediction.py         # /api/v1/prediction 入血预测
    │   └── expert.py             # /api/v1/expert     专家模式
    ├── services/
    │   ├── ml.py                 # V2 模型加载（线程安全懒加载）+ 矩阵批量推理
    │   ├── feature_engine.py     # RDKit 特征引擎（19维 ccTCM / 13维 HERB + Morgan 指纹）
    │   ├── pharmacology.py       # GSEA 富集（Enrichr + 动态归一化 + LRU 缓存）
    │   ├── ai_service.py         # AI 大模型调用（SSE 流式，Key 前端传入不落盘）
    │   └── auth.py               # JWT 签发校验 + bcrypt
    └── ml/pre-model/             # 训练好的 joblib 模型
        ├── cctcm_pu_model_v2.joblib      # ccTCM 完整版 93MB（本地默认）
        ├── cctcm_pu_model_v2_lite.joblib # ccTCM 精简版 31MB（云端 512MB）
        ├── herb_pu_model_v2.joblib       # HERB 3.6MB
        ├── tune_cctcm_v2.py              # PU 类定义（joblib 反序列化必需）
        └── pu_blood_prediction_herb_v2.py
```

## 快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 下载数据库文件
#    从 GitHub Release 下载 asthma_v2.db.zip，解压到 data/asthma_v2.db

# 3. 配置环境变量（可选）
cp .env.example .env

# 4. 启动服务
python run.py
```

服务启动后访问：
- API 文档（Swagger）：http://localhost:8000/docs
- API 文档（ReDoc）：http://localhost:8000/redoc

> 模型为线程安全懒加载：首次调用预测接口时加载 ccTCM 完整版（93MB，数秒），之后常驻内存。

## API 接口总览

### 统一响应格式

```json
{ "code": 200, "message": "success", "data": { ... } }
```

异常时 `code` 为 401（未认证）/ 422（参数错误）/ 500（服务器错误），`data` 为 `null`。

### 1. 用户认证 `/api/v1/auth`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/register` | 注册（bcrypt 哈希存储） |
| POST | `/login` | 登录，返回 JWT |
| GET | `/me` | 当前用户信息（Bearer Token） |

### 2. 系统大屏 `/api/v1/system`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/statistics` | 总体统计（方剂/药材/化合物/靶点/高概率化合物数） |
| GET | `/search?keyword=麻黄` | 全局模糊搜索（中文+拼音首字母+药材反查方剂） |

### 3. 方剂分析 `/api/v1/prescriptions`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 方剂列表（分页/关键词） |
| GET | `/{id}` | 方剂详情 + 药材列表（含剂量） |
| GET | `/{id}/network?min_prob=0.7` | Cytoscape.js 四层拓扑数据（方剂→药材→化合物→靶点） |
| GET | `/{id}/radar` | 疗效雷达图（概率加权 GSEA） |
| GET | `/{id}/compounds?min_prob=` | 方剂入血化合物列表 |

### 4. 自定义处方 `/api/v1/prescriptions`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/analyze` | 自由组合中药 → 聚合入血化合物/靶点/雷达评分 |
| POST | `/ai-report` | AI 深度分析报告（SSE 流式，Key 由请求头传入） |
| POST | `/existing-ai-report` | 已收录方剂的 AI 报告 |

### 5. 中药材 `/api/v1/herbs`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 药材列表（分页/功效分类筛选） |
| GET | `/filter-options` | 功效分类等筛选项 |
| GET | `/{id}` | 药材详情 |
| GET | `/{id}/compounds` | 药材化合物（按 prob_cctcm 降序） |

### 6. 化合物与算法 `/api/v1/compounds`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 列表（分页/min_prob 过滤/概率排序） |
| GET | `/high-potential` | 双模型高潜化合物（prob_cctcm≥0.85 且 prob_herb≥0.85） |
| GET | `/{id}` | 化合物详情（双模型概率+雷达评分） |
| GET | `/{id}/targets` | 化合物靶点列表 |
| GET | `/{id}/radar` | 疗效雷达图（实时 Enrichr GSEA） |
| GET | `/{id}/structure` | 分子结构图（RDKit 渲染） |

### 7. 入血预测 `/api/v1/prediction`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/models` | 模型信息 + 特征列表（前端动态渲染表单） |
| POST | `/predict/smiles` | **SMILES 预测**（自动算特征，支持 `adme_overrides` 实验值校准） |
| POST | `/predict/smiles/batch` | JSON 批量（≤500 条，矩阵化推理） |
| POST | `/predict/smiles/upload` | 文件上传批量（.xlsx/.csv，检测 SMILES 列 + 可选 ADME 列） |
| GET | `/predict/smiles/download/{file}` | 下载批量结果文件（xlsx/csv） |
| POST | `/predict/cctcm` | ccTCM 手动 19 维特征预测 |
| POST | `/predict/herb` | HERB 手动 7 维特征预测 |

### 8. 专家模式 `/api/v1/expert`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/metrics` | 模型评估指标 |
| GET | `/feature-importance` | 特征贡献度分析 |

## 核心算法说明

### PU Learning 入血预测（V2）

| | ccTCM V2 | HERB V2 |
|---|---|---|
| 特征维度 | 1043 = 19 特征 + Morgan(1024) | 1037 = 13 描述符 + Morgan(1024) |
| 基分类器 | RandomForest(300) | XGBoost |
| PU 抽样 | 1:1 对称 × 30 轮 | 1:5 非对称 × 30 轮 |
| 网格 ROC-AUC | 0.8229 ± 0.0081 | 0.8463 ± 0.0105 |
| 工作阈值 | 0.56 | 0.62 |
| 模型文件 | 93MB（lite 版 31MB） | 3.6MB |

推理管线（`services/ml.py`）：

1. SMILES → RDKit 计算 19 维特征（`feature_engine.py`，缺失 ADME 由推算值/中位数填补）
2. Morgan 指纹 radius=2 → 1024 bit
3. 按 bundle 的 `feature_cols` 组装矩阵 → `SimpleImputer(median)` → `StandardScaler`
4. 30 轮 PU Bagging 概率平均 → 入血概率
5. 概率对照工作阈值动态分档（≥ t+0.2 高 / ≥ t 中 / 其余低）

**性能要点**：
- 完整版单条预测约 4s（9000 棵树 × 30 轮），批量接口用矩阵化 `predict_smiles_batch` 一次推理 500 条
- Render 512MB 内存用 `CCTCM_MODEL_FILE=cctcm_pu_model_v2_lite.joblib`（31MB，ROC 0.815，与完整版概率相关系数 0.9956）
- PU 类反序列化要求模块名匹配，`pre-model/` 下的 `tune_cctcm_v2.py` / `pu_blood_prediction_herb_v2.py` 不可删除

### GSEA 富集分析

1. 查询化合物靶点基因列表
2. 调用 Enrichr（KEGG_2021_Human + GO_Biological_Process_2021）
3. 按关键词映射 3 个疗效维度：**抗炎效能 / 免疫调节 / 气道修复**
4. 入血概率加权 + 动态归一化为 0-100 雷达图分数

性能优化：LRU 缓存（64 条）+ `asyncio.to_thread` 异步封装。

### 网络药理学拓扑

方剂→药材→化合物→靶点四层网络，支持 `min_prob` 入血概率阈值、`asthma_only` 哮喘靶点过滤、每化合物靶点数上限，返回 Cytoscape.js 格式 nodes/edges。

## 全局异常处理

| 异常类型 | 业务 code | 说明 |
|---------|----------|------|
| HTTPException（认证） | 401 | JWT 缺失/过期 |
| RequestValidationError | 422 | 参数校验失败 |
| SQLAlchemyError | 500 | 数据库错误 |
| Exception（兜底） | 500 | 未预期异常 |

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DB_PATH` | 数据库路径 | `data/asthma_v2.db` |
| `JWT_SECRET_KEY` | JWT 密钥（生产必改） | dev 默认值 |
| `CCTCM_MODEL_FILE` | ccTCM 模型：完整版/精简版 | 完整版 |
| `CORS_ORIGINS` / `CORS_EXTRA_ORIGINS` | 跨域域名 | localhost:5173 |

## 云端部署（Render）

`render.yaml` 已配置：Python 3.11、lite 模型、`generateValue` 自动生成 JWT 密钥。数据库文件需随仓库或通过磁盘挂载提供。

## License

本项目为重点大创项目，仅供学术研究使用。
