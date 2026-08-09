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
          <el-table-column label="预测入血概率" width="180" align="center">
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
    const text = `${herb.value.name}含有的化合物，共${list.length}个。${list.map((c, i) => `第${i + 1}个，${c.name}，分子量${c.mw}，预测入血概率${Math.round(c.bloodEntryProbability * 100)}%`).join('。')}。`
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
          bloodEntryProbability: c.blood_entry_probability || 0,
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
        bloodEntryProbability: c.blood_entry_probability || 0,
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
  padding: 40px;
  background: var(--bg-gradient);
  min-height: 100vh;
}

.back-bar {
  margin-bottom: 24px;
}

.info-card {
  border-radius: 16px;
  margin-bottom: 24px;
}

.herb-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.herb-title-area {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.herb-name {
  font-size: 32px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0;
}

.herb-pinyin {
  font-size: 16px;
  color: #999;
  font-style: italic;
}

.asthma-tag {
  margin-left: 4px;
}

.speech-btn {
  color: #909399;
  transition: all 0.3s ease;
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
  color: #999;
  font-weight: 500;
}

.info-item .value {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
}

.compounds-card {
  border-radius: 16px;
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
  font-size: 20px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0;
}

.compound-search {
  margin-bottom: 16px;
  max-width: 400px;
}

.compound-search-input {
  height: 40px;
}

.compound-name {
  font-weight: 500;
  color: #1a1a2e;
}
</style>
