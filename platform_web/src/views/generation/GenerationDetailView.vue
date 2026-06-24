<template>
  <div class="generation-detail-view">
    <div class="page-header flex-between mb-md">
      <div>
        <el-page-header @back="goBack" title="返回列表">
          <template #content>
            <span class="page-title">{{ '[任务 #' + taskId + ']' + task.name }}</span>
          </template>
        </el-page-header>
      </div>
      <div class="header-actions flex gap-md">
        <el-button type="danger" :icon="Close" v-if="['processing', 'pending'].includes(task.status || '')" @click="cancelTask">取消任务</el-button>
        <el-button type="warning" :icon="Refresh" v-if="task.failed_count && task.failed_count > 0" @click="retryFailed">重试失败</el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="24">
        <div class="card mb-md">
          <h3 class="section-title">任务概览</h3>
          <el-descriptions :column="4" border>
            <el-descriptions-item label="任务状态">
              <el-tag :type="getStatusType(task.status || '')" size="large">{{ getStatusLabel(task.status || '') }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatDate(task.created_at || '') }}</el-descriptions-item>
            <el-descriptions-item label="完成时间">{{ formatDate(task.completed_at || '') || '-' }}</el-descriptions-item>
            <el-descriptions-item label="任务耗时">{{ task.completed_at ? formatDuration(task.duration_seconds) : '-' }}</el-descriptions-item>
            <el-descriptions-item label="模板创作ID">{{ task.template_id || '-' }}</el-descriptions-item>
            <el-descriptions-item label="素材对标ID">{{ task.benchmark_material_id || '-' }}</el-descriptions-item>
            <el-descriptions-item label="文本模型">
              <div class="editable-field">
                <el-select v-model="selectedTextModelConfigId" placeholder="选择文本模型" style="width: 250px;" size="small" clearable @change="onTaskTextModelChange">
                  <el-option label="自动选择" :value="0" />
                  <el-option v-for="m in allLlmModels" :key="m.id" :label="m.platform + ' / ' + m.model_name" :value="m.id" />
                </el-select>
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="图片模型">
              <div class="editable-field">
                <el-select v-model="selectedImageModelConfigId" placeholder="选择图片模型" style="width: 250px;" size="small" clearable @change="onTaskImageModelChange">
                  <el-option label="自动选择" :value="0" />
                  <el-option v-for="m in allImageModels" :key="m.id" :label="m.platform + ' / ' + m.model_name" :value="m.id" />
                </el-select>
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="子任务总数">{{ task.total_count || 0 }} 人</el-descriptions-item>
            <el-descriptions-item label="内容平台">{{ task.template_info?.platform_name || '-' }}</el-descriptions-item>
            <!-- 去重配置 -->
            <el-descriptions-item label="文案去重">
              <el-switch v-model="task.dedup_enabled" size="small" @change="onDedupChange('dedup')" :loading="savingDedup" />
              <template v-if="task.dedup_enabled">
                <span class="config-detail-inline">阈值: {{ ((task.dedup_threshold || 0) * 100).toFixed(0) }}%</span>
                <span class="config-detail-inline">重试: {{ task.dedup_retry_count || 3 }}次</span>
              </template>
            </el-descriptions-item>
            <el-descriptions-item label="图片去重">
              <el-switch v-model="task.image_dedup_enabled" size="small" @change="onDedupChange('image_dedup')" :loading="savingDedup" />
              <template v-if="task.image_dedup_enabled">
                <span class="config-detail-inline">阈值: {{ ((task.image_dedup_threshold || 0) * 100).toFixed(0) }}%</span>
              </template>
            </el-descriptions-item>
            <!-- 对标配置 -->
            <el-descriptions-item label="文案对标">
              <el-tag :type="task.benchmark_text_enabled ? 'success' : 'info'" size="small">{{ task.benchmark_text_enabled ? '开启' : '关闭' }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="图片对标">
              <el-tag :type="task.benchmark_image_enabled ? 'success' : 'info'" size="small">{{ task.benchmark_image_enabled ? '开启' : '关闭' }}</el-tag>
            </el-descriptions-item>
          </el-descriptions>

          <!-- 素材展示区域（可折叠） -->
          <div class="materials-section mt-lg" v-if="task.template_info || task.benchmark_material_info">
            <div class="collapsible-header" @click="materialsCollapsed = !materialsCollapsed">
              <h4 class="section-label">任务素材</h4>
              <el-icon class="collapse-icon" :class="{ 'is-expanded': !materialsCollapsed }">
                <ArrowRight />
              </el-icon>
            </div>
            <el-collapse-transition>
              <el-row :gutter="16" v-show="!materialsCollapsed">
              <!-- 模板创作 -->
              <el-col :span="12" v-if="task.template_info">
                <div class="material-card">
                  <div class="material-header">
                    <span class="material-label">模板创作库</span>
                    <span class="material-title">{{ task.template_info.name }}</span>
                  </div>
                  <!-- 模板缩略图 -->
                  <div class="material-thumbnails" v-if="task.template_info.thumbnails?.length">
                    <el-image
                      v-for="(thumb, idx) in task.template_info.thumbnails.slice(0, 4)"
                      :key="idx"
                      :src="thumb"
                      fit="cover"
                      class="material-thumb"
                      :preview-src-list="task.template_info.thumbnails"
                      :initial-index="idx"
                      preview-teleported
                    />
                    <span v-if="task.template_info.thumbnails.length > 4" class="more-count">+{{ task.template_info.thumbnails.length - 4 }}</span>
                  </div>
                  <div class="no-thumbnails" v-else>
                    <span>暂无缩略图</span>
                  </div>
                  <!-- 提示词创意 -->
                  <div class="template-prompt-info" v-if="task.template_info.description">
                    <div class="prompt-label">提示词创意</div>
                    <div class="prompt-content">{{ task.template_info.description }}</div>
                  </div>
                  <!-- 提示词指令 -->
                  <div class="template-prompt-info" v-if="task.template_info.prompt_template">
                    <div class="prompt-label">提示词指令</div>
                    <pre class="prompt-content">{{ task.template_info.prompt_template }}</pre>
                  </div>
                  <!-- 输出设置 -->
                  <div class="template-output-settings" v-if="task.template_info.image_size_ratio || task.template_info.add_watermark !== undefined">
                    <div class="output-setting-item" v-if="task.template_info.image_size_ratio">
                      <span class="setting-label">输出图片尺寸比例</span>
                      <span class="setting-value">{{ task.template_info.image_size_ratio }}</span>
                    </div>
                    <div class="output-setting-item" v-if="task.template_info.add_watermark !== undefined && task.template_info.add_watermark !== null">
                      <span class="setting-label">输出图片水印</span>
                      <el-tag :type="task.template_info.add_watermark ? 'success' : 'info'" size="small">{{ task.template_info.add_watermark ? '开启' : '关闭' }}</el-tag>
                    </div>
                  </div>
                  <!-- 产品卖点 -->
                  <div class="template-prompt-info" v-if="task.template_info.product_selling_points">
                    <div class="prompt-label">产品卖点</div>
                    <div class="prompt-content">{{ task.template_info.product_selling_points }}</div>
                  </div>
                  <!-- 爆款类型 + 创意种子 -->
                  <div class="template-prompt-info" v-if="task.template_info.viral_type || task.template_info.opening_seed_name || task.template_info.emotion_seed_name || task.template_info.ending_seed_name">
                    <div class="prompt-label">爆款类型与创意种子</div>
                    <div class="prompt-content">
                      <el-tag size="small" type="warning" v-if="task.template_info.viral_type_label" class="mr-xs mb-xs">
                        爆款类型: {{ task.template_info.viral_type_label }}
                      </el-tag>
                      <el-tag size="small" type="primary" v-if="task.template_info.opening_seed_name" class="mr-xs mb-xs">
                        开头: {{ task.template_info.opening_seed_name }}
                      </el-tag>
                      <el-tag size="small" type="primary" v-if="task.template_info.emotion_seed_name" class="mr-xs mb-xs">
                        情感: {{ task.template_info.emotion_seed_name }}
                      </el-tag>
                      <el-tag size="small" type="primary" v-if="task.template_info.ending_seed_name" class="mr-xs mb-xs">
                        结尾: {{ task.template_info.ending_seed_name }}
                      </el-tag>
                    </div>
                  </div>
                </div>
              </el-col>
              <!-- 对标素材 -->
              <el-col :span="12" v-if="task.benchmark_material_info">
                <div class="material-card">
                  <div class="material-header">
                    <span class="material-label">素材对标库</span>
                    <span class="material-title">{{ task.benchmark_material_info.title }}</span>
                  </div>
                  <div class="material-thumbnails" v-if="task.benchmark_material_info.thumbnails?.length">
                    <el-image
                      v-for="(thumb, idx) in task.benchmark_material_info.thumbnails.slice(0, 4)"
                      :key="idx"
                      :src="thumb"
                      fit="cover"
                      class="material-thumb"
                      :preview-src-list="task.benchmark_material_info.thumbnails"
                      :initial-index="idx"
                      preview-teleported
                    />
                    <span v-if="task.benchmark_material_info.thumbnails.length > 4" class="more-count">+{{ task.benchmark_material_info.thumbnails.length - 4 }}</span>
                  </div>
                  <div class="no-thumbnails" v-else>
                    <span>暂无缩略图</span>
                  </div>
                  <!-- 对标素材正文和话题 -->
                  <div class="benchmark-text-info" v-if="task.benchmark_material_info.content || task.benchmark_material_info.topic">
                    <div class="benchmark-content" v-if="task.benchmark_material_info.content">
                      <span class="content-label">正文</span>
                      <div class="content-value">{{ task.benchmark_material_info.content }}</div>
                    </div>
                    <div class="benchmark-topic" v-if="task.benchmark_material_info.topic">
                      <span class="topic-label">话题</span>
                      <div class="topic-value">#{{ task.benchmark_material_info.topic }}</div>
                    </div>
                  </div>
                </div>
              </el-col>
              </el-row>
            </el-collapse-transition>
          </div>

          <div class="progress-section mt-lg">
            <div class="progress-header flex-between">
              <span class="progress-title">生成进度</span>
              <span class="progress-text">{{ getProgress }}%</span>
            </div>
            <el-progress :percentage="getProgress" :status="task.status === 'failed' ? 'exception' : undefined" />
            <div class="progress-stats flex-between mt-md">
              <div class="stat-group flex gap-lg">
                <span class="stat-item"><span class="label">排队中:</span> <span class="value">{{ task.queued_count || 0 }}</span></span>
                <span class="stat-item"><span class="label">生成中:</span> <span class="value primary">{{ task.generating_count || 0 }}</span></span>
                <span class="stat-item"><span class="label">已生成:</span> <span class="value success">{{ task.completed_count || 0 }}</span></span>
                <span class="stat-item"><span class="label">失败:</span> <span class="value danger">{{ task.failed_count || 0 }}</span></span>
              </div>
              <div class="stat-group flex gap-lg">
                <span class="stat-item"><span class="label">已分发:</span> <span class="value info">{{ task.distributed_count || 0 }}</span></span>
                <span class="stat-item"><span class="label">待发布:</span> <span class="value warning">{{ task.pending_publish_count || 0 }}</span></span>
                <span class="stat-item"><span class="label">已发布:</span> <span class="value success">{{ task.published_count || 0 }}</span></span>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="24">
        <div class="card">
          <div class="toolbar flex-between mb-md">
            <div class="toolbar-left flex gap-md">
              <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 140px;">
                <el-option label="全部" value="" />
                <el-option label="排队中" value="queued" />
                <el-option label="生成中" value="generating" />
                <el-option label="已暂停" value="paused" />
                <el-option label="已完成" value="completed" />
                <el-option label="失败" value="failed" />
              </el-select>
              <el-input
                v-model="searchKeyword"
                placeholder="搜索创作者昵称"
                :prefix-icon="Search"
                clearable
                style="width: 200px;"
              />
            </div>
            <div class="toolbar-right flex gap-md" v-if="selectedItems.length > 0">
              <el-button type="warning" size="small" @click="batchPause" :disabled="!canBatchPause">暂停选中</el-button>
              <el-button type="primary" size="small" @click="batchResume" :disabled="!canBatchResume">继续选中</el-button>
              <el-button type="warning" size="small" @click="batchRetry" :disabled="!canBatchRetry">重试选中</el-button>
            </div>
          </div>

          <el-table :data="items" style="width: 100%" @selection-change="handleSelectionChange" v-loading="loading" row-class-name="clickable-row" @row-click="handleRowClick">
            <el-table-column type="selection" width="50" />
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="sub_user_name" label="用户名" width="90" />
            <el-table-column label="状态" width="130">
              <template #default="{ row }">
                <el-tag :type="getItemStatusType(row.status, row.distribution_status)" size="small">
                  {{ getItemStatusLabel(row.status, row.distribution_status) }}
                </el-tag>
                <!-- 重试次数提示：排队中但重试过说明之前失败 -->
                <span v-if="row.retry_count > 0 && row.status === 'queued'" class="retry-hint" style="font-size:11px;color:#E6A23C;">
                  重试 {{ row.retry_count }}
                </span>
                <div v-if="row.status === 'generating' && row.current_step" class="step-hint">
                  {{ getCurrentStepLabel(row.current_step) }}
                </div>
                <!-- 失败/排队重试中的错误提示 -->
                <div v-if="row.error_message && (row.status === 'failed' || row.status === 'queued')" class="step-hint error-step-hint" style="font-size:11px;color:#F56C6C;max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                  {{ row.error_message }}
                </div>
              </template>
            </el-table-column>
            <el-table-column label="生成预览" min-width="280">
              <template #default="{ row }">
                <div class="preview-cell" v-if="row.generated_title || parseImageUrls(row.generated_image_urls_json).length">
                  <div class="preview-images" v-if="parseImageUrls(row.generated_image_urls_json).length">
                    <el-image
                      v-for="(img, idx) in parseImageUrls(row.generated_image_thumbnails_json || row.generated_image_urls_json).slice(0, 3)"
                      :key="idx"
                      :src="img"
                      fit="cover"
                      class="preview-thumb"
                      :preview-src-list="parseImageUrls(row.generated_image_urls_json)"
                      :initial-index="idx"
                      preview-teleported
                      @click.stop
                    />
                    <span v-if="parseImageUrls(row.generated_image_urls_json).length > 3" class="more-images">+{{ parseImageUrls(row.generated_image_urls_json).length - 3 }}</span>
                  </div>
                  <div class="preview-text">
                    <div class="content-title" v-if="row.generated_title">{{ row.generated_title }}</div>
                    <div class="content-text">{{ row.generated_text?.substring(0, 100) }}{{ row.generated_text && row.generated_text.length > 100 ? '...' : '' }}</div>
                  </div>
                </div>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
            <el-table-column label="文本模型" width="140">
              <template #default="{ row }">
                <span v-if="row.model_platform && row.model_id">{{ row.model_platform }} / {{ row.model_id }}</span>
                <span v-else-if="row.model_platform">{{ row.model_platform }}</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="图片模型" width="140">
              <template #default="{ row }">
                <span v-if="row.image_model_platform && row.image_model_id">{{ row.image_model_platform }} / {{ row.image_model_id }}</span>
                <span v-else-if="row.image_model_platform">{{ row.image_model_platform }}</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="耗时" width="100">
              <template #default="{ row }">
                <span v-if="row.started_at && row.completed_at">{{ calcDuration(row.started_at, row.completed_at) }}</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip width="150">
              <template #default="{ row }">
                <span v-if="row.error_message" class="error-text">{{ row.error_message }}</span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" min-width="220" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click.stop="openDetailDrawer(row)">详情</el-button>
                <el-button type="warning" link size="small" v-if="row.status === 'failed'" @click.stop="retryItem(row)">重试</el-button>
                <el-button type="primary" link size="small" v-if="row.status === 'failed'" @click.stop="regenerateItem(row)">重新生成</el-button>
                <el-button type="warning" link size="small" v-if="row.status === 'queued' || row.status === 'generating'" @click.stop="pauseItem(row)">暂停</el-button>
                <el-button type="primary" link size="small" v-if="row.status === 'paused'" @click.stop="resumeItem(row)">继续</el-button>
                <el-button type="success" link size="small" v-if="row.status === 'completed' && row.distribution_status === 'pending_publish'" @click.stop="regenerateItem(row)">重新生成</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination mt-lg flex-between">
            <span class="total-text">共 {{ total }} 条子任务</span>
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="total"
              layout="total, sizes, prev, pager, next, jumper"
            />
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 子任务详情抽屉 -->
    <el-drawer v-model="drawerVisible" :title="`子任务 #${detailItem?.id || ''} 详情`" size="70%" direction="rtl" :destroy-on-close="true">
      <div class="drawer-content" v-if="detailItem" v-loading="detailLoading">
        <el-tabs v-model="drawerTab">
          <!-- Tab1: 输入内容 -->
          <el-tab-pane label="输入内容" name="input">
            <div class="input-section">
              <!-- 提示词模板信息 -->
              <div class="input-block" v-if="detailItem.text_prompt_template_name || detailItem.image_prompt_template_name">
                <h4 class="block-title">提示词模板</h4>

                <!-- 文案提示词模板 -->
                <div class="prompt-template-section" v-if="detailItem.text_prompt_template_name">
                  <div class="template-header">
                    <span class="template-label">文案提示词模板</span>
                    <el-tag type="primary" size="small">{{ detailItem.text_prompt_template_name }}</el-tag>
                  </div>
                  <pre class="prompt-content">{{ textPromptTemplateContent || '加载中...' }}</pre>
                </div>

                <!-- 图片提示词模板 -->
                <div class="prompt-template-section mt-md" v-if="detailItem.image_prompt_template_name">
                  <div class="template-header">
                    <span class="template-label">图片提示词模板</span>
                    <el-tag type="success" size="small">{{ detailItem.image_prompt_template_name }}</el-tag>
                  </div>
                  <pre class="prompt-content">{{ imagePromptTemplateContent || '加载中...' }}</pre>
                </div>
              </div>

              <!-- 模板信息 -->
              <div class="input-block mt-lg">
                <h4 class="block-title">模板信息</h4>
                <el-descriptions :column="2" border size="small">
                  <el-descriptions-item label="模板名称">
                    <span class="info-text">{{ detailItem.input_template_name || '-' }}</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="爆款类型">
                    <el-tag v-if="detailItem.input_viral_type" type="success" size="small">{{ detailItem.input_viral_type }}</el-tag>
                    <span v-else>-</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="产品卖点" :span="2">
                    <pre class="info-text">{{ detailItem.input_product_selling_points || '-' }}</pre>
                  </el-descriptions-item>
                  <el-descriptions-item label="提示词创意" :span="2">
                    <pre class="info-text">{{ detailItem.input_prompt_creativity || '-' }}</pre>
                  </el-descriptions-item>
                  <el-descriptions-item label="提示词指令" :span="2">
                    <pre class="info-text code-text">{{ detailItem.input_prompt_instruction || '-' }}</pre>
                  </el-descriptions-item>
                  <el-descriptions-item label="开头模式">
                    <el-tag v-if="detailItem.input_opening_seed_name" type="primary" size="small">{{ detailItem.input_opening_seed_name }}</el-tag>
                    <span v-else>-</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="情感基调">
                    <el-tag v-if="detailItem.input_emotion_seed_name" type="success" size="small">{{ detailItem.input_emotion_seed_name }}</el-tag>
                    <span v-else>-</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="结尾模式">
                    <el-tag v-if="detailItem.input_ending_seed_name" type="warning" size="small">{{ detailItem.input_ending_seed_name }}</el-tag>
                    <span v-else>-</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="输出图片尺寸比例">
                    <span class="info-text">{{ detailItem.input_image_size_ratio || '-' }}</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="输出图片水印">
                    <el-tag v-if="detailItem.input_watermark !== null && detailItem.input_watermark !== undefined" :type="detailItem.input_watermark ? 'success' : 'info'" size="small">
                      {{ detailItem.input_watermark ? '开启' : '关闭' }}
                    </el-tag>
                    <span v-else>-</span>
                  </el-descriptions-item>
                </el-descriptions>
                <!-- 模板图片 -->
                <div class="input-images mt-sm" v-if="detailItem.input_template_images_json?.length">
                  <h5 class="input-sub-label">模板图片</h5>
                  <div class="image-row">
                    <el-image
                      v-for="(img, idx) in detailItem.input_template_images_json"
                      :key="idx"
                      :src="img"
                      fit="cover"
                      class="input-image-thumb"
                      :preview-src-list="detailItem.input_template_images_json"
                      :initial-index="idx"
                      preview-teleported
                    />
                  </div>
                </div>
              </div>

              <!-- 素材对标信息 -->
              <div class="input-block mt-lg">
                <h4 class="block-title">素材对标信息</h4>
                <el-descriptions :column="2" border size="small">
                  <el-descriptions-item label="对标标题">
                    <span class="info-text">{{ detailItem.input_benchmark_title || '-' }}</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="对标话题">
                    <span class="info-text">{{ detailItem.input_benchmark_topic || '-' }}</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="对标内容" :span="2">
                    <pre class="info-text">{{ detailItem.input_benchmark_content || '-' }}</pre>
                  </el-descriptions-item>
                </el-descriptions>
                <!-- 对标图片 -->
                <div class="input-images mt-sm" v-if="detailItem.input_benchmark_images_json?.length">
                  <h5 class="input-sub-label">对标图片</h5>
                  <div class="image-row">
                    <el-image
                      v-for="(img, idx) in detailItem.input_benchmark_images_json"
                      :key="idx"
                      :src="img"
                      fit="cover"
                      class="input-image-thumb"
                      :preview-src-list="detailItem.input_benchmark_images_json"
                      :initial-index="idx"
                      preview-teleported
                    />
                    <!-- 角色标签 -->
                    <el-tag
                      v-if="(detailItem as any).input_benchmark_image_roles_json && getBenchmarkRoleTag(idx)"
                      size="small"
                      type="warning"
                      class="image-role-tag"
                    >
                      {{ getBenchmarkRoleTag(idx) }}
                    </el-tag>
                  </div>
                </div>

                <!-- V5.0: 双图组合模式指示 -->
                <div
                  v-if="isPairModeEnabled(detailItem as any)"
                  class="pair-mode-indicator mt-sm"
                >
                  <el-alert
                    type="success"
                    :closable="false"
                    show-icon
                  >
                    <template #title>
                      <span class="pair-mode-title">双图组合模式已启用</span>
                    </template>
                    <template #default>
                      <div class="pair-mode-detail">
                        每张生成图片仅传入
                        <el-tag size="small" type="warning">1张对标图</el-tag>
                        +
                        <el-tag size="small" type="success">1张模板图</el-tag>
                        ，提示词中明确描述「图2产品替换到图1构图/场景/风格」
                      </div>
                      <div class="pair-combinations" v-if="pairCombinations.length">
                        <div
                          v-for="(combo, cIdx) in pairCombinations"
                          :key="cIdx"
                          class="pair-combo-item"
                        >
                          <span class="combo-label">图{{ cIdx + 1 }}:</span>
                          <el-tag size="small" type="warning">{{ combo.benchLabel }}</el-tag>
                          <span class="combo-arrow">+</span>
                          <el-tag size="small" type="success">{{ combo.tplLabel }}</el-tag>
                        </div>
                      </div>
                    </template>
                  </el-alert>
                </div>
              </div>

              <!-- 创作者信息 -->
              <div class="input-block mt-lg">
                <h4 class="block-title">创作者信息</h4>
                <el-descriptions :column="2" border size="small">
                  <el-descriptions-item label="创作者名称">
                    <span class="info-text">{{ detailItem.sub_user_name || '-' }}</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="账号定位">
                    <span class="info-text">{{ detailItem.input_sub_user_positioning || '-' }}</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="粉丝画像" :span="2">
                    <pre class="info-text">{{ detailItem.input_sub_user_profile || '-' }}</pre>
                  </el-descriptions-item>
                  <el-descriptions-item label="内容风格" :span="2">
                    <span class="info-text">{{ detailItem.input_sub_user_style || '-' }}</span>
                  </el-descriptions-item>
                </el-descriptions>
              </div>
            </div>
          </el-tab-pane>

          <!-- Tab2: 输出内容 -->
          <el-tab-pane label="输出内容" name="output">
            <div class="output-section">
              <!-- 调试模式开关和模型选择 -->
              <div class="debug-toolbar">
                <div class="toolbar-top">
                  <el-switch v-model="promptDebugMode" active-text="提示词调试模式" inactive-text="提示词调试模式" />
                </div>
                <div class="toolbar-bottom" v-if="promptDebugMode">
                  <div class="model-group">
                    <span class="group-label">文本模型:</span>
                    <el-select v-model="selectedTextModelPlatform" placeholder="平台" style="width: 120px;" clearable @change="onTextModelPlatformChange">
                      <el-option label="全部" value="" />
                      <el-option v-for="platform in textModelPlatforms.filter(p => p)" :key="platform" :label="platform" :value="platform" />
                    </el-select>
                    <el-select v-model="selectedTextModelId" placeholder="选择模型" style="width: 180px;" clearable>
                      <el-option v-for="model in availableTextModels" :key="model.model_id" :label="model.model_name" :value="model.model_id" />
                    </el-select>
                  </div>
                  <div class="model-group">
                    <span class="group-label">图片模型:</span>
                    <el-select v-model="selectedImageModelPlatform" placeholder="平台" style="width: 120px;" clearable @change="onImageModelPlatformChange">
                      <el-option label="全部" value="" />
                      <el-option v-for="platform in imageModelPlatforms.filter(p => p)" :key="platform" :label="platform" :value="platform" />
                    </el-select>
                    <el-select v-model="selectedImageModelId" placeholder="选择模型" style="width: 180px;" clearable>
                      <el-option v-for="model in availableImageModels" :key="model.model_id" :label="model.model_name" :value="model.model_id" />
                    </el-select>
                  </div>
                </div>
              </div>

              
              <!-- 文案生成器的提示词 -->
              <div class="output-block">
                <h4 class="block-title">文案生成器提示词</h4>
                <el-tabs v-model="textPromptSubTab" type="card" class="prompt-sub-tabs">
                  <el-tab-pane label="📝 文案系统提示词" name="system_text">
                    <div v-if="promptDebugMode">
                      <el-input
                        v-model="debugTextSystemPrompt"
                        type="textarea"
                        :rows="8"
                        placeholder="系统提示词"
                      />
                    </div>
                    <pre v-else class="prompt-box">{{ detailItem.output_system_text_prompt || '无' }}</pre>
                  </el-tab-pane>
                  <el-tab-pane label="📝 文案用户提示词" name="user_text">
                    <div v-if="promptDebugMode">
                      <el-input
                        v-model="debugTextUserPrompt"
                        type="textarea"
                        :rows="8"
                        placeholder="用户提示词"
                      />
                    </div>
                    <pre v-else class="prompt-box">{{ detailItem.output_user_text_prompt || '无' }}</pre>
                  </el-tab-pane>
                </el-tabs>

                <!-- 调试模式下的内容生成输出 -->
                <div v-if="promptDebugMode" class="debug-output-section">
                  <div class="sub-block-header">
                    <h5 class="sub-block-title">📄 文案输出预览</h5>
                    <div class="header-right">
                      <el-tag v-if="textGenerating" type="warning" size="small">
                        <span class="loading-dot"></span>
                        生成中
                      </el-tag>
                      <el-tag v-else-if="debugGeneratedText" type="success" size="small">已完成</el-tag>
                      <el-button type="primary" size="small" :loading="textGenerating" @click="debugGenerateText">内容生成</el-button>
                    </div>
                  </div>
                  <div v-if="debugGeneratedText" class="text-output-preview">
                    <div class="output-item">
                      <span class="output-label">标题</span>
                      <div class="output-value title">{{ debugGeneratedText.title }}</div>
                    </div>
                    <div class="output-item">
                      <span class="output-label">正文</span>
                      <div class="output-value content">{{ debugGeneratedText.content }}</div>
                    </div>
                    <div class="output-item" v-if="debugGeneratedText.topics?.length">
                      <span class="output-label">话题</span>
                      <div class="topics-list">
                        <el-tag v-for="(topic, idx) in debugGeneratedText.topics" :key="idx" type="warning" size="small" class="topic-tag">
                          #{{ topic }}
                        </el-tag>
                      </div>
                    </div>
                  </div>
                  <div v-else class="empty-preview">
                    <span class="text-muted">点击"内容生成"按钮查看生成结果</span>
                  </div>
                </div>
              </div>

              <!-- 去重检测结果 -->
              <div class="output-block" v-if="detailItem.dedup_checked_at">
                <h4 class="block-title">
                  <el-tag :type="detailItem.dedup_check_passed ? 'success' : 'danger'" size="small" class="mr-sm">去重检测</el-tag>
                </h4>
                <div class="dedup-result">
                  <div class="dedup-summary">
                    <span class="dedup-status" :class="detailItem.dedup_check_passed ? 'passed' : 'failed'">
                      {{ detailItem.dedup_check_passed ? '✅ 通过' : '❌ 未通过' }}
                    </span>
                    <span class="dedup-similarity">
                      最大相似度: <strong>{{ detailItem.dedup_similarity != null ? (detailItem.dedup_similarity * 100).toFixed(1) : '0.0' }}%</strong>
                    </span>
                  </div>
                  <div class="dedup-time" v-if="detailItem.dedup_checked_at">
                    检测时间: {{ formatDate(detailItem.dedup_checked_at) }}
                  </div>
                  <!-- 相似内容引用 -->
                  <div class="dedup-references" v-if="detailItem.dedup_referenced_items_json && detailItem.dedup_referenced_items_json.length">
                    <h5 class="sub-block-title">相似内容引用</h5>
                    <div v-for="ref in detailItem.dedup_referenced_items_json" :key="ref.item_id" class="ref-item">
                      <span class="ref-item-id">子任务#{{ ref.item_id }}</span>
                      <span class="ref-similarity">{{ (ref.similarity * 100).toFixed(1) }}%</span>
                      <span class="ref-preview">{{ ref.text_preview }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- AIGC 提示词生成器产出 -->
              <div class="output-block" v-if="detailItem.aigc_generated_prompt">
                <h4 class="block-title">
                  <el-tag type="warning" size="small" class="mr-sm">节点 1</el-tag>
                  AIGC 提示词生成器产出
                </h4>
                <pre class="prompt-box aigc-prompt-box">{{ detailItem.aigc_generated_prompt }}</pre>
              </div>

              <!-- 图片生成器的提示词 -->
              <div class="output-block">
                <h4 class="block-title">图片生成器提示词</h4>

                <!-- 参考图片输入显示 -->
                <div v-if="promptDebugMode && (debugReferenceImageUrls?.length || detailItem.input_template_images_json?.length)" class="input-materials-section">
                  <div class="sub-block-header">
                    <h5 class="sub-block-title">📎 参考图片</h5>
                  </div>
                  <div class="material-images-row">
                    <el-image
                      v-for="(img, idx) in (debugReferenceImageUrls?.length ? debugReferenceImageUrls : detailItem.input_template_images_json)"
                      :key="idx"
                      :src="img"
                      fit="cover"
                      class="material-image-thumb"
                      :preview-src-list="debugReferenceImageUrls?.length ? debugReferenceImageUrls : detailItem.input_template_images_json"
                      :initial-index="idx"
                      preview-teleported
                    />
                  </div>
                </div>

                <div class="image-prompts-section">
                  <div v-if="promptDebugMode">
                    <div v-if="debugImageUserPrompts.length > 0">
                      <div v-for="(_, idx) in debugImageUserPrompts" :key="idx" class="image-prompt-item">
                        <div class="image-prompt-header">
                          <span class="prompt-label">图片 {{ idx + 1 }}</span>
                          <el-button type="danger" link size="small" @click="removeImagePrompt(idx)" v-if="debugImageUserPrompts.length > 1">删除</el-button>
                        </div>
                        <el-input
                          v-model="debugImageUserPrompts[idx]"
                          type="textarea"
                          :rows="5"
                          :placeholder="`图片 ${idx + 1} 的提示词`"
                        />
                      </div>
                      <el-button type="primary" size="small" @click="addImagePrompt" class="mt-2">+ 添加图片提示词</el-button>
                    </div>
                    <div v-else>
                      <el-input
                        v-model="debugImageUserPrompt"
                        type="textarea"
                        :rows="8"
                        placeholder="用户提示词"
                      />
                      <el-button type="primary" size="small" @click="addImagePrompt" class="mt-2">+ 添加图片提示词</el-button>
                    </div>
                  </div>
                  <div v-else>
                    <div v-if="detailItem.aigc_user_image_prompts_json && detailItem.aigc_user_image_prompts_json.length > 0">
                      <div v-for="(prompt, idx) in detailItem.aigc_user_image_prompts_json" :key="idx" class="image-prompt-item">
                        <div class="image-prompt-header">
                          <span class="prompt-label">图片 {{ idx + 1 }}</span>
                        </div>
                        <pre class="prompt-box">{{ prompt }}</pre>
                      </div>
                    </div>
                    <pre v-else class="prompt-box">{{ detailItem.output_user_image_prompt || '无' }}</pre>
                  </div>
                </div>

                <!-- 调试模式下的图片生成输出 -->
                <div v-if="promptDebugMode" class="debug-output-section">
                  <div class="sub-block-header">
                    <h5 class="sub-block-title">🖼️ 图片输出预览</h5>
                    <div class="header-right">
                      <el-tag v-if="imageGenerating" type="warning" size="small">
                        <span class="loading-dot"></span>
                        生成中
                      </el-tag>
                      <el-tag v-else-if="debugGeneratedImages.length" type="success" size="small">已完成</el-tag>
                      <el-button type="primary" size="small" :loading="imageGenerating" @click="debugGenerateImages">内容生成</el-button>
                    </div>
                  </div>
                  <div v-if="debugGeneratedImages.length" class="image-output-preview">
                    <div class="output-images-grid">
                      <el-image
                        v-for="(img, idx) in debugGeneratedImages"
                        :key="idx"
                        :src="img"
                        fit="cover"
                        class="output-image-item"
                        :preview-src-list="debugGeneratedImages"
                        :initial-index="idx"
                        preview-teleported
                      />
                    </div>
                  </div>
                  <div v-else class="empty-preview">
                    <span class="text-muted">点击"内容生成"按钮查看生成结果</span>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>
          <!-- Tab3: 生成内容 -->
          <el-tab-pane label="生成内容" name="content">
            <div class="content-section">
              <!-- 结构化文案区域（标题/正文/话题拆分） -->
              <div class="structured-content">
                <!-- 标题 -->
                <div class="content-card title-card">
                  <div class="card-header">
                    <span class="card-icon">📌</span>
                    <span class="card-label">标题</span>
                    <el-button v-if="detailItem.generated_title" type="primary" link size="small" @click="copyText(detailItem.generated_title)">复制标题</el-button>
                  </div>
                  <div class="card-body title-body">
                    {{ detailItem.generated_title || '无标题' }}
                  </div>
                </div>

                <!-- 正文 -->
                <div class="content-card body-card">
                  <div class="card-header">
                    <span class="card-icon">📄</span>
                    <span class="card-label">正文内容</span>
                    <el-button v-if="detailItem.generated_text" type="primary" link size="small" @click="copyText(detailItem.generated_text)">复制全文</el-button>
                  </div>
                  <div class="card-body text-body">
                    <!-- 如果后端已解析出正文，使用 parsedText；否则使用原始文本 -->
                    <div v-if="parsedText.content" class="parsed-text">
                      <template v-for="(paragraph, idx) in parsedText.content.split('\n')" :key="idx">
                        <span v-if="paragraph" class="text-paragraph">{{ paragraph }}</span>
                        <br v-else>
                      </template>
                    </div>
                    <div v-else class="parsed-text">{{ detailItem.generated_text || '无内容' }}</div>
                  </div>
                  <div v-if="detailItem.generated_text && detailItem.generated_text.length > 500" class="card-footer">
                    <el-button type="primary" link @click="textCollapsed = !textCollapsed">
                      {{ textCollapsed ? '展开全部' : '收起' }}
                    </el-button>
                  </div>
                </div>

                <!-- 话题 -->
                <div class="content-card topics-card" v-if="detailItem.output_topics">
                  <div class="card-header">
                    <span class="card-icon">🏷️</span>
                    <span class="card-label">输出话题</span>
                    <el-button type="primary" link size="small" @click="copyTopics">复制话题</el-button>
                  </div>
                  <div class="card-body topics-body">
                    <el-tag
                      v-for="(tag, idx) in parseTopics(detailItem.output_topics)"
                      :key="idx"
                      type="warning"
                      size="large"
                      class="topic-tag"
                    >#{{ tag }}</el-tag>
                  </div>
                </div>
              </div>

              <!-- 生成图片 -->
              <div class="image-gallery mt-lg" v-if="parseImageUrls(detailItem.generated_image_urls_json).length">
                <h4 class="section-label">生成图片 ({{ parseImageUrls(detailItem.generated_image_urls_json).length }})</h4>
                <div class="gallery-grid">
                  <el-image
                    v-for="(img, idx) in getDisplayImages(detailItem)"
                    :key="idx"
                    :src="img"
                    fit="cover"
                    class="gallery-item"
                    :preview-src-list="parseImageUrls(detailItem.generated_image_urls_json)"
                    :initial-index="idx"
                    preview-teleported
                  />
                </div>
              </div>
              <div v-else class="empty-images mt-md">
                <el-empty description="暂无生成图片" :image-size="80" />
              </div>

              <div class="error-section mt-lg" v-if="detailItem.error_message">
                <h4 class="section-label error">错误信息</h4>
                <div class="error-detail-block">
                  <div class="error-content">{{ detailItem.error_message }}</div>
                </div>
              </div>

              <div class="actions-bar mt-lg">
                <el-button type="primary" @click="copyFullTextContent">复制文案</el-button>
                <el-button v-if="detailItem.error_message" type="danger" plain @click="copyError">复制错误信息</el-button>
              </div>
            </div>
          </el-tab-pane>
          <!-- Tab4: 执行链路 -->
          <el-tab-pane label="执行链路" name="execution">
            <div class="execution-section" v-loading="logsLoading">
              <!-- 执行情况概览 -->
              <div class="execution-summary mb-md" v-if="detailItem.execution_started_at || detailItem.execution_ended_at">
                <el-descriptions :column="3" border size="small">
                  <el-descriptions-item label="开始时间">
                    <span class="info-text">{{ detailItem.execution_started_at ? formatDate(detailItem.execution_started_at) : '-' }}</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="结束时间">
                    <span class="info-text">{{ detailItem.execution_ended_at ? formatDate(detailItem.execution_ended_at) : '-' }}</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="执行结果">
                    <el-tag v-if="detailItem.execution_result" :type="getExecutionResultType(detailItem.execution_result)" size="small">
                      {{ getExecutionResultLabel(detailItem.execution_result) }}
                    </el-tag>
                    <span v-else>-</span>
                  </el-descriptions-item>
                </el-descriptions>
              </div>

              <el-timeline v-if="executionLogs.length > 0">
                <el-timeline-item
                  v-for="log in executionLogs"
                  :key="log.id"
                  :type="getLogTimelineType(log.node_status)"
                  :timestamp="formatLogTime(log)"
                  placement="top"
                  :hollow="log.node_status === 'skipped'"
                >
                  <div class="log-node-header">
                    <span class="log-node-name">{{ getNodeLabel(log.node_name) }}</span>
                    <el-tag :type="getLogStatusType(log.node_status)" size="small" class="ml-sm">{{ log.node_status }}</el-tag>
                    <span v-if="log.duration_ms" class="log-duration ml-sm">{{ log.duration_ms }}ms</span>
                  </div>

                  <!-- 可展开的详情 -->
                  <el-collapse class="log-detail-collapse">
                    <el-collapse-item title="查看详情">
                      <div class="log-detail-content">
                        <div class="log-section" v-if="log.input_data">
                          <h5 class="log-section-title">输入</h5>
                          <pre class="json-block">{{ formatJson(log.input_data) }}</pre>
                        </div>
                        <div class="log-section" v-if="log.output_data">
                          <h5 class="log-section-title">输出</h5>
                          <pre class="json-block">{{ formatJson(log.output_data) }}</pre>
                        </div>
                        <div class="log-section" v-if="log.error_data">
                          <h5 class="log-section-title error">错误</h5>
                          <pre class="json-block error-block">{{ formatJson(log.error_data) }}</pre>
                        </div>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                </el-timeline-item>
              </el-timeline>
              <el-empty v-else description="暂无执行日志" />
            </div>
          </el-tab-pane>

        </el-tabs>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Close, ArrowRight } from '@element-plus/icons-vue'
import { apiClient } from '@/api/types'
import type { GenerationTask, GenerationItem, ExecutionLog, GenerationItemDetail } from '@/api/types'
import { copyToClipboard } from '@/utils/clipboard'

const router = useRouter()
const route = useRoute()
const taskId = ref(Number(route.params.id))
const filterStatus = ref('')
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const selectedItems = ref<GenerationItem[]>([])
const loading = ref(false)

// 抽屉状态
const drawerVisible = ref(false)
const drawerTab = ref('content')
const textPromptSubTab = ref('system_text') // 文案生成器提示词 TAB
const detailItem = ref<GenerationItemDetail | null>(null)
const textCollapsed = ref(true)
const executionLogs = ref<ExecutionLog[]>([])
const logsLoading = ref(false)
const detailLoading = ref(false)

// 折叠状态
const promptTemplateCollapsed = ref(true)  // 提示词模板内容默认折叠
const materialsCollapsed = ref(true)        // 任务素材默认折叠

// 防御解析图片 URL 数组（兼容后端返回字符串的情况）
const parseImageUrls = (data: any): string[] => {
  if (Array.isArray(data)) return data
  if (typeof data === 'string') {
    try { return JSON.parse(data) } catch { /* fall through */ }
  }
  return []
}

// 获取显示的图片列表（优先使用缩略图，无缩略图时使用原图）
const getDisplayImages = (item: GenerationItemDetail): string[] => {
  const thumbnails = parseImageUrls(item.generated_image_thumbnails_json)
  if (thumbnails.length > 0) {
    return thumbnails
  }
  return parseImageUrls(item.generated_image_urls_json)
}

// 解析话题为标签数组
const parseTopics = (topicsStr: string | string[] | undefined | null): string[] => {
  if (!topicsStr) return []
  // 如果已经是数组，直接返回
  if (Array.isArray(topicsStr)) {
    return topicsStr.filter(Boolean)
  }
  try {
    const parsed = JSON.parse(topicsStr)
    if (Array.isArray(parsed)) return parsed
  } catch { /* not JSON */ }
  // 兼容逗号分隔或空格分隔的字符串
  return topicsStr
    .split(/[,，、\s]+/)
    .map(t => t.replace(/^#/, '').trim())
    .filter(Boolean)
}

// 调试状态
const debugPrompt = ref('')
const debugModelPlatform = ref('')
const debugModelId = ref('')

// 提示词调试模式状态
const promptDebugMode = ref(false)
const promptTemplateTab = ref('text')
const debugTextSystemPrompt = ref('')
const debugTextUserPrompt = ref('')
const debugImageUserPrompt = ref('')
const debugImageUserPrompts = ref<string[]>([])
const debugReferenceImageUrls = ref<string[]>([])

// ========== V5.0: 双图组合模式辅助方法 ==========
const roleLabelMap: Record<string, string> = {
  composition: '构图',
  scene: '场景',
  style: '风格',
}

/** 判断是否启用了双图组合模式 */
function isPairModeEnabled(item: any): boolean {
  return !!(
    item?.input_benchmark_image_enabled
    && item?.input_benchmark_image_roles_json
    && Object.keys(item.input_benchmark_image_roles_json).length > 0
    && item?.input_template_product_mapping_json
    && Object.keys(item.input_template_product_mapping_json).length > 0
    && item?.input_benchmark_images_json?.length > 0
    && item?.input_template_images_json?.length > 0
  )
}

/** 获取指定对标图的角色标签 */
function getBenchmarkRoleTag(idx: number): string {
  if (!detailItem.value?.input_benchmark_image_roles_json) return ''
  const key = `benchmark_${idx + 1}`
  const roles = detailItem.value.input_benchmark_image_roles_json[key]
  if (!roles || !roles.length) return ''
  return roles.map((r: string) => roleLabelMap[r] || r).join(' / ')
}

/** 获取双图组合列表（computed，自动响应 detailItem 变化） */
const pairCombinations = computed<Array<{benchLabel: string, tplLabel: string}>>(() => {
  const item = detailItem.value
  if (!item || !isPairModeEnabled(item)) return []

  const benchCount = item?.input_benchmark_images_json?.length ?? 0
  const tplCount = item?.input_template_images_json?.length ?? 0
  const mapping = item?.input_template_product_mapping_json || {}
  const roles = item?.input_benchmark_image_roles_json || {}

  const combos: Array<{benchLabel: string, tplLabel: string}> = []
  const maxShow = Math.min(benchCount * tplCount, 6) // 最多展示6组

  for (let i = 0; i < maxShow; i++) {
    const bIdx = i % benchCount
    const tIdx = i % tplCount

    const benchKey = `benchmark_${bIdx + 1}`
    const benchRoles = roles[benchKey] || []
    const roleText = benchRoles.map((r: string) => roleLabelMap[r] || r).join('/') || '参考'

    let productLabel = `产品${tIdx + 1}`
    for (const [key, val] of Object.entries(mapping)) {
      if (val === `template_images[${tIdx}]`) {
        productLabel = key
        break
      }
    }

    combos.push({
      benchLabel: `对标${bIdx + 1}(${roleText})`,
      tplLabel: `${productLabel}`,
    })
  }

  return combos
})

// 模型相关状态
const selectedTextModelPlatform = ref('')
const selectedTextModelId = ref('')
const selectedImageModelPlatform = ref('')
const selectedImageModelId = ref('')
const modelPlatforms = ref<string[]>([])
const allModelConfigs = ref<any[]>([])

// 可用的文本模型
const availableTextModels = computed(() => {
  const models = selectedTextModelPlatform.value
    ? allModelConfigs.value.filter(m => m.platform === selectedTextModelPlatform.value && m.model_type === 'llm')
    : allModelConfigs.value.filter(m => m.model_type === 'llm')
  return [{ id: 'auto', model_id: 'auto', model_name: '自动选择' }, ...models]
})

// 可用的图片模型
const availableImageModels = computed(() => {
  const models = selectedImageModelPlatform.value
    ? allModelConfigs.value.filter(m => m.platform === selectedImageModelPlatform.value && m.model_type === 'image')
    : allModelConfigs.value.filter(m => m.model_type === 'image')
  return [{ id: 'auto', model_id: 'auto', model_name: '自动选择' }, ...models]
})

// 文本模型平台选项
const textModelPlatforms = computed(() => {
  const platforms = new Set(allModelConfigs.value.filter(m => m.model_type === 'llm').map(m => m.platform))
  return ['', ...Array.from(platforms)]
})

// 平台切换时清空模型选择
const onTextModelPlatformChange = () => {
  selectedTextModelId.value = ''
}

const onImageModelPlatformChange = () => {
  selectedImageModelId.value = ''
}

// ========== 任务概览可编辑字段 ==========
const selectedTextModelConfigId = ref<number>(0)     // 0=自动
const selectedImageModelConfigId = ref<number>(0)   // 0=自动
const savingDedup = ref(false)

// 所有可用模型（不按平台筛选，用于单一下拉框）
const allLlmModels = computed(() =>
  allModelConfigs.value.filter((m: any) => m.model_type === 'llm' && m.status === 'active')
)
const allImageModels = computed(() =>
  allModelConfigs.value.filter((m: any) => m.model_type === 'image' && m.status === 'active')
)

// 初始化编辑值（从任务数据同步，找到对应的模型配置 ID）
const initEditValues = () => {
  // 文本模型：根据 platform+model_id 找到对应的 config id
  const textConfig = allModelConfigs.value.find(
    (m: any) => m.platform === task.model_platform && m.model_id === task.model_id && m.model_type === 'llm'
  )
  selectedTextModelConfigId.value = textConfig?.id || 0

  // 图片模型
  const imageConfig = allModelConfigs.value.find(
    (m: any) => m.platform === task.image_model_platform && m.model_id === task.image_model_id && m.model_type === 'image'
  )
  selectedImageModelConfigId.value = imageConfig?.id || 0
}

// 保存任务字段（调用后端 API）
const saveTaskField = async (field: string, value: any) => {
  try {
    const updateData: Record<string, any> = { [field]: value }
    await apiClient.updateGenerationTask(taskId.value, updateData as any)
  } catch (error: any) {
    ElMessage.error(`保存失败: ${error.message || '未知错误'}`)
    // 恢复原值
    await refreshTask()
  }
}

// 文本模型变更 → 查找 config 并保存 platform + model_id
const onTaskTextModelChange = (configId: number) => {
  const model = allModelConfigs.value.find((m: any) => m.id === configId)
  const platform = model?.platform || ''
  const modelId = model?.model_id || ''
  task.model_platform = platform
  task.model_id = modelId
  saveTaskField('model_platform', platform)
  saveTaskField('model_id', modelId)
}

// 图片模型变更 → 查找 config 并保存 platform + model_id
const onTaskImageModelChange = (configId: number) => {
  const model = allModelConfigs.value.find((m: any) => m.id === configId)
  const platform = model?.platform || ''
  const modelId = model?.model_id || ''
  task.image_model_platform = platform
  task.image_model_id = modelId
  saveTaskField('image_model_platform', platform)
  saveTaskField('image_model_id', modelId)
}

// 去重开关变更 → 立即保存
const onDedupChange = async (type: 'dedup' | 'image_dedup') => {
  savingDedup.value = true
  try {
    const field = type === 'dedup' ? 'dedup_enabled' : 'image_dedup_enabled'
    const value = type === 'dedup' ? task.dedup_enabled : task.image_dedup_enabled
    await apiClient.updateGenerationTask(taskId.value, { [field]: value } as any)
  } catch (error: any) {
    ElMessage.error(`保存失败: ${error.message || '未知错误'}`)
    if (type === 'dedup') {
      task.dedup_enabled = !task.dedup_enabled
    } else {
      task.image_dedup_enabled = !task.image_dedup_enabled
    }
  } finally {
    savingDedup.value = false
  }
}

// 刷新任务数据（恢复编辑值）
const refreshTask = async () => {
  await fetchTask()
  initEditValues()
}

// 图片模型平台选项
const imageModelPlatforms = computed(() => {
  const platforms = new Set(allModelConfigs.value.filter(m => m.model_type === 'image').map(m => m.platform))
  return ['', ...Array.from(platforms)]
})

// 提示词模板内容
const textPromptTemplateContent = ref('')
const imagePromptTemplateContent = ref('')
const textPromptTemplateId = ref<number | null>(null)
const imagePromptTemplateId = ref<number | null>(null)

// 任务详情页的提示词模板内容和 TAB
const taskTextPromptTemplateContent = ref('')
const taskImagePromptTemplateContent = ref('')
const taskPromptTemplateTab = ref('text')
// 跟踪提示词模板是否已加载，避免在轮询时重复加载
const taskPromptTemplatesLoaded = ref(false)
const lastTextPromptTemplateId = ref<number | null>(null)
const lastImagePromptTemplateId = ref<number | null>(null)

// 调试模式内容生成状态
const textGenerating = ref(false)
const imageGenerating = ref(false)
const promptsGenerating = ref(false)
const debugGeneratedText = ref<{ title: string; content: string; topics: string[] } | null>(null)
const debugGeneratedImages = ref<string[]>([])

// 任务详情
const task = reactive<Partial<GenerationTask>>({
  status: 'pending',
  total_count: 0,
  queued_count: 0,
  generating_count: 0,
  completed_count: 0,
  failed_count: 0,
  paused_count: 0,
  distributed_count: 0,
  pending_publish_count: 0,
  published_count: 0,
  created_at: ''
})

// 子任务列表
const items = ref<GenerationItem[]>([])

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 计算耗时
const calcDuration = (startAt: string, completedAt: string) => {
  const start = new Date(startAt).getTime()
  const end = new Date(completedAt).getTime()
  const seconds = Math.round((end - start) / 1000)
  if (seconds < 60) return `${seconds}秒`
  const minutes = Math.floor(seconds / 60)
  const remainSeconds = seconds % 60
  return `${minutes}分${remainSeconds}秒`
}

// 格式化任务总耗时（秒数转为可读格式）
const formatDuration = (seconds: number | undefined | null) => {
  if (seconds === undefined || seconds === null || Number.isNaN(seconds)) return '-'
  if (seconds < 0) return '-'
  if (seconds < 60) return `${seconds}秒`
  const minutes = Math.floor(seconds / 60)
  const remainSeconds = seconds % 60
  if (minutes < 60) {
    return remainSeconds > 0 ? `${minutes}分${remainSeconds}秒` : `${minutes}分钟`
  }
  const hours = Math.floor(minutes / 60)
  const remainMinutes = minutes % 60
  return `${hours}小时${remainMinutes}分钟`
}

// 计算进度百分比
const getProgress = computed(() => {
  if (task.total_count === 0) return 0
  return Math.round((task.completed_count! / task.total_count!) * 100)
})

// 获取任务状态标签
const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    pending: '排队中',
    processing: '生成中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return labels[status] || status
}

// 获取子任务状态标签
const getItemStatusLabel = (status: string, distributionStatus?: string) => {
  // 如果有分发状态且生成已完成，优先显示分发状态
  if (status === 'completed' && distributionStatus) {
    const distributionLabels: Record<string, string> = {
      draft: '草稿',
      ready: '待分发',
      distributed: '已分发',
      pending_publish: '待发布',
      published: '已发布'
    }
    if (distributionLabels[distributionStatus]) {
      return distributionLabels[distributionStatus]
    }
  }
  const labels: Record<string, string> = {
    queued: '排队中',
    generating: '生成中',
    paused: '已暂停',
    completed: '已完成',
    failed: '失败'
  }
  return labels[status] || status
}

// 批量操作权限判断
const canBatchPause = computed(() => selectedItems.value.some(item => ['queued', 'generating'].includes(item.status)))
const canBatchResume = computed(() => selectedItems.value.some(item => item.status === 'paused'))
const canBatchRetry = computed(() => selectedItems.value.some(item => item.status === 'failed'))

// 获取任务详情
const fetchTask = async (forceLoadTemplates: boolean = false) => {
  try {
    const response = await apiClient.getGenerationTask(taskId.value)
    Object.assign(task, response)
    // 先加载模型配置（下拉选项数据），再初始化编辑值
    await loadModelConfigs()
    initEditValues()
    // 只在第一次加载或模板ID变化时才加载提示词模板内容
    if (forceLoadTemplates || !taskPromptTemplatesLoaded.value ||
        lastTextPromptTemplateId.value !== task.text_prompt_template_id ||
        lastImagePromptTemplateId.value !== task.image_prompt_template_id) {
      await loadTaskPromptTemplates()
      taskPromptTemplatesLoaded.value = true
    }
  } catch (error: any) {
    ElMessage.error(error.message || '获取任务详情失败')
  }
}

// 加载任务详情页的提示词模板内容
const loadTaskPromptTemplates = async () => {
  // 重置内容
  taskTextPromptTemplateContent.value = ''
  taskImagePromptTemplateContent.value = ''

  // 设置默认 TAB
  if (task.text_prompt_template_id) {
    taskPromptTemplateTab.value = 'text'
  } else if (task.image_prompt_template_id) {
    taskPromptTemplateTab.value = 'image'
  }

  // 记录当前加载的模板ID
  lastTextPromptTemplateId.value = task.text_prompt_template_id || null
  lastImagePromptTemplateId.value = task.image_prompt_template_id || null

  // 加载文案提示词模板
  if (task.text_prompt_template_id) {
    try {
      const template = await apiClient.getPromptTemplate(task.text_prompt_template_id)
      taskTextPromptTemplateContent.value = template.content
    } catch (error) {
      console.error('加载文案提示词模板失败:', error)
      taskTextPromptTemplateContent.value = '加载失败'
    }
  }

  // 加载图片提示词模板
  if (task.image_prompt_template_id) {
    try {
      const template = await apiClient.getPromptTemplate(task.image_prompt_template_id)
      taskImagePromptTemplateContent.value = template.content
    } catch (error) {
      console.error('加载图片提示词模板失败:', error)
      taskImagePromptTemplateContent.value = '加载失败'
    }
  }
}

// 获取子任务列表
const fetchItems = async () => {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      limit: pageSize.value
    }
    if (filterStatus.value) {
      params.status = filterStatus.value
    }
    const response = await apiClient.getGenerationItems(taskId.value, params)
    items.value = response.items || []
    total.value = response.total || 0
  } catch (error: any) {
    ElMessage.error(error.message || '获取子任务列表失败')
  } finally {
    loading.value = false
  }
}

