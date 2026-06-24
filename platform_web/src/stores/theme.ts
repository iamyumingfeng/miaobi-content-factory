import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { useAuthStore } from './auth'

export type ThemeMode = 'light' | 'dark'

const THEME_KEY_PREFIX = 'aigc-platform-theme-'

// 获取当前用户的主题存储key
const getThemeKey = (userId: number | null): string => {
  if (userId) {
    return `${THEME_KEY_PREFIX}${userId}`
  }
  return `${THEME_KEY_PREFIX}guest`
}

export const useThemeStore = defineStore('theme', () => {
  const mode = ref<ThemeMode>('light')

  // 为指定用户初始化主题
  const initThemeForUser = (userId: number | null) => {
    const themeKey = getThemeKey(userId)
    const savedTheme = localStorage.getItem(themeKey) as ThemeMode | null
    if (savedTheme) {
      mode.value = savedTheme
    } else {
      // 检查系统偏好
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      mode.value = prefersDark ? 'dark' : 'light'
    }
    applyTheme()
  }

  // Initialize theme - 需要在用户信息加载后调用
  const initTheme = () => {
    const authStore = useAuthStore()
    initThemeForUser(authStore.user?.id || null)
  }

  // 当用户登录/登出时重新加载主题
  const reloadThemeForCurrentUser = () => {
    const authStore = useAuthStore()
    initThemeForUser(authStore.user?.id || null)
  }

  // Apply theme to DOM
  const applyTheme = () => {
    const html = document.documentElement
    if (mode.value === 'dark') {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
  }

  // Toggle theme
  const toggleTheme = () => {
    mode.value = mode.value === 'light' ? 'dark' : 'light'
  }

  // Watch for mode changes and persist to current user's key
  watch(mode, (newMode) => {
    const authStore = useAuthStore()
    const themeKey = getThemeKey(authStore.user?.id || null)
    localStorage.setItem(themeKey, newMode)
    applyTheme()
  })

  return {
    mode,
    initTheme,
    reloadThemeForCurrentUser,
    toggleTheme
  }
})
