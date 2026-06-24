<template>
  <div class="sub-users-view">
    <h2 class="page-title">创作员管理</h2>

    <el-row :gutter="20">
      <el-col :span="4">
        <div class="card category-panel">
          <div class="panel-header flex-between">
            <span class="panel-title">
              {{ isSuperAdmin ? '创作管理员' : '用户标签' }}
            </span>
            <el-button
              v-if="!isSuperAdmin"
              type="primary"
              link
              size="small"
              @click="showTagDialog = true"
            >
              <el-icon><Plus /></el-icon>
              添加
            </el-button>
          </div>
          <div class="category-list">
            <!-- 超级管理员：显示创作管理员列表 -->
            <template v-if="isSuperAdmin">
              <div
                class="category-item"
                :class="{ active: selectedOperatorId === null }"
                @click="handleOperatorClick(null)"
              >
                <span class="category-name">
                  全部创作管理员
                  <span class="category-count">({{ globalAllUsersTotal }})</span>
                </span>
              </div>
              <div
                v-for="operator in operatorList"
                :key="operator.id"
                class="category-item"
                :class="{ active: selectedOperatorId === operator.id }"
                @click="handleOperatorClick(operator)"
              >
                <span class="category-name">
                  {{ operator.nickname }}
                  <span class="category-count">({{ operatorUserCounts[operator.id] || 0 }})</span>
                </span>
              </div>
            </template>

            <!-- 创作管理员：显示标签列表 -->
            <template v-else>
              <div
                class="category-item"
                :class="{ active: selectedTagId === null }"
                @click="handleTagClick(null)"
              >
                <span class="category-name">
                  全部
                  <span class="category-count">({{ allUsersTotal }})</span>
                </span>
              </div>
              <div
                v-for="tag in userTags"
                :key="tag.id"
                class="category-item"
                :class="{ active: selectedTagId === tag.id }"
                @click="handleTagClick(tag)"
              >
                <span class="category-name">
                  {{ tag.name }}
                  <span class="category-count">({{ tagCounts[tag.id] || 0 }})</span>
                </span>
                <el-icon
                  class="delete-icon"
                  @click.stop="handleDeleteTag(tag)"
                >
                  <Delete />
                </el-icon>
              </div>
            </template>
          </div>
        </div>
      </el-col>

      <el-col :span="20">
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
              <template v-if="isSuperAdmin">
                <el-button type="warning" :disabled="selectedUsers.length === 0" @click="showTransferDialog = true">
                  批量转移
                </el-button>
              </template>
              <template v-else>
                <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
                  创建用户
                </el-button>
                <el-button type="danger" :icon="Delete" :disabled="selectedUsers.length === 0" @click="handleBatchDelete">
                  批量删除
                </el-button>
              </template>
            </div>
          </div>

          <el-table :data="userList" style="width: 100%" @selection-change="handleSelectionChange" v-loading="loading">
            <el-table-column type="selection" width="55" />
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="userid" label="用户名" width="120" />
            <el-table-column prop="nickname" label="备注名" width="120" />
            <el-table-column prop="display_name" label="自定义昵称" width="120" />
            <!-- 超级管理员显示所属创作管理员 -->
            <el-table-column v-if="isSuperAdmin" label="所属管理员" width="120">
              <template #default="{ row }">
                {{ operatorMap[(row as any).owner_operator_id]?.nickname || '-' }}
              </template>
            </el-table-column>
            <!-- 显示标签名称 -->
            <el-table-column label="标签" width="160">
              <template #default="{ row }">
                <el-tag
                  v-for="tag in (row as any).tags"
                  :key="tag.id"
                  size="small"
                  :style="getTagStyle(tag.color)"
                  style="margin-right: 4px; margin-bottom: 4px;"
                >
                  {{ tag.name }}
                </el-tag>
                <span v-if="!(row as any).tags?.length" style="color: #909399;">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
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
            <el-table-column label="操作" min-width="280" fixed="right" align="left">
              <template #default="{ row }">
                <div class="action-btns">
                  <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
                  <el-button v-if="!isSuperAdmin" type="warning" link size="small" @click="handleResetPassword(row)">重置密码</el-button>
                  <el-button :type="row.status === 'disabled' ? 'success' : 'danger'" link size="small" @click="handleToggleStatus(row)">
                    {{ row.status === 'disabled' ? '启用' : '禁用' }}
                  </el-button>
                  <el-button v-if="!isSuperAdmin" type="danger" link size="small" @click="handleDeleteUser(row)">删除</el-button>
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
              @current-change="loadUsers"
              @size-change="loadUsers"
            />
          </div>
        </div>
      </el-col>
    </el-row>

    <el-dialog v-model="showCreateDialog" title="创建用户" width="600px">
      <el-form :model="userForm" :rules="userRules" ref="userFormRef" label-width="100px">
        <el-form-item label="备注名" prop="nickname">
          <el-input v-model="userForm.nickname" placeholder="请输入备注名（昵称）" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="userForm.password" type="password" placeholder="留空则自动生成" show-password />
        </el-form-item>
        <el-form-item label="用户标签" prop="tag_ids">
          <el-select v-model="userForm.tag_ids" multiple placeholder="请选择标签（用于分类管理，可多选）" style="width: 100%;">
            <el-option
              v-for="tag in userTags"
              :key="tag.id"
              :label="tag.name"
              :value="tag.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="粉丝画像" prop="fan_profile">
          <el-input
            v-model="userForm.fan_profile"
            type="textarea"
            :rows="3"
            placeholder="请输入粉丝画像描述（可选）"
          />
          <div class="form-tip">
            <strong>要点</strong>：粉丝年龄（如：22-35岁）、职业（如：职场白领、自媒体创作者、学生）、地域（如：一线/新一线城市）、偏好等
          </div>
        </el-form-item>
        <el-form-item label="账号定位" prop="user_positioning">
          <el-input
            v-model="userForm.user_positioning"
            type="textarea"
            :rows="3"
            placeholder="请输入账号定位描述（可选）"
          />
          <div class="form-tip">
            <strong>要点</strong>：核心赛道（职场、美妆、科普、美食、育儿、穿搭等）、核心价值（实用技巧、干货攻略、避坑指南、高效创作与低成本变现思路）、目标受众匹配（面向各领域新手、从业者及爱好者）、账号层级（入门实操、进阶提升、高阶操盘）。
          </div>
        </el-form-item>
        <el-form-item label="内容风格" prop="content_style">
          <el-input
            v-model="userForm.content_style"
            type="textarea"
            :rows="3"
            placeholder="请输入内容风格描述（可选）"
          />
          <div class="form-tip">
            <strong>要点</strong>：文案语气（如：口语化接地气、专业严谨、活泼俏皮、温和干货向）、排版逻辑（如：开头痛点吸睛→中间步骤/干货→结尾引导互动/关注）、核心调性（如：纯干货向、种草向、避坑向、案例拆解向）
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateUser" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showTagDialog" title="新增标签" width="400px">
      <el-form label-width="100px">
        <el-form-item label="标签名称">
          <el-input v-model="newTagName" placeholder="请输入标签名称" />
        </el-form-item>
        <el-form-item label="标签颜色">
          <el-color-picker v-model="newTagColor" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTagDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddTag" :loading="tagSubmitLoading">添加</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showEditDialog" title="编辑用户" width="600px">
      <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="100px">
        <el-form-item label="备注名" prop="nickname">
          <el-input v-model="editForm.nickname" placeholder="请输入备注名（昵称）" />
        </el-form-item>
        <el-form-item label="自定义昵称">
          <el-input v-model="editForm.display_name" placeholder="请输入自定义昵称" disabled />
        </el-form-item>
        <el-form-item label="用户标签" prop="tag_ids">
          <el-select v-model="editForm.tag_ids" multiple placeholder="请选择标签（用于分类管理，可多选）" style="width: 100%;">
            <el-option
              v-for="tag in (isSuperAdmin ? currentOperatorTags : userTags)"
              :key="tag.id"
              :label="tag.name"
              :value="tag.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="粉丝画像" prop="fan_profile">
          <el-input
            v-model="editForm.fan_profile"
            type="textarea"
            :rows="3"
            placeholder="请输入粉丝画像描述（可选）"
          />
          <div class="form-tip">
            <strong>要点</strong>：粉丝年龄（如：22-35岁）、职业（如：职场白领、自媒体创作者、学生）、地域（如：一线/新一线城市）、偏好等
          </div>
        </el-form-item>
        <el-form-item label="账号定位" prop="user_positioning">
          <el-input
            v-model="editForm.user_positioning"
            type="textarea"
            :rows="3"
            placeholder="请输入账号定位描述（可选）"
          />
          <div class="form-tip">
            <strong>要点</strong>：核心赛道（职场、美妆、科普、美食、育儿、穿搭等）、核心价值（实用技巧、干货攻略、避坑指南、高效创作与低成本变现思路）、目标受众匹配（面向各领域新手、从业者及爱好者）、账号层级（入门实操、进阶提升、高阶操盘）。
          </div>
        </el-form-item>
        <el-form-item label="内容风格" prop="content_style">
          <el-input
            v-model="editForm.content_style"
            type="textarea"
            :rows="3"
            placeholder="请输入内容风格描述（可选）"
          />
          <div class="form-tip">
            <strong>要点</strong>：文案语气（如：口语化接地气、专业严谨、活泼俏皮、温和干货向）、排版逻辑（如：开头痛点吸睛→中间步骤/干货→结尾引导互动/关注）、核心调性（如：纯干货向、种草向、避坑向、案例拆解向）
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpdateUser" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 批量转移对话框 -->
    <el-dialog v-model="showTransferDialog" title="批量转移用户" width="500px">
      <el-form label-width="120px">
        <el-form-item label="已选择用户">
          <div style="color: #606266;">
            共 {{ selectedUsers.length }} 个用户
          </div>
        </el-form-item>
        <el-form-item label="目标创作管理员" required>
          <el-select
            v-model="transferTargetOperatorId"
            placeholder="请选择目标创作管理员"
            style="width: 100%;"
          >
            <el-option
              v-for="operator in operatorList"
              :key="operator.id"
              :label="operator.nickname"
              :value="operator.id"
              :disabled="selectedUsers.some(u => (u as any).owner_operator_id === operator.id)"
            />
          </el-select>
          <div style="color: #909399; font-size: 12px; margin-top: 4px;">
            注意：用户的标签将在目标创作管理员下自动创建
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTransferDialog = false">取消</el-button>
        <el-button
          type="primary"
          :disabled="!transferTargetOperatorId"
          @click="handleBatchTransfer"
          :loading="submitLoading"
        >
          确定转移
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { Search, Plus, Delete } from '@element-plus/icons-vue'
import { apiClient, type User, type UserTag, type OperationLogCreateParams } from '@/api/types'
import { useAuthStore } from '@/stores/auth'

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

