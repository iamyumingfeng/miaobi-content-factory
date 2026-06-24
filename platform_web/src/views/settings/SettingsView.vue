<template>
  <div class="settings-view">
    <h2 class="page-title">系统设置</h2>

    <el-row :gutter="20">
      <el-col :span="6">
        <div class="card">
          <el-menu
            :default-active="activeMenu"
            class="settings-menu"
            @select="handleMenuSelect"
          >
            <el-menu-item index="profile">
              <el-icon><User /></el-icon>
              <span>个人设置</span>
            </el-menu-item>
            <!-- 仅超级管理员和创作管理员可见模型平台配置 -->
            <el-menu-item v-if="!isSubUser" index="model">
              <el-icon><Setting /></el-icon>
              <span>模型平台配置</span>
            </el-menu-item>
            <!-- 仅超级管理员和创作管理员过期清理策略和通知设置 -->
            <!-- <el-menu-item v-if="isSuperAdmin" index="cleanup">
              <el-icon><Delete /></el-icon>
              <span>过期清理策略</span>
            </el-menu-item>-->
          </el-menu>
        </div>
      </el-col>

      <el-col :span="18">
        <div class="card">
          <div v-if="activeMenu === 'profile'" class="settings-panel">
            <h3 class="section-title">个人设置</h3>

            <el-divider content-position="left">个人信息</el-divider>
            <el-form label-width="120px" style="max-width: 450px;">
              <el-form-item label="当前用户名">
                <el-input v-model="profileForm.username" disabled />
              </el-form-item>
              <el-form-item label="自定义昵称">
                <el-input v-model="profileForm.nickname" placeholder="请输入自定义昵称" clearable />
              </el-form-item>
            </el-form>
            <div class="settings-actions">
              <el-button type="primary" @click="saveProfile">保存昵称</el-button>
            </div>

            <el-divider content-position="left" class="mt-lg">修改密码</el-divider>
            <el-form
              ref="passwordFormRef"
              :model="passwordForm"
              :rules="passwordRules"
              label-width="120px"
              style="max-width: 450px;"
            >
              <el-form-item label="原密码" prop="oldPassword">
                <el-input
                  v-model="passwordForm.oldPassword"
                  type="password"
                  placeholder="请输入原密码"
                  show-password
                />
              </el-form-item>
              <el-form-item label="新密码" prop="newPassword">
                <el-input
                  v-model="passwordForm.newPassword"
                  type="password"
                  placeholder="请输入新密码"
                  show-password
                />
              </el-form-item>
              <el-form-item label="确认新密码" prop="confirmPassword">
                <el-input
                  v-model="passwordForm.confirmPassword"
                  type="password"
                  placeholder="请再次输入新密码"
                  show-password
                />
              </el-form-item>
            </el-form>
            <div class="settings-actions">
              <el-button type="primary" @click="savePassword">修改密码</el-button>
            </div>
          </div>

          <div v-if="activeMenu === 'model'" class="settings-panel">
            <h3 class="section-title">模型平台配置</h3>

            <el-divider content-position="left">默认模型设置</el-divider>
            <el-form label-width="160px" style="max-width: 480px;">
              <el-form-item label="默认文本模型">
                <el-select v-model="defaultModels.text" style="width: 100%;" size="small" @change="saveDefaultModels">
                  <el-option label="自动选择" value="auto" />
                  <el-option v-for="model in getAllTextModels" :key="model.id" :label="getPlatformName(model.platform) + '/' + model.model_id" :value="model.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="默认图片模型">
                <el-select v-model="defaultModels.image" style="width: 100%;" size="small" @change="saveDefaultModels">
                  <el-option label="自动选择" value="auto" />
                  <el-option v-for="model in getAllImageModels" :key="model.id" :label="getPlatformName(model.platform) + '/' + model.model_id" :value="model.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="默认Embedding模型">
                <el-select v-model="defaultModels.embedding" style="width: 100%;" size="small" @change="saveDefaultModels">
                  <el-option label="自动选择" value="auto" />
                  <el-option v-for="model in getAllEmbeddingModels" :key="model.id" :label="getPlatformName(model.platform) + '/' + model.model_id" :value="model.id" />
                </el-select>
              </el-form-item>
            </el-form>

            <!-- 仅超级管理员可见模型平台配置部分 -->
            <el-tabs v-if="isSuperAdmin" v-model="activePlatform" class="platform-tabs">
              <el-tab-pane
                v-for="platform in platforms"
                :key="platform.id"
                :label="platform.name"
                :name="platform.id"
              >
                <div class="platform-content">
                  <el-collapse v-model="activeCollapse" class="model-collapse">
                    <el-collapse-item v-if="isModelTypeEnabled(platform.id, 'llm')" name="text">
                      <template #title>
                        <div class="collapse-header">
                          <span class="collapse-title">
                            <el-tag type="primary" size="small">文本模型</el-tag>
                            <span class="model-count">({{ getModelsByType(platform.id, 'llm').length }})</span>
                          </span>
                          <el-button type="primary" :icon="Plus" size="small" link @click.stop="showAddModelDialog(platform.id, 'llm')">
                            添加
                          </el-button>
                        </div>
                      </template>
                      <div class="model-list">
                        <el-table :data="getModelsByType(platform.id, 'llm')" style="width: 100%;" size="small">
                          <el-table-column prop="model_id" label="模型 ID" width="280" />
                          <el-table-column prop="base_url" label="API URL" show-overflow-tooltip />
                          <el-table-column prop="max_concurrency" label="并发 QPS" width="90" />
                          <el-table-column prop="status" label="状态" width="70">
                            <template #default="{ row }">
                              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                                {{ row.status === 'active' ? '启用' : '禁用' }}
                              </el-tag>
                            </template>
                          </el-table-column>
                          <el-table-column label="操作" width="180">
                            <template #default="{ row }">
                              <el-button type="primary" link size="small" @click.stop="editModel(platform.id, row)">编辑</el-button>
                              <el-button type="warning" link size="small" @click="toggleModelStatus(platform.id, row)">
                                {{ row.status === 'active' ? '禁用' : '启用' }}
                              </el-button>
                              <el-button type="danger" link size="small" @click="deleteModel(platform.id, row)">删除</el-button>
                            </template>
                          </el-table-column>
                        </el-table>
                      </div>
                    </el-collapse-item>

                    <el-collapse-item v-if="isModelTypeEnabled(platform.id, 'image')" name="image">
                      <template #title>
                        <div class="collapse-header">
                          <span class="collapse-title">
                            <el-tag type="success" size="small">图片模型</el-tag>
                            <span class="model-count">({{ getModelsByType(platform.id, 'image').length }})</span>
                          </span>
                          <el-button type="primary" :icon="Plus" size="small" link @click.stop="showAddModelDialog(platform.id, 'image')">
                            添加
                          </el-button>
                        </div>
                      </template>
                      <div class="model-list">
                        <el-table :data="getModelsByType(platform.id, 'image')" style="width: 100%;" size="small">
                          <el-table-column prop="model_id" label="模型 ID" width="280" />
                          <el-table-column prop="base_url" label="API URL" show-overflow-tooltip />
                          <el-table-column prop="max_concurrency" label="并发 QPS" width="90" />
                          <el-table-column prop="status" label="状态" width="70">
                            <template #default="{ row }">
                              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                                {{ row.status === 'active' ? '启用' : '禁用' }}
                              </el-tag>
                            </template>
                          </el-table-column>
                          <el-table-column label="操作" width="180">
                            <template #default="{ row }">
                              <el-button type="primary" link size="small" @click.stop="editModel(platform.id, row)">编辑</el-button>
                              <el-button type="warning" link size="small" @click="toggleModelStatus(platform.id, row)">
                                {{ row.status === 'active' ? '禁用' : '启用' }}
                              </el-button>
                              <el-button type="danger" link size="small" @click="deleteModel(platform.id, row)">删除</el-button>
                            </template>
                          </el-table-column>
                        </el-table>
                      </div>
                    </el-collapse-item>

                    <el-collapse-item v-if="isModelTypeEnabled(platform.id, 'video')" name="video">
                      <template #title>
                        <div class="collapse-header">
                          <span class="collapse-title">
                            <el-tag type="warning" size="small">视频模型</el-tag>
                            <span class="model-count">({{ getModelsByType(platform.id, 'video').length }})</span>
                          </span>
                          <el-button type="primary" :icon="Plus" size="small" link @click.stop="showAddModelDialog(platform.id, 'video')">
                            添加
                          </el-button>
                        </div>
                      </template>
                      <div class="model-list">
                        <el-table :data="getModelsByType(platform.id, 'video')" style="width: 100%;" size="small">
                          <el-table-column prop="model_id" label="模型 ID" width="280" />
                          <el-table-column prop="base_url" label="API URL" show-overflow-tooltip />
                          <el-table-column prop="max_concurrency" label="并发 QPS" width="90" />
                          <el-table-column prop="status" label="状态" width="70">
                            <template #default="{ row }">
                              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                                {{ row.status === 'active' ? '启用' : '禁用' }}
                              </el-tag>
                            </template>
                          </el-table-column>
                          <el-table-column label="操作" width="180">
                            <template #default="{ row }">
                              <el-button type="primary" link size="small" @click.stop="editModel(platform.id, row)">编辑</el-button>
                              <el-button type="warning" link size="small" @click="toggleModelStatus(platform.id, row)">
                                {{ row.status === 'active' ? '禁用' : '启用' }}
                              </el-button>
                              <el-button type="danger" link size="small" @click="deleteModel(platform.id, row)">删除</el-button>
                            </template>
                          </el-table-column>
                        </el-table>
                      </div>
                    </el-collapse-item>

                    <el-collapse-item v-if="isModelTypeEnabled(platform.id, 'embedding')" name="embedding">
                      <template #title>
                        <div class="collapse-header">
                          <span class="collapse-title">
                            <el-tag type="info" size="small">Embedding 模型</el-tag>
                            <span class="model-count">({{ getModelsByType(platform.id, 'embedding').length }})</span>
                          </span>
                          <el-button type="primary" :icon="Plus" size="small" link @click.stop="showAddModelDialog(platform.id, 'embedding')">
                            添加
                          </el-button>
                        </div>
                      </template>
                      <div class="model-list">
                        <el-table :data="getModelsByType(platform.id, 'embedding')" style="width: 100%;" size="small">
                          <el-table-column prop="model_id" label="模型 ID" width="280" />
                          <el-table-column prop="base_url" label="API URL" show-overflow-tooltip />
                          <el-table-column prop="max_concurrency" label="并发 QPS" width="90" />
                          <el-table-column prop="status" label="状态" width="70">
                            <template #default="{ row }">
                              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                                {{ row.status === 'active' ? '启用' : '禁用' }}
                              </el-tag>
                            </template>
                          </el-table-column>
                          <el-table-column label="操作" width="180">
                            <template #default="{ row }">
                              <el-button type="primary" link size="small" @click.stop="editModel(platform.id, row)">编辑</el-button>
                              <el-button type="warning" link size="small" @click="toggleModelStatus(platform.id, row)">
                                {{ row.status === 'active' ? '禁用' : '启用' }}
                              </el-button>
                              <el-button type="danger" link size="small" @click="deleteModel(platform.id, row)">删除</el-button>
                            </template>
                          </el-table-column>
                        </el-table>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>

          <div v-if="activeMenu === 'cleanup'" class="settings-panel">
            <h3 class="section-title">过期清理策略</h3>
            <el-alert
              title="配置自动清理规则，系统将定期清理过期的生成内容以节省存储空间"
              type="info"
              :closable="false"
              class="mb-md"
            />
            <el-form label-width="160px" style="max-width: 500px;">
              <el-form-item label="启用自动清理">
                <el-switch v-model="cleanup.enabled" />
              </el-form-item>
              <el-form-item label="内容保留期">
                <el-select v-model="cleanup.retentionPeriod" style="width: 200px;">
                  <el-option label="7 天" :value="7" />
                  <el-option label="15 天" :value="15" />
                  <el-option label="30 天" :value="30" />
                  <el-option label="60 天" :value="60" />
                  <el-option label="90 天" :value="90" />
                </el-select>
              </el-form-item>
              <el-form-item label="清理前提醒">
                <el-switch v-model="cleanup.notifyBeforeCleanup" />
              </el-form-item>
            </el-form>
            <div class="settings-actions mt-lg">
              <el-button type="primary" @click="saveCleanupSettings">保存配置</el-button>
              <el-button type="warning" @click="triggerCleanup">立即清理</el-button>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-dialog v-model="showModelDialog" :title="isEditModel ? '编辑模型' : '添加模型'" width="500px">
      <el-form :model="modelForm" label-width="120px">
        <el-form-item label="模型类型">
          <el-tag :type="getModelTypeTag(modelForm.model_type)" size="small">
            {{ getModelTypeLabel(modelForm.model_type) }}
          </el-tag>
        </el-form-item>
        <el-form-item label="模型 ID" required>
          <el-input v-model="modelForm.model_id" placeholder="请输入模型 ID" />
        </el-form-item>
        <el-form-item label="模型名称" required>
          <el-input v-model="modelForm.model_name" placeholder="请输入模型名称" />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="modelForm.base_url" placeholder="请输入 Base URL" />
        </el-form-item>
        <!-- 可灵平台：使用 AccessKey + SecretKey 动态生成 JWT Token -->
        <template v-if="modelForm.platform === 'kling'">
          <el-form-item label="Access Key ID" required>
            <el-input v-model="modelForm.access_key_id" type="password" placeholder="请输入可灵 Access Key ID" show-password />
          </el-form-item>
          <el-form-item label="Access Key Secret" required>
            <el-input v-model="modelForm.access_key_secret" type="password" placeholder="请输入可灵 Access Key Secret" show-password />
            <div class="form-tip">可灵 API 使用动态 JWT Token 认证，每次请求自动生成并缓存（30分钟有效期）</div>
          </el-form-item>
        </template>
        <!-- 即梦AI平台：使用火山引擎签名认证（AccessKey + SecretKey） -->
        <template v-else-if="modelForm.platform === 'jimeng'">
          <el-form-item label="Access Key ID" required>
            <el-input v-model="modelForm.access_key" type="password" placeholder="请输入即梦 Access Key ID" show-password />
          </el-form-item>
          <el-form-item label="Access Key Secret" required>
            <el-input v-model="modelForm.secret_key" type="password" placeholder="请输入即梦 Access Key Secret" show-password />
            <div class="form-tip">即梦 API 使用火山引擎 HMAC-SHA256 签名认证，每次请求自动签名</div>
          </el-form-item>
        </template>
        <!-- 其他平台：使用静态 API Key -->
        <template v-else>
          <el-form-item label="API Key">
            <el-input v-model="modelForm.api_key" type="password" placeholder="请输入 API Key" show-password />
          </el-form-item>
        </template>
        <el-form-item label="并发 QPS" required>
          <el-input-number v-model="modelForm.max_concurrency" :min="1" :max="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showModelDialog = false">取消</el-button>
        <el-button type="primary" :loading="modelLoading" @click="saveModel">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Setting, Delete, Plus, User } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { apiClient, type ModelConfig } from '@/api/types'

