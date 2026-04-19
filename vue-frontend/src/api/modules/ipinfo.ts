export interface IPGeoInfo {
    ip: string;
    country: string;      // 国家名称（用于区域高亮）
    city: string;         // 城市名称
    region: string;       // 省份/州
    latitude: number;     // 纬度
    longitude: number;    // 经度
    loc: string;          // "纬度,经度" 格式
    timezone: string;     // 时区
}