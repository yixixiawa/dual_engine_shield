import { apiCall } from "../client"

export interface IPData {
    ip: string
    city?: string
    region?: string
    country?: string
    loc?: string
    org?: string
    postal?: string
    timezone?: string
    hostname?: string
}

export interface IPQueryResponse {
    status: string
    source: 'cache' | 'api'
    ip_id?: number
    data: IPData
}

export interface BatchIPQueryResponse {
    status: string
    total: number
    cached: number
    queried: number
    failed: number
    results: Array<{
        ip: string
        source: 'cache' | 'api'
        ip_id?: number
        data: IPData
    }>
}

export interface IPDatabaseInfo {
    total_ips: number
    active_ips: number
    countries_count: number
    last_updated: string
}

export interface DatabaseInfoResponse {
    status: string
    database_info: IPDatabaseInfo
}

export const ipinfoAPI = {
    /**
     * 查询单个IP信息
     */
    async query(ipAddress: string, useCache = true): Promise<IPQueryResponse> {
        return apiCall<IPQueryResponse>("/ipinfo/query/", "POST", {
            ip_address: ipAddress,
            use_cache: useCache
        })
    },

    /**
     * 批量查询IP信息
     */
    async batchQuery(ipAddresses: string[], useCache = true): Promise<BatchIPQueryResponse> {
        return apiCall<BatchIPQueryResponse>("/ipinfo/batch-query/", "POST", {
            ip_addresses: ipAddresses,
            use_cache: useCache
        })
    },

    /**
     * 获取IP数据库信息
     */
    async getDatabaseInfo(): Promise<DatabaseInfoResponse> {
        return apiCall<DatabaseInfoResponse>("/ipinfo/database-info/", "GET")
    }
}
