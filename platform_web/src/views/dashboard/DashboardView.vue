<template>
  <div class="dashboard-view">
    <h2 class="page-title">AIGC看板</h2>

    <!-- Tab切换 -->
    <div class="tab-container">
      <el-radio-group v-model="activeTab" size="default">
        <el-radio-button value="overview">总览</el-radio-button>
        <el-radio-button value="trend">趋势分析</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 总览Tab -->
    <div v-show="activeTab === 'overview'">
      <!-- 统计部分 -->
      <div class="card stats-section">
      <!-- 统计卡片筛选控件 - 仅对管理员显示 -->
      <el-row v-if="!isSubUser" :gutter="12" class="mb-md" align="middle">
        <el-col :span="1.5">
          <span class="filter-label">统计范围</span>
        </el-col>
        <el-col :span="6">
          <el-date-picker
            v-model="statsDateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            size="small"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
            @change="handleStatsFilterChange"
          />
        </el-col>
        <el-col v-if="isSuperAdmin" :span="1.5">
          <span class="filter-label">管理员</span>
        </el-col>
        <el-col v-if="isSuperAdmin" :span="4">
          <el-select
            v-model="statsOperatorId"
            placeholder="全部管理员"
            clearable
            size="small"
            style="width: 100%"
            @change="handleStatsFilterChange"
          >
            <el-option
              v-for="op in operatorList"
              :key="op.id"
              :label="op.name"
              :value="op.id"
            />
          </el-select>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <!-- 创作者只显示待发布和已发布 -->
        <el-col v-if="!isSubUser" :span="6">
          <div class="stat-card">
            <div class="stat-icon stat-icon-primary">
              <el-icon :size="24" color="#fff"><User /></el-icon>
            </div>
            <div class="stat-content">
              <div v-if="statsLoading" class="stat-value-loading">
                <el-icon class="loading-spinner"><Loading /></el-icon>
              </div>
              <div v-else class="stat-value">{{ stats.total_sub_users || 0 }}</div>
              <div class="stat-label">总创作者数</div>
            </div>
          </div>
        </el-col>
        <el-col v-if="!isSubUser" :span="6">
          <div class="stat-card">
            <div class="stat-icon stat-icon-info">
              <el-icon :size="24" color="#fff"><Document /></el-icon>
            </div>
            <div class="stat-content">
              <div v-if="statsLoading" class="stat-value-loading">
                <el-icon class="loading-spinner"><Loading /></el-icon>
              </div>
              <div v-else class="stat-value">{{ stats.today_generated || 0 }}</div>
              <div class="stat-label">生成内容（周期内）</div>
            </div>
          </div>
        </el-col>
        <el-col :span="isSubUser ? 12 : 6">
          <div class="stat-card">
            <div class="stat-icon stat-icon-warning">
              <el-icon :size="24" color="#fff"><Clock /></el-icon>
            </div>
            <div class="stat-content">
              <div v-if="statsLoading" class="stat-value-loading">
                <el-icon class="loading-spinner"><Loading /></el-icon>
              </div>
              <div v-else class="stat-value">{{ stats.pending_publish || 0 }}</div>
              <div class="stat-label">今日待发内容</div>
            </div>
          </div>
        </el-col>
        <el-col :span="isSubUser ? 12 : 6">
          <div class="stat-card">
            <div class="stat-icon stat-icon-success">
              <el-icon :size="24" color="#fff"><SuccessFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div v-if="statsLoading" class="stat-value-loading">
                <el-icon class="loading-spinner"><Loading /></el-icon>
              </div>
              <div v-else class="stat-value">{{ stats.published || 0 }}</div>
              <div class="stat-label">今日已发内容</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 队列状态监控 - 仅超级管理员可见 -->
    <div v-if="isSuperAdmin" class="mt-lg">
      <div class="card">
        <div class="card-header flex-between">
          <h3 class="section-title" style="margin-bottom: 0;">
            <el-icon style="margin-right: 4px;"><Monitor /></el-icon>
            任务队列监控
          </h3>
          <el-button type="primary" size="small" :loading="queueLoading" @click="loadQueueStatus">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
        <div v-loading="queueLoading" class="queue-status-content">
          <!-- 队列统计卡片 -->
          <el-row :gutter="20" class="mb-md">
            <el-col :span="6">
              <div class="queue-stat-card active">
                <div class="queue-stat-icon queue-icon-primary">
                  <el-icon :size="28" color="#fff"><VideoPlay /></el-icon>
                </div>
                <div class="queue-stat-content">
                  <div class="queue-stat-value">{{ queueStatus.active_count || 0 }}</div>
                  <div class="queue-stat-label">活跃任务</div>
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="queue-stat-card waiting">
                <div class="queue-stat-icon queue-icon-warning">
                  <el-icon :size="28" color="#fff"><Timer /></el-icon>
                </div>
                <div class="queue-stat-content">
                  <div class="queue-stat-value">{{ queueStatus.waiting_count || 0 }}</div>
                  <div class="queue-stat-label">等待任务</div>
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="queue-stat-card running">
                <div class="queue-stat-icon queue-icon-danger">
                  <el-icon :size="28" color="#fff"><Cpu /></el-icon>
                </div>
                <div class="queue-stat-content">
                  <div class="queue-stat-value">{{ workerStatus.worker_running_count || 0 }}</div>
                  <div class="queue-stat-label">Worker 运行数</div>
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="queue-stat-card idle">
                <div class="queue-stat-icon queue-icon-success">
                  <el-icon :size="28" color="#fff"><Cpu /></el-icon>
                </div>
                <div class="queue-stat-content">
                  <div class="queue-stat-value">{{ workerStatus.worker_idle_count || 0 }}</div>
                  <div class="queue-stat-label">Worker 空闲数</div>
                </div>
              </div>
            </el-col>
          </el-row>

          <!-- 队列容量进度条 -->
          <div class="queue-capacity-bar mb-md">
            <div class="capacity-label">Worker 使用率</div>
            <el-progress
              :percentage="workerUsagePercentage"
              :color="workerUsageColor"
              :stroke-width="20"
              :text-inside="true"
            />
            <div class="capacity-text">
              当前：{{ workerStatus.worker_running_count || 0 }} 运行 / {{ workerStatus.worker_idle_count || 0 }} 空闲 / {{ workerStatus.worker_total || 0 }} 总计
            </div>
          </div>

          <!-- 最近活跃任务列表 -->
          <div v-if="queueStatus.active_tasks && queueStatus.active_tasks.length > 0" class="mb-md">
            <h4 class="sub-title">最近活跃任务</h4>
            <el-table :data="queueStatus.active_tasks" size="small" style="width: 100%;">
              <el-table-column prop="item_id" label="任务ID" width="100" />
              <el-table-column prop="celery_task_id" label="Celery任务ID" show-overflow-tooltip />
              <el-table-column label="开始时间" width="170">
                <template #default="{ row }">
                  {{ formatDateTime(row.started_at) }}
                </template>
              </el-table-column>
              <el-table-column label="运行时长" width="120">
                <template #default="{ row }">
                  {{ getRunningTime(row.started_at) }}
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 最近等待任务列表 -->
          <div v-if="queueStatus.waiting_tasks && queueStatus.waiting_tasks.length > 0">
            <h4 class="sub-title">等待队列（前5个）</h4>
            <el-table :data="queueStatus.waiting_tasks" size="small" style="width: 100%;">
              <el-table-column prop="item_id" label="任务ID" width="100" />
              <el-table-column prop="owner_operator_id" label="管理员ID" width="100" />
              <el-table-column prop="priority" label="优先级" width="80" />
            </el-table>
          </div>
          <el-empty v-if="!queueLoading && queueStatus.active_count === 0 && queueStatus.waiting_count === 0" 
                    description="队列为空" />
        </div>
      </div>
    </div>

    <el-row :gutter="20" class="mt-lg">
      <el-col :span="24">
        <div class="card">
          <div class="card-header flex-between">
            <h3 class="section-title" style="margin-bottom: 0;">{{ isSubUser ? '最近内容' : '最近任务' }}</h3>
            <div class="flex-center gap-sm">
              <!-- 超级管理员：创作管理员筛选 -->
              <el-select
                v-if="isSuperAdmin"
                v-model="selectedOperatorId"
                placeholder="选择管理员"
                clearable
                size="small"
                style="width: 150px"
                @change="handleOperatorChange"
              >
                <el-option
                  v-for="op in operatorList"
                  :key="op.id"
                  :label="op.name"
                  :value="op.id"
                />
              </el-select>
              <!-- 日期范围筛选 -->
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                size="small"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 240px"
                @change="handleDateChange"
              />
              <el-button type="primary" size="small" :loading="tasksLoading" @click="loadRecentTasks">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </div>

          <!-- 创作者内容列表 -->
          <template v-if="isSubUser">
            <div v-loading="tasksLoading" class="sub-user-item-list">
              <el-empty v-if="subUserItems.length === 0 && !tasksLoading" description="暂无内容数据" />
              <el-card v-for="item in subUserItems" :key="item.id" class="sub-user-item-card mb-md" shadow="hover">
                <div class="item-header flex-between">
                  <div class="item-title">
                    <span class="task-name">{{ item.taskName || item.task_name || '任务 #' + item.task_id }}</span>
                    <el-tag :type="getSubUserItemStatusType(item)" size="small" style="margin-left: 12px;">
                      {{ getSubUserItemStatusLabel(item) }}
                    </el-tag>
                  </div>
                  <div class="item-time">{{ formatDateTime(item.created_at) }}</div>
                </div>
                <div class="item-content mt-md">
                  <!-- 标题 -->
                  <div v-if="item.generated_title" class="content-row title-row">
                    <span class="row-label">📌 标题</span>
                    <span class="row-value title-value">{{ item.generated_title }}</span>
                  </div>
                  <!-- 正文 -->
                  <div v-if="item.generated_text" class="content-row text-row">
                    <span class="row-label">📄 正文</span>
                    <span class="row-value text-value">{{ item.generated_text.length > 150 ? item.generated_text.substring(0, 150) + '...' : item.generated_text }}</span>
                  </div>
                  <!-- 话题 -->
                  <div v-if="parseTopics((item as any).output_topics).length > 0" class="content-row topics-row">
                    <span class="row-label">🏷️ 话题</span>
                    <div class="row-value topics-value">
                      <el-tag v-for="(tag, idx) in parseTopics((item as any).output_topics).slice(0, 3)" :key="idx" type="warning" size="small" class="topic-mini-tag">#{{ tag }}</el-tag>
                      <span v-if="parseTopics((item as any).output_topics).length > 3" class="more-topics">+{{ parseTopics((item as any).output_topics).length - 3 }}</span>
                    </div>
                  </div>
                  <!-- 图片预览 -->
                  <div v-if="item.generated_images && item.generated_images.length > 0" class="content-row images-row">
                    <span class="row-label">🖼️ 图片</span>
                    <div class="row-value images-value">
                      <div class="image-thumbs">
                        <el-image
                          v-for="(img, idx) in (item.generated_thumbnails || item.generated_images).slice(0, 4)"
                          :key="idx"
                          :src="img"
                          class="image-thumb"
                          fit="cover"
                          preview-teleported
                          :preview-src-list="item.generated_images"
                          :initial-index="idx"
                        />
                        <div v-if="item.generated_images.length > 4" class="more-images">
                          +{{ item.generated_images.length - 4 }}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="item-footer flex-between mt-sm">
                  <div class="item-meta">
                    <span class="meta-item id-tag">内容 #{{ item.id }}</span>
                  </div>
                  <div class="item-actions">
                    <el-button type="primary" link @click="viewSubUserItemDetail(item)">查看详情</el-button>
                  </div>
                </div>
              </el-card>
            </div>
            <div v-if="subUserItemsTotal > 0" class="pagination mt-md flex-between">
              <span class="total-text">共 {{ subUserItemsTotal }} 条记录</span>
              <el-pagination
                v-model:current-page="subUserItemsPage"
                v-model:page-size="subUserItemsPageSize"
                :page-sizes="[10, 20, 50, 100]"
                :total="subUserItemsTotal"
                layout="total, sizes, prev, pager, next, jumper"
                @current-change="loadSubUserItems"
                @size-change="loadSubUserItems"
              />
            </div>
          </template>

          <!-- 管理员任务列表 -->
          <template v-else>
            <el-table v-loading="tasksLoading" :data="recentTasks" style="width: 100%">
              <el-table-column prop="id" label="任务ID" width="80" />
              <el-table-column prop="name" label="任务名称" min-width="160" show-overflow-tooltip />
              <!-- 超级管理员：显示所属管理员列 -->
              <el-table-column v-if="isSuperAdmin" prop="owner_admin_name" label="所属管理员" width="100">
                <template #default="{ row }">
                  <span>{{ row.owner_admin_name || '-' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="total_count" label="总数" width="80" align="center">
                <template #default="{ row }">
                  <span style="font-weight: 600;">{{ row.total_count }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="queued_count" label="排队中" width="80" align="center">
                <template #default="{ row }">
                  <span style="color: #909399;">{{ row.queued_count }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="generating_count" label="生成中" width="80" align="center">
                <template #default="{ row }">
                  <span style="color: var(--color-primary);">{{ row.generating_count }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="failed_count" label="失败" width="80" align="center">
                <template #default="{ row }">
                  <span v-if="row.failed_count > 0" style="color: #f56c6c; font-weight: 600;">{{ row.failed_count }}</span>
                  <span v-else>{{ row.failed_count }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="pending_publish_count" label="待发布" width="80" align="center" />
              <el-table-column prop="published_count" label="已发布" width="80" align="center" />
              <el-table-column prop="created_at" label="创建时间" width="170">
                <template #default="{ row }">
                  {{ formatDateTime(row.created_at) }}
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="getStatusType(row.status)" size="small">
                    {{ row.status }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="90" align="center">
                <template #default="{ row }">
                  <el-button type="primary" link size="small" @click="viewTask(row)">查看</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!tasksLoading && recentTasks.length === 0" description="暂无任务数据" />
            <div v-if="recentTasksTotal > 0" class="pagination mt-md flex-between">
              <span class="total-text">共 {{ recentTasksTotal }} 条记录</span>
              <el-pagination
                v-model:current-page="recentTasksPage"
                v-model:page-size="recentTasksPageSize"
                :page-sizes="[10, 20, 50, 100]"
                :total="recentTasksTotal"
                layout="total, sizes, prev, pager, next, jumper"
                @current-change="loadRecentTasks"
                @size-change="loadRecentTasks"
              />
            </div>
          </template>
        </div>
      </el-col>
    </el-row>

    <!-- 失败任务告警 - 仅对管理员显示 -->
    <el-row v-if="!isSubUser" :gutter="20" class="mt-lg">
      <el-col :span="24">
        <div class="card">
          <div class="card-header flex-between">
            <h3 class="section-title" style="margin-bottom: 0; color: #f56c6c;">
              <el-icon style="margin-right: 4px;"><WarningFilled /></el-icon>
              失败任务告警
            </h3>
            <el-button type="danger" size="small" :disabled="failedTasks.length === 0" @click="clearAllAlerts">
              <el-icon><Delete /></el-icon>
              清除告警
            </el-button>
          </div>
          <el-table v-loading="failedTasksLoading" :data="failedTasks" style="width: 100%">
            <el-table-column prop="id" label="任务ID" width="80" />
            <el-table-column prop="name" label="任务名称" min-width="140" show-overflow-tooltip />
            <!-- 超级管理员：显示所属管理员列 -->
            <el-table-column v-if="isSuperAdmin" prop="owner_admin_name" label="所属管理员" width="120">
              <template #default="{ row }">
                <span>{{ row.owner_admin_name || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="failed_count" label="失败数量" width="100" />
            <el-table-column prop="error" label="错误信息" show-overflow-tooltip />
            <el-table-column prop="latest_failed_at" label="失败时间" width="170">
              <template #default="{ row }">
                {{ formatDateTime(row.latest_failed_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="viewFailedTask(row)">查看</el-button>
                <el-button type="danger" size="small" @click="clearAlert(row)">清除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!failedTasksLoading && failedTasks.length === 0" description="暂无失败任务" />
        </div>
      </el-col>
    </el-row>
    </div>

    <!-- 趋势分析Tab -->
    <TrendAnalysisPanel v-if="activeTab === 'trend'" />

    <!-- 创作者内容详情抽屉 -->
    <SubUserItemDetailDrawer
      v-model:visible="subUserItemDrawerVisible"
      :item="currentSubUserItem"
      @published="handlePublished"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User,
  Document,
  Clock,
  SuccessFilled,
  WarningFilled,
  Refresh,
  Delete,
  Loading,
  Monitor,
  VideoPlay,
  Timer,
  Cpu
} from '@element-plus/icons-vue'
import { apiClient, type OperatorOption } from '@/api/types'
import { useAuthStore } from '@/stores/auth'
import TrendAnalysisPanel from './TrendAnalysisPanel.vue'
import SubUserItemDetailDrawer from '@/components/SubUserItemDetailDrawer.vue'

defineOptions({
  name: 'DashboardView'
})

const router = useRouter()
const authStore = useAuthStore()

const activeTab = ref('overview')
const isSuperAdmin = computed(() => authStore.userRole === 'super_admin')
const isSubUser = computed(() => authStore.userRole === 'sub_user')

// 防止重复加载的标志
const isLoadingData = ref(false)

// 统计卡片筛选 - 日期范围，默认当天
const today = new Date().toISOString().split('T')[0]
const statsDateRange = ref<[string, string]>([today, today])
const statsOperatorId = ref<number | undefined>(undefined)

// 创作管理员列表和筛选
const operatorList = ref<OperatorOption[]>([])
const selectedOperatorId = ref<number | undefined>(undefined)
const dateRange = ref<[string, string] | null>(null)

// 统计数据
const stats = ref({
  total_sub_users: 0,
  today_generated: 0,
  pending_publish: 0,
  published: 0
})

// 表格数据
const recentTasks = ref<any[]>([])
const recentTasksTotal = ref(0)
const recentTasksPage = ref(1)
const recentTasksPageSize = ref(10)
const failedTasks = ref<any[]>([])

// 创作者内容列表数据
const subUserItems = ref<any[]>([])
const subUserItemsTotal = ref(0)
const subUserItemsPage = ref(1)
const subUserItemsPageSize = ref(10)

// 创作者内容详情抽屉
const subUserItemDrawerVisible = ref(false)
const currentSubUserItem = ref<any>(null)

// 加载状态
const statsLoading = ref(true)
const tasksLoading = ref(true)
const failedTasksLoading = ref(true)
const queueLoading = ref(true)

// 队列状态（仅超级管理员）
const queueStatus = ref<any>({
  max_concurrent: 0,
  active_count: 0,
  waiting_count: 0,
  can_dispatch: true,
  active_tasks: [],
  waiting_tasks: []
})

// Worker 状态（仅超级管理员）
const workerStatus = ref<any>({
  worker_running_count: 0,
  worker_idle_count: 0,
  worker_total: 0,
  workers: []
})

// 格式化日期时间
const formatDateTime = (dateStr: string | undefined) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 加载统计数据
const loadStats = async () => {
  try {
    statsLoading.value = true
    const params: any = {}
    if (statsDateRange.value && statsDateRange.value.length === 2) {
      params.start_date = statsDateRange.value[0]
      params.end_date = statsDateRange.value[1]
    }
    if (statsOperatorId.value) {
      params.operator_id = statsOperatorId.value
    }
    const res = await apiClient.getDashboardStats(params)
    if (res) {
      stats.value = res
    }
  } catch (error: any) {
    console.error('加载统计数据失败:', error)
    ElMessage.error('加载统计数据失败')
  } finally {
    statsLoading.value = false
  }
}

// 加载创作管理员列表
const loadOperatorList = async () => {
  if (!isSuperAdmin.value) return
  try {
    const res = await apiClient.getOperatorList()
    operatorList.value = res || []
  } catch (error: any) {
    console.error('加载创作管理员列表失败:', error)
  }
}

// 加载最近任务
const loadRecentTasks = async () => {
  try {
    tasksLoading.value = true
    const params: any = { limit: recentTasksPageSize.value, page: recentTasksPage.value }
    if (selectedOperatorId.value) {
      params.operator_id = selectedOperatorId.value
    }
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const res = await apiClient.getDashboardRecentTasks(params)
    recentTasks.value = res?.tasks || []
    recentTasksTotal.value = res?.total || 0
  } catch (error: any) {
    console.error('加载最近任务失败:', error)
    ElMessage.error('加载最近任务失败')
  } finally {
    tasksLoading.value = false
  }
}

// 加载失败任务
const loadFailedTasks = async () => {
  try {
    failedTasksLoading.value = true
    const res = await apiClient.getDashboardFailedTasks({ limit: 10 })
    failedTasks.value = res?.tasks || []
  } catch (error: any) {
    console.error('加载失败任务失败:', error)
    ElMessage.error('加载失败任务失败')
  } finally {
    failedTasksLoading.value = false
  }
}

// 处理创作管理员筛选变化
const handleOperatorChange = () => {
  recentTasksPage.value = 1
  loadRecentTasks()
}

// 处理日期筛选变化
const handleDateChange = () => {
  if (isSubUser.value) {
    subUserItemsPage.value = 1
    loadSubUserItems()
  } else {
    recentTasksPage.value = 1
    loadRecentTasks()
  }
}

// 处理统计卡片筛选变化
const handleStatsFilterChange = () => {
  loadStats()
}

const getStatusType = (status: string) => {
  const map: Record<string, any> = {
    '生成中': 'primary',
    '已完成': 'success',
    '排队中': 'info',
    '失败': 'danger'
  }
  return map[status] || 'info'
}

const viewTask = (row: any) => {
  router.push(`/generation/detail/${row.id}`)
}

const clearAllAlerts = async () => {
  try {
    await ElMessageBox.confirm('确定要清除所有失败任务告警吗？', '提示', {
      type: 'warning',
      confirmButtonText: '确定清除',
      cancelButtonText: '取消'
    })
    await apiClient.dismissAllAlerts()
    failedTasks.value = []
    ElMessage.success('已清除所有告警')
  } catch {
  }
}

const clearAlert = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要清除这条告警吗？', '提示', {
      type: 'warning',
      confirmButtonText: '确定清除',
      cancelButtonText: '取消'
    })
    await apiClient.dismissAlert(row.id)
    const index = failedTasks.value.findIndex(item => item.id === row.id)
    if (index !== -1) {
      failedTasks.value.splice(index, 1)
    }
    ElMessage.success('已清除告警')
  } catch {
  }
}

const viewFailedTask = (row: any) => {
  router.push(`/generation/detail/${row.id}`)
}

// 创作者相关函数
const loadSubUserItems = async () => {
  try {
    tasksLoading.value = true
    const params: any = { limit: subUserItemsPageSize.value, page: subUserItemsPage.value }
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const res = await apiClient.getSubUserGenerationItems(params)
    // 转换数据格式，确保字段名兼容
    subUserItems.value = (res?.items || []).map((item: any) => ({
      ...item,
      taskName: item.taskName || item.task_name,
      generated_images: item.generated_images || item.generated_image_urls_json,
      generated_thumbnails: item.generated_thumbnails || item.generated_image_thumbnails_json,
      generated_videos: item.generated_videos || (item.generated_video_url ? [item.generated_video_url] : [])
    }))
    subUserItemsTotal.value = res?.total || 0
  } catch (error: any) {
    console.error('加载创作者内容列表失败:', error)
    ElMessage.error('加载内容列表失败')
  } finally {
    tasksLoading.value = false
  }
}

const getSubUserItemStatusType = (item: any) => {
  // 已发布状态
  if ((item as any).distribution_status === 'published') return 'success'
  // 待发布状态（包括distributed和pending_publish）
  if (item.distribution_status === 'distributed' || item.distribution_status === 'pending_publish') return 'warning'
  // 生成完成但未分发���显示为待发布
  if (item.status === 'completed') return 'warning'
  if (item.status === 'failed') return 'danger'
  if (item.status === 'generating') return 'primary'
  if (item.status === 'queued') return 'info'
  return 'info'
}

const getSubUserItemStatusLabel = (item: any) => {
  // 已发布状态
  if ((item as any).distribution_status === 'published') return '已发布'
  // 已分发或待发布状态都显示为待发布
  if (item.distribution_status === 'distributed' || item.distribution_status === 'pending_publish') return '待发布'
  // 生成完成但未分发也显示为待发布
  if (item.status === 'completed') return '待发布'
  if (item.status === 'failed') return '失败'
  if (item.status === 'generating') return '生成中'
  if (item.status === 'queued') return '排队中'
  return item.status
}

const viewSubUserItemDetail = (item: any) => {
  // 转换数据格式，确保字段名兼容
  currentSubUserItem.value = {
    ...item,
    taskName: item.taskName || item.task_name,
    generated_images: item.generated_images || item.generated_image_urls_json,
    generated_thumbnails: item.generated_thumbnails || item.generated_image_thumbnails_json,
    generated_videos: item.generated_videos || (item.generated_video_url ? [item.generated_video_url] : [])
  }
  subUserItemDrawerVisible.value = true
}

const parseTopics = (topics: any): string[] => {
  if (!topics) return []
  if (Array.isArray(topics)) return topics
  if (typeof topics === 'string') {
    try {
      const parsed = JSON.parse(topics)
      return Array.isArray(parsed) ? parsed : []
    } catch {
      return topics.split(',').map(t => t.trim()).filter(Boolean)
    }
  }
  return []
}

const handlePublished = () => {
  // 重新加载数据
  loadStats()
  if (isSubUser.value) {
    loadSubUserItems()
  } else {
    loadRecentTasks()
  }
}

// 加载队列状态（仅超级管理员）
const loadQueueStatus = async () => {
  if (!isSuperAdmin.value) return
  
  try {
    queueLoading.value = true
    const [queueRes, workerRes] = await Promise.all([
      apiClient.getQueueStatus(),
      apiClient.getWorkerStatus()
    ])
    if (queueRes) {
      queueStatus.value = queueRes
    }
    if (workerRes) {
      workerStatus.value = workerRes
    }
  } catch (error: any) {
    console.error('加载队列状态失败:', error)
    // 不显示错误提示，避免影响其他数据加载
  } finally {
    queueLoading.value = false
  }
}

// 计算 Worker 使用率百分比
const workerUsagePercentage = computed(() => {
  const total = workerStatus.value.worker_total || 0
  const running = workerStatus.value.worker_running_count || 0
  if (total === 0) return 0
  return Math.round((running / total) * 100)
})

// Worker 使用率颜色
const workerUsageColor = computed(() => {
  const percentage = workerUsagePercentage.value
  if (percentage >= 90) return '#f56c6c'  // 红色：接近满载
  if (percentage >= 70) return '#e6a23c'  // 橙色：较高
  return '#67c23a'  // 绿色：正常
})

// 计算任务运行时长
const getRunningTime = (startedAt: string | undefined) => {
  if (!startedAt) return '-'
  const start = new Date(startedAt)
  const now = new Date()
  const diffMs = now.getTime() - start.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 60) return `${diffMins}分钟`
  const hours = Math.floor(diffMins / 60)
  const mins = diffMins % 60
  return `${hours}小时${mins}分钟`
}

// 加载所有数据
const loadAllData = async () => {
  // 防止重复加载（除非强制刷新）
  if (isLoadingData.value) {
    console.log('[Dashboard] 已在加载中，跳过')
    return
  }
  isLoadingData.value = true

  try {
    // 确保用户信息已加载
    if (!authStore.user && !authStore.isInitialized) {
      console.log('[Dashboard] 等待用户信息加载...')
      await authStore.fetchUser()
    }

    // 根据用户角色决定加载哪些数据
    const role = authStore.userRole
    console.log('[Dashboard] 当前用户角色:', role, '用户信息:', authStore.user)

        const promises = [
            loadStats(),
            loadOperatorList(),
            loadQueueStatus()  // 加载队列状态（仅超级管理员）
        ]

    if (role === 'sub_user') {
      console.log('[Dashboard] 加载创作者内容列表')
      promises.push(loadSubUserItems())
    } else {
      console.log('[Dashboard] 加载管理员任务列表')
      promises.push(loadRecentTasks())
      promises.push(loadFailedTasks())
    }

    await Promise.all(promises)
  } finally {
    isLoadingData.value = false
  }
}

// 是否是首次加载
let isFirstLoad = true

onMounted(async () => {
  console.log('[Dashboard] onMounted, isFirstLoad:', isFirstLoad)
  // 首次加载
  if (isFirstLoad) {
    isFirstLoad = false
    await loadAllData()
  }
})

// 组件激活时刷新数据（从其他页面返回时）
onActivated(async () => {
  console.log('[Dashboard] onActivated, isFirstLoad:', isFirstLoad)
  // 非首次加载时才刷新（首次由 onMounted 处理）
  if (!isFirstLoad) {
    await loadAllData()
  }
})
</script>

<style lang="scss" scoped>
// 导入高级设计规范样式
@import './dashboard.scss';

.dashboard-view {
  padding: 0;
}

.tab-container {
  margin-bottom: 20px;
}

.card {
  background: var(--bg-secondary);
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--color-border-default);
  padding: 20px;
}

.stats-section {
  margin-bottom: 16px;
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 0;
}


  .stat-card {
    display: flex;
    align-items: center;
    gap: 14px;
    background: var(--bg-secondary);
    padding: 18px 20px;
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--color-border-default);
    transition: all var(--transition-normal) var(--easing-standard);

    &:hover {
      box-shadow: var(--shadow-md);
      border-color: var(--color-border-hover);
    }
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: var(--radius-lg);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

    &.stat-icon-primary {
      background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
      color: #fff;
      box-shadow: 0 4px 12px rgba(22, 119, 255, 0.20);
    }

    &.stat-icon-success {
      background: linear-gradient(135deg, var(--color-success) 0%, #23C343 100%);
      color: #fff;
      box-shadow: 0 4px 12px rgba(0, 180, 42, 0.20);
    }

    &.stat-icon-warning {
      background: linear-gradient(135deg, var(--color-warning) 0%, #FF9A2E 100%);
      color: #fff;
      box-shadow: 0 4px 12px rgba(255, 125, 0, 0.20);
    }

    &.stat-icon-info {
      background: linear-gradient(135deg, var(--color-info) 0%, #9DA4AE 100%);
      color: #fff;
    }

    &.stat-icon-danger {
      background: linear-gradient(135deg, var(--color-error) 0%, #FF6B6B 100%);
      color: #fff;
      box-shadow: 0 4px 12px rgba(245, 63, 63, 0.20);
    }
  }



.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-value-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 29px;
}

.loading-spinner {
  animation: loading-rotate 1s linear infinite;
}

@keyframes loading-rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.card-header {
  margin-bottom: 16px;
}

.mt-lg {
  margin-top: 20px;
}

.mb-lg {
  margin-bottom: 20px;
}

.flex-between {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.flex-center {
  display: flex;
  align-items: center;
}

.gap-sm {
  gap: 8px;
}

.section-title {
  font-size: 16px;
  font-weight: 500;
  margin: 0;
  color: var(--text-primary);
}

.filter-label {
  color: var(--text-secondary);
  font-size: 14px;
}

.admin-label {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 2px;
}

.pagination {
  padding: $spacing-sm 0;
  margin-top: $spacing-md;
  white-space: nowrap;
  display: flex;
  align-items: center;
}

.total-text {
  color: var(--color-text-secondary);
  font-size: $font-size-sm;
  white-space: nowrap;
  font-size: 14px;
  white-space: nowrap;
}

.mt-md {
  margin-top: 12px;
}

.mb-md {
  margin-bottom: 12px;
}

.clickable-table {
  :deep(.el-table__row) {
    cursor: pointer;
  }
}

/* 创作者内容列表样式 */
.sub-user-item-list {
  .sub-user-item-card {
    transition: all 0.3s;

    &:hover {
      box-shadow: var(--shadow-lg);
    }

    .item-header {
      .item-title {
        display: flex;
        align-items: center;
        gap: 12px;

        .task-name {
          font-size: 16px;
          font-weight: 600;
          color: var(--text-primary);
        }
      }

      .item-time {
        font-size: 14px;
        color: var(--text-secondary);
      }
    }

    .item-content {
      .content-row {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 8px 0;
        border-bottom: 1px dashed var(--border-color);

        &:last-child {
          border-bottom: none;
        }

        .row-label {
          flex-shrink: 0;
          width: 60px;
          font-size: 12px;
          color: var(--text-placeholder);
          padding-top: 2px;
        }

        .row-value {
          flex: 1;
          min-width: 0;
        }
      }

      .title-row {
        .title-value {
          font-size: 15px;
          font-weight: 600;
          color: var(--text-primary);
          line-height: 1.5;
        }
      }

      .text-row {
        .text-value {
          font-size: 13px;
          color: var(--text-secondary);
          line-height: 1.6;
          display: -webkit-box;
          -webkit-line-clamp: 3;
          line-clamp: 3;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
      }

      .topics-row {
        .topics-value {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          align-items: center;

          .topic-mini-tag {
            font-size: 11px;
          }

          .more-topics {
            font-size: 11px;
            color: var(--text-placeholder);
          }
        }
      }

      .images-row {
        .images-value {
          .image-thumbs {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;

            .image-thumb {
              width: 60px;
              height: 60px;
              border-radius: 4px;
              cursor: pointer;
              transition: transform 0.2s;

              &:hover {
                transform: scale(1.05);
              }
            }

            .more-images {
              width: 60px;
              height: 60px;
              border-radius: 4px;
              background: var(--bg-tertiary);
              display: flex;
              align-items: center;
              justify-content: center;
              font-size: 12px;
              color: var(--text-placeholder);
            }
          }
        }
      }
    }

    .item-footer {
      .item-meta {
        display: flex;
        gap: 16px;

        .meta-item {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 14px;
          color: var(--text-secondary);
        }

        .id-tag {
          font-family: var(--font-family-mono);
          font-size: 12px;
          color: var(--text-placeholder);
          background: var(--bg-tertiary);
          padding: 2px 8px;
          border-radius: 4px;
        }
      }
    }
  }
}

.mt-sm {
  margin-top: 4px;
}

/* 创作者内容详情抽屉样式 */
.sub-user-item-detail {
  .detail-section {
    margin-bottom: 24px;

    h4 {
      font-size: 15px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 12px;
    }

    p {
      font-size: 14px;
      color: var(--text-secondary);
      line-height: 1.6;
      margin: 0;
    }

    .text-content {
      white-space: pre-wrap;
      word-break: break-word;
    }
  }

  .image-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 16px;

    .image-item {
      border-radius: 8px;
      overflow: hidden;
      box-shadow: var(--shadow-sm);

      :deep(.el-image) {
        width: 100%;
        height: 200px;
      }
    }
  }

  .video-list {
    display: flex;
    flex-direction: column;
    gap: 16px;

    .video-item {
      video {
        width: 100%;
        max-height: 400px;
        border-radius: 8px;
      }
    }
  }

  .publish-section {
    margin-top: 32px;
    padding-top: 24px;
    border-top: 1px solid var(--border-color);
    text-align: center;
  }

  .mb-lg {
    margin-bottom: 16px;
  }

  .mt-lg {
    margin-top: 16px;
  }

  /* 结构化内容卡片 */
  .structured-content {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .content-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    overflow: hidden;
    transition: border-color 0.2s;

    &:hover {
      border-color: #dcdfe6;
    }
  }

  .card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    background: var(--bg-tertiary);
    border-bottom: 1px solid var(--border-color);

    .card-icon {
      font-size: 16px;
    }

    .card-label {
      font-size: 13px;
      font-weight: 600;
      color: var(--text-primary);
      flex: 1;
    }
  }

  .card-body {
    padding: 16px;
  }

  .card-footer {
    padding: 8px 16px;
    border-top: 1px solid var(--border-color);
    text-align: center;
  }

  /* 标题卡片 */
  .title-card .title-body {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
  }

  /* 正文卡片 */
  .body-card .text-body {
    font-size: 14px;
    color: var(--text-secondary);
    line-height: 1.8;
    max-height: 400px;
    overflow-y: auto;

    &.collapsed {
      max-height: 200px;
      overflow: hidden;
      position: relative;

      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 40px;
        background: linear-gradient(transparent, white);
      }
    }
  }

  .parsed-text {
    white-space: pre-wrap;
    word-break: break-word;
  }

  .text-paragraph {
    display: inline;
  }

  /* 话题卡片 */
  .topics-card .topics-body {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 12px 16px;

    .topic-tag {
      font-weight: 500;
    }
  }

  .image-gallery {
    .gallery-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
      gap: 12px;
    }
    .gallery-item {
      width: 100%;
      height: 150px;
      border-radius: 6px;
      background: var(--bg-tertiary);
    }
  }

  .video-section {
    .section-label {
      font-size: 14px;
      font-weight: 500;
      color: var(--text-primary);
      margin-bottom: 8px;
    }
    .video-player-container {
      .video-player {
        width: 100%;
        max-height: 400px;
        border-radius: 8px;
      }
    }
    .video-list {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
  }

  .section-label {
    font-size: 14px;
    font-weight: 500;
    color: var(--text-primary);
    margin-bottom: 8px;
  }

  .actions-bar {
    padding-top: 16px;
    border-top: 1px solid var(--border-color);
  }
}

/* ============================================
   任务队列监控样式
   ============================================ */
.queue-status-content {
  padding: 16px 0;
}

// 统计卡片
.queue-stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--color-bg-tertiary);
  padding: 16px 18px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-default);
  height: 100%;
  transition: all var(--transition-normal) var(--easing-standard);

  &:hover {
    box-shadow: var(--shadow-md);
    border-color: var(--color-border-hover);
    transform: translateY(-2px);
  }

  &.active {
    border-left: 4px solid var(--color-primary);
  }
  &.waiting {
    border-left: 4px solid var(--color-warning);
  }
  &.running {
    border-left: 4px solid var(--color-error);
  }
  &.idle {
    border-left: 4px solid var(--color-success);
  }
}

// 图标容器 + 配色
.queue-stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.queue-icon-primary {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
  box-shadow: 0 4px 12px rgba(22, 119, 255, 0.25);
}

.queue-icon-warning {
  background: linear-gradient(135deg, var(--color-warning) 0%, #FF9A2E 100%);
  box-shadow: 0 4px 12px rgba(255, 125, 0, 0.25);
}

.queue-icon-danger {
  background: linear-gradient(135deg, var(--color-error) 0%, #FF6B6B 100%);
  box-shadow: 0 4px 12px rgba(245, 63, 63, 0.25);
}

.queue-icon-success {
  background: linear-gradient(135deg, var(--color-success) 0%, #23C343 100%);
  box-shadow: 0 4px 12px rgba(0, 180, 42, 0.25);
}

.queue-stat-content {
  flex: 1;
  min-width: 0;
}

.queue-stat-value {
  font-family: var(--font-family-heading);
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1.1;
}

.queue-stat-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-top: 4px;
}

// 容量进度条
.queue-capacity-bar {
  margin: 20px 0;
  padding: 20px;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-default);

  // 进度条内文字 - 用深色确保在任何填充%下都可读
  :deep(.el-progress-bar__innerText) {
    color: var(--color-text-primary) !important;
    font-weight: 700;
    font-size: 13px;
  }

  // 轨道背景加深
  :deep(.el-progress-bar__outer) {
    background-color: var(--color-bg-secondary);
  }
}

.capacity-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 12px;
}

.capacity-text {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-top: 10px;
  text-align: center;
  font-weight: 500;
}

// 子标题
.sub-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 20px 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border-default);
}
</style>
