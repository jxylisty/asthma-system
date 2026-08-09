<template>
  <div class="node-editor-container">
    <div class="editor-header">
      <div class="header-left">
        <h2 class="page-title">节点编排</h2>
        <p class="page-desc">可视化编排哮喘方剂分析流程，支持节点连接和执行</p>
      </div>
      <div class="header-right">
        <el-button :class="{ active: isConnecting }" @click="toggleConnectMode">
          <el-icon><Link /></el-icon>
          连线模式
        </el-button>
        <el-button type="primary" @click="saveWorkflow">
          <el-icon><Document /></el-icon>
          保存
        </el-button>
        <el-button @click="showLoadDialog">
          <el-icon><Document /></el-icon>
          加载
        </el-button>
        <el-button type="danger" @click="clearAll">
          <el-icon><Delete /></el-icon>
          清空
        </el-button>
      </div>
    </div>

    <div class="toolbar">
      <div class="toolbar-group">
        <span class="toolbar-label">添加节点:</span>
        <div class="node-buttons">
          <el-button class="node-btn input-node" @click="addNode('input')">
            <el-icon><EditPen /></el-icon>
            症状输入
          </el-button>
          <el-button class="node-btn library-node" @click="addNode('library')">
            <el-icon><Notebook /></el-icon>
            方剂库
          </el-button>
          <el-button class="node-btn rule-node" @click="addNode('rule')">
            <el-icon><DataAnalysis /></el-icon>
            配伍规则
          </el-button>
          <el-button class="node-btn output-node" @click="addNode('output')">
            <el-icon><Monitor /></el-icon>
            输出
          </el-button>
        </div>
      </div>
      <div class="toolbar-info" v-if="isConnecting">
        <el-icon class="info-icon"><Warning /></el-icon>
        <span>点击第一个节点，然后点击第二个节点建立连接</span>
      </div>
    </div>

    <div class="canvas-container" ref="canvasRef" @click="handleCanvasClick">
      <svg class="connections-layer" :width="canvasWidth" :height="canvasHeight">
        <defs>
          <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto" markerUnits="strokeWidth">
            <polygon points="0 0, 10 3.5, 0 7" fill="#666" />
          </marker>
          <marker id="arrowhead-active" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto" markerUnits="strokeWidth">
            <polygon points="0 0, 10 3.5, 0 7" fill="#409eff" />
          </marker>
        </defs>
        <g v-for="connection in connections" :key="connection.id">
          <path
            :d="createCurvePath(connection)"
            :class="{ active: selectedConnection === connection.id }"
            :stroke="selectedConnection === connection.id ? '#409eff' : '#666'"
            :stroke-width="selectedConnection === connection.id ? 3 : 2"
            fill="none"
            :marker-end="selectedConnection === connection.id ? 'url(#arrowhead-active)' : 'url(#arrowhead)'"
            cursor="pointer"
            @click.stop="handleConnectionClick(connection.id)"
          />
        </g>
      </svg>

      <div
        v-for="node in nodes"
        :key="node.id"
        class="node"
        :class="[`node-${node.type}`, { selected: selectedNode === node.id }]"
        :style="{ left: node.x + 'px', top: node.y + 'px' }"
        @mousedown="startDrag($event, node)"
        @click.stop="selectNode(node.id)"
      >
        <div class="node-header">
          <span class="node-title">{{ getNodeTitle(node.type) }}</span>
          <div class="node-header-actions">
            <el-button 
              v-if="node.type === 'output'" 
              class="run-btn" 
              icon="VideoPlay" 
              @click.stop="runSingleOutput(node)" 
              type="success"
              size="small"
            >
              运行
            </el-button>
            <el-button class="delete-btn" icon="Delete" @click.stop="deleteNode(node.id)" type="danger" size="small">
              删除
            </el-button>
          </div>
        </div>
        <div class="node-content">
          <div v-if="node.type === 'input'" class="input-node-content">
            <el-input
              v-model="node.data.symptoms"
              placeholder="输入哮喘症状，如：喘息、咳嗽"
              type="textarea"
              :rows="3"
            />
          </div>
          <div v-else-if="node.type === 'library'" class="library-node-content">
            <el-select v-model="node.data.selectedPrescription" placeholder="选择方剂" style="width: 100%">
              <el-option v-for="p in prescriptions" :key="p.name" :label="p.name" :value="p.name" />
            </el-select>
            <div v-if="node.data.selectedPrescription" class="prescription-detail">
              <div class="detail-title">方剂详情</div>
              <div class="detail-item">
                <span>组成：</span>
                <span>{{ getPrescriptionByName(node.data.selectedPrescription)?.ingredients }}</span>
              </div>
              <div class="detail-item">
                <span>功效：</span>
                <span>{{ getPrescriptionByName(node.data.selectedPrescription)?.effect }}</span>
              </div>
            </div>
          </div>
          <div v-else-if="node.type === 'rule'" class="rule-node-content">
            <div class="rule-item">
              <span class="rule-label">君臣佐使</span>
              <el-switch v-model="node.data.rule1" />
            </div>
            <div class="rule-item">
              <span class="rule-label">寒热平衡</span>
              <el-switch v-model="node.data.rule2" />
            </div>
            <div class="rule-item">
              <span class="rule-label">升降浮沉</span>
              <el-switch v-model="node.data.rule3" />
            </div>
            <div class="rule-item">
              <span class="rule-label">毒性禁忌</span>
              <el-switch v-model="node.data.rule4" />
            </div>
          </div>
          <div v-else-if="node.type === 'output'" class="output-node-content">
            <div v-if="node.data.result" class="result-content">
              <div class="result-title">分析结果</div>
              <div class="result-text">{{ node.data.result }}</div>
            </div>
            <div v-else class="result-placeholder">
              <el-icon><Document /></el-icon>
              <span>等待执行结果...</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog title="加载记录" v-model="loadDialogVisible" width="400px">
      <el-select v-model="selectedWorkflow" placeholder="请选择记录" style="width: 100%;">
        <el-option v-for="opt in workflowOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
      <template #footer>
        <el-button @click="loadDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmLoad">加载</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Link,
  VideoPlay,
  Delete,
  EditPen,
  Notebook,
  DataAnalysis,
  Monitor,
  Warning,
  Document
} from '@element-plus/icons-vue'
import { useSettings } from '../composables/useSettings'

