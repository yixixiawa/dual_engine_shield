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
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
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
    
    // 排除不显示在侧边栏的路由
    const hiddenRoutes = ['earthmodel', 'NotFound']
    
    return routes
        .filter(r => r.meta?.title && r.name && !hiddenRoutes.includes(r.name as string))
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
@use '@/styles/mixins.scss' as *;

.sidebar {
    position: sticky;
    top: 0;
    align-self: start;
    width: 100%;
    min-height: 100vh;
    background: rgba(255, 255, 255, 0.92);
    backdrop-filter: blur(18px);
    border-right: 1px solid rgba(24, 144, 255, 0.08);
    display: flex;
    flex-direction: column;
}

.logo-section {
    padding: $space-8 $space-6 $space-6;
    text-align: center;
    border-bottom: 1px solid rgba(15, 23, 42, 0.06);

    .logo {
        font-size: 1.5rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: $space-2;
    }

    .subtitle {
        font-size: 0.75rem;
        color: $text-secondary;
        font-family: 'JetBrains Mono', monospace;
    }

    .tagline {
        font-size: 0.75rem;
        color: $text-muted;
        margin-top: $space-1;
    }
}

.sidebar-menu {
    flex: 1;
    border-right: none;
    background: transparent;
    padding: $space-4;

    :deep(.el-menu-item) {
        border-radius: $radius-md;
        margin-bottom: $space-2;
        height: auto;
        padding: 0.875rem 1rem;
        color: $text-secondary;

        &:hover {
            background: rgba(24, 144, 255, 0.08);
            color: $primary-active;
        }

        &.is-active {
            background: rgba(24, 144, 255, 0.12);
            color: $primary-active;
            border-left: 3px solid $primary;
            font-weight: 600;
        }
    }
}

.system-status {
    margin: $space-4;
    padding: $space-4;
    @include app-card;

    .status-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.75rem;
        color: $text-secondary;
        margin-bottom: $space-3;
    }

    .status-content {
        font-size: 0.8125rem;

        .model-group {
            margin-bottom: $space-3;

            .group-title {
                font-weight: 600;
                color: $text-primary;
                margin-bottom: $space-2;
            }

            .model-list {
                display: flex;
                flex-wrap: wrap;
                gap: $space-2;
            }
        }

        .task-info {
            display: flex;
            justify-content: space-between;
            padding-top: $space-3;
            border-top: 1px solid rgba(15, 23, 42, 0.06);
            color: $text-secondary;
        }
    }
}

@media (max-width: $breakpoint-md) {
    .sidebar {
        position: static;
        min-height: auto;
        border-right: none;
        border-bottom: 1px solid rgba(24, 144, 255, 0.08);
    }

    .logo-section {
        padding: $space-5 $space-4;
    }

    .sidebar-menu {
        padding: $space-3;
    }

    .system-status {
        margin-top: 0;
    }
}
</style>
