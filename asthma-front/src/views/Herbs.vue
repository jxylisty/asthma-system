<template>
  <div class="herbs-container">
    <div class="page-header">
      <h2 class="page-title">中药详情</h2>
      <p class="page-desc">系统收录的中药药材数据汇总，点击卡片查看含有的化合物信息</p>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索中药名称、拼音、科属..."
        class="search-input"
        clearable
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <div class="extra-filters">
        <el-tooltip content="仅显示与哮喘相关的中药" placement="top">
          <el-switch
            v-model="asthmaOnly"
            active-text="哮喘相关"
            inline-prompt
            class="asthma-switch"
          />
        </el-tooltip>

        <el-input-number
          v-model="minCompoundCount"
          :min="0"
          :step="1"
          controls-position="right"
          class="compound-input"
        >
          <template #prefix>
            <span class="compound-prefix">化合物≥</span>
          </template>
        </el-input-number>

        <el-button type="warning" plain @click="resetFilters">
          <el-icon><RefreshLeft /></el-icon>
          重置筛选
        </el-button>
      </div>
    </div>

    <div class="filter-section" v-loading="filterLoading">
      <div class="filter-row">
        <span class="filter-label">功效分类</span>
        <div class="filter-tags">
          <el-tag
            v-for="opt in filterOptions.categories"
            :key="opt"
            :type="selectedCategories.includes(opt) ? '' : 'info'"
            :effect="selectedCategories.includes(opt) ? 'dark' : 'plain'"
            class="filter-tag"
            @click="toggleFilter(selectedCategories, opt)"
          >
            {{ opt }}
          </el-tag>
          <span v-if="!filterOptions.categories || filterOptions.categories.length === 0" class="empty-tip">暂无选项</span>
        </div>
      </div>
    </div>

    <div v-loading="loading" class="herb-grid stagger-grid">
      <el-card
        v-for="(item, index) in herbs"
        :key="item.id"
        class="herb-card stagger-item"
        :style="{ '--i': String(index) }"
        @click="handleCardClick(item)"
      >
        <!-- Row 1: 名称 + 拼音 + 分类标签 -->
        <div class="hc-top">
          <div class="hc-title-line">
            <span class="hc-icon">🌿</span>
            <span class="hc-name">{{ item.name }}</span>
            <span class="hc-pinyin">{{ item.pinyin || '' }}</span>
          </div>
          <el-tag v-if="item.category" size="small" effect="dark" class="hc-cat-tag">
            {{ item.category }}
          </el-tag>
        </div>

        <!-- Row 2-3: 性味/归经/科属/功效 紧凑两行 -->
        <div class="hc-divider"></div>
        <div class="hc-meta">
          <div class="hc-meta-row">
            <span class="hc-meta-label">☯️ 性味：</span>
            <span>{{ item.nature || '—' }} / {{ item.flavor || '—' }}</span>
            <span class="hc-meta-sep">|</span>
            <span class="hc-meta-label">🏷️ 科属：</span>
            <span>{{ item.family || '—' }}</span>
          </div>
          <div class="hc-meta-row">
            <span class="hc-meta-label">📍 归经：</span>
            <span>{{ item.meridians || '—' }}</span>
          </div>
          <div class="hc-meta-row hc-func-row">
            <span class="hc-meta-label">✨ 功效：</span>
            <span class="hc-func-text">{{ item.functions || '—' }}</span>
          </div>
        </div>

        <!-- 底部：化合物数 + 详情按钮 -->
        <div class="hc-divider"></div>
        <div class="hc-footer">
          <div class="hc-stats">
            <span class="hc-stat">
              <strong>{{ item.compoundCount }}</strong> 个化合物
            </span>
          </div>
          <el-button text type="primary" size="small" @click.stop="handleCardClick(item)">
            查看中药详情 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </el-card>
    </div>

    <div class="pagination-wrapper" v-if="totalHerbs > 0">
      <el-pagination
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="currentPage"
        :page-sizes="[12, 24, 36, 48]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="totalHerbs"
      >
      </el-pagination>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Search, ArrowRight, RefreshLeft } from '@element-plus/icons-vue'
import { getHerbs, getHerbFilterOptions } from '../api'

const router = useRouter()

const loading = ref(false)
const filterLoading = ref(false)
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(12)

