<template>
  <div class="home-container">
    <canvas ref="particleCanvas" class="particle-bg"></canvas>

    <div class="main-content">
      <!-- 标题区 -->
      <div class="header-section">
        <h1 class="system-title">哮喘方剂智能分析系统</h1>
        <p class="system-subtitle">基于入血预测的中医治疗儿童哮喘作用机制分析平台</p>
      </div>

      <!-- 统计指标区：4 卡片 -->
      <div class="data-ticker">
        <div class="ticker-card" v-for="(item, index) in tickerData" :key="index">
          <div class="ticker-icon">{{ item.icon }}</div>
          <div class="ticker-label">{{ item.label }}</div>
          <div class="ticker-value">
            <span class="ticker-number">{{ item.displayValue }}</span>
            <span class="ticker-unit">{{ item.unit }}</span>
          </div>
        </div>
      </div>

      <!-- 搜索区 -->
      <div class="search-center">
        <div class="search-bar-outer">
          <!-- 分类选择 + 分隔线 + 搜索框：使用原生 select，彻底无白底 -->
          <select v-model="searchCategory" class="cat-sel-native">
            <option value="prescription">方剂</option>
            <option value="herb">中药材</option>
            <option value="compound">化合物</option>
          </select>
          <span class="cat-divider" />
          <div class="search-input-wrap">
            <el-icon class="search-ic"><Search /></el-icon>
            <input
              v-model="searchQuery"
              class="search-input-native"
              placeholder="请输入方剂名称、中药或化合物..."
              @keyup.enter="handleSearch"
              @focus="handleInputFocus"
            />
            <el-icon class="voice-ic" @click="handleVoice"><Microphone /></el-icon>
          </div>
        </div>

        <!-- 热门标签 -->
        <div class="hot-tags">
          <span class="tag-label">热门检索：</span>
          <el-popover
            v-for="tag in hotTags" :key="tag.name"
            placement="top" :width="220" trigger="hover" :show-after="300"
          >
            <template #reference>
              <el-tag class="hot-tag" @click="selectTag(tag.name)" effect="plain">{{ tag.name }}</el-tag>
            </template>
            <div class="tag-preview">
              <div class="tp-name">{{ tag.name }}</div>
              <div class="tp-stats">
                <span>🌿 {{ tag.herbCount }} 味</span>
                <span>🧪 {{ tag.bloodCount }} 入血</span>
                <span>🎯 {{ tag.targetCount }} 靶点</span>
              </div>
            </div>
          </el-popover>
        </div>

        <!-- 联想下拉 -->
        <div class="suggestions" v-if="showSuggestions && filteredSuggestions.length > 0">
          <div v-for="item in filteredSuggestions" :key="item.name + item.type" class="suggestion-item" @click="selectSuggestion(item)">
             <span class="sug-name">{{ item.name }}</span>
             <span class="sug-type">{{ item.type === 'rx' ? '方剂' : item.type === 'herb' ? '中药' : '化合物' }}</span>
           </div>
        </div>
      </div>

      <!-- 快捷分析入口 -->
      <div class="quick-actions">
        <div class="qa-title">⚡ 快捷分析入口</div>
        <div class="qa-grid">
          <div class="qa-card group" @click="$router.push('/prediction')">
            <div class="qa-icon-box">🩸</div>
            <div class="qa-info">
              <div class="qa-name">化合物入血预测</div>
              <div class="qa-desc">输入 SMILES 或上传分子文件</div>
            </div>
            <div class="qa-arrow">→</div>
          </div>
          <div class="qa-card group" @click="$router.push('/custom-prescription')">
            <div class="qa-icon-box">📝</div>
            <div class="qa-info">
              <div class="qa-name">自定义方剂分析</div>
              <div class="qa-desc">自由组合中药，一键智能分析</div>
            </div>
            <div class="qa-arrow">→</div>
          </div>
          <div class="qa-card group" @click="$router.push('/prescriptions')">
            <div class="qa-icon-box">🕸️</div>
            <div class="qa-info">
              <div class="qa-name">异构网络图谱</div>
              <div class="qa-desc">可视化方剂作用机制</div>
            </div>
            <div class="qa-arrow">→</div>
          </div>
        </div>
      </div>

      <!-- 热门方剂 -->
      <div class="explore-cards">
        <div class="explore-title">📊 热门方剂</div>
        <div class="explore-grid">
          <div v-for="card in exploreCards" :key="card.name" class="explore-card" @click="handlePrescriptionClick(card)">
            <div class="ec-emoji">{{ card.emoji }}</div>
            <div class="ec-name">{{ card.name }}</div>
            <div class="ec-stats">
              <span>🌿 {{ card.herbCount }}味</span>
              <span>🧪 {{ card.bloodCount }}入血</span>
              <span>🎯 {{ card.targetCount }}靶点</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <el-dialog v-model="loadingVisible" class="loading-dialog" :show-close="false" :close-on-click-modal="false" :close-on-press-escape="false" width="400px" center>
      <div class="loading-content">
        <div class="loading-spinner"></div>
        <div class="loading-text">{{ loadingText }}</div>
        <div class="loading-progress">
          <div class="progress-bar" :style="{ width: progressWidth + '%' }"></div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Microphone } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getStatistics, search, getPrescriptions } from '../api'

