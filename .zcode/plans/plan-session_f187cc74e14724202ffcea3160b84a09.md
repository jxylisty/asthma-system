# 食养有据（shiyang/frontend）品质级交互动效升级计划

## 调研结论（GitHub 高交互项目借鉴）

**核心洞察：这个项目 80% 的品质级动效不需要引库。** 2026 年的 CSS 已足够强大——`linear()` spring 缓动（三大引擎已铺开）、View Transitions API（iOS 18+/Chrome，不支持时自动直切无副作用）、`@starting-style` 纯 CSS 入场。引库仅在列表增删时值得考虑 auto-animate（5.5KB），其余均纯 CSS/小组件。

**学习的项目与范式**：
- **Apple Health/CareKit 健康范式**：环形进度 + count-up 数字同步 + 卡片按信息层级 stagger 入场
- **Headspace/Calm 治愈风**：呼吸圆环（scale 4s 循环 + blur 光晕）、流动渐变 blob、蒸汽上升
- **Linear 风**：hero 光斑跟随、卡片背后渐变光束（overflow:hidden + blur 容器）、滚动渐入
- **magicui（MIT, 22.8k★）**：光束卡片/文字动画思路可移植成 Vue/CSS；**uiverse.io（MIT）**：纯 HTML/CSS 按钮动效可直接抄
- **mobvue（Vue3+Vant 同栈精品模板）**：路由过渡工程组织参考

**明确不用**：motion-v（70KB 太重）、@vueuse/motion（停更）、lottie（77KB）、tsparticles（费电且不符调性）、Lenis（与 Vant 手势冲突）

**用户已确认**：范围=全量（地基+全页+彩蛋）；风格=治愈健康系为主+数据页科技点缀。

---

## 实施步骤

### 第一步：动效地基（全局令牌 + 公共样式 + 工具组件）

**1.1 全局动效令牌**（style.css）
- 定义 CSS 变量统一手感：`--spring-bounce: linear(0, 0.008, ... , 1)` 系列曲线变量（--ease-spring、--ease-out-soft、--dur-fast .2s、--dur-med .35s、--dur-slow .6s），全站 transition/animation 统一引用——手感一致的关键
- `prefers-reduced-motion` 全局降级：动画时长压到 0.01ms
- 移动端点击基建：`-webkit-tap-highlight-color: transparent`、`touch-action: manipulation`
- 抽公共 keyframes：`rise`（入场）、`shimmer`（骨架）、`pop`（弹跳确认）、`shake`（错误）、`steam`（蒸汽）——消除现有 3-4 份复制
- 全局可点反馈 class：`.pressable`（:active scale(0.97) spring）统一应用到卡片/按钮/选项

**1.2 工具组件/组合式函数**（新建 src/utils/ 或 components/motion/）
- `useCountUp(target)` composable：rAF + easeOutCubic 数字滚动（Home hero 已有雏形，抽出复用）
- `RingProgress.vue`：SVG 环形进度（stroke-dashoffset + spring transition + 圆头端点）
- `TextReveal.vue`：中文逐字 reveal（拆 span + --d 错峰，比引 GSAP SplitText 划算）
- 骨架屏统一：`van-skeleton` + 全局 shimmer class 替换各页自绘骨架

### 第二步：页面逐页升级（按体验差距从大到小）

**2.1 Quiz.vue 体质测评（最大短板，最值得精做）**
- 加载问卷时骨架屏（现在一片空白）
- 题目切换过渡：题目卡左右滑入（forward/back 方向感）
- 选项按压 spring + 选中弹跳 pop 动画
- 进度条 width 用 spring 缓动 + 轻微 overshoot
- 提交按钮 loading spinner（现在只有文字变"判定中…"）
- 答题→结果页 View Transition 硬切改平滑揭示
- 结果页：九维进度条从 0 生长动画、主体质卡 pop 入场、分数 count-up

**2.2 RecipeDetail.vue 方子详情（291 行最重页面）**
- **数据加载骨架屏**（现在全空白——最高优先级）
- 收藏 star pop 动画 + 成功 toast（现在打卡有 toast 收藏没有，补齐不对称）
- 配料图片懒加载淡入
- 三维机制进度条从 0 生长
- 网络图容器淡入 + loading 占位
- 返回顶部浮钮（长页）

**2.3 Home.vue 首页**
- hero 光斑跟随（`@media (hero:hover)` 桌面端增强，移动端静态光晕）
- hero 数字改用 useCountUp
- 今日推荐卡 pop 入场 + 桌面 hover 3D tilt（可选）
- 场景图标 hover 轻摆/按压反馈
- 时令横滑卡已好，微调即可

**2.4 Recipes.vue / Herbs.vue / Compounds.vue 三个列表页一致性补齐**
- 全部卡片加 `.pressable` 按压反馈（现在只有 Herbs 有）
- 筛选切换：旧列表淡出→新列表 stagger 重入（现在硬切重放）
- 筛选 tag 选中态过渡
- Compounds：概率条从 0 生长（现在半生效）、数字 count-up、考虑成分卡点击弹层（现在死路列表）
- Herbs：弹层内容渐入、搜索结果过渡
- 三页共用 stagger/shimmer 抽到全局（第一步已备好）

**2.5 Me.vue 我的**
- 字号分段控件滑动滑块动画
- 打卡七格 `.hit` 打勾 pop + `navigator.vibrate(10)` 触觉
- 体质分数对比 count-up
- 列表入场 stagger、骨架→内容交叉淡入
- **暗色模式切换圆形扩散彩蛋**：View Transitions API `clip-path: circle()` 从开关位置扩散（iOS 18+/Chrome 生效，其余直切）

**2.6 其余页面快赢项**
- Login：卡片入场、登录/注册模式切换高度过渡、错误 shake、按钮 loading 圈、input focus 过渡
- Constitution：骨架屏替换裸文字、入场动画、hero 体质主色渐变
- NotFound：叶子飘落小动效
- NetworkGraph：loading 占位（现在空白）、容器淡入、修复 resize 监听（expose 了 resize 但没人调）
- AIReport：idle→streaming 淡入、Key 行折叠高度过渡、打字机平滑输出
- SharePoster：生成中 spinner + 进度感、海报淡入缩放、长按保存引导文案

### 第三步：彩蛋与增强

- 暗色切换圆形扩散（已在 2.5）
- 空状态内联 SVG 动效（茶杯蒸汽上升、叶片轻摆——替代 van-empty 默认图，避免引 lottie）
- 桌面端 `@media (hover:hover)` 下 hero/场景卡 3D tilt + spotlight 光斑
- View Transitions API 路由过渡（push 滑入/pop 滑出方向感，不支持的浏览器自动降级）
- scroll-driven 阅读进度条（详情页顶部，`@supports` 包裹仅装饰）

### 第四步：验证

- `npm run build` 确认构建通过
- 逐页目视检查（dev server 起来后人工过一遍关键页面：Quiz 答题流、详情页加载、暗色切换）
- 检查 `prefers-reduced-motion` 下全部动画正确降级
- 确认无新依赖（package.json 不变）或仅 +auto-animate

## 关键约束

- **零新依赖**（至多 auto-animate 5.5KB），全靠 CSS + 小组件
- 暗色模式、字号调节（data-fontsize）两套主题变量体系不能破坏
- Vant 组件自带的过渡覆写时只动 enter/leave class，不动组件逻辑
- 所有动效 0.2–0.5s 完成（Apple HIG），关键确认时刻才允许 overshoot