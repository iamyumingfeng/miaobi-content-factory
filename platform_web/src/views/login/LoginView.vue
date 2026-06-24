<template>
  <div class="login-page">
    <!-- 装饰性背景光晕 -->
    <div class="bg-glow glow-1"></div>
    <div class="bg-glow glow-2"></div>

    <div class="login-container">
      <!-- 左侧品牌区域 -->
      <div class="brand-section">
        <!-- 顶部装饰线 -->
        <div class="brand-accent"></div>
        
        <div class="brand-content">
          <div class="logo-wrapper">
            <div class="logo-container">
              <svg width="52" height="52" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect width="64" height="64" rx="16" fill="url(#logoGrad)"/>
                <path d="M20 32L28 40L44 24" stroke="white" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
                <defs>
                  <linearGradient id="logoGrad" x1="0" y1="0" x2="64" y2="64">
                    <stop offset="0%" stop-color="var(--color-primary)"/>
                    <stop offset="100%" stop-color="var(--color-primary-light)"/>
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <div class="logo-badge">v2.0</div>
          </div>

          <div class="brand-hero">
            <h1 class="brand-title">
              <span class="title-line">妙笔内容工场</span>
              <span class="title-sub">Miaobi Content Studio</span>
            </h1>
            <p class="brand-description">
              AI 驱动的全链路内容生产与分发平台，<br/>
              赋能新媒体运营，让每一次创作都精准高效
            </p>
          </div>

          <div class="brand-features">
            <div class="feature-item">
              <div class="feature-icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                </svg>
              </div>
              <div class="feature-text">
                <div class="feature-title">智能创作</div>
                <div class="feature-desc">模板化批量生成，多模型支持</div>
              </div>
            </div>

            <div class="feature-item">
              <div class="feature-icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="12,6 12,12 16,14"/>
                </svg>
              </div>
              <div class="feature-text">
                <div class="feature-title">高效分发</div>
                <div class="feature-desc">一键推送至创作者，支持确认发布</div>
              </div>
            </div>

            <div class="feature-item">
              <div class="feature-icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
              </div>
              <div class="feature-text">
                <div class="feature-title">团队协作</div>
                <div class="feature-desc">多角色权限管理，统一素材与任务</div>
              </div>
            </div>
          </div>

          <!-- 底部装饰 -->
          <div class="brand-footer">
            <span class="brand-footer-text">© 2026 Miaobi · 安全可靠的企业级平台</span>
          </div>
        </div>
      </div>

      <!-- 右侧登录区域 -->
      <div class="form-section">
        <div class="form-wrapper">
          <div class="form-card">
            <div class="form-header">
              <div class="header-icon">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" stroke-width="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </div>
              <h2 class="form-title">欢迎登录</h2>
              <p class="form-subtitle">登录您的账号，开启智能创作之旅</p>
            </div>

            <el-form
              ref="loginFormRef"
              :model="loginForm"
              :rules="loginRules"
              class="login-form"
              size="large"
            >
              <el-form-item prop="username">
                <div class="input-label">用户名</div>
                <el-input
                  v-model="loginForm.username"
                  placeholder="请输入用户名"
                  :prefix-icon="User"
                  clearable
                  class="custom-input"
                />
              </el-form-item>

              <el-form-item prop="password">
                <div class="input-label">密码</div>
                <el-input
                  v-model="loginForm.password"
                  type="password"
                  placeholder="请输入密码"
                  :prefix-icon="Lock"
                  show-password
                  @keyup.enter="handleLogin"
                  class="custom-input"
                />
              </el-form-item>

              <el-form-item class="button-item">
                <el-button
                  type="primary"
                  class="login-button"
                  :loading="loading"
                  @click="handleLogin"
                >
                  {{ loading ? '登录中...' : '登 录' }}
                </el-button>
              </el-form-item>
            </el-form>

            <div class="form-footer">
              <div class="security-notice">
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M8 1L2 3.5V7.5C2 11.09 4.56 14.44 8 15.5C11.44 14.44 14 11.09 14 7.5V3.5L8 1Z" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M5.5 8L7 9.5L10.5 6" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span>连续5次登录失败将锁定账号15分钟</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loginFormRef = ref()
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  await loginFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      loading.value = true
      try {
        await authStore.login(loginForm.username, loginForm.password)
        ElMessage.success('登录成功')
        await new Promise(resolve => setTimeout(resolve, 100))
        router.replace('/dashboard')
      } catch (error: any) {
        const errorMsg = error?.message || '登录失败，请检查用户名和密码'
        ElMessage.error(errorMsg)
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style lang="scss" scoped>
@import '@/assets/styles/variables.scss';

// ============================================
// 页面容器
// ============================================
.login-page {
  position: relative;
  width: 100%;
  height: 100vh;
  background: var(--color-bg-primary);
  overflow: hidden;
}

// ============================================
// 装饰背景光晕
// ============================================
.bg-glow {
  position: fixed;
  border-radius: 50%;
  filter: blur(120px);
  opacity: 0.4;
  pointer-events: none;
  z-index: 0;

  &.glow-1 {
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, var(--color-primary-bg), transparent 70%);
    top: -200px;
    left: -100px;
  }

  &.glow-2 {
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(var(--color-primary-rgb, 22, 119, 255), 0.06), transparent 70%);
    bottom: -100px;
    right: -50px;
  }
}

