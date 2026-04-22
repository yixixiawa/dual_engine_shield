import type { EarthConfig } from './earth-common'

export const earth3dConfig: Partial<EarthConfig> = {
  mode: '3d',
  autoRotate: true,
  rotateSpeed: 0.005,  // 降低旋转速度，减少卡顿
  radius: 160,         // 减小半径，提升渲染性能
  stopRotateByHover: true,
  dragConfig: {
    rotationSpeed: 0.5,  // 降低拖拽旋转速度
    inertiaFactor: 5,    // 降低惯性系数，拖拽更跟手
    disableX: false,
    disableY: false
  }
}

export default earth3dConfig
