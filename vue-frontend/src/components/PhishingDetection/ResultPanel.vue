<template>
    <div class="result-panel">
        <el-card :class="['risk-card', riskClass]" shadow="hover">
            <div class="risk-content">
                <div class="risk-info">
                    <div class="risk-header">
                        <span class="risk-label">综合风险评估</span>
                        <div class="badges">
                            <el-tag v-if="isEduDomain" type="success" size="small" effect="plain">教育域名保护</el-tag>
                            <el-tag v-if="isIPObfuscate" type="danger" size="small" effect="dark"
                                class="animate-pulse">IP混淆攻击</el-tag>
                            <el-tag size="small" effect="plain">{{ modelName }}</el-tag>
                        </div>
                    </div>

                    <div class="risk-score">
                        <span :class="['risk-level', riskClass]">{{ riskText }}</span>
                        <div class="score-percent">{{ (result.final * 100).toFixed(1) }}%</div>
                    </div>

                    <p class="risk-desc">{{ riskDesc }}</p>

                    <el-alert v-if="isIPObfuscate" title="攻击向量检测" :description="'IP混淆/十六进制编码攻击'" type="error" show-icon
                        :closable="false" class="attack-alert" />
                </div>

                <ModelDetailPanel :result="result" :threshold="threshold" />
            </div>
        </el-card>

        <FeatureList :features="result.features || []" />

        <div class="engine-stats">
            <EngineCard title="深度语义分析" description="基于GTE模型的语义向量空间距离计算"
                :score="result.models?.gte?.score || result.gte || 0" color="primary" />
            <EngineCard title="特征规则匹配" description="基于SVM的15维特征工程规则检测"
                :score="result.models?.svm?.score || result.svm || 0" color="info" />
        </div>

        <!-- 完整后端响应数据 -->
        <el-card shadow="hover" class="response-card">
            <div class="response-header">
                <h3>
                    <el-icon>
                        <Document />
                    </el-icon>
                    完整后端响应
                </h3>
                <el-button type="text" size="small" @click="toggleResponseView">
                    {{ showResponse ? '隐藏' : '显示' }}
                </el-button>
            </div>
            <el-collapse v-model="activeResponseTab">
                <el-collapse-item title="原始数据" name="1">
                    <pre class="response-json">{{ formattedResponse }}</pre>
                </el-collapse-item>
            </el-collapse>
        </el-card>
    </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import ModelDetailPanel from './ModelDetailPanel.vue'
import FeatureList from './FeatureList.vue'
import EngineCard from './EngineCard.vue'
import { Document } from '@element-plus/icons-vue'

const props = defineProps<{
    result: any
    model: string
    threshold: number
}>()

const modelName = computed(() => {
    const names: Record<string, string> = {
        svm: 'SVM',
        gte: 'GTE',
        ngram: 'N-gram',
        deep: 'DEEP'
    }
    return names[props.model] || props.model.toUpperCase()
})

const isEduDomain = computed(() => false) // 从store获取
const isIPObfuscate = computed(() => false) // 从store获取

const riskClass = computed(() => {
    const score = props.result.final
    if (score >= 0.95) return 'critical'
    if (score >= 0.8) return 'high'
    if (score >= props.threshold / 100) return 'medium'
    if (score >= 0.3) return 'low'
    return 'safe'
})

const riskText = computed(() => {
    const score = props.result.final
    if (score >= 0.95) return '极高风险'
    if (score >= 0.8) return '高风险'
    if (score >= props.threshold / 100) return '中风险'
    if (score >= 0.3) return '低风险'
    return '安全'
})

const riskDesc = computed(() => {
    const score = props.result.final
    if (score >= 0.95) return '确认钓鱼攻击特征，立即拦截！'
    if (score >= 0.8) return isIPObfuscate.value ? '检测到IP混淆攻击手法' : '多重钓鱼特征匹配'
    if (score >= props.threshold / 100) return '存在可疑特征，请谨慎访问'
    if (score >= 0.3) return '轻微异常或新域名'
    return '未检测到钓鱼特征'
})

// 后端响应显示控制
const showResponse = ref(false)
const activeResponseTab = ref(['1'])

const formattedResponse = computed(() => {
    try {
        return JSON.stringify(props.result, null, 2)
    } catch (error) {
        return '无法格式化响应数据'
    }
})

const toggleResponseView = () => {
    showResponse.value = !showResponse.value
    if (showResponse.value) {
        activeResponseTab.value = ['1']
    }
}
</script>

<style lang="scss" scoped>
.result-panel {
    margin-bottom: 1.5rem;
}

.risk-card {
    margin-bottom: 1rem;

    &.safe {
        border-left: 4px solid #10b981;
    }

    &.low {
        border-left: 4px solid #3b82f6;
    }

    &.medium {
        border-left: 4px solid #f59e0b;
    }

    &.high {
        border-left: 4px solid #ef4444;
    }

    &.critical {
        border-left: 4px solid #dc2626;
        animation: pulse-red 2s infinite;
    }

    :deep(.el-card__body) {
        padding: 1.5rem;
    }
}

.risk-content {
    display: flex;
    flex-direction: column;
    gap: 1rem;

    @media (min-width: 768px) {
        flex-direction: row;
        justify-content: space-between;
    }
}

.risk-info {
    flex: 1;

    .risk-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        flex-wrap: wrap;
        margin-bottom: 0.75rem;

        .risk-label {
            font-size: 0.875rem;
            font-weight: 500;
            color: #6b7280;
        }

        .badges {
            display: flex;
            gap: 0.5rem;
        }
    }

    .risk-score {
        display: flex;
        align-items: baseline;
        gap: 1rem;
        margin-bottom: 0.5rem;

        .risk-level {
            font-size: 2rem;
            font-weight: 800;

            &.safe {
                color: #059669;
            }

            &.low {
                color: #2563eb;
            }

            &.medium {
                color: #d97706;
            }

            &.high {
                color: #dc2626;
            }

            &.critical {
                color: #991b1b;
            }
        }

        .score-percent {
            font-size: 1.5rem;
            font-family: monospace;
            font-weight: 700;
            color: #4b5563;
        }
    }

    .risk-desc {
        color: #6b7280;
    }

    .attack-alert {
        margin-top: 1rem;
    }
}

.engine-stats {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1rem;
    margin-top: 1rem;

    @media (min-width: 768px) {
        grid-template-columns: 1fr 1fr;
    }
}

.response-card {
    margin-top: 1.5rem;
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(16px);

    :deep(.el-card__body) {
        padding: 1.5rem;
    }

    .response-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;

        h3 {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 1rem;
            font-weight: 600;
            color: #374151;
        }
    }

    .response-json {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 0.375rem;
        padding: 1rem;
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 0.875rem;
        line-height: 1.5;
        white-space: pre-wrap;
        overflow-x: auto;
        max-height: 400px;
        overflow-y: auto;
        color: #374151;

        &::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }

        &::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 3px;
        }

        &::-webkit-scrollbar-thumb {
            background: #c1c1c1;
            border-radius: 3px;
        }

        &::-webkit-scrollbar-thumb:hover {
            background: #a8a8a8;
        }
    }
}

@keyframes pulse-red {

    0%,
    100% {
        box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.3);
    }

    50% {
        box-shadow: 0 0 0 12px rgba(220, 38, 38, 0);
    }
}
</style>