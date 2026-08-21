<template>
  <template v-if="isLoginPage">
    <router-view />
  </template>
  <template v-else>
    <Layout />
    <ClickEffect />
  </template>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Layout from './components/Layout.vue'
import ClickEffect from './components/ClickEffect.vue'

const route = useRoute()
const isLoginPage = computed(() => route.path === '/login')
</script>

<style>
/* ===== 全局主题变量（统一设计规范） ===== */
:root {
  --bg-primary: #0b1120;
  --bg-secondary: #1e293b;
  --bg-card: rgba(30, 41, 59, 0.7);
  --bg-card-hover: rgba(30, 41, 59, 0.9);
  --bg-gradient: #0b1120;

  --color-primary: #2dd4bf;
  --color-primary-light: #5eead4;
  --color-primary-dark: #14b8a6;
  --color-secondary: #38bdf8;
  --color-accent: #a78bfa;

  --text-color: #f1f5f9;
  --text-secondary: #cbd5e1;
  --text-muted: #94a3b8;
  --text-disabled: #64748b;

  --border-color: rgba(255, 255, 255, 0.08);
  --border-color-hover: rgba(45, 212, 191, 0.3);

  --color-success: #34d399;
  --color-warning: #fbbf24;
  --color-danger: #f87171;
  --color-info: #60a5fa;

  --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;

  /* ===== 字体层级规范（H1 → H2 → H3 → 正文 → 辅助 → 最小） ===== */
  --fs-h1: 28px;        /* 页面主标题 */
  --fs-h2: 22px;        /* 模块 / 卡片标题 */
  --fs-h3: 18px;        /* 子模块 / 条目标题 */
  --fs-body: 14px;      /* 正文默认（正文、数值、列表） */
  --fs-sub: 12px;       /* 辅助：key 标签、时间、次要信息 */
  --fs-tiny: 11px;      /* 最小：角标、说明、小标签 */
  --fs-display: 36px;   /* 登录/首页展示性大标题 */

  --fw-black: 900;
  --fw-bold: 800;
  --fw-semi: 600;
  --fw-medium: 500;
  --fw-regular: 400;

  --font-size-base: var(--fs-body);
  --font-size-sm: var(--fs-sub);
  --font-size-lg: var(--fs-h3);

  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;

  --shadow-card-sm: 0 2px 8px rgba(0, 0, 0, 0.18);
  --shadow-card: 0 4px 20px rgba(0, 0, 0, 0.22);
  --shadow-card-lg: 0 12px 40px rgba(0, 0, 0, 0.35);
  --shadow-hover: 0 8px 30px rgba(0, 0, 0, 0.3);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  width: 100%;
  height: 100%;
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #0b1120 !important;
  color: var(--text-color);
}

html {
  background-color: #0b1120 !important;
}

#app {
  width: 100%;
  min-height: 100vh;
  background: #0b1120;
}

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.3);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.5);
}

::selection {
  background: rgba(45, 212, 191, 0.25);
  color: var(--text-color);
}

/* ===== Element Plus 全局暗色主题覆盖 ===== */
.el-card {
  background: var(--bg-card) !important;
  border: 1px solid var(--border-color) !important;
  border-radius: var(--radius-md) !important;
  color: var(--text-color) !important;
  backdrop-filter: blur(10px);
}

.el-card__header {
  border-bottom: 1px solid var(--border-color) !important;
  padding: 16px 20px !important;
}

.el-card__body {
  padding: 20px !important;
  color: var(--text-color) !important;
}

.el-input__wrapper {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid var(--border-color) !important;
  box-shadow: none !important;
  border-radius: var(--radius-sm) !important;
}

.el-input__wrapper:hover {
  border-color: var(--border-color-hover) !important;
}

.el-input__wrapper.is-focus {
  border-color: var(--color-primary) !important;
  box-shadow: 0 0 0 2px rgba(45, 212, 191, 0.1) !important;
}

.el-input__inner {
  color: var(--text-color) !important;
}

.el-input__inner::placeholder {
  color: var(--text-disabled) !important;
}

.el-textarea__inner {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid var(--border-color) !important;
  color: var(--text-color) !important;
  border-radius: var(--radius-sm) !important;
}

.el-textarea__inner:focus {
  border-color: var(--color-primary) !important;
}

.el-form-item__label {
  color: var(--text-secondary) !important;
}

.el-radio__label {
  color: var(--text-secondary) !important;
}

.el-radio.is-checked .el-radio__label {
  color: var(--color-primary) !important;
}

.el-radio__inner {
  background: transparent !important;
  border-color: var(--text-disabled) !important;
}

