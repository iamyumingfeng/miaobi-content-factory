<template>
  <div class="time-stats-cell">
    <template v-if="item.status === 'completed'">
      <div class="time-row">
        <span class="time-label">排队:</span>
        <span class="time-value">{{ formatDuration(item.queued_at, item.started_at) }}</span>
      </div>
      <div class="time-row">
        <span class="time-label">生成:</span>
        <span class="time-value success">{{ formatDuration(item.started_at, item.completed_at) }}</span>
      </div>
    </template>
    <template v-else-if="item.status === 'generating'">
      <div class="time-row">
        <span class="time-label">已运行:</span>
        <span class="time-value primary">{{ formatDuration(item.started_at) }}</span>
      </div>
    </template>
    <template v-else-if="item.status === 'queued'">
      <div class="time-row">
        <span class="time-label">已等待:</span>
        <span class="time-value warning">{{ formatDuration(item.queued_at) }}</span>
      </div>
    </template>
    <span v-else>-</span>
  </div>
</template>

<script setup lang="ts">
/**
 * 生成子任务时间统计组件 (GenerationItemTimeStats.vue)
 *
 * 展示单个生成子任务的耗时统计，包括：
 * - 排队时间（从入队到开始生成）
 * - 生成时间（从开始到完成）
 * - 已运行时间（进行中任务）
 * - 已等待时间（排队中任务）
 *
 * @Props
 * - item: 生成子任务数据，包含时间字段和状态
 *
 * @Example
 * ```vue
 * <el-table-column label="耗时统计" width="220">
 *   <template #default="{ row }">
 *     <GenerationItemTimeStats :item="row" />
 *   </template>
 * </el-table-column>
 * ```
 */

interface GenerationItem {
  status: 'queued' | 'generating' | 'completed' | 'failed' | 'paused'
  queued_at?: string
  started_at?: string
  completed_at?: string
}

defineProps<{
  item: GenerationItem
}>()

/**
 * 格式化时间间隔为人类可读格式
 * @param start - 开始时间（ISO字符串）
 * @param end - 结束时间（ISO字符串，可选，默认当前时间）
 * @returns 格式化的时间字符串，如 "2m 30s"
 */
const formatDuration = (start?: string, end?: string): string => {
  if (!start) return '-'

  const startTime = new Date(start).getTime()
  const endTime = end ? new Date(end).getTime() : Date.now()
  const duration = endTime - startTime

  if (duration < 1000) {
    return '0s'
  }

  const seconds = Math.floor(duration / 1000)
  if (seconds < 60) {
    return `${seconds}s`
  }

  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  if (minutes < 60) {
    return `${minutes}m ${remainingSeconds}s`
  }

  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return `${hours}h ${remainingMinutes}m`
}
</script>

<style lang="scss" scoped>
.time-stats-cell {
  font-size: 12px;

  .time-row {
    display: flex;
    align-items: center;
    margin-bottom: 2px;

    &:last-child {
      margin-bottom: 0;
    }

    .time-label {
      color: #909399;
      width: 40px;
      flex-shrink: 0;
    }

    .time-value {
      font-weight: 500;

      &.success {
        color: #67C23A;
      }

      &.primary {
        color: var(--color-primary);
      }

      &.warning {
        color: #E6A23C;
      }
    }
  }
}
</style>
