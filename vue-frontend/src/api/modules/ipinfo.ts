import { apiCall } from "../client"

export interface IPInfoResponse {
    ip: string;
    hostname?: string;
    city?: string;
    region?: string;
    country?: string;
    loc?: string;        // 经纬度格式："纬度,经度"
    postal?: string;
    timezone?: string;
    org?: string;        // ISP 信息
    asn?: {
        asn: string;
        name: string;
        domain: string;
        route: string;
        type: string;
    };
    company?: {
        name: string;
        domain: string;
        type: string;
    };
    carrier?: {
        name: string;
        mcc: string;
        mnc: string;
    };
    abuse?: {
        address: string;
        country: string;
        email: string;
        name: string;
        network: string;
        phone: string;
    };
    domains?: {
        ip: string;
        total: number;
        domains: string[];
    };
}

// 配置接口
export interface IPinfoConfig {
    baseUrl: string;
    apiToken: string;
}

// 错误响应
export interface ErrorResponse {
    error: {
        title: string;
        message: string;
        status: number;
    };
}

export const ipinfoAPI = {
    /**
     * 获取指定 IP 的信息
     * @param ip 要查询的 IP 地址（不填则查询当前 IP）
     */
    getInfo(ip?: string): Promise<IPInfoResponse> {
        const path = ip ? `/api/ipinfo/${ip}` : "/api/ipinfo"
        return apiCall<IPInfoResponse>(path, "GET")
    },

    /**
     * 批量获取多个 IP 的信息
     * @param ips 要查询的 IP 地址数组
     */
    async batchGetInfo(ips: string[]): Promise<{ results: IPInfoResponse[]; total: number }> {
        const results = await Promise.all(ips.map(ip => this.getInfo(ip)))
        return { results, total: results.length }
    }
}
