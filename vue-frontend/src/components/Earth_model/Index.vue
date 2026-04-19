<template>
  <Earth_model />
</template>

<script setup lang="ts">
import Earth_model from './Earth_model.vue'

// ✅ 把 meta 写在组件里，不需要维护外部映射表
defineOptions({
  meta: {
    title: '地球模型',
    icon: 'Monitor',
    order: 2
  }
})
</script>