const { loadSettings } = useSettings()

onMounted(() => {
  loadSettings()
  loadWorkflow()
})

const canvasRef = ref(null)
const canvasWidth = ref(2000)
const canvasHeight = ref(2000)

const nodes = reactive([])
const connections = reactive([])
const selectedNode = ref(null)
const selectedConnection = ref(null)
const isConnecting = ref(false)
const connectStartNode = ref(null)
const loadDialogVisible = ref(false)
const selectedWorkflow = ref('')
const workflowOptions = ref([])
let dragNode = null
let dragOffset = { x: 0, y: 0 }

const prescriptions = [
  { name: '麻黄汤', ingredients: '麻黄、桂枝、杏仁、甘草', effect: '发汗解表，宣肺平喘' },
  { name: '桂枝汤', ingredients: '桂枝、芍药、生姜、大枣、甘草', effect: '解肌发表，调和营卫' },
  { name: '小青龙汤', ingredients: '麻黄、桂枝、干姜、细辛、半夏', effect: '解表散寒，温肺化饮' },
  { name: '麻杏甘石汤', ingredients: '麻黄、杏仁、石膏、甘草', effect: '辛凉宣泄，清肺平喘' },
  { name: '定喘汤', ingredients: '白果、麻黄、款冬花、半夏、桑白皮', effect: '宣肺降气，清热化痰' },
  { name: '苏子降气汤', ingredients: '紫苏子、半夏、当归、甘草', effect: '降气平喘，祛痰止咳' }
]

let nodeIdCounter = 1
let connectionIdCounter = 1

