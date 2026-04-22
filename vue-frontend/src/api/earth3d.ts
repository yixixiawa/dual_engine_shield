import type { EarthConfig } from './earth-common'

export const earth3dConfig: Partial<EarthConfig> = {
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
}

export default earth3dConfig