const authStore = useAuthStore()
const isSuperAdmin = computed(() => authStore.userRole === 'super_admin')

const searchKeyword = ref('')
const searchStatus = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const allUsersTotal = ref(0) // 全部用户数量（不受筛选影响）
const globalAllUsersTotal = ref(0) // 全局全部用户数量（超级管理员用，不受创作管理员筛选影响）
const loading = ref(false)
const submitLoading = ref(false)
const tagSubmitLoading = ref(false)
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showTagDialog = ref(false)
const showTransferDialog = ref(false)
const transferTargetOperatorId = ref<number | null>(null)
const newTagName = ref('')
const newTagColor = ref('#8B7CF6')
const selectedTagId = ref<number | null>(null)
const selectedOperatorId = ref<number | null>(null)
const selectedUsers = ref<User[]>([])
const userFormRef = ref<FormInstance>()
const editFormRef = ref<FormInstance>()
const editingUser = ref<User | null>(null)
const tagCounts = ref<Record<number, number>>({})
const operatorUserCounts = ref<Record<number, number>>({})

const userForm = reactive({
  password: '',
  nickname: '',
  fan_profile: '',
  user_positioning: '',
  user_category: '',
  content_style: '',
  tag_ids: [] as number[]
})

const userRules = {
  nickname: [{ required: true, message: '请输入备注名', trigger: 'blur' }]
}