function getNodeTitle(type) {
  const titles = {
    input: '症状输入',
    library: '方剂库',
    rule: '配伍规则',
    output: '输出'
  }
  return titles[type] || '节点'
}

function getNodeColor(type) {
  const colors = {
    input: '#409eff',
    library: '#67c23a',
    rule: '#e6a23c',
    output: '#f56c6c'
  }
  return colors[type] || '#999'
}

function addNode(type) {
  const node = {
    id: `node-${nodeIdCounter++}`,
    type,
    x: 100 + (nodes.length % 4) * 200,
    y: 100 + Math.floor(nodes.length / 4) * 200,
    data: getDefaultNodeData(type)
  }
  nodes.push(node)
}

function getDefaultNodeData(type) {
  switch (type) {
    case 'input':
      return { symptoms: '' }
    case 'library':
      return { selectedPrescription: '' }
    case 'rule':
      return { rule1: true, rule2: true, rule3: false, rule4: true }
    case 'output':
      return { result: '' }
    default:
      return {}
  }
}

function startDrag(event, node) {
  dragNode = node
  dragOffset = {
    x: event.clientX - node.x,
    y: event.clientY - node.y
  }
  selectedNode.value = node.id
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

function onDrag(event) {
  if (dragNode) {
    dragNode.x = event.clientX - dragOffset.x
    dragNode.y = event.clientY - dragOffset.y
  }
}

function stopDrag() {
  dragNode = null
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

function selectNode(nodeId) {
  selectedConnection.value = null
  
  if (!isConnecting.value) {
    selectedNode.value = nodeId
    return
  }
  
  if (!connectStartNode.value) {
    connectStartNode.value = nodeId
    selectedNode.value = nodeId
    ElMessage.info('请点击另一个节点建立连接')
  } else if (connectStartNode.value === nodeId) {
    connectStartNode.value = null
    selectedNode.value = nodeId
  } else {
    const fromNode = connectStartNode.value
    const toNode = nodeId
    
    if (fromNode === toNode) {
      ElMessage.warning('不能连接同一个节点')
      connectStartNode.value = null
      selectedNode.value = nodeId
      return
    }
    
    const exists = connections.some(c => c.from === fromNode && c.to === toNode)
    if (exists) {
      ElMessage.warning('连接已存在')
      connectStartNode.value = null
      selectedNode.value = nodeId
      return
    }
    
    const reverseExists = connections.some(c => c.from === toNode && c.to === fromNode)
    if (reverseExists) {
      ElMessage.warning('反向连接已存在')
      connectStartNode.value = null
      selectedNode.value = nodeId
      return
    }
    
    connections.push({
      id: `conn-${connectionIdCounter++}`,
      from: fromNode,
      to: toNode
    })
    
    updateConnections()
    
    ElMessage.success('连接成功')
    connectStartNode.value = null
    selectedNode.value = null
  }
}

function toggleConnectMode() {
  isConnecting.value = !isConnecting.value
  connectStartNode.value = null
  selectedConnection.value = null
  selectedNode.value = null
}

function saveWorkflow() {
  ElMessageBox.prompt(
    '请输入记录名称',
    '保存画布',
    {
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      inputPlaceholder: '如：哮喘方剂分析方案'
    }
  ).then(({ value }) => {
    const name = value.trim()
    if (!name) {
      ElMessage.warning('请输入记录名称')
      return
    }
    
    const savedWorkflows = getSavedWorkflows()
    savedWorkflows[name] = {
      nodes: JSON.parse(JSON.stringify(nodes)),
      connections: JSON.parse(JSON.stringify(connections)),
      savedAt: new Date().toLocaleString()
    }
    
    localStorage.setItem('nodeEditorWorkflows', JSON.stringify(savedWorkflows))
    ElMessage.success(`画布已保存为"${name}"`)
  }).catch(() => {
    ElMessage.info('已取消保存')
  })
}

function getSavedWorkflows() {
  const saved = localStorage.getItem('nodeEditorWorkflows')
  return saved ? JSON.parse(saved) : {}
}

function loadWorkflowByName(name) {
  const savedWorkflows = getSavedWorkflows()
  const workflow = savedWorkflows[name]
  
  if (!workflow) {
    ElMessage.error('记录不存在')
    return
  }
  
  try {
    nodes.splice(0, nodes.length)
    workflow.nodes.forEach(node => {
      nodes.push(node)
    })
    
    connections.splice(0, connections.length)
    workflow.connections.forEach(conn => {
      connections.push(conn)
    })
    
    let maxNodeId = 0
    nodes.forEach(node => {
      const match = node.id.match(/node-(\d+)/)
      if (match) maxNodeId = Math.max(maxNodeId, parseInt(match[1]))
    })
    nodeIdCounter = maxNodeId + 1
    
    let maxConnId = 0
    connections.forEach(conn => {
      const match = conn.id.match(/conn-(\d+)/)
      if (match) maxConnId = Math.max(maxConnId, parseInt(match[1]))
    })
    connectionIdCounter = maxConnId + 1
    
    ElMessage.success(`已加载记录"${name}"`)
  } catch (e) {
    console.error('Failed to load workflow:', e)
    ElMessage.error('加载失败')
  }
}

function showLoadDialog() {
  const savedWorkflows = getSavedWorkflows()
  const workflowNames = Object.keys(savedWorkflows)
  
  if (workflowNames.length === 0) {
    ElMessage.info('暂无保存的记录')
    return
  }
  
  workflowOptions.value = workflowNames.map(name => {
    const workflow = savedWorkflows[name]
    return {
      label: `${name} (${workflow.savedAt})`,
      value: name
    }
  })
  
  selectedWorkflow.value = ''
  loadDialogVisible.value = true
}

function confirmLoad() {
  if (!selectedWorkflow.value) {
    ElMessage.warning('请选择记录')
    return
  }
  
  loadWorkflowByName(selectedWorkflow.value)
  loadDialogVisible.value = false
}

function loadWorkflow() {
  const saved = localStorage.getItem('nodeEditorWorkflow')
  if (!saved) return
  
  try {
    const workflow = JSON.parse(saved)
    
    nodes.splice(0, nodes.length)
    workflow.nodes.forEach(node => {
      nodes.push(node)
    })
    
    connections.splice(0, connections.length)
    workflow.connections.forEach(conn => {
      connections.push(conn)
    })
    
    let maxNodeId = 0
    nodes.forEach(node => {
      const match = node.id.match(/node-(\d+)/)
      if (match) maxNodeId = Math.max(maxNodeId, parseInt(match[1]))
    })
    nodeIdCounter = maxNodeId + 1
    
    let maxConnId = 0
    connections.forEach(conn => {
      const match = conn.id.match(/conn-(\d+)/)
      if (match) maxConnId = Math.max(maxConnId, parseInt(match[1]))
    })
    connectionIdCounter = maxConnId + 1
    
    ElMessage.info('画布内容已加载')
  } catch (e) {
    console.error('Failed to load workflow:', e)
  }
}

function deleteNode(nodeId) {
  for (let i = connections.length - 1; i >= 0; i--) {
    const conn = connections[i]
    if (conn.from === nodeId || conn.to === nodeId) {
      connections.splice(i, 1)
    }
  }
  const index = nodes.findIndex(n => n.id === nodeId)
  if (index !== -1) {
    nodes.splice(index, 1)
  }
  if (selectedNode.value === nodeId) {
    selectedNode.value = null
  }
}



function handleConnectionClick(connId) {
  selectedConnection.value = connId
  selectedNode.value = null
  ElMessageBox.confirm(
    '确认删除该连线？',
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    const index = connections.findIndex(c => c.id === connId)
    if (index !== -1) {
      connections.splice(index, 1)
    }
    selectedConnection.value = null
    ElMessage.success('连线已删除')
  }).catch(() => {
    selectedConnection.value = null
  })
}

function deleteConnection(connId) {
  const index = connections.findIndex(c => c.id === connId)
  if (index !== -1) {
    connections.splice(index, 1)
  }
  selectedConnection.value = null
}

function handleCanvasClick(event) {
  if (event.target === canvasRef.value || event.target.classList.contains('connections-layer')) {
    selectedNode.value = null
    selectedConnection.value = null
  }
}

const NODE_WIDTH = 300

function getNodeHeight(nodeId) {
  const node = nodes.find(n => n.id === nodeId)
  if (!node) return 160
  const typeHeights = {
    input: 160,
    library: 200,
    rule: 220,
    output: 180
  }
  return typeHeights[node.type] || 160
}

function getNodeOutputPort(nodeId) {
  const node = nodes.find(n => n.id === nodeId)
  if (!node) return { x: 0, y: 0 }
  const height = getNodeHeight(nodeId)
  return {
    x: node.x + NODE_WIDTH,
    y: node.y + height / 2
  }
}

function getNodeInputPort(nodeId) {
  const node = nodes.find(n => n.id === nodeId)
  if (!node) return { x: 0, y: 0 }
  const height = getNodeHeight(nodeId)
  return {
    x: node.x,
    y: node.y + height / 2
  }
}

function createCurvePath(connection) {
  const from = getNodeOutputPort(connection.from)
  const to = getNodeInputPort(connection.to)
  const dx = to.x - from.x
  const controlOffset = Math.max(Math.abs(dx) * 0.5, 50)
  return `M ${from.x} ${from.y} C ${from.x + controlOffset} ${from.y}, ${to.x - controlOffset} ${to.y}, ${to.x} ${to.y}`
}

function updateConnections() {
  const seen = new Set()
  for (let i = connections.length - 1; i >= 0; i--) {
    const conn = connections[i]
    const key = `${conn.from}-${conn.to}`
    if (seen.has(key)) {
      connections.splice(i, 1)
    } else {
      seen.add(key)
    }
  }
}

function clearAll() {
  nodes.splice(0, nodes.length)
  connections.splice(0, connections.length)
  selectedNode.value = null
  selectedConnection.value = null
  ElMessage.info('已清空所有节点和连线')
}

function getPrescriptionByName(name) {
  return prescriptions.find(p => p.name === name)
}

function runWorkflow() {
  const inputNodes = nodes.filter(n => n.type === 'input')
  const outputNodes = nodes.filter(n => n.type === 'output')

  if (inputNodes.length === 0) {
    ElMessage.warning('请添加症状输入节点')
    return
  }
  if (outputNodes.length === 0) {
    ElMessage.warning('请添加输出节点')
    return
  }

  if (connections.length === 0) {
    ElMessage.warning('请先连接节点')
    return
  }

  const reachableNodes = findReachableNodes(inputNodes.map(n => n.id))
  
  const connectedInputNodes = inputNodes.filter(n => reachableNodes.has(n.id))
  const connectedLibraryNodes = nodes.filter(n => n.type === 'library' && reachableNodes.has(n.id))
  const connectedRuleNodes = nodes.filter(n => n.type === 'rule' && reachableNodes.has(n.id))
  const connectedOutputNodes = outputNodes.filter(n => reachableNodes.has(n.id))

  if (connectedOutputNodes.length === 0) {
    ElMessage.warning('没有连接到输出节点')
    return
  }

  let symptoms = ''
  if (connectedInputNodes.length > 0) {
    symptoms = connectedInputNodes[0].data.symptoms || '未指定症状'
  }

  let prescriptionName = ''
  let prescriptionInfo = ''
  if (connectedLibraryNodes.length > 0) {
    const selected = connectedLibraryNodes[0].data.selectedPrescription
    if (selected) {
      prescriptionName = selected
      const p = getPrescriptionByName(selected)
      prescriptionInfo = `\n方剂：${p.name}\n组成：${p.ingredients}\n功效：${p.effect}`
    } else {
      prescriptionName = '未选择方剂'
    }
  } else {
    prescriptionName = '未添加方剂库节点'
  }

  let rulesApplied = ''
  if (connectedRuleNodes.length > 0) {
    const rules = connectedRuleNodes[0].data
    rulesApplied = '\n配伍规则：'
    if (rules.rule1) rulesApplied += '君臣佐使、'
    if (rules.rule2) rulesApplied += '寒热平衡、'
    if (rules.rule3) rulesApplied += '升降浮沉、'
    if (rules.rule4) rulesApplied += '毒性禁忌'
    if (!rules.rule1 && !rules.rule2 && !rules.rule3 && !rules.rule4) {
      rulesApplied += '无'
    }
  } else {
    rulesApplied = '\n配伍规则：未添加'
  }

  const result = `输入症状：${symptoms}${prescriptionInfo}${rulesApplied}\n\n分析完成：方剂已根据症状和配伍规则进行筛选和优化。`

  connectedOutputNodes.forEach(outputNode => {
    outputNode.data.result = result
  })

  ElMessage.success('运行成功')
}

function runSingleOutput(outputNode) {
  const inputNodes = nodes.filter(n => n.type === 'input')
  
  if (inputNodes.length === 0) {
    ElMessage.warning('请添加症状输入节点')
    return
  }

  const reachableNodes = findReachableNodes(inputNodes.map(n => n.id))
  
  if (!reachableNodes.has(outputNode.id)) {
    ElMessage.warning('该输出节点未连接到输入节点')
    return
  }

  const connectedInputNodes = inputNodes.filter(n => reachableNodes.has(n.id))
  const connectedLibraryNodes = nodes.filter(n => n.type === 'library' && reachableNodes.has(n.id))
  const connectedRuleNodes = nodes.filter(n => n.type === 'rule' && reachableNodes.has(n.id))

  let symptoms = ''
  if (connectedInputNodes.length > 0) {
    symptoms = connectedInputNodes[0].data.symptoms || '未指定症状'
  }

  let prescriptionName = ''
  let prescriptionInfo = ''
  if (connectedLibraryNodes.length > 0) {
    const selected = connectedLibraryNodes[0].data.selectedPrescription
    if (selected) {
      prescriptionName = selected
      const p = getPrescriptionByName(selected)
      prescriptionInfo = `\n方剂：${p.name}\n组成：${p.ingredients}\n功效：${p.effect}`
    } else {
      prescriptionName = '未选择方剂'
    }
  } else {
    prescriptionName = '未添加方剂库节点'
  }

  let rulesApplied = ''
  if (connectedRuleNodes.length > 0) {
    const rules = connectedRuleNodes[0].data
    rulesApplied = '\n配伍规则：'
    if (rules.rule1) rulesApplied += '君臣佐使、'
    if (rules.rule2) rulesApplied += '寒热平衡、'
    if (rules.rule3) rulesApplied += '升降浮沉、'
    if (rules.rule4) rulesApplied += '毒性禁忌'
    if (!rules.rule1 && !rules.rule2 && !rules.rule3 && !rules.rule4) {
      rulesApplied += '无'
    }
  } else {
    rulesApplied = '\n配伍规则：未添加'
  }

  outputNode.data.result = `输入症状：${symptoms}${prescriptionInfo}${rulesApplied}\n\n分析完成：方剂已根据症状和配伍规则进行筛选和优化。`

  ElMessage.success('运行成功')
}

function findReachableNodes(startNodeIds) {
  const reachable = new Set(startNodeIds)
  let changed = true
  
  while (changed) {
    changed = false
    for (const conn of connections) {
      if (reachable.has(conn.from) && !reachable.has(conn.to)) {
        reachable.add(conn.to)
        changed = true
      }
    }
  }
  
  return reachable
}
</script>

<style scoped>
.node-editor-container {
  padding: 20px;
  background: var(--bg-gradient);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  color: var(--text-color);
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  flex-direction: column;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-color);
  margin: 0;
}

