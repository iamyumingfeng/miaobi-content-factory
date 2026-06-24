<template>
  <router-view />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

// 监听账号被禁用事件
const handleAccountDisabled = (event: CustomEvent) => {
  const message = event.detail?.message || '账号已被禁用，请联系管理员'
  ElMessage.error(message)
}

onMounted(() => {
  window.addEventListener('account-disabled', handleAccountDisabled as EventListener)
})

onUnmounted(() => {
  window.removeEventListener('account-disabled', handleAccountDisabled as EventListener)
})
</script>

<style lang="scss">
#app {
  width: 100%;
  height: 100vh;
}
</style>
