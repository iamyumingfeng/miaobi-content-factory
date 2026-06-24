"""
内容生成模型 (generation.py)

Author: Claude Code
Date: 2025
"""

from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Enum, DateTime, Text, Integer, ForeignKey, JSON, Boolean, Float
from sqlalchemy.orm import relationship

from app.core.database import Base


class ContentEmbedding(Base):
    """
    内容嵌入向量表（独立存储，用于去重优化）

    缓存所有生成内容的 embedding 向量，避免重复计算。
    支持文案和图片分别存储和对比。
    """
    __tablename__ = "content_embedding"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")

    # 关联信息
    owner_operator_id = Column(BigInteger, ForeignKey("operator.id"), nullable=False, index=True, comment="所属创作管理员ID")
    generation_item_id = Column(BigInteger, ForeignKey("generation_item.id"), nullable=True, index=True, comment="关联的生成项ID")
    task_id = Column(BigInteger, ForeignKey("generation_task.id"), nullable=True, index=True, comment="关联的任务ID")

    # 内容类型
    content_type = Column(String(20), nullable=False, index=True, comment="内容类型：text / image")
    content_index = Column(Integer, nullable=False, default=0, comment="内容索引（多张图片时使用）")

    # 嵌入向量
    embedding = Column(JSON, nullable=False, comment="嵌入向量数据")

    # 内容摘要（用于调试和展示）
    content_preview = Column(String(500), nullable=True, comment="内容预览（文案前100字/图片URL）")
    content_hash = Column(String(64), nullable=True, index=True, comment="内容哈希（用于快速查找重复内容）")

    # 使用统计
    used_for_dedup_count = Column(Integer, nullable=False, default=0, comment="用于去重检测的次数")
    last_used_at = Column(DateTime, nullable=True, comment="最后使用时间")

    # 元数据
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    # 关联
    generation_item = relationship("GenerationItem", foreign_keys=[generation_item_id])
    task = relationship("GenerationTask", foreign_keys=[task_id])

    def __repr__(self):
        return f"<ContentEmbedding(id={self.id}, type={self.content_type}, item_id={self.generation_item_id})>"


class GenerationTaskTemplate(Base):
    """
    生成任务-模板关联表
    """
    __tablename__ = "generation_task_template"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    task_id = Column(BigInteger, ForeignKey("generation_task.id"), nullable=False, comment="任务ID")
    template_id = Column(BigInteger, ForeignKey("template.id"), nullable=False, comment="模板ID")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序权重")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    # 关联
    task = relationship("GenerationTask", back_populates="task_templates", foreign_keys=[task_id])
    template = relationship("Template", back_populates="generation_task_templates", foreign_keys=[template_id])

    def __repr__(self):
        return f"<GenerationTaskTemplate(id={self.id}, task_id={self.task_id}, template_id={self.template_id})>"


class GenerationTaskSubuser(Base):
    """
    生成任务-创作者关联表
    """
    __tablename__ = "generation_task_subuser"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    task_id = Column(BigInteger, ForeignKey("generation_task.id"), nullable=False, comment="任务ID")
    sub_user_id = Column(BigInteger, ForeignKey("sub_user.id"), nullable=False, comment="创作者ID")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    # 关联
    task = relationship("GenerationTask", back_populates="task_subusers", foreign_keys=[task_id])
    sub_user = relationship("SubUser", back_populates="generation_task_subusers", foreign_keys=[sub_user_id])

    def __repr__(self):
        return f"<GenerationTaskSubuser(id={self.id}, task_id={self.task_id}, sub_user_id={self.sub_user_id})>"


