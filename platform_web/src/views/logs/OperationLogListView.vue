<template>
  <div class="operation-logs-view">
    <h2 class="page-title">操作日志</h2>

    <div class="card">
      <!-- 筛选工具栏 -->
      <div class="toolbar flex-between mb-md">
        <div class="toolbar-left flex gap-md flex-wrap">
          <el-select v-model="queryParams.module" placeholder="模块筛选" clearable style="width: 140px;">
            <el-option label="用户管理" value="users" />
            <el-option label="模板管理" value="templates" />
            <el-option label="素材管理" value="materials" />
            <el-option label="内容生成" value="generation" />
            <el-option label="分发管理" value="distribution" />
            <el-option label="系统设置" value="system" />
          </el-select>
          <el-select v-model="queryParams.action" placeholder="操作类型" clearable style="width: 120px;">
            <el-option label="创建" value="create" />
            <el-option label="更新" value="update" />
            <el-option label="删除" value="delete" />
            <el-option label="分发" value="distribute" />
            <el-option label="发布" value="publish" />
            <el-option label="登录" value="login" />
            <el-option label="退出" value="logout" />
            <el-option label="取消" value="cancel" />
            <el-option label="重试" value="retry" />
            <el-option label="复制" value="copy" />
            <el-option label="禁用" value="disable" />
            <el-option label="启用" value="enable" />
            <el-option label="导入" value="import" />
            <el-option label="导出" value="export" />
          </el-select>
          <el-select v-model="queryParams.user_type" placeholder="用户类型" clearable style="width: 130px;">
            <el-option label="超级管理员" value="super_admin" />
            <el-option label="创作管理员" value="operator" />
            <el-option label="创作者" value="sub_user" />
          </el-select>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 260px;"
            @change="handleDateChange"
          />
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
        </div>
        <div class="toolbar-right">
          <el-button :icon="Download" @click="handleExport">导出</el-button>
        </div>
      </div>

      <!-- 日志列表 -->
      <el-table :data="logList" style="width: 100%" v-loading="loading" :default-sort="{ prop: 'created_at', order: 'descending' }">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="模块" width="100">
          <template #default="{ row }">
            <el-tag :type="getModuleTagType(row.module)" size="small">
              {{ getModuleName(row.module) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-tag :type="getActionTagType(row.action)" size="small">
              {{ getActionName(row.action) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="用户类型" width="100">
          <template #default="{ row }">
            <span>{{ getUserTypeName(row.operator_id, row.sub_user_id) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作者名称" width="120">
          <template #default="{ row }">
            <span>{{ row.operator_name || row.sub_user_name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="table_name" label="表名" width="120" show-overflow-tooltip />
        <el-table-column prop="record_id" label="记录ID" width="80" />
        <el-table-column prop="ip_address" label="IP地址" width="130" />
        <el-table-column prop="created_at" label="操作时间" width="170" sortable />
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleViewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination mt-md flex-between">
        <span class="total-text">共 {{ total }} 条记录</span>
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.limit"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="loadLogs"
          @size-change="loadLogs"
        />
      </div>
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="showDetailDialog" title="日志详情" width="700px">
      <el-descriptions :column="2" border v-if="currentLog">
        <el-descriptions-item label="ID">{{ currentLog.id }}</el-descriptions-item>
        <el-descriptions-item label="模块">{{ getModuleName(currentLog.module) }}</el-descriptions-item>
        <el-descriptions-item label="操作">{{ getActionName(currentLog.action) }}</el-descriptions-item>
        <el-descriptions-item label="描述">{{ currentLog.description || '-' }}</el-descriptions-item>
        <el-descriptions-item label="操作者名称">{{ currentLog.operator_name || currentLog.sub_user_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="表名">{{ currentLog.table_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="记录ID">{{ currentLog.record_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ currentLog.ip_address || '-' }}</el-descriptions-item>
        <el-descriptions-item label="User-Agent" :span="2">{{ currentLog.user_agent || '-' }}</el-descriptions-item>
        <el-descriptions-item label="操作时间" :span="2">{{ currentLog.created_at }}</el-descriptions-item>
        <el-descriptions-item label="旧值" :span="2">
          <pre v-if="currentLog.old_value_json" style="margin: 0; white-space: pre-wrap;">{{ formatJson(currentLog.old_value_json) }}</pre>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="新值" :span="2">
          <pre v-if="currentLog.new_value_json" style="margin: 0; white-space: pre-wrap;">{{ formatJson(currentLog.new_value_json) }}</pre>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="额外数据" :span="2">
          <pre v-if="currentLog.extra_data_json" style="margin: 0; white-space: pre-wrap;">{{ formatJson(currentLog.extra_data_json) }}</pre>
          <span v-else>-</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Search, Refresh, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { apiClient, type OperationLog, type OperationLogQueryParams } from '@/api/types'

const loading = ref(false)
const logList = ref<OperationLog[]>([])
const total = ref(0)
const dateRange = ref<[string, string] | null>(null)

const queryParams = reactive<OperationLogQueryParams>({
  page: 1,
  limit: 20,
  module: undefined,
  action: undefined,
  user_type: undefined,
  start_date: undefined,
  end_date: undefined
})

const showDetailDialog = ref(false)
const currentLog = ref<OperationLog | null>(null)

// 模块名称映射
const moduleNames: Record<string, string> = {
  users: '用户管理',
  templates: '模板管理',
  materials: '素材管理',
  generation: '内容生成',
  distribution: '分发管理',
  system: '系统设置'
}

// 操作名称映射
const actionNames: Record<string, string> = {
  create: '创建',
  update: '更新',
  delete: '删除',
  distribute: '分发',
  publish: '发布',
  login: '登录',
  logout: '退出',
  cancel: '取消',
  retry: '重试',
  copy: '复制',
  disable: '禁用',
  enable: '启用',
  transfer: '转移',
  import: '导入',
  export: '导出'
}

// 模块标签类型
function getModuleTagType(module?: string): string {
  const types: Record<string, string> = {
    users: 'warning',
    templates: 'primary',
    materials: 'success',
    generation: 'danger',
    distribution: 'info',
    system: ''
  }
  return types[module || ''] || 'info'
}

// 操作标签类型
function getActionTagType(action?: string): string {
  const types: Record<string, string> = {
    create: 'success',
    update: 'primary',
    delete: 'danger',
    distribute: 'warning',
    publish: 'success',
    login: 'info',
    logout: 'info',
    cancel: 'warning',
    retry: 'warning',
    copy: 'primary',
    disable: 'danger',
    enable: 'success',
    import: 'primary',
    export: 'primary'
  }
  return types[action || ''] || 'info'
}

function getModuleName(module?: string): string {
  return module ? (moduleNames[module] || module) : '-'
}

function getActionName(action?: string): string {
  return action ? (actionNames[action] || action) : '-'
}

function getUserTypeName(operatorId?: number, subUserId?: number): string {
  if (subUserId) return '创作者'
  if (operatorId) return '创作管理员'
  return '-'
}

function handleDateChange(val: [string, string] | null) {
  if (val) {
    queryParams.start_date = val[0]
    queryParams.end_date = val[1]
  } else {
    queryParams.start_date = undefined
    queryParams.end_date = undefined
  }
}

function handleSearch() {
  queryParams.page = 1
  loadLogs()
}

function handleReset() {
  queryParams.module = undefined
  queryParams.action = undefined
  queryParams.user_type = undefined
  queryParams.start_date = undefined
  queryParams.end_date = undefined
  dateRange.value = null
  queryParams.page = 1
  loadLogs()
}

function handleViewDetail(row: OperationLog) {
  currentLog.value = row
  showDetailDialog.value = true
}

function formatJson(jsonStr?: string | Record<string, any>): string {
  if (!jsonStr) return ''
  if (typeof jsonStr === 'object') {
    return JSON.stringify(jsonStr, null, 2)
  }
  try {
    return JSON.stringify(JSON.parse(jsonStr), null, 2)
  } catch {
    return jsonStr
  }
}

function handleExport() {
  ElMessage.info('导出功能开发中')
}

async function loadLogs() {
  loading.value = true
  try {
    const res = await apiClient.getOperationLogs(queryParams)
    logList.value = res.items
    total.value = res.total
  } catch (error) {
    ElMessage.error('加载日志失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadLogs()
})
</script>

<style lang="scss" scoped>
@import './logs.scss';

.operation-logs-view {
  padding: 0;
}

.pre {
  margin: 0;
  white-space: pre-wrap;
  font-family: var(--font-family-mono);
  font-size: 12px;
  background: rgba(255, 255, 255, 0.02);
  padding: 12px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  color: var(--color-text-secondary);
}
</style>
