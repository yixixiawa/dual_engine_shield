<template>
    <div class="combined-detection">
        <div class="header-actions">
            <el-tag type="success" effect="plain" class="status-tag">
                <el-icon>
                    <Check />
                </el-icon>
                全功能就绪
            </el-tag>
            <el-button @click="generateReport" text>
                <el-icon>
                    <Document />
                </el-icon>
                生成报告
            </el-button>
        </div>

        <el-card class="input-card" shadow="hover">
            <h2 class="card-title">🔍 综合安全检测</h2>
            <p class="card-desc">输入目标URL，执行钓鱼检测和漏洞检测一体化分析</p>

            <div class="input-area">
                <el-input v-model="url" placeholder="输入目标网址 (https://example.com)" size="large" clearable
                    @keyup.enter="startDetection" />
                <el-button type="primary" :loading="isDetecting" @click="startDetection">
                    <el-icon>
                        <Search />
                    </el-icon>
                    开始综合检测
                </el-button>
            </div>
        </el-card>

        <!-- 进度面板 -->
        <el-card v-if="isDetecting || showProgress" class="progress-card" shadow="hover">
            <template #header>
                <span class="card-header">检测进度</span>
            </template>

            <div class="progress-steps">
                <div v-for="step in steps" :key="step.key" class="step-item">
                    <div class="step-icon" :class="step.status">
                        <el-icon v-if="step.status === 'completed'">
                            <Check />
                        </el-icon>
                        <el-icon v-else-if="step.status === 'processing'">
                            <Loading />
                        </el-icon>
                        <span v-else class="step-number">{{ step.number }}</span>
                    </div>
                    <div class="step-content">
                        <div class="step-title">{{ step.title }}</div>
                        <div class="step-status">{{ step.statusText }}</div>
                        <el-progress :percentage="step.progress" :show-text="false" :stroke-width="6"
                            :status="step.status === 'completed' ? 'success' : undefined" />
                    </div>
                </div>
            </div>
        </el-card>

        <!-- 结果面板 -->
        <el-card v-if="result" class="result-card" shadow="hover">
            <template #header>
                <span class="card-header">检测结果</span>
            </template>

            <div class="result-summary">
                <div class="summary-item">
                    <div class="summary-label">钓鱼检测</div>
                    <div class="summary-value" :class="getPhishingRiskClass(phishingScore)">
                        {{ (phishingScore * 100).toFixed(1) }}%
                    </div>
                    <div class="summary-detail">{{ getPhishingRiskText(phishingScore) }}</div>
                </div>

                <div class="summary-item">
                    <div class="summary-label">漏洞检测</div>
                    <div class="summary-value" :class="totalVulns > 0 ? 'text-danger' : 'text-success'">
                        {{ totalVulns > 0 ? `${totalVulns} 个` : '安全' }}
                    </div>
                    <div class="summary-detail">{{ totalVulns > 0 ? `发现 ${totalVulns} 个安全问题` : '未检测到漏洞' }}</div>
                </div>
            </div>

            <!-- 爬虫信息 -->
            <div v-if="crawlInfo" class="crawl-info">
                <el-divider content-position="left">网站信息</el-divider>
                <div class="info-grid">
                    <div class="info-item">
                        <span class="info-label">抓取页面</span>
                        <span class="info-value">{{ crawlInfo.pages || 0 }}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">发现链接</span>
                        <span class="info-value">{{ crawlInfo.links || 0 }}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">发现表单</span>
                        <span class="info-value">{{ crawlInfo.forms || 0 }}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">代码语言</span>
                        <span class="info-value">{{ (crawlInfo.lang || 'HTML').toUpperCase() }}</span>
                    </div>
                </div>
            </div>

            <!-- 漏洞详情 -->
            <div v-if="totalVulns > 0" class="vuln-details">
                <el-divider content-position="left">漏洞详情</el-divider>
                <div class="detail-grid">
                    <div class="detail-item">
                        <span class="detail-label">源码漏洞</span>
                        <span class="detail-value" :class="codeVulnCount > 0 ? 'text-danger' : 'text-success'">
                            {{ codeVulnCount > 0 ? `${codeVulnCount} 个` : '安全' }}
                        </span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">URL漏洞</span>
                        <span class="detail-value" :class="urlVulnCount > 0 ? 'text-danger' : 'text-success'">
                            {{ urlVulnCount > 0 ? '有风险' : '安全' }}
                        </span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Web漏洞</span>
                        <span class="detail-value" :class="webVulnCount > 0 ? 'text-danger' : 'text-success'">
                            {{ webVulnCount > 0 ? `${webVulnCount} 个` : '安全' }}
                        </span>
                    </div>
                </div>
            </div>

            <!-- 总体评估 -->
            <div class="overall-assessment" :class="overallRiskClass">
                <div class="assessment-header">
                    <span class="assessment-label">总体评估</span>
                    <span class="assessment-badge">{{ overallRiskText }}</span>
                </div>
                <p class="assessment-desc">{{ overallRiskDesc }}</p>
            </div>
        </el-card>
    </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useTasksStore } from '@/stores/tasks'

