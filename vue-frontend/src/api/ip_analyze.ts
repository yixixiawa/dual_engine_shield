import { apiCall } from "./client"

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

// 域名查询结果
export interface DomainQueryResult {
    status: string;
    domain: string;
    ips: string[];
    total_ips: number;
    results: Array<{
        ip: string;
        source: string;
        data: {
            ip: string;
            country: string;
            city: string;
            loc: string;
            org?: string;
            timezone?: string;
            region?: string;
            latitude?: number;
            longitude?: number;
        };
        error?: string;
    }>;
}

// 地球模型需要的数据格式
export interface GlobeScatterData {
    lon: number;
    lat: number;
    name: string;
    value: number;
}

let cachedToken: string | null = null;

export async function getToken(): Promise<string | null> {
    if (cachedToken) {
        return cachedToken;
    }

    try {
        const response = await fetch("/ipinfo/token/");
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
        const path = ip ? `/ipinfo/${ip}/` : "/ipinfo/";
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

/**
 * 查询域名的地理位置信息
 * 将域名转换为 IP，然后查询该 IP 的地理信息
 * @param domain 域名或 URL
 * @param useCache 是否使用缓存
 * @param resolveAll 是否解析所有 IP
 * @returns 域名查询结果
 */
export async function queryDomain(
    domain: string,
    useCache: boolean = true,
    resolveAll: boolean = false
): Promise<DomainQueryResult | null> {
    try {
        if (!domain || domain.trim() === '') {
            console.error("域名不能为空");
            return null;
        }

        console.log(`🔍 开始查询域名: ${domain}`);

        const response = await fetch("/ipinfo/domain/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                domain: domain.trim(),
                use_cache: useCache,
                resolve_all: resolveAll,
            }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error(
                `❌ 域名查询失败 (${response.status}):`,
                errorData.message || errorData.error || "未知错误"
            );
            return null;
        }

        const result: DomainQueryResult = await response.json();

        if (result.status === "success") {
            console.log(`✅ 域名查询成功:`, result);
            // 解析坐标信息
            result.results.forEach((item) => {
                if (item.data && item.data.loc) {
                    const [lat, lon] = item.data.loc.split(",").map(Number);
                    item.data.latitude = lat;
                    item.data.longitude = lon;
                }
            });
            return result;
        } else {
            console.error("❌ 域名查询返回错误状态:", result.status);
            return null;
        }
    } catch (error) {
        console.error("❌ 域名查询异常:", error);
        return null;
    }
}

/**
 * 将域名查询结果转换为地球模型需要的散点数据格式
 * @param domainResult 域名查询结果
 * @param riskScore 风险评分 (0-100)
 * @returns 地球模型散点数据数组
 */
export function convertToGlobeScatterData(
    domainResult: DomainQueryResult,
    riskScore: number = 90
): GlobeScatterData[] {
    if (!domainResult || !domainResult.results || domainResult.results.length === 0) {
        console.warn("⚠️ 没有有效的地理位置数据");
        return [];
    }

    const scatterData: GlobeScatterData[] = [];

    domainResult.results.forEach((result) => {
        if (result.data && result.data.latitude !== undefined && result.data.longitude !== undefined) {
            const {
                latitude,
                longitude,
                city,
                country,
            } = result.data;

            const displayName = `${domainResult.domain}`;
            const locationName = `${city || "未知"}, ${country || "未知"}`;

            scatterData.push({
                lon: longitude,
                lat: latitude,
                name: `${displayName} (${locationName})`,
                value: riskScore,
            });

            console.log(`📍 添加散点: ${displayName} at (${latitude}, ${longitude})`);
        }
    });

    return scatterData;
}

export function parseLocation(loc: string): { latitude: number; longitude: number } {
    const [latitude, longitude] = (loc || "0,0").split(",").map(Number);
    return {
        latitude: latitude || 0,
        longitude: longitude || 0,
    };
}

/**
 * 获取钓鱼检测结果
 * 从真实的钓鱼检测记录中获取钓鱼链接和威胁等级
 * @returns 钓鱼检测结果数组
 */
export interface PhishingDetectionResult {
    id: number;
    url: string;
    threat_level: string;
    combined_score?: number;
    svm_score?: number;
    ngram_score?: number;
    gte_score?: number;
    model_used?: string;
}

export async function getPhishingDetectionResults(
    filters?: {
        threat_level?: string;
        limit?: number;
        offset?: number;
    }
): Promise<PhishingDetectionResult[]> {
    try {
        console.log('🔍 开始获取钓鱼检测结果...');
        
        // 构建查询参数
        const params = new URLSearchParams();
        if (filters?.threat_level) {
            params.append('threat_level', filters.threat_level);
        }
        if (filters?.limit) {
            params.append('limit', filters.limit.toString());
        }
        if (filters?.offset) {
            params.append('offset', filters.offset.toString());
        }

        // 调用钓鱼检测 API
        const queryString = params.toString() ? `?${params.toString()}` : '';
        const response = await fetch(`/phishing/${queryString}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            console.error(`❌ 获取钓鱼检测结果失败 (${response.status})`);
            return [];
        }

        const data = await response.json();
        
        // 处理分页响应
        let results: PhishingDetectionResult[] = [];
        if (Array.isArray(data)) {
            results = data;
        } else if (data.results && Array.isArray(data.results)) {
            results = data.results;
        } else if (data.data && Array.isArray(data.data)) {
            results = data.data;
        }

        console.log(`✅ 获取到 ${results.length} 条钓鱼检测结果`);
        return results;
    } catch (error) {
        console.error('❌ 获取钓鱼检测结果异常:', error);
        return [];
    }
}

/**
 * 获取仅钓鱼类的检测结果
 * @param limit 限制数量
 * @returns 钓鱼检测结果数组
 */
export async function getPhishingOnlyResults(limit: number = 100): Promise<PhishingDetectionResult[]> {
    return getPhishingDetectionResults({
        threat_level: 'phishing',
        limit: limit,
    });
}
