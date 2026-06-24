<template>
  <div class="scheduled-task-create-view">
    <div class="page-header mb-md">
      <el-page-header @back="handleBack">
        <template #content>
          <span class="page-title">{{ isEdit ? '编辑定时任务' : '创建定时任务' }}</span>
        </template>
      </el-page-header>
    </div>

    <div class="card">
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="140px"
        v-loading="loading"
      >
        <!-- 基本信息 -->
        <div class="form-section">
          <div class="section-title">基本信息</div>
          
          <el-form-item label="任务名称" prop="name">
            <el-input
              v-model="formData.name"
              placeholder="请输入任务名称"
              maxlength="100"
              show-word-limit
            />
          </el-form-item>

          <el-form-item label="任务类型" prop="task_type">
            <el-radio-group v-model="formData.task_type">
              <el-radio value="custom">自定义文案</el-radio>
              <el-radio value="benchmark">对标文案</el-radio>
            </el-radio-group>
          </el-form-item>
        </div>

        <!-- 调度配置 -->
        <div class="form-section">
          <div class="section-title">调度配置</div>
          
          <el-form-item label="调度类型" prop="schedule_config_json.type">
            <el-radio-group v-model="formData.schedule_config_json.type">
              <el-radio value="daily">每日</el-radio>
              <el-radio value="weekly">每周</el-radio>
              <el-radio value="periodic">周期</el-radio>
            </el-radio-group>
          </el-form-item>
          
          <!-- 每日调度 -->
          <el-form-item
            v-if="formData.schedule_config_json.type === 'daily'"
            label="执行时间点"
            prop="schedule_config_json.times">
            <div class="time-points-container">
              <div v-for="(_, index) in formData.schedule_config_json.times" :key="index" class="time-point-item">
                <el-time-picker
                  v-model="formData.schedule_config_json.times[index]"
                  placeholder="选择时间"
                  format="HH:mm"
                  value-format="HH:mm"
                />
                <el-button
                  v-if="formData.schedule_config_json.times.length > 1"
                  type="danger"
                  :icon="Delete"
                  circle
                  size="small"
                  @click="removeTimePoint(index, 'daily')"
                />
              </div>
              <el-button type="primary" :icon="Plus" size="small" @click="addTimePoint('daily')">
                添加时间点
              </el-button>
            </div>
          </el-form-item>
          
          <!-- 每周调度 -->
          <template v-if="formData.schedule_config_json.type === 'weekly'">
            <el-form-item label="执行日期" prop="schedule_config_json.weekdays">
              <el-checkbox-group v-model="formData.schedule_config_json.weekdays">
                <el-checkbox :value="1">周一</el-checkbox>
                <el-checkbox :value="2">周二</el-checkbox>
                <el-checkbox :value="3">周三</el-checkbox>
                <el-checkbox :value="4">周四</el-checkbox>
                <el-checkbox :value="5">周五</el-checkbox>
                <el-checkbox :value="6">周六</el-checkbox>
                <el-checkbox :value="7">周日</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
            
            <el-form-item label="执行时间点" prop="schedule_config_json.weekly_times">
              <div class="time-points-container">
                <div v-for="(_, index) in formData.schedule_config_json.weekly_times" :key="index" class="time-point-item">
                  <el-time-picker
                    v-model="formData.schedule_config_json.weekly_times[index]"
                    placeholder="选择时间"
                    format="HH:mm"
                    value-format="HH:mm"
                  />
                  <el-button
                    v-if="formData.schedule_config_json.weekly_times.length > 1"
                    type="danger"
                    :icon="Delete"
                    circle
                    size="small"
                    @click="removeTimePoint(index, 'weekly')"
                  />
                </div>
                <el-button type="primary" :icon="Plus" size="small" @click="addTimePoint('weekly')">
                  添加时间点
                </el-button>
              </div>
            </el-form-item>
          </template>
          
          <!-- 周期调度 -->
          <template v-if="formData.schedule_config_json.type === 'periodic'">
            <el-form-item label="开始日期" prop="schedule_config_json.start_date">
              <el-date-picker
                v-model="formData.schedule_config_json.start_date"
                type="date"
                placeholder="选择开始日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
            
            <el-form-item label="结束日期" prop="schedule_config_json.end_date">
              <el-date-picker
                v-model="formData.schedule_config_json.end_date"
                type="date"
                placeholder="选择结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
            
            <el-form-item
              label="执行时间点"
              prop="schedule_config_json.times">
              <div class="time-points-container">
                <div v-for="(_, index) in formData.schedule_config_json.times" :key="index" class="time-point-item">
                  <el-time-picker
                    v-model="formData.schedule_config_json.times[index]"
                    placeholder="选择时间"
                    format="HH:mm"
                    value-format="HH:mm"
                  />
                  <el-button
                    v-if="formData.schedule_config_json.times.length > 1"
                    type="danger"
                    :icon="Delete"
                    circle
                    size="small"
                    @click="removeTimePoint(index, 'periodic')"
                  />
                </div>
                <el-button type="primary" :icon="Plus" size="small" @click="addTimePoint('periodic')">
                  添加时间点
                </el-button>
              </div>
            </el-form-item>
          </template>
        </div>

        <!-- 素材和模板配置 -->
        <div class="form-section">
          <div class="section-title">素材和模板配置</div>

          <!-- 自定义文案：选择创作素材 -->
          <el-form-item label="模板选择" prop="template_ids_json">
            <div class="selection-display">
              <div class="selected-tags" style="margin-bottom: 8px;">
                <el-tag
                  v-for="tplId in formData.template_ids_json"
                  :key="tplId"
                  closable
                  @close="removeTemplate(tplId)"
                  class="mr-xs mb-xs"
                >
                  {{ getTemplateName(tplId) }}
                </el-tag>
                <span v-if="formData.template_ids_json.length === 0" class="text-muted">暂未选择模板</span>
              </div>
              <el-button type="primary" @click="showTemplateDialog = true">
                选择模板
              </el-button>
            </div>
            <TemplateSelectDialog
              v-model="showTemplateDialog"
              :current-template-ids="formData.template_ids_json"
              @select="handleTemplateSelect"
            />
          </el-form-item>

          <!-- 对标文案：选择对标素材 -->
          <el-form-item
            v-if="formData.task_type === 'benchmark'"
            label="对标素材"
            prop="benchmark_material_ids_json"
          >
            <div class="selection-display">
              <div class="selected-tags" style="margin-bottom: 8px;">
                <el-tag
                  v-for="material in selectedBenchmarkMaterials"
                  :key="material.id"
                  closable
                  @close="removeBenchmarkMaterial(material.id)"
                  class="mr-xs mb-xs"
                >
                  {{ material.title }}
                </el-tag>
                <span v-if="selectedBenchmarkMaterials.length === 0" class="text-muted">暂未选择对标素材</span>
              </div>
              <el-button type="primary" @click="showBenchmarkMaterialDialog = true">
                选择对标素材
              </el-button>
            </div>
            <MaterialSelectDialog
              v-model="showBenchmarkMaterialDialog"
              :is-benchmark="true"
              :current-material-ids="formData.benchmark_material_ids_json"
              @select="handleBenchmarkMaterialSelect"
            />
          </el-form-item>
        </div>

        <!-- 创作者配置 -->
        <div class="form-section">
          <div class="section-title">创作者配置</div>

          <el-form-item label="创作者选择" prop="sub_user_ids_json">
            <div class="selection-display">
              <div class="selected-tags" style="margin-bottom: 8px;">
                <el-tag
                  v-for="userId in formData.sub_user_ids_json"
                  :key="userId"
                  closable
                  @close="removeSubUser(userId)"
                  class="mr-xs mb-xs"
                >
                  {{ getSubUserName(userId) }}
                </el-tag>
                <span v-if="formData.sub_user_ids_json.length === 0" class="text-muted">暂未选择创作者</span>
              </div>
              <el-button type="primary" @click="showSubUserDialog = true">
                选择创作者
              </el-button>
            </div>
            <SubUserSelectDialog
              v-model="showSubUserDialog"
              :current-user-ids="formData.sub_user_ids_json"
              @select="handleSubUserSelect"
            />
          </el-form-item>
        </div>

        <!-- 模型配置 -->
        <div class="form-section">
          <div class="section-title">模型配置</div>

          <el-form-item label="模型选择方式" prop="model_selection_mode">
            <el-radio-group v-model="formData.model_selection_mode">
              <el-radio value="auto">自动选择</el-radio>
              <el-radio value="manual">手动选择</el-radio>
            </el-radio-group>
          </el-form-item>

          <template v-if="formData.model_selection_mode === 'manual'">
            <el-row :gutter="10">
              <el-col :span="10">
                <el-form-item label="文案模型">
                  <el-select
                    v-model="formData.model_id"
                    placeholder="请选择文案模型"
                    clearable
                    style="width: 100%;"
                  >
                    <el-option
                      v-for="model in llmModels"
                      :key="model.model_id"
                      :label="getModelLabel(model)"
                      :value="model.model_id"
                    />
                  </el-select>
                </el-form-item>
              </el-col>

              <el-col :span="10">
                <el-form-item label="图片模型">
                  <el-select
                    v-model="formData.image_model_id"
                    placeholder="请选择图片模型"
                    clearable
                    style="width: 100%;"
                  >
                    <el-option
                      v-for="model in imageModels"
                      :key="model.model_id"
                      :label="getModelLabel(model)"
                      :value="model.model_id"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </template>

          <el-form-item label="任务并发数">
            <el-input-number
              v-model="formData.max_concurrency"
              :min="1"
              :max="maxConcurrencyLimit"
              :step="1"
            />
            <span class="form-item-tip">每个任务同时执行的最大并发数（1-{{ maxConcurrencyLimit }}，Worker 总数的一半）</span>
          </el-form-item>
        </div>

        <!-- 去重配置 -->
        <div class="form-section">
          <div class="section-title">去重配置</div>

          <!-- 第一行：文案去重和图片去重开关 -->
          <el-row :gutter="0">
            <el-col :span="10">
              <el-form-item label="文案去重">
                <el-switch v-model="formData.dedup_enabled" />
              </el-form-item>
            </el-col>

            <el-col :span="10">
              <el-form-item label="图片去重">
                <el-switch v-model="formData.image_dedup_enabled" />
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 第二行：文案相似度阈值和图片相似度阈值 -->
          <template v-if="formData.dedup_enabled || formData.image_dedup_enabled">
            <el-row :gutter="0">
              <el-col :span="10" v-if="formData.dedup_enabled">
                <el-form-item label="文案相似度阈值">
                  <el-slider
                    v-model="formData.dedup_threshold"
                    :min="0.5"
                    :max="0.95"
                    :step="0.05"
                    show-input
                    :show-input-controls="false"
                  />
                </el-form-item>
              </el-col>

              <el-col :span="10" v-if="formData.image_dedup_enabled">
                <el-form-item label="图片相似度阈值">
                  <el-slider
                    v-model="formData.image_dedup_threshold"
                    :min="0.5"
                    :max="0.95"
                    :step="0.05"
                    show-input
                    :show-input-controls="false"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </template>

          <!-- 第三行：文案去重范围和图片去重范围 -->
          <template v-if="formData.dedup_enabled || formData.image_dedup_enabled">
            <el-row :gutter="0">
              <el-col :span="10" v-if="formData.dedup_enabled">
                <el-form-item label="文案去重范围">
                  <el-checkbox-group v-model="formData.dedup_scope">
                    <el-checkbox value="subuser_history">创作者历史</el-checkbox>
                    <el-checkbox value="current_task">当前任务</el-checkbox>
                    <el-checkbox value="all_history">全部历史</el-checkbox>
                  </el-checkbox-group>
                </el-form-item>
              </el-col>

              <el-col :span="10" v-if="formData.image_dedup_enabled">
                <el-form-item label="图片去重范围">
                  <el-checkbox-group v-model="formData.image_dedup_scope">
                    <el-checkbox value="subuser_image_history">创作者图片历史</el-checkbox>
                    <el-checkbox value="current_task_images">当前任务图片</el-checkbox>
                    <el-checkbox value="all_image_history">全部图片历史</el-checkbox>
                  </el-checkbox-group>
                </el-form-item>
              </el-col>
            </el-row>
          </template>
        </div>

        <!-- 对标配置（仅对标文案） -->
        <div v-if="formData.task_type === 'benchmark'" class="form-section">
          <div class="section-title">对标配置</div>

          <!-- 第一行：对标文案和对标图片开关 -->
          <el-row :gutter="0">
            <el-col :span="10">
              <el-form-item label="对标图片">
                <el-switch v-model="formData.benchmark_image_enabled" />
              </el-form-item>
            </el-col>
            <el-col :span="10">
              <el-form-item label="对标文案">
                <el-switch v-model="formData.benchmark_text_enabled" />
              </el-form-item>
            </el-col>

          </el-row>

          <!-- 第二行：图片参考选项（只有启用对标图片时显示） -->
          <template v-if="formData.benchmark_image_enabled">
            <el-form-item label="图片参考选项">
              <el-checkbox-group v-model="formData.benchmark_image_reference_options">
                <el-checkbox value="composition">构图</el-checkbox>
                <el-checkbox value="color">色调</el-checkbox>
                <el-checkbox value="style">风格</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </template>
        </div>

        <!-- 图片数量 -->
        <div class="form-section">
          <div class="section-title">图片配置</div>

          <el-form-item label="生成图片数量">
            <el-input-number
              v-model="formData.image_count"
              :min="1"
              :max="9"
              :step="1"
            />
          </el-form-item>
        </div>

        <!-- 操作按钮 -->
        <div class="form-actions">
          <el-button @click="handleBack">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEdit ? '保存' : '创建' }}
          </el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { apiClient } from '@/api/types'
