<template>
  <div class="prediction-container">
    <!-- 左侧控制区 -->
    <div class="control-panel">
      <div class="panel-header">
        <h2 class="panel-title">入血预测</h2>
        <p class="panel-desc">化合物入血概率预测</p>
      </div>

      <!-- 功能标签页：仅 2 个 -->
      <el-tabs v-model="activeTab" class="predict-tabs">
        <!-- ===== 选项卡 1：单化合物精准预测 ===== -->
        <el-tab-pane label="单化合物精准预测" name="single">
          <el-card class="form-card" shadow="never">
            <el-form :model="form" label-position="top" class="predict-form">
              <!-- 模型选择 -->
              <el-form-item label="预测模型">
                <el-radio-group v-model="form.model" class="model-radio-group">
                  <el-radio value="CCTCM">
                    <span class="model-option">
                      <span>CCTCM 2.0 高维模型</span>
                      <el-tag size="small" type="success" effect="dark" class="rec-tag">推荐</el-tag>
                    </span>
                  </el-radio>
                  <el-radio value="HERB">
                    <span class="model-option">HERB 2.0 基础模型</span>
                  </el-radio>
                </el-radio-group>
              </el-form-item>

              <!-- SMILES 输入（唯一入口） -->
              <el-form-item label="SMILES 结构式">
                <el-input
                  v-model="form.smiles"
                  placeholder="请粘贴或输入 SMILES 结构式，如 CC(=O)OC1=CC=CC=C1C(=O)O"
                  clearable
                  class="full-width"
                  type="textarea"
                  :rows="2"
                  @keydown.ctrl.enter="runSmilesPrediction"
                />
              </el-form-item>

              <!-- 化合物名称（可选） -->
              <el-form-item label="化合物名称（可选）">
                <el-input
                  v-model="form.compoundName"
                  placeholder="如：阿司匹林"
                  clearable
                  class="full-width"
                />
              </el-form-item>

              <!-- ADME 实验值校准（可选折叠） -->
              <div class="adme-accordion" v-if="activeTab === 'single'">
                <el-collapse v-model="admeActiveNames" class="dark-collapse">
                  <el-collapse-item name="adme">
                    <template #title>
                      <span class="collapse-title">⚙️ ADME 实验值校准（可选）</span>
                      <span class="collapse-hint">留空由算法自动推算</span>
                    </template>
                    <div class="adme-grid">
                      <div class="adme-field" v-for="f in admeFields" :key="f.key">
                        <label class="adme-label">{{ f.label }} <span class="adme-unit">{{ f.unit }}</span></label>
                        <el-input
                          v-if="f.type === 'input'"
                          v-model="admeValues[f.key]"
                          :placeholder="f.placeholder"
                          size="small"
                          clearable
                        />
                        <el-select
                          v-if="f.type === 'select'"
                          v-model="admeValues[f.key]"
                          placeholder="未知"
                          size="small"
                          clearable
                        >
                          <el-option v-for="o in f.options" :key="o.value" :label="o.label" :value="o.value" />
                        </el-select>
                      </div>
                    </div>
                  </el-collapse-item>
                </el-collapse>
              </div>

              <!-- 预测按钮 -->
              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  class="predict-btn"
                  :loading="predicting"
                  @click="runSmilesPrediction"
                >
                  <el-icon v-if="!predicting"><MagicStick /></el-icon>
                  {{ predicting ? (form.model === 'CCTCM' ? '预测中...' : '预测中...') : '发起预测' }}
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-tab-pane>

        <!-- ===== 选项卡 2：批量文件预测 ===== -->
        <el-tab-pane label="批量文件预测 (.xlsx/.csv)" name="batch">
          <el-card class="form-card" shadow="never">
            <el-form label-position="top">
              <el-form-item label="预测模型">
                <el-radio-group v-model="batchForm.model">
                  <el-radio value="CCTCM">CCTCM 2.0</el-radio>
                  <el-radio value="HERB">HERB 2.0</el-radio>
                </el-radio-group>
              </el-form-item>

              <el-form-item label="上传文件">
                <el-upload
                  ref="uploadRef"
                  drag
                  :auto-upload="false"
                  :limit="1"
                  accept=".csv,.xlsx,.xls"
                  :on-change="handleFileChange"
                  :on-exceed="handleExceed"
                >
                  <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                  <div class="el-upload__text">拖拽文件到此处 或 <em>点击上传</em></div>
                  <template #tip>
                    <div class="upload-tip">
                      支持 .xlsx / .csv 格式，文件须包含 <strong>SMILES</strong> 列
                      <el-button text type="primary" size="small" @click.stop="showFormatDialog = true">查看格式规范</el-button>
                    </div>
                  </template>
                </el-upload>
              </el-form-item>

              <!-- 预览 -->
              <div v-if="batchPreview.length > 0" class="preview-section">
                <span class="section-label">数据预览（前 {{ batchPreview.length }} 行）</span>
                <el-table :data="batchPreview" size="small" border stripe max-height="200" class="preview-table">
                  <el-table-column v-for="col in batchPreviewCols" :key="col" :prop="col" :label="col" show-overflow-tooltip />
                </el-table>
              </div>

              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  class="predict-btn"
                  :loading="batchPredicting"
                  :disabled="!batchFile"
                  @click="runBatchPrediction"
                >
                  <el-icon v-if="!batchPredicting"><Upload /></el-icon>
                  {{ batchPredicting ? '批量预测中...' : '开始批量预测' }}
                </el-button>
              </el-form-item>

              <!-- 进度 -->
              <div v-if="batchProgress.total > 0" class="batch-progress">
                <el-progress :percentage="Math.round(batchProgress.done / batchProgress.total * 100)" :status="batchProgress.done === batchProgress.total ? 'success' : ''" />
                <span class="progress-text">{{ batchProgress.done }} / {{ batchProgress.total }}</span>
              </div>

              <!-- 结果 -->
              <div v-if="batchResult" class="batch-result-section">
                <el-divider />
                <div class="batch-summary">
                  <el-tag type="success">成功 {{ batchResult.success }}</el-tag>
                  <el-tag v-if="batchResult.failed > 0" type="danger">失败 {{ batchResult.failed }}</el-tag>
                  <el-tag type="info">共 {{ batchResult.total }}</el-tag>
                </div>
                <div class="download-buttons" v-if="batchResult.download_filename_xlsx">
                  <el-button type="success" @click="downloadResult(batchResult.download_filename_xlsx)">
                    <el-icon><Download /></el-icon> 下载 Excel
                  </el-button>
                  <el-button @click="downloadResult(batchResult.download_filename_csv)">
                    <el-icon><Download /></el-icon> 下载 CSV
                  </el-button>
                </div>
                <el-table v-if="batchResult.preview && batchResult.preview.length > 0" :data="batchResult.preview" size="small" border stripe max-height="300" class="result-table">
                  <el-table-column prop="compound_name" label="名称" width="120" show-overflow-tooltip />
                  <el-table-column prop="smiles" label="SMILES" show-overflow-tooltip />
                  <el-table-column prop="probability" label="入血概率" width="100">
                    <template #default="{ row }">
                      <span :style="{ color: getProbabilityColor(row.probability) }">{{ (row.probability * 100).toFixed(1) }}%</span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="level" label="等级" width="60" />
                  <el-table-column prop="mw" label="分子量" width="80" />
                </el-table>
              </div>
            </el-form>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 右侧渲染区 -->
    <div class="render-panel">
      <!-- 预测结果概览 -->
      <div class="render-header" v-if="predictionResult">
        <div class="result-info">
          <span class="result-label">预测入血概率：</span>
          <span class="result-value" :style="{ color: getProbabilityColor(predictionResult.probability) }">
            {{ (predictionResult.probability * 100).toFixed(1) }}%
          </span>
          <el-tag :type="predictionResult.model_name === 'cctcm' ? 'success' : 'primary'" size="small" effect="dark">
            {{ predictionResult.model_name === 'cctcm' ? 'CCTCM 2.0' : 'HERB 2.0' }}
          </el-tag>
          <el-tag :type="getLevelTagType(predictionResult.level)" size="small" effect="plain">
            {{ predictionResult.level }}
          </el-tag>
          <span v-if="predictionResult.mw" class="result-mw">MW: {{ predictionResult.mw }}</span>
        </div>
        <el-button text @click="showFeatureDrawer = true">
          完整特征矩阵 ({{ totalFeatureCount }}项) <el-icon><ArrowLeft /></el-icon>
        </el-button>
      </div>

      <!-- CCTCM 专用：ADME 估算误差提示 -->
      <div v-if="predictionResult && form.model === 'CCTCM' && !calibrating" class="adme-warning-banner">
        <el-popover placement="bottom" :width="440" trigger="click">
          <template #reference>
            <span class="adme-warning-trigger">
              <el-icon class="warning-icon"><WarningFilled /></el-icon>
              7 项 ADME 特征由系统基于 SMILES 推算
              <el-tag size="small" type="warning" effect="plain">估算误差约 10%-15%</el-tag>
              <el-icon class="info-icon"><InfoFilled /></el-icon>
            </span>
          </template>
          <div class="adme-popover-content">
            <h4>关于 ADME 特征估算</h4>
            <p>以下 7 项 ADME/药代动力学特征为系统通过算法估算：</p>
            <ul>
              <li>LogS（溶解度）</li>
              <li>LogD（分布系数）</li>
              <li>P-糖蛋白抑制剂/底物</li>
              <li>20% 吸收分数</li>
              <li>Caco-2 渗透性</li>
              <li>MDCK 渗透性</li>
            </ul>
            <p>估算值可能存在 <strong>10%~15%</strong> 的偏差。</p>
            <p>如果您拥有上述指标的体外实验或权威测定数据，请点击下方 <strong>「校准 ADME 参数」</strong> 填入真实值，以获得更精准的预测。</p>
          </div>
        </el-popover>
      </div>

      <!-- CCTCM 专用：已校准提示 -->
      <div v-if="predictionResult && form.model === 'CCTCM' && !predictionResult.adme_estimated" class="adme-calibrated-banner">
        <el-icon class="calibrated-icon"><SuccessFilled /></el-icon>
        ADME 特征已使用实验值校准
      </div>

      <!-- 核心特征展示区 -->
      <div v-if="predictionResult" class="features-section">
        <!-- CCTCM：分两栏展示 -->
        <template v-if="form.model === 'CCTCM'">
          <div class="feature-columns">
            <!-- 左栏：RDKit 拓扑特征（只读） -->
            <div class="feature-column rdkit-column">
              <div class="column-header">
                <span class="column-title">RDKit 拓扑特征</span>
                <el-tag size="small" type="info" effect="plain">11 项 · 精确计算</el-tag>
              </div>
              <div class="column-body">
                <div v-for="(val, key) in rdkitTopoList" :key="key" class="feature-item rdkit-item">
                  <span class="fi-label">{{ getFeatureLabel(key) }}</span>
                  <span class="fi-value">{{ formatValue(val) }}</span>
                </div>
              </div>
            </div>

            <!-- 右栏：ADME 特征（可校准） -->
            <div class="feature-column adme-column">
              <div class="column-header">
                <span class="column-title">ADME / 药代动力学特征</span>
                <div class="column-header-right">
                  <el-tag size="small" :type="calibrating ? 'warning' : 'info'" effect="plain">
                    {{ calibrating ? '编辑中' : '7 项 · 算法推算' }}
                  </el-tag>
                  <el-button
                    v-if="!calibrating"
                    text
                    type="warning"
                    size="small"
                    @click="startCalibrate"
                  >
                    <el-icon><EditPen /></el-icon> 校准 ADME 参数
                  </el-button>
                  <el-button
                    v-if="calibrating"
                    text
                    type="info"
                    size="small"
                    @click="cancelCalibrate"
                  >
                    恢复推算值
                  </el-button>
                </div>
              </div>
              <div class="column-body">
                <div v-for="(val, key) in admeList" :key="key" class="feature-item" :class="{ 'adme-editable': calibrating }">
                  <span class="fi-label">{{ getFeatureLabel(key) }}</span>
                  <el-input-number
                    v-if="calibrating"
                    v-model="calibrateValues[key]"
                    :precision="4"
                    :step="0.1"
                    size="small"
                    controls-position="right"
                    class="adme-input"
                  />
                  <span v-else class="fi-value">{{ formatValue(val) }}</span>
                </div>
              </div>
              <!-- 重新计算按钮 -->
              <div v-if="calibrating" class="recalc-section">
                <el-button type="warning" :loading="recalculating" @click="recalculateWithCalibration">
                  <el-icon><Refresh /></el-icon>
                  {{ recalculating ? '重新计算中...' : '使用校准值重新计算' }}
                </el-button>
              </div>
            </div>
          </div>
        </template>

        <!-- HERB：简单展示 -->
        <template v-else>
          <div class="herb-features">
            <div class="core-features">
              <div v-for="f in coreFeatureList" :key="f.name" class="core-feature-card">
                <span class="feature-label">{{ f.label }}</span>
                <span class="feature-value">{{ f.value != null ? f.value : '—' }}<small v-if="f.unit"> {{ f.unit }}</small></span>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- 网络图 -->
      <div class="network-wrapper" v-loading="predicting || recalculating" element-loading-text="正在分析...">
        <div ref="networkContainer" class="network-container"></div>
        <!-- 空状态：功能特色三卡片 -->
        <div class="network-empty" v-if="!predictionResult && !predicting && !recalculating">
          <div class="empty-welcome">
            <el-icon class="empty-main-icon"><DataAnalysis /></el-icon>
            <p class="empty-title">入血预测</p>
            <p class="empty-subtitle">输入 SMILES 结构式，获取预测结果</p>
          </div>
          <div class="empty-feature-cards">
            <div class="empty-feature-card">
              <el-icon class="efc-icon" style="color:#409eff"><MagicStick /></el-icon>
              <span class="efc-title">SMILES 结构解析</span>
              <span class="efc-desc">RDKit 计算 11 项拓扑特征</span>
            </div>
            <div class="empty-feature-card">
              <el-icon class="efc-icon" style="color:#67c23a"><Cpu /></el-icon>
              <span class="efc-title">CCTCM 2.0 模型预测</span>
              <span class="efc-desc">PU 学习模型，含 7 项 ADME 特征</span>
            </div>
            <div class="empty-feature-card">
              <el-icon class="efc-icon" style="color:#e6a23c"><Download /></el-icon>
              <span class="efc-title">结果导出</span>
              <span class="efc-desc">支持 .xlsx/.csv 批量预测</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 清空结果按钮 -->
      <el-button v-if="predictionResult" class="clear-btn" type="info" circle size="small" @click="clearResult" title="清空结果">
        <el-icon><Delete /></el-icon>
      </el-button>
      <!-- 历史记录按钮 -->
      <el-button class="history-btn" type="primary" circle @click="showHistoryDrawer = true">
        <el-icon><Clock /></el-icon>
      </el-button>
    </div>

    <!-- ===== 完整特征矩阵抽屉 ===== -->
    <el-drawer v-model="showFeatureDrawer" title="完整特征矩阵（19 项）" direction="rtl" size="450px">
      <el-table :data="allFeaturesTableData" border stripe size="small">
        <el-table-column prop="label" label="特征名" />
        <el-table-column prop="value" label="计算值">
          <template #default="{ row }">
            <span v-if="row.value == null" class="na-value">NaN（中位数填补）</span>
            <span v-else>{{ row.value }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="unit" label="单位" width="80" />
      </el-table>
    </el-drawer>

    <!-- ===== 历史记录侧边栏 ===== -->
    <el-drawer v-model="showHistoryDrawer" title="预测历史记录" direction="rtl" size="420px">
      <div class="history-toolbar">
        <el-input v-model="historySearch" placeholder="搜索化合物名/SMILES" clearable size="small" class="history-search" />
        <el-button type="danger" text size="small" @click="clearHistory">清空</el-button>
      </div>
      <div class="history-list">
        <div v-for="record in filteredHistory" :key="record.id" class="history-card">
          <!-- 顶部：时间 + 等级标签 + 操作 -->
          <div class="history-card-head">
            <span class="hch-time">{{ formatTime(record.timestamp) }}</span>
            <el-tag :type="getLevelTagType(record.level)" size="small" effect="dark" class="hch-level">
              {{ record.level === '高' ? '高概率入血' : record.level === '中' ? '中等概率' : '低概率' }}
            </el-tag>
          </div>
          <!-- 中部：化合物名称 + SMILES 截断 -->
          <div class="history-card-body">
            <span class="hcb-name" :title="record.compound_name || record.smiles">
              化合物：{{ record.compound_name || '未命名' }}
            </span>
            <span class="hcb-smiles" :title="record.smiles">SMILES: {{ record.smiles }}</span>
          </div>
          <!-- 底部：概率 + MW + LogP -->
          <div class="history-card-stats">
            <span class="hcs-item">
              预测概率: <strong :style="{ color: getProbabilityColor(record.probability) }">{{ (record.probability * 100).toFixed(1) }}%</strong>
            </span>
            <span class="hcs-item" v-if="record.mw">| MW: {{ record.mw }}</span>
            <span class="hcs-item" v-if="record.logp != null">| LogP: {{ record.logp }}</span>
          </div>
          <!-- 底部：操作按钮 -->
          <div class="history-card-actions">
            <el-button text type="primary" size="small" @click.stop="restoreHistory(record)">
              <el-icon><RefreshLeft /></el-icon> 回填到预测框
            </el-button>
            <el-button text type="info" size="small" @click.stop="previewHistoryDetail(record)">
              <el-icon><View /></el-icon> 查看特征明细
            </el-button>
            <el-button text type="danger" size="small" @click.stop="deleteHistoryRecord(record.id)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </div>
        </div>
        <div v-if="filteredHistory.length === 0" class="history-empty">
          <el-icon style="font-size:40px;color:var(--text-muted);margin-bottom:12px"><FolderOpened /></el-icon>
          <p>暂无预测历史记录</p>
        </div>
      </div>
    </el-drawer>

    <!-- ===== 格式规范弹窗（暗色主题） ===== -->
    <el-dialog v-model="showFormatDialog" title="批量预测文件格式规范" width="540px" class="dark-dialog">
      <div class="format-guide">
        <h4>📄 文件要求</h4>
        <ul>
          <li>格式：<strong>.xlsx</strong> 或 <strong>.csv</strong></li>
          <li>必须包含名为 <strong>SMILES</strong> 的列（不区分大小写）</li>
          <li>可选列：<strong>化合物名称</strong>（Name / Compound / 名称 均可）</li>
        </ul>
        <h4>⚙️ 高级模式（可选 ADME 列）</h4>
        <p style="color:var(--text-secondary);font-size:13px">除 <strong>SMILES</strong> 外，支持以下<em>可选列</em>——<strong>有值则使用实验值，无值或留空则由算法自动推算</strong>：</p>
        <ul>
          <li><strong>LogS</strong> — 水溶解度 (log mol/L)</li>
          <li><strong>LogD</strong> — 分布系数 (pH 7.4)</li>
          <li><strong>LogP</strong> — 脂水分配系数</li>
          <li><strong>Caco2</strong> — Caco-2 渗透性 (cm/s)</li>
          <li><strong>MDCK</strong> — MDCK 渗透性 (cm/s)</li>
          <li><strong>F20</strong> — 20% 吸收分数 (%)</li>
          <li><strong>Pgp</strong> — P-gp 底物/抑制剂 (unknown/substrate/inhibitor/both)</li>
        </ul>
        <h4>📋 CSV 示例</h4>
        <pre class="format-example">SMILES,化合物名称,LogS,Caco2
CC(=O)OC1=CC=CC=C1C(=O)O,阿司匹林,-2.15,-4.85
CC(C)CC1=CC=C(C=C1)C(C)C(=O)O,布洛芬,,
CCN(CC)CC(=O)NC1=C(C=CC=C1)C,利多卡因,,</pre>
        <h4>📤 输出结果</h4>
        <p>结果文件将在原表基础上追加以下列：</p>
        <ul style="column-count:2;column-gap:20px">
          <li>RDKit拓扑特征(11项)</li>
          <li>ADME特征(7项，标注推算/实验)</li>
          <li>CCTCM 2.0 入血概率(%)</li>
          <li>预测等级(高/中/低)</li>
        </ul>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onUnmounted, nextTick, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  DataAnalysis, MagicStick, UploadFilled, Upload, Download,
  ArrowLeft, Clock, WarningFilled, InfoFilled, SuccessFilled,
  EditPen, Refresh, Cpu, RefreshLeft, View, FolderOpened, Delete
} from '@element-plus/icons-vue'
import cytoscape from 'cytoscape'
import { getHighPotentialCompounds, getCompoundTargets, getPredictionModels, predictBySmiles, uploadAndPredict, downloadBatchResult } from '../api'
import { usePredictionHistory } from '../composables/usePredictionHistory'

