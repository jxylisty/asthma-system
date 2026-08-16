<template>
  <div class="expert-container">
    <!-- 顶部导航栏 -->
    <div class="top-bar">
      <div class="logo" @click="$router.push('/')">
        <el-icon><HomeFilled /></el-icon>
        <span>哮喘方剂智能分析系统</span>
      </div>
      <el-button type="success" class="back-btn" @click="$router.push('/detail')">
        <el-icon><Back /></el-icon>
        返回科普模式
      </el-button>
    </div>

    <!-- 模块 A：核心算法性能面板 -->
    <div class="module-a">
      <div class="card">
        <div class="card-header">
          <h2>核心算法性能面板</h2>
          <el-tag type="danger" effect="plain">PU 学习算法 vs 传统机器学习对比</el-tag>
        </div>
        <div class="charts-row">
          <!-- ROC 曲线 -->
          <div class="chart-wrapper">
            <h3>ROC 曲线 (AUC 对比)</h3>
            <div ref="rocChart" class="metric-chart"></div>
          </div>
          <!-- PR 曲线 -->
          <div class="chart-wrapper">
            <h3>PR 曲线 (AUPRC 对比)</h3>
            <div ref="prChart" class="metric-chart"></div>
          </div>
          <!-- 特征权重热力图 -->
          <div class="chart-wrapper heatmap-wrapper">
            <h3>特征权重热力图</h3>
            <div ref="heatmapChart" class="metric-chart"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 模块 B：高维靶点拓扑网络 -->
    <div class="module-b card">
      <div class="card-header">
        <h2>高维靶点拓扑网络</h2>
        <div class="header-actions">
          <el-tooltip content="点击任意节点高亮其一阶邻居" placement="top">
            <el-tag type="info" effect="plain">
              <el-icon><InfoFilled /></el-icon>
              交互提示
            </el-tag>
          </el-tooltip>
          <el-button type="primary" size="small" @click="exportNetwork">
            <el-icon><Download /></el-icon>
            一键导出 PNG
          </el-button>
        </div>
      </div>
      <div ref="networkContainer" class="network-container"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import cytoscape from 'cytoscape'
import { HomeFilled, Back, InfoFilled, Download } from '@element-plus/icons-vue'

const rocChart = ref(null)
const prChart = ref(null)
const heatmapChart = ref(null)
const networkContainer = ref(null)

let cyInstance = null

// ROC 曲线数据 - PU学习 vs SVM
const rocDataPU = [
  [0, 0], [0.05, 0.45], [0.1, 0.72], [0.15, 0.85], [0.2, 0.9],
  [0.3, 0.94], [0.4, 0.96], [0.5, 0.97], [0.6, 0.98], [0.8, 0.99], [1, 1]
]
const rocDataSVM = [
  [0, 0], [0.1, 0.25], [0.2, 0.4], [0.3, 0.52], [0.4, 0.62],
  [0.5, 0.7], [0.6, 0.76], [0.7, 0.82], [0.8, 0.88], [0.9, 0.94], [1, 1]
]

// PR 曲线数据
const prDataPU = [
  [1, 0.92], [0.95, 0.94], [0.9, 0.95], [0.8, 0.96], [0.7, 0.97],
  [0.6, 0.975], [0.5, 0.98], [0.4, 0.985], [0.3, 0.99], [0.2, 0.995], [0.1, 0.998]
]
const prDataSVM = [
  [1, 0.6], [0.9, 0.65], [0.8, 0.68], [0.7, 0.72], [0.6, 0.75],
  [0.5, 0.78], [0.4, 0.82], [0.3, 0.85], [0.2, 0.9], [0.1, 0.95]
]

