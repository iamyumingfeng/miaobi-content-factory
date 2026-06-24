// 妙笔内容工场 - TypeScript类型定义和API客户端 (适配后端版本)

// ==================== 通用类型定义 ====================

// 后端响应格式
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

// ==================== 任务队列相关类型 ====================

export interface QueueStatusData {
  max_concurrent: number
  active_count: number
  idle_count: number
  waiting_count: number
  active_tasks: QueueActiveTask[]
  waiting_tasks: QueueWaitingTask[]
}

export interface QueueActiveTask {
  item_id: number
  celery_task_id: string
  started_at: string
}

export interface QueueWaitingTask {
  item_id: number
  owner_operator_id: number
  priority: number
}

export interface QueueConfig {
  max_concurrent: number
  active_count: number
  idle_count: number
  waiting_count: number
  can_dispatch: boolean
}

export interface DispatchResult {
  dispatched_count: number
  active_count: number
  waiting_count: number
}

export interface ClearQueueResult {
  cleared_count: number
  message: string
}

export interface RecoverStaleResult {
  timeout_minutes: number
  stale_count: number
  stale_tasks: StaleTaskInfo[]
}

export interface StaleTaskInfo {
  item_id: number
  celery_task_id: string
  started_at: string
  elapsed_minutes: number
}

export interface PaginationParams {
  page?: number
  limit?: number
  page_size?: number
}

export interface PaginationResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  total_pages?: number
}

// ==================== 用户相关类型 ====================

export type UserRole = 'super_admin' | 'operator' | 'sub_user'

export type UserStatus = 'online' | 'offline' | 'disabled'

export interface User {
  id: number
  userid: string
  nickname: string
  display_name?: string
  role: UserRole
  status: UserStatus
  fan_profile?: string
  user_positioning?: string
  user_category?: string
  content_style?: string
  account_type?: string
  created_by?: number
  managed_by?: number
  owner_operator_id?: number
  created_at: string
  updated_at: string
  tags?: UserTag[]
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

export interface TemplateAttachment {
  id: number
  template_id: number
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
  platform_id?: number
  category_id?: number
  original_template_id?: number
  created_by: number
  owner_admin_id: number
  created_at: string
  updated_at: string
  tags?: TemplateTag[]
  category?: TemplateCategory
  platform?: TemplatePlatform
  image_count: number
  video_count: number
  attachments?: TemplateAttachment[]
  // 图片尺寸比例：1:1(2048x2048), 4:3(2304x1728), 16:9(2560x1440), 3:4(1728x2304), 9:16(1440x2560)
  image_size_ratio?: string
  // 是否添加水印
  add_watermark?: boolean
  // ===== 爆款模板字段 =====
  viral_type?: string
  product_name?: string  // 产品名称（必填）
  product_selling_points?: string
  // "auto" 表示随机选择，数字表示指定种子ID
  opening_seed_id?: number | null | "auto"
  emotion_seed_id?: number | null | "auto"
  ending_seed_id?: number | null | "auto"
  viral_score?: number
  viral_tags?: string[]
  use_count?: number
  success_count?: number
}

export interface TemplatePlatform {
  id: number
  name: string
  description?: string
  color?: string
  sort_order: number
  is_system: boolean
  created_by: number
  owner_admin_id: number
  status: 'active' | 'inactive'
  template_count?: number
  created_at: string
  updated_at: string
}

// ==================== 分类平台相关类型（3级结构）====================

export interface CategoryPlatform {
  id: number
  name: string
  description?: string
  color?: string
  sort_order: number
  is_system: boolean
  created_by: number
  owner_operator_id: number
  status: 'active' | 'inactive'
  category_count?: number
  material_category_count?: number
  template_category_count?: number
  created_at: string
  updated_at: string
}

export interface MaterialCategory {
  id: number
  name: string
  description?: string
  color?: string
  sort_order: number
  platform_id: number
  created_by: number
  owner_operator_id: number
  status: 'active' | 'inactive'
  tag_count?: number
  material_count?: number
  created_at: string
  updated_at: string
  platform?: CategoryPlatform
  tags?: MaterialTag[]
}

export interface TemplateCategory {
  id: number
  name: string
  description?: string
  color?: string
  sort_order: number
  template_platform_id: number  // 所属模板平台ID
  created_by: number
  owner_operator_id: number
  status: 'active' | 'inactive'
  tag_count?: number
  template_count?: number
  created_at: string
  updated_at: string
  platform?: TemplatePlatform  // 关联的平台对象
  tags?: TemplateTag[]
}

export interface CategoryTreeTag {
  id: number
  name: string
  description?: string
  color?: string
  material_count?: number
  template_count?: number
  created_at: string
}

export interface CategoryTreeCategory {
  id: number
  name: string
  description?: string
  color?: string
  material_count?: number
  template_count?: number
  tag_count: number
  tags: CategoryTreeTag[]
}

export interface CategoryTreePlatform {
  id: number
  name: string
  description?: string
  color?: string
  material_category_count?: number
  template_category_count?: number
  category_count: number
  categories: CategoryTreeCategory[]
}

export interface CategoryTreeResponse {
  platforms: CategoryTreePlatform[]
  material_total: number
  template_total: number
}

// ==================== 模板相关类型 ====================

export interface TemplateTag {
  id: number
  name: string
  description?: string
  color?: string
  category_id?: number
  is_system: boolean
  created_by: number
  created_at: string
  updated_at: string
  template_count?: number
  category?: TemplateCategory
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

export interface MaterialTag {
  id: number
  name: string
  description?: string
  color?: string
  is_system: boolean
  category_id: number
  created_by: number
  owner_admin_id: number
  created_at: string
  updated_at: string
  material_count?: number
  category?: MaterialCategory
}

export interface MaterialTagStats {
  tag_id: number
  tag_name: string
  material_count: number
  material_ids: number[]
}

export interface MaterialTagSummary {
  total: number
  no_tag_count: number
  tag_counts: Record<number, number>
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
  content: string  // 素材内容（必填）
  topic: string    // 素材话题（必选）
  library_type: 'creation' | 'benchmark'  // 素材库类型
  text_content?: string
  source_url?: string
  source_type: 'upload' | 'link' | 'description'
  content_type: ContentType | 'mix'
  category_id?: number
  category?: MaterialCategory & { platform_id?: number }
  platform?: { id: number; name: string; description?: string; color?: string }
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
  content: string  // 素材内容
  topic: string    // 素材话题
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
  name?: string
  material_id?: number
  benchmark_material_id?: number
  model_platform?: string
  model_id?: string
  image_model_platform?: string
  image_model_id?: string
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
  template_id?: number
  template_info?: TemplateInfo
  material_info?: MaterialBrief
  benchmark_material_info?: MaterialBrief
  // 新增字段
  image_count?: number
  dedup_enabled?: boolean
  dedup_threshold?: number
  dedup_retry_count?: number
  dedup_scope?: string[]  // 去重范围配置：subuser_history/current_task/all_history
  // 图片去重配置（独立于文案去重）
  image_dedup_enabled?: boolean
  image_dedup_threshold?: number
  image_dedup_retry_count?: number
  image_dedup_scope?: string[]
  // 素材对标配置
  benchmark_text_enabled?: boolean
  benchmark_image_enabled?: boolean
  benchmark_image_reference_options?: string[]
  // 图片角色配置（交互式编辑）- 字段名与后端Schema一致
  benchmark_image_roles_json?: Record<string, string[]>
  template_product_mapping_json?: Record<string, string>
  // 任务耗时
  duration_seconds?: number
  completed_at?: string
}

export interface MaterialBrief {
  id: number
  title: string
  content_type: string
  content?: string
  topic?: string
  thumbnails?: string[]
}

export interface TemplateInfo {
  id: number
  name: string
  description?: string
  prompt_template?: string
  thumbnails?: string[]
  image_size_ratio?: string
  add_watermark?: boolean
  platform_name?: string  // 所属内容平台名称（如小红书、抖音）
  // 爆款模板新增字段
  viral_type?: string  // 爆款类型值
  viral_type_label?: string  // 爆款类型名称
  opening_seed_name?: string  // 开头模式种子名称
  emotion_seed_name?: string  // 情感基调种子名称
  ending_seed_name?: string  // 结尾模式种子名称
  product_selling_points?: string  // 产品卖点描述
}

export interface GenerationTaskListItem {
  id: number
  name?: string
  material?: {
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
  owner_admin_id?: number
  owner_admin_name?: string
  created_at: string
  updated_at: string
}

export interface GenerationItem {
  id: number
  task_id: number
  sub_user_id: number
  sub_user_name?: string
  template_id: number
  model_platform?: string
  model_id?: string
  image_model_platform?: string
  image_model_id?: string
  generated_title?: string
  generated_text?: string
  generated_image_urls_json?: any
  generated_image_thumbnails_json?: any
  generated_video_url?: string
  output_topics?: string | string[]
  final_prompt?: string
  status: ItemStatus
  retry_count: number
  error_message?: string
  queued_at?: string
  started_at?: string
  completed_at?: string
  distribution_status?: 'draft' | 'ready' | 'distributed' | 'pending_publish' | 'published'
  distributed_at?: string
  confirmed_at?: string
  owner_admin_id: number
  task_name?: string
  created_at: string
  updated_at: string
  // 执行情况
  execution_started_at?: string
  execution_ended_at?: string
  execution_result?: string
  // 当前步骤（用于 UI 细粒度状态展示）
  current_step?: string
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

export type NodeStatus = 'running' | 'success' | 'failed' | 'skipped'

export interface ExecutionLog {
  id: number
  item_id: number
  node_name: string
  node_status: NodeStatus
  input_data?: any
  output_data?: any
  error_data?: any
  duration_ms?: number
  started_at?: string
  completed_at?: string
  created_at: string
  updated_at: string
}

export interface DebugRerunRequest {
  prompt_override?: string
  model_platform_override?: string
  model_id_override?: string
}

// 调试模式 - 提示词/文案/图片生成
export interface DebugGeneratePromptsRequest {
  item_id: number
  text_system_prompt_override?: string
  image_system_prompt_override?: string
  model_platform_override?: string
  model_id_override?: string
}

export interface DebugGeneratePromptsResponse {
  // 文案提示词生成结果
  text_prompt_success: boolean
  text_prompt_error?: string
  text_generator_user_prompt: string
  topics: string[]
  text_generator_system_prompt: string

