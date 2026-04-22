<template>
    <div class="combined-detection page-shell">
        <section class="page-header">
            <div>
                <h1 class="page-header__title">综合检测</h1>
                <p class="page-header__desc">输入目标网址，一次性完成爬取、钓鱼检测与漏洞检测分析。</p>
            </div>
            <div class="page-actions">
                <el-tag type="success" effect="plain" class="status-tag">
                    <el-icon>
                        <Check />
                    </el-icon>
                    全功能就绪
                </el-tag>
                <el-button text @click="generateReport">
                    <el-icon>
                        <Document />
                    </el-icon>
                    生成报告
                </el-button>
            </div>
        </section>

        <el-card class="input-card" shadow="never">
            <h2 class="card-title">综合安全检测</h2>
            <p class="card-desc">输入目标 URL，执行钓鱼检测和漏洞检测一体化分析。</p>

            <div class="input-area">
                <el-input
                    v-model="url"
                    placeholder="输入目标网址 (https://example.com)"
                    size="large"
                    clearable
                    @keyup.enter="startDetection"
                />
                <el-button type="primary" :loading="isDetecting" @click="startDetection">
                    <el-icon>
                        <Search />
                    </el-icon>
                    开始综合检测
                </el-button>
            </div>
        </el-card>

        <el-card v-if="isDetecting || showProgress" class="progress-card" shadow="never">
            <template #header>
                <div class="card-header">
                    <el-icon>
                        <Loading />
                    </el-icon>
                    <span>检测进度</span>
                </div>
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
                        <el-progress
                            :percentage="step.progress"
                            :show-text="false"
                            :stroke-width="6"
                            :status="step.status === 'completed' ? 'success' : undefined"
                        />
                    </div>
                </div>
            </div>
        </el-card>

        <el-card v-if="result" class="result-card" shadow="never">
            <template #header>
                <div class="card-header">
                    <el-icon>
                        <Check />
                    </el-icon>
                    <span>检测结果</span>
                </div>
            </template>

            <div class="result-summary">
                <div class="summary-item">
                    <div class="summary-label">钓鱼检测</div>
                    <div class="summary-value" :class="getPhishingRiskClass(phishingScore)">
                        {{ (phishingScore * 100).toFixed(1) }}%
                    </div>
                    <div class="summary-detail">{{ getPhishingRiskText(phishingScore) }}</div>
                    <div class="summary-status" :class="isPhishing ? 'text-danger' : 'text-success'">
                        {{ isPhishing ? '钓鱼网站' : '安全网站' }}
                    </div>
                </div>

                <div class="summary-item">
                    <div class="summary-label">漏洞检测</div>
                    <div class="summary-value" :class="totalVulns > 0 ? 'text-danger' : 'text-success'">
                        {{ totalVulns > 0 ? `${totalVulns} 个` : '安全' }}
                    </div>
                    <div class="summary-detail">{{ totalVulns > 0 ? `发现 ${totalVulns} 个安全问题` : '未检测到漏洞' }}</div>
                    <div class="summary-status" :class="isVulnerable ? 'text-danger' : 'text-success'">
                        {{ isVulnerable ? '存在漏洞' : '无漏洞' }}
                    </div>
                </div>

                <div class="summary-item">
                    <div class="summary-label">综合风险</div>
                    <div class="summary-value" :class="overallRiskClass">
                        {{ overallRiskText }}
                    </div>
                    <div class="summary-detail">
                        {{ (result.value?.comprehensive_risk?.score || 0) * 100 }}%
                    </div>
                    <div class="summary-status" :class="overallRiskClass">
                        {{ overallRiskDesc }}
                    </div>
                </div>
            </div>

            <div v-if="crawlInfo" class="crawl-info section-block">
                <div class="section-title">
                    <span>网站信息</span>
                </div>
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

            <div v-if="totalVulns > 0" class="vuln-details section-block">
                <div class="section-title">
                    <span>漏洞详情</span>
                </div>
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
import { apiCall } from '@/api/client'

