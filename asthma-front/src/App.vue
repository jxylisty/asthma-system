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
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-card: rgba(30, 41, 59, 0.7);
  --bg-card-hover: rgba(30, 41, 59, 0.9);
  --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1a2744 50%, #0f172a 100%);

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
  --font-size-base: 14px;
  --font-size-sm: 12px;
  --font-size-lg: 16px;

  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;

  --shadow-card: 0 4px 20px rgba(0, 0, 0, 0.2);
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
  background: var(--bg-primary);
  color: var(--text-color);
}

#app {
  width: 100%;
  min-height: 100vh;
  background: var(--bg-gradient);
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
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-color) !important;
  border-radius: var(--radius-lg) !important;
  color: var(--text-color) !important;
}

.el-dialog__title {
  color: var(--text-color) !important;
}

.el-dialog__body {
  color: var(--text-secondary) !important;
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
  color: var(--text-color) !important;
}

.el-message-box__title {
  color: var(--text-color) !important;
}

.el-message-box__message {
  color: var(--text-secondary) !important;
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

/* ===== 弹窗层级与居中修复 ===== */
.el-overlay {
  z-index: 2999 !important;
}
.el-overlay-dialog {
  z-index: 3000 !important;
  display: block !important;
  width: 100% !important;
  text-align: center !important;
}
.el-dialog {
  z-index: 3000 !important;
  margin: 0 auto !important;
  display: inline-block !important;
  text-align: left !important;
  vertical-align: middle !important;
}
</style>