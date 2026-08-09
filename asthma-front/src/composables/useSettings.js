import { ref, watch } from 'vue'

const STORAGE_KEY = 'asthma-settings'

const bgColors = [
  { label: '深蓝科技', value: 'dark-blue', gradient: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)', dark: true },
  { label: '清新绿', value: 'fresh-green', gradient: 'linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%)', dark: false },
  { label: '温暖橙', value: 'warm-orange', gradient: 'linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%)', dark: false },
  { label: '优雅紫', value: 'elegant-purple', gradient: 'linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%)', dark: false },
  { label: '简约白', value: 'simple-white', gradient: 'linear-gradient(135deg, #f5f7fa 0%, #e4e9f2 100%)', dark: false },
  { label: '暗夜黑', value: 'midnight-black', gradient: 'linear-gradient(135deg, #0d0d0d 0%, #1a1a2e 50%, #16213e 100%)', dark: true },
  { label: '国风科技', value: 'guofeng-tech', gradient: 'url("/现代国风暗色科技感背景.png") center center / 100% auto no-repeat fixed, #1a1a2e', dark: true }
]

const darkBgColors = ['dark-blue', 'midnight-black', 'guofeng-tech']

const fontFamilyMap = {
  default: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  microsoft: '"Microsoft YaHei", "微软雅黑", sans-serif',
  pingfang: '"PingFang SC", "苹方", sans-serif',
  songti: '"SimSun", "宋体", serif',
  kaiti: '"KaiTi", "楷体", serif',
  arial: '"Arial", "Helvetica Neue", Helvetica, sans-serif'
}

const fontSizeMap = {
  small: '12px',
  default: '14px',
  medium: '16px',
  large: '18px',
  xlarge: '20px'
}

const clickEffectOptions = [
  { label: '无特效', value: 'none' },
  { label: '涟漪扩散', value: 'ripple' },
  { label: '科技光环', value: 'tech' },
  { label: '粒子爆发', value: 'particles' }
]

const defaultSettings = {
  bgColor: 'dark-blue',
  fontFamily: 'default',
  fontSize: 'default',
  clickEffect: 'ripple',
  autoRefresh: false,
  refreshInterval: 60,
  cacheData: true,
  probabilityThreshold: 70,
  systemNotification: true,
  analysisCompleteNotification: true,
  dataUpdateNotification: true,
  speechVoice: '',
  speechRate: 1,
  speechPitch: 1,
  speechEnabled: true
}

const bgColor = ref(defaultSettings.bgColor)
const fontFamily = ref(defaultSettings.fontFamily)
const fontSize = ref(defaultSettings.fontSize)
const clickEffect = ref(defaultSettings.clickEffect)
const autoRefresh = ref(defaultSettings.autoRefresh)
const refreshInterval = ref(defaultSettings.refreshInterval)
const cacheData = ref(defaultSettings.cacheData)
const probabilityThreshold = ref(defaultSettings.probabilityThreshold)
const systemNotification = ref(defaultSettings.systemNotification)
const analysisCompleteNotification = ref(defaultSettings.analysisCompleteNotification)
const dataUpdateNotification = ref(defaultSettings.dataUpdateNotification)
const speechVoice = ref(defaultSettings.speechVoice)
const speechRate = ref(defaultSettings.speechRate)
const speechPitch = ref(defaultSettings.speechPitch)
const speechEnabled = ref(defaultSettings.speechEnabled)

function applySettings() {
  const root = document.documentElement
  const selectedColor = bgColors.find(c => c.value === bgColor.value)
  
  if (selectedColor) {
    root.style.setProperty('--bg-gradient', selectedColor.gradient)
  }
  
  root.style.setProperty('--font-family', fontFamilyMap[fontFamily.value])
  root.style.setProperty('--font-size-base', fontSizeMap[fontSize.value])
  
  const isDark = darkBgColors.includes(bgColor.value)
  root.style.setProperty('--is-dark', isDark ? 'true' : 'false')
  root.style.setProperty('--text-color', isDark ? '#fff' : '#1a1a2e')
  root.style.setProperty('--text-secondary', isDark ? 'rgba(255, 255, 255, 0.6)' : '#666')
  root.style.setProperty('--text-muted', isDark ? 'rgba(255, 255, 255, 0.4)' : '#999')
}

