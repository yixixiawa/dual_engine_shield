<template>
    <el-card class="feature-list-card" shadow="hover">
        <template #header>
            <div class="card-header">
                <el-icon>
                    <Warning />
                </el-icon>
                <span>检测到的风险特征</span>
                <span class="header-hint">(置信度/贡献度)</span>
            </div>
        </template>

        <div v-if="features.length === 0" class="empty-state">
            <el-empty description="等待检测数据..." :image-size="80" />
        </div>

        <div v-else class="feature-list">
            <div v-for="(feature, index) in features" :key="index" class="feature-item"
                :style="{ animationDelay: `${index * 0.05}s` }">
                <div class="feature-header">
                    <div class="feature-info">
                        <span class="feature-name">{{ feature.name || feature.feature || '未知特征' }}</span>
                        <el-tag :type="getFeatureTagType(feature.score)" size="small">
                            {{ feature.score > 0 ? '+' : '' }}{{ (feature.score * 100).toFixed(0) }}%
                        </el-tag>
                    </div>
                    <div class="feature-icon">
                        {{ finalScore >= 0.8 ? '⚠️' : (feature.score > 0.5 ? '⚠️' : '✓') }}
                    </div>
                </div>

                <el-progress :percentage="Math.min(Math.abs(feature.score) * 100, 100)" :stroke-width="8"
                    :color="getFeatureColor(feature.score)" :show-text="false" />

                <div v-if="feature.description" class="feature-desc">
                    {{ feature.description }}
                </div>
            </div>
        </div>
    </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
    features: Array<{
        name?: string
        feature?: string
        score: number
        description?: string
    }>
    finalScore?: number // 最终风险分数
}>()

// 根据最终风险等级决定特征颜色
const getFeatureColor = (score: number) => {
    const finalScore = props.finalScore || 0
    // 如果整体是高风险，所有特征都显示为红色
    if (finalScore >= 0.8) {
        return '#ef4444'
    }
    // 中风险
    if (finalScore >= 0.5) {
        return score > 0.5 ? '#ef4444' : '#f59e0b'
    }
    // 低风险或安全
    return score > 0.5 ? '#ef4444' : '#10b981'
}

const getFeatureTagType = (score: number) => {
    const finalScore = props.finalScore || 0
    // 如果整体是高风险，所有特征都显示为危险色
    if (finalScore >= 0.8) {
        return 'danger'
    }
    // 中风险
    if (finalScore >= 0.5) {
        return score > 0.5 ? 'danger' : 'warning'
    }
    // 低风险或安全
    return score > 0.5 ? 'danger' : 'success'
}
</script>

<style lang="scss" scoped>
.feature-list-card {
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(16px);
    margin-bottom: 1rem;

    .card-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-weight: 500;

        .header-hint {
            font-size: 0.7rem;
            color: #9ca3af;
            font-weight: normal;
        }
    }

    .empty-state {
        padding: 1rem;
    }

    .feature-list {
        .feature-item {
            padding: 0.75rem;
            border-bottom: 1px solid #f0f0f0;
            animation: fadeIn 0.3s ease-out forwards;

            &:last-child {
                border-bottom: none;
            }

            .feature-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 0.5rem;

                .feature-info {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    flex-wrap: wrap;

                    .feature-name {
                        font-size: 0.875rem;
                        font-weight: 500;
                        color: #374151;
                    }
                }

                .feature-icon {
                    font-size: 1.125rem;
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

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateX(-10px);
    }

    to {
        opacity: 1;
        transform: translateX(0);
    }
}
</style>