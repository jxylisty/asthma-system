# shiyang 用户交互与设置增强

## 背景（现状盘点结论）

用户体系已完整（用户名密码 + JWT + bcrypt，user.db 独立库）；体质档案历史 + 两次对比、收藏增删查、AI 解读（BYO Key 流式）、网络图都可用。但体验层有明显缺口：

1. **分享海报是坏的**：`SharePoster.vue` 模板里没有 `<canvas ref="canvasEl">`，`draw()` 里 `canvasEl.value` 为 null 直接抛 TypeError——点「生成分享海报」只会弹一个空 popup，且每次进详情页都报错一次
2. **收藏状态不回显**：详情页 `favState` 初始为空，已收藏的方子永远显示「收藏」，重复点也不报错但用户不知情
3. **未登录点收藏 → 跳登录后丢失来源页**（`window.location.href='/login'`，登录成功固定跳 `/me`）
4. **「我的」页零设置项**：没有字号调节、没有暗色模式、没有清空本地数据
5. **无浏览历史**

用户确认范围（多选题未答复，按推荐的全部四项推进——均为高性价比、低风险项）。

## 实施步骤

### 1. 修复分享海报（SharePoster.vue）
- 模板 popup 内补 `<canvas ref="canvasEl" style="display:none">`，绘制仍走现有 draw() 逻辑
- 改为**打开 popup 时才 draw**（懒绘制）：watch `show`，首次打开才请求配方数据并绘制——省掉每次进详情页的无效请求和报错
- 保留 PNG 下载；下载文件名带方子名

### 2. 收藏体验闭环
- **详情页回显**：登录状态下 onMounted 时调一次 `listFavorites()`，把已收藏 id 填进 `favState`，按钮显示「取消收藏」+ 实星
- **登录回跳**：未登录点收藏 → `router.push({ path: '/login', query: { redirect: 当前详情页路径 } })`；Login.vue 登录/注册成功后优先跳 `route.query.redirect`，无则 `/me`
- Recipes.vue 与 Me.vue 的收藏列表行加实心星标（本地比对即可：Me 页数据本来就来自收藏接口；列表页仅登录用户显示已收藏标记，需调 listFavorites 比对——仅一次请求）
- 切换路由到其他详情页时重置/重查 favState（watch route.params.id）

### 3. 浏览历史（纯本地，不动后端）
- api 层新增 `pushHistory(recipe)` / `getHistory()` / `clearHistory()`：localStorage key `shiyang_history_v1`，存 `{id, name, type, oneliner, ts}` 数组，去重置顶，上限 20 条
- RecipeDetail 加载成功后 pushHistory
- Me.vue 加「最近浏览」区块（最多显示 5 条 + 「清空」按钮），未登录也可用
- 注意：清空历史按钮需 `van-dialog.confirm` 二次确认，防误触

### 4. 设置中心（Me.vue 内新增「设置」卡片 + 全局生效）
- **字号调节**：`html[data-fontsize]` 三档（标准/大/特大，对应根字号 16/17.5/19px），style.css 的 body 字号与行高改为相对 `rem` 不必全面重做——只对正文内容容器 `.page` 设置 `font-size: calc(...)` 方案，避免 Vant 组件被强行放大走样；localStorage `shiyang_fontscale`
- **暗色模式**：Vant 4 自带 `van-theme-dark`（`ConfigProvider` + `<html class="van-theme-dark">`）。现有 CSS 变量已集中管理，补一组 `[data-theme="dark"]` 覆盖（--bg/--card/--ink-*），Vant 组件用其官方 dark 变量。localStorage `shiyang_theme`，App.vue 启动时读取并设 `document.documentElement.dataset`
- **清空本地数据**：一键清 `shiyang_quiz_v1`、`shiyang_history_v1`、`shiyang_ai_key`（不动 token，登录态保留），`van-dialog.confirm` 确认 + `van-toast` 成功提示
- 设置项持久化用 localStorage（与现有「个性化全本地」的架构一致，不动后端 user 表）

### 5. 顺手小修（盘点发现的技术债，低风险）
- `main.py`：`/constitution/{code}` 路由目前定义在 `if __name__ == "__main__"` 之后（uvicorn 启动时注册不到的风险点）——移到其上方
- 收藏 401 时也带 redirect 参数

## 不做什么
- 不做改昵称/改密码/注销账号（需要新后端端点+表变更，下一轮）
- 不做 AI 服务端托管 Key（涉密钥管理，需与导师确认）
- 不做后端浏览历史表（本地方案已满足，且未登录可用）

## 验证
- `npm run build` 通过
- 浏览器 390px + 1440px 双端回归：海报生成与下载、收藏回显/取消、未登录收藏→登录→回跳原方子、浏览历史记录与清空、字号三档切换、暗色模式切换（重点看方子卡/成分说明书的可读性）、清空本地数据
- 回归确认不破坏：测评提交链路、Me 页档案对比、AI 解读

## 涉及文件
- `frontend/src/components/SharePoster.vue`（修 canvas + 懒绘制）
- `frontend/src/views/RecipeDetail.vue`（收藏回显 + redirect + pushHistory）
- `frontend/src/views/Login.vue`（redirect 支持）
- `frontend/src/views/Me.vue`（浏览历史 + 设置卡片）
- `frontend/src/App.vue`（启动时应用字号/主题 + ConfigProvider）
- `frontend/src/api/index.js`（history 工具函数）
- `frontend/src/style.css`（暗色变量 + 字号档位）
- `backend/app/main.py`（路由位置小修）