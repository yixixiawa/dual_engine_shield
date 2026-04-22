<template>
    <div class="phishing-detection page-shell">
        <section class="page-header">
            <div>
                <h1 class="page-header__title">钓鱼检测</h1>
                <p class="page-header__desc">输入可疑网址并查看风险评分、模型输出和历史检测记录。</p>
            </div>
            <div class="page-actions">
                <el-tag type="success" effect="plain" class="status-tag">
                    <el-icon>
                        <Check />
                    </el-icon>
                    {{ currentModelName }} 模式就绪
                </el-tag>
                <el-button @click="toggleWhitelistPanel" text>
                    <el-icon>
                        <Star />
                    </el-icon>
                    白名单管理
                </el-button>
            </div>
        </section>

        <ModelSelector />

        <DetectionPanel @detect="handleDetect" @batchDetect="handleBatchDetect" />

        <el-card v-if="normalizedResult && !batchResult" class="result-section" shadow="never">
            <template #header>
                <div class="section-title">
                    <el-icon>
                        <DataAnalysis />
                    </el-icon>
                    <span>检测结果</span>
                </div>
            </template>
            <PhishingResultDetail :result="normalizedResult" />
        </el-card>

        <el-card v-if="batchResult" class="result-section" shadow="never">
            <template #header>
                <div class="section-title">
                    <el-icon>
                        <DataAnalysis />
                    </el-icon>
                    <span>批量检测结果</span>
                    <el-tag size="small" type="info" class="batch-stats">
                        共 {{ batchResult.total_urls }} 个URL，{{ batchResult.phishing_count }} 个钓鱼网站
                    </el-tag>
                </div>
            </template>
            <el-table :data="batchResult.results" style="width: 100%">
                <el-table-column prop="url" label="URL" min-width="300">
                    <template #default="scope">
                        <a :href="scope.row.url" target="_blank" rel="noopener noreferrer" class="url-link">
                            {{ scope.row.url }}
                        </a>
                    </template>
                </el-table-column>
                <el-table-column prop="is_phishing" label="是否钓鱼" width="120">
                    <template #default="scope">
                        <el-tag :type="scope.row.is_phishing ? 'danger' : 'success'">
                            {{ scope.row.is_phishing ? '是' : '否' }}
                        </el-tag>
                    </template>
                </el-table-column>
                <el-table-column prop="score" label="风险评分" width="120">
                    <template #default="scope">
                        <div class="score-container">
                            <el-progress 
                                :percentage="Math.round(scope.row.score * 100)" 
                                :color="getScoreColor(scope.row.score)"
                                :stroke-width="10"
                                :show-text="false"
                            />
                            <span class="score-text">{{ (scope.row.score * 100).toFixed(1) }}%</span>
                        </div>
                    </template>
                </el-table-column>
                <el-table-column prop="latency_ms" label="检测时间(ms)" width="120">
                    <template #default="scope">
                        {{ scope.row.latency_ms.toFixed(2) }}
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="120">
                    <template #default="scope">
                        <el-button size="small" type="primary" @click="viewDetails(scope.row)">
                            查看详情
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-card>

        <HistoryTable :history="detectionStore.history" @clear="clearHistory" />
    </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useDetectionStore } from '@/stores/detection'
import { useWhitelistStore } from '@/stores/whitelist'
import type { PhishingTrackResponse, BatchPhishingDetectResponse, PhishingDetectResponse } from '@/api/modules/phishing'
import ModelSelector from './ModelSelector.vue'
import DetectionPanel from './DetectionPanel.vue'
import HistoryTable from './HistoryTable.vue'
import PhishingResultDetail from '../common/PhishingResultDetail.vue'

const detectionStore = useDetectionStore()
const whitelistStore = useWhitelistStore()
const batchResult = ref<BatchPhishingDetectResponse | null>(null)

const currentModelName = computed(() => 'GTE 深度语义检测')

const normalizedResult = computed(() => {
    const result = detectionStore.currentResult as PhishingTrackResponse | null
    const detection = result?.phishing_detection

    if (!result || !detection) return null

    return {
        ...detection,
        is_phishing: result.is_phishing,
        message: result.message,
        domain_resolution: result.domain_resolution,
        ipinfo: result.ipinfo,
        geolocation_sync: result.geolocation_sync,
        risk_score: Number(detection.score) || 0,
        final: Number(detection.score) || 0,
        total_time_ms: detection.latency_ms,
        models: {
            gte: {
                score: Number(detection.score) || 0
            },
            original: {
                score: Number(detection.scores_per_model?.original) || 0
            },
            chiphish: {
                score: Number(detection.scores_per_model?.chiphish) || 0
            }
        },
        features: detection.token_attribution?.map(item => ({
            name: item.token,
            score: Math.abs(item.score),
            description: `贡献分数 ${item.score.toFixed(4)}`
        })) ?? []
    }
})

const toggleWhitelistPanel = () => {
    whitelistStore.togglePanel()
}

const handleDetect = (url: string) => {
    batchResult.value = null
    detectionStore.detectPhishing(url)
}

const handleBatchDetect = async (urls: string[]) => {
    try {
        const result = await detectionStore.batchDetectPhishing(urls)
        batchResult.value = result
    } catch (error) {
        console.error('批量检测失败:', error)
    }
}

const clearHistory = () => {
    detectionStore.clearHistory()
}

const getScoreColor = (score: number) => {
    if (score >= 0.7) return '#F56C6C'
    if (score >= 0.4) return '#E6A23C'
    return '#67C23A'
}

const viewDetails = (result: PhishingDetectResponse) => {
    // 这里可以实现查看详细信息的逻辑
    // 例如打开一个对话框显示详细信息
    console.log('查看详情:', result)
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.phishing-detection {
    .status-tag {
        padding: 0.5rem 0.875rem;
        border-radius: 999px;
    }

    .result-section {
        @include app-card;

        .section-title {
            display: flex;
            align-items: center;
            gap: $space-2;

            .batch-stats {
                margin-left: auto;
            }
        }

        .url-link {
            color: $primary;
            text-decoration: none;
            word-break: break-all;

            &:hover {
                text-decoration: underline;
            }
        }

        .score-container {
            position: relative;
            width: 100%;
            height: 20px;

            .score-text {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                text-align: center;
                font-size: 0.75rem;
                line-height: 20px;
            }
        }
    }
}
</style>