class GenerationTaskProgressLog(Base):
    """
    生成任务进度快照表
    """
    __tablename__ = "generation_task_progress_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    task_id = Column(BigInteger, ForeignKey("generation_task.id"), nullable=False, comment="任务ID")
    queued_count = Column(Integer, nullable=False, default=0, comment="队列中数量")
    generating_count = Column(Integer, nullable=False, default=0, comment="生成中数量")
    completed_count = Column(Integer, nullable=False, default=0, comment="已完成数量")
    failed_count = Column(Integer, nullable=False, default=0, comment="失败数量")
    status = Column(
        Enum("pending", "processing", "completed", "failed", "cancelled", name="generation_task_status_enum"),
        nullable=False,
        comment="任务状态"
    )
    progress_message = Column(String(1000), nullable=True, comment="进度信息")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="记录时间")

    # 关联
    task = relationship("GenerationTask", back_populates="progress_logs", foreign_keys=[task_id])

    def __repr__(self):
        return f"<GenerationTaskProgressLog(id={self.id}, task_id={self.task_id}, status={self.status})>"


class GenerationTask(Base):
    """
    生成任务表

    一次批量生成为一条任务。
    """
    __tablename__ = "generation_task"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(200), nullable=True, comment="任务名称")
    material_id = Column(BigInteger, ForeignKey("material.id"), nullable=True, comment="素材创作(创作库素材)")
    benchmark_material_id = Column(BigInteger, ForeignKey("material.id"), nullable=True, comment="素材对标(对标库素材)")
    model_platform = Column(String(100), nullable=True, comment="选择的文本模型平台")
    model_id = Column(String(100), nullable=True, comment="选择的文本模型")
    image_model_platform = Column(String(100), nullable=True, comment="选择的图片模型平台")
    image_model_id = Column(String(100), nullable=True, comment="选择的图片模型")
    model_selection_mode = Column(
        Enum("auto", "manual", name="model_selection_mode_enum"),
        nullable=False,
        default="auto",
        comment="模型选择模式：auto（自动选择）/ manual（手动指定）"
    )
    max_concurrency = Column(Integer, nullable=False, default=5, comment="本次任务最大并发数")
    variable_values_json = Column(JSON, nullable=True, comment="变量值JSON")
    dedup_rules_json = Column(JSON, nullable=True, comment="去重规则JSON")
    status = Column(
        Enum("pending", "processing", "completed", "failed", "cancelled", name="generation_task_status_enum"),
        nullable=False,
        default="pending",
        comment="状态：pending（待处理）/ processing（处理中）/ completed（已完成）/ failed（失败）/ cancelled（已取消）"
    )
    total_count = Column(Integer, nullable=False, default=0, comment="子任务总数")
    queued_count = Column(Integer, nullable=False, default=0, comment="队列中数量")
    generating_count = Column(Integer, nullable=False, default=0, comment="生成中数量")
    completed_count = Column(Integer, nullable=False, default=0, comment="已完成数")
    failed_count = Column(Integer, nullable=False, default=0, comment="失败数")
    paused_count = Column(Integer, nullable=False, default=0, comment="已暂停数量")
    distributed_count = Column(Integer, nullable=False, default=0, comment="已分发数量")
    pending_publish_count = Column(Integer, nullable=False, default=0, comment="待发布数量")
    published_count = Column(Integer, nullable=False, default=0, comment="已发布数量")
    created_by = Column(BigInteger, ForeignKey("operator.id"), nullable=True, comment="发起者创作管理员ID")
    owner_operator_id = Column(BigInteger, ForeignKey("operator.id"), nullable=False, index=True, comment="所属创作管理员ID（数据隔离用）")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    started_at = Column(DateTime, nullable=True, comment="任务开始处理时间（首次变为 processing 时设置）")
    completed_at = Column(DateTime, nullable=True, comment="任务完成时间（变为最终状态时设置）")

    # ============================================
    # 去重配置（仅 GenerationTask 级别）
    # ============================================
    image_count = Column(Integer, nullable=True, default=4, comment="生成图片数量")
    # 文案去重配置
    dedup_enabled = Column(Boolean, nullable=True, default=False, comment="文案去重检测开关")
    dedup_threshold = Column(Float, nullable=True, default=0.9, comment="文案去重阈值")
    dedup_retry_count = Column(Integer, nullable=True, default=3, comment="文案去重失败重试次数")
    dedup_scope = Column(JSON, nullable=True, comment="文案去重范围配置：subuser_history/current_task/all_history")
    # 图片去重配置（独立于文案去重）
    image_dedup_enabled = Column(Boolean, nullable=True, default=False, comment="图片去重检测开关")
    image_dedup_threshold = Column(Float, nullable=True, default=0.9, comment="图片相似度阈值（高于此值认为相似）")
    image_dedup_retry_count = Column(Integer, nullable=True, default=3, comment="图片去重失败重试次数")
    image_dedup_scope = Column(JSON, nullable=True, comment="图片去重范围：subuser_image_history/current_task_images/all_image_history")

    # ============================================
    # 素材对标配置
    # ============================================
    benchmark_text_enabled = Column(Boolean, nullable=True, default=False, comment="文案对标开关")
    benchmark_image_enabled = Column(Boolean, nullable=True, default=False, comment="图片对标开关")
    benchmark_image_reference_options = Column(JSON, nullable=True, comment="图片参考选项：['composition', 'scene', 'style']")
    # 图片角色配置（交互式编辑）
    benchmark_image_roles_json = Column(JSON, nullable=True, comment="对标图角色配置，如{'image_1': ['composition', 'scene'], 'image_2': ['style']}")
    template_product_mapping_json = Column(JSON, nullable=True, comment="模板产品映射，如{'product_1': 'template_images[0]'}")

    # 关联
    owner_operator = relationship("Operator", back_populates="generation_tasks", foreign_keys=[owner_operator_id])
    material = relationship("Material", back_populates="generation_tasks", foreign_keys=[material_id])
    benchmark_material = relationship("Material", foreign_keys=[benchmark_material_id])
    task_templates = relationship("GenerationTaskTemplate", back_populates="task", foreign_keys="GenerationTaskTemplate.task_id", cascade="all, delete-orphan")
    task_subusers = relationship("GenerationTaskSubuser", back_populates="task", foreign_keys="GenerationTaskSubuser.task_id", cascade="all, delete-orphan")
    progress_logs = relationship("GenerationTaskProgressLog", back_populates="task", foreign_keys="GenerationTaskProgressLog.task_id", cascade="all, delete-orphan")
    generation_items = relationship("GenerationItem", back_populates="task", foreign_keys="GenerationItem.task_id", cascade="all, delete-orphan")
    distributions = relationship("Distribution", back_populates="task", foreign_keys="Distribution.task_id")

    def __repr__(self):
        return f"<GenerationTask(id={self.id}, status={self.status}, total_count={self.total_count})>"


