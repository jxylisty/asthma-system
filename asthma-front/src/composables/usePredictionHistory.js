/**
 * 预测历史记录管理（IndexedDB via localStorage 降级）
 * 使用 localStorage 存储，上限 200 条 FIFO
 */
import { ref } from 'vue'

const STORAGE_KEY = 'prediction_history'
const MAX_RECORDS = 200

const history = ref([])

// 从 localStorage 加载
function loadHistory() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      history.value = JSON.parse(raw)
    }
  } catch (e) {
    console.error('加载预测历史失败:', e)
    history.value = []
  }
}

// 保存到 localStorage
function saveHistory() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history.value))
  } catch (e) {
    console.error('保存预测历史失败:', e)
  }
}

// 初始化加载
loadHistory()

export function usePredictionHistory() {
  /**
   * 保存一条预测记录
   * @param {Object} record - { smiles, compound_name, model_name, probability, level, features_computed, mw, timestamp }
   */
  function saveRecord(record) {
    const item = {
      id: Date.now() + '_' + Math.random().toString(36).slice(2, 8),
      timestamp: new Date().toISOString(),
      ...record
    }
    history.value.unshift(item)
    // FIFO 限制
    if (history.value.length > MAX_RECORDS) {
      history.value = history.value.slice(0, MAX_RECORDS)
    }
    saveHistory()
    return item
  }

  /**
   * 获取历史记录（支持搜索）
   * @param {string} query - 搜索关键词（化合物名/SMILES）
   * @returns {Array}
   */
  function getRecords(query = '') {
    if (!query) return history.value
    const q = query.toLowerCase()
    return history.value.filter(r =>
      (r.compound_name || '').toLowerCase().includes(q) ||
      (r.smiles || '').toLowerCase().includes(q)
    )
  }

  /**
   * 删除单条记录
   * @param {string} id
   */
  function deleteRecord(id) {
    history.value = history.value.filter(r => r.id !== id)
    saveHistory()
  }

  /**
   * 清空所有记录
   */
  function clearAll() {
    history.value = []
    saveHistory()
  }

  /**
   * 获取单条记录
   * @param {string} id
   */
  function getRecord(id) {
    return history.value.find(r => r.id === id)
  }

  return {
    history,
    saveRecord,
    getRecords,
    getRecord,
    deleteRecord,
    clearAll
  }
}
