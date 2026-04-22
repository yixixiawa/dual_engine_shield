<template>
    <el-card class="model-detail-panel" shadow="never" body-class="detail-body">
        <template #header>
            <div class="detail-header">
                <el-icon>
                    <DataLine />
                </el-icon>
                <span>模型检测详情</span>
            </div>
        </template>

        <div class="model-scores">
            <div v-for="model in activeModels" :key="model.key" class="model-score-item">
                <div class="model-info">
                    <div :class="['model-dot', model.color]"></div>
                    <span class="model-name">{{ model.name }}</span>
                    <span class="model-score" :class="getScoreClass(model.score)">
                            {{ (model.score * 100).toFixed(2) }}%
                        </span>
                </div>
                <el-progress :percentage="model.score * 100" :color="getProgressColor(model.score, model.color)"
                    :stroke-width="8" :show-text="false" />
            </div>
        </div>

        <div v-if="result.layers" class="layer-details">
            <el-divider content-position="left">
                <el-icon>
                    <Connection />
                </el-icon>
                四层检测详情
            </el-divider>

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
                        <span class="layer-score">{{ (result.layers[layer.key]?.score * 100).toFixed(2) }}%</span>
                    </div>
                </div>
                <div class="layer-time" v-if="result.layers[layer.key]?.time_ms">
                    <el-icon>
                        <Timer />
                    </el-icon>
                    耗时: {{ result.layers[layer.key]?.time_ms.toFixed(1) }}ms
                </div>
            </div>

            <div class="total-time" v-if="result.total_time_ms">
                <el-icon>
                    <Stopwatch />
                </el-icon>
                总耗时: {{ result.total_time_ms.toFixed(1) }}ms
            </div>
        </div>
    </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
    result: any
    threshold: number
}>()

const activeModels = computed(() => {
    const models = []
    
    // 显示原始模型
    if (props.result.scores_per_model?.original !== undefined) {
        models.push({
            key: 'original',
            name: 'GTE 原始模型',
            color: 'purple',
            score: props.result.scores_per_model.original
        })
    }
    
    // 显示ChiPhish模型
    if (props.result.scores_per_model?.chiphish !== undefined) {
        models.push({
            key: 'chiphish',
            name: 'GTE ChiPhish模型',
            color: 'cyan',
            score: props.result.scores_per_model.chiphish
        })
    }
    
    // 如果没有scores_per_model，使用score作为fallback
    if (models.length === 0 && props.result.score !== undefined) {
        models.push({
            key: 'gte',
            name: 'GTE 深度语义检测',
            color: 'purple',
            score: props.result.score
        })
    }
    
    return models
})

const layerConfigs = [
    { key: 'layer1', name: 'L1: 极速预筛', desc: 'URL字符串分析' },
    { key: 'layer2', name: 'L2: 协议探测', desc: 'HEAD请求+证书' },
    { key: 'layer3', name: 'L3: 语义分析', desc: '网页爬取+GTE' },
    { key: 'layer4', name: 'L4: 融合决策', desc: '动态权重融合' }
]

const getScoreClass = (score: number) => {
    if (score > props.threshold / 100) return 'text-danger'
    return 'text-primary'
}

const getProgressColor = (_score: number, color: string) => {
    const colors: Record<string, string> = {
        blue: '#3b82f6',
        purple: '#8b5cf6',
        orange: '#f59e0b'
    }
    return colors[color] || '#3b82f6'
}

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
.model-detail-panel {
    width: 320px;
    background: rgba(255, 255, 255, 0.5);

    :deep(.detail-body) {
        padding: 1rem;
    }

    .detail-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.75rem;
        font-weight: 600;
        color: #6b7280;
        text-transform: uppercase;
    }
}

.model-scores {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    margin-bottom: 1rem;

    .model-score-item {
        .model-info {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.5rem;

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

            .model-name {
                font-size: 0.875rem;
                font-weight: 500;
                color: #374151;
            }

            .model-score {
                margin-left: auto;
                font-size: 0.875rem;
                font-family: monospace;
                font-weight: 700;

                &.text-danger {
                    color: #ef4444;
                }

                &.text-primary {
                    color: #3b82f6;
                }
            }
        }
    }
}

.layer-details {
    .layer-item {
        padding: 0.75rem;
        background: #f9fafb;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;

        .layer-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;

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
            margin-top: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.25rem;
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
</style>