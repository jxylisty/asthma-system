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

    <div v-loading="loading" class="rx-grid">
      <div
        v-for="item in filteredPrescriptions"
        :key="item.id"
        class="rx-card"
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
  padding: 24px 32px;
  min-height: 100vh;
  background: var(--bg-gradient);
}
.page-header { margin-bottom: 20px }
.page-title { font-size: 24px; font-weight: 700; color: var(--text-color); margin: 0 0 4px 0 }
.page-desc { font-size: 13px; color: var(--text-secondary); margin: 0 }
.search-bar { margin-bottom: 20px; max-width: 480px }
.search-input :deep(.el-input__inner) { background: rgba(255,255,255,0.06); border-color: rgba(255,255,255,0.1) }

.rx-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 16px;
}
.rx-card {
  background: rgba(30, 41, 59, 0.85);
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
}
.rx-card:hover {
  border-color: rgba(64, 158, 255, 0.3);
  background: rgba(30, 41, 59, 0.95);
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.rx-head {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 14px;
}
.rx-name {
  font-size: 18px; font-weight: 700; color: var(--text-color);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  margin: 0; flex: 1; min-width: 0;
}
.rx-speech { color: var(--text-muted); padding: 4px; flex-shrink: 0 }
.rx-speech.speaking { color: #67c23a }

.rx-herbs { margin-bottom: 14px }
.rx-label { font-size: 13px; color: var(--text-secondary); display: block; margin-bottom: 8px }
.rx-dosage-list { display: flex; flex-wrap: wrap; gap: 6px }
.dosage-chip {
  display: inline-block;
  padding: 3px 10px;
  background: rgba(99, 179, 237, 0.1);
  border: 1px solid rgba(99, 179, 237, 0.2);
  border-radius: 6px;
  font-size: 13px; color: #93c5fd;
  white-space: nowrap;
}
.dosage-more {
  display: inline-block;
  padding: 3px 8px;
  font-size: 12px; color: var(--text-muted);
  line-height: 1.6;
}

.rx-stats {
  display: flex; gap: 16px;
  margin-bottom: 14px;
}
.rx-stat {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 12px;
  background: rgba(148, 163, 184, 0.05);
  border-radius: 8px;
  flex: 1;
}
.rx-stat-icon { font-size: 14px; flex-shrink: 0 }
.rx-stat-label { font-size: 12px; color: var(--text-secondary); white-space: nowrap }
.rx-stat-val { font-size: 13px; font-weight: 600; color: var(--text-color); margin-left: auto }
.rx-footer {
  display: flex; justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid rgba(255,255,255,0.06);
}
.pagination-wrapper { margin-top: 24px; display: flex; justify-content: center }
.rx-no-dosage { font-size: 13px; color: var(--text-muted) }
</style>
