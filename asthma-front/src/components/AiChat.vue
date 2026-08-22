<template>
  <div class="ai-chat-fab">
    <!-- 浮动按钮 -->
    <button class="fab-btn" :class="{ active: open }" @click="toggle" :title="open ? '关闭' : 'AI 助手'">
      <span v-if="!open" class="fab-icon">🤖</span>
      <span v-else class="fab-icon">✕</span>
    </button>

    <!-- 聊天面板 -->
    <transition name="slide-up">
      <div v-if="open" class="chat-panel">
        <div class="chat-header">
          <span class="chat-title">🤖 AI 智能助手</span>
          <span class="chat-subtitle">基于 DeepSeek · 中医药知识问答</span>
        </div>

        <div class="chat-body" ref="chatBody">
          <div v-if="messages.length === 0" class="chat-empty">
            <div class="empty-icon">💬</div>
            <div class="empty-text">我是您的 AI 科研助手</div>
            <div class="empty-hints">
              <span class="hint" @click="sendHint('麻黄治疗哮喘的作用机制是什么？')">麻黄治疗哮喘的作用机制？</span>
              <span class="hint" @click="sendHint('小青龙汤包含哪些中药？')">小青龙汤包含哪些中药？</span>
              <span class="hint" @click="sendHint('什么是入血预测？')">什么是入血预测？</span>
            </div>
          </div>

          <div v-for="(m, i) in messages" :key="i" :class="['msg', m.role]">
            <div class="msg-avatar">{{ m.role === 'user' ? '👤' : '🤖' }}</div>
            <div class="msg-content">
              <div class="msg-text" v-html="renderMarkdown(m.content)"></div>
              <span v-if="m.role === 'assistant' && streaming && i === messages.length - 1" class="cursor-blink">▌</span>
            </div>
          </div>

          <div v-if="streaming && !messages[messages.length-1]?.content" class="msg assistant">
            <div class="msg-avatar">🤖</div>
            <div class="msg-content">
              <span class="thinking-dots">思考中<span class="dots">...</span></span>
            </div>
          </div>
        </div>

        <div class="chat-footer">
          <input
            v-model="input"
            class="chat-input"
            placeholder="输入您的问题..."
            @keyup.enter="send"
            :disabled="streaming"
          />
          <button class="send-btn" @click="send" :disabled="!input.trim() || streaming">
            <span v-if="!streaming">发送</span>
            <span v-else>⏹</span>
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, nextTick, onBeforeUnmount } from 'vue'
import { useAiSettings } from '../composables/useAiSettings'
import { streamAiChat } from '../api'

const { buildAiHeaders } = useAiSettings()

const open = ref(false)
const input = ref('')
const streaming = ref(false)
const chatBody = ref(null)
const messages = ref([])
let abortController = null

const SYSTEM_PROMPT = `你是一个专业的中医药科研助手，专注于儿童哮喘方剂分析。你可以：
1. 解释中药的药理作用和作用机制
2. 分析方剂的组成和配伍原理
3. 解释入血预测、网络药理学、GSEA富集分析等概念
4. 回答关于中药化合物、靶点、信号通路的问题
请用专业但易懂的中文回答，适当使用emoji让回答更生动。`

function toggle() {
  open.value = !open.value
  if (open.value) {
    nextTick(() => scrollBottom())
  }
}

function scrollBottom() {
  nextTick(() => {
    if (chatBody.value) {
      chatBody.value.scrollTop = chatBody.value.scrollHeight
    }
  })
}

function renderMarkdown(text) {
  if (!text) return ''
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
}

function sendHint(text) {
  input.value = text
  send()
}

async function send() {
  const q = input.value.trim()
  if (!q || streaming.value) return

  input.value = ''
  messages.value.push({ role: 'user', content: q })
  messages.value.push({ role: 'assistant', content: '' })
  scrollBottom()

  streaming.value = true
  abortController = new AbortController()

  const chatMessages = [
    { role: 'system', content: SYSTEM_PROMPT },
    ...messages.value.filter(m => m.content).slice(0, -1).map(m => ({ role: m.role, content: m.content })),
  ]

  await streamAiChat({
    messages: chatMessages,
    aiHeaders: buildAiHeaders(),
    onDelta: (delta) => {
      const last = messages.value[messages.value.length - 1]
      if (last) {
        last.content += delta
        scrollBottom()
      }
    },
    onError: (err) => {
      const last = messages.value[messages.value.length - 1]
      if (last && !last.content) {
        last.content = '❌ ' + (err.message || '对话失败，请检查 API Key 是否配置正确')
      }
      streaming.value = false
    },
    onDone: () => {
      streaming.value = false
    },
    signal: abortController.signal,
  })
}

