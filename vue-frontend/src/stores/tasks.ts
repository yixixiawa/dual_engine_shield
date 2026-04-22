import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getTaskList, type Task as ApiTask } from '@/api'

// 定义任务接口
export interface Task {
    id: string
    type: 'phishing' | 'source_code' | 'url' | 'web' | 'batch' | 'combined' | 'vulnerability'
    status: 'pending' | 'processing' | 'completed' | 'failed'
    target: string
    createdAt: string
    result?: any
}

export const useTasksStore = defineStore('tasks', () => {
    const tasks = ref<Task[]>([])
    const currentTask = ref<Task | null>(null)
    const detailVisible = ref(false)
    const isLoading = ref(false)

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
    const convertApiTaskToTask = (apiTask: ApiTask): Task => {
        // 尝试解析 input_data 为 JSON，获取目标 URL
        let target = apiTask.input_data
        try {
            const inputData = JSON.parse(apiTask.input_data)
            if (inputData.url) {
                target = inputData.url
            }
        } catch (e) {
            // 如果解析失败，使用原始 input_data
        }

        return {
            id: `TASK_${apiTask.task_id}`,
            type: 'phishing', // 默认为钓鱼检测
            status: apiTask.status as 'pending' | 'processing' | 'completed' | 'failed',
            target: target,
            createdAt: apiTask.created_at,
            result: apiTask.error_message ? { error: apiTask.error_message } : undefined
        }
    }

    // 获取任务列表
    const fetchTasks = async () => {
        isLoading.value = true
        try {
            // 从后端 API 获取任务列表
            const response = await getTaskList()
            
            // 转换 API 任务为前端任务
            tasks.value = response.tasks.map(convertApiTaskToTask)
        } catch (error: any) {
            console.error('获取任务列表失败:', error)
        } finally {
            isLoading.value = false
        }
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
        pendingCount,
        processingCount,
        completedCount,
        failedCount,
        addTask,
        updateTask,
        getTask,
        removeTask,
        clearTasks,
        fetchTasks,
        showTaskDetail,
        closeTaskDetail
    }
})