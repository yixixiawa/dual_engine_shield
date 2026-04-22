<template>
    <el-dialog v-model="dialogVisible" :title="`任务详情 - ${currentTask?.id || ''}`" width="700px"
        :close-on-click-modal="false" @close="handleClose">
        <div v-if="currentTask" class="task-detail">
            <!-- 基本信息 -->
            <el-descriptions :column="2" border>
                <el-descriptions-item label="任务ID">
                    <span class="mono">{{ currentTask.id }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="任务类型">
                    <el-tag :type="getTypeTagType(currentTask.type)" size="small">
                        {{ getTypeName(currentTask.type) }}
                    </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="任务状态">
                    <el-tag :type="getStatusTagType(currentTask.status)" size="small">
                        {{ getStatusName(currentTask.status) }}
                    </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="创建时间">
                    {{ currentTask.createdAt }}
                </el-descriptions-item>
                <el-descriptions-item label="检测目标" :span="2">
                    <span class="target-text">{{ currentTask.target }}</span>
                </el-descriptions-item>
            </el-descriptions>

            <!-- 检测结果 -->
            <div v-if="currentTask.status === 'completed'" class="result-section">
                <el-divider content-position="left">
                    <el-icon>
                        <DataAnalysis />
                    </el-icon>
                    检测结果
                </el-divider>

                <!-- 漏洞检测结果 -->
                <template v-if="isVulnerabilityTask">
                    <VulnerabilityResultDetail :result="currentTask.result" />
                </template>

                <!-- 钓鱼检测结果 -->
                <template v-else-if="isPhishingTask">
                    <PhishingResultDetail :result="currentTask.result" />
                </template>

                <!-- 综合检测结果 -->
                <template v-else-if="isCombinedTask">
                    <CombinedResultDetail :result="currentTask.result" />
                </template>

                <!-- URL/Web扫描结果 -->
                <template v-else-if="isUrlOrWebTask">
                    <UrlWebResultDetail :result="currentTask.result" :type="currentTask.type" />
                </template>

                <!-- 通用结果展示 -->
                <template v-else>
                    <el-collapse>
                        <el-collapse-item title="查看原始数据" name="raw">
                            <pre class="raw-data">{{ JSON.stringify(currentTask.result, null, 2) }}</pre>
                        </el-collapse-item>
                    </el-collapse>
                </template>
            </div>

            <!-- 失败状态 -->
            <div v-else-if="currentTask.status === 'failed'" class="error-section">
                <el-alert title="检测失败" :description="currentTask.result?.error || '未知错误'" type="error" show-icon
                    :closable="false" />
            </div>

            <!-- 处理中状态 -->
            <div v-else-if="currentTask.status === 'processing'" class="processing-section">
                <el-skeleton :rows="5" animated />
                <div class="processing-tip">
                    <el-icon class="is-loading">
                        <Loading />
                    </el-icon>
                    <span>任务正在处理中，请稍后刷新查看结果...</span>
                </div>
            </div>

            <!-- 待处理状态 -->
            <div v-else class="pending-section">
                <el-empty description="任务尚未开始处理" />
            </div>
        </div>

        <template #footer>
            <div class="dialog-footer">
                <el-button @click="handleClose">关闭</el-button>
                <el-button v-if="canRetry" type="primary" @click="handleRetry">
                    <el-icon>
                        <RefreshRight />
                    </el-icon>
                    重新检测
                </el-button>
                <el-button v-if="canExport" type="success" @click="exportReport">
                    <el-icon>
                        <Download />
                    </el-icon>
                    导出报告
                </el-button>
            </div>
        </template>
    </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useTasksStore } from '@/stores/tasks'
import VulnerabilityResultDetail from './VulnerabilityResultDetail.vue'
import PhishingResultDetail from './PhishingResultDetail.vue'
import CombinedResultDetail from './CombinedResultDetail.vue'
import UrlWebResultDetail from './UrlWebResultDetail.vue'
import { ElMessage } from 'element-plus'

const tasksStore = useTasksStore()

const dialogVisible = computed({
    get: () => tasksStore.detailVisible,
    set: (val) => {
        if (!val) tasksStore.closeTaskDetail()
    }
})

const currentTask = computed(() => tasksStore.currentTask)

const isVulnerabilityTask = computed(() => {
    const type = currentTask.value?.type
    return type === 'source_code' || type === 'vulnerability'
})

const isPhishingTask = computed(() => {
    return currentTask.value?.type === 'phishing'
})

const isCombinedTask = computed(() => {
    return currentTask.value?.type === 'combined'
})

const isUrlOrWebTask = computed(() => {
    const type = currentTask.value?.type
    return type === 'url' || type === 'web'
})

const canRetry = computed(() => {
    return currentTask.value?.status === 'failed'
})

const canExport = computed(() => {
    return currentTask.value?.status === 'completed'
})

const getTypeName = (type: string) => {
    const names: Record<string, string> = {
        phishing: '钓鱼检测',
        source_code: '源码检测',
        vulnerability: '漏洞检测',
        url: 'URL检测',
        web: 'Web扫描',
        batch: '批量检测',
        combined: '综合检测'
    }
    return names[type] || type
}

const getTypeTagType = (type: string) => {
    const types: Record<string, string> = {
        phishing: 'danger',
        source_code: 'warning',
        vulnerability: 'warning',
        url: 'info',
        web: 'success',
        batch: 'primary',
        combined: ''
    }
    return types[type] || 'info'
}

const getStatusName = (status: string) => {
    const names: Record<string, string> = {
        pending: '待处理',
        processing: '检测中',
        completed: '已完成',
        failed: '失败'
    }
    return names[status] || status
}

const getStatusTagType = (status: string) => {
    const types: Record<string, string> = {
        pending: 'warning',
        processing: 'info',
        completed: 'success',
        failed: 'danger'
    }
    return types[status] || 'info'
}

const handleClose = () => {
    tasksStore.closeTaskDetail()
}

const handleRetry = () => {
    ElMessage.info('重试功能开发中...')
}

const exportReport = () => {
    if (!currentTask.value?.result) {
        ElMessage.warning('暂无结果数据')
        return
    }

    const dataStr = JSON.stringify(currentTask.value.result, null, 2)
    const blob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `report_${currentTask.value.id}.json`
    link.click()
    URL.revokeObjectURL(url)
    ElMessage.success('报告已导出')
}
</script>

<style lang="scss" scoped>
.task-detail {
    .mono {
        font-family: monospace;
        font-size: 0.75rem;
    }

    .target-text {
        word-break: break-all;
        font-size: 0.875rem;
    }

    .result-section {
        margin-top: 1rem;
    }

    .error-section {
        margin-top: 1rem;
    }

    .processing-section {
        margin-top: 1rem;

        .processing-tip {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            margin-top: 1rem;
            padding: 1rem;
            background: #f3f4f6;
            border-radius: 0.5rem;
            color: #6b7280;

            .is-loading {
                animation: spin 1s linear infinite;
            }
        }
    }

    .pending-section {
        margin-top: 1rem;
    }

    .raw-data {
        background: #1e1e2e;
        color: #e2e8f0;
        padding: 1rem;
        border-radius: 0.5rem;
        font-size: 0.75rem;
        overflow-x: auto;
        max-height: 300px;
    }
}

.dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
}

@keyframes spin {
    from {
        transform: rotate(0deg);
    }

    to {
        transform: rotate(360deg);
    }
}
</style>