const router = useRouter()
const searchCategory = ref('prescription')
const searchQuery = ref('')
const showSuggestions = ref(false)
const hotTags = ref([])
const emojiList = ['🍵', '🌿', '💊']
const exploreCards = ref([])

const suggestions = ref([])

// 联想下拉：调用后端搜索 API（支持拼音首字母 + 药材名反查）
let suggestTimer = null
function fetchSuggestions(q) {
  if (!q.trim()) { suggestions.value = []; return }
  clearTimeout(suggestTimer)
  suggestTimer = setTimeout(async () => {
    try {
      const res = await search(q)
      const all = []
      for (const p of (res.prescriptions || [])) all.push({ name: p.name, type: 'rx', id: p.id })
      for (const h of (res.herbs || [])) all.push({ name: h.name, type: 'herb', id: h.id })
      for (const c of (res.compounds || [])) all.push({ name: c.name, type: 'compound', id: c.id })
      suggestions.value = all.slice(0, 8)
    } catch { suggestions.value = [] }
  }, 250)
}
watch(searchQuery, fetchSuggestions)

const filteredSuggestions = computed(() => suggestions.value)

function selectSuggestion(item) {
  searchQuery.value = item.name
  showSuggestions.value = false
  // 根据类型直接路由
  if (item.type === 'rx') router.push({ path: '/detail', query: { id: item.id } })
  else if (item.type === 'herb') router.push({ path: '/herbs/detail', query: { id: item.id, name: item.name } })
  else if (item.type === 'compound') router.push({ path: `/compounds/detail/${item.id}` })
}

const tickerData = ref([
  { icon: '🍵', label: '经典方剂', value: 46, displayValue: 0, unit: '首' },
  { icon: '🌿', label: '涵盖中药', value: 278, displayValue: 0, unit: '味' },
  { icon: '🧪', label: '入血预测化合物', value: 569, displayValue: 0, unit: '维特征' },
  { icon: '🎯', label: '哮喘相关靶点', value: 7398, displayValue: 0, unit: '个' }
])

const loadingVisible = ref(false)
const loadingText = ref('')
const progressWidth = ref(0)

// 粒子
const particleCanvas = ref(null)
let animationId, particles, ctx

function initParticles() {
  const canvas = particleCanvas.value
  if (!canvas) return
  ctx = canvas.getContext('2d')
  canvas.width = canvas.parentElement.clientWidth
  canvas.height = canvas.parentElement.clientHeight
  particles = []
  for (let i = 0; i < 80; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.8,
      vy: (Math.random() - 0.5) * 0.8,
      radius: Math.random() * 2 + 1
    })
  }
}

function drawParticles() {
  if (!ctx || !particleCanvas.value) return
  const canvas = particleCanvas.value
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  particles.forEach(p => { p.x += p.vx; p.y += p.vy; if (p.x < 0 || p.x > canvas.width) p.vx *= -1; if (p.y < 0 || p.y > canvas.height) p.vy *= -1 })
  ctx.strokeStyle = 'rgba(64,158,255,0.15)'; ctx.lineWidth = 1
  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const dx = particles[i].x - particles[j].x, dy = particles[i].y - particles[j].y
      if (Math.sqrt(dx * dx + dy * dy) < 120) { ctx.beginPath(); ctx.moveTo(particles[i].x, particles[i].y); ctx.lineTo(particles[j].x, particles[j].y); ctx.stroke() }
    }
  }
  particles.forEach(p => { ctx.beginPath(); ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2); ctx.fillStyle = 'rgba(64,158,255,0.6)'; ctx.fill() })
  animationId = requestAnimationFrame(drawParticles)
}