const editForm = reactive({
  nickname: '',
  display_name: '',
  fan_profile: '',
  user_positioning: '',
  content_style: '',
  tag_ids: [] as number[]
})

const editRules = {
  nickname: [{ required: true, message: '请输入备注名', trigger: 'blur' }]
}

const userTags = ref<UserTag[]>([])
const operatorList = ref<User[]>([])
const operatorMap = ref<Record<number, User>>({})
const currentOperatorTags = ref<UserTag[]>([])
const userList = ref<User[]>([])

const loadOperators = async () => {
  try {
    const result = await apiClient.getOperators({ limit: 100 })
    operatorList.value = result?.items || []
    operatorMap.value = {}
    operatorList.value.forEach(op => {
      operatorMap.value[op.id] = op
    })
  } catch (error: any) {
    console.error('加载创作管理员失败:', error)
  }
}

const loadTags = async () => {
  try {
    const params: any = { tag_type: 'subuser_tag' }

    // 超级管理员：如果选中了创作管理员，加载该创作管理员的标签
    if (isSuperAdmin.value && selectedOperatorId.value) {
      params.operator_id = selectedOperatorId.value
    }

    const [tags, counts] = await Promise.all([
      apiClient.getUserTags(params),
      apiClient.getTagCounts(isSuperAdmin.value && selectedOperatorId.value ? { operator_id: selectedOperatorId.value } : undefined)
    ])
    userTags.value = tags || []
    tagCounts.value = counts || {}

    // 如果是超级管理员且选中了创作管理员，保存该创作管理员的标签供编辑使用
    if (isSuperAdmin.value && selectedOperatorId.value) {
      currentOperatorTags.value = tags || []
    }
  } catch (error: any) {
    console.error('加载标签失败:', error)
  }
}

