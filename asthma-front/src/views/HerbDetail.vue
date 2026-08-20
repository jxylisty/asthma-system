<template>
  <div class="herb-detail-container" v-loading="loading">
    <template v-if="herb">
      <!-- 返回按钮 -->
      <div class="back-bar">
        <el-button @click="goBack" text>
          <el-icon><ArrowLeft /></el-icon>
          返回中药列表
        </el-button>
      </div>

      <!-- 中药基本信息 -->
      <el-card class="info-card">
        <div class="herb-header">
          <div class="herb-title-area">
            <h1 class="herb-name">{{ herb.name }}</h1>
            <span class="herb-pinyin" v-if="herb.pinyin">{{ herb.pinyin }}</span>
            <el-tag v-if="herb.asthmaRelated" type="danger" size="small" class="asthma-tag">哮喘相关</el-tag>
            <el-button class="speech-btn" :class="{ speaking: isSpeakingInfo }" size="small" @click="toggleSpeakInfo">
              <el-icon><VideoPause v-if="isSpeakingInfo" /><Mic v-else /></el-icon>
              {{ isSpeakingInfo ? '停止' : '播报' }}
            </el-button>
          </div>
          <div class="herb-image" v-if="herb.image">
            <img :src="herb.image" :alt="herb.name" @error="onImgError" />
          </div>
        </div>

        <div class="herb-info-grid">
          <div class="info-item">
            <span class="label">别名</span>
            <span class="value">{{ herb.alias || '—' }}</span>
          </div>
          <div class="info-item">
            <span class="label">拉丁名</span>
            <span class="value">{{ herb.latinName || '—' }}</span>
          </div>
          <div class="info-item">
            <span class="label">药材分类</span>
            <span class="value">{{ herb.category || '—' }}</span>
          </div>
          <div class="info-item">
            <span class="label">性</span>
            <span class="value">{{ herb.nature || '—' }}</span>
          </div>
          <div class="info-item">
            <span class="label">味</span>
            <span class="value">{{ herb.flavor || '—' }}</span>
          </div>
          <div class="info-item">
            <span class="label">归经</span>
            <span class="value">{{ herb.meridians || '—' }}</span>
          </div>
          <div class="info-item">
            <span class="label">药用部位</span>
            <span class="value">{{ herb.medicinalPart || '—' }}</span>
          </div>
          <div class="info-item">
            <span class="label">植物科属</span>
            <span class="value">{{ herb.family || '—' }}</span>
          </div>
          <div class="info-item">
            <span class="label">用法用量</span>
            <span class="value">{{ herb.dosage || '—' }}</span>
          </div>
          <div class="info-item">
            <span class="label">毒性</span>
            <span class="value">{{ herb.toxicity || '—' }}</span>
          </div>
          <div class="info-item full-width">
            <span class="label">主要功能</span>
            <span class="value">{{ herb.functions || '—' }}</span>
          </div>
          <div class="info-item full-width" v-if="herb.asthmaFunctions">
            <span class="label">相关哮喘功能</span>
            <span class="value">{{ herb.asthmaFunctions }}</span>
          </div>
          <div class="info-item full-width" v-if="herb.contraindication && herb.contraindication !== 'NA'">
            <span class="label">禁忌</span>
            <span class="value">{{ herb.contraindication }}</span>
          </div>
          <div class="info-item full-width" v-if="herb.source && herb.source !== 'NA'">
            <span class="label">药材来源</span>
            <span class="value">{{ herb.source }}</span>
          </div>
          <div class="info-item full-width" v-if="herb.characteristics && herb.characteristics !== 'NA'">
            <span class="label">药材性状</span>
            <span class="value">{{ herb.characteristics }}</span>
          </div>
        </div>
      </el-card>

      <!-- 含有的化合物列表 -->
      <el-card class="compounds-card">
        <template #header>
          <div class="section-header">
            <h2 class="section-title">含有的化合物</h2>
            <div class="section-actions">
              <el-tag type="primary" size="small">共 {{ herb.compounds.length }} 个化合物</el-tag>
              <el-button class="speech-btn" :class="{ speaking: isSpeakingCompounds }" size="small" @click="toggleSpeakCompounds">
                <el-icon><VideoPause v-if="isSpeakingCompounds" /><Mic v-else /></el-icon>
                {{ isSpeakingCompounds ? '停止' : '播报' }}
              </el-button>
            </div>
          </div>
        </template>

        <div class="compound-search">
          <el-input
            v-model="compoundSearch"
            placeholder="搜索化合物名称..."
            clearable
            class="compound-search-input"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>

        <el-table
          :data="filteredCompoundDetails"
          stripe
          style="width: 100%"
          v-loading="loadingCompounds"
        >
          <el-table-column prop="name" label="化合物名称" min-width="180">
            <template #default="{ row }">
              <span class="compound-name">{{ row.name }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="mw" label="分子量 (MW)" width="130" align="center">
            <template #default="{ row }">
              {{ row.mw || '—' }}
            </template>
          </el-table-column>
          <el-table-column label="ccTCM 入血概率" width="180" align="center">
            <template #default="{ row }">
              <el-progress
                :percentage="Math.round((row.bloodEntryProbability || 0) * 100)"
                :color="getProbabilityColor(row.bloodEntryProbability)"
                :stroke-width="12"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" align="center" fixed="right">
            <template #default="{ row }">
              <el-button
                type="primary"
                size="small"
                @click="viewCompound(row)"
              >
                <el-icon><DataLine /></el-icon>
                查看化合物图谱
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>

    <el-empty v-else-if="!loading" description="未找到该中药信息" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Search, DataLine, Mic, VideoPause } from '@element-plus/icons-vue'
