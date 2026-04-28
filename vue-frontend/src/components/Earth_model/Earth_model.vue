<template>
    <div class="homepage-container">
        <EarthModelStatsPanel v-model:display-mode="displayMode" :stats="stats" />
        <!-- 添加 ref -->
        <EarthModelGlobePanel 
            ref="globePanelRef"
            :display-mode="displayMode" 
            :loading="!globeInitialized" />
        <EarthModelRiskIpListPanel
            v-model:url-search-keyword="urlSearchKeyword"
            :urls-loading="urlsLoading"
            :globe-loading="globeLoading"
            :filtered-phishing-urls="filteredPhishingUrls"
            :get-risk-type="getRiskType"
            :get-threat-level-text="getThreatLevelText"
            :get-score-color="getScoreColor"
            :get-risk-level-by-score="getRiskLevelByScore"
            :get-risk-type-by-score="getRiskTypeByScore"
            :format-date="formatDate"
            @refresh="refreshData"
            @clear-highlights="clearHighlights"
            @highlight-test="runHighlightTestCase"
            @view-detail="handleViewDetail"
            @highlight="handleHighlight"
        />
        <EarthModelDetailDialog
            v-model="detailDialogVisible"
            :selected-url="selectedUrl"
            :format-date="formatDate"
            :get-risk-type="getRiskType"
            :get-threat-level-text="getThreatLevelText"
            :get-score-color="getScoreColor"
            @locate="locateOnGlobe"
        />
    </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useEarthFeature } from '@/api/modules/useEarthModelFeature'
import type { GeoPhishingLocationEntity } from '@/api/modules/geoPhishingLocations'
import EarthModelStatsPanel from './modules/EarthModelStatsPanel.vue'
import EarthModelGlobePanel from './modules/EarthModelGlobePanel.vue'
import EarthModelRiskIpListPanel from './modules/EarthModelRiskIpListPanel.vue'
import EarthModelDetailDialog from './modules/EarthModelDetailDialog.vue'

const GLOBE_CONTAINER_ID = 'globeContainer'
const globePanelRef = ref<InstanceType<typeof EarthModelGlobePanel> | null>(null)

const earthFeature = useEarthFeature()

const displayMode = ref<'2d' | '3d'>('3d')
const urlSearchKeyword = ref('')
const urlsLoading = ref(false)
const detailDialogVisible = ref(false)
const selectedUrl = ref<GeoPhishingLocationEntity | null>(null)

const globeLoading = earthFeature.locationsLoading
const ipDataList = ref<GeoPhishingLocationEntity[]>([])

const phishingUrlsCount = ref(0)
const detectedCount = ref(0)
const avgRiskScore = ref(0)
const highRiskCount = ref(0)

const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-'
    try {
        const date = new Date(dateStr)
        return date.toLocaleString('zh-CN')
    } catch {
        return dateStr
    }
}

const getThreatLevelText = (level: string) => {
    const map: Record<string, string> = {
        phishing: '钓鱼',
        malware: '恶意软件',
        suspicious: '可疑',
        safe: '安全',
        unknown: '未知'
    }
    return map[level] || level || '未知'
}

const getRiskType = (riskLevel: string) => {
    const typeMap: Record<string, string> = {
        phishing: 'danger',
        malware: 'danger',
        suspicious: 'warning',
        safe: 'success',
        unknown: 'info'
    }
    return typeMap[riskLevel] || 'info'
}

const getScoreColor = (score: number) => {
    if (score >= 0.8) return '#F56C6C'
    if (score >= 0.5) return '#E6A23C'
    return '#67C23A'
}

const getRiskLevelByScore = (score: number) => {
    if (score >= 90) return '严重'
    if (score >= 80) return '高级'
    if (score >= 70) return '中级'
    if (score >= 60) return '低级'
    return '安全'
}

const getRiskTypeByScore = (score: number) => {
    if (score >= 90) return 'danger'
    if (score >= 80) return 'warning'
    if (score >= 70) return 'info'
    if (score >= 60) return 'primary'
    return 'success'
}

const updateStatistics = (locations: GeoPhishingLocationEntity[], total: number) => {
    console.log('updateStatistics locations:', locations)
    console.log('updateStatistics total:', total)
    ipDataList.value = locations
    detectedCount.value = total
    phishingUrlsCount.value = locations.filter((item) => item.is_phishing).length
    // 新的接口返回的risk_score是百分比值，所以使用80作为阈值
    highRiskCount.value = locations.filter((item) => (item.risk_score || 0) >= 80).length

    if (locations.length === 0) {
        avgRiskScore.value = 0
        return
    }

    const totalScore = locations.reduce((sum, item) => sum + (item.risk_score || 0), 0)
    // 新的接口返回的risk_score已经是百分比值，所以不需要再乘以100
    avgRiskScore.value = parseFloat((totalScore / locations.length).toFixed(1))
}

const stats = computed(() => ({
    phishingUrlsCount: phishingUrlsCount.value,
    detectedCount: detectedCount.value,
    avgRiskScore: avgRiskScore.value,
    highRiskCount: highRiskCount.value
}))

const resetStatistics = () => {
    ipDataList.value = []
    detectedCount.value = 0
    phishingUrlsCount.value = 0
    highRiskCount.value = 0
    avgRiskScore.value = 0
}