const loadOperatorUserCounts = async () => {
  if (!isSuperAdmin.value) return

  try {
    // 获取所有创作管理员的创作者数量统计
    const counts: Record<number, number> = {}
    for (const operator of operatorList.value) {
      const result = await apiClient.getSubUsers({ operator_id: operator.id, page: 1, limit: 1 })
      counts[operator.id] = result?.total || 0
    }
    operatorUserCounts.value = counts
  } catch (error: any) {
    console.error('加载创作管理员用户统计失败:', error)
  }
}

const loadUsers = async () => {
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

    // 超级管理员：使用 selectedOperatorId
    if (isSuperAdmin.value) {
      if (selectedOperatorId.value) {
        params.operator_id = selectedOperatorId.value
      }
      // tag_id 由前端筛选处理，或者在选中创作管理员时使用
      if (selectedTagId.value && selectedOperatorId.value) {
        params.tag_id = selectedTagId.value
      }
    } else {
      // 创作管理员：使用 selectedTagId
      if (selectedTagId.value) {
        params.tag_id = selectedTagId.value
      }
    }

    // 同时获取筛选后的用户列表和全部用户数量
    const allParams: any = { page: 1, limit: 1 }
    if (isSuperAdmin.value && selectedOperatorId.value) {
      allParams.operator_id = selectedOperatorId.value
    }

    // 超级管理员还需要获取全局全部用户数量（不受创作管理员筛选影响）
    const globalAllParams: any = { page: 1, limit: 1 }

    const promises: Promise<any>[] = [
      apiClient.getSubUsers(params),
      apiClient.getSubUsers(allParams)
    ]
    if (isSuperAdmin.value) {
      promises.push(apiClient.getSubUsers(globalAllParams))
    }

    const [filteredResult, allUsersResult, globalAllUsersResult] = await Promise.all(promises)

    userList.value = filteredResult?.items || []
    total.value = filteredResult?.total || 0
    allUsersTotal.value = allUsersResult?.total || 0
    if (isSuperAdmin.value && globalAllUsersResult) {
      globalAllUsersTotal.value = globalAllUsersResult?.total || 0
    }
  } catch (error: any) {
    ElMessage.error(error.message || '加载失败')
  } finally {
    loading.value = false
  }
}

