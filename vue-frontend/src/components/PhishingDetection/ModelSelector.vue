<template>
    <el-card class="model-info-card" shadow="hover" body-class="model-card-body">
        <template #header>
            <div class="card-header">
                <el-icon>
                    <Setting />
                </el-icon>
                <span>GTE 深度语义检测模型</span>
                <el-tag type="primary" effect="dark" style="margin-left: auto;">活跃</el-tag>
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
.model-info-card {
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

.model-detail {
    display: flex;
    flex-direction: column;
    gap: 1rem;

    .model-info-row {
        display: flex;
        gap: 1rem;
        padding: 0.75rem;
        background: rgba(59, 130, 246, 0.05);
        border-radius: 0.5rem;

        .label {
            font-weight: 600;
            color: #3b82f6;
            min-width: 120px;
        }

        .value {
            color: #6b7280;
            flex: 1;
        }
    }
}
</style>