const herbs = ref([])
const totalHerbs = ref(0)

const filterOptions = ref({ categories: [] })
const selectedCategories = ref([])
const asthmaOnly = ref(false)
const minCompoundCount = ref(0)

function toggleFilter(list, val) {
  const idx = list.indexOf(val)
  if (idx > -1) { list.splice(idx, 1) } else { list.push(val) }
}

async function loadFilterOptions() {
  filterLoading.value = true
  try {
    const raw = await getHerbFilterOptions()
    const data = raw.data || raw
    filterOptions.value = { categories: data.categories || [] }
  } catch (e) { console.error('Filter options:', e) }
  finally { filterLoading.value = false }
}

async function loadHerbs() {
  loading.value = true
  try {
    const raw = await getHerbs({
      page: currentPage.value, page_size: pageSize.value,
      keyword: searchQuery.value,
      category: selectedCategories.value.join(','),
      asthma_related: asthmaOnly.value || undefined,
      min_compound_count: minCompoundCount.value || undefined
    })
    const data = raw.data || raw
    herbs.value = (data.items || []).map(item => ({
      id: item.id, name: item.name, pinyin: item.pinyin || '',
      category: item.category || '', nature: item.nature || '',
      flavor: item.flavor || '', meridians: item.meridians || '',
      family: item.family || '', functions: item.functions || '',
      compoundCount: item.compound_count || 0,
      asthmaRelated: item.asthma_related || false
    }))
    totalHerbs.value = data.total || 0
  } catch (e) { console.error('Herbs:', e) }
  finally { loading.value = false }
}

function resetFilters() {
  selectedCategories.value = []; asthmaOnly.value = false
  minCompoundCount.value = 0; searchQuery.value = ''
  currentPage.value = 1; loadHerbs()
}

onMounted(() => { loadFilterOptions(); loadHerbs() })

let searchTimer = null
watch([searchQuery, selectedCategories, asthmaOnly, minCompoundCount],
  () => { clearTimeout(searchTimer); searchTimer = setTimeout(() => { currentPage.value = 1; loadHerbs() }, 300) },
  { deep: true }
)

function handleCardClick(item) {
  router.push({ path: '/herbs/detail', query: { id: item.id, name: item.name } })
}
function handleSizeChange(v) { pageSize.value = v; currentPage.value = 1; loadHerbs() }
function handleCurrentChange(v) { currentPage.value = v; loadHerbs() }
</script>

<style scoped>
.herbs-container {
  padding: 16px 40px;
  max-width: 1600px;
  margin: 0 auto;
  background: var(--bg-gradient);
  min-height: 100vh;
}
.page-header { margin-bottom: 20px }
.page-title { font-size: var(--fs-h1); font-weight: var(--fw-bold); color: var(--text-color); margin-bottom: 6px }
.page-desc { font-size: var(--fs-body); color: var(--text-secondary) }

.search-bar { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; flex-wrap: wrap }
.search-input { flex: 1; min-width: 280px; height: 44px }
.search-input :deep(.el-input__wrapper) {
  background: rgba(30,41,59,0.6) !important;
  box-shadow: 0 0 0 1px rgba(148,163,184,0.15) inset !important;
  border-radius: 10px;
}
.search-input :deep(.el-input__inner) { color: var(--text-color) !important }
.search-input :deep(.el-input__inner::placeholder) { color: var(--text-muted) }
.search-input :deep(.el-input__prefix),
.search-input :deep(.el-input__suffix) { color: var(--text-muted) }
.extra-filters { display: flex; align-items: center; gap: 16px; flex-wrap: wrap }
.asthma-switch { margin-right: 4px }
.compound-input { width: 160px }
.compound-input :deep(.el-input-number__decrease),
.compound-input :deep(.el-input-number__increase) {
  background: rgba(255,255,255,0.04) !important;
  color: var(--text-secondary) !important;
  border-color: rgba(148,163,184,0.15) !important;
}
.compound-input :deep(.el-input__wrapper) {
  background: rgba(30,41,59,0.6) !important;
  box-shadow: 0 0 0 1px rgba(148,163,184,0.15) inset !important;
}
.compound-input :deep(.el-input__inner) { color: var(--text-color) !important }
.compound-prefix { font-size: var(--fs-sub); color: var(--text-muted); white-space: nowrap }

