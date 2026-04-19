<template>
    <aside class="sidebar">
        <div class="logo-section">
            <div class="logo">
                <span class="gradient-text">双擎智盾</span>
            </div>
            <div class="subtitle">Dual Engine Shield v3.0</div>
            <div class="tagline">智能安全检测平台</div>
        </div>

        <el-menu :default-active="activeMenu" class="sidebar-menu" @select="handleMenuSelect">
            <template v-for="item in menuItems" :key="item.name">
                <el-menu-item :index="item.name">
                    <el-icon>
                        <component :is="item.icon" />
                    </el-icon>
                    <span>{{ item.title }}</span>
                    <el-badge v-if="item.badge" class="menu-badge" :value="item.badge" :type="item.badgeType" />
                </el-menu-item>
            </template>
        </el-menu>

        <div class="system-status">
            <div class="status-header">
                <span>系统状态</span>
                <el-badge :value="'在线'" type="success" />
            </div>

            <div class="status-content">
                <div class="model-group">
                    <div class="group-title">钓鱼检测模型</div>
                    <div class="model-list">
                        <el-tag size="small" type="info">SVM</el-tag>
                        <el-tag size="small" type="info">GTE</el-tag>
                        <el-tag size="small" type="info">N-gram</el-tag>
                    </div>
                </div>

                <div class="model-group">
                    <div class="group-title">漏洞检测模型</div>
                    <el-tag size="small" type="info">VR</el-tag>
                </div>

                <div class="task-info">
                    <span>待处理任务:</span>
                    <strong>{{ pendingTasksCount }}</strong>
                </div>
            </div>
        </div>
    </aside>
</template>

<script setup lang="ts">
import { computed, h } from 'vue'
import { useRoute, useRouter, RouteRecordRaw } from 'vue-router'
import { useTasksStore } from '@/stores/tasks'
import { Monitor, Warning, Lock, Document } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const tasksStore = useTasksStore()

const activeMenu = computed(() => route.name as string || 'combineddetection')
const pendingTasksCount = computed(() => tasksStore.pendingCount)

interface MenuItem {
    name: string
    title: string
    icon: any
    badge?: string | number
    badgeType?: string
    order: number
}

const iconMap: Record<string, any> = {
    'Monitor': Monitor,
    'Warning': Warning,
    'Lock': Lock,
    'Document': Document
}

const menuItems = computed<MenuItem[]>(() => {
    const routes = router.getRoutes()
    
    return routes
        .filter(r => r.meta?.title && r.name)
        .map(r => {
            const name = r.name as string
            const title = r.meta?.title as string || name
            const iconName = r.meta?.icon as string || 'Document'
            const icon = iconMap[iconName] || Document
            const badge = r.meta?.badge as string | number | undefined
            const badgeType = r.meta?.badgeType as string | undefined
            const order = r.meta?.order as number || 999
            
            // 任务列表特殊处理，显示待处理任务数
            let finalBadge = badge
            if (name === 'taskmanager' && pendingTasksCount.value > 0) {
                finalBadge = pendingTasksCount.value
            }
            
            return {
                name,
                title,
                icon,
                badge: finalBadge,
                badgeType,
                order
            }
        })
        .sort((a, b) => a.order - b.order)
})

const handleMenuSelect = (index: string) => {
    router.push({ name: index })
}
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.sidebar {
    position: fixed;
    left: 0;
    top: 0;
    width: 280px;
    height: 100vh;
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(16px);
    border-right: 1px solid rgba(255, 255, 255, 0.6);
    display: flex;
    flex-direction: column;
    z-index: 50;
}

.logo-section {
    padding: 1.5rem;
    text-align: center;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);

    .logo {
        font-size: 1.5rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 0.5rem;
    }

    .subtitle {
        font-size: 0.75rem;
        color: #6b7280;
        font-family: monospace;
    }

    .tagline {
        font-size: 0.625rem;
        color: #9ca3af;
        margin-top: 0.25rem;
    }
}

.sidebar-menu {
    flex: 1;
    border-right: none;
    background: transparent;
    padding: 0.75rem;

    :deep(.el-menu-item) {
        border-radius: 0.75rem;
        margin-bottom: 0.25rem;
        height: auto;
        padding: 0.75rem 1rem;

        &:hover {
            background: rgba(59, 130, 246, 0.08);
        }

        &.is-active {
            background: linear-gradient(90deg, rgba(59, 130, 246, 0.12), transparent);
            border-left: 3px solid #3b82f6;

            &::before {
                content: '';
                position: absolute;
                left: 0;
                top: 0;
                height: 100%;
                width: 3px;
                background: linear-gradient(to bottom, #3b82f6, #8b5cf6);
            }
        }
    }
}

.system-status {
    margin: 1rem;
    padding: 1rem;
    @include glass;
    border-radius: 0.75rem;

    .status-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.75rem;
        color: #6b7280;
        margin-bottom: 0.75rem;
    }

    .status-content {
        font-size: 0.75rem;

        .model-group {
            margin-bottom: 0.75rem;

            .group-title {
                font-weight: 500;
                color: #374151;
                margin-bottom: 0.5rem;
            }

            .model-list {
                display: flex;
                gap: 0.5rem;
            }
        }

        .task-info {
            display: flex;
            justify-content: space-between;
            padding-top: 0.5rem;
            border-top: 1px solid rgba(0, 0, 0, 0.05);
        }
    }
}
</style>