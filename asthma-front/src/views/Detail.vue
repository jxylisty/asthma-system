<template>
  <div class="detail-container">
    <div class="top-bar">
      <div class="logo" @click="$router.push('/')">
        <el-icon><HomeFilled /></el-icon>
        <span>哮喘方剂智能分析系统</span>
      </div>
    </div>

    <div class="main-content">
      <el-tabs v-model="activeTab" class="detail-tabs">
        <el-tab-pane label="方剂详情" name="detail">
          <!-- ===== 顶部 Hero：方剂全景概览 ===== -->
          <div class="hero-card card">
            <div class="hero-top">
              <h1 class="hero-name">{{ prescriptionInfo?.name || '加载中...' }}</h1>
              <div class="hero-tags">
                <el-tag v-if="prescriptionInfo?.core_effect" type="success" effect="dark" size="large">
                  功效：{{ prescriptionInfo.core_effect }}
                </el-tag>
                <el-tag type="info" effect="plain" size="large">常用方剂</el-tag>
              </div>
              <el-button type="primary" size="default" class="hero-ai-btn" @click="openAiReport" :disabled="!isAiConfigured">
                <el-icon><MagicStick /></el-icon> AI 智能分析报告
              </el-button>
            </div>
            <!-- 药材组成卡片化（带剂量） -->
            <div class="herb-composition">
              <div class="herb-label">🌿 处方组成（{{ herbs.length }} 味）</div>
              <div class="herb-chips">
                <el-tooltip
                  v-for="herb in herbs"
                  :key="herb.name"
                  placement="top"
                  effect="dark"
                  :content="herb.description || herb.name"
                >
                  <div class="herb-chip" @click="$router.push({ path: '/herbs/detail', query: { id: herb.id, name: herb.name } })">
                    <span class="chip-name">{{ herb.name }}</span>
                    <span v-if="herb.dosage" class="chip-dose">{{ herb.dosage }}</span>
                  </div>
                </el-tooltip>
              </div>
            </div>
          </div>

          <!-- ===== 中部：左 (化合物排行) + 右 (雷达图) ===== -->
          <div class="dual-row">
            <!-- 左栏：核心入血化合物分析 -->
            <div class="module-left card">
              <div class="card-header">
                <h2>🧪 核心入血化合物分析（Blood-Inflow Compounds）</h2>
              </div>
              <div class="compound-list" v-loading="loadingCompounds">
                <div v-for="(compound, index) in displayedCompounds" :key="compound.name" class="compound-item">
                  <div class="compound-rank-header">
                    <span class="rank-badge" :class="index === 0 ? 'rank-1' : index === 1 ? 'rank-2' : index === 2 ? 'rank-3' : ''">
                      {{ index === 0 ? '🏆' : index === 1 ? '🥈' : index === 2 ? '🥉' : '' }}
                      TOP {{ (compoundCurrentPage - 1) * compoundPageSize + index + 1 }}
                    </span>
                    <span class="compound-name-text">{{ compound.name }}</span>
                  </div>
                  <!-- CCTCM 2.0（主力模型，高亮） -->
                  <div class="prob-row prob-ccTCM">
                    <span class="prob-model">CCTCM 2.0</span>
                    <el-progress
                      :percentage="Math.round((compound.prob_cctcm || 0) * 1000) / 10"
                      :stroke-width="12"
                      color="#409eff"
                      :show-text="false"
                      class="compound-progress"
                    />
                    <span class="prob-percent">{{ compound.prob_cctcm ? (compound.prob_cctcm * 100).toFixed(1) + '%' : '—' }}</span>
                    <el-tag v-if="compound.prob_cctcm" :type="compound.prob_cctcm >= 0.85 ? 'danger' : compound.prob_cctcm >= 0.5 ? 'warning' : 'info'" size="small" effect="dark">
                      {{ compound.prob_cctcm >= 0.85 ? '高' : compound.prob_cctcm >= 0.5 ? '中' : '低' }}
                    </el-tag>
                  </div>
                  <!-- HERB 2.0（辅助对比，弱化） -->
                  <div class="prob-row prob-herb">
                    <span class="prob-model">HERB 2.0</span>
                    <el-progress
                      v-if="compound.prob_herb != null"
                      :percentage="Math.round(compound.prob_herb * 1000) / 10"
                      :stroke-width="8"
                      color="#b0b0b0"
                      :show-text="false"
                      class="compound-progress"
                    />
                    <span v-else class="prob-model" style="flex:1">—</span>
                    <span class="prob-percent-herb">{{ compound.prob_herb != null ? (compound.prob_herb * 100).toFixed(1) + '%' : '—' }}</span>
                  </div>
                </div>
                <el-empty v-if="!loadingCompounds && compounds.length === 0" description="暂无入血化合物数据" />
                <div class="pagination-wrapper" v-if="compounds.length > compoundPageSize">
                  <el-pagination
                    v-model:current-page="compoundCurrentPage" :page-size="compoundPageSize"
                    :total="compounds.length" layout="prev, pager, next, jumper" small background
                  />
                </div>
              </div>
            </div>

            <!-- 右栏：作用机制雷达图 + 统计摘要 -->
            <div class="module-right card">
              <div class="card-header">
                <h2>🎯 作用机制与效能雷达图</h2>
                <el-tooltip placement="top" effect="dark" content="基于 KEGG 通路富集分析映射算法">
                  <el-icon class="info-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </div>
              <div ref="radarChart" class="radar-chart" v-loading="loadingRadar" element-loading-text="加载中..."></div>
              <!-- 统计摘要卡片 -->
              <div class="stats-cards" v-if="prescriptionInfo?.stats">
                <div class="stat-card">
                  <span class="stat-num">{{ prescriptionInfo.stats.blood_compound_count }}</span>
                  <span class="stat-label">入血化合物总数</span>
                </div>
                <div class="stat-card">
                  <span class="stat-num">{{ prescriptionInfo.stats.asthma_target_count }}</span>
                  <span class="stat-label">哮喘命中靶点</span>
                </div>
                <div class="stat-card">
                  <span class="stat-num">{{ prescriptionInfo.stats.pathway_count }}</span>
                  <span class="stat-label">核心调控通路</span>
                </div>
              </div>
              <el-button type="primary" plain size="default" class="network-btn" @click="activeTab = 'network'; nextTick(() => loadNetwork())">
                <el-icon><Share /></el-icon> 查看方剂—中药—化合物—靶点异构网络图谱
              </el-button>
            </div>
          </div>
        </el-tab-pane>

        <!-- Tab 2: 作用机制网络图 -->
        <el-tab-pane label="🕸️ 作用机制网络图" name="network">
          <div class="network-module card">
            <div class="card-header">
              <h2>方剂—中药—化合物—靶点 异构网络图谱</h2>
              <span class="network-stat">节点 {{ networkStats.nodes }} · 边 {{ networkStats.edges }}</span>
            </div>
            <div class="network-controls">
              <div class="control-item"><span class="control-label">入血概率阈值</span>
                <el-slider v-model="networkMinProb" :min="0" :max="1" :step="0.05"
                  :format-tooltip="val => (val * 100).toFixed(0) + '%'" style="width: 180px" @change="loadNetwork"
                /><span class="control-value">{{ (networkMinProb * 100).toFixed(0) }}%</span>
              </div>
              <div class="control-item"><span class="control-label">靶点过滤</span>
                <el-switch v-model="asthmaOnly" active-text="仅哮喘相关" inactive-text="全部靶点" @change="loadNetwork" />
              </div>
              <div class="control-item legend">
                <span class="legend-item"><span class="legend-dot prescription"></span>方剂</span>
                <span class="legend-item"><span class="legend-dot herb"></span>中药</span>
                <span class="legend-item"><span class="legend-dot compound"></span>化合物</span>
                <span class="legend-item"><span class="legend-dot target"></span>靶点</span>
                <span class="legend-item"><span class="legend-dot target-asthma"></span>哮喘靶点</span>
              </div>
            </div>
            <div class="network-canvas-wrapper" v-loading="loadingNetwork" element-loading-text="构建异构网络中...">
              <div ref="networkCanvas" class="network-canvas"></div>
              <el-empty v-if="!loadingNetwork && networkStats.nodes === 0"
                description="当前阈值下无网络数据，请调低入血概率阈值" class="network-empty" />
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- AI 报告对话框 -->
    <el-dialog v-model="aiReportVisible" title="AI 智能分析报告" width="70%" top="5vh" :close-on-click-modal="false">
      <div class="ai-dialog-actions" style="margin-bottom:12px;display:flex;gap:8px">
        <el-button v-if="aiReportContent && !generatingAiReport" type="primary" size="small" plain @click="exportAiPdf"><el-icon><Download /></el-icon> 导出 PDF</el-button>
        <el-button v-if="aiReportContent && !generatingAiReport" size="small" @click="copyAiReport"><el-icon><DocumentCopy /></el-icon> 复制</el-button>
        <el-button v-if="generatingAiReport" type="danger" size="small" plain @click="stopAiReport"><el-icon><VideoPause /></el-icon> 停止生成</el-button>
      </div>
      <div class="ai-report-body" v-loading="generatingAiReport && !aiReportContent" element-loading-text="AI 正在生成报告..." style="max-height:65vh;overflow-y:auto;font-size:14px;line-height:1.8">
        <div v-html="renderedAiReport"></div>
        <span v-if="generatingAiReport" style="color:#409eff;animation:blink 1s infinite">▊</span>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import * as echarts from 'echarts'
