<template>
  <div class="scheduled-task-list-view">
    <!-- 页面头部 -->
    <div class="page-header flex-between mb-md">
      <h2 class="page-title">定时任务管理</h2>
      <el-button v-if="userRole !== 'super_admin'" type="primary" :icon="Plus" @click="handleCreate">创建任务</el-button>
    </div>

    <div class="content-layout">
      <!-- 左侧管理员列表（仅超级管理员可见） -->
      <div v-if="userRole === 'super_admin'" class="operator-sidebar">
        <div class="sidebar-header">
          <h3>管理员列表</h3>
        </div>
        <div class="operator-list">
          <div
            class="operator-item"
            :class="{ active: selectedOperatorId === null }"
            @click="handleSelectOperator(null)"
          >
            <el-icon><User /></el-icon>
            <span>全部管理员</span>
          </div>
          <div
            v-for="op in operators"
            :key="op.id"
            class="operator-item"
            :class="{ active: selectedOperatorId === op.id }"
            @click="handleSelectOperator(op.id)"
          >
            <el-icon><User /></el-icon>
            <span>{{ op.name }}</span>
          </div>
        </div>
      </div>

      <!-- 右侧任务列表 -->
      <div class="task-list-content">
        <div class="card">
          <!-- 搜索栏 -->
          <div class="toolbar mb-md">
            <div style="display: flex; gap: 12px;">
              <el-input
                v-model="searchKeyword"
                placeholder="搜索任务名称"
                :prefix-icon="Search"
                clearable
                style="width: 280px;"
                @clear="handleSearch"
                @keyup.enter="handleSearch"
              />
              <el-select v-model="searchStatus" placeholder="任务状态" clearable style="width: 130px;" @change="handleSearch">
                <el-option label="全部" value="" />
                <el-option label="已启用" value="active" />
                <el-option label="已禁用" value="paused" />
              </el-select>
              <el-select v-model="searchTaskType" placeholder="任务类型" clearable style="width: 130px;" @change="handleSearch">
                <el-option label="全部" value="" />
                <el-option label="自定义文案" value="custom" />
                <el-option label="对标文案" value="benchmark" />
              </el-select>
              <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
            </div>
          </div>

          <!-- 任务列表 -->
          <el-table
            v-loading="loading"
            :data="taskList"
            stripe
            style="width: 100%"
          >
            <el-table-column prop="name" label="任务名称" min-width="180">
              <template #default="{ row }">
                <div class="task-name">
                  <span class="name-text">{{ row.name }}</span>
                  <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                    {{ row.is_active ? '已启用' : '已禁用' }}
                  </el-tag>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="task_type" label="任务类型" width="100">
              <template #default="{ row }">
                <el-tag :type="row.task_type === 'custom' ? 'primary' : 'warning'" size="small">
                  {{ row.task_type === 'custom' ? '自定义文案' : '对标文案' }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="schedule_config_json" label="调度配置" min-width="180">
              <template #default="{ row }">
                <div class="schedule-info">
                  <div class="schedule-type">
                    <el-icon><Clock /></el-icon>
                    <span>{{ 
                      row.schedule_type === 'daily' ? '每日' : 
                      row.schedule_type === 'weekly' ? '每周' : 
                      row.schedule_type === 'periodic' ? '周期' : row.schedule_type 
                    }}</span>
                  </div>
                  <div class="schedule-times">
                    <template v-if="row.schedule_type === 'daily'">
                      {{ row.schedule_config_json?.times?.join('、') || '-' }}
                    </template>
                    <template v-else-if="row.schedule_type === 'weekly'">
                      {{ formatWeekdays(row.schedule_config_json?.days || []) }}
                      {{ row.schedule_config_json?.times?.join('、') || '' }}
                    </template>
                    <template v-else-if="row.schedule_type === 'periodic'">
                      {{ row.schedule_config_json?.start_date || '' }} 至 {{ row.schedule_config_json?.end_date || '' }}
                      （{{ row.schedule_config_json?.times?.join('、') || '' }}）
                    </template>
                    <template v-else>
                      -
                    </template>
                  </div>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="next_execution_at" label="下次执行时间" width="160">
              <template #default="{ row }">
                <span v-if="row.next_execution_at">{{ formatDateTime(row.next_execution_at) }}</span>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>

            <el-table-column label="执行统计" width="200">
              <template #default="{ row }">
                <div class="execution-stats">
                  <div class="stat-item">
                    <span class="stat-label">总计:</span>
                    <span class="stat-value">{{ row.total_executions || 0 }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">成功:</span>
                    <span class="stat-value success">{{ row.successful_executions || 0 }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">失败:</span>
                    <span class="stat-value error">{{ row.failed_executions || 0 }}</span>
                  </div>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="created_at" label="创建时间" width="160">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>

            <el-table-column label="操作" width="300" fixed="right">
              <template #default="{ row }">
                <el-button-group>
                  <el-button size="small" @click="handleView(row)">查看</el-button>
                  <el-button size="small" type="primary" @click="handleEdit(row)">编辑</el-button>
                  <el-button
                    size="small"
                    :type="row.is_active ? 'warning' : 'success'"
                    @click="handleToggle(row)"
                  >
                    {{ row.is_active ? '禁用' : '启用' }}
                  </el-button>
                  <!-- 创作管理员才显示执行按钮 -->
                  <el-button
                    v-if="userRole === 'operator'"
                    size="small"
                    type="success"
                    :disabled="!row.is_active"
                    @click="handleExecute(row)"
                  >
                    执行
                  </el-button>
                  <!-- 超级管理员和创作管理员都可以删除 -->
                  <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
                </el-button-group>
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
              @current-change="handlePageChange"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Clock, User } from '@element-plus/icons-vue'
import { apiClient } from '@/api/types'
import type { ScheduledTaskListItem, OperatorOption } from '@/api/types'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const userRole = computed(() => authStore.userRole)

// 搜索条件
const searchKeyword = ref('')
const searchStatus = ref('')
const searchTaskType = ref('')

// 列表数据
const loading = ref(false)
const taskList = ref<ScheduledTaskListItem[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 管理员列表（仅超级管理员使用）
const operators = ref<OperatorOption[]>([])
const selectedOperatorId = ref<number | null>(null)

// 加载管理员列表（超级管理员）
const loadOperators = async () => {
  if (userRole.value !== 'super_admin') return
  
  try {
    const response = await apiClient.getOperatorList()
    operators.value = response
  } catch (error: any) {
    ElMessage.error(error.message || '加载管理员列表失败')
  }
}

// 选择管理员
const handleSelectOperator = (operatorId: number | null) => {
  selectedOperatorId.value = operatorId
  currentPage.value = 1
  loadTasks()
}

// 加载任务列表
const loadTasks = async () => {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      limit: pageSize.value
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (searchStatus.value) params.status = searchStatus.value
    if (searchTaskType.value) params.task_type = searchTaskType.value
    
    // 超级管理员选择了特定管理员时，添加 operator_id 参数
    if (userRole.value === 'super_admin' && selectedOperatorId.value) {
      params.operator_id = selectedOperatorId.value
    }

    const response = await apiClient.getScheduledTasks(params)
    taskList.value = response.items
    total.value = response.total
  } catch (error: any) {
    ElMessage.error(error.message || '加载任务列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  loadTasks()
}

// 分页
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadTasks()
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  loadTasks()
}

// 创建任务
const handleCreate = () => {
  router.push('/scheduled-tasks/create')
}

// 查看详情
const handleView = (row: ScheduledTaskListItem) => {
  router.push(`/scheduled-tasks/${row.id}`)
}

// 编辑任务
const handleEdit = (row: ScheduledTaskListItem) => {
  router.push(`/scheduled-tasks/edit/${row.id}`)
}

// 启用/禁用任务
const handleToggle = async (row: ScheduledTaskListItem) => {
  const action = row.is_active ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确定要${action}任务 "${row.name}" 吗？`, '确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await apiClient.toggleScheduledTask(row.id, !row.is_active)
    ElMessage.success(`任务已${action}`)
    loadTasks()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || `${action}失败`)
    }
  }
}

// 立即执行
const handleExecute = async (row: ScheduledTaskListItem) => {
  try {
    await ElMessageBox.confirm(`确定要立即执行任务 "${row.name}" 吗？`, '确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    })
    
    const result = await apiClient.executeScheduledTask(row.id)
    ElMessage.success(`任务已开始执行，生成任务ID: ${result.generation_task_id}`)
    loadTasks()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '执行失败')
    }
  }
}

// 删除任务
const handleDelete = async (row: ScheduledTaskListItem) => {
  try {
    await ElMessageBox.confirm(`确定要删除任务 "${row.name}" 吗？此操作不可恢复。`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'error'
    })
    
    await apiClient.deleteScheduledTask(row.id)
    ElMessage.success('任务已删除')
    loadTasks()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
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

onMounted(() => {
  // 超级管理员加载管理员列表
  if (userRole.value === 'super_admin') {
    loadOperators()
  }
  loadTasks()
})
</script>

<style scoped lang="scss">
@import './scheduled-tasks.scss';

.scheduled-task-list-view {
  .page-header {
    .page-title {
      margin: 0;
    }
  }

  .content-layout {
    display: flex;
    gap: 16px;
  }

  .operator-sidebar {
    width: 220px;
    min-width: 220px;
    background: var(--bg-secondary);
    border-radius: 8px;
    box-shadow: 0 2px 8px var(--shadow-color, rgba(0, 0, 0, 0.08));
    padding: 16px;
    height: fit-content;

    .sidebar-header {
      margin-bottom: 12px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border-color, #e4e7ed);

      h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        color: var(--text-primary);
      }
    }

    .operator-list {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .operator-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 12px;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s;
      color: var(--text-regular);
      font-size: 14px;

      &:hover {
        background: var(--bg-primary, #f5f7fa);
      }

      &.active {
        background: var(--el-color-primary-light-9, #ecf5ff);
        color: var(--el-color-primary, var(--color-primary));
        font-weight: 500;
      }

      .el-icon {
        font-size: 16px;
      }

      span {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
  }

  .task-list-content {
    flex: 1;
    min-width: 0;
  }

  .card {
    background: var(--bg-secondary);
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 8px var(--shadow-color, rgba(0, 0, 0, 0.08));
  }

  .toolbar {
    padding: $spacing-sm 0;
    margin-bottom: $spacing-md;
    border-bottom: 1px solid var(--color-border-default);
  }

  .task-name {
    display: flex;
    align-items: center;
    gap: 8px;

    .name-text {
      font-weight: 500;
      color: var(--text-primary);
    }
  }

  .schedule-info {
    .schedule-type {
      display: flex;
      align-items: center;
      gap: 4px;
      font-weight: 500;
      color: var(--text-primary);
      margin-bottom: 4px;
    }

    .schedule-times {
      font-size: 12px;
      color: var(--text-secondary);
    }
  }

  .execution-stats {
    display: flex;
    gap: 12px;
    font-size: 13px;

    .stat-item {
      display: flex;
      gap: 4px;

      .stat-label {
        color: var(--color-text-secondary);
        font-weight: 500;
      }

      .stat-value {
        font-weight: 500;
        color: var(--text-primary);

        &.success {
          color: var(--el-color-success);
        }

        &.error {
          color: var(--el-color-danger);
        }
      }
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
}

.flex-between {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mb-md {
  margin-bottom: 16px;
}

.mt-md {
  margin-top: 16px;
}
</style>
