<template>
  <div :class="['feature-card', { 'feature-card--active': active }]">
    <!-- 图标 -->
    <div class="feature-icon">
      <component :is="icon" v-if="icon" />
      <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
      </svg>
    </div>

    <!-- 文字内容 -->
    <div class="feature-text">
      <div class="feature-title">{{ title }}</div>
      <div v-if="description" class="feature-description">{{ description }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  icon?: any
  title: string
  description?: string
  active?: boolean
}

withDefaults(defineProps<Props>(), {
  active: false
})
</script>

<style lang="scss" scoped>
@import '@/assets/styles/mixins.scss';

.feature-card {
  @include card-base;
  @include flex-vertical-center;
  gap: $spacing-lg;
  padding: $spacing-lg;
  cursor: pointer;

  // 悬停效果
  &:hover {
    border-color: var(--color-border-hover);
    box-shadow: var(--shadow-sm);
  }

  &--active {
    background: var(--color-primary-bg);
    border-color: var(--color-primary);
  }

  // 图标容器
  .feature-icon {
    flex-shrink: 0;
    @include flex-center;
    width: 48px;
    height: 48px;
    background: var(--color-primary-bg);
    border: 1px solid var(--color-border-default);
    border-radius: $radius-md;
    color: var(--color-primary);

    svg {
      width: 24px;
      height: 24px;
    }
  }

  // 文字内容
  .feature-text {
    flex: 1;
  }

  // 标题
  .feature-title {
    font-size: $font-size-md;
    font-weight: $font-weight-semibold;
    color: var(--color-text-primary);
    margin-bottom: $spacing-xs;
    letter-spacing: $letter-spacing-tight;
  }

  // 描述
  .feature-description {
    font-size: $font-size-sm;
    font-weight: $font-weight-normal;
    color: var(--color-text-muted);
    letter-spacing: $letter-spacing-tight;
  }
}
</style>