/* 重置按钮 */
.extra-filters :deep(.el-button--warning.is-plain) {
  background: rgba(230,162,60,0.1) !important;
  border-color: rgba(230,162,60,0.3) !important;
  color: #e6a23c !important;
}
.extra-filters :deep(.el-button--warning.is-plain:hover) {
  background: rgba(230,162,60,0.2) !important;
}

.filter-section {
  background: rgba(30,41,59,0.6);
  border-radius: 14px;
  padding: 16px 20px;
  margin-bottom: 20px;
  border: 1px solid rgba(148,163,184,0.1);
}
.filter-row { display: flex; align-items: flex-start; gap: 12px }
.filter-label { flex-shrink: 0; width: 72px; padding-top: 4px; font-size: var(--fs-body); font-weight: var(--fw-semi); color: var(--text-secondary) }
.filter-tags { display: flex; flex-wrap: wrap; gap: 8px; flex: 1 }
.filter-tag {
  cursor: pointer;
  user-select: none;
  transition: all 0.2s;
  border-radius: 6px;
}
.filter-tag:hover { transform: translateY(-1px) }
.empty-tip { font-size: var(--fs-body); color: var(--text-muted); line-height: 28px }

/* Grid */
.herb-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 16px; min-height: 200px }

/* Card：对齐深蓝半透明卡 */
.herb-card {
  cursor: pointer;
  transition: all 0.3s;
  border-radius: 14px;
  overflow: hidden;
  background: rgba(30,41,59,0.6) !important;
  border: 1px solid rgba(148,163,184,0.1) !important;
}
.herb-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 30px rgba(0,0,0,0.3);
  border-color: rgba(64,158,255,0.4) !important;
}
.herb-card :deep(.el-card__body) {
  padding: 18px 20px;
  color: var(--text-color);
}

.hc-top { display: flex; justify-content: space-between; align-items: center; gap: 12px }
.hc-title-line { display: flex; align-items: baseline; gap: 8px; min-width: 0; flex: 1 }
.hc-icon { font-size: var(--fs-h3); flex-shrink: 0 }
.hc-name { font-size: var(--fs-h3); font-weight: var(--fw-bold); color: var(--text-color); white-space: nowrap }
.hc-pinyin { font-size: var(--fs-body); color: var(--text-muted); font-style: italic; white-space: nowrap; overflow: hidden; text-overflow: ellipsis }
.hc-cat-tag { flex-shrink: 0 }

.hc-divider { height: 1px; background: rgba(148,163,184,0.1); margin: 12px 0 }

.hc-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: rgba(255,255,255,0.03);
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid rgba(148,163,184,0.06);
}
.hc-meta-row { display: flex; align-items: center; gap: 4px; font-size: var(--fs-body); color: var(--text-secondary) }
.hc-meta-label { color: var(--text-muted); white-space: nowrap; font-weight: var(--fw-medium) }
.hc-meta-sep { color: rgba(148,163,184,0.2); margin: 0 6px }
.hc-func-row { overflow: hidden }
.hc-func-text { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-color) }

.hc-footer { display: flex; justify-content: space-between; align-items: center }
.hc-stats { display: flex; gap: 16px }
.hc-stat { font-size: var(--fs-body); color: var(--text-secondary) }
.hc-stat strong { color: var(--text-color); font-size: var(--fs-h3); margin-right: 2px; font-weight: var(--fw-bold) }

/* 详情按钮颜色修复 */
.hc-footer :deep(.el-button--text) {
  color: var(--text-secondary) !important;
  font-weight: var(--fw-medium);
}
.hc-footer :deep(.el-button--text:hover) {
  color: #409eff !important;
  background: rgba(64,158,255,0.08);
}

.pagination-wrapper { display: flex; justify-content: center; margin-top: 32px }
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

/* 功效标签未选中 -> info plain 时保持可见 */
.filter-tag.el-tag--info.is-plain {
  color: var(--text-secondary) !important;
  background: rgba(255,255,255,0.03) !important;
  border-color: rgba(148,163,184,0.15) !important;
}
.filter-tag.el-tag.is-plain:hover {
  opacity: 0.85;
}

@media (max-width: 1200px) {
  .herbs-container { padding: 16px }
  .herb-grid { grid-template-columns: 1fr }
}
</style>