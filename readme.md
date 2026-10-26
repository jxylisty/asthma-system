# 东方智喘 · 儿童哮喘方剂智能分析系统

> 基于入血预测的中医治疗儿童哮喘作用机制分析 · 重点大创项目
>
> 传统中医药研究"什么成分入了血"依赖实验测定，成本高、通量低。本系统用 **PU Learning（正例-未标注学习）双模型** 预测中药化合物入血概率，结合网络药理学拓扑与 GSEA 富集分析，为中医治疗儿童哮喘提供**从方剂 → 药材 → 入血化合物 → 靶点 → 通路**的全链条智能分析平台。

## 目录

- [项目概览](#项目概览)
- [关键代码定位](#关键代码定位软著申请用)
- [系统架构](#系统架构)
- [核心功能](#核心功能)
- [入血预测模型](#入血预测模型)
- [数据库设计](#数据库设计)
- [API 接口总览](#api-接口总览)
- [快速启动](#快速启动)
- [云端部署](#云端部署)
- [配置说明](#配置说明)
- [项目结构](#项目结构)
- [数据质量与溯源](#数据质量与溯源)
- [License](#license)

## 项目概览

| 项 | 说明 |
|---|---|
| 项目类型 | 大学生创新创业训练计划（重点）项目 |
| 技术领域 | 中医药信息学 + 机器学习 + 网络药理学 |
| 代码规模 | 后端 4,519 行 Python / 前端 12,315 行 Vue+JS |
| 数据规模 | 46 首经典方剂、279 味药材、569 个入血化合物、7,398 个靶点 |
| 开发周期 | 2026 年 6 月 - 2026 年 10 月 |
| 运行形态 | Web 前后端分离（Vue 3 + FastAPI） |

### 项目解决的三个问题

1. **入血成分识别难**：中药复方含数百种化合物，哪些真能吸收入血发挥作用，传统上只能靠动物实验逐个测定。本系统用 PU Learning 模型，输入 SMILES 结构式即可秒级预测入血概率。
2. **作用机制阐释不足**：单一成分、单一靶点的研究无法解释复方的多成分-多靶点协同作用。本系统构建"方剂→药材→成分→靶点"四层网络，并用 GSEA 富集分析映射到抗炎、免疫调节、气道修复三个疗效维度。
3. **临床与科研数据脱节**：本系统把 46 首临床常用哮喘方剂与化合物结构、靶点通路数据打通，支持自定义处方的即时机制分析。

## 关键代码定位（软著申请用）

> 软著申请需要提交源代码文档，以下按功能模块列出核心文件，便于提取。

### 后端核心算法（`asthma-core/app/`）

| 功能模块 | 文件 | 行数 | 说明 |
|---|---|---|---|
| **PU Learning 模型推理** | `services/ml.py` | 303 | 模型懒加载、特征组装、双模型预测入口 |
| **RDKit 特征引擎** | `services/feature_engine.py` | 281 | 从 SMILES 计算 19 维理化特征 + 1024 位 Morgan 指纹 |
| **PU 算法实现** | `ml/pre-model/tune_cctcm_v2.py` | 46 | 非对称 Bagging 分类器（ccTCM 模型反序列化依赖） |
| **PU 算法实现（HERB）** | `ml/pre-model/pu_blood_prediction_herb_v2.py` | 47 | HERB 模型配套的 PU Bagging 类 |
| **GSEA 富集分析** | `services/pharmacology.py` | 159 | 靶点基因集 → KEGG/GO 富集 → 三维疗效评分 |
| **AI 报告生成** | `services/ai_service.py` | 238 | 兼容 OpenAI 协议的 SSE 流式生成 |
| **ORM 数据模型** | `models/tables.py` | 226 | 7 张核心表的结构定义 |
| **方剂四层网络** | `routers/prescriptions.py` | 508 | 方剂→药材→成分→靶点的拓扑数据组装 |
| **自定义处方分析** | `routers/custom_prescription.py` | 577 | 任意药材组合的即时机制分析 |
| **入血预测接口** | `routers/prediction.py` | 498 | 单条/批量/文件上传三种预测模式 |
| **化合物分析** | `routers/compounds.py` | 375 | 化合物详情、靶点、雷达图 |
| **药材分析** | `routers/herbs.py` | 208 | 药材详情、成分列表 |
| **全局搜索** | `routers/system.py` | 148 | 拼音首字母 + 药材反查方剂 |
| **认证** | `routers/auth.py` + `services/auth.py` | 156 | JWT + bcrypt |

### 前端核心页面（`asthma-front/src/views/`）

| 页面 | 文件 | 行数 | 说明 |
|---|---|---|---|
| 入血预测控制台 | `Prediction.vue` | 1,312 | 单条/批量预测、ADME 校准、历史记录 |
| 自定义处方分析 | `CustomPrescription.vue` | 1,340 | 药材勾选、成分聚合、AI 报告、PDF 导出 |
| 化合物详情 | `CompoundDetail.vue` | 1,018 | 雷达图、靶点列表、3D 分子结构 |
| 网络拓扑编辑器 | `NodeEditor.vue` | 1,113 | Cytoscape 图编辑 |
| 方剂详情 | `Detail.vue` | 504 | 四层网络、成分列表、雷达图 |
| 专家模式 | `Expert.vue` | 666 | 模型指标、特征贡献度 |
| 系统设置 | `Settings.vue` | 608 | AI Key、语音、主题配置 |
| 药材详情 | `HerbDetail.vue` | 633 | 性味归经、成分、关联方剂 |
| 首页 | `Home.vue` | 506 | 数据总览、快捷入口 |

### 模型训练工程（`入血预测/`，不参与部署）

| 文件 | 说明 |
|---|---|
| `cctcm2.0_v2/pu_blood_prediction_v2.py` | ccTCM V2 基线训练（RDKit 补缺 + Morgan 指纹） |
| `cctcm2.0_v2/tune_cctcm_v2.py` | PU 分类器定义 + 超参网格搜索 |
| `cctcm2.0_v2/final_cctcm_union.py` | 正式版训练（复方标签 ∪ 桥接标签并集） |
| `cctcm2.0_v2/make_union_lite.py` | 云端精简版生成（30 轮 → 10 轮） |
| `cctcm2.0_v2/union_results.md` | 训练指标快照 |

### 数据修复与质量核查脚本（`asthma-core/scripts/`）

| 文件 | 说明 |
|---|---|
| `repair_data_quality.py` | 药材-成分重建、理化属性重算、靶点脏字段清理、方剂组成重建 |
| `recompute_radar_gsea.py` | 三维机制评分真实 GSEA 重算（带缓存与断点续跑） |
| `rebuild_physchem.py` | 理化性质表错位数据修复（957 行） |
| `repredict_probabilities.py` | 用重训模型重算库内入血概率 |
| `repurify_probabilities.py` | 历史概率重灌脚本（含脏值审计） |

## 系统架构

```
┌─────────────────────────────┐        ┌──────────────────────────────────┐
│  asthma-front (Vercel)      │  HTTP  │  asthma-core (Render)            │
│  Vue 3 + Element Plus       │ ─────► │  FastAPI + SQLAlchemy            │
│  ECharts / Cytoscape.js     │  /api  │                                  │
│                             │        │  ┌────────────────────────────┐  │
│  · 入血预测控制台            │        │  │ PU Learning 双模型          │  │
│  · 方剂/药材/化合物浏览      │        │  │ ccTCM: RF300+PU, 1043维    │  │
│  · 网络药理学拓扑图          │        │  │ HERB: XGB+PU, 1037维       │  │
│  · AI 分析报告 (SSE)        │        │  └────────────────────────────┘  │
│  · 专家模式 / 系统设置       │        │  · RDKit 特征引擎               │
└─────────────────────────────┘        │  · GSEA 富集 (Enrichr)          │
                                       │  · SQLite (asthma_v2.db)        │
                                       └──────────────────────────────────┘
```

## 核心功能

### 1. 入血预测控制台（`/prediction`）

- **单化合物精准预测**：粘贴 SMILES 结构式，后端 RDKit 自动计算特征矩阵后调用模型，返回入血概率、预测等级（按模型工作阈值动态分档）、19 维特征明细
- **ADME 实验值校准**：7 项 ADME/药代动力学特征（LogS、LogD、LogP、Caco-2、MDCK、F(20%)、P-gp）默认由算法推算，有实验数据的用户可填入真实值重新预测
- **批量文件预测**：上传 `.xlsx` / `.csv`（须含 SMILES 列，单次最多 500 条，可选 ADME 实验值列），服务端矩阵化批量推理，结果追加预测概率/等级/分子量列后供下载
- **预测历史**：localStorage 持久化，支持搜索、回填、查看历史特征明细

### 2. 方剂智能分析（`/prescriptions`、`/detail`）

- 46 首经典哮喘方剂，含每味药材精确剂量
- **网络药理学拓扑**：方剂 → 药材 → 化合物 → 靶点四层网络（Cytoscape.js 渲染），入血概率阈值、哮喘靶点过滤、节点数量上限均可调节
- **疗效雷达图**：入血化合物靶点经 GSEA 富集分析（KEGG + GO 生物过程），按三大疗效维度打分——**抗炎效能 / 免疫调节 / 气道修复**，概率加权平均
- **自定义方剂**（`/custom-prescription`）：自由勾选中药组合，系统自动聚合入血成分与靶点生成分析报告，并可调用 AI 大模型生成深度解读（SSE 流式输出，支持导出 PDF）

### 3. 数据浏览与检索

- **药材库**：279 味中药，性味归经、功效主治，按功效分类筛选
- **化合物库**：569 个入血预测化合物，ccTCM / HERB 双模型概率、分子量、LogP、哮喘相关性，支持概率阈值过滤与排序
- **智能搜索**：中文模糊匹配 + **拼音首字母**（输入 `mh` 匹配"麻黄"）+ **药材名反查方剂**（输入"麻黄"推荐含麻黄的方剂），250ms 防抖实时联想
- **专家模式**（`/expert`）：模型特征贡献度、数据集统计等分析视图

### 4. AI 报告生成

兼容 OpenAI / DeepSeek 及任何 Chat Completions 协议的大模型，SSE 流式生成方剂机制分析报告；API Key 由前端请求头传入，后端不持久化。

## 入血预测模型

训练细节见 `入血预测/` 目录（训练脚本 + 调参日志 + 结果报告）。

### 模型概览

| | ccTCM 2.0（主力模型） | HERB 2.0（兜底模型） |
|---|---|---|
| 数据源 | ccTCM 2.0 三表融合 | HERB 中药数据库 |
| 基分类器 | RandomForest(300) | XGBoost |
| PU 策略 | Asymmetric Bagging 1:1 × 30 轮 | Asymmetric Bagging 1:5 × 30 轮 |
| 特征维度 | **1043** = 19 特征 + Morgan 指纹 1024 | **1037** = 13 描述符 + Morgan 指纹 1024 |
| 标签来源 | 复方数据集 ∪ 桥接表 Yes 标记（并集 685 正样本） | 同左 |
| 网格 ROC-AUC | 0.8237 ± 0.0058 | 0.8463 ± 0.0105 |
| **测试 ROC-AUC** | **0.8129** | 0.8243 |
| **测试 PR-AUC** | **0.7025** | — |
| 工作阈值 | 0.47 | 0.62 |
| 模型文件 | `cctcm_pu_model_v2.joblib`（94.6MB） | `herb_pu_model_v2.joblib`（3.5MB） |

> 2026-10-26 更新：修正训练数据中 957 行理化性质错位问题后重训。测试集 ROC-AUC 从 0.8073 提升至 **0.8129**，PR-AUC 从 0.7003 提升至 **0.7025**，最优 F1 从 0.6414 提升至 **0.6546**。

### ccTCM 19 维特征

| 类别 | 特征 | 来源 |
|------|------|------|
| ADME（7 项） | LogS、LogD、Pgp-inhibitor、Pgp-substrate、F(20%)、Caco-2 Permeability、MDCK Permeability | 实验值，缺失时中位数填补 |
| RDKit 拓扑（12 项） | LogP、氢键受体/供体数、TPSA、可旋转键数、环数、最大环、杂原子数 nHet、形式电荷 fChar、刚性键数 nRig、柔韧性 Flex、立体中心数 nStereo | SMILES 结构实时精确计算 |

另加 Morgan 指纹（radius=2，1024 bit）。推理管线：

```
SMILES → RDKit 特征 → SimpleImputer(median) → StandardScaler
       → 30 轮 PU Bagging 平均 → 入血概率
```

> **为什么用 PU Learning？** 中药成分"确定入血"的只有实验验证过的正样本，其余大量化合物是"未标注"而非"不入血"。PU 学习把未标注集反复抽样当负集训练再集成，避免把潜在正样本硬当负例造成的系统性偏差。

### 云端精简版（lite）

Render 免费实例仅 512MB 内存，加载完整版会 OOM。为此训练了精简版（Bagging 轮数 30→10）：

| | 完整版（本地默认） | 精简版（云端） |
|---|---|---|
| 文件体积 | 94.6MB | 31.7MB |
| 测试 ROC-AUC | 0.8129 | 0.8246 |
| 与完整版概率相关系数 | — | **0.9952** |

通过环境变量 `CCTCM_MODEL_FILE` 切换，见[配置说明](#配置说明)。

## 数据库设计

SQLite 单文件 `asthma-core/data/asthma_v2.db`（7.4MB，随仓库提交）。

### 数据规模

| 数据 | 数量 |
|------|------|
| 经典方剂 | 46 首 |
| 中药药材 | 279 味 |
| 入血预测化合物 | 569 个（双模型概率零空值） |
| 哮喘相关靶点 | 7,398 个 |
| 方剂-药材关联 | 246 条 |
| 药材-成分关联 | 1,504 条 |
| 成分-靶点关联 | 40,634 条 |
| 三维机制评分（GSEA） | 415 个化合物 |

### 核心表

| 表 | 说明 |
|----|------|
| `prescription` | 方剂（名称、组成描述、功效） |
| `herb` | 药材（性味归经、功效） |
| `compound` | 化合物。关键字段：`prob_cctcm`（主力模型概率）、`prob_herb`（兜底模型概率）、`radar_*_gsea`（三维疗效评分，真实 GSEA）、`asthma_related` |
| `target` | 靶点（基因名、哮喘相关性） |
| `rel_herb_compound` | 药材-成分多对多关联 |
| `rel_compound_target` | 成分-靶点多对多关联 |
| `rel_prescription_herb` | 方剂-药材关联（含剂量） |
| `user` | 用户（bcrypt 密码哈希，JWT 认证） |

**关于 `radar_*` 与 `radar_*_gsea`**：`radar_anti_inflammatory` / `radar_immune_regulation` / `radar_airway_repair` 三列是历史遗留字段，来源无法追溯，**不应在新分析中使用**。`radar_*_gsea` 三列是 2026-10 用真实 Enrichr 富集分析重算的结果，API 优先返回这组值。

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
| 方剂 | GET | `/prescriptions/{id}/radar` | 疗效雷达图数据（GSEA） |
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

> 数据库与模型文件均已随仓库提交，无需额外下载。

### 2. 启动后端（端口 8000）

```bash
cd asthma-core
pip install -r requirements.txt
cp .env.example .env        # 可选：改 JWT 密钥
python run.py
```

验证：访问 http://localhost:8000/docs 能看到 Swagger 文档。

> 首次调用预测接口需加载 94.6MB 模型（数秒），之后常驻内存。本地默认完整版模型。

### 3. 启动前端（端口 5173）

```bash
cd asthma-front
npm install
npm run dev
```

访问 http://localhost:5173 ，注册账号登录即可（首个注册用户即为系统用户，无默认账号）。

### 4. 一键启动（Windows）

仓库根目录执行 `startall.bat` 可同时拉起前后端（自动检测环境、创建虚拟环境、安装依赖）。

## 云端部署

### 后端 → Render

`asthma-core/render.yaml` 已就绪：

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
├── startall.bat               # Windows 一键启动
├── docs/                      # 数据质量报告
│   ├── 大创数据库数据质量诊断报告.md
│   ├── 大创数据库修复报告.md
│   └── 导师源数据质量核查报告.md
├── asthma-core/               # 后端
│   ├── run.py                 # 启动入口
│   ├── requirements.txt
│   ├── render.yaml            # Render 部署配置
│   ├── data/asthma_v2.db      # SQLite 数据库（7.4MB）
│   ├── scripts/               # 数据修复与质量核查脚本
│   └── app/
│       ├── main.py            # FastAPI 入口 + CORS + 异常处理
│       ├── core/              # 配置 + 数据库引擎
│       ├── models/tables.py   # ORM 模型
│       ├── schemas/           # Pydantic 请求/响应模型
│       ├── routers/           # 10 个路由模块
│       ├── services/          # ml.py / feature_engine.py / pharmacology.py
│       │                      # ai_service.py / auth.py
│       └── ml/pre-model/      # V2 模型 joblib + PU 类反序列化模块
├── asthma-front/              # 前端
│   ├── src/api/               # Axios 封装
│   ├── src/views/             # 13 个页面组件
│   ├── src/components/        # Layout / Sidebar / AiChat / ClickEffect
│   └── src/composables/       # 认证 / 设置持久化
└── 入血预测/                  # 模型训练工程（不部署）
    ├── cctcm2.0_v2/           # ccTCM V2 训练脚本 + 调参日志 + 结果
    └── herb2.0_v2/            # HERB V2 训练脚本 + 调参日志 + 结果
```

## 数据质量与溯源

本项目数据来自导师提供的 ccTCM 2.0 / HERB 2.0 数据集，在整合过程中做过系统性质量核查与修复，详细报告见 `docs/`：

| 报告 | 内容 |
|---|---|
| [数据质量诊断报告](docs/大创数据库数据质量诊断报告.md) | 发现并定位 5 类数据问题（药材-成分归属 99.2% 错误、理化属性随机数、三维评分无溯源等） |
| [数据库修复报告](docs/大创数据库修复报告.md) | 修复措施、验证结果、模型重训前后指标对比 |
| [源数据质量核查报告](docs/导师源数据质量核查报告.md) | 8 个源文件逐项核查（理化表 957 行错位、靶点跨物种歧义等） |

### 关键数据溯源

| 数据 | 来源 |
|---|---|
| 方剂组成 | `中药复方血中移行成分数据集.xlsx`（导师提供，46 首方剂完整组成） |
| 药材-成分归属 | `药材-化合物-含量-赵玉男.xlsx`（6,191 行文献含量数据） |
| 化合物结构 | `化合物数据_cctcm2.0.xlsx`（1,499 个化合物 SMILES） |
| 靶点关联 | `化合物作用靶点.xlsx`（40,634 条，含物种与活性值） |
| 理化性质 | RDKit 从 SMILES 计算 + 导师实测 ADME 值 |
| 入血概率 | PU Learning 双模型预测（`prob_cctcm` / `prob_herb`） |
| 三维机制评分 | Enrichr 在线富集分析（KEGG + GO Biological Process） |

### 已知限制

1. **ADME 特征部分缺失**：源表 957 行理化数据存在整行错位（原始值不可恢复），这些化合物的 LogS/LogD/Pgp/F20%/Caco-2/MDCK 由中位数填补，其余 12 个结构描述符已用 RDKit 精确重算。
2. **三维评分覆盖 415/569**：154 个化合物因人类蛋白靶点不足 2 个，无法做富集分析，其 `radar_*_gsea` 为空。
3. **入血标签只有正样本**：源数据仅标注"已知入血"成分，无明确负样本，这是采用 PU Learning 而非有监督分类的原因。模型指标应理解为"排序能力"而非"分类准确率"。

## License

本项目为重点大创项目，仅供学术研究使用。
