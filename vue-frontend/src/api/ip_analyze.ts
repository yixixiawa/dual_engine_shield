import { type IPGeoInfo } from "@/api/modules/ipinfo.ts";

export async function getIPGeoInfo(ip: string): Promise<IPGeoInfo | null> {
    const token = 'YOUR_IPINFO_TOKEN';
    
    try {
        const response = await fetch(`https://ipinfo.io/${ip}?token=${token}`);
        const data = await response.json();
        
        const [latitude, longitude] = (data.loc || '0,0').split(',').map(Number);
        
        return {
            ip: data.ip,
            country: data.country_name || data.country,
            city: data.city,
            latitude: latitude,
            longitude: longitude,
        };
    } catch (error) {
        console.error('IPinfo 查询失败:', error);
        return null;
    }
}