.el-radio__input.is-checked .el-radio__inner {
  background: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
}

.el-button--primary {
  background: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
  color: #0f172a !important;
  font-weight: 600;
}

.el-button--primary:hover {
  background: var(--color-primary-light) !important;
  border-color: var(--color-primary-light) !important;
}

.el-button {
  border-radius: var(--radius-sm) !important;
}

.el-tag {
  border-radius: 4px !important;
}

.el-table {
  background: transparent !important;
  color: var(--text-secondary) !important;
}

.el-table th.el-table__cell {
  background: rgba(255, 255, 255, 0.03) !important;
  color: var(--text-color) !important;
  border-bottom: 1px solid var(--border-color) !important;
}

.el-table td.el-table__cell {
  border-bottom: 1px solid var(--border-color) !important;
}

.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell {
  background: rgba(255, 255, 255, 0.02) !important;
}

.el-table__body tr:hover > td.el-table__cell {
  background: rgba(45, 212, 191, 0.05) !important;
}

.el-tabs__item {
  color: var(--text-muted) !important;
}

.el-tabs__item.is-active {
  color: var(--color-primary) !important;
}

.el-tabs__active-bar {
  background-color: var(--color-primary) !important;
}

.el-tabs__nav-wrap::after {
  background-color: var(--border-color) !important;
}

.el-dialog {
  background: #1e293b !important;
  border: 1px solid rgba(255,255,255,0.1) !important;
  border-radius: 12px !important;
  color: #f1f5f9 !important;
  box-shadow: 0 16px 48px rgba(0,0,0,0.6) !important;
  z-index: 9999 !important;
}

.el-dialog__header {
  padding: 20px 24px 0 !important;
}

.el-dialog__title {
  color: #f8fafc !important;
  font-weight: 600 !important;
  font-size: 16px !important;
}

.el-dialog__body {
  color: #cbd5e1 !important;
  padding: 20px 24px !important;
}

.el-dialog__footer {
  padding: 12px 24px 20px !important;
}

/* 弹窗内表格适配 */
.el-dialog .el-table {
  --el-table-bg-color: #1e293b;
  --el-table-tr-bg-color: #1e293b;
  --el-table-text-color: #e2e8f0;
  --el-table-header-bg-color: #0f172a;
  --el-table-header-text-color: #f8fafc;
  --el-table-border-color: rgba(255,255,255,0.08);
  background: #1e293b !important;
}
.el-dialog .el-table th.el-table__cell {
  background: #0f172a !important;
  color: #f8fafc !important;
  border-bottom: 1px solid rgba(255,255,255,0.1) !important;
}
.el-dialog .el-table td.el-table__cell {
  border-bottom: 1px solid rgba(255,255,255,0.05) !important;
}
.el-dialog .el-table--striped .el-table__body tr.el-table__row--striped td {
  background: rgba(255,255,255,0.02) !important;
}

.el-drawer {
  background: var(--bg-secondary) !important;
  color: var(--text-color) !important;
}

.el-drawer__header {
  color: var(--text-color) !important;
  border-bottom: 1px solid var(--border-color) !important;
}

.el-select-dropdown {
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-color) !important;
}

.el-select-dropdown__item {
  color: var(--text-secondary) !important;
}

.el-select-dropdown__item.hover,
.el-select-dropdown__item:hover {
  background: rgba(45, 212, 191, 0.1) !important;
  color: var(--color-primary) !important;
}

.el-select-dropdown__item.selected {
  color: var(--color-primary) !important;
  font-weight: 600;
}

.el-message-box {
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-color) !important;
  border-radius: var(--radius-lg) !important;
  color: var(--text-color) !important;
  box-shadow: 0 12px 48px rgba(0,0,0,0.5) !important;
}

.el-message-box__header {
  padding: 20px 24px 0 !important;
}

.el-message-box__title {
  color: var(--text-color) !important;
  font-size: 16px !important;
  font-weight: 700 !important;
}

.el-message-box__message {
  color: var(--text-secondary) !important;
  padding: 16px 24px !important;
  font-size: 14px !important;
}

.el-message-box__btns {
  padding: 12px 24px 20px !important;
}

.el-message-box__btns .el-button {
  border-radius: 8px !important;
  padding: 8px 20px !important;
  font-weight: 600 !important;
}

.el-message-box__btns .el-button--primary {
  background: var(--color-danger) !important;
  border-color: var(--color-danger) !important;
  color: #fff !important;
}

.el-message-box__btns .el-button--primary:hover {
  background: #ef4444 !important;
  border-color: #ef4444 !important;
}

