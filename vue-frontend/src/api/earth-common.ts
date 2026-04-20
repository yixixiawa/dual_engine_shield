/**
 * 地球模型通用配置和样式
 * 共享的资源和配置
 */
import earthFlyLine from "earth-flyline";
import geojson from "@/assets/world.json" with { type: "json" };

export interface ChartStyle {
  earthColor: { value: string };
  areaColor: { value: string };
  lineColor: { value: string };
}

// 默认样式配置
export const defaultChartStyle: ChartStyle = {
  earthColor: { value: '#2C5F8D' },
  areaColor: { value: '#6E98BA' },
  lineColor: { value: '#FF6B6B' }
};

/**
 * 注册地图资源
 */
export const registerMapResource = () => {
  try {
    earthFlyLine.registerMap("world", geojson as any);
  } catch (error) {
    console.warn('地图已注册或注册失败:', error);
  }
};

/**
 * 验证DOM容器
 */
export const validateContainer = (containerId: string) => {
  const dom = document.getElementById(containerId) as HTMLElement;
  if (!dom) {
    console.error(`Container element #${containerId} not found`);
    return null;
  }
  return dom;
};

/**
 * 获取基础配置（3D/2D通用）
 */
export const getBaseConfig = (chartstyle: ChartStyle) => ({
  R: 140,
  mapStyle: {
    areaColor: chartstyle.areaColor.value,
    lineColor: chartstyle.lineColor.value,
    opacity: 0.8,
    material: "MeshBasicMaterial"
  },
  spriteStyle: {
    color: chartstyle.lineColor.value,
    show: true
  }
});

/**
 * 设置点击事件监听
 */
export const setupClickListener = (chart: any) => {
  if (chart && chart.on) {
    chart.on('click', (params: any) => {
      console.log('地图点击:', params);
      if (params.type === 'scatter') {
        console.log(`IP位置: ${params.data.name}`);
      } else if (params.type === 'region') {
        console.log(`选中了国家: ${params.name}`);
      }
    });
  }
};

/**
 * 添加散点数据
 */
export const addScatterData = (chart: any, data: Array<{ lon: number; lat: number; name: string; value: number }>) => {
  if (!chart) return;
  
  if (typeof chart.addScatter === 'function') {
    chart.addScatter(data);
  } else if (typeof chart.setScatterData === 'function') {
    chart.setScatterData(data);
  } else if (typeof chart.setData === 'function') {
    chart.setData({
      type: 'point',
      data: data
    });
  } else if (typeof chart.addData === 'function') {
    chart.addData({
      type: 'point',
      data: data
    });
  } else {
    console.warn('Chart object does not have scatter data method');
  }
};

/**
 * 添加飞线数据
 */
export const addFlyLineData = (chart: any, data: Array<{ from: { lon: number; lat: number }; to: { lon: number; lat: number }; name: string }>) => {
  if (!chart) return;
  
  if (typeof chart.addFlyLines === 'function') {
    chart.addFlyLines(data);
  } else if (typeof chart.setLinesData === 'function') {
    chart.setLinesData(data);
  } else if (typeof chart.setData === 'function') {
    chart.setData({
      type: 'flyLine',
      data: data
    });
  } else if (typeof chart.addData === 'function') {
    chart.addData({
      type: 'flyLine',
      data: data
    });
  } else {
    console.warn('Chart object does not have flyline data method');
  }
};

/**
 * 销毁图表
 */
export const disposeChart = (chart: any) => {
  if (chart && typeof chart.dispose === 'function') {
    chart.dispose();
  }
};

/**
 * 更新地球颜色
 */
export const updateEarthColor = (chart: any, color: string) => {
  if (chart) {
    chart.updateConfig({
      earth: {
        color: color
      }
    });
  }
};

/**
 * 更新地图区域颜色
 */
export const updateMapAreaColor = (chart: any, color: string) => {
  if (chart) {
    chart.updateConfig({
      mapStyle: {
        areaColor: color
      }
    });
  }
};

/**
 * 更新地图线条颜色
 */
export const updateMapLineColor = (chart: any, color: string) => {
  if (chart) {
    chart.updateConfig({
      mapStyle: {
        lineColor: color
      }
    });
  }
};
