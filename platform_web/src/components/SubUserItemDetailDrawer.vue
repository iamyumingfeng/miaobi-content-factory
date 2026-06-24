<template>
  <el-drawer
    :model-value="visible"
    title="内容详情"
    size="50%"
    :close-on-click-modal="false"
    @update:model-value="$emit('update:visible', $event)"
  >
    <template v-if="item">
      <div class="sub-user-item-detail">
        <!-- 基本信息 -->
        <div class="detail-section mb-lg">
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="任务名称">
              {{ item.taskName || item.task_name || '任务 #' + item.task_id }}
            </el-descriptions-item>
            <el-descriptions-item label="内容ID">
              #{{ item.id }}
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusType(item)" size="small">
                {{ getStatusLabel(item) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatDateTime(item.created_at) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 结构化内容区域 -->
        <div class="structured-content">
          <!-- 标题卡片 -->
          <div class="content-card title-card" v-if="item.generated_title">
            <div class="card-header">
              <span class="card-icon">📌</span>
              <span class="card-label">标题</span>
              <el-button type="primary" link size="small" @click="copyTitle">复制标题</el-button>
            </div>
            <div class="card-body title-body">
              {{ item.generated_title }}
            </div>
          </div>

          <!-- 正文卡片 -->
          <div class="content-card body-card" v-if="item.generated_text">
            <div class="card-header">
              <span class="card-icon">📄</span>
              <span class="card-label">正文内容</span>
              <el-button type="primary" link size="small" @click="copyText(item.generated_text)">复制全文</el-button>
            </div>
            <div class="card-body text-body">
              <div class="parsed-text">
                <template v-for="(paragraph, idx) in item.generated_text.split('\n')" :key="idx">
                  <span v-if="paragraph" class="text-paragraph">{{ paragraph }}</span>
                  <br v-else>
                </template>
              </div>
            </div>
            <div v-if="item.generated_text.length > 500" class="card-footer">
              <el-button type="primary" link @click="textCollapsed = !textCollapsed">
                {{ textCollapsed ? '展开全部' : '收起' }}
              </el-button>
            </div>
          </div>

          <!-- 话题卡片 -->
          <div class="content-card topics-card" v-if="parseTopics((item as any).output_topics).length > 0">
            <div class="card-header">
              <span class="card-icon">🏷️</span>
              <span class="card-label">输出话题</span>
              <el-button type="primary" link size="small" @click="copyTopics">复制话题</el-button>
            </div>
            <div class="card-body topics-body">
              <el-tag
                v-for="(tag, idx) in parseTopics((item as any).output_topics)"
                :key="idx"
                type="warning"
                size="large"
                class="topic-tag"
              >#{{ tag }}</el-tag>
            </div>
          </div>
        </div>

        <!-- 生成图片 -->
        <div class="image-gallery mt-lg" v-if="parseImageUrls(item.generated_images || item.generated_image_urls_json).length > 0">
          <h4 class="section-label">生成图片 ({{ parseImageUrls(item.generated_images || item.generated_image_urls_json).length }})</h4>
          <div class="gallery-grid">
            <el-image
              v-for="(img, idx) in parseImageUrls(item.generated_thumbnails || item.generated_image_thumbnails_json || item.generated_images || item.generated_image_urls_json)"
              :key="idx"
              :src="img"
              fit="cover"
              class="gallery-item"
              preview-teleported
              :preview-src-list="parseImageUrls(item.generated_images || item.generated_image_urls_json)"
              :initial-index="idx"
            />
          </div>
        </div>

        <!-- 生成视频 -->
        <div class="video-section mt-lg" v-if="item.generated_video_url || (item.generated_videos && item.generated_videos.length > 0)">
          <h4 class="section-label">生成视频</h4>
          <div v-if="item.generated_video_url" class="video-player-container">
            <video :src="item.generated_video_url" controls class="video-player" />
          </div>
          <div v-else-if="item.generated_videos" class="video-list">
            <div v-for="(video, idx) in item.generated_videos" :key="idx" class="video-player-container">
              <video :src="video" controls class="video-player" />
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="actions-bar mt-lg">
          <el-button type="primary" @click="copyFullTextContent">复制文案</el-button>
          <el-button
            v-if="(item as any).distribution_status === 'pending_publish' || (item as any).distribution_status === 'distributed'"
            type="success"
            :loading="publishing"
            @click="handlePublish"
          >
            完成发布
          </el-button>
        </div>
      </div>
    </template>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiClient } from '@/api/types'
import { copyToClipboard } from '@/utils/clipboard'

const props = defineProps<{
  visible: boolean
  item: any
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'published': []
}>()

const textCollapsed = ref(true)
const publishing = ref(false)

// 格式化日期时间
const formatDateTime = (dateStr: string | undefined) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 状态类型
const getStatusType = (item: any) => {
  if (item.distribution_status === 'published') return 'success'
  if (item.distribution_status === 'distributed' || item.distribution_status === 'pending_publish') return 'warning'
  if (item.status === 'completed') return 'warning'
  if (item.status === 'failed') return 'danger'
  if (item.status === 'generating') return 'primary'
  if (item.status === 'queued') return 'info'
  return 'info'
}

// 状态标签
const getStatusLabel = (item: any) => {
  if (item.distribution_status === 'published') return '已发布'
  if (item.distribution_status === 'distributed' || item.distribution_status === 'pending_publish') return '待发布'
  if (item.status === 'completed') return '待发布'
  if (item.status === 'failed') return '失败'
  if (item.status === 'generating') return '生成中'
  if (item.status === 'queued') return '排队中'
  return item.status
}

// 解析话题
const parseTopics = (topics: any): string[] => {
  if (!topics) return []
  if (Array.isArray(topics)) return topics
  if (typeof topics === 'string') {
    try {
      const parsed = JSON.parse(topics)
      return Array.isArray(parsed) ? parsed : []
    } catch {
      return topics.split(',').map(t => t.trim()).filter(Boolean)
    }
  }
  return []
}

// 解析图片URL
const parseImageUrls = (urls: any): string[] => {
  if (!urls) return []
  if (Array.isArray(urls)) return urls
  if (typeof urls === 'string') {
    try {
      const parsed = JSON.parse(urls)
      return Array.isArray(parsed) ? parsed : []
    } catch {
      return urls.split(',').map(u => u.trim()).filter(Boolean)
    }
  }
  return []
}

// 复制标题
const copyTitle = async () => {
  if (!props.item?.generated_title) {
    ElMessage.warning('没有标题可复制')
    return
  }
  const success = await copyToClipboard(props.item.generated_title)
  if (success) {
    ElMessage.success('标题已复制到剪贴板')
  } else {
    ElMessage.error('复制失败，请手动复制')
  }
}

// 复制文本
const copyText = async (text: string) => {
  const success = await copyToClipboard(text)
  if (success) {
    ElMessage.success('已复制到剪贴板')
  } else {
    ElMessage.error('复制失败，请手动复制')
  }
}

// 复制话题
const copyTopics = async () => {
  if (!props.item) return
  const topics = parseTopics((props.item as any).output_topics)
  if (topics.length === 0) {
    ElMessage.warning('没有话题可复制')
    return
  }
  const topicsText = topics.map(t => `#${t}`).join(' ')
  const success = await copyToClipboard(topicsText)
  if (success) {
    ElMessage.success('话题已复制到剪贴板')
  } else {
    ElMessage.error('复制失败，请手动复制')
  }
}

// 复制全部文案
const copyFullTextContent = async () => {
  if (!props.item) return
  const parts: string[] = []
  if (props.item.generated_title) {
    parts.push(props.item.generated_title)
  }
  if (props.item.generated_text) {
    parts.push('')
    parts.push(props.item.generated_text)
  }
  const topics = parseTopics((props.item as any).output_topics)
  if (topics.length > 0) {
    parts.push('')
    parts.push(topics.map(t => `#${t}`).join(' '))
  }
  const textToCopy = parts.join('\n')
  if (!textToCopy) {
    ElMessage.warning('没有可复制的内容')
    return
  }
  const success = await copyToClipboard(textToCopy)
  if (success) {
    ElMessage.success('全部文案已复制到剪贴板')
  } else {
    ElMessage.error('复制失败，请手动复制')
  }
}

// 发布
const handlePublish = async () => {
  if (!props.item) return
  try {
    await ElMessageBox.confirm(
      '确定要标记此内容为已发布吗？',
      '发布确认',
      {
        confirmButtonText: '确认发布',
        cancelButtonText: '再想想',
        type: 'success',
      }
    )
    publishing.value = true
    await apiClient.publishGenerationItem(props.item.id)
    ElMessage.success('发布成功')
    emit('update:visible', false)
    emit('published')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '发布失败')
    }
  } finally {
    publishing.value = false
  }
}
</script>

<style lang="scss" scoped>
.sub-user-item-detail {
  .mb-lg {
    margin-bottom: 16px;
  }

  .mt-lg {
    margin-top: 16px;
  }

  /* 结构化内容卡片 */
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

  /* 标题卡片 */
  .title-card .title-body {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
  }

  /* 正文卡片 */
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

  /* 话题卡片 */
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
    .section-label {
      font-size: 14px;
      font-weight: 500;
      color: var(--text-primary);
      margin-bottom: 8px;
    }
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

  .video-section {
    .section-label {
      font-size: 14px;
      font-weight: 500;
      color: var(--text-primary);
      margin-bottom: 8px;
    }
    .video-player-container {
      .video-player {
        width: 100%;
        max-height: 400px;
        border-radius: 8px;
      }
    }
    .video-list {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
  }

  .actions-bar {
    padding-top: 16px;
    border-top: 1px solid var(--border-color);
  }
}
</style>
