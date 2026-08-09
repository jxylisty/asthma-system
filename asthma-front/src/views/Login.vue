<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <div class="logo-wrapper">
          <el-icon class="logo-icon"><Search /></el-icon>
        </div>
        <h1 class="login-title">东方智喘</h1>
        <p class="login-subtitle">基于入血预测的中医治疗儿童哮喘机制分析系统</p>
      </div>

      <el-tabs v-model="activeTab" class="login-tabs" stretch>
        <el-tab-pane label="登录" name="login">
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
                placeholder="请输入用户名"
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
              type="primary"
              size="large"
              class="submit-btn"
              :loading="loading"
              @click="handleLogin"
            >
              登 录
            </el-button>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
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
              type="primary"
              size="large"
              class="submit-btn"
              :loading="loading"
              @click="handleRegister"
            >
              注 册
            </el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, User, Lock, Message } from '@element-plus/icons-vue'
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
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 440px;
  background: #fff;
  border-radius: 20px;
  padding: 40px 36px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  margin-bottom: 16px;
}

.logo-icon {
  font-size: 32px;
  color: #fff;
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 8px;
}

.login-subtitle {
  font-size: 14px;
  color: #999;
  line-height: 1.5;
}

.login-tabs :deep(.el-tabs__header) {
  margin-bottom: 24px;
}

.login-tabs :deep(.el-tabs__item) {
  font-size: 16px;
  font-weight: 500;
}

.login-tabs :deep(.el-tabs__active-bar) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-tabs :deep(.el-form-item__label) {
  font-weight: 500;
  color: #333;
}

.submit-btn {
  width: 100%;
  margin-top: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 4px;
}

.submit-btn:hover {
  opacity: 0.9;
}
</style>
