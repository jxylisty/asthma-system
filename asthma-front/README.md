# 东方智喘 - 前端应用

> Vue 3 + Element Plus + ECharts + Cytoscape.js 前端应用

## 技术栈

| 组件 | 用途 |
|------|------|
| Vue 3 (Composition API) | 前端框架 |
| Element Plus | UI 组件库（暗色主题定制） |
| ECharts 5 | 雷达图 / 柱状图 / 统计图表 |
| Cytoscape.js | 网络药理学拓扑图 |
| Vite 4 | 构建工具 |
| Vue Router 4 | 路由 |
| Axios | HTTP 请求（统一响应拦截） |
| xlsx | 批量预测文件解析（浏览器端预览） |
| marked + html2pdf.js | AI 报告 Markdown 渲染与 PDF 导出 |

## 目录结构

```
asthma-front/
├── index.html
├── package.json
├── vite.config.js             # 开发代理 /api → localhost:8000
├── start_all.bat              # Windows 一键启动前后端
└── src/
    ├── main.js                # 入口
    ├── App.vue                # 根组件
    ├── api/index.js           # Axios 实例 + 全部接口封装 + SSE 流式
    ├── composables/
    │   ├── useAuth.js         # JWT 认证状态
    │   ├── useAiSettings.js   # AI 供应商/Key 本地持久化
    │   ├── useSettings.js     # 用户偏好（模型默认值、阈值等）
    │   └── usePredictionHistory.js  # 预测历史 localStorage
    ├── components/
    │   ├── Layout.vue         # 主布局（侧边栏 + 内容区）
    │   └── Sidebar.vue        # 暗色侧边栏导航
    ├── views/                 # 13 个页面
    │   ├── Login.vue          # 登录/注册
    │   ├── Home.vue           # 首页（全局搜索 + 数据概览）
    │   ├── Prediction.vue     # 入血预测控制台
    │   ├── Prescriptions.vue  # 方剂列表
    │   ├── Detail.vue         # 方剂详情 + 网络药理学
    │   ├── Herbs.vue          # 中药列表
    │   ├── HerbDetail.vue     # 中药详情
    │   ├── Compounds.vue      # 化合物列表
    │   ├── CompoundDetail.vue # 化合物详情
    │   ├── CustomPrescription.vue  # 自定义方剂 + AI 报告
    │   ├── Expert.vue         # 专家模式（特征贡献度等）
    │   ├── NodeEditor.vue     # 网络图节点编辑
    │   └── Settings.vue       # 系统设置
    └── router/index.js        # 路由配置（登录守卫）
```

## 快速启动

```bash
npm install        # 安装依赖
npm run dev        # 开发服务器
npm run build      # 生产构建
```

开发服务器默认运行在 http://localhost:5173，请求代理到 http://localhost:8000（需先启动后端）。

首次使用需在登录页注册账号。

## API 代理配置

Vite 开发代理配置在 `vite.config.js`：

```js
server: {
  proxy: { '/api': 'http://localhost:8000' }
}
```

生产环境通过 Vercel 部署，API 地址在构建时指向 Render 后端域名。

## 页面功能

| 页面 | 路由 | 核心功能 |
|------|------|---------|
| 登录 | `/login` | JWT 注册/登录 |
| 首页 | `/` | 全局搜索（拼音首字母+药材反查）、数据概览、热门方剂 |
| 入血预测 | `/prediction` | 单化合物 SMILES 预测 + 批量文件预测 + ADME 实验值校准 + 预测历史 |
| 方剂列表 | `/prescriptions` | 46 首经典方剂分页浏览 |
| 方剂详情 | `/detail?id=` | 药材组成（含剂量）、入血化合物、Cytoscape 四层网络图、疗效雷达图 |
| 中药列表 | `/herbs` | 278 味中药，功效分类筛选 |
| 中药详情 | `/herbs/detail?id=` | 性味归经、含化合物及入血概率 |
| 化合物列表 | `/compounds` | 569 个化合物，概率阈值过滤、高潜专区 |
| 化合物详情 | `/compounds/detail?id=` | 双模型概率、分子结构、靶点、GSEA 雷达图 |
| 自定义方剂 | `/custom-prescription` | 自由组合中药 + AI 流式分析报告（可导出 PDF） |
| 专家模式 | `/expert` | 模型指标、特征贡献度分析视图 |
| 系统设置 | `/settings` | AI 供应商/Key 配置、预测默认偏好、缓存管理 |

## 入血预测页交互细节

- **模型切换**：CCTCM 2.0 高维模型（推荐）/ HERB 2.0 基础模型
- **特征展示**：CCTCM 结果分两栏——RDKit 拓扑特征（11 项，只读精确计算）+ ADME 特征（7 项，可校准）
- **ADME 校准**：预测后可编辑 ADME 值（LogS/LogD/LogP/Caco-2/MDCK/F20/P-gp），携带 `adme_overrides` 重新预测
- **预测前填实验值**：左侧表单可折叠的"ADME 实验值校准"面板，留空则算法推算
- **批量预测**：拖拽上传 .xlsx/.csv（含 SMILES 列，可选 ADME 实验值列），浏览器端预览前 10 行，结果下载 xlsx/csv
- **等级分档**：按模型工作阈值动态分档（ccTCM t=0.56 / HERB t=0.62；≥t+0.2 高 / ≥t 中 / 其余低）
- **预测历史**：localStorage 持久化，支持关键词搜索、一键回填、查看特征明细、单条删除

## AI 报告

自定义方剂页支持调用 AI 大模型生成深度分析报告：

- 兼容 OpenAI / DeepSeek 及任何 Chat Completions 协议端点（设置页配置）
- SSE 流式输出，Markdown 实时渲染
- API Key 仅存浏览器本地，请求时经 Header 传给后端转发，后端不落盘
- 报告支持导出 PDF（html2pdf.js）

## 搜索特性

首页搜索支持：

- 中文精确/模糊匹配
- 拼音首字母匹配（输入 `mh` 匹配"麻黄"）
- 药材名反查方剂（输入"麻黄"推荐含麻黄的方剂）
- 实时联想下拉（250ms 防抖）

## License

重点大创项目，仅供学术研究使用。
