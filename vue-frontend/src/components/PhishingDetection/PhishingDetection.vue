<template>
    <div class="phishing-detection">
        <div class="header-actions">
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

        <ModelSelector />

        <DetectionPanel @detect="handleDetect" />

        <ResultPanel v-if="detectionStore.currentResult" :result="detectionStore.currentResult"
            :model="detectionStore.currentModel" :threshold="detectionStore.threshold" />

        <HistoryTable :history="detectionStore.history" />
    </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useDetectionStore } from '@/stores/detection'
import { useWhitelistStore } from '@/stores/whitelist'
import ModelSelector from './ModelSelector.vue'
import DetectionPanel from './DetectionPanel.vue'
import ResultPanel from './ResultPanel.vue'
import HistoryTable from './HistoryTable.vue'

const detectionStore = useDetectionStore()
const whitelistStore = useWhitelistStore()

const currentModelName = computed(() => {
    return 'GTE 深度语义检测'
})

const toggleWhitelistPanel = () => {
    whitelistStore.togglePanel()
}

const handleDetect = (url: string) => {
    detectionStore.detectPhishing(url)
}
</script>

<style lang="scss" scoped>
.phishing-detection {
    max-width: 1280px;
    margin: 0 auto;

    .header-actions {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;

        .status-tag {
            padding: 0.5rem 1rem;
            border-radius: 9999px;
        }
    }
}
</style>