import { useSpeech } from '../composables/useSpeech'
import { useSettings } from '../composables/useSettings'
import { getHerbDetail, getHerbCompounds } from '../api'

const route = useRoute()
const router = useRouter()
const { speak, stop } = useSpeech()
const { speechVoice, speechRate, speechPitch, speechEnabled } = useSettings()

const loading = ref(false)
const loadingCompounds = ref(false)
const herb = ref(null)
const compoundSearch = ref('')

const isSpeakingInfo = ref(false)
const isSpeakingCompounds = ref(false)

function stopOtherSpeaking() {
  stop()
  isSpeakingInfo.value = false
  isSpeakingCompounds.value = false
}

function toggleSpeakInfo() {
  if (!speechEnabled.value) return

  if (isSpeakingInfo.value) {
    stop()
    isSpeakingInfo.value = false
  } else {
    stopOtherSpeaking()
    const h = herb.value
    const text = `${h.name}。${h.alias ? '别名：' + h.alias + '。' : ''}分类：${h.category || '未知'}。性：${h.nature || '未知'}。味：${h.flavor || '未知'}。归经：${h.meridians || '未知'}。药用部位：${h.medicinalPart || '未知'}。科属：${h.family || '未知'}。用法用量：${h.dosage || '未知'}。毒性：${h.toxicity || '未知'}。主要功能：${h.functions || '未知'}。${h.asthmaFunctions ? '相关哮喘功能：' + h.asthmaFunctions + '。' : ''}${h.contraindication && h.contraindication !== 'NA' ? '禁忌：' + h.contraindication + '。' : ''}`
    speak(text, { voice: speechVoice.value, rate: speechRate.value, pitch: speechPitch.value })
    isSpeakingInfo.value = true
  }
}

function toggleSpeakCompounds() {
  if (!speechEnabled.value) return

  if (isSpeakingCompounds.value) {
    stop()
    isSpeakingCompounds.value = false
  } else {
    stopOtherSpeaking()
    const list = filteredCompoundDetails.value
    const text = `${herb.value.name}含有的化合物，共${list.length}个。${list.map((c, i) => `第${i + 1}个，${c.name}，分子量${c.mw}，ccTCM入血概率${Math.round(c.bloodEntryProbability * 100)}%`).join('。')}。`
    speak(text, { voice: speechVoice.value, rate: speechRate.value, pitch: speechPitch.value })
    isSpeakingCompounds.value = true
  }
}

