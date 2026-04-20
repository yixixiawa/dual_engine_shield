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
    latency_ms: number
    error: string | null
    token_attribution?: Array<{ token: string; score: number }>
    timestamp?: string
}

export interface BatchPhishingDetectResponse {
    api_version: string
    kind: string
    total_urls: number
    phishing_count: number
    latency_ms: number
    results: PhishingDetectResponse[]
}

export interface PhishingConfigResponse {
    mode: string
    threshold: number
    ensemble_strategy: string
    weights: { original: number; chiphish: number }
    available_models: string[]
}

export const phishingAPI = {
    async detect(url: string, htmlContent?: string, explain = false, explainTopK = 20): Promise<PhishingDetectResponse> {
        const payload: any = { url }
        if (htmlContent) payload.html_content = htmlContent
        if (explain) {
            payload.explain = true
            payload.explain_top_k = explainTopK
        }
        return apiCall<PhishingDetectResponse>("/detect/fish/", "POST", payload)
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
