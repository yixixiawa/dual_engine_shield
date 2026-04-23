<template>
    <div class="phishing-result-detail">
        <!-- 结果头部 -->
        <div class="result-header" :class="riskClass">
            <div class="result-icon">
                <el-icon v-if="isRisky" :size="32">
                    <WarningFilled />
                </el-icon>
                <el-icon v-else :size="32">
                    <CircleCheck />
                </el-icon>
            </div>
            <div class="result-info">
                <div class="result-title">{{ riskText }}</div>
                <div class="result-subtitle">{{ riskDesc }}</div>
            </div>
            <div class="score-circle">
                <el-progress type="circle" :percentage="scorePercent" :width="70" :stroke-width="6"
                    :color="progressColor" />
            </div>
        </div>

        <!-- 模型分数详情 -->
        <div class="model-scores">
            <div class="section-title">
                <el-icon>
                    <DataLine />
                </el-icon>
                <span>模型检测详情</span>
            </div>

            <div class="model-grid">
                <div v-if="hasModel('svm')" class="model-item">
                    <div class="model-header">
                        <span class="model-name">
                            <span class="model-dot blue"></span>
                            SVM
                        </span>
                        <span class="model-score" :class="getScoreClass(getModelScore('svm'))">
                            {{ (getModelScore('svm') * 100).toFixed(1) }}%
                        </span>
                    </div>
                    <el-progress :percentage="getModelScore('svm') * 100" :stroke-width="6"
                        :color="getProgressColor(getModelScore('svm'))" :show-text="false" />
                </div>

                <div v-if="hasModel('gte')" class="model-item">
                    <div class="model-header">
                        <span class="model-name">
                            <span class="model-dot purple"></span>
                            GTE
                        </span>
                        <span class="model-score" :class="getScoreClass(getModelScore('gte'))">
                            {{ (getModelScore('gte') * 100).toFixed(1) }}%
                        </span>
                    </div>
                    <el-progress :percentage="getModelScore('gte') * 100" :stroke-width="6"
                        :color="getProgressColor(getModelScore('gte'))" :show-text="false" />
                </div>

                <div v-if="hasModel('ngram')" class="model-item">
                    <div class="model-header">
                        <span class="model-name">
                            <span class="model-dot orange"></span>
                            N-gram
                        </span>
                        <span class="model-score" :class="getScoreClass(getModelScore('ngram'))">
                            {{ (getModelScore('ngram') * 100).toFixed(1) }}%
                        </span>
                    </div>
                    <el-progress :percentage="getModelScore('ngram') * 100" :stroke-width="6"
                        :color="getProgressColor(getModelScore('ngram'))" :show-text="false" />
                </div>
            </div>
        </div>

        <!-- 四层检测详情 -->
        <div v-if="result.layers" class="layer-details">
            <div class="section-title">
                <el-icon>
                    <Connection />
                </el-icon>
                <span>四层检测详情</span>
            </div>

            <div class="layer-list">
                <div v-for="layer in layerConfigs" :key="layer.key" class="layer-item">
                    <div class="layer-header">
                        <div>
                            <span class="layer-name">{{ layer.name }}</span>
                            <span class="layer-desc">{{ layer.desc }}</span>
                        </div>
                        <div class="layer-right">
                            <el-tag :type="getDecisionType(result.layers[layer.key]?.decision)" size="small">
                                {{ getDecisionText(result.layers[layer.key]?.decision) }}
                            </el-tag>
                            <span class="layer-score">{{ (result.layers[layer.key]?.score * 100).toFixed(1) }}%</span>
                        </div>
                    </div>
                    <div v-if="result.layers[layer.key]?.time_ms" class="layer-time">
                        <el-icon>
                            <Timer />
                        </el-icon>
                        耗时: {{ result.layers[layer.key]?.time_ms.toFixed(1) }}ms
                    </div>
                    <el-progress v-if="result.layers[layer.key]?.score !== undefined"
                        :percentage="result.layers[layer.key]?.score * 100" :stroke-width="4" :show-text="false"
                        class="layer-progress" />
                </div>
            </div>

            <div v-if="result.total_time_ms" class="total-time">
                <el-icon>
                    <Stopwatch />
                </el-icon>
                总耗时: {{ result.total_time_ms.toFixed(1) }}ms
            </div>
        </div>

        <!-- 风险特征列表 -->
        <div v-if="features.length > 0" class="features-section">
            <div class="section-title">
                <el-icon>
                    <List />
                </el-icon>
                <span>检测到的风险特征</span>
            </div>

            <div class="feature-list">
                <div v-for="(feature, idx) in features" :key="idx" class="feature-item">
                    <div class="feature-header">
                        <span class="feature-name">{{ feature.name || feature.feature || '未知特征' }}</span>
                        <span class="feature-score" :class="feature.score > 0.5 ? 'text-danger' : 'text-success'">
                            {{ (feature.score * 100).toFixed(1) }}%
                        </span>
                    </div>
                    <el-progress :percentage="parseFloat((Math.abs(feature.score) * 100).toFixed(1))" :stroke-width="6"
                        :color="feature.score > 0.5 ? '#ef4444' : '#10b981'" :show-text="false" />
                    <div v-if="feature.description" class="feature-desc">
                        {{ feature.description }}
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
    result: any
}>()