function animateNumber(item) {
  const duration = 2000, steps = 60, stepValue = item.value / steps
  let step = 0
  const timer = setInterval(() => {
    step++
    item.displayValue = Math.min(Math.round(stepValue * step), item.value)
    if (step >= steps) { clearInterval(timer); item.displayValue = item.value }
  }, duration / steps)
}

function selectTag(tagName) { searchQuery.value = tagName; handleSearch() }
function handlePrescriptionClick(card) { if (card.id) router.push({ path: '/detail', query: { id: card.id } }) }
function handleVoice() { ElMessage.info('语音识别功能暂未启用') }
function handleInputFocus() { showSuggestions.value = true }

async function handleSearch() {
  const q = searchQuery.value.trim()
  if (!q) return
  loadingVisible.value = true; progressWidth.value = 0
  let searchResult = null
  const searchPromise = search(q).then(res => { searchResult = res }).catch(e => { console.error(e) })
  const steps = [{ text: '正在智能检索中...', progress: 40 }, { text: '分析完成，即将跳转 ✨', progress: 100 }]
  for (const step of steps) { loadingText.value = step.text; progressWidth.value = step.progress; await new Promise(r => setTimeout(r, 400)) }
  await searchPromise
  loadingVisible.value = false

  const prescriptions = searchResult?.prescriptions || []
  const herbs = searchResult?.herbs || []
  const compounds = searchResult?.compounds || []

  if (searchCategory.value === 'prescription' && prescriptions.length > 0) {
    router.push({ path: '/detail', query: { id: prescriptions[0].id } })
  } else if (searchCategory.value === 'herb' && herbs.length > 0) {
    router.push({ path: '/herbs/detail', query: { id: herbs[0].id, name: herbs[0].name } })
  } else if (searchCategory.value === 'compound' && compounds.length > 0) {
    router.push({ path: `/compounds/detail/${compounds[0].id}` })
  } else if (prescriptions.length > 0) {
    router.push({ path: '/detail', query: { id: prescriptions[0].id } })
  } else if (herbs.length > 0) {
    router.push({ path: '/herbs/detail', query: { id: herbs[0].id, name: herbs[0].name } })
  } else if (compounds.length > 0) {
    router.push({ path: `/compounds/detail/${compounds[0].id}` })
  } else {
    ElMessage.warning('未找到匹配结果')
  }
}

onMounted(async () => {
  initParticles(); drawParticles()
  try {
    const stats = await getStatistics()
    if (stats) {
      if (stats.prescription_count != null) tickerData.value[0].value = stats.prescription_count
      if (stats.herb_count != null) tickerData.value[1].value = stats.herb_count
      if (stats.compound_count != null) tickerData.value[2].value = stats.compound_count
      if (stats.target_count != null) tickerData.value[3].value = stats.target_count
    }
  } catch (e) { console.error('Stats:', e) }

  try {
    const rxData = await getPrescriptions(1, 50)
    const allRx = rxData?.items || []
    if (allRx.length > 0) {
      const sorted = [...allRx].sort((a, b) => (b.blood_compound_count || 0) - (a.blood_compound_count || 0))
      const top3 = sorted.slice(0, 3)
      hotTags.value = top3.map(r => ({ name: r.name, herbCount: r.herb_count || 0, bloodCount: r.blood_compound_count || 0, targetCount: r.asthma_target_count || 0, id: r.id }))
      exploreCards.value = top3.map((r, i) => ({ name: r.name, id: r.id, herbCount: r.herb_count || 0, bloodCount: r.blood_compound_count || 0, targetCount: r.asthma_target_count || 0, emoji: emojiList[i] }))
    }
  } catch (e) { console.error('Rx:', e) }

  tickerData.value.forEach((item, i) => setTimeout(() => animateNumber(item), i * 200))
  window.addEventListener('resize', initParticles)
})

