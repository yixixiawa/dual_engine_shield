<template>
  <el-card class="ip-database-info-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="title">
          <el-icon><DataAnalysis /></el-icon>
          IP数据库统计
        </span>
        <el-button @click="loadInfo" :loading="loading" text type="primary">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </template>

    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="3" animated />
    </div>

    <div v-else-if="info" class="info-content">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <el-statistic
            :value="info.total_ips"
            title="IP总数"
            :precision="0"
          >
            <template #prefix>
              <el-icon style="color: #409EFF"><DataAnalysis /></el-icon>
            </template>
          </el-statistic>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-statistic
            :value="info.active_ips"
            title="活跃IP数"
            :precision="0"
          >
            <template #prefix>
              <el-icon style="color: #67C23A"><SuccessFilled /></el-icon>
            </template>
          </el-statistic>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-statistic
            :value="info.countries_count"
            title="覆盖国家数"
            :precision="0"
          >
            <template #prefix>
              <el-icon style="color: #E6A23C"><Location /></el-icon>
            </template>
          </el-statistic>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-statistic
            :value="activePercentage"
            title="活跃率"
            suffix="%"
            :precision="2"
          >
            <template #prefix>
              <el-icon style="color: #f56c6c"><PieChart /></el-icon>
            </template>
          </el-statistic>
        </el-col>
      </el-row>

      <el-divider />

      <div class="last-updated">
        <el-icon><Clock /></el-icon>
        <span>最后更新: {{ formatTime(info.last_updated) }}</span>
      </div>

      <el-progress
        :percentage="activePercentage"
        :color="getProgressColor"
        style="margin-top: 12px"
      />
    </div>

    <div v-else class="error-container">
      <el-empty description="无法加载数据库信息" />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { DataAnalysis, Refresh, SuccessFilled, Location, PieChart, Clock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { ipinfoAPI } from '@/api'
import type { IPDatabaseInfo } from '@/api/modules/ipinfo'

const info = ref<IPDatabaseInfo | null>(null)
const loading = ref(false)

const loadInfo = async () => {
  loading.value = true
  try {
    const response = await ipinfoAPI.getDatabaseInfo()
    info.value = response.database_info
  } catch (error: any) {
    ElMessage.error(error.message || '加载数据库信息失败')
  } finally {
    loading.value = false
  }
}

const activePercentage = computed(() => {
  if (!info.value || info.value.total_ips === 0) return 0
  return (info.value.active_ips / info.value.total_ips) * 100
})

const getProgressColor = (percentage: number) => {
  if (percentage >= 85) return '#67C23A'
  if (percentage >= 70) return '#E6A23C'
  return '#F56C6C'
}

const formatTime = (dateString: string) => {
  try {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN')
  } catch {
    return dateString
  }
}

onMounted(() => {
  loadInfo()
})
</script>

<style scoped lang="scss">
.ip-database-info-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;

  :deep(.el-card__body) {
    color: white;
  }

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: white;

    .title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 16px;
      font-weight: 600;
    }
  }

  .loading-container,
  .error-container {
    min-height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .info-content {
    color: #303133;

    :deep(.el-statistic__content) {
      font-size: 24px;
      color: #303133;
    }

    :deep(.el-statistic__title) {
      font-size: 12px;
      color: #909399;
      margin-top: 8px;
    }
  }

  .last-updated {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: #606266;
    margin-top: 12px;
  }
}
</style>