const router = useRouter()
const authStore = useAuthStore()
const activeMenu = ref('profile')
const passwordFormRef = ref()

const isSuperAdmin = computed(() => authStore.userRole === 'super_admin')
const isSubUser = computed(() => authStore.userRole === 'sub_user')

const profileForm = reactive({
  username: '',
  nickname: ''
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirmPassword = (_rule: any, value: any, callback: any) => {
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const saveProfile = async () => {
  try {
    await apiClient.updateDisplayName(profileForm.nickname || '')
    authStore.updateUser({ display_name: profileForm.nickname || null })
    ElMessage.success('昵称保存成功')
  } catch (error: any) {
    console.error('保存昵称失败:', error)
    ElMessage.error(error.message || '保存昵称失败')
  }
}

const savePassword = async () => {
  if (!passwordFormRef.value) return
  await passwordFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      try {
        await apiClient.changePassword(passwordForm.oldPassword, passwordForm.newPassword)
        ElMessage.success('密码修改成功，请重新登录')
        Object.assign(passwordForm, { oldPassword: '', newPassword: '', confirmPassword: '' })

        setTimeout(async () => {
          await authStore.logout()
          router.replace('/login')
        }, 1500)
      } catch (error: any) {
        ElMessage.error(error.message || '密码修改失败，请检查原密码是否正确')
      }
    }
  })
}