function saveSettings() {
  const settings = {
    bgColor: bgColor.value,
    fontFamily: fontFamily.value,
    fontSize: fontSize.value,
    clickEffect: clickEffect.value,
    autoRefresh: autoRefresh.value,
    refreshInterval: refreshInterval.value,
    cacheData: cacheData.value,
    probabilityThreshold: probabilityThreshold.value,
    systemNotification: systemNotification.value,
    analysisCompleteNotification: analysisCompleteNotification.value,
    dataUpdateNotification: dataUpdateNotification.value,
    speechVoice: speechVoice.value,
    speechRate: speechRate.value,
    speechPitch: speechPitch.value,
    speechEnabled: speechEnabled.value
  }
  
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
}

function loadSettings() {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    try {
      const settings = JSON.parse(saved)
      bgColor.value = settings.bgColor ?? defaultSettings.bgColor
      fontFamily.value = settings.fontFamily ?? defaultSettings.fontFamily
      fontSize.value = settings.fontSize ?? defaultSettings.fontSize
      clickEffect.value = settings.clickEffect ?? defaultSettings.clickEffect
      autoRefresh.value = settings.autoRefresh ?? defaultSettings.autoRefresh
      refreshInterval.value = settings.refreshInterval ?? defaultSettings.refreshInterval
      cacheData.value = settings.cacheData ?? defaultSettings.cacheData
      probabilityThreshold.value = settings.probabilityThreshold ?? defaultSettings.probabilityThreshold
      systemNotification.value = settings.systemNotification ?? defaultSettings.systemNotification
      analysisCompleteNotification.value = settings.analysisCompleteNotification ?? defaultSettings.analysisCompleteNotification
      dataUpdateNotification.value = settings.dataUpdateNotification ?? defaultSettings.dataUpdateNotification
      speechVoice.value = settings.speechVoice ?? defaultSettings.speechVoice
      speechRate.value = settings.speechRate ?? defaultSettings.speechRate
      speechPitch.value = settings.speechPitch ?? defaultSettings.speechPitch
      speechEnabled.value = settings.speechEnabled ?? defaultSettings.speechEnabled
    } catch (e) {
      console.error('Failed to load settings:', e)
    }
  }
  
  applySettings()
}

function resetSettings() {
  bgColor.value = defaultSettings.bgColor
  fontFamily.value = defaultSettings.fontFamily
  fontSize.value = defaultSettings.fontSize
  clickEffect.value = defaultSettings.clickEffect
  autoRefresh.value = defaultSettings.autoRefresh
  refreshInterval.value = defaultSettings.refreshInterval
  cacheData.value = defaultSettings.cacheData
  probabilityThreshold.value = defaultSettings.probabilityThreshold
  systemNotification.value = defaultSettings.systemNotification
  analysisCompleteNotification.value = defaultSettings.analysisCompleteNotification
  dataUpdateNotification.value = defaultSettings.dataUpdateNotification
  speechVoice.value = defaultSettings.speechVoice
  speechRate.value = defaultSettings.speechRate
  speechPitch.value = defaultSettings.speechPitch
  speechEnabled.value = defaultSettings.speechEnabled
  
  localStorage.removeItem(STORAGE_KEY)
  applySettings()
}

watch([bgColor, fontFamily, fontSize, clickEffect, autoRefresh, refreshInterval, cacheData, probabilityThreshold, systemNotification, analysisCompleteNotification, dataUpdateNotification, speechVoice, speechRate, speechPitch, speechEnabled], () => {
  applySettings()
  saveSettings()
}, { deep: true })

export function useSettings() {
  return {
    bgColor,
    fontFamily,
    fontSize,
    clickEffect,
    autoRefresh,
    refreshInterval,
    cacheData,
    probabilityThreshold,
    systemNotification,
    analysisCompleteNotification,
    dataUpdateNotification,
    speechVoice,
    speechRate,
    speechPitch,
    speechEnabled,
    bgColors,
    fontFamilyMap,
    fontSizeMap,
    clickEffectOptions,
    loadSettings,
    resetSettings,
    applySettings
  }
}

export { loadSettings as initSettings }