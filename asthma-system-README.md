# 儿童哮喘入血预测系统

> 基于入血预测的中医治疗儿童哮喘作用机制分析 · 省级重点大创项目

## 项目结构

| 仓库 | 技术栈 | 说明 |
|------|--------|------|
| [asthma-core](https://github.com/jxylisty/asthma-core) | FastAPI + SQLAlchemy + SQLite | 后端 API 服务 |
| [asthma-front](https://github.com/jxylisty/asthma-front) | Vue 3 + Element Plus + ECharts | 前端 Web 应用 |

## 快速启动

### 1. 克隆前后端

```bash
git clone https://github.com/jxylisty/asthma-core.git
git clone https://github.com/jxylisty/asthma-front.git
```

### 2. 下载数据库

后端运行需要数据库文件，请从 asthma-core Release 下载：

- [下载 asthma_v2.db.zip](https://github.com/jxylisty/asthma-core/releases/latest)
- 解压到 `asthma-core/data/asthma_v2.db`

### 3. 启动后端

```bash
cd asthma-core
pip install -r requirements.txt
cp .env.example .env   # 可选：编辑 .env 配置 JWT 密钥
python run.py
```

后端启动后访问：
- API 文档：http://localhost:8000/docs

### 4. 启动前端

```bash
cd asthma-front
npm install
npm run dev
```

前端访问：http://localhost:5173

## 配置说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DB_PATH` | 数据库文件路径 | `data/asthma_v2.db` |
| `JWT_SECRET_KEY` | JWT 签名密钥 | `dev-secret-change-in-production` |

## 数据库说明

数据库文件 `asthma_v2.db` 不直接提交到 Git，通过 GitHub Release 分发：

- 包含 46 首方剂、278 味中药、569 个化合物、哮喘靶点
- 每味药材在方剂中的精确剂量
- 双模型（ccTCM + HERB）入血预测概率

如需最新版本数据库，请关注 [asthma-core Releases](https://github.com/jxylisty/asthma-core/releases)。