// 初始化用户信息
onMounted(() => {
  if (authStore.user) {
    profileForm.username = authStore.user.userid
    profileForm.nickname = authStore.user.display_name || authStore.user.nickname || ''
  }
  // 权限检查，确保当前激活的菜单项有权限访问
  if (activeMenu.value === 'model' && isSubUser.value) {
    activeMenu.value = 'profile'
  } else if (activeMenu.value === 'cleanup' && !isSuperAdmin.value) {
    activeMenu.value = 'profile'
  }
  loadModelConfigs()
})

// ==================== 模型平台配置 ====================

const activePlatform = ref('bailian')
const activeCollapse = ref<string[]>([])
const showModelDialog = ref(false)
const isEditModel = ref(false)
const editingPlatform = ref('')
const editingModelId = ref<number | null>(null)
const modelLoading = ref(false)

// 平台模型类型配置（从后端 API 动态加载，无需前端硬编码）
const platformModelTypes = ref<Record<string, string[]>>({})

// 动态生成平台列表（从 API 响应 platformModelTypes 提取，直接用 ID 作为显示名）
const platforms = computed(() => {
  const types = platformModelTypes.value || {}
  return Object.keys(types).map(id => ({
    id,
    name: id  // 直接用平台 ID 作为显示名
  }))
})

