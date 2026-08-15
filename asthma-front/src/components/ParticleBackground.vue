<template>
  <canvas ref="canvasRef" class="particle-bg"></canvas>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const canvasRef = ref(null)
let ctx = null
let animationId = null
let particles = []
let mouse = { x: null, y: null, radius: 150 }

const config = {
  particleCount: 60,
  particleColor: 'rgba(45, 212, 191, 0.5)',
  lineColor: 'rgba(45, 212, 191, 0.1)',
  lineDistance: 120,
  speed: 0.6,
  minRadius: 1,
  maxRadius: 3
}

function initCanvas() {
  const canvas = canvasRef.value
  if (!canvas) return
  ctx = canvas.getContext('2d')
  resizeCanvas()
  initParticles()
}

function resizeCanvas() {
  const canvas = canvasRef.value
  if (!canvas) return
  canvas.width = window.innerWidth
  canvas.height = window.innerHeight
}

function initParticles() {
  particles = []
  const canvas = canvasRef.value
  if (!canvas) return

  for (let i = 0; i < config.particleCount; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * config.speed,
      vy: (Math.random() - 0.5) * config.speed,
      radius: Math.random() * (config.maxRadius - config.minRadius) + config.minRadius
    })
  }
}

function draw() {
  const canvas = canvasRef.value
  if (!ctx || !canvas) return

  ctx.clearRect(0, 0, canvas.width, canvas.height)

  // 更新粒子位置
  particles.forEach(p => {
    p.x += p.vx
    p.y += p.vy

    // 边界反弹
    if (p.x < 0 || p.x > canvas.width) p.vx *= -1
    if (p.y < 0 || p.y > canvas.height) p.vy *= -1

    // 鼠标交互：粒子被鼠标吸引/排斥
    if (mouse.x !== null && mouse.y !== null) {
      const dx = p.x - mouse.x
      const dy = p.y - mouse.y
      const dist = Math.sqrt(dx * dx + dy * dy)
      if (dist < mouse.radius) {
        const force = (mouse.radius - dist) / mouse.radius
        p.x += (dx / dist) * force * 2
        p.y += (dy / dist) * force * 2
      }
    }
  })

  // 绘制连线
  ctx.strokeStyle = config.lineColor
  ctx.lineWidth = 1
  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const dx = particles[i].x - particles[j].x
      const dy = particles[i].y - particles[j].y
      const dist = Math.sqrt(dx * dx + dy * dy)
      if (dist < config.lineDistance) {
        ctx.beginPath()
        ctx.moveTo(particles[i].x, particles[i].y)
        ctx.lineTo(particles[j].x, particles[j].y)
        ctx.stroke()
      }
    }
  }

  // 绘制粒子
  particles.forEach(p => {
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
    ctx.fillStyle = config.particleColor
    ctx.fill()
  })

  animationId = requestAnimationFrame(draw)
}

function handleMouseMove(e) {
  mouse.x = e.clientX
  mouse.y = e.clientY
}

function handleMouseLeave() {
  mouse.x = null
  mouse.y = null
}

function handleResize() {
  resizeCanvas()
  initParticles()
}

onMounted(() => {
  initCanvas()
  draw()
  window.addEventListener('mousemove', handleMouseMove)
  window.addEventListener('mouseleave', handleMouseLeave)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (animationId) cancelAnimationFrame(animationId)
  window.removeEventListener('mousemove', handleMouseMove)
  window.removeEventListener('mouseleave', handleMouseLeave)
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.particle-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
}
</style>