  // 图片提示词生成结果
  image_prompt_success: boolean
  image_prompt_error?: string
  image_prompts: string[]
  image_generator_system_prompt: string

  // 参考图片（用于图片生成）
  reference_image_urls?: string[]
}

export interface DebugGenerateTextRequest {
  item_id: number
  system_prompt_override?: string
  user_prompt_override?: string
  model_platform_override?: string
  model_id_override?: string
}

export interface DebugGenerateTextResponse {
  title: string
  content: string
  topics: string[]
  image_prompts: string[]
}

export interface DebugGenerateImagesRequest {
  item_id: number
  system_prompt_override?: string
  user_prompts_override?: string[]
  model_platform_override?: string
  model_id_override?: string
  image_count_override?: number
  reference_image_urls_override?: string[]
}

export interface DebugGenerateImagesResponse {
  image_urls: string[]
  reference_image_urls?: string[]
}

export interface GenerationItemDetail {
  id: number
  task_id: number
  sub_user_id: number
  sub_user_name?: string
  template_id?: number
  model_platform?: string
  model_id?: string
  image_model_platform?: string
  image_model_id?: string

  // 生成结果
  generated_title?: string
  generated_text?: string
  text_file_url?: string
  generated_image_urls_json?: string[]
  generated_image_thumbnails_json?: string[]
  generated_video_url?: string
  output_topics?: string | string[]

  // 状态
  status: ItemStatus
  retry_count: number
  error_message?: string
  distribution_status?: 'draft' | 'ready' | 'distributed'
  queued_at?: string
  started_at?: string
  completed_at?: string
  distributed_at?: string
  confirmed_at?: string

  // 输入内容 - 模板信息
  input_prompt_creativity?: string
  input_prompt_instruction?: string
  input_template_images_json?: string[]
  input_image_size_ratio?: string
  input_watermark?: boolean
  // 输入内容 - 模板扩展信息
  input_template_name?: string
  input_viral_type?: string
  input_product_selling_points?: string
  input_opening_seed_name?: string
  input_emotion_seed_name?: string
  input_ending_seed_name?: string

  // 输入内容 - 素材对标信息
  input_benchmark_title?: string
  input_benchmark_content?: string
  input_benchmark_topic?: string
  input_benchmark_images_json?: string[]
  // 输入内容 - 素材对标配置
  input_benchmark_text_enabled?: boolean
  input_benchmark_image_enabled?: boolean
  input_benchmark_image_reference_options?: string[]
  // 图片角色配置（交互式编辑）- 字段名与后端Schema一致
  input_benchmark_image_roles_json?: Record<string, string[]>
  input_template_product_mapping_json?: Record<string, string>

  // 输入内容 - 创作者信息
  input_sub_user_profile?: string
  input_sub_user_positioning?: string
  input_sub_user_style?: string

  // 输出内容 - AIGC重构提示词
  aigc_generated_prompt?: string
  output_system_text_prompt?: string
  output_user_text_prompt?: string
  output_system_image_prompt?: string
  output_user_image_prompt?: string

  // AIGC 用户提示词
  aigc_user_text_generator_user_prompt?: string
  aigc_user_image_prompts_json?: string[]

  // 去重检测
  dedup_check_passed?: boolean
  dedup_similarity?: number
  dedup_referenced_items_json?: Array<{ item_id: number; similarity: number; text_preview: string }>
  dedup_checked_at?: string

  // 当前步骤
  current_step?: string
  generated_image_count?: number

  // 调试
  final_prompt?: string

  // 执行情况
  execution_started_at?: string
  execution_ended_at?: string
  execution_result?: string

