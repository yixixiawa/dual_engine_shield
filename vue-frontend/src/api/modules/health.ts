import { apiCall } from "../client"

export interface ModelStatus {
    name: string
    type: string
    status: string
    loaded: boolean
    memory_usage: string
}

export interface DatabaseStatus {
    connected: boolean
    type: string
}

export interface PythonBridgeStatus {
    running: boolean
    process_id: number
    uptime: string
}

export interface HealthResponse {
    status: string
    python: string
    backend_version: string
    api_version: string
    models: ModelStatus[]
    database: DatabaseStatus
    python_bridge: PythonBridgeStatus
    timestamp: string
}

export const healthAPI = {
    getHealth() {
        return apiCall<HealthResponse>('/api/health', 'GET')
    }
}