<template>
  <div class="prescriptions-container">
    <div class="page-header">
      <h2 class="page-title">方剂列表</h2>
      <p class="page-desc">系统收录经典方剂 · 含药材剂量与入血预测</p>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索方剂名称..."
        class="search-input"
        clearable
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <div v-loading="loading" class="rx-grid stagger-grid">
      <div
        v-for="(item, index) in filteredPrescriptions"
        :key="item.id"
        class="rx-card stagger-item"
        :style="{ '--i': String(index) }"
        @click="handleViewDetail(item)"
      >
        <div class="rx-head">
          <h3 class="rx-name">{{ item.name }}</h3>
          <el-button
            class="rx-speech"
            :class="{ speaking: speakingCards.has(item.id) }"
            size="small"
            text
            @click.stop="toggleSpeech(item)"
          >
            <el-icon><VideoPause v-if="speakingCards.has(item.id)" /><Mic v-else /></el-icon>
          </el-button>
        </div>

        <div class="rx-herbs">
          <span class="rx-label">处方组成：</span>
          <div class="rx-dosage-list" v-if="item.herbNames && item.herbNames.length">
            <span v-for="(d, i) in dosageDisplay(item).slice(0, 6)" :key="i" class="dosage-chip">{{ d }}</span>
            <span v-if="dosageDisplay(item).length > 6" class="dosage-more">+{{ dosageDisplay(item).length - 6 }}</span>
          </div>
          <span v-else class="rx-no-dosage">{{ item.herbCount || 0 }} 味药材</span>
        </div>

        <div class="rx-stats">
          <div class="rx-stat">
            <span class="rx-stat-icon">🧪</span>
            <span class="rx-stat-label">高概率入血成分</span>
            <span class="rx-stat-val">{{ item.bloodCompoundCount || 0 }} 个</span>
          </div>
          <div class="rx-stat">
            <span class="rx-stat-icon">🎯</span>
            <span class="rx-stat-label">哮喘相关靶点</span>
            <span class="rx-stat-val">{{ item.asthmaTargetCount || 0 }} 个</span>
          </div>
        </div>

        <div class="rx-footer">
          <el-button type="primary" size="small" text @click.stop="handleViewDetail(item)">
            查看方剂详情 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>

      <el-empty v-if="!loading && filteredPrescriptions.length === 0" description="无匹配方剂" />
    </div>

    <div class="pagination-wrapper" v-if="totalPrescriptions > pageSize && !loading">
      <el-pagination
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="currentPage"
        :page-sizes="[6, 12, 18, 24]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="totalPrescriptions"
        background
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Mic, VideoPause, ArrowRight } from '@element-plus/icons-vue'
import { useSpeech } from '../composables/useSpeech'
import { useSettings } from '../composables/useSettings'
import { getPrescriptions } from '../api'

const { speak, stop, isSpeaking } = useSpeech()
const { speechVoice, speechRate, speechPitch, speechEnabled } = useSettings()
const speakingCards = ref(new Set())

function toggleSpeech(item) {
  if (!speechEnabled.value) return
  const id = item.id
  if (speakingCards.value.has(id)) { stop(); speakingCards.value.delete(id); return }
  speak(`${item.name}`, { voice: speechVoice.value, rate: speechRate.value, pitch: speechPitch.value })
  speakingCards.value.add(id)
}

const router = useRouter()
function handleViewDetail(item) { router.push(`/detail?id=${item.id}`) }

const searchQuery = ref('')
const loading = ref(false)
const prescriptions = ref([])
const currentPage = ref(1)
const pageSize = ref(12)
const totalPrescriptions = ref(0)

const filteredPrescriptions = computed(() => {
  if (!searchQuery.value.trim()) return prescriptions.value
  const q = searchQuery.value.trim().toLowerCase()
  return prescriptions.value.filter(p =>
    p.name.toLowerCase().includes(q) ||
    (p.herbNames || []).some(n => n.toLowerCase().includes(q))
  )
})

async function loadPrescriptions() {
  loading.value = true
  try {
    const raw = await getPrescriptions(currentPage.value, pageSize.value, searchQuery.value.trim())
    const data = raw.data || raw
    prescriptions.value = (data.items || []).map(item => ({
      id: item.id,
      name: item.name,
      coreEffect: item.core_effect || '',
      herbCount: item.herb_count || 0,
      herbNames: item.herb_names || [],
      herbDosages: item.herb_dosages || [],
      bloodCompoundCount: item.blood_compound_count || 0,
      asthmaTargetCount: item.asthma_target_count || 0
    }))
    totalPrescriptions.value = data.total || 0
  } catch (e) {
    console.error('Loading prescriptions failed:', e)
  } finally {
    loading.value = false
  }
}

function dosageDisplay(item) {
  const names = item.herbNames || []
  const dosages = item.herbDosages || []
  return names.map((name, i) => {
    const d = dosages[i]
    if (d && d !== 'None' && d !== 'nan') return `${name} ${d}`
    return name
  })
}

function handleSizeChange(val) { pageSize.value = val; currentPage.value = 1; loadPrescriptions() }
function handleCurrentChange(val) { currentPage.value = val; loadPrescriptions() }

