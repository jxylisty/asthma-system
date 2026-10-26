# 「食养有据」前端填充改造计划

## 诊断结论

「空荡荡」的根源不是数据少（73 方/34 药材/165 化合物/2807 靶点都已入库），而是：
1. **列表全是两行纯文字**：Home/Recipes 的方子卡片无图无视觉停留点，56 张食材图只用在详情页 44px 小图
2. **数据资产没有可逛页面**：后端 `/herbs`（34味药材，含性味归经功效）、`/compounds`（165化合物，含双模型入血概率）接口已就绪，前端没有对应页面
3. **无骨架屏/无动效**：加载态是文字「加载中…」，页面无过渡无入场动画
4. **AI 解读要自备 API Key**，对普通用户等于不存在
5. 海报无二维码，无拉新闭环

## 实施方案

### A. 视觉填充（纯前端 + 现有接口）

**A1. 方子卡片图文化**
- `fetch_material_images.py` 已有 56 张 480px CC0/PD 图片，按高频配料名补齐缺口（冰糖、麦冬已有没有的：枣→大枣映射、蜜枣、猪瘦肉→猪肉、铁皮石斛→石斛、芡实、鲜芦根、花生等，约 20 张）
- Recipes.vue / Home.vue 卡片改为「左图右文」布局：首味配料图做封面（或按茶饮/药膳给品牌渐变兜底），加时长/体质标签
- `api/index.js` 加 `matImg(name)` 工具函数统一图片路径与 onerror 兜底

**A2. 首页「活」起来**
- hero 下新增「今日茶饮」卡片：按日期从 73 方轮换推荐 1 方（`Math.floor(Date.now()/86400000) % n` 纯前端即可），带图
- 新增「时令场景」横滑区：把换季调理（25方，最大场景）等做成可横滑的图片场景卡
- hero-stats 数字加滚动动画（纯 CSS/JS，不引库）

**A3. 骨架屏与微动效**
- Recipes/Me/Home 列表加载态换成 Vant `van-skeleton` 卡片骨架
- 卡片入场用 CSS `@keyframes` 淡入上移错峰（stagger）动画
- 路由切换加页面级 fade 过渡

### B. 新功能页（接口已就绪，只补前端）

**B1. 药材图鉴 `/herbs`**（新页面 Herbs.vue + 路由）
- 搜索 + 按拼音/化合物数排序的网格卡片（图 + 性味 + 功效摘要）
- 点击展开 popup 详情：性味归经、功效、含多少化合物
- 数据源：`GET /api/v1/herbs?q=`

**B2. 成分库 `/compounds`**（新页面 Compounds.vue + 路由）
- 按入血概率排序的卡片列表，入血概率双模型对比条（ccTCM vs HERB）
- 三维雷达分（抗炎/免疫/气道修复）用小进度条展示
- 数据源：`GET /api/v1/compounds?min_prob=`
- 导航栏加「药材」「成分」入口；首页 stats 区也可挂跳转

**B3. 体质详情页 `/constitution/:code`**（新页面，可选小页面）
- 数据源 `GET /api/v1/constitution/{code}`（现仅在测评结果内联使用）
- 测评结果页的体质徽章可点击跳转

### C. 小量后端改动的新能力（用户已确认三项都要）

**C1. AI 免门槛化（预生成解读）**
- `ai_service.py` 加 `pregen_report(recipe_id)`：用环境变量里的平台级 DeepSeek key（`SHIYANG_AI_KEY`）为 69 个 analysis_ready 方子预生成解读，存入新表 `recipe_pregen_ai`（一次性脚本跑）
- `/recipes/{rid}/ai-report` 改为：有用户 key 走实时 SSE（现有逻辑不动）；无 key 先查预生成表，命中则以 SSE 节奏流式回放（保留打字机体验）
- 前端 AIReport.vue 去掉「必须填 Key」的阻断态，改为「AI 解读」直接可看 + 可选自带 Key 获得更个性解读

**C2. 饮用打卡**
- 后端：user.db 加 `checkin` 表（uid, recipe_id, date, note），`POST/DELETE /checkins/{rid}`、`GET /checkins`（含连续天数统计）
- 前端：RecipeDetail 头部加「今日打卡」按钮；Me 页加「本周打卡」卡片（周视图格子 + 连续天数），方子库卡片已打卡的显示对勾

**C3. 海报二维码**
- `SharePoster.vue` 用 `qrcode` npm 包（前端生成 dataURL）画到海报右下角，扫码直达站点首页
- 站点 URL 从 `window.location.origin` 取，本地/线上都能用

### D. 不做（明确排除）
- Vercel/Render 部署配置（用户确认本次不做）
- CCMQ 逆向计分核对（属数据正确性，另开任务）
- TCMSP 补 32 味药材数据（属数据建设，另开任务）
- requirements.txt 补 httpx/bcrypt/python-jose（顺手做，1 分钟）

## 实施顺序

1. **A3 + A1**：骨架屏动效 + 卡片图文（最大程度消除空旷感）
2. **A2**：首页改造
3. **B1/B2**：药材图鉴 + 成分库两个新页面
4. **C1**：AI 免门槛（预生成脚本 + 接口改造）
5. **C2**：打卡（后端表 + 接口 + 前端）
6. **C3**：海报二维码
7. 顺手：requirements.txt 补依赖；启动前后端跑一遍全部页面验证

## 验证方式

- 本地起后端（127.0.0.1:8100）+ 前端（5174），逐页检查：Home/Recipes/RecipeDetail/Herbs/Compounds/Me/Quiz
- 打卡走通：登录 → 详情打卡 → Me 周视图显示
- AI 解读无 Key 打开详情页可直接看到流式输出
- 海报下载后扫码能打开站点