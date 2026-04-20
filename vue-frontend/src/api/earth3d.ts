/**
 * 3D地球模型初始化和管理
 * 
 * 改进：使用 useEarthFactory 工厂函数
 * 代码减少: 从 99 行 → 17 行 (83% 削减)
 */
import { useEarthFactory } from "./useEarthFactory";

export const useEarth3D = () => {
  return useEarthFactory({
    mode: "3d",
    autoRotate: true,
    rotateSpeed: 0.01,
    dragConfig: {
      rotationSpeed: 1,
      inertiaFactor: 10,
      disableX: false,
      disableY: false
    }
  });
};

export default useEarth3D;
