import { apiCall } from "./modules/ipinfo";

export interface IPGeoInfo {
    ip: string;
    country: string;
    city: string;
    latitude: number;
    longitude: number;
    org?: string;
    hostname?: string;
    region?: string;
    timezone?: string;
}

let cachedToken: string | null = null;

export async function getToken(): Promise<string | null> {
    if (cachedToken) {
        return cachedToken;
    }

    try {
        const response = await fetch("/api/ipinfo/token/");
        if (response.ok) {
            const data = await response.json();
            cachedToken = data.token;
            return cachedToken;
        }
    } catch (error) {
        console.error("获取 IPinfo Token 失败:", error);
    }
    return null;
}

export function clearTokenCache(): void {
    cachedToken = null;
}

export async function getIPGeoInfo(ip?: string): Promise<IPGeoInfo | null> {
    try {
        const path = ip ? `/api/ipinfo/${ip}/` : "/api/ipinfo/";
        const data: any = await apiCall(path, "GET");

        if (data.error) {
            console.error("IPinfo 查询失败:", data.error);
            return null;
        }

        const [latitude, longitude] = (data.loc || "0,0").split(",").map(Number);

        return {
            ip: data.ip || ip || "",
            country: data.country || "",
            city: data.city || "",
            latitude: latitude || 0,
            longitude: longitude || 0,
            org: data.org,
            hostname: data.hostname,
            region: data.region,
            timezone: data.timezone,
        };
    } catch (error) {
        console.error("IPinfo 查询失败:", error);
        return null;
    }
}

export async function batchGetIPGeoInfo(ips: string[]): Promise<IPGeoInfo[]> {
    try {
        const results: IPGeoInfo[] = [];

        for (const ip of ips) {
            const geoInfo = await getIPGeoInfo(ip);
            if (geoInfo) {
                results.push(geoInfo);
            }
        }

        return results;
    } catch (error) {
        console.error("批量 IPinfo 查询失败:", error);
        return [];
    }
}

export function parseLocation(loc: string): { latitude: number; longitude: number } {
    const [latitude, longitude] = (loc || "0,0").split(",").map(Number);
    return {
        latitude: latitude || 0,
        longitude: longitude || 0,
    };
}
