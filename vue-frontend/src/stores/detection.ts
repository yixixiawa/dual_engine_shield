import { defineStore } from 'pinia'
import { ref } from 'vue'
import { phishingAPI, vulnerabilityAPI } from '@/api'
import { ElMessage } from 'element-plus'
import type { PhishingDetectResponse } from '@/api/modules/phishing'
import type { CodeDetectResponse } from '@/api/modules/vulnerability'

export type DetectionResult = PhishingDetectResponse | CodeDetectResponse

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

    // 钓鱼检测
    const detectPhishing = async (url: string) => {
        isLoading.value = true
        try {
            const result = await phishingAPI.detect(url) as DetectionResult

            currentResult.value = result

            // 添加到历史
            const score = 'score' in result ? Number(result.score) || 0 : 0
            
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

    // 批量钓鱼检测
    const batchDetectPhishing = async (urls: string[]) => {
        isLoading.value = true
        try {
            const result = await phishingAPI.batchDetect(urls)
            return result
        } catch (error: any) {
            ElMessage.error(error.message || '批量检测失败')
            throw error
        } finally {
            isLoading.value = false
        }
    }

    // 代码漏洞检测
    const detectVulnerability = async (code: string, language: string, cweIds?: string[]) => {
        isLoading.value = true
        try {
            // 将 cweIds 转换为数字数组
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

    // URL漏洞检测 - 暂不支持（后端API未提供此端点）
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