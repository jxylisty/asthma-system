<template>
  <div class="settings-container">
    <div class="page-header">
      <h2 class="page-title">⚙️ 系统设置</h2>
      <p class="page-desc">配置 AI 模型、预测偏好与数据管理</p>
    </div>

    <div class="settings-grid">
      <!-- ===== 板块 1：AI 模型配置 ===== -->
      <el-card class="settings-card ai-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon class="header-icon"><MagicStick /></el-icon>
            <span class="header-title">🤖 AI 模型配置</span>
            <el-tag v-if="isAiConfigured" type="success" size="small" effect="dark" class="config-status">
              <el-icon><CircleCheckFilled /></el-icon> 已配置
            </el-tag>
            <el-tag v-else type="warning" size="small" effect="dark" class="config-status">未配置</el-tag>
          </div>
        </template>

        <div class="settings-form">
          <el-form-item label="AI 服务商">
            <el-radio-group v-model="provider">
              <el-radio-button v-for="p in providerPresets" :key="p.value" :value="p.value">
                {{ p.label }}
              </el-radio-button>
            </el-radio-group>
            <div class="form-hint">{{ providerPresets.find(p => p.value === provider)?.desc || '' }}</div>
          </el-form-item>

          <el-form-item label="API Key">
            <el-input v-model="apiKey" type="password" show-password placeholder="粘贴你的 AI API Key" clearable>
              <template #prefix><el-icon><Key /></el-icon></template>
            </el-input>
            <div class="form-hint">
              Key 仅保存在浏览器本地，不会上传服务器。
              <el-link v-if="providerPresets.find(p => p.value === provider)?.applyUrl" type="primary"
                :href="providerPresets.find(p => p.value === provider).applyUrl" target="_blank">
                <el-icon><Link /></el-icon> 前往申请 Key
              </el-link>
            </div>
          </el-form-item>

          <el-form-item label="Base URL（可选）">
            <el-input v-model="baseUrl" placeholder="留空使用默认地址" clearable />
          </el-form-item>

          <el-form-item label="模型（可选）">
            <el-input v-model="model" placeholder="留空使用默认模型" clearable />
          </el-form-item>

          <el-form-item label="默认预测模型">
            <el-radio-group v-model="defaultModel" class="model-radio">
              <el-radio label="cctcm">CCTCM 2.0 高维模型</el-radio>
              <el-radio label="herb">HERB 2.0 基础模型</el-radio>
            </el-radio-group>
            <div class="form-hint">控制入血预测控制台默认选中的模型</div>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="testAiKey" :disabled="!apiKey.trim()">
              <el-icon><Check /></el-icon> 保存并验证
            </el-button>
            <el-button @click="resetAi">
              <el-icon><RefreshLeft /></el-icon> 重置
            </el-button>
          </el-form-item>
        </div>
      </el-card>

      <!-- ===== 板块 2：预测与分析偏好 ===== -->
      <el-card class="settings-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon class="header-icon"><DataAnalysis /></el-icon>
            <span class="header-title">📊 预测与分析偏好</span>
          </div>
        </template>

        <div class="settings-form">
          <el-form-item label="默认入血概率阈值">
            <div class="slider-row">
              <el-slider v-model="defaultThreshold" :min="0" :max="100" :step="5" show-input />
            </div>
            <div class="form-hint">低于此阈值的化合物在列表中默认隐藏，网络图谱默认不显示</div>
          </el-form-item>

          <el-form-item label="批量预测导出格式">
            <el-radio-group v-model="exportFormat">
              <el-radio label="xlsx">📄 Excel (.xlsx)</el-radio>
              <el-radio label="csv">📋 CSV (.csv)</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="网络图谱最大节点数">
            <div class="slider-row">
              <el-slider v-model="maxNetworkNodes" :min="50" :max="500" :step="50" show-input />
            </div>
            <div class="form-hint">超过此数量时自动合并次要节点，避免图谱卡顿</div>
          </el-form-item>
        </div>
      </el-card>

      <!-- ===== 板块 3：数据与缓存 ===== -->
      <el-card class="settings-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon class="header-icon"><Coin /></el-icon>
            <span class="header-title">💾 数据与缓存</span>
          </div>
        </template>

        <div class="settings-form">
          <!-- 实时数据库统计 -->
          <div class="db-stats">
            <div class="db-stat"><span class="db-stat-icon">🍵</span><strong>{{ dbStats.prescriptions }}</strong> 首方剂</div>
            <div class="db-stat"><span class="db-stat-icon">🌿</span><strong>{{ dbStats.herbs }}</strong> 味中药</div>
            <div class="db-stat"><span class="db-stat-icon">🧪</span><strong>{{ dbStats.compounds }}</strong> 个化合物</div>
            <div class="db-stat"><span class="db-stat-icon">🎯</span><strong>{{ dbStats.targets }}</strong> 个靶点</div>
          </div>

          <el-form-item>
            <el-button @click="clearCache">
              <el-icon><Delete /></el-icon> 清除本地缓存
            </el-button>
            <el-button @click="resetAll" type="danger" plain>
              <el-icon><RefreshLeft /></el-icon> 重置全部设置
            </el-button>
          </el-form-item>
        </div>
      </el-card>

      <!-- ===== 板块 4：关于系统 ===== -->
      <el-card class="settings-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon class="header-icon"><InfoFilled /></el-icon>
            <span class="header-title">ℹ️ 关于系统</span>
          </div>
        </template>

        <div class="about-grid">
          <div class="about-item"><span class="about-label">系统名称</span><span>哮喘方剂智能分析系统</span></div>
          <div class="about-item"><span class="about-label">版本号</span><span>v1.0.0</span></div>
          <div class="about-item"><span class="about-label">技术栈</span><span>Vue 3 + Element Plus + FastAPI + SQLite</span></div>
          <div class="about-item"><span class="about-label">预测方法</span><span>PU Learning 双模型入血预测</span></div>
          <div class="about-item"><span class="about-label">前端仓库</span>
            <el-link type="primary" href="https://github.com/jxylisty/asthma-front" target="_blank">github.com/jxylisty/asthma-front</el-link>
          </div>
          <div class="about-item"><span class="about-label">后端仓库</span>
            <el-link type="primary" href="https://github.com/jxylisty/asthma-core" target="_blank">github.com/jxylisty/asthma-core</el-link>
          </div>
          <div class="about-item"><span class="about-label">项目总览</span>
            <el-link type="primary" href="https://github.com/jxylisty/asthma-system" target="_blank">github.com/jxylisty/asthma-system</el-link>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  MagicStick, Key, Link, Check, RefreshLeft, CircleCheckFilled,
  DataAnalysis, Coin, Delete, InfoFilled
} from '@element-plus/icons-vue'
import { useAiSettings } from '../composables/useAiSettings'
import { getStatistics } from '../api'