onUnmounted(() => {
  if (animationId) cancelAnimationFrame(animationId)
  window.removeEventListener('resize', initParticles)
})
</script>

<style scoped>
.home-container { position: relative; width: 100%; height: 100vh; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); overflow: hidden }
.particle-bg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 0 }
.main-content { position: relative; z-index: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-start; height: 100vh; padding: 20px 20px 16px; overflow-y: auto }

/* 标题 */
.header-section { text-align: center; margin-bottom: 16px; flex-shrink: 0 }
.system-title { font-size: 28px; font-weight: 700; color: #fff; margin-bottom: 4px; text-shadow: 0 2px 16px rgba(64,158,255,0.25) }
.system-subtitle { font-size: 13px; color: rgba(255,255,255,0.6); font-weight: 300 }

/* 统计 */
.data-ticker { display: flex; gap: 12px; margin-bottom: 24px; flex-shrink: 0 }
.ticker-card { background: rgba(255,255,255,0.06); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 12px 22px; text-align: center; transition: all 0.25s; min-width: 130px }
.ticker-card:hover { background: rgba(255,255,255,0.09); transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.15) }
.ticker-icon { font-size: 18px; margin-bottom: 4px }
.ticker-label { font-size: 11px; color: rgba(255,255,255,0.5); margin-bottom: 4px }
.ticker-value { display: flex; align-items: baseline; justify-content: center; gap: 2px }
.ticker-number { font-size: 26px; font-weight: 700; color: #409eff; font-family: 'DIN Alternate','Helvetica Neue',sans-serif; line-height: 1 }
.ticker-unit { font-size: 12px; color: rgba(255,255,255,0.45); white-space: nowrap }

/* 搜索栏：暗色融合外壳 */
.search-center { width: 100%; max-width: 640px; flex-shrink: 0 }
.search-bar-outer {
  display: flex; align-items: center;
  background: rgba(255,255,255,0.08);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 28px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.25);
  height: 48px;
  overflow: hidden;
}

/* 分类选择：原生 select，彻底无白底 */
.cat-sel-native {
  width: 90px; flex-shrink: 0;
  background: transparent; border: none; outline: none;
  color: #93c5fd; font-size: 12px; font-weight: 600;
  cursor: pointer; padding: 0 4px 0 14px;
  border-right: 1px solid #334155;
  text-align: center;
  appearance: none; -webkit-appearance: none;
  color-scheme: dark;
  /* 自定义下拉箭头 */
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M3 4.5L6 7.5L9 4.5' fill='none' stroke='%2394a3b8' stroke-width='1.2' stroke-linecap='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 6px center;
  padding-right: 20px;
}

/* 下拉面板 - 全部替换为原生 select 不再需要 */

/* 分隔线 */
.cat-divider { width: 1px; height: 20px; background: rgba(255,255,255,0.15); flex-shrink: 0 }

