<template>
  <div class="auth-wrap">
    <!-- 左栏：图片背景 + 品牌大字 -->
    <aside class="auth-brand">
      <div class="brand-mask"></div>
      <div class="brand-content">
        <h1 class="brand-title">东方智喘</h1>
        <p class="brand-subtitle">哮喘方剂智能分析平台</p>
        <div class="brand-divider"></div>
        <p class="brand-tagline">
          基于 PU 学习 · GSEA 富集分析 · 网络药理学<br/>
          中医药现代化科研系统
        </p>
      </div>
    </aside>

    <!-- 右栏：侧边栏深色主题表单区 -->
    <main class="auth-form">
      <div class="form-inner">
        <div class="form-head">
          <h3>欢迎回来</h3>
          <p class="form-desc">请登录您的账户以继续</p>
        </div>

        <!-- Tab 切换 -->
        <div class="tab-switch">
          <button
            :class="['tab-btn', { active: activeTab === 'login' }]"
            @click="activeTab = 'login'"
          >
            登录
          </button>
          <button
            :class="['tab-btn', { active: activeTab === 'register' }]"
            @click="activeTab = 'register'"
          >
            注册
          </button>
        </div>

        <!-- 登录表单 -->
        <div v-show="activeTab === 'login'" class="form-panel">
          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            label-position="top"
            @keyup.enter="handleLogin"
          >
            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="请输入您的用户名"
                size="large"
                :prefix-icon="User"
              />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                :prefix-icon="Lock"
                show-password
              />
            </el-form-item>
            <el-button
              class="submit-btn"
              type="primary"
              size="large"
              :loading="loading"
              @click="handleLogin"
            >
              登 录
            </el-button>
          </el-form>

          <div class="guest-line">
            <span class="guest-tip">想快速体验完整功能？</span>
            <button class="guest-btn" @click="fillGuestAccount">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 4a4 4 0 1 0 4 4 4 4 0 0 0-4-4Zm0 10c-4 0-7 2-7 5v1h14v-1c0-3-3-5-7-5Z" fill="currentColor"/>
              </svg>
              体验测试账号
            </button>
            <span class="guest-hint">账号：myasw / 密码：myasw2026</span>
          </div>
        </div>

        <!-- 注册表单 -->
        <div v-show="activeTab === 'register'" class="form-panel">
          <el-form
            ref="registerFormRef"
            :model="registerForm"
            :rules="registerRules"
            label-position="top"
            @keyup.enter="handleRegister"
          >
            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="registerForm.username"
                placeholder="请设置用户名"
                size="large"
                :prefix-icon="User"
              />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="请设置密码（至少6位）"
                size="large"
                :prefix-icon="Lock"
                show-password
              />
            </el-form-item>
            <el-form-item label="邮箱（选填）" prop="email">
              <el-input
                v-model="registerForm.email"
                placeholder="请输入邮箱"
                size="large"
                :prefix-icon="Message"
              />
            </el-form-item>
            <el-button
              class="submit-btn"
              type="primary"
              size="large"
              :loading="loading"
              @click="handleRegister"
            >
              注 册
            </el-button>
          </el-form>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'
import { login, register } from '../api'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const { setAuth } = useAuth()

const activeTab = ref('login')
const loading = ref(false)

const loginFormRef = ref()
const registerFormRef = ref()

const loginForm = reactive({
  username: '',
  password: ''
})

const registerForm = reactive({
  username: '',
  password: '',
  email: ''
})

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const registerRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }]
}

async function handleLogin() {
  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const data = await login(loginForm.username, loginForm.password)
      setAuth(data.token, data.user)
      ElMessage.success('登录成功')
      router.push('/')
    } catch (e) {
      ElMessage.error(e.message || '登录失败')
    } finally {
      loading.value = false
    }
  })
}

async function handleRegister() {
  await registerFormRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const data = await register(registerForm.username, registerForm.password, registerForm.email)
      setAuth(data.token, data.user)
      ElMessage.success('注册成功，已自动登录')
      router.push('/')
    } catch (e) {
      ElMessage.error(e.message || '注册失败')
    } finally {
      loading.value = false
    }
  })
}

function fillGuestAccount() {
  loginForm.username = 'myasw'
  loginForm.password = 'myasw2026'
}
</script>

<style scoped>
.auth-wrap {
  min-height: 100vh;
  display: flex;
  background: #0f172a;
  width: 100%;
}

/* ===== 左栏：图片背景 + 品牌文字层 ===== */
.auth-brand {
  flex: 1;
  min-width: 0;
  background-image: url('/现代国风暗色科技感背景.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  position: relative;
  overflow: hidden;
}

/* 图片上的暗化遮罩（确保大字可读） */
.brand-mask {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    rgba(15, 23, 42, 0.15) 0%,
    rgba(15, 23, 42, 0.35) 45%,
    rgba(15, 23, 42, 0.65) 78%,
    rgba(15, 23, 42, 0.9) 100%
  );
  z-index: 1;
  pointer-events: none;
}

