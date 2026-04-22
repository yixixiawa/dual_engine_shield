<template>
  <CombinedDetection />
</template>

<script setup lang="ts">
import CombinedDetection from './CombinedDetection.vue'

// ✅ 把 meta 写在组件里，不需要维护外部映射表
defineOptions({
  meta: {
    title: '综合检测',
    icon: 'Monitor',
    order: 1
  }
})
</script>
