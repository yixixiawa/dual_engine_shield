<template>
    <div class="homepage-container">
        <!-- 顶部：2D/3D 切换和统计卡片 -->
        <div class="top-section">
            <div class="mode-switcher">
                <el-segmented v-model="displayMode" :options="[
                    { label: '3D 地球模型', value: '3d' },
                    { label: '2D 平面图', value: '2d' }
                ]" />
            </div>

            <el-row :gutter="20" class="stats-row">
                <el-col :xs="24" :sm="12" :md="6">
                    <el-statistic title="今日钓鱼地址" :value="phishingUrlsCount" size="large">
                        <template #prefix>
                            <el-icon style="color: #F56C6C"><Warning /></el-icon>
                        </template>
                    </el-statistic>
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                    <el-statistic title="已检测地址" :value="detectedCount" size="large">
                        <template #prefix>
                            <el-icon style="color: #409EFF"><Search /></el-icon>
                        </template>
                    </el-statistic>
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                    <el-statistic title="检测准确率" :value="accuracy" suffix="%" size="large">
                        <template #prefix>
                            <el-icon style="color: #67C23A"><SuccessFilled /></el-icon>
                        </template>
                    </el-statistic>
                </el-col>
                <el-col :xs="24" :sm="12" :md="6">
                    <el-statistic title="检测速度" :value="detectionSpeed" suffix="ms" size="large">
                        <template #prefix>
                            <el-icon style="color: #E6A23C"><Timer /></el-icon>
                        </template>
                    </el-statistic>
                </el-col>
            </el-row>
        </div>

        <!-- 中间：地球/平面图容器 -->
        <div class="middle-section">
            <div class="globe-wrapper">
                <!-- 3D 地球模型 -->
                <div v-show="displayMode === '3d'" class="earth earth-3d" id="container"></div>
                
                <!-- 2D 平面图 -->
                <div v-show="displayMode === '2d'" class="earth earth-2d" id="container-2d"></div>
            </div>
        </div>

        <!-- 下方：今日钓鱼地址列表 -->
        <div class="bottom-section">
            <el-card shadow="hover">
                <template #header>
                    <div class="card-header">
                        <span class="title">
                            <el-icon><Warning /></el-icon>
                            今日发现的钓鱼地址
                        </span>
                        <div class="header-actions">
                            <el-input
                                v-model="urlSearchKeyword"
                                placeholder="搜索钓鱼地址..."
                                clearable
                                style="width: 250px"
                            >
                                <template #prefix>
                                    <el-icon><Search /></el-icon>
                                </template>
                            </el-input>
                            <el-button @click="refreshPhishingUrls" :loading="urlsLoading">
                                <el-icon><Refresh /></el-icon>
                            </el-button>
                        </div>
                    </div>
                </template>

                <div v-if="urlsLoading" class="loading-container">
                    <el-skeleton :rows="5" animated />
                </div>

                <el-table
                    v-else
                    :data="filteredPhishingUrls"
                    stripe
                    height="400"
                    default-sort="{ prop: 'detectedAt', order: 'descending' }"
                >
                    <el-table-column type="expand">
                        <template #default="{ row }">
                            <div class="expand-detail">
                                <el-row :gutter="20">
                                    <el-col :span="12">
                                        <p><strong>完整URL:</strong></p>
                                        <el-text type="info" truncated>{{ row.url }}</el-text>
                                    </el-col>
                                    <el-col :span="12">
                                        <p><strong>检测信息:</strong></p>
                                        <div>
                                            <el-tag type="danger" size="small">{{ row.riskLevel }}</el-tag>
                                            <el-tag size="small">置信度: {{ (row.confidence * 100).toFixed(1) }}%</el-tag>
                                        </div>
                                    </el-col>
                                </el-row>
                            </div>
                        </template>
                    </el-table-column>

                    <el-table-column prop="domain" label="域名" width="200" show-overflow-tooltip />

                    <el-table-column label="威胁等级" width="100">
                        <template #default="{ row }">
                            <el-tag :type="getRiskType(row.riskLevel)">
                                {{ row.riskLevel }}
                            </el-tag>
                        </template>
                    </el-table-column>

                    <el-table-column label="风险评分" width="120">
                        <template #default="{ row }">
                            <el-progress
                                :percentage="Math.round(row.score * 100)"
                                :color="getScoreColor(row.score)"
                                :show-text="false"
                            />
                            <span class="score-text">{{ (row.score * 100).toFixed(1) }}%</span>
                        </template>
                    </el-table-column>

                    <el-table-column prop="region" label="来源地" width="100" />

                    <el-table-column prop="detectedAt" label="检测时间" width="150" sortable />

                    <el-table-column label="操作" width="100" fixed="right">
                        <template #default="{ row }">
                            <el-button link type="primary" @click="handleViewDetail(row)">详情</el-button>
                        </template>
                    </el-table-column>
                </el-table>

                <el-empty v-if="filteredPhishingUrls.length === 0" description="暂无钓鱼地址记录" />
            </el-card>
        </div>

        <!-- 详情对话框 -->
        <el-dialog v-model="detailDialogVisible" title="钓鱼地址详情" width="600px">
            <div v-if="selectedUrl" class="detail-content">
                <el-descriptions :column="1" border>
                    <el-descriptions-item label="域名">{{ selectedUrl.domain }}</el-descriptions-item>
                    <el-descriptions-item label="完整URL">
                        <el-text type="info" truncated>{{ selectedUrl.url }}</el-text>
                    </el-descriptions-item>
                    <el-descriptions-item label="风险等级">
                        <el-tag :type="getRiskType(selectedUrl.riskLevel)">
                            {{ selectedUrl.riskLevel }}
                        </el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="风险评分">{{ (selectedUrl.score * 100).toFixed(1) }}%</el-descriptions-item>
                    <el-descriptions-item label="置信度">{{ (selectedUrl.confidence * 100).toFixed(1) }}%</el-descriptions-item>
                    <el-descriptions-item label="来源地">{{ selectedUrl.region }}</el-descriptions-item>
                    <el-descriptions-item label="检测时间">{{ selectedUrl.detectedAt }}</el-descriptions-item>
                    <el-descriptions-item label="检测模型">
                        <el-tag type="info">{{ selectedUrl.model }}</el-tag>
                    </el-descriptions-item>
                </el-descriptions>
            </div>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Warning, Search, Refresh, SuccessFilled, Timer } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import useEarthModel from "@/api/earth_model"