// 取消任务
const cancelTask = async () => {
  try {
    await ElMessageBox.confirm('确定要取消此任务吗？未完成的子任务将被取消。', '确认取消', { type: 'warning' })
    await apiClient.cancelGenerationTask(taskId.value)
    ElMessage.success('任务已取消')
    fetchTask()
  } catch (error: any) {
    if (error.message !== 'cancel') {
      ElMessage.error(error.message || '取消任务失败')
    }
  }
}

// 重试失败项
const retryFailed = async () => {
  try {
    await apiClient.batchRetryGenerationItems({ task_id: taskId.value })
    ElMessage.success('重试失败的子任务已加入队列')
    fetchItems()
    fetchTask()
  } catch (error: any) {
    ElMessage.error(error.message || '重试失败')
  }
}

// 表格选择
const handleSelectionChange = (selection: GenerationItem[]) => {
  selectedItems.value = selection
}

// 行点击
const handleRowClick = (row: GenerationItem) => {
  openDetailDrawer(row)
}

// 打开详情抽屉
const openDetailDrawer = async (item: GenerationItem) => {
  drawerVisible.value = true
  drawerTab.value = 'content'
  textCollapsed.value = true
  textPromptSubTab.value = 'system_text'

  // 初始化调试字段
  debugPrompt.value = item.final_prompt || ''
  debugModelPlatform.value = item.model_platform || ''
  debugModelId.value = item.model_id || ''

  // 加载模型配置
  await loadModelConfigs()

  // 加载完整详情
  await fetchDetail(item.id)

  // 加载提示词模板内容
  await loadPromptTemplates()

  // 加载执行日志
  await fetchExecutionLogs(item.id)
}