.page-desc {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 8px 0 0;
}

.header-right {
  display: flex;
  gap: 12px;
}

.header-right :deep(.el-button) {
  padding: 10px 20px;
  font-size: 14px;
}

.header-right :deep(.el-button.active) {
  background: rgba(64, 158, 255, 0.3);
  border-color: #409eff;
  color: #409eff;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  margin-bottom: 16px;
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 16px;
}

.toolbar-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.node-buttons {
  display: flex;
  gap: 8px;
}

.node-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 13px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.node-btn.input-node {
  background: rgba(64, 158, 255, 0.2);
  border-color: #409eff;
  color: #409eff;
}

.node-btn.library-node {
  background: rgba(103, 194, 58, 0.2);
  border-color: #67c23a;
  color: #67c23a;
}

.node-btn.rule-node {
  background: rgba(230, 162, 60, 0.2);
  border-color: #e6a23c;
  color: #e6a23c;
}

.node-btn.output-node {
  background: rgba(245, 108, 108, 0.2);
  border-color: #f56c6c;
  color: #f56c6c;
}

.node-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.toolbar-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(230, 162, 60, 0.15);
  border-radius: 6px;
  font-size: 13px;
  color: #e6a23c;
}

.info-icon {
  font-size: 16px;
}

.canvas-container {
  flex: 1;
  position: relative;
  background-image: 
    linear-gradient(rgba(0, 0, 0, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 0, 0, 0.05) 1px, transparent 1px);
  background-size: 20px 20px;
  border-radius: 12px;
  overflow: hidden;
  border: 2px solid rgba(64, 158, 255, 0.3);
  box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.05);
}

