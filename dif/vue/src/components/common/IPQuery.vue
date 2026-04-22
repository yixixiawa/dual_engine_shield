<template>
  <div class="ip-query-container">
    <el-card class="query-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon><Search /></el-icon>
            IP 地理位置查询
          </span>
        </div>
      </template>

      <el-form :model="formData" @submit.prevent="handleQuery" class="query-form">
        <el-form-item label="查询模式">
          <el-radio-group v-model="queryMode">
            <el-radio label="single">单个查询</el-radio>
            <el-radio label="batch">批量查询</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="queryMode === 'single'" label="IP地址">
          <el-input
            v-model="formData.singleIp"
            placeholder="例如: 8.8.8.8"
            clearable
          />
        </el-form-item>

        <el-form-item v-if="queryMode === 'batch'" label="IP列表">
          <el-input
            v-model="formData.batchIps"
            type="textarea"
            rows="4"
            placeholder="每行一个IP地址"
          />
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="formData.useCache">使用缓存</el-checkbox>
        </el-form-item>

        <el-button type="primary" @click="handleQuery" :loading="loading">
          <el-icon><Search /></el-icon>
          查询
        </el-button>
      </el-form>
    </el-card>

    <!-- 单个查询结果 -->
    <div v-if="queryMode === 'single' && singleResult" class="results-container">
      <el-card shadow="hover">
        <template #header>
          <div class="card-header">
            <span>查询结果 - {{ singleResult.data.ip }}</span>
            <el-tag :type="singleResult.source === 'cache' ? 'success' : 'info'">
              {{ singleResult.source === 'cache' ? '缓存' : 'API' }}
            </el-tag>
          </div>
        </template>

        <el-row :gutter="20">
          <el-col :xs="24" :sm="12" :md="8">
            <div class="info-item">
              <div class="label">IP 地址</div>
              <div class="value">{{ singleResult.data.ip }}</div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <div class="info-item">
              <div class="label">国家/地区</div>
              <div class="value">{{ singleResult.data.country || '-' }}</div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <div class="info-item">
              <div class="label">城市</div>
              <div class="value">{{ singleResult.data.city || '-' }}</div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <div class="info-item">
              <div class="label">州/地区</div>
              <div class="value">{{ singleResult.data.region || '-' }}</div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <div class="info-item">
              <div class="label">时区</div>
              <div class="value">{{ singleResult.data.timezone || '-' }}</div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <div class="info-item">
              <div class="label">运营商</div>
              <div class="value">{{ singleResult.data.org || '-' }}</div>
            </div>
          </el-col>
        </el-row>

        <el-divider v-if="singleResult.data.loc" />

        <div v-if="singleResult.data.loc" class="location-info">
          <div class="label">坐标</div>
          <div class="value">{{ singleResult.data.loc }}</div>
        </div>
      </el-card>
    </div>

    <!-- 批量查询结果 -->
    <div v-if="queryMode === 'batch' && batchResult" class="results-container">
      <el-card shadow="hover">
        <template #header>
          <div class="card-header">
            <span>批量查询结果</span>
            <el-tag>共 {{ batchResult.total }} 条</el-tag>
          </div>
        </template>

        <el-descriptions :column="4" border>
          <el-descriptions-item label="总数">{{ batchResult.total }}</el-descriptions-item>
          <el-descriptions-item label="缓存">{{ batchResult.cached }}</el-descriptions-item>
          <el-descriptions-item label="查询">{{ batchResult.queried }}</el-descriptions-item>
          <el-descriptions-item label="失败">{{ batchResult.failed }}</el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <el-table :data="batchResult.results" stripe>
          <el-table-column prop="ip" label="IP地址" width="120" />
          <el-table-column prop="data.country" label="国家" width="80" />
          <el-table-column prop="data.city" label="城市" width="100" />
          <el-table-column prop="data.timezone" label="时区" width="100" />
          <el-table-column label="来源" width="80">
            <template #default="{ row }">
              <el-tag :type="row.source === 'cache' ? 'success' : 'info'">
                {{ row.source === 'cache' ? '缓存' : 'API' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="详情" width="80" fixed="right">
            <template #default="{ row }">
              <el-button @click="showDetail(row)" link type="primary" size="small">
                查看
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="IP详细信息" width="600px">
      <div v-if="selectedDetail" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="IP">{{ selectedDetail.data.ip }}</el-descriptions-item>
          <el-descriptions-item label="来源">
            <el-tag :type="selectedDetail.source === 'cache' ? 'success' : 'info'">
              {{ selectedDetail.source === 'cache' ? '缓存' : 'API' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="国家">{{ selectedDetail.data.country || '-' }}</el-descriptions-item>
          <el-descriptions-item label="城市">{{ selectedDetail.data.city || '-' }}</el-descriptions-item>
          <el-descriptions-item label="州/地区">{{ selectedDetail.data.region || '-' }}</el-descriptions-item>
          <el-descriptions-item label="邮编">{{ selectedDetail.data.postal || '-' }}</el-descriptions-item>
          <el-descriptions-item label="时区">{{ selectedDetail.data.timezone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="运营商">{{ selectedDetail.data.org || '-' }}</el-descriptions-item>
          <el-descriptions-item label="主机名">{{ selectedDetail.data.hostname || '-' }}</el-descriptions-item>
          <el-descriptions-item v-if="selectedDetail.data.loc" label="坐标">{{ selectedDetail.data.loc }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { ipinfoAPI } from '@/api'
import type { IPQueryResponse, BatchIPQueryResponse } from '@/api/modules/ipinfo'

type QueryMode = 'single' | 'batch'

const queryMode = ref<QueryMode>('single')
const loading = ref(false)

const formData = ref({
  singleIp: '',
  batchIps: '',
  useCache: true
})

const singleResult = ref<IPQueryResponse | null>(null)
const batchResult = ref<BatchIPQueryResponse | null>(null)

const detailDialogVisible = ref(false)
const selectedDetail = ref<any>(null)

const handleQuery = async () => {
  if (queryMode.value === 'single') {
    if (!formData.value.singleIp.trim()) {
      ElMessage.warning('请输入IP地址')
      return
    }
    await querySingle()
  } else {
    if (!formData.value.batchIps.trim()) {
      ElMessage.warning('请输入IP地址列表')
      return
    }
    await queryBatch()
  }
}

const querySingle = async () => {
  loading.value = true
  try {
    singleResult.value = await ipinfoAPI.query(formData.value.singleIp, formData.value.useCache)
    ElMessage.success('查询成功')
  } catch (error: any) {
    ElMessage.error(error.message || '查询失败')
  } finally {
    loading.value = false
  }
}

const queryBatch = async () => {
  loading.value = true
  try {
    const ips = formData.value.batchIps
      .split('\n')
      .map(ip => ip.trim())
      .filter(ip => ip.length > 0)

    if (ips.length === 0) {
      ElMessage.warning('请输入有效的IP地址')
      return
    }

    batchResult.value = await ipinfoAPI.batchQuery(ips, formData.value.useCache)
    ElMessage.success(`查询成功，共 ${batchResult.value.total} 条记录`)
  } catch (error: any) {
    ElMessage.error(error.message || '查询失败')
  } finally {
    loading.value = false
  }
}

const showDetail = (row: any) => {
  selectedDetail.value = row
  detailDialogVisible.value = true
}
</script>

<style scoped lang="scss">
.ip-query-container {
  .query-card {
    margin-bottom: 20px;

    .card-header {
      display: flex;
      align-items: center;
      gap: 12px;

      .title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
      }
    }

    .query-form {
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

    .info-item {
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
        word-break: break-all;
      }
    }

    .location-info {
      padding: 12px;
      background: #f5f7fa;
      border-radius: 6px;

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
  }

  .detail-content {
    padding: 12px 0;
  }
}
</style>
