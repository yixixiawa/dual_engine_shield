<template>
    <el-card class="detection-panel" shadow="never">
        <div class="detection-header">
            <h2 class="panel-title">
                <el-icon>
                    <Search />
                </el-icon>
                URL 安全检测
            </h2>

            <div class="threshold-control">
                <span class="label">检测强度</span>
                <span class="strict">严格</span>
                <el-slider v-model="threshold" :min="30" :max="90" :step="5" :show-tooltip="false"
                    class="threshold-slider" />
                <span class="loose">宽松</span>
                <el-tag size="small" type="info" class="threshold-value">{{ threshold }}%</el-tag>
            </div>
        </div>

        <div class="input-area">
            <el-tabs v-model="activeTab">
                <el-tab-pane label="单URL检测">
                    <el-input v-model="url" placeholder="输入可疑网址，例如: https://portal.gdust.edu.cn 或 https://192.168.1.1.bank.com"
                        size="large" clearable @keyup.enter="detect">
                        <template #append>
                            <el-button type="primary" :loading="detectionStore.isLoading" @click="detect">
                                <el-icon>
                                    <Search />
                                </el-icon>
                                开始检测
                            </el-button>
                        </template>
                    </el-input>
                </el-tab-pane>
                <el-tab-pane label="多URL检测">
                    <el-input
                        v-model="urlsText"
                        type="textarea"
                        :rows="4"
                        placeholder="输入多个网址，每行一个，例如：
https://www.llojin-mettaamak-uk.godaddysites.com/
https://ze2413.craftum.io/"
                        size="large"
                    />
                    <div class="batch-actions">
                        <el-button type="primary" :loading="detectionStore.isLoading" @click="batchDetect">
                            <el-icon>
                                <Search />
                            </el-icon>
                            批量检测
                        </el-button>
                        <el-button @click="clearUrls">
                            <el-icon>
                                <Delete />
                            </el-icon>
                            清空
                        </el-button>
                    </div>
                </el-tab-pane>
            </el-tabs>
        </div>

        <div class="quick-tests">
            <span class="label">快速测试</span>
            <el-button size="small" type="success" plain @click="quickTest('https://portal.gdust.edu.cn')">
                教育网(应通过)
            </el-button>
            <el-button size="small" type="danger" plain @click="quickTest('https://paypa1.com/login')">
                仿冒PayPal(应拦截)
            </el-button>
            <el-button size="small" type="warning" plain @click="quickTest('https://192.168.1.1.bank.com')">
                IP混淆(应拦截)
            </el-button>
        </div>
    </el-card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useDetectionStore } from '@/stores/detection'

const detectionStore = useDetectionStore()
const url = ref('')
const urlsText = ref('')
const threshold = ref(detectionStore.threshold)
const activeTab = ref('0')

watch(threshold, (val) => {
    detectionStore.setThreshold(val)
})

const detect = () => {
    if (url.value.trim()) {
        emit('detect', url.value.trim())
    }
}

const batchDetect = () => {
    const urls = urlsText.value
        .split('\n')
        .map(url => url.trim())
        .filter(url => url)
    
    if (urls.length > 0) {
        emit('batchDetect', urls)
    }
}

const clearUrls = () => {
    urlsText.value = ''
}

const quickTest = (testUrl: string) => {
    url.value = testUrl
    activeTab.value = '0'
    detect()
}

const emit = defineEmits<{
    (e: 'detect', url: string): void
    (e: 'batchDetect', urls: string[]): void
}>()
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.detection-panel {
    @include app-card;

    .detection-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        flex-wrap: wrap;
        gap: $space-4;
        margin-bottom: $space-6;
    }

    .panel-title {
        display: flex;
        align-items: center;
        gap: $space-2;
        margin: 0;
        font-size: 1.25rem;
        font-weight: 700;
        color: $text-primary;
    }

    .threshold-control {
        display: grid;
        grid-template-columns: auto auto minmax(120px, 180px) auto auto;
        align-items: center;
        gap: $space-3;

        .label,
        .threshold-value {
            white-space: nowrap;
        }

        .label,
        .strict,
        .loose {
            font-size: 0.8125rem;
            color: $text-secondary;
        }

        .strict {
            color: $danger;
            font-weight: 600;
        }

        .loose {
            color: $success;
            font-weight: 600;
        }
    }

    .input-area {
        margin-bottom: $space-4;

        :deep(.el-input-group__append) {
            padding: 0;
        }

        :deep(.el-input-group__append .el-button) {
            min-width: 132px;
            border-top-left-radius: 0;
            border-bottom-left-radius: 0;
        }

        .batch-actions {
            margin-top: $space-3;
            display: flex;
            gap: $space-2;
        }
    }

    .quick-tests {
        display: flex;
        align-items: center;
        gap: $space-2;
        flex-wrap: wrap;

        .label {
            color: $text-secondary;
            font-size: 0.8125rem;
        }
    }
}

@media (max-width: $breakpoint-md) {
    .detection-panel {
        .threshold-control {
            grid-template-columns: 1fr;
            justify-items: start;
        }
    }
}
</style>