  created_at: string
  updated_at: string
}

export interface CreateGenerationTaskRequest {
  name?: string
  material_id: number
  benchmark_material_id?: number
  template_ids?: number[]
  model_selection_mode?: ModelSelectionMode
  model_platform?: string
  model_id?: string
  max_concurrency?: number
  variable_values_json?: any
  dedup_rules_json?: any
  sub_user_ids: number[]
  // 新增字段
  image_count?: number
  dedup_enabled?: boolean
  dedup_threshold?: number
  dedup_retry_count?: number
  dedup_scope?: string[]  // 文案去重范围配置：subuser_history/current_task/all_history
  // 图片去重配置
  image_dedup_enabled?: boolean
  image_dedup_threshold?: number  // 图片相似度阈值（0.5-0.95）
  image_dedup_retry_count?: number  // 图片去重最大重试次数
  image_dedup_scope?: string[]  // 图片去重范围：subuser_image_history/current_task_images/all_image_history
  // 素材对标配置
  benchmark_text_enabled?: boolean
  benchmark_image_enabled?: boolean
  benchmark_image_reference_options?: string[]
  // 图片角色配置（交互式编辑）- 字段名与后端Schema一致
  benchmark_image_roles_json?: Record<string, string[]>
  template_product_mapping_json?: Record<string, string>
}

// ==================== 提示词模板管理类型 ====================

// ==================== 微信登录相关类型 ====================

export interface LoginRequest {
  userid: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  refresh_expires_in: number
  user: UserInfo
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface RefreshTokenResponse {
  access_token: string
  token_type: string
  expires_in: number
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

// ==================== 模型配置相关类型 ====================

export type ModelType = 'llm' | 'image' | 'video' | 'embedding'
export type ModelConfigStatus = 'active' | 'inactive'

export interface ModelConfig {
  id: number
  platform: string
  model_id: string
  model_name: string
  model_type: ModelType
  base_url?: string
  api_endpoint?: string
  is_default: boolean
  max_concurrency: number
  config_json?: any
  status: ModelConfigStatus
  is_system: boolean
  created_by?: number
  created_at: string
  updated_at: string
}

export interface CreateModelConfigRequest {
  platform: string
  model_id: string
  model_name: string
  model_type: ModelType
  base_url?: string
  api_endpoint?: string
  is_default?: boolean
  max_concurrency?: number
  config_json?: any
  status?: ModelConfigStatus
}

export interface UpdateModelConfigRequest {
  platform?: string
  model_id?: string
  model_name?: string
  model_type?: ModelType
  base_url?: string
  api_endpoint?: string
  is_default?: boolean
  max_concurrency?: number
  config_json?: any
  status?: ModelConfigStatus
}

// ==================== 用户默认模型相关类型 ====================

export interface UserDefaultModelUpdate {
  llm_model_config_id?: number | null
  image_model_config_id?: number | null
  video_model_config_id?: number | null
  embedding_model_config_id?: number | null
}

export interface UserDefaultModelResponse {
  llm_model_config_id?: number | null
  image_model_config_id?: number | null
  video_model_config_id?: number | null
  embedding_model_config_id?: number | null
  updated_at?: string
}

// ==================== 仪表盘相关类型 ====================

export interface DashboardStats {
  total_sub_users: number
  today_generated: number
  pending_publish: number
  published: number
  start_date?: string
  end_date?: string
}

export interface TrendDataPoint {
  date: string
  generated: number
  distributed: number
  published: number
}

export interface DashboardTrend {
  data: TrendDataPoint[]
}

export interface RecentTaskItem {
  id: number
  name?: string
  status: string
  total_count: number
  queued_count: number
  generating_count: number
  completed_count: number
  failed_count: number
  paused_count: number
  pending_publish_count: number
  published_count: number
  owner_admin_id?: number
  owner_admin_name?: string
  created_at: string
  updated_at: string
}

export interface FailedTaskItem {
  id: number
  name: string
  failed_count: number
  error: string
  owner_admin_id?: number
  owner_admin_name?: string
  latest_failed_at?: string
}

export interface OperatorOption {
  id: number
  name: string
}

export interface DashboardRecentTasks {
  tasks: RecentTaskItem[]
  total: number
}

export interface DashboardFailedTasks {
  tasks: FailedTaskItem[]
}

// ==================== 趋势分析相关类型 ====================

export type TimeDimension = 'day' | 'week' | 'month'
export type CompareType = 'none' | 'chain' | 'year'
// 内容类型：纯文本、图文、视频文案（后端模板使用 text/image_text/video_text）
export type ContentType = 'all' | 'text' | 'image_text' | 'video' | 'video_text'

export interface TrendAnalysisDataPoint {
  date: string
  generated: number
  distributed: number
  published: number
  success_rate: number
}

export interface ComparisonData {
  current: number
  previous: number
  change: number
  change_rate: number
}

export interface GenerationTrendResponse {
  data: TrendAnalysisDataPoint[]
  total: number
  avg_daily: number
  max_daily: number
  compare?: ComparisonData
}

export interface DistributionTrendResponse {
  data: TrendAnalysisDataPoint[]
  total_distributed: number
  total_published: number
  distribution_rate: number
  publish_rate: number
  distributed_compare?: ComparisonData
  published_compare?: ComparisonData
}

export interface PublishTrendResponse {
  data: TrendAnalysisDataPoint[]
  total_generated: number
  total_published: number
  success_rate: number
  generated_compare?: ComparisonData
  published_compare?: ComparisonData
}

export interface OperatorTrendItem {
  operator_id: number
  operator_name: string
  generated: number
  distributed: number
  published: number
}

export interface OperatorTrendResponse {
  data: OperatorTrendItem[]
}

export interface TrendAnalysisFilterOptions {
  operators: OperatorOption[]
  content_types: { value: string; label: string }[]
  dimensions: { value: string; label: string }[]
}

export interface TrendAnalysisParams {
  start_date?: string
  end_date?: string
  dimension?: TimeDimension
  compare_type?: CompareType
  content_type?: ContentType
  operator_id?: number
}

// ==================== 定时任务类型 ====================

export type ScheduledTaskStatus = 'enabled' | 'disabled'
export type ScheduledTaskType = 'custom' | 'benchmark'  // 自定义文案 / 对标文案
export type ScheduleType = 'daily' | 'weekly' | 'periodic'  // 每日 / 每周 / 周期

export interface ScheduleConfig {
  type: ScheduleType
  // 每日：时间点列表，如 ["09:00", "15:30"]
  times?: string[]
  // 每周：日期列表（1-7，1=周一），如 [1, 3, 5]
  days?: number[]
  weekdays?: number[]  // 兼容旧字段
  weekly_times?: string[]  // 每周的时间点（兼容旧字段）
  // 周期：日期范围 + 每日时间点
  start_date?: string  // 周期开始日期，格式：YYYY-MM-DD
  end_date?: string    // 周期结束日期，格式：YYYY-MM-DD
}

export interface ScheduledTask {
  id: number
  name: string
  task_type: ScheduledTaskType
  schedule_type: string  // daily / weekly
  schedule_config_json: ScheduleConfig
  status: ScheduledTaskStatus
  
  // 素材和模板配置
  material_id?: number
  benchmark_material_ids_json?: number[]
  benchmark_material_titles?: string[]
  template_ids_json?: number[]
  template_names?: string[]
  
  // 创作者配置
  sub_user_ids_json?: number[]
  sub_user_names?: string[]  // 创作者名称列表
  
  // 模型配置
  model_selection_mode?: ModelSelectionMode
  model_platform?: string
  model_id?: string
  image_model_platform?: string
  image_model_id?: string
  max_concurrency?: number
  
  // 去重配置
  dedup_enabled?: boolean
  dedup_threshold?: number
  dedup_retry_count?: number
  dedup_scope?: string[]
  image_dedup_enabled?: boolean
  image_dedup_threshold?: number
  image_dedup_retry_count?: number
  image_dedup_scope?: string[]
  
  // 对标配置
  benchmark_text_enabled?: boolean
  benchmark_image_enabled?: boolean
  benchmark_image_reference_options?: string[]
  benchmark_image_roles_json?: Record<string, string[]>
  template_product_mapping_json?: Record<string, string>
  variable_values_json?: Record<string, any>
  
  // 图片数量
  image_count?: number
  
  // 执行统计
  total_executions?: number
  successful_executions?: number
  failed_executions?: number
  last_execution_at?: string
  last_execution_status?: string
  next_execution_at?: string
  
  // 元数据
  is_active?: boolean
  created_by: number
  owner_operator_id: number
  created_at: string
  updated_at: string
  
  // 关联信息（标题/名称，由后端 enrich 返回）
  material_title?: string
  owner_operator_name?: string
}

export interface ScheduledTaskListItem {
  id: number
  name: string
  task_type: ScheduledTaskType
  schedule_config_json: ScheduleConfig
  status: ScheduledTaskStatus
  is_active?: boolean
  next_execution_at?: string
  total_executions?: number
  successful_executions?: number
  failed_executions?: number
  created_at: string
  updated_at: string
}

export interface CreateScheduledTaskRequest {
  name: string
  task_type: ScheduledTaskType
  schedule_config_json: ScheduleConfig
  material_id?: number
  benchmark_material_ids_json?: number[]
  template_ids_json?: number[]
  sub_user_ids_json?: number[]
  model_selection_mode?: ModelSelectionMode
  model_platform?: string
  model_id?: string
  image_model_platform?: string
  image_model_id?: string
  dedup_enabled?: boolean
  dedup_threshold?: number
  dedup_retry_count?: number
  dedup_scope?: string[]
  image_dedup_enabled?: boolean
  image_dedup_threshold?: number
  image_dedup_retry_count?: number
  image_dedup_scope?: string[]
  benchmark_text_enabled?: boolean
  benchmark_image_enabled?: boolean
  benchmark_image_reference_options?: string[]
  benchmark_image_roles_json?: Record<string, string[]>
  template_product_mapping_json?: Record<string, string>
  image_count?: number
  max_concurrency?: number
}

export interface UpdateScheduledTaskRequest {
  name?: string
  task_type?: ScheduledTaskType
  schedule_config_json?: ScheduleConfig
  material_id?: number
  benchmark_material_ids_json?: number[]
  template_ids_json?: number[]
  sub_user_ids_json?: number[]
  model_selection_mode?: ModelSelectionMode
  model_platform?: string
  model_id?: string
  image_model_platform?: string
  image_model_id?: string
  dedup_enabled?: boolean
  dedup_threshold?: number
  dedup_retry_count?: number
  dedup_scope?: string[]
  image_dedup_enabled?: boolean
  image_dedup_threshold?: number
  image_dedup_retry_count?: number
  image_dedup_scope?: string[]
  benchmark_text_enabled?: boolean
  benchmark_image_enabled?: boolean
  benchmark_image_reference_options?: string[]
  benchmark_image_roles_json?: Record<string, string[]>
  template_product_mapping_json?: Record<string, string>
  image_count?: number
  max_concurrency?: number
  variable_values_json?: Record<string, any>
}

export interface ScheduledTaskExecution {
  id: number
  scheduled_task_id: number
  generation_task_id?: number
  execution_type: 'scheduled' | 'manual'
  scheduled_at: string
  started_at?: string
  completed_at?: string
  execution_time: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'partial' | 'cancelled'
  error_message?: string
  total_items?: number
  success_items?: number
  failed_items?: number
  created_at: string
}

// ==================== 操作日志类型 ====================

export type OperationLogModule = 'users' | 'templates' | 'materials' | 'generation' | 'distribution' | 'system' | 'scheduled_tasks'
export type OperationLogAction = 'create' | 'update' | 'delete' | 'distribute' | 'publish' | 'login' | 'logout' | 'cancel' | 'retry' | 'copy' | 'disable' | 'enable' | 'transfer' | 'import' | 'export' | 'execute'

export interface OperationLog {
  id: number
  super_admin_id?: number
  operator_id?: number
  operator_name?: string
  sub_user_id?: number
  sub_user_name?: string
  module?: OperationLogModule
  action: OperationLogAction
  description?: string
  table_name?: string
  record_id?: number
  old_value_json?: Record<string, any>
  new_value_json?: Record<string, any>
  extra_data_json?: Record<string, any>
  ip_address?: string
  user_agent?: string
  created_at: string
}

export interface OperationLogCreateParams {
  module?: OperationLogModule
  action: OperationLogAction
  description?: string
  table_name?: string
  record_id?: number
  old_value?: Record<string, any>
  new_value?: Record<string, any>
  extra_data?: Record<string, any>
}

export interface OperationLogQueryParams {
  page?: number
  limit?: number
  module?: OperationLogModule
  action?: OperationLogAction
  user_id?: number
  user_type?: string
  table_name?: string
  record_id?: number
  start_date?: string
  end_date?: string
}

// ==================== API客户端 ====================

// Token 存储 key 常量 - 与 auth store 保持一致
const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const USER_KEY = 'user'
const TOKEN_EXPIRE_TIME_KEY = 'token_expire_time'

export class ApiClient {
  private baseUrl: string
  private isRefreshing: boolean = false
  private refreshPromise: Promise<string | null> | null = null

  constructor(baseUrl: string = '/api/v1') {
    this.baseUrl = baseUrl
  }

  setAccessToken(token: string) {
    localStorage.setItem(ACCESS_TOKEN_KEY, token)
  }

  setToken(token: string) {
    this.setAccessToken(token)
  }

  setRefreshToken(token: string) {
    localStorage.setItem(REFRESH_TOKEN_KEY, token)
  }

  setTokenExpireTime(expireInSeconds: number) {
    const expireAt = Date.now() + expireInSeconds * 1000
    localStorage.setItem(TOKEN_EXPIRE_TIME_KEY, expireAt.toString())
  }

  clearToken() {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    localStorage.removeItem(TOKEN_EXPIRE_TIME_KEY)
  }

  /**
   * 检查 token 是否即将过期（提前 5 分钟）
   */
  private isTokenExpiringSoon(): boolean {
    const expireTimeStr = localStorage.getItem(TOKEN_EXPIRE_TIME_KEY)
    if (!expireTimeStr) return false

    const expireTime = parseInt(expireTimeStr, 10)
    const now = Date.now()
    const fiveMinutes = 5 * 60 * 1000

    return now > expireTime - fiveMinutes
  }

  /**
   * 刷新 access token
   */
  private async refreshAccessToken(): Promise<string | null> {
    if (this.isRefreshing && this.refreshPromise) {
      return this.refreshPromise
    }

    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
    if (!refreshToken) return null

    this.isRefreshing = true
    this.refreshPromise = this.doRefresh(refreshToken)
      .finally(() => {
        this.isRefreshing = false
        this.refreshPromise = null
      })

    return this.refreshPromise
  }

  private async doRefresh(refreshToken: string): Promise<string | null> {
    try {
      const response = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ refresh_token: refreshToken })
      })

