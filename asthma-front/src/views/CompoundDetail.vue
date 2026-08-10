<template>
  <div class="compound-detail-container" v-loading="loading">
    <template v-if="compound">
      <!-- 返回按钮 -->
      <div class="back-bar">
        <el-button @click="goBack" text size="small">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
      </div>

      <!-- 顶部：基本信息 + 3D结构 并排 -->
      <div class="top-row">
        <!-- 左：分子信息卡 -->
        <div class="info-card">
          <div class="compound-header">
            <div class="name-section">
              <h1 class="compound-name">{{ compound.name }}</h1>
              <span v-if="compound.molecularFormula" class="formula-text">{{ compound.molecularFormula }}</span>
            </div>
            <div class="badge-section">
              <el-tag v-if="compound.asthmaRelated" type="danger" size="small" effect="dark">哮喘相关</el-tag>
              <el-tag v-if="entryBadge" :type="entryBadge.type" size="small" effect="dark">{{ entryBadge.label }}</el-tag>
              <el-tag v-if="compound.numAromaticRings > 0" type="warning" size="small" effect="plain">芳香化合物</el-tag>
            </div>
          </div>

          <!-- 入血概率 -->
          <div class="prob-bar">
            <span class="prob-label">预测入血概率</span>
            <el-progress
              :percentage="Math.round((compound.bloodEntryProbability || 0) * 100)"
              :color="getProbabilityColor(compound.bloodEntryProbability)"
              :stroke-width="14"
              class="prob-progress"
            />
            <span class="prob-value">{{ ((compound.bloodEntryProbability || 0) * 100).toFixed(1) }}%</span>
          </div>

          <!-- 双列物理化学属性 -->
          <div class="props-grid">
            <div class="prop-item">
              <span class="prop-key">分子量 MW</span>
              <span class="prop-val">{{ compound.mw ? compound.mw.toFixed(2) : '—' }} <small>g/mol</small></span>
            </div>
            <div class="prop-item">
              <span class="prop-key">LogP</span>
              <span class="prop-val">{{ compound.logp != null ? compound.logp.toFixed(2) : '—' }}</span>
            </div>
            <div class="prop-item">
              <span class="prop-key">氢键供体 HBD</span>
              <span class="prop-val">{{ compound.hbd ?? '—' }}</span>
            </div>
            <div class="prop-item">
              <span class="prop-key">氢键受体 HBA</span>
              <span class="prop-val">{{ compound.hba ?? '—' }}</span>
            </div>
            <div class="prop-item">
              <span class="prop-key">极性表面积 TPSA</span>
              <span class="prop-val">{{ compound.tpsa != null ? compound.tpsa.toFixed(1) : '—' }} <small>Å²</small></span>
            </div>
            <div class="prop-item">
              <span class="prop-key">可旋转键</span>
              <span class="prop-val">{{ compound.rotatableBonds ?? '—' }}</span>
            </div>
            <div class="prop-item">
              <span class="prop-key">环数</span>
              <span class="prop-val">{{ compound.numRings ?? '—' }}<small v-if="compound.numAromaticRings != null"> ({{ compound.numAromaticRings }} 芳香)</small></span>
            </div>
            <div class="prop-item">
              <span class="prop-key">重原子数</span>
              <span class="prop-val">{{ compound.numHeavyAtoms ?? '—' }}</span>
            </div>
          </div>

          <!-- 类药性评估 (Lipinski五规则) -->
          <div class="lipinski-bar" v-if="lipinskiResult">
            <el-icon :class="lipinskiResult.passed ? 'lipinski-pass' : 'lipinski-fail'">
              <CircleCheck v-if="lipinskiResult.passed" /><CircleClose v-else />
            </el-icon>
            <span class="lipinski-text">Lipinski 五规则：<strong>{{ lipinskiResult.passed ? '符合' : '违反' }}</strong> ({{ lipinskiResult.detail }})</span>
          </div>

          <!-- SMILES 截断 + 复制/展开 -->
          <div class="smiles-section">
            <div class="smiles-header">
              <span class="smiles-label">SMILES</span>
              <div class="smiles-actions">
                <el-button text size="small" @click="toggleSmilesExpand">
                  <el-icon><ArrowDown v-if="!smilesExpanded" /><ArrowUp v-else /></el-icon>
                  {{ smilesExpanded ? '收起' : '展开' }}
                </el-button>
                <el-button text size="small" @click="copySmiles">
                  <el-icon><DocumentCopy /></el-icon>
                  复制
                </el-button>
              </div>
            </div>
            <code class="smiles-code" :class="{ expanded: smilesExpanded }">
              {{ smilesExpanded ? compound.smiles : truncatedSmiles }}
            </code>
          </div>
        </div>

        <!-- 右：3D 分子结构 -->
        <div class="structure-card">
          <div class="structure-header">
            <span class="structure-title">3D 分子结构</span>
            <div class="structure-controls">
              <el-tooltip content="球棍模型" placement="top">
                <el-button :type="currentStyle === 'stick' ? 'primary' : 'default'" size="small" @click="setStyle('stick')">球棍</el-button>
              </el-tooltip>
              <el-tooltip content="空间填充" placement="top">
                <el-button :type="currentStyle === 'sphere' ? 'primary' : 'default'" size="small" @click="setStyle('sphere')">填充</el-button>
              </el-tooltip>
              <el-tooltip content="线框模型" placement="top">
                <el-button :type="currentStyle === 'line' ? 'primary' : 'default'" size="small" @click="setStyle('line')">线框</el-button>
              </el-tooltip>
            </div>
          </div>
          <div ref="molViewer" class="mol-viewer" v-loading="loadingStructure" element-loading-text="生成3D结构中...">
            <el-empty v-if="!loadingStructure && !hasStructure" description="无可用 SMILES 数据" :image-size="60" />
          </div>
          <div class="structure-tip" v-if="hasStructure">
            <el-icon><InfoFilled /></el-icon>
            <span>鼠标拖拽旋转 · 滚轮缩放 · 右键平移</span>
          </div>
        </div>
      </div>

      <!-- 中部：雷达图 + 靶点统计 并排 -->
      <div class="mid-row">
        <!-- 雷达图 -->
        <div class="radar-card">
          <div class="card-header">
            <h2>效能雷达图</h2>
            <el-button class="speech-btn" :class="{ speaking: isSpeakingRadar }" size="small" @click="toggleSpeakRadar">
              <el-icon><VideoPause v-if="isSpeakingRadar" /><Mic v-else /></el-icon>
              {{ isSpeakingRadar ? '停止' : '播报' }}
            </el-button>
          </div>
          <div ref="radarChart" class="radar-chart"></div>
          <div class="radar-summary" v-if="compound.radarScores">
            <div class="radar-summary-item">
              <span class="summary-label">抗炎</span>
              <span class="summary-value">{{ compound.radarScores.antiInflammatory }}</span>
            </div>
            <div class="radar-summary-item">
              <span class="summary-label">免疫</span>
              <span class="summary-value">{{ compound.radarScores.immuneRegulation }}</span>
            </div>
            <div class="radar-summary-item">
              <span class="summary-label">气道修复</span>
              <span class="summary-value">{{ compound.radarScores.airwayRepair }}</span>
            </div>
          </div>
        </div>

        <!-- 靶点统计概要 -->
        <div class="targets-overview-card">
          <div class="card-header">
            <h2>靶点概览</h2>
            <el-tag type="primary" size="small">共 {{ compound.targets.length }} 个</el-tag>
          </div>
          <div class="targets-stats">
            <div class="stat-item asthma">
              <span class="stat-num">{{ asthmaTargetCount }}</span>
              <span class="stat-label">哮喘相关</span>
            </div>
            <div class="stat-item total">
              <span class="stat-num">{{ compound.targets.length }}</span>
              <span class="stat-label">总靶点</span>
            </div>
            <div class="stat-item">
              <span class="stat-num">{{ highCentralityCount }}</span>
              <span class="stat-label">核心靶点</span>
            </div>
          </div>
          <div class="source-herbs" v-if="compound.herbNames && compound.herbNames.length > 0">
            <span class="herb-label">来源药材：</span>
            <el-tag v-for="herb in compound.herbNames" :key="herb" size="small" effect="plain" class="herb-tag">{{ herb }}</el-tag>
          </div>
        </div>
      </div>

      <!-- 底部：靶点列表 -->
      <div class="targets-card">
        <div class="card-header">
          <h2>靶点列表</h2>
          <div class="header-right">
            <el-input v-model="targetSearch" placeholder="搜索靶点基因..." clearable class="target-search" size="small">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
          </div>
        </div>
        <el-table :data="paginatedTargets" stripe size="small" style="width: 100%" @sort-change="handleSortChange">
          <el-table-column prop="gene" label="靶点基因" min-width="120" sortable="custom">
            <template #default="{ row }"><span class="target-gene">{{ row.gene }}</span></template>
          </el-table-column>
          <el-table-column prop="targetType" label="靶点类型" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">{{ row.targetType || '—' }}</template>
          </el-table-column>
          <el-table-column prop="species" label="物种" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">{{ row.species || '—' }}</template>
          </el-table-column>
          <el-table-column prop="sourceDB" label="来源数据库" width="110" align="center" sortable="custom">
            <template #default="{ row }">
              <el-tag v-if="row.sourceDB && row.sourceDB !== '—'" size="small" :type="getDbTagType(row.sourceDB)">{{ row.sourceDB }}</el-tag>
              <span v-else>—</span>
            </template>
          </el-table-column>
          <el-table-column prop="networkCentrality" label="网络核心度" width="130" align="center" sortable="custom">
            <template #default="{ row }">
              <el-progress v-if="row.networkCentrality > 0" :percentage="Math.round(row.networkCentrality * 100)" :color="getCentralityColor(row.networkCentrality)" :stroke-width="10" />
              <span v-else>—</span>
            </template>
          </el-table-column>
          <el-table-column prop="asthmaRelated" label="哮喘相关" width="80" align="center" sortable="custom">
            <template #default="{ row }">
              <el-tag v-if="row.asthmaRelated" type="danger" size="small">是</el-tag>
              <el-tag v-else type="info" size="small">否</el-tag>
            </template>
          </el-table-column>
        </el-table>
        <div class="target-pagination" v-if="filteredTargets.length > targetPageSize">
          <el-pagination @size-change="handleTargetSizeChange" @current-change="handleTargetCurrentChange" :current-page="targetCurrentPage" :page-sizes="[10, 20, 50]" :page-size="targetPageSize" layout="total, sizes, prev, pager, next" :total="filteredTargets.length" size="small" />
        </div>
      </div>
    </template>
    <el-empty v-else-if="!loading" description="未找到该化合物信息" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Search, Mic, VideoPause, DocumentCopy, ArrowDown, ArrowUp, CircleCheck, CircleClose, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { useSpeech } from '../composables/useSpeech'
