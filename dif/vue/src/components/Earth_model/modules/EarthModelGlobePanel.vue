<template>
    <div class="middle-section">
        <div class="globe-wrapper">
            <div v-if="loading" class="loading-container">
                <el-skeleton :rows="1" animated style="width: 100%; height: 100%" />
                <div class="loading-text">加载地球模型中...</div>
            </div>
            <div v-else class="earth" id="globeContainer"></div>
            <div class="mode-indicator">当前模式：{{ displayMode === '3d' ? '3D 地球' : '2D 平面图' }}</div>
        </div>
    </div>
</template>

<script setup lang="ts">
defineProps<{
    displayMode: '2d' | '3d'
    loading?: boolean
}>()
</script>

<style scoped lang="scss">
.middle-section {
    width: 100%;

    .globe-wrapper {
        position: relative;
        width: 100%;
        height: 550px;
        background: white;
        border-radius: 16px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        overflow: hidden;

        .earth {
            width: 100%;
            height: 100%;
        }

        .mode-indicator {
            position: absolute;
            top: 16px;
            right: 16px;
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.9);
            color: #606266;
            font-size: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            pointer-events: none;
        }

        .loading-container {
            position: relative;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background: #f5f7fa;
        }

        .loading-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #606266;
            font-size: 14px;
            margin-top: 40px;
        }
    }
}

@media (max-width: 768px) {
    .middle-section .globe-wrapper {
        height: 350px;
    }
}
</style>
