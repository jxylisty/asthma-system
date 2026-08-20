# 东方智喘 · 儿童哮喘方剂智能分析系统

> 基于入血预测的中医治疗儿童哮喘作用机制分析 · 重点大创项目
>
> 传统中医药研究"什么成分入了血"依赖实验测定，成本高、通量低。本系统用 **PU Learning（正例-未标注学习）双模型** 预测中药化合物入血概率，结合网络药理学拓扑与 GSEA 富集分析，为中医治疗儿童哮喘提供**从方剂 → 药材 → 入血化合物 → 靶点 → 通路**的全链条智能分析平台。

## 目录

- [系统架构](#系统架构)
- [核心功能](#核心功能)
- [入血预测模型（V2）](#入血预测模型v2)
- [数据库设计](#数据库设计)
- [API 接口总览](#api-接口总览)
- [快速启动](#快速启动)
- [云端部署](#云端部署)
- [配置说明](#配置说明)
- [项目结构](#项目结构)
- [License](#license)

## 系统架构

```
┌─────────────────────────────┐        ┌──────────────────────────────────┐
│  asthma-front (Vercel)      │  HTTP  │  asthma-core (Render)            │
│  Vue 3 + Element Plus       │ ─────► │  FastAPI + SQLAlchemy            │
│  ECharts / Cytoscape.js     │  /api  │                                  │
│                             │        │  ┌────────────────────────────┐  │
│  · 入血预测控制台            │        │  │ PU Learning 双模型 (V2)     │  │
│  · 方剂/药材/化合物浏览      │        │  │ ccTCM: RF300+PU, 1043维    │  │
│  · 网络药理学拓扑图          │        │  │ HERB: XGB+PU, 1037维       │  │
│  · AI 分析报告 (SSE)        │        │  └────────────────────────────┘  │
│  · 专家模式 / 系统设置       │        │  · RDKit 特征引擎               │
└─────────────────────────────┘        │  · GSEA 富集 (Enrichr)          │
                                       │  · SQLite (asthma_v2.db)        │
                                       └──────────────────────────────────┘
```

前后端分离，各自独立仓库：

| 子项目 | 技术栈 | 仓库 |
|--------|--------|------|
| asthma-core | FastAPI + SQLAlchemy 2.0 + RDKit + scikit-learn/XGBoost + gseapy | [jxylisty/asthma-core](https://github.com/jxylisty/asthma-core) |
| asthma-front | Vue 3 + Element Plus + ECharts 5 + Cytoscape.js + Vite 4 | [jxylisty/asthma-front](https://github.com/jxylisty/asthma-front) |

## 核心功能

### 1. 入血预测控制台（`/prediction`）

- **单化合物精准预测**：粘贴 SMILES 结构式，后端 RDKit 自动计算特征矩阵后调用模型，返回入血概率、预测等级（按模型工作阈值动态分档）、19 维特征明细
- **ADME 实验值校准**：7 项 ADME/药代动力学特征（LogS、LogD、LogP、Caco-2、MDCK、F(20%)、P-gp）默认由算法推算（误差约 10%-15%），有实验数据的用户可填入真实值重新预测，显著提升精度
- **批量文件预测**：上传 `.xlsx` / `.csv`（须含 SMILES 列，单次最多 500 条，可选 ADME 实验值列），服务端矩阵化批量推理，结果追加预测概率/等级/分子量列后供下载
- **预测历史**：localStorage 持久化，支持搜索、回填、查看历史特征明细

### 2. 方剂智能分析（`/prescriptions`、`/detail`）

- 46 首经典哮喘方剂，含每味药材精确剂量
- **网络药理学拓扑**：方剂 → 药材 → 化合物 → 靶点四层网络（Cytoscape.js 渲染），入血概率阈值、哮喘靶点过滤、节点数量上限均可调节
- **疗效雷达图**：入血化合物靶点经 GSEA 富集分析（KEGG + GO 生物过程），按三大疗效维度打分——**抗炎效能 / 免疫调节 / 气道修复**，概率加权平均
- **自定义方剂**（`/custom-prescription`）：自由勾选中药组合，系统自动聚合入血成分与靶点生成分析报告，并可调用 AI 大模型生成深度解读（SSE 流式输出，支持导出 PDF）

### 3. 数据浏览与检索

- **药材库**：278 味中药，性味归经、功效主治，按功效分类筛选
- **化合物库**：569 个入血预测化合物，ccTCM / HERB 双模型概率、分子量、LogP、哮喘相关性，支持概率阈值过滤与排序；高潜化合物专区（双模型概率均 ≥ 0.85）
- **智能搜索**：中文模糊匹配 + **拼音首字母**（输入 `mh` 匹配"麻黄"）+ **药材名反查方剂**（输入"麻黄"推荐含麻黄的方剂），250ms 防抖实时联想
- **专家模式**（`/expert`）：模型特征贡献度、数据集统计等分析视图

### 4. AI 报告生成

兼容 OpenAI / DeepSeek 及任何 Chat Completions 协议的大模型，SSE 流式生成方剂机制分析报告；API Key 由前端请求头传入，后端不持久化。

## 入血预测模型（V2）

2026-08 集成的正式版本，训练细节见 `入血预测/` 目录（训练脚本 + 调参日志 + 结果报告）。

### 模型概览

| | ccTCM 2.0（主力模型） | HERB 2.0（兜底模型） |
|---|---|---|
| 数据源 | ccTCM 2.0 三表融合（403 精英库） | HERB 中药数据库（29023 全库） |
| 基分类器 | RandomForest(300) | XGBoost |
| PU 策略 | Asymmetric Bagging 1:1 对称 × 30 轮 | Asymmetric Bagging 1:5 非对称 × 30 轮 |
| 特征维度 | **1043** = 19 特征 + Morgan 指纹 1024 | **1037** = 13 描述符 + Morgan 指纹 1024 |
| 网格 ROC-AUC | 0.8229 ± 0.0081 | 0.8463 ± 0.0105 |
| 测试 ROC-AUC | 0.8073 | 0.8243 |
| 工作阈值 | **0.56** | **0.62** |
| 模型文件 | cctcm_pu_model_v2.joblib（93MB） | herb_pu_model_v2.joblib（3.6MB） |

### ccTCM 19 维特征

| 类别 | 特征 | 来源 |
|------|------|------|
| ADME（8 项） | LogS、LogD、LogP、Pgp-inhibitor、Pgp-substrate、F(20%)、Caco-2 Permeability、MDCK Permeability | ccTCM 数据库实验值，缺失时算法推算 |
| RDKit 拓扑（11 项） | 氢键受体/供体数、TPSA、可旋转键数、环数、最大环、杂原子数 nHet、形式电荷 fChar、刚性键数 nRig、柔韧性 Flex、立体中心数 nStereo | SMILES 结构实时精确计算 |

另加 Morgan 指纹（radius=2，1024 bit）。推理管线：`SMILES → RDKit 特征 → SimpleImputer(median) → StandardScaler → 30 轮 PU Bagging 平均 → 入血概率`。

> **为什么用 PU Learning？** 中药成分"确定入血"的只有实验验证过的正样本，其余大量化合物是"未标注"而非"不入血"。PU 学习把未标注集反复抽样当负集训练再集成，避免把潜在正样本硬当负例造成的系统性偏差。

### 云端精简版（lite）

Render 免费实例仅 512MB 内存，加载 93MB 完整版（解压后数百 MB）会 OOM。为此训练了 `cctcm_pu_model_v2_lite.joblib`（31MB，Bagging 轮数 30→10）：

| | 完整版（本地默认） | 精简版（云端） |
|---|---|---|
| 文件体积 | 93MB | 31MB |
| ROC-AUC | 0.823 | 0.815 |
| 与完整版概率相关系数 | — | **0.9956** |

通过环境变量 `CCTCM_MODEL_FILE` 切换，见[配置说明](#配置说明)。

## 数据库设计

SQLite 单文件 `asthma-core/data/asthma_v2.db`（通过 [GitHub Release](https://github.com/jxylisty/asthma-core/releases) 分发，不入 Git）。

### 数据规模

| 数据 | 数量 |
|------|------|
| 经典方剂 | 46 首 |
| 中药药材 | 278 味 |
| 入血预测化合物 | 569 个（双模型概率零空值） |
| 哮喘相关靶点 | 7398 个 |

### 核心表

| 表 | 说明 |
|----|------|
| `prescription` | 方剂（名称、主治、功效分类） |
| `herb` | 药材（性味归经、功效） |
| `compound` | 化合物。关键字段：`prob_cctcm`（主力模型概率）、`prob_herb`（兜底模型概率）、`radar_*` 三维疗效评分、`asthma_related` |
| `target` | 靶点（基因名、哮喘相关性） |
| `rel_herb_compound` / `rel_compound_target` | 多对多关联 |
| `rel_prescription_herb` | 方剂-药材关联（含剂量） |
| `user` | 用户（bcrypt 密码哈希，JWT 认证） |

> 入血概率字段说明：前端所有"ccTCM 入血概率"展示均读取 `prob_cctcm`；历史遗留的 `blood_entry_probability` 列已于 2026-08 清理下线，API 响应中的同名字段仅作兼容别名。

## API 接口总览

统一前缀 `/api/v1`，统一响应 `{code, message, data}`。交互式文档：http://localhost:8000/docs

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 认证 | POST | `/auth/register` `/auth/login` | 注册 / 登录（JWT） |
| 认证 | GET | `/auth/me` | 当前用户信息 |
| 系统 | GET | `/system/statistics` | 数据库总体统计 |
| 系统 | GET | `/system/search?keyword=` | 全局模糊搜索（拼音首字母 + 药材反查） |
| 方剂 | GET | `/prescriptions` `/{id}` | 方剂列表 / 详情 |
| 方剂 | GET | `/prescriptions/{id}/network` | 四层拓扑网络（min_prob、asthma_only 等参数） |
| 方剂 | GET | `/prescriptions/{id}/radar` | 疗效雷达图数据 |
| 方剂 | GET | `/prescriptions/{id}/compounds` | 方剂入血化合物（概率过滤） |
| 自定义 | POST | `/prescriptions/analyze` | 自定义中药组合分析 |
| 自定义 | POST | `/prescriptions/ai-report` | AI 深度报告（SSE 流式） |
| 药材 | GET | `/herbs` `/{id}` `/filter-options` | 列表 / 详情 / 筛选项 |
| 药材 | GET | `/herbs/{id}/compounds` | 药材化合物（按入血概率降序） |
| 化合物 | GET | `/compounds` `/{id}` | 列表（分页/过滤/排序）/ 详情 |
| 化合物 | GET | `/compounds/high-potential` | 双模型高潜化合物 |
| 化合物 | GET | `/compounds/{id}/targets` `/radar` `/structure` | 靶点 / 雷达 / 分子结构 |
| 预测 | GET | `/prediction/models` | 模型信息 + 特征列表 |
| 预测 | POST | `/prediction/predict/smiles` | 单条 SMILES 预测（支持 adme_overrides） |
| 预测 | POST | `/prediction/predict/smiles/batch` | JSON 批量（≤500 条） |
| 预测 | POST | `/prediction/predict/smiles/upload` | 文件上传批量（.xlsx/.csv） |
| 预测 | GET | `/prediction/predict/smiles/download/{file}` | 下载批量结果 |
| 预测 | POST | `/prediction/predict/cctcm` `/predict/herb` | 手动输入特征预测 |
| 专家 | GET | `/expert/metrics` `/expert/feature-importance` | 模型指标 / 特征贡献度 |

## 快速启动

### 前提条件

- Python ≥ 3.10（依赖含 RDKit，建议 Anaconda）
- Node.js ≥ 18
- Git

### 1. 克隆项目

```bash
git clone https://github.com/jxylisty/asthma-system.git
cd asthma-system
```

### 2. 下载数据库

从 [asthma-core Releases](https://github.com/jxylisty/asthma-core/releases) 下载 `asthma_v2.db.zip`，解压到 `asthma-core/data/asthma_v2.db`。

模型文件（joblib）已随仓库提交，无需额外下载。

### 3. 启动后端（端口 8000）

```bash
cd asthma-core
pip install -r requirements.txt
cp .env.example .env        # 可选：改 JWT 密钥
python run.py
```

验证：访问 http://localhost:8000/docs 能看到 Swagger 文档。

> 首次调用预测接口需加载 93MB 模型（数秒），之后常驻内存。本地默认完整版模型。

### 4. 启动前端（端口 5173）

```bash
cd asthma-front
npm install
npm run dev
```

访问 http://localhost:5173 ，注册账号登录即可（首个注册用户即为系统用户，无默认账号）。

### 5. 一键启动（Windows）

仓库根目录执行 `asthma-front/start_all.bat` 可同时拉起前后端。

## 云端部署

### 后端 → Render

仓库 `asthma-core/render.yaml` 已就绪：

- Build：`pip install -r requirements.txt`
- Start：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- 关键环境变量：`CCTCM_MODEL_FILE=cctcm_pu_model_v2_lite.joblib`（512MB 内存专用精简版）、`DB_PATH=data/asthma_v2.db`

### 前端 → Vercel

根目录 `vercel.json` 已就绪：构建 `asthma-front` 并输出 `dist`，SPA 路由重写到 `index.html`。

生产环境前端的 API 地址指向 Render 后端域名，跨域由后端 `CORS_EXTRA_ORIGINS` 控制。

## 配置说明

后端环境变量（`.env` 或 Render 控制台）：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DB_PATH` | SQLite 数据库路径 | `data/asthma_v2.db` |
| `JWT_SECRET_KEY` | JWT 签名密钥（生产必须修改） | `dev-secret-change-in-production` |
| `CCTCM_MODEL_FILE` | ccTCM 模型文件名：完整版 `cctcm_pu_model_v2.joblib` / 精简版 `cctcm_pu_model_v2_lite.joblib` | 完整版 |
| `CORS_ORIGINS` | 允许跨域域名（逗号分隔） | `http://localhost:5173` |
| `CORS_EXTRA_ORIGINS` | 追加跨域域名（Render 上配置 Vercel 前端域名） | 空 |

## 项目结构

```
asthma-system/
├── readme.md                  # 本文件
├── vercel.json                # Vercel 前端部署配置
├── asthma-core/               # 后端（独立仓库同步）
│   ├── run.py                 # 启动入口
│   ├── requirements.txt
│   ├── render.yaml            # Render 部署配置
│   ├── data/                  # SQLite 数据库（Release 分发）
│   ├── scripts/               # 运维脚本（概率重算迁移等）
│   └── app/
│       ├── main.py            # FastAPI 入口 + CORS + 异常处理
│       ├── core/              # 配置 + 数据库引擎
│       ├── models/tables.py   # ORM 模型
│       ├── schemas/           # Pydantic 请求/响应模型
│       ├── routers/           # 8 个路由模块
│       ├── services/          # ml.py(模型推理) feature_engine.py(RDKit特征)
│       │                      # pharmacology.py(GSEA) ai_service.py auth.py
│       └── ml/pre-model/      # V2 模型 joblib + PU 类反序列化模块
├── asthma-front/              # 前端（独立仓库同步）
│   ├── src/api/               # Axios 封装
│   ├── src/views/             # 13 个页面组件
│   ├── src/components/        # Layout / Sidebar
│   └── src/composables/       # 认证 / 设置持久化
└── 入血预测/                  # 模型训练工程（不部署）
    ├── cctcm2.0_v2/           # ccTCM V2 训练脚本 + 调参日志 + 结果
    ├── herb2.0_v2/            # HERB V2 训练脚本 + 调参日志 + 结果
    └── 模型调用说明.md
```

## License

本项目为重点大创项目，仅供学术研究使用。