const handleTagClick = (tag: UserTag | null) => {
  selectedTagId.value = tag?.id || null
  currentPage.value = 1
  loadUsers()
}

const handleOperatorClick = (operator: User | null) => {
  selectedOperatorId.value = operator?.id || null
  selectedTagId.value = null
  currentPage.value = 1
  // 重新加载标签和用户
  Promise.all([loadTags(), loadUsers()])
}

const handleSearch = () => {
  currentPage.value = 1
  loadUsers()
}

const handleSelectionChange = (selection: User[]) => {
  selectedUsers.value = selection
}

const handleEdit = (row: User) => {
  editingUser.value = row

  // 如果是超级管理员，需要先加载该创作者所属创作管理员的标签
  if (isSuperAdmin.value && (row as any).owner_operator_id) {
    apiClient.getUserTags({ tag_type: 'subuser_tag', operator_id: (row as any).owner_operator_id })
      .then(tags => {
        currentOperatorTags.value = tags || []
      })
  }

  Object.assign(editForm, {
    nickname: row.nickname,
    display_name: row.display_name || '',
    fan_profile: row.fan_profile || '',
    user_positioning: row.user_positioning || '',
    content_style: row.content_style || '',
    tag_ids: (row as any).tags?.map((t: any) => t.id) || []
  })
  showEditDialog.value = true
}

const handleUpdateUser = async () => {
  if (!editFormRef.value || !editingUser.value) return
  const userId = editingUser.value.id
  const oldValue = {
    nickname: editingUser.value.nickname,
    display_name: editingUser.value.display_name,
    fan_profile: editingUser.value.fan_profile,
    user_positioning: editingUser.value.user_positioning,
    content_style: editingUser.value.content_style
  }
  await editFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      submitLoading.value = true
      try {
        const newValue = {
          nickname: editForm.nickname,
          display_name: editForm.display_name,
          fan_profile: editForm.fan_profile,
          user_positioning: editForm.user_positioning,
          content_style: editForm.content_style,
          tag_ids: editForm.tag_ids
        }
        await apiClient.updateSubUser(userId, newValue)
        ElMessage.success('更新成功')
        // 记录操作日志
        await logOperation({
          module: MODULE_USERS,
          action: 'update',
          description: `更新创作者：${editForm.nickname}`,
          table_name: 'sub_user',
          record_id: userId,
          old_value: oldValue,
          new_value: newValue
        })
        showEditDialog.value = false
        editFormRef.value?.resetFields()
        await Promise.all([loadUsers(), loadTags()])
      } catch (error: any) {
        ElMessage.error(error.message || '更新失败')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const handleResetPassword = async (row: User) => {
  try {
    await ElMessageBox.confirm(`确定要重置用户 ${row.nickname} 的密码吗？`, '提示', {
      type: 'warning'
    })
    // 生成随机密码
    const newPassword = Math.random().toString(36).slice(-8)
    await apiClient.resetSubUserPassword(row.id, newPassword)
    ElMessage.success(`密码已重置为: ${newPassword}`)
    // 记录操作日志
    await logOperation({
      module: MODULE_USERS,
      action: 'update',
      description: `重置创作者密码：${row.nickname}`,
      table_name: 'sub_user',
      record_id: row.id,
      extra_data: { action_type: 'reset_password' }
    })
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '重置密码失败')
    }
  }
}

const handleToggleStatus = async (row: User) => {
  const isDisabled = row.status === 'disabled'
  const action = isDisabled ? '启用' : '禁用'
  try {
    await ElMessageBox.confirm(`确定要${action}用户 ${row.nickname} 吗？`, '提示', {
      type: 'warning'
    })
    await apiClient.updateSubUser(row.id, {
      status: isDisabled ? 'offline' : 'disabled'
    })
    ElMessage.success(`${action}成功`)
    // 记录操作日志
    await logOperation({
      module: MODULE_USERS,
      action: isDisabled ? 'enable' : 'disable',
      description: `${action}创作者：${row.nickname}`,
      table_name: 'sub_user',
      record_id: row.id,
      old_value: { status: row.status },
      new_value: { status: isDisabled ? 'offline' : 'disabled' }
    })
    loadUsers()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '操作失败')
    }
  }
}