const networkContainer = ref(null)
let cyInstance = null
const predicting = ref(false)
const recalculating = ref(false)
const predictionResult = ref(null)
const activeTab = ref('single')

// 校准状态
const calibrating = ref(false)
const calibrateValues = reactive({})
const originalAdmeValues = ref({})

// ADME 实验值输入（预测前填写）
const admeActiveNames = ref([])  // 默认折叠
const admeValues = reactive({
  LogS: '', LogD: '', LogP: '', caco2: '', mdck: '', f20: '', pgp: ''
})
const admeFields = [
  { key: 'LogS', label: '水溶解度 LogS', unit: 'log mol/L', type: 'input', placeholder: '如 -2.15' },
  { key: 'LogD', label: '分布系数 LogD', unit: '(pH 7.4)', type: 'input', placeholder: '如 1.35' },
  { key: 'LogP', label: '脂水分配 LogP', unit: '', type: 'input', placeholder: '如 0.85' },
  { key: 'caco2', label: 'Caco-2 渗透性', unit: 'cm/s', type: 'input', placeholder: '如 -5.2e-6' },
  { key: 'mdck', label: 'MDCK 渗透性', unit: 'cm/s', type: 'input', placeholder: '如 -4.8e-6' },
  { key: 'f20', label: '20% 吸收分数 F(20%)', unit: '%', type: 'input', placeholder: '如 36' },
  { key: 'pgp', label: 'P-gp 底物/抑制剂', unit: '', type: 'select', options: [
    { label: '未知', value: 'unknown' },
    { label: '底物', value: 'substrate' },
    { label: '抑制剂', value: 'inhibitor' },
    { label: '两者皆是', value: 'both' }
  ] }
]

