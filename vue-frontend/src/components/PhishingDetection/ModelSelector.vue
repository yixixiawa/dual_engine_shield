<template>
    <el-card class="model-selector" shadow="hover" body-class="model-card-body">
        <template #header>
            <div class="card-header">
                <el-icon>
                    <Setting />
                </el-icon>
                <span>选择检测模型</span>
            </div>
        </template>

        <div class="model-grid">
            <div v-for="model in models" :key="model.id" class="model-item"
                :class="{ active: detectionStore.currentModel === model.id }" @click="selectModel(model.id)">
                <div class="model-header">
                    <span class="model-name">{{ model.name }}</span>
                    <el-tag :type="model.tagType" size="small">{{ model.size }}</el-tag>
                </div>
                <p class="model-desc">{{ model.desc }}</p>
                <div class="model-metrics">
                    <span class="metric">{{ model.metric }}</span>
                </div>
            </div>

            <div class="model-item deep-model" @click="selectModel('deep')">
                <div class="model-header">
                    <span class="model-name">🔍 深度综合检测</span>
                    <el-tag type="danger" size="small" effect="dark">推荐</el-tag>
                </div>
                <p class="model-desc">三模型融合投票 + 网页抓取分析</p>
            </div>
        </div>
    </el-card>
</template>

<script setup lang="ts">
import { useDetectionStore } from '@/stores/detection'

const detectionStore = useDetectionStore()

const models: Array<{ id: 'svm' | 'gte' | 'ngram'; name: string; size: string; desc: string; metric: string; tagType: 'info' | 'primary' | 'warning' }> = [
    { id: 'svm', name: 'SVM', size: '1.62MB', desc: '传统特征工程模型', metric: '94.21% G-mean', tagType: 'info' },
    { id: 'gte', name: 'GTE', size: '417MB', desc: '深度语义理解模型', metric: '98.95% G-mean', tagType: 'primary' },
    { id: 'ngram', name: 'N-gram', size: '36MB', desc: '神经网络序列模型', metric: '96% 准确率', tagType: 'warning' }
]

const selectModel = (model: 'svm' | 'gte' | 'ngram' | 'deep') => {
    detectionStore.selectModel(model)
}
</script>

<style lang="scss" scoped>
.model-selector {
    margin-bottom: 1.5rem;
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.8);

    :deep(.el-card__header) {
        border-bottom: 1px solid rgba(0, 0, 0, 0.05);
        padding: 1rem;

        .card-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 500;
        }
    }
}

.model-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
}

.model-item {
    padding: 1rem;
    border-radius: 0.75rem;
    border: 2px solid rgba(59, 130, 246, 0.15);
    background: rgba(255, 255, 255, 0.6);
    cursor: pointer;
    transition: all 0.3s ease;

    &:hover {
        border-color: rgba(59, 130, 246, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 12px 24px -8px rgba(59, 130, 246, 0.2);
    }

    &.active {
        border-color: #3b82f6;
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.05));
        position: relative;

        &::after {
            content: '✓';
            position: absolute;
            top: 8px;
            right: 8px;
            width: 20px;
            height: 20px;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
        }
    }

    .model-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;

        .model-name {
            font-size: 1.125rem;
            font-weight: 700;
        }
    }

    .model-desc {
        font-size: 0.75rem;
        color: #6b7280;
        margin-bottom: 0.5rem;
    }

    .model-metrics {
        .metric {
            font-size: 0.7rem;
            color: #3b82f6;
            font-weight: 600;
        }
    }
}

.deep-model {
    grid-column: span 1;
    border-style: dashed;

    &:hover {
        border-color: #8b5cf6;
    }
}
</style>