import type { Material, Template, User, ModelConfig, ScheduleConfig } from '@/api/types'

// 导入弹窗选择组件
import MaterialSelectDialog from '@/components/selectors/MaterialSelectDialog.vue'
import TemplateSelectDialog from '@/components/selectors/TemplateSelectDialog.vue'
import SubUserSelectDialog from '@/components/selectors/SubUserSelectDialog.vue'

const router = useRouter()
const route = useRoute()

// 判断是否是编辑模式
const isEdit = computed(() => route.params.id !== undefined)
const taskId = computed(() => route.params.id ? Number(route.params.id) : null)

// 表单引用
const formRef = ref<FormInstance>()
const loading = ref(false)
const submitting = ref(false)

// 弹窗状态
const showCreationMaterialDialog = ref(false)
const showBenchmarkMaterialDialog = ref(false)
const showTemplateDialog = ref(false)
const showSubUserDialog = ref(false)

// 选中项状态
const selectedCreationMaterial = ref<Material | null>(null)
const selectedBenchmarkMaterials = ref<Material[]>([])
const selectedTemplates = ref<Template[]>([])
const selectedSubUsers = ref<User[]>([])

// 模型列表（用于下拉选择）
const llmModels = ref<ModelConfig[]>([])
const imageModels = ref<ModelConfig[]>([])

