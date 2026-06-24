<template>
  <el-dialog
    v-model="visible"
    title="选择创作者"
    width="700px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="sub-user-select-dialog">
      <div class="selector-toolbar mb-md">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索创作者名称"
          :prefix-icon="Search"
          style="width: 200px;"
          clearable
          @keyup.enter="handleSearch"
        />
        <el-select v-model="tagFilter" placeholder="标签筛选" clearable style="width: 130px;" @change="handleSearch">
          <el-option label="全部标签" value="" />
          <el-option v-for="tag in tags" :key="tag.id" :label="tag.name" :value="tag.id" />
        </el-select>
        <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
      </div>

      <el-table
        ref="tableRef"
        :data="users"
        v-loading="loading"
        max-height="400px"
        @selection-change="handleSelectionChange"
        style="width: 100%;"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="nickname" label="用户名称" min-width="120" />
        <el-table-column prop="display_name" label="显示名称" min-width="120" />
        <el-table-column prop="account_positioning" label="账号定位" min-width="150" show-overflow-tooltip />
        <el-table-column prop="content_style" label="内容风格" min-width="120" />
        <el-table-column label="标签" min-width="150">
          <template #default="{ row }">
            <el-tag v-for="tag in parseTags(row.tags)" :key="tag" size="small" class="mr-xs">
              {{ tag }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper mt-md">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSearch"
          @current-change="handlePageChange"
        />
      </div>

      <div v-if="selectedUsers.length > 0" class="selected-preview mt-md">
        <el-alert type="info" :closable="false">
          <template #default>
            已选择 <strong>{{ selectedUsers.length }}</strong> 个创作者
          </template>
        </el-alert>
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :disabled="selectedUsers.length === 0" @click="handleConfirm">确认选择</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { apiClient } from '@/api/types'
import type { SubUser, UserTag } from '@/api/types'

const props = defineProps<{
  modelValue: boolean
  currentUserIds?: number[]  // 当前已选中的用户ID（编辑时）
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'select', users: SubUser[]): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 数据
const loading = ref(false)
const users = ref<SubUser[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

// 筛选
const searchKeyword = ref('')
const tagFilter = ref<number | undefined>(undefined)
const tags = ref<UserTag[]>([])

// 选中状态
const selectedUsers = ref<SubUser[]>([])
const tableRef = ref()

// 加载标签
const loadTags = async () => {
  try {
    const response = await apiClient.getTags()
    tags.value = response.data || []
  } catch (error) {
    console.error('Failed to load tags:', error)
  }
}

// 加载用户列表
const loadUsers = async () => {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    
    if (searchKeyword.value) params.search = searchKeyword.value
    if (tagFilter.value) params.tag_id = tagFilter.value
    
    const response = await apiClient.getSubUsers(params)
    users.value = response.items || []
    total.value = response.total || 0
    
    // 如果传入了 currentUserIds，预选中
    if (props.currentUserIds && props.currentUserIds.length > 0) {
      await nextTick()
      const preSelected = users.value.filter(u => props.currentUserIds?.includes(u.id))
      preSelected.forEach(user => {
        tableRef.value?.toggleRowSelection(user, true)
      })
    }
  } catch (error) {
    console.error('Failed to load users:', error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  loadUsers()
}

// 页码变化
const handlePageChange = (page: number) => {
  currentPage.value = page
  loadUsers()
}

// 选择变化
const handleSelectionChange = (selection: SubUser[]) => {
  selectedUsers.value = selection
}

// 解析标签
const parseTags = (tags: any): string[] => {
  if (!tags) return []
  if (Array.isArray(tags)) return tags.map(t => typeof t === 'string' ? t : t.name)
  return []
}

// 确认选择
const handleConfirm = () => {
  emit('select', selectedUsers.value)
  handleClose()
}

// 关闭弹窗
const handleClose = () => {
  selectedUsers.value = []
  visible.value = false
}

onMounted(() => {
  loadTags()
  loadUsers()
})
</script>

<style lang="scss" scoped>
.sub-user-select-dialog {
  .selector-toolbar {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .pagination-wrapper {
    display: flex;
    justify-content: flex-end;
  }

  .selected-preview {
    .el-alert {
      background: var(--bg-tertiary);
    }
  }
}
</style>
