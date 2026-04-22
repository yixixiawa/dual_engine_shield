import earthFlyLine from 'earth-flyline'
import {
  addFlyLineData,
  addScatterData,
  buildInitConfig,
  defaultChartStyle,
  defaultEarthConfig,
  disposeChart,
  registerMapResource,
  removeChartData,
  updateEarthColor as applyEarthColor,
  updateMapAreaColor,
  updateMapLineColor,
  updateRadius,
  validateContainer
} from './earth-common'
import type { ChartStyle, DragConfig, EarthConfig, EarthMode, FlyLineData, ScatterData } from './earth-common'
import earth2dConfig from './earth2d'
import earth3dConfig from './earth3d'

const mergeDragConfig = (mode: EarthMode, customConfig: Partial<EarthConfig>): DragConfig => {
  const defaults = defaultEarthConfig[mode].dragConfig
  const merged = {
    ...(defaults || {}),
    ...(customConfig.dragConfig || {})
  }

  return {
    rotationSpeed: merged.rotationSpeed ?? (mode === '3d' ? 1 : 0),
    inertiaFactor: merged.inertiaFactor ?? (mode === '3d' ? 10 : 0),
    disableX: merged.disableX ?? (mode === '2d'),
    disableY: merged.disableY ?? (mode === '2d')
  }
}

const mergeConfig = (mode: EarthMode, customConfig: Partial<EarthConfig>): EarthConfig => {
  const defaults = defaultEarthConfig[mode]

  return {
    mode,
    autoRotate: customConfig.autoRotate ?? defaults.autoRotate ?? (mode === '3d'),
    rotateSpeed: customConfig.rotateSpeed ?? defaults.rotateSpeed,
    radius: customConfig.radius ?? defaults.radius,
    stopRotateByHover: customConfig.stopRotateByHover ?? defaults.stopRotateByHover,
    dragConfig: mergeDragConfig(mode, customConfig)
  }
}

const initEarthChart = (containerId: string, config: EarthConfig, chartStyle: ChartStyle): any => {
  registerMapResource()
  const dom = validateContainer(containerId)
  if (!dom) return null

  try {
    const initConfig = buildInitConfig({ dom, mode: config.mode, config, chartStyle })
    return earthFlyLine.init(initConfig as any)
  } catch (error) {
    console.error(`${config.mode.toUpperCase()} 地球初始化失败:`, error)
    return null
  }
}

export const useEarthModel = () => {
  const chartStyle: ChartStyle = { ...defaultChartStyle }
  const finalConfigs: Record<EarthMode, EarthConfig> = {
    '3d': mergeConfig('3d', earth3dConfig),
    '2d': mergeConfig('2d', earth2dConfig)
  }

  let currentChart: any = null
  let currentMode: EarthMode = '3d'

  const init = (containerId: string, mode: EarthMode) => {
    disposeChart(currentChart)
    currentChart = initEarthChart(containerId, finalConfigs[mode], chartStyle)
    currentMode = mode
    return currentChart
  }

  const initChart = (containerId: string) => init(containerId, '3d')

  const init2dChart = (containerId: string) => init(containerId, '2d')

  const switchMode = (containerId: string, mode: EarthMode) => init(containerId, mode)

  const addScatter = (data: ScatterData[]) => {
    removeChartData(currentChart, 'point', 'removeAll')
    if (!data.length) return
    addScatterData(currentChart, data)
  }

  const addFlyLines = (data: FlyLineData[]) => {
    addFlyLineData(currentChart, data)
  }

  const addData = (type: 'flyLine' | 'point' | 'road' | 'wall' | 'mapStreamLine' | 'bar' | 'textMark', data: any) => {
    if (!currentChart) return

    if (typeof currentChart.addData === 'function') {
      currentChart.addData(type, data)
      return
    }

    if (typeof currentChart.setData === 'function') {
      currentChart.setData(type, data)
    }
  }

  const removeData = (type: 'flyLine' | 'point' | 'road' | 'wall' | 'mapStreamLine' | 'bar' | 'textMark', ids: string[] | 'removeAll') => {
    removeChartData(currentChart, type, ids)
  }

  const clearScatter = () => {
    removeChartData(currentChart, 'point', 'removeAll')
  }

  const getChart = () => currentChart

  const getChart3d = () => (currentMode === '3d' ? currentChart : null)

  const getChart2d = () => (currentMode === '2d' ? currentChart : null)

  const getMode = () => currentMode

  const updateEarthColor = (color: string) => {
    chartStyle.earthColor = color
    applyEarthColor(currentChart, color)
  }

  const updateAreaColor = (color: string) => {
    chartStyle.areaColor = color
    updateMapAreaColor(currentChart, color)
  }

  const updateLineColor = (color: string) => {
    chartStyle.lineColor = color
    updateMapLineColor(currentChart, color)
  }

  const setEarthRadius = (radius: number) => {
    updateRadius(currentChart, radius)
  }

  const dispose = () => {
    disposeChart(currentChart)
    currentChart = null
  }

  return {
    initChart,
    init2dChart,
    switchMode,
    addScatter,
    addFlyLines,
    addData,
    removeData,
    clearScatter,
    getChart,
    getChart3d,
    getChart2d,
    getMode,
    dispose,
    chartStyle,
    updateEarthColor,
    updateAreaColor,
    updateLineColor,
    setEarthRadius
  }
}

export default useEarthModel