const form = reactive({
  model: 'CCTCM',
  smiles: '',
  compoundName: ''
})

// 批量预测
const batchForm = reactive({ model: 'CCTCM' })
const batchFile = ref(null)
const batchPreview = ref([])
const batchPreviewCols = ref([])
const batchPredicting = ref(false)
const batchResult = ref(null)
const batchProgress = reactive({ total: 0, done: 0 })
const showFormatDialog = ref(false)
const uploadRef = ref(null)

// 特征抽屉
const showFeatureDrawer = ref(false)

// 历史
const showHistoryDrawer = ref(false)
const historySearch = ref('')
const { history, saveRecord, getRecords, deleteRecord, clearAll } = usePredictionHistory()

const filteredHistory = computed(() => getRecords(historySearch.value))

const totalFeatureCount = computed(() => {
  if (!predictionResult.value) return 0
  return Object.keys(predictionResult.value.features_computed || {}).length
})

// 从预测结果中提取 RDKit 拓扑特征列表
const rdkitTopoList = computed(() => {
  if (!predictionResult.value || !predictionResult.value.rdkit_topology_features) return []
  return predictionResult.value.rdkit_topology_features
})

// 从预测结果中提取 ADME 特征列表
const admeList = computed(() => {
  if (!predictionResult.value || !predictionResult.value.adme_features) return []
  return predictionResult.value.adme_features
})