.el-popover {
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-color) !important;
  color: var(--text-color) !important;
}

.el-collapse {
  border-top: 1px solid var(--border-color) !important;
  border-bottom: 1px solid var(--border-color) !important;
}

.el-collapse-item__header {
  background: transparent !important;
  color: var(--text-secondary) !important;
  border-bottom: 1px solid var(--border-color) !important;
}

.el-collapse-item__wrap {
  background: transparent !important;
  border-bottom: 1px solid var(--border-color) !important;
}

.el-collapse-item__content {
  color: var(--text-muted) !important;
}

.el-upload-dragger {
  background: rgba(255, 255, 255, 0.03) !important;
  border: 2px dashed var(--border-color) !important;
}

.el-upload-dragger:hover {
  border-color: var(--color-primary) !important;
}

.el-upload__text {
  color: var(--text-secondary) !important;
}

.el-upload__text em {
  color: var(--color-primary) !important;
  font-style: normal;
}

.el-progress-bar__outer {
  background: rgba(255, 255, 255, 0.06) !important;
}

.el-slider__runway {
  background: rgba(255, 255, 255, 0.1) !important;
}

.el-slider__bar {
  background: var(--color-primary) !important;
}

.el-slider__button {
  border-color: var(--color-primary) !important;
}

.el-input-number__decrease,
.el-input-number__increase {
  background: rgba(255, 255, 255, 0.04) !important;
  color: var(--text-secondary) !important;
  border-color: var(--border-color) !important;
}

.el-divider {
  background-color: var(--border-color) !important;
}

/* ===== 分页组件暗色主题 ===== */
.el-pagination {
  background: var(--bg-card) !important;
  padding: 12px 16px !important;
  border-radius: var(--radius-md) !important;
  border: 1px solid var(--border-color) !important;
  color: var(--text-secondary) !important;
  backdrop-filter: blur(10px);
}

.el-pagination .el-pagination__total {
  color: var(--text-secondary) !important;
}

.el-pagination .el-pagination__sizes .el-input .el-input__wrapper {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid var(--border-color) !important;
}

.el-pagination .btn-prev,
.el-pagination .btn-next {
  background: rgba(255, 255, 255, 0.04) !important;
  color: var(--text-secondary) !important;
}

.el-pagination .el-pager li {
  background: rgba(255, 255, 255, 0.04) !important;
  color: var(--text-secondary) !important;
  border-radius: 4px !important;
  margin: 0 2px !important;
}

.el-pagination .el-pager li:hover {
  color: var(--color-primary) !important;
}

.el-pagination .el-pager li.is-active {
  background: var(--color-primary) !important;
  color: #0f172a !important;
  font-weight: 600;
}

.el-pagination .el-pagination__jump {
  color: var(--text-secondary) !important;
}

.el-pagination .el-pagination__jump .el-input__wrapper {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid var(--border-color) !important;
}

/* ===== 标签组件暗色主题 ===== */
.el-tag {
  background: rgba(255, 255, 255, 0.06) !important;
  border: 1px solid var(--border-color) !important;
  color: var(--text-secondary) !important;
}

.el-tag--info {
  background: rgba(148, 163, 184, 0.15) !important;
  border-color: rgba(148, 163, 184, 0.3) !important;
  color: #cbd5e1 !important;
}

.el-tag--success {
  background: rgba(52, 211, 153, 0.15) !important;
  border-color: rgba(52, 211, 153, 0.3) !important;
  color: #34d399 !important;
}

.el-tag--warning {
  background: rgba(251, 191, 36, 0.15) !important;
  border-color: rgba(251, 191, 36, 0.3) !important;
  color: #fbbf24 !important;
}

.el-tag--danger {
  background: rgba(248, 113, 113, 0.15) !important;
  border-color: rgba(248, 113, 113, 0.3) !important;
  color: #f87171 !important;
}

.el-tag--primary {
  background: rgba(45, 212, 191, 0.15) !important;
  border-color: rgba(45, 212, 191, 0.3) !important;
  color: var(--color-primary) !important;
}

/* ===== 下拉菜单暗色主题 ===== */
.el-dropdown-menu {
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-color) !important;
  border-radius: var(--radius-md) !important;
  padding: 6px !important;
}

.el-dropdown-menu__item {
  color: var(--text-secondary) !important;
  border-radius: 4px !important;
}

.el-dropdown-menu__item:hover {
  background: rgba(45, 212, 191, 0.1) !important;
  color: var(--color-primary) !important;
}

/* ===== 日期/时间选择器暗色主题 ===== */
.el-picker-panel {
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-color) !important;
  color: var(--text-color) !important;
}