import { 
    queryDomain, 
    convertToGlobeScatterData,
    getPhishingDetectionResults,
    getPhishingOnlyResults
} from "@/api/ip_analyze"

// 钓鱼地址类型定义
interface PhishingUrl {
    id: number
    domain: string
    url: string
    riskLevel: string
    score: number
    confidence: number
    region: string
    detectedAt: string
    model: string
}

const earthModel = useEarthModel()
const displayMode = ref<'2d' | '3d'>('3d')
const urlSearchKeyword = ref('')
const urlsLoading = ref(false)
const detailDialogVisible = ref(false)
const selectedUrl = ref<PhishingUrl | null>(null)
const globeLoading = ref(false)

// 统计数据
const phishingUrlsCount = ref(128)
const detectedCount = ref(1245)
const accuracy = ref(98.95)
const detectionSpeed = ref(234)

// 模拟的钓鱼地址数据
const phishingUrls = ref<PhishingUrl[]>([
    {
        id: 1,
        domain: 'paypal-secure.xyz',
        url: 'https://paypal-secure.xyz/verify',
        riskLevel: '极高',
        score: 0.95,
        confidence: 0.98,
        region: '中国',
        detectedAt: '2026-04-20 14:32:15',
        model: 'GTE'
    },
    {
        id: 2,
        domain: 'amazon-verify.com',
        url: 'https://amazon-verify.com/account',
        riskLevel: '高',
        score: 0.82,
        confidence: 0.95,
        region: '美国',
        detectedAt: '2026-04-20 13:45:22',
        model: 'GTE'
    },
    {
        id: 3,
        domain: 'bank-of-china.net',
        url: 'https://bank-of-china.net/login',
        riskLevel: '高',
        score: 0.78,
        confidence: 0.92,
        region: '中国',
        detectedAt: '2026-04-20 12:15:08',
        model: 'ChiPhish'
    },
    {
        id: 4,
        domain: 'apple-id-verify.io',
        url: 'https://apple-id-verify.io/auth',
        riskLevel: '极高',
        score: 0.91,
        confidence: 0.96,
        region: '日本',
        detectedAt: '2026-04-20 11:22:45',
        model: 'GTE'
    },
    {
        id: 5,
        domain: 'google-account-secure.tk',
        url: 'https://google-account-secure.tk/signin',
        riskLevel: '中',
        score: 0.65,
        confidence: 0.88,
        region: '中国',
        detectedAt: '2026-04-20 10:15:30',
        model: 'GTE'
    },
    {
        id: 6,
        domain: 'microsoft-login.ml',
        url: 'https://microsoft-login.ml/live',
        riskLevel: '高',
        score: 0.85,
        confidence: 0.93,
        region: '美国',
        detectedAt: '2026-04-20 09:45:12',
        model: 'ChiPhish'
    }
])

