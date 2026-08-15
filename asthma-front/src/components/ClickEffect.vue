<template>
  <div class="click-effects">
    <!-- 自定义光标 -->
    <div class="custom-cursor" :class="{ hover: isHovering }" :style="cursorStyle"></div>
    <div class="custom-cursor-ring" :class="{ hover: isHovering }" :style="cursorRingStyle"></div>

    <!-- 鼠标移动拖尾波纹 -->
    <div
      v-for="trail in trails"
      :key="trail.id"
      class="trail-ripple"
      :style="{ left: trail.x + 'px', top: trail.y + 'px' }"
    ></div>

    <!-- 点击效果 -->
    <div
      v-for="effect in effects"
      :key="effect.id"
      class="click-effect"
      :class="effect.type"
      :style="{
        left: effect.x + 'px',
        top: effect.y + 'px',
        '--color': effect.color
      }"
    >
      <template v-if="effect.type === 'ripple'">
        <span class="ripple"></span>
        <span class="ripple ripple-delay"></span>
      </template>
      <template v-else-if="effect.type === 'tech'">
        <span class="tech-ring tech-ring-1"></span>
        <span class="tech-ring tech-ring-2"></span>
        <span class="tech-ring tech-ring-3"></span>
        <span class="tech-center"></span>
        <span class="tech-corner tech-corner-1"></span>
        <span class="tech-corner tech-corner-2"></span>
        <span class="tech-corner tech-corner-3"></span>
        <span class="tech-corner tech-corner-4"></span>
      </template>
      <template v-else-if="effect.type === 'particles'">
        <span
          v-for="i in 12"
          :key="i"
          class="particle"
          :style="{ '--angle': (i - 1) * 30 + 'deg' }"
        ></span>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useSettings } from '../composables/useSettings'

const { clickEffect } = useSettings()

const effects = ref([])
const trails = ref([])
let effectId = 0
let trailId = 0

// 自定义光标位置
const cursorX = ref(0)
const cursorY = ref(0)
const ringX = ref(0)
const ringY = ref(0)
const isHovering = ref(false)

const cursorStyle = ref({ left: '0px', top: '0px' })
const cursorRingStyle = ref({ left: '0px', top: '0px' })

const colors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399']
const techColors = ['#00d4ff', '#00ff88', '#ff00ff', '#ffff00']

// 可点击元素选择器
const clickableSelector = 'a, button, .el-button, .el-tag, .el-card, .herb-card, .compound-card, .prescription-card, [role="button"], input[type="submit"], input[type="button"]'

function createEffect(e) {
  const type = clickEffect.value
  if (type === 'none') return

  let color
  if (type === 'tech') {
    color = techColors[Math.floor(Math.random() * techColors.length)]
  } else {
    color = colors[Math.floor(Math.random() * colors.length)]
  }

  const newEffect = {
    id: effectId++,
    x: e.clientX,
    y: e.clientY,
    type,
    color
  }

  effects.value.push(newEffect)

  setTimeout(() => {
    const index = effects.value.findIndex(e => e.id === newEffect.id)
    if (index !== -1) {
      effects.value.splice(index, 1)
    }
  }, type === 'particles' ? 800 : 1000)
}

// 鼠标移动拖尾效果
let lastTrailTime = 0
function createTrail(e) {
  const now = Date.now()
  if (now - lastTrailTime < 30) return // 限制频率
  lastTrailTime = now

  const newTrail = {
    id: trailId++,
    x: e.clientX,
    y: e.clientY
  }

  trails.value.push(newTrail)

  setTimeout(() => {
    const index = trails.value.findIndex(t => t.id === newTrail.id)
    if (index !== -1) {
      trails.value.splice(index, 1)
    }
  }, 600)
}

// 自定义光标跟随
function updateCursor(e) {
  cursorX.value = e.clientX
  cursorY.value = e.clientY
  cursorStyle.value = { left: e.clientX + 'px', top: e.clientY + 'px' }
}

// 环形光标平滑跟随
let animationFrame = null
function animateRing() {
  ringX.value += (cursorX.value - ringX.value) * 0.15
  ringY.value += (cursorY.value - ringY.value) * 0.15
  cursorRingStyle.value = { left: ringX.value + 'px', top: ringY.value + 'px' }
  animationFrame = requestAnimationFrame(animateRing)
}

// 检测鼠标是否悬停在可点击元素上
function checkHover(e) {
  const target = e.target
  if (target.closest(clickableSelector)) {
    isHovering.value = true
  } else {
    isHovering.value = false
  }
}

function handleMouseMove(e) {
  updateCursor(e)
  createTrail(e)
  checkHover(e)
}

onMounted(() => {
  document.addEventListener('click', createEffect)
  document.addEventListener('mousemove', handleMouseMove)
  animateRing()

  // 隐藏默认光标
  document.body.style.cursor = 'none'
})

onUnmounted(() => {
  document.removeEventListener('click', createEffect)
  document.removeEventListener('mousemove', handleMouseMove)
  if (animationFrame) cancelAnimationFrame(animationFrame)
  document.body.style.cursor = ''
})
</script>