/* 品牌文案区（图片底部左对齐，与右栏视觉平衡） */
.brand-content {
  position: absolute;
  z-index: 2;
  left: clamp(32px, 7vw, 96px);
  bottom: clamp(80px, 18vh, 220px);
  max-width: 620px;
  color: #fff;
  pointer-events: none;
  animation: brand-fade-in 1.1s cubic-bezier(0.22, 1, 0.36, 1) 0.1s both;
}

@keyframes brand-fade-in {
  from { opacity: 0; transform: translateY(24px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ⭐ 东方智喘 4 个大字 */
.brand-title {
  font-size: clamp(48px, 7vw, 96px);
  font-weight: 900;
  letter-spacing: 0.12em;
  line-height: 1.1;
  margin: 0 0 16px 0;
  color: #ffffff;
  /* 三层叠加：浅金描边 + 双层阴影，形成立体浮刻效果 */
  -webkit-text-stroke: 1.2px rgba(255, 215, 130, 0.55);
  text-shadow:
    0 2px 0 rgba(0, 0, 0, 0.35),
    0 12px 32px rgba(0, 0, 0, 0.55),
    0 0 40px rgba(45, 212, 191, 0.2);
  font-family: "PingFang SC", "Microsoft YaHei", "STHeiti", "SimHei", -apple-system, system-ui, sans-serif;
  position: relative;
  isolation: isolate;
  display: inline-block;
}

/* 流光叠加层（覆盖在原字之上，clip 到文字区域形成扫光） */
.brand-title::before {
  content: "东方智喘";
  position: absolute;
  inset: 0;
  z-index: 2;
  font-size: inherit;
  font-weight: inherit;
  letter-spacing: inherit;
  line-height: inherit;
  -webkit-text-stroke: 0;
  text-shadow: none;
  background: linear-gradient(
    110deg,
    transparent 30%,
    rgba(255, 255, 255, 0.85) 46%,
    rgba(255, 233, 173, 0.95) 50%,
    rgba(255, 255, 255, 0.85) 54%,
    transparent 70%
  );
  background-size: 220% 100%;
  background-position: 220% 0;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: brand-shimmer 6s ease-in-out infinite;
  pointer-events: none;
}

@keyframes brand-shimmer {
  0%   { background-position: 220% 0 }
  45%  { background-position: -120% 0 }
  100% { background-position: -120% 0 }
}

.brand-title::after {
  content: "";
  display: block;
  width: 0.9em;
  height: 3px;
  margin-top: 10px;
  background: linear-gradient(90deg, #2dd4bf 0%, rgba(45,212,191,0) 100%);
  border-radius: 2px;
  position: relative;
  z-index: 1;
}

/* 副标题 */
.brand-subtitle {
  font-size: clamp(18px, 2vw, 26px);
  font-weight: 600;
  letter-spacing: 0.25em;
  color: rgba(255, 255, 255, 0.92);
  margin: 0 0 20px 0;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.45);
}

/* 分隔线 */
.brand-divider {
  width: 64px;
  height: 2px;
  background: linear-gradient(90deg, #2dd4bf 0%, rgba(45,212,191,0) 100%);
  margin-bottom: 20px;
  border-radius: 2px;
}

/* 宣传语 */
.brand-tagline {
  font-size: clamp(13px, 1.25vw, 16px);
  line-height: 1.85;
  letter-spacing: 0.05em;
  color: rgba(203, 213, 225, 0.9);
  margin: 0;
  text-shadow: 0 1px 8px rgba(0, 0, 0, 0.5);
}

/* ===== 右栏：侧边栏深色主题 ===== */
.auth-form {
  width: 540px;
  flex-shrink: 0;
  background: linear-gradient(180deg, #0f172a 0%, #12233d 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 52px;
  position: relative;
}
.auth-form::before,
.auth-form::after {
  content: "";
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  opacity: 0.35;
  pointer-events: none;
}
.auth-form::before {
  width: 360px;
  height: 360px;
  background: #2dd4bf;
  top: -140px;
  right: -100px;
}
.auth-form::after {
  width: 280px;
  height: 280px;
  background: #38bdf8;
  bottom: -120px;
  left: -80px;
  opacity: 0.2;
}

.form-inner {
  width: 100%;
  max-width: 400px;
  z-index: 1;
}

.form-head {
  margin-bottom: 26px;
}
.form-head h3 {
  font-size: 28px;
  font-weight: 700;
  color: #f1f5f9;
  line-height: 1.3;
  margin-bottom: 6px;
}
.form-head .form-desc {
  font-size: 13px;
  color: #94a3b8;
}

/* Tab */
.tab-switch {
  display: flex;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 4px;
  margin-bottom: 24px;
  background: rgba(30, 41, 59, 0.7);
}
.tab-btn {
  flex: 1;
  height: 38px;
  border: none;
  background: transparent;
  color: #94a3b8;
  font-size: 14px;
  font-weight: 500;
  border-radius: 7px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.tab-btn.active {
  background: rgba(45, 212, 191, 0.1);
  color: #2dd4bf;
  box-shadow: inset 2px 0 0 0 #2dd4bf, 0 1px 3px rgba(0, 0, 0, 0.2);
}

/* 表单元素 */
.form-panel :deep(.el-form-item__label) {
  font-size: 13px;
  font-weight: 500;
  color: #cbd5e1;
  padding-bottom: 6px;
  line-height: 1;
}
.form-panel :deep(.el-input__wrapper) {
  border-radius: 10px;
  padding: 4px 14px;
  box-shadow: 0 0 0 1px rgba(45, 212, 191, 0.15) inset !important;
  background: rgba(30, 41, 59, 0.7);
  transition: all 0.2s ease;
}
.form-panel :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(45, 212, 191, 0.35) inset !important;
}
.form-panel :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px rgba(45, 212, 191, 0.8) inset !important;
  background: rgba(30, 41, 59, 0.9);
}
.form-panel :deep(.el-input__inner) {
  color: #f1f5f9;
  font-size: 14px;
  background: transparent;
}
.form-panel :deep(.el-input__inner::placeholder) {
  color: #64748b;
}
.form-panel :deep(.el-input__prefix-inner .el-icon) {
  color: #2dd4bf !important;
}
.form-panel :deep(.el-input__suffix-inner .el-icon) {
  color: #94a3b8 !important;
}
.form-panel :deep(.el-form-item) {
  margin-bottom: 18px;
}

/* 提交按钮（侧边栏风格 2dd4bf） */
.submit-btn {
  width: 100%;
  height: 44px;
  margin-top: 6px;
  border-radius: 10px;
  background: linear-gradient(135deg, #2dd4bf 0%, #14b8a6 100%);
  border: none;
  color: #0f172a;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 1px;
  transition: all 0.2s ease;
  box-shadow: 0 4px 14px rgba(45, 212, 191, 0.25);
}
.submit-btn:hover,
.submit-btn:focus {
  background: linear-gradient(135deg, #5eead4 0%, #2dd4bf 100%);
  color: #0f172a;
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(45, 212, 191, 0.35);
}
.submit-btn:active {
  transform: translateY(0);
}

/* 体验账号 */
.guest-line {
  margin-top: 28px;
  text-align: center;
}
.guest-tip {
  display: block;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 10px;
}
.guest-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 20px;
  height: 40px;
  border-radius: 10px;
  border: 1px solid rgba(45, 212, 191, 0.25);
  background: rgba(45, 212, 191, 0.08);
  color: #2dd4bf;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}
.guest-btn:hover {
  background: rgba(45, 212, 191, 0.15);
  border-color: rgba(45, 212, 191, 0.4);
  transform: translateY(-1px);
}
.guest-btn svg {
  width: 16px;
  height: 16px;
}
.guest-hint {
  display: block;
  font-size: 11px;
  color: #64748b;
  margin-top: 8px;
}

/* ===== 响应式 ===== */
@media (max-width: 960px) {
  .auth-wrap {
    flex-direction: column;
  }
  .auth-brand {
    min-height: 320px;
  }
  .brand-content {
    left: 28px !important;
    bottom: 32px !important;
    right: 28px;
    max-width: none;
  }
  .brand-title {
    font-size: 48px !important;
    letter-spacing: 0.08em;
  }
  .brand-subtitle {
    font-size: 16px !important;
    letter-spacing: 0.15em;
  }
  .auth-form {
    width: 100%;
    padding: 36px 24px;
  }
  .form-inner {
    max-width: 100%;
  }
  .form-head h3 {
    font-size: 24px;
  }
}
@media (max-width: 520px) {
  .auth-brand {
    min-height: 240px;
  }
  .brand-content {
    left: 20px !important;
    bottom: 20px !important;
    right: 20px;
  }
  .brand-title {
    font-size: 36px !important;
    letter-spacing: 0.06em;
    margin-bottom: 10px;
  }
  .brand-title::after {
    height: 2px;
    margin-top: 6px;
  }
  .brand-subtitle {
    font-size: 13px !important;
    letter-spacing: 0.1em;
    margin-bottom: 12px;
  }
  .brand-divider {
    width: 40px;
    margin-bottom: 12px;
  }
  .brand-tagline {
    font-size: 11px !important;
    line-height: 1.7;
  }
  .auth-form {
    padding: 28px 18px;
  }
  .form-head h3 {
    font-size: 22px;
  }
}
</style>