function stopGeneration() {
  if (abortController) {
    abortController.abort()
    streaming.value = false
  }
}

onBeforeUnmount(() => {
  if (abortController) abortController.abort()
})
</script>

<style scoped>
.ai-chat-fab { position: fixed; bottom: 24px; right: 24px; z-index: 9999; font-family: var(--font-family); }

.fab-btn {
  width: 52px; height: 52px; border-radius: 50%; border: none;
  background: linear-gradient(135deg, #2dd4bf, #14b8a6);
  color: #fff; cursor: pointer; font-size: 22px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 20px rgba(45, 212, 191, 0.35);
  transition: all 0.25s;
  position: relative; z-index: 2;
}
.fab-btn:hover { transform: scale(1.08); box-shadow: 0 6px 28px rgba(45, 212, 191, 0.5); }
.fab-btn.active { background: #475569; box-shadow: 0 4px 16px rgba(0,0,0,0.4); }
.fab-icon { line-height: 1; }

.chat-panel {
  position: absolute; bottom: 64px; right: 0; width: 380px; height: 520px;
  background: #1e293b; border: 1px solid rgba(255,255,255,0.1);
  border-radius: 16px; box-shadow: 0 12px 48px rgba(0,0,0,0.5);
  display: flex; flex-direction: column; overflow: hidden;
}

.chat-header {
  padding: 16px 20px; border-bottom: 1px solid rgba(255,255,255,0.06);
  flex-shrink: 0;
}
.chat-title { font-size: 16px; font-weight: 700; color: #f1f5f9; display: block }
.chat-subtitle { font-size: 11px; color: #94a3b8; margin-top: 2px; display: block }

.chat-body { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }

.chat-empty { text-align: center; padding: 40px 20px }
.empty-icon { font-size: 40px; margin-bottom: 12px }
.empty-text { color: #94a3b8; font-size: 14px; margin-bottom: 16px }
.empty-hints { display: flex; flex-direction: column; gap: 8px }
.hint {
  display: block; padding: 10px 14px; background: rgba(45,212,191,0.08);
  border: 1px solid rgba(45,212,191,0.15); border-radius: 10px;
  color: #5eead4; font-size: 13px; cursor: pointer; text-align: left;
  transition: all 0.2s;
}
.hint:hover { background: rgba(45,212,191,0.15); border-color: rgba(45,212,191,0.3) }

.msg { display: flex; gap: 10px; animation: msg-in 0.3s ease }
.msg.user { flex-direction: row-reverse }
.msg-avatar { width: 30px; height: 30px; border-radius: 50%; background: rgba(255,255,255,0.06); display: flex; align-items: center; justify-content: center; font-size: 14px; flex-shrink: 0 }
.msg-content { max-width: 80% }
.msg-text {
  padding: 10px 14px; border-radius: 12px; font-size: 13px; line-height: 1.65;
  word-break: break-word;
}
.msg-text :deep(strong) { color: #5eead4 }
.msg-text :deep(code) { background: rgba(0,0,0,0.3); padding: 2px 6px; border-radius: 4px; font-size: 12px }
.msg.user .msg-text { background: rgba(45,212,191,0.15); color: #f1f5f9 }
.msg.assistant .msg-text { background: rgba(255,255,255,0.04); color: #cbd5e1 }

.cursor-blink { animation: blink 1s infinite; color: #2dd4bf }

.thinking-dots { color: #94a3b8; font-size: 13px; padding: 10px 14px }
.dots { animation: blink 1.5s infinite }

.chat-footer {
  padding: 12px 16px; border-top: 1px solid rgba(255,255,255,0.06);
  display: flex; gap: 8px; flex-shrink: 0;
}
.chat-input {
  flex: 1; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px; padding: 10px 14px; color: #f1f5f9; font-size: 13px;
  outline: none; transition: border-color 0.2s;
}
.chat-input:focus { border-color: rgba(45,212,191,0.4) }
.chat-input::placeholder { color: #64748b }
.send-btn {
  padding: 10px 16px; background: #2dd4bf; border: none; border-radius: 10px;
  color: #0f172a; font-weight: 700; font-size: 13px; cursor: pointer;
  transition: all 0.2s; white-space: nowrap;
}
.send-btn:hover:not(:disabled) { background: #5eead4 }
.send-btn:disabled { opacity: 0.4; cursor: not-allowed }

.slide-up-enter-active { transition: all 0.3s ease }
.slide-up-leave-active { transition: all 0.2s ease }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translateY(20px) scale(0.95) }

@keyframes msg-in { from { opacity: 0; transform: translateY(10px) } to { opacity: 1; transform: translateY(0) } }
@keyframes blink { 0%, 100% { opacity: 1 } 50% { opacity: 0 } }
</style>