<template>
  <div class="scheduled-task-execution-list-view">
    <div class="page-header mb-md">
      <el-page-header @back="handleBack">
        <template #content>
          <span class="page-title">执行历史 - {{ taskName }}</span>
        </template>
      </el-page-header>
    </div>

    <div class="card">
      <el-table
        :data="executions"
        v-loading="loading"
        style="width: 100%"
        stripe
        border
      >
        <el-table-column prop="id" label="ID" width="80" />
        
        <el-table-column prop="execution_time" label="执行时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.execution_time) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="generation_task_id" label="生成任务ID" width="120">
          <template #default="{ row }">
            <router-link
              v-if="row.generation_task_id"
              :to="`/generation/detail/${row.generation_task_id}`"
              class="link-type"
            >
              {{ row.generation_task_id }}
            </router-link>
            <span v-else>-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="error_message" label="错误信息">
          <template #default="{ row }">
            <el-tooltip
              v-if="row.error_message"
              :content="row.error_message"
              placement="top"
              :show-after="500"
            >
              <span class="error-message">{{ truncateText(row.error_message, 50) }}</span>
            </el-tooltip>
            <span v-else>-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.generation_task_id"
              type="primary"
              size="small"
              @click="viewGenerationTask(row.generation_task_id)"
            >
              查看任务
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container mt-md">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { apiClient } from '@/api/types'

const route = useRoute()
const router = useRouter()

// 响应式数据
const taskId = ref<number>(Number(route.params.taskId))
const taskName = ref<string>('')
const executions = ref<any[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 获取执行历史
const fetchExecutions = async () => {
  loading.value = true
  try {
    const response = await apiClient.getScheduledTaskExecutions(taskId.value, {
      page: currentPage.value,
      limit: pageSize.value,
    })
    
    if (response.success) {
      executions.value = response.data.items
      total.value = response.data.total
    }
  } catch (error: any) {
    ElMessage.error(error.message || '获取执行历史失败')
  } finally {
    loading.value = false
  }
}

// 获取任务详情
const fetchTaskDetail = async () => {
  try {
    const response = await apiClient.getScheduledTask(taskId.value)
    if (response.success) {
      taskName.value = response.data.name
    }
  } catch (error: any) {
    ElMessage.error(error.message || '获取任务详情失败')
  }
}

// 格式化日期时间
const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

// 获取状态类型
const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    'success': 'success',
    'failed': 'danger',
    'partial': 'warning',
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    'success': '成功',
    'failed': '失败',
    'partial': '部分成功',
  }
  return textMap[status] || status
}

// 截断文本
const truncateText = (text: string, maxLength: number) => {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

// 查看生成任务详情
const viewGenerationTask = (taskId: number) => {
  router.push(`/generation/detail/${taskId}`)
}

// 处理页码变化
const handleCurrentChange = (page: number) => {
  currentPage.value = page
  fetchExecutions()
}

// 处理每页数量变化
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchExecutions()
}

// 返回
const handleBack = () => {
  router.push(`/scheduled-tasks/${taskId.value}`)
}

// 初始化
onMounted(() => {
  fetchTaskDetail()
  fetchExecutions()
})
</script>

<style lang="scss" scoped>
@import './scheduled-tasks.scss';

.scheduled-task-execution-list-view {
  padding: 0;
}

.page-header {
  margin-bottom: 20px;
}

.card {
  @include glass-card;
  padding: 32px;
  border-radius: 24px;
}

.mb-md {
  margin-bottom: 20px;
}

.mt-md {
  margin-top: 20px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.link-type {
  color: var(--color-primary);
  text-decoration: none;
}

.link-type:hover {
  text-decoration: underline;
}

.error-message {
  color: #f56c6c;
  cursor: pointer;
}

:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-table th) {
  background-color: #f5f7fa;
  color: #606266;
  font-weight: 600;
}
</style>
