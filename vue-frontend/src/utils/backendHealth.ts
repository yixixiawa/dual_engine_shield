import { API_BASE } from '../api/client'

/**
 * 检测后端服务器健康状态
 * @returns Promise<boolean> - 后端服务器是否可达
 */
export const checkBackendHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch(`${API_BASE}/api/health`, {
      method: 'GET',
      timeout: 3000,
      credentials: 'include'
    })
    return response.ok
  } catch (error) {
    console.error('后端服务器检测失败:', error)
    return false
  }
}

/**
 * 检测后端服务器状态并返回结果
 * @returns Promise<{ isOnline: boolean; message: string }>
 */
export const getBackendStatus = async (): Promise<{ isOnline: boolean; message: string }> => {
  try {
    const isOnline = await checkBackendHealth()
    if (isOnline) {
      return {
        isOnline: true,
        message: '后端服务器正常运行'
      }
    } else {
      return {
        isOnline: false,
        message: '后端服务器无法访问，请检查服务器是否启动'
      }
    }
  } catch (error) {
    return {
      isOnline: false,
      message: '未能找到后端服务器，请确保后端服务已启动'
    }
  }
}

/**
 * 检测后端服务器状态并显示提示
 * @param onStatusChange - 状态变化回调
 */
export const monitorBackendStatus = async (onStatusChange?: (isOnline: boolean, message: string) => void): Promise<void> => {
  const status = await getBackendStatus()
  if (onStatusChange) {
    onStatusChange(status.isOnline, status.message)
  }
  return status
}