// ============================================
// 主布局
// ============================================
.login-container {
  position: relative;
  z-index: 1;
  display: flex;
  width: 100%;
  height: 100vh;
}

// ============================================
// 左侧品牌区 (55% 宽度)
// ============================================
.brand-section {
  flex: 0 0 55%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 80px 72px;
  position: relative;
  background: linear-gradient(160deg, 
    var(--color-primary-bg) 0%, 
    var(--color-bg-primary) 40%, 
    var(--color-bg-secondary) 100%
  );
  border-right: 1px solid var(--color-border-default);

  // 装饰性细线
  .brand-accent {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg,
      transparent 0%,
      var(--color-primary) 20%,
      var(--color-primary-light) 50%,
      var(--color-primary) 80%,
      transparent 100%
    );
  }
}

.brand-content {
  max-width: 480px;
  width: 100%;
  display: flex;
  flex-direction: column;
  min-height: 560px;
}

// ============================================
// Logo & 品牌标识
// ============================================
.logo-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 14px;
  margin-bottom: 48px;
}

.logo-container {
  display: inline-flex;
  filter: drop-shadow(0 8px 24px rgba(var(--color-primary-rgb, 22, 119, 255), 0.2));
}

.logo-badge {
  font-family: var(--font-family-heading);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-primary);
  background: var(--color-primary-bg);
  padding: 2px 8px;
  border-radius: 10px;
  letter-spacing: 0.05em;
}

// ============================================
// 品牌文案
// ============================================
.brand-hero {
  margin-bottom: 56px;
}

.brand-title {
  margin: 0 0 20px 0;

  .title-line {
    display: block;
    font-family: var(--font-family-heading);
    font-size: 44px;
    font-weight: 800;
    color: var(--color-text-primary);
    line-height: 1.1;
    letter-spacing: -0.03em;
  }

  .title-sub {
    display: block;
    font-family: var(--font-family-heading);
    font-size: 14px;
    font-weight: 500;
    color: var(--color-text-muted);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-top: 8px;
  }
}

.brand-description {
  font-size: 16px;
  color: var(--color-text-secondary);
  line-height: 1.9;
  margin: 0;
}

// ============================================
// 功能特性
// ============================================
.brand-features {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 16px 20px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-default);
  border-radius: var(--radius-xl);
  transition: border-color 240ms ease, box-shadow 240ms ease, background 240ms ease;

  &:hover {
    background: var(--color-bg-primary);
    border-color: var(--color-primary);
    box-shadow: var(--shadow-md);
  }
}

.feature-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  background: var(--color-primary-bg);
  border-radius: var(--radius-lg);
  color: var(--color-primary);
}

.feature-text {
  flex: 1;
}

.feature-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 3px;
}

.feature-desc {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.4;
}