// 获取平台启用的模型类型
const getEnabledModelTypes = (platformId: string): string[] => {
  return platformModelTypes.value[platformId] || []
}

// 检查平台是否启用指定模型类型
const isModelTypeEnabled = (platformId: string, modelType: 'llm' | 'image' | 'video' | 'embedding'): boolean => {
  const enabledTypes = getEnabledModelTypes(platformId)
  return enabledTypes.includes(modelType)
}

const defaultModels = reactive({
  text: 'auto' as string | number,
  image: 'auto' as string | number,
  video: 'auto' as string | number,
  embedding: 'auto' as string | number
})

const modelConfigs = ref<ModelConfig[]>([])

const modelForm = reactive({
  platform: '',
  model_id: '',
  model_name: '',
  base_url: '',
  api_key: '',
  // 可灵平台专用：AccessKey + SecretKey（用于动态 JWT Token）
  access_key_id: '',
  access_key_secret: '',
  // 即梦AI平台专用：AccessKey + SecretKey（用于火山引擎签名认证）
  access_key: '',
  secret_key: '',
  max_concurrency: 5,
  model_type: 'llm' as 'llm' | 'image' | 'video' | 'embedding',
  is_default: false,
  status: 'active' as 'active' | 'inactive'
})

const loadModelConfigs = async () => {
  try {
    const configs = await apiClient.getModelConfigs()
    modelConfigs.value = configs || []

    // 加载平台模型类型配置
    const types = await apiClient.getPlatformModelTypes()
    platformModelTypes.value = (types?.platform_types || {}) as Record<string, string[]>

    // 加载用户默认模型设置
    const userDefaults = await apiClient.getUserDefaultModels()
    defaultModels.text = userDefaults.llm_model_config_id || 'auto'
    defaultModels.image = userDefaults.image_model_config_id || 'auto'
    defaultModels.video = userDefaults.video_model_config_id || 'auto'
    defaultModels.embedding = userDefaults.embedding_model_config_id || 'auto'
  } catch (error: any) {
    console.error('加载模型配置失败:', error)
  }
}