const tasksStore = useTasksStore()
const url = ref('')
const isDetecting = ref(false)
const showProgress = ref(false)
const result = ref<any>(null)
const crawlInfo = ref<any>(null)

const steps = ref([
    { key: 'crawl', number: 1, title: '爬虫抓取', status: 'pending', statusText: '等待中', progress: 0 },
    { key: 'phishing', number: 2, title: '钓鱼检测', status: 'pending', statusText: '等待中', progress: 0 },
    { key: 'vuln', number: 3, title: '漏洞检测', status: 'pending', statusText: '等待中', progress: 0 }
])

const phishingScore = computed(() => {
    return result.value?.phishing?.final || result.value?.phishing?.risk_score || 0
})

const codeVulnCount = computed(() => {
    return result.value?.code?.vulnerabilities?.length || 0
})

const urlVulnCount = computed(() => {
    return result.value?.url?.is_vulnerable ? 1 : 0
})

const webVulnCount = computed(() => {
    return result.value?.web?.vulnerabilities_found || 0
})

const totalVulns = computed(() => {
    return codeVulnCount.value + urlVulnCount.value + webVulnCount.value
})

const overallRiskClass = computed(() => {
    const score = phishingScore.value
    const vulns = totalVulns.value
    if (score >= 0.8 || vulns > 2) return 'risk-critical'
    if (score >= 0.5 || vulns > 0) return 'risk-medium'
    return 'risk-safe'
})

const overallRiskText = computed(() => {
    const score = phishingScore.value
    const vulns = totalVulns.value
    if (score >= 0.8 || vulns > 2) return '高风险'
    if (score >= 0.5 || vulns > 0) return '中风险'
    return '安全'
})

const overallRiskDesc = computed(() => {
    const score = phishingScore.value
    const vulns = totalVulns.value
    if (score >= 0.8 || vulns > 2) return '检测到严重安全威胁，建议立即处理'
    if (score >= 0.5 || vulns > 0) return '发现安全问题，建议尽快修复'
    return '未检测到安全威胁'
})

const updateStep = (key: string, status: string, progress: number, statusText: string) => {
    const step = steps.value.find(s => s.key === key)
    if (step) {
        step.status = status
        step.progress = progress
        step.statusText = statusText
    }
}

const resetSteps = () => {
    steps.value.forEach(step => {
        step.status = 'pending'
        step.progress = 0
        step.statusText = '等待中'
    })
}

const getPhishingRiskClass = (score: number) => {
    if (score >= 0.8) return 'text-danger'
    if (score >= 0.5) return 'text-warning'
    return 'text-success'
}

const getPhishingRiskText = (score: number) => {
    if (score >= 0.8) return '高风险'
    if (score >= 0.5) return '中风险'
    return '低风险'
}

const startDetection = async () => {
    if (!url.value.trim()) {
        ElMessage.warning('请输入目标网址')
        return
    }

    isDetecting.value = true
    showProgress.value = true
    result.value = null
    resetSteps()

    const taskId = tasksStore.addTask({
        type: 'combined',
        status: 'processing',
        target: url.value,
        createdAt: new Date().toLocaleString()
    })

    try {
        // 模拟步骤1：爬虫抓取
        updateStep('crawl', 'processing', 30, '正在抓取...')
        await new Promise(r => setTimeout(r, 1500))
        updateStep('crawl', 'completed', 100, '完成')
        crawlInfo.value = { pages: 5, links: 23, forms: 2, lang: 'html' }

        // 模拟步骤2：钓鱼检测
        updateStep('phishing', 'processing', 50, '分析中...')
        await new Promise(r => setTimeout(r, 1500))
        updateStep('phishing', 'completed', 100, '完成')

        // 模拟步骤3：漏洞检测
        updateStep('vuln', 'processing', 60, '扫描中...')
        await new Promise(r => setTimeout(r, 2000))
        updateStep('vuln', 'completed', 100, '完成')

        // 模拟结果
        result.value = {
            phishing: { final: Math.random() * 0.8, risk_score: Math.random() * 0.8 },
            code: { vulnerabilities: Math.random() > 0.7 ? [{ type: 'SQL注入' }] : [] },
            url: { is_vulnerable: Math.random() > 0.8 },
            web: { vulnerabilities_found: Math.random() > 0.7 ? Math.floor(Math.random() * 3) : 0 }
        }

        tasksStore.updateTask(taskId, {
            status: 'completed',
            result: result.value
        })

        ElMessage.success('检测完成')
    } catch (error) {
        tasksStore.updateTask(taskId, {
            status: 'failed',
            result: { error: (error as Error).message }
        })
        ElMessage.error('检测失败: ' + (error as Error).message)
    } finally {
        isDetecting.value = false
    }
}