// HERB 核心特征
const coreFeatureList = computed(() => {
  if (!predictionResult.value || !predictionResult.value.core_features) return []
  return predictionResult.value.core_features
})

// 完整特征矩阵表格数据
const allFeaturesTableData = computed(() => {
  if (!predictionResult.value || !predictionResult.value.features_computed) return []
  const labels = {
    'LogS': 'LogS（溶解度）', 'LogD': 'LogD（分布系数）', 'LogP': 'LogP（脂水分配系数）',
    'Pgp-inhibitor': 'P-糖蛋白抑制剂', 'Pgp-substrate': 'P-糖蛋白底物',
    'F(20%)': '20%吸收分数', 'Caco-2 Permeability': 'Caco-2 渗透性',
    'MDCK Permeability (cm/s)': 'MDCK 渗透性',
    'Num. H-bond acceptors': '氢键受体数', 'Num. H-bond donors': '氢键供体数',
    'TPSA': '拓扑极性表面积', 'Num. Rotatable bonds': '可旋转键数',
    'Num. Rings': '环数', 'MaxRing': '最大环大小', 'nHet': '杂原子数',
    'fChar': '形式电荷', 'nRig': '刚性键数', 'Flex': '柔韧性', 'nStereo': '立体中心数'
  }
  const units = {
    'LogS': 'log mol/L', 'LogD': 'pH7.4', 'TPSA': 'Å²',
    'Caco-2 Permeability': 'cm/s', 'MDCK Permeability (cm/s)': 'cm/s', 'F(20%)': '%'
  }
  return Object.entries(predictionResult.value.features_computed).map(([key, val]) => ({
    label: labels[key] || key,
    value: val,
    unit: units[key] || ''
  }))
})

