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

      <!-- 板块5：外观设置（仅管理员） -->
      <el-card v-if="isAdmin" class="settings-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon class="header-icon"><Brush /></el-icon>
            <span class="header-title">外观设置</span>
            <el-tag type="warning" size="small" effect="dark" class="config-status">管理员</el-tag>
          </div>
        </template>

        <div class="settings-form">
          <!-- 预设主题 -->
          <el-form-item label="预设主题">
            <div class="theme-presets">
              <button
                v-for="t in themePresets" :key="t.name"
                :class="['theme-preset-btn', { active: activePreset === t.name }]"
                :style="{ background: t.preview }"
                :title="t.label"
                @click="applyPreset(t)"
              >
                <span class="preset-dot" :style="{ background: t.accent }"></span>
                <span class="preset-label">{{ t.label }}</span>
              </button>
            </div>
          </el-form-item>

          <!-- 背景色 -->
          <el-form-item label="页面背景色">
            <div class="color-picker-row">
              <el-color-picker v-model="themeColors.bgPrimary" @change="applyTheme" />
              <el-input v-model="themeColors.bgPrimary" size="small" class="color-input" />
              <span class="color-label">--bg-primary</span>
            </div>
          </el-form-item>

          <el-form-item label="卡片背景色">
            <div class="color-picker-row">
              <el-color-picker v-model="themeColors.bgSecondary" @change="applyTheme" />
              <el-input v-model="themeColors.bgSecondary" size="small" class="color-input" />
              <span class="color-label">--bg-secondary</span>
            </div>
          </el-form-item>

          <el-form-item label="主文字颜色">
            <div class="color-picker-row">
              <el-color-picker v-model="themeColors.textColor" @change="applyTheme" />
              <el-input v-model="themeColors.textColor" size="small" class="color-input" />
              <span class="color-label">--text-color</span>
            </div>
          </el-form-item>

          <el-form-item label="次要文字颜色">
            <div class="color-picker-row">
              <el-color-picker v-model="themeColors.textSecondary" @change="applyTheme" />
              <el-input v-model="themeColors.textSecondary" size="small" class="color-input" />
              <span class="color-label">--text-secondary</span>
            </div>
          </el-form-item>

          <el-form-item label="主题强调色">
            <div class="color-picker-row">
              <el-color-picker v-model="themeColors.colorPrimary" @change="applyTheme" />
              <el-input v-model="themeColors.colorPrimary" size="small" class="color-input" />
              <span class="color-label">--color-primary</span>
            </div>
          </el-form-item>

          <!-- 实时预览 -->
          <el-form-item label="预览">
            <div class="theme-preview" :style="previewStyle">
              <div class="preview-header">
                <span class="preview-dot" :style="{ background: themeColors.colorPrimary }"></span>
                <span class="preview-title">儿童哮喘方剂智能分析系统</span>
              </div>
              <div class="preview-body">
                <div class="preview-card">
                  <span class="preview-card-title">方剂名称</span>
                  <span class="preview-card-sub">12 味中药 · 36 个化合物</span>
                </div>
                <div class="preview-card">
                  <span class="preview-card-title">目标靶点</span>
                  <span class="preview-card-sub">MAPK · EGFR · IL6 · TNF</span>
                </div>
              </div>
              <div class="preview-footer">
                <span class="preview-tag"># 哮喘</span>
                <span class="preview-tag"># 中药</span>
                <span class="preview-tag"># 入血预测</span>
              </div>
            </div>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="applyTheme">
              <el-icon><Check /></el-icon> 应用外观
            </el-button>
            <el-button @click="resetTheme">
              <el-icon><RefreshLeft /></el-icon> 恢复默认
            </el-button>
          </el-form-item>
        </div>
      </el-card>

      <!-- 板块6：语音播报设置 -->
      <el-card class="settings-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon class="header-icon"><Microphone /></el-icon>
            <span class="header-title">语音播报设置</span>
            <el-tag v-if="speechEnabled" type="success" size="small" effect="dark" class="config-status">已启用</el-tag>
            <el-tag v-else type="info" size="small" effect="dark" class="config-status">已禁用</el-tag>
          </div>
        </template>

        <div class="settings-form">
          <el-form-item label="语音播报">
            <el-switch v-model="speechEnabled" active-text="启用" inactive-text="关闭" />
            <div class="form-hint">开启后可在详情页点击播报按钮朗读数据</div>
          </el-form-item>

          <el-form-item label="语音音色">
            <el-select v-model="speechVoice" placeholder="选择语音" clearable :disabled="!speechEnabled">
              <el-option v-for="v in voiceList" :key="v.name" :label="v.name" :value="v.name" />
            </el-select>
            <div class="form-hint">选择中文语音效果最佳，留空则使用浏览器默认语音</div>
          </el-form-item>

          <el-form-item label="语速">
            <el-slider v-model="speechRate" :min="0.5" :max="2" :step="0.1" show-input :disabled="!speechEnabled" />
            <div class="form-hint">正常语速为 1.0，数值越大越快</div>
          </el-form-item>

          <el-form-item label="音调">
            <el-slider v-model="speechPitch" :min="0.5" :max="2" :step="0.1" show-input :disabled="!speechEnabled" />
            <div class="form-hint">正常音调为 1.0，数值越大越尖锐</div>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" :disabled="!speechEnabled" @click="testSpeech">
              <el-icon><Microphone /></el-icon> {{ isSpeaking ? '停止测试' : '测试播报' }}
            </el-button>
            <el-button :disabled="!speechEnabled" @click="refreshVoices">
              <el-icon><RefreshLeft /></el-icon> 刷新语音列表
            </el-button>
          </el-form-item>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import {
  MagicStick, Key, Link, Check, RefreshLeft, CircleCheckFilled,
  DataAnalysis, Coin, Delete, InfoFilled, Brush, Sunny, Moon, Picture, Microphone
} from '@element-plus/icons-vue'
import { useAiSettings } from '../composables/useAiSettings'
import { useAuth } from '../composables/useAuth'
import { useSpeech } from '../composables/useSpeech'
import { useSettings } from '../composables/useSettings'
import { getStatistics } from '../api'

