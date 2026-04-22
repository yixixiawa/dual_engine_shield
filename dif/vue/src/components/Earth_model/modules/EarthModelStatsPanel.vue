<template>
    <div class="top-section">
        <div class="mode-switcher">
            <el-segmented
                :model-value="displayMode"
                :options="modeOptions"
                @update:model-value="emit('update:displayMode', $event as '2d' | '3d')"
            />
        </div>

        <el-row :gutter="20" class="stats-row">
            <el-col :xs="24" :sm="12" :md="6">
                <el-statistic title="钓鱼 IP 数量" :value="stats.phishingUrlsCount" size="large">
                    <template #prefix>
                        <el-icon style="color: #F56C6C"><Warning /></el-icon>
                    </template>
                </el-statistic>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
                <el-statistic title="已检测 IP" :value="stats.detectedCount" size="large">
                    <template #prefix>
                        <el-icon style="color: #409EFF"><Search /></el-icon>
                    </template>
                </el-statistic>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
                <el-statistic title="平均风险分" :value="stats.avgRiskScore" suffix="分" size="large">
                    <template #prefix>
                        <el-icon style="color: #E6A23C"><Timer /></el-icon>
                    </template>
                </el-statistic>
            </el-col>
            <el-col :xs="24" :sm="12" :md="6">
                <el-statistic title="高危 IP" :value="stats.highRiskCount" size="large">
                    <template #prefix>
                        <el-icon style="color: #F56C6C"><Warning /></el-icon>
                    </template>
                </el-statistic>
            </el-col>
        </el-row>
    </div>
</template>

<script setup lang="ts">
import { Warning, Search, Timer } from '@element-plus/icons-vue'

const modeOptions = [
    { label: '3D 地球模型', value: '3d' },
    { label: '2D 平面图', value: '2d' }
] as const

defineProps<{
    displayMode: '2d' | '3d'
    stats: {
        phishingUrlsCount: number
        detectedCount: number
        avgRiskScore: number
        highRiskCount: number
    }
}>()

const emit = defineEmits<{
    (e: 'update:displayMode', value: '2d' | '3d'): void
}>()
</script>

<style scoped lang="scss">
.top-section {
    display: flex;
    flex-direction: column;
    gap: 16px;

    .mode-switcher {
        display: flex;
        justify-content: center;
        padding: 8px 0;

        :deep(.el-segmented) {
            background: white;
            border-radius: 12px;
            padding: 4px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        }
    }

    .stats-row {
        width: 100%;
        margin: 0 !important;

        .el-col {
            margin-bottom: 0;
        }

        :deep(.el-statistic) {
            background: white;
            padding: 16px 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            transition: all 0.3s ease;

            &:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
            }

            .el-statistic__head {
                font-size: 14px;
                color: #606266;
            }

            .el-statistic__number {
                font-size: 28px;
                font-weight: 600;
            }
        }
    }
}
</style>
