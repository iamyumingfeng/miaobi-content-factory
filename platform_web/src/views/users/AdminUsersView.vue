<template>
  <div class="admin-users-view">
    <h2 class="page-title">创作管理员</h2>

    <div class="card">
      <div class="toolbar flex-between mb-md">
        <div class="toolbar-left flex gap-md">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索备注名"
            :prefix-icon="Search"
            clearable
            style="width: 240px;"
            @keyup.enter="handleSearch"
          />
          <el-select v-model="searchStatus" placeholder="状态筛选" clearable style="width: 120px;">
            <el-option label="全部" value="" />
            <el-option label="在线" value="online" />
            <el-option label="离线" value="offline" />
            <el-option label="已禁用" value="disabled" />
          </el-select>
          <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
        </div>
        <div class="toolbar-right">
          <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
            新增管理员
          </el-button>
        </div>
      </div>

      <el-table :data="adminList" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="userid" label="用户名" min-width="160" show-overflow-tooltip />
        <el-table-column prop="nickname" label="备注名" min-width="120" show-overflow-tooltip />
        <el-table-column prop="display_name" label="自定义昵称" min-width="120" show-overflow-tooltip />
        <el-table-column label="角色" min-width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'super_admin' ? 'danger' : 'primary'" size="small">
              {{ row.role === 'super_admin' ? '超级管理员' : '创作管理员' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag
              :type="
                row.status === 'online'
                  ? 'success'
                  : row.status === 'offline'
                  ? 'info'
                  : 'danger'
              "
              size="small"
            >
              {{
                row.status === 'online'
                  ? '在线'
                  : row.status === 'offline'
                  ? '离线'
                  : '已禁用'
              }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login_at" label="最后登录" width="180">
          <template #default="{ row }">
            {{ row.last_login_at || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" min-width="220" fixed="right">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
              <el-button type="warning" link size="small" @click="handleResetPassword(row)">重置密码</el-button>
              <el-button v-if="row.role !== 'super_admin'" :type="row.status === 'disabled' ? 'success' : 'danger'" link size="small" @click="handleToggleStatus(row)">
                {{ row.status === 'disabled' ? '启用' : '禁用' }}
              </el-button>
              <el-button v-if="row.role !== 'super_admin'" type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination mt-md flex-between">
        <span class="total-text">共 {{ total }} 条记录</span>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="loadAdmins"
          @size-change="loadAdmins"
        />
      </div>
    </div>

    <el-dialog v-model="showCreateDialog" :title="editMode ? '编辑管理员' : '新增管理员'" width="500px">
      <el-form :model="adminForm" :rules="adminRules" ref="adminFormRef" label-width="100px">
        <el-form-item label="角色" prop="role" v-if="!editMode">
          <el-select v-model="adminForm.role" placeholder="请选择角色" style="width: 100%;">
            <el-option label="创作管理员" value="operator" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注名" prop="nickname">
          <el-input v-model="adminForm.nickname" placeholder="请输入备注名" />
        </el-form-item>
        <el-form-item label="自定义昵称" prop="display_name" v-if="editMode">
          <el-input v-model="adminForm.display_name" placeholder="请输入自定义昵称" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!editMode">
          <el-input v-model="adminForm.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { Search, Plus } from '@element-plus/icons-vue'
import { apiClient, type User, type OperationLogCreateParams } from '@/api/types'

// 操作日志模块常量
const MODULE_USERS = 'users'

// 记录操作日志
async function logOperation(params: OperationLogCreateParams) {
  try {
    await apiClient.createOperationLog(params)
  } catch (e) {
    console.error('Failed to log operation:', e)
  }
}

const searchKeyword = ref('')
const searchStatus = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const loading = ref(false)
const submitLoading = ref(false)
const showCreateDialog = ref(false)
const editMode = ref(false)
const adminFormRef = ref<FormInstance>()
const editingAdmin = ref<User | null>(null)

const adminList = ref<User[]>([])

const adminForm = reactive({
  nickname: '',
  display_name: '',
  role: 'operator' as const,
  password: ''
})

const adminRules = {
  nickname: [{ required: true, message: '请输入备注名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur', min: 6 }]
}

const loadAdmins = async () => {
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

    // 只加载创作管理员，不显示超级管理员
    const operatorsResult = await apiClient.getOperators(params)

    const operators = (operatorsResult?.items || []).map((admin: any) => ({
      ...admin,
      role: 'operator' as const
    }))

    adminList.value = operators
    total.value = operatorsResult?.total || 0
  } catch (error: any) {
    ElMessage.error(error.message || '加载失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadAdmins()
}

const handleEdit = (row: User) => {
  editMode.value = true
  editingAdmin.value = row
  Object.assign(adminForm, {
    nickname: row.nickname,
    display_name: row.display_name || '',
    role: row.role || 'operator',
    password: ''
  })
  showCreateDialog.value = true
}

const handleResetPassword = async (row: User) => {
  try {
    await ElMessageBox.confirm(`确定要重置管理员 ${row.userid} 的密码吗？`, '提示', {
      type: 'warning'
    })
    // 生成随机密码
    const newPassword = Math.random().toString(36).slice(-8)
    // 调用后端API更新密码
    if (row.role === 'super_admin') {
      await apiClient.resetSuperAdminPassword(row.id, newPassword)
    } else {
      await apiClient.resetOperatorPassword(row.id, newPassword)
    }
    ElMessage.success(`密码已重置为: ${newPassword}，请妥善保存`)
    // 记录操作日志
    await logOperation({
      module: MODULE_USERS,
      action: 'update',
      description: `重置管理员密码：${row.userid}`,
      table_name: 'operator',
      record_id: row.id,
      extra_data: { action_type: 'reset_password' }
    })
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '重置密码失败')
    }
  }
}

const handleSubmit = async () => {
  if (!adminFormRef.value) return
  await adminFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      submitLoading.value = true
      try {
        if (editMode.value && editingAdmin.value) {
          const oldValue = {
            nickname: editingAdmin.value.nickname,
            display_name: editingAdmin.value.display_name
          }
          const newValue = {
            nickname: adminForm.nickname,
            display_name: adminForm.display_name
          }
          if (editingAdmin.value.role === 'super_admin') {
            await apiClient.updateSuperAdmin(editingAdmin.value.id, newValue)
          } else {
            await apiClient.updateOperator(editingAdmin.value.id, newValue)
          }
          ElMessage.success('更新成功')
          // 记录操作日志
          await logOperation({
            module: MODULE_USERS,
            action: 'update',
            description: `更新管理员：${editingAdmin.value.userid}`,
            table_name: 'operator',
            record_id: editingAdmin.value.id,
            old_value: oldValue,
            new_value: newValue
          })
        } else {
          const newAdmin = await apiClient.createOperator({
            nickname: adminForm.nickname,
            password: adminForm.password,
            display_name: adminForm.display_name
          })
          ElMessage.success('创建成功')
          // 记录操作日志
          await logOperation({
            module: MODULE_USERS,
            action: 'create',
            description: `创建管理员：${adminForm.nickname}`,
            table_name: 'operator',
            record_id: newAdmin?.id,
            new_value: {
              nickname: adminForm.nickname,
              display_name: adminForm.display_name,
              role: adminForm.role
            }
          })
        }
        showCreateDialog.value = false
        editMode.value = false
        editingAdmin.value = null
        adminFormRef.value?.resetFields()
        loadAdmins()
      } catch (error: any) {
        ElMessage.error(error.message || '操作失败')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const handleToggleStatus = async (row: User) => {
  const isDisabled = row.status === 'disabled'
  const action = isDisabled ? '启用' : '禁用'
  try {
    await ElMessageBox.confirm(`确定要${action}管理员 ${row.userid} 吗？`, '提示', {
      type: 'warning'
    })
    await apiClient.updateOperator(row.id, {
      status: isDisabled ? 'offline' : 'disabled'
    })
    ElMessage.success(`${action}成功`)
    // 记录操作日志
    await logOperation({
      module: MODULE_USERS,
      action: isDisabled ? 'enable' : 'disable',
      description: `${action}管理员：${row.userid}`,
      table_name: 'operator',
      record_id: row.id,
      old_value: { status: row.status },
      new_value: { status: isDisabled ? 'offline' : 'disabled' }
    })
    loadAdmins()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '操作失败')
    }
  }
}

const handleDelete = async (row: User) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除管理员 ${row.userid} 吗？此操作不可恢复！`,
      '警告',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )
    const oldValue = {
      nickname: row.nickname,
      display_name: row.display_name,
      userid: row.userid
    }
    await apiClient.deleteOperator(row.id)
    ElMessage.success('删除成功')
    // 记录操作日志
    await logOperation({
      module: MODULE_USERS,
      action: 'delete',
      description: `删除管理员：${row.userid}`,
      table_name: 'operator',
      record_id: row.id,
      old_value: oldValue
    })
    loadAdmins()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

onMounted(() => {
  loadAdmins()
})
</script>

<style lang="scss" scoped>
@import './users.scss';

.admin-users-view {
  padding: 0;
}

.toolbar {
  margin-bottom: 16px;
}

.gap-md {
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
  margin-bottom: 16px;
}

.mt-md {
  margin-top: 16px;
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
  font-size: $font-size-sm;
  white-space: nowrap;
}

.action-btns {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: nowrap;
  gap: 2px;
}
</style>