// 加载提示词模板内容
const loadPromptTemplates = async () => {
  if (!detailItem.value) return

  // 重置内容
  textPromptTemplateContent.value = ''
  imagePromptTemplateContent.value = ''

  // 加载文案提示词模板
  if (detailItem.value.text_prompt_template_id) {
    try {
      const template = await apiClient.getPromptTemplate(detailItem.value.text_prompt_template_id)
      textPromptTemplateContent.value = template.content
      textPromptTemplateId.value = template.id
    } catch (error) {
      console.error('加载文案提示词模板失败:', error)
      textPromptTemplateContent.value = '加载失败'
    }
  }

  // 加载图片提示词模板
  if (detailItem.value.image_prompt_template_id) {
    try {
      const template = await apiClient.getPromptTemplate(detailItem.value.image_prompt_template_id)
      imagePromptTemplateContent.value = template.content
      imagePromptTemplateId.value = template.id
    } catch (error) {
      console.error('加载图片提示词模板失败:', error)
      imagePromptTemplateContent.value = '加载失败'
    }
  }
}

// 加载模型配置
const loadModelConfigs = async () => {
  try {
    const configs = await apiClient.getModelConfigs()
    allModelConfigs.value = configs
    // 提取唯一的平台列表
    modelPlatforms.value = [...new Set(configs.map((c: any) => c.platform))]
  } catch (error) {
    console.error('加载模型配置失败:', error)
  }
}

