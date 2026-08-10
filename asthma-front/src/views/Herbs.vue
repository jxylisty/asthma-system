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

    <div v-loading="loading" class="herb-grid">
      <el-card
        v-for="item in herbs"
        :key="item.id"
        class="herb-card"
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
.herbs-container { padding: 40px; background: var(--bg-gradient); min-height: 100vh }
.page-header { margin-bottom: 32px }
.page-title { font-size: 32px; font-weight: 700; color: var(--text-color); margin-bottom: 8px }
.page-desc { font-size: 16px; color: var(--text-secondary) }

.search-bar { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; flex-wrap: wrap }
.search-input { flex: 1; min-width: 280px; height: 44px }
.extra-filters { display: flex; align-items: center; gap: 16px; flex-wrap: wrap }
.asthma-switch { margin-right: 4px }
.compound-input { width: 160px }
.compound-prefix { font-size: 12px; color: #909399; white-space: nowrap }

.filter-section { background: var(--card-bg, #fff); border-radius: 12px; padding: 16px 20px; margin-bottom: 24px; box-shadow: 0 2px 12px rgba(0,0,0,0.08) }
.filter-row { display: flex; align-items: flex-start; gap: 12px }
.filter-label { flex-shrink: 0; width: 72px; padding-top: 4px; font-size: 14px; font-weight: 600; color: #303133 }
.filter-tags { display: flex; flex-wrap: wrap; gap: 8px; flex: 1 }
.filter-tag { cursor: pointer; user-select: none; transition: all 0.2s; border-radius: 6px }
.filter-tag:hover { transform: translateY(-1px) }
.empty-tip { font-size: 13px; color: #c0c4cc; line-height: 28px }

/* Grid */
.herb-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 20px; min-height: 200px }

/* Card */
.herb-card { cursor: pointer; transition: all 0.3s; border-radius: 14px; overflow: hidden; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08) }
.herb-card:hover { transform: translateY(-3px); box-shadow: 0 8px 30px rgba(0,0,0,0.25); border-color: rgba(255,255,255,0.15) }
.herb-card :deep(.el-card__body) { padding: 18px 20px }

.hc-top { display: flex; justify-content: space-between; align-items: center; gap: 12px }
.hc-title-line { display: flex; align-items: baseline; gap: 8px; min-width: 0; flex: 1 }
.hc-icon { font-size: 18px; flex-shrink: 0 }
.hc-name { font-size: 18px; font-weight: 700; color: var(--text-color); white-space: nowrap }
.hc-pinyin { font-size: 13px; color: var(--text-muted,#999); font-style: italic; white-space: nowrap; overflow: hidden; text-overflow: ellipsis }
.hc-cat-tag { flex-shrink: 0 }

.hc-divider { height: 1px; background: rgba(255,255,255,0.06); margin: 12px 0 }

.hc-meta { display: flex; flex-direction: column; gap: 6px }
.hc-meta-row { display: flex; align-items: center; gap: 4px; font-size: 13px; color: var(--text-secondary,#666) }
.hc-meta-label { color: var(--text-muted,#999); white-space: nowrap }
.hc-meta-sep { color: rgba(255,255,255,0.15); margin: 0 6px }
.hc-func-row { overflow: hidden }
.hc-func-text { overflow: hidden; text-overflow: ellipsis; white-space: nowrap }

.hc-footer { display: flex; justify-content: space-between; align-items: center }
.hc-stats { display: flex; gap: 16px }
.hc-stat { font-size: 13px; color: var(--text-secondary,#666) }
.hc-stat strong { color: var(--text-color,#333); font-size: 16px; margin-right: 2px }

.pagination-wrapper { display: flex; justify-content: center; margin-top: 40px }
.pagination-wrapper :deep(.el-pagination) { background: var(--card-bg,#fff); padding: 16px 24px; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08) }
</style>