const generateReport = () => {
    ElMessage.info('正在生成综合检测报告...')
}
</script>

<style lang="scss" scoped>
.combined-detection {
    max-width: 1024px;
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

    .input-card,
    .progress-card,
    .result-card {
        margin-bottom: 1.5rem;
        background: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(16px);

        .card-title {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .card-desc {
            color: #6b7280;
            margin-bottom: 1.5rem;
        }

        .input-area {
            display: flex;
            gap: 1rem;

            .el-input {
                flex: 1;
            }
        }

        .card-header {
            font-weight: 600;
        }
    }

    .progress-steps {
        .step-item {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;

            &:last-child {
                margin-bottom: 0;
            }

            .step-icon {
                width: 32px;
                height: 32px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 0.875rem;
                font-weight: 600;
                flex-shrink: 0;

                &.pending {
                    background: #f3f4f6;
                    color: #9ca3af;
                }

                &.processing {
                    background: #3b82f6;
                    color: white;
                    animation: spin 1s linear infinite;
                }

                &.completed {
                    background: #10b981;
                    color: white;
                }

                .step-number {
                    font-size: 0.875rem;
                    font-weight: 600;
                }
            }

            .step-content {
                flex: 1;

                .step-title {
                    font-weight: 500;
                    margin-bottom: 0.25rem;
                }

                .step-status {
                    font-size: 0.75rem;
                    color: #6b7280;
                    margin-bottom: 0.5rem;
                }
            }
        }
    }

    .result-summary {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.5rem;
        margin-bottom: 1.5rem;

        .summary-item {
            text-align: center;
            padding: 1rem;
            background: rgba(0, 0, 0, 0.02);
            border-radius: 0.75rem;

            .summary-label {
                font-size: 0.875rem;
                color: #6b7280;
                margin-bottom: 0.5rem;
            }

            .summary-value {
                font-size: 2rem;
                font-weight: 700;

                &.text-danger {
                    color: #ef4444;
                }

                &.text-warning {
                    color: #f59e0b;
                }

                &.text-success {
                    color: #10b981;
                }
            }

            .summary-detail {
                font-size: 0.75rem;
                color: #9ca3af;
                margin-top: 0.25rem;
            }
        }
    }

    .crawl-info {
        .info-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;

            .info-item {
                text-align: center;

                .info-label {
                    font-size: 0.75rem;
                    color: #6b7280;
                    display: block;
                    margin-bottom: 0.25rem;
                }

                .info-value {
                    font-size: 1.25rem;
                    font-weight: 600;
                }
            }
        }
    }

    .vuln-details {
        .detail-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;

            .detail-item {
                text-align: center;

                .detail-label {
                    font-size: 0.75rem;
                    color: #6b7280;
                    display: block;
                    margin-bottom: 0.25rem;
                }

                .detail-value {
                    font-size: 1rem;
                    font-weight: 600;

                    &.text-danger {
                        color: #ef4444;
                    }

                    &.text-success {
                        color: #10b981;
                    }
                }
            }
        }
    }

    .overall-assessment {
        margin-top: 1.5rem;
        padding: 1rem;
        border-radius: 0.75rem;

        &.risk-safe {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid #10b981;
        }

        &.risk-medium {
            background: rgba(245, 158, 11, 0.1);
            border: 1px solid #f59e0b;
        }

        &.risk-critical {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid #ef4444;
        }

        .assessment-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;

            .assessment-label {
                font-weight: 600;
            }

            .assessment-badge {
                font-size: 0.875rem;
                font-weight: 600;
            }
        }

        .assessment-desc {
            font-size: 0.875rem;
            margin: 0;
        }
    }
}

@keyframes spin {
    from {
        transform: rotate(0deg);
    }

    to {
        transform: rotate(360deg);
    }
}
</style>