// 提示词生成
const generatePrompts = async () => {
  if (!detailItem.value?.id) {
    ElMessage.warning('请先选择一个子任务')
    return
  }
  promptsGenerating.value = true
  try {
    const response = await apiClient.debugGeneratePrompts({
      item_id: detailItem.value.id,
      text_system_prompt_override: debugTextSystemPrompt.value || undefined,
      model_platform_override: selectedTextModelPlatform.value || undefined,
      model_id_override: selectedTextModelId.value || undefined
    })

    // 更新输出提示词到 detailItem
    if (detailItem.value) {
      detailItem.value.output_system_text_prompt = response.text_generator_system_prompt
      detailItem.value.output_user_text_prompt = response.text_generator_user_prompt
      detailItem.value.aigc_user_image_prompts_json = response.image_prompts
      detailItem.value.output_topics = response.topics
      // 构建 AIGC 提示词生成器产出的预览内容（生图模型不使用系统提示词）
      detailItem.value.aigc_generated_prompt = JSON.stringify({
        text_generator_user_prompt: response.text_generator_user_prompt,
        image_prompts: response.image_prompts,
        topics: response.topics,
        text_generator_system_prompt: response.text_generator_system_prompt,
        text_prompt_success: response.text_prompt_success,
        image_prompt_success: response.image_prompt_success
      }, null, 2)

      // 更新调试模式下的编辑框
      debugTextSystemPrompt.value = response.text_generator_system_prompt
      debugTextUserPrompt.value = response.text_generator_user_prompt
      debugImageUserPrompts.value = response.image_prompts || []
      debugReferenceImageUrls.value = response.reference_image_urls || []

      // 显示结果消息
      let message = '提示词生成完成'
      if (!response.text_prompt_success && response.text_prompt_error) {
        message += ` | 文案提示词失败: ${response.text_prompt_error}`
      }
      if (!response.image_prompt_success && response.image_prompt_error) {
        message += ` | 图片提示词失败: ${response.image_prompt_error}`
      }
      ElMessage.success(message)
    }

    // 如果是调试模式，同时更新到调试输入框中
    if (promptDebugMode.value) {
      debugTextSystemPrompt.value = response.text_generator_system_prompt || ''
      debugTextUserPrompt.value = response.text_generator_user_prompt || ''
      // 图片用户提示词 - 更新所有提示词
      if (response.image_prompts && response.image_prompts.length > 0) {
        debugImageUserPrompts.value = [...response.image_prompts]
        debugImageUserPrompt.value = response.image_prompts[0]
      } else {
        debugImageUserPrompts.value = []
        debugImageUserPrompt.value = ''
      }
    }

    ElMessage.success('提示词生成成功')
  } catch (error: any) {
    ElMessage.error(error.message || '提示词生成失败')
  } finally {
    promptsGenerating.value = false
  }
}