// Worker 状态（用于计算最大并发数）
const workerTotal = ref(32)
const maxConcurrencyLimit = computed(() => Math.max(1, Math.floor(workerTotal.value / 2)))

// 加载模型列表
const loadModels = async () => {
  try {
    const models = await apiClient.getModelConfigs()
    console.log('Loaded models:', models)
    // 过滤出激活的模型（后端状态是 active，不是 enabled）
    const activeModels = models.filter((m: any) => m.status === 'active')
    console.log('Active models:', activeModels)
    llmModels.value = activeModels.filter((m: any) => m.model_type === 'llm')
    imageModels.value = activeModels.filter((m: any) => m.model_type === 'image')
    console.log('LLM models:', llmModels.value)
    console.log('Image models:', imageModels.value)
  } catch (error) {
    console.error('Failed to load models:', error)
  }
}

// 加载 Worker 状态
const loadWorkerStatus = async () => {
  try {
    const status = await apiClient.getWorkerStatus()
    workerTotal.value = status.worker_total || 32
  } catch (error) {
    console.error('Failed to load worker status:', error)
    // 使用默认值 32
  }
}

// 模型显示名称（平台名 + 模型名）
const getModelLabel = (model: ModelConfig) => {
  return `${model.platform}/${model.model_name}`
}

