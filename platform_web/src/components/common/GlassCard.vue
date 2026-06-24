<template>
  <div :class="['glass-card', { 'glass-card--hoverable': hoverable }]">
    <div class="card-content">
      <slot></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  hoverable?: boolean
  showHighlight?: boolean
}

withDefaults(defineProps<Props>(), {
  hoverable: false,
  showHighlight: false
})
</script>

<style lang="scss" scoped>
@import '@/assets/styles/mixins.scss';

.glass-card {
  @include glass-card;
  padding: $spacing-xl;

  &--hoverable {
    @include card-hover;
    cursor: pointer;
  }

  .card-content {
    position: relative;
  }

  @include mobile {
    padding: $spacing-lg;
  }
}
</style>