import { useSettings } from '../composables/useSettings'
import { getCompoundDetail, getCompoundTargets, getCompoundRadar, getCompoundStructure } from '../api'

const route = useRoute()
const router = useRouter()
const { speak, stop } = useSpeech()
const { speechVoice, speechRate, speechPitch, speechEnabled } = useSettings()

const loading = ref(false)
const loadingStructure = ref(false)
const compound = ref(null)
const radarChart = ref(null)
const molViewer = ref(null)
let chartInstance = null
let viewer3D = null

const isSpeakingRadar = ref(false)
const smilesExpanded = ref(false)
const currentStyle = ref('stick')
const hasStructure = ref(false)

// SMILES 截断
const truncatedSmiles = computed(() => {
  const s = compound.value?.smiles || ''
  return s.length > 40 ? s.substring(0, 40) + '...' : s
})

// 入血等级 Badge
const entryBadge = computed(() => {
  const prob = compound.value?.bloodEntryProbability || 0
  if (prob >= 0.7) return { type: 'success', label: '高概率入血' }
  if (prob >= 0.5) return { type: 'warning', label: '可能入血' }
  if (prob > 0) return { type: 'info', label: '低概率入血' }
  return null
})

// Lipinski 五规则评估
const lipinskiResult = computed(() => {
  if (!compound.value) return null
  const c = compound.value
  if (c.mw == null && c.logp == null && c.hbd == null && c.hba == null) return null
  const violations = []
  if (c.mw != null && c.mw > 500) violations.push('MW>500')
  if (c.logp != null && c.logp > 5) violations.push('LogP>5')
  if (c.hbd != null && c.hbd > 5) violations.push('HBD>5')
  if (c.hba != null && c.hba > 10) violations.push('HBA>10')
  return {
    passed: violations.length === 0,
    detail: violations.length === 0 ? '全部符合' : violations.join(', ')
  }
})

