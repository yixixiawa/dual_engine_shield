import { ref } from 'vue'
import { useEarthModel } from '@/api/earth_model'
import type { EarthMode, ScatterData } from '@/api/earth-common'
import { getGeoPhishingLocations } from './geoPhishingLocations'
import type { GeoPhishingLocationEntity, GeoPhishingLocationsQuery, GeoPhishingThreatLevel } from './geoPhishingLocations'
import { apiCall } from '../client'

const threatColorMap: Record<GeoPhishingThreatLevel, string> = {
  phishing: '#ff3366',
  malware: '#ff6600',
  suspicious: '#ffaa00',
  safe: '#33ff66',
  unknown: '#888888'
}

const getColorByRiskScore = (riskScore: number): string => {
  if (riskScore >= 0.8) return '#ff0000' // 高风险 - 红色
  if (riskScore >= 0.6) return '#ff6600' // 中高风险 - 橙色
  if (riskScore >= 0.4) return '#ffaa00' // 中风险 - 黄色
  if (riskScore >= 0.2) return '#33ff66' // 低风险 - 绿色
  return '#33ff66' // 安全 - 绿色
}

const buildLocationName = (item: GeoPhishingLocationEntity, count: number = 1, ips: string[] = []) => {
  const locationName = item.city ? `${item.city}, ${item.country || '未知'}` : item.country || '未知位置'
  let name = `${item.ip_address}\n${locationName}\n风险: ${(item.risk_score || 0).toFixed(1)}分\n威胁: ${item.threat_level || 'unknown'}`
  
  // 如果是聚类点，显示IP数量
  if (count > 1) {
    name = `IP集群 (${count}个IP)\n${locationName}\n风险: ${(item.risk_score || 0).toFixed(1)}分\n威胁: ${item.threat_level || 'unknown'}`
    // 显示前3个IP作为示例
    if (ips.length > 0) {
      const sampleIps = ips.slice(0, 3).join(', ')
      const moreIps = ips.length > 3 ? `...等${ips.length}个IP` : ''
      name += `\n示例IP: ${sampleIps}${moreIps}`
    }
  }
  
  return name
}

const hasCoordinates = (item: GeoPhishingLocationEntity | null | undefined): item is GeoPhishingLocationEntity & { latitude: number; longitude: number } => {
  return typeof item?.latitude === 'number' && Number.isFinite(item.latitude) && typeof item?.longitude === 'number' && Number.isFinite(item.longitude)
}

// 计算两个经纬度之间的距离（使用简化的欧几里得距离，适用于小范围）
const calculateDistance = (lat1: number, lon1: number, lat2: number, lon2: number): number => {
  const dLat = lat2 - lat1
  const dLon = lon2 - lon1
  return Math.sqrt(dLat * dLat + dLon * dLon)
}

// 对IP地址进行聚类，将经纬度差距不超过3的IP归为一类
const clusterIPLocations = (locations: (GeoPhishingLocationEntity & { latitude: number; longitude: number })[]): Array<{
  location: GeoPhishingLocationEntity & { latitude: number; longitude: number }
  count: number
  ips: string[]
}> => {
  const clusters: Array<{
    location: GeoPhishingLocationEntity & { latitude: number; longitude: number }
    count: number
    ips: string[]
  }> = []

  locations.forEach(location => {
    let foundCluster = false
    
    // 检查是否属于现有聚类
    for (const cluster of clusters) {
      const distance = calculateDistance(
        location.latitude,
        location.longitude,
        cluster.location.latitude,
        cluster.location.longitude
      )
      
      // 如果距离小于3，归为同一聚类
      if (distance < 3) {
        cluster.count++
        cluster.ips.push(location.ip_address)
        foundCluster = true
        break
      }
    }
    
    // 如果没有找到聚类，创建新聚类
    if (!foundCluster) {
      clusters.push({
        location,
        count: 1,
        ips: [location.ip_address]
      })
    }
  })
  
  return clusters
}

const toBasePoint = (item: GeoPhishingLocationEntity & { latitude: number; longitude: number }, totalPoints: number, count: number = 1, ips: string[] = []): ScatterData => {
  let size = 8
  if (totalPoints <= 5) {
    size = 10
  } else if (totalPoints <= 10) {
    size = 8
  } else {
    size = Math.max(1.8, 8 - Math.floor((totalPoints - 10) / 10) * 2)
  }
  
  // 根据聚类数量调整点的大小
  if (count > 1) {
    // 聚类点增大size，最多增大到15
    size = Math.min(15, size + Math.log(count) * 2)
  }
  
  return {
    id: `base-ip-${item.id ?? item.ip_address}`,
    lon: item.longitude,
    lat: item.latitude,
    name: buildLocationName(item, count, ips),
    value: item.risk_score || 0,
    style: {
      color: threatColorMap[item.threat_level] || getColorByRiskScore((item.risk_score || 0) / 100),
      size: size,
      effect: true
    }
  }
}

const toHighlightPoint = (item: GeoPhishingLocationEntity & { latitude: number; longitude: number }): ScatterData => ({
  id: `active-ip-${item.id ?? item.ip_address}`,
  lon: item.longitude,
  lat: item.latitude,
  name: buildLocationName(item),
  value: item.risk_score || 0,
  style: {
    color: '#ffcc00',
    size: 10,
    effect: true
  }
})

