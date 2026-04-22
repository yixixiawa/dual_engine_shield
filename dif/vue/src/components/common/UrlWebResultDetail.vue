<template>
    <div class="url-web-result">
        <div class="result-header" :class="isVulnerable ? 'result-danger' : 'result-success'">
            <el-icon :size="32">
                <WarningFilled v-if="isVulnerable" />
                <CircleCheck v-else />
            </el-icon>
            <div class="result-info">
                <div class="result-title">{{ isVulnerable ? '存在风险' : '安全' }}</div>
                <div class="result-desc">{{ description }}</div>
            </div>
        </div>

        <div v-if="isVulnerable && vulnerabilities.length > 0" class="vuln-list">
            <div class="section-title">发现的漏洞</div>
            <div v-for="(vuln, idx) in vulnerabilities" :key="idx" class="vuln-item">
                <el-tag :type="getSeverityType(vuln.severity)" size="small">
                    {{ getSeverityText(vuln.severity) }}
                </el-tag>
                <span class="vuln-name">{{ vuln.type || vuln.name }}</span>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
    result: any
    type: string
}>()

const isVulnerable = computed(() => {
    if (props.type === 'url') {
        return props.result?.is_vulnerable === true
    }
    return (props.result?.vulnerabilities_found || 0) > 0
})

const vulnerabilities = computed(() => {
    if (props.type === 'url') {
        return props.result?.vulnerabilities || []
    }
    return props.result?.vulnerabilities || []
})

const description = computed(() => {
    if (!isVulnerable.value) return '未检测到安全风险'
    if (props.type === 'url') {
        return `检测到 ${vulnerabilities.value.length} 个漏洞`
    }
    return `发现 ${props.result?.vulnerabilities_found || 0} 个漏洞`
})

const getSeverityType = (severity: string) => {
    const types: Record<string, string> = {
        critical: 'danger',
        high: 'danger',
        medium: 'warning',
        low: 'info'
    }
    return types[severity] || 'info'
}

const getSeverityText = (severity: string) => {
    const texts: Record<string, string> = {
        critical: '严重',
        high: '高危',
        medium: '中危',
        low: '低危'
    }
    return texts[severity] || severity
}
</script>

<style lang="scss" scoped>
.url-web-result {
    .result-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;

        &.result-danger {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid #ef4444;
        }

        &.result-success {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid #10b981;
        }

        .result-info {
            flex: 1;

            .result-title {
                font-weight: 600;
                margin-bottom: 0.25rem;
            }

            .result-desc {
                font-size: 0.75rem;
                color: #6b7280;
            }
        }
    }

    .vuln-list {
        .section-title {
            font-weight: 500;
            margin-bottom: 0.5rem;
        }

        .vuln-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem;
            background: #f9fafb;
            border-radius: 0.5rem;
            margin-bottom: 0.5rem;

            .vuln-name {
                font-size: 0.875rem;
            }
        }
    }
}
</style>