// 靶点统计
const asthmaTargetCount = computed(() => compound.value?.targets?.filter(t => t.asthmaRelated).length || 0)
const highCentralityCount = computed(() => compound.value?.targets?.filter(t => t.networkCentrality >= 0.5).length || 0)

// Target table state
const targetSearch = ref('')
const targetCurrentPage = ref(1)
const targetPageSize = ref(10)
const sortProp = ref('')
const sortOrder = ref('')

const filteredTargets = computed(() => {
  let result = compound.value?.targets || []
  if (targetSearch.value) {
    const q = targetSearch.value.toLowerCase()
    result = result.filter(t => (t.gene || '').toLowerCase().includes(q))
  }
  if (sortProp.value) {
    const prop = sortProp.value
    const order = sortOrder.value === 'ascending' ? 1 : -1
    result = [...result].sort((a, b) => {
      const va = a[prop], vb = b[prop]
      if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * order
      return String(va || '').localeCompare(String(vb || '')) * order
    })
  }
  return result
})

const paginatedTargets = computed(() => {
  const s = (targetCurrentPage.value - 1) * targetPageSize.value
  return filteredTargets.value.slice(s, s + targetPageSize.value)
})

function handleSortChange({ prop, order }) { sortProp.value = prop; sortOrder.value = order; targetCurrentPage.value = 1 }
function handleTargetSizeChange(v) { targetPageSize.value = v; targetCurrentPage.value = 1 }
function handleTargetCurrentChange(v) { targetCurrentPage.value = v }