const loadPhysicalAddresses = async () => {
    urlsLoading.value = true
    try {
        const result = await earthFeature.loadAndHighlightFromGeoAPI({
            page: 1,
            page_size: 500
        })
        console.log('loadPhysicalAddresses result:', result)
        updateStatistics(result.data, result.total)
        
        // 应用所有点
        earthFeature.setBaseIPPoints(result.data)
    } catch (error) {
        console.error('加载钓鱼 IP 数据失败:', error)
        ElMessage.error('加载钓鱼 IP 数据失败')
        resetStatistics()
    } finally {
        urlsLoading.value = false
    }
}

const refreshData = async () => {
    await loadPhysicalAddresses()
    ElMessage.success('数据已刷新')
}

const clearHighlights = () => {
    const success = earthFeature.clearHighlights()
    if (success) {
        ElMessage.success('已清除当前高亮标记')
    } else {
        ElMessage.warning('当前没有可清除的高亮')
    }
}

const handleViewDetail = (row: GeoPhishingLocationEntity) => {
    selectedUrl.value = row
    detailDialogVisible.value = true
}

const handleHighlight = (row: GeoPhishingLocationEntity) => {
    earthFeature.highlightIPPoint(row)
}

const locateOnGlobe = (location: GeoPhishingLocationEntity | null) => {
    if (!location || typeof location.latitude !== 'number' || typeof location.longitude !== 'number') {
        ElMessage.warning('无法定位：缺少经纬度信息')
        return
    }

    earthFeature.highlightIPPoint(location)
    ElMessage.success(`已定位到 ${location.city || location.country || location.ip_address}`)
    detailDialogVisible.value = false
}

const runHighlightTestCase = () => {
    if (!ipDataList.value.length) {
        ElMessage.warning('当前没有可高亮的真实IP数据，请先刷新')
        return
    }

    // 高亮前3个高风险IP
    const topHighRiskIPs = [...ipDataList.value]
        .sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0))
        .slice(0, 3)
    
    if (topHighRiskIPs.length > 0) {
        earthFeature.highlightMultipleIPPoints(topHighRiskIPs)
        ElMessage.success(`已高亮 ${topHighRiskIPs.length} 个高风险IP`)
    }
}

const filteredPhishingUrls = computed(() => {
    console.log('ipDataList.value:', ipDataList.value)
    if (!urlSearchKeyword.value) return ipDataList.value
    const keyword = urlSearchKeyword.value.toLowerCase()
    return ipDataList.value.filter(
        (item) => item.ip_address?.toLowerCase().includes(keyword) ||
            item.domain?.toLowerCase().includes(keyword) ||
            item.city?.toLowerCase().includes(keyword) ||
            item.country?.toLowerCase().includes(keyword)
    )
})

const handleWindowResize = () => {
    globePanelRef.value?.handleResize()
}


const globeInitialized = ref(false)
const initAttempts = ref(0)
const maxInitAttempts = 10

const initGlobeWithRetry = async () => {
    const container = document.getElementById(GLOBE_CONTAINER_ID)
    if (!container) {
        if (initAttempts.value < maxInitAttempts) {
            initAttempts.value++
            setTimeout(initGlobeWithRetry, 100)
        }
        return
    }
    
    const width = container.clientWidth
    const height = container.clientHeight
    
    // 确保容器有有效尺寸
    if (width <= 0 || height <= 0) {
        if (initAttempts.value < maxInitAttempts) {
            initAttempts.value++
            setTimeout(initGlobeWithRetry, 100)
        }
        return
    }
    
    try {
        // 初始化地球模型
        earthFeature.initChart(GLOBE_CONTAINER_ID)
        globeInitialized.value = true
        console.log('[Earth Model] 地球模型初始化成功')
        
        // 等待一小段时间确保 canvas 创建完成
        await new Promise(resolve => setTimeout(resolve, 50))
        
        // 调整尺寸
        globePanelRef.value?.handleResize()
        console.log('[Earth Model] 尺寸调整完成')
        
        // 启动渲染循环
        globePanelRef.value?.startRenderLoop()
        console.log('[Earth Model] 渲染循环已启动')
        
        // 加载数据
        await loadPhysicalAddresses()
        console.log('[Earth Model] 数据加载完成')
        
    } catch (error) {
        console.error('[Earth Model] 初始化失败:', error)
        if (initAttempts.value < maxInitAttempts) {
            initAttempts.value++
            setTimeout(initGlobeWithRetry, 200)
        }
    }
}

onMounted(async () => {
    // 添加窗口 resize 监听（先添加，确保 resize 事件能被捕获）
    window.addEventListener('resize', handleWindowResize)
    
    // 等待 DOM 完全渲染后再初始化
    await nextTick()
    await nextTick()
    
    // 开始初始化（带重试机制）
    initGlobeWithRetry()
})

watch(detailDialogVisible, (visible) => {
    if (!visible) {
        earthFeature.clearActiveHighlight()
    }
})

watch(displayMode, async (newMode) => {
    if (globeInitialized.value) {
        await nextTick()
        earthFeature.switchMode(GLOBE_CONTAINER_ID, newMode)
    }
})

onBeforeUnmount(() => {
    earthFeature.dispose()
    window.removeEventListener('resize', handleWindowResize)
})
</script>

<style scoped lang="scss">
.homepage-container {
    width: 100%;
    padding: 20px;
    background: #f0f2f6;
    display: flex;
    flex-direction: column;
    gap: 20px;
    min-height: 100vh;
    box-sizing: border-box;
}

@media (max-width: 768px) {
    .homepage-container {
        padding: 12px;
    }
}
</style>
