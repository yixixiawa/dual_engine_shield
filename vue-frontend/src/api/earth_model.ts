import useEarth3D from "./earth3d";
import useEarth2D from "./earth2d";
import { 
  defaultChartStyle, 
  addScatterData, 
  addFlyLineData,
  updateEarthColor as updateEarth3dColor,
  updateMapAreaColor,
  updateMapLineColor
} from "./earth-common";

export const useEarthModel = () => {
  const earth3d = useEarth3D();
  const earth2d = useEarth2D();
  
  const chartstyle = { ...defaultChartStyle };

  const initChart = (containerId: string) => {
    return earth3d.initChart(containerId, chartstyle);
  };

  const init2dChart = (containerId: string) => {
    return earth2d.initChart(containerId, chartstyle);
  };

  // 更新地球颜色
  const updateEarthColor = (color: string) => {
    chartstyle.earthColor.value = color;
    updateEarth3dColor(earth3d.getChart(), color);
  };

  // 更新区域颜色
  const updateAreaColor = (color: string) => {
    chartstyle.areaColor.value = color;
    updateMapAreaColor(earth3d.getChart(), color);
    updateMapAreaColor(earth2d.getChart(), color);
  };

  // 更新飞线颜色
  const updateLineColor = (color: string) => {
    chartstyle.lineColor.value = color;
    updateMapLineColor(earth3d.getChart(), color);
    updateMapLineColor(earth2d.getChart(), color);
  };

  // 添加散点数据
  const addScatter = (data: Array<{ lon: number; lat: number; name: string; value: number }>) => {
    const chart3dInstance = earth3d.getChart();
    const chart2dInstance = earth2d.getChart();
    
    if (chart3dInstance) {
      addScatterData(chart3dInstance, data);
    }
    if (chart2dInstance) {
      addScatterData(chart2dInstance, data);
    }
  };

  // 添加飞线数据
  const addFlyLines = (data: Array<{ from: { lon: number; lat: number }; to: { lon: number; lat: number }; name: string }>) => {
    const chart3dInstance = earth3d.getChart();
    if (chart3dInstance) {
      addFlyLineData(chart3dInstance, data);
    }
  };

  // 获取图表实例
  const getChart = () => earth3d.getChart() || earth2d.getChart();
  
  // 获取3D图表
  const getChart3d = () => earth3d.getChart();
  
  // 获取2D图表
  const getChart2d = () => earth2d.getChart();
  
  // 销毁图表
  const disposeChart = () => {
    earth3d.dispose();
    earth2d.dispose();
  };

  return {
    initChart,
    init2dChart,
    addScatter,
    addFlyLines,
    getChart,
    getChart3d,
    getChart2d,
    disposeChart,
    chartstyle,
    updateEarthColor,
    updateAreaColor,
    updateLineColor
  };
};

export default useEarthModel;