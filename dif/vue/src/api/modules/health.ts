import { apiCall } from "../client"

export interface ModelInfo {
    enabled: boolean
    available: boolean
}

export interface HealthResponse {
    status: string
    timestamp: string
    services: {
        database: string
        models: {
            phishing: ModelInfo
            vulnerability: ModelInfo
        }
    }
}

export const healthAPI = {
    async getHealth(): Promise<HealthResponse> {
        return apiCall<HealthResponse>("/health/", "GET")
    }
}