// 初始化 ROC 曲线
function initROCChart() {
  const chart = echarts.init(rocChart.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(50,50,50,0.9)',
      borderColor: '#409eff',
      textStyle: { color: '#fff' }
    },
    legend: {
      data: ['PU学习算法 (AUC=0.98)', '传统SVM (AUC=0.72)'],
      bottom: 0
    },
    grid: {
      left: '8%',
      right: '8%',
      top: '10%',
      bottom: '18%'
    },
    xAxis: {
      type: 'value',
      name: 'False Positive Rate',
      nameLocation: 'middle',
      nameGap: 25,
      min: 0,
      max: 1,
      axisLine: { lineStyle: { color: '#666' } }
    },
    yAxis: {
      type: 'value',
      name: 'True Positive Rate',
      nameLocation: 'middle',
      nameGap: 40,
      min: 0,
      max: 1,
      axisLine: { lineStyle: { color: '#666' } }
    },
    series: [
      {
        name: 'PU学习算法 (AUC=0.98)',
        type: 'line',
        data: rocDataPU,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 3, color: '#67c23a' },
        areaStyle: { color: 'rgba(103, 194, 58, 0.2)' }
      },
      {
        name: '传统SVM (AUC=0.72)',
        type: 'line',
        data: rocDataSVM,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 3, color: '#e6a23c' },
        areaStyle: { color: 'rgba(230, 162, 60, 0.15)' }
      }
    ]
  }

  chart.setOption(option)
  return chart
}

// 初始化 PR 曲线
function initPRChart() {
  const chart = echarts.init(prChart.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(50,50,50,0.9)',
      borderColor: '#409eff',
      textStyle: { color: '#fff' }
    },
    legend: {
      data: ['PU学习算法', '传统SVM'],
      bottom: 0
    },
    grid: {
      left: '8%',
      right: '8%',
      top: '10%',
      bottom: '18%'
    },
    xAxis: {
      type: 'value',
      name: 'Recall',
      nameLocation: 'middle',
      nameGap: 25,
      min: 0,
      max: 1,
      axisLine: { lineStyle: { color: '#666' } }
    },
    yAxis: {
      type: 'value',
      name: 'Precision',
      nameLocation: 'middle',
      nameGap: 40,
      min: 0,
      max: 1,
      axisLine: { lineStyle: { color: '#666' } }
    },
    series: [
      {
        name: 'PU学习算法',
        type: 'line',
        data: prDataPU,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 3, color: '#409eff' },
        areaStyle: { color: 'rgba(64, 158, 255, 0.2)' }
      },
      {
        name: '传统SVM',
        type: 'line',
        data: prDataSVM,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 3, color: '#f56c6c' },
        areaStyle: { color: 'rgba(245, 108, 108, 0.15)' }
      }
    ]
  }

  chart.setOption(option)
  return chart
}

// 初始化热力图
function initHeatmapChart() {
  const chart = echarts.init(heatmapChart.value)

  // 特征数据
  const features = ['MW分子量', 'LogP脂水分配系数', 'TPSA拓扑极性表面积', 'HBD氢键供体', 'HBA氢键受体']
  const compounds = ['麻黄碱', '黄芩苷', '苦杏仁苷', '次黄嘌呤', '槲皮素']

  // Mock 热力数据
  const data = [
    [0, 0, 0.85], [0, 1, 0.72], [0, 2, 0.45], [0, 3, 0.91], [0, 4, 0.38],
    [1, 0, 0.62], [1, 1, 0.88], [1, 2, 0.75], [1, 3, 0.55], [1, 4, 0.92],
    [2, 0, 0.45], [2, 1, 0.38], [2, 2, 0.82], [2, 3, 0.65], [2, 4, 0.78],
    [3, 0, 0.72], [3, 1, 0.55], [3, 2, 0.42], [3, 3, 0.88], [3, 4, 0.62],
    [4, 0, 0.38], [4, 1, 0.92], [4, 2, 0.68], [4, 3, 0.42], [4, 4, 0.85]
  ]

  const option = {
    tooltip: {
      position: 'top',
      formatter: (params) => `${compounds[params.data[0]]}<br/>${features[params.data[1]]}: ${params.data[2]}`
    },
    grid: {
      left: '15%',
      right: '10%',
      top: '5%',
      bottom: '20%'
    },
    xAxis: {
      type: 'category',
      data: features,
      axisLabel: {
        rotate: 30,
        fontSize: 11
      },
      splitArea: { show: true }
    },
    yAxis: {
      type: 'category',
      data: compounds,
      axisLabel: { fontSize: 11 },
      splitArea: { show: true }
    },
    visualMap: {
      min: 0,
      max: 1,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '0%',
      inRange: {
        color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8',
                '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
      }
    },
    series: [{
      type: 'heatmap',
      data: data.map(d => [d[1], d[0], d[2]]),
      label: {
        show: true,
        fontSize: 10,
        formatter: (params) => params.data[2].toFixed(2)
      },
      emphasis: {
        itemStyle: { shadowBlur: 10 }
      }
    }]
  }

  chart.setOption(option)
  return chart
}