      if (!response.ok) {
        throw new Error('Refresh token failed')
      }

      const result = await response.json()
      if (result.success && result.data) {
        const { access_token, expires_in } = result.data
        this.setToken(access_token)
        this.setTokenExpireTime(expires_in)
        return access_token
      }

      throw new Error('Invalid response format')
    } catch (error) {
      console.error('Refresh token failed:', error)
      this.clearToken()
      return null
    }
  }

  /**
   * 处理未授权响应 - 清除本地状态并跳转到登录页
   * @param reason 错误原因，用于区分普通过期和账号被禁用
   */
  private handleUnauthorized(reason?: string) {
    this.clearToken()

    // 区分账号被禁用和其他未授权情况
    const isDisabled = reason?.includes('禁用') || reason?.includes('disabled')

    if (isDisabled) {
      // 账号被禁用：发送自定义事件，让 App 组件显示提示并跳转
      window.dispatchEvent(new CustomEvent('account-disabled', {
        detail: { message: '账号已被禁用，请联系管理员' }
      }))
      // 延迟跳转，给提示显示的时间
      setTimeout(() => {
        window.location.href = '/login'
      }, 2000)
    } else {
      // 普通过期：直接跳转
      window.location.href = '/login'
    }
  }

  private async request<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH',
    endpoint: string,
    data?: any,
    params?: Record<string, any>,
    options?: { skipAutoRedirect?: boolean },
    isFormData?: boolean
  ): Promise<T> {
    const headers: Record<string, string> = isFormData ? {} : {
      'Content-Type': 'application/json'
    }

    // 检查是否需要刷新 token（且不是刷新 token 接口本身）
    if (!endpoint.includes('/auth/refresh')) {
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
      if (refreshToken && this.isTokenExpiringSoon()) {
        await this.refreshAccessToken()
      }
    }

    // 每次请求都从 localStorage 获取最新 token
    let currentToken = localStorage.getItem(ACCESS_TOKEN_KEY)
    if (currentToken) {
      headers['Authorization'] = `Bearer ${currentToken}`
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
      headers
    }

    if (data && method !== 'GET') {
      config.body = isFormData ? data : JSON.stringify(data)
    }

    try {
      console.log('API Request:', method, url)
      const response = await fetch(url, config)
      console.log('API Response status:', response.status)

      const result = await this.handleResponse(response, options)

      return result.data as T
    } catch (error: any) {
      console.error('API请求失败:', error)
      // 增强错误信息
      if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
        throw new Error(`网络连接失败，请检查服务器是否正常运行 (${url})`)
      }
      throw error
    }
  }

  /**
   * 处理 API 响应（提取为独立方法供文件上传等复用）
   */
  private async handleResponse(response: Response, options?: { skipAutoRedirect?: boolean }): Promise<any> {
    const text = await response.text()
    console.log('API Response text:', text.substring(0, 200))
    let result: any = {}

    if (text) {
      try {
        result = JSON.parse(text)
      } catch {
        throw new Error(`服务器返回了无效的响应: ${text.substring(0, 100)}`)
      }
    }

    // 处理 401 未授权响应
    if (response.status === 401 && !options?.skipAutoRedirect) {
      let errorReason = ''
      if (result.message) {
        errorReason = String(result.message)
      } else if (result.detail) {
        if (Array.isArray(result.detail)) {
          errorReason = result.detail.map((e: any) => e.msg || '').join('; ')
        } else {
          errorReason = String(result.detail)
        }
      } else if (result.code) {
        errorReason = String(result.code)
      }
      this.handleUnauthorized(errorReason)
      throw new Error(errorReason || '登录已过期，请重新登录')
    }

    // 处理 HTTP 错误响应
    if (!response.ok) {
      let errorMsg = ''
      if (result.detail) {
        if (Array.isArray(result.detail)) {
          errorMsg = result.detail.map((e: any) => e.msg || `${e.loc?.join('.')}: ${e.type}`).join('; ')
        } else if (typeof result.detail === 'object') {
          errorMsg = JSON.stringify(result.detail)
        } else {
          errorMsg = String(result.detail)
        }
      }
      if (!errorMsg) {
        errorMsg = result.message || result.error || `请求失败 (${response.status})`
      }
      throw new Error(errorMsg)
    }

    // 处理业务错误响应
    if (result.success === false) {
      throw new Error(result.message || result.error || '请求失败')
    }

    return result
  }

  // ==================== 认证接口 ====================

  async login(userid: string, password: string) {
    // 登录接口的 401 响应不自动跳转，让调用者处理错误消息
    return this.request<LoginResponse>('POST', '/auth/login', { userid, password }, undefined, { skipAutoRedirect: true })
  }

  async refreshToken(refreshToken: string) {
    return this.request<RefreshTokenResponse>('POST', '/auth/refresh', { refresh_token: refreshToken }, undefined, { skipAutoRedirect: true })
  }

  async logout() {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
    return this.request('POST', '/auth/logout', { refresh_token: refreshToken })
  }

