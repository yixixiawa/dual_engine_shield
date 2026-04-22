import type { EarthConfig } from './earth-common'

export const earth2dConfig: Partial<EarthConfig> = {
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

export default earth2dConfig