function getProbabilityColor(p) {
  if (p >= 0.7) return '#67c23a'
  if (p >= 0.5) return '#e6a23c'
  return '#f56c6c'
}
function getCentralityColor(v) {
  if (v >= 0.7) return '#f56c6c'
  if (v >= 0.4) return '#e6a23c'
  return '#409eff'
}
function getDbTagType(db) {
  return { CTD: 'primary', DrugBank: 'success', KEGG: 'warning', BindingDB: 'danger', PubChem: 'info' }[db] || 'info'
}

function toggleSmilesExpand() { smilesExpanded.value = !smilesExpanded.value }

async function copySmiles() {
  try {
    await navigator.clipboard.writeText(compound.value.smiles)
    ElMessage.success('SMILES 已复制到剪贴板')
  } catch {
    ElMessage.warning('复制失败，请手动选择文本')
  }
}

function stopOtherSpeaking() { stop(); isSpeakingRadar.value = false }

function toggleSpeakRadar() {
  if (!speechEnabled.value) return
  if (isSpeakingRadar.value) { stop(); isSpeakingRadar.value = false }
  else {
    stopOtherSpeaking()
    const s = compound.value.radarScores
    speak(`效能雷达图。抗炎效能${s.antiInflammatory}分。免疫调节${s.immuneRegulation}分。气道修复${s.airwayRepair}分。`, { voice: speechVoice.value, rate: speechRate.value, pitch: speechPitch.value })
    isSpeakingRadar.value = true
  }
}

// ===== 3D 分子结构渲染 =====
function setStyle(style) {
  currentStyle.value = style
  if (viewer3D && hasStructure.value) {
    renderMolecule(style)
  }
}

function renderMolecule(style) {
  if (!viewer3D || !compound.value?.molblock) return

  viewer3D.removeAllModels()
  viewer3D.addModel(compound.value.molblock, 'sdf')

  if (style === 'stick') {
    viewer3D.setStyle({}, { stick: { radius: 0.15, colorscheme: 'Jmol' } })
  } else if (style === 'sphere') {
    viewer3D.setStyle({}, { sphere: { scale: 0.3, colorscheme: 'Jmol' }, stick: { radius: 0.1, colorscheme: 'Jmol' } })
  } else if (style === 'line') {
    viewer3D.setStyle({}, { line: { linewidth: 2, colorscheme: 'Jmol' } })
  }

  viewer3D.setBackgroundColor('#fafbfc')
  viewer3D.zoomTo()
  viewer3D.render()
}

async function load3DStructure(compoundId) {
  if (!window.$3Dmol) {
    console.warn('3Dmol.js 未加载')
    return
  }
  loadingStructure.value = true
  try {
    const raw = await getCompoundStructure(compoundId)
    const res = raw.data || raw
    if (res && res.molblock) {
      compound.value.molblock = res.molblock
      hasStructure.value = true
      await nextTick()
      if (molViewer.value) {
        viewer3D = window.$3Dmol.createViewer(molViewer.value, {
          backgroundColor: '#fafbfc',
          antialias: true
        })
        renderMolecule(currentStyle.value)
      }
    }
  } catch (e) {
    console.error('3D 结构加载失败:', e)
  } finally {
    loadingStructure.value = false
  }
}

