import earthFlyLine from 'earth-flyline'
import worldGeoJSON from '@/assets/world.json'

export type EarthMode = '2d' | '3d'

export interface DragConfig {
  rotationSpeed: number
  inertiaFactor: number
  disableX: boolean
  disableY: boolean
}

export interface EarthConfig {
  mode: EarthMode
  autoRotate?: boolean
  rotateSpeed?: number
  radius?: number
  stopRotateByHover?: boolean
  dragConfig?: DragConfig
}

export interface ScatterData {
  id?: string | number
  lon: number
  lat: number
  name: string
  value?: number
  style?: {
    color?: string
    size?: number
    effect?: boolean
  }
}

export interface FlyLineData {
  from: { lon: number; lat: number }
  to: { lon: number; lat: number }
  name?: string
  style?: {
    color?: string
    width?: number
  }
}

export interface ChartStyle {
  earthColor: string
  areaColor: string
  lineColor: string
  backgroundColor: string
}

export const defaultChartStyle: ChartStyle = {
  earthColor: '#2C5F8D',
  areaColor: '#6E98BA',
  lineColor: '#FF6B6B',
  backgroundColor: '#f5f7fa'
}

export const defaultEarthConfig: Record<EarthMode, Partial<EarthConfig>> = {
  '3d': {
    mode: '3d',
    autoRotate: true,
    rotateSpeed: 0.01,
    radius: 180,
    stopRotateByHover: true,
    dragConfig: {
      rotationSpeed: 1,
      inertiaFactor: 10,
      disableX: false,
      disableY: false
    }
  },
  '2d': {
    mode: '2d',
    autoRotate: false,
    radius: 160,
    stopRotateByHover: false,
    dragConfig: {
      rotationSpeed: 0,
      inertiaFactor: 0,
      disableX: true,
      disableY: true
    }
  }
}

let isMapRegistered = false

export const registerMapResource = (): void => {
  if (isMapRegistered) return

  try {
    earthFlyLine.registerMap('world', worldGeoJSON as any)
    isMapRegistered = true
  } catch (error) {
    console.warn('地图注册失败（可能已注册）:', error)
  }
}

export const validateContainer = (containerId: string): HTMLElement | null => {
  const dom = document.getElementById(containerId)
  if (!dom) return null

  while (dom.firstChild) {
    dom.removeChild(dom.firstChild)
  }

  return dom as HTMLElement
}

export const buildInitConfig = ({
  dom,
  mode,
  config,
  chartStyle
}: {
  dom: HTMLElement
  mode: EarthMode
  config: EarthConfig
  chartStyle: ChartStyle
}) => {
  const radius = config.radius ?? defaultEarthConfig[mode].radius ?? (mode === '3d' ? 180 : 160)

  if (mode === '2d') {
    return {
      dom,
      map: 'world',
      mode: '2d',
      autoRotate: false,
      config: {
        R: radius,
        enableZoom: true,
        stopRotateByHover: config.stopRotateByHover ?? false,
        mapStyle: {
          areaColor: chartStyle.areaColor,
          lineColor: chartStyle.lineColor,
          opacity: 0.9
        },
        bgStyle: {
          color: chartStyle.backgroundColor,
          opacity: 1
        },
        scatterStyle: {
          color: '#ff3366',
          size: 0.8,
          effect: true
        }
      }
    }
  }

  return {
    dom,
    map: 'world',
    mode: '3d',
    autoRotate: config.autoRotate ?? true,
    rotateSpeed: config.rotateSpeed ?? 0.01,
    config: {
      R: radius,
      mapStyle: {
        areaColor: chartStyle.areaColor,
        lineColor: chartStyle.lineColor,
        opacity: 0.8
      },
      earth: {
        color: chartStyle.earthColor
      },
      spriteStyle: {
        show: true,
        color: chartStyle.lineColor
      },
      scatterStyle: {
        color: '#ff3366',
        size: 0.8,
        effect: true
      }
    }
  }
}

export const addScatterData = (chart: any, data: ScatterData[]): void => {
  if (!chart) return

  const points = data.map((item) => ({
    id: item.id,
    lon: item.lon,
    lat: item.lat,
    name: item.name,
    value: item.value ?? 0,
    style: {
      color: item.style?.color ?? '#ff3366',
      size: item.style?.size ?? 0.8,
      effect: item.style?.effect !== false
    }
  }))

  if (typeof chart.addScatter === 'function') {
    chart.addScatter(points)
    return
  }

  if (typeof chart.setScatterData === 'function') {
    chart.setScatterData(points)
    return
  }

  if (typeof chart.addData === 'function') {
    chart.addData('point', points)
    return
  }

  if (typeof chart.setData === 'function') {
    chart.setData('point', points)
  }
}

export const addFlyLineData = (chart: any, data: FlyLineData[]): void => {
  if (!chart) return

  if (typeof chart.addFlyLines === 'function') {
    chart.addFlyLines(data)
    return
  }

  if (typeof chart.setLinesData === 'function') {
    chart.setLinesData(data)
    return
  }

  if (typeof chart.addData === 'function') {
    chart.addData('flyLine', data)
    return
  }

  if (typeof chart.setData === 'function') {
    chart.setData('flyLine', data)
  }
}

export const removeChartData = (
  chart: any,
  type: 'flyLine' | 'point' | 'road' | 'wall' | 'mapStreamLine' | 'bar' | 'textMark',
  ids: string[] | 'removeAll'
): void => {
  if (!chart || typeof chart.remove !== 'function') return
  chart.remove(type, ids)
}

export const disposeChart = (chart: any): void => {
  if (chart && typeof chart.dispose === 'function') {
    chart.dispose()
  }
}

export const updateEarthColor = (chart: any, color: string): void => {
  chart?.updateConfig?.({ earth: { color } })
}

export const updateMapAreaColor = (chart: any, color: string): void => {
  chart?.updateConfig?.({ mapStyle: { areaColor: color } })
}

export const updateMapLineColor = (chart: any, color: string): void => {
  chart?.updateConfig?.({ mapStyle: { lineColor: color } })
}

export const updateRadius = (chart: any, radius: number): void => {
  chart?.updateConfig?.({ R: radius })
}
