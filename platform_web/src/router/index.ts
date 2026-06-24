import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'

// Token 存储 key
const ACCESS_TOKEN_KEY = 'access_token'

// 清理旧的 token key（兼容性处理）
const LEGACY_TOKEN_KEYS = ['token']
;(() => {
  LEGACY_TOKEN_KEYS.forEach(key => {
    if (localStorage.getItem(key)) {
      localStorage.removeItem(key)
    }
  })
})()

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true },
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/DashboardView.vue'),
        meta: { title: '仪表盘' }
      },
      {
        path: 'users/admin',
        name: 'AdminUsers',
        component: () => import('@/views/users/AdminUsersView.vue'),
        meta: { title: '创作管理员' }
      },
      {
        path: 'users/sub',
        name: 'SubUsers',
        component: () => import('@/views/users/SubUsersView.vue'),
        meta: { title: '创作员管理' }
      },
      {
        path: 'templates/list',
        name: 'TemplatesList',
        component: () => import('@/views/templates/TemplateListView.vue'),
        meta: { title: '模板创作库' }
      },
      {
        path: 'materials',
        name: 'Materials',
        component: () => import('@/views/materials/MaterialListView.vue'),
        meta: { title: '素材对标库' }
      },
      {
        path: 'settings/creative-seeds',
        name: 'CreativeSeeds',
        component: () => import('@/views/settings/CreativeSeedView.vue'),
        meta: { title: '创意种子库管理' }
      },
      {
        path: 'generation/create',
        name: 'GenerationCreate',
        component: () => import('@/views/generation/GenerationCreateView.vue'),
        meta: { title: '创建任务' }
      },
      {
        path: 'generation/list',
        name: 'GenerationList',
        component: () => import('@/views/generation/GenerationListView.vue'),
        meta: { title: '任务列表' }
      },
      {
        path: 'generation/detail/:id',
        name: 'GenerationDetail',
        component: () => import('@/views/generation/GenerationDetailView.vue'),
        meta: { title: '任务详情' }
      },
      {
        path: 'scheduled-tasks',
        name: 'ScheduledTaskList',
        component: () => import('@/views/scheduled-tasks/ScheduledTaskListView.vue'),
        meta: { title: '定时任务管理' }
      },
      {
        path: 'scheduled-tasks/create',
        name: 'ScheduledTaskCreate',
        component: () => import('@/views/scheduled-tasks/ScheduledTaskCreateView.vue'),
        meta: { title: '创建定时任务' }
      },
      {
        path: 'scheduled-tasks/edit/:id',
        name: 'ScheduledTaskEdit',
        component: () => import('@/views/scheduled-tasks/ScheduledTaskCreateView.vue'),
        meta: { title: '编辑定时任务' }
      },
      {
        path: 'scheduled-tasks/:id',
        name: 'ScheduledTaskDetail',
        component: () => import('@/views/scheduled-tasks/ScheduledTaskDetailView.vue'),
        meta: { title: '定时任务详情' }
      },
      {
        path: 'scheduled-tasks/:taskId/executions',
        name: 'ScheduledTaskExecutions',
        component: () => import('@/views/scheduled-tasks/ScheduledTaskExecutionListView.vue'),
        meta: { title: '执行历史' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/settings/SettingsView.vue'),
        meta: { title: '系统设置' }
      },
      {
        path: 'logs/operation',
        name: 'OperationLogs',
        component: () => import('@/views/logs/OperationLogListView.vue'),
        meta: { title: '操作日志', roles: ['super_admin'] }
      }
    ]
  },
  // 404 页面重定向到登录页
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 标记是否已经初始化过用户信息
let userInitialized = false

// 角色权限映射：路由需要的角色列表
const routeRoles: Record<string, Array<'super_admin' | 'operator' | 'sub_user'>> = {
  '/users/admin': ['super_admin'],  // 只有超级管理员可以访问创作管理员
  '/users/sub': ['super_admin', 'operator'],  // 超级管理员和创作管理员可以访问创作员管理
  '/logs/operation': ['super_admin'],  // 只有超级管理员可以访问操作日志
  '/templates/list': ['super_admin', 'operator'],  // 只有超级管理员和创作管理员可以访问模板库
  '/materials': ['super_admin', 'operator'],  // 只有超级管理员和创作管理员可以访问素材库
  '/settings/creative-seeds': ['super_admin', 'operator'],  // 只有超级管理员和创作管理员可以访问创意种子库
  '/generation/create': ['super_admin', 'operator'],  // 只有超级管理员和创作管理员可以创建任务
  '/scheduled-tasks': ['super_admin', 'operator'],  // 只有超级管理员和创作管理员可以访问定时任务管理
  '/scheduled-tasks/create': ['super_admin', 'operator'],  // 只有超级管理员和创作管理员可以创建定时任务
}

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()
  const themeStore = useThemeStore()
  const token = localStorage.getItem(ACCESS_TOKEN_KEY)
  const isLoggedIn = !!token

  // 需要认证的路由（默认需要认证，除非显式设置 requiresAuth: false）
  const requiresAuth = to.meta.requiresAuth !== false

  // 如果有token但还没初始化用户信息，先从服务器获取
  if (isLoggedIn && !userInitialized) {
    try {
      await authStore.fetchUser()
      // 用户信息加载完成后，重新加载对应的主题设置
      themeStore.reloadThemeForCurrentUser()
    } catch {
      // 获取用户信息失败会在 fetchUser 内部处理
    }
    userInitialized = true
  }

  if (requiresAuth && !isLoggedIn) {
    // 未登录，重定向到登录页
    userInitialized = false
    next({
      path: '/login',
      query: { redirect: to.fullPath }
    })
    return
  }

  // 已登录状态访问登录页，重定向到首页
  if (to.path === '/login' && isLoggedIn) {
    next('/dashboard')
    return
  }

  // 角色权限检查
  if (isLoggedIn && authStore.userRole) {
    const allowedRoles = routeRoles[to.path]
    if (allowedRoles && !allowedRoles.includes(authStore.userRole)) {
      // 无权限访问，重定向到仪表盘
      next('/dashboard')
      return
    }
  }

  next()
})

export default router