const getPlatformName = (platformId: string): string => {
  return platformId  // 直接用平台 ID 作为显示名
}

const saveDefaultModels = async () => {
  try {
    const updateData = {
      llm_model_config_id: defaultModels.text === 'auto' ? null : defaultModels.text as number,
      image_model_config_id: defaultModels.image === 'auto' ? null : defaultModels.image as number,
      video_model_config_id: defaultModels.video === 'auto' ? null : defaultModels.video as number,
      embedding_model_config_id: defaultModels.embedding === 'auto' ? null : defaultModels.embedding as number
    }
    await apiClient.updateUserDefaultModels(updateData)
    ElMessage.success('默认模型设置已保存')
  } catch (error: any) {
    console.error('保存默认模型失败:', error)
    ElMessage.error(error.message || '保存失败')
  }
}

const getAllTextModels = computed(() => {
  return modelConfigs.value.filter(m => m.model_type === 'llm')
})

const getAllImageModels = computed(() => {
  return modelConfigs.value.filter(m => m.model_type === 'image')
})

const getAllVideoModels = computed(() => {
  return modelConfigs.value.filter(m => m.model_type === 'video')
})

const getAllEmbeddingModels = computed(() => {
  return modelConfigs.value.filter(m => m.model_type === 'embedding')
})