// 文案生成
const generateText = async () => {
  ElMessage.info('文案生成功能待后端API支持')
  // TODO: 实现文案生成功能
}

// 图片生成
const generateImages = async () => {
  ElMessage.info('图片生成功能待后端API支持')
  // TODO: 实现图片生成功能
}

// 调试模式下的文案生成
const debugGenerateText = async () => {
  if (!detailItem.value?.id) {
    ElMessage.warning('请先选择一个子任务')
    return
  }
  textGenerating.value = true
  try {
    const response = await apiClient.debugGenerateText({
      item_id: detailItem.value.id,
      system_prompt_override: debugTextSystemPrompt.value || undefined,
      user_prompt_override: debugTextUserPrompt.value || undefined,
      model_platform_override: selectedTextModelPlatform.value || undefined,
      model_id_override: selectedTextModelId.value && selectedTextModelId.value !== 'auto' ? selectedTextModelId.value : undefined
    })

    debugGeneratedText.value = {
      title: response.title,
      content: response.content,
      topics: response.topics
    }

    // 如果返回了图片提示词，更新到图片生成区域
    if (response.image_prompts && response.image_prompts.length > 0) {
      debugImageUserPrompts.value = [...response.image_prompts]
      debugImageUserPrompt.value = response.image_prompts[0]
      ElMessage.success(`文案生成成功，解析出 ${response.image_prompts.length} 条图片提示词`)
    } else {
      ElMessage.success('文案生成成功')
    }
  } catch (error: any) {
    ElMessage.error(error.message || '文案生成失败')
  } finally {
    textGenerating.value = false
  }
}