// ===== 雷达图 =====
function initRadarChart() {
  if (!radarChart.value || !compound.value) return
  if (chartInstance) chartInstance.dispose()

  chartInstance = echarts.init(radarChart.value)
  const s = compound.value.radarScores
  const data = [
    { name: '抗炎效能', value: s.antiInflammatory },
    { name: '免疫调节', value: s.immuneRegulation },
    { name: '气道修复', value: s.airwayRepair }
  ]

  chartInstance.setOption({
    color: ['#409eff'],
    tooltip: { trigger: 'item' },
    radar: {
      indicator: data.map(d => ({ name: d.name, max: 100 })),
      shape: 'polygon',
      splitNumber: 4,
      radius: '58%',
      axisName: { color: '#666', fontSize: 12 },
      splitLine: { lineStyle: { color: 'rgba(64,158,255,0.2)' } },
      splitArea: { areaStyle: { color: ['rgba(64,158,255,0.05)', 'rgba(64,158,255,0.1)'] } },
      axisLine: { lineStyle: { color: 'rgba(64,158,255,0.3)' } }
    },
    series: [{
      type: 'radar',
      data: [{
        value: data.map(d => d.value),
        name: '效能评分',
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2, color: '#409eff' },
        areaStyle: { color: 'rgba(64,158,255,0.35)' },
        itemStyle: { color: '#409eff' }
      }]
    }]
  })
}

async function loadCompound() {
  loading.value = true
  try {
    const compoundId = route.query.id
    const compoundName = route.query.name
    if (compoundId) {
      const [detailRes, targetsRes] = await Promise.allSettled([
        getCompoundDetail(compoundId),
        getCompoundTargets(compoundId)
      ])
      if (detailRes.status !== 'fulfilled' || !detailRes.value) return
      const d = detailRes.value
      compound.value = {
        name: d.name || compoundName,
        id: d.id,
        mw: d.mw,
        logp: d.logp,
        hbd: d.hbd,
        hba: d.hba,
        tpsa: d.tpsa,
        rotatableBonds: d.rotatable_bonds,
        numRings: d.num_rings,
        numAromaticRings: d.num_aromatic_rings,
        numHeavyAtoms: d.num_heavy_atoms,
        molecularFormula: d.molecular_formula,
        bloodEntryProbability: d.blood_entry_probability || 0,
        smiles: d.smiles || '',
        asthmaRelated: d.asthma_related || false,
        herbNames: d.herb_names || [],
        targets: [],
        radarScores: { antiInflammatory: 0, immuneRegulation: 0, airwayRepair: 0 },
        molblock: null
      }
      if (targetsRes.status === 'fulfilled' && targetsRes.value) {
        compound.value.targets = (targetsRes.value || []).map(t => ({
          gene: t.gene,
          targetType: t.target_type || '—',
          species: t.species || '—',
          sourceDB: t.source_db || '—',
          networkCentrality: t.network_centrality || 0,
          asthmaRelated: t.asthma_related || false
        }))
      }
      // 雷达图异步加载
      getCompoundRadar(compoundId).then(r => {
        if (r) {
          compound.value.radarScores = {
            antiInflammatory: r.anti_inflammatory || 0,
            immuneRegulation: r.immune_regulation || 0,
            airwayRepair: r.airway_repair || 0
          }
          nextTick(() => initRadarChart())
        }
      }).catch(() => {})
      // 3D 结构异步加载
      load3DStructure(compoundId)
      await nextTick()
      initRadarChart()
    }
  } catch (e) {
    console.error('Failed to load compound:', e)
  } finally {
    loading.value = false
  }
}

function goBack() { router.push('/compounds') }

onMounted(() => { loadCompound() })
onUnmounted(() => {
  if (chartInstance) { chartInstance.dispose(); chartInstance = null }
  if (viewer3D) { viewer3D = null }
})
</script>

<style scoped>
.compound-detail-container {
  padding: 16px 24px;
  background: var(--bg-gradient);
  min-height: 100vh;
  max-width: 1500px;
  margin: 0 auto;
}

.back-bar { margin-bottom: 12px; }

