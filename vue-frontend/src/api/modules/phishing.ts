import { apiCall } from "../client"

export interface PhishingDetectPayload {
    url: string
    model_type: string
    threshold: number
}

export interface ModelPrediction {
    score: number
    prediction: number
}

export interface PhishingFeatures {
    brand_typo: boolean
    subdomain_count: number
    domain_age: number
    ip_address: boolean
    url_length: number
    special_chars: boolean
    has_dash: boolean
    tld_suspicious: boolean
    port_number: boolean
    protocol_https: boolean
    dns_record: boolean
    page_rank: number
    whois_age: number
    favicon_match: boolean
    content_similarity: number
}

export interface PhishingDetectResponse {
    url: string
    is_phishing: boolean
    probability: number
    scan_time: string
    confidence: number
    models: {
        svm: ModelPrediction
        ngram: ModelPrediction
        gte: ModelPrediction
    }
    features: PhishingFeatures
}

export const phishingAPI = {
    detect(url: string, modelType = "combined", threshold = 70): Promise<PhishingDetectResponse> {
        return apiCall<PhishingDetectResponse>("/api/phishing/detect", "POST", {
            url,
            model_type: modelType,
            threshold: threshold / 100
        })
    },
    async batchDetect(urls: string[], modelType = "combined", threshold = 70): Promise<{ results: PhishingDetectResponse[]; total: number }> {
        const results = await Promise.all(
            urls.map((url) => this.detect(url, modelType, threshold))
        )
        return { results, total: results.length }
    }
}
