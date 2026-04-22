<template>
    <div class="combined-result">
        <div class="result-summary">
            <div class="summary-item">
                <div class="summary-label">钓鱼检测</div>
                <div class="summary-value" :class="getPhishingRiskClass(phishingScore)">
                    {{ (phishingScore * 100).toFixed(1) }}%
                </div>
            </div>
            <div class="summary-item">
                <div class="summary-label">漏洞检测</div>
                <div class="summary-value" :class="totalVulns > 0 ? 'text-danger' : 'text-success'">
                    {{ totalVulns > 0 ? `${totalVulns} 个` : '安全' }}
                </div>
            </div>
        </div>

        <el-divider />

        <div class="detail-list">
            <div class="detail-item">
                <span class="detail-label">源码漏洞：</span>
                <span :class="codeVulnCount > 0 ? 'text-danger' : 'text-success'">
                    {{ codeVulnCount > 0 ? `${codeVulnCount} 个` : '安全' }}
                </span>
            </div>
            <div class="detail-item">
                <span class="detail-label">URL漏洞：</span>
                <span :class="urlVulnCount > 0 ? 'text-danger' : 'text-success'">
                    {{ urlVulnCount > 0 ? '有风险' : '安全' }}
                </span>
            </div>
            <div class="detail-item">
                <span class="detail-label">Web漏洞：</span>
                <span :class="webVulnCount > 0 ? 'text-danger' : 'text-success'">
                    {{ webVulnCount > 0 ? `${webVulnCount} 个` : '安全' }}
                </span>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
    result: any
}>()

// 兼容两种数据格式：
// 1. 后端综合检测返回格式：{ phishing_detection: {...}, code_vulnerabilities: [...], comprehensive_risk: {...} }
// 2. 旧格式：{ phishing: {...}, code: {...}, url: {...}, web: {...} }

const phishingScore = computed(() => {
    // 新格式
    const phishingDetection = props.result?.phishing_detection
    if (phishingDetection && phishingDetection.score !== undefined) {
        return phishingDetection.score
    }
    // 旧格式
    return props.result?.phishing?.final || props.result?.phishing?.risk_score || 0
})

const codeVulnCount = computed(() => {
    // 新格式
    const codeVulns = props.result?.code_vulnerabilities
    if (Array.isArray(codeVulns)) {
        return codeVulns.length
    }
    // 旧格式
    return props.result?.code?.vulnerabilities?.length || 0
})

const urlVulnCount = computed(() => {
    return props.result?.url?.is_vulnerable ? 1 : 0
})

const webVulnCount = computed(() => {
    return props.result?.web?.vulnerabilities_found || 0
})

const totalVulns = computed(() => {
    // 新格式：直接使用 total_vulnerabilities
    if (props.result?.total_vulnerabilities !== undefined) {
        return props.result.total_vulnerabilities
    }
    return codeVulnCount.value + urlVulnCount.value + webVulnCount.value
})

const getPhishingRiskClass = (score: number) => {
    if (score >= 0.8) return 'text-danger'
    if (score >= 0.5) return 'text-warning'
    return 'text-success'
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.combined-result {
    .result-summary {
        @include info-grid(180px);
        margin-bottom: $space-2;
    }

    .summary-item {
        @include stat-tile;
        text-align: center;
    }

    .summary-label {
        margin-bottom: $space-2;
        font-size: 0.8125rem;
        color: $text-secondary;
    }

    .summary-value {
        font-size: 1.75rem;
        font-weight: 700;
    }

    .detail-list {
        display: flex;
        flex-direction: column;
        gap: $space-3;
    }

    .detail-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: $space-4;
        padding: $space-3 $space-4;
        border-radius: $radius-md;
        background: $surface-muted;
        border: 1px solid rgba(24, 144, 255, 0.08);
        font-size: 0.875rem;
        color: $text-primary;
    }

    .detail-label {
        color: $text-secondary;
        font-weight: 500;
    }

    .text-danger {
        color: $danger;
    }

    .text-warning {
        color: $warning;
    }

    .text-success {
        color: $success;
    }
}

@media (max-width: $breakpoint-sm) {
    .combined-result {
        .detail-item {
            flex-direction: column;
            align-items: flex-start;
        }
    }
}
</style>