/* 顶部并排 */
.top-row {
  display: grid;
  grid-template-columns: 1fr 420px;
  gap: 16px;
  margin-bottom: 16px;
}

.info-card, .structure-card, .radar-card, .targets-overview-card, .targets-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

/* 化合物头部 */
.compound-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
}

.name-section { display: flex; flex-direction: column; gap: 4px; }

.compound-name {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0;
  line-height: 1.2;
}

.formula-text {
  font-size: 13px;
  color: #909399;
  font-family: 'Courier New', monospace;
}

.badge-section { display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }

/* 入血概率 */
.prob-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.prob-bar .prob-label {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  white-space: nowrap;
}

.prob-bar .prob-progress { flex: 1; }

.prob-bar .prob-value {
  font-size: 14px;
  font-weight: 700;
  color: #409eff;
  min-width: 50px;
  text-align: right;
}

/* 双列属性 */
.props-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 16px;
  margin-bottom: 12px;
}

.prop-item {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 6px 10px;
  background: #f9fafc;
  border-radius: 6px;
}

.prop-key {
  font-size: 12px;
  color: #909399;
  font-weight: 500;
}

.prop-val {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.prop-val small {
  font-size: 11px;
  color: #c0c4cc;
  font-weight: 400;
}

/* Lipinski */
.lipinski-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  margin-bottom: 12px;
  background: #f0f9ff;
  border: 1px solid #d0e3f5;
}

.lipinski-bar .el-icon { font-size: 18px; }
.lipinski-pass { color: #67c23a; }
.lipinski-fail { color: #f56c6c; }

.lipinski-text {
  font-size: 13px;
  color: #606266;
}

/* SMILES */
.smiles-section {
  border-top: 1px solid #ebeef5;
  padding-top: 10px;
}

.smiles-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.smiles-label {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
}

.smiles-actions { display: flex; gap: 4px; }

.smiles-code {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #409eff;
  background: rgba(64, 158, 255, 0.06);
  padding: 8px 12px;
  border-radius: 6px;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: all 0.3s;
}

.smiles-code.expanded {
  white-space: pre-wrap;
  word-break: break-all;
}

/* 3D 结构卡 */
.structure-card {
  display: flex;
  flex-direction: column;
}

.structure-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.structure-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.structure-controls { display: flex; gap: 4px; }

.mol-viewer {
  width: 100%;
  height: 320px;
  border-radius: 8px;
  border: 1px solid #ebeef5;
  background: #fafbfc;
  position: relative;
}

.structure-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-size: 11px;
  color: #c0c4cc;
}

/* 中部并排 */
.mid-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-header h2 {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.header-right { display: flex; align-items: center; gap: 8px; }
.target-search { width: 200px; }

/* 雷达图 */
.radar-chart {
  width: 100%;
  height: 220px;
}

.radar-summary {
  display: flex;
  justify-content: space-around;
  padding-top: 8px;
  border-top: 1px solid #ebeef5;
}

.radar-summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.summary-label { font-size: 11px; color: #909399; }
.summary-value { font-size: 18px; font-weight: 700; color: #409eff; }

/* 靶点概览 */
.targets-overview-card { display: flex; flex-direction: column; }

.targets-stats {
  display: flex;
  justify-content: space-around;
  padding: 12px 0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-num {
  font-size: 28px;
  font-weight: 700;
  color: #409eff;
}

.stat-item.asthma .stat-num { color: #f56c6c; }
.stat-item.total .stat-num { color: #303133; }

.stat-label {
  font-size: 12px;
  color: #909399;
}

.source-herbs {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  padding-top: 10px;
  border-top: 1px solid #ebeef5;
}

.herb-label {
  font-size: 12px;
  color: #909399;
  font-weight: 600;
}

.herb-tag { margin: 0; }

/* 靶点表 */
.targets-card { margin-bottom: 16px; }

.target-gene { font-weight: 600; color: #303133; }

.target-pagination {
  display: flex;
  justify-content: center;
  margin-top: 12px;
}

.speech-btn {
  color: #909399;
  transition: all 0.3s ease;
}
.speech-btn:hover { color: #409eff; }
.speech-btn.speaking { color: #67c23a; animation: pulse 1s infinite; }

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

/* 响应式 */
@media (max-width: 1200px) {
  .top-row, .mid-row {
    grid-template-columns: 1fr;
  }
  .compound-detail-container { padding: 12px; }
}
</style>