  async getCurrentUser() {
    return this.request<UserInfo>('GET', '/auth/me')
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
    operator_id?: number
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

  async updateSubUser(id: number, data: any) {
    return this.request<User>('PUT', `/users/sub-users/${id}`, data)
  }

  async deleteSubUser(id: number) {
    return this.request('DELETE', `/users/sub-users/${id}`)
  }

  async resetSubUserPassword(id: number, newPassword: string) {
    return this.request('POST', `/users/sub-users/${id}/reset-password`, {
      new_password: newPassword
    })
  }

  async transferSubUsers(userIds: number[], fromOperatorId: number, toOperatorId: number) {
    return this.request('POST', '/users/sub-users/transfer', {
      user_ids: userIds,
      from_operator_id: fromOperatorId,
      to_operator_id: toOperatorId
    })
  }

  async getUserTags(params?: { tag_type?: 'operator_tag' | 'subuser_tag', operator_id?: number }) {
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

  async updateUserTag(id: number, data: any) {
    return this.request<UserTag>('PUT', `/users/tags/${id}`, data)
  }

  async deleteUserTag(id: number) {
    return this.request('DELETE', `/users/tags/${id}`)
  }

  async getTagCounts(params?: { operator_id?: number }) {
    return this.request<Record<number, number>>('GET', '/users/tags/counts', undefined, params)
  }

  async updateSuperAdmin(id: number, data: any) {
    return this.request<User>('PUT', `/users/super-admins/${id}`, data)
  }

  async deleteSuperAdmin(id: number) {
    return this.request('DELETE', `/users/super-admins/${id}`)
  }

  async deleteOperator(id: number) {
    return this.request('DELETE', `/users/operators/${id}`)
  }

  async transferOperators(userIds: number[], fromOperatorId: number, toOperatorId: number) {
    return this.request('POST', '/users/operators/transfer', {
      user_ids: userIds,
      from_operator_id: fromOperatorId,
      to_operator_id: toOperatorId
    })
  }

  async resetOperatorPassword(id: number, newPassword: string) {
    return this.request('POST', `/users/operators/${id}/reset-password`, {
      new_password: newPassword
    })
  }

  async resetSuperAdminPassword(id: number, newPassword: string) {
    return this.request('POST', `/users/super-admins/${id}/reset-password`, {
      new_password: newPassword
    })
  }

  // ==================== 素材库平台分类接口（独立平台表）====================

  async getMaterialPlatformTree(params?: { owner_operator_id?: number }) {
    return this.request<CategoryTreeResponse>('GET', '/materials/platforms/tree', undefined, params)
  }

  async getMaterialPlatforms(params?: { owner_operator_id?: number }) {
    return this.request<CategoryPlatform[]>('GET', '/materials/platforms', undefined, params)
  }

  async createMaterialPlatform(data: { name: string; description?: string; color?: string; sort_order?: number }) {
    return this.request<CategoryPlatform>('POST', '/materials/platforms', data)
  }

  async updateMaterialPlatform(id: number, data: { name?: string; description?: string; color?: string; sort_order?: number }) {
    return this.request<CategoryPlatform>('PUT', `/materials/platforms/${id}`, data)
  }

  async deleteMaterialPlatform(id: number) {
    return this.request('DELETE', `/materials/platforms/${id}`)
  }

  // ==================== 模板库平台分类接口（独立平台表）====================

  async getTemplatePlatformTree(params?: { owner_operator_id?: number }) {
    return this.request<CategoryTreeResponse>('GET', '/templates/platforms/tree', undefined, params)
  }

  async getTemplatePlatforms(params?: { owner_operator_id?: number }) {
    return this.request<CategoryPlatform[]>('GET', '/templates/platforms', undefined, params)
  }

  async createTemplatePlatform(data: { name: string; description?: string; color?: string; sort_order?: number }) {
    return this.request<CategoryPlatform>('POST', '/templates/platforms', data)
  }

  async updateTemplatePlatform(id: number, data: { name?: string; description?: string; color?: string; sort_order?: number }) {
    return this.request<CategoryPlatform>('PUT', `/templates/platforms/${id}`, data)
  }

  async deleteTemplatePlatform(id: number) {
    return this.request('DELETE', `/templates/platforms/${id}`)
  }

  // ==================== 模板分类接口 ====================

  async getTemplateCategories(platformId?: number) {
    return this.request<TemplateCategory[]>('GET', '/templates/categories', undefined, platformId ? { platform_id: platformId } : undefined)
  }

  async createTemplateCategory(data: {
    name: string
    platform_id: number
    description?: string
    color?: string
    sort_order?: number
  }) {
    return this.request<TemplateCategory>('POST', '/templates/categories', data)
  }

  async updateTemplateCategory(id: number, data: { name?: string; description?: string; color?: string; sort_order?: number }) {
    return this.request<TemplateCategory>('PUT', `/templates/categories/${id}`, data)
  }

  async deleteTemplateCategory(id: number) {
    return this.request('DELETE', `/templates/categories/${id}`)
  }

  // ==================== 模板管理接口 ====================

  async getTemplates(params?: PaginationParams & {
    keyword?: string
    platform_id?: number
    tag_ids?: string
    tag_id?: number
    content_type?: ContentType
    status?: 'enabled' | 'disabled'
    owner_operator_id?: number
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

  async copyTemplate(id: number, data?: {
    name?: string;
    target_operator_id?: number;
    target_platform_id?: number;
    target_category_id?: number;
    target_tag_ids?: number[];
  }) {
    return this.request<Template>('POST', `/templates/${id}/copy`, data)
  }

  async getTemplateTags(categoryId?: number) {
    return this.request<TemplateTag[]>('GET', '/templates/tags', undefined, categoryId ? { category_id: categoryId } : undefined)
  }

  async createTemplateTag(data: {
    name: string
    category_id: number
    description?: string
    color?: string
  }) {
    return this.request<TemplateTag>('POST', '/templates/tags', data)
  }

  async updateTemplateTag(id: number, data: {
    name?: string
    description?: string
    color?: string
  }) {
    return this.request<TemplateTag>('PUT', `/templates/tags/${id}`, data)
  }

  async deleteTemplateTag(id: number) {
    return this.request('DELETE', `/templates/tags/${id}`)
  }

  async getTemplatePlatformStats(id: number) {
    return this.request<{ platform_id: number; template_count: number; category_count: number; tag_count: number }>('GET', `/templates/platforms/${id}/stats`)
  }

  async getTemplateCategoryStats(id: number) {
    return this.request<{ category_id: number; template_count: number; tag_count: number }>('GET', `/templates/categories/${id}/stats`)
  }

  async getTemplateTagStats(id: number) {
    return this.request<{ tag_id: number; template_count: number }>('GET', `/templates/tags/${id}/stats`)
  }

  async uploadTemplateImage(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    return this.request<{ url: string }>('POST', '/templates/upload-image', formData, undefined, undefined, true)
  }

  async uploadTemplate(data: {
    name: string
    product_name?: string  // 产品名称
    description?: string
    prompt_template?: string
    text_content?: string
    content_type?: string
    tag_ids?: number[]
    platform_id?: number
    style_reference?: string
    platform_rules_json?: string
    files?: File[]
    image_size_ratio?: string
    add_watermark?: boolean
    // ===== 爆款模板字段 =====
    viral_type?: string
    product_selling_points?: string
    // "auto" 表示随机选择，数字表示指定种子ID
    opening_seed_id?: number | string
    emotion_seed_id?: number | string
    ending_seed_id?: number | string
    viral_tags?: string[]
  }) {
    const formData = new FormData()
    formData.append('name', data.name)
    if (data.description !== undefined && data.description !== null && data.description !== '') {
      formData.append('description', data.description)
    }

    if (data.prompt_template) formData.append('prompt_template', data.prompt_template)
    if (data.text_content) formData.append('text_content', data.text_content)
    if (data.content_type) formData.append('content_type', data.content_type)
    if (data.platform_id !== undefined && data.platform_id !== null) {
      formData.append('platform_id', String(data.platform_id))
    }
    if (data.style_reference) formData.append('style_reference', data.style_reference)
    if (data.platform_rules_json) formData.append('platform_rules_json', data.platform_rules_json)
    if (data.tag_ids && data.tag_ids.length > 0) {
      formData.append('tag_ids', data.tag_ids.join(','))
    }
    if (data.files) {
      data.files.forEach(file => {
        formData.append('files', file)
      })
    }
    if (data.image_size_ratio) formData.append('image_size_ratio', data.image_size_ratio)
    if (data.add_watermark !== undefined) formData.append('add_watermark', String(data.add_watermark))
    // ===== 爆款模板字段（uploadTemplate） =====
    if (data.viral_type !== undefined) formData.append('viral_type', String(data.viral_type || ''))
    if (data.product_name !== undefined) formData.append('product_name', String(data.product_name || ''))
    if (data.product_selling_points !== undefined) formData.append('product_selling_points', String(data.product_selling_points || ''))
    // 种子 ID：始终发送，空字符串表示清空（随机选择），后端转为 NULL
    if (data.opening_seed_id !== undefined && data.opening_seed_id !== null) {
      formData.append('opening_seed_id', String(data.opening_seed_id))
    }
    if (data.emotion_seed_id !== undefined && data.emotion_seed_id !== null) {
      formData.append('emotion_seed_id', String(data.emotion_seed_id))
    }
    if (data.ending_seed_id !== undefined && data.ending_seed_id !== null) {
      formData.append('ending_seed_id', String(data.ending_seed_id))
    }
    if (data.viral_tags && data.viral_tags.length > 0) {
      formData.append('viral_tags', JSON.stringify(data.viral_tags))
    }

    const currentToken = localStorage.getItem('access_token')
    const headers: Record<string, string> = {}
    if (currentToken) {
      headers['Authorization'] = `Bearer ${currentToken}`
    }
    // 注意：不设置 Content-Type，让浏览器自动设置 multipart/form-data + boundary

    const url = `${this.baseUrl}/templates/upload`
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    })

    const result = await this.handleResponse(response)
    return result.data as Template
  }

  async updateTemplateWithAttachments(data: {
    id: number
    name?: string
    description?: string
    prompt_template?: string
    content_type?: string
    tag_ids?: number[]
    platform_id?: number
    style_reference?: string
    platform_rules_json?: string
    status?: string
    delete_attachment_ids?: number[]
    files?: File[]
    image_size_ratio?: string
    add_watermark?: boolean
    // ===== 爆款模板字段 =====
    viral_type?: string
    product_name?: string  // 产品名称
    product_selling_points?: string
    // "auto" 表示随机选择，数字表示指定种子ID
    opening_seed_id?: number | string
    emotion_seed_id?: number | string
    ending_seed_id?: number | string
    viral_tags?: string[]
  }) {
    const formData = new FormData()
    if (data.name !== undefined) formData.append('name', data.name)
    if (data.description !== undefined && data.description !== null && data.description !== '') {
      formData.append('description', data.description)
    }
    if (data.prompt_template) formData.append('prompt_template', data.prompt_template)
    if (data.content_type) formData.append('content_type', data.content_type)
    if (data.platform_id !== undefined && data.platform_id !== null) {
      formData.append('platform_id', String(data.platform_id))
    }
    if (data.style_reference) formData.append('style_reference', data.style_reference)
    if (data.platform_rules_json) formData.append('platform_rules_json', data.platform_rules_json)
    if (data.status) formData.append('status', data.status)
    if (data.tag_ids && data.tag_ids.length > 0) {
      formData.append('tag_ids', data.tag_ids.join(','))
    }
    if (data.delete_attachment_ids && data.delete_attachment_ids.length > 0) {
      formData.append('delete_attachment_ids', data.delete_attachment_ids.join(','))
    }
    if (data.files) {
      data.files.forEach(file => {
        formData.append('files', file)
      })
    }
    if (data.image_size_ratio) formData.append('image_size_ratio', data.image_size_ratio)
    if (data.add_watermark !== undefined) formData.append('add_watermark', String(data.add_watermark))
    // ===== 爆款模板字段（updateWithAttachments） =====
    if (data.viral_type !== undefined) formData.append('viral_type', String(data.viral_type || ''))
    if (data.product_name !== undefined) formData.append('product_name', String(data.product_name || ''))
    if (data.product_selling_points !== undefined) formData.append('product_selling_points', String(data.product_selling_points || ''))
    // 种子 ID：始终发送，空字符串表示清空（随机选择），后端转为 NULL
    if (data.opening_seed_id !== undefined && data.opening_seed_id !== null) {
      formData.append('opening_seed_id', String(data.opening_seed_id))
    }
    if (data.emotion_seed_id !== undefined && data.emotion_seed_id !== null) {
      formData.append('emotion_seed_id', String(data.emotion_seed_id))
    }
    if (data.ending_seed_id !== undefined && data.ending_seed_id !== null) {
      formData.append('ending_seed_id', String(data.ending_seed_id))
    }
    if (data.viral_tags && data.viral_tags.length > 0) {
      formData.append('viral_tags', JSON.stringify(data.viral_tags))
    }

    const currentToken = localStorage.getItem('access_token')
    const headers: Record<string, string> = {}
    if (currentToken) {
      headers['Authorization'] = `Bearer ${currentToken}`
    }

    const url = `${this.baseUrl}/templates/${data.id}/update-with-attachments`
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    })

    const result = await this.handleResponse(response)
    return result.data as Template
  }