// ── AI 配置（复用现有 composable） ──
const {
  provider, apiKey, baseUrl, model, providerPresets,
  isConfigured: isAiConfigured, resetAiSettings,
} = useAiSettings()

function testAiKey() {
  if (!apiKey.value.trim()) { ElMessage.warning('请先填写 API Key'); return }
  ElMessage.success('配置已保存，可在自定义处方或方剂详情页测试生成报告')
}
function resetAi() { resetAiSettings(); ElMessage.info('已重置 AI 配置') }

// ── 预测与分析偏好 ──
const defaultModel = ref(localStorage.getItem('settings_defaultModel') || 'cctcm')
const defaultThreshold = ref(Number(localStorage.getItem('settings_defaultThreshold') || 50))
const exportFormat = ref(localStorage.getItem('settings_exportFormat') || 'xlsx')
const maxNetworkNodes = ref(Number(localStorage.getItem('settings_maxNetworkNodes') || 200))

// 保存到 localStorage（自动 watch）
import { watch } from 'vue'
watch(defaultModel, v => localStorage.setItem('settings_defaultModel', v))
watch(defaultThreshold, v => localStorage.setItem('settings_defaultThreshold', String(v)))
watch(exportFormat, v => localStorage.setItem('settings_exportFormat', v))
watch(maxNetworkNodes, v => localStorage.setItem('settings_maxNetworkNodes', String(v)))

// ── 数据库实时统计 ──
const dbStats = ref({ prescriptions: '—', herbs: '—', compounds: '—', targets: '—' })
async function loadDbStats() {
  try {
    const s = await getStatistics()
    if (s) {
      dbStats.value = {
        prescriptions: s.prescription_count ?? '—',
        herbs: s.herb_count ?? '—',
        compounds: s.compound_count ?? '—',
        targets: s.target_count ?? '—'
      }
    }
  } catch (e) { /* 静默 */ }
}

