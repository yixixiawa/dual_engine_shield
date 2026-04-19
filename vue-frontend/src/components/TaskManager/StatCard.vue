<template>
  <el-card class="stat-card" :class="`stat-card-${color}`" shadow="hover" body-class="stat-card-body">
    <div class="stat-content">
      <div class="stat-info">
        <div class="stat-label">{{ label }}</div>
        <div class="stat-value">{{ value }}</div>
      </div>
      <div class="stat-icon" :class="`icon-bg-${color}`">
        <el-icon :size="24">
          <component :is="iconComponent" />
        </el-icon>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import * as Icons from '@element-plus/icons-vue'

const props = defineProps<{
  label: string
  value: number | string
  color: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  icon: string
}>()

const iconComponent = computed(() => {
  return (Icons as any)[props.icon] || Icons.Document
})
</script>

<style lang="scss" scoped>
.stat-card {
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 20px 40px -12px rgba(0, 0, 0, 0.15);
  }
  
  :deep(.stat-card-body) {
    padding: 1.25rem;
  }
  
  .stat-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .stat-info {
      .stat-label {
        font-size: 0.875rem;
        color: #6b7280;
        margin-bottom: 0.25rem;
      }
      
      .stat-value {
        font-size: 2rem;
        font-weight: 700;
        line-height: 1.2;
      }
    }
    
    .stat-icon {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      
      &.icon-bg-primary {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        color: white;
      }
      
      &.icon-bg-success {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
      }
      
      &.icon-bg-warning {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
      }
      
      &.icon-bg-danger {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
      }
      
      &.icon-bg-info {
        background: linear-gradient(135deg, #8b5cf6, #7c3aed);
        color: white;
      }
    }
  }
}

// 不同颜色的文字
.stat-card-primary .stat-value { color: #3b82f6; }
.stat-card-success .stat-value { color: #10b981; }
.stat-card-warning .stat-value { color: #f59e0b; }
.stat-card-danger .stat-value { color: #ef4444; }
.stat-card-info .stat-value { color: #8b5cf6; }
</style>