<template>
  <el-card class="phishing-config-card" shadow="hover">
    <template #header>
      <div class="card-header">
        <span class="title">
          <el-icon><Setting /></el-icon>
          钓鱼检测配置
        </span>
        <el-button @click="loadConfig" :loading="loading" text type="primary">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </template>

    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="4" animated />
    </div>

    <div v-else-if="config" class="config-content">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <div class="config-item">
            <div class="label">检测模式</div>
            <div class="value">{{ config.mode }}</div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="config-item">
            <div class="label">决策阈值</div>
            <div class="value">{{ (config.threshold * 100).toFixed(0) }}%</div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="config-item">
            <div class="label">融合策略</div>
            <div class="value">{{ config.ensemble_strategy }}</div>
          </div>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <div class="config-item">
            <div class="label">可用模型数</div>
            <div class="value">{{ config.available_models?.length || 0 }}</div>
          </div>
        </el-col>
      </el-row>

      <el-divider v-if="config.weights" />

      <div v-if="config.weights" class="weights-section">
        <div class="section-title">模型权重分配</div>
        <el-row :gutter="20" class="weights-row">
          <el-col v-for="(weight, model) in config.weights" :key="model" :xs="24" :sm="12" :md="8">
            <div class="weight-item">
              <div class="model-name">{{ formatModelName(model) }}</div>
              <el-progress :percentage="Math.round(weight * 100)" :color="getWeightColor(weight)" />
              <div class="weight-value">{{ (weight * 100).toFixed(1) }}%</div>
            </div>
          </el-col>
        </el-row>
      </div>

      <div v-if="config.available_models && config.available_models.length" class="models-section">
        <el-divider />
        <div class="section-title">可用模型</div>
        <el-tag
          v-for="model in config.available_models"
          :key="model"
          type="info"
          size="large"
          class="model-tag"
        >
          {{ model }}
        </el-tag>
      </div>
    </div>

    <div v-else class="error-container">
      <el-empty description="无法加载配置信息" />
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Setting, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { phishingAPI } from '@/api'
import type { PhishingConfigResponse } from '@/api/modules/phishing'

const config = ref<PhishingConfigResponse | null>(null)
const loading = ref(false)

const loadConfig = async () => {
  loading.value = true
  try {
    config.value = await phishingAPI.getConfig()
  } catch (error: any) {
    ElMessage.error(error.message || '加载配置失败')
  } finally {
    loading.value = false
  }
}

const formatModelName = (model: string) => {
  const names: Record<string, string> = {
    original: 'GTE 原始模型',
    chiphish: 'GTE ChiPhish模型'
  }
  return names[model] || model
}

const getWeightColor = (weight: number) => {
  if (weight >= 0.6) return '#67C23A'
  if (weight >= 0.3) return '#E6A23C'
  return '#F56C6C'
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped lang="scss">
.phishing-config-card {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
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

  .config-content {
    .config-item {
      text-align: center;
      padding: 16px;
      background: rgba(255, 255, 255, 0.8);
      border-radius: 8px;
      backdrop-filter: blur(10px);

      .label {
        font-size: 12px;
        color: #909399;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
      }

      .value {
        font-size: 18px;
        font-weight: 600;
        color: #303133;
      }
    }
  }

  .weights-section {
    .section-title {
      font-size: 14px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .weights-row {
      .weight-item {
        padding: 12px;
        background: rgba(255, 255, 255, 0.6);
        border-radius: 8px;

        .model-name {
          font-size: 12px;
          font-weight: 600;
          color: #606266;
          margin-bottom: 8px;
        }

        .weight-value {
          font-size: 12px;
          color: #909399;
          margin-top: 8px;
          text-align: center;
        }
      }
    }
  }

  .models-section {
    .section-title {
      font-size: 14px;
      font-weight: 600;
      color: #303133;
      margin-bottom: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .model-tag {
      margin-right: 8px;
      margin-bottom: 8px;
    }
  }
}
</style>