const handleMenuSelect = (key: string) => {
  // 权限验证
  if (key === 'model' && isSubUser.value) {
    ElMessage.warning('您没有权限访问此页面')
    activeMenu.value = 'profile'
    return
  }
  if ((key === 'cleanup') && !isSuperAdmin.value) {
    ElMessage.warning('您没有权限访问此页面')
    activeMenu.value = 'profile'
    return
  }
  activeMenu.value = key
}

const getModelsByType = (platformId: string, modelType: 'llm' | 'image' | 'video' | 'embedding') => {
  return modelConfigs.value.filter(m => m.platform === platformId && m.model_type === modelType)
}

const showAddModelDialog = (platformId: string, modelType: 'llm' | 'image' | 'video' | 'embedding') => {
  isEditModel.value = false
  editingPlatform.value = platformId
  editingModelId.value = null

  // 完全重置所有字段，避免不同平台之间的字段污染
  modelForm.platform = platformId
  modelForm.model_id = ''
  modelForm.model_name = ''
  modelForm.base_url = ''
  modelForm.api_key = ''
  modelForm.access_key_id = ''
  modelForm.access_key_secret = ''
  modelForm.access_key = ''
  modelForm.secret_key = ''
  modelForm.max_concurrency = 5
  modelForm.model_type = modelType
  modelForm.is_default = false
  modelForm.status = 'active'

  showModelDialog.value = true
}

