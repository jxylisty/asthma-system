# 儿童哮喘方剂智能分析系统 - 前端

> Vue 3 + Element Plus + ECharts + Cytoscape.js 前端应用

## 技术栈

| 组件 | 用途 |
|------|------|
| Vue 3 (Composition API) | 前端框架 |
| Element Plus | UI 组件库 |
| ECharts 5 | 雷达图 / 柱状图 / 热力图 |
| Cytoscape.js | 网络药理学拓扑图 |
| Vite 4 | 构建工具 |
| Vue Router 4 | 路由 |
| Pinia | 状态管理（认证） |
| Axios | HTTP 请求 |

## 目录结构

```
asthma-front/
├── index.html
├── package.json
├── vite.config.js
├── .env                       # 环境变量（API 代理地址）
├── .gitignore
└── src/
    ├── main.js                # 入口
    ├── App.vue                # 根组件
    ├── api/
    │   └── index.js           # API 封装（Axios 实例 + 响应拦截）
    ├── composables/
    │   ├── useAuth.js         # 认证逻辑
    │   ├── useAiSettings.js   # AI 配置持久化
    │   └── useSettings.js     # 用户偏好设置
    ├── components/
    │   ├── Layout.vue         # 主布局（侧边栏 + 内容区）
    │   └── Sidebar.vue        # 暗色侧边栏导航
    ├── views/
    │   ├── Login.vue          # 登录页
    │   ├── Home.vue           # 首页（搜索 + 快捷入口 + 热门方剂）
    │   ├── Prediction.vue     # 入血预测控制台
    │   ├── Prescriptions.vue  # 方剂列表
    │   ├── Detail.vue         # 方剂详情 + 网络药理学
    │   ├── Herbs.vue          # 中药列表
    │   ├── HerbDetail.vue     # 中药详情
    │   ├── Compounds.vue      # 化合物列表
    │   ├── CompoundDetail.vue # 化合物详情
    │   ├── CustomPrescription.vue  # 自定义方剂分析
    │   └── Settings.vue       # 系统设置
    └── router/
        └── index.js           # 路由配置
```

## 快速启动

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

开发服务器默认运行在 http://localhost:5173，请求代理到 http://localhost:8000。

## API 代理配置

Vite 开发代理配置在 `vite.config.js`：

```js
server: {
  proxy: {
    '/api': 'http://localhost:8000'
  }
}
```

## 页面功能

| 页面 | 路由 | 核心功能 |
|------|------|---------|
| 登录 | `/login` | JWT 认证 |
| 首页 | `/` | 全局搜索（拼音首字母+药材反查）、数据概览、快捷入口 |
| 入血预测 | `/prediction` | 单化合物 + 批量文件预测、ADME 实验值校准 |
| 方剂列表 | `/prescriptions` | 46首经典方剂分页列表 |
| 方剂详情 | `/detail?id=` | 药材组成、化合物入血概率、Cytoscape 网络图 |
| 中药列表 | `/herbs` | 278味中药浏览 |
| 化合物列表 | `/compounds` | 569个化合物高潜筛选 |
| 自定义方剂 | `/custom-prescription` | 自由组合中药 + AI 分析 |
| 系统设置 | `/settings` | AI 配置、预测偏好、数据缓存管理 |

## 搜索特性

首页搜索支持：
- 中文精确/模糊匹配
- 拼音首字母匹配（输入 `mh` 匹配"麻黄"）
- 药材名反查方剂（输入"麻黄"推荐含麻黄的方剂）
- 实时联想下拉（250ms 防抖）

## License

省级重点大创项目，仅供学术研究使用。