async function loadHerb() {
  loading.value = true
  try {
    const herbId = route.query.id
    const herbName = route.query.name

    if (herbId) {
      // 并行加载详情和化合物列表
      const [detailRes, compoundsRes] = await Promise.allSettled([
        getHerbDetail(herbId),
        getHerbCompounds(herbId)
      ])

      if (detailRes.status === 'fulfilled' && detailRes.value) {
        const detail = detailRes.value
        herb.value = {
          name: detail.name || herbName,
          alias: detail.alias || '',
          pinyin: detail.pinyin || '',
          latinName: detail.latin_name || '',
          category: detail.category || '',
          nature: detail.nature || '',
          flavor: detail.flavor || '',
          meridians: detail.meridians || '',
          medicinalPart: detail.medicinal_part || '',
          family: detail.family || '',
          dosage: detail.dosage || '',
          toxicity: detail.toxicity || '',
          functions: detail.functions || '',
          asthmaRelated: detail.asthma_related || false,
          asthmaFunctions: detail.asthma_functions || '',
          contraindication: detail.contraindication || '',
          source: detail.source || '',
          characteristics: detail.characteristics || '',
          image: detail.image || '',
          compounds: []
        }
      }

      // 化合物列表（可能失败）
      if (compoundsRes.status === 'fulfilled' && compoundsRes.value) {
        const compounds = compoundsRes.value
        compoundDetails.value = (compounds || []).map(c => ({
          name: c.name,
          mw: c.mw,
          logp: c.logp,
          bloodEntryProbability: c.prob_cctcm ?? c.blood_entry_probability ?? 0,
          id: c.id,
          herbName: c.herb_name || ''
        }))
        if (herb.value) {
          herb.value.compounds = compoundDetails.value.map(c => c.name)
        }
      }
      loadingCompounds.value = false
    } else {
      // Fallback to local JSON
      const axios = (await import('axios')).default
      const res = await axios.get('/data/herbs.json')
      const found = res.data.find(h => h.id === herbId || h.name === herbName)
      if (found) {
        herb.value = found
        await loadCompoundDetails(null, found.compounds || [])
      }
    }
  } catch (e) {
    console.error('Failed to load herb:', e)
  } finally {
    loading.value = false
  }
}

const compoundDetails = ref([])

async function loadCompoundDetails(herbId, compoundNames) {
  loadingCompounds.value = true
  try {
    if (herbId) {
      // Load via API
      const compounds = await getHerbCompounds(herbId)
      compoundDetails.value = (compounds || []).map(c => ({
        name: c.name,
        mw: null,
        bloodEntryProbability: c.prob_cctcm ?? c.blood_entry_probability ?? 0,
        id: c.id,
        herbName: c.herb_name || ''
      }))
      // Update herb.compounds list for the count display
      if (herb.value) {
        herb.value.compounds = compoundDetails.value.map(c => c.name)
      }
    } else if (compoundNames && compoundNames.length > 0) {
      // Fallback to local JSON
      const axios = (await import('axios')).default
      const res = await axios.get('/data/compound-summaries.json')
      const summaryMap = new Map(res.data.map(c => [c.name, c]))
      compoundDetails.value = compoundNames
        .map(name => summaryMap.get(name))
        .filter(c => c !== undefined)
    } else {
      compoundDetails.value = []
    }
  } catch (e) {
    console.error('Failed to load compound details:', e)
    compoundDetails.value = []
  } finally {
    loadingCompounds.value = false
  }
}

const filteredCompoundDetails = computed(() => {
  if (!compoundSearch.value) return compoundDetails.value
  const query = compoundSearch.value.toLowerCase()
  return compoundDetails.value.filter(c =>
    c.name.toLowerCase().includes(query)
  )
})

function getProbabilityColor(prob) {
  if (prob >= 0.7) return '#67c23a'
  if (prob >= 0.5) return '#e6a23c'
  return '#f56c6c'
}

function viewCompound(compound) {
  router.push({
    path: '/compounds/detail',
    query: { name: compound.name, id: compound.id }
  })
}

function goBack() {
  router.push('/herbs')
}

function onImgError(e) {
  e.target.style.display = 'none'
}

onMounted(() => {
  loadHerb()
})
</script>

<style scoped>
.herb-detail-container {
  padding: 16px 40px;
  max-width: 1600px;
  margin: 0 auto;
  background: var(--bg-gradient);
  min-height: 100vh;
}

.back-bar {
  margin-bottom: 20px;
}
.back-bar :deep(.el-button--text) {
  color: var(--text-secondary);
  font-weight: 600;
}
.back-bar :deep(.el-button--text:hover) {
  color: #409eff;
}

/* ==== 统一卡片：与 Detail.vue 的 .card 对齐 ==== */
.info-card,
.compounds-card {
  background: rgba(30,41,59,0.6) !important;
  border-radius: 14px;
  padding: 20px;
  border: 1px solid rgba(148,163,184,0.1) !important;
  margin-bottom: 16px;
  color: var(--text-color);
}
.info-card :deep(.el-card__body),
.compounds-card :deep(.el-card__body) {
  padding: 0;
  color: var(--text-color);
}
.info-card :deep(.el-card__header),
.compounds-card :deep(.el-card__header) {
  border-bottom: 1px solid rgba(148,163,184,0.1) !important;
  background: transparent !important;
  padding: 0 0 14px 0;
  margin-bottom: 20px;
}

