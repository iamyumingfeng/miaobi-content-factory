<template>
  <div class="template-media-config-tab">
    <el-alert
      title="此处配置为模板的默认值，创建生成任务时可覆盖"
      type="info"
      :closable="false"
      class="mb-md"
    />

    <!-- 图片配置 -->
    <div class="config-section" v-if="['image_text', 'video_text'].includes(contentType)">
      <h4 class="section-title">
        <el-icon><Picture /></el-icon>
        图片生成配置
      </h4>
      <el-form label-width="140px">
        <!-- 快速预设 -->
        <el-form-item label="平台预设">
          <el-radio-group v-model="imagePreset">
            <el-radio-button value="xiaohongshu">小红书</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <!-- 尺寸比例 -->
        <el-form-item label="图片尺寸">
          <el-radio-group v-model="modelValue.size">
            <el-radio label="1:1">
              <div class="ratio-preview square-1-1"></div>
              1:1
            </el-radio>
            <el-radio label="3:4">
              <div class="ratio-preview square-3-4"></div>
              3:4
            </el-radio>
            <el-radio label="4:3">
              <div class="ratio-preview square-4-3"></div>
              4:3
            </el-radio>
            <el-radio label="9:16">
              <div class="ratio-preview square-9-16"></div>
              9:16
            </el-radio>
            <el-radio label="16:9">
              <div class="ratio-preview square-16-9"></div>
              16:9
            </el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- 自定义尺寸 -->
        <el-form-item label="自定义尺寸" v-if="modelValue.size === 'custom'">
          <el-input-number v-model="modelValue.width" :min="256" :max="4096" />
          <span style="margin: 0 8px;">×</span>
          <el-input-number v-model="modelValue.height" :min="256" :max="4096" />
          <span style="margin-left: 8px; color: #909399;">像素</span>
        </el-form-item>

        <!-- 图片质量 -->
        <el-form-item label="图片质量">
          <el-radio-group v-model="modelValue.quality">
            <el-radio label="low">低质量</el-radio>
            <el-radio label="medium">中等</el-radio>
            <el-radio label="high">高质量</el-radio>
            <el-radio label="ultra">超高清</el-radio>
          </el-radio-group>
          <div class="quality-hint" style="margin-top: 8px; color: #909399; font-size: 12px;">
            <span v-if="modelValue.quality === 'low'">约 100-300KB，适合预览测试</span>
            <span v-else-if="modelValue.quality === 'medium'">约 300-800KB，日常使用推荐</span>
            <span v-else-if="modelValue.quality === 'high'">约 800KB-2MB，正式发布推荐</span>
            <span v-else-if="modelValue.quality === 'ultra'">约 2-5MB，专业用途</span>
          </div>
        </el-form-item>

        <!-- 图片风格 -->
        <el-form-item label="图片风格">
          <el-select v-model="modelValue.style" placeholder="选择图片风格（可选）" clearable style="width: 300px;">
            <el-option label="写实风格" value="realistic" />
            <el-option label="卡通风格" value="cartoon" />
            <el-option label="油画风格" value="oil_painting" />
            <el-option label="水彩风格" value="watercolor" />
            <el-option label="二次元风格" value="anime" />
            <el-option label="3D渲染" value="3d_render" />
            <el-option label="摄影风格" value="photography" />
            <el-option label="手绘风格" value="hand_drawn" />
          </el-select>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 模板媒体配置组件 (TemplateMediaConfigTab.vue)
 *
 * 提供图片和视频生成的配置功能，包括：
 * - 平台预设快速配置（小红书、抖音、公众号等）
 * - 图片尺寸比例选择（带视觉预览）
 * - 图片质量、风格配置
 * - 视频宽高比、分辨率、帧率、时长配置
 *
 * @Props
 * - contentType: 内容类型 ('text' | 'image_text' | 'video_text')
 * - modelValue: 图片配置对象
 * - modelValueVideo: 视频配置对象（可选）
 *
 * @Emits
 * - update:modelValue: 图片配置更新时触发
 * - update:modelValueVideo: 视频配置更新时触发
 *
 * @Example
 * ```vue
 * <TemplateMediaConfigTab
 *   :content-type="templateForm.contentType"
 *   v-model="templateForm.default_image_config"
 *   v-model:model-value-video="templateForm.default_video_config"
 * />
 * ```
 */

import { ref, watch } from 'vue'
import { Picture } from '@element-plus/icons-vue'

export interface ImageConfig {
  size?: '1:1' | '3:4' | '4:3' | '9:16' | '16:9' | 'custom'
  width?: number
  height?: number
  quality?: 'low' | 'medium' | 'high' | 'ultra'
  style?: string
}

export interface VideoConfig {
  aspect_ratio?: '9:16' | '16:9' | '1:1'
  duration?: number
  resolution?: '720p' | '1080p' | '4k'
  fps?: number
  style?: string
}

interface Props {
  contentType: 'text' | 'image_text' | 'video_text'
  modelValue: ImageConfig
  modelValueVideo?: VideoConfig
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue', 'update:modelValueVideo'])

// 平台预设配置
const platformPresets = {
  xiaohongshu: {
    image: { size: '3:4', quality: 'high', width: 1080, height: 1440 }
  },
  douyin: {
    image: { size: '9:16', quality: 'high', width: 1080, height: 1920 },
    video: { aspect_ratio: '9:16', resolution: '1080p', fps: 30, duration: 15 }
  },
  gongzhonghao: {
    image: { size: '16:9', quality: 'medium', width: 1280, height: 720 }
  },
  shipinhao: {
    video: { aspect_ratio: '9:16', resolution: '1080p', fps: 30, duration: 30 }
  },
  bilibili: {
    video: { aspect_ratio: '16:9', resolution: '1080p', fps: 30, duration: 60 }
  }
}

const imagePreset = ref('custom')
const videoPreset = ref('custom')

// 监听图片预设变化
watch(imagePreset, (preset) => {
  if (preset !== 'custom') {
    const presetConfig = platformPresets[preset as keyof typeof platformPresets] as { image?: ImageConfig }
    if (presetConfig?.image) {
      emit('update:modelValue', { ...props.modelValue, ...presetConfig.image })
    }
  }
})

// 监听视频预设变化
watch(videoPreset, (preset) => {
  if (preset !== 'custom' && props.modelValueVideo) {
    const presetConfig = platformPresets[preset as keyof typeof platformPresets] as { video?: VideoConfig }
    if (presetConfig?.video) {
      emit('update:modelValueVideo', { ...props.modelValueVideo, ...presetConfig.video })
    }
  }
})
</script>

<style lang="scss" scoped>
.template-media-config-tab {
  padding: 8px 0;
}

.config-section {
  .section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 500;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid #ebeef5;
  }
}

.ratio-preview {
  display: inline-block;
  vertical-align: middle;
  margin-right: 6px;
  border: 1px solid #dcdfe6;
  border-radius: 2px;
  background: #f5f7fa;
}

.square-1-1 { width: 20px; height: 20px; }
.square-3-4 { width: 15px; height: 20px; }
.square-4-3 { width: 20px; height: 15px; }
.square-9-16 { width: 11px; height: 20px; }
.square-16-9 { width: 20px; height: 11px; }

.mb-md {
  margin-bottom: 16px;
}

.mt-lg {
  margin-top: 24px;
}
</style>
