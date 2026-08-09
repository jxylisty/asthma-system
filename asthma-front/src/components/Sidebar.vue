<template>
  <aside class="sidebar">
    <!-- Logo 区 -->
    <div class="sidebar-header">
      <div class="logo">
        <el-icon class="logo-icon"><Search /></el-icon>
        <span class="logo-text">哮喘方剂分析</span>
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
        <span>{{ item.label }}</span>
      </router-link>

      <div class="nav-divider" />

      <!-- 子项 -->
      <router-link to="/herbs" class="nav-item" :class="{ 'nav-active': isActive({ path: '/herbs', match: ['/herbs'] }) }">
        <el-icon class="nav-icon"><FirstAidKit /></el-icon>
        <span>中药列表</span>
      </router-link>
      <router-link to="/compounds" class="nav-item" :class="{ 'nav-active': isActive({ path: '/compounds', match: ['/compounds'] }) }">
        <el-icon class="nav-icon"><Document /></el-icon>
        <span>化合物列表</span>
      </router-link>
    </nav>

    <!-- 底部用户区 -->
    <div class="sidebar-footer" v-if="user">
      <div class="user-row">
        <el-icon class="user-icon"><UserFilled /></el-icon>
        <span class="user-name">{{ user.username }}</span>
        <button class="logout-btn" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          <span>登出</span>
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
  Search, HomeFilled, Notebook, DataAnalysis, EditPen,
  FirstAidKit, Document, Setting, UserFilled, SwitchButton
} from '@element-plus/icons-vue'
import { useAuth } from '../composables/useAuth'

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
  background: #111827;
  border-right: 1px solid rgba(255,255,255,0.06);
  display: flex; flex-direction: column;
  position: fixed; left: 0; top: 0; z-index: 1000;
}
.sidebar-header {
  padding: 24px 20px 20px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  margin-bottom: 10px;
}
.logo { display: flex; align-items: center; gap: 10px }
.logo-icon { font-size: 24px; color: #38bdf8 }
.logo-text { font-size: 17px; font-weight: 700; color: #e2e8f0; letter-spacing: 1px }

/* 导航 */
.nav-menu { flex: 1; padding: 0 12px }
.nav-item {
  display: flex; align-items: center; gap: 11px;
  padding: 10px 14px; margin-bottom: 3px;
  border-radius: 8px;
  font-size: 14px; color: #94a3b8;
  text-decoration: none;
  transition: all 0.18s;
}
.nav-item:hover { background: rgba(255,255,255,0.06); color: #cbd5e1 }
.nav-active {
  background: rgba(16,185,129,0.1) !important;
  color: #34d399 !important;
  font-weight: 600;
  box-shadow: inset 2px 0 0 0 #10b981;
}
.nav-icon { font-size: 19px; flex-shrink: 0 }
.nav-divider { height: 1px; background: rgba(255,255,255,0.06); margin: 10px 14px }

/* 底部 */
.sidebar-footer { padding: 16px 18px; border-top: 1px solid rgba(255,255,255,0.06); margin-top: auto }
.user-row { display: flex; align-items: center; gap: 8px }
.user-icon { font-size: 18px; color: #38bdf8 }
.user-name { flex: 1; font-size: 14px; color: #cbd5e1; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap }
.logout-btn { display: flex; align-items: center; gap: 4px; font-size: 12px; color: #64748b; background: none; border: none; cursor: pointer; padding: 2px 4px; transition: color 0.15s }
.logout-btn:hover { color: #f87171 }
</style>