onMounted(loadPrescriptions)
</script>

<style scoped>
.prescriptions-container {
  padding: 16px 40px;
  min-height: 100vh;
  background: transparent !important; background-image: none !important;
}
.page-header { margin-bottom: 20px }
.page-title { font-size: var(--fs-h1); font-weight: var(--fw-bold); color: var(--text-color); margin: 0 0 6px 0 }
.page-desc { font-size: var(--fs-body); color: var(--text-secondary); margin: 0 }
.search-bar { margin-bottom: 20px; max-width: 600px }
.search-input { height: 44px }
.search-input :deep(.el-input__wrapper) {
  background: rgba(30,41,59,0.6) !important;
  box-shadow: 0 0 0 1px rgba(148,163,184,0.15) inset !important;
  border-radius: 10px;
}
.search-input :deep(.el-input__inner) { color: var(--text-color) !important }
.search-input :deep(.el-input__inner::placeholder) { color: var(--text-muted) }
.search-input :deep(.el-input__prefix),
.search-input :deep(.el-input__suffix) { color: var(--text-muted) }

.rx-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 16px;
  min-height: 200px;
}
.rx-card {
  background: rgba(30,41,59,0.6) !important;
  border: 1px solid rgba(148,163,184,0.1) !important;
  border-radius: 14px;
  padding: 18px 20px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
}
.rx-card:hover {
  border-color: rgba(64,158,255,0.4) !important;
  background: rgba(30,41,59,0.8) !important;
  transform: translateY(-3px);
  box-shadow: 0 8px 30px rgba(0,0,0,0.35);
}
.rx-head {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 14px;
  gap: 8px;
}
.rx-name {
  font-size: var(--fs-h3); font-weight: var(--fw-bold); color: var(--text-color);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  margin: 0; flex: 1; min-width: 0;
}

/* 方剂播报按钮（App.vue 全局已兜底，这里加强选择器） */
.rx-speech :deep(.el-button__text) {
  color: var(--text-secondary) !important;
}
.rx-speech.speaking :deep(.el-button__text) {
  color: #67c23a !important;
}

.rx-herbs {
  margin-bottom: 14px;
  background: rgba(255,255,255,0.03);
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid rgba(148,163,184,0.06);
}
.rx-label { font-size: var(--fs-sub); color: var(--text-muted); display: block; margin-bottom: 8px; font-weight: var(--fw-medium) }
.rx-dosage-list { display: flex; flex-wrap: wrap; gap: 6px }
.dosage-chip {
  display: inline-block;
  padding: 3px 10px;
  background: rgba(99, 179, 237, 0.1);
  border: 1px solid rgba(99, 179, 237, 0.22);
  border-radius: 6px;
  font-size: var(--fs-body); color: #93c5fd;
  white-space: nowrap;
  font-weight: var(--fw-medium);
}
.dosage-more {
  display: inline-block;
  padding: 3px 8px;
  font-size: var(--fs-sub); color: var(--text-muted);
  line-height: 1.6;
}

.rx-stats {
  display: flex; gap: 12px;
  margin-bottom: 14px;
}
.rx-stat {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 12px;
  background: rgba(148,163,184,0.06);
  border: 1px solid rgba(148,163,184,0.08);
  border-radius: 8px;
  flex: 1;
}
.rx-stat-icon { font-size: var(--fs-h3); flex-shrink: 0 }
.rx-stat-label { font-size: var(--fs-sub); color: var(--text-muted); white-space: nowrap; font-weight: var(--fw-medium) }
.rx-stat-val { font-size: var(--fs-body); font-weight: var(--fw-bold); color: var(--text-color); margin-left: auto }
.rx-footer {
  display: flex; justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid rgba(148,163,184,0.1);
}
.rx-footer :deep(.el-button--text) {
  color: var(--text-secondary) !important;
  font-weight: var(--fw-medium);
}
.rx-footer :deep(.el-button--text:hover) {
  color: #409eff !important;
  background: rgba(64,158,255,0.08);
}
.pagination-wrapper { margin-top: 24px; display: flex; justify-content: center }
.pagination-wrapper :deep(.el-pagination) {
  color: var(--text-secondary);
  background: rgba(30,41,59,0.6);
  padding: 12px 20px;
  border-radius: 12px;
  border: 1px solid rgba(148,163,184,0.1);
}
.pagination-wrapper :deep(.el-pagination .el-pager li),
.pagination-wrapper :deep(.el-pagination button) {
  background: rgba(255,255,255,0.04) !important;
  color: var(--text-secondary) !important;
  border: 1px solid rgba(148,163,184,0.1) !important;
  border-radius: 6px;
}
.pagination-wrapper :deep(.el-pagination .el-pager li.is-active) {
  background: #409eff !important;
  color: #fff !important;
  border-color: #409eff !important;
}
.rx-no-dosage { font-size: var(--fs-body); color: var(--text-muted) }

@media (max-width: 1200px) {
  .prescriptions-container { padding: 16px }
  .rx-grid { grid-template-columns: 1fr }
}
</style>