import cytoscape from 'cytoscape'
import { HomeFilled, QuestionFilled, Mic, VideoPause, MagicStick, Download, DocumentCopy, Share } from '@element-plus/icons-vue'
import { useSpeech } from '../composables/useSpeech'
import { useSettings } from '../composables/useSettings'
import { useAiSettings } from '../composables/useAiSettings'
import { getPrescriptionDetail, getPrescriptionRadar, getPrescriptionCompounds, getPrescriptionNetwork, streamAiReport } from '../api'
import { marked } from 'marked'
import { ElMessage } from 'element-plus'

const { speak, stop } = useSpeech()
const { speechVoice, speechRate, speechPitch, speechEnabled } = useSettings()
const { isConfigured: isAiConfigured, buildAiHeaders } = useAiSettings()

// ===== AI 报告 =====
const aiReportVisible = ref(false)
const aiReportContent = ref('')
const generatingAiReport = ref(false)
let aiAbortController = null
const renderedAiReport = computed(() => {
  if (!aiReportContent.value) return ''
  try { return marked.parse(aiReportContent.value, { breaks: true }) } catch { return aiReportContent.value }
})

async function openAiReport() {
  if (!isAiConfigured.value) { ElMessage.warning('请先在系统设置中配置 AI API Key'); return }
  const id = prescriptionId.value
  if (!id) { ElMessage.warning('请先选择方剂'); return }
  aiReportVisible.value = true; aiReportContent.value = ''; generatingAiReport.value = true
  aiAbortController = new AbortController()
  await streamAiReport({
    url: '/api/v1/prescriptions/existing-ai-report',
    body: { prescription_id: id, min_prob: 0.5, top_compounds: 15 },
    aiHeaders: buildAiHeaders(),
    signal: aiAbortController.signal,
    onDelta: (delta) => { aiReportContent.value += delta },
    onError: (err) => { ElMessage.error(err.message || 'AI 生成失败') },
    onDone: () => { generatingAiReport.value = false },
  })
}
function stopAiReport() { if (aiAbortController) { aiAbortController.abort(); generatingAiReport.value = false } }
async function exportAiPdf() {
  if (!aiReportContent.value) return
  try {
    const html2pdf = (await import('html2pdf.js')).default
    const container = document.createElement('div')
    container.style.padding = '24px'
    container.innerHTML = `<h1 style="text-align:center;font-size:22px;margin-bottom:8px">${prescriptionInfo.value?.name || ''} - AI 智能分析报告</h1><p style="text-align:center;color:#666;font-size:13px;margin-bottom:24px">${new Date().toLocaleString('zh-CN')}</p><div style="font-size:14px;line-height:1.8">${renderedAiReport.value}</div>`
    document.body.appendChild(container)
    await html2pdf().set({ margin: [10, 10], filename: `${prescriptionInfo.value?.name || '方剂'}_AI报告.pdf`, image: { type: 'jpeg', quality: 0.95 }, html2canvas: { scale: 2, useCORS: true }, jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' } }).from(container).save()
    document.body.removeChild(container); ElMessage.success('PDF 导出成功')
  } catch (e) { ElMessage.error('导出失败：' + e.message) }
}
async function copyAiReport() { try { await navigator.clipboard.writeText(aiReportContent.value); ElMessage.success('已复制') } catch { ElMessage.error('复制失败') } }

// ===== 状态 =====
const router = useRouter()
const route = useRoute()
const radarChart = ref(null)
const networkCanvas = ref(null)
let chartInstance = null
let cyInstance = null
const activeTab = ref('detail')
const prescriptionInfo = ref(null)
const herbs = ref([])
const compounds = ref([])
const radarData = ref([])
const networkMinProb = ref(0.5)
const asthmaOnly = ref(false)
const loadingNetwork = ref(false)
const loadingCompounds = ref(false)
const loadingRadar = ref(false)
const networkStats = ref({ nodes: 0, edges: 0 })
const compoundPageSize = 5
const compoundCurrentPage = ref(1)
const sortedCompounds = computed(() => [...compounds.value].sort((a, b) => (b.prob_cctcm || 0) - (a.prob_cctcm || 0)))
const displayedCompounds = computed(() => {
  const start = (compoundCurrentPage.value - 1) * compoundPageSize
  return sortedCompounds.value.slice(start, start + compoundPageSize)
})

const prescriptionId = computed(() => {
  const id = route.query.id
  return id ? Number(id) : null
})

// ===== 加载 =====
async function loadDetail() {
  let id = prescriptionId.value
  if (!id && route.query.keyword) {
    try {
      const { search } = await import('../api')
      const results = await search(route.query.keyword)
      if (results?.prescriptions?.length > 0) id = results.prescriptions[0].id
    } catch (e) { console.error('搜索方剂失败:', e) }
  }
  if (!id) return

  try {
    const detailRaw = await getPrescriptionDetail(id)
    if (!detailRaw) return
    const detail = detailRaw.data || detailRaw
    prescriptionInfo.value = detail
    herbs.value = (detail.herbs || []).map(h => ({
      id: h.id, name: h.name, description: h.functions || '', dosage: h.dosage || ''
    }))
  } catch (e) { console.error('方剂详情加载失败:', e); return }

  loadingCompounds.value = true
  getPrescriptionCompounds(id, 0.5).then(raw => {
    const res = raw.data || raw
    if (res) {
      compounds.value = (res.items || []).map(c => ({
        name: `${c.name} (来源: ${c.herb_name || '未知'})`,
        prob_cctcm: c.prob_cctcm, prob_herb: c.prob_herb
      }))
      compoundCurrentPage.value = 1
    }
  }).finally(() => { loadingCompounds.value = false })

  loadingRadar.value = true
  getPrescriptionRadar(id).then(raw => {
    const radarRaw = raw.data || raw
    if (radarRaw?.length > 0) {
      radarData.value = radarRaw.map(r => ({ name: r.efficacy_type, value: r.count }))
      nextTick(() => initRadarChart())
    }
  }).finally(() => { loadingRadar.value = false })
}

// ===== 网络图 =====
async function loadNetwork() {
  const id = prescriptionId.value
  if (!id) return
  loadingNetwork.value = true
  try {
    const netRaw = await getPrescriptionNetwork(id, networkMinProb.value, asthmaOnly.value)
    const net = netRaw.data || netRaw
    if (net?.nodes?.length > 0) { networkStats.value = { nodes: net.nodes.length, edges: net.edges.length }; await nextTick(); renderNetwork(net.nodes, net.edges) }
    else { networkStats.value = { nodes: 0, edges: 0 }; if (cyInstance) { cyInstance.destroy(); cyInstance = null } }
  } catch (e) { console.error('网络图加载失败:', e) }
  finally { loadingNetwork.value = false }
}

function renderNetwork(nodes, edges) {
  if (!networkCanvas.value) return
  if (cyInstance) { cyInstance.destroy(); cyInstance = null }
  const elements = [...nodes.map(n => ({ data: { ...n } })), ...edges.map((e, i) => ({ data: { id: `e_${i}`, source: e.source, target: e.target, category: e.category } }))]
  const concentricMap = { 'prescription': 4, 'herb': 3, 'compound': 2, 'target': 1 }
  cyInstance = cytoscape({
    container: networkCanvas.value, elements, wheelSensitivity: 0.2,
    style: [
      { selector: 'node', style: { 'label': 'data(label)', 'text-valign': 'center', 'text-halign': 'center', 'font-size': '10px', 'color': '#fff', 'text-wrap': 'wrap', 'text-max-width': '60px', 'width': 40, 'height': 40, 'background-color': '#999', 'border-width': 2, 'border-color': '#fff' } },
      { selector: 'node[category="prescription"]', style: { 'background-color': '#e74c3c', 'width': 65, 'height': 65, 'font-size': '12px', 'font-weight': 'bold', 'border-color': '#c0392b', 'border-width': 3 } },
      { selector: 'node[category="herb"]', style: { 'background-color': '#27ae60', 'width': 50, 'height': 50, 'font-size': '11px', 'border-color': '#1e8449' } },
      { selector: 'node[category="compound"]', style: { 'background-color': '#3498db', 'width': 40, 'height': 40, 'font-size': '9px', 'border-color': '#2471a3' } },
      { selector: 'node[category="target"]', style: { 'background-color': '#f39c12', 'width': 32, 'height': 32, 'font-size': '8px' } },
      { selector: 'node[?asthma_related]', style: { 'background-color': '#e74c3c', 'border-color': '#922b21', 'border-width': 3 } },
      { selector: 'edge', style: { 'width': 1.5, 'line-color': '#bbb', 'target-arrow-color': '#bbb', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier', 'opacity': 0.6 } },
      { selector: 'edge[category="p2h"]', style: { 'line-color': '#e74c3c', 'target-arrow-color': '#e74c3c' } },
      { selector: 'edge[category="h2c"]', style: { 'line-color': '#27ae60', 'target-arrow-color': '#27ae60' } },
      { selector: 'edge[category="c2t"]', style: { 'line-color': '#3498db', 'target-arrow-color': '#3498db' } },
      { selector: ':selected', style: { 'border-width': 4, 'border-color': '#ff6b6b', 'line-color': '#ff6b6b', 'target-arrow-color': '#ff6b6b', 'opacity': 1 } }
    ],
    layout: { name: 'concentric', concentric: (node) => concentricMap[node.data('category')] || 1, levelWidth: () => 1, minNodeSpacing: 20, animate: true, animationDuration: 500, spacingFactor: 1.2, startAngle: -Math.PI / 2 }
  })
  cyInstance.on('mouseover', 'node', function(evt) { const n = evt.target; n.style('opacity', 1); cyInstance.elements().difference(n.neighborhood()).style('opacity', 0.3) })
  cyInstance.on('mouseout', 'node', function() { cyInstance.elements().style('opacity', 1) })
}

watch(activeTab, (val) => { if (val === 'network' && !cyInstance && networkStats.value.nodes === 0) nextTick(() => loadNetwork()) })

// ===== 雷达图 =====
function initRadarChart() {
  if (!radarChart.value || radarData.value.length === 0) return
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(radarChart.value)
  const option = {
    color: ['#409eff'], tooltip: { trigger: 'item' },
    radar: {
      indicator: radarData.value.map(item => ({ name: item.name, max: 100 })),
      shape: 'polygon', splitNumber: 4, radius: '60%', center: ['50%', '50%'],
      axisName: { color: '#666', fontSize: 12 },
      splitLine: { lineStyle: { color: 'rgba(64,158,255,0.2)' } },
      splitArea: { areaStyle: { color: ['rgba(64,158,255,0.05)', 'rgba(64,158,255,0.1)'] } },
      axisLine: { lineStyle: { color: 'rgba(64,158,255,0.3)' } }
    },
    series: [{ type: 'radar', data: [{ value: radarData.value.map(i => i.value), name: '干预效能', symbol: 'circle', symbolSize: 6, lineStyle: { width: 2, color: '#409eff' }, areaStyle: { color: 'rgba(64,158,255,0.35)' }, itemStyle: { color: '#409eff' } }] }]
  }
  chartInstance.setOption(option)
  window.addEventListener('resize', () => chartInstance?.resize())
}

onMounted(() => { loadDetail() })
</script>



<style scoped>
.detail-container { min-height: 100vh; background: var(--bg-gradient) }
.top-bar { display: flex; align-items: center; padding: 12px 40px; background: rgba(30,41,59,0.8); box-shadow: 0 2px 12px rgba(0,0,0,0.3); position: sticky; top: 0; z-index: 100; border-bottom: 1px solid rgba(148,163,184,0.1) }
.logo { display: flex; align-items: center; gap: 10px; font-size: 18px; font-weight: 600; color: var(--text-color); cursor: pointer }
.logo:hover { color: #409eff }
.logo .el-icon { font-size: 24px }
.main-content { padding: 16px 40px; max-width: 1600px; margin: 0 auto }
.detail-tabs :deep(.el-tabs__header) { margin-bottom: 16px }
.detail-tabs :deep(.el-tabs__item) { font-size: 15px; font-weight: 600; color: var(--text-secondary) }
.detail-tabs :deep(.el-tabs__item.is-active) { color: var(--text-color) }

.card { background: rgba(30,41,59,0.6); border-radius: 14px; padding: 20px; border: 1px solid rgba(148,163,184,0.1); margin-bottom: 16px }
.card-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 14px }
.card-header h2 { font-size: 16px; color: var(--text-color); margin: 0 }
.info-icon { color: var(--text-muted); cursor: pointer; font-size: 18px }

/* Hero */
.hero-card { padding: 24px 28px }
.hero-top { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; margin-bottom: 18px }
.hero-name { font-size: 28px; color: var(--text-color); margin: 0; font-weight: 800 }
.hero-tags { display: flex; gap: 8px }
.hero-ai-btn { margin-left: auto }
.herb-composition { background: rgba(255,255,255,0.03); border-radius: 10px; padding: 14px 18px; border: 1px solid rgba(148,163,184,0.08) }
.herb-label { font-size: 13px; color: var(--text-secondary); margin-bottom: 10px; font-weight: 600 }
.herb-chips { display: flex; flex-wrap: wrap; gap: 8px }
.herb-chip { display: flex; align-items: center; gap: 6px; padding: 6px 14px; background: rgba(100,150,255,0.1); border-radius: 20px; cursor: pointer; transition: all 0.2s; border: 1px solid rgba(100,150,255,0.15) }
.herb-chip:hover { background: rgba(100,150,255,0.2); transform: translateY(-1px) }
.chip-name { font-size: 13px; color: var(--text-color); font-weight: 600 }
.chip-dose { font-size: 12px; color: #67c23a; font-weight: 700; background: rgba(103,194,58,0.15); padding: 1px 8px; border-radius: 10px }

/* dual row */
.dual-row { display: grid; grid-template-columns: 1.2fr 1fr; gap: 16px }
.module-left { }
.module-right { }

/* compound list */
.compound-list { display: flex; flex-direction: column; gap: 10px }
.compound-item { padding: 14px; background: rgba(255,255,255,0.03); border-radius: 10px; border: 1px solid rgba(255,255,255,0.05); transition: background 0.2s }
.compound-item:hover { background: rgba(255,255,255,0.06) }
.compound-rank-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px }
.rank-badge { padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 700; color: #fff; background: linear-gradient(135deg, #409eff, #67c23a) }
.rank-badge.rank-1 { background: linear-gradient(135deg, #e6a23c, #f56c6c) }
.rank-badge.rank-2 { background: linear-gradient(135deg, #909399, #606266) }
.rank-badge.rank-3 { background: linear-gradient(135deg, #b88230, #8b6914) }
.compound-name-text { font-size: 14px; font-weight: 600; color: var(--text-color) }
.prob-row { display: flex; align-items: center; gap: 8px; margin-bottom: 5px }
.prob-row:last-child { margin-bottom: 0 }
.prob-model { font-size: 11px; font-weight: 600; color: var(--text-muted); white-space: nowrap; width: 72px }
.prob-ccTCM .prob-model { color: #409eff }
.prob-herb .prob-model { color: var(--text-muted); font-size: 10px }
.compound-progress { flex: 1; margin-bottom: 0 }
.prob-ccTCM .compound-progress :deep(.el-progress-bar__outer) { background-color: rgba(64,158,255,0.1) }
.prob-herb .compound-progress :deep(.el-progress-bar__outer) { background-color: rgba(255,255,255,0.05) }
.prob-percent { font-size: 13px; font-weight: 700; color: #409eff; white-space: nowrap; min-width: 54px; text-align: right }
.prob-percent-herb { font-size: 11px; color: var(--text-muted); white-space: nowrap; min-width: 50px; text-align: right }
.pagination-wrapper { display: flex; justify-content: center; padding: 8px 0 }

/* radar */
.radar-chart { width: 100%; height: 240px }
.stats-cards { display: flex; gap: 12px; margin-top: 14px }
.stat-card { flex: 1; text-align: center; padding: 12px 8px; background: rgba(255,255,255,0.04); border-radius: 10px; border: 1px solid rgba(255,255,255,0.06) }
.stat-num { font-size: 26px; font-weight: 800; color: #409eff; display: block }
.stat-label { font-size: 11px; color: var(--text-muted); margin-top: 4px }
.network-btn { width: 100%; margin-top: 14px }

/* network */
.network-module { padding: 20px }
.network-stat { font-size: 13px; color: var(--text-muted); background: rgba(255,255,255,0.05); padding: 4px 12px; border-radius: 12px }
.network-controls { display: flex; align-items: center; gap: 32px; padding: 12px 16px; background: rgba(255,255,255,0.03); border-radius: 10px; margin-bottom: 14px; flex-wrap: wrap }
.control-item { display: flex; align-items: center; gap: 10px }
.control-label { font-size: 13px; font-weight: 600; color: var(--text-secondary); white-space: nowrap }
.control-value { font-size: 13px; font-weight: 700; color: #409eff; min-width: 36px }
.control-item.legend { margin-left: auto; gap: 14px }
.legend-item { display: flex; align-items: center; gap: 5px; font-size: 12px; color: var(--text-muted) }
.legend-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block }
.legend-dot.prescription { background: #e74c3c }
.legend-dot.herb { background: #27ae60 }
.legend-dot.compound { background: #3498db }
.legend-dot.target { background: #f39c12 }
.legend-dot.target-asthma { background: #e74c3c; border: 2px solid #922b21 }
.network-canvas-wrapper { position: relative; width: 100%; height: 600px; background: rgba(0,0,0,0.15); border-radius: 10px; border: 1px solid rgba(148,163,184,0.08) }
.network-canvas { width: 100%; height: 100% }
.network-empty { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%) }

@keyframes blink { 0%,50% { opacity:1 } 51%,100% { opacity:0 } }
.ai-report-body :deep(h1) { font-size:20px; font-weight:700; margin:14px 0 10px; border-bottom:2px solid #409eff; padding-bottom:6px }
.ai-report-body :deep(h2) { font-size:17px; font-weight:600; margin:12px 0 8px; border-left:4px solid #409eff; padding-left:10px }
.ai-report-body :deep(h3) { font-size:15px; font-weight:600; margin:10px 0 6px; color:#409eff }
.ai-report-body :deep(p) { margin:6px 0 }
.ai-report-body :deep(table) { width:100%; border-collapse:collapse; margin:10px 0; font-size:13px }
.ai-report-body :deep(th),.ai-report-body :deep(td) { border:1px solid #ebeef5; padding:6px 8px; text-align:left }
.ai-report-body :deep(th) { background:#f5f7fa; font-weight:600 }
.ai-report-body :deep(strong) { color:#f56c6c }
.ai-report-body :deep(ul),.ai-report-body :deep(ol) { padding-left:24px; margin:6px 0 }
.ai-report-body :deep(blockquote) { border-left:4px solid #e6a23c; background:#fdf6ec; padding:6px 10px; margin:8px 0; color:#606266 }
@media (max-width:1200px) { .main-content { padding:16px } .dual-row { grid-template-columns:1fr } .network-canvas-wrapper { height:450px } .network-controls { gap:16px } .control-item.legend { margin-left:0 } }
</style>