export const useEarthFeature = () => {
  const isLoading = ref(false)
  const locationsLoading = ref(false)

  const {
    initChart,
    init2dChart,
    switchMode: switchEarthMode,
    addScatter,
    addData,
    removeData,
    clearScatter,
    getChart,
    getChart3d,
    getChart2d,
    dispose,
    updateEarthColor,
    updateAreaColor,
    updateLineColor,
    setEarthRadius
  } = useEarthModel()

  const basePoints = ref<ScatterData[]>([])
  const highlightedPoints = ref<ScatterData[]>([])
  const highlightedLocations = ref<GeoPhishingLocationEntity[]>([])

  const applyBasePoints = () => {
    addScatter(basePoints.value)
  }

  const applyHighlightedPoints = () => {
    highlightedPoints.value.forEach(point => {
      addData('point', [point])
    })
  }

  const clearActiveHighlight = () => {
    if (highlightedPoints.value.length === 0) return false
    const ids = highlightedPoints.value.map(point => point.id)
    removeData('point', ids)
    highlightedPoints.value = []
    highlightedLocations.value = []
    return true
  }

  const reapplyPoints = () => {
    applyBasePoints()
    applyHighlightedPoints()
  }

  const setBaseIPPoints = (ipList: GeoPhishingLocationEntity[]) => {
    try {
      const filteredList = (ipList || []).filter(hasCoordinates)
      
      // 对IP地址进行聚类
      const clusters = clusterIPLocations(filteredList)
      const totalPoints = clusters.length
      
      // 根据聚类结果生成点
      basePoints.value = clusters.map(cluster => 
        toBasePoint(cluster.location, totalPoints, cluster.count, cluster.ips)
      )
      
      applyBasePoints()

      // 重新应用高亮点
      applyHighlightedPoints()

      return basePoints.value
    } catch (error) {
      console.error('setBaseIPPoints error:', error)
      return []
    }
  }

  const highlightIPPoint = (location: GeoPhishingLocationEntity | null) => {
    if (!hasCoordinates(location)) return false

    // 检查是否已经高亮
    const isAlreadyHighlighted = highlightedLocations.value.some(loc => loc.ip_address === location.ip_address)
    if (isAlreadyHighlighted) return false

    const highlightPoint = toHighlightPoint(location)
    addData('point', [highlightPoint])
    highlightedPoints.value.push(highlightPoint)
    highlightedLocations.value.push(location)
    return true
  }

  const highlightMultipleIPPoints = (locations: GeoPhishingLocationEntity[]) => {
    const validLocations = locations.filter(hasCoordinates)
    if (validLocations.length === 0) return false

    validLocations.forEach(location => {
      // 检查是否已经高亮
      const isAlreadyHighlighted = highlightedLocations.value.some(loc => loc.ip_address === location.ip_address)
      if (!isAlreadyHighlighted) {
        const highlightPoint = toHighlightPoint(location)
        addData('point', [highlightPoint])
        highlightedPoints.value.push(highlightPoint)
        highlightedLocations.value.push(location)
      }
    })
    return true
  }

  const switchMode = (containerId: string, mode: EarthMode) => {
    if (mode === '2d') {
      init2dChart(containerId)
    } else {
      switchEarthMode(containerId, mode)
    }

    reapplyPoints()
  }

  // 调用批量检测接口
  const batchDetectPhishing = async (urls: string[]) => {
    try {
      const response = await apiCall('/detect/batch-fish/', 'POST', { urls })
      return response
    } catch (error) {
      console.error('批量检测失败:', error)
      throw error
    }
  }

  // 从geo-phishing/locations/获取IP数据
  const loadAndHighlightFromGeoAPI = async (params?: GeoPhishingLocationsQuery) => {
    if (locationsLoading.value) {
      return { points: [], total: 0, data: [] as GeoPhishingLocationEntity[] }
    }

    locationsLoading.value = true

    try {
      const response = await getGeoPhishingLocations({
        country: params?.country,
        city: params?.city,
        status: params?.status,
        page: params?.page || 1,
        page_size: params?.page_size || 100
      })

      if (response.status === 'success') {
        // 只存储数据，不渲染
        const filteredList = (response.data || []).filter(hasCoordinates)
        
        // 对IP地址进行聚类
        const clusters = clusterIPLocations(filteredList)
        const totalPoints = clusters.length
        
        // 根据聚类结果生成点
        basePoints.value = clusters.map(cluster => 
          toBasePoint(cluster.location, totalPoints, cluster.count, cluster.ips)
        )
        
        return {
          points: basePoints.value,
          total: response.count,
          data: response.data
        }
      }

      basePoints.value = []
      return { points: [], total: 0, data: [] as GeoPhishingLocationEntity[] }
    } catch (error) {
      console.error('加载物理地址数据失败:', error)
      basePoints.value = []
      return { points: [], total: 0, data: [] as GeoPhishingLocationEntity[] }
    } finally {
      locationsLoading.value = false
    }
  }

  const clearHighlights = () => clearActiveHighlight()

  const addIPHighlights = (ipList: GeoPhishingLocationEntity[]) => setBaseIPPoints(ipList)

  return {
    isLoading,
    locationsLoading,
    initChart,
    init2dChart,
    switchMode,
    dispose,
    updateEarthColor,
    updateAreaColor,
    updateLineColor,
    setEarthRadius,
    getChart,
    getChart3d,
    getChart2d,
    loadAndHighlightFromGeoAPI,
    batchDetectPhishing,
    clearHighlights,
    clearActiveHighlight,
    addIPHighlights,
    setBaseIPPoints,
    highlightIPPoint,
    highlightMultipleIPPoints,
    reapplyPoints
  }
}

export default useEarthFeature