.el-date-table th {
  color: var(--text-muted) !important;
}

.el-date-table td.available:hover {
  background: rgba(45, 212, 191, 0.1) !important;
}

.el-date-table td.today .el-date-table-cell__text {
  color: var(--color-primary) !important;
}

/* ===== 开关组件 ===== */
.el-switch__core {
  background: rgba(255, 255, 255, 0.15) !important;
  border-color: var(--border-color) !important;
}

.el-switch.is-checked .el-switch__core {
  background: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
}

/* ===== 复选框 ===== */
.el-checkbox__label {
  color: var(--text-secondary) !important;
}

.el-checkbox__inner {
  background: rgba(255, 255, 255, 0.04) !important;
  border-color: var(--text-disabled) !important;
}

.el-checkbox__input.is-checked .el-checkbox__inner {
  background: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
}

/* ===== 空状态 ===== */
.el-empty__description p {
  color: var(--text-muted) !important;
}

/* ===== 面包屑 ===== */
.el-breadcrumb__inner {
  color: var(--text-muted) !important;
}

.el-breadcrumb__inner.is-link:hover {
  color: var(--color-primary) !important;
}

/* ===== 加载动画 ===== */
.el-loading-mask {
  background: rgba(15, 23, 42, 0.8) !important;
}

.el-loading-text {
  color: var(--color-primary) !important;
}

/* ===== 原生表单控件暗色主题 ===== */
select {
  background-color: var(--bg-secondary) !important;
  color: var(--text-color) !important;
  border: 1px solid var(--border-color) !important;
  color-scheme: dark;
}

select option {
  background: var(--bg-secondary) !important;
  color: var(--text-color) !important;
  padding: 8px 12px;
}

select option:hover,
select option:checked {
  background: rgba(45, 212, 191, 0.2) !important;
  color: var(--color-primary) !important;
}

input[type="text"],
input[type="number"],
input[type="password"],
input[type="email"],
input[type="search"],
input[type="tel"],
input[type="url"],
textarea {
  color: var(--text-color) !important;
}

input::placeholder,
textarea::placeholder {
  color: var(--text-disabled) !important;
}

/* ===== 通用白色背景兜底修复 ===== */
[style*="background-color: rgb(255, 255, 255)"],
[style*="background-color: #fff"],
[style*="background-color: #ffffff"],
[style*="background: rgb(255, 255, 255)"],
[style*="background: #fff"],
[style*="background: #ffffff"] {
  background-color: var(--bg-card) !important;
  background: var(--bg-card) !important;
}




/* ===== 弹窗在内容区域居中，不被侧边栏遮挡 ===== */
.el-overlay {
  z-index: 9998 !important;
}
.el-overlay-dialog {
  z-index: 9999 !important;
  padding-left: 230px !important;
  box-sizing: border-box !important;
}
.el-drawer {
  z-index: 9999 !important;
}

/* ===== 全局语音播报按钮：统一样式 + 彻底解决"看不清" ===== */
.el-button.speech-btn,
.el-button.rx-speech {
  color: var(--text-secondary) !important;
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(148,163,184,0.18) !important;
  border-radius: 6px !important;
  padding: 4px 10px !important;
  min-width: 44px !important;
  transition: all 0.2s ease !important;
}
.el-button.speech-btn .el-button__text,
.el-button.rx-speech .el-button__text {
  color: inherit !important;
  display: flex !important;
  align-items: center !important;
  gap: 4px !important;
  font-weight: 500 !important;
}
.el-button.speech-btn:hover,
.el-button.rx-speech:hover {
  color: #409eff !important;
  border-color: rgba(64,158,255,0.4) !important;
  background: rgba(64,158,255,0.1) !important;
}
.el-button.speech-btn.speaking,
.el-button.rx-speech.speaking {
  color: #67c23a !important;
  border-color: rgba(103,194,58,0.45) !important;
  background: rgba(103,194,58,0.12) !important;
  animation: speech-pulse 1s infinite;
}
.el-button.speech-btn.speaking .el-button__text,
.el-button.rx-speech.speaking .el-button__text {
  color: inherit !important;
}

@keyframes speech-pulse {
  0%, 100% { transform: scale(1); box-shadow: 0 0 0 rgba(103,194,58,0); }
  50% { transform: scale(1.05); box-shadow: 0 0 0 6px rgba(103,194,58,0.08); }
}

/* ===== 列表页面板容器全局统一：背景 + padding + max-width ===== */
.prescriptions-container,
.herbs-container,
.compounds-container {
  max-width: 1600px !important;
  margin: 0 auto !important;
}