// ===== 特征中文标签映射 =====
const FEATURE_LABELS = {
  'LogS': 'LogS（溶解度）',
  'LogD': 'LogD（分布系数）',
  'LogP': 'LogP（脂水分配系数）',
  'Pgp-inhibitor': 'P-糖蛋白抑制剂',
  'Pgp-substrate': 'P-糖蛋白底物',
  'F(20%)': '20%吸收分数',
  'Caco-2 Permeability': 'Caco-2 渗透性',
  'MDCK Permeability (cm/s)': 'MDCK 渗透性',
  'Num. H-bond acceptors': '氢键受体数',
  'Num. H-bond donors': '氢键供体数',
  'TPSA': '拓扑极性表面积',
  'Num. Rotatable bonds': '可旋转键数',
  'Num. Rings': '环数',
  'MaxRing': '最大环大小',
  'nHet': '杂原子数',
  'fChar': '形式电荷',
  'nRig': '刚性键数',
  'Flex': '柔韧性',
  'nStereo': '立体中心数'
}

function getFeatureLabel(key) {
  return FEATURE_LABELS[key] || key
}

function formatValue(val) {
  if (val == null) return '—'
  if (typeof val === 'number') {
    if (Math.abs(val) >= 1000) return val.toFixed(0)
    if (Math.abs(val) >= 1) return val.toFixed(2)
    return val.toExponential(2)
  }
  return val
}

// ===== 工具函数 =====
function getProbabilityColor(prob) {
  if (prob >= 0.7) return '#67c23a'
  if (prob >= 0.5) return '#e6a23c'
  return '#f56c6c'
}

function getLevelTagType(level) {
  if (level === '高') return 'danger'
  if (level === '中') return 'warning'
  return 'info'
}

