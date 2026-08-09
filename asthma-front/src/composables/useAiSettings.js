import { ref, watch, computed } from 'vue'

const STORAGE_KEY = 'asthma-ai-settings'

const defaultAiSettings = {
  provider: 'deepseek',       // deepseek | openai
  apiKey: '',
  baseUrl: '',                // 留空使用 provider 默认
  model: '',                  // 留空使用 provider 默认
}

const provider = ref(defaultAiSettings.provider)
const apiKey = ref(defaultAiSettings.apiKey)
const baseUrl = ref(defaultAiSettings.baseUrl)
const model = ref(defaultAiSettings.model)

// 提供商预设
const providerPresets = [
  {
    label: 'DeepSeek',
    value: 'deepseek',
    baseUrl: 'https://api.deepseek.com/v1',
    model: 'deepseek-chat',
    desc: '性价比高，推荐使用',
    applyUrl: 'https://platform.deepseek.com/api_keys',
  },
  {
    label: 'OpenAI',
    value: 'openai',
    baseUrl: 'https://api.openai.com/v1',
    model: 'gpt-4o',
    desc: 'GPT-4o，效果最佳',
    applyUrl: 'https://platform.openai.com/api-keys',
  },
]

const isConfigured = computed(() => Boolean(apiKey.value && apiKey.value.trim()))

function loadAiSettings() {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    try {
      const s = JSON.parse(saved)
      provider.value = s.provider ?? defaultAiSettings.provider
      apiKey.value = s.apiKey ?? defaultAiSettings.apiKey
      baseUrl.value = s.baseUrl ?? defaultAiSettings.baseUrl
      model.value = s.model ?? defaultAiSettings.model
    } catch (e) {
      console.error('Failed to load AI settings:', e)
    }
  }
}

function saveAiSettings() {
  const settings = {
    provider: provider.value,
    apiKey: apiKey.value,
    baseUrl: baseUrl.value,
    model: model.value,
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
}

function resetAiSettings() {
  provider.value = defaultAiSettings.provider
  apiKey.value = defaultAiSettings.apiKey
  baseUrl.value = defaultAiSettings.baseUrl
  model.value = defaultAiSettings.model
  localStorage.removeItem(STORAGE_KEY)
}

// 切换 provider 时自动填充默认 base_url / model（仅当用户未自定义时）
watch(provider, (val) => {
  const preset = providerPresets.find(p => p.value === val)
  if (preset) {
    baseUrl.value = preset.baseUrl
    model.value = preset.model
  }
})

watch([provider, apiKey, baseUrl, model], () => {
  saveAiSettings()
}, { deep: true })

/**
 * 构造调用后端 AI 接口所需的请求头
 */
function buildAiHeaders() {
  return {
    'X-AI-API-Key': apiKey.value || '',
    'X-AI-Provider': provider.value || 'deepseek',
    'X-AI-Base-URL': baseUrl.value || '',
    'X-AI-Model': model.value || '',
  }
}

export function useAiSettings() {
  return {
    provider,
    apiKey,
    baseUrl,
    model,
    providerPresets,
    isConfigured,
    loadAiSettings,
    saveAiSettings,
    resetAiSettings,
    buildAiHeaders,
  }
}

export { loadAiSettings as initAiSettings }
