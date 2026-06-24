// 妙笔内容工场 - TypeScript类型定义和API客户端 (适配后端版本)

// ==================== 通用类型定义 ====================

// 后端响应格式
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

export interface PaginationParams {
  page?: number
  page_size?: number
}

export interface PaginationResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  total_pages: number
}

// ==================== 用户相关类型 ====================

export type UserRole = 'super_admin' | 'operator' | 'sub_user'

export type UserStatus = 'online' | 'offline' | 'disabled'

export interface User {
  id: number
  userid: string
  nickname: string
  role: UserRole
  wechat_openid?: string
  wechat_unionid?: string
  status: UserStatus
  user_positioning?: string
  user_category?: string
  content_style?: string
  account_type?: string
  created_by?: number
  managed_by?: number
  owner_admin_id?: number
  created_at: string
  updated_at: string
}

export interface UserTag {
  id: number
  name: string
  tag_type: 'operator_tag' | 'subuser_tag'
  description?: string
  color?: string
  created_by: number
  created_at: string
  updated_at: string
}

// ==================== 模板相关类型 ====================

export type ContentType = 'text' | 'image_text' | 'video_text'

export interface Template {
  id: number
  name: string
  description?: string
  content_type: ContentType
  prompt_template: string
  variables_json: any
  style_reference?: string
  platform_rules_json?: any
  status: 'enabled' | 'disabled'
  platform_id: number
  original_template_id?: number
  created_by: number
  owner_admin_id: number
  created_at: string
  updated_at: string
  tags?: TemplateTag[]
  platform?: TemplatePlatform
}

export interface TemplatePlatform {
  id: number
  name: string
  description?: string
  color?: string
  sort_order: number
  created_by: number
  owner_admin_id: number
  status: 'active' | 'inactive'
  template_count?: number
  created_at: string
  updated_at: string
}

export interface TemplateTag {
  id: number
  name: string
  description?: string
  color?: string
  created_by: number
  created_at: string
  updated_at: string
  template_count?: number
}

export interface TemplateListItem {
  id: number
  name: string
  description?: string
  content_type: ContentType
  platform: {
    id: number
    name: string
    color?: string
  }
  tags: Array<{
    id: number
    name: string
    color?: string
  }>
  status: 'enabled' | 'disabled'
  usage_count?: number
  created_at: string
  updated_at: string
}

// ==================== 素材相关类型 ====================

export interface MaterialCategory {
  id: number
  name: string
  description?: string
  color?: string
  sort_order: number
  created_by: number
  owner_admin_id: number
  status: 'active' | 'inactive'
  material_count?: number
  created_at: string
  updated_at: string
}

export interface MaterialTag {
  id: number
  name: string
  description?: string
  color?: string
  created_by: number
  owner_admin_id: number
  created_at: string
  updated_at: string
  material_count?: number
}

export interface MaterialAttachment {
  id: number
  material_id: number
  file_type: 'image' | 'video'
  file_url: string
  file_name: string
  file_size: number
  sort_order: number
  width?: number
  height?: number
  duration?: number
  thumbnail_url?: string
  created_at: string
  updated_at: string
}

export interface Material {
  id: number
  title: string
  text_content?: string
  source_url?: string
  source_type: 'upload' | 'link' | 'description'
  content_type: ContentType | 'mix'
  category_id?: number
  category?: MaterialCategory
  image_count: number
  video_count: number
  status: 'available' | 'disabled'
  is_favorite?: boolean
  created_by: number
  owner_admin_id: number
  original_material_id?: number
  created_at: string
  updated_at: string
  attachments?: MaterialAttachment[]
  tags?: MaterialTag[]
}

export interface MaterialListItem {
  id: number
  title: string
  content_type: ContentType | 'mix'
  category?: {
    id: number
    name: string
    color?: string
  }
  tags: Array<{
    id: number
    name: string
    color?: string
  }>
  image_count: number
  video_count: number
  status: 'available' | 'disabled'
  is_favorite: boolean
  usage_count?: number
  created_at: string
  updated_at: string
}

// ==================== 内容生成相关类型 ====================

export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'

export type ItemStatus = 'queued' | 'generating' | 'completed' | 'failed' | 'paused'

export type ModelSelectionMode = 'auto' | 'manual'