.connections-layer {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 1;
  pointer-events: auto;
}

.connections-layer path {
  fill: none;
  cursor: pointer;
  transition: all 0.3s ease;
}

.connections-layer path:hover {
  stroke: #409eff !important;
  stroke-width: 3 !important;
}

.node {
  position: absolute;
  width: 300px;
  background: rgba(30, 30, 50, 0.95);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
  cursor: move;
  z-index: 10;
  transition: box-shadow 0.3s ease, border-color 0.3s ease;
  border: 2px solid transparent;
}

.node:hover {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
}

.node.selected {
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.2), 0 8px 30px rgba(0, 0, 0, 0.5);
}

.node-input {
  border-top: 4px solid #409eff;
}

.node-library {
  border-top: 4px solid #67c23a;
}

.node-rule {
  border-top: 4px solid #e6a23c;
}

.node-output {
  border-top: 4px solid #f56c6c;
}

.node-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px 12px 0 0;
}

.node-title {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
}

.node-header-actions {
  display: flex;
  gap: 6px;
}

.run-btn {
  padding: 4px 8px;
  font-size: 12px;
}

.delete-btn {
  padding: 4px 8px;
  font-size: 12px;
}

.node-content {
  padding: 16px;
  color: rgba(255, 255, 255, 0.8);
}