// ── 操作 ──
function clearCache() {
  // 保留 AI 配置和用户偏好 settings_ 键，只清系统缓存
  const preserve = ['ai_provider', 'ai_apiKey', 'ai_baseUrl', 'ai_model']
  const keep = {}
  preserve.forEach(k => { const v = localStorage.getItem(k); if (v) keep[k] = v })
  const settingsKeys = Object.keys(localStorage).filter(k => k.startsWith('settings_'))
  settingsKeys.forEach(k => { const v = localStorage.getItem(k); if (v) keep[k] = v })
  localStorage.clear()
  Object.entries(keep).forEach(([k, v]) => localStorage.setItem(k, v))
  ElMessage.success('本地缓存已清理（保留 AI 配置与偏好设置）')
}

function resetAll() {
  const keep = {}
  // 保留 AI 配置
  ;['ai_provider', 'ai_apiKey', 'ai_baseUrl', 'ai_model'].forEach(k => {
    const v = localStorage.getItem(k); if (v) keep[k] = v
  })
  // 清除所有 settings_ 键
  const settingsKeys = Object.keys(localStorage).filter(k => k.startsWith('settings_'))
  settingsKeys.forEach(k => localStorage.removeItem(k))
  // 恢复 AI 配置
  Object.entries(keep).forEach(([k, v]) => localStorage.setItem(k, v))
  // 恢复默认值
  defaultModel.value = 'cctcm'
  defaultThreshold.value = 50
  exportFormat.value = 'xlsx'
  maxNetworkNodes.value = 200
  ElMessage.success('已重置全部偏好设置（AI 配置保留）')
}

onMounted(loadDbStats)
</script>

<style scoped>
.settings-container {
  padding: 32px 40px;
  min-height: 100vh;
  background: #0f172a;
}
.page-header { margin-bottom: 28px }
.page-title { font-size: 26px; font-weight: 700; color: #e2e8f0; margin-bottom: 6px }
.page-desc { font-size: 14px; color: #94a3b8 }

.settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  max-width: 1200px;
}

.settings-card {
  background: #1e293b;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px;
  color: #e2e8f0;
}
.settings-card :deep(.el-card__header) {
  border-bottom: 1px solid rgba(255,255,255,0.06);
  padding: 16px 20px;
}
.settings-card :deep(.el-card__body) { padding: 20px }

.ai-card { border-color: rgba(16,185,129,0.3) }

.card-header {
  display: flex; align-items: center; gap: 10px;
}
.header-icon { font-size: 18px; color: #38bdf8 }
.header-title { font-size: 15px; font-weight: 600; color: #e2e8f0 }
.config-status { margin-left: auto }

.settings-form :deep(.el-form-item) { margin-bottom: 20px }
.settings-form :deep(.el-form-item__label) {
  font-weight: 500; color: #94a3b8; font-size: 13px;
}

.form-hint { font-size: 12px; color: #64748b; margin-top: 4px }

.slider-row { width: 100% }
.slider-row :deep(.el-slider) { margin-right: 8px }

/* 数据库统计 */
.db-stats {
  display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
  margin-bottom: 18px; padding: 14px;
  background: rgba(255,255,255,0.03); border-radius: 10px;
}
.db-stat { font-size: 13px; color: #94a3b8; display: flex; align-items: center; gap: 6px }
.db-stat strong { color: #e2e8f0; font-size: 16px; margin-right: 2px }
.db-stat-icon { font-size: 14px }

/* 关于 */
.about-grid { display: flex; flex-direction: column; gap: 10px }
.about-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.04);
  font-size: 13px; color: #94a3b8;
}
.about-item:last-child { border-bottom: none }
.about-label { color: #64748b; flex-shrink: 0; margin-right: 12px }

/* 组件暗色覆盖 */
.settings-form :deep(.el-radio-button__inner) {
  background: #1e293b; border-color: rgba(255,255,255,0.1); color: #94a3b8;
}
.settings-form :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: rgba(16,185,129,0.15); border-color: #10b981; color: #34d399;
}
.settings-form :deep(.el-radio) { --el-radio-text-color: #94a3b8; margin-right: 16px }
.settings-form :deep(.el-radio.is-checked) { --el-radio-text-color: #34d399 }
.settings-form :deep(.el-input__wrapper) {
  background: rgba(255,255,255,0.04); border-color: rgba(255,255,255,0.08);
}
.settings-form :deep(.el-input__inner) { color: #e2e8f0 }
.model-radio { display: flex; flex-direction: column; gap: 6px }
</style>