// 调试模式下的图片生成
const debugGenerateImages = async () => {
  if (!detailItem.value?.id) {
    ElMessage.warning('请先选择一个子任务')
    return
  }
  imageGenerating.value = true
  try {
    // Determine the user prompts to use - 优先使用所有的图片提示词
    let userPrompts: string[] | undefined = undefined
    if (debugImageUserPrompts.value && debugImageUserPrompts.value.length > 0) {
      userPrompts = [...debugImageUserPrompts.value]
    } else if (debugImageUserPrompt.value) {
      userPrompts = [debugImageUserPrompt.value]
    } else if (detailItem.value?.aigc_user_image_prompts_json?.length) {
      userPrompts = detailItem.value.aigc_user_image_prompts_json
    } else if (detailItem.value?.output_user_image_prompt) {
      userPrompts = [detailItem.value.output_user_image_prompt]
    }

    const response = await apiClient.debugGenerateImages({
      item_id: detailItem.value.id,
      user_prompts_override: userPrompts,
      model_platform_override: selectedImageModelPlatform.value || undefined,
      model_id_override: selectedImageModelId.value && selectedImageModelId.value !== 'auto' ? selectedImageModelId.value : undefined,
      reference_image_urls_override: debugReferenceImageUrls.value?.length ? debugReferenceImageUrls.value : undefined
    })

    debugGeneratedImages.value = response.image_urls
    ElMessage.success('图片生成成功')
  } catch (error: any) {
    ElMessage.error(error.message || '图片生成失败')
  } finally {
    imageGenerating.value = false
  }
}

// 添加图片提示词
const addImagePrompt = () => {
  if (debugImageUserPrompts.value.length === 0 && debugImageUserPrompt.value) {
    debugImageUserPrompts.value = [debugImageUserPrompt.value]
  }
  debugImageUserPrompts.value.push('')
}

// 删除图片提示词
const removeImagePrompt = (idx: number) => {
  debugImageUserPrompts.value.splice(idx, 1)
  // 如果删除后没有提示词了，把单个提示词也清空
  if (debugImageUserPrompts.value.length === 0) {
    debugImageUserPrompt.value = ''
  }
}

// 加载子任务完整详情
const fetchDetail = async (itemId: number) => {
  detailLoading.value = true
  try {
    const detail = await apiClient.getGenerationItemDetail(itemId)
    detailItem.value = detail

    // 初始化调试模式的提示词
    debugTextSystemPrompt.value = detail.output_system_text_prompt || ''
    debugTextUserPrompt.value = detail.output_user_text_prompt || ''
    // 图片用户提示词 - 存储所有提示词（生图模型不使用系统提示词）
    if (detail.aigc_user_image_prompts_json && detail.aigc_user_image_prompts_json.length > 0) {
      debugImageUserPrompts.value = [...detail.aigc_user_image_prompts_json]
      debugImageUserPrompt.value = detail.aigc_user_image_prompts_json[0]
    } else if (detail.output_user_image_prompt) {
      debugImageUserPrompts.value = [detail.output_user_image_prompt]
      debugImageUserPrompt.value = detail.output_user_image_prompt
    } else {
      debugImageUserPrompts.value = []
      debugImageUserPrompt.value = ''
    }
    // 初始化参考图片（从子任务详情中获取）
    // 后端已正确填充 input_template_images_json（模板附件中的产品图）
    // 和 input_benchmark_images_json（对标素材附件中的对标图）
    debugReferenceImageUrls.value = [
      ...(detail.input_template_images_json || []),  // 产品图
      ...(detail.input_benchmark_images_json || [])  // 对标图
    ]
    console.log('[Frontend] 参考图片初始化 | product=', detail.input_template_images_json?.length || 0, 
               'benchmark=', detail.input_benchmark_images_json?.length || 0)
  } catch (error: any) {
    console.error('获取子任务详情失败:', error)
  } finally {
    detailLoading.value = false
  }
}

// 获取执行日志
const fetchExecutionLogs = async (itemId: number) => {
  logsLoading.value = true
  try {
    executionLogs.value = await apiClient.getItemExecutionLogs(itemId)
  } catch (error: any) {
    console.error('获取执行日志失败:', error)
    executionLogs.value = []
  } finally {
    logsLoading.value = false
  }
}

// 节点标签映射
const getNodeLabel = (name: string) => {
  const labels: Record<string, string> = {
    prompt_build: '提示词构建',
    llm_call: '文本模型调用',
    image_call: '图片模型调用',
    aigc_prompt_generator: 'AIGC 提示词生成器',
    aigc_copy_generator: 'AIGC 文案生成器',
    aigc_image_generator: 'AIGC 图片生成器',
    dedup_check: '去重检测',
    save_result: '结果保存',
  }
  return labels[name] || name
}

// 日志时间线类型
const getLogTimelineType = (status: string) => {
  const map: Record<string, string> = {
    running: 'primary',
    success: 'success',
    failed: 'danger',
    skipped: 'info',
  }
  return map[status] || 'info'
}

// 日志状态标签类型
const getLogStatusType = (status: string) => {
  const map: Record<string, any> = {
    running: 'primary',
    success: 'success',
    failed: 'danger',
    skipped: 'info',
  }
  return map[status] || 'info'
}

// 格式化日志时间
const formatLogTime = (log: ExecutionLog) => {
  const parts: string[] = []
  if (log.started_at) parts.push(`开始: ${formatDate(log.started_at)}`)
  if (log.completed_at) parts.push(`完成: ${formatDate(log.completed_at)}`)
  if (log.duration_ms) parts.push(`耗时: ${log.duration_ms}ms`)
  return parts.join(' | ') || '-'
}

// 格式化 JSON
const formatJson = (data: any) => {
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}

// 执行结果标签
const getExecutionResultType = (result: string) => {
  const map: Record<string, string> = {
    success: 'success',
    failed: 'danger',
    partial: 'warning',
  }
  return map[result] || 'info'
}

const getExecutionResultLabel = (result: string) => {
  const map: Record<string, string> = {
    success: '成功',
    failed: '失败',
    partial: '部分成功',
  }
  return map[result] || result
}

// 解析文案输出：拆分标题、正文、话题
const parsedText = computed(() => {
  const text = detailItem.value?.generated_text
  if (!text) return { title: null, content: null, topics: [] }

  // 优先使用已解析的标题字段
  const title = detailItem.value?.generated_title

  // 如果内容已包含结构化数据且标题不在正文中，直接使用正文
  if (title && !text.startsWith(title)) {
    return { title, content: text, topics: [] }
  }

  // 尝试去除可能的 JSON 包裹
  let cleaned = text.trim()
  // 去除开头的标题行
  if (title && cleaned.startsWith(title)) {
    cleaned = cleaned.slice(title.length).trim()
    // 去除可能的换行分隔
    cleaned = cleaned.replace(/^\n+/, '')
  }

  return {
    title,
    content: cleaned || text,
    topics: []
  }
})

// 通用复制方法（兼容 HTTP/HTTPS）
const copyText = async (text: string) => {
  if (text) {
    const success = await copyToClipboard(text)
    if (success) {
      ElMessage.success('已复制到剪贴板')
    } else {
      ElMessage.error('复制失败，请手动复制')
    }
  }
}

// 复制文案（标题+正文+话题）
const copyFullTextContent = async () => {
  const title = detailItem.value?.generated_title || ''
  const text = detailItem.value?.generated_text || ''
  const topics = parseTopics(detailItem.value?.output_topics)
  const topicsText = topics.map(t => `#${t}`).join(' ')

  const fullContent = [title, text, topicsText].filter(Boolean).join('\n\n')
  if (fullContent) {
    const success = await copyToClipboard(fullContent)
    if (success) {
      ElMessage.success('文案已复制到剪贴板')
    } else {
      ElMessage.error('复制失败，请手动复制')
    }
  }
}

// 复制话题
const copyTopics = async () => {
  const topics = parseTopics(detailItem.value?.output_topics)
  if (topics.length > 0) {
    const topicsText = topics.map(t => `#${t}`).join(' ')
    const success = await copyToClipboard(topicsText)
    if (success) {
      ElMessage.success('话题已复制到剪贴板')
    } else {
      ElMessage.error('复制失败，请手动复制')
    }
  }
}