const filteredPhishingUrls = computed(() => {
    if (!urlSearchKeyword.value) return phishingUrls.value
    const keyword = urlSearchKeyword.value.toLowerCase()
    return phishingUrls.value.filter(
        url => url.domain.toLowerCase().includes(keyword) || url.url.toLowerCase().includes(keyword)
    )
})

const refreshPhishingUrls = async () => {
    urlsLoading.value = true
    try {
        console.log('🔄 刷新钓鱼地址列表...')
        
        // 从真实 API 获取钓鱼检测结果
        const detections = await getPhishingDetectionResults({
            threat_level: 'phishing',
            limit: 100
        })
        
        if (detections && detections.length > 0) {
            // 将检测结果转换为 PhishingUrl 格式
            phishingUrls.value = detections.map((detection, index) => ({
                id: detection.id || index,
                domain: new URL(detection.url).hostname || detection.url,
                url: detection.url,
                riskLevel: detection.threat_level === 'phishing' ? '极高' : 
                           detection.threat_level === 'malware' ? '极高' :
                           detection.threat_level === 'suspicious' ? '高' : '中',
                score: detection.combined_score || 0.85,
                confidence: detection.combined_score ? 0.95 : 0.80,
                region: '未知',
                detectedAt: new Date().toLocaleString('zh-CN'),
                model: detection.model_used || 'GTE'
            }))
            
            phishingUrlsCount.value = phishingUrls.value.length
            console.log(`✅ 已更新 ${phishingUrls.value.length} 条钓鱼地址`)
            ElMessage.success(`✅ 钓鱼地址列表已更新（${phishingUrls.value.length} 条）`)
        } else {
            console.warn('⚠️ 没有获取到钓鱼检测结果')
            ElMessage.info('⚠️ 暂无钓鱼检测结果')
        }
    } catch (error) {
        console.error('❌ 刷新钓鱼地址列表失败:', error)
        ElMessage.error('❌ 刷新失败，请稍后重试')
    } finally {
        urlsLoading.value = false
    }
}

// 🆕 从真实的钓鱼检测结果加载地址到地球模型
const loadPhishingAddressesToGlobe = async () => {
    if (globeLoading.value) return
    
    globeLoading.value = true
    console.log('🌍 开始从真实数据加载钓鱼地址到地球模型...')
    
    try {
        // 🆕 第一步：获取真实的钓鱼检测结果
        console.log('📡 正在获取钓鱼检测结果数据库...')
        const phishingDetections = await getPhishingOnlyResults(100)
        
        if (!phishingDetections || phishingDetections.length === 0) {
            console.warn('⚠️ 没有找到钓鱼检测结果')
            ElMessage.warning('没有找到钓鱼检测结果')
            globeLoading.value = false
            return
        }
        
        console.log(`✅ 获取到 ${phishingDetections.length} 条钓鱼检测记录`)
        
        // 更新统计信息
        phishingUrlsCount.value = phishingDetections.length
        detectedCount.value = Math.max(detectedCount.value, phishingDetections.length)
        
        // 🆕 第二步：对每个检测结果进行域名解析
        let successCount = 0
        for (let index = 0; index < phishingDetections.length; index++) {
            const detection = phishingDetections[index]
            try {
                console.log(`🔍 [${index + 1}/${phishingDetections.length}] 查询域名: ${detection.url}`)
                
                // 调用域名查询 API 进行 DNS 解析和地理定位
                const domainResult = await queryDomain(detection.url, true, false)
                
                if (domainResult && domainResult.results.length > 0) {
                    // 根据威胁等级设置风险评分
                    let riskScore = 50
                    switch (detection.threat_level) {
                        case 'phishing':
                            riskScore = Math.round((detection.combined_score || 0.95) * 100)
                            break
                        case 'malware':
                            riskScore = 95
                            break
                        case 'suspicious':
                            riskScore = 70
                            break
                        default:
                            riskScore = 40
                    }
                    
                    // 将查询结果转换为地球模型需要的格式
                    const scatterData = convertToGlobeScatterData(
                        domainResult,
                        Math.max(riskScore, 60)
                    )
                    
                    // 添加到地球模型
                    if (scatterData.length > 0) {
                        earthModel.addScatter(scatterData)
                        console.log(`✅ [${index + 1}/${phishingDetections.length}] 已添加 ${scatterData.length} 个标记点`)
                        successCount++
                    }
                } else {
                    console.warn(`⚠️ 无法解析域名: ${detection.url}`)
                }
            } catch (error) {
                console.error(`❌ 查询 ${detection.url} 时出错:`, error)
            }
            
            // 避免过度请求，添加延迟
            await new Promise(resolve => setTimeout(resolve, 300))
        }
        
        console.log(`✅ 加载完成：成功加载 ${successCount}/${phishingDetections.length} 个钓鱼地址到地球模型`)
        ElMessage.success(`✅ 已加载 ${successCount} 个钓鱼地址到地球模型`)
    } catch (error) {
        console.error('❌ 加载钓鱼地址到地球模型时出错:', error)
        ElMessage.error('加载钓鱼地址失败')
    } finally {
        globeLoading.value = false
    }
}

