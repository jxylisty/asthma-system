import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000
})

// 请求拦截器：自动携带 JWT
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：统一提取 data
api.interceptors.response.use(
  response => {
    const res = response.data
    if (res.code !== 200) {
      console.error('API Error:', res.message)
      // 401 未登录：清除 token 跳转登录
      if (res.code === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      }
      return Promise.reject(new Error(res.message))
    }
    return res.data
  },
  error => Promise.reject(error)
)

// ===== 认证 =====
export const login = (username, password) => api.post('/auth/login', { username, password })
export const register = (username, password, email = '') => api.post('/auth/register', { username, password, email })
export const getCurrentUser = () => api.get('/auth/me')

// ===== 系统 =====
export const getStatistics = () => api.get('/system/statistics')
export const search = (keyword) => api.get('/system/search', { params: { keyword } })

// ===== 方剂 =====
export const getPrescriptions = (page = 1, pageSize = 20, keyword = '') => api.get('/prescriptions', { params: { page, page_size: pageSize, keyword } })
export const getPrescriptionDetail = (id) => api.get(`/prescriptions/${id}`)
export const getPrescriptionNetwork = (id, minProb = 0.5, asthmaOnly = false, maxCompounds = 30, maxTargets = 10) => api.get(`/prescriptions/${id}/network`, { params: { min_prob: minProb, asthma_only: asthmaOnly, max_compounds: maxCompounds, max_targets_per_compound: maxTargets } })
export const getPrescriptionRadar = (id) => api.get(`/prescriptions/${id}/radar`)
export const getPrescriptionCompounds = (id, minProb = 0.5) => api.get(`/prescriptions/${id}/compounds`, { params: { min_prob: minProb } })

// ===== 自定义处方分析 =====
export const analyzeCustomPrescription = (data, minProb = 0.5) => api.post('/prescriptions/analyze', data, { params: { min_prob: minProb } })

/**
 * 流式调用 AI 报告接口（SSE）
 * @param {string} url - 后端接口地址
 * @param {object} body - 请求体
 * @param {object} aiHeaders - AI 配置请求头（X-AI-API-Key 等）
 * @param {function} onSnapshot - 收到结构化快照回调
 * @param {function} onDelta - 收到增量文本回调
 * @param {function} onError - 错误回调
 * @param {function} onDone - 完成回调
 * @param {AbortSignal} signal - 可选，用于中止请求
 */
export async function streamAiReport({
  url,
  body,
  aiHeaders,
  onSnapshot,
  onDelta,
  onError,
  onDone,
  signal,
}) {
  const token = localStorage.getItem('token')
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...aiHeaders,
  }

  let resp
  try {
    resp = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      signal,
    })
  } catch (e) {
    if (e.name === 'AbortError') return
    onError && onError({ code: 'network_error', message: '网络连接失败：' + e.message })
    return
  }

  if (!resp.ok) {
    onError && onError({ code: 'http_error', message: `请求失败 (${resp.status})` })
    return
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      // 按 SSE 事件分割（双换行）
      const parts = buffer.split('\n\n')
      buffer = parts.pop() // 最后一段可能不完整，保留

      for (const part of parts) {
        const lines = part.split('\n')
        for (const line of lines) {
          if (!line.startsWith('data:')) continue
          const payload = line.slice(5).trim()
          if (!payload) continue
          try {
            const obj = JSON.parse(payload)
            if (obj.type === 'snapshot' && onSnapshot) {
              onSnapshot(obj.data)
            } else if (obj.type === 'delta' && onDelta) {
              onDelta(obj.content)
            } else if (obj.type === 'error' && onError) {
              onError({ code: obj.code, message: obj.message })
            } else if (obj.type === 'done' && onDone) {
              onDone()
            }
          } catch (e) {
            // 忽略解析失败的行
          }
        }
      }
    }
    onDone && onDone()
  } catch (e) {
    if (e.name === 'AbortError') return
    onError && onError({ code: 'stream_error', message: '流读取失败：' + e.message })
  }
}

// ===== 药材 =====
export const getHerbs = (params = {}) => api.get('/herbs', { params })
export const getHerbFilterOptions = () => api.get('/herbs/filter-options')
export const getHerbDetail = (id) => api.get(`/herbs/${id}`)
export const getHerbCompounds = (id) => api.get(`/herbs/${id}/compounds`)

// ===== 化合物 =====
export const getCompounds = (page = 1, pageSize = 20, keyword = '', minProb = 0) => api.get('/compounds', { params: { page, page_size: pageSize, keyword, min_prob: minProb } })
export const getCompoundDetail = (id) => api.get(`/compounds/${id}`)
export const getHighPotentialCompounds = (page = 1, pageSize = 20) => api.get('/compounds/high-potential', { params: { page, page_size: pageSize } })
export const getCompoundTargets = (id) => api.get(`/compounds/${id}/targets`)
export const getCompoundRadar = (id) => api.get(`/compounds/${id}/radar`)
export const getCompoundStructure = (id) => api.get(`/compounds/${id}/structure`)

// ===== 预测 =====
export const getPredictionModels = () => api.get('/prediction/models')
export const predictCctcm = (data) => api.post('/prediction/predict/cctcm', data)
export const predictHerb = (data) => api.post('/prediction/predict/herb', data)
// SMILES 自动预测
export const predictBySmiles = (data) => api.post('/prediction/predict/smiles', data)
export const batchPredictBySmiles = (data) => api.post('/prediction/predict/smiles/batch', data)
export const uploadAndPredict = (formData, modelName = 'cctcm') => api.post(`/prediction/predict/smiles/upload?model_name=${modelName}`, formData, {
  headers: { 'Content-Type': 'multipart/form-data' },
  timeout: 300000
})
export const downloadBatchResult = (filename) => `${api.defaults.baseURL}/prediction/predict/smiles/download/${filename}`

// ===== 专家模式 =====
export const getExpertMetrics = () => api.get('/expert/metrics')
export const getFeatureImportance = () => api.get('/expert/feature-importance')