// ============================================
// 品牌底部
// ============================================
.brand-footer {
  margin-top: auto;
  padding-top: 40px;
}

.brand-footer-text {
  font-size: 12px;
  color: var(--color-text-muted);
}

// ============================================
// 右侧表单区 (45% 宽度)
// ============================================
.form-section {
  flex: 0 0 45%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 80px 60px;
  background: var(--color-bg-secondary);
}

.form-wrapper {
  width: 100%;
  max-width: 420px;
}

// ============================================
// 表单卡片
// ============================================
.form-card {
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border-default);
  border-radius: var(--radius-2xl);
  padding: 48px 44px 40px;
  box-shadow: var(--shadow-md);
}

// ============================================
// 表单头部
// ============================================
.form-header {
  text-align: center;
  margin-bottom: 40px;

  .header-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 56px;
    height: 56px;
    background: var(--color-primary-bg);
    border-radius: 50%;
    margin-bottom: 20px;
  }
}

.form-title {
  font-family: var(--font-family-heading);
  font-size: 26px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0 0 10px 0;
  letter-spacing: -0.01em;
}

.form-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.5;
}

// ============================================
// 表单输入
// ============================================
.login-form {
  .input-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--color-text-primary);
    margin-bottom: 8px;
    letter-spacing: 0.02em;
  }

  :deep(.el-form-item) {
    margin-bottom: 24px;
  }

  :deep(.el-input__wrapper) {
    padding: 12px 16px;
    background: var(--color-bg-secondary);
    border: 1.5px solid var(--color-border-default);
    border-radius: var(--radius-lg);
    box-shadow: none;
    transition: all 240ms cubic-bezier(0.4, 0, 0.2, 1);

    &:hover {
      background: var(--color-bg-tertiary);
      border-color: var(--color-border-hover);
    }

    &.is-focus {
      background: var(--color-bg-secondary);
      border-color: var(--color-primary);
      box-shadow: 0 0 0 3px var(--color-primary-bg);
    }
  }

  :deep(.el-input__inner) {
    font-size: 15px;
    font-weight: 400;
    color: var(--color-text-primary);

    &::placeholder {
      color: var(--color-text-muted);
    }
  }

  :deep(.el-input__prefix),
  :deep(.el-input__suffix) {
    color: var(--color-text-secondary);
  }

  :deep(.el-form-item__error) {
    font-size: 12px;
    padding-top: 6px;
  }

  .button-item {
    margin-top: 8px;
    margin-bottom: 0;
  }
}

// ============================================
// 登录按钮
// ============================================
.login-button {
  width: 100%;
  height: 50px;
  font-size: 16px;
  font-weight: 600;
  border-radius: var(--radius-lg);
  letter-spacing: 0.06em;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  border: none;
  box-shadow: 0 4px 16px rgba(var(--color-primary-rgb, 22, 119, 255), 0.25);
  transition: all 240ms ease;

  &:hover {
    box-shadow: 0 6px 24px rgba(var(--color-primary-rgb, 22, 119, 255), 0.35);
    transform: translateY(-1px);
  }

  &:active {
    transform: translateY(0);
  }
}

// ============================================
// 表单底部
// ============================================
.form-footer {
  margin-top: 36px;
  padding-top: 28px;
  border-top: 1px solid var(--color-border-default);
}

.security-notice {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 12px;
  color: var(--color-text-muted);

  svg {
    flex-shrink: 0;
    color: var(--color-primary);
  }
}

// ============================================
// 响应式
// ============================================
@media (max-width: 1200px) {
  .brand-section {
    flex: 0 0 50%;
    padding: 60px 48px;
  }
  .form-section {
    flex: 0 0 50%;
    padding: 60px 40px;
  }
  .brand-title .title-line {
    font-size: 36px;
  }
}

@media (max-width: 960px) {
  .brand-section {
    display: none;
  }
  .form-section {
    flex: 1;
    padding: 40px 28px;
  }
  .bg-glow {
    display: none;
  }
}

@media (max-width: 480px) {
  .form-section {
    padding: 24px 16px;
  }
  .form-card {
    padding: 36px 24px 32px;
  }
}
</style>