class GenerationItem(Base):
    """
    生成明细表/子任务表

    一个子任务对应一个创作者 + 一个模板。
    """
    __tablename__ = "generation_item"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    task_id = Column(BigInteger, ForeignKey("generation_task.id"), nullable=False, index=True, comment="任务ID")
    sub_user_id = Column(BigInteger, ForeignKey("sub_user.id"), nullable=False, index=True, comment="目标创作者ID")
    template_id = Column(BigInteger, ForeignKey("template.id"), nullable=True, comment="使用的模板")
    model_platform = Column(String(100), nullable=True, comment="实际使用的模型平台")
    model_id = Column(String(100), nullable=True, comment="实际使用的模型")
    image_model_platform = Column(String(100), nullable=True, comment="实际使用的图片模型平台")
    image_model_id = Column(String(100), nullable=True, comment="实际使用的图片模型")
    generated_title = Column(Text, nullable=True, comment="生成的标题")
    generated_text = Column(Text, nullable=True, comment="生成的文本内容")
    text_file_url = Column(String(500), nullable=True, comment="保存到COS的文案文件URL")
    generated_image_urls_json = Column(JSON, nullable=True, comment="生成的图片URL列表JSON")
    generated_image_thumbnails_json = Column(JSON, nullable=True, comment="生成的图片缩略图URL列表JSON")
    generated_video_url = Column(String(500), nullable=True, comment="生成的视频URL")
    status = Column(
        Enum("queued", "generating", "completed", "failed", "paused", name="generation_item_status_enum"),
        nullable=False,
        default="queued",
        index=True,
        comment="生成状态：queued(待处理)/ generating(处理中)/ completed(已完成)/ failed(失败)/ paused(已暂停)"
    )
    retry_count = Column(Integer, nullable=False, default=0, comment="重试次数")
    error_message = Column(Text, nullable=True, comment="错误信息")
    queued_at = Column(DateTime, nullable=True, comment="进入队列时间")
    started_at = Column(DateTime, nullable=True, comment="开始生成时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    distribution_status = Column(
        Enum("draft", "ready", "distributed", "pending_publish", "published", name="distribution_status_enum"),
        nullable=False,
        default="draft",
        comment="分发状态：draft(草稿)/ ready(待分发)/ distributed(已分发)/ pending_publish(待发布)/ published(已发布)"
    )
    distributed_at = Column(DateTime, nullable=True, comment="分发时间")
    confirmed_at = Column(DateTime, nullable=True, comment="确认发布时间")
    owner_operator_id = Column(BigInteger, ForeignKey("operator.id"), nullable=False, index=True, comment="所属创作管理员ID（数据隔离用）")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关联
    task = relationship("GenerationTask", back_populates="generation_items", foreign_keys=[task_id])
    sub_user = relationship("SubUser", back_populates="generation_items", foreign_keys=[sub_user_id])
    template = relationship("Template", back_populates="generation_items", foreign_keys=[template_id])
    owner_operator = relationship("Operator", back_populates="generation_items", foreign_keys=[owner_operator_id])
    final_prompt = Column(Text, nullable=True, comment="最终发送给模型的完整提示词")
    distributions = relationship("Distribution", back_populates="generation_item", foreign_keys="Distribution.generation_item_id")
    execution_logs = relationship("GenerationItemExecutionLog", back_populates="item", foreign_keys="GenerationItemExecutionLog.item_id", cascade="all, delete-orphan")

    # ============================================
    # 输入内容快照（生成时捕获的原始输入信息）
    # ============================================
    sub_user_name = Column(String(100), nullable=True, comment="创作者名称快照（昵称）")

    # 模板信息
    input_prompt_creativity = Column(Text, nullable=True, comment="模板提示词创意（description）")
    input_prompt_instruction = Column(Text, nullable=True, comment="模板提示词指令（prompt_template）")
    input_template_images_json = Column(JSON, nullable=True, comment="模板图片URL列表")
    input_image_size_ratio = Column(String(20), nullable=True, comment="输出图片尺寸比例（如 16:9）")
    input_watermark = Column(Integer, nullable=True, comment="输出图片水印开关（1=开 0=关）")

    # 素材对标信息
    input_benchmark_title = Column(String(200), nullable=True, comment="素材对标标题")
    input_benchmark_content = Column(Text, nullable=True, comment="素材对标内容")
    input_benchmark_topic = Column(String(200), nullable=True, comment="素材对标话题")
    input_benchmark_images_json = Column(JSON, nullable=True, comment="素材对标图片URL列表")
    # 素材对标配置快照
    input_benchmark_text_enabled = Column(Boolean, nullable=True, comment="文案对标开关")
    input_benchmark_image_enabled = Column(Boolean, nullable=True, comment="图片对标开关")
    input_benchmark_image_reference_options = Column(JSON, nullable=True, comment="图片参考选项")
    # 图片角色配置快照（交互式编辑）
    input_benchmark_image_roles_json = Column(JSON, nullable=True, comment="对标图角色配置快照")
    input_template_product_mapping_json = Column(JSON, nullable=True, comment="模板产品映射快照")

    # 创作者信息
    input_sub_user_profile = Column(Text, nullable=True, comment="创作者粉丝画像")
    input_sub_user_positioning = Column(String(500), nullable=True, comment="创作者账号定位")
    input_sub_user_style = Column(String(500), nullable=True, comment="创作者内容风格")

    # ============================================
    # 输出内容（AIGC 重构后的提示词和最终文案）
    # ============================================
    aigc_generated_prompt = Column(Text, nullable=True, comment="AIGC提示词生成器产出的精炼提示词")
    output_system_text_prompt = Column(Text, nullable=True, comment="AIGC文案系统提示词")
    output_user_text_prompt = Column(Text, nullable=True, comment="AIGC文案用户提示词")
    output_system_image_prompt = Column(Text, nullable=True, comment="图片系统提示词")
    output_user_image_prompt = Column(Text, nullable=True, comment="图片用户提示词")
    output_topics = Column(JSON, nullable=True, comment="输出话题")

    # ============================================
    # 执行情况
    # ============================================
    execution_started_at = Column(DateTime, nullable=True, comment="子任务执行开始时间")
    execution_ended_at = Column(DateTime, nullable=True, comment="子任务执行结束时间")
    execution_result = Column(String(20), nullable=True, comment="执行结果：success / failed / partial")

    # ============================================
    # AIGC 生成的用户提示词
    # ============================================
    aigc_user_text_generator_user_prompt = Column(Text, nullable=True, comment="AIGC生成的文案用户提示词")
    aigc_user_image_prompts_json = Column(JSON, nullable=True, comment="AIGC生成的图片用户提示词列表")

    # ============================================
    # 去重检测
    # ============================================
    dedup_check_passed = Column(Boolean, nullable=True, comment="文案去重检测是否通过")
    dedup_similarity = Column(Float, nullable=True, comment="文案最大相似度")
    dedup_referenced_items_json = Column(JSON, nullable=True, comment="文案相似内容引用")
    dedup_checked_at = Column(DateTime, nullable=True, comment="文案去重检测时间")

    # ============================================
    # 图片去重检测结果
    # ============================================
    image_dedup_passed = Column(Boolean, nullable=True, comment="图片去重检测是否通过（整批图片）")
    image_dedup_max_similarity = Column(Float, nullable=True, comment="图片最高相似度")
    image_dedup_similarities_json = Column(JSON, nullable=True, comment="每张图片的相似度列表")
    image_dedup_referenced_images_json = Column(JSON, nullable=True, comment="相似图片引用")
    image_dedup_checked_at = Column(DateTime, nullable=True, comment="图片去重检测时间")
    image_dedup_retry_count = Column(Integer, nullable=True, default=0, comment="图片去重实际重试次数")

    # ============================================
    # 当前执行步骤（用于 UI 细粒度状态展示）
    # ============================================
    current_step = Column(String(50), nullable=True, comment="当前执行步骤")
    generated_image_count = Column(Integer, nullable=True, comment="实际生成图片数量")

    def __repr__(self):
        return f"<GenerationItem(id={self.id}, task_id={self.task_id}, status={self.status})>"


