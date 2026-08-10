<template>
  <div class="cp-container">
    <div class="page-header">
      <h2 class="page-title">自定义处方分析</h2>
      <p class="page-desc">自由组合中药，系统自动计算入血成分与靶点，并调用 AI 生成深度分析报告</p>
    </div>

    <div class="cp-layout" :class="{ 'builder-collapsed': builderCollapsed }">
      <!-- ============ 左侧：处方构建器 ============ -->
      <div class="builder-panel card" v-show="!builderCollapsed">
        <div class="card-header">
          <h3>处方构建器</h3>
          <el-button text size="small" @click="builderCollapsed = true" title="折叠面板">
            <el-icon><Fold /></el-icon>
            折叠
          </el-button>
        </div>

        <el-form label-position="top" class="builder-form">
          <el-form-item label="处方名称">
            <el-input v-model="prescriptionName" placeholder="如：自拟哮喘平喘方1号" clearable />
          </el-form-item>

          <el-form-item label="入血概率阈值">
            <el-slider
              v-model="minProbSlider"
              :min="0"
              :max="100"
              :step="5"
              :format-tooltip="v => v + '%'"
              style="width: 100%"
            />
            <span class="threshold-value">{{ minProbSlider }}%</span>
          </el-form-item>

          <el-form-item label="组方中药">
            <el-button type="primary" plain @click="openHerbDialog" style="width: 100%">
              <el-icon><Plus /></el-icon>
              编辑添加中药
            </el-button>
          </el-form-item>
        </el-form>

        <!-- 已选药材列表 -->
        <div class="herb-list-section">
          <div class="section-title">
            <span>组方药材（{{ selectedHerbs.length }}味）</span>
          </div>
          <div v-if="selectedHerbs.length === 0" class="empty-herbs">
            <el-empty description="尚未添加药材" :image-size="60" />
          </div>
          <div v-else class="herb-items">
            <div v-for="(h, idx) in selectedHerbs" :key="h.herb_id" class="herb-row">
              <div class="herb-row-line1">
                <span class="herb-idx">{{ idx + 1 }}</span>
                <span class="herb-name">{{ h.herb_name }}</span>
                <el-tag v-if="h.nature" size="small" effect="plain">{{ h.nature }}</el-tag>
                <el-tag v-if="h.category" size="small" type="info" effect="plain">{{ h.category }}</el-tag>
              </div>
              <div class="herb-row-line2">
                <el-input
                  v-model="h.dosage"
                  placeholder="如 9g"
                  size="small"
                  class="dosage-input"
                />
                <el-button type="danger" size="small" text @click="removeHerb(idx)">
                  <el-icon><Delete /></el-icon>
                  移除
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="builder-actions">
          <el-button
            type="primary"
            :loading="analyzing"
            :disabled="!canAnalyze"
            @click="runAnalyze"
            style="width: 100%"
          >
            <el-icon><DataAnalysis /></el-icon>
            一键预测分析
          </el-button>
          <el-button
            type="success"
            :loading="generatingReport"
            :disabled="!analysisData || !isAiConfigured"
            @click="runAiReport"
            style="width: 100%; margin-top: 8px"
          >
            <el-icon><MagicStick /></el-icon>
            生成 AI 智能报告
          </el-button>
          <div v-if="!isAiConfigured" class="ai-warn-tip">
            <el-icon><WarningFilled /></el-icon>
            <span>未配置 AI API Key，</span>
            <el-link type="primary" @click="$router.push('/settings')">去设置</el-link>
          </div>
        </div>
      </div>

      <!-- ============ 右侧：分析结果 + AI 报告 ============ -->
      <div class="result-panel">
        <!-- 折叠时的展开按钮 -->
        <div v-if="builderCollapsed" class="expand-builder-bar">
          <el-button type="primary" plain size="small" @click="builderCollapsed = false">
            <el-icon><Expand /></el-icon>
            展开处方构建器
          </el-button>
          <span class="collapsed-info" v-if="selectedHerbs.length">
            当前处方：{{ prescriptionName || '未命名' }} · {{ selectedHerbs.length }}味中药
          </span>
        </div>

        <!-- 统计概览 -->
        <div v-if="analysisData" class="stats-row">
          <div class="stat-card">
            <div class="stat-value">{{ analysisData.stats.herb_count }}</div>
            <div class="stat-label">药材数</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ analysisData.stats.compound_count }}</div>
            <div class="stat-label">化合物数</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ analysisData.stats.target_count }}</div>
            <div class="stat-label">靶点数</div>
          </div>
          <div class="stat-card highlight">
            <div class="stat-value">{{ analysisData.stats.asthma_target_count }}</div>
            <div class="stat-label">哮喘靶点</div>
          </div>
          <div class="stat-card highlight">
            <div class="stat-value">{{ analysisData.stats.high_prob_compound_count }}</div>
            <div class="stat-label">高概率入血(≥70%)</div>
          </div>
        </div>

        <!-- 雷达图 + Top化合物 -->
        <div v-if="analysisData" class="dual-row">
          <div class="card radar-card">
            <div class="card-header">
              <h3>干预效能雷达图</h3>
            </div>
            <div ref="radarChart" class="radar-chart"></div>
          </div>
          <div class="card compound-card">
            <div class="card-header">
              <h3>Top 入血化合物</h3>
              <span class="count-badge">{{ analysisData.compounds.length }}</span>
            </div>
            <div class="compound-table-wrapper">
              <el-table :data="analysisData.compounds.slice(0, 10)" size="small" stripe max-height="320">
                <el-table-column type="index" label="#" width="40" />
                <el-table-column prop="name" label="化合物" min-width="140" show-overflow-tooltip />
                <el-table-column prop="herb_name" label="来源" width="80" show-overflow-tooltip />
                <el-table-column label="ccTCM 2.0" width="82">
                  <template #default="{ row }">
                    <span :class="['prob-text', probClass(row.prob_cctcm)]">
                      {{ row.prob_cctcm != null ? (row.prob_cctcm * 100).toFixed(1) + '%' : '—' }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column label="HERB 2.0" width="82">
                  <template #default="{ row }">
                    <span :class="['prob-text', probClass(row.prob_herb)]">
                      {{ row.prob_herb != null ? (row.prob_herb * 100).toFixed(1) + '%' : '—' }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column label="分子量" width="80">
                  <template #default="{ row }">{{ row.mw != null ? row.mw.toFixed(1) : '—' }}</template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </div>

        <!-- 靶点列表 -->
        <div v-if="analysisData && analysisData.targets.length" class="card">
          <div class="card-header">
            <h3>核心靶点（哮喘相关高亮）</h3>
            <span class="count-badge">{{ analysisData.targets.length }}</span>
          </div>
          <div class="target-tags">
            <el-tag
              v-for="t in analysisData.targets.slice(0, 60)"
              :key="t.gene"
              :type="t.asthma_related ? 'danger' : 'info'"
              :effect="t.asthma_related ? 'dark' : 'plain'"
              class="target-tag"
            >
              {{ t.gene }}
            </el-tag>
          </div>
        </div>

        <!-- AI 报告区 -->
        <div class="card ai-report-card" v-if="reportContent || generatingReport">
          <div class="card-header">
            <h3>AI 智能分析报告</h3>
            <div class="report-actions">
              <el-button
                v-if="reportContent && !generatingReport"
                size="small"
                type="primary"
                plain
                @click="exportPdf"
              >
                <el-icon><Download /></el-icon>
                导出 PDF
              </el-button>
              <el-button
                v-if="reportContent && !generatingReport"
                size="small"
                @click="copyReport"
              >
                <el-icon><DocumentCopy /></el-icon>
                复制
              </el-button>
              <el-button
                v-if="generatingReport"
                size="small"
                type="danger"
                plain
                @click="abortReport"
              >
                <el-icon><VideoPause /></el-icon>
                停止
              </el-button>
            </div>
          </div>
          <div class="report-body" v-loading="generatingReport && !reportContent" element-loading-text="AI 正在生成报告...">
            <div class="markdown-content" v-html="renderedReport"></div>
            <span v-if="generatingReport" class="cursor-blink">▊</span>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="!analysisData && !analyzing" class="empty-state">
          <el-empty description="构建处方后点击「一键预测分析」查看结果" :image-size="120" />
        </div>
      </div>
    </div>

    <!-- ============ 中药选择对话框 ============ -->
    <el-dialog
      v-model="herbDialogVisible"
      title="编辑添加中药"
      width="80%"
      top="5vh"
      :close-on-click-modal="false"
    >
      <!-- 搜索筛选栏 -->
      <div class="dialog-search-bar">
        <el-input
          v-model="dialogSearchQuery"
          placeholder="搜索中药名称、拼音、科属..."
          clearable
          style="width: 280px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <div class="dialog-extra-filters">
          <el-tooltip content="仅显示与哮喘相关的中药" placement="top">
            <el-switch
              v-model="dialogAsthmaOnly"
              active-text="哮喘相关"
              inline-prompt
            />
          </el-tooltip>

          <el-input-number
            v-model="dialogMinCompoundCount"
            :min="0"
            :step="1"
            controls-position="right"
            style="width: 140px"
          >
            <template #prefix>
              <span style="font-size: 12px">化合物≥</span>
            </template>
          </el-input-number>

          <el-button type="warning" plain size="small" @click="resetDialogFilters">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
        </div>
      </div>

      <!-- 功效分类筛选 -->
      <div class="dialog-filter-section" v-loading="dialogFilterLoading">
        <span class="dialog-filter-label">功效分类</span>
        <div class="dialog-filter-tags">
          <el-tag
            v-for="opt in dialogFilterOptions.categories"
            :key="opt"
            :type="dialogSelectedCategories.includes(opt) ? '' : 'info'"
            :effect="dialogSelectedCategories.includes(opt) ? 'dark' : 'plain'"
            class="dialog-filter-tag"
            @click="toggleDialogFilter(dialogSelectedCategories, opt)"
          >
            {{ opt }}
          </el-tag>
        </div>
      </div>

      <!-- 中药卡片网格 -->
      <div v-loading="dialogLoading" class="dialog-herb-grid">
        <div
          v-for="item in dialogHerbs"
          :key="item.id"
          class="dialog-herb-card"
          :class="{ 'is-selected': isSelectedInDialog(item.id) }"
        >
          <div class="dialog-card-header">
            <h4 class="dialog-card-title">{{ item.name }}</h4>
            <el-tag v-if="item.asthmaRelated" type="danger" size="small">哮喘</el-tag>
            <el-tag v-else type="info" size="small">普通</el-tag>
          </div>
          <div class="dialog-card-body">
            <div class="dialog-info-row">
              <span class="dialog-label">拼音：</span>
              <span>{{ item.pinyin || '—' }}</span>
            </div>
            <div class="dialog-info-row">
              <span class="dialog-label">分类：</span>
              <span>{{ item.category || '—' }}</span>
            </div>
            <div class="dialog-info-row">
              <span class="dialog-label">性味：</span>
              <span>{{ item.nature }} / {{ item.flavor }}</span>
            </div>
            <div class="dialog-info-row">
              <span class="dialog-label">功效：</span>
              <span class="dialog-text-ellipsis">{{ item.functions || '—' }}</span>
            </div>
            <div class="dialog-info-row">
              <span class="dialog-label">化合物数：</span>
              <span class="dialog-count-badge">{{ item.compoundCount }}</span>
            </div>
          </div>
          <div class="dialog-card-footer">
            <el-button
              v-if="!isSelectedInDialog(item.id)"
              type="primary"
              size="small"
              @click="addHerbFromDialog(item)"
            >
              <el-icon><Plus /></el-icon>
              添加
            </el-button>
            <el-button
              v-else
              type="success"
              size="small"
              disabled
            >
              <el-icon><Check /></el-icon>
              已添加
            </el-button>
          </div>
        </div>
        <el-empty v-if="!dialogLoading && dialogHerbs.length === 0" description="未找到匹配的中药" :image-size="80" />
      </div>

      <!-- 分页 -->
      <div class="dialog-pagination">
        <el-pagination
          v-model:current-page="dialogCurrentPage"
          v-model:page-size="dialogPageSize"
          :total="dialogTotalHerbs"
          :page-sizes="[12, 24, 48]"
          layout="total, sizes, prev, pager, next"
          background
          small
        />
      </div>

      <template #footer>
        <div class="dialog-footer">
          <span class="dialog-selected-count">已选 {{ selectedHerbs.length }} 味中药</span>
          <el-button @click="herbDialogVisible = false">完成</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  DataAnalysis, MagicStick, Delete, Download, DocumentCopy,
  VideoPause, WarningFilled, Plus, Search, RefreshLeft, Check,
  Fold, Expand,
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { marked } from 'marked'
import { getHerbs, getHerbFilterOptions, analyzeCustomPrescription, streamAiReport } from '../api'
import { useAiSettings } from '../composables/useAiSettings'

const { isConfigured: isAiConfigured, buildAiHeaders } = useAiSettings()

// ===== 处方构建器状态 =====
const prescriptionName = ref('')
const minProbSlider = ref(50)
const selectedHerbs = ref([])
const builderCollapsed = ref(false)

const minProb = computed(() => minProbSlider.value / 100)
const canAnalyze = computed(() => prescriptionName.value.trim() && selectedHerbs.value.length > 0)

// ===== 中药选择对话框状态 =====
const herbDialogVisible = ref(false)
const dialogSearchQuery = ref('')
const dialogAsthmaOnly = ref(false)
const dialogMinCompoundCount = ref(0)
const dialogSelectedCategories = ref([])
const dialogFilterOptions = ref({ categories: [] })
const dialogFilterLoading = ref(false)
const dialogHerbs = ref([])
const dialogLoading = ref(false)
const dialogCurrentPage = ref(1)
const dialogPageSize = ref(12)
const dialogTotalHerbs = ref(0)
let dialogSearchTimer = null

function openHerbDialog() {
  herbDialogVisible.value = true
  if (dialogFilterOptions.value.categories.length === 0) {
    loadDialogFilterOptions()
  }
  if (dialogHerbs.value.length === 0) {
    loadDialogHerbs()
  }
}

async function loadDialogFilterOptions() {
  dialogFilterLoading.value = true
  try {
    const data = await getHerbFilterOptions()
    dialogFilterOptions.value = { categories: data.categories || [] }
  } catch (e) {
    console.error('加载筛选选项失败:', e)
  } finally {
    dialogFilterLoading.value = false
  }
}

async function loadDialogHerbs() {
  dialogLoading.value = true
  try {
    const data = await getHerbs({
      page: dialogCurrentPage.value,
      page_size: dialogPageSize.value,
      keyword: dialogSearchQuery.value,
      category: dialogSelectedCategories.value.join(','),
      asthma_related: dialogAsthmaOnly.value || undefined,
      min_compound_count: dialogMinCompoundCount.value || undefined,
    })
    dialogHerbs.value = (data.items || []).map(item => ({
      id: item.id,
      name: item.name,
      pinyin: item.pinyin || '',
      category: item.category || '',
      nature: item.nature || '',
      flavor: item.flavor || '',
      meridians: item.meridians || '',
      functions: item.functions || '',
      compoundCount: item.compound_count || 0,
      asthmaRelated: item.asthma_related || false,
    }))
    dialogTotalHerbs.value = data.total || 0
  } catch (e) {
    console.error('加载中药列表失败:', e)
  } finally {
    dialogLoading.value = false
  }
}

function resetDialogFilters() {
  dialogSelectedCategories.value = []
  dialogAsthmaOnly.value = false
  dialogMinCompoundCount.value = 0
  dialogSearchQuery.value = ''
  dialogCurrentPage.value = 1
  loadDialogHerbs()
}

function toggleDialogFilter(list, val) {
  const idx = list.indexOf(val)
  if (idx > -1) list.splice(idx, 1)
  else list.push(val)
}

function isSelectedInDialog(herbId) {
  return selectedHerbs.value.some(h => h.herb_id === herbId)
}

function addHerbFromDialog(item) {
  if (isSelectedInDialog(item.id)) {
    ElMessage.warning('该药材已添加')
    return
  }
  selectedHerbs.value.push({
    herb_id: item.id,
    herb_name: item.name,
    nature: item.nature,
    category: item.category,
    dosage: '',
  })
  ElMessage.success(`已添加「${item.name}」`)
}

// 对话框筛选变化时重新加载（300ms 防抖）
watch(
  [dialogSearchQuery, dialogSelectedCategories, dialogAsthmaOnly, dialogMinCompoundCount],
  () => {
    clearTimeout(dialogSearchTimer)
    dialogSearchTimer = setTimeout(() => {
      dialogCurrentPage.value = 1
      loadDialogHerbs()
    }, 300)
  },
  { deep: true }
)

watch(dialogCurrentPage, () => { if (herbDialogVisible.value) loadDialogHerbs() })
watch(dialogPageSize, () => { dialogCurrentPage.value = 1; if (herbDialogVisible.value) loadDialogHerbs() })

// ===== 分析结果 =====
const analyzing = ref(false)
const analysisData = ref(null)
const radarChart = ref(null)
let chartInstance = null

// ===== AI 报告 =====
const generatingReport = ref(false)
const reportContent = ref('')
const abortController = ref(null)

const renderedReport = computed(() => {
  if (!reportContent.value) return ''
  try {
    return marked.parse(reportContent.value, { breaks: true })
  } catch {
    return reportContent.value
  }
})

function removeHerb(idx) {
  selectedHerbs.value.splice(idx, 1)
}

// ===== 结构化分析 =====
async function runAnalyze() {
  if (!canAnalyze.value) return
  analyzing.value = true
  analysisData.value = null
  reportContent.value = ''
  try {
    const data = await analyzeCustomPrescription(
      {
        prescription_name: prescriptionName.value.trim(),
        herbs: selectedHerbs.value.map(h => ({
          herb_id: h.herb_id,
          herb_name: h.herb_name,
          dosage: h.dosage,
        })),
      },
      minProb.value,
    )
    analysisData.value = data
    ElMessage.success(`分析完成：${data.stats.compound_count} 个化合物，${data.stats.target_count} 个靶点`)
    await nextTick()
    initRadar(data.radar || [])
  } catch (e) {
    ElMessage.error('分析失败：' + (e.message || '未知错误'))
  } finally {
    analyzing.value = false
  }
}

// ===== 雷达图 =====
function initRadar(radarData) {
  if (!radarChart.value || !radarData.length) return
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(radarChart.value)
  chartInstance.setOption({
    color: ['#409eff'],
    tooltip: { trigger: 'item' },
    radar: {
      indicator: radarData.map(r => ({ name: r.efficacy_type, max: 100 })),
      shape: 'polygon',
      radius: '60%',
      axisName: { color: '#666', fontSize: 12 },
      splitArea: { areaStyle: { color: ['rgba(64,158,255,0.05)', 'rgba(64,158,255,0.1)'] } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: radarData.map(r => r.count),
        name: '干预效能',
        areaStyle: { color: 'rgba(64,158,255,0.35)' },
        lineStyle: { width: 2, color: '#409eff' },
        itemStyle: { color: '#409eff' },
      }],
    }],
  })
}

