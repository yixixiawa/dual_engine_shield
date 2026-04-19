/**
 * API 配置 - Django 后端
 */

// API 基础 URL
export const BASE_URL = 'http://localhost:8000/api'

// API 端点
export const ENDPOINTS = {
  // 健康检查
  health: {
    check: '/health/check/',
  },

  // 钓鱼检测
  phishing: {
    detect: '/phishing/detect/',
    list: '/phishing/',
  },

  // 漏洞检测
  vulnerabilities: {
    detectCode: '/vulnerabilities/detect_code/',
    batchDetect: '/vulnerabilities/batch_detect/',
    scanFile: '/vulnerabilities/scan_file/',
    scanDirectory: '/vulnerabilities/scan_directory/',
    list: '/vulnerabilities/',
  },
}

// 请求超时（毫秒）
export const REQUEST_TIMEOUT = 30000

// API 请求配置
export const API_CONFIG = {
  baseURL: BASE_URL,
  timeout: REQUEST_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
}

// 模型选项
export const PHISHING_MODELS = [
  { value: 'svm', label: 'SVM 模型' },
  { value: 'ngram', label: 'N-gram 模型' },
  { value: 'gte', label: 'GTE 模型' },
  { value: 'combined', label: '综合模型' },
]

export const SUPPORTED_LANGUAGES = [
  'c',
  'python',
  'java',
  'javascript',
  'cpp',
  'csharp',
]

export const DEVICE_OPTIONS = [
  { value: 'auto', label: '自动' },
  { value: 'cuda', label: 'CUDA (GPU)' },
  { value: 'cpu', label: 'CPU' },
]
