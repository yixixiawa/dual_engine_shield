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
                        <div class="score-percent">{{ (result.score * 100).toFixed(1) }}%</div>
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
                :score="result.scores_per_model?.original || result.score || 0" color="primary" />
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
    return 'GTE 深度语义检测'
})

const isEduDomain = computed(() => false) // 从store获取
const isIPObfuscate = computed(() => false) // 从store获取

const riskClass = computed(() => {
    const score = props.result.score || 0
    const threshold = props.result.threshold || 0.5
    if (score >= 0.95) return 'critical'
    if (score >= 0.8) return 'high'
    if (score >= threshold) return 'medium'
    if (score >= 0.3) return 'low'
    return 'safe'
})

const riskText = computed(() => {
    const score = props.result.score || 0
    const threshold = props.result.threshold || 0.5
    if (score >= 0.95) return '极高风险'
    if (score >= 0.8) return '高风险'
    if (score >= threshold) return '中风险'
    if (score >= 0.3) return '低风险'
    return '安全'
})

const riskDesc = computed(() => {
    const score = props.result.score || 0
    const threshold = props.result.threshold || 0.5
    if (score >= 0.95) return '确认钓鱼攻击特征，立即拦截！'
    if (score >= 0.8) return isIPObfuscate.value ? '检测到IP混淆攻击手法' : '多重钓鱼特征匹配'
    if (score >= threshold) return '存在可疑特征，请谨慎访问'
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
@use '@/styles/variables.scss' as *;

.result-panel {
    margin-bottom: 1.5rem;
    animation: slideInDown 0.3s ease-out;
}

.risk-card {
    margin-bottom: 1rem;
    transition: all 0.2s ease;
    border: 1px solid rgba(79, 70, 229, 0.2);

    &:hover {
        box-shadow: 0 12px 24px -8px rgba(0, 0, 0, 0.15);
    }

    &.safe {
        border-left: 4px solid #10b981;

        &:hover {
            box-shadow: 0 12px 24px -8px rgba(16, 185, 129, 0.2);
        }
    }

    &.low {
        border-left: 4px solid #3b82f6;

        &:hover {
            box-shadow: 0 12px 24px -8px rgba(59, 130, 246, 0.2);
        }
    }

    &.medium {
        border-left: 4px solid #f59e0b;

        &:hover {
            box-shadow: 0 12px 24px -8px rgba(245, 158, 11, 0.2);
        }
    }

    &.high {
        border-left: 4px solid #ef4444;

        &:hover {
            box-shadow: 0 12px 24px -8px rgba(239, 68, 68, 0.2);
        }
    }

    &.critical {
        border-left: 4px solid #dc2626;
        animation: pulse-red 2s infinite;

        &:hover {
            box-shadow: 0 12px 24px -8px rgba(220, 38, 38, 0.3);
        }
    }

    :deep(.el-card__body) {
        padding: 1.5rem;
        transition: all 0.2s ease;
    }
}

.risk-content {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    transition: all 0.2s ease;

    @media (min-width: 768px) {
        flex-direction: row;
        justify-content: space-between;
    }
}

.risk-info {
    flex: 1;
    transition: all 0.2s ease;

    .risk-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        flex-wrap: wrap;
        margin-bottom: 0.75rem;
        transition: all 0.2s ease;

        .risk-label {
            font-size: 0.875rem;
            font-weight: 500;
            color: #6b7280;
            transition: all 0.2s ease;
        }

        .badges {
            display: flex;
            gap: 0.5rem;

            :deep(.el-tag) {
                transition: all 0.2s ease;

                &:hover {
                    transform: scale(1.05);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                }
            }
        }
    }

    .risk-score {
        display: flex;
        align-items: baseline;
        gap: 1rem;
        margin-bottom: 0.5rem;
        transition: all 0.2s ease;

        .risk-level {
            font-size: 2rem;
            font-weight: 800;
            transition: all 0.2s ease;

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
                animation: pulse 1s ease-in-out infinite;
            }
        }

        .score-percent {
            font-size: 1.5rem;
            font-family: monospace;
            font-weight: 700;
            color: #4b5563;
            transition: all 0.2s ease;
        }
    }

    .risk-desc {
        color: #6b7280;
        transition: all 0.2s ease;
        animation: fadeIn 0.3s ease-out;
    }

    .attack-alert {
        margin-top: 1rem;
        transition: all 0.2s ease;

        :deep(.el-alert) {
            animation: slideInDown 0.3s ease-out;
        }
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

    :deep(.engine-card) {
        transition: all 0.2s ease;

        &:hover {
            transform: translateY(-2px);
        }
    }
}

.response-card {
    margin-top: 1.5rem;
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(16px);
    transition: all 0.2s ease;
    border: 1px solid rgba(79, 70, 229, 0.2);

    &:hover {
        box-shadow: 0 12px 24px -8px rgba(79, 70, 229, 0.15);
        border-color: rgba(79, 70, 229, 0.3);
    }

    :deep(.el-card__body) {
        padding: 1.5rem;
    }

    .response-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        transition: all 0.2s ease;

        h3 {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 1rem;
            font-weight: 600;
            color: #374151;
            transition: all 0.2s ease;

            &:hover {
                color: $primary;
            }
        }

        :deep(.el-button) {
            transition: all 0.2s ease;

            &:hover {
                transform: translateY(-2px);
            }
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
        transition: all 0.2s ease;

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
            transition: all 0.2s ease;
        }

        &::-webkit-scrollbar-thumb:hover {
            background: #a8a8a8;
        }
    }
}

@keyframes slideInDown {
    from {
        opacity: 0;
        transform: translateY(-20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}

@keyframes pulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.8;
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