export interface GenerationTask {
  id: number
  material_id: number
  model_platform?: string
  model_id?: string
  model_selection_mode: ModelSelectionMode
  max_concurrency?: number
  variable_values_json?: any
  dedup_rules_json?: any
  status: TaskStatus
  total_count: number
  queued_count: number
  generating_count: number
  completed_count: number
  failed_count: number
  paused_count: number
  distributed_count: number
  pending_publish_count: number
  published_count: number
  created_by: number
  owner_admin_id: number
  created_at: string
  updated_at: string
}

export interface GenerationTaskListItem {
  id: number
  material: {
    id: number
    title: string
  }
  status: TaskStatus
  total_count: number
  queued_count: number
  generating_count: number
  completed_count: number
  failed_count: number
  paused_count: number
  distributed_count: number
  pending_publish_count: number
  published_count: number
  created_at: string
  updated_at: string
}

export interface GenerationItem {
  id: number
  task_id: number
  sub_user_id: number
  template_id: number
  model_platform?: string
  model_id?: string
  generated_title?: string
  generated_text?: string
  generated_image_urls_json?: any
  generated_video_url?: string
  status: ItemStatus
  retry_count: number
  error_message?: string
  queued_at?: string
  started_at?: string
  completed_at?: string
  distribution_status?: 'draft' | 'ready' | 'distributed'
  distributed_at?: string
  confirmed_at?: string
  owner_admin_id: number
  created_at: string
  updated_at: string
}

export interface GenerationProgressLog {
  id: number
  task_id: number
  queued_count: number
  generating_count: number
  completed_count: number
  failed_count: number
  paused_count: number
  status: TaskStatus
  progress_message?: string
  created_at: string
}

export interface CreateGenerationTaskRequest {
  material_id: number
  template_ids: number[]
  model_selection_mode?: ModelSelectionMode
  model_platform?: string
  model_id?: string
  max_concurrency?: number
  variable_values_json?: any
  dedup_rules_json?: any
  sub_user_ids: number[]
}

// ==================== 微信登录相关类型 ====================

export interface LoginRequest {
  userid: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: UserInfo
}

export interface UserInfo {
  id: number
  userid: string
  nickname?: string
  display_name?: string
  role: string
  wechat_bound: boolean
}

export interface WechatQRResponse {
  qr_url: string
  state: string
  expires_in: number
}

export interface WechatQRStatusResponse {
  status: 'pending' | 'scanned' | 'confirmed'
  action?: 'login' | 'bind_required'
  bind_token?: string
  wechat_info?: {
    openid: string
    unionid?: string
    nickname?: string
    avatar?: string
  }
  access_token?: string
  token_type?: string
  expires_in?: number
  user?: UserInfo
}

export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

export interface UpdateDisplayNameRequest {
  display_name: string
}

// ==================== API客户端 ====================

export class ApiClient {
  private baseUrl: string
  private token: string | null

  constructor(baseUrl: string = '/api/v1') {
    this.baseUrl = baseUrl
    this.token = localStorage.getItem('access_token')
  }

  setToken(token: string) {
    this.token = token
    localStorage.setItem('access_token', token)
  }

  clearToken() {
    this.token = null
    localStorage.removeItem('access_token')
  }