// 表单数据
const formData = reactive({
  name: '' as string,
  task_type: 'custom' as 'custom' | 'benchmark',
  schedule_config_json: {
    type: 'daily' as const,
    times: ['09:00'],
    weekdays: [1],
    weekly_times: ['09:00']
  } as ScheduleConfig,
  material_id: undefined as number | undefined,
  benchmark_material_ids_json: [] as number[],
  template_ids_json: [] as number[],
  sub_user_ids_json: [] as number[],
  model_selection_mode: 'auto' as 'auto' | 'manual',
  model_platform: undefined as string | undefined,
  model_id: undefined as string | undefined,
  image_model_platform: undefined as string | undefined,
  image_model_id: undefined as string | undefined,
  dedup_enabled: false,
  dedup_threshold: 0.95,
  dedup_retry_count: 3,
  dedup_scope: ['subuser_history'],
  image_dedup_enabled: false,
  image_dedup_threshold: 0.95,
  image_dedup_retry_count: 3,
  image_dedup_scope: ['subuser_image_history'],
  benchmark_text_enabled: false,  // 默认关闭对标文案
  benchmark_image_enabled: false,  // 默认关闭对标图片
  benchmark_image_reference_options: [] as string[],
  benchmark_image_roles_json: undefined as Record<string, string[]> | undefined,
  template_product_mapping_json: undefined as Record<string, string> | undefined,
  image_count: 1,
  max_concurrency: 5,
  variable_values_json: undefined as Record<string, any> | undefined
})

