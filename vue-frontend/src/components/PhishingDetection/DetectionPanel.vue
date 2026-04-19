<template>
    <el-card class="detection-panel" shadow="hover">
        <div class="detection-header">
            <h2>
                <el-icon>
                    <Search />
                </el-icon>
                URL 安全检测
            </h2>

            <div class="threshold-control">
                <span class="label">检测强度:</span>
                <span class="strict">严格</span>
                <el-slider v-model="threshold" :min="30" :max="90" :step="5" :show-tooltip="false"
                    class="threshold-slider" />
                <span class="loose">宽松</span>
                <el-tag size="small" type="info" class="threshold-value">{{ threshold }}%</el-tag>
            </div>
        </div>

        <div class="input-area">
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
        </div>

        <div class="quick-tests">
            <span class="label">快速测试:</span>
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
const threshold = ref(detectionStore.threshold)

watch(threshold, (val) => {
    detectionStore.setThreshold(val)
})

const detect = () => {
    if (url.value.trim()) {
        emit('detect', url.value.trim())
    }
}

const quickTest = (testUrl: string) => {
    url.value = testUrl
    detect()
}

const emit = defineEmits<{
    (e: 'detect', url: string): void
}>()
</script>

<style lang="scss" scoped>
.detection-panel {
    margin-bottom: 1.5rem;
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(16px);

    .detection-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 1rem;
        margin-bottom: 1.5rem;

        h2 {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 1.25rem;
            font-weight: 600;
        }

        .threshold-control {
            display: flex;
            align-items: center;
            gap: 0.75rem;

            .label,
            .strict,
            .loose {
                font-size: 0.75rem;
                color: #6b7280;
            }

            .strict {
                color: #ef4444;
                font-weight: 500;
            }

            .loose {
                color: #10b981;
                font-weight: 500;
            }

            .threshold-slider {
                width: 160px;
            }
        }
    }

    .input-area {
        margin-bottom: 1rem;

        :deep(.el-input-group__append) {
            padding: 0;
        }
    }

    .quick-tests {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex-wrap: wrap;

        .label {
            font-size: 0.75rem;
            color: #6b7280;
        }
    }
}
</style>