<template>
  <el-dialog
    v-model="visible"
    :title="title"
    width="900px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="material-select-dialog">
      <el-row :gutter="20">
        <!-- 左侧标签分类 -->
        <el-col :span="6">
          <div class="category-panel card">
            <div class="panel-header flex-between">
              <span class="panel-title">标签分类</span>
            </div>
            <div class="tag-list">
              <div
                v-for="tag in tags"
                :key="tag.id"
                class="tag-item"
                :class="{ active: tagFilter === tag.id }"
                @click="handleTagClick(tag)"
              >
                <span class="tag-name">{{ tag.name }}</span>
                <span v-if="tag.material_count !== undefined" class="tag-count">({{ tag.material_count }})</span>
              </div>
            </div>
          </div>
        </el-col>

        <!-- 右侧素材列表 -->
        <el-col :span="18">
          <div class="selector-toolbar mb-md">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索素材标题"
              :prefix-icon="Search"
              style="width: 200px;"
              clearable
              @keyup.enter="handleSearch"
            />
            <el-select v-model="contentTypeFilter" placeholder="内容类型" clearable style="width: 120px;" @change="handleSearch">
              <el-option label="纯文本" value="text" />
              <el-option label="图文" value="image_text" />
              <el-option label="视频文字" value="video_text" />
              <el-option label="混合" value="mix" />
            </el-select>
            <el-select v-model="statusFilter" placeholder="状态" clearable style="width: 120px;" @change="handleSearch">
              <el-option label="可用" value="available" />
              <el-option label="禁用" value="disabled" />
            </el-select>
            <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
          </div>

          <el-table
            ref="tableRef"
            :data="materials"
            v-loading="loading"
            max-height="400px"
            @selection-change="handleSelectionChange"
            style="width: 100%;"
          >
            <el-table-column type="selection" width="50" />
            <el-table-column label="预览" width="100">
              <template #default="{ row }">
                <el-image
                  v-if="row.attachments && row.attachments.length > 0"
                  :src="row.attachments[0].thumbnail_url || row.attachments[0].file_url"
                  fit="cover"
                  style="width: 60px; height: 45px; border-radius: 4px;"
                />
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="标题" min-width="150" show-overflow-tooltip />
            <el-table-column prop="content_type" label="类型" width="90">
              <template #default="{ row }">
                <el-tag size="small">{{ getContentTypeLabel(row.content_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'available' ? 'success' : 'info'" size="small">
                  {{ row.status === 'available' ? '可用' : '禁用' }}
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
        </el-col>
      </el-row>
    </div>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :disabled="selectedMaterials.length === 0" @click="handleConfirm">确认选择</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { apiClient } from '@/api/types'
import type { Material, MaterialTag } from '@/api/types'

const props = defineProps<{
  modelValue: boolean
  isBenchmark?: boolean  // true=对标素材, false=创作素材
  currentMaterialIds?: number[]  // 当前已选中的素材ID（编辑时，支持多选）
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'select', materials: Material[]): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const title = computed(() => props.isBenchmark ? '选择对标素材' : '选择创作素材')

// 数据
const loading = ref(false)
const materials = ref<Material[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

// 筛选
const searchKeyword = ref('')
const contentTypeFilter = ref<string | undefined>(undefined)
const statusFilter = ref<string | undefined>(undefined)
const tagFilter = ref<number | undefined>(undefined)

// 选项数据
const tags = ref<MaterialTag[]>([])

// 选中状态
const selectedMaterials = ref<Material[]>([])
const tableRef = ref()

// 加载选项数据
const loadOptions = async () => {
  try {
    const tagRes = await apiClient.getMaterialTags()
    tags.value = tagRes || []
  } catch (error) {
    console.error('Failed to load material tags:', error)
  }
}

// 加载素材列表
const loadMaterials = async () => {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    
    if (searchKeyword.value) params.search = searchKeyword.value
    if (contentTypeFilter.value) params.content_type = contentTypeFilter.value
    if (statusFilter.value) params.status = statusFilter.value
    if (tagFilter.value) params.tag_id = tagFilter.value
    
    // 根据 isBenchmark 设置 library_type 参数
    if (props.isBenchmark) {
      params.library_type = 'benchmark'
      params.status = 'available'
    } else {
      params.library_type = 'creation'
    }
    
    const response = await apiClient.getMaterials(params)
    
    materials.value = response.items || []
    total.value = response.total || 0
    
    // 如果传入了 currentMaterialIds，预选中
    if (props.currentMaterialIds && props.currentMaterialIds.length > 0) {
      await nextTick()
      const preSelected = materials.value.filter(m => props.currentMaterialIds?.includes(m.id))
      preSelected.forEach(material => {
        tableRef.value?.toggleRowSelection(material, true)
      })
    }
  } catch (error) {
    console.error('Failed to load materials:', error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  loadMaterials()
}

// 页码变化
const handlePageChange = (page: number) => {
  currentPage.value = page
  loadMaterials()
}

// 标签点击
const handleTagClick = (tag: MaterialTag) => {
  if (tagFilter.value === tag.id) {
    tagFilter.value = undefined
  } else {
    tagFilter.value = tag.id
  }
  handleSearch()
}

// 选择变化
const handleSelectionChange = (selection: Material[]) => {
  selectedMaterials.value = selection
}

// 获取内容类型标签
const getContentTypeLabel = (type: string): string => {
  const map: Record<string, string> = {
    'text': '纯文本',
    'image_text': '图文',
    'video_text': '视频文字',
    'mix': '混合'
  }
  return map[type] || type
}

// 确认选择
const handleConfirm = () => {
  emit('select', selectedMaterials.value)
  handleClose()
}

// 关闭弹窗
const handleClose = () => {
  selectedMaterials.value = []
  visible.value = false
}

onMounted(() => {
  loadOptions()
  loadMaterials()
})
</script>

<style lang="scss" scoped>
.material-select-dialog {
  .category-panel {
    background: var(--bg-secondary);
    padding: 16px;
    border-radius: 8px;
    max-height: 500px;
    overflow-y: auto;
  }

  .panel-header {
    margin-bottom: 12px;
    
    .panel-title {
      font-weight: 600;
      color: var(--text-primary);
    }
  }

  .tag-list {
    .tag-item {
      padding: 8px 12px;
      cursor: pointer;
      border-radius: 6px;
      margin-bottom: 4px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      transition: all 0.2s;

      &:hover {
        background: var(--bg-hover);
      }

      &.active {
        background: var(--el-color-primary-light-9);
        color: var(--el-color-primary);
        font-weight: 500;
      }

      .tag-name {
        font-size: 14px;
      }

      .tag-count {
        font-size: 12px;
        color: var(--text-secondary);
      }
    }
  }

  .selector-toolbar {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .pagination-wrapper {
    display: flex;
    justify-content: flex-end;
  }
}
</style>
