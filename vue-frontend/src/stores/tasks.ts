import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

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

    // 获取任务列表
    const fetchTasks = async () => {
        isLoading.value = true
        try {
            // 在实际应用中，这里会从API获取任务列表
            // const method = alovaInstance.Get('/api/tasks')
            // const result = await method.send()
            // tasks.value = result

            // 暂时使用模拟数据
            tasks.value = [
                {
                    id: 'TASK_1',
                    type: 'phishing',
                    status: 'completed',
                    target: 'https://example.com',
                    createdAt: new Date().toISOString(),
                    result: {
                        risk_score: 85,
                        risk_level: '高',
                        decision: '钓鱼网站'
                    }
                },
                {
                    id: 'TASK_2',
                    type: 'vulnerability',
                    status: 'completed',
                    target: 'sample.js',
                    createdAt: new Date().toISOString(),
                    result: {
                        is_vulnerable: true,
                        severity: '中等',
                        cwe_id: 'CWE-79',
                        cwe_name: '跨站脚本'
                    }
                },
                {
                    id: 'TASK_3',
                    type: 'combined',
                    status: 'processing',
                    target: 'https://test.com',
                    createdAt: new Date().toISOString()
                }
            ]
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