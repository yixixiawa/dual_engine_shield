import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getTaskList, type Task as ApiTask } from '@/api'

// 定义任务接口
export interface Task {
    id: number
    task_id: number
    detection_type: string
    status: string
    input_data: string
    result?: any
    processing_time?: number
    error_message?: string | null
    createdAt: string
    updatedAt: string
}

export const useTasksStore = defineStore('tasks', () => {
    const tasks = ref<Task[]>([])
    const currentTask = ref<Task | null>(null)
    const detailVisible = ref(false)
    const isLoading = ref(false)
    
    // 分页状态
    const currentPage = ref(1)
    const pageSize = ref(20)
    const totalTasks = ref(0)

    // 计算属性
    const pendingCount = computed(() => tasks.value.filter(t => t.status === 'pending').length)
    const processingCount = computed(() => tasks.value.filter(t => t.status === 'processing').length)
    const completedCount = computed(() => tasks.value.filter(t => t.status === 'completed').length)
    const failedCount = computed(() => tasks.value.filter(t => t.status === 'failed').length)

    // 添加任务
    const addTask = (task: Omit<Task, 'id'>) => {
        const newTask: Task = {
            id: `TASK_${Date.now()}`,
            ...task
        }
        tasks.value.unshift(newTask)
        return newTask.id
    }

    // 更新任务
    const updateTask = (taskId: string, updates: Partial<Task>) => {
        const task = tasks.value.find(t => t.id === taskId)
        if (task) {
            Object.assign(task, updates)
        }
    }

    // 获取任务
    const getTask = (taskId: string) => tasks.value.find(t => t.id === taskId)

    // 删除任务
    const removeTask = (taskId: string) => {
        const index = tasks.value.findIndex(t => t.id === taskId)
        if (index !== -1) tasks.value.splice(index, 1)
    }

    // 清空任务
    const clearTasks = () => {
        tasks.value = []
    }

    // 从API任务转换为前端任务
    const convertApiTaskToTask = (apiTask: any): Task => {
        // 尝试解析 input_data 为 JSON，获取目标 URL
        let inputData = apiTask.input_data
        try {
            const parsed = JSON.parse(apiTask.input_data)
            if (parsed.url) {
                inputData = parsed.url
            } else if (parsed.urls) {
                inputData = `批量检测: ${parsed.urls.length} 个URL`
            }
        } catch (e) {
            // 如果解析失败，使用原始 input_data
        }

        return {
            id: apiTask.id,
            task_id: apiTask.task_id || apiTask.id, // 兼容后端数据，使用id作为task_id的 fallback
            detection_type: apiTask.detection_type || 'phishing',
            status: apiTask.status,
            input_data: inputData,
            result: apiTask.result,
            processing_time: apiTask.processing_time_ms || apiTask.processing_time, // 兼容后端数据，处理字段名差异
            error_message: apiTask.error_message,
            createdAt: apiTask.created_at,
            updatedAt: apiTask.updated_at
        }
    }

    // 获取任务列表
    const fetchTasks = async () => {
        isLoading.value = true
        try {
            // 从后端 API 获取任务列表，传递分页参数
            const response = await getTaskList({ 
                page: currentPage.value,
                page_size: pageSize.value
            })
            
            // 后端返回的是数组格式 [{...}, {...}, ...]
            if (Array.isArray(response)) {
                tasks.value = response.map(convertApiTaskToTask)
                totalTasks.value = response.length
            } else if (response.results) {
                // 标准格式：{ results: [...], count: number }
                tasks.value = response.results.map(convertApiTaskToTask)
                totalTasks.value = response.count || 0
            } else {
                console.warn('获取任务列表返回了非预期的数据格式:', response)
                tasks.value = []
                totalTasks.value = 0
            }
        } catch (error: any) {
            console.error('获取任务列表失败:', error)
            tasks.value = []
            totalTasks.value = 0
        } finally {
            isLoading.value = false
        }
    }

    // 设置当前页码
    const setPage = (page: number) => {
        currentPage.value = page
        fetchTasks()
    }

    // 设置每页大小
    const setPageSize = (size: number) => {
        pageSize.value = size
        currentPage.value = 1 // 重置为第一页
        fetchTasks()
    }

    // 重置分页
    const resetPagination = () => {
        currentPage.value = 1
        pageSize.value = 20
    }

    // 显示任务详情
    const showTaskDetail = (task: Task) => {
        currentTask.value = task
        detailVisible.value = true
    }

    const closeTaskDetail = () => {
        detailVisible.value = false
        currentTask.value = null
    }

    return {
        tasks,
        currentTask,
        detailVisible,
        isLoading,
        // 分页相关
        currentPage,
        pageSize,
        totalTasks,
        // 计算属性
        pendingCount,
        processingCount,
        completedCount,
        failedCount,
        // 方法
        addTask,
        updateTask,
        getTask,
        removeTask,
        clearTasks,
        fetchTasks,
        showTaskDetail,
        closeTaskDetail,
        setPage,
        setPageSize,
        resetPagination
    }
})