const editModel = (platformId: string, model: ModelConfig) => {
  isEditModel.value = true
  editingPlatform.value = platformId
  editingModelId.value = model.id
  const cj = model.config_json || {}

  // 先完全重置所有字段，避免不同平台之间的字段污染
  modelForm.platform = model.platform
  modelForm.model_id = model.model_id
  modelForm.model_name = model.model_name
  modelForm.base_url = model.base_url || ''
  modelForm.api_key = ''
  modelForm.access_key_id = ''
  modelForm.access_key_secret = ''
  modelForm.access_key = ''
  modelForm.secret_key = ''

  // 根据平台类型设置相应的认证字段
  if (model.platform === 'kling') {
    modelForm.access_key_id = cj.access_key_id || ''
    modelForm.access_key_secret = cj.access_key_secret || ''
  } else if (model.platform === 'jimeng') {
    modelForm.access_key = cj.access_key || ''
    modelForm.secret_key = cj.secret_key || ''
  } else {
    modelForm.api_key = cj.api_key || ''
  }

  modelForm.max_concurrency = model.max_concurrency
  modelForm.model_type = model.model_type
  modelForm.is_default = model.is_default
  modelForm.status = model.status

  showModelDialog.value = true
}

const saveModel = async () => {
  if (!modelForm.model_id || !modelForm.model_name) {
    ElMessage.warning('请填写完整信息')
    return
  }

  modelLoading.value = true
  try {
    // 构建认证配置：可灵/即梦使用 AccessKey+SecretKey，其他平台使用 API Key
    let configJson: Record<string, string> | undefined
    if (modelForm.platform === 'kling') {
      configJson = {
        access_key_id: modelForm.access_key_id || '',
        access_key_secret: modelForm.access_key_secret || ''
      }
    } else if (modelForm.platform === 'jimeng') {
      configJson = {
        access_key: modelForm.access_key || '',
        secret_key: modelForm.secret_key || ''
      }
    } else {
      // 始终保存 api_key，即使为空（确保更新数据库）
      configJson = { api_key: modelForm.api_key || '' }
    }

    const configData = {
      platform: modelForm.platform,
      model_id: modelForm.model_id,
      model_name: modelForm.model_name,
      model_type: modelForm.model_type,
      base_url: modelForm.base_url || undefined,
      api_endpoint: undefined,
      is_default: modelForm.is_default,
      max_concurrency: modelForm.max_concurrency,
      config_json: configJson,
      status: modelForm.status
    }

    // 可灵平台校验 AccessKey
    if (modelForm.platform === 'kling' && (!modelForm.access_key_id || !modelForm.access_key_secret)) {
      ElMessage.warning('请填写可灵平台的 Access Key ID 和 Secret')
      modelLoading.value = false
      return
    }

    // 即梦AI平台校验 AccessKey
    if (modelForm.platform === 'jimeng' && (!modelForm.access_key || !modelForm.secret_key)) {
      ElMessage.warning('请填写即梦平台的 Access Key ID 和 Secret')
      modelLoading.value = false
      return
    }

    if (isEditModel.value && editingModelId.value) {
      const updatedConfig = await apiClient.updateModelConfig(editingModelId.value, configData)
      const index = modelConfigs.value.findIndex(m => m.id === editingModelId.value)
      if (index > -1) {
        modelConfigs.value[index] = updatedConfig
      }
      ElMessage.success('模型更新成功')
    } else {
      const created = await apiClient.createModelConfig(configData)
      modelConfigs.value.push(created)
      ElMessage.success('模型添加成功')
    }
    showModelDialog.value = false
  } catch (error: any) {
    console.error('保存模型失败:', error)
    ElMessage.error(error.message || '保存失败')
  } finally {
    modelLoading.value = false
  }
}

const toggleModelStatus = async (_platformId: string, model: ModelConfig) => {
  try {
    const newStatus = model.status === 'active' ? 'inactive' : 'active'
    await apiClient.updateModelConfig(model.id, { status: newStatus })
    const index = modelConfigs.value.findIndex(m => m.id === model.id)
    if (index > -1) {
      modelConfigs.value[index].status = newStatus
    }
    ElMessage.success(newStatus === 'active' ? '已启用' : '已禁用')
  } catch (error: any) {
    console.error('切换状态失败:', error)
    ElMessage.error(error.message || '操作失败')
  }
}

