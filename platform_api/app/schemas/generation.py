"""
内容生成 Schema (generation.py)

包含内容生成相关的 Pydantic 模型。

Author: Claude Code
Date: 2025
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from .common import BaseSchema


class MaterialBrief(BaseModel):
    """
    素材简要信息（用于任务详情展示）
    """
    id: int = Field(..., description="素材ID")
    title: str = Field(..., description="素材标题")
    content_type: str = Field(..., description="内容类型")
    content: Optional[str] = Field(default=None, description="素材正文/内容")
    topic: Optional[str] = Field(default=None, description="素材话题")
    thumbnails: Optional[List[str]] = Field(default=None, description="缩略图URL列表")


class TemplateInfo(BaseModel):
    """
    模板简要信息（用于任务详情展示）
    """
    id: int = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(default=None, description="提示词创意（素材创作要点）")
    prompt_template: Optional[str] = Field(default=None, description="提示词指令（完整提示词）")
    thumbnails: Optional[List[str]] = Field(default=None, description="模板附件缩略图URL列表")
    image_size_ratio: Optional[str] = Field(default=None, description="输出图片尺寸比例（如 16:9）")
    add_watermark: Optional[bool] = Field(default=None, description="是否添加输出图片水印")
    platform_name: Optional[str] = Field(default=None, description="所属内容平台名称（如小红书、抖音）")
    # 爆款模板新增字段
    viral_type: Optional[str] = Field(default=None, description="爆款类型值")
    viral_type_label: Optional[str] = Field(default=None, description="爆款类型名称（随机/指定）")
    opening_seed_name: Optional[str] = Field(default=None, description="开头模式种子名称")
    emotion_seed_name: Optional[str] = Field(default=None, description="情感基调种子名称")
    ending_seed_name: Optional[str] = Field(default=None, description="结尾模式种子名称")
    product_selling_points: Optional[str] = Field(default=None, description="产品卖点描述")


class GenerationTaskBase(BaseModel):
    """
    生成任务基础信息
    """
    name: Optional[str] = Field(default=None, description="任务名称", max_length=200)
    material_id: Optional[int] = Field(default=None, description="素材创作(创作库素材ID)")
    benchmark_material_id: Optional[int] = Field(default=None, description="素材对标(对标库素材ID)")
    model_platform: Optional[str] = Field(default=None, description="选择的文本模型平台", max_length=100)
    model_id: Optional[str] = Field(default=None, description="选择的文本模型", max_length=100)
    image_model_platform: Optional[str] = Field(default=None, description="选择的图片模型平台", max_length=100)
    image_model_id: Optional[str] = Field(default=None, description="选择的图片模型", max_length=100)
    model_selection_mode: str = Field(default="auto", description="模型选择模式：auto / manual")
    max_concurrency: int = Field(default=5, description="本次任务最大并发数", ge=1, le=50)
    variable_values_json: Optional[Dict[str, Any]] = Field(default=None, description="变量值JSON")
    dedup_rules_json: Optional[Dict[str, Any]] = Field(default=None, description="去重规则JSON")
    # 新增字段
    image_count: int = Field(default=4, description="生成图片数量", ge=1, le=10)
    # 文案去重配置
    dedup_enabled: Optional[bool] = Field(default=False, description="文案去重检测开关")
    dedup_threshold: Optional[float] = Field(default=0.9, description="文案去重阈值")
    dedup_retry_count: Optional[int] = Field(default=3, description="文案去重失败重试次数")
    dedup_scope: Optional[List[str]] = Field(default=None, description="文案去重范围配置：subuser_history/current_task/all_history")
    # 图片去重配置（独立于文案去重）
    image_dedup_enabled: Optional[bool] = Field(default=False, description="图片去重检测开关")
    image_dedup_threshold: Optional[float] = Field(default=0.9, description="图片相似度阈值（高于此值认为相似）")
    image_dedup_retry_count: Optional[int] = Field(default=3, description="图片去重失败重试次数")
    image_dedup_scope: Optional[List[str]] = Field(default=None, description="图片去重范围：subuser_image_history/current_task_images/all_image_history")
    # 素材对标配置
    benchmark_text_enabled: Optional[bool] = Field(default=False, description="文案对标开关")
    benchmark_image_enabled: Optional[bool] = Field(default=False, description="图片对标开关")
    benchmark_image_reference_options: Optional[List[str]] = Field(default=None, description="图片参考选项：composition（构图）/ scene（场景）/ style（风格）")
    # 图片角色配置（交互式编辑）
    benchmark_image_roles_json: Optional[Dict[str, List[str]]] = Field(default=None, description="对标图角色配置，如{'image_1': ['composition', 'scene']}")
    template_product_mapping_json: Optional[Dict[str, str]] = Field(default=None, description="模板产品映射，如{'product_1': 'template_images[0]'}")


class GenerationTaskCreate(GenerationTaskBase):
    """
    创建生成任务请求
    """
    template_ids: Optional[List[int]] = Field(default=None, description="模板ID列表(已废弃，使用素材创作)")
    sub_user_ids: List[int] = Field(..., description="创作者ID列表")


class GenerationTaskUpdate(BaseModel):
    """
    更新生成任务请求
    """
    status: Optional[str] = Field(default=None, description="状态")
    # 模型配置
    model_platform: Optional[str] = Field(default=None, description="文本模型平台")
    model_id: Optional[str] = Field(default=None, description="文本模型ID")
    image_model_platform: Optional[str] = Field(default=None, description="图片模型平台")
    image_model_id: Optional[str] = Field(default=None, description="图片模型ID")
    # 去重配置
    dedup_enabled: Optional[bool] = Field(default=None, description="文案去重开关")
    image_dedup_enabled: Optional[bool] = Field(default=None, description="图片去重开关")


class GenerationTaskResponse(GenerationTaskBase, BaseSchema):
    """
    生成任务响应
    """
    status: str = Field(..., description="状态")
    total_count: int = Field(..., description="子任务总数")
    queued_count: int = Field(..., description="队列中数量")
    generating_count: int = Field(..., description="生成中数量")
    completed_count: int = Field(..., description="已完成数")
    failed_count: int = Field(..., description="失败数")
    paused_count: int = Field(..., description="已暂停数量")
    distributed_count: int = Field(..., description="已分发数量")
    pending_publish_count: int = Field(..., description="待发布数量")
    published_count: int = Field(..., description="已发布数量")
    created_by: Optional[int] = Field(default=None, description="发起者创作管理员ID")
    owner_admin_id: Optional[int] = Field(default=None, description="所属创作管理员ID")
    owner_admin_name: Optional[str] = Field(default=None, description="所属创作管理员名称")
    template_id: Optional[int] = Field(default=None, description="模板创作ID（主模板ID）")
    template_info: Optional[TemplateInfo] = Field(default=None, description="模板创作信息")
    material_info: Optional[MaterialBrief] = Field(default=None, description="素材对标信息")
    benchmark_material_info: Optional[MaterialBrief] = Field(default=None, description="对标素材信息")
    # 任务耗时
    duration_seconds: Optional[int] = Field(default=None, description="任务总耗时秒数（从创建到完成的时长）")
    completed_at: Optional[datetime] = Field(default=None, description="任务完成时间")


class GenerationItemBase(BaseModel):
    """
    生成子任务基础信息
    """
    generated_title: Optional[str] = Field(default=None, description="生成的标题")
    generated_text: Optional[str] = Field(default=None, description="生成的文本内容")
    generated_image_urls_json: Optional[List[str]] = Field(default=None, description="生成的图片URL列表")
    generated_image_thumbnails_json: Optional[List[str]] = Field(default=None, description="生成的图片缩略图URL列表")
    generated_video_url: Optional[str] = Field(default=None, description="生成的视频URL", max_length=500)
    output_topics: Optional[List[str]] = Field(default=None, description="输出话题")
    status: str = Field(default="queued", description="状态")
    distribution_status: str = Field(default="draft", description="分发状态")


class GenerationItemUpdate(BaseModel):
    """
    更新生成子任务请求
    """
    status: Optional[str] = Field(default=None, description="状态")
    distribution_status: Optional[str] = Field(default=None, description="分发状态")


class GenerationItemResponse(GenerationItemBase, BaseSchema):
    """
    生成子任务响应（列表展示用）
    """
    task_id: int = Field(..., description="任务ID")
    task_name: Optional[str] = Field(default=None, description="任务名称")
    sub_user_id: int = Field(..., description="目标创作者ID")
    sub_user_name: Optional[str] = Field(default=None, description="创作者名称快照")
    template_id: Optional[int] = Field(default=None, description="使用的模板")
    model_platform: Optional[str] = Field(default=None, description="实际使用的模型平台")
    model_id: Optional[str] = Field(default=None, description="实际使用的模型")
    image_model_platform: Optional[str] = Field(default=None, description="实际使用的图片模型平台")
    image_model_id: Optional[str] = Field(default=None, description="实际使用的图片模型")
    retry_count: int = Field(..., description="重试次数")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    final_prompt: Optional[str] = Field(default=None, description="最终发送给模型的完整提示词")
    queued_at: Optional[datetime] = Field(default=None, description="进入队列时间")
    started_at: Optional[datetime] = Field(default=None, description="开始生成时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    distributed_at: Optional[datetime] = Field(default=None, description="分发时间")
    confirmed_at: Optional[datetime] = Field(default=None, description="确认发布时间")
    # 执行情况
    execution_started_at: Optional[datetime] = Field(default=None, description="子任务执行开始时间")
    execution_ended_at: Optional[datetime] = Field(default=None, description="子任务执行结束时间")
    execution_result: Optional[str] = Field(default=None, description="执行结果：success / failed / partial")
    # 当前步骤（用于 UI 细粒度状态展示）
    current_step: Optional[str] = Field(default=None, description="当前执行步骤")


class SubUserItemsListResponse(BaseModel):
    """
    创作者内容列表响应
    """
    items: List[GenerationItemResponse] = Field(..., description="内容项列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    limit: int = Field(..., description="每页数量")


class GenerationItemDetailResponse(BaseModel):
    """
    生成子任务详情响应（含完整输入/输出内容）
    """
    id: int = Field(..., description="子任务ID")
    task_id: int = Field(..., description="任务ID")
    sub_user_id: int = Field(..., description="目标创作者ID")
    sub_user_name: Optional[str] = Field(default=None, description="创作者名称快照")
    template_id: Optional[int] = Field(default=None, description="使用的模板")
    model_platform: Optional[str] = Field(default=None, description="实际使用的模型平台")
    model_id: Optional[str] = Field(default=None, description="实际使用的模型")
    image_model_platform: Optional[str] = Field(default=None, description="实际使用的图片模型平台")
    image_model_id: Optional[str] = Field(default=None, description="实际使用的图片模型")

    # 生成结果
    generated_title: Optional[str] = Field(default=None, description="生成的标题")
    generated_text: Optional[str] = Field(default=None, description="生成的文本内容")
    text_file_url: Optional[str] = Field(default=None, description="文案文件URL")
    generated_image_urls_json: Optional[List[str]] = Field(default=None, description="生成的图片URL列表")
    generated_image_thumbnails_json: Optional[List[str]] = Field(default=None, description="生成的图片缩略图URL列表")
    generated_video_url: Optional[str] = Field(default=None, description="生成的视频URL")
    output_topics: Optional[List[str]] = Field(default=None, description="输出话题")

    # 状态
    status: str = Field(default="queued", description="状态")
    retry_count: int = Field(..., description="重试次数")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    distribution_status: str = Field(default="draft", description="分发状态")
    queued_at: Optional[datetime] = Field(default=None, description="进入队列时间")
    started_at: Optional[datetime] = Field(default=None, description="开始生成时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    distributed_at: Optional[datetime] = Field(default=None, description="分发时间")
    confirmed_at: Optional[datetime] = Field(default=None, description="确认发布时间")

    # 输入内容 - 模板信息
    input_prompt_creativity: Optional[str] = Field(default=None, description="模板提示词创意")
    input_prompt_instruction: Optional[str] = Field(default=None, description="模板提示词指令")
    input_template_images_json: Optional[List[str]] = Field(default=None, description="模板图片URL列表")
    input_image_size_ratio: Optional[str] = Field(default=None, description="输出图片尺寸比例")
    input_watermark: Optional[bool] = Field(default=None, description="输出图片水印开关")
    # 输入内容 - 模板扩展信息
    input_template_name: Optional[str] = Field(default=None, description="模板名称")
    input_viral_type: Optional[str] = Field(default=None, description="爆款类型")
    input_product_selling_points: Optional[str] = Field(default=None, description="产品卖点")
    input_opening_seed_name: Optional[str] = Field(default=None, description="开头模式种子名称")
    input_emotion_seed_name: Optional[str] = Field(default=None, description="情感基调种子名称")
    input_ending_seed_name: Optional[str] = Field(default=None, description="结尾模式种子名称")

    # 输入内容 - 素材对标信息
    input_benchmark_title: Optional[str] = Field(default=None, description="素材对标标题")
    input_benchmark_content: Optional[str] = Field(default=None, description="素材对标内容")
    input_benchmark_topic: Optional[str] = Field(default=None, description="素材对标话题")
    input_benchmark_images_json: Optional[List[str]] = Field(default=None, description="素材对标图片URL列表")
    # 输入内容 - 素材对标配置
    input_benchmark_text_enabled: Optional[bool] = Field(default=None, description="文案对标开关")
    input_benchmark_image_enabled: Optional[bool] = Field(default=None, description="图片对标开关")
    input_benchmark_image_reference_options: Optional[List[str]] = Field(default=None, description="图片参考选项")
    # 输入内容 - 图片角色配置（交互式编辑）
    input_benchmark_image_roles_json: Optional[Dict[str, List[str]]] = Field(default=None, description="对标图角色配置快照")
    input_template_product_mapping_json: Optional[Dict[str, str]] = Field(default=None, description="模板产品映射快照")

    # 输入内容 - 创作者信息
    input_sub_user_profile: Optional[str] = Field(default=None, description="创作者粉丝画像")
    input_sub_user_positioning: Optional[str] = Field(default=None, description="创作者账号定位")
    input_sub_user_style: Optional[str] = Field(default=None, description="创作者内容风格")

    # 输出内容 - AIGC重构提示词
    aigc_generated_prompt: Optional[str] = Field(default=None, description="AIGC提示词生成器产出的精炼提示词")
    output_system_text_prompt: Optional[str] = Field(default=None, description="AIGC文案系统提示词")
    output_user_text_prompt: Optional[str] = Field(default=None, description="AIGC文案用户提示词")
    output_user_image_prompt: Optional[str] = Field(default=None, description="图片用户提示词（自包含完整创作指导）")

    # 调试
    final_prompt: Optional[str] = Field(default=None, description="最终发送给模型的完整提示词")

    # 执行情况
    execution_started_at: Optional[datetime] = Field(default=None, description="子任务执行开始时间")
    execution_ended_at: Optional[datetime] = Field(default=None, description="子任务执行结束时间")
    execution_result: Optional[str] = Field(default=None, description="执行结果")

    # AIGC 生成的用户提示词
    aigc_user_text_generator_user_prompt: Optional[str] = Field(default=None, description="AIGC生成的文案用户提示词")
    aigc_user_image_prompts_json: Optional[List[str]] = Field(default=None, description="AIGC生成的图片用户提示词列表")

    # 去重检测
    dedup_check_passed: Optional[bool] = Field(default=None, description="去重检测是否通过")
    dedup_similarity: Optional[float] = Field(default=None, description="最大相似度")
    dedup_referenced_items_json: Optional[List[Dict[str, Any]]] = Field(default=None, description="相似内容引用")
    dedup_checked_at: Optional[datetime] = Field(default=None, description="去重检测时间")

    # 当前步骤
    current_step: Optional[str] = Field(default=None, description="当前执行步骤")
    generated_image_count: Optional[int] = Field(default=None, description="实际生成图片数量")

    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class GenerationTaskProgressLogResponse(BaseSchema):
    """
    任务进度日志响应
    """
    task_id: int = Field(..., description="任务ID")
    queued_count: int = Field(..., description="队列中数量")
    generating_count: int = Field(..., description="生成中数量")
    completed_count: int = Field(..., description="已完成数量")
    failed_count: int = Field(..., description="失败数量")
    status: str = Field(..., description="任务状态")
    progress_message: Optional[str] = Field(default=None, description="进度信息")


class BatchRetryRequest(BaseModel):
    """
    批量重试请求
    """
    item_ids: Optional[List[int]] = Field(default=None, description="要重试的子任务ID列表（留空则使用 task_id）")
    task_id: Optional[int] = Field(default=None, description="任务ID（当 item_ids 为空时， 重试该任务下所有失败项）")


class BatchPauseRequest(BaseModel):
    """
    批量暂停请求
    """
    item_ids: Optional[List[int]] = Field(default=None, description="要暂停的子任务ID列表（留空则暂停所有可暂停项）")
    pause: bool = Field(..., description="true=暂停, false=继续")


class ExecutionLogResponse(BaseModel):
    """
    子任务执行日志响应
    """
    id: int = Field(..., description="主键ID")
    item_id: int = Field(..., description="子任务ID")
    node_name: str = Field(..., description="节点名称")
    node_status: str = Field(..., description="节点状态")
    input_data: Optional[Dict[str, Any]] = Field(default=None, description="节点输入数据")
    output_data: Optional[Dict[str, Any]] = Field(default=None, description="节点输出数据")
    error_data: Optional[Dict[str, Any]] = Field(default=None, description="结构化错误信息")
    duration_ms: Optional[int] = Field(default=None, description="耗时毫秒")
    started_at: Optional[datetime] = Field(default=None, description="节点开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="节点完成时间")
    created_at: datetime = Field(..., description="创建时间")


class DebugRerunRequest(BaseModel):
    """
    调试重跑请求
    """
    prompt_override: Optional[str] = Field(default=None, description="覆盖提示词")
    model_platform_override: Optional[str] = Field(default=None, description="覆盖模型平台")
    model_id_override: Optional[str] = Field(default=None, description="覆盖模型ID")


# ============================================
# 调试模式相关 Schema
# ============================================

class DebugGeneratePromptsRequest(BaseModel):
    """
    调试模式：提示词生成请求
    """
    item_id: int = Field(..., description="子任务ID")
    # 可选覆盖参数（生图模型不使用系统提示词）
    text_system_prompt_override: Optional[str] = Field(default=None, description="覆盖文案系统提示词")
    # 模型覆盖参数
    model_platform_override: Optional[str] = Field(default=None, description="覆盖模型平台")
    model_id_override: Optional[str] = Field(default=None, description="覆盖模型ID")


class DebugGeneratePromptsResponse(BaseModel):
    """
    调试模式：提示词生成响应
    """
    # 文案提示词生成结果
    text_prompt_success: bool = Field(..., description="文案提示词生成是否成功")
    text_prompt_error: Optional[str] = Field(default=None, description="文案提示词生成错误信息")
    text_generator_user_prompt: str = Field(..., description="文案用户提示词")
    topics: List[str] = Field(..., description="推荐话题列表")
    text_generator_system_prompt: str = Field(..., description="文案生成器系统提示词")

    # 图片提示词生成结果（生图模型不使用系统提示词）
    image_prompt_success: bool = Field(..., description="图片提示词生成是否成功")
    image_prompt_error: Optional[str] = Field(default=None, description="图片提示词生成错误信息")
    image_prompts: List[str] = Field(..., description="图片用户提示词列表（自包含完整创作指导）")

    # 参考图片（用于图片生成）
    reference_image_urls: Optional[List[str]] = Field(default=None, description="参考图片URL列表")


class DebugGenerateTextRequest(BaseModel):
    """
    调试模式：文案生成请求
    """
    item_id: int = Field(..., description="子任务ID")
    # 可选覆盖参数
    system_prompt_override: Optional[str] = Field(default=None, description="覆盖系统提示词")
    user_prompt_override: Optional[str] = Field(default=None, description="覆盖用户提示词")
    model_platform_override: Optional[str] = Field(default=None, description="覆盖模型平台")
    model_id_override: Optional[str] = Field(default=None, description="覆盖模型ID")


class DebugGenerateTextResponse(BaseModel):
    """
    调试模式：文案生成响应
    """
    title: str = Field(..., description="生成的标题")
    content: str = Field(..., description="生成的正文")
    topics: List[str] = Field(default_factory=list, description="生成的话题列表")
    image_prompts: List[str] = Field(default_factory=list, description="解析出的图片提示词列表")


class DebugGenerateImagesRequest(BaseModel):
    """
    调试模式：图片生成请求（生图模型不使用系统提示词）
    """
    item_id: int = Field(..., description="子任务ID")
    # 可选覆盖参数
    user_prompts_override: Optional[List[str]] = Field(default=None, description="覆盖用户提示词列表")
    model_platform_override: Optional[str] = Field(default=None, description="覆盖模型平台")
    model_id_override: Optional[str] = Field(default=None, description="覆盖模型ID")
    image_count_override: Optional[int] = Field(default=None, description="覆盖生成图片数量")
    reference_image_urls_override: Optional[List[str]] = Field(default=None, description="覆盖参考图片URL列表")


class DebugGenerateImagesResponse(BaseModel):
    """
    调试模式：图片生成响应
    """
    image_urls: List[str] = Field(..., description="生成的图片URL列表")
    reference_image_urls: Optional[List[str]] = Field(default=None, description="使用的参考图片URL列表")
