<template>
  <div class="scheduled-task-detail-view">
    <div class="page-header mb-md">
      <el-page-header @back="handleBack">
        <template #content>
          <span class="page-title">任务详情</span>
        </template>
        <template #extra>
          <el-button type="primary" @click="handleEdit">编辑任务</el-button>
        </template>
      </el-page-header>
    </div>

    <div v-loading="loading" class="task-detail-content">
      <!-- 任务基本信息 -->
      <div class="card mb-md">
        <div class="card-header">
          <span class="card-title">基本信息</span>
          <el-tag :type="task?.status === 'enabled' ? 'success' : 'info'" size="large">
            {{ task?.status === 'enabled' ? '已启用' : '已禁用' }}
          </el-tag>
        </div>
        <div class="card-body">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="任务名称">
              {{ task?.name }}
            </el-descriptions-item>
            <el-descriptions-item label="任务类型">
              <el-tag :type="task?.task_type === 'custom' ? 'primary' : 'warning'" size="small">
                {{ task?.task_type === 'custom' ? '自定义文案' : '对标文案' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="调度类型">
                {{ task?.schedule_type === 'daily' ? '每日' : task?.schedule_type === 'weekly' ? '每周' : '周期' }}
              </el-descriptions-item>
              <el-descriptions-item label="执行时间">
                <template v-if="task?.schedule_type === 'daily'">
                  {{ task?.schedule_config_json?.times?.join('、') }}
                </template>
                <template v-else-if="task?.schedule_type === 'weekly'">
                  {{ formatWeekdays(task?.schedule_config_json?.days || []) }}
                  {{ task?.schedule_config_json?.times?.join('、') }}
                </template>
                <template v-else-if="task?.schedule_type === 'periodic'">
                  {{ task?.schedule_config_json?.start_date }} 至 {{ task?.schedule_config_json?.end_date }}
                  （{{ task?.schedule_config_json?.times?.join('、') }}）
                </template>
              </el-descriptions-item>
            <el-descriptions-item label="下次执行时间">
              {{ task?.next_execution_at ? formatDateTime(task.next_execution_at) : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ task?.created_at ? formatDateTime(task.created_at) : '-' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>

      <!-- 执行统计 -->
      <div class="card mb-md">
        <div class="card-header">
          <span class="card-title">执行统计</span>
        </div>
        <div class="card-body">
          <el-row :gutter="16">
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-value">{{ task?.total_executions || 0 }}</div>
                <div class="stat-label">总执行次数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card success">
                <div class="stat-value">{{ task?.successful_executions || 0 }}</div>
                <div class="stat-label">成功次数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card error">
                <div class="stat-value">{{ task?.failed_executions || 0 }}</div>
                <div class="stat-label">失败次数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-value">
                  {{ task?.successful_executions && task?.total_executions
                    ? Math.round((task.successful_executions / task.total_executions) * 100)
                    : 0 }}%
                </div>
                <div class="stat-label">成功率</div>
              </div>
            </el-col>
          </el-row>
        </div>
      </div>

      <!-- 配置详情 -->
      <div class="card mb-md">
        <div class="card-header">
          <span class="card-title">配置详情</span>
        </div>
        <div class="card-body">
          <el-tabs v-model="activeTab">
            <el-tab-pane label="素材和模板" name="material">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="选择模板">
                  <div v-if="task?.template_names && task.template_names.length > 0">
                    <el-tag v-for="(name, idx) in task.template_names" :key="idx" size="small" class="mr-xs">
                      {{ name }}
                    </el-tag>
                  </div>
                  <span v-else class="text-muted">-</span>
                </el-descriptions-item>
                <el-descriptions-item v-if="task?.task_type === 'benchmark'" label="对标素材">
                  <div v-if="task?.benchmark_material_titles && task.benchmark_material_titles.length > 0">
                    <el-tag v-for="(title, idx) in task.benchmark_material_titles" :key="idx" size="small" class="mr-xs mb-xs">
                      {{ title }}
                    </el-tag>
                  </div>
                  <span v-else class="text-muted">-</span>
                </el-descriptions-item>
              </el-descriptions>
            </el-tab-pane>

            <el-tab-pane label="创作者" name="subusers">
              <el-table :data="task?.sub_user_ids_json?.map((id: number, idx: number) => ({ id, nickname: task?.sub_user_names?.[idx] || `用户${id}` })) || []" stripe>
                <el-table-column prop="id" label="ID" width="60" />
                <el-table-column prop="nickname" label="昵称" />
              </el-table>
            </el-tab-pane>

            <el-tab-pane label="模型配置" name="model">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="模型选择方式">
                  {{ task?.model_selection_mode === 'auto' ? '自动选择' : '手动选择' }}
                </el-descriptions-item>
                <template v-if="task?.model_selection_mode === 'manual'">
                  <el-descriptions-item label="文案模型">
                    {{ task?.model_platform }} - {{ task?.model_id }}
                  </el-descriptions-item>
                  <el-descriptions-item label="图片模型">
                    {{ task?.image_model_platform }} - {{ task?.image_model_id }}
                  </el-descriptions-item>
                </template>
              </el-descriptions>
            </el-tab-pane>

            <el-tab-pane label="去重配置" name="dedup">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="文案去重">
                  <el-tag :type="task?.dedup_enabled ? 'success' : 'info'" size="small">
                    {{ task?.dedup_enabled ? '已启用' : '已禁用' }}
                  </el-tag>
                </el-descriptions-item>
                <template v-if="task?.dedup_enabled">
                  <el-descriptions-item label="文案相似度阈值">
                    {{ task?.dedup_threshold }}%
                  </el-descriptions-item>
                  <el-descriptions-item label="文案去重范围">
                    {{ task?.dedup_scope?.join('、') }}
                  </el-descriptions-item>
                </template>
                <el-descriptions-item label="图片去重">
                  <el-tag :type="task?.image_dedup_enabled ? 'success' : 'info'" size="small">
                    {{ task?.image_dedup_enabled ? '已启用' : '已禁用' }}
                  </el-tag>
                </el-descriptions-item>
                <template v-if="task?.image_dedup_enabled">
                  <el-descriptions-item label="图片相似度阈值">
                    {{ task?.image_dedup_threshold }}%
                  </el-descriptions-item>
                  <el-descriptions-item label="图片去重范围">
                    {{ task?.image_dedup_scope?.join('、') }}
                  </el-descriptions-item>
                </template>
              </el-descriptions>
            </el-tab-pane>

            <el-tab-pane label="对标配置" name="benchmark" v-if="task?.task_type === 'benchmark'">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="对标文案">
                  <el-tag :type="task?.benchmark_text_enabled ? 'success' : 'info'" size="small">
                    {{ task?.benchmark_text_enabled ? '已启用' : '已禁用' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="对标图片">
                  <el-tag :type="task?.benchmark_image_enabled ? 'success' : 'info'" size="small">
                    {{ task?.benchmark_image_enabled ? '已启用' : '已禁用' }}
                  </el-tag>
                </el-descriptions-item>
                <template v-if="task?.benchmark_image_enabled">
                  <el-descriptions-item label="图片参考选项">
                    {{ task?.benchmark_image_reference_options?.join('、') }}
                  </el-descriptions-item>
                </template>
              </el-descriptions>
            </el-tab-pane>

            <el-tab-pane label="图片配置" name="image">
              <el-descriptions :column="2" border>
                <el-descriptions-item label="生成图片数量">
                  {{ task?.image_count || 3 }}
                </el-descriptions-item>
              </el-descriptions>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>

      <!-- 执行历史 -->
      <div class="card">
        <div class="card-header">
          <span class="card-title">执行历史</span>
        </div>
        <div class="card-body">
          <el-table
            v-loading="loadingExecutions"
            :data="executions"
            stripe
          >
            <el-table-column prop="execution_type" label="执行类型" width="100">
              <template #default="{ row }">
                <el-tag :type="row.execution_type === 'scheduled' ? 'primary' : 'success'" size="small">
                  {{ row.execution_type === 'scheduled' ? '定时' : '手动' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="scheduled_at" label="计划时间" width="160">
              <template #default="{ row }">
                {{ row.scheduled_at ? formatDateTime(row.scheduled_at) : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="started_at" label="开始时间" width="160">
              <template #default="{ row }">
                {{ row.started_at ? formatDateTime(row.started_at) : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="completed_at" label="完成时间" width="160">
              <template #default="{ row }">
                {{ row.completed_at ? formatDateTime(row.completed_at) : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="120">
              <template #default="{ row }">
                <div class="status-with-icon">
                  <el-icon :color="getExecutionStatusColor(row.status)" :size="16">
                    <CircleCheckFilled v-if="row.status === 'completed'" />
                    <CircleCloseFilled v-else-if="row.status === 'failed'" />
                    <Loading v-else-if="row.status === 'running'" />
                    <Clock v-else-if="row.status === 'pending'" />
                    <RemoveFilled v-else-if="row.status === 'cancelled'" />
                  </el-icon>
                  <el-tag :type="getExecutionStatusType(row.status)" size="small">
                    {{ getExecutionStatusLabel(row.status) }}
                  </el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="执行耗时" width="120">
              <template #default="{ row }">
                <span :class="getDurationClass(row)">
                  {{ calculateDuration(row) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="执行结果" width="180">
              <template #default="{ row }">
                <div v-if="row.total_items" class="execution-result">
                  <span>总计: {{ row.total_items }}</span>
                  <span class="success">成功: {{ row.success_items }}</span>
                  <span class="error">失败: {{ row.failed_items }}</span>
                </div>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="generation_task_id" label="生成任务ID" width="120">
              <template #default="{ row }">
                <el-link v-if="row.generation_task_id" type="primary" @click="handleViewTask(row.generation_task_id)">
                  {{ row.generation_task_id }}
                </el-link>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button
                  size="small"
                  type="primary"
                  link
                  :disabled="!row.error_message && !row.started_at"
                  @click="handleViewLog(row)"
                >
                  查看日志
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <div v-if="executionsTotal > 0" class="pagination-container mt-md">
            <el-pagination
              v-model:current-page="executionsCurrentPage"
              v-model:page-size="executionsPageSize"
              :page-sizes="[10, 20, 50]"
              :total="executionsTotal"
              layout="total, sizes, prev, pager, next"
              @size-change="loadExecutions"
              @current-change="loadExecutions"
            />
          </div>
        </div>
      </div>

      <!-- 执行日志弹窗 -->
      <el-dialog
        v-model="logDialogVisible"
        title="执行日志"
        width="600px"
        :close-on-click-modal="false"
        @close="handleCloseLog"
      >
        <div v-if="currentLogExecution" class="execution-log-content">
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="执行ID">
              {{ currentLogExecution.id }}
            </el-descriptions-item>
            <el-descriptions-item label="执行类型">
              <el-tag :type="currentLogExecution.execution_type === 'scheduled' ? 'primary' : 'success'" size="small">
                {{ currentLogExecution.execution_type === 'scheduled' ? '定时' : '手动' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getExecutionStatusType(currentLogExecution.status)" size="small">
                {{ getExecutionStatusLabel(currentLogExecution.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="执行耗时">
              {{ calculateDuration(currentLogExecution) }}
            </el-descriptions-item>
            <el-descriptions-item label="计划时间" :span="2">
              {{ currentLogExecution.scheduled_at ? formatDateTime(currentLogExecution.scheduled_at) : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="开始时间" :span="2">
              {{ currentLogExecution.started_at ? formatDateTime(currentLogExecution.started_at) : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="完成时间" :span="2">
              {{ currentLogExecution.completed_at ? formatDateTime(currentLogExecution.completed_at) : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="执行结果" :span="2">
              <div v-if="currentLogExecution.total_items" class="execution-result-detail">
                <div>总任务数: {{ currentLogExecution.total_items }}</div>
                <div class="success">成功: {{ currentLogExecution.success_items || 0 }}</div>
                <div class="error">失败: {{ currentLogExecution.failed_items || 0 }}</div>
              </div>
              <span v-else class="text-muted">-</span>
            </el-descriptions-item>
            <el-descriptions-item v-if="currentLogExecution.generation_task_id" label="生成任务ID" :span="2">
              <el-link type="primary" @click="handleViewTask(currentLogExecution.generation_task_id!)">
                {{ currentLogExecution.generation_task_id }}
              </el-link>
            </el-descriptions-item>
          </el-descriptions>

          <!-- 错误信息 -->
          <div v-if="currentLogExecution.error_message" class="error-section mt-md">
            <div class="error-title">错误信息：</div>
            <el-alert
              :title="currentLogExecution.error_message"
              type="error"
              :closable="false"
              show-icon
            />
          </div>
        </div>
        <template #footer>
          <el-button @click="handleCloseLog">关闭</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  CircleCheckFilled,
  CircleCloseFilled,
  Loading,
  Clock,
  RemoveFilled
} from '@element-plus/icons-vue'
import { apiClient } from '@/api/types'
import type { ScheduledTask, ScheduledTaskExecution } from '@/api/types'

const router = useRouter()
const route = useRoute()

const taskId = Number(route.params.id)

// 任务详情
const loading = ref(false)
const task = ref<ScheduledTask>()

// 执行历史
const loadingExecutions = ref(false)
const executions = ref<ScheduledTaskExecution[]>([])
const executionsCurrentPage = ref(1)
const executionsPageSize = ref(20)
const executionsTotal = ref(0)

// Tab
const activeTab = ref('material')

// 加载任务详情
const loadTaskDetail = async () => {
  loading.value = true
  try {
    task.value = await apiClient.getScheduledTask(taskId)
  } catch (error: any) {
    ElMessage.error(error.message || '加载任务详情失败')
    router.back()
  } finally {
    loading.value = false
  }
}

// 加载执行历史
const loadExecutions = async () => {
  loadingExecutions.value = true
  try {
    const response = await apiClient.getScheduledTaskExecutions(taskId, {
      page: executionsCurrentPage.value,
      limit: executionsPageSize.value
    })
    executions.value = response.items
    executionsTotal.value = response.total
  } catch (error: any) {
    ElMessage.error(error.message || '加载执行历史失败')
  } finally {
    loadingExecutions.value = false
  }
}

// 编辑任务
const handleEdit = () => {
  router.push(`/scheduled-tasks/edit/${taskId}`)
}

// 查看生成任务
const handleViewTask = (generationTaskId: number) => {
  router.push(`/generation/detail/${generationTaskId}`)
}

// 返回
const handleBack = () => {
  router.back()
}

// 格式化周几
const formatWeekdays = (weekdays: number[]): string => {
  if (!weekdays || weekdays.length === 0) return '-'
  const weekdayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  return weekdays.map(d => weekdayNames[d - 1]).join('、')
}

// 格式化日期时间（后端 naive datetime 为 CST，显式加时区避免前端误判为 UTC）
const formatDateTime = (dateStr: string): string => {
  if (!dateStr) return '-'
  // 后端返回无时区的 datetime 字符串，实际上为北京时间（CST）
  const date = new Date(dateStr.includes('+') || dateStr.endsWith('Z') ? dateStr : dateStr + '+08:00')
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 执行状态类型
const getExecutionStatusType = (status: string): string => {
  const typeMap: Record<string, string> = {
    pending: 'info',
    running: 'primary',
    completed: 'success',
    failed: 'danger',
    cancelled: 'warning'
  }
  return typeMap[status] || 'info'
}

// 执行状态颜色
const getExecutionStatusColor = (status: string): string => {
  const colorMap: Record<string, string> = {
    pending: '#909399',
    running: '#8B7CF6',
    completed: '#34C759',
    failed: '#FF3B30',
    cancelled: '#E6A23C'
  }
  return colorMap[status] || '#909399'
}

// 执行状态标签
const getExecutionStatusLabel = (status: string): string => {
  const labelMap: Record<string, string> = {
    pending: '待执行',
    running: '执行中',
    completed: '已完成',
    failed: '已失败',
    cancelled: '已取消'
  }
  return labelMap[status] || status
}

// 计算执行耗时
const calculateDuration = (row: ScheduledTaskExecution): string => {
  if (!row.started_at) return '-'
  
  const start = new Date(row.started_at).getTime()
  const end = row.completed_at ? new Date(row.completed_at).getTime() : Date.now()
  
  const durationMs = end - start
  const seconds = Math.floor(durationMs / 1000)
  
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分${seconds % 60}秒`
  return `${Math.floor(seconds / 3600)}时${Math.floor((seconds % 3600) / 60)}分`
}

// 耗时样式类
const getDurationClass = (row: ScheduledTaskExecution): string => {
  if (row.status === 'failed') return 'duration-error'
  if (row.status === 'completed') {
    const duration = row.completed_at && row.started_at 
      ? (new Date(row.completed_at).getTime() - new Date(row.started_at).getTime()) / 1000 
      : 0
    if (duration > 300) return 'duration-warning'  // 超过5分钟显示警告
    return 'duration-normal'
  }
  return 'duration-pending'
}

// 执行日志弹窗
const logDialogVisible = ref(false)
const currentLogExecution = ref<ScheduledTaskExecution | null>(null)

// 查看执行日志
const handleViewLog = (row: ScheduledTaskExecution) => {
  currentLogExecution.value = row
  logDialogVisible.value = true
}

// 关闭日志弹窗
const handleCloseLog = () => {
  logDialogVisible.value = false
  currentLogExecution.value = null
}

onMounted(() => {
  loadTaskDetail()
  loadExecutions()
})
</script>

<style scoped lang="scss">
@import './scheduled-tasks.scss';

.scheduled-task-detail-view {
  .card {
    background: var(--bg-secondary);
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 8px var(--shadow-color, rgba(0, 0, 0, 0.08));

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border-color);

      .card-title {
        font-size: 16px;
        font-weight: 600;
        color: var(--text-primary);
      }
    }

    .card-body {
      // 空内容样式
    }
  }

  // 状态图标和标签的布局
  :deep(.status-with-icon) {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  // 执行耗时样式
  :deep(.duration-error) {
    color: var(--el-color-danger);
    font-weight: 500;
  }

  :deep(.duration-warning) {
    color: var(--el-color-warning);
    font-weight: 500;
  }

  :deep(.duration-normal) {
    color: var(--el-color-success);
  }

  :deep(.duration-pending) {
    color: var(--text-placeholder);
  }

  // 执行日志弹窗内容样式
  :deep(.execution-log-content) {
    .execution-result-detail {
      display: flex;
      gap: 16px;
      font-size: 13px;

      .success {
        color: var(--el-color-success);
      }

      .error {
        color: var(--el-color-danger);
      }
    }

    .error-section {
      .error-title {
        font-weight: 500;
        margin-bottom: 8px;
        color: var(--el-color-danger);
      }
    }
  }

  .stat-card {
    padding: 16px;
    background: var(--bg-tertiary);
    border-radius: 4px;
    text-align: center;

    .stat-value {
      font-size: 24px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 8px;
    }

    .stat-label {
      font-size: 13px;
      color: var(--text-muted);
    }

    &.success {
      background: var(--bg-success, #f0f9ff);
      .stat-value {
        color: var(--el-color-success);
      }
    }

    &.error {
      background: var(--bg-danger, #fef0f0);
      .stat-value {
        color: var(--el-color-danger);
      }
    }
  }

  .execution-result {
    display: flex;
    gap: 8px;
    font-size: 13px;

    .success {
      color: var(--el-color-success);
    }

    .error {
      color: var(--el-color-danger);
    }
  }

  .pagination-container {
    display: flex;
    justify-content: flex-end;
    margin-top: 16px;
  }

  .text-muted {
    color: var(--text-placeholder);
  }

  .ml-xs {
    margin-left: 4px;
  }

  .mr-xs {
    margin-right: 4px;
  }
}

.mb-md {
  margin-bottom: 16px;
}

.mt-md {
  margin-top: 16px;
}
</style>