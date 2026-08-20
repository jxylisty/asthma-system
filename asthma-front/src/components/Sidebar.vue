<template>
  <aside class="sidebar" :class="{ 'sidebar--collapsed': isCollapse }">
    <!-- Logo 区 -->
    <div class="sidebar-header">
      <!-- 折叠/展开按钮 -->
      <button class="collapse-btn" :title="isCollapse ? '展开侧边栏' : '折叠侧边栏'" @click="$emit('update:isCollapse', !isCollapse)">
        <el-icon><component :is="isCollapse ? Expand : Fold" /></el-icon>
      </button>

      <div class="logo" :class="{ 'logo--collapsed': isCollapse }">
        <!-- Logo 图标（展开/折叠都显示） -->
        <div class="logo-mark" aria-hidden="true">
          <span class="logo-mark-main">智</span>
        </div>

        <!-- 品牌文字（仅展开态显示） -->
        <div class="logo-texts" v-if="!isCollapse">
          <span class="logo-title">东方智喘</span>
          <span class="logo-subtitle">方剂智能分析</span>
        </div>
      </div>
    </div>

    <!-- 导航菜单 -->
    <nav class="nav-menu">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ 'nav-active': isActive(item) }"
      >
        <el-icon class="nav-icon"><component :is="item.icon" /></el-icon>
        <span v-if="!isCollapse">{{ item.label }}</span>
      </router-link>

      <div class="nav-divider" v-if="!isCollapse" />

      <!-- 子项 -->
      <router-link to="/herbs" class="nav-item" :class="{ 'nav-active': isActive({ path: '/herbs', match: ['/herbs'] }) }">
        <el-icon class="nav-icon"><FirstAidKit /></el-icon>
        <span v-if="!isCollapse">中药列表</span>
      </router-link>
      <router-link to="/compounds" class="nav-item" :class="{ 'nav-active': isActive({ path: '/compounds', match: ['/compounds'] }) }">
        <el-icon class="nav-icon"><Document /></el-icon>
        <span v-if="!isCollapse">化合物列表</span>
      </router-link>
    </nav>

    <!-- 底部用户区 -->
    <div class="sidebar-footer" :class="{ 'sidebar-footer--collapsed': isCollapse }" v-if="user">
      <div class="user-row">
        <el-icon class="user-icon"><UserFilled /></el-icon>
        <template v-if="!isCollapse">
          <span class="user-name">{{ user.username }}</span>
          <button class="logout-btn" @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
            <span>登出</span>
          </button>
        </template>
        <button v-else class="logout-btn logout-btn--icon" @click="handleLogout" title="登出">
          <el-icon><SwitchButton /></el-icon>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  HomeFilled, Notebook, DataAnalysis, EditPen,
  FirstAidKit, Document, Setting, UserFilled, SwitchButton,
  Fold, Expand
} from '@element-plus/icons-vue'
import { useAuth } from '../composables/useAuth'

defineProps({
  isCollapse: { type: Boolean, default: false }
})
defineEmits(['update:isCollapse'])

const route = useRoute()
const router = useRouter()
const { user, logout } = useAuth()

const navItems = [
  { path: '/',          label: '工作台',       icon: HomeFilled,   match: ['/'] },
  { path: '/prediction', label: '入血预测',     icon: DataAnalysis, match: ['/prediction'] },
  { path: '/prescriptions', label: '方剂列表', icon: Notebook,    match: ['/prescriptions', '/detail'] },
  { path: '/custom-prescription', label: '自定义方剂分析', icon: EditPen, match: ['/custom-prescription'] },
  { path: '/settings',   label: '系统设置',   icon: Setting,     match: ['/settings'] },
]

function isActive(item) {
  const matches = item.match || [item.path]
  return matches.some(m => route.path === m || (m !== '/' && route.path.startsWith(m)))
}

function handleLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'
  }).then(() => {
    logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  }).catch(() => {})
}
</script>

<style scoped>
.sidebar {
  width: 230px; height: 100vh;
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(10px);
  border-right: 1px solid var(--border-color);
  display: flex; flex-direction: column;
  position: fixed; left: 0; top: 0; z-index: 20;
  transition: width 0.28s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}
/* 折叠态宽度：只够放图标 */
.sidebar--collapsed { width: 68px; }

/* ========== Logo 区 ========== */
.sidebar-header {
  position: relative;
  padding: 22px 20px 18px;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 10px;
  transition: padding 0.28s ease;
}
.sidebar--collapsed .sidebar-header {
  padding: 22px 8px 18px;
}

/* 折叠按钮：右上角，绝对定位 */
.collapse-btn {
  position: absolute;
  top: 12px; right: 10px;
  width: 28px; height: 28px;
  border-radius: 7px;
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-muted);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}
.collapse-btn:hover {
  color: var(--text-primary);
  background: rgba(255,255,255,0.06);
  border-color: rgba(255,255,255,0.1);
}
.collapse-btn .el-icon { font-size: 16px; }
.sidebar--collapsed .collapse-btn {
  /* 折叠态：把按钮移到顶部居中，方便点展开 */
  top: 8px; right: 50%;
  transform: translateX(50%);
  width: 30px; height: 30px;
}