// ===== AI 报告生成 =====
async function runAiReport() {
  if (!isAiConfigured.value) {
    ElMessage.warning('请先在系统设置中配置 AI API Key')
    return
  }
  if (!analysisData.value) {
    ElMessage.warning('请先完成结构化分析')
    return
  }

  generatingReport.value = true
  reportContent.value = ''
  abortController.value = new AbortController()

  const body = {
    prescription_name: prescriptionName.value.trim(),
    herbs: selectedHerbs.value.map(h => ({
      herb_id: h.herb_id,
      herb_name: h.herb_name,
      dosage: h.dosage,
    })),
    min_prob: minProb.value,
    top_compounds: 15,
  }

  await streamAiReport({
    url: '/api/v1/prescriptions/ai-report',
    body,
    aiHeaders: buildAiHeaders(),
    signal: abortController.value.signal,
    onSnapshot: (data) => {
      // 如果还没有结构化数据，用快照填充
      if (!analysisData.value) {
        analysisData.value = {
          prescription_name: data.prescription_name,
          herbs: data.herbs,
          compounds: data.compounds,
          targets: data.targets,
          radar: [],
          stats: {
            herb_count: data.herbs.length,
            compound_count: data.compounds.length,
            target_count: data.targets.length,
            asthma_target_count: data.targets.filter(t => t.asthma_related).length,
            high_prob_compound_count: data.compounds.filter(c => (c.prob_cctcm || 0) >= 0.7).length,
          },
        }
      }
    },
    onDelta: (delta) => {
      reportContent.value += delta
    },
    onError: (err) => {
      const msgMap = {
        key_missing: '未配置 AI API Key，请在系统设置中填写',
        key_invalid: 'AI API Key 无效，请检查系统设置',
        quota_exhausted: 'AI API 额度已耗尽或触发限流，请充值后重试',
        network_error: 'AI 服务网络连接失败，请稍后重试',
      }
      ElMessage.error(msgMap[err.code] || err.message || 'AI 生成失败')
    },
    onDone: () => {
      generatingReport.value = false
    },
  })
}