// 复制错误信息
const copyError = async () => {
  if (detailItem.value?.error_message) {
    const success = await copyToClipboard(detailItem.value.error_message)
    if (success) {
      ElMessage.success('错误信息已复制到剪贴板')
    } else {
      ElMessage.error('复制失败，请手动复制')
    }
  }
}

// 单个子任务操作
const retryItem = async (row: GenerationItem) => {
  try {
    await apiClient.retryGenerationItem(row.id)
    ElMessage.success('重试成功')
    fetchItems()
    fetchTask()
  } catch (error: any) {
    ElMessage.error(error.message || '重试失败')
  }
}

const regenerateItem = async (row: GenerationItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要重新生成子任务 #${row.id} 吗？\n\n重新生成将清除当前内容并重新生成。`,
      '确认重新生成',
      { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' }
    )
    await apiClient.regenerateGenerationItem(row.id)
    ElMessage.success('重新生成任务已提交')
    fetchItems()
    fetchTask()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '重新生成失败')
    }
  }
}

const pauseItem = async (row: GenerationItem) => {
  try {
    await apiClient.pauseGenerationItem(row.id)
    ElMessage.success('已暂停')
    fetchItems()
    fetchTask()
  } catch (error: any) {
    ElMessage.error(error.message || '暂停失败')
  }
}

const resumeItem = async (row: GenerationItem) => {
  try {
    await apiClient.resumeGenerationItem(row.id)
    ElMessage.success('已继续')
    fetchItems()
    fetchTask()
  } catch (error: any) {
    ElMessage.error(error.message || '继续失败')
  }
}

// 批量操作
const batchPause = async () => {
  try {
    const itemIds = selectedItems.value.map(item => item.id)
    await apiClient.batchPauseGenerationItems({ item_ids: itemIds, pause: true })
    ElMessage.success('批量暂停成功')
    selectedItems.value = []
    fetchItems()
    fetchTask()
  } catch (error: any) {
    ElMessage.error(error.message || '批量暂停失败')
  }
}

const batchResume = async () => {
  try {
    const itemIds = selectedItems.value.map(item => item.id)
    await apiClient.batchPauseGenerationItems({ item_ids: itemIds, pause: false })
    ElMessage.success('批量继续成功')
    selectedItems.value = []
    fetchItems()
    fetchTask()
  } catch (error: any) {
    ElMessage.error(error.message || '批量继续失败')
  }
}

const batchRetry = async () => {
  try {
    const itemIds = selectedItems.value.map(item => item.id)
    await apiClient.batchRetryGenerationItems({ item_ids: itemIds })
    ElMessage.success('批量重试成功')
    selectedItems.value = []
    fetchItems()
    fetchTask()
  } catch (error: any) {
    ElMessage.error(error.message || '批量重试失败')
  }
}

// 状态筛选变化
watch(filterStatus, () => {
  currentPage.value = 1
  fetchItems()
})

// 分页变化
watch([currentPage, pageSize], () => {
  fetchItems()
})

// 切换抽屉 Tab 时退出调试模式
watch(drawerTab, (newTab) => {
  if (newTab !== 'output') {
    promptDebugMode.value = false
  }
})

// 自动轮询逻辑
const pollingTimer = ref<number | null>(null)

watch(() => task.status, (status) => {
  if (status === 'processing') {
    // 任务处理中时，每 5 秒自动刷新子任务列表
    pollingTimer.value = window.setInterval(() => {
      fetchItemsLight()
    }, 5000)
  } else {
    if (pollingTimer.value) {
      clearInterval(pollingTimer.value)
      pollingTimer.value = null
    }
  }
})

onUnmounted(() => {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
})

// 轻量级刷新（刷新子任务列表 + 任务详情）
const fetchItemsLight = async () => {
  try {
    // 同时刷新子任务列表和任务详情
    const params: any = {
      page: currentPage.value,
      limit: pageSize.value
    }
    if (filterStatus.value) {
      params.status = filterStatus.value
    }
    const [itemsResponse] = await Promise.all([
      apiClient.getGenerationItems(taskId.value, params),
      fetchTask(),
    ])
    items.value = itemsResponse.items || []
    total.value = itemsResponse.total || 0
  } catch (error: any) {
    console.error('轻量级刷新失败:', error)
  }
}

// current_step 中文映射
const currentStepLabels: Record<string, string> = {
  prompt_building: '提示词构建中',
  aigc_prompt_gen: 'AIGC提示词生成中',
  text_generating: '文案生成中',
  dedup_checking: '去重检测中',
  dedup_retrying: '去重重试中',
  image_prompt_gen: '图片提示词生成中',
  image_generating: '图片生成中',
  saving: '结果保存中',
}

const getCurrentStepLabel = (step: string | undefined) => {
  if (!step) return ''
  return currentStepLabels[step] || step
}

// 组件挂载时获取数据
onMounted(() => {
  fetchTask()
  fetchItems()
})

const getStatusType = (status: string) => {
  const map: Record<string, any> = {
    pending: 'info',
    processing: 'primary',
    completed: 'success',
    failed: 'warning',
    cancelled: 'info'
  }
  return map[status] || 'info'
}

