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

const phishingScore = computed(() => {
    return props.result?.phishing?.final || props.result?.phishing?.risk_score || 0
})

const codeVulnCount = computed(() => {
    return props.result?.code?.vulnerabilities?.length || 0
})

const urlVulnCount = computed(() => {
    return props.result?.url?.is_vulnerable ? 1 : 0
})

const webVulnCount = computed(() => {
    return props.result?.web?.vulnerabilities_found || 0
})

const totalVulns = computed(() => {
    return codeVulnCount.value + urlVulnCount.value + webVulnCount.value
})

const getPhishingRiskClass = (score: number) => {
    if (score >= 0.8) return 'text-danger'
    if (score >= 0.5) return 'text-warning'
    return 'text-success'
}
</script>

<style lang="scss" scoped>
.combined-result {
    .result-summary {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;

        .summary-item {
            text-align: center;
            padding: 1rem;
            background: #f9fafb;
            border-radius: 0.5rem;

            .summary-label {
                font-size: 0.75rem;
                color: #6b7280;
                margin-bottom: 0.5rem;
            }

            .summary-value {
                font-size: 1.5rem;
                font-weight: 700;
            }
        }
    }

    .detail-list {
        .detail-item {
            padding: 0.5rem 0;
            font-size: 0.875rem;

            .detail-label {
                font-weight: 500;
                color: #6b7280;
                margin-right: 0.5rem;
            }
        }
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