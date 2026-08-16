<template>
  <div class="compounds-container">
    <div class="page-header">
      <h2 class="page-title">化合物详情</h2>
      <p class="page-desc">系统收录的化合物数据汇总，点击卡片查看分子特征与靶点信息</p>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索化合物名称..."
        class="search-input"
        clearable
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <div v-loading="loading" class="compound-grid">
      <el-card
        v-for="item in compounds"
        :key="item.id"
        class="compound-card"
        @click="handleCardClick(item)"
      >
        <!-- Row 1: 名称 + 哮喘标签 -->
        <div class="cc-top">
          <div class="cc-name-line">
            <span class="cc-icon">🧬</span>
            <span class="cc-name" :title="item.name">{{ item.name }}</span>
          </div>
          <el-tag v-if="item.asthmaRelated" type="danger" size="small" effect="dark">哮喘相关</el-tag>
          <el-tag v-else type="info" size="small" effect="plain">普通</el-tag>
        </div>

        <!-- Row 2: 预测入血概率条 -->
        <div class="cc-prob-section">
          <span class="cc-prob-label">ccTCM 入血概率</span>
          <div class="cc-prob-bar-wrap">
            <div class="cc-prob-bar">
              <div
                class="cc-prob-fill"
                :style="{
                  width: Math.round(item.bloodEntryProbability * 100) + '%',
                  background: getBarGradient(item.bloodEntryProbability)
                }"
              ></div>
            </div>
            <span class="cc-prob-num" :style="{ color: getProbColor(item.bloodEntryProbability) }">
              {{ (item.bloodEntryProbability * 100).toFixed(1) }}%
            </span>
          </div>
        </div>

        <div class="cc-divider"></div>

        <!-- Row 3: 4 项核心指标 -->
        <div class="cc-metrics">
        <div class="cc-metric">
        <span class="cc-m-label">分子量</span>
        <span class="cc-m-value">
        {{ item.mw != null ? item.mw.toFixed(2) : '—' }}<template v-if="item.mw != null"> g/mol</template>
        </span>
        </div>
        <div class="cc-metric">
        <span class="cc-m-label">脂水分配 LogP</span>
        <span class="cc-m-value">{{ item.logp != null ? item.logp.toFixed(2) : '—' }}</span>
        </div>
        <div class="cc-metric cc-metric-wide">
        <span class="cc-m-label">来源药材</span>
        <div class="cc-herb-tags">
        <template v-if="item.herbNames && item.herbNames.length">
        <el-tag
        v-for="(herb, idx) in item.herbNames.slice(0, 3)"
        :key="idx"
        type="success"
        size="small"
        effect="light"
        class="cc-herb-tag"
        >{{ herb }}</el-tag>
        <span v-if="item.herbNames.length > 3" class="cc-more-herbs">+{{ item.herbNames.length - 3 }}</span>
        </template>
        <span v-else class="cc-m-value-muted">—</span>
        </div>
        </div>
        <div class="cc-metric">
        <span class="cc-m-label">哮喘命中靶点</span>
        <span class="cc-m-value cc-highlight">{{ item.targetCount || 0 }} 个</span>
        </div>
        </div>

        <div class="cc-divider"></div>

        <!-- Row 4: SMILES 截断展示 + 复制完整 -->
        <div class="cc-smiles-row">
        <div class="cc-smiles-info">
        <span class="cc-smiles-label">SMILES</span>
        <span
        class="cc-smiles-text"
        :title="'点击复制查看完整 SMILES: ' + (item.smiles || item.smileShort)"
        >
        {{ item.smileShort || '—' }}<template v-if="item.smiles && item.smileShort && item.smiles !== item.smileShort">…</template>
        </span>
        <el-icon v-if="item.smiles && item.smileShort && item.smiles !== item.smileShort" class="cc-trunc-icon"><WarningFilled /></el-icon>
        </div>
        <el-button
        v-if="item.smiles || item.smileShort"
        text
        type="primary"
        size="small"
        class="cc-copy-btn"
        @click.stop="copySmiles(item.smiles || item.smileShort)"
        >
        <el-icon><CopyDocument /></el-icon> 复制
        </el-button>
        </div>

        <div class="cc-divider"></div>

        <!-- Footer: 详情按钮 -->
        <div class="cc-footer">
          <el-button text type="primary" size="small" @click.stop="handleCardClick(item)">
            查看化合物详情 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </el-card>
    </div>

    <div class="pagination-wrapper" v-if="totalCompounds > pageSize">
      <el-pagination
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="currentPage"
        :page-sizes="[12, 24, 36, 48]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="totalCompounds"
      >
      </el-pagination>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Search, ArrowRight, CopyDocument, WarningFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getCompounds } from '../api'

const router = useRouter()

const loading = ref(false)
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(12)

const compounds = ref([])
const totalCompounds = ref(0)

async function loadCompounds() {
  loading.value = true
  try {
    const raw = await getCompounds(currentPage.value, pageSize.value, searchQuery.value)
    const data = raw.data || raw
    compounds.value = (data.items || []).map(item => ({
      id: item.id,
      name: item.name,
      mw: item.mw,
      logp: item.logp,
      tpsa: item.tpsa,
      bloodEntryProbability: item.prob_cctcm ?? item.blood_entry_probability ?? 0,
      targetCount: item.target_count || 0,
      asthmaRelated: item.asthma_related || false,
      smileShort: item.smile_short || '',
      smiles: item.smiles || '',          // 完整 SMILES（用于复制）
      herbNames: item.herb_names || []     // 来源药材
    }))
    totalCompounds.value = data.total || 0
  } catch (e) { console.error('Compounds:', e) }
  finally { loading.value = false }
}

