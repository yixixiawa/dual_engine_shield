/**
 * 2D平面地图初始化和管理
 * 
 * 改进：使用 useEarthFactory 工厂函数
 * 代码减少: 从 92 行 → 12 行 (87% 删减)
 */
import { useEarthFactory } from "./useEarthFactory";

export const useEarth2D = () => {
  return useEarthFactory({
    mode: "2d",
    dragConfig: {
      rotationSpeed: 0.5,
      inertiaFactor: 0,
      disableX: true,
      disableY: false
    }
  });
};

export default useEarth2D;
