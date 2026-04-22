import { apiCall } from "../client"

export interface PhishingDetectResponse {
    api_version: string
    kind: string
    url: string
    is_phishing: boolean
    score: number
    threshold: number
    scores_per_model?: {
        original?: number
        chiphish?: number
    }
    strategy_used?: string
    allowlist_domain?: string | null
    policy_note?: string | null
    content_stats?: {
        html_char_len: number
        model_input_char_len: number
        html_snippet_max: number
        tokenizer_max_length: number
    }
    latency_ms: number
    error: string | null
    explanation?: string | null
    token_attribution?: Array<{ token: string; score: number }>
    timestamp?: string
}

export interface PhishingTrackIPInfoItem {
    ip: string
    source?: string
    database_id?: number | null
    status?: string
    error?: string
    data?: Record<string, any>
}

export interface PhishingTrackGeoSyncItem {
    ip: string
    status: string
    created?: boolean
    geolocation_id?: number
    location?: {
        country?: string
        city?: string
        latitude?: number
        longitude?: number
        risk_score?: number
    }
    error?: string
}

export interface PhishingTrackResponse {
    status: string
    task_id: number
    phishing_detection: PhishingDetectResponse
    is_phishing: boolean
    domain_resolution: {
        domain: string
        ip_addresses: string[]
        total_ips: number
    } | null
    ipinfo: PhishingTrackIPInfoItem[] | null
    geolocation_sync: PhishingTrackGeoSyncItem[] | null
    message: string
}

export interface IPInfoResult {
    url: string
    status: string
    ip: string
    database_id: number
}

export interface BatchPhishingDetectResponse {
    api_version: string
    kind: string
    timestamp: string
    total_urls: number
    phishing_count: number
    latency_ms: number
    results: PhishingDetectResponse[]
    task_id: number
    task_status: string
    processing_time_ms: number
    ipinfo_results: IPInfoResult[]
}

export interface PhishingConfigResponse {
    mode: string
    threshold: number
    ensemble_strategy: string
    weights: { original: number; chiphish: number }
    available_models: string[]
}

export const phishingAPI = {
    async detect(url: string, htmlContent?: string, explain = false, explainTopK = 20): Promise<PhishingTrackResponse> {
        const payload: any = {
            url,
            use_cache: true,
            resolve_all: false,
            sync_to_geo: true
        }
        if (htmlContent) payload.html_content = htmlContent
        if (explain) {
            payload.explain = true
            payload.explain_top_k = explainTopK
        }
        return apiCall<PhishingTrackResponse>("/detect/phishing-track/", "POST", payload)
    },

    async batchDetect(urls: string[], htmlContents?: Record<string, string>): Promise<BatchPhishingDetectResponse> {
        const payload: any = { urls }
        if (htmlContents) payload.html_contents = htmlContents
        return apiCall<BatchPhishingDetectResponse>("/detect/batch-fish/", "POST", payload)
    },

    async getConfig(): Promise<PhishingConfigResponse> {
        return apiCall<PhishingConfigResponse>("/detect/fish-config/", "GET")
    }
}
