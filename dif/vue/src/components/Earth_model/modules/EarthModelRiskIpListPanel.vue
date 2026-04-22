<template>
    <el-card shadow="hover" class="ip-list-card">
        <template #header>
            <div class="card-header">
                <span class="title">
                    <el-icon color="#F56C6C"><Warning /></el-icon>
                    <span>钓鱼 IP 地址列表</span>
                </span>
                <div class="header-actions">
                    <el-input
                        :model-value="urlSearchKeyword"
                        placeholder="搜索 IP 地址..."
                        clearable
                        style="width: 240px"
                        size="default"
                        @update:model-value="emit('update:urlSearchKeyword', $event)"
                    >
                        <template #prefix>
                            <el-icon><Search /></el-icon>
                        </template>
                    </el-input>
                    <el-button @click="emit('refresh')" :loading="urlsLoading" type="primary" plain>
                        <el-icon><Refresh /></el-icon>
                        刷新
                    </el-button>
                    <el-button type="warning" plain @click="emit('highlight-test')" :loading="globeLoading">
                        <el-icon><Warning /></el-icon>
                        测试高亮IP
                    </el-button>
                    <el-button type="danger" plain @click="emit('clear-highlights')" :loading="globeLoading">
                        <el-icon><Delete /></el-icon>
                        清除高亮
                    </el-button>
                </div>
            </div>
        </template>

        <div v-if="urlsLoading" class="loading-container">
            <el-skeleton :rows="5" animated />
        </div>

        <el-table
            v-else-if="displayUrls.length > 0"
            :data="displayUrls"
            stripe
            height="400"
            :default-sort="{ prop: 'risk_score', order: 'descending' }"
            style="width: 100%"
            @row-click="(row) => {
                $emit('view-detail', row)
                $emit('highlight', row)
            }"
        >
            <el-table-column type="expand">
                <template #default="{ row }">
                    <div class="expand-detail">
                        <el-descriptions :column="2" border size="small">
                            <el-descriptions-item label="IP 地址">
                                <el-tag type="info" size="small">{{ row.ip_address }}</el-tag>
                            </el-descriptions-item>
                            <el-descriptions-item label="所属域名">
                                {{ row.domain || '-' }}
                            </el-descriptions-item>
                            <el-descriptions-item label="地理位置">
                                <el-tag :type="row.city ? 'success' : 'info'" size="small">
                                    {{ row.city || '未知' }}, {{ row.country || '未知' }}
                                </el-tag>
                            </el-descriptions-item>
                            <el-descriptions-item label="经纬度">
                                {{ row.latitude ?? '-' }}, {{ row.longitude ?? '-' }}
                            </el-descriptions-item>
                            <el-descriptions-item label="查询次数">
                                {{ row.query_count ?? 0 }} 次
                            </el-descriptions-item>
                            <el-descriptions-item label="状态">
                                {{ row.status || '-' }}
                            </el-descriptions-item>
                            <el-descriptions-item label="最后发现" :span="2">
                                {{ formatDate(row.last_seen || undefined) }}
                            </el-descriptions-item>
                        </el-descriptions>
                    </div>
                </template>
            </el-table-column>

            <el-table-column prop="ip_address" label="IP 地址" width="140" show-overflow-tooltip>
                <template #default="{ row }">
                    <span class="ip-address">{{ row.ip_address }}</span>
                </template>
            </el-table-column>

            <el-table-column label="威胁等级" width="100" align="center">
                <template #default="{ row }">
                    <el-tag :type="getRiskType(row.threat_level)" size="small" effect="dark">
                        {{ getThreatLevelText(row.threat_level) }}
                    </el-tag>
                </template>
            </el-table-column>

            <el-table-column label="风险等级" width="100" align="center">
                <template #default="{ row }">
                    <el-tag :type="getRiskTypeByScore(row.risk_score || 0)" size="small" effect="dark">
                        {{ getRiskLevelByScore(row.risk_score || 0) }}
                    </el-tag>
                </template>
            </el-table-column>

            <el-table-column label="风险评分" width="140">
                <template #default="{ row }">
                    <div class="score-cell">
                        <el-progress
                            :percentage="Math.round(row.risk_score || 0)"
                            :color="getScoreColor((row.risk_score || 0) / 100)"
                            :stroke-width="8"
                            :show-text="false"
                        />
                        <span class="score-text">{{ (row.risk_score || 0).toFixed(1) }}分</span>
                    </div>
                </template>
            </el-table-column>

            <el-table-column prop="country" label="国家" width="100">
                <template #default="{ row }">
                    <div class="country-cell">
                        <span>{{ row.country || '未知' }}</span>
                    </div>
                </template>
            </el-table-column>

            <el-table-column prop="city" label="城市" width="120">
                <template #default="{ row }">
                    <span>{{ row.city || '未知' }}</span>
                </template>
            </el-table-column>

            <el-table-column prop="status" label="状态" width="110">
                <template #default="{ row }">
                    <span>{{ row.status || '-' }}</span>
                </template>
            </el-table-column>

            <el-table-column prop="last_seen" label="最后发现" width="170" sortable>
                <template #default="{ row }">
                    <span class="time-text">{{ formatDate(row.last_seen || undefined) }}</span>
                </template>
            </el-table-column>

            <el-table-column label="操作" width="80" fixed="right" align="center">
                <template #default="{ row }">
                    <el-button link type="primary" size="small" @click="emit('view-detail', row)">
                        详情
                    </el-button>
                </template>
            </el-table-column>
        </el-table>

        <div v-else class="empty-container">
            <el-empty description="暂无钓鱼 IP 记录">
                <template #image>
                    <el-icon :size="80" color="#909399"><Warning /></el-icon>
                </template>
                <el-button type="primary" @click="emit('refresh')" :loading="urlsLoading">
                    刷新数据
                </el-button>
            </el-empty>
        </div>
    </el-card>