let searchTimer = null
watch(searchQuery, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { currentPage.value = 1; loadCompounds() }, 300)
})

onMounted(() => { loadCompounds() })

function getProbColor(prob) {
  if (!prob && prob !== 0) return '#999'
  if (prob >= 0.7) return '#67c23a'
  if (prob >= 0.5) return '#e6a23c'
  return '#f56c6c'
}

function getBarGradient(prob) {
  if (!prob && prob !== 0) return 'linear-gradient(90deg, #666, #999)'
  if (prob >= 0.7) return 'linear-gradient(90deg, #52c41a, #73d13d)'
  if (prob >= 0.5) return 'linear-gradient(90deg, #faad14, #ffc53d)'
  return 'linear-gradient(90deg, #f5222d, #ff7875)'
}

async function copySmiles(smiles) {
  const text = smiles || ''
  if (!text) {
    ElMessage.warning('无可复制内容')
    return
  }
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('SMILES 已复制到剪贴板')
  } catch { ElMessage.error('复制失败') }
}

function handleCardClick(item) {
  router.push({ path: '/compounds/detail', query: { id: item.id, name: item.name } })
}
function handleSizeChange(v) { pageSize.value = v; currentPage.value = 1; loadCompounds() }
function handleCurrentChange(v) { currentPage.value = v; loadCompounds() }
</script>

<style scoped>
.compounds-container { padding: 40px; background: transparent; min-height: 100vh }
.page-header { margin-bottom: 32px }
.page-title { font-size: 32px; font-weight: 700; color: var(--text-color); margin-bottom: 8px }
.page-desc { font-size: 16px; color: var(--text-secondary) }

.search-bar { display: flex; gap: 16px; margin-bottom: 32px; max-width: 600px }
.search-input { flex: 1; height: 44px }

/* Grid */
.compound-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 20px; min-height: 200px }

/* Card */
.compound-card { cursor: pointer; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); border-radius: 16px; overflow: hidden; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); backdrop-filter: blur(8px) }
.compound-card:hover { transform: translateY(-4px); box-shadow: 0 12px 40px rgba(0,0,0,0.3); border-color: rgba(255,255,255,0.18) }
.compound-card :deep(.el-card__body) { padding: 20px 22px }

/* Top: 名称行 */
.cc-top { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 16px }
.cc-name-line { display: flex; align-items: center; gap: 8px; min-width: 0; flex: 1 }
.cc-icon { font-size: 20px; flex-shrink: 0 }
.cc-name { font-size: 18px; font-weight: 700; color: var(--text-color); overflow: hidden; text-overflow: ellipsis; white-space: nowrap }

/* 概率条 */
.cc-prob-section { display: flex; align-items: center; gap: 12px; margin-bottom: 10px }
.cc-prob-label { font-size: 13px; color: var(--text-secondary, #999); white-space: nowrap; font-weight: 500 }
.cc-prob-bar-wrap { flex: 1; display: flex; align-items: center; gap: 12px }
.cc-prob-bar { flex: 1; height: 10px; background: rgba(255,255,255,0.08); border-radius: 5px; overflow: hidden }
.cc-prob-fill { height: 100%; border-radius: 5px; transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1) }
.cc-prob-num { font-size: 16px; font-weight: 700; white-space: nowrap; min-width: 56px; text-align: right }

.cc-divider { height: 1px; background: rgba(255,255,255,0.06); margin: 14px 0 }

/* Metrics */
.cc-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 16px }
.cc-metric { display: flex; flex-direction: column; gap: 3px; padding: 4px 0 }
.cc-metric-wide { grid-column: span 2 }
.cc-m-label { font-size: 12px; color: var(--text-muted,#999); font-weight: 500 }
.cc-m-value { font-size: 15px; font-weight: 600; color: var(--text-color,#fff) }
.cc-m-value-muted { font-size: 15px; font-weight: 500; color: var(--text-muted,#999) }
.cc-highlight { color: #67c23a !important }

/* 来源药材标签 */
.cc-herb-tags { display: flex; flex-wrap: wrap; gap: 4px; align-items: center }
.cc-herb-tag { font-size: 11px !important }
.cc-more-herbs { font-size: 11px; color: var(--text-muted,#999); margin-left: 2px }

/* SMILES 行 */
.cc-smiles-row { display: flex; align-items: center; justify-content: space-between; gap: 12px }
.cc-smiles-info { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0 }
.cc-smiles-label { font-size: 11px; color: var(--text-muted,#999); font-weight: 500; white-space: nowrap }
.cc-smiles-text { font-size: 12px; color: var(--text-secondary,#aaa); font-family: 'SF Mono', 'Fira Code', monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1 }
.cc-trunc-icon { font-size: 13px; color: #e6a23c; flex-shrink: 0 }
.cc-copy-btn { flex-shrink: 0; font-weight: 500 }

.cc-footer { display: flex; justify-content: flex-end; padding-top: 2px }

.pagination-wrapper { display: flex; justify-content: center; margin-top: 40px }
.pagination-wrapper :deep(.el-pagination) { background: var(--bg-card); padding: 16px 24px; border-radius: 12px; box-shadow: var(--shadow-card) }
</style>