// 表单验证规则
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入任务名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  task_type: [
    { required: true, message: '请选择任务类型', trigger: 'change' }
  ],
  'schedule_config_json.type': [
    { required: true, message: '请选择调度类型', trigger: 'change' }
  ],
  'schedule_config_json.times': [
    {
      validator: (_, value, callback) => {
        if (formData.schedule_config_json.type === 'daily' || formData.schedule_config_json.type === 'periodic') {
          if (!value || value.length === 0) {
            callback(new Error('请至少添加一个执行时间点'))
          } else {
            callback()
          }
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  'schedule_config_json.start_date': [
    {
      validator: (_, value, callback) => {
        if (formData.schedule_config_json.type === 'periodic') {
          if (!value) {
            callback(new Error('请选择开始日期'))
          } else {
            callback()
          }
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  'schedule_config_json.end_date': [
    {
      validator: (_, value, callback) => {
        if (formData.schedule_config_json.type === 'periodic') {
          if (!value) {
            callback(new Error('请选择结束日期'))
          } else if (formData.schedule_config_json.start_date && value < formData.schedule_config_json.start_date) {
            callback(new Error('结束日期不能早于开始日期'))
          } else {
            callback()
          }
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  'schedule_config_json.weekdays': [
    {
      validator: (_, value, callback) => {
        if (formData.schedule_config_json.type === 'weekly') {
          if (!value || value.length === 0) {
            callback(new Error('请至少选择一个执行日期'))
          } else {
            callback()
          }
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  material_id: [
    {
      validator: (_, value, callback) => {
        if (formData.task_type === 'custom') {
          if (!value) {
            callback(new Error('请选择创作素材'))
          } else {
            callback()
          }
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  benchmark_material_ids: [
    { required: true, message: '请至少选择一个对标素材', trigger: 'change', type: 'array' }
  ],
  template_ids: [
    { required: true, message: '请至少选择一个模板', trigger: 'change', type: 'array' }
  ],
  sub_user_ids: [
    { required: true, message: '请至少选择一个创作者', trigger: 'change', type: 'array' }
  ]
}

// ========== 弹窗选择处理函数 ==========

// 创作素材选择
const handleCreationMaterialSelect = (material: Material) => {
  selectedCreationMaterial.value = material
  formData.material_id = material.id
  // 清除验证状态
  nextTick(() => {
    formRef.value?.clearValidate('material_id')
  })
}

const clearCreationMaterial = () => {
  selectedCreationMaterial.value = null
  formData.material_id = undefined
}

// 对标素材选择（支持多选）
const handleBenchmarkMaterialSelect = (materials: Material[]) => {
  selectedBenchmarkMaterials.value = materials
  formData.benchmark_material_ids_json = materials.map(m => m.id)
  // 清除验证状态
  nextTick(() => {
    formRef.value?.clearValidate('benchmark_material_ids_json')
  })
}

// 移除单个对标素材
const removeBenchmarkMaterial = (id: number) => {
  const index = formData.benchmark_material_ids_json.indexOf(id)
  if (index > -1) {
    formData.benchmark_material_ids_json.splice(index, 1)
    selectedBenchmarkMaterials.value = selectedBenchmarkMaterials.value.filter(m => m.id !== id)
  }
  // 清除验证状态
  nextTick(() => {
    formRef.value?.clearValidate('benchmark_material_ids_json')
  })
}

// 模板选择
const handleTemplateSelect = (templates: Template[]) => {
  selectedTemplates.value = templates
  formData.template_ids_json = templates.map(t => t.id)
  // 清除验证状态
  nextTick(() => {
    formRef.value?.clearValidate('template_ids_json')
  })
}

const removeTemplate = (id: number) => {
  const index = formData.template_ids_json.indexOf(id)
  if (index > -1) {
    formData.template_ids_json.splice(index, 1)
    selectedTemplates.value = selectedTemplates.value.filter(t => t.id !== id)
  }
  // 清除验证状态
  nextTick(() => {
    formRef.value?.clearValidate('template_ids_json')
  })
}

const getTemplateName = (id: number): string => {
  const template = selectedTemplates.value.find(t => t.id === id)
  return template ? template.name : `模板${id}`
}

// 创作者选择
const handleSubUserSelect = (users: User[]) => {
  selectedSubUsers.value = users
  formData.sub_user_ids_json = users.map(u => u.id)
  // 清除验证状态
  nextTick(() => {
    formRef.value?.clearValidate('sub_user_ids_json')
  })
}

const removeSubUser = (id: number) => {
  const index = formData.sub_user_ids_json.indexOf(id)
  if (index > -1) {
    formData.sub_user_ids_json.splice(index, 1)
    selectedSubUsers.value = selectedSubUsers.value.filter(u => u.id !== id)
  }
}

const getSubUserName = (id: number): string => {
  const user = selectedSubUsers.value.find(u => u.id === id)
  return user ? (user as any).nickname || (user as any).display_name || `用户${id}` : `用户${id}`
}

// ========== 加载数据（编辑模式） ==========

// 加载任务详情（编辑模式）
const loadTaskDetail = async () => {
  if (!taskId.value) return
  
  loading.value = true
  try {
    const task = await apiClient.getScheduledTask(taskId.value)
    
    // 填充表单数据
    formData.name = task.name
    formData.task_type = task.task_type
    // 调度配置：将后端 schedule_type + schedule_config_json 映射到前端 formData 结构
    const scheduleType = (task as any).schedule_type || 'daily'
    const configJson = (task as any).schedule_config_json || {}
    formData.schedule_config_json.type = scheduleType
    if (scheduleType === 'daily') {
      formData.schedule_config_json.times = configJson.times || ['09:00']
      formData.schedule_config_json.weekdays = [1]  // 重置默认值
      formData.schedule_config_json.weekly_times = ['09:00']  // 重置默认值
      formData.schedule_config_json.start_date = undefined  // 清除周期字段
      formData.schedule_config_json.end_date = undefined  // 清除周期字段
    } else if (scheduleType === 'periodic') {
      formData.schedule_config_json.start_date = configJson.start_date || undefined
      formData.schedule_config_json.end_date = configJson.end_date || undefined
      formData.schedule_config_json.times = configJson.times || ['09:00']
      formData.schedule_config_json.weekdays = [1]  // 重置默认值
      formData.schedule_config_json.weekly_times = ['09:00']  // 重置默认值
    } else {
      formData.schedule_config_json.times = ['09:00']  // 重置默认值
      formData.schedule_config_json.weekdays = configJson.days || [1]  // 后端用 days
      formData.schedule_config_json.weekly_times = configJson.times || ['09:00']
      formData.schedule_config_json.start_date = undefined  // 清除周期字段
      formData.schedule_config_json.end_date = undefined  // 清除周期字段
    }
    formData.material_id = task.material_id
    // 兼容后端可能的字段名：benchmark_material_ids_json (新) / benchmark_material_ids (旧) / benchmark_material_id (更旧)
    const benchmarkIds = (task as any).benchmark_material_ids_json || 
                       (task as any).benchmark_material_ids || 
                       ((task as any).benchmark_material_id ? [(task as any).benchmark_material_id] : [])
    formData.benchmark_material_ids_json = benchmarkIds
    // 兼容后端可能的字段名：template_ids_json (新) / template_ids (旧)
    formData.template_ids_json = (task as any).template_ids_json || (task as any).template_ids || []
    // 兼容后端可能的字段名：sub_user_ids_json (新) / sub_user_ids (旧)
    formData.sub_user_ids_json = (task as any).sub_user_ids_json || (task as any).sub_user_ids || []
    formData.model_selection_mode = task.model_selection_mode || 'auto'
    formData.model_platform = task.model_platform
    formData.model_id = task.model_id
    formData.image_model_platform = task.image_model_platform
    formData.image_model_id = task.image_model_id
    formData.dedup_enabled = task.dedup_enabled || false
    // 后端存储的是 0-100 的整数，前端 slider 需要 0.0-1.0 的小数
    formData.dedup_threshold = (task.dedup_threshold || 90) / 100
    formData.dedup_scope = task.dedup_scope || []
    formData.image_dedup_enabled = task.image_dedup_enabled || false
    // 后端存储的是 0-100 的整数，前端 slider 需要 0.0-1.0 的小数
    formData.image_dedup_threshold = (task.image_dedup_threshold || 90) / 100
    formData.image_dedup_scope = task.image_dedup_scope || []
    formData.benchmark_text_enabled = task.benchmark_text_enabled || false
    formData.benchmark_image_enabled = task.benchmark_image_enabled || false
    formData.benchmark_image_reference_options = task.benchmark_image_reference_options || []
    formData.image_count = task.image_count || 3
    formData.max_concurrency = task.max_concurrency || 5

    // 加载选中的素材详情
    if (task.material_id) {
      try {
        selectedCreationMaterial.value = await apiClient.getMaterial(task.material_id)
      } catch (e) { /* ignore */ }
    }
    // 加载选中的对标素材详情
    if (benchmarkIds.length > 0) {
      try {
        const materials = await Promise.all(
          benchmarkIds.map((id: number) => apiClient.getMaterial(id))
        )
        selectedBenchmarkMaterials.value = materials
      } catch (e) { /* ignore */ }
    }

    // 加载选中的模板详情（兼容字段名）
    const templateIds = (task as any).template_ids_json || (task as any).template_ids || []
    if (templateIds.length > 0) {
      try {
        const templatePromises = templateIds.map((id: number) => apiClient.getTemplate(id))
        selectedTemplates.value = await Promise.all(templatePromises)
      } catch (e) { /* ignore */ }
    }

    // 加载选中的创作者详情（兼容字段名）
    const subUserIds = (task as any).sub_user_ids_json || (task as any).sub_user_ids || []
    if (subUserIds.length > 0) {
      try {
        const userPromises = subUserIds.map((id: number) => apiClient.getSubUser(id))
        selectedSubUsers.value = await Promise.all(userPromises)
      } catch (e) { /* ignore */ }
    }

    // 模型选择（model_id 和 image_model_id 已经直接设置为字符串，el-select 会正确显示）
  } catch (error: any) {
    ElMessage.error(error.message || '加载任务详情失败')
    router.back()
  } finally {
    loading.value = false
  }
}

// 添加时间点
const addTimePoint = (type: 'daily' | 'weekly' | 'periodic') => {
  if (type === 'daily' || type === 'periodic') {
    formData.schedule_config_json.times.push('09:00')
  } else {
    formData.schedule_config_json.weekly_times.push('09:00')
  }
}

// 移除时间点
const removeTimePoint = (index: number, type: 'daily' | 'weekly' | 'periodic') => {
  if (type === 'daily' || type === 'periodic') {
    formData.schedule_config_json.times.splice(index, 1)
  } else {
    formData.schedule_config_json.weekly_times.splice(index, 1)
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      // 构建 schedule_config_json，根据 schedule_type 只发送对应字段
      let scheduleConfigJson: any = {}
      if (formData.schedule_config_json.type === 'daily') {
        scheduleConfigJson = {
          times: formData.schedule_config_json.times
        }
      } else if (formData.schedule_config_json.type === 'weekly') {
        scheduleConfigJson = {
          days: formData.schedule_config_json.weekdays,  // 后端期望 days 字段名
          times: formData.schedule_config_json.weekly_times  // 后端期望 times 字段名
        }
      } else if (formData.schedule_config_json.type === 'periodic') {
        scheduleConfigJson = {
          start_date: formData.schedule_config_json.start_date,
          end_date: formData.schedule_config_json.end_date,
          times: formData.schedule_config_json.times
        }
      }

      // 构建提交数据，字段名已经与后端匹配（都使用 _json 后缀）
      const submitData: any = {
        name: formData.name,
        task_type: formData.task_type,
        schedule_type: formData.schedule_config_json.type,  // 添加 schedule_type 字段
        schedule_config_json: scheduleConfigJson,  // 使用转换后的结构
        material_id: formData.task_type === 'custom' ? formData.material_id : undefined,  // 自定义文案才有创作素材
        benchmark_material_ids_json: formData.task_type === 'benchmark' ? (formData.benchmark_material_ids_json || undefined) : undefined,  // 对标文案才有对标素材
        template_ids_json: formData.template_ids_json || undefined,
        sub_user_ids_json: formData.sub_user_ids_json || [],  // 确保始终发送数组，即使是空数组
        model_selection_mode: formData.model_selection_mode,
        model_platform: formData.model_platform,
        model_id: formData.model_id,
        image_model_platform: formData.image_model_platform,
        image_model_id: formData.image_model_id,
        dedup_enabled: formData.dedup_enabled,
        dedup_threshold: Math.round(formData.dedup_threshold * 100),  // 转换为 0-100 的整数
        dedup_retry_count: formData.dedup_retry_count,
        dedup_scope: formData.dedup_scope,
        image_dedup_enabled: formData.image_dedup_enabled,
        image_dedup_threshold: Math.round(formData.image_dedup_threshold * 100),  // 转换为 0-100 的整数
        image_dedup_retry_count: formData.image_dedup_retry_count,
        image_dedup_scope: formData.image_dedup_scope,
      }

      // 对标配置：仅在对标文案时发送
      if (formData.task_type === 'benchmark') {
        submitData.benchmark_text_enabled = formData.benchmark_text_enabled
        submitData.benchmark_image_enabled = formData.benchmark_image_enabled
        submitData.benchmark_image_reference_options = formData.benchmark_image_reference_options
        submitData.benchmark_image_roles_json = formData.benchmark_image_roles_json
        submitData.template_product_mapping_json = formData.template_product_mapping_json
      }

      // 通用配置
      submitData.variable_values_json = formData.variable_values_json
      submitData.image_count = formData.image_count
      submitData.max_concurrency = formData.max_concurrency

      // 调用 API
      if (isEdit.value && taskId.value) {
        await apiClient.updateScheduledTask(taskId.value, submitData)
        ElMessage.success('任务已更新')
      } else {
        await apiClient.createScheduledTask(submitData)
        ElMessage.success('任务已创建')
      }

      router.push('/scheduled-tasks')
    } catch (error: any) {
      ElMessage.error(error.message || (isEdit.value ? '更新失败' : '创建失败'))
    } finally {
      submitting.value = false
    }
  })
}

// 返回
const handleBack = () => {
  router.back()
}

onMounted(async () => {
  // 加载模型列表
  await loadModels()
  // 加载 Worker 状态
  await loadWorkerStatus()
  
  if (isEdit.value) {
    await loadTaskDetail()
  }
})

// ============================================
// 监听 model_id / image_model_id 变化，自动设置对应的 platform
// ============================================
watch(() => formData.model_id, (newVal) => {
  if (newVal) {
    const model = llmModels.value.find(m => m.model_id === newVal)
    formData.model_platform = model?.platform
  } else {
    formData.model_platform = undefined
  }
})

watch(() => formData.image_model_id, (newVal) => {
  if (newVal) {
    const model = imageModels.value.find(m => m.model_id === newVal)
    formData.image_model_platform = model?.platform
  } else {
    formData.image_model_platform = undefined
  }
})
</script>

<style scoped lang="scss">
@import './scheduled-tasks.scss';

.scheduled-task-create-view {
  .card {
    background: var(--bg-secondary);
    padding: 24px;
    border-radius: 8px;
    box-shadow: 0 2px 8px var(--shadow-color, rgba(0, 0, 0, 0.08));
  }

  .form-section {
    margin-bottom: 32px;

    .section-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 16px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--border-color);
    }
  }

  .time-points-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;

    .time-point-item {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }

  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 16px;
    margin-top: 32px;
    padding-top: 16px;
    border-top: 1px solid var(--border-color);
  }
  .form-item-tip {
    margin-left: 12px;
    font-size: 12px;
    color: var(--text-secondary, #909399);
  }
}

.mb-md {
  margin-bottom: 16px;
}
</style>