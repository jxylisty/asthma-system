# 儿童哮喘方剂智能分析系统

> 基于入血预测的中医治疗儿童哮喘作用机制分析 · 校级重点大创项目

## 项目简介

本项目融合 AI 入血预测（PU Learning 双模型）、网络药理学拓扑分析和 GSEA 富集分析，
为中医治疗儿童哮喘提供从分子到靶点的全链条智能分析平台。

### 核心能力

- **双模型入血预测**：ccTCM 2.0（19维特征）+ HERB 2.0（7维特征），预测中药化合物入血概率
- **网络药理学拓扑**：方剂→药材→化合物→靶点四层网络可视化
- **GSEA 富集分析**：实时调用 Enrichr 通路富集，输出抗炎/免疫/气道修复雷达图
- **智能搜索**：支持拼音首字母、药材名反查方剂等模糊匹配

## 项目结构

```
asthma-system/
├── asthma-core/       # FastAPI 后端 API 服务
├── asthma-front/      # Vue 3 + Element Plus 前端应用
└── README.md
```

| 子项目 | 技术栈 | 独立仓库 |
|--------|--------|---------|
| asthma-core | FastAPI + SQLAlchemy + SQLite | [jxylisty/asthma-core](https://github.com/jxylisty/asthma-core) |
| asthma-front | Vue 3 + Element Plus + ECharts | [jxylisty/asthma-front](https://github.com/jxylisty/asthma-front) |

## 快速启动

### 前提条件

- Python >= 3.10
- Node.js >= 18
- Git

### 1. 克隆项目

```bash
git clone https://github.com/jxylisty/asthma-system.git
cd asthma-system
```

### 2. 下载数据库

后端运行需要数据库文件，请从 [asthma-core Releases](https://github.com/jxylisty/asthma-core/releases) 下载：

- 下载 `asthma_v2.db.zip`
- 解压到 `asthma-core/data/asthma_v2.db`

### 3. 启动后端

```bash
cd asthma-core
pip install -r requirements.txt
cp .env.example .env   # 可选：编辑 JWT 密钥
python run.py
```

后端 API 文档：http://localhost:8000/docs

### 4. 启动前端

```bash
cd asthma-front
npm install
npm run dev
```

前端地址：http://localhost:5173

## 数据库

数据库 `asthma_v2.db` 包含：

| 数据 | 数量 |
|------|------|
| 经典方剂 | 46 首 |
| 涵盖中药 | 278 味 |
| 入血预测化合物 | 569 个 |
| 哮喘相关靶点 | 7398 个 |

每味药材在方剂中标注了精确剂量。数据库通过 GitHub Release 分发，不直接提交到 Git。

## 配置说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DB_PATH` | 数据库路径 | `data/asthma_v2.db` |
| `JWT_SECRET_KEY` | JWT 签名密钥 | `dev-secret-change-in-production` |
| `CORS_ORIGINS` | 允许的跨域域名 | `http://localhost:5173` |

## License

本项目为校级重点大创项目，仅供学术研究使用。