/* Logo 主体 */
.logo {
  display: flex; align-items: center; gap: 10px;
  padding-top: 4px;
  width: 100%;
  transition: justify-content 0.28s ease, padding 0.28s ease;
}
.logo--collapsed {
  justify-content: center;
  padding-top: 26px; /* 给顶部居中的折叠按钮留空 */
  gap: 0;
}

/* Logo 图形：方形"智"字徽标 —— 青绿纯色背景，无边框 */
.logo-mark {
  flex-shrink: 0;
  width: 38px; height: 38px;
  border-radius: 10px;
  position: relative;
  background: #2DD4BF;
  display: flex; align-items: center; justify-content: center;
  overflow: hidden;
}
.logo-mark-main {
  font-family: "Ma Shan Zheng", "STKaiti", "KaiTi", "PingFang SC", "Microsoft YaHei", serif;
  font-size: 22px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 0;
  text-shadow: 0 1px 2px rgba(13, 148, 136, 0.3);
}

/* 品牌文字：大字 + 小字 */
.logo-texts {
  display: flex; flex-direction: column; line-height: 1.15;
}
.logo-title {
  font-size: 18px;
  font-weight: 800;
  color: #f8fafc;
  letter-spacing: 1.2px;
  font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
}
.logo-subtitle {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  letter-spacing: 1px;
  margin-top: 3px;
}

/* ========== 导航 ========== */
.nav-menu { flex: 1; padding: 0 12px; transition: padding 0.28s ease; }
.sidebar--collapsed .nav-menu { padding: 0 8px; }

.nav-item {
  display: flex; align-items: center; gap: 11px;
  padding: 10px 14px; margin-bottom: 3px;
  border-radius: 8px;
  font-size: 14px; color: var(--text-muted);
  text-decoration: none;
  transition: all 0.18s;
  white-space: nowrap;
  min-height: 40px;
}
.nav-item:hover { background: rgba(255,255,255,0.06); color: var(--text-secondary) }
.nav-active {
  background: rgba(45, 212, 191, 0.1) !important;
  color: var(--color-primary) !important;
  font-weight: 600;
  box-shadow: inset 2px 0 0 0 var(--color-primary);
}
.nav-icon { font-size: 19px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; }

/* 折叠态：菜单项只保留图标，居中，去掉左边 inset 阴影，改圆角圆点 */
.sidebar--collapsed .nav-item {
  padding: 10px 0;
  justify-content: center;
  gap: 0;
  border-radius: 10px;
  margin-bottom: 6px;
  box-shadow: none !important;
  position: relative;
}
.sidebar--collapsed .nav-item::after {
  /* 折叠态激活提示：右侧圆点 */
  content: "";
  position: absolute;
  right: 4px;
  top: 50%;
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
  transform: translateY(-50%) scale(0);
  transition: transform 0.2s;
  box-shadow: 0 0 8px var(--color-primary);
}
.sidebar--collapsed .nav-active::after { transform: translateY(-50%) scale(1); }
.sidebar--collapsed .nav-icon { font-size: 20px; }

.nav-divider { height: 1px; background: var(--border-color); margin: 10px 14px; transition: margin 0.28s; }

/* ========== 底部 ========== */
.sidebar-footer {
  padding: 16px 18px; border-top: 1px solid var(--border-color); margin-top: auto;
  transition: padding 0.28s ease;
}
.sidebar-footer--collapsed { padding: 16px 0; }
.user-row { display: flex; align-items: center; gap: 8px; }
.sidebar-footer--collapsed .user-row { justify-content: center; gap: 0; flex-direction: column; }

.user-icon { font-size: 18px; color: var(--color-secondary); flex-shrink: 0; }
.sidebar-footer--collapsed .user-icon {
  width: 36px; height: 36px;
  border-radius: 50%;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  display: flex; align-items: center; justify-content: center;
  font-size: 16px;
  margin-bottom: 8px;
}

.user-name { flex: 1; font-size: 14px; color: var(--text-secondary); font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap }

.logout-btn {
  display: flex; align-items: center; gap: 4px;
  font-size: 12px; color: var(--text-disabled);
  background: none; border: none; cursor: pointer;
  padding: 2px 4px;
  transition: color 0.15s;
}
.logout-btn:hover { color: var(--color-danger) }

/* 折叠态：登出做成小图标按钮 */
.logout-btn--icon {
  width: 32px; height: 32px;
  border-radius: 8px;
  justify-content: center;
  font-size: 15px;
  color: var(--text-disabled);
}
.logout-btn--icon:hover {
  background: rgba(244, 63, 94, 0.1);
  color: var(--color-danger);
}

/* 折叠时用户区的"用户图标+登出按钮"竖排对齐 */
.sidebar-footer--collapsed .user-row {
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
</style>