/* 搜索输入区 */
.search-input-wrap { flex: 1; display: flex; align-items: center; padding: 0 18px; height: 48px }
.search-ic { font-size: 18px; color: #60a5fa; flex-shrink: 0; margin-right: 10px }
.voice-ic { font-size: 18px; color: #60a5fa; flex-shrink: 0; margin-left: 10px; cursor: pointer; transition: color 0.2s }
.voice-ic:hover { color: #34d399 }
.search-input-native {
  flex: 1; background: transparent; border: none; outline: none;
  font-size: 15px; color: #e2e8f0; caret-color: #60a5fa;
  font-family: inherit;
}
.search-input-native::placeholder { color: rgba(148,163,184,0.5) }

/* 热门标签 */
.hot-tags { display: flex; align-items: center; gap: 8px; margin-top: 10px; flex-wrap: wrap; justify-content: center }
.tag-label { color: rgba(255,255,255,0.45); font-size: 12px }
.hot-tag { cursor: pointer; transition: all 0.25s; background: rgba(56,189,248,0.1) !important; border: 1px solid rgba(56,189,248,0.3) !important; color: rgba(255,255,255,0.85) !important; box-shadow: 0 0 8px rgba(56,189,248,0.1) }
.hot-tag:hover { background: rgba(56,189,248,0.22) !important; border-color: #38bdf8 !important; color: #fff !important; box-shadow: 0 0 18px rgba(56,189,248,0.35); transform: translateY(-2px) }
.tag-preview { font-size: 13px; line-height: 1.8 }
.tp-name { font-weight: 600; font-size: 15px; color: #303133; margin-bottom: 6px }
.tp-stats { display: flex; gap: 12px; color: #606266 }
.tp-stats span { white-space: nowrap }

/* 联想 */
.suggestions { position: absolute; top: 100%; left: 0; right: 0; background: #1e293b; border-radius: 12px; margin-top: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); z-index: 100; overflow: hidden; border: 1px solid rgba(255,255,255,0.08) }
.suggestion-item { padding: 11px 20px; cursor: pointer; transition: background 0.15s; color: #94a3b8; font-size: 14px; display: flex; justify-content: space-between; align-items: center }
.suggestion-item:hover { background: rgba(56,189,248,0.1); color: #38bdf8 }
.sug-type { font-size: 10px; color: #64748b; background: rgba(255,255,255,0.06); padding: 1px 6px; border-radius: 4px; flex-shrink: 0 }

/* 快捷入口 - 横向工业风 */
.quick-actions { width: 100%; max-width: 720px; margin-top: 20px; flex-shrink: 0 }
.qa-title {
  font-size: 11px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 1.5px;
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 10px; margin-top: 4px;
}
.qa-grid { display: flex; gap: 12px }
.qa-card {
  flex: 1; display: flex; align-items: center; gap: 12px;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px; padding: 12px 14px; cursor: pointer;
  transition: all 0.25s;
}
.qa-card:hover { background: rgba(255,255,255,0.08); border-color: rgba(64,158,255,0.3); box-shadow: 0 4px 16px rgba(0,0,0,0.25) }
.qa-icon-box {
  width: 40px; height: 40px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px; font-size: 20px;
}
.qa-info { flex: 1; min-width: 0 }
.qa-name { font-weight: 600; color: #e2e8f0; font-size: 13px; margin-bottom: 3px }
.qa-desc { font-size: 11px; color: #64748b }
.qa-arrow { font-size: 14px; color: #475569; transition: all 0.2s; flex-shrink: 0 }
.qa-card:hover .qa-arrow { color: #409eff; transform: translateX(3px) }

/* 热门方剂 */
.explore-cards { width: 100%; max-width: 720px; margin-top: 20px; flex-shrink: 0; padding-bottom: 16px }
.explore-title {
  font-size: 11px; font-weight: 700; color: #94a3b8;
  text-transform: uppercase; letter-spacing: 1.5px;
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 10px; margin-top: 4px;
}
.explore-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px }
.explore-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 12px; text-align: center; cursor: pointer; transition: all 0.25s }
.explore-card:hover { background: rgba(56,189,248,0.1); border-color: rgba(56,189,248,0.3); transform: translateY(-3px); box-shadow: 0 6px 20px rgba(0,0,0,0.25) }
.ec-emoji { font-size: 24px; margin-bottom: 6px }
.ec-name { font-weight: 600; color: #e2e8f0; font-size: 14px; margin-bottom: 2px }
.ec-stats { display: flex; flex-direction: column; gap: 1px; font-size: 10px; color: rgba(148,163,184,0.5) }

/* Loading */
:deep(.loading-dialog) { background: transparent !important }
:deep(.el-dialog) { background: rgba(17,24,39,0.96) !important; border-radius: 20px !important; border: 1px solid rgba(56,189,248,0.25) !important }
:deep(.el-dialog__header), :deep(.el-dialog__body) { padding: 28px 36px !important }
.loading-content { text-align: center }
.loading-spinner { width: 52px; height: 52px; margin: 0 auto 20px; border: 3px solid rgba(56,189,248,0.15); border-top-color: #38bdf8; border-radius: 50%; animation: spin 1s linear infinite }
@keyframes spin { to { transform: rotate(360deg) } }
.loading-text { color: #e2e8f0; font-size: 14px; margin-bottom: 16px; min-height: 20px }
.loading-progress { width: 100%; height: 3px; background: rgba(255,255,255,0.08); border-radius: 2px; overflow: hidden }
.progress-bar { height: 100%; background: linear-gradient(90deg, #38bdf8, #34d399); transition: width 0.3s }
</style>
