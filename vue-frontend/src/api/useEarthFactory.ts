/**
 * 地球模型通用工厂
 * 
 * 功能：提供统一的地球初始化和管理逻辑
 * 避免 earth2d.ts 和 earth3d.ts 的代码重复
 */

import earthFlyLine from "earth-flyline"
import type { ChartStyle } from "./earth-common"
import { 
  registerMapResource, 
  validateContainer, 
  setupClickListener 
} from "./earth-common"

export interface EarthConfig {
  mode: "2d" | "3d"
  autoRotate?: boolean
  rotateSpeed?: number
  radius?: number
  stopRotateByHover?: boolean
  dragConfig?: {
    rotationSpeed: number
    inertiaFactor: number
    disableX: boolean
    disableY: boolean
  }
}

/**
 * 创建地球模型
 * @param config 地球配置
 * @returns 地球模型相关的方法
 */
export const useEarthFactory = (config: EarthConfig) => {
  let chart: any = null

  const defaultConfig = {
    radius: 140,
    autoRotate: false,
    rotateSpeed: 0.01,
    stopRotateByHover: false,
  }

  /**
   * 初始化地球图表
   */
  const initChart = (containerId: string, chartStyle: ChartStyle) => {
    // 注册地图资源
    registerMapResource()

    // 验证容器
    const dom = validateContainer(containerId)
    if (!dom) return null

    try {
      let initConfig: any

      // 2D 模式的配置
      if (config.mode === "2d") {
        initConfig = {
          dom,
          map: "world",
          mode: "2d",
          autoRotate: false,
          config: {
            R: config.radius || defaultConfig.radius,
            stopRotateByHover: false,
            earth: {
              color: chartStyle.earthColor.value,
              dragConfig: config.dragConfig || {
                rotationSpeed: 0.5,
                inertiaFactor: 0,
                disableX: true,
                disableY: false
              }
            },
            mapStyle: {
              areaColor: chartStyle.areaColor.value,
              lineColor: chartStyle.lineColor.value,
              opacity: 0.9
            },
            spriteStyle: {
              color: chartStyle.lineColor.value,
              show: false
            },
            bgStyle: {
              color: "#f5f7fa",
              opacity: 1
            },
            enableZoom: true
          }
        }
      }
      // 3D 模式的配置
      else if (config.mode === "3d") {
        initConfig = {
          dom,
          map: "world",
          mode: "3d",
          autoRotate: true,
          rotateSpeed: config.rotateSpeed || 0.01,
          config: {
            R: config.radius || defaultConfig.radius,
            mapStyle: {
              areaColor: chartStyle.areaColor.value,
              lineColor: chartStyle.lineColor.value,
              opacity: 0.8
            },
            earth: {
              color: chartStyle.earthColor.value,
              dragConfig: config.dragConfig || {
                rotationSpeed: 1,
                inertiaFactor: 10,
                disableX: true,
                disableY: true
              }
            },
            spriteStyle: {
              color: chartStyle.lineColor.value,
              show: true
            }
          }
        }
      }

      // 初始化图表
      chart = earthFlyLine.init(initConfig)

      console.log(`✅ ${config.mode.toUpperCase()}地球初始化成功`)
      console.log(`Chart ${config.mode} object:`, chart)

      // 设置点击事件
      setupClickListener(chart)

      return chart
    } catch (error) {
      console.error(`❌ ${config.mode.toUpperCase()}地球初始化失败:`, error)
      return null
    }
  }

  /**
   * 获取图表实例
   */
  const getChart = () => chart

  /**
   * 销毁图表
   */
  const dispose = () => {
    if (chart && typeof chart.dispose === "function") {
      chart.dispose()
      chart = null
      console.log(`${config.mode.toUpperCase()}地球已销毁`)
    }
  }

  /**
   * 更新配置
   */
  const updateConfig = (newConfig: any) => {
    if (chart && typeof chart.updateConfig === "function") {
      chart.updateConfig(newConfig)
      console.log(`${config.mode.toUpperCase()}地球配置已更新`, newConfig)
    }
  }

  return {
    initChart,
    getChart,
    dispose,
    updateConfig
  }
}

export default useEarthFactory