// 初始化 Cytoscape 网络
function initNetwork() {
  cyInstance = cytoscape({
    container: networkContainer.value,

    // 网络元素数据
    elements: {
      nodes: [
        // 方剂节点
        { data: { id: 'P_01', label: '降气平哮方', category: 'prescription' } },
        // 药材节点
        { data: { id: 'H_麻黄', label: '麻黄', category: 'herb' } },
        { data: { id: 'H_地龙', label: '地龙', category: 'herb' } },
        // 化合物节点（大小与入血概率绑定）
        { data: { id: 'C_麻黄碱', label: '麻黄碱', category: 'compound', prob: 98 } },
        { data: { id: 'C_伪麻黄碱', label: '伪麻黄碱', category: 'compound', prob: 92 } },
        { data: { id: 'C_次黄嘌呤', label: '次黄嘌呤', category: 'compound', prob: 86 } },
        // 靶点节点
        { data: { id: 'T_IL4', label: 'IL-4', category: 'target' } },
        { data: { id: 'T_TNF', label: 'TNF', category: 'target' } },
        { data: { id: 'T_IL13', label: 'IL-13', category: 'target' } },
        { data: { id: 'T_STAT1', label: 'STAT1', category: 'target' } }
      ],
      edges: [
        // 方剂->药材
        { data: { source: 'P_01', target: 'H_麻黄', category: 'p2h' } },
        { data: { source: 'P_01', target: 'H_地龙', category: 'p2h' } },
        // 药材->成分
        { data: { source: 'H_麻黄', target: 'C_麻黄碱', category: 'h2c' } },
        { data: { source: 'H_麻黄', target: 'C_伪麻黄碱', category: 'h2c' } },
        { data: { source: 'H_地龙', target: 'C_次黄嘌呤', category: 'h2c' } },
        // 成分->靶点（活性不同的连线）
        { data: { source: 'C_麻黄碱', target: 'T_IL4', category: 'c2t', activity: 0.9 } },
        { data: { source: 'C_麻黄碱', target: 'T_TNF', category: 'c2t', activity: 0.8 } },
        { data: { source: 'C_伪麻黄碱', target: 'T_IL13', category: 'c2t', activity: 0.7 } },
        { data: { source: 'C_次黄嘌呤', target: 'T_STAT1', category: 'c2t', activity: 0.85 } },
        { data: { source: 'C_麻黄碱', target: 'T_STAT1', category: 'c2t', activity: 0.6 } }
      ]
    },

    // 样式
    style: [
      // 方剂节点：金黄色五角星
      {
        selector: 'node[category="prescription"]',
        style: {
          'background-color': '#f1c40f',
          'shape': 'star',
          'width': 50,
          'height': 50,
          'label': 'data(label)',
          'color': '#fff',
          'text-valign': 'bottom',
          'text-margin-y': 10,
          'font-size': 14,
          'font-weight': 'bold',
          'text-outline-color': '#1a1a2e',
          'text-outline-width': 2
        }
      },
      // 药材节点：绿色方块
      {
        selector: 'node[category="herb"]',
        style: {
          'background-color': '#2ecc71',
          'shape': 'round-rectangle',
          'width': 40,
          'height': 30,
          'label': 'data(label)',
          'color': '#fff',
          'text-valign': 'center',
          'font-size': 12,
          'font-weight': 'bold'
        }
      },
      // 化合物节点：蓝色圆形，大小与入血概率绑定
      {
        selector: 'node[category="compound"]',
        style: {
          'background-color': '#3498db',
          'shape': 'ellipse',
          'width': 'mapData(prob, 80, 100, 25, 45)',
          'height': 'mapData(prob, 80, 100, 25, 45)',
          'label': 'data(label)',
          'color': '#fff',
          'text-valign': 'center',
          'font-size': 11
        }
      },
      // 靶点节点：红色菱形
      {
        selector: 'node[category="target"]',
        style: {
          'background-color': '#e74c3c',
          'shape': 'diamond',
          'width': 35,
          'height': 35,
          'label': 'data(label)',
          'color': '#fff',
          'text-valign': 'bottom',
          'text-margin-y': 8,
          'font-size': 11,
          'font-weight': 'bold'
        }
      },
      // 方剂->药材连线：灰色
      {
        selector: 'edge[category="p2h"]',
        style: {
          'width': 2,
          'line-color': '#95a5a6',
          'curve-style': 'bezier',
          'target-arrow-shape': 'triangle',
          'target-arrow-color': '#95a5a6'
        }
      },
      // 药材->成分连线：灰色
      {
        selector: 'edge[category="h2c"]',
        style: {
          'width': 2,
          'line-color': '#95a5a6',
          'curve-style': 'bezier',
          'target-arrow-shape': 'triangle',
          'target-arrow-color': '#95a5a6'
        }
      },
      // 成分->靶点连线：半透明科技蓝发光线
      {
        selector: 'edge[category="c2t"]',
        style: {
          'width': 'mapData(activity, 0.5, 1, 1, 4)',
          'line-color': '#00d4ff',
          'line-opacity': 0.8,
          'curve-style': 'bezier',
          'target-arrow-shape': 'triangle',
          'target-arrow-color': '#00d4ff',
          'target-arrow-fill': '#00d4ff',
          'overlay-opacity': 0
        }
      }
    ],

    // 布局算法
    layout: {
      name: 'breadthfirst',
      directed: true,
      padding: 50,
      spacingFactor: 1.5,
      avoidOverlap: true
    }
  })

  // 一阶邻居高亮交互
  cyInstance.on('tap', 'node', function(evt) {
    const node = evt.target

    // 重置所有节点和边的样式
    cyInstance.elements().removeClass('dimmed')
    cyInstance.elements().removeClass('highlighted')

    if (node.selected()) {
      // 获取一阶邻居
      const neighborhood = node.closedNeighborhood()

      // 其他节点和边半透明
      cyInstance.elements().difference(neighborhood).addClass('dimmed')

      // 邻居节点和边高亮
      neighborhood.addClass('highlighted')

      // 显示提示
      console.log(`点击节点: ${node.data('label')}, 一阶邻居: ${neighborhood.nodes().length} 个节点, ${neighborhood.edges().length} 条边`)
    }
  })

  // 添加高亮样式
  cyInstance.style()
    .selector('.dimmed')
    .style({
      'opacity': 0.2
    })
    .selector('.highlighted')
    .style({
      'opacity': 1
    })
    .update()
}