const handleDeleteUser = async (row: User) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 ${row.nickname} 吗？此操作不可恢复！`,
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
    await apiClient.deleteSubUser(row.id)
    ElMessage.success('删除成功')
    // 记录操作日志
    await logOperation({
      module: MODULE_USERS,
      action: 'delete',
      description: `删除创作者：${row.nickname}`,
      table_name: 'sub_user',
      record_id: row.id,
      old_value: oldValue
    })
    loadUsers()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedUsers.value.length} 个用户吗？此操作不可恢复！`,
      '警告',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )
    // 记录批量删除前的用户信息
    const deletedUsers = selectedUsers.value.map(u => ({
      id: u.id,
      nickname: u.nickname,
      display_name: u.display_name,
      userid: u.userid
    }))
    // 逐个删除
    for (const user of selectedUsers.value) {
      await apiClient.deleteSubUser(user.id)
    }
    ElMessage.success('批量删除成功')
    // 记录操作日志
    await logOperation({
      module: MODULE_USERS,
      action: 'delete',
      description: `批量删除创作者：${deletedUsers.length}个用户`,
      table_name: 'sub_user',
      extra_data: { deleted_users: deletedUsers }
    })
    loadUsers()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '批量删除失败')
    }
  }
}

const handleCreateUser = async () => {
  if (!userFormRef.value) return
  await userFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      submitLoading.value = true
      try {
        const newUser = await apiClient.createSubUser({
          nickname: userForm.nickname,
          password: userForm.password || undefined,
          fan_profile: userForm.fan_profile,
          user_positioning: userForm.user_positioning,
          user_category: userForm.user_category,
          content_style: userForm.content_style,
          tag_ids: userForm.tag_ids
        })
        ElMessage.success('创建成功')
        // 记录操作日志
        await logOperation({
          module: MODULE_USERS,
          action: 'create',
          description: `创建创作者：${userForm.nickname}`,
          table_name: 'sub_user',
          record_id: newUser?.id,
          new_value: {
            nickname: userForm.nickname,
            fan_profile: userForm.fan_profile,
            user_positioning: userForm.user_positioning,
            content_style: userForm.content_style,
            tag_ids: userForm.tag_ids
          }
        })
        showCreateDialog.value = false
        userFormRef.value?.resetFields()
        await Promise.all([loadUsers(), loadTags()])
      } catch (error: any) {
        ElMessage.error(error.message || '创建失败')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const handleAddTag = async () => {
  if (!newTagName.value) {
    ElMessage.warning('请输入标签名称')
    return
  }
  tagSubmitLoading.value = true
  try {
    const newTag = await apiClient.createUserTag({
      name: newTagName.value,
      tag_type: 'subuser_tag',
      color: newTagColor.value
    })
    newTagName.value = ''
    newTagColor.value = '#8B7CF6'
    ElMessage.success('标签添加成功')
    // 记录操作日志
    await logOperation({
      module: MODULE_USERS,
      action: 'create',
      description: `添加创作者标签：${newTag?.name || newTagName.value}`,
      table_name: 'user_tag',
      record_id: newTag?.id,
      new_value: {
        name: newTagName.value,
        tag_type: 'subuser_tag',
        color: newTagColor.value
      }
    })
    showTagDialog.value = false
    loadTags()
  } catch (error: any) {
    ElMessage.error(error.message || '添加标签失败')
  } finally {
    tagSubmitLoading.value = false
  }
}

const handleDeleteTag = async (tag: UserTag) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除标签 ${tag.name} 吗？`,
      '提示',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )
    await apiClient.deleteUserTag(tag.id)
    ElMessage.success('标签删除成功')
    // 记录操作日志
    await logOperation({
      module: MODULE_USERS,
      action: 'delete',
      description: `删除创作者标签：${tag.name}`,
      table_name: 'user_tag',
      record_id: tag.id,
      old_value: { name: tag.name, color: tag.color }
    })
    if (selectedTagId.value === tag.id) {
      selectedTagId.value = null
    }
    loadTags()
    loadUsers()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除标签失败')
    }
  }
}

const handleBatchTransfer = async () => {
  if (!transferTargetOperatorId.value) {
    ElMessage.warning('请选择目标创作管理员')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要将选中的 ${selectedUsers.value.length} 个用户转移到 ${operatorMap.value[transferTargetOperatorId.value]?.nickname} 吗？`,
      '提示',
      {
        type: 'warning',
        confirmButtonText: '确定转移',
        cancelButtonText: '取消'
      }
    )

    submitLoading.value = true

    // 记录转移前的用户信息
    const transferredUsers = selectedUsers.value.map(u => ({
      id: u.id,
      nickname: u.nickname,
      from_operator_id: (u as any).owner_operator_id
    }))

    // 按来源创作管理员分组
    const userGroups: Record<number, number[]> = {}
    for (const user of selectedUsers.value) {
      const fromOperatorId = (user as any).owner_operator_id
      if (!userGroups[fromOperatorId]) {
        userGroups[fromOperatorId] = []
      }
      userGroups[fromOperatorId].push(user.id)
    }

    // 逐个分组转移
    for (const [fromOperatorId, userIds] of Object.entries(userGroups)) {
      await apiClient.transferSubUsers(
        userIds,
        parseInt(fromOperatorId),
        transferTargetOperatorId.value
      )
    }

    ElMessage.success('转移成功')
    // 记录操作日志
    await logOperation({
      module: MODULE_USERS,
      action: 'transfer',
      description: `批量转移创作者：${transferredUsers.length}个用户转移至${operatorMap.value[transferTargetOperatorId.value]?.nickname}`,
      table_name: 'sub_user',
      extra_data: {
        transferred_users: transferredUsers,
        target_operator_id: transferTargetOperatorId.value,
        target_operator_name: operatorMap.value[transferTargetOperatorId.value]?.nickname
      }
    })
    showTransferDialog.value = false
    transferTargetOperatorId.value = null
    selectedUsers.value = []
    loadUsers()
    loadOperatorUserCounts()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '转移失败')
    }
  } finally {
    submitLoading.value = false
  }
}