function abortReport() {
  if (abortController.value) {
    abortController.value.abort()
    generatingReport.value = false
    ElMessage.info('已停止生成')
  }
}

// ===== 导出 PDF =====
async function exportPdf() {
  if (!reportContent.value) return
  try {
    const html2pdf = (await import('html2pdf.js')).default
    const container = document.createElement('div')
    container.style.padding = '24px'
    container.innerHTML = `
      <h1 style="text-align:center;font-size:22px;margin-bottom:8px;">${prescriptionName.value} - AI 智能分析报告</h1>
      <p style="text-align:center;color:#666;font-size:13px;margin-bottom:24px;">生成时间：${new Date().toLocaleString('zh-CN')}</p>
      <div style="font-size:14px;line-height:1.8;">${renderedReport.value}</div>
    `
    document.body.appendChild(container)
    await html2pdf().set({
      margin: [10, 10],
      filename: `${prescriptionName.value}_AI分析报告.pdf`,
      image: { type: 'jpeg', quality: 0.95 },
      html2canvas: { scale: 2, useCORS: true },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
    }).from(container).save()
    document.body.removeChild(container)
    ElMessage.success('PDF 导出成功')
  } catch (e) {
    ElMessage.error('导出失败：' + e.message)
  }
}

async function copyReport() {
  try {
    await navigator.clipboard.writeText(reportContent.value)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

// ===== 工具函数 =====
function probClass(p) {
  if (p == null) return 'gray'
  if (p >= 0.7) return 'high'
  if (p >= 0.5) return 'mid'
  return 'low'
}

onMounted(() => {
  window.addEventListener('resize', () => chartInstance && chartInstance.resize())
})
</script>

<style scoped>
.cp-container {
  padding: 32px;
  background: var(--bg-gradient);
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-color);
  margin-bottom: 6px;
}

.page-desc {
  font-size: 14px;
  color: var(--text-secondary);
}

.cp-layout {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 20px;
  align-items: start;
}

.cp-layout.builder-collapsed {
  grid-template-columns: 1fr;
}

.expand-builder-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 10px 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.collapsed-info {
  font-size: 13px;
  color: #606266;
}

.card {
  background: #fff;
  border-radius: 12px;
  padding: 18px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.card-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.count-badge {
  display: inline-block;
  min-width: 24px;
  padding: 0 8px;
  height: 22px;
  line-height: 22px;
  text-align: center;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #409eff, #67c23a);
  border-radius: 11px;
}

/* ===== 处方构建器 ===== */
.builder-panel {
  position: sticky;
  top: 20px;
}

.builder-form :deep(.el-form-item) {
  margin-bottom: 16px;
}

.builder-form :deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
  padding-bottom: 4px;
}

.threshold-value {
  margin-left: 12px;
  color: #409eff;
  font-weight: 600;
  font-size: 14px;
}

.herb-list-section {
  margin-top: 12px;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 10px;
}

.empty-herbs {
  padding: 12px 0;
}

.herb-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 280px;
  overflow-y: auto;
}