const tasksStore = useTasksStore()
const url = ref('')
const isDetecting = ref(false)
const showProgress = ref(false)
const result = ref<any>(null)
const crawlInfo = ref<any>(null)
const reportData = ref<any>(null)

const steps = ref([
    { key: 'crawl', number: 1, title: '爬虫抓取', status: 'pending', statusText: '等待中', progress: 0 },
    { key: 'phishing', number: 2, title: '钓鱼检测', status: 'pending', statusText: '等待中', progress: 0 },
    { key: 'vuln', number: 3, title: '漏洞检测', status: 'pending', statusText: '等待中', progress: 0 }
])

const phishingScore = computed(() => {
    return result.value?.phishing_detection?.score || 0
})

const codeVulnCount = computed(() => {
    return result.value?.code_vulnerabilities?.length || 0
})

const totalVulns = computed(() => {
    return result.value?.total_vulnerabilities || 0
})

const overallRiskLevel = computed(() => {
    return result.value?.comprehensive_risk?.level || 'low'
})

const isPhishing = computed(() => {
    return result.value?.is_phishing || false
})

const isVulnerable = computed(() => {
    return result.value?.is_vulnerable || false
})

const overallRiskClass = computed(() => {
    const level = overallRiskLevel.value
    if (level === 'high') return 'risk-critical'
    if (level === 'medium') return 'risk-medium'
    return 'risk-safe'
})

const overallRiskText = computed(() => {
    const level = overallRiskLevel.value
    if (level === 'high') return '高风险'
    if (level === 'medium') return '中风险'
    return '安全'
})