/**
 * 计算标签样式，确保文字颜色与背景色对比度足够
 */
const getTagStyle = (color: string | undefined) => {
  if (!color) {
    return {
      backgroundColor: '#8B7CF6',
      color: '#ffffff'
    }
  }

  // 移除 # 前缀（如果有）
  let hex = color.replace('#', '')

  // 处理短格式颜色（3位）
  if (hex.length === 3) {
    hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2]
  }

  // 解析RGB值
  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)

  // 计算相对亮度（使用W3C公式）
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255

  // 根据亮度选择文字颜色（亮度>0.5使用深色，否则使用白色）
  const textColor = luminance > 0.5 ? '#303133' : '#ffffff'

  return {
    backgroundColor: color,
    color: textColor,
    borderColor: color
  }
}

onMounted(() => {
  if (isSuperAdmin.value) {
    Promise.all([loadOperators(), loadTags(), loadUsers()]).then(() => {
      loadOperatorUserCounts()
    })
  } else {
    Promise.all([loadTags(), loadUsers()])
  }
})
</script>

<style lang="scss" scoped>
@import './users.scss';

.sub-users-view {
  padding: 0;
}

.category-panel {
  // 样式已在 users.scss 中统一定义
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

.form-tip {
  margin-top: $spacing-sm;
  font-size: $font-size-xs;
  color: var(--color-text-secondary);
  line-height: 1.5;

  strong {
    color: var(--color-primary);
  }
}

.action-btns {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  flex-wrap: nowrap;
  gap: 8px;
  white-space: nowrap;

  .el-button {
    white-space: nowrap;
  }
}
</style>