function formatTime(iso) {
  const d = new Date(iso)
  return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`
}

// ===== SMILES 预测（统一入口） =====
async function runSmilesPrediction() {
  if (!form.smiles || !form.smiles.trim()) {
    ElMessage.warning('请输入 SMILES 结构式')
    return
  }

  predicting.value = true
  predictionResult.value = null
  calibrating.value = false

  try {
    // 构建 ADME 覆盖值（只发送非空的实验值）
    const admePayload = {}
    for (const [key, val] of Object.entries(admeValues)) {
      if (val != null && val !== '' && val !== undefined) {
        admePayload[key] = key === 'pgp' ? val : Number(val)
      }
    }

    const res = await predictBySmiles({
      smiles: form.smiles.trim(),
      model_name: form.model.toLowerCase(),
      compound_name: form.compoundName || null,
      ...(Object.keys(admePayload).length > 0 ? { adme_overrides: admePayload } : {})
    })

    const data = res.data || res
    predictionResult.value = data

    // 保存原始 ADME 值用于校准
    if (data.adme_features) {
      originalAdmeValues.value = { ...data.adme_features }
      // 初始化校准值
      Object.keys(data.adme_features).forEach(k => {
        calibrateValues[k] = data.adme_features[k]
      })
    }

    // 保存历史
    saveRecord({
      smiles: form.smiles.trim(),
      compound_name: data.compound_name || form.compoundName || form.smiles.trim().substring(0, 30) + '...',
      model_name: data.model_name,
      probability: data.probability,
      level: data.level,
      mw: data.mw,
      logp: data.features_computed ? data.features_computed.LogP : null,
      features_computed: data.features_computed,
      core_features: data.core_features,
      rdkit_topology_features: data.rdkit_topology_features,
      adme_features: data.adme_features,
      adme_estimated: data.adme_estimated
    })

    // 渲染网络图
    await nextTick()
    renderNetwork(data.compound_name || form.compoundName || 'Unknown', data.probability)

    ElMessage.success(`预测完成！入血概率 ${(data.probability * 100).toFixed(1)}%`)
  } catch (e) {
    console.error('SMILES prediction failed:', e)
    ElMessage.error(e.message || '预测失败，请检查 SMILES 格式')
  } finally {
    predicting.value = false
  }
}

// ===== ADME 校准 =====
function startCalibrate() {
  calibrating.value = true
}

function cancelCalibrate() {
  calibrating.value = false
  // 恢复原始值
  if (originalAdmeValues.value) {
    Object.keys(originalAdmeValues.value).forEach(k => {
      calibrateValues[k] = originalAdmeValues.value[k]
    })
  }
}

async function recalculateWithCalibration() {
  if (!form.smiles) return

  recalculating.value = true

  // 构建 ADME 覆盖值（只发送非空值）
  const overrides = {}
  for (const [key, val] of Object.entries(calibrateValues)) {
    if (val != null && val !== '') {
      overrides[key] = Number(val)
    }
  }

  if (Object.keys(overrides).length === 0) {
    ElMessage.warning('请至少填入一个校准值')
    recalculating.value = false
    return
  }

  try {
    const res = await predictBySmiles({
      smiles: form.smiles.trim(),
      model_name: form.model.toLowerCase(),
      compound_name: form.compoundName || null,
      adme_overrides: overrides
    })

    const data = res.data || res
    predictionResult.value = data

    // 更新校准值
    if (data.adme_features) {
      Object.keys(data.adme_features).forEach(k => {
        calibrateValues[k] = data.adme_features[k]
      })
    }

    await nextTick()
    renderNetwork(data.compound_name || form.compoundName || 'Unknown', data.probability)

    ElMessage.success(`校准后重新计算完成！入血概率 ${(data.probability * 100).toFixed(1)}%`)
  } catch (e) {
    console.error('Calibration failed:', e)
    ElMessage.error(e.message || '校准预测失败，请重试')
  } finally {
    recalculating.value = false
  }
}

// ===== 批量预测 =====
function handleFileChange(file) {
  batchFile.value = file.raw
  parsePreview(file.raw)
}

function handleExceed() {
  ElMessage.warning('只能上传一个文件，请先移除已有文件')
}

async function parsePreview(file) {
  try {
    const XLSX = await import('xlsx')
    const data = await file.arrayBuffer()
    const wb = XLSX.read(data)
    const ws = wb.Sheets[wb.SheetNames[0]]
    const json = XLSX.utils.sheet_to_json(ws, { header: 1 })
    if (json.length > 0) {
      const headers = json[0]
      batchPreviewCols.value = headers.map(h => String(h))
      batchPreview.value = json.slice(1, 11).map(row => {
        const obj = {}
        headers.forEach((h, i) => { obj[String(h)] = row[i] })
        return obj
      })
    }
  } catch (e) {
    console.error('Preview parse failed:', e)
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target.result
      const lines = text.split('\n').filter(l => l.trim())
      if (lines.length > 0) {
        const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''))
        batchPreviewCols.value = headers
        batchPreview.value = lines.slice(1, 11).map(line => {
          const vals = line.split(',')
          const obj = {}
          headers.forEach((h, i) => { obj[h] = vals[i]?.trim().replace(/^"|"$/g, '') })
          return obj
        })
      }
    }
    reader.readAsText(file)
  }
}

async function runBatchPrediction() {
  if (!batchFile.value) {
    ElMessage.warning('请先上传文件')
    return
  }

  batchPredicting.value = true
  batchResult.value = null
  batchProgress.total = 0
  batchProgress.done = 0

  try {
    const formData = new FormData()
    formData.append('file', batchFile.value)
    const res = await uploadAndPredict(formData, batchForm.model.toLowerCase())
    const data = res.data || res
    batchResult.value = data
    batchProgress.total = data.total
    batchProgress.done = data.success + data.failed
    ElMessage.success(`批量预测完成！成功 ${data.success} 条`)
  } catch (e) {
    console.error('Batch prediction failed:', e)
    ElMessage.error(e.message || '批量预测失败')
  } finally {
    batchPredicting.value = false
  }
}

function downloadResult(filename) {
  const url = downloadBatchResult(filename)
  window.open(url, '_blank')
}

// ===== 网络图渲染 =====
function renderNetwork(compoundName, probability) {
  if (cyInstance) { cyInstance.destroy(); cyInstance = null }

  const elements = {
    nodes: [{
      data: { id: 'compound', label: compoundName, category: 'compound', prob: Math.round(probability * 100) }
    }],
    edges: []
  }

  cyInstance = cytoscape({
    container: networkContainer.value,
    elements: elements,
    style: [
      {
        selector: 'node[category="compound"]',
        style: {
          'background-color': function(ele) {
            const p = ele.data('prob')
            if (p >= 70) return '#67c23a'
            if (p >= 50) return '#e6a23c'
            return '#f56c6c'
          },
          'shape': 'circle', 'width': 80, 'height': 80,
          'label': 'data(label)', 'color': '#fff',
          'text-valign': 'center', 'text-halign': 'center',
          'font-size': 12, 'font-weight': 'bold',
          'text-wrap': 'wrap', 'text-max-width': 74,
          'border-width': 3, 'border-color': '#fff'
        }
      }
    ],
    layout: { name: 'preset' }
  })
}

// ===== 历史记录操作 =====
function restoreHistory(record) {
  form.smiles = record.smiles
  form.compoundName = record.compound_name || ''
  form.model = (record.model_name || 'cctcm').toUpperCase()
  predictionResult.value = record
  calibrating.value = false
  if (record.adme_features) {
    originalAdmeValues.value = { ...record.adme_features }
    Object.keys(record.adme_features).forEach(k => {
      calibrateValues[k] = record.adme_features[k]
    })
  }
  showHistoryDrawer.value = false
  activeTab.value = 'single'
  nextTick(() => renderNetwork(record.compound_name || 'Unknown', record.probability))
  ElMessage.success('已恢复历史预测记录')
}

function deleteHistoryRecord(id) {
  deleteRecord(id)
  ElMessage.success('已删除')
}

function previewHistoryDetail(record) {
  // 回填到预测框并展示特征明细
  restoreHistory(record)
  showFeatureDrawer.value = true
}

function clearHistory() {
  clearAll()
  ElMessage.success('历史记录已清空')
}

function clearResult() {
  predictionResult.value = null
  recalibrated.value = false
  calibrating.value = false
  originalAdmeValues.value = {}
  calibrateValues.value = {}
  form.smiles = ''
  form.compoundName = ''
  if (cyInstance) { cyInstance.destroy(); cyInstance = null }
  ElMessage.success('结果已清空')
}

onUnmounted(() => {
  if (cyInstance) { cyInstance.destroy(); cyInstance = null }
})
</script>

<style scoped>
.prediction-container {
  display: flex; height: 100vh;
  background: transparent; overflow: hidden;
}

.control-panel {
  width: 38%; min-width: 400px; max-width: 560px;
  padding: 20px; overflow-y: auto;
  border-right: 1px solid rgba(255,255,255,0.08);
  scrollbar-width: none; -ms-overflow-style: none;
}
.control-panel::-webkit-scrollbar { width: 6px }
.control-panel::-webkit-scrollbar-track { background: transparent }
.control-panel::-webkit-scrollbar-thumb { background: transparent; border-radius: 3px }
.control-panel::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.15) }

.panel-header { margin-bottom: 16px }
.panel-title { font-size: 22px; font-weight: 700; color: var(--text-color); margin: 0 0 4px 0 }
.panel-desc { font-size: 13px; color: var(--text-secondary); margin: 0 }

.predict-tabs :deep(.el-tabs__header) { margin-bottom: 16px }
.predict-tabs :deep(.el-tabs__item) { color: var(--text-secondary); font-size: 14px }
.predict-tabs :deep(.el-tabs__item.is-active) { color: var(--text-color); font-weight: 600 }

.form-card {
  border-radius: 12px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
}
.form-card :deep(.el-card__body) { padding: 20px }

.predict-form :deep(.el-form-item__label) { color: var(--text-secondary); font-size: 13px; font-weight: 500; padding-bottom: 4px }
.predict-form :deep(.el-radio__label) { color: var(--text-secondary); font-size: 13px }

.model-radio-group { display: flex; flex-direction: column; gap: 8px }
.model-option { display: flex; align-items: center; gap: 8px }
.rec-tag { font-size: 11px; padding: 0 6px; line-height: 18px }
.full-width { width: 100% }

.predict-btn { width: 100%; font-size: 16px; font-weight: 600; letter-spacing: 1px; margin-top: 8px }

/* ===== 右侧渲染区 ===== */
.render-panel { flex: 1; display: flex; flex-direction: column; position: relative; overflow: hidden }

.render-header {
  padding: 16px 24px; background: rgba(255,255,255,0.04);
  border-bottom: 1px solid rgba(255,255,255,0.08);
  display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;
}
.result-info { display: flex; align-items: center; gap: 12px; flex-wrap: wrap }
.result-label { font-size: 16px; color: var(--text-secondary) }
.result-value { font-size: 28px; font-weight: 700 }
.result-mw { font-size: 13px; color: var(--text-muted) }

/* ===== ADME 估算提示 ===== */
.adme-warning-banner {
  padding: 8px 24px;
  background: rgba(230, 162, 60, 0.08);
  border-bottom: 1px solid rgba(230, 162, 60, 0.15);
  display: flex; align-items: center;
}
.adme-warning-trigger {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; color: #e6a23c; cursor: pointer;
}
.warning-icon { font-size: 16px }
.info-icon { font-size: 14px; color: var(--text-muted) }

.adme-popover-content h4 { margin: 0 0 8px 0; color: #e6a23c }
.adme-popover-content p { font-size: 13px; color: var(--text-secondary); line-height: 1.6; margin: 8px 0 }
.adme-popover-content ul { font-size: 12px; color: var(--text-muted); padding-left: 20px; line-height: 1.8 }

.adme-calibrated-banner {
  padding: 8px 24px;
  background: rgba(103, 194, 58, 0.08);
  border-bottom: 1px solid rgba(103, 194, 58, 0.15);
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; color: #67c23a;
}
.calibrated-icon { font-size: 16px }

/* ===== 特征展示区 ===== */
.features-section {
  padding: 12px 24px;
  background: rgba(255,255,255,0.02);
  border-bottom: 1px solid rgba(255,255,255,0.06);
  max-height: 320px;
  overflow-y: auto;
}

.feature-columns {
  display: flex; gap: 16px;
}

.feature-column {
  flex: 1;
  min-width: 0;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.08);
  overflow: hidden;
}

.rdkit-column {
  background: rgba(255,255,255,0.03);
}

.adme-column {
  background: rgba(230, 162, 60, 0.03);
  border-color: rgba(230, 162, 60, 0.15);
}

.column-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  flex-wrap: wrap; gap: 4px;
}
.column-title { font-size: 13px; font-weight: 600; color: var(--text-color) }
.column-header-right { display: flex; align-items: center; gap: 6px; flex-wrap: wrap }

.column-body {
  padding: 6px 12px;
}

.feature-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 4px 0;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  gap: 8px;
}
.feature-item:last-child { border-bottom: none }

.fi-label { font-size: 12px; color: var(--text-secondary); flex-shrink: 0 }
.fi-value { font-size: 13px; font-weight: 600; color: var(--text-color); font-family: 'Courier New', monospace }

.rdkit-item .fi-label { color: rgba(255,255,255,0.5) }
.rdkit-item .fi-value { color: rgba(255,255,255,0.7) }

.adme-editable { background: rgba(230, 162, 60, 0.05); border-radius: 4px; padding: 4px 8px; margin: 2px -8px }
.adme-input { width: 140px }
.adme-input :deep(.el-input-number__decrease),
.adme-input :deep(.el-input-number__increase) { width: 20px }
.adme-input :deep(.el-input__inner) { text-align: right; font-size: 12px; height: 28px }

.recalc-section {
  padding: 10px 12px;
  border-top: 1px solid rgba(230, 162, 60, 0.15);
  display: flex; justify-content: center;
}

/* HERB 核心特征 */
.herb-features { padding: 4px 0 }
.core-features {
  display: flex; flex-wrap: wrap; gap: 12px;
}
.core-feature-card {
  display: flex; flex-direction: column; align-items: center;
  background: rgba(255,255,255,0.06); border-radius: 8px; padding: 8px 16px;
  min-width: 80px;
}
.feature-label { font-size: 11px; color: var(--text-secondary); margin-bottom: 4px }
.feature-value { font-size: 18px; font-weight: 700; color: var(--text-color) }
.feature-value small { font-size: 11px; font-weight: 400; color: var(--text-muted) }

/* 网络图 */
.network-wrapper { flex: 1; position: relative; overflow: hidden }
.network-container { width: 100%; height: 100% }

.network-empty {
  position: absolute; inset: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-align: center; padding: 40px;
}
.empty-welcome { margin-bottom: 32px }
.empty-main-icon { font-size: 56px; color: rgba(255,255,255,0.12); margin-bottom: 16px }
.empty-title { font-size: 20px; font-weight: 700; color: var(--text-color); margin: 0 0 8px 0 }
.empty-subtitle { font-size: 14px; color: var(--text-muted); margin: 0 }
.empty-feature-cards {
  display: flex; gap: 16px; flex-wrap: wrap; justify-content: center;
}
.empty-feature-card {
  display: flex; flex-direction: column; align-items: center;
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px; padding: 20px 24px; width: 180px;
  transition: border-color 0.2s, background 0.2s;
}
.empty-feature-card:hover { border-color: rgba(255,255,255,0.12); background: rgba(255,255,255,0.06) }
.efc-icon { font-size: 28px; margin-bottom: 10px }
.efc-title { font-size: 14px; font-weight: 600; color: var(--text-color); margin-bottom: 4px }
.efc-desc { font-size: 12px; color: var(--text-muted); line-height: 1.4 }

.history-btn { position: absolute; top: 16px; right: 16px; z-index: 10 }
.clear-btn { position: absolute; top: 16px; right: 56px; z-index: 10 }

.na-value { color: var(--text-muted); font-style: italic; font-size: 12px }

/* ===== 批量预测暗色主题 ===== */
:deep(.el-upload-dragger) {
  background: rgba(30,41,59,0.6) !important;
  border: 2px dashed rgba(148,163,184,0.3) !important;
  border-radius: 10px;
}
:deep(.el-upload-dragger:hover) { border-color: rgba(148,163,184,0.5) !important }
:deep(.el-upload__text) { color: var(--text-secondary) !important }
:deep(.el-upload__text em) { color: var(--text-color); font-style: normal }

.preview-section { margin: 12px 0 }
.preview-table { margin-top: 8px }
.upload-tip { font-size: 12px; color: var(--text-secondary); line-height: 1.6 }
.batch-progress { margin: 12px 0 }
.progress-text { font-size: 13px; color: var(--text-secondary); margin-left: 8px }
.batch-result-section { margin-top: 16px }
.batch-summary { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap }
.download-buttons { display: flex; gap: 8px; margin-bottom: 12px }
.result-table { margin-top: 8px }

/* ===== 历史记录 — 暗色卡片 ===== */
.history-toolbar { display: flex; gap: 8px; margin-bottom: 12px; align-items: center }
.history-search { flex: 1 }
.history-list { display: flex; flex-direction: column; gap: 10px; padding-bottom: 20px }

.history-card {
  background: rgba(30,41,59,0.5); border: 1px solid rgba(148,163,184,0.15);
  border-radius: 10px; padding: 14px;
  transition: border-color 0.2s, background 0.2s;
}
.history-card:hover { border-color: rgba(148,163,184,0.3); background: rgba(30,41,59,0.7) }

.history-card-head {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;
}
.hch-time { font-size: 12px; color: var(--text-muted) }

.history-card-body { display: flex; flex-direction: column; gap: 4px; margin-bottom: 10px }
.hcb-name { font-size: 14px; font-weight: 600; color: var(--text-color); white-space: nowrap; overflow: hidden; text-overflow: ellipsis }
.hcb-smiles {
  font-size: 11px; color: var(--text-muted); font-family: monospace;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

.history-card-stats { display: flex; flex-wrap: wrap; gap: 12px; font-size: 12px; color: var(--text-secondary); margin-bottom: 10px }
.hcs-item strong { font-weight: 700 }

.history-card-actions { display: flex; gap: 4px; flex-wrap: wrap; padding-top: 8px; border-top: 1px solid rgba(148,163,184,0.08) }

.history-empty {
  text-align: center; color: var(--text-muted); padding: 60px 0; font-size: 14px;
  display: flex; flex-direction: column; align-items: center;
}


/* 暗色 dialog */
.dark-dialog :deep(.el-dialog) {
  background: #1e293b !important;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.6);
}
.dark-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding: 20px 24px 16px;
}
.dark-dialog :deep(.el-dialog__title) {
  color: #e2e8f0 !important;
  font-weight: 700;
  font-size: 16px;
}
.dark-dialog :deep(.el-dialog__headerbtn) {
  top: 20px;
  right: 20px;
}
.dark-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #64748b !important;
  font-size: 18px;
}
.dark-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: #f1f5f9 !important;
}
.dark-dialog :deep(.el-dialog__body) {
  color: #94a3b8 !important;
  padding: 20px 24px 24px;
}

.format-guide h4 { margin: 14px 0 8px 0; color: #e2e8f0; font-size: 14px }
.format-guide h4:first-child { margin-top: 0 }
.format-guide ul { margin: 0; padding-left: 20px; color: #94a3b8; line-height: 1.8 }
.format-guide li { margin-bottom: 2px }
.format-guide p strong { color: #cbd5e1 }
.format-example {
  background: #0f172a;
  padding: 14px;
  border-radius: 8px;
  font-size: 12px;
  overflow-x: auto;
  color: #6ee7b7;
  font-family: 'SF Mono', 'Fira Code', monospace;
  border: 1px solid rgba(255, 255, 255, 0.08);
  line-height: 1.6;
  margin-top: 8px;
}

/* ADME 折叠面板 */
.adme-accordion { margin-top: 12px }
.dark-collapse {
  --el-collapse-border-color: rgba(255, 255, 255, 0.08);
  --el-collapse-header-height: 38px;
  --el-collapse-header-bg-color: rgba(255, 255, 255, 0.03);
  --el-collapse-header-text-color: var(--text-color);
  --el-collapse-header-font-size: 13px;
  --el-collapse-content-bg-color: rgba(255, 255, 255, 0.02);
  --el-collapse-content-font-size: 12px;
  --el-collapse-content-text-color: var(--text-secondary);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  overflow: hidden;
}
.dark-collapse :deep(.el-collapse-item__header) {
  padding: 0 14px;
  font-weight: 500;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.dark-collapse :deep(.el-collapse-item__content) {
  padding: 14px;
}
.dark-collapse :deep(.el-collapse-item__wrap) {
  border-bottom: none;
}
.collapse-title {
  flex: 1;
}
.collapse-hint {
  font-size: 11px;
  color: var(--text-muted);
  margin-right: 8px;
  white-space: nowrap;
}

/* ADME 2 列网格 */
.adme-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 16px;
}
.adme-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.adme-label {
  font-size: 12px;
  color: var(--text-secondary);
}
.adme-unit {
  font-size: 11px;
  color: var(--text-muted);
}
</style>