const handleViewDetail = (row: PhishingUrl) => {
    selectedUrl.value = row
    detailDialogVisible.value = true
}

const getRiskType = (riskLevel: string) => {
    const typeMap: Record<string, string> = {
        '极高': 'danger',
        '高': 'warning',
        '中': 'warning',
        '低': 'info',
        '安全': 'success'
    }
    return typeMap[riskLevel] || 'info'
}

const getScoreColor = (score: number) => {
    if (score >= 0.85) return '#F56C6C'
    if (score >= 0.65) return '#E6A23C'
    return '#67C23A'
}

onMounted(async () => {
    console.log('⏳ 初始化3D地球模型和加载真实数据...')
    // 初始化3D图表
    earthModel.initChart("container")
    
    // 给地球初始化留出时间
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 并行执行两个操作：
    // 1. 在地球模型上显示钓鱼地址位置
    // 2. 在下面表格中显示钓鱼地址详情
    console.log('📡 并行加载地球模型数据和表格数据...')
    await Promise.all([
        loadPhishingAddressesToGlobe(),
        refreshPhishingUrls()
    ])
    
    console.log('✅ 数据加载完成')
})

// 监听displayMode变化，处理2D/3D切换
watch(displayMode, async (newMode) => {
    // 给DOM更新时间
    await new Promise(resolve => setTimeout(resolve, 0))
    
    if (newMode === '2d') {
        // 初始化2D图表
        earthModel.init2dChart("container-2d")
    }
}, { immediate: false })
</script>

<style scoped lang="scss">
.homepage-container {
    width: 100%;
    padding: 20px;
    background: #f5f7fa;
    display: flex;
    flex-direction: column;
    gap: 20px;

    .top-section {
        display: flex;
        flex-direction: column;
        gap: 16px;

        .mode-switcher {
            display: flex;
            justify-content: center;
            padding: 12px 0;

            :deep(.el-segmented) {
                background: white;
                border-radius: 8px;
                padding: 4px;
            }
        }

        .stats-row {
            width: 100%;
        }
    }

    .middle-section {
        width: 100%;
        flex: 1;

        .globe-wrapper {
            width: 100%;
            height: 600px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
            overflow: hidden;

            .earth {
                width: 100%;
                height: 100%;

                &.earth-3d {
                    display: flex;
                }

                &.earth-2d {
                    display: flex;
                    flex-direction: column;
                }
            }

            .map-2d {
                width: 100%;
                height: 100%;
                display: none;
            }
        }
    }

    .bottom-section {
        width: 100%;

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
            }

            .header-actions {
                display: flex;
                align-items: center;
                gap: 12px;
            }
        }

        .loading-container {
            padding: 20px;
        }

        .expand-detail {
            padding: 20px;
            background: #f5f7fa;

            p {
                margin: 0 0 8px 0;
                font-weight: 600;
                color: #303133;
            }

            :deep(.el-text) {
                display: block;
                padding: 8px;
                background: white;
                border-radius: 4px;
                border-left: 3px solid #409EFF;
                padding-left: 12px;
            }
        }

        .score-text {
            display: block;
            margin-top: 4px;
            font-size: 12px;
            text-align: center;
            color: #606266;
        }
    }

    .detail-content {
        padding: 12px 0;
    }
}

@media (max-width: 768px) {
    .homepage-container {
        padding: 12px;

        .middle-section .globe-wrapper {
            height: 400px;
        }

        .bottom-section .card-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 12px;

            .header-actions {
                width: 100%;
                flex-wrap: wrap;
            }
        }
    }
}
</style>