  // 模板批量操作
  async batchDeleteTemplates(templateIds: number[]) {
    return this.request<{ success_count: number; failed_ids: number[] }>('POST', '/templates/batch-delete', { template_ids: templateIds })
  }

  async batchUpdateTemplateStatus(templateIds: number[], status: 'enabled' | 'disabled') {
    return this.request<{ success_count: number }>('POST', '/templates/batch-status', { template_ids: templateIds, status })
  }

  async batchCopyTemplates(params: {
    template_ids: number[];
    new_names?: Record<string, string>;
    target_operator_id?: number;
    target_platform_id: number;
    target_category_id: number;
    target_tag_ids: number[];
  }) {
    return this.request<{ success_count: number; failed_ids: number[] }>('POST', '/templates/batch-copy', {
      template_ids: params.template_ids,
      new_names: params.new_names,
      target_operator_id: params.target_operator_id,
      target_platform_id: params.target_platform_id,
      target_category_id: params.target_category_id,
      target_tag_ids: params.target_tag_ids,
    })
  }

  async batchTransferTemplates(templateIds: number[], targetOperatorId: number, targetPlatformId: number, targetCategoryId: number, targetTagIds: number[]) {
    return this.request<{ success_count: number; failed_ids: number[] }>('POST', '/templates/batch-transfer', {
      template_ids: templateIds,
      target_operator_id: targetOperatorId,
      target_platform_id: targetPlatformId,
      target_category_id: targetCategoryId,
      target_tag_ids: targetTagIds
    })
  }

  // 模板标签迁移
  async migrateTagTemplates(tagId: number, targetTagId: number) {
    return this.request<{ migrated_count: number; template_ids: number[] }>('POST', `/templates/tags/${tagId}/migrate`, { target_tag_id: targetTagId })
  }

  async batchMigrateTemplates(templateIds: number[], targetTagId: number, sourceTagId?: number) {
    return this.request<{ migrated_count: number }>('POST', '/templates/batch-migrate-tags', {
      template_ids: templateIds,
      target_tag_id: targetTagId,
      source_tag_id: sourceTagId
    })
  }

  // 模板标签统计
  async getTemplateTagSummary(ownerOperatorId?: number) {
    return this.request<{ total: number; no_tag_count: number; tagged_count: number; tag_counts: Array<{ tag_id: number; tag_name: string; category_id: number; template_count: number }> }>('GET', '/templates/tag-summary', undefined, ownerOperatorId ? { owner_operator_id: ownerOperatorId } : undefined)
  }

  async deleteMaterialTag(id: number) {
    return this.request('DELETE', `/materials/tags/${id}`)
  }

  async getMaterialTagStats(id: number) {
    return this.request<MaterialTagStats>('GET', `/materials/tags/${id}/stats`)
  }

  async getMaterialCategoryStats(id: number) {
    return this.request<{ category_id: number; material_count: number; tag_count: number }>('GET', `/materials/categories/${id}/stats`)
  }

  async getMaterialPlatformStats(id: number) {
    return this.request<{ platform_id: number; material_count: number; category_count: number; tag_count: number }>('GET', `/materials/platforms/${id}/stats`)
  }

  async migrateTagMaterials(tagId: number, targetTagId: number) {
    return this.request<{ source_tag_id: number; target_tag_id: number; migrated_count: number }>('POST', `/materials/tags/${tagId}/migrate`, {
      target_tag_id: targetTagId
    })
  }

  async batchMigrateMaterials(materialIds: number[], targetTagId: number, sourceTagId?: number) {
    return this.request<{ target_tag_id: number; migrated_count: number }>('POST', '/materials/batch-migrate-tags', {
      material_ids: materialIds,
      target_tag_id: targetTagId,
      source_tag_id: sourceTagId
    })
  }

  async batchTransferMaterials(params: {
    material_ids: number[];
    target_operator_id: number;
    target_platform_id: number;
    target_category_id: number;
    target_tag_ids: number[];
  }) {
    return this.request<{
      total_count: number
      success_count: number
      failed_count: number
      failed_ids: number[]
      created_material_ids: number[]
    }>('POST', '/materials/batch-transfer', params)
  }

  async getMaterialTagSummary(params?: { owner_operator_id?: number | null }) {
    return this.request<MaterialTagSummary>('GET', '/materials/tag-summary', undefined, params)
  }

  // ==================== 素材管理接口 ====================

  async getMaterials(params?: PaginationParams & {
    keyword?: string
    platform_id?: number
    category_id?: number
    tag_id?: number
    no_tag?: boolean
    content_type?: ContentType | 'mix'
    library_type?: 'creation' | 'benchmark'
    status?: 'available' | 'disabled'
    is_favorite?: boolean
    favorite_user_id?: number
    owner_operator_id?: number | null
  }) {
    return this.request<PaginationResponse<Material>>('GET', '/materials', undefined, params)
  }

  async getMaterial(id: number) {
    return this.request<Material>('GET', `/materials/${id}`)
  }

  async createMaterial(data: any) {
    return this.request<Material>('POST', '/materials', data)
  }

