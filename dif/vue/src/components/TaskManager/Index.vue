<template>
  <TaskManager />
</template>

<script setup lang="ts">
import TaskManager from './TaskManager.vue'

// ✅ 把 meta 写在组件里，不需要维护外部映射表
defineOptions({
  meta: {
    title: '历史任务',
    icon: 'Document',
    badgeType: 'warning',
    order: 5
  }
})
</script>