const getItemStatusType = (status: string, distributionStatus?: string) => {
  // 如果有分发状态且生成已完成，优先显示分发状态对应的类型
  if (status === 'completed' && distributionStatus) {
    const distributionMap: Record<string, any> = {
      draft: 'info',
      ready: 'info',
      distributed: 'success',
      pending_publish: 'warning',
      published: 'success'
    }
    if (distributionMap[distributionStatus]) {
      return distributionMap[distributionStatus]
    }
  }
  const map: Record<string, any> = {
    queued: 'info',
    generating: 'primary',
    paused: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

const goBack = () => {
  router.push('/generation')
}
</script>

<style lang="scss" scoped>
@import '../../assets/styles/variables.scss';

.generation-detail-view {
  padding: 0;
}

.page-header {
  margin-bottom: 16px;
}

.header-actions {
  align-items: center;
}

.mb-md {
  margin-bottom: 16px;
}

.mt-md {
  margin-top: 16px;
}

.mt-lg {
  margin-top: 24px;
}

.ml-sm {
  margin-left: 8px;
}

.ml-md {
  margin-left: 12px;
}

.flex {
  display: flex;
}

.flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.gap-sm {
  gap: 6px;
}

.gap-md {
  gap: 12px;
}

.gap-lg {
  gap: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.section-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
}

// 可折叠头部
.collapsible-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  padding: 8px 12px;
  background: var(--bg-secondary);
  border-radius: 6px;
  margin-bottom: 12px;
  transition: background-color 0.2s;

  &:hover {
    background: var(--bg-secondary);
  }

  .section-label {
    margin-bottom: 0;
  }

  .collapse-icon {
    transition: transform 0.3s;
    color: var(--text-placeholder);
    font-size: 14px;

    &.is-expanded {
      transform: rotate(90deg);
    }
  }
}

.progress-section {
  .progress-header {
    margin-bottom: 8px;
    .progress-title {
      font-size: 14px;
      font-weight: 500;
    }
    .progress-text {
      font-size: 18px;
      font-weight: 600;
      color: var(--color-primary);
    }
  }
  .progress-stats {
    .stat-item {
      .label {
        color: var(--text-muted);
        margin-right: 4px;
      }
      .value {
        font-weight: 600;
        &.primary { color: var(--color-primary); }
        &.success { color: #67C23A; }
        &.danger { color: #F56C6C; }
        &.warning { color: #E6A23C; }
        &.info { color: var(--color-primary); }
      }
    }
  }
}

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

.pagination {
  padding: $spacing-sm 0;
  white-space: nowrap;
  display: flex;
  align-items: center;
}

.total-text {
  color: var(--color-text-secondary);
  font-size: $font-size-sm;
  white-space: nowrap;
}

// 生成预览单元格
.preview-cell {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.preview-images {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.preview-thumb {
  width: 48px;
  height: 48px;
  border-radius: 4px;
  background: var(--bg-tertiary);
  flex-shrink: 0;
}

.more-images {
  width: 48px;
  height: 48px;
  border-radius: 4px;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: var(--text-placeholder);
  flex-shrink: 0;
}

.preview-text {
  min-width: 0;
  .content-title {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-primary);
    line-height: 1.4;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .content-text {
    font-size: 12px;
    color: var(--text-placeholder);
    line-height: 1.4;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }
}

// 可点击行
:deep(.clickable-row) {
  cursor: pointer;
}

// 抽屉内容
.drawer-content {
  padding: 0 8px;
}

// 生成内容 Tab
.content-section {
  .content-value {
    color: var(--text-secondary);
    font-size: 14px;
  }
  .content-body {
    .text-content {
      color: var(--text-secondary);
      line-height: 1.8;
      font-size: 14px;
      white-space: pre-wrap;
      &.collapsed {
        max-height: 200px;
        overflow: hidden;
        position: relative;
        &::after {
          content: '';
          position: absolute;
          bottom: 0;
          left: 0;
          right: 0;
          height: 40px;
          background: linear-gradient(transparent, white);
        }
      }
    }
  }
}

// 结构化内容卡片
.structured-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.content-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.2s;

  &:hover {
    border-color: #dcdfe6;
  }
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--bg-tertiary);
  border-bottom: 1px solid var(--border-color);

  .card-icon {
    font-size: 16px;
  }

  .card-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    flex: 1;
  }
}

.card-body {
  padding: 16px;
}

.card-footer {
  padding: 8px 16px;
  border-top: 1px solid var(--border-color);
  text-align: center;
}

// 标题卡片
.title-card .title-body {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

// 正文卡片
.body-card .text-body {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.8;
  max-height: 400px;
  overflow-y: auto;

  &.collapsed {
    max-height: 200px;
    overflow: hidden;
    position: relative;

    &::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 40px;
      background: linear-gradient(transparent, white);
    }
  }
}

.parsed-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.text-paragraph {
  display: inline;
}

// 话题卡片
.topics-card .topics-body {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px;

  .topic-tag {
    font-weight: 500;
  }
}

.image-gallery {
  .gallery-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 12px;
  }
  .gallery-item {
    width: 100%;
    height: 150px;
    border-radius: 6px;
    background: var(--bg-tertiary);
  }
}

.actions-bar {
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

// 错误信息区块
.error-section {
  .section-label.error {
    color: #F56C6C;
  }
}

.error-detail-block {
  background: #fef0f0;
  border: 1px solid #fbc4c4;
  border-radius: 6px;
  padding: 12px 16px;

  .error-content {
    color: #F56C6C;
    font-size: 13px;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
    font-family: var(--font-family-mono);
    max-height: 300px;
    overflow-y: auto;
  }
}

// 执行链路 Tab
.execution-section {
  padding-top: 8px;
}

.log-node-header {
  display: flex;
  align-items: center;
  .log-node-name {
    font-weight: 500;
    font-size: 14px;
    color: var(--text-primary);
  }
  .log-duration {
    font-size: 12px;
    color: var(--text-placeholder);
  }
}

.log-detail-collapse {
  margin-top: 8px;
  border: none;
  :deep(.el-collapse-item__header) {
    height: 28px;
    line-height: 28px;
    font-size: 12px;
    color: var(--color-primary);
    border: none;
    background: transparent;
  }
  :deep(.el-collapse-item__wrap) {
    border: none;
    background: transparent;
  }
}

.log-detail-content {
  .log-section {
    margin-bottom: 12px;
    .log-section-title {
      font-size: 12px;
      font-weight: 500;
      color: var(--text-secondary);
      margin-bottom: 4px;
      &.error {
        color: #F56C6C;
      }
    }
  }
}

.json-block {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 6px;
  font-family: var(--font-family-mono);
  font-size: 12px;
  line-height: 1.5;
  max-height: 300px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  &.small {
    font-size: 11px;
    max-height: 200px;
  }
  &.error-block {
    border: 1px solid #F56C6C;
  }
}

// 调试重跑 Tab
.debug-section {
  .debug-tip {
    margin-bottom: 16px;
  }
}

// 素材展示区域
.materials-section {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  margin-top: 16px;
}

// 当前步骤提示
.step-hint {
  font-size: 11px;
  color: var(--text-placeholder);
  margin-top: 2px;
  line-height: 1.2;
}

// 输出内容区块 - 新增样式
.output-section {
  .output-block {
    margin-bottom: 24px;
    .block-title.primary {
      border-left-color: var(--color-primary);
    }
    .node-status {
      font-size: 12px;
      color: #67C23A;
      margin-left: 8px;
    }
  }
  .sub-block {
    margin: 16px 0;
    padding: 12px;
    background: var(--bg-tertiary);
    border-radius: 6px;
    .sub-block-title {
      font-size: 13px;
      font-weight: 500;
      color: var(--text-primary);
      margin-bottom: 8px;
    }
  }
  .image-prompt-item {
    margin-bottom: 16px;
    padding: 12px;
    background: var(--bg-tertiary);
    border-radius: 6px;
    .image-prompt-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
      .prompt-label {
        font-size: 13px;
        font-weight: 500;
        color: var(--color-primary);
      }
    }
    .prompt-index {
      font-size: 12px;
      color: var(--text-secondary);
      margin-right: 8px;
    }
    .prompt-box {
      display: inline-block;
      max-width: calc(100% - 40px);
      vertical-align: top;
    }
  }
  .mt-2 {
    margin-top: 8px;
  }
  .topics-preview {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    .topic-tag {
      font-weight: 500;
    }
  }
}

// 去重检测结果样式
.dedup-result {
  background: var(--bg-tertiary);
  border-radius: 6px;
  padding: 12px 16px;
  .dedup-summary {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 8px;
    .dedup-status {
      font-weight: 600;
      &.passed { color: #67C23A; }
      &.failed { color: #F56C6C; }
    }
    .dedup-similarity {
      font-size: 13px;
      color: var(--text-secondary);
    }
  }
  .dedup-time {
    font-size: 12px;
    color: var(--text-placeholder);
    margin-bottom: 8px;
  }
  .dedup-references {
    margin-top: 8px;
    .ref-item {
      display: flex;
      align-items: flex-start;
      gap: 8px;
      padding: 8px;
      background: var(--bg-secondary);
      border-radius: 4px;
      margin-bottom: 6px;
      font-size: 12px;
      .ref-item-id {
        color: var(--color-primary);
        flex-shrink: 0;
      }
      .ref-similarity {
        color: #E6A23C;
        flex-shrink: 0;
      }
      .ref-preview {
        color: var(--text-secondary);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
  }
}

.material-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 12px;
  
  .material-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    
    .material-label {
      font-size: 12px;
      color: var(--text-muted);
      background: var(--bg-tertiary);
      padding: 2px 8px;
      border-radius: 4px;
    }
    
    .material-title {
      font-size: 13px;
      font-weight: 500;
      color: var(--text-primary);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      flex: 1;
    }
  }
  
  .material-thumbnails {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    
    .material-thumb {
      width: 60px;
      height: 60px;
      border-radius: 4px;
      background: var(--bg-secondary);
      flex-shrink: 0;
    }
    
    .more-count {
      width: 60px;
      height: 60px;
      border-radius: 4px;
      background: var(--bg-tertiary);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      color: var(--text-placeholder);
      flex-shrink: 0;
    }
  }
  
  .no-thumbnails {
    color: var(--text-placeholder);
    font-size: 12px;
    text-align: center;
    padding: 20px 0;
  }

  .template-prompt-info {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px dashed #dcdfe6;

    .prompt-label {
      font-size: 12px;
      color: var(--text-muted);
      margin-bottom: 4px;
    }

    .prompt-content {
      font-size: 12px;
      color: var(--text-secondary);
      line-height: 1.6;
      background: var(--bg-secondary);
      padding: 8px;
      border-radius: 4px;
      max-height: 150px;
      overflow-y: auto;
      white-space: pre-wrap;
      word-break: break-word;

      &.code {
        font-family: var(--font-family-mono);
        font-size: 11px;
        background: #1e1e1e;
        color: #d4d4d4;
      }
    }
  }

  // 对标素材正文和话题信息
  .benchmark-text-info {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px dashed #dcdfe6;

    .benchmark-topic {
      margin-bottom: 8px;

      .topic-label {
        font-size: 12px;
        color: var(--text-placeholder);
        margin-right: 6px;
      }

      .topic-value {
        font-size: 12px;
        color: #E6A23C;
        font-weight: 500;
        line-height: 1.6;
        background: var(--bg-secondary);
        padding: 8px;
        border-radius: 4px;
        max-height: 120px;
        overflow-y: auto;
        white-space: pre-wrap;
        word-break: break-word;
      }
    }

    .benchmark-content {
      .content-label {
        font-size: 12px;
        color: var(--text-placeholder);
        margin-bottom: 4px;
        display: block;
      }

      .content-value {
        font-size: 12px;
        color: var(--text-secondary);
        line-height: 1.6;
        background: var(--bg-secondary);
        padding: 8px;
        border-radius: 4px;
        max-height: 120px;
        overflow-y: auto;
        white-space: pre-wrap;
        word-break: break-word;
      }
    }
  }

  .template-output-settings {
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px dashed #dcdfe6;
    display: flex;
    gap: 16px;
    flex-wrap: wrap;

    .output-setting-item {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;

      .setting-label {
        color: var(--text-muted);
      }

      .setting-value {
        color: var(--text-primary);
        font-weight: 500;
      }
    }
  }
}

.model-id-text {
  font-size: 12px;
  color: var(--text-secondary);
  font-family: var(--font-family-mono);
}

// 通用
.text-muted {
  color: var(--text-placeholder);
  font-size: 13px;
}

.error-text {
  color: #F56C6C;
  font-size: 12px;
}

// 输入内容 Tab
.input-section {
  .input-block {
    padding: 16px;
    background: var(--bg-tertiary);
    border-radius: 8px;
    border: 1px solid var(--border-color);

    .block-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 12px;
      padding-left: 10px;
      border-left: 3px solid var(--color-primary);
    }

    .input-sub-label {
      font-size: 12px;
      color: var(--text-placeholder);
      margin-bottom: 8px;
      margin-top: 8px;
    }

    .image-row {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;

      .input-image-thumb {
        width: 80px;
        height: 80px;
        border-radius: 6px;
        background: var(--bg-secondary);
        flex-shrink: 0;
      }

      .image-role-tag {
        align-self: center;
        font-size: 11px;
      }
    }

    // V5.0: 双图组合模式指示器
    .pair-mode-indicator {
      border: 1px solid #e1f3d8;
      border-radius: 8px;
      background: #f0f9eb;

      .pair-mode-title {
        font-weight: 600;
        font-size: 14px;
        color: #67c23a;
      }

      .pair-mode-detail {
        margin-top: 6px;
        font-size: 13px;
        color: var(--text-secondary);
        line-height: 1.6;
      }

      .pair-combinations {
        margin-top: 10px;
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }

      .pair-combo-item {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        background: var(--bg-secondary);
        padding: 3px 8px;
        border-radius: 4px;
        border: 1px solid #e1f3d8;

        .combo-label {
          color: var(--text-placeholder);
          font-weight: 500;
        }

        .combo-arrow {
          color: #c0c4cc;
        }
      }
    }

    .info-text {
      color: var(--text-secondary);
      line-height: 1.6;
      font-size: 13px;
      white-space: pre-wrap;
      word-break: break-word;
      margin: 0;

      &.code-text {
        font-family: var(--font-family-mono);
        font-size: 12px;
        background: #1e1e1e;
        color: #d4d4d4;
        padding: 8px;
        border-radius: 4px;
        max-height: 150px;
        overflow-y: auto;
      }
    }
  }
}

// 输出内容 Tab
.output-section {
  .output-block {
    .block-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 12px;
      padding-left: 10px;
      border-left: 3px solid #67C23A;
    }
  }

  .prompt-box {
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 12px 16px;
    font-family: var(--font-family-mono);
    font-size: 12px;
    line-height: 1.6;
    color: var(--text-primary);
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 400px;
    overflow-y: auto;
  }

  .aigc-prompt-box {
    background: #fff8e6;
    border-color: #faecd8;
    max-height: 500px;
  }

  .user-text-prompt-box {
    background: #f0f9eb;
    border-color: #e1f3d8;
    max-height: 500px;
  }
}

// 提示词调试模式样式
.block-title-with-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.debug-mode-container {
  padding: 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8f4fd 100%);
  border-radius: 8px;
  border: 2px solid var(--color-primary);
}

.debug-prompt-section {
  margin-bottom: 16px;
}

.debug-section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.debug-output-card {
  margin-top: 16px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: 6px;
  border: 1px solid #dcdfe6;
}

.debug-output-content {
  .output-preview-item {
    margin-bottom: 12px;
  }

  .output-label {
    display: block;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-placeholder);
    margin-bottom: 4px;
  }

  .output-preview-text {
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    padding: 12px;
    font-family: var(--font-family-mono);
    font-size: 12px;
    line-height: 1.6;
    color: var(--text-secondary);
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 300px;
    overflow-y: auto;
    margin: 0;
  }
}

.debug-tip {
  margin-top: 12px;
}

// 输出话题
.output-topics {
  .topics-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  .topic-tag {
    font-weight: 500;
  }
}

// 执行情况概览
.execution-summary {
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: 6px;
}

// 调试工具栏
.debug-toolbar {
  display: flex;
  flex-direction: column;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e6f7ff 100%);
  border: 1px solid #bae7ff;
  border-radius: 8px;
  margin-bottom: 24px;

  .toolbar-top {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
  }

  .toolbar-bottom {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }

  .model-group {
    display: flex;
    align-items: center;
    gap: 8px;

    .group-label {
      font-size: 13px;
      color: var(--text-secondary);
      font-weight: 500;
      white-space: nowrap;
    }
  }
}

// 子块头部
.sub-block-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

// 提示词模板 TAB 样式
.prompt-template-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 12px;
  }

  :deep(.el-tabs__item) {
    font-size: 13px;
    padding: 0 16px;
    height: 36px;
    line-height: 36px;
  }
}

// 提示词模板区域
.prompt-template-section {
  .prompt-content {
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 12px;
    font-family: var(--font-family-mono);
    font-size: 12px;
    line-height: 1.6;
    color: var(--text-primary);
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 250px;
    overflow-y: auto;
    margin: 0;
  }

  .mt-sm {
    margin-top: 8px;
  }
}

.mt-md {
  margin-top: 16px;
}

// 调试输出区域
.debug-output-section {
  margin-top: 16px;
  padding: 16px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e6f7ff 100%);
  border-radius: 8px;
  border: 1px solid #bae7ff;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.loading-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #E6A23C;
  margin-right: 6px;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.text-output-preview {
  margin-top: 12px;
}

.output-item {
  margin-bottom: 16px;

  &:last-child {
    margin-bottom: 0;
  }
}

.output-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-placeholder);
  margin-bottom: 6px;
}

.output-value {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;

  &.title {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
  }

  &.content {
    font-size: 14px;
    color: var(--text-secondary);
    max-height: 200px;
    overflow-y: auto;
  }
}

.topics-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.empty-preview {
  text-align: center;
  padding: 32px 16px;
  color: var(--text-placeholder);
}

// 输入素材图片区域
.input-materials-section {
  margin-bottom: 16px;
  padding: 12px;
  background: #fff8e6;
  border-radius: 6px;
  border: 1px solid #faecd8;
}

.material-images-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.material-image-thumb {
  width: 80px;
  height: 80px;
  border-radius: 6px;
  background: var(--bg-secondary);
  flex-shrink: 0;
  border: 2px solid transparent;
  transition: border-color 0.2s;

  &:hover {
    border-color: #E6A23C;
  }
}

// 图片输出预览
.image-output-preview {
  margin-top: 12px;
}

.output-images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.output-image-item {
  width: 100%;
  height: 120px;
  border-radius: 6px;
  background: var(--bg-tertiary);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
}

.config-detail {
  margin-left: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.config-detail-inline {
  margin-left: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.editable-field {
  display: flex;
  gap: 6px;
  align-items: center;
}

.mr-xs { margin-right: 6px; }
.mb-xs { margin-bottom: 6px; }

.template-extra-info {
  margin-top: 12px;
  padding: 10px 12px;
  background: var(--bg-tertiary);
  border-radius: 6px;
  .extra-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 6px;
  }
  .extra-content {
    font-size: 13px;
    color: var(--text-secondary);
    line-height: 1.5;
  }
  .extra-tags {
    display: flex;
    flex-wrap: wrap;
  }
}
</style>
