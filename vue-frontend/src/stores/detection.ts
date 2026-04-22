import { defineStore } from 'pinia'
import { ref } from 'vue'
import { phishingAPI, vulnerabilityAPI } from '@/api'
import { ElMessage } from 'element-plus'
import type { PhishingTrackResponse } from '@/api/modules/phishing'
import type { CodeDetectResponse } from '@/api/modules/vulnerability'

export type DetectionResult = PhishingTrackResponse | CodeDetectResponse

export const useDetectionStore = defineStore('detection', () => {
    const currentModel = ref<'gte'>('gte')
    const threshold = ref(50)
    const isLoading = ref(false)
    const currentResult = ref<DetectionResult | null>(null)
    const history = ref<Array<{ url: string; score: number; timestamp: Date; result: any }>>([])

    const selectModel = (model: 'gte') => {
        currentModel.value = model
    }

    const setThreshold = (value: number) => {
        threshold.value = value
    }

    const detectPhishing = async (url: string) => {
        isLoading.value = true
        try {
            const result = await phishingAPI.detect(url)

            currentResult.value = result

            const score = Number(result.phishing_detection?.score) || 0

            history.value.unshift({
                url,
                score,
                timestamp: new Date(),
                result
            })

            if (history.value.length > 20) history.value.pop()

            return result
        } catch (error: any) {
            ElMessage.error(error.message || '检测失败')
            throw error
        } finally {
            isLoading.value = false
        }
    }

    const batchDetectPhishing = async (urls: string[]) => {
        isLoading.value = true
        try {
            const result = await phishingAPI.batchDetect(urls)
            
            // 将批量检测结果添加到历史记录
            result.results.forEach((item, index) => {
                const score = Number(item.score) || 0
                history.value.unshift({
                    url: item.url,
                    score,
                    timestamp: new Date(),
                    result: item
                })
            })
            
            if (history.value.length > 20) history.value.pop()
            
            return result
        } catch (error: any) {
            ElMessage.error(error.message || '批量检测失败')
            throw error
        } finally {
            isLoading.value = false
        }
    }

    const detectVulnerability = async (code: string, language: string, cweIds?: string[]) => {
        isLoading.value = true
        try {
            const numericCweIds = cweIds ? cweIds.map(id => parseInt(id)) : []
            const result = await vulnerabilityAPI.detectCode(code, language, numericCweIds)
            currentResult.value = result
            return result
        } catch (error: any) {
            ElMessage.error(error.message || '检测失败')
            throw error
        } finally {
            isLoading.value = false
        }
    }

    const detectUrlVulnerability = async (_url: string, _detectTypes?: string[], _maxCodeLength?: number, _cweIds?: string[]) => {
        ElMessage.warning('URL漏洞检测功能暂不支持')
        throw new Error('URL漏洞检测功能暂不支持')
    }

    const clearHistory = () => {
        history.value = []
    }

    return {
        currentModel,
        threshold,
        isLoading,
        currentResult,
        history,
        selectModel,
        setThreshold,
        detectPhishing,
        batchDetectPhishing,
        detectVulnerability,
        detectUrlVulnerability,
        clearHistory
    }
})