class GenerationItemExecutionLog(Base):
    """
    生成子任务执行日志表

    记录每个子任务处理链路中的关键节点（提示词构建、模型调用、结果保存等），
    用于调试和质量追踪。
    """
    __tablename__ = "generation_item_execution_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键")
    item_id = Column(BigInteger, ForeignKey("generation_item.id"), nullable=False, index=True, comment="子任务ID")
    node_name = Column(String(50), nullable=False, comment="节点名称: prompt_build / llm_call / image_call / save_result")
    node_status = Column(
        Enum("running", "success", "failed", "skipped", name="execution_node_status_enum"),
        nullable=False,
        comment="节点状态: running / success / failed / skipped"
    )
    input_data = Column(JSON, nullable=True, comment="节点输入数据(JSON)")
    output_data = Column(JSON, nullable=True, comment="节点输出数据(JSON)")
    error_data = Column(JSON, nullable=True, comment="结构化错误信息(JSON)")
    duration_ms = Column(Integer, nullable=True, comment="耗时毫秒")
    started_at = Column(DateTime, nullable=True, comment="节点开始时间")
    completed_at = Column(DateTime, nullable=True, comment="节点完成时间")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    # 关联
    item = relationship("GenerationItem", back_populates="execution_logs", foreign_keys=[item_id])

    def __repr__(self):
        return f"<GenerationItemExecutionLog(id={self.id}, item_id={self.item_id}, node={self.node_name}, status={self.node_status})>"