  private async request<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    endpoint: string,
    data?: any,
    params?: Record<string, any>
  ): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    let url = `${this.baseUrl}${endpoint}`

    if (params) {
      const searchParams = new URLSearchParams()
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value))
        }
      })
      const queryString = searchParams.toString()
      if (queryString) {
        url += `?${queryString}`
      }
    }

    const config: RequestInit = {
      method,
      headers,
      credentials: 'include'
    }

    if (data && method !== 'GET') {
      config.body = JSON.stringify(data)
    }

    try {
      const response = await fetch(url, config)
      const result: ApiResponse<T> = await response.json()

      if (!result.success) {
        throw new Error(result.message || result.error || '请求失败')
      }

      return result.data as T
    } catch (error) {
      console.error('API请求失败:', error)
      throw error
    }
  }

  // ==================== 认证接口 ====================

  async login(userid: string, password: string) {
    return this.request<LoginResponse>('POST', '/auth/login', { userid, password })
  }

  async logout() {
    return this.request('POST', '/auth/logout')
  }

  async getWechatQr() {
    return this.request<WechatQRResponse>('GET', '/auth/wechat/qr')
  }

  async checkWechatQrStatus(state: string) {
    return this.request<WechatQRStatusResponse>('GET', `/auth/wechat/qr/${state}`)
  }

  async changePassword(oldPassword: string, newPassword: string) {
    return this.request('POST', '/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword
    })
  }

  async updateDisplayName(displayName: string) {
    return this.request('POST', '/auth/update-display-name', {
      display_name: displayName
    })
  }

  // ==================== 用户管理接口 ====================

  async getSuperAdmins(params?: PaginationParams & { keyword?: string; status?: string }) {
    return this.request<PaginationResponse<User>>('GET', '/users/super-admins', undefined, params)
  }

  async createSuperAdmin(data: {
    userid?: string
    nickname: string
    password: string
    user_positioning?: string
    tag_ids?: number[]
  }) {
    return this.request<User>('POST', '/users/super-admins', data)
  }

  async getOperators(params?: PaginationParams & { keyword?: string; status?: string }) {
    return this.request<PaginationResponse<User>>('GET', '/users/operators', undefined, params)
  }

  async createOperator(data: {
    userid?: string
    nickname: string
    password: string
    display_name?: string
    user_positioning?: string
    user_category?: string
  }) {
    return this.request<User>('POST', '/users/operators', data)
  }

  async getOperator(id: number) {
    return this.request<User>('GET', `/users/operators/${id}`)
  }

  async updateOperator(id: number, data: any) {
    return this.request<User>('PUT', `/users/operators/${id}`, data)
  }

  async getSubUsers(params?: PaginationParams & {
    keyword?: string
    tag_id?: number
    status?: string
  }) {
    return this.request<PaginationResponse<User>>('GET', '/users/sub-users', undefined, params)
  }

  async createSubUser(data: {
    userid?: string
    nickname: string
    password?: string
    display_name?: string
    user_positioning?: string
    user_category?: string
    content_style?: string
    account_type?: string
    tag_ids?: number[]
  }) {
    return this.request<User>('POST', '/users/sub-users', data)
  }

  async getSubUser(id: number) {
    return this.request<User>('GET', `/users/sub-users/${id}`)
  }

  async getUserTags(params?: { tag_type?: 'operator_tag' | 'subuser_tag' }) {
    return this.request<UserTag[]>('GET', '/users/tags', undefined, params)
  }

  async createUserTag(data: {
    name: string
    tag_type: 'operator_tag' | 'subuser_tag'
    description?: string
    color?: string
  }) {
    return this.request<UserTag>('POST', '/users/tags', data)
  }

  // ==================== 模板管理接口 ====================

  async getTemplates(params?: PaginationParams & {
    keyword?: string
    platform_id?: number
    tag_ids?: string
    content_type?: ContentType
    status?: 'enabled' | 'disabled'
  }) {
    return this.request<PaginationResponse<Template>>('GET', '/templates', undefined, params)
  }

  async getTemplate(id: number) {
    return this.request<Template>('GET', `/templates/${id}`)
  }

  async createTemplate(data: {
    name: string
    description?: string
    content_type: ContentType
    platform_id: number
    prompt_template: string
    variables_json: any
    style_reference?: string
    platform_rules_json?: any
    tag_ids?: number[]
  }) {
    return this.request<Template>('POST', '/templates', data)
  }

  async updateTemplate(id: number, data: any) {
    return this.request<Template>('PUT', `/templates/${id}`, data)
  }

  async deleteTemplate(id: number) {
    return this.request('DELETE', `/templates/${id}`)
  }

  async copyTemplate(id: number, data?: { name?: string }) {
    return this.request<Template>('POST', `/templates/${id}/copy`, data)
  }

  async getTemplatePlatforms() {
    return this.request<TemplatePlatform[]>('GET', '/templates/platforms')
  }

  async createTemplatePlatform(data: {
    name: string
    description?: string
    color?: string
    sort_order?: number
  }) {
    return this.request<TemplatePlatform>('POST', '/templates/platforms', data)
  }

  async getTemplateTags() {
    return this.request<TemplateTag[]>('GET', '/templates/tags')
  }

  async createTemplateTag(data: {
    name: string
    description?: string
    color?: string
  }) {
    return this.request<TemplateTag>('POST', '/templates/tags', data)
  }

  // ==================== 素材管理接口 ====================

  async getMaterials(params?: PaginationParams & {
    keyword?: string
    category_id?: number
    tag_ids?: string
    content_type?: ContentType | 'mix'
    status?: 'available' | 'disabled'
    favorite?: boolean
  }) {
    return this.request<PaginationResponse<Material>>('GET', '/materials', undefined, params)
  }

  async getMaterial(id: number) {
    return this.request<Material>('GET', `/materials/${id}`)
  }

  async createMaterial(data: FormData) {
    const headers: Record<string, string> = {}
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    const response = await fetch(`${this.baseUrl}/materials`, {
      method: 'POST',
      headers,
      body: data,
      credentials: 'include'
    })
    const result: ApiResponse<Material> = await response.json()

    if (!result.success) {
      throw new Error(result.message || result.error || '请求失败')
    }

    return result.data as Material
  }

  async updateMaterial(id: number, data: FormData | any) {
    if (data instanceof FormData) {
      const headers: Record<string, string> = {}
      if (this.token) {
        headers['Authorization'] = `Bearer ${this.token}`
      }

      const response = await fetch(`${this.baseUrl}/materials/${id}`, {
        method: 'PUT',
        headers,
        body: data,
        credentials: 'include'
      })
      const result: ApiResponse<Material> = await response.json()

      if (!result.success) {
        throw new Error(result.message || result.error || '请求失败')
      }

      return result.data as Material
    } else {
      return this.request<Material>('PUT', `/materials/${id}`, data)
    }
  }

  async deleteMaterial(id: number) {
    return this.request('DELETE', `/materials/${id}`)
  }

  async copyMaterial(id: number, data?: { title?: string }) {
    return this.request<Material>('POST', `/materials/${id}/copy`, data)
  }

  async favoriteMaterial(id: number) {
    return this.request<{ is_favorite: boolean }>('POST', `/materials/${id}/favorite`)
  }

  async getMaterialCategories() {
    return this.request<MaterialCategory[]>('GET', '/materials/categories')
  }

  async createMaterialCategory(data: {
    name: string
    description?: string
    color?: string
    sort_order?: number
  }) {
    return this.request<MaterialCategory>('POST', '/materials/categories', data)
  }

  async getMaterialTags() {
    return this.request<MaterialTag[]>('GET', '/materials/tags')
  }

  async createMaterialTag(data: {
    name: string
    description?: string
    color?: string
  }) {
    return this.request<MaterialTag>('POST', '/materials/tags', data)
  }

  // ==================== 内容生成接口 ====================

  async createGenerationTask(data: CreateGenerationTaskRequest) {
    return this.request<GenerationTask>('POST', '/generation/tasks', data)
  }

  async getGenerationTasks(params?: PaginationParams & {
    status?: TaskStatus
    keyword?: string
  }) {
    return this.request<PaginationResponse<GenerationTaskListItem>>('GET', '/generation/tasks', undefined, params)
  }

  async getGenerationTask(id: number) {
    return this.request<GenerationTask>('GET', `/generation/tasks/${id}`)
  }

  async cancelGenerationTask(id: number) {
    return this.request<GenerationTask>('POST', `/generation/tasks/${id}/cancel`)
  }

  async getGenerationItems(taskId: number, params?: PaginationParams & {
    status?: ItemStatus
  }) {
    return this.request<PaginationResponse<GenerationItem>>('GET', `/generation/tasks/${taskId}/items`, undefined, params)
  }

  async getGenerationItem(id: number) {
    return this.request<GenerationItem>('GET', `/generation/items/${id}`)
  }

  async retryGenerationItem(id: number) {
    return this.request<GenerationItem>('POST', `/generation/items/${id}/retry`)
  }

  async pauseGenerationItem(id: number) {
    return this.request<GenerationItem>('POST', `/generation/items/${id}/pause`)
  }

  async resumeGenerationItem(id: number) {
    return this.request<GenerationItem>('POST', `/generation/items/${id}/resume`)
  }

  async getTaskProgressLogs(id: number, limit?: number) {
    return this.request<GenerationProgressLog[]>('GET', `/generation/tasks/${id}/progress-logs`, undefined, limit ? { limit } : undefined)
  }
}

// 创建默认的API客户端实例
export const apiClient = new ApiClient()

export default apiClient
