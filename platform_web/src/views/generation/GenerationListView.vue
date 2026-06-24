<template>
  <div class="generation-list-view">
    <h2 class="page-title">{{ isSubUser ? '我的内容' : '生成任务列表' }}</h2>

    <div class="card">
      <!-- 创作者视图 -->
      <template v-if="isSubUser">
        <div class="toolbar flex-between mb-md">
          <div class="toolbar-left flex gap-md">
            <el-select v-model="subUserSearchStatus" placeholder="状态筛选" style="width: 140px;">
              <el-option label="全部" value="" />
              <el-option label="待发布" value="pending_publish" />
              <el-option label="已发布" value="published" />
            </el-select>
            <el-button type="primary" :icon="Search" @click="handleSubUserSearch">搜索</el-button>
          </div>
        </div>

        <div class="sub-user-item-list" v-loading="subUserLoading">
          <el-empty v-if="subUserItems.length === 0 && !subUserLoading" description="暂无内容" />
          <el-card v-for="item in subUserItems" :key="item.id" class="sub-user-item-card mb-md" shadow="hover">
            <div class="item-header flex-between">
              <div class="item-title">
                <span class="task-name">{{ item.taskName || '任务 #' + item.task_id }}</span>
                <el-tag :type="getSubUserItemStatusType(item)" size="small" style="margin-left: 12px;">
                  {{ getSubUserItemStatusLabel(item) }}
                </el-tag>
              </div>
              <div class="item-time">{{ formatDate(item.created_at) }}</div>
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
              <div v-if="item.generated_image_urls_json && item.generated_image_urls_json.length > 0" class="content-row images-row">
                <span class="row-label">🖼️ 图片</span>
                <div class="row-value images-value">
                  <div class="image-thumbs">
                    <el-image
                      v-for="(img, idx) in (item.generated_image_thumbnails_json || item.generated_image_urls_json).slice(0, 4)"
                      :key="idx"
                      :src="img"
                      class="image-thumb"
                      fit="cover"
                      preview-teleported
                      :preview-src-list="item.generated_image_urls_json"
                      :initial-index="idx"
                    />
                    <div v-if="item.generated_image_urls_json.length > 4" class="more-images">
                      +{{ item.generated_image_urls_json.length - 4 }}
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

        <div class="pagination mt-lg flex-between" v-if="isSubUser">
          <span class="total-text">共 {{ subUserTotal }} 条记录</span>
          <el-pagination
            v-model:current-page="subUserCurrentPage"
            v-model:page-size="subUserPageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="subUserTotal"
            layout="total, sizes, prev, pager, next, jumper"
          />
        </div>
      </template>

      <!-- 管理员视图 -->
      <template v-else>
        <div class="toolbar flex-between mb-md">
          <div class="toolbar-left flex gap-md">
            <el-select v-model="searchStatus" placeholder="状态筛选" clearable style="width: 140px;">
              <el-option label="排队中" value="pending" />
              <el-option label="生成中" value="processing" />
              <el-option label="已完成" value="completed" />
              <el-option label="失败" value="failed" />
            </el-select>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
            />
            <el-input
              v-model="searchKeyword"
              placeholder="搜索任务ID/名称"
              :prefix-icon="Search"
              clearable
              style="width: 240px;"
            />
            <!-- 超级管理员：创作管理员筛选 -->
            <el-select
              v-if="isSuperAdmin"
              v-model="selectedOperatorId"
              placeholder="选择管理员"
              clearable
              style="width: 150px"
            >
              <el-option
                v-for="op in operatorList"
                :key="op.id"
                :label="op.name"
                :value="op.id"
              />
            </el-select>
            <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          </div>
          <div class="toolbar-right">
            <el-button v-if="!isSuperAdmin" type="primary" :icon="Plus" @click="goToCreate">创建任务</el-button>
          </div>
        </div>

        <div class="task-list" v-loading="loading">
          <el-empty v-if="tasks.length === 0 && !loading" description="暂无任务数据" />
          <el-card v-for="task in tasks" :key="task.id" class="task-card mb-md" shadow="hover">
            <div class="task-header flex-between">
              <div class="task-title">
                <span class="task-id">#{{ task.id }}</span>
                <span class="task-name">{{ task.name || task.material?.title || '素材 #' + task.material?.id || '-' }}</span>
                <el-tag :type="getStatusType(task.status)" size="small" style="margin-left: 12px;">
                  {{ getStatusLabel(task.status) }}
                </el-tag>
              </div>
              <div class="task-time">{{ formatDate(task.created_at) }}</div>
            </div>
            <div class="task-progress">
              <div class="progress-stats flex gap-lg">
                <div class="stat-item">
                  <span class="stat-label">总数</span>
                  <span class="stat-value">{{ task.total_count }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">排队中</span>
                  <span class="stat-value pending">{{ task.queued_count }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">生成中</span>
                  <span class="stat-value processing">{{ task.generating_count }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">失败</span>
                  <span class="stat-value failed">{{ task.failed_count }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">待发布</span>
                  <span class="stat-value pending-publish">{{ task.pending_publish_count }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">已发布</span>
                  <span class="stat-value published">{{ task.published_count }}</span>
                </div>
              </div>
              <el-progress
                :percentage="getProgress(task)"
                :status="task.status === 'failed' ? 'exception' : undefined"
                class="mt-md"
              />
            </div>
            <div class="task-footer flex-between mt-md">
              <div class="task-meta">
                <span v-if="isSuperAdmin && task.owner_admin_name" class="meta-item admin-name">
                  <el-icon><User /></el-icon>
                  管理员: {{ task.owner_admin_name }}
                </span>
                <span class="meta-item">
                  <el-icon><User /></el-icon>
                  创作者: {{ task.total_count }} 人
                </span>
              </div>
              <div class="task-actions">
                <el-button type="primary" link @click="viewDetail(task)">查看详情</el-button>
                <el-button type="warning" link v-if="task.failed_count > 0 && task.status !== 'cancelled'" @click="handleRetryFailed(task)">重试失败</el-button>
                <el-button type="danger" link v-if="task.status === 'processing'" @click="handleCancel(task)">取消</el-button>
              </div>
            </div>
          </el-card>
        </div>

        <div class="pagination mt-lg flex-between">
          <span class="total-text">共 {{ total }} 条记录</span>
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="total"
            layout="total, sizes, prev, pager, next, jumper"
          />
        </div>
      </template>
    </div>

    <!-- 创作者内容详情抽屉 -->
    <SubUserItemDetailDrawer
      v-model:visible="subUserItemDrawerVisible"
      :item="currentSubUserItem"
      @published="handlePublished"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, User, Document, Clock } from '@element-plus/icons-vue'
import { apiClient, type OperatorOption, type OperationLogCreateParams } from '@/api/types'
import type { GenerationTaskListItem, PaginationResponse, GenerationItem } from '@/api/types'
import { useAuthStore } from '@/stores/auth'
import SubUserItemDetailDrawer from '@/components/SubUserItemDetailDrawer.vue'

defineOptions({
  name: 'GenerationListView'
})

// 操作日志模块常量
const MODULE_GENERATION = 'generation'

// 记录操作日志
async function logOperation(params: OperationLogCreateParams) {
  try {
    await apiClient.createOperationLog(params)
  } catch (e) {
    console.error('Failed to log operation:', e)
  }
}

const router = useRouter()
const authStore = useAuthStore()
const isSuperAdmin = computed(() => authStore.userRole === 'super_admin')
const isSubUser = computed(() => authStore.userRole === 'sub_user')

const searchKeyword = ref('')
const searchStatus = ref('')
const dateRange = ref<[Date, Date] | null>(null)
const selectedOperatorId = ref<number | undefined>(undefined)
const operatorList = ref<OperatorOption[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const loading = ref(false)

// 任务列表
const tasks = ref<GenerationTaskListItem[]>([])

// 创作者相关
const subUserSearchStatus = ref('')
const subUserCurrentPage = ref(1)
const subUserPageSize = ref(10)
const subUserTotal = ref(0)
const subUserLoading = ref(false)
const subUserItems = ref<(GenerationItem & { taskName?: string })[]>([])
const subUserItemDrawerVisible = ref(false)
const currentSubUserItem = ref<(GenerationItem & { taskName?: string }) | null>(null)
const taskCache = ref<Map<number, string>>(new Map())

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 计算进度百分比
const getProgress = (task: GenerationTaskListItem) => {
  if (task.total_count === 0) return 0
  return Math.round((task.completed_count / task.total_count) * 100)
}

// 获取状态标签
const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    pending: '排队中',
    processing: '生成中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return labels[status] || status
}

// 状态映射
const statusOptions = [
  { label: '全部', value: '' },
  { label: '排队中', value: 'pending' },
  { label: '生成中', value: 'processing' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' },
  { label: '已取消', value: 'cancelled' }
]

// 获取任务列表
const fetchTasks = async () => {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      limit: pageSize.value
    }
    if (searchStatus.value) {
      params.status = searchStatus.value
    }
    if (searchKeyword.value) {
      params.keyword = searchKeyword.value
    }
    // 日期筛选
    if (dateRange.value && dateRange.value.length === 2) {
      const startDate = new Date(dateRange.value[0])
      const endDate = new Date(dateRange.value[1])
      params.start_date = `${startDate.getFullYear()}-${String(startDate.getMonth() + 1).padStart(2, '0')}-${String(startDate.getDate()).padStart(2, '0')}`
      params.end_date = `${endDate.getFullYear()}-${String(endDate.getMonth() + 1).padStart(2, '0')}-${String(endDate.getDate()).padStart(2, '0')}`
    }
    // 超级管理员创作管理员筛选
    if (isSuperAdmin.value && selectedOperatorId.value) {
      params.operator_id = selectedOperatorId.value
    }
    
    const response = await apiClient.getGenerationTasks(params)
    tasks.value = response.items || []
    total.value = response.total || 0
  } catch (error: any) {
    ElMessage.error(error.message || '获取任务列表失败')
  } finally {
    loading.value = false
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

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  fetchTasks()
}

// 重置搜索
const handleReset = () => {
  searchKeyword.value = ''
  searchStatus.value = ''
  dateRange.value = null
  selectedOperatorId.value = undefined
  currentPage.value = 1
  fetchTasks()
}

// 取消任务
const handleCancel = async (task: GenerationTaskListItem) => {
  try {
    await ElMessageBox.confirm(
      '确定要取消此任务吗？取消后正在运行的子任务将停止，已完成的内容保留。',
      '取消确认',
      {
        confirmButtonText: '确定取消',
        cancelButtonText: '再想想',
        type: 'warning',
      }
    )

    await apiClient.cancelGenerationTask(task.id)
    ElMessage.success('任务已取消')
    // 记录操作日志
    await logOperation({
      module: MODULE_GENERATION,
      action: 'cancel',
      description: `取消生成任务：${task.name || `任务 #${task.id}`}`,
      table_name: 'generation_task',
      record_id: task.id,
      old_value: { status: task.status }
    })
    fetchTasks()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '取消任务失败')
    }
  }
}


// 重试失败项（调用批量重试）
const handleRetryFailed = async (task: GenerationTaskListItem) => {
  try {
    // TODO: 实现批量重试 API
    ElMessage.info('正在重试失败的子任务...')
    // await apiClient.batchRetryGenerationItems({ task_id: task.id })
  } catch (error: any) {
    ElMessage.error(error.message || '重试失败')
  }
}

// 分页变化
watch([currentPage, pageSize], () => {
  if (!isSubUser.value) {
    fetchTasks()
  }
})

// 状态筛选变化
watch(searchStatus, () => {
  if (!isSubUser.value) {
    currentPage.value = 1
    fetchTasks()
  }
})

// 日期筛选变化
watch(dateRange, () => {
  if (!isSubUser.value) {
    currentPage.value = 1
    fetchTasks()
  }
})

// 创作管理员筛选变化
watch(selectedOperatorId, () => {
  if (!isSubUser.value) {
    currentPage.value = 1
    fetchTasks()
  }
})

// 组件激活时获取数据（keep-alive 激活或首次挂载）
let isInitialized = false
onActivated(() => {
  if (!isInitialized) {
    if (isSubUser.value) {
      fetchSubUserItems()
    } else {
      fetchTasks()
      loadOperatorList()
    }
    isInitialized = true
  } else {
    // 后续激活时只刷新数据，用于处理可能的状态变化
    if (isSubUser.value) {
      fetchSubUserItems()
    } else {
      fetchTasks()
    }
  }
})

const getStatusType = (status: string) => {
  const map: Record<string, any> = {
    pending: 'info',
    processing: 'primary',
    completed: 'success',
    failed: 'warning',
    cancelled: 'info'
  }
  return map[status] || 'info'
}

const goToCreate = () => {
  router.push('/generation/create')
}

const viewDetail = (task: GenerationTaskListItem) => {
  router.push(`/generation/detail/${task.id}`)
}

// 创作者相关功能
const fetchSubUserItems = async () => {
  subUserLoading.value = true
  try {
    // 使用专门的创作者内容 API
    const params: any = {
      page: subUserCurrentPage.value,
      limit: subUserPageSize.value
    }

    // 状态筛选：待发布或已发布
    if (subUserSearchStatus.value) {
      params.distribution_status = subUserSearchStatus.value
    }

    const response = await apiClient.getSubUserGenerationItems(params)
    subUserItems.value = (response.items || []).map((item: any) => ({
      ...item,
      taskName: item.taskName || item.task_name || `任务 #${item.task_id}`
    }))
    subUserTotal.value = response.total || 0
  } catch (error: any) {
    ElMessage.error(error.message || '获取内容列表失败')
  } finally {
    subUserLoading.value = false
  }
}

const handleSubUserSearch = () => {
  subUserCurrentPage.value = 1
  fetchSubUserItems()
}

const getSubUserItemStatusType = (item: any) => {
  // 已发布状态
  if ((item as any).distribution_status === 'published') return 'success'
  // 待发布状态（包括distributed和pending_publish）
  if (item.distribution_status === 'distributed' || item.distribution_status === 'pending_publish') return 'warning'
  // 生成完成但未分发也显示为待发布
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

const viewSubUserItemDetail = async (item: GenerationItem & { taskName?: string }) => {
  // 转换数据格式，确保字段名兼容
  currentSubUserItem.value = {
    ...item,
    taskName: item.taskName || item.task_name,
    generated_images: (item as any).generated_images || item.generated_image_urls_json,
    generated_thumbnails: (item as any).generated_thumbnails || item.generated_image_thumbnails_json,
    generated_videos: (item as any).generated_videos || (item.generated_video_url ? [item.generated_video_url] : [])
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
  // 刷新列表
  fetchSubUserItems()
}

// 创作者分页监听
watch([subUserCurrentPage, subUserPageSize], () => {
  if (isSubUser.value) {
    fetchSubUserItems()
  }
})
</script>

<style lang="scss" scoped>
@import './generation.scss';

.generation-list-view {
  padding: 0;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: $spacing-sm;
  padding: $spacing-sm 0;
  margin-bottom: $spacing-md;
  border-bottom: 1px solid var(--color-border-default);
}

.gap-md {
  gap: 8px;
}

.gap-lg {
  gap: 12px;
}

.flex {
  display: flex;
}

.flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.mb-md {
  margin-bottom: 8px;
}

.mt-md {
  margin-top: 8px;
}

.mt-sm {
  margin-top: 4px;
}

.mt-lg {
  margin-top: 16px;
}

.mb-lg {
  margin-bottom: 16px;
}

.task-list,
.sub-user-item-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-card,
.sub-user-item-card {
  padding: 4px 8px;

  .task-header,
  .item-header {
    margin-bottom: 0;
    .task-title,
    .item-title {
      display: flex;
      align-items: center;
      gap: 6px;
      .task-id,
      .item-id {
        font-family: var(--font-family-mono);
        color: var(--color-text-muted);
        font-size: 14px;
      }
      .task-name {
        font-size: 16px;
        font-weight: 500;
        color: var(--color-text-primary);
      }
    }
    .task-time,
    .item-time {
      font-size: 13px;
      color: var(--color-text-muted);
    }
  }

  .task-progress {
    // stat-item/stat-label/stat-value 已在 generation.scss 统一定义
    .progress-stats {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 2px;
    }

    :deep(.el-progress) {
      margin: 0;
      --el-progress-height: 3px;
    }
  }

  .item-content {
    .generated-title {
      font-size: 14px;
      margin-bottom: 4px;
    }
    .generated-text {
      font-size: 13px;
      color: var(--text-secondary);
      line-height: 1.5;
    }
  }

  .task-footer,
  .item-footer {
    margin-top: 2px;
  }

  .task-meta,
  .item-meta {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    .meta-item {
      display: inline-flex;
      align-items: center;
      color: var(--color-text-secondary);
      font-size: 13px;
      .el-icon {
        margin-right: 4px;
      }
      &.admin-name {
        color: var(--color-primary);
        font-weight: 500;
      }
    }
  }

  .task-actions,
  .item-actions {
    display: flex;
    gap: 4px;
  }
}

.sub-user-item-detail {
  .detail-section {
    .section-title {
      font-size: $font-size-md;
      font-weight: $font-weight-semibold;
      margin-bottom: $spacing-md;
      color: var(--color-text-primary);
    }
    .info-item {
      margin-bottom: $spacing-sm;
      font-size: $font-size-sm;
      .info-label {
        color: var(--color-text-secondary);
      }
      .info-value {
        color: var(--color-text-primary);
      }
    }
    .detail-item {
      margin-bottom: $spacing-sm;
      font-size: $font-size-sm;
      line-height: 1.6;
    }
    .detail-actions {
      display: flex;
      gap: 8px;
    }
    .image-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
  }
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

// 结构化内容卡片
.structured-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.content-card {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-default);
  border-radius: $radius-lg;
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
  background: var(--color-bg-tertiary);
  border-bottom: 1px solid var(--color-border-default);

  .card-icon {
    font-size: 16px;
  }

  .card-label {
    font-size: $font-size-sm;
    font-weight: $font-weight-semibold;
    color: var(--color-text-primary);
    flex: 1;
  }
}

.card-body {
  padding: 16px;
}

.card-footer {
  padding: 8px 16px;
  border-top: 1px solid var(--color-border-default);
  text-align: center;
}

// 标题卡片
.title-card .title-body {
  font-size: $font-size-md;
  font-weight: $font-weight-semibold;
  color: var(--color-text-primary);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

// 正文卡片
.body-card .text-body {
  font-size: $font-size-sm;
  color: var(--color-text-secondary);
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

// 话题卡片
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
    background: var(--color-bg-tertiary);
  }
}

.video-section {
  .video-player {
    width: 100%;
    max-height: 400px;
    border-radius: 6px;
  }
}

.actions-bar {
  padding-top: 16px;
  border-top: 1px solid var(--color-border-default);
}

// 创作者任务列表内容行样式
.content-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px dashed var(--color-border-default);

  &:last-child {
    border-bottom: none;
  }

  .row-label {
    flex-shrink: 0;
    width: 60px;
    font-size: 12px;
    color: var(--color-text-muted);
    padding-top: 4px;
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
    color: var(--color-text-secondary);
    line-height: 1.5;
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
      color: var(--color-text-muted);
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
        background: var(--color-bg-tertiary);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        color: var(--color-text-muted);
      }
    }
  }
}

.id-tag {
  font-family: var(--font-family-mono);
  font-size: 12px;
  color: var(--color-text-muted);
  background: var(--color-bg-tertiary);
  padding: 2px 8px;
  border-radius: 4px;
}
</style>
