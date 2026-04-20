<template>
  <el-card class="health-check-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="title">
          <el-icon><Monitor /></el-icon>
          系统健康检查
        </span>
        <el-button @click="loadHealth" :loading="loading" text type="primary">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </template>

    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="4" animated />
    </div>

    <div v-else-if="health" class="health-content">
      <div class="status-section">
        <div class="status-header">
          <span>系统状态</span>
          <el-tag
            :type="health.status === 'healthy' ? 'success' : 'danger'"
            size="large"
          >
            <el-icon><CircleCheckFilled v-if="health.status === 'healthy'" /></el-icon>
            <el-icon><CircleCloseFilled v-else /></el-icon>
            {{ health.status === 'healthy' ? '健康' : '异常' }}
          </el-tag>
        </div>
      </div>

      <el-divider />

      <div class="services-section">
        <div class="section-title">
          <el-icon><Setting /></el-icon>
          服务状态
        </div>

        <el-row :gutter="20">
          <el-col :xs="24" :sm="12" :md="6">
            <div class="service-item">
              <div class="service-name">数据库</div>
              <el-tag :type="getServiceType(health.services.database)">
                {{ health.services.database }}
              </el-tag>
            </div>
          </el-col>

          <el-col v-if="health.services.models" :xs="24" :sm="12" :md="6">
            <div class="service-item">
              <div class="service-name">钓鱼检测模型</div>
              <el-tag
                v-if="health.services.models.phishing"
                :type="
                  health.services.models.phishing.available && health.services.models.phishing.enabled
                    ? 'success'
                    : 'info'
                "
              >
                {{
                  health.services.models.phishing.available && health.services.models.phishing.enabled
                    ? '可用'
                    : '离线'
                }}
              </el-tag>
            </div>
          </el-col>

          <el-col v-if="health.services.models" :xs="24" :sm="12" :md="6">
            <div class="service-item">
              <div class="service-name">代码检测模型</div>
              <el-tag
                v-if="health.services.models.vulnerability"
                :type="
                  health.services.models.vulnerability.available &&
                  health.services.models.vulnerability.enabled
                    ? 'success'
                    : 'info'
                "
              >
                {{
                  health.services.models.vulnerability.available &&
                  health.services.models.vulnerability.enabled
                    ? '可用'
                    : '离线'
                }}
              </el-tag>
            </div>
          </el-col>

          <el-col :xs="24" :sm="12" :md="6">
            <div class="service-item">
              <div class="service-name">最后检查</div>
              <div class="timestamp">{{ formatTime(health.timestamp) }}</div>
            </div>
          </el-col>
        </el-row>
      </div>
    </div>

    <div v-else class="error-container">
      <el-empty description="无法加载健康检查信息" />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Monitor, Refresh, CircleCheckFilled, CircleCloseFilled, Setting } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { healthAPI } from '@/api'
import type { HealthResponse } from '@/api/modules/health'

const health = ref<HealthResponse | null>(null)
const loading = ref(false)

const loadHealth = async () => {
  loading.value = true
  try {
    health.value = await healthAPI.getHealth()
  } catch (error: any) {
    ElMessage.error(error.message || '加载健康检查信息失败')
  } finally {
    loading.value = false
  }
}

const getServiceType = (status: string) => {
  const typeMap: Record<string, string> = {
    connected: 'success',
    disconnected: 'danger',
    connecting: 'warning'
  }
  return typeMap[status.toLowerCase()] || 'info'
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
  loadHealth()
})
</script>

<style scoped lang="scss">
.health-check-card {
  background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
  border-radius: 12px;

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;

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

  .health-content {
    .status-section {
      padding: 16px;
      background: rgba(255, 255, 255, 0.8);
      border-radius: 8px;

      .status-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-weight: 600;
        color: #303133;
      }
    }

    .services-section {
      .section-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        font-weight: 600;
        color: #303133;
        margin-bottom: 12px;
      }

      .service-item {
        padding: 12px;
        background: rgba(255, 255, 255, 0.6);
        border-radius: 8px;
        text-align: center;

        .service-name {
          font-size: 12px;
          color: #606266;
          margin-bottom: 8px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .timestamp {
          font-size: 12px;
          color: #606266;
          word-break: break-all;
        }
      }
    }
  }
}
</style>