const finalScore = computed(() => {
    return props.result?.final || props.result?.risk_score || 0
})

const scorePercent = computed(() => {
    return Math.round(finalScore.value * 100)
})

const isRisky = computed(() => {
    return finalScore.value >= 0.5
})

const riskText = computed(() => {
    const score = finalScore.value
    if (score >= 0.95) return '极高风险'
    if (score >= 0.8) return '高风险'
    if (score >= 0.5) return '中风险'
    if (score >= 0.3) return '低风险'
    return '安全'
})

const riskDesc = computed(() => {
    const score = finalScore.value
    if (score >= 0.95) return '确认钓鱼攻击特征，立即拦截！'
    if (score >= 0.8) return '多重钓鱼特征匹配，建议拦截'
    if (score >= 0.5) return '存在可疑特征，请谨慎访问'
    if (score >= 0.3) return '轻微异常或新域名'
    return '未检测到钓鱼特征'
})

const riskClass = computed(() => {
    const score = finalScore.value
    if (score >= 0.95) return 'risk-critical'
    if (score >= 0.8) return 'risk-high'
    if (score >= 0.5) return 'risk-medium'
    if (score >= 0.3) return 'risk-low'
    return 'risk-safe'
})

const progressColor = computed(() => {
    const score = finalScore.value
    if (score >= 0.8) return '#ef4444'
    if (score >= 0.5) return '#f59e0b'
    return '#10b981'
})

const features = computed(() => {
    return props.result?.features || []
})

const hasModel = (model: string) => {
    return props.result?.models?.[model] || props.result?.[model] !== undefined
}

const getModelScore = (model: string) => {
    return props.result?.models?.[model]?.score ?? props.result?.[model] ?? 0
}

const getScoreClass = (score: number) => {
    if (score >= 0.8) return 'text-danger'
    if (score >= 0.5) return 'text-warning'
    return 'text-success'
}

const getProgressColor = (score: number) => {
    if (score >= 0.8) return '#ef4444'
    if (score >= 0.5) return '#f59e0b'
    return '#10b981'
}

const layerConfigs = [
    { key: 'layer1', name: 'L1: 极速预筛', desc: 'URL字符串分析' },
    { key: 'layer2', name: 'L2: 协议探测', desc: 'HEAD请求+证书' },
    { key: 'layer3', name: 'L3: 语义分析', desc: '网页爬取+GTE' },
    { key: 'layer4', name: 'L4: 融合决策', desc: '动态权重融合' }
]

const getDecisionType = (decision: string) => {
    const types: Record<string, string> = {
        block: 'danger',
        pass: 'success',
        review: 'warning',
        observe: 'info',
        continue: ''
    }
    return types[decision] || 'info'
}

