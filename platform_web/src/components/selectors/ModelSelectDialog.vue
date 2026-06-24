<template>
  <el-dialog
    v-model="visible"
    title="选择模型"
    width="700px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="model-select-dialog">
      <div class="selector-toolbar mb-md">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索模型名称或平台"
          :prefix-icon="Search"
          style="width: 200px;"
          clearable
          @keyup.enter="handleSearch"
        />
        <el-select v-model="typeFilter" placeholder="模型类型" clearable style="width: 130px;" @change="handleSearch">
          <el-option label="全部" value="" />
          <el-option label="文本模型" value="llm" />
          <el-option label="图片模型" value="image" />
        </el-select>
        <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
      </div>

      <el-table
        ref="tableRef"
        :data="models"
        v-loading="loading"
        highlight-current-row
        @row-click="handleRowClick"
        max-height="400px"
        style="width: 100%;"
      >
        <el-table-column prop="platform" label="平台" width="120" />
        <el-table-column prop="model_name" label="模型名称" min-width="150" />
        <el-table-column prop="model_id" label="模型ID" min-width="150" show-overflow-tooltip />
        <el-table-column prop="type" label="类型" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.type === 'llm' ? '' : 'warning'">
              {{ row.type === 'llm' ? '文本' : '图片' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_default" label="默认" width="70">
          <template #default="{ row }">
            <el-icon v-if="row.is_default" color="#67C23A"><Check /></el-icon>
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
    </div>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :disabled="!selectedModel" @click="handleConfirm">确认选择</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Search, Check } from '@element-plus/icons-vue'
import { apiClient } from '@/api/types'
import type { ModelConfig } from '@/api/types'

const props = defineProps<{
  modelValue: boolean
  modelType?: 'llm' | 'image'  // 限制模型类型
  currentModelId?: number  // 当前已选中的模型ID（编辑时）
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'select', model: ModelConfig): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 数据
const loading = ref(false)
const models = ref<ModelConfig[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

// 筛选
const searchKeyword = ref('')
const typeFilter = ref<string>('')

// 选中状态
const selectedModel = ref<ModelConfig | null>(null)
const tableRef = ref()

// 加载模型列表
const loadModels = async () => {
  loading.value = true
  try {
    const params: any = {}
    
    if (searchKeyword.value) params.search = searchKeyword.value
    if (props.modelType) params.type = props.modelType
    if (typeFilter.value) params.type = typeFilter.value
    
    const modelsData = await apiClient.getModelConfigs()
    // getModelConfigs 返回的是 ModelConfig[] 数组
    let filteredModels = modelsData || []
    
    // 前端搜索过滤
    if (searchKeyword.value) {
      const keyword = searchKeyword.value.toLowerCase()
      filteredModels = filteredModels.filter(m => 
        m.model_name?.toLowerCase().includes(keyword) || 
        m.platform?.toLowerCase().includes(keyword)
      )
    }
    
    // 前端类型过滤
    if (props.modelType) {
      filteredModels = filteredModels.filter((m: any) => m.model_type === props.modelType)
    }
    if (typeFilter.value) {
      filteredModels = filteredModels.filter((m: any) => m.model_type === typeFilter.value)
    }
    
    // 简单分页
    total.value = filteredModels.length
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    models.value = filteredModels.slice(start, end)
    
    // 如果传入了 currentModelId，预选中
    if (props.currentModelId) {
      const preSelected = modelsData.find((m: any) => m.id === props.currentModelId)
      if (preSelected) {
        selectedModel.value = preSelected
        await nextTick()
        tableRef.value?.setCurrentRow(preSelected)
      }
    }
  } catch (error) {
    console.error('Failed to load models:', error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  loadModels()
}

// 页码变化
const handlePageChange = (page: number) => {
  currentPage.value = page
  loadModels()
}

// 行点击
const handleRowClick = (row: ModelConfig) => {
  selectedModel.value = row
}

// 确认选择
const handleConfirm = () => {
  if (selectedModel.value) {
    emit('select', selectedModel.value)
    handleClose()
  }
}

// 关闭弹窗
const handleClose = () => {
  selectedModel.value = null
  visible.value = false
}

onMounted(() => {
  loadModels()
})
</script>

<style lang="scss" scoped>
.model-select-dialog {
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