  async uploadMaterial(data: {
    title: string
    content: string
    topic: string
    text_content?: string
    source_url?: string
    source_type?: string
    content_type?: string
    tag_ids?: number[]
    files?: File[]
  }) {
    const formData = new FormData()
    formData.append('title', data.title)
    formData.append('content', data.content)
    formData.append('topic', data.topic)

    if (data.text_content) formData.append('text_content', data.text_content)
    if (data.source_url) formData.append('source_url', data.source_url)
    if (data.source_type) formData.append('source_type', data.source_type)
    if (data.content_type) formData.append('content_type', data.content_type)
    if (data.tag_ids && data.tag_ids.length > 0) {
      formData.append('tag_ids', data.tag_ids.join(','))
    }
    if (data.files) {
      data.files.forEach(file => {
        formData.append('files', file)
      })
    }

    const currentToken = localStorage.getItem('access_token')
    const headers: Record<string, string> = {}
    if (currentToken) {
      headers['Authorization'] = `Bearer ${currentToken}`
    }
    // 注意：不设置 Content-Type，让浏览器自动设置 multipart/form-data + boundary

    const url = `${this.baseUrl}/materials/upload`
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    })

    const result = await this.handleResponse(response)
    return result.data as Material
  }

  async updateMaterial(id: number, data: any) {
    return this.request<Material>('PUT', `/materials/${id}`, data)
  }

  async updateMaterialWithAttachments(data: {
    id: number
    title?: string
    content?: string
    topic?: string
    content_type?: string
    text_content?: string
    tag_ids?: number[]
    platform_id?: number
    category_id?: number
    source_url?: string
    delete_attachment_ids?: number[]
    files?: File[]
  }) {
    const formData = new FormData()
    if (data.title !== undefined) formData.append('title', data.title)
    if (data.content !== undefined) formData.append('content', data.content)
    if (data.topic !== undefined) formData.append('topic', data.topic)
    if (data.content_type) formData.append('content_type', data.content_type)
    if (data.text_content) formData.append('text_content', data.text_content)
    if (data.platform_id !== undefined && data.platform_id !== null) {
      formData.append('platform_id', String(data.platform_id))
    }
    if (data.category_id !== undefined && data.category_id !== null) {
      formData.append('category_id', String(data.category_id))
    }
    if (data.source_url) formData.append('source_url', data.source_url)
    if (data.tag_ids && data.tag_ids.length > 0) {
      formData.append('tag_ids', data.tag_ids.join(','))
    }
    if (data.delete_attachment_ids && data.delete_attachment_ids.length > 0) {
      formData.append('delete_attachment_ids', data.delete_attachment_ids.join(','))
    }
    if (data.files) {
      data.files.forEach(file => {
        formData.append('files', file)
      })
    }

    const currentToken = localStorage.getItem('access_token')
    const headers: Record<string, string> = {}
    if (currentToken) {
      headers['Authorization'] = `Bearer ${currentToken}`
    }

    const url = `${this.baseUrl}/materials/${data.id}/update-with-attachments`
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    })

    const result = await this.handleResponse(response)
    return result.data as Material
  }

  async deleteMaterial(id: number) {
    return this.request('DELETE', `/materials/${id}`)
  }

  async copyMaterial(id: number, data?: { title?: string; target_operator_id?: number; tag_ids?: number[] }) {
    return this.request<Material>('POST', `/materials/${id}/copy`, data)
  }

  async favoriteMaterial(id: number) {
    return this.request<{ is_favorite: boolean }>('POST', `/materials/${id}/favorite`)
  }

  async addMaterialAttachment(materialId: number, data: {
    file_type: 'image' | 'video'
    file_url: string
    file_name: string
    file_size?: number
    sort_order?: number
    width?: number
    height?: number
    duration?: number
    thumbnail_url?: string
  }) {
    return this.request<MaterialAttachment>('POST', `/materials/${materialId}/attachments`, data)
  }

  async getMaterialCategories(platformId?: number) {
    return this.request<MaterialCategory[]>('GET', '/materials/categories', undefined, platformId ? { platform_id: platformId } : undefined)
  }

  async createMaterialCategory(data: {
    name: string
    platform_id: number
    description?: string
    color?: string
    sort_order?: number
  }) {
    return this.request<MaterialCategory>('POST', '/materials/categories', data)
  }

  async updateMaterialCategory(id: number, data: { name?: string; description?: string; color?: string; sort_order?: number }) {
    return this.request<MaterialCategory>('PUT', `/materials/categories/${id}`, data)
  }

  async deleteMaterialCategory(id: number) {
    return this.request('DELETE', `/materials/categories/${id}`)
  }

  async getMaterialTags(params?: {
    category_id?: number
    owner_operator_id?: number
  }) {
    return this.request<MaterialTag[]>('GET', '/materials/tags', undefined, params)
  }

  async createMaterialTag(data: {
    name: string
    category_id: number
    description?: string
    color?: string
  }) {
    return this.request<MaterialTag>('POST', '/materials/tags', data)
  }

  async updateMaterialTag(id: number, data: { name?: string; description?: string; color?: string }) {
    return this.request<MaterialTag>('PUT', `/materials/tags/${id}`, data)
  }

  // ==================== 素材批量操作接口 ====================

  async batchDeleteMaterials(materialIds: number[]) {
    return this.request<{ success_count: number; failed_ids: number[] }>('DELETE', '/materials/batch', {
      material_ids: materialIds
    })
  }

  async batchUpdateMaterialStatus(materialIds: number[], status: 'available' | 'disabled') {
    return this.request<{ success_count: number; failed_ids: number[] }>('PUT', '/materials/batch-status', {
      material_ids: materialIds,
      status
    })
  }

  async batchCopyMaterials(params: {
    material_ids: number[];
    new_titles?: Record<string, string>;
    target_operator_id?: number;
    target_platform_id: number;
    target_category_id: number;
    target_tag_ids: number[];
  }) {
    return this.request<{ success_count: number; failed_ids: number[]; new_material_ids: number[] }>('POST', '/materials/batch-copy', params)
  }

  async transferMaterial(materialId: number, targetOperatorId: number) {
    return this.request<{ material_id: number; new_owner_id: number }>('POST', `/materials/${materialId}/transfer`, {
      target_operator_id: targetOperatorId
    })
  }

  // ==================== 内容生成接口 ====================

  async createGenerationTask(data: CreateGenerationTaskRequest) {
    return this.request<GenerationTask>('POST', '/generation/tasks', data)
  }

  async getGenerationTasks(params?: PaginationParams & {
    status?: TaskStatus
    keyword?: string
    start_date?: string
    end_date?: string
    operator_id?: number
  }) {
    return this.request<PaginationResponse<GenerationTaskListItem>>('GET', '/generation/tasks', undefined, params)
  }

  async getGenerationTask(id: number) {
    return this.request<GenerationTask>('GET', `/generation/tasks/${id}`)
  }

  async cancelGenerationTask(id: number) {
    return this.request<GenerationTask>('POST', `/generation/tasks/${id}/cancel`)
  }

  async updateGenerationTask(id: number, data: Partial<GenerationTask>) {
    return this.request<GenerationTask>('PATCH', `/generation/tasks/${id}`, data)
  }

  async recalculateTaskCounts(id: number) {
    return this.request<GenerationTask>('POST', `/generation/tasks/${id}/recalculate`)
  }

  async getGenerationItems(taskId: number, params?: PaginationParams & {
    status?: ItemStatus
  }) {
    return this.request<PaginationResponse<GenerationItem>>('GET', `/generation/tasks/${taskId}/items`, undefined, params)
  }

  async getGenerationItem(id: number) {
    return this.request<GenerationItem>('GET', `/generation/items/${id}`)
  }

  async getGenerationItemDetail(id: number) {
    return this.request<GenerationItemDetail>('GET', `/generation/items/${id}/detail`)
  }

  async retryGenerationItem(id: number) {
    return this.request<GenerationItem>('POST', `/generation/items/${id}/retry`)
  }

  async regenerateGenerationItem(id: number) {
    return this.request<GenerationItem>('POST', `/generation/items/${id}/regenerate`)
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

  async batchRetryGenerationItems(data: { item_ids?: number[]; task_id?: number }) {
    return this.request<GenerationItem[]>('POST', '/generation/items/batch-retry', data)
  }

  async batchPauseGenerationItems(data: { item_ids: number[]; pause: boolean }) {
    return this.request<GenerationItem[]>('POST', '/generation/items/batch-pause', data)
  }

  async getItemExecutionLogs(itemId: number) {
    return this.request<ExecutionLog[]>('GET', `/generation/items/${itemId}/execution-logs`)
  }

  async debugRerunItem(itemId: number, data: DebugRerunRequest) {
    return this.request<GenerationItem>('POST', `/generation/items/${itemId}/debug-rerun`, data)
  }

  // ==================== 调试模式 - 提示词/文案/图片生成 ====================

  async debugGeneratePrompts(data: DebugGeneratePromptsRequest) {
    return this.request<DebugGeneratePromptsResponse>('POST', '/generation/debug/generate-prompts', data)
  }

  async debugGenerateText(data: DebugGenerateTextRequest) {
    return this.request<DebugGenerateTextResponse>('POST', '/generation/debug/generate-text', data)
  }

  async debugGenerateImages(data: DebugGenerateImagesRequest) {
    return this.request<DebugGenerateImagesResponse>('POST', '/generation/debug/generate-images', data)
  }

  async publishGenerationItem(id: number) {
    return this.request<GenerationItem>('POST', `/generation/items/${id}/publish`)
  }

  async getSubUserGenerationItems(params?: { page?: number; limit?: number; start_date?: string; end_date?: string; distribution_status?: string }) {
    return this.request<{ items: GenerationItem[]; total: number }>('GET', '/generation/sub-user-items', undefined, params)
  }

  // ==================== 模型配置接口 ====================

  async getModelConfigs() {
    // 添加时间戳参数，避免浏览器缓存
    const params = { _t: Date.now() }
    return this.request<ModelConfig[]>('GET', '/settings/model-configs', undefined, params)
  }

  async getPlatformModelTypes() {
    return this.request<Record<string, string[]>>('GET', '/settings/platform-model-types')
  }

  async getModelConfig(id: number) {
    return this.request<ModelConfig>('GET', `/settings/model-configs/${id}`)
  }

  async createModelConfig(data: CreateModelConfigRequest) {
    return this.request<ModelConfig>('POST', '/settings/model-configs', data)
  }

  async updateModelConfig(id: number, data: UpdateModelConfigRequest) {
    return this.request<ModelConfig>('PUT', `/settings/model-configs/${id}`, data)
  }

  async deleteModelConfig(id: number) {
    return this.request('DELETE', `/settings/model-configs/${id}`)
  }

  // ==================== 用户默认模型接口 ====================

  async getUserDefaultModels() {
    return this.request<UserDefaultModelResponse>('GET', '/settings/user-default-models')
  }

  async updateUserDefaultModels(data: UserDefaultModelUpdate) {
    return this.request<UserDefaultModelResponse>('PUT', '/settings/user-default-models', data)
  }

  // ==================== 仪表盘接口 ====================

  async getDashboardStats(params?: { start_date?: string; end_date?: string; operator_id?: number }) {
    return this.request<DashboardStats>('GET', '/dashboard/stats', undefined, params)
  }

  async getDashboardTrend(params?: { days?: number }) {
    return this.request<DashboardTrend>('GET', '/dashboard/trend', undefined, params)
  }

  async getDashboardRecentTasks(params?: { 
    limit?: number
    page?: number
    operator_id?: number
    start_date?: string
    end_date?: string
  }) {
    return this.request<DashboardRecentTasks>('GET', '/dashboard/recent-tasks', undefined, params)
  }

  async getDashboardFailedTasks(params?: { limit?: number }) {
    return this.request<DashboardFailedTasks>('GET', '/dashboard/failed-tasks', undefined, params)
  }

  async getOperatorList() {
    return this.request<OperatorOption[]>('GET', '/dashboard/operators')
  }

  async dismissAlert(taskId: number) {
    return this.request('POST', '/dashboard/dismiss-alert', { task_id: taskId })
  }

  async dismissAllAlerts() {
    return this.request('POST', '/dashboard/dismiss-all-alerts')
  }

  // ==================== 版本信息接口 ====================

  async getBackendVersion() {
    const response = await fetch('/api/version')
    const result = await response.json()
    return result.backend_version as string
  }

  // ==================== 趋势分析接口 ====================

  async getGenerationTrend(params?: TrendAnalysisParams) {
    return this.request<GenerationTrendResponse>('GET', '/trend-analysis/generation', undefined, params)
  }

  async getDistributionTrend(params?: TrendAnalysisParams) {
    return this.request<DistributionTrendResponse>('GET', '/trend-analysis/distribution', undefined, params)
  }

  async getPublishTrend(params?: TrendAnalysisParams) {
    return this.request<PublishTrendResponse>('GET', '/trend-analysis/publish', undefined, params)
  }

  async getOperatorTrend(params?: { start_date?: string; end_date?: string; operator_id?: number }) {
    return this.request<OperatorTrendResponse>('GET', '/trend-analysis/operators', undefined, params)
  }

  async getTrendAnalysisFilterOptions() {
    return this.request<TrendAnalysisFilterOptions>('GET', '/trend-analysis/filter-options')
  }

  // ==================== 操作日志接口 ====================

  async createOperationLog(params: OperationLogCreateParams) {
    return this.request<{ id: number; created_at: string }>('POST', '/operation-logs', params)
  }

  async getOperationLogs(params?: OperationLogQueryParams) {
    return this.request<PaginationResponse<OperationLog>>('GET', '/operation-logs', undefined, params)
  }

  async getOperationLog(id: number) {
    return this.request<OperationLog>('GET', `/operation-logs/${id}`)
  }

  // ==================== 创意种子接口 ====================

  async getCreativeSeeds(params?: PaginationParams & {
    seed_type?: 'opening' | 'emotion' | 'ending'
    status?: 'enabled' | 'disabled'
  }) {
    return this.request<PaginationResponse<any>>('GET', '/creative-seeds', undefined, params)
  }

  async getCreativeSeed(id: number) {
    return this.request<any>('GET', `/creative-seeds/${id}`)
  }

  async createCreativeSeed(data: {
    name: string
    seed_type: 'opening' | 'emotion' | 'ending'
    template: string
    description?: string
    forbidden_patterns?: string[]
    example_phrases?: string[]
    avoid_phrases?: string[]
    category?: string
  }) {
    return this.request<any>('POST', '/creative-seeds', data)
  }

  async updateCreativeSeed(id: number, data: {
    name?: string
    template?: string
    description?: string
    forbidden_patterns?: string[]
    example_phrases?: string[]
    avoid_phrases?: string[]
    status?: 'enabled' | 'disabled'
    category?: string
  }) {
    return this.request<any>('PUT', `/creative-seeds/${id}`, data)
  }

  async deleteCreativeSeed(id: number) {
    return this.request<void>('DELETE', `/creative-seeds/${id}`)
  }

  // ==================== 平台配置接口 ====================

  async getViralTypes() {
    return this.request<{ value: string; label: string; description: string; keywords?: string[] }[]>('GET', '/config/viral-types')
  }

  async getTemplateOptions() {
    return this.request<{
      viral_types: { value: string; label: string; description: string; keywords?: string[] }[]
      image_size_ratios: { value: string; label: string; description: string }[]
      content_types: { value: string; label: string; description: string }[]
      categories: string[]
      seed_types: Record<string, { label: string; description: string }>
    }>('GET', '/config/template-options')
  }

  // ==================== 定时任务接口 ====================

  async getScheduledTasks(params?: PaginationParams & {
    keyword?: string
    status?: ScheduledTaskStatus
    task_type?: ScheduledTaskType
    operator_id?: number
  }) {
    return this.request<PaginationResponse<ScheduledTaskListItem>>('GET', '/scheduled-tasks', undefined, params)
  }

  async getScheduledTask(id: number) {
    return this.request<ScheduledTask>('GET', `/scheduled-tasks/${id}`)
  }

  async createScheduledTask(data: CreateScheduledTaskRequest) {
    return this.request<ScheduledTask>('POST', '/scheduled-tasks', data)
  }

  async updateScheduledTask(id: number, data: UpdateScheduledTaskRequest) {
    return this.request<ScheduledTask>('PUT', `/scheduled-tasks/${id}`, data)
  }

  async deleteScheduledTask(id: number) {
    return this.request('DELETE', `/scheduled-tasks/${id}`)
  }

  async toggleScheduledTask(id: number, isActive: boolean) {
    return this.request<ScheduledTask>('POST', `/scheduled-tasks/${id}/toggle?is_active=${isActive}`)
  }

  async executeScheduledTask(id: number) {
    return this.request<{ execution_id: number; generation_task_id: number }>('POST', `/scheduled-tasks/${id}/execute`)
  }

  async getScheduledTaskExecutions(taskId: number, params?: PaginationParams) {
    return this.request<PaginationResponse<ScheduledTaskExecution>>('GET', `/scheduled-tasks/${taskId}/executions`, undefined, params)
  }

  // ==================== 任务队列管理接口 ====================

  async getQueueStatus() {
    return this.request<QueueStatusData>('GET', '/task-queue/status')
  }

  async getWorkerStatus() {
    return this.request<{
      worker_running_count: number
      worker_idle_count: number
      worker_total: number
      workers: Array<{
        name: string
        running_tasks: number
        status: 'running' | 'idle'
        pool?: number | string
      }>
      error?: string
    }>('GET', '/task-queue/workers')
  }

  async getQueueConfig() {
    return this.request<QueueConfig>('GET', '/task-queue/config')
  }

  async updateQueueConfig(maxConcurrent: number) {
    return this.request<{ max_concurrent: number; message: string }>('PUT', '/task-queue/config', { max_concurrent: maxConcurrent })
  }

  async triggerDispatch(maxDispatch?: number) {
    const params: any = {}
    if (maxDispatch !== undefined) {
      params.max_dispatch = maxDispatch
    }
    return this.request<DispatchResult>('POST', '/task-queue/dispatch', undefined, params)
  }

  async clearWaitingQueue(confirm: boolean = true) {
    return this.request<ClearQueueResult>('DELETE', `/task-queue/clear?confirm=${confirm}`)
  }

  async recoverStaleTasks(timeoutMinutes?: number) {
    const params: any = {}
    if (timeoutMinutes !== undefined) {
      params.timeout_minutes = timeoutMinutes
    }
    return this.request<RecoverStaleResult>('POST', '/task-queue/recover-stale', undefined, params)
  }

  async getActiveTasks() {
    return this.request<QueueActiveTask[]>('GET', '/task-queue/active')
  }

  async getWaitingTasks(limit?: number) {
    const params: any = {}
    if (limit !== undefined) {
      params.limit = limit
    }
    return this.request<QueueWaitingTask[]>('GET', '/task-queue/waiting', undefined, params)
  }
}

// 创建默认的API客户端实例 - 使用相对路径通过Vite代理
export const apiClient = new ApiClient('/api/v1')

export default apiClient
