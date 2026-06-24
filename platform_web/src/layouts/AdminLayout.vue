<template>
  <el-container class="layout-container">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="layout-aside">
      <div class="logo-section">
        <el-icon v-if="isCollapse" :size="28" color="var(--color-primary)"><Promotion /></el-icon>
        <template v-else>
          <el-icon :size="24" color="var(--color-primary)"><Promotion /></el-icon>
          <span class="logo-text">妙笔内容工场</span>
        </template>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :unique-opened="true"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <template #title>AIGC看板</template>
        </el-menu-item>
        <el-sub-menu index="users" v-if="showUserMenu">
          <template #title>
            <el-icon><UserFilled /></el-icon>
            <span>用户管理</span>
          </template>
          <el-menu-item index="/users/admin" v-if="showAdminMenu">创作管理员</el-menu-item>
          <el-menu-item index="/users/sub">创作员管理</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="templates" v-if="showMaterialMenu">
          <template #title>
            <el-icon><Document /></el-icon>
            <span>素材管理</span>
          </template>
          <el-menu-item index="/settings/creative-seeds">创意种子库</el-menu-item>
          <el-menu-item index="/templates/list">模板创作库</el-menu-item>
          <el-menu-item index="/materials">素材对标库</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="generation">
          <template #title>
            <el-icon><MagicStick /></el-icon>
            <span>内容生成</span>
          </template>
          <el-menu-item v-if="showGenerationMenu && !isSuperAdmin" index="/generation/create">单次生成</el-menu-item>
          <el-menu-item v-if="showGenerationMenu" index="/scheduled-tasks">定时生成</el-menu-item>
          <el-menu-item index="/generation/list">任务列表</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="settings">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </template>
          <el-menu-item index="/settings">个人设置</el-menu-item>
          <el-menu-item v-if="isSuperAdmin" index="/logs/operation">操作日志</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <el-container class="layout-main">
      <el-header class="layout-header">
        <div class="header-left">
          <el-icon class="collapse-icon" @click="toggleCollapse">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentRoute.meta?.title">
              {{ currentRoute.meta?.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <ThemeToggle />
          <el-dropdown @command="handleCommand">
            <div class="user-info">
              <el-avatar :size="32" icon="UserFilled" />
              <span class="username">{{ displayUserName }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  个人设置
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="layout-content">
        <router-view v-slot="{ Component }">
          <keep-alive :include="['DashboardView', 'GenerationListView']">
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </el-main>

    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Promotion,
  Odometer,
  UserFilled,
  Document,
  MagicStick,
  Setting,
  Fold,
  Expand,
  ArrowDown,
  User,
  SwitchButton
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import ThemeToggle from '@/components/common/ThemeToggle.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const isCollapse = ref(false)
const currentRoute = computed(() => route)
const activeMenu = computed(() => route.path)
const displayUserName = computed(() => authStore.userName)
const userRole = computed(() => authStore.userRole)

// 权限检查
const isSuperAdmin = computed(() => userRole.value === 'super_admin')
const isSubUser = computed(() => userRole.value === 'sub_user')

// 是否显示用户管理菜单
const showUserMenu = computed(() => !isSubUser.value)
// 是否显示创作管理员菜单
const showAdminMenu = computed(() => isSuperAdmin.value)
// 是否显示素材管理菜单
const showMaterialMenu = computed(() => !isSubUser.value)
// 是否显示内容生成菜单
const showGenerationMenu = computed(() => !isSubUser.value)

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

const handleCommand = async (command: string) => {
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      // 清除登录状态
      await authStore.logout()
      ElMessage.success('已退出登录')
      // 跳转到登录页
      router.push('/login')
    } catch {
      // User cancelled
    }
  } else if (command === 'profile') {
    router.push('/settings')
  }
}
</script>

<style lang="scss" scoped>
.layout-container {
  width: 100%;
  height: 100vh;
}

// 侧边栏 - 浅色编辑风
.layout-aside {
  background: var(--color-bg-sidebar);
  border-right: 1px solid var(--color-border-default);
  transition: width 0.3s;
  overflow: hidden;
}

.logo-section {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 0 16px;
  border-bottom: 1px solid var(--color-border-default);
}

.logo-text {
  color: var(--color-text-sidebar);
  font-size: 16px;
  font-weight: 700;
  font-family: var(--font-family-heading);
  letter-spacing: -0.02em;
}

.sidebar-menu {
  border: none;
  background: var(--color-bg-sidebar);
  padding: 12px 10px;
}

:deep(.el-menu) {
  background-color: transparent;
  border-right: none;
}

:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  color: var(--color-text-sidebar) !important;
  border-radius: 12px;
  margin-bottom: 4px;
  height: 44px;
  line-height: 44px;
}

:deep(.el-menu-item:hover),
:deep(.el-sub-menu__title:hover) {
  background-color: var(--color-primary-bg) !important;
  color: var(--color-primary) !important;
}

:deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, var(--color-primary-bg) 0%, rgba(64, 158, 255, 0.06) 100%) !important;
  color: var(--color-primary) !important;
  font-weight: 600;
}

:deep(.el-menu--inline) {
  background-color: transparent !important;
}

:deep(.el-menu--inline .el-menu-item) {
  color: var(--color-text-sidebar-secondary) !important;
}

:deep(.el-menu--inline .el-menu-item:hover) {
  background-color: var(--color-primary-bg) !important;
  color: var(--color-primary) !important;
}

:deep(.el-menu--inline .el-menu-item.is-active) {
  background-color: var(--color-primary-bg) !important;
  color: var(--color-primary) !important;
}

:deep(.el-menu-item .el-icon),
:deep(.el-sub-menu__title .el-icon) {
  color: inherit !important;
}

:deep(.el-sub-menu__icon-arrow) {
  color: var(--color-text-sidebar-secondary) !important;
}

// 主内容区
.layout-main {
  display: flex;
  flex-direction: column;
  background: var(--color-bg-primary);
}

.layout-header {
  height: 64px;
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-default);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  z-index: 20;
  position: relative;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-icon {
  font-size: 20px;
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: color 0.25s ease;

  &:hover {
    color: var(--color-primary);
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;

  .username {
    color: var(--color-text-primary);
    font-size: 14px;
  }
}

.layout-content {
  flex: 1;
  padding: 28px 32px;
  overflow: auto;
  position: relative;
  z-index: 1;
}


</style>
