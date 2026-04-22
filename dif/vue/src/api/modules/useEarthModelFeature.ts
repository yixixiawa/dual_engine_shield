import { ref } from 'vue'
import { useEarthModel } from '@/api/earth_model'
import type { EarthMode, ScatterData } from '@/api/earth-common'
import { getGeoPhishingLocations } from './geoPhishingLocations'
import type { GeoPhishingLocationEntity, GeoPhishingLocationsQuery, GeoPhishingThreatLevel } from './geoPhishingLocations'

const threatColorMap: Record<GeoPhishingThreatLevel, string> = {
  phishing: '#ff3366',
  malware: '#ff6600',
  suspicious: '#ffaa00',
  safe: '#33ff66',
  unknown: '#888888'
}

const getColorByRiskScore = (riskScore: number): string => {
  if (riskScore >= 0.8) return '#ff0000'
  if (riskScore >= 0.6) return '#ff6600'
  if (riskScore >= 0.4) return '#ffaa00'
  if (riskScore >= 0.2) return '#33ff66'
  return '#66ccff'
}

const buildLocationName = (item: GeoPhishingLocationEntity) => {
  const locationName = item.city ? `${item.city}, ${item.country || '未知'}` : item.country || '未知位置'
  return `${item.ip_address}\n${locationName}\n风险: ${(item.risk_score || 0).toFixed(1)}分\n威胁: ${item.threat_level || 'unknown'}`
}

const hasCoordinates = (item: GeoPhishingLocationEntity | null | undefined): item is GeoPhishingLocationEntity & { latitude: number; longitude: number } => {
  return typeof item?.latitude === 'number' && Number.isFinite(item.latitude) && typeof item?.longitude === 'number' && Number.isFinite(item.longitude)
}

const toBasePoint = (item: GeoPhishingLocationEntity & { latitude: number; longitude: number }): ScatterData => ({
  id: `base-ip-${item.id ?? item.ip_address}`,
  lon: item.longitude,
  lat: item.latitude,
  name: buildLocationName(item),
  value: item.risk_score || 0,
  style: {
    color: threatColorMap[item.threat_level] || getColorByRiskScore((item.risk_score || 0) / 100),
    size: 8,
    effect: true
  }
})

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
      basePoints.value = filteredList.map(toBasePoint)
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
        basePoints.value = filteredList.map(toBasePoint)
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
