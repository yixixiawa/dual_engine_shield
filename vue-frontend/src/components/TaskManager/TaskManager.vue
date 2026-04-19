<template>
    <div class="task-manager">
        <!-- 统计卡片 -->
        <div class="stats-grid">
            <StatCard v-for="stat in stats" :key="stat.label" :label="stat.label" :value="stat.value"
                :color="stat.color" :icon="stat.icon" />
        </div>

        <!-- 筛选栏 -->
        <el-card class="filter-card" shadow="hover">
            <div class="filters">
                <div class="filter-group">
                    <span class="filter-label">状态筛选:</span>
                    <el-select v-model="statusFilter" placeholder="全部" clearable size="default">
                        <el-option label="全部" value="all" />
                        <el-option label="待处理" value="pending" />
                        <el-option label="检测中" value="processing" />
                        <el-option label="已完成" value="completed" />
                        <el-option label="失败" value="failed" />
                    </el-select>
                </div>

                <div class="filter-group">
                    <span class="filter-label">类型筛选:</span>
                    <el-select v-model="typeFilter" placeholder="全部" clearable size="default">
                        <el-option label="全部" value="all" />
                        <el-option label="钓鱼检测" value="phishing" />
                        <el-option label="源码检测" value="source_code" />
                        <el-option label="URL检测" value="url" />
                        <el-option label="Web扫描" value="web" />
                        <el-option label="综合检测" value="combined" />
                    </el-select>
                </div>

                <el-button @click="refreshTasks" :icon="Refresh">刷新</el-button>
            </div>
        </el-card>

        <!-- 任务列表 -->
        <el-card class="task-list-card" shadow="hover">
            <template #header>
                <div class="card-header">
                    <el-icon>
                        <List />
                    </el-icon>
                    <span>任务列表</span>
                </div>
            </template>

            <el-table :data="filteredTasks" stripe v-loading="tasksStore.isLoading" style="width: 100%">
                <el-table-column prop="id" label="任务ID" width="200">
                    <template #default="{ row }">
                        <span class="mono text-sm">{{ row.id }}</span>
                    </template>
                </el-table-column>

                <el-table-column prop="type" label="类型" width="120">
                    <template #default="{ row }">
                        <el-tag :type="getTypeTagType(row.type)" size="small">
                            {{ getTypeName(row.type) }}
                        </el-tag>
                    </template>
                </el-table-column>

                <el-table-column prop="status" label="状态" width="110">
                    <template #default="{ row }">
                        <el-tag :type="getStatusTagType(row.status)" size="small">
                            {{ getStatusName(row.status) }}
                        </el-tag>
                    </template>
                </el-table-column>

                <el-table-column prop="target" label="目标" min-width="200" show-overflow-tooltip />

                <el-table-column prop="result" label="结果" width="180">
                    <template #default="{ row }">
                        <TaskResultBadge :task="row" />
                    </template>
                </el-table-column>

                <el-table-column prop="createdAt" label="创建时间" width="170" />

                <el-table-column label="操作" width="100" fixed="right">
                    <template #default="{ row }">
                        <el-button type="primary" link size="small" @click="showTaskDetail(row)">
                            查看详情
                        </el-button>
                    </template>
                </el-table-column>
            </el-table>

            <div v-if="filteredTasks.length === 0" class="empty-state">
                <el-empty description="暂无任务" />
            </div>
        </el-card>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useTasksStore } from '@/stores/tasks'
import StatCard from './StatCard.vue'
import TaskResultBadge from './TaskResultBadge.vue'
import { Refresh, List } from '@element-plus/icons-vue'

const tasksStore = useTasksStore()
const statusFilter = ref('all')
const typeFilter = ref('all')

type StatColor = 'primary' | 'success' | 'warning' | 'danger' | 'info'

const stats = computed(() => [
    { label: '总任务数', value: tasksStore.tasks.length, color: 'primary' as StatColor, icon: 'Document' },
    { label: '待处理', value: tasksStore.pendingCount, color: 'warning' as StatColor, icon: 'Timer' },
    { label: '检测中', value: tasksStore.processingCount, color: 'info' as StatColor, icon: 'Loading' },
    { label: '已完成', value: tasksStore.completedCount, color: 'success' as StatColor, icon: 'Check' }
])

const filteredTasks = computed(() => {
    let filtered = tasksStore.tasks
    if (statusFilter.value !== 'all') {
        filtered = filtered.filter(t => t.status === statusFilter.value)
    }
    if (typeFilter.value !== 'all') {
        filtered = filtered.filter(t => t.type === typeFilter.value)
    }
    return filtered
})

const getTypeName = (type: string) => {
    const names: Record<string, string> = {
        phishing: '钓鱼检测',
        source_code: '源码检测',
        url: 'URL检测',
        web: 'Web扫描',
        batch: '批量检测',
        combined: '综合检测',
        vulnerability: '漏洞检测'
    }
    return names[type] || type
}

const getTypeTagType = (type: string) => {
    const types: Record<string, string> = {
        phishing: 'danger',
        source_code: 'warning',
        url: 'info',
        web: 'success',
        batch: 'primary',
        combined: '',
        vulnerability: 'warning'
    }
    return types[type] || 'info'
}

const getStatusName = (status: string) => {
    const names: Record<string, string> = {
        pending: '待处理',
        processing: '检测中',
        completed: '已完成',
        failed: '失败'
    }
    return names[status] || status
}

const getStatusTagType = (status: string) => {
    const types: Record<string, string> = {
        pending: 'warning',
        processing: 'info',
        completed: 'success',
        failed: 'danger'
    }
    return types[status] || 'info'
}

const showTaskDetail = (task: any) => {
    tasksStore.showTaskDetail(task)
}

const refreshTasks = () => {
    tasksStore.fetchTasks()
}

onMounted(() => {
    tasksStore.fetchTasks()
})
</script>

<style lang="scss" scoped>
.task-manager {
    max-width: 1400px;
    margin: 0 auto;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.filter-card {
    margin-bottom: 1.5rem;
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(16px);

    .filters {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 1rem;

        .filter-group {
            display: flex;
            align-items: center;
            gap: 0.5rem;

            .filter-label {
                font-size: 0.875rem;
                color: #6b7280;
            }
        }
    }
}

.task-list-card {
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(16px);

    .card-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-weight: 500;
    }

    :deep(.el-table) {
        background: transparent;

        th {
            background: rgba(0, 0, 0, 0.02);
        }

        .mono {
            font-family: monospace;
        }

        .text-sm {
            font-size: 0.75rem;
        }
    }
}

.empty-state {
    padding: 2rem;
}
</style>