// 导出网络为 PNG
function exportNetwork() {
  if (cyInstance) {
    const png = cyInstance.png({
      output: 'blob',
      bg: '#1a1a2e',
      full: true,
      scale: 2
    })

    // 创建下载链接
    const link = document.createElement('a')
    link.href = URL.createObjectURL(png)
    link.download = '靶点拓扑网络_降气平哮方.png'
    link.click()
  }
}

// 图表实例
let charts = []

onMounted(() => {
  charts.push(initROCChart())
  charts.push(initPRChart())
  charts.push(initHeatmapChart())
  initNetwork()

  // 窗口大小变化时重绘图表
  window.addEventListener('resize', () => {
    charts.forEach(chart => chart && chart.resize())
  })
})

onUnmounted(() => {
  charts.forEach(chart => chart && chart.dispose())
  if (cyInstance) {
    cyInstance.destroy()
  }
  window.removeEventListener('resize', () => {
    charts.forEach(chart => chart && chart.resize())
  })
})
</script>

<style scoped>
.expert-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  color: #fff;
}

/* 顶部导航栏 */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 40px;
  background: rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  cursor: pointer;
}

.logo:hover {
  color: #409eff;
}

.logo .el-icon {
  font-size: 24px;
}

.back-btn {
  font-size: 14px;
}

/* 模块 A */
.module-a {
  padding: 24px 40px;
}

.card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.card-header h2 {
  font-size: 18px;
  color: #fff;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
}

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 20px;
}

.chart-wrapper {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 16px;
}

.chart-wrapper h3 {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.85);
  margin: 0 0 12px 0;
  text-align: center;
}

.metric-chart {
  width: 100%;
  height: 250px;
}

.heatmap-wrapper {
  grid-column: auto;
}

/* 模块 B */
.module-b {
  margin: 0 40px 24px;
}

.network-container {
  width: 100%;
  height: 500px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
}

/* 响应式 */
@media (max-width: 1400px) {
  .charts-row {
    grid-template-columns: 1fr 1fr;
  }

  .heatmap-wrapper {
    grid-column: 1 / 3;
  }
}

@media (max-width: 900px) {
  .charts-row {
    grid-template-columns: 1fr;
  }

  .heatmap-wrapper {
    grid-column: auto;
  }
}
</style>