<template>
  <PhishingDetection />
</template>

<script setup lang="ts">
import PhishingDetection from './PhishingDetection.vue'

// ✅ 把 meta 写在组件里，不需要维护外部映射表
defineOptions({
  meta: {
    title: '钓鱼检测',
    icon: 'Warning',
    order: 3
  }
})
</script>