const deleteModel = async (_platformId: string, model: ModelConfig) => {
  try {
    await ElMessageBox.confirm('确定要删除这个模型吗？', '提示', { type: 'warning' })
    await apiClient.deleteModelConfig(model.id)
    const index = modelConfigs.value.findIndex(m => m.id === model.id)
    if (index > -1) {
      modelConfigs.value.splice(index, 1)
    }
    ElMessage.success('删除成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(error.message || '删除失败')
    }
  }
}

const getModelTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    llm: '文本模型',
    image: '图片模型',
    video: '视频模型',
    embedding: 'Embedding 模型'
  }
  return labels[type] || type
}

const getModelTypeTag = (type: string) => {
  const tags: Record<string, string> = {
    llm: 'primary',
    image: 'success',
    video: 'warning',
    embedding: 'info'
  }
  return tags[type] || 'info'
}

const cleanup = reactive({
  enabled: true,
  retentionPeriod: 30,
  notifyBeforeCleanup: true
})

const saveCleanupSettings = () => {
  ElMessage.success('清理策略保存成功')
}

const triggerCleanup = async () => {
  try {
    await ElMessageBox.confirm('确定要立即执行清理操作吗？这将删除所有过期的生成内容。', '确认清理', {
      type: 'warning',
      confirmButtonText: '确定清理',
      cancelButtonText: '取消'
    })
    ElMessage.success('清理任务已提交')
  } catch {
  }
}
</script>

<style lang="scss" scoped>
@import './settings.scss';

.settings-view {
  padding: 0;
}

.mb-md {
  margin-bottom: 16px;
}

.mt-lg {
  margin-top: 24px;
}

.form-tip {
  font-size: 12px;
  color: var(--color-text-muted);
  line-height: 1.5;
  margin-top: 6px;
  padding-left: 2px;
}

// section-title 已在 settings.scss 统一定义（带装饰线）
.section-title { /* 使用 settings.scss */ }

.platform-tabs {
  // 使用 settings.scss 统一优化（tabs 渐变下划线等）
}

.platform-content {
  min-height: 300px;
}

.model-collapse {
  :deep(.el-collapse-item__header) {
    padding: 6px 10px;
    height: 36px;
    line-height: 36px;
    background: transparent;
    border-bottom: 1px solid var(--color-border-default);
    border-radius: var(--radius-md);
    font-weight: 500;
    font-size: 13px;
    color: var(--color-text-primary);
    transition: background-color var(--transition-fast);

    &:hover {
      background: var(--color-bg-tertiary);
    }

    .el-collapse-item__arrow {
      color: var(--color-text-secondary);
      font-size: 14px;
      margin-right: 0;
    }
  }

  :deep(.el-collapse-item__wrap) {
    background: transparent;
    border: none;
    padding: 0 8px;
  }

  :deep(.el-collapse-item__content) {
    padding: 8px 0;
  }
}

.collapse-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.collapse-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-count {
  color: var(--color-text-secondary);
  font-size: 13px;
  font-weight: 400;
}

.settings-menu {
  border: none;
}

:deep(.settings-menu) {
  background-color: transparent !important;
  border-radius: 10px !important;
  padding: 4px !important;
}

:deep(.settings-menu .el-menu-item) {
  // 已迁移至 settings.scss
}

:deep(.settings-menu .el-menu-item:hover) {
  background-color: rgba(64, 158, 255, 0.1) !important;
  color: var(--color-primary) !important;
}

:deep(.settings-menu .el-menu-item.is-active) {
  background-color: var(--color-primary) !important;
  color: #ffffff !important;
}

:deep(.settings-menu .el-menu-item .el-icon) {
  color: var(--text-secondary) !important;
}

:deep(.settings-menu .el-menu-item.is-active .el-icon) {
  color: #ffffff !important;
}

:deep(.settings-menu .el-menu-item:hover .el-icon) {
  color: var(--color-primary) !important;
}

.model-list {
  :deep(.el-table) {
    font-size: 13px;
  }
}

.settings-actions {
  display: flex;
  gap: 12px;
}
</style>
