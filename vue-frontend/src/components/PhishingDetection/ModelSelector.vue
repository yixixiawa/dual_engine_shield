<template>
    <el-card class="model-info-card" shadow="never" body-class="model-card-body">
        <template #header>
            <div class="card-header">
                <el-icon>
                    <Setting />
                </el-icon>
                <span>GTE 深度语义检测模型</span>
                <el-tag type="primary" effect="plain" class="active-tag">活跃</el-tag>
            </div>
        </template>

        <div class="model-detail">
            <div class="model-info-row">
                <span class="label">模型类型：</span>
                <span class="value">GTE (Generalized Text Embeddings)</span>
            </div>
            <div class="model-info-row">
                <span class="label">模型大小：</span>
                <span class="value">417MB</span>
            </div>
            <div class="model-info-row">
                <span class="label">描述：</span>
                <span class="value">基于深度学习的语义向量空间距离计算，通过网页内容语义分析进行钓鱼检测</span>
            </div>
            <div class="model-info-row">
                <span class="label">性能指标：</span>
                <span class="value">98.95% G-mean</span>
            </div>
            <div class="model-info-row">
                <span class="label">工作模式：</span>
                <span class="value">URL解析 → 网页爬取 → 语义编码 → 相似度匹配 → 风险评估</span>
            </div>
        </div>
    </el-card>
</template>

<script setup lang="ts">
// GTE模型已自动激活，无需选择
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.model-info-card {
    @include app-card;

    :deep(.el-card__header) {
        padding: $space-4 $space-5;
    }

    :deep(.model-card-body) {
        padding: $space-5;
    }

    .card-header {
        @include app-card-header;

        .active-tag {
            margin-left: auto;
        }
    }
}

.model-detail {
    display: flex;
    flex-direction: column;
    gap: $space-3;

    .model-info-row {
        display: flex;
        gap: $space-4;
        padding: $space-4;
        background: $surface-muted;
        border: 1px solid rgba(24, 144, 255, 0.08);
        border-radius: $radius-md;

        .label {
            min-width: 120px;
            font-weight: 600;
            color: $primary-active;
        }

        .value {
            flex: 1;
            color: $text-secondary;
            line-height: 1.6;
        }
    }
}

@media (max-width: $breakpoint-sm) {
    .model-detail {
        .model-info-row {
            flex-direction: column;
            gap: $space-2;

            .label {
                min-width: 0;
            }
        }
    }
}
</style>
