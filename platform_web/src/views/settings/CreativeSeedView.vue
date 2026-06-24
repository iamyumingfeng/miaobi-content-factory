<template>
  <div class="creative-seed-view">
    <h2 class="page-title">创意种子库管理</h2>

    <div class="card">
      <!-- 类型筛选 Tab -->
      <el-tabs v-model="activeType" @tab-change="loadSeeds" class="mb-md">
        <el-tab-pane label="全部" name="" />
        <el-tab-pane label="开头模式" name="opening" />
        <el-tab-pane label="情感基调" name="emotion" />
        <el-tab-pane label="结尾模式" name="ending" />
      </el-tabs>

      <!-- 工具栏 -->
      <div class="toolbar flex-between mb-md">
        <div class="toolbar-left flex gap-md">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索种子名称/模板"
            :prefix-icon="Search"
            clearable
            style="width: 240px;"
            @clear="loadSeeds"
            @keyup.enter="loadSeeds"
          />
          <el-select v-model="filterCategory" placeholder="品类筛选" clearable style="width: 120px;" @change="loadSeeds">
            <el-option label="全部" value="" />
            <el-option v-for="c in categoryOptions" :key="c" :label="c" :value="c" />
          </el-select>
          <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 120px;" @change="loadSeeds">
            <el-option label="全部" value="" />
            <el-option label="启用" value="enabled" />
            <el-option label="禁用" value="disabled" />
          </el-select>
          <el-button type="primary" :icon="Search" @click="loadSeeds">搜索</el-button>
        </div>
        <div class="toolbar-right">
          <el-button type="primary" :icon="Plus" @click="handleAdd">
            新建种子
          </el-button>
        </div>
      </div>

      <!-- 表格 -->
      <el-table :data="seeds" v-loading="loading" stripe style="width: 100%;">
        <el-table-column prop="name" label="种子名称" min-width="120" />
        <el-table-column prop="seed_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.seed_type)" size="small">
              {{ getTypeLabel(row.seed_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="template" label="模板示例" min-width="250">
          <template #default="{ row }">
            <div class="template-cell" v-html="formatTemplateHtml(row.template)" />
          </template>
        </el-table-column>
        <el-table-column prop="category" label="适用品类" width="100">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.category || '通用' }}</el-tag>
          </template>
        </el-table-column>
        <!--<el-table-column prop="use_count" label="使用次数" width="100" align="center">
          <template #default="{ row }">
            <span>{{ row.use_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="系统种子" width="90" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_system" type="info" size="small">系统</el-tag>
          </template>
        </el-table-column>-->
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'enabled' ? 'success' : 'danger'" size="small">
              {{ row.status === 'enabled' ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button
              v-if="row.is_system === true"
              size="small"
              :type="row.status === 'enabled' ? 'warning' : 'success'"
              link
              @click="handleToggleStatus(row)"
            >
              {{ row.status === 'enabled' ? '禁用' : '启用' }}
            </el-button>
            <el-button
              v-if="row.is_system !== true || isSuperAdmin"
              size="small"
              type="danger"
              link
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadSeeds"
          @current-change="loadSeeds"
        />
      </div>
    </div>

    <!-- 编辑/新建弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingSeed ? '编辑种子' : '新建种子'"
      width="700px"
      @close="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="种子名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入种子名称，如：反常识开头" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="种子类型" prop="seed_type">
          <el-select v-model="form.seed_type" style="width: 100%;" :disabled="!!editingSeed?.is_system">
            <el-option label="开头模式" value="opening" />
            <el-option label="情感基调" value="emotion" />
            <el-option label="结尾模式" value="ending" />
          </el-select>
        </el-form-item>
        <el-form-item label="模板示例" prop="template">
          <el-input
            v-model="form.template"
            type="textarea"
            :rows="3"
            placeholder="单个模板：没想到这个xxx居然...&#10;多个模板（JSON数组）：[&#10;  &quot;没想到这个xxx居然...&quot;,&#10;  &quot;谁能想到xxx竟然...&quot;&#10;]"
          />
          <div class="form-tip">模板是创意种子的核心表达方式。支持单个模板或JSON数组格式（多个模板时AI会随机选择参考）</div>
        </el-form-item>
        <el-form-item label="使用说明">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="请描述该种子的使用场景和注意事项" />
        </el-form-item>
        <el-form-item label="禁止模式">
          <el-select
            v-model="form.forbidden_patterns"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入后按回车添加"
            style="width: 100%;"
          />
          <div class="form-tip">禁止使用的词汇或表达方式，避免生成不当内容</div>
        </el-form-item>
        <el-form-item label="典型表达">
          <el-select
            v-model="form.example_phrases"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入后按回车添加"
            style="width: 100%;"
          />
          <div class="form-tip">推荐的典型表达示例，供AI参考</div>
        </el-form-item>
        <el-form-item label="避免表达">
          <el-select
            v-model="form.avoid_phrases"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入后按回车添加"
            style="width: 100%;"
          />
          <div class="form-tip">应避免的表达方式</div>
        </el-form-item>
        <el-form-item label="适用品类">
          <el-select v-model="form.category" style="width: 100%;">
            <el-option v-for="c in categoryOptions" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio value="enabled">启用</el-radio>
            <el-radio value="disabled">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { apiClient } from '@/api/types'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const isSuperAdmin = computed(() => authStore.userRole === 'super_admin')

interface CreativeSeed {
  id: number
  name: string
  seed_type: 'opening' | 'emotion' | 'ending'
  template: string
  description?: string
  forbidden_patterns?: string[]
  example_phrases?: string[]
  avoid_phrases?: string[]
  category?: string
  status: 'enabled' | 'disabled'
  is_system: boolean
  use_count: number
  created_at: string
  updated_at: string
}

const seeds = ref<CreativeSeed[]>([])
const loading = ref(false)
const submitting = ref(false)
const activeType = ref('')
const filterCategory = ref('')
const filterStatus = ref('')
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const categoryOptions = [
  '通用',
  '美妆护肤',
  '服饰穿搭',
  '美食探店',
  '家居生活',
  '母婴育儿',
  '数码3C',
  '旅行风景',
  '运动健身',
  '宠物萌宠',
  '教育学习',
  '职场成长',
  '情感心理',
  '娱乐追剧',
  '游戏二次元',
  '汽车出行',
  '珠宝首饰',
  '图书文具',
  '大健康养生',
  '本地生活',
]

const dialogVisible = ref(false)
const editingSeed = ref<CreativeSeed | null>(null)
const formRef = ref<FormInstance>()

const form = ref({
  name: '',
  seed_type: 'opening' as 'opening' | 'emotion' | 'ending',
  template: '',
  description: '',
  forbidden_patterns: [] as string[],
  example_phrases: [] as string[],
  avoid_phrases: [] as string[],
  category: '通用',
  status: 'enabled' as 'enabled' | 'disabled',
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入种子名称', trigger: 'blur' }],
  seed_type: [{ required: true, message: '请选择种子类型', trigger: 'change' }],
  template: [{ required: true, message: '请输入模板示例', trigger: 'blur' }],
}

const typeLabels: Record<string, string> = {
  opening: '开头模式',
  emotion: '情感基调',
  ending: '结尾模式',
}

const typeTagTypes: Record<string, string> = {
  opening: 'primary',
  emotion: 'success',
  ending: 'warning',
}

function getTypeLabel(type: string): string {
  return typeLabels[type] || type
}

function getTypeTagType(type: string): string {
  return typeTagTypes[type] || ''
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function formatTemplateHtml(template: string): string {
  if (!template) return ''
  try {
    // 尝试解析 JSON
    const parsed = JSON.parse(template)
    if (Array.isArray(parsed)) {
      // JSON 数组格式，用列表显示
      return parsed.map((item, index) => `<div>${index + 1}. ${escapeHtml(item)}</div>`).join('')
    }
    // 解析成功但不是数组（如普通字符串），直接显示
    return escapeHtml(template)
  } catch {
    // 解析失败，说明是普通字符串，直接显示
    return escapeHtml(template)
  }
}

function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

async function loadSeeds() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      limit: pageSize.value,
    }
    if (activeType.value) params.seed_type = activeType.value
    if (filterCategory.value) params.category = filterCategory.value
    if (filterStatus.value) params.status = filterStatus.value
    if (searchKeyword.value) params.keyword = searchKeyword.value

    const resp = await apiClient.getCreativeSeeds(params)
    seeds.value = resp.items || []
    total.value = resp.total || 0
  } catch (e: any) {
    ElMessage.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function handleAdd() {
  editingSeed.value = null
  form.value = {
    name: '',
    seed_type: 'opening',
    template: '',
    description: '',
    forbidden_patterns: [],
    example_phrases: [],
    avoid_phrases: [],
    category: '通用',
    status: 'enabled',
  }
  dialogVisible.value = true
}

function handleEdit(row: CreativeSeed) {
  editingSeed.value = row
  // 解析 template 字段：如果是 JSON 数组，转换为易读的换行格式；否则保持原样
  let displayTemplate = row.template || ''
  try {
    const parsed = JSON.parse(row.template)
    if (Array.isArray(parsed)) {
      // JSON 数组转换为每行一个的格式
      displayTemplate = parsed.join('\n')
    }
    // 如果不是数组，保持原样（普通字符串）
  } catch {
    // 解析失败，说明是普通字符串，保持原样
    displayTemplate = row.template || ''
  }
  
  form.value = {
    name: row.name,
    seed_type: row.seed_type,
    template: displayTemplate,
    description: row.description || '',
    forbidden_patterns: row.forbidden_patterns || [],
    example_phrases: row.example_phrases || [],
    avoid_phrases: row.avoid_phrases || [],
    category: row.category || '通用',
    status: row.status,
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      // 处理 template 字段：如果包含换行符，转换为 JSON 数组
      let templateToSave = form.value.template
      if (templateToSave.includes('\n')) {
        // 将换行分隔的模板转换为 JSON 数组
        const templates = templateToSave.split('\n').map(t => t.trim()).filter(t => t)
        templateToSave = JSON.stringify(templates)
      }
      
      if (editingSeed.value) {
        await apiClient.updateCreativeSeed(editingSeed.value.id, {
          name: form.value.name,
          template: templateToSave,
          description: form.value.description,
          forbidden_patterns: form.value.forbidden_patterns,
          example_phrases: form.value.example_phrases,
          avoid_phrases: form.value.avoid_phrases,
          status: form.value.status,
          category: form.value.category,
        })
        ElMessage.success('更新成功')
      } else {
        await apiClient.createCreativeSeed({
          name: form.value.name,
          seed_type: form.value.seed_type,
          template: templateToSave,
          description: form.value.description,
          forbidden_patterns: form.value.forbidden_patterns,
          example_phrases: form.value.example_phrases,
          avoid_phrases: form.value.avoid_phrases,
          category: form.value.category,
        })
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      loadSeeds()
    } catch (e: any) {
      ElMessage.error(e.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

async function handleToggleStatus(row: CreativeSeed) {
  const newStatus = row.status === 'enabled' ? 'disabled' : 'enabled'
  const actionText = newStatus === 'enabled' ? '启用' : '禁用'

  try {
    await ElMessageBox.confirm(
      `确定${actionText}系统种子"${row.name}"吗？`,
      `确认${actionText}`,
      { type: 'warning' }
    )

    await apiClient.updateCreativeSeed(row.id, { status: newStatus })
    ElMessage.success(`${actionText}成功`)
    loadSeeds()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '操作失败')
    }
  }
}

async function handleDelete(row: CreativeSeed) {
  try {
    const seedTypeLabel = getTypeLabel(row.seed_type)
    let confirmMessage = `确定要删除${seedTypeLabel}"${row.name}"吗？\n\n删除后：\n- 模板中如果引用了此种子，会自动使用随机种子替代\n- 此操作不可恢复`
    
    // 系统种子需要额外警告
    if (row.is_system) {
      confirmMessage = `⚠️ 这是系统种子！\n\n${confirmMessage}\n\n删除系统种子可能影响系统的默认功能，请谨慎操作！`
    }
    
    await ElMessageBox.confirm(
      confirmMessage,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        distinguishCancelAndClose: true
      }
    )
    await apiClient.deleteCreativeSeed(row.id)
    ElMessage.success('删除成功')
    loadSeeds()
  } catch (e: any) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

function resetForm() {
  formRef.value?.resetFields()
}

onMounted(() => {
  loadSeeds()
})
</script>

<style lang="scss" scoped>
@import '../../assets/styles/variables.scss';
@import '../../assets/styles/mixins.scss';

.creative-seed-view {
  padding: 0;
}

// ============================================
// 主卡片 - 高级浮起效果
// ============================================

.card {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-default);
  border-radius: $radius-xl;
  box-shadow:
    0 1px 3px rgba(15, 23, 42, 0.04),
    0 4px 12px rgba(15, 23, 42, 0.03);
  padding: $spacing-lg;
}

// ============================================
// Tabs 样式优化
// ============================================

.mb-md {
  margin-bottom: $spacing-md;

  // Tab 高级样式
  :deep(.el-tabs__header) {
    margin-bottom: $spacing-md;
  }

  :deep(.el-tabs__nav-wrap::after) {
    background-color: var(--color-border-default);
  }

  :deep(.el-tabs__item) {
    font-family: var(--font-family-body);
    font-weight: $font-weight-medium;
    font-size: $font-size-sm;
    color: var(--color-text-secondary);
    transition: all $transition-normal $easing-standard;

    &:hover { color: var(--color-primary); }
    &.is-active {
      color: var(--color-primary);
      font-weight: $font-weight-semibold;
    }
  }

  :deep(.el-tabs__active-bar) {
    background: linear-gradient(90deg, var(--color-primary), var(--color-primary-light));
    height: 3px;
    border-radius: 2px;
  }
}

// ============================================
// 工具栏 - 无边框无背景紧凑设计
// ============================================

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

.toolbar-left {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
}

.flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

// ============================================
// 分页 - 紧凑设计
// ============================================

.pagination-wrapper {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin-top: $spacing-sm;
  padding: $spacing-sm 0;
  background: transparent;
  border-radius: 0;
  border: none;
  border-top: 1px solid var(--color-border-default);
}

// ============================================
// 表单提示
// ============================================

.form-tip {
  font-size: $font-size-xs;
  color: var(--color-text-muted);
  line-height: 1.5;
  margin-top: 6px;
  padding-left: 2px;
}

// ============================================
// 模板单元格
// ============================================

.template-cell {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
  color: var(--color-text-secondary);
  font-size: $font-size-sm;
}
</style>