/* ===== 主要操作按钮：Micro-Bounce（按下微弹跳反馈） =====
   —— 适用于所有带文字标签的 type=primary / type=success / type=warning / 自定义强调色按钮，
      以及登录、提交、搜索、体验测试账号等"下一步/行动"按钮。
*/
.el-button--primary,
.el-button--success,
.el-button--warning,
.el-button--danger,
.submit-btn,
.guest-btn {
  transform-origin: center center;
  transform-box: border-box;
  transition:
    transform 180ms cubic-bezier(0.18, 0.89, 0.32, 1.28),
    box-shadow 200ms ease,
    background 200ms ease,
    color 200ms ease,
    border-color 200ms ease !important;
  will-change: transform;
}

/* hover：抬起 + 轻微放大 */
.el-button--primary:hover,
.el-button--success:hover,
.el-button--warning:hover,
.el-button--danger:hover,
.submit-btn:hover,
.guest-btn:hover {
  transform: translateY(-1px) scale(1.015) !important;
}

/* focus 键盘可达：轻微抬升 */
.el-button--primary:focus-visible,
.el-button--success:focus-visible,
.el-button--warning:focus-visible,
.el-button--danger:focus-visible,
.submit-btn:focus-visible,
.guest-btn:focus-visible {
  transform: translateY(-1px) scale(1.01) !important;
  outline: 2px solid rgba(45,212,191,0.35);
  outline-offset: 2px;
}

/* ⭐ 按下 Micro-Bounce：先压 96% → 回弹 101.2% → 归位（像按压真按钮） */
.el-button--primary:active,
.el-button--success:active,
.el-button--warning:active,
.el-button--danger:active,
.submit-btn:active,
.guest-btn:active {
  animation: btn-micro-bounce 320ms cubic-bezier(0.22, 1, 0.36, 1) both;
}

@keyframes btn-micro-bounce {
  0%   { transform: translateY(0)    scale(1); }
  30%  { transform: translateY(2px)  scale(0.965); }       /* 按下沉 */
  60%  { transform: translateY(-1px) scale(1.018); }       /* 弹起过冲 */
  80%  { transform: translateY(0)    scale(1.005); }       /* 回落 */
  100% { transform: translateY(0)    scale(1); }           /* 归位 */
}

/* disabled 态不允许互动反馈 */
.el-button.is-disabled,
.el-button[disabled] {
  animation: none !important;
  transform: none !important;
  cursor: not-allowed !important;
}

/* =========================================================================
 * 全站卡片入场 Stagger 动画（统一命名，纯 CSS，零 JS）
 * 用法：
 *   1. 容器加 class="stagger-grid"（可选，仅语义）
 *   2. 循环卡片加 class="stagger-item"
 *   3. 循环上通过 :style="{ '--i': String(index) }" 把 index 传给 CSS
 *   4. 需要"每次数据变化都重新播放"时，给 :key 绑定能代表"这次渲染批次"的变量，
 *      或使用 Vue 的 <TransitionGroup>；本实现默认对"首次挂载"生效（最常见场景）。
 * ========================================================================= */
.stagger-item {
  /* 关键帧：透明度 0→1 + 上浮 16px 归位 + 轻微缩放 */
  animation-name: stagger-card-enter;
  animation-timing-function: cubic-bezier(0.22, 1, 0.36, 1);
  animation-fill-mode: both;                      /* 动画前停留在 0 态，动画后保留 1 态 */
  animation-duration: 620ms;
  /* 核心：每张卡根据 index（自定义属性 --i）延迟 50ms，最多延迟 500ms 封顶，
     避免数据 >10 条时后入场要等太久 */
  animation-delay: calc(60ms * var(--i, 0));
  will-change: transform, opacity;
}

/* 容器本身做 80ms 前置延迟（给列表里第一个 60ms 不要太抢，header/search 先出来） */
.stagger-grid .stagger-item:first-child,
.stagger-grid + * { /* 预留：stagger-grid 之后的模块也有延迟 */ }

@keyframes stagger-card-enter {
  0% {
    opacity: 0;
    transform: translateY(18px) scale(0.975);
    filter: blur(4px);
  }
  55% {
    filter: blur(0);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
    filter: blur(0);
  }
}

/* ===== 可访问性兜底：用户开启"减少动效"时，所有 stagger 失效 ===== */
@media (prefers-reduced-motion: reduce) {
  .stagger-item {
    animation: none !important;
    opacity: 1 !important;
    transform: none !important;
    filter: none !important;
  }
}
</style>