const getDecisionText = (decision: string) => {
    const texts: Record<string, string> = {
        block: '拦截',
        pass: '放行',
        review: '审核',
        observe: '观察',
        continue: '继续'
    }
    return texts[decision] || decision
}
</script>

<style lang="scss" scoped>
.phishing-result-detail {
    .result-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem 1.25rem;
        border-radius: 0.75rem;
        margin-bottom: 1.5rem;

        &.risk-safe {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05));
            border: 1px solid #10b981;
        }

        &.risk-low {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.05));
            border: 1px solid #3b82f6;
        }

        &.risk-medium {
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(217, 119, 6, 0.05));
            border: 1px solid #f59e0b;
        }

        &.risk-high,
        &.risk-critical {
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.05));
            border: 1px solid #ef4444;
        }

        .result-info {
            flex: 1;

            .result-title {
                font-size: 1.125rem;
                font-weight: 700;
                margin-bottom: 0.25rem;

                .risk-safe & {
                    color: #059669;
                }

                .risk-low & {
                    color: #2563eb;
                }

                .risk-medium & {
                    color: #d97706;
                }

                .risk-high &,
                .risk-critical & {
                    color: #dc2626;
                }
            }

            .result-subtitle {
                font-size: 0.75rem;
                color: #6b7280;
            }
        }
    }

    .section-title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
        color: #374151;
    }

    .model-scores {
        margin-bottom: 1rem;

        .model-grid {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;

            .model-item {
                .model-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 0.25rem;

                    .model-name {
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;
                        font-weight: 500;

                        .model-dot {
                            width: 8px;
                            height: 8px;
                            border-radius: 50%;

                            &.blue {
                                background: #3b82f6;
                            }

                            &.purple {
                                background: #8b5cf6;
                            }

                            &.orange {
                                background: #f59e0b;
                            }
                        }
                    }

                    .model-score {
                        font-family: monospace;
                        font-weight: 600;

                        &.text-danger {
                            color: #ef4444;
                        }

                        &.text-warning {
                            color: #f59e0b;
                        }

                        &.text-success {
                            color: #10b981;
                        }
                    }
                }
            }
        }
    }

    .layer-details {
        margin-bottom: 1rem;

        .layer-list {
            .layer-item {
                padding: 0.75rem;
                background: #f9fafb;
                border-radius: 0.5rem;
                margin-bottom: 0.5rem;

                .layer-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    flex-wrap: wrap;
                    gap: 0.5rem;
                    margin-bottom: 0.5rem;

                    .layer-name {
                        font-weight: 600;
                        font-size: 0.875rem;
                    }

                    .layer-desc {
                        font-size: 0.7rem;
                        color: #9ca3af;
                        margin-left: 0.5rem;
                    }

                    .layer-right {
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;

                        .layer-score {
                            font-family: monospace;
                            font-weight: 700;
                            font-size: 0.875rem;
                            color: #3b82f6;
                        }
                    }
                }

                .layer-time {
                    font-size: 0.7rem;
                    color: #9ca3af;
                    margin-bottom: 0.5rem;
                    display: flex;
                    align-items: center;
                    gap: 0.25rem;
                }

                .layer-progress {
                    margin-top: 0.5rem;
                }
            }
        }

        .total-time {
            margin-top: 0.75rem;
            padding: 0.5rem;
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.05));
            border-radius: 0.5rem;
            font-size: 0.875rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
    }

    .features-section {
        .feature-list {
            .feature-item {
                padding: 0.75rem;
                border-bottom: 1px solid #f0f0f0;

                &:last-child {
                    border-bottom: none;
                }

                .feature-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 0.5rem;

                    .feature-name {
                        font-size: 0.875rem;
                        font-weight: 500;
                    }

                    .feature-score {
                        font-family: monospace;
                        font-weight: 600;

                        &.text-danger {
                            color: #ef4444;
                        }

                        &.text-success {
                            color: #10b981;
                        }
                    }
                }

                .feature-desc {
                    margin-top: 0.5rem;
                    font-size: 0.7rem;
                    color: #9ca3af;
                }
            }
        }
    }
}
</style>