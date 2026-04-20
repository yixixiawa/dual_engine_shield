<template>
    <el-card class="history-card" shadow="hover">
        <template #header>
            <div class="card-header">
                <el-icon>
                    <Clock />
                </el-icon>
                <span>检测历史</span>
                <el-button v-if="history.length > 0" type="danger" link size="small" @click="clearHistory">
                    清空历史
                </el-button>
            </div>
        </template>

        <div v-if="history.length === 0" class="empty-state">
            <el-empty description="暂无检测历史" :image-size="80" />
        </div>

        <el-table v-else :data="history" stripe style="width: 100%">
            <el-table-column prop="url" label="URL" min-width="200" show-overflow-tooltip>
                <template #default="{ row }">
                    <span class="url-text">{{ row.url }}</span>
                </template>
            </el-table-column>

            <el-table-column prop="model" label="检测模型" width="140">
                <template #default="{ row }">
                    <el-tag size="small" :type="getModelType(row.model)">{{ getModelName(row.model) }}</el-tag>
                </template>
            </el-table-column>

            <el-table-column prop="score" label="风险评分" width="100">
                <template #default="{ row }">
                    <span :class="getScoreClass(row.score)" class="score-value">
                        {{ (row.score * 100).toFixed(1) }}%
                    </span>
                </template>
            </el-table-column>

            <el-table-column prop="mainThreat" label="主要威胁特征" min-width="150" show-overflow-tooltip>
                <template #default="{ row }">
                    <span class="threat-text">{{ row.mainThreat || '无威胁' }}</span>
                </template>
            </el-table-column>

            <el-table-column prop="result" label="判定结果" width="100">
                <template #default="{ row }">
                    <el-tag :type="getResultType(row.score)" size="small">
                        {{ getResultText(row.score) }}
                    </el-tag>
                </template>
            </el-table-column>

            <el-table-column prop="timestamp" label="检测时间" width="160">
                <template #default="{ row }">
                    {{ formatTime(row.timestamp) }}
                </template>
            </el-table-column>
        </el-table>
    </el-card>
</template>

<script setup lang="ts">
import { ElMessageBox } from 'element-plus'

const props = defineProps<{
    history: Array<{
        url: string
        score: number
        model?: string
        mainThreat?: string
        timestamp: Date | string
        features?: any[]
    }>
}>()

const emit = defineEmits<{
    (e: 'clear'): void
}>()

const getScoreClass = (score: number) => {
    if (score >= 0.8) return 'text-danger'
    if (score >= 0.5) return 'text-warning'
    return 'text-success'
}

const getModelName = (_model: string) => {
    return 'GTE'
}

const getModelType = (_model: string) => {
    return 'primary'
}

const getResultType = (score: number) => {
    if (score >= 0.8) return 'danger'
    if (score >= 0.5) return 'warning'
    return 'success'
}

const getResultText = (score: number) => {
    if (score >= 0.8) return '拦截'
    if (score >= 0.5) return '警告'
    return '通过'
}

const formatTime = (time: Date | string) => {
    if (time instanceof Date) {
        return time.toLocaleString()
    }
    return time
}

const clearHistory = () => {
    ElMessageBox.confirm('确定要清空所有检测历史吗？', '确认清空', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
    }).then(() => {
        emit('clear')
    }).catch(() => { })
}
</script>

<style lang="scss" scoped>
.history-card {
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(16px);

    .card-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-weight: 500;

        .el-button {
            margin-left: auto;
        }
    }

    .empty-state {
        padding: 2rem;
    }

    .url-text {
        font-family: monospace;
        font-size: 0.75rem;
    }

    .score-value {
        font-weight: 600;
        font-family: monospace;
    }

    .threat-text {
        font-size: 0.75rem;
        color: #6b7280;
    }

    .text-danger {
        color: #ef4444;
    }

    .text-warning {
        color: #f59e0b;
    }

    .text-success {
        color: #10b981;
    }
}
</style>