<style scoped>
.click-effects {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 9999;
}

/* ===== 自定义光标 ===== */
.custom-cursor {
  position: fixed;
  width: 8px;
  height: 8px;
  background: var(--color-primary, #2dd4bf);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
  z-index: 10000;
  box-shadow: 0 0 10px var(--color-primary, #2dd4bf),
              0 0 20px rgba(45, 212, 191, 0.5);
  transition: width 0.2s, height 0.2s, background 0.2s;
}

.custom-cursor.hover {
  width: 16px;
  height: 16px;
  background: rgba(45, 212, 191, 0.3);
}

.custom-cursor-ring {
  position: fixed;
  width: 36px;
  height: 36px;
  border: 1.5px solid rgba(45, 212, 191, 0.6);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  pointer-events: none;
  z-index: 9999;
  transition: width 0.25s, height 0.25s, border-color 0.25s, background 0.25s;
}

.custom-cursor-ring.hover {
  width: 50px;
  height: 50px;
  border-color: var(--color-primary, #2dd4bf);
  background: rgba(45, 212, 191, 0.08);
}

/* ===== 鼠标移动拖尾波纹 ===== */
.trail-ripple {
  position: absolute;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 1px solid rgba(45, 212, 191, 0.4);
  transform: translate(-50%, -50%);
  pointer-events: none;
  animation: trailFade 0.6s ease-out forwards;
}

@keyframes trailFade {
  0% {
    width: 8px;
    height: 8px;
    opacity: 0.8;
    border-color: rgba(45, 212, 191, 0.6);
  }
  100% {
    width: 40px;
    height: 40px;
    opacity: 0;
    border-color: rgba(45, 212, 191, 0);
  }
}

/* ===== 点击效果 ===== */
.click-effect {
  position: absolute;
  transform: translate(-50%, -50%);
}

.ripple {
  display: block;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid var(--color);
  animation: rippleEffect 1s ease-out forwards;
}

.ripple-delay {
  animation-delay: 0.1s;
}

.tech-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  border-radius: 50%;
  border: 1px solid var(--color);
  animation: techRingEffect 1s ease-out forwards;
}

.tech-ring-1 {
  width: 10px;
  height: 10px;
  margin: -5px 0 0 -5px;
}

.tech-ring-2 {
  width: 10px;
  height: 10px;
  margin: -5px 0 0 -5px;
  animation-delay: 0.15s;
}

.tech-ring-3 {
  width: 10px;
  height: 10px;
  margin: -5px 0 0 -5px;
  animation-delay: 0.3s;
}

.tech-center {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 6px;
  height: 6px;
  margin: -3px 0 0 -3px;
  border-radius: 50%;
  background: var(--color);
  animation: techCenterEffect 0.8s ease-out forwards;
}

.tech-corner {
  position: absolute;
  width: 8px;
  height: 8px;
  border-color: var(--color);
  animation: techCornerEffect 0.8s ease-out forwards;
}

.tech-corner-1 {
  top: -4px;
  left: -4px;
  border-top: 2px solid;
  border-left: 2px solid;
}

.tech-corner-2 {
  top: -4px;
  right: -4px;
  border-top: 2px solid;
  border-right: 2px solid;
}

.tech-corner-3 {
  bottom: -4px;
  left: -4px;
  border-bottom: 2px solid;
  border-left: 2px solid;
}

.tech-corner-4 {
  bottom: -4px;
  right: -4px;
  border-bottom: 2px solid;
  border-right: 2px solid;
}

.particle {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 4px;
  height: 4px;
  margin: -2px 0 0 -2px;
  border-radius: 50%;
  background: var(--color);
  animation: particleEffect 0.8s ease-out forwards;
}

@keyframes rippleEffect {
  0% {
    width: 0;
    height: 0;
    opacity: 1;
    transform: scale(0);
  }
  100% {
    width: 100px;
    height: 100px;
    opacity: 0;
    transform: scale(2);
  }
}

@keyframes techRingEffect {
  0% {
    width: 10px;
    height: 10px;
    margin: -5px 0 0 -5px;
    opacity: 1;
  }
  100% {
    width: 120px;
    height: 120px;
    margin: -60px 0 0 -60px;
    opacity: 0;
  }
}

@keyframes techCenterEffect {
  0% {
    transform: scale(1);
    opacity: 1;
    box-shadow: 0 0 0 0 var(--color);
  }
  50% {
    transform: scale(1.5);
    box-shadow: 0 0 20px 5px var(--color);
  }
  100% {
    transform: scale(2);
    opacity: 0;
    box-shadow: 0 0 0 0 transparent;
  }
}

@keyframes techCornerEffect {
  0% {
    transform: scale(0);
    opacity: 1;
  }
  30% {
    transform: scale(1);
    opacity: 1;
  }
  100% {
    transform: scale(2);
    opacity: 0;
  }
}

@keyframes particleEffect {
  0% {
    transform: rotate(var(--angle)) translateY(0) scale(1);
    opacity: 1;
  }
  100% {
    transform: rotate(var(--angle)) translateY(60px) scale(0);
    opacity: 0;
  }
}
</style>