</template>

<script setup lang="ts">
import { Delete, Refresh, Search, Warning } from '@element-plus/icons-vue'
import { computed, watch } from 'vue'
import type { GeoPhishingLocationEntity } from '@/api/modules/geoPhishingLocations'

const props = defineProps<{
    urlSearchKeyword: string
    urlsLoading: boolean
    globeLoading: boolean
    filteredPhishingUrls: GeoPhishingLocationEntity[]
    getRiskType: (riskLevel: string) => string
    getThreatLevelText: (level: string) => string
    getScoreColor: (score: number) => string
    getRiskLevelByScore: (score: number) => string
    getRiskTypeByScore: (score: number) => string
    formatDate: (dateStr?: string) => string
}>()

const emit = defineEmits<{
    (e: 'update:urlSearchKeyword', value: string): void
    (e: 'refresh'): void
    (e: 'clear-highlights'): void
    (e: 'highlight-test'): void
    (e: 'view-detail', row: GeoPhishingLocationEntity): void
    (e: 'highlight', location: GeoPhishingLocationEntity): void
}>()

const displayUrls = computed(() => {
    return props.filteredPhishingUrls || []
})
</script>

<style scoped lang="scss">
.ip-list-card {
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);

    :deep(.el-card__header) {
        padding: 16px 20px;
        border-bottom: 1px solid #e4e7ed;
        background: #fafafa;
    }

    .card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        width: 100%;

        .title {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 16px;
            font-weight: 600;
            color: #303133;

            .el-icon {
                font-size: 18px;
            }
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }
    }
}

.loading-container {
    padding: 40px;
    text-align: center;
}

.empty-container {
    padding: 60px 20px;
    text-align: center;
}

.expand-detail {
    padding: 16px 20px;
    background: #f8f9fa;
    border-radius: 8px;
}

.score-cell {
    display: flex;
    align-items: center;
    gap: 8px;

    .score-text {
        font-size: 12px;
        font-weight: 500;
        color: #606266;
        min-width: 45px;
    }
}

.ip-address {
    font-family: 'Courier New', monospace;
    font-weight: 500;
    color: #409EFF;
}

.country-cell {
    display: flex;
    align-items: center;
    gap: 4px;
}

.time-text {
    font-size: 12px;
    color: #909399;
}

:deep(.el-table) {
    font-size: 13px;

    .el-table__header th {
        background: #f5f7fa;
        color: #606266;
        font-weight: 600;
    }

    .el-table__row:hover {
        background: #f5f7fa;
    }
}

@media (max-width: 768px) {
    .ip-list-card .card-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 12px;

        .header-actions {
            width: 100%;
            flex-wrap: wrap;
        }
    }
}
</style>