.input-node-content :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(64, 158, 255, 0.3);
  color: #fff;
}

.library-node-content :deep(.el-select) {
  margin-bottom: 12px;
}

.library-node-content :deep(.el-select .el-input__inner) {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(103, 194, 58, 0.3);
  color: #fff;
}

.prescription-detail {
  padding: 12px;
  background: rgba(103, 194, 58, 0.1);
  border-radius: 8px;
}

.detail-title {
  font-size: 13px;
  font-weight: 600;
  color: #67c23a;
  margin-bottom: 8px;
}

.detail-item {
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 4px;
}

.detail-item span:first-child {
  color: rgba(255, 255, 255, 0.5);
}

.rule-node-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rule-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(230, 162, 60, 0.1);
  border-radius: 6px;
}

.rule-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
}

.output-node-content {
  min-height: 120px;
}

.result-content {
  padding: 12px;
  background: rgba(245, 108, 108, 0.1);
  border-radius: 8px;
}

.result-title {
  font-size: 13px;
  font-weight: 600;
  color: #f56c6c;
  margin-bottom: 8px;
}

.result-text {
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  color: rgba(255, 255, 255, 0.9);
}

.result-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 120px;
  color: rgba(255, 255, 255, 0.3);
  gap: 8px;
}

.result-placeholder .el-icon {
  font-size: 24px;
}

</style>
