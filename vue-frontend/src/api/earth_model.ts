import earthFlyLine from "earth-flyline";
import geojson from "@/assets/world.json";
import type EarthModel from "@/api/modules/Earth_model";



export const useEarthModel = () => {
  let chart: any = null;

  const initChart = (containerId: string) => {
    // 注册地图
    earthFlyLine.registerMap("world", geojson);

    // 获取dom节点作为容器
    const dom = document.getElementById(containerId) as HTMLElement;
    if (!dom) {
      console.error(`Container element #${containerId} not found`);
      return null;
    }

    // 初始化图表
    chart = earthFlyLine.init({
      dom,
      map: "world",
      config: {
        R: 140,
        earth: {
          color: chartstyle.earthColor.value,
        }
      }
    });

    // 调试：查看 chart 对象结构
    console.log('Chart object:', chart);
    console.log('Chart methods:', Object.keys(chart));

    // 设置点击事件
    if (chart && chart.on) {
      chart.on('click', (params: any) => {
        console.log('点击了:', params);
        if (params.type === 'scatter') {
          alert(`IP位置: ${params.data.name}`);
        } else if (params.type === 'region') {
          alert(`选中了国家: ${params.name}`);
        }
      });
    }

    return chart;
  };

  // 更新地球颜色
  const updateEarthColor = (color: string) => {
    chartstyle.earthColor.value = color;
    if (chart) {
      chart.updateConfig({
        earth: {
          color: color
        }
      });
    }
  };

  // 更新区域颜色
  const updateAreaColor = (color: string) => {
    chartstyle.areaColor.value = color;
  };

  // 更新飞线颜色
  const updateLineColor = (color: string) => {
    chartstyle.lineColor.value = color;
  };

  // 添加散点数据
  const addScatter = (data: Array<{ lon: number; lat: number; name: string; value: number }>) => {
    if (chart) {
      if (typeof chart.addScatter === 'function') {
        chart.addScatter(data);
      } else if (typeof chart.setScatterData === 'function') {
        // 尝试使用替代方法
        chart.setScatterData(data);
      } else if (typeof chart.setData === 'function') {
        // 使用 earth-flyline 正确的 API
        chart.setData({
          type: 'point',
          data: data
        });
      } else if (typeof chart.addData === 'function') {
        // 尝试使用 addData 方法
        chart.addData({
          type: 'point',
          data: data
        });
      } else {
        console.warn('Chart object does not have addScatter, setScatterData, setData or addData method');
        console.log('Available methods:', Object.keys(chart));
      }
    } else {
      console.warn('Chart is not initialized');
    }
  };

  // 添加飞线数据
  const addFlyLines = (data: Array<{ from: { lon: number; lat: number }; to: { lon: number; lat: number }; name: string }>) => {
    if (chart) {
      if (typeof chart.addFlyLines === 'function') {
        chart.addFlyLines(data);
      } else if (typeof chart.setLinesData === 'function') {
        // 尝试使用替代方法
        chart.setLinesData(data);
      } else if (typeof chart.setData === 'function') {
        // 使用 earth-flyline 正确的 API
        chart.setData({
          type: 'flyLine',
          data: data
        });
      } else if (typeof chart.addData === 'function') {
        // 尝试使用 addData 方法
        chart.addData({
          type: 'flyLine',
          data: data
        });
      } else {
        console.warn('Chart object does not have addFlyLines, setLinesData, setData or addData method');
        console.log('Available methods:', Object.keys(chart));
      }
    } else {
      console.warn('Chart is not initialized');
    }
  };

  // 获取图表实例
  const getChart = () => chart;

  return {
    initChart,
    addScatter,
    addFlyLines,
    getChart,
    chartstyle,
    updateEarthColor,
    updateAreaColor,
    updateLineColor
  };
};

export default useEarthModel;