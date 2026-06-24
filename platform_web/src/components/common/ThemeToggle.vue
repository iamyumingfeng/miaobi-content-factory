<template>
  <el-tooltip :content="tooltipText" placement="bottom">
    <button class="theme-toggle" @click="toggleTheme" :aria-label="ariaLabel">
      <el-icon v-if="themeStore.mode === 'light'" class="icon sun-icon">
        <Sunny />
      </el-icon>
      <el-icon v-else class="icon moon-icon">
        <Moon />
      </el-icon>
    </button>
  </el-tooltip>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Sunny, Moon } from '@element-plus/icons-vue'
import { useThemeStore } from '@/stores/theme'

const themeStore = useThemeStore()

const tooltipText = computed(() => {
  return themeStore.mode === 'light' ? '切换到夜间模式' : '切换到日间模式'
})

const ariaLabel = computed(() => {
  return themeStore.mode === 'light' ? 'Switch to dark mode' : 'Switch to light mode'
})

const toggleTheme = () => {
  themeStore.toggleTheme()
}
</script>

<style lang="scss" scoped>
.theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: transparent;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background: var(--bg-tertiary);
  }

  .icon {
    font-size: 20px;
    color: var(--text-primary);
    transition: transform 0.3s ease, color 0.3s ease;
  }

  &:hover .icon {
    transform: rotate(15deg);
  }
}
</style>