.herb-row {
  padding: 10px 12px;
  background: #f9fafc;
  border-radius: 8px;
  border-left: 3px solid #409eff;
}

.herb-row-line1 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.herb-row-line2 {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-left: 28px;
}

.dosage-input {
  width: 120px;
  flex-shrink: 0;
}

.herb-idx {
  width: 20px;
  height: 20px;
  line-height: 20px;
  text-align: center;
  background: #409eff;
  color: #fff;
  border-radius: 50%;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
}

.herb-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
}

.herb-row-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.builder-actions {
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.builder-actions :deep(.el-button) {
  margin-left: 0 !important;
}

.ai-warn-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 10px;
  font-size: 12px;
  color: #e6a23c;
}

/* ===== 结果面板 ===== */
.result-panel {
  min-width: 0;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 14px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.stat-card.highlight {
  background: linear-gradient(135deg, #fff 0%, #ecf5ff 100%);
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #409eff;
  line-height: 1.2;
}

.stat-card.highlight .stat-value {
  color: #e6a23c;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.dual-row {
  display: grid;
  grid-template-columns: 1fr 1.4fr;
  gap: 16px;
  margin-bottom: 16px;
}

.radar-chart {
  width: 100%;
  height: 280px;
}

.compound-table-wrapper {
  max-height: 320px;
  overflow-y: auto;
}

.prob-text.high { color: #f56c6c; font-weight: 600; }
.prob-text.mid { color: #e6a23c; font-weight: 600; }
.prob-text.low { color: #409eff; }
.prob-text.gray { color: #c0c4cc; }

.target-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.target-tag {
  margin: 0;
}

/* ===== AI 报告 ===== */
.ai-report-card {
  border: 2px solid #409eff;
}

.report-actions {
  display: flex;
  gap: 8px;
}

.report-body {
  font-size: 14px;
  line-height: 1.8;
  color: #303133;
  max-height: 700px;
  overflow-y: auto;
  padding: 8px 4px;
}

.markdown-content :deep(h1) {
  font-size: 22px;
  font-weight: 700;
  margin: 16px 0 12px;
  color: #303133;
  border-bottom: 2px solid #409eff;
  padding-bottom: 8px;
}

.markdown-content :deep(h2) {
  font-size: 18px;
  font-weight: 600;
  margin: 14px 0 10px;
  color: #303133;
  border-left: 4px solid #409eff;
  padding-left: 10px;
}

.markdown-content :deep(h3) {
  font-size: 16px;
  font-weight: 600;
  margin: 12px 0 8px;
  color: #409eff;
}

.markdown-content :deep(p) {
  margin: 8px 0;
}

.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 13px;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid #ebeef5;
  padding: 8px 10px;
  text-align: left;
}

.markdown-content :deep(th) {
  background: #f5f7fa;
  font-weight: 600;
  color: #303133;
}

.markdown-content :deep(tr:nth-child(even)) {
  background: #fafbfc;
}

.markdown-content :deep(strong) {
  color: #f56c6c;
  font-weight: 600;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 24px;
  margin: 8px 0;
}

.markdown-content :deep(li) {
  margin: 4px 0;
}

.markdown-content :deep(blockquote) {
  border-left: 4px solid #e6a23c;
  background: #fdf6ec;
  padding: 8px 12px;
  margin: 10px 0;
  color: #606266;
}

.cursor-blink {
  display: inline-block;
  color: #409eff;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.empty-state {
  padding: 60px 0;
}

/* ===== 响应式 ===== */
/* ===== 中药选择对话框 ===== */
.dialog-search-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.dialog-extra-filters {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dialog-filter-section {
  margin-bottom: 14px;
  padding: 10px 12px;
  background: #f9fafc;
  border-radius: 8px;
}

.dialog-filter-label {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-right: 8px;
}

.dialog-filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.dialog-filter-tag {
  cursor: pointer;
  user-select: none;
}

.dialog-herb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
  max-height: 50vh;
  overflow-y: auto;
  padding: 4px;
}

.dialog-herb-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
}

.dialog-herb-card:hover {
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.15);
  border-color: #409eff;
}

.dialog-herb-card.is-selected {
  border-color: #67c23a;
  background: #f0f9eb;
}

.dialog-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.dialog-card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin: 0;
  flex: 1;
}

.dialog-card-body {
  flex: 1;
  font-size: 12px;
  color: #606266;
  line-height: 1.6;
}

.dialog-info-row {
  display: flex;
  margin-bottom: 3px;
}

.dialog-label {
  color: #909399;
  white-space: nowrap;
  min-width: 56px;
}

.dialog-text-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dialog-count-badge {
  display: inline-block;
  min-width: 20px;
  padding: 0 6px;
  height: 18px;
  line-height: 18px;
  text-align: center;
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  background: #409eff;
  border-radius: 9px;
}

.dialog-card-footer {
  margin-top: 10px;
  text-align: right;
}

.dialog-pagination {
  margin-top: 14px;
  display: flex;
  justify-content: center;
}

.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.dialog-selected-count {
  font-size: 14px;
  font-weight: 600;
  color: #409eff;
}

@media (max-width: 1200px) {
  .cp-layout {
    grid-template-columns: 1fr;
  }
  .builder-panel {
    position: static;
  }
  .stats-row {
    grid-template-columns: repeat(3, 1fr);
  }
  .dual-row {
    grid-template-columns: 1fr;
  }
}
</style>
