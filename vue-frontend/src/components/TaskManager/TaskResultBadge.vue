<template>
    <div class="task-result-badge">
        <template v-if="task.status !== 'completed'">
            <span class="text-gray-400">-</span>
        </template>

        <template v-else-if="task.detection_type === 'source_code' || task.detection_type === 'vulnerability'">
            <div v-if="task.result?.is_vulnerable" class="result-vulnerable">
                <el-tag type="danger" size="small" effect="dark">⚠️ 存在漏洞</el-tag>
                <el-tag :type="severityTagType" size="small" class="severity-tag">
                    {{ severityText }}
                </el-tag>
                <div class="result-detail">{{ task.result.cwe_name || '未知类型' }}</div>
            </div>
            <div v-else class="result-safe">
                <el-tag type="success" size="small">✅ 代码安全</el-tag>
            </div>
        </template>

        <template v-else-if="task.detection_type === 'phishing'">
            <div v-if="task.result?.final || task.result?.risk_score || phishingScore > 0">
                <el-tag :type="getPhishingTagType(phishingScore)" size="small">
                    {{ phishingScore > 50 ? '⚠️' : '✅' }} {{ phishingScore.toFixed(1) }}%
                </el-tag>
            </div>
            <span v-else-if="batchResultInfo" class="text-gray-400">{{ batchResultInfo }}</span>
            <span v-else class="text-gray-400">-</span>
        </template>

        <template v-else-if="task.detection_type === 'url'">
            <el-tag :type="task.result?.is_vulnerable ? 'danger' : 'success'" size="small">
                {{ task.result?.is_vulnerable ? '存在风险' : '安全' }}
            </el-tag>
        </template>

        <template v-else-if="task.detection_type === 'web'">
            <el-tag :type="(task.result?.vulnerabilities_found || 0) > 0 ? 'danger' : 'success'" size="small">
                发现 {{ task.result?.vulnerabilities_found || 0 }} 个漏洞
            </el-tag>
        </template>

        <template v-else-if="task.detection_type === 'combined'">
            <el-tag :type="getCombinedRiskType(task.result)" size="small">
                {{ getCombinedRiskText(task.result) }}
            </el-tag>
        </template>

        <template v-else>
            <el-tag v-if="task.result?.error" type="danger" size="small">失败</el-tag>
            <el-tag v-else-if="task.result" type="success" size="small">完成</el-tag>
            <span v-else class="text-gray-400">-</span>
        </template>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
    task: {
        id: number
        detection_type: string
        status: string
        result?: any
    }
}>()

const phishingScore = computed(() => {
    const result = props.task.result
    if (!result) return 0
    
    // 处理批量检测结果
    if (result.kind === 'BatchAnalyzeResult' && result.results) {
        // 如果有多个结果，返回钓鱼网站数量比例
        const phishingCount = result.phishing_count || 0
        const totalUrls = result.total_urls || 1
        return (phishingCount / totalUrls) * 100
    }
    
    // 处理单个检测结果
    if (result.final !== undefined) return result.final * 100
    if (result.risk_score !== undefined) return result.risk_score * 100
    if (result.score !== undefined) return result.score * 100
    return 0
})

const batchResultInfo = computed(() => {
    const result = props.task.result
    if (!result) return null
    
    // 处理批量检测结果
    if (result.kind === 'BatchAnalyzeResult' && result.results) {
        return `批量检测: ${result.total_urls} 个URL, ${result.phishing_count} 个钓鱼`
    }
    
    return null
})

const severityText = computed(() => {
    const severity = props.task.result?.severity
    const texts: Record<string, string> = {
        critical: '严重',
        high: '高危',
        medium: '中危',
        low: '低危'
    }
    return texts[severity] || '未知'
})

const severityTagType = computed(() => {
    const severity = props.task.result?.severity
    const types: Record<string, string> = {
        critical: 'danger',
        high: 'danger',
        medium: 'warning',
        low: 'info'
    }
    return types[severity] || 'info'
})

const getPhishingTagType = (scoreValue: number) => {
    if (scoreValue >= 80) return 'danger'
    if (scoreValue >= 50) return 'warning'
    return 'success'
}

const getCombinedRiskType = (result: any) => {
    if (!result) return 'info'
    const phishingRisk = result.phishing?.final || result.phishing?.risk_score || 0
    const vulnCount = (result.code?.vulnerabilities?.length || 0) +
        (result.url?.is_vulnerable ? 1 : 0) +
        (result.web?.vulnerabilities_found || 0)

    if (phishingRisk >= 0.8 || vulnCount > 2) return 'danger'
    if (phishingRisk >= 0.5 || vulnCount > 0) return 'warning'
    return 'success'
}

const getCombinedRiskText = (result: any) => {
    if (!result) return '待检测'
    const phishingRisk = result.phishing?.final || result.phishing?.risk_score || 0
    const vulnCount = (result.code?.vulnerabilities?.length || 0) +
        (result.url?.is_vulnerable ? 1 : 0) +
        (result.web?.vulnerabilities_found || 0)

    if (phishingRisk >= 0.8 || vulnCount > 2) return '高风险'
    if (phishingRisk >= 0.5 || vulnCount > 0) return '中风险'
    return '安全'
}
</script>

<style lang="scss" scoped>
.task-result-badge {
    .result-vulnerable {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.25rem;

        .severity-tag {
            margin-left: 0.25rem;
        }

        .result-detail {
            font-size: 0.7rem;
            color: #6b7280;
            margin-top: 0.125rem;
            width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
    }

    .result-safe {
        display: inline-flex;
    }

    .text-gray-400 {
        color: #9ca3af;
    }
}
</style>