.herb-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  gap: 20px;
  flex-wrap: wrap;
}

.herb-title-area {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.herb-name {
  font-size: 28px;
  font-weight: 800;
  color: var(--text-color);
  margin: 0;
}

.herb-pinyin {
  font-size: 15px;
  color: var(--text-muted);
  font-style: italic;
}

.asthma-tag {
  margin-left: 4px;
}

.speech-btn {
  color: var(--text-muted);
  transition: all 0.3s ease;
}
.speech-btn :deep(.el-button__text) {
  color: inherit;
}

.speech-btn:hover {
  color: #409eff;
}

.speech-btn.speaking {
  color: #67c23a;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.herb-image {
  width: 120px;
  height: 120px;
  border-radius: 12px;
  overflow: hidden;
  flex-shrink: 0;
  border: 1px solid rgba(148,163,184,0.15);
  background: rgba(0,0,0,0.15);
}

.herb-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.herb-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  background: rgba(255,255,255,0.03);
  border-radius: 10px;
  padding: 16px 18px;
  border: 1px solid rgba(148,163,184,0.08);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-item .label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 600;
  letter-spacing: 0.3px;
}

.info-item .value {
  font-size: 14px;
  color: var(--text-color);
  line-height: 1.7;
}

.compounds-card {
  border-radius: 14px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-title {
  font-size: 16px;
  color: var(--text-color);
  margin: 0;
  font-weight: 600;
}

.compound-search {
  margin-bottom: 16px;
  max-width: 400px;
}

.compound-search-input {
  height: 40px;
}
.compound-search-input :deep(.el-input__wrapper) {
  background: rgba(255,255,255,0.05) !important;
  box-shadow: 0 0 0 1px rgba(148,163,184,0.15) inset !important;
  border-radius: 8px;
}
.compound-search-input :deep(.el-input__inner) {
  color: var(--text-color) !important;
}
.compound-search-input :deep(.el-input__inner::placeholder) {
  color: var(--text-muted);
}
.compound-search-input :deep(.el-input__prefix),
.compound-search-input :deep(.el-input__suffix) {
  color: var(--text-muted);
}

/* ==== el-table 深色适配 ==== */
.compounds-card :deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(255,255,255,0.04);
  --el-table-header-text-color: var(--text-secondary);
  --el-table-text-color: var(--text-color);
  --el-table-border-color: rgba(148,163,184,0.1);
  --el-table-row-hover-bg-color: rgba(64,158,255,0.08);
  color: var(--text-color);
  background: transparent;
}
.compounds-card :deep(.el-table::before) {
  background-color: rgba(148,163,184,0.1);
}
.compounds-card :deep(.el-table th.el-table__cell) {
  background: rgba(255,255,255,0.04) !important;
  color: var(--text-secondary) !important;
  border-bottom: 1px solid rgba(148,163,184,0.12);
  font-weight: 600;
}
.compounds-card :deep(.el-table td.el-table__cell) {
  border-bottom: 1px solid rgba(148,163,184,0.08);
  color: var(--text-color);
}
.compounds-card :deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) {
  background: rgba(255,255,255,0.02) !important;
}
.compounds-card :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: rgba(64,158,255,0.08) !important;
}
.compounds-card :deep(.el-table .cell) {
  color: inherit;
}

/* ==== el-pagination 深色适配（如果 compounds 表格有分页） ==== */
.compounds-card :deep(.el-pagination) {
  color: var(--text-secondary);
  --el-pagination-bg-color: transparent;
  --el-pagination-hover-color: #409eff;
}
.compounds-card :deep(.el-pagination button),
.compounds-card :deep(.el-pagination .el-pager li) {
  background: rgba(255,255,255,0.04) !important;
  color: var(--text-secondary) !important;
  border: 1px solid rgba(148,163,184,0.1) !important;
}
.compounds-card :deep(.el-pagination .el-pager li.is-active) {
  background: #409eff !important;
  color: #fff !important;
  border-color: #409eff !important;
}

/* ==== el-tag / el-button 在卡片里的文字修正 ==== */
.compounds-card :deep(.el-tag--primary) {
  color: #fff;
}

/* ==== el-empty 深色适配 ==== */
.herb-detail-container :deep(.el-empty__description) {
  color: var(--text-muted);
}

.compound-name {
  font-weight: 500;
  color: var(--text-color);
}

@media (max-width: 1200px) {
  .herb-detail-container { padding: 16px; }
  .herb-info-grid { grid-template-columns: 1fr; }
}
</style>