const { user } = useAuth()
const isAdmin = computed(() => (user.value?.role === 'admin' || user.value?.username === 'admin'))

const { speak, stop, getVoices, isSpeaking } = useSpeech()
const { speechVoice, speechRate, speechPitch, speechEnabled } = useSettings()

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

// ===== 语音播报设置 =====
const voiceList = ref([])
function refreshVoices() {
  voiceList.value = getVoices()
  if (voiceList.value.length === 0) {
    // 有些浏览器需要异步加载语音
    setTimeout(() => { voiceList.value = getVoices() }, 500)
  }
}
function testSpeech() {
  if (isSpeaking.value) { stop(); return }
  speak('您好，这是语音播报测试。当前语速为' + speechRate.value + '，音调为' + speechPitch.value + '。', {
    voice: speechVoice.value,
    rate: speechRate.value,
    pitch: speechPitch.value
  })
}
onMounted(() => { refreshVoices() })

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

// ===== 外观设置（管理员） =====
const themePresets = [
  { name: 'default', label: '默认暗色', preview: 'linear-gradient(135deg, #0f172a, #1e293b)', accent: '#2dd4bf',
    bgPrimary: '#0f172a', bgSecondary: '#1e293b', textColor: '#f1f5f9', textSecondary: '#cbd5e1', colorPrimary: '#2dd4bf' },
  { name: 'deep-blue', label: '深蓝', preview: 'linear-gradient(135deg, #0a1628, #132240)', accent: '#38bdf8',
    bgPrimary: '#0a1628', bgSecondary: '#132240', textColor: '#e2e8f0', textSecondary: '#94a3b8', colorPrimary: '#38bdf8' },
  { name: 'pure-dark', label: '纯黑', preview: 'linear-gradient(135deg, #09090b, #18181b)', accent: '#a78bfa',
    bgPrimary: '#09090b', bgSecondary: '#18181b', textColor: '#fafafa', textSecondary: '#a1a1aa', colorPrimary: '#a78bfa' },
  { name: 'forest', label: '墨绿', preview: 'linear-gradient(135deg, #0f1a14, #1a3028)', accent: '#34d399',
    bgPrimary: '#0f1a14', bgSecondary: '#1a3028', textColor: '#ecfdf5', textSecondary: '#a7f3d0', colorPrimary: '#34d399' },
  { name: 'warm', label: '暖棕', preview: 'linear-gradient(135deg, #1c120c, #2d1f14)', accent: '#fbbf24',
    bgPrimary: '#1c120c', bgSecondary: '#2d1f14', textColor: '#fef3c7', textSecondary: '#fcd34d', colorPrimary: '#fbbf24' },
]

const activePreset = ref(localStorage.getItem('theme_preset') || 'default')
const themeColors = ref({
  bgPrimary: '#0f172a',
  bgSecondary: '#1e293b',
  textColor: '#f1f5f9',
  textSecondary: '#cbd5e1',
  colorPrimary: '#2dd4bf',
})

// 初始化：从 localStorage 恢复
const saved = localStorage.getItem('theme_colors')
if (saved) {
  try { themeColors.value = JSON.parse(saved) } catch {}
}

const previewStyle = computed(() => ({
  background: themeColors.value.bgPrimary,
  color: themeColors.value.textColor,
  borderColor: themeColors.value.bgSecondary,
}))

function applyPreset(t) {
  activePreset.value = t.name
  themeColors.value = {
    bgPrimary: t.bgPrimary,
    bgSecondary: t.bgSecondary,
    textColor: t.textColor,
    textSecondary: t.textSecondary,
    colorPrimary: t.colorPrimary,
  }
  applyTheme()
}

function applyTheme() {
  const c = themeColors.value
  const root = document.documentElement
  root.style.setProperty('--bg-primary', c.bgPrimary)
  root.style.setProperty('--bg-secondary', c.bgSecondary)
  root.style.setProperty('--bg-gradient', c.bgPrimary)
  root.style.setProperty('--text-color', c.textColor)
  root.style.setProperty('--text-secondary', c.textSecondary)
  root.style.setProperty('--color-primary', c.colorPrimary)
  root.style.setProperty('--color-primary-light', adjustColor(c.colorPrimary, 20))
  root.style.setProperty('--el-bg-color', c.bgPrimary)
  root.style.setProperty('--el-bg-color-overlay', c.bgSecondary)
  root.style.setProperty('--el-bg-color-page', c.bgPrimary)
  root.style.setProperty('--el-fill-color-blank', c.bgPrimary)
  root.style.setProperty('--el-text-color-primary', c.textColor)
  root.style.setProperty('--el-text-color-regular', c.textSecondary)
  localStorage.setItem('theme_preset', activePreset.value)
  localStorage.setItem('theme_colors', JSON.stringify(c))
  ElMessage.success('外观已应用')
}

function adjustColor(hex, amount) {
  const num = parseInt(hex.replace('#', ''), 16)
  const r = Math.min(255, (num >> 16) + amount)
  const g = Math.min(255, ((num >> 8) & 0x00FF) + amount)
  const b = Math.min(255, (num & 0x0000FF) + amount)
  return `#${(r << 16 | g << 8 | b).toString(16).padStart(6, '0')}`
}

function resetTheme() {
  localStorage.removeItem('theme_preset')
  localStorage.removeItem('theme_colors')
  const def = themePresets[0]
  applyPreset(def)
  ElMessage.success('已恢复默认外观')
}

// 离开设置页时清除内联样式，恢复 App.vue 的 CSS 变量默认值
function clearThemeInline() {
  const root = document.documentElement
  const vars = [
    '--bg-primary', '--bg-secondary', '--bg-gradient',
    '--text-color', '--text-secondary', '--color-primary', '--color-primary-light',
    '--el-bg-color', '--el-bg-color-overlay', '--el-bg-color-page', '--el-fill-color-blank',
    '--el-text-color-primary', '--el-text-color-regular'
  ]
  vars.forEach(v => root.style.removeProperty(v))
}
onBeforeUnmount(clearThemeInline)
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

/* 外观设置 */
.theme-presets { display: flex; gap: 10px; flex-wrap: wrap }
.theme-preset-btn {
  width: 90px; height: 52px; border-radius: 10px; border: 2px solid transparent;
  cursor: pointer; position: relative; overflow: hidden;
  transition: all 0.2s; padding: 0;
}
.theme-preset-btn:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.4) }
.theme-preset-btn.active { border-color: var(--color-primary); box-shadow: 0 0 0 3px rgba(45,212,191,0.25) }
.preset-dot { position: absolute; top: 8px; right: 8px; width: 10px; height: 10px; border-radius: 50% }
.preset-label { position: absolute; bottom: 6px; left: 8px; font-size: 11px; color: rgba(255,255,255,0.85); font-weight: 600 }

.color-picker-row { display: flex; align-items: center; gap: 10px }
.color-input { width: 120px }
.color-label { font-size: var(--fs-sub); color: var(--text-muted); white-space: nowrap }

/* 预览卡片 */
.theme-preview {
  border-radius: 12px; border: 1px solid; padding: 16px; width: 100%;
  transition: all 0.3s;
}
.preview-header { display: flex; align-items: center; gap: 8px; margin-bottom: 12px }
.preview-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0 }
.preview-title { font-size: 14px; font-weight: 700 }
.preview-body { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 10px }
.preview-card {
  padding: 10px; border-radius: 8px; background: rgba(255,255,255,0.06);
}
.preview-card-title { font-size: 13px; font-weight: 600; display: block; margin-bottom: 3px; opacity: 0.9 }
.preview-card-sub { font-size: 11px; opacity: 0.55 }
.preview-footer { display: flex; gap: 6px; flex-wrap: wrap }
.preview-tag {
  font-size: 10px; padding: 2px 8px; border-radius: 4px;
  background: rgba(255,255,255,0.08); opacity: 0.7;
}
</style>
