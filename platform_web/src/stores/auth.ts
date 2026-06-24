/**
 * 用户认证状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { apiClient } from '../api/types'
import { useThemeStore } from './theme'

export interface UserInfo {
  id: number
  userid: string
  nickname: string | null
  display_name: string | null
  role: 'super_admin' | 'operator' | 'sub_user'
}

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const access_token = ref<string | null>(localStorage.getItem('access_token'))
  const user = ref<UserInfo | null>(null)
  const isInitialized = ref(false)

  // 计算属性
  const isLoggedIn = computed(() => !!access_token.value)
  const userRole = computed(() => user.value?.role || null)
  const userName = computed(() => user.value?.display_name || user.value?.nickname || user.value?.userid || '')

  // 从 localStorage 同步状态
  const syncFromLocalStorage = () => {
    const token = localStorage.getItem('access_token')
    const savedUser = localStorage.getItem('user')

    access_token.value = token

    if (savedUser) {
      try {
        user.value = JSON.parse(savedUser)
      } catch {
        user.value = null
      }
    } else {
      user.value = null
    }
  }

  // 初始化用户信息（从localStorage恢复）
  const initUser = () => {
    syncFromLocalStorage()

    // 监听 storage 变化（处理 API client 清除 token 的情况）
    window.addEventListener('storage', (event) => {
      if (event.key === 'access_token' || event.key === 'refresh_token' || event.key === 'user') {
        syncFromLocalStorage()
      }
    })
  }

  // 从服务器获取当前用户信息
  const fetchUser = async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      access_token.value = null
      user.value = null
      isInitialized.value = true
      return
    }

    try {
      const userData = await apiClient.getCurrentUser()
user.value = {
      id: userData.id,
      userid: userData.userid,
      nickname: userData.nickname ?? null,
      display_name: userData.display_name ?? null,
      role: userData.role as any
    }
      localStorage.setItem('user', JSON.stringify(user.value))
    } catch (error) {
      console.error('获取用户信息失败:', error)
      // 如果获取用户信息失败，使用 API client 统一清除状态
      syncFromLocalStorage()
    } finally {
      isInitialized.value = true
    }
  }

  // 登录
  const login = async (userid: string, password: string) => {
    const response = await apiClient.login(userid, password)

    // 保存token和用户信息
    access_token.value = response.access_token
    user.value = {
      id: response.user.id,
      userid: response.user.userid,
      nickname: response.user.nickname ?? null,
      display_name: response.user.display_name ?? null,
      role: response.user.role as 'super_admin' | 'operator' | 'sub_user'
    }

    // 持久化存储
    apiClient.setAccessToken(response.access_token)
    apiClient.setRefreshToken(response.refresh_token)
    apiClient.setTokenExpireTime(Date.now() + response.expires_in * 1000)
    localStorage.setItem('user', JSON.stringify(user.value))
    isInitialized.value = true

    return response
  }

  // 登出
  const logout = async () => {
    try {
      await apiClient.logout()
    } catch {
      // 忽略登出错误
    } finally {
      // 清除本地状态
      access_token.value = null
      user.value = null
      isInitialized.value = false
      apiClient.clearToken()
      localStorage.removeItem('user')
    }
  }

  // 更新用户信息
  const updateUser = (userInfo: Partial<UserInfo>) => {
    if (user.value) {
      user.value = { ...user.value, ...userInfo }
      localStorage.setItem('user', JSON.stringify(user.value))
    }
  }

  // 初始化
  initUser()

  // 监听用户变化，当用户登录/登出时重新加载主题
  watch(user, (newUser, oldUser) => {
    if (newUser?.id !== oldUser?.id) {
      const themeStore = useThemeStore()
      themeStore.reloadThemeForCurrentUser()
    }
  })

  return {
    access_token,
    user,
    isInitialized,
    isLoggedIn,
    userRole,
    userName,
    login,
    logout,
    updateUser,
    fetchUser
  }
})
