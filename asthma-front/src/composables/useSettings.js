import { ref } from 'vue'

const STORAGE_KEY = 'asthma-settings'

const clickEffectOptions = [
  { label: '无特效', value: 'none' },
  { label: '涟漪扩散', value: 'ripple' },
  { label: '科技光环', value: 'tech' },
  { label: '粒子爆发', value: 'particles' }
]

const defaultSettings = {
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

function saveSettings() {
  const settings = {
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
      const s = JSON.parse(saved)
      clickEffect.value = s.clickEffect ?? defaultSettings.clickEffect
      autoRefresh.value = s.autoRefresh ?? defaultSettings.autoRefresh
      refreshInterval.value = s.refreshInterval ?? defaultSettings.refreshInterval
      cacheData.value = s.cacheData ?? defaultSettings.cacheData
      probabilityThreshold.value = s.probabilityThreshold ?? defaultSettings.probabilityThreshold
      systemNotification.value = s.systemNotification ?? defaultSettings.systemNotification
      analysisCompleteNotification.value = s.analysisCompleteNotification ?? defaultSettings.analysisCompleteNotification
      dataUpdateNotification.value = s.dataUpdateNotification ?? defaultSettings.dataUpdateNotification
      speechVoice.value = s.speechVoice ?? defaultSettings.speechVoice
      speechRate.value = s.speechRate ?? defaultSettings.speechRate
      speechPitch.value = s.speechPitch ?? defaultSettings.speechPitch
      speechEnabled.value = s.speechEnabled ?? defaultSettings.speechEnabled
    } catch (e) {
      console.error('Failed to load settings:', e)
    }
  }
}

export function useSettings() {
  return {
    clickEffect,
    clickEffectOptions,
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
    loadSettings,
    saveSettings
  }
}

export { loadSettings as initSettings }