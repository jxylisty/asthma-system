<template>
  <div class="settings-container">
    <div class="page-header">
      <h2 class="page-title">系统设置</h2>
      <p class="page-desc">配置预测模型、分析偏好与数据管理</p>
    </div>

    <div class="settings-grid">
      <!-- 板块1：AI 模型配置 -->
      <el-card class="settings-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon class="header-icon"><MagicStick /></el-icon>
            <span class="header-title">AI 模型配置</span>
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
            <el-input v-model="apiKey" type="password" show-password placeholder="输入 API Key" clearable>
              <template #prefix><el-icon><Key /></el-icon></template>
            </el-input>
            <div class="form-hint">
              Key 仅保存在浏览器本地，不会上传服务器。
              <el-link v-if="providerPresets.find(p => p.value === provider)?.applyUrl" type="primary"
                :href="providerPresets.find(p => p.value === provider).applyUrl" target="_blank">
                <el-icon><Link /></el-icon> 申请 Key
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
              <el-radio value="cctcm">CCTCM 2.0 高维模型</el-radio>
              <el-radio value="herb">HERB 2.0 基础模型</el-radio>
            </el-radio-group>
            <div class="form-hint">控制入血预测页默认选中的模型</div>
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

      <!-- 板块2：预测与分析偏好 -->
      <el-card class="settings-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon class="header-icon"><DataAnalysis /></el-icon>
            <span class="header-title">预测与分析偏好</span>
          </div>
        </template>

        <div class="settings-form">
          <el-form-item label="默认入血概率阈值">
            <div class="slider-row">
              <el-slider v-model="defaultThreshold" :min="0" :max="100" :step="5" show-input />
            </div>
            <div class="form-hint">低于此阈值的化合物在列表中默认隐藏</div>
          </el-form-item>

          <el-form-item label="批量预测导出格式">
            <el-radio-group v-model="exportFormat">
              <el-radio value="xlsx">Excel (.xlsx)</el-radio>
              <el-radio value="csv">CSV (.csv)</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="网络图谱最大节点数">
            <div class="slider-row">
              <el-slider v-model="maxNetworkNodes" :min="50" :max="500" :step="50" show-input />
            </div>
            <div class="form-hint">超过此数量时自动合并次要节点</div>
          </el-form-item>
        </div>
      </el-card>

      <!-- 板块3：数据与缓存 -->
      <el-card class="settings-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon class="header-icon"><Coin /></el-icon>
            <span class="header-title">数据与缓存</span>
          </div>
        </template>

        <div class="settings-form">
          <div class="db-stats">
            <div class="db-stat"><strong>{{ dbStats.prescriptions }}</strong><span>首方剂</span></div>
            <div class="db-stat"><strong>{{ dbStats.herbs }}</strong><span>味中药</span></div>
            <div class="db-stat"><strong>{{ dbStats.compounds }}</strong><span>个化合物</span></div>
            <div class="db-stat"><strong>{{ dbStats.targets }}</strong><span>个靶点</span></div>
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

      <!-- 板块4：关于系统 -->
      <el-card class="settings-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon class="header-icon"><InfoFilled /></el-icon>
            <span class="header-title">关于系统</span>
          </div>
        </template>

        <div class="about-grid">
          <div class="about-item"><span class="about-label">系统名称</span><span>儿童哮喘方剂智能分析系统</span></div>
          <div class="about-item"><span class="about-label">版本号</span><span>v1.0.0</span></div>
          <div class="about-item"><span class="about-label">技术栈</span><span>Vue 3 + FastAPI + SQLite</span></div>
          <div class="about-item"><span class="about-label">预测方法</span><span>PU Learning 双模型</span></div>
          <div class="about-item"><span class="about-label">前端仓库</span>
            <el-link type="primary" href="https://github.com/jxylisty/asthma-front" target="_blank">查看</el-link>
          </div>
          <div class="about-item"><span class="about-label">后端仓库</span>
            <el-link type="primary" href="https://github.com/jxylisty/asthma-core" target="_blank">查看</el-link>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  MagicStick, Key, Link, Check, RefreshLeft, CircleCheckFilled,
  DataAnalysis, Coin, Delete, InfoFilled
} from '@element-plus/icons-vue'
import { useAiSettings } from '../composables/useAiSettings'
import { getStatistics } from '../api'

const {
  provider, apiKey, baseUrl, model, providerPresets,
  isConfigured: isAiConfigured, resetAiSettings,
} = useAiSettings()

function testAiKey() {
  if (!apiKey.value.trim()) { ElMessage.warning('请先填写 API Key'); return }
  ElMessage.success('配置已保存')
}
function resetAi() { resetAiSettings(); ElMessage.info('已重置 AI 配置') }

const defaultModel = ref(localStorage.getItem('settings_defaultModel') || 'cctcm')
const defaultThreshold = ref(Number(localStorage.getItem('settings_defaultThreshold') || 50))
const exportFormat = ref(localStorage.getItem('settings_exportFormat') || 'xlsx')
const maxNetworkNodes = ref(Number(localStorage.getItem('settings_maxNetworkNodes') || 200))

watch(defaultModel, v => localStorage.setItem('settings_defaultModel', v))
watch(defaultThreshold, v => localStorage.setItem('settings_defaultThreshold', String(v)))
watch(exportFormat, v => localStorage.setItem('settings_exportFormat', v))
watch(maxNetworkNodes, v => localStorage.setItem('settings_maxNetworkNodes', String(v)))

const dbStats = ref({ prescriptions: '—', herbs: '—', compounds: '—', targets: '—' })
async function loadDbStats() {
  try {
    const raw = await getStatistics()
    const s = (raw && raw.data) || raw
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

function clearCache() {
  const preserve = ['ai_provider', 'ai_apiKey', 'ai_baseUrl', 'ai_model']
  const keep = {}
  preserve.forEach(k => { const v = localStorage.getItem(k); if (v) keep[k] = v })
  const settingsKeys = Object.keys(localStorage).filter(k => k.startsWith('settings_'))
  settingsKeys.forEach(k => { const v = localStorage.getItem(k); if (v) keep[k] = v })
  localStorage.clear()
  Object.entries(keep).forEach(([k, v]) => localStorage.setItem(k, v))
  ElMessage.success('本地缓存已清理')
}

function resetAll() {
  const keep = {}
  ;['ai_provider', 'ai_apiKey', 'ai_baseUrl', 'ai_model'].forEach(k => {
    const v = localStorage.getItem(k); if (v) keep[k] = v
  })
  const settingsKeys = Object.keys(localStorage).filter(k => k.startsWith('settings_'))
  settingsKeys.forEach(k => localStorage.removeItem(k))
  Object.entries(keep).forEach(([k, v]) => localStorage.setItem(k, v))
  defaultModel.value = 'cctcm'
  defaultThreshold.value = 50
  exportFormat.value = 'xlsx'
  maxNetworkNodes.value = 200
  ElMessage.success('已重置偏好设置')
}

onMounted(loadDbStats)
</script>

<style scoped>
.settings-container {
  padding: 32px 40px;
  min-height: 100vh;
  background: transparent;
}
.page-header { margin-bottom: 28px }
.page-title { font-size: var(--fs-h1); font-weight: var(--fw-bold); color: var(--text-color); margin-bottom: 6px }
.page-desc { font-size: var(--fs-body); color: var(--text-muted) }

.settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  max-width: 1200px;
}

.settings-card {
  background: var(--bg-card) !important;
  border: 1px solid var(--border-color) !important;
  border-radius: var(--radius-lg) !important;
  color: var(--text-color) !important;
}

.card-header {
  display: flex; align-items: center; gap: 10px;
}
.header-icon { font-size: var(--fs-h3); color: var(--color-primary) }
.header-title { font-size: var(--fs-body); font-weight: var(--fw-semi); color: var(--text-color) }
.config-status { margin-left: auto }

.settings-form :deep(.el-form-item) { margin-bottom: 20px }
.settings-form :deep(.el-form-item__label) {
  font-weight: var(--fw-medium); color: var(--text-secondary); font-size: var(--fs-body);
}

.form-hint { font-size: var(--fs-sub); color: var(--text-muted); margin-top: 4px; line-height: 1.5 }

.slider-row { width: 100% }
.slider-row :deep(.el-slider) { margin-right: 8px }

/* 数据库统计 */
.db-stats {
  display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
  margin-bottom: 18px; padding: 16px;
  background: rgba(255,255,255,0.03); border-radius: var(--radius-md);
}
.db-stat { display: flex; align-items: baseline; gap: 6px; font-size: var(--fs-body); color: var(--text-muted) }
.db-stat strong { color: var(--color-primary); font-size: var(--fs-h2); font-weight: var(--fw-bold) }

/* 关于 */
.about-grid { display: flex; flex-direction: column; gap: 4px }
.about-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 0; border-bottom: 1px solid var(--border-color);
  font-size: var(--fs-body); color: var(--text-secondary);
}
.about-item:last-child { border-bottom: none }
.about-label { color: var(--text-muted); flex-shrink: 0; margin-right: 12px }

.model-radio { display: flex; flex-direction: column; gap: 8px }
</style>
