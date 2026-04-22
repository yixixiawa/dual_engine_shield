<template>
  <div class="code-detection-container">
    <el-card shadow="hover" class="detection-card">
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon><DocumentCopy /></el-icon>
            代码漏洞检测
          </span>
          <el-radio-group v-model="detectionMode">
            <el-radio label="single">单个</el-radio>
            <el-radio label="batch">批量</el-radio>
          </el-radio-group>
        </div>
      </template>

      <!-- 单个代码检测 -->
      <div v-if="detectionMode === 'single'" class="single-detection">
        <el-form :model="singleForm" class="detection-form">
          <el-form-item label="编程语言">
            <el-select
              v-model="singleForm.language"
              placeholder="选择编程语言"
              clearable
            >
              <el-option
                v-for="lang in supportedLanguages"
                :key="lang"
                :label="lang"
                :value="lang"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="代码片段">
            <el-input
              v-model="singleForm.code"
              type="textarea"
              rows="6"
              placeholder="输入要检测的代码"
            />
          </el-form-item>

          <el-form-item label="CWE IDs (可选)">
            <el-input
              v-model="cweInput"
              placeholder="多个用逗号分隔，如: 120,94"
            />
          </el-form-item>

          <el-button
            type="primary"
            @click="detectSingleCode"
            :loading="loading"
            :disabled="!singleForm.code.trim() || !singleForm.language"
          >
            <el-icon><Search /></el-icon>
            检测
          </el-button>
        </el-form>
      </div>

      <!-- 批量代码检测 -->
      <div v-if="detectionMode === 'batch'" class="batch-detection">
        <el-form :model="batchForm" class="detection-form">
          <el-form-item>
            <template #label>
              <span>
                代码片段列表
                <el-text type="info" size="small">(JSON格式，每个对象包含code和language)</el-text>
              </span>
            </template>
            <el-input
              v-model="batchForm.jsonInput"
              type="textarea"
              rows="8"
              placeholder='[{"code":"code1","language":"python"},{"code":"code2","language":"c"}]'
            />
          </el-form-item>

          <el-button
            type="primary"
            @click="detectBatchCode"
            :loading="loading"
            :disabled="!batchForm.jsonInput.trim()"
          >
            <el-icon><Search /></el-icon>
            批量检测
          </el-button>
        </el-form>
      </div>
    </el-card>

    <!-- 单个检测结果 -->
    <div v-if="detectionMode === 'single' && singleResult" class="results-container">
      <el-card shadow="hover">
        <template #header>
          <div class="card-header">
            <span>检测结果</span>
            <el-tag
              :type="singleResult.is_vulnerable ? 'danger' : 'success'"
              size="large"
            >
              {{ singleResult.is_vulnerable ? '存在漏洞' : '未检测到漏洞' }}
            </el-tag>
          </div>
        </template>

        <el-row :gutter="20">
          <el-col :xs="24" :sm="12" :md="6">
            <div class="result-item">
              <div class="label">置信度</div>
              <div class="value">{{ (singleResult.confidence * 100).toFixed(2) }}%</div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :md="6">
            <div class="result-item">
              <div class="label">推断时间</div>
              <div class="value">{{ singleResult.inference_time.toFixed(2) }}ms</div>
            </div>
          </el-col>
          <el-col v-if="singleResult.is_vulnerable" :xs="24" :sm="12" :md="6">
            <div class="result-item">
              <div class="label">严重级别</div>
              <el-tag :type="getSeverityType(singleResult.severity)">
                {{ singleResult.severity }}
              </el-tag>
            </div>
          </el-col>
          <el-col v-if="singleResult.cwe_id" :xs="24" :sm="12" :md="6">
            <div class="result-item">
              <div class="label">CWE ID</div>
              <div class="value">{{ singleResult.cwe_id }}</div>
            </div>
          </el-col>
        </el-row>

        <el-divider v-if="singleResult.is_vulnerable" />

        <div v-if="singleResult.is_vulnerable" class="vulnerability-details">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="CWE 名称" v-if="singleResult.cwe_name">
              {{ singleResult.cwe_name }}
            </el-descriptions-item>
            <el-descriptions-item label="漏洞说明">
              {{ singleResult.explanation }}
            </el-descriptions-item>
            <el-descriptions-item label="修复建议">
              {{ singleResult.fix_suggestion }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-card>
    </div>

    <!-- 批量检测结果 -->
    <div v-if="detectionMode === 'batch' && batchResult" class="results-container">
      <el-card shadow="hover">
        <template #header>
          <div class="card-header">
            <span>批量检测结果</span>
            <el-tag>共 {{ batchResult.total }} 条</el-tag>
          </div>
        </template>

        <el-table :data="batchResult.results" stripe>
          <el-table-column label="语言" prop="language" width="100" />
          <el-table-column label="代码预览" prop="code" width="200">
            <template #default="{ row }">
              <el-text truncated>{{ row.code }}</el-text>
            </template>
          </el-table-column>
          <el-table-column label="是否存在漏洞" width="120">
            <template #default="{ row }">
              <el-tag :type="row.is_vulnerable ? 'danger' : 'success'">
                {{ row.is_vulnerable ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="严重级别" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.severity" :type="getSeverityType(row.severity)">
                {{ row.severity }}
              </el-tag>
              <el-tag v-else type="info">-</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="CWE" prop="cwe_id" width="100" />
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }">
              <el-button @click="showBatchDetail(row)" link type="primary" size="small">
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="漏洞详情" width="600px">
      <div v-if="selectedDetail" class="detail-content">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="是否存在漏洞">
            <el-tag :type="selectedDetail.is_vulnerable ? 'danger' : 'success'">
              {{ selectedDetail.is_vulnerable ? '是' : '否' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="语言">{{ selectedDetail.language }}</el-descriptions-item>
          <el-descriptions-item label="代码">
            <el-text truncated>{{ selectedDetail.code }}</el-text>
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedDetail.is_vulnerable" label="CWE">
            {{ selectedDetail.cwe_id }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedDetail.is_vulnerable" label="严重级别">
            <el-tag :type="getSeverityType(selectedDetail.severity)">
              {{ selectedDetail.severity }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { DocumentCopy, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { vulnerabilityAPI } from '@/api'
import type { CodeDetectResponse, BatchCodeDetectResponse } from '@/api/modules/vulnerability'

type DetectionMode = 'single' | 'batch'

const supportedLanguages = ['python', 'c', 'cpp', 'java', 'javascript', 'csharp']

const detectionMode = ref<DetectionMode>('single')
const loading = ref(false)

const singleForm = ref({
  language: '',
  code: ''
})

const batchForm = ref({
  jsonInput: ''
})

const cweInput = ref('')

const singleResult = ref<CodeDetectResponse | null>(null)
const batchResult = ref<BatchCodeDetectResponse | null>(null)

const detailDialogVisible = ref(false)
const selectedDetail = ref<any>(null)

const getSeverityType = (severity: string) => {
  const typeMap: Record<string, string> = {
    critical: 'danger',
    high: 'warning',
    medium: 'warning',
    low: 'info'
  }
  return typeMap[severity.toLowerCase()] || 'info'
}

const detectSingleCode = async () => {
  if (!singleForm.value.code.trim() || !singleForm.value.language) {
    ElMessage.warning('请输入代码和选择语言')
    return
  }

  loading.value = true
  try {
    const cweIds = cweInput.value
      .split(',')
      .map(id => parseInt(id.trim()))
      .filter(id => !isNaN(id))

    singleResult.value = await vulnerabilityAPI.detectCode(
      singleForm.value.code,
      singleForm.value.language,
      cweIds
    )
    ElMessage.success('检测完成')
  } catch (error: any) {
    ElMessage.error(error.message || '检测失败')
  } finally {
    loading.value = false
  }
}

const detectBatchCode = async () => {
  loading.value = true
  try {
    const snippets = JSON.parse(batchForm.value.jsonInput)
    if (!Array.isArray(snippets)) {
      throw new Error('JSON必须是数组格式')
    }

    batchResult.value = await vulnerabilityAPI.batchDetectCode(snippets)
    ElMessage.success(`检测完成，共 ${batchResult.value.total} 条`)
  } catch (error: any) {
    ElMessage.error(error.message || 'JSON格式错误或检测失败')
  } finally {
    loading.value = false
  }
}

const showBatchDetail = (row: any) => {
  selectedDetail.value = row
  detailDialogVisible.value = true
}
</script>

<style scoped lang="scss">
.code-detection-container {
  .detection-card {
    margin-bottom: 20px;

    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;

      .title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
      }
    }

    .detection-form {
      .el-form-item {
        margin-bottom: 16px;
      }
    }
  }

  .results-container {
    margin-top: 20px;

    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }

    .result-item {
      padding: 12px;
      background: #f5f7fa;
      border-radius: 6px;
      text-align: center;

      .label {
        font-size: 12px;
        color: #909399;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
      }

      .value {
        font-size: 14px;
        font-weight: 600;
        color: #303133;
      }
    }

    .vulnerability-details {
      margin-top: 12px;
    }
  }

  .detail-content {
    padding: 12px 0;
  }
}
</style>
