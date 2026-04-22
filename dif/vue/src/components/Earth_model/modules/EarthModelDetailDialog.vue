<template>
    <el-dialog :model-value="modelValue" title="钓鱼 IP 详情" width="650px" destroy-on-close @update:model-value="emit('update:modelValue', $event)">
        <div v-if="selectedUrl" class="detail-content">
            <el-descriptions :column="2" border>
                <el-descriptions-item label="IP 地址" :span="2">
                    <el-tag type="danger" size="large">{{ selectedUrl.ip_address }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="所属域名">
                    {{ selectedUrl.domain || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="威胁等级">
                    <el-tag :type="getRiskType(selectedUrl.threat_level)">
                        {{ getThreatLevelText(selectedUrl.threat_level) }}
                    </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="风险评分" :span="2">
                    <el-progress
                        :percentage="Math.round((selectedUrl.risk_score || 0) * 100)"
                        :color="getScoreColor(selectedUrl.risk_score || 0)"
                        :stroke-width="14"
                    />
                </el-descriptions-item>
                <el-descriptions-item label="地理位置">
                    {{ selectedUrl.city || '未知' }}, {{ selectedUrl.country || '未知' }}
                </el-descriptions-item>
                <el-descriptions-item label="经纬度">
                    {{ selectedUrl.latitude ?? '-' }}, {{ selectedUrl.longitude ?? '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="是否钓鱼">
                    {{ selectedUrl.is_phishing ? '是' : '否' }}
                </el-descriptions-item>
                <el-descriptions-item label="状态">
                    {{ selectedUrl.status || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="查询次数">
                    {{ selectedUrl.query_count ?? 0 }} 次
                </el-descriptions-item>
                <el-descriptions-item label="最后发现">
                    {{ formatDate(selectedUrl.last_seen || undefined) }}
                </el-descriptions-item>
            </el-descriptions>
        </div>
        <template #footer>
            <el-button @click="emit('update:modelValue', false)">关闭</el-button>
            <el-button type="primary" @click="emit('locate', selectedUrl)" v-if="selectedUrl">
                在地球上定位
            </el-button>
        </template>
    </el-dialog>
</template>

<script setup lang="ts">
import type { GeoPhishingLocationEntity } from '@/api/modules/geoPhishingLocations'

defineProps<{
    modelValue: boolean
    selectedUrl: GeoPhishingLocationEntity | null
    formatDate: (dateStr?: string) => string
    getRiskType: (riskLevel: string) => string
    getThreatLevelText: (level: string) => string
    getScoreColor: (score: number) => string
}>()

const emit = defineEmits<{
    (e: 'update:modelValue', value: boolean): void
    (e: 'locate', location: GeoPhishingLocationEntity | null): void
}>()
</script>

<style scoped lang="scss">
.detail-content {
    padding: 8px 0;

    :deep(.el-descriptions) {
        .el-descriptions__label {
            width: 100px;
            background: #f8f9fa;
        }
    }
}
</style>
