<template>
    <el-drawer v-model="whitelistStore.panelVisible" title="白名单管理" direction="rtl" size="400px">
        <div class="whitelist-panel">
            <el-alert title="教育网自动保护" type="success" :closable="false" class="alert-section">
                <template #default>
                    <p>自动匹配 *.edu.cn 及子域名</p>
                    <code class="domain-pattern">.*\.edu\.cn$</code>
                    <el-checkbox v-model="eduForceReduce" class="force-reduce">
                        启用强制风险降级 (×0.3)
                    </el-checkbox>
                </template>
            </el-alert>

            <el-alert title="IP混淆强制拦截" type="warning" :closable="false" class="alert-section">
                <template #default>
                    <p>以下模式将无视阈值直接标记高危:</p>
                    <ul class="pattern-list">
                        <li>• xxx.xxx.xxx.xxx.domain.com</li>
                        <li>• 0xXX.0xXX.0xXX.0xXX.*</li>
                        <li>• IP+品牌词组合</li>
                    </ul>
                </template>
            </el-alert>

            <div class="custom-whitelist">
                <div class="section-title">
                    <el-icon>
                        <Plus />
                    </el-icon>
                    自定义白名单
                </div>

                <div class="add-form">
                    <el-input v-model="newDomain" placeholder="example.com" @keyup.enter="addWhitelist" />
                    <el-button type="primary" @click="addWhitelist">添加</el-button>
                </div>

                <div class="whitelist-items">
                    <div v-for="item in whitelistStore.whitelist" :key="item.domain" class="whitelist-item">
                        <span class="domain mono">{{ item.domain }}</span>
                        <div class="item-actions">
                            <el-tag v-if="item.isSystem" type="success" size="small">系统</el-tag>
                            <el-button v-else type="danger" link size="small" @click="removeWhitelist(item.domain)">
                                <el-icon>
                                    <Delete />
                                </el-icon>
                            </el-button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </el-drawer>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useWhitelistStore } from '@/stores/whitelist'

const whitelistStore = useWhitelistStore()
const newDomain = ref('')
const eduForceReduce = ref(true)

const addWhitelist = () => {
    if (newDomain.value.trim()) {
        whitelistStore.addWhitelist(newDomain.value.trim())
        newDomain.value = ''
    }
}

const removeWhitelist = (domain: string) => {
    whitelistStore.removeWhitelist(domain)
}
</script>

<style lang="scss" scoped>
.whitelist-panel {
    padding: 0 0.5rem;

    .alert-section {
        margin-bottom: 1.5rem;

        :deep(.el-alert__content) {
            width: 100%;
        }

        .domain-pattern {
            display: block;
            background: #f3f4f6;
            padding: 0.5rem;
            border-radius: 0.5rem;
            font-family: monospace;
            font-size: 0.75rem;
            margin: 0.5rem 0;
        }

        .force-reduce {
            margin-top: 0.5rem;
        }

        .pattern-list {
            margin-top: 0.5rem;
            padding-left: 1rem;
            font-size: 0.75rem;
            color: #6b7280;
            font-family: monospace;
        }
    }

    .custom-whitelist {
        .section-title {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 500;
            margin-bottom: 1rem;
        }

        .add-form {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }

        .whitelist-items {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            max-height: 300px;
            overflow-y: auto;

            .whitelist-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.5rem 0.75rem;
                background: #f9fafb;
                border-radius: 0.5rem;
                border: 1px solid #e5e7eb;

                .domain {
                    font-size: 0.875rem;
                    color: #374151;
                }

                .item-actions {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                }
            }
        }
    }
}
</style>