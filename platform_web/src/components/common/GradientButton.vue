<template>
  <button
    :class="['gradient-button', `gradient-button--${type}`, `gradient-button--${size}`]"
    :disabled="disabled || loading"
    @click="handleClick"
  >
    <!-- 加载状态 -->
    <svg v-if="loading" class="loading-icon" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" opacity="0.3"/>
      <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" stroke-width="3" stroke-linecap="round">
        <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
      </path>
    </svg>

    <!-- 图标 -->
    <component v-if="icon && !loading" :is="icon" class="button-icon" />

    <!-- 文字 -->
    <span class="button-text">{{ loading ? loadingText : text }}</span>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  type?: 'primary' | 'secondary' | 'ghost'
  size?: 'small' | 'medium' | 'large'
  text?: string
  loadingText?: string
  icon?: any
  loading?: boolean
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'primary',
  size: 'medium',
  text: '按钮',
  loadingText: '加载中...',
  loading: false,
  disabled: false
})

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const handleClick = (event: MouseEvent) => {
  if (!props.disabled && !props.loading) {
    emit('click', event)
  }
}
</script>

<style lang="scss" scoped>
@import '@/assets/styles/mixins.scss';

.gradient-button {
  @include button-base;
  border-radius: $radius-lg;
  font-family: $font-family-body;

  // 尺寸
  &--small {
    height: 40px;
    padding: 0 $spacing-lg;
    font-size: $font-size-sm;
  }

  &--medium {
    height: 48px;
    padding: 0 $spacing-xl;
    font-size: $font-size-md;
  }

  &--large {
    height: 56px;
    padding: 0 $spacing-2xl;
    font-size: $font-size-md;
  }

  // 类型
  &--primary {
    @include button-primary;
  }

  &--secondary {
    @include button-secondary;
  }

  &--ghost {
    background: transparent;
    color: var(--color-primary);

    &:hover {
      background: var(--color-primary-bg);
    }
  }

  // 禁用状态
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none !important;
  }

  // 加载图标
  .loading-icon {
    width: 20px;
    height: 20px;
    margin-right: $spacing-sm;
  }

  // 按钮图标
  .button-icon {
    width: 20px;
    height: 20px;
    margin-right: $spacing-sm;
  }

  // 按钮文字
  .button-text {
    display: inline-flex;
  }
}
</style>