const overallRiskDesc = computed(() => {
    const level = overallRiskLevel.value
    if (level === 'high') return '检测到严重安全威胁，建议立即处理'
    if (level === 'medium') return '发现安全问题，建议尽快修复'
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
    reportData.value = null
    resetSteps()

    const taskId = tasksStore.addTask({
        type: 'combined',
        status: 'processing',
        target: url.value,
        createdAt: new Date().toLocaleString()
    })

    try {
        updateStep('crawl', 'processing', 30, '正在抓取...')
        await new Promise(r => setTimeout(r, 1000))
        updateStep('crawl', 'completed', 100, '完成')

        updateStep('phishing', 'processing', 50, '分析中...')
        await new Promise(r => setTimeout(r, 1000))
        updateStep('phishing', 'completed', 100, '完成')

        updateStep('vuln', 'processing', 60, '扫描中...')
        
        // 调用综合检测API
        const response = await apiCall('/api/detect/comprehensive/', 'POST', { url: url.value })
        
        result.value = response
        reportData.value = response
        
        updateStep('vuln', 'completed', 100, '完成')

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
    if (!reportData.value) {
        ElMessage.warning('请先完成检测')
        return
    }

    try {
        // 生成JSON报告
        const report = {
            url: reportData.value.url,
            timestamp: new Date().toISOString(),
            phishing_detection: reportData.value.phishing_detection,
            code_vulnerabilities: reportData.value.code_vulnerabilities,
            comprehensive_risk: reportData.value.comprehensive_risk,
            total_vulnerabilities: reportData.value.total_vulnerabilities,
            is_phishing: reportData.value.is_phishing,
            is_vulnerable: reportData.value.is_vulnerable
        }

        // 转换为JSON字符串
        const reportJson = JSON.stringify(report, null, 2)

        // 创建下载链接
        const blob = new Blob([reportJson], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `comprehensive-report-${new Date().toISOString().replace(/[:.]/g, '-')}.json`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)

        ElMessage.success('报告已下载')
    } catch (error) {
        ElMessage.error('生成报告失败: ' + (error as Error).message)
    }
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;
@use '@/styles/mixins.scss' as *;

.combined-detection {
    .page-actions {
        display: flex;
        align-items: center;
        gap: $space-3;
        flex-wrap: wrap;
    }

    .status-tag {
        padding: 0.5rem 0.875rem;
        border-radius: 999px;
    }

    .input-card,
    .progress-card,
    .result-card {
        @include app-card;
    }

    .card-title {
        @include clamp-title(1.375rem);
        margin: 0 0 $space-2;
    }

    .card-desc {
        margin: 0 0 $space-5;
        color: $text-secondary;
        line-height: 1.6;
    }

    .card-header,
    .section-title {
        @include app-card-header;
    }

    .input-area {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: $space-3;
        align-items: center;
    }

    .progress-steps {
        display: flex;
        flex-direction: column;
        gap: $space-4;
    }

    .step-item {
        display: flex;
        gap: $space-4;
        align-items: flex-start;
        padding: $space-4;
        border: 1px solid rgba(24, 144, 255, 0.08);
        border-radius: $radius-md;
        background: $surface-muted;
    }

    .step-icon {
        width: 2.125rem;
        height: 2.125rem;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        font-size: 0.875rem;
        font-weight: 700;

        &.pending {
            background: #eef2f7;
            color: $text-muted;
        }

        &.processing {
            background: rgba(24, 144, 255, 0.12);
            color: $primary-active;

            :deep(.el-icon) {
                animation: spin 1s linear infinite;
            }
        }

        &.completed {
            background: rgba(82, 196, 26, 0.14);
            color: $success;
        }
    }

    .step-content {
        flex: 1;
        min-width: 0;
    }

    .step-title {
        font-weight: 600;
        color: $text-primary;
        margin-bottom: $space-1;
    }

    .step-status {
        font-size: 0.8125rem;
        color: $text-secondary;
        margin-bottom: $space-2;
    }

    .result-summary,
    .info-grid,
    .detail-grid {
        @include info-grid(180px);
    }

    .summary-item,
    .info-item,
    .detail-item {
        @include stat-tile;
        text-align: center;
    }

    .summary-label,
    .info-label,
    .detail-label {
        display: block;
        margin-bottom: $space-2;
        color: $text-secondary;
        font-size: 0.8125rem;
    }

    .summary-value,
    .info-value,
    .detail-value {
        display: block;
        font-weight: 700;
        color: $text-primary;
    }

    .summary-value {
        font-size: 1.875rem;
    }

    .info-value {
        font-size: 1.25rem;
    }

    .detail-value {
        font-size: 1rem;
    }

    .summary-detail {
        margin-top: $space-2;
        font-size: 0.8125rem;
        color: $text-muted;
    }

    .summary-status {
        margin-top: $space-1;
        font-size: 0.75rem;
        font-weight: 500;
    }

    .section-block {
        margin-top: $space-6;
    }

    .overall-assessment {
        margin-top: $space-6;
        padding: $space-5;
        border-radius: $radius-lg;
        border: 1px solid $border;

        &.risk-safe {
            background: rgba(82, 196, 26, 0.08);
            border-color: rgba(82, 196, 26, 0.24);
        }

        &.risk-medium {
            background: rgba(250, 173, 20, 0.1);
            border-color: rgba(250, 173, 20, 0.28);
        }

        &.risk-critical {
            background: rgba(255, 77, 79, 0.08);
            border-color: rgba(255, 77, 79, 0.26);
        }
    }

    .assessment-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: $space-3;
        margin-bottom: $space-2;
    }

    .assessment-label,
    .assessment-badge {
        font-weight: 700;
        color: $text-primary;
    }

    .assessment-desc {
        margin: 0;
        color: $text-secondary;
        line-height: 1.6;
    }

    .text-danger {
        color: $danger;
    }

    .text-warning {
        color: $warning;
    }

    .text-success {
        color: $success;
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

@media (max-width: $breakpoint-md) {
    .combined-detection {
        .input-area {
            grid-template-columns: 1fr;
        }

        .assessment-header {
            align-items: flex-start;